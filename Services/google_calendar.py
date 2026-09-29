"""One-way synchronization from choir events to one shared Google Calendar."""

import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests
from cryptography.fernet import Fernet, InvalidToken

from Services.google_oauth import TOKEN_ENDPOINT


CALENDAR_SCOPES = (
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.events",
)
LEGACY_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"


class CalendarError(RuntimeError):
    pass


class CalendarNotConnected(CalendarError):
    pass


class GoogleCalendarService:
    def __init__(self, repository):
        self.repository = repository
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        self.key = os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY", "").strip()

    @property
    def configured(self):
        if not (self.client_id and self.client_secret and self.key):
            return False
        try:
            Fernet(self.key.encode())
            return True
        except (ValueError, TypeError):
            return False

    def _fernet(self):
        if not self.configured:
            raise CalendarError("Manjka veljavna konfiguracija za varno shranjevanje Google žetonov.")
        return Fernet(self.key.encode())

    def _encrypt(self, value):
        return self._fernet().encrypt(value.encode()).decode() if value else None

    def _decrypt(self, value):
        if not value:
            return None
        try:
            return self._fernet().decrypt(value.encode()).decode()
        except InvalidToken as error:
            raise CalendarError("Shranjene povezave z Googlom ni mogoče odpreti. Poveži račun znova.") from error

    @staticmethod
    def token_expiry(token_data):
        seconds = int(token_data.get("expires_in") or 3600)
        return datetime.now(timezone.utc) + timedelta(seconds=max(seconds - 30, 0))

    def store_authorization(self, token_data, claims, user_id):
        granted_scopes = set((token_data.get("scope") or "").split())
        if not (set(CALENDAR_SCOPES).issubset(granted_scopes) or LEGACY_CALENDAR_SCOPE in granted_scopes):
            raise CalendarError("Google ni odobril zahtevanega dostopa do koledarja.")
        self.repository.save_calendar_credentials({
            "google_email": claims["email"].strip().lower(),
            "access_token_encrypted": self._encrypt(token_data["access_token"]),
            "refresh_token_encrypted": self._encrypt(token_data.get("refresh_token")),
            "token_expires_at": self.token_expiry(token_data),
            "scopes": token_data.get("scope", ""),
            "connected_by": user_id,
        })

    def _refresh(self, connection):
        refresh_token = self._decrypt(connection.get("refresh_token_encrypted"))
        if not refresh_token:
            raise CalendarNotConnected("Google povezava je potekla. Poveži račun znova.")
        try:
            result = requests.post(TOKEN_ENDPOINT, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }, timeout=15)
            result.raise_for_status()
            payload = result.json()
        except (requests.RequestException, ValueError) as error:
            raise CalendarError("Google povezave ni bilo mogoče osvežiti.") from error
        access_token = payload.get("access_token")
        if not access_token:
            raise CalendarError("Google ni vrnil novega dostopnega žetona.")
        self.repository.update_calendar_tokens(
            self._encrypt(access_token),
            self._encrypt(payload.get("refresh_token")),
            self.token_expiry(payload),
        )
        return access_token

    def _access_token(self, connection):
        if not connection or not connection.get("active"):
            raise CalendarNotConnected("Skupni Google Koledar še ni povezan.")
        expiry = connection.get("token_expires_at")
        if expiry and expiry > datetime.now(timezone.utc) + timedelta(seconds=30):
            token = self._decrypt(connection.get("access_token_encrypted"))
            if token:
                return token
        return self._refresh(connection)

    def _request(self, method, path, *, connection=None, retry=True, **kwargs):
        connection = connection or self.repository.get_calendar_connection()
        token = self._access_token(connection)
        headers = {**kwargs.pop("headers", {}), "Authorization": f"Bearer {token}"}
        try:
            result = requests.request(method, f"{CALENDAR_API}{path}", headers=headers, timeout=15, **kwargs)
        except requests.RequestException as error:
            raise CalendarError("Google Koledar trenutno ni dosegljiv.") from error
        if result.status_code == 401 and retry:
            token = self._refresh(connection)
            headers["Authorization"] = f"Bearer {token}"
            return self._request(method, path, connection=self.repository.get_calendar_connection(), retry=False, headers={k:v for k,v in headers.items() if k != "Authorization"}, **kwargs)
        return result

    def list_calendars(self):
        result = self._request("GET", "/users/me/calendarList", params={"minAccessRole": "writer"})
        if not result.ok:
            raise CalendarError("Seznama koledarjev ni bilo mogoče pridobiti.")
        return [{"id": item["id"], "name": item.get("summaryOverride") or item.get("summary") or item["id"], "primary": bool(item.get("primary"))} for item in result.json().get("items", [])]

    def select_calendar(self, calendar_id):
        connection = self.repository.get_calendar_connection()
        if connection and connection.get("calendar_id") and connection["calendar_id"] != calendar_id:
            raise CalendarError("Ciljni koledar je že izbran. Za varno zamenjavo je potrebna načrtovana migracija dogodkov.")
        calendars = self.list_calendars()
        selected = next((item for item in calendars if item["id"] == calendar_id), None)
        if not selected:
            raise CalendarError("Izbrani koledar ni na voljo za urejanje.")
        self.repository.select_google_calendar(selected["id"], selected["name"])
        return selected

    @staticmethod
    def google_event_id(event_id):
        digest = hashlib.sha256(f"choir-event:{event_id}".encode()).digest()[:15]
        encoded = base64.b32hexencode(digest).decode().lower().rstrip("=")
        return f"choirevent{encoded}"

    @staticmethod
    def event_payload(event, google_event_id):
        start = event["event_date"]
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        end = start + timedelta(hours=2)
        return {
            "id": google_event_id,
            "summary": event["name"],
            "location": event.get("place") or "",
            "description": event.get("event_type") or "",
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
            "extendedProperties": {"private": {"zborissimoEventId": str(event["id"])}},
        }

    def sync_event(self, event):
        connection = self.repository.get_calendar_connection()
        if not connection or not connection.get("active") or not connection.get("calendar_id"):
            raise CalendarNotConnected("Skupni Google Koledar še ni povezan in izbran.")
        calendar_id = connection["calendar_id"]
        google_id = self.google_event_id(event["id"])
        link = self.repository.get_event_calendar_link(event["id"])
        if link and link["calendar_id"] != calendar_id:
            raise CalendarError("Dogodek je že povezan z drugim ciljnim koledarjem.")
        path = f"/calendars/{quote(calendar_id, safe='')}/events"
        payload = self.event_payload(event, google_id)
        try:
            if link:
                result = self._request("PUT", f"{path}/{quote(google_id, safe='')}", connection=connection, json=payload)
                if result.status_code == 404:
                    result = self._request("POST", path, connection=connection, json=payload)
                    if result.status_code == 409:
                        result = self._request("PUT", f"{path}/{quote(google_id, safe='')}", connection=connection, json=payload)
            else:
                result = self._request("POST", path, connection=connection, json=payload)
                if result.status_code == 409:
                    result = self._request("PUT", f"{path}/{quote(google_id, safe='')}", connection=connection, json=payload)
            if not result.ok:
                raise CalendarError(f"Google Koledar je vrnil napako ({result.status_code}).")
        except CalendarError as error:
            self.repository.record_event_calendar_sync(event["id"], calendar_id, google_id, str(error))
            raise
        self.repository.record_event_calendar_sync(event["id"], calendar_id, google_id)

    def delete_event(self, event_id):
        link = self.repository.get_event_calendar_link(event_id)
        if not link:
            return
        connection = self.repository.get_calendar_connection()
        if not connection or not connection.get("active") or connection.get("calendar_id") != link["calendar_id"]:
            raise CalendarNotConnected("Pred izbrisom dogodka znova poveži njegov skupni Google Koledar.")
        path = f"/calendars/{quote(link['calendar_id'], safe='')}/events/{quote(link['google_event_id'], safe='')}"
        result = self._request("DELETE", path, connection=connection)
        if result.status_code not in {204, 404, 410}:
            raise CalendarError(f"Dogodka ni bilo mogoče izbrisati iz Google Koledarja ({result.status_code}).")
        self.repository.clear_event_calendar_link(event_id)

    def sync_all(self):
        succeeded = failed = 0
        for event in self.repository.list_events():
            try:
                self.sync_event(event)
                succeeded += 1
            except CalendarError:
                failed += 1
        return succeeded, failed

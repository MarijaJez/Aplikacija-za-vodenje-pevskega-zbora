"""One-way choir event synchronization to consenting members' primary calendars."""

import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests
from cryptography.fernet import Fernet, InvalidToken

from Services.google_oauth import TOKEN_ENDPOINT

CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events.owned"
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
            raise CalendarNotConnected("Shranjene povezave ni mogoče odpreti. Poveži račun znova.") from error

    @staticmethod
    def token_expiry(token_data):
        seconds = int(token_data.get("expires_in") or 3600)
        return datetime.now(timezone.utc) + timedelta(seconds=max(seconds - 30, 0))

    def store_authorization(self, token_data, claims, user_id):
        if CALENDAR_SCOPE not in (token_data.get("scope") or "").split():
            raise CalendarError("Google ni odobril dostopa do dogodkov v koledarju.")
        user = self.repository.get_user_by_id(user_id)
        google_email = (claims.get("email") or "").strip().lower()
        if not user or google_email != user["email"].strip().lower():
            raise CalendarError("Poveži Google račun z enakim e-poštnim naslovom kot tvoj članski račun.")
        subject = claims.get("sub")
        if not subject:
            raise CalendarError("Google ni vrnil identitete računa.")
        previous = self.repository.get_user_calendar_connection(user_id)
        if not token_data.get("refresh_token") and not (previous and previous["google_subject"] == subject and previous.get("refresh_token_encrypted")):
            raise CalendarError("Google ni vrnil trajnega dovoljenja. Odstrani dovoljenje v Google računu in poveži znova.")
        if previous and previous["google_subject"] != subject:
            if previous["active"]:
                raise CalendarError("Najprej prekini staro povezavo, nato poveži drug Google račun.")
            self.repository.reset_user_calendar_account(user_id)
        self.repository.save_user_calendar_credentials({
            "user_id": user_id, "google_subject": subject, "google_email": google_email,
            "access_token_encrypted": self._encrypt(token_data["access_token"]),
            "refresh_token_encrypted": self._encrypt(token_data.get("refresh_token")),
            "token_expires_at": self.token_expiry(token_data),
            "scopes": token_data.get("scope", ""),
        })

    def _refresh(self, connection):
        refresh_token = self._decrypt(connection.get("refresh_token_encrypted"))
        if not refresh_token:
            raise CalendarNotConnected("Dovoljenje je poteklo. Poveži Google Koledar znova.")
        try:
            result = requests.post(TOKEN_ENDPOINT, data={
                "client_id": self.client_id, "client_secret": self.client_secret,
                "refresh_token": refresh_token, "grant_type": "refresh_token",
            }, timeout=(3, 7))
        except requests.RequestException as error:
            raise CalendarError("Google povezave trenutno ni mogoče osvežiti.") from error
        if result.status_code == 400:
            try:
                if result.json().get("error") == "invalid_grant":
                    raise CalendarNotConnected("Google dovoljenje je preklicano ali poteklo. Poveži račun znova.")
            except ValueError:
                pass
        if not result.ok:
            raise CalendarError("Google povezave trenutno ni mogoče osvežiti.")
        try:
            payload = result.json()
            token = payload["access_token"]
        except (ValueError, KeyError) as error:
            raise CalendarError("Google ni vrnil novega dostopnega žetona.") from error
        self.repository.update_user_calendar_tokens(
            connection["user_id"], self._encrypt(token),
            self._encrypt(payload.get("refresh_token")), self.token_expiry(payload),
        )
        return token

    def _access_token(self, connection):
        if not connection or not connection.get("active"):
            raise CalendarNotConnected("Google Koledar člana ni povezan.")
        expiry = connection.get("token_expires_at")
        if expiry and expiry > datetime.now(timezone.utc) + timedelta(seconds=30):
            token = self._decrypt(connection.get("access_token_encrypted"))
            if token:
                return token
        return self._refresh(connection)

    def _request(self, method, path, *, connection, **kwargs):
        token = self._access_token(connection)
        for attempt in range(2):
            try:
                result = requests.request(method, f"{CALENDAR_API}{path}",
                                          headers={"Authorization": f"Bearer {token}"},
                                          timeout=(3, 7), **kwargs)
            except requests.RequestException as error:
                raise CalendarError("Google Koledar trenutno ni dosegljiv.") from error
            if result.status_code != 401 or attempt:
                return result
            token = self._refresh(connection)
        return result

    @staticmethod
    def google_event_id(user_id, event_id):
        digest = hashlib.sha256(f"choir-event:{user_id}:{event_id}".encode()).digest()[:15]
        return "choirevent" + base64.b32hexencode(digest).decode().lower().rstrip("=")

    @staticmethod
    def event_payload(event, google_event_id):
        start = event["event_date"]
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        return {
            "id": google_event_id, "summary": event["name"],
            "location": event.get("place") or "",
            "description": event.get("event_type") or "",
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": (start + timedelta(hours=2)).isoformat()},
            "extendedProperties": {"private": {"zborissimoEventId": str(event["id"])}}
        }

    def sync_event_for_user(self, event, user_id):
        connection = self.repository.get_user_calendar_connection(user_id)
        if not connection or not connection["active"]:
            raise CalendarNotConnected("Google Koledar člana ni povezan.")
        google_id = self.google_event_id(user_id, event["id"])
        link = self.repository.get_user_event_calendar_link(user_id, event["id"])
        path = "/calendars/primary/events"
        payload = self.event_payload(event, google_id)
        try:
            method = "PUT" if link and link.get("last_synced_at") else "POST"
            suffix = f"/{quote(google_id, safe='')}" if method == "PUT" else ""
            result = self._request(method, path + suffix, connection=connection, json=payload)
            if method == "PUT" and result.status_code == 404:
                result = self._request("POST", path, connection=connection, json=payload)
            elif method == "POST" and result.status_code == 409:
                result = self._request("PUT", path + f"/{quote(google_id, safe='')}", connection=connection, json=payload)
            if not result.ok:
                raise CalendarError(f"Google Koledar je vrnil napako ({result.status_code}).")
        except CalendarError as error:
            self.repository.record_user_event_calendar_sync(user_id, event["id"], google_id, str(error))
            raise
        self.repository.record_user_event_calendar_sync(user_id, event["id"], google_id)

    def sync_event(self, event):
        succeeded = failed = 0
        for connection in self.repository.list_user_calendar_connections():
            try:
                self.sync_event_for_user(event, connection["user_id"])
                succeeded += 1
            except CalendarError:
                failed += 1
        return succeeded, failed

    def delete_event(self, event_id):
        """Queue failed remote deletions so local event deletion can still succeed."""
        succeeded = failed = 0
        for link in self.repository.list_event_calendar_links(event_id):
            user_id, google_id = link["user_id"], link["google_event_id"]
            connection = self.repository.get_user_calendar_connection(user_id)
            try:
                if not connection or not connection["active"]:
                    raise CalendarNotConnected("Član mora znova povezati Google račun.")
                result = self._request("DELETE", f"/calendars/primary/events/{quote(google_id, safe='')}", connection=connection)
                if result.status_code not in {204, 404, 410}:
                    raise CalendarError(f"Google Koledar je vrnil napako ({result.status_code}).")
                succeeded += 1
            except CalendarError as error:
                self.repository.queue_user_calendar_deletion(user_id, google_id, str(error))
                failed += 1
        return succeeded, failed

    def sync_all(self, user_id):
        succeeded = failed = 0
        connection = self.repository.get_user_calendar_connection(user_id)
        if not connection or not connection["active"]:
            raise CalendarNotConnected("Google Koledar člana ni povezan.")
        for deletion in self.repository.list_user_calendar_pending_deletions(user_id):
            try:
                result = self._request("DELETE", f"/calendars/primary/events/{quote(deletion['google_event_id'], safe='')}", connection=connection)
                if result.status_code not in {204, 404, 410}:
                    raise CalendarError(f"Google Koledar je vrnil napako ({result.status_code}).")
                self.repository.clear_user_calendar_pending_deletion(user_id, deletion["google_event_id"])
                succeeded += 1
            except CalendarError:
                failed += 1
        for event in self.repository.list_events():
            try:
                self.sync_event_for_user(event, user_id)
                succeeded += 1
            except CalendarError:
                failed += 1
        return succeeded, failed

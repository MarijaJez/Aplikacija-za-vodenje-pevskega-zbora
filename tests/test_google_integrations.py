import re
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import bcrypt
from cryptography.fernet import Fernet

from Services.auth_service import AuthService
from Services.choir_service import ChoirService
from Services.google_calendar import CALENDAR_SCOPE, CalendarError, GoogleCalendarService
from Services.google_oauth import GoogleOAuthClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


class IdentityRepository:
    def __init__(self):
        self.calls = []

    def find_or_link_google_user(self, issuer, subject, email):
        self.calls.append((issuer, subject, email))
        return {"id": 7, "email": email}, None


class MemberRepository:
    def __init__(self):
        self.created = None

    def username_exists(self, _username):
        return False

    def create_member(self, values, username, password_hash, roles, must_change_password=False):
        self.created = (values, username, password_hash, roles, must_change_password)
        return 12


class CalendarRepository:
    def __init__(self):
        self.connection = {"user_id": 5, "active": True, "google_subject": "abc", "google_email": "member@example.si"}
        self.links = {}
        self.credentials = None
        self.pending = {}

    def get_user_by_id(self, user_id):
        return {"id": user_id, "email": "member@example.si"}

    def get_user_calendar_connection(self, user_id):
        return self.connection

    def list_user_calendar_connections(self):
        return [self.connection] if self.connection["active"] else []

    def get_user_event_calendar_link(self, user_id, event_id):
        return self.links.get((user_id, event_id))

    def record_user_event_calendar_sync(self, user_id, event_id, google_event_id, error=None):
        previous = self.links.get((user_id, event_id), {})
        self.links[(user_id, event_id)] = {
            "user_id": user_id, "event_id": event_id,
            "google_event_id": google_event_id, "last_error": error,
            "last_synced_at": 1 if error is None else previous.get("last_synced_at"),
        }

    def save_user_calendar_credentials(self, values):
        self.credentials = values

    def list_event_calendar_links(self, event_id):
        return [link for (user_id, linked_event), link in self.links.items() if linked_event == event_id]

    def queue_user_calendar_deletion(self, user_id, google_id, error):
        self.pending[(user_id, google_id)] = error

    def list_user_calendar_pending_deletions(self, user_id):
        return [{"google_event_id": google_id} for (member_id, google_id) in self.pending if member_id == user_id]

    def clear_user_calendar_pending_deletion(self, user_id, google_id):
        del self.pending[(user_id, google_id)]

    def list_events(self):
        return []


class GoogleIntegrationTests(unittest.TestCase):
    def test_google_identity_requires_verified_email(self):
        repository = IdentityRepository()
        service = AuthService(repository)
        user, reason = service.authenticate_google({
            "iss": "https://accounts.google.com", "sub": "abc",
            "email": "Member@Example.si", "email_verified": True,
        })
        self.assertEqual(user["id"], 7)
        self.assertIsNone(reason)
        self.assertEqual(repository.calls, [("https://accounts.google.com", "abc", "member@example.si")])

        user, reason = service.authenticate_google({
            "iss": "https://accounts.google.com", "sub": "abc",
            "email": "member@example.si", "email_verified": False,
        })
        self.assertIsNone(user)
        self.assertEqual(reason, "unverified_email")
        self.assertEqual(len(repository.calls), 1)

    def test_new_member_email_is_normalized_and_password_is_not_name_based(self):
        repository = MemberRepository()
        service = ChoirService(repository)
        _, username = service.create_member({
            "first_name": "Maja", "last_name": "Test",
            "email": "  MAJA.Test@Example.SI ", "voice": "Alt",
            "phone": "", "birth_date": "",
        }, [])
        values, _, password_hash, _, must_change = repository.created
        self.assertEqual(values["email"], "maja.test@example.si")
        self.assertEqual(username, "maja.test")
        self.assertFalse(must_change)
        self.assertFalse(bcrypt.checkpw(username.encode(), password_hash.encode()))

    @patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "client", "GOOGLE_CLIENT_SECRET": "secret"})
    def test_authorization_url_uses_state_nonce_and_pkce(self):
        client = GoogleOAuthClient()
        flow = client.new_flow_values()
        url = client.authorization_url("https://example.si/callback", ["openid", "email"], flow)
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["state"], [flow["state"]])
        self.assertEqual(query["nonce"], [flow["nonce"]])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertIn("openid", query["scope"][0])

    def test_calendar_retry_updates_same_google_event_instead_of_duplicating(self):
        repository = CalendarRepository()
        service = GoogleCalendarService(repository)
        service._request = Mock(return_value=FakeResponse(200))
        event = {
            "id": 42, "name": "Vaja", "place": "Dvorana",
            "event_type": "Redna vaja",
            "event_date": datetime(2026, 9, 27, 18, 0, tzinfo=timezone.utc),
        }

        service.sync_event(event)
        service.sync_event(event)

        first, second = service._request.call_args_list
        self.assertEqual(first.args[0], "POST")
        self.assertEqual(second.args[0], "PUT")
        google_id = repository.links[(5, 42)]["google_event_id"]
        self.assertRegex(google_id, r"^[0-9a-v]{5,1024}$")
        self.assertIn(google_id, second.args[1])
        self.assertIn("/calendars/primary/events", first.args[1])

    def test_calendar_tokens_are_encrypted_before_repository_storage(self):
        key = Fernet.generate_key().decode()
        repository = CalendarRepository()
        with patch.dict("os.environ", {
            "GOOGLE_CLIENT_ID": "client", "GOOGLE_CLIENT_SECRET": "secret",
            "GOOGLE_TOKEN_ENCRYPTION_KEY": key,
        }):
            service = GoogleCalendarService(repository)
            service.store_authorization({
                "access_token": "access-secret",
                "refresh_token": "refresh-secret",
                "scope": f"openid email {CALENDAR_SCOPE}",
                "expires_in": 3600,
            }, {"email": "member@example.si", "sub": "abc"}, 5)
        stored = repository.credentials
        self.assertNotIn("access-secret", stored["access_token_encrypted"])
        self.assertNotIn("refresh-secret", stored["refresh_token_encrypted"])
        cipher = Fernet(key.encode())
        self.assertEqual(cipher.decrypt(stored["refresh_token_encrypted"].encode()).decode(), "refresh-secret")

    def test_member_cannot_connect_another_google_account(self):
        key = Fernet.generate_key().decode()
        repository = CalendarRepository()
        with patch.dict("os.environ", {
            "GOOGLE_CLIENT_ID": "client", "GOOGLE_CLIENT_SECRET": "secret",
            "GOOGLE_TOKEN_ENCRYPTION_KEY": key,
        }):
            service = GoogleCalendarService(repository)
            with self.assertRaises(CalendarError):
                service.store_authorization({
                    "access_token": "access", "refresh_token": "refresh",
                    "scope": CALENDAR_SCOPE,
                }, {"email": "other@example.si", "sub": "other"}, 5)
        self.assertIsNone(repository.credentials)

    def test_calendar_retry_recreates_event_when_previous_create_never_arrived(self):
        repository = CalendarRepository()
        google_id = GoogleCalendarService.google_event_id(5, 9)
        repository.record_user_event_calendar_sync(5, 9, google_id, "temporary error")
        service = GoogleCalendarService(repository)
        service._request = Mock(side_effect=[FakeResponse(409), FakeResponse(200)])
        service.sync_event_for_user({
            "id": 9, "name": "Koncert", "place": "Dvorana",
            "event_type": "Koncert",
            "event_date": datetime(2026, 10, 2, 19, 0, tzinfo=timezone.utc),
        }, 5)
        self.assertEqual([call.args[0] for call in service._request.call_args_list], ["POST", "PUT"])
        self.assertIsNone(repository.links[(5, 9)]["last_error"])

    def test_failed_member_does_not_prevent_other_member_sync(self):
        repository = CalendarRepository()
        repository.list_user_calendar_connections = Mock(return_value=[{"user_id": 5}, {"user_id": 6}])
        service = GoogleCalendarService(repository)
        service.sync_event_for_user = Mock(side_effect=[CalendarError("revoked"), None])
        self.assertEqual(service.sync_event({"id": 10}), (1, 1))

    def test_failed_delete_is_queued_for_retry(self):
        repository = CalendarRepository()
        repository.record_user_event_calendar_sync(5, 9, GoogleCalendarService.google_event_id(5, 9))
        service = GoogleCalendarService(repository)
        service._request = Mock(return_value=FakeResponse(403))
        self.assertEqual(service.delete_event(9), (0, 1))
        self.assertEqual(len(repository.pending), 1)


if __name__ == "__main__":
    unittest.main()

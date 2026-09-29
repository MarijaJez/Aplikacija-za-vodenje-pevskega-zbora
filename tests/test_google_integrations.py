import re
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import bcrypt
from cryptography.fernet import Fernet

from Services.auth_service import AuthService
from Services.choir_service import ChoirService
from Services.google_calendar import GoogleCalendarService
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
        self.connection = {"active": True, "calendar_id": "choir@example.si"}
        self.links = {}
        self.credentials = None

    def get_calendar_connection(self):
        return self.connection

    def get_event_calendar_link(self, event_id):
        return self.links.get(event_id)

    def record_event_calendar_sync(self, event_id, calendar_id, google_event_id, error=None):
        self.links[event_id] = {
            "event_id": event_id, "calendar_id": calendar_id,
            "google_event_id": google_event_id, "last_error": error,
        }

    def save_calendar_credentials(self, values):
        self.credentials = values


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
        google_id = repository.links[42]["google_event_id"]
        self.assertRegex(google_id, r"^[0-9a-v]{5,1024}$")
        self.assertIn(google_id, second.args[1])

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
                "scope": "openid email https://www.googleapis.com/auth/calendar.calendarlist.readonly https://www.googleapis.com/auth/calendar.events",
                "expires_in": 3600,
            }, {"email": "choir@example.si"}, 5)
        stored = repository.credentials
        self.assertNotIn("access-secret", stored["access_token_encrypted"])
        self.assertNotIn("refresh-secret", stored["refresh_token_encrypted"])
        cipher = Fernet(key.encode())
        self.assertEqual(cipher.decrypt(stored["refresh_token_encrypted"].encode()).decode(), "refresh-secret")

    def test_calendar_retry_recreates_event_when_previous_create_never_arrived(self):
        repository = CalendarRepository()
        google_id = GoogleCalendarService.google_event_id(9)
        repository.record_event_calendar_sync(9, "choir@example.si", google_id, "temporary error")
        service = GoogleCalendarService(repository)
        service._request = Mock(side_effect=[FakeResponse(404), FakeResponse(200)])
        service.sync_event({
            "id": 9, "name": "Koncert", "place": "Dvorana",
            "event_type": "Koncert",
            "event_date": datetime(2026, 10, 2, 19, 0, tzinfo=timezone.utc),
        })
        self.assertEqual([call.args[0] for call in service._request.call_args_list], ["PUT", "POST"])
        self.assertIsNone(repository.links[9]["last_error"])


if __name__ == "__main__":
    unittest.main()

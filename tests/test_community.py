import hashlib
import hmac
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from bottle import Bottle
from PIL import Image

from Presentation.community import register_community_routes
from Services.community_service import CommunityValidationError, clean_text, normalize_photo


class DummyUpload:
    def __init__(self, data, content_type):
        self.file = io.BytesIO(data)
        self.content_type = content_type


class CommunityServiceTests(unittest.TestCase):
    def test_photo_is_decoded_resized_and_metadata_removed(self):
        image = Image.new("RGB", (2800, 1200), "red")
        exif = Image.Exif()
        exif[271] = "Private camera make"
        raw = io.BytesIO()
        image.save(raw, format="JPEG", exif=exif)
        result = normalize_photo(DummyUpload(raw.getvalue(), "image/jpeg"))
        with Image.open(io.BytesIO(result)) as clean:
            self.assertLessEqual(max(clean.size), 2400)
            self.assertEqual(clean.format, "JPEG")
            self.assertFalse(clean.getexif())

    def test_photo_mime_and_content_must_match(self):
        image = Image.new("RGB", (10, 10), "blue")
        raw = io.BytesIO()
        image.save(raw, format="PNG")
        with self.assertRaises(CommunityValidationError):
            normalize_photo(DummyUpload(raw.getvalue(), "image/jpeg"))
        with self.assertRaises(CommunityValidationError):
            normalize_photo(DummyUpload(b"<script>alert(1)</script>", "image/png"))

    def test_text_length_and_required(self):
        self.assertEqual(clean_text("  hej  ", 10, "Sporočilo", True), "hej")
        with self.assertRaises(CommunityValidationError):
            clean_text(" ", 10, "Sporočilo", True)
        with self.assertRaises(CommunityValidationError):
            clean_text("x" * 2001, 2000, "Sporočilo", True)


class FakeCommunityRepository:
    def __init__(self, database):
        self.sent = []
        self.edited = []
        self.deleted = []

    def add_message(self, user_id, body):
        self.sent.append((user_id, body))
        return len(self.sent)

    def edit_message(self, message_id, actor_id, body):
        self.edited.append((message_id, actor_id, body))
        return actor_id == 7

    def delete_message(self, message_id, actor_id, moderator=False):
        self.deleted.append((message_id, actor_id, moderator))
        return actor_id == 7 or moderator


class CommunityRouteTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeCommunityRepository(None)
        self.user = {"id": 7, "roles": ["Član"]}
        self.secret = "test-cookie-secret"
        self.notifications = []
        self.app = Bottle()
        with patch("Presentation.community.CommunityRepository", return_value=self.fake):
            with tempfile.TemporaryDirectory() as temp:
                register_community_routes(
                    self.app, None, lambda *args, **kwargs: "ok", lambda: self.user,
                    lambda fn: fn, lambda permission: (lambda fn: fn), Path(temp), self.secret,
                    on_message=lambda user_id: self.notifications.append(user_id),
                )

    def post(self, path, fields):
        body = urlencode(fields).encode()
        environment = {
            "REQUEST_METHOD": "POST", "PATH_INFO": path, "QUERY_STRING": "",
            "CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body), "wsgi.errors": io.StringIO(),
            "wsgi.url_scheme": "https", "SERVER_NAME": "example.org", "SERVER_PORT": "443",
            "SERVER_PROTOCOL": "HTTP/1.1", "SCRIPT_NAME": "", "wsgi.version": (1, 0),
            "wsgi.multithread": False, "wsgi.multiprocess": False, "wsgi.run_once": False,
        }
        status = []
        response = self.app(environment, lambda value, headers, exc_info=None: status.append(value))
        list(response)
        return status[0]

    def test_chat_post_requires_csrf_and_notifies_without_preview(self):
        self.assertTrue(self.post("/klepet", {"body": "Zasebno sporočilo"}).startswith("403"))
        self.assertEqual(self.fake.sent, [])
        token = hmac.new(self.secret.encode(), b"community:7", hashlib.sha256).hexdigest()
        self.assertTrue(self.post("/klepet", {"csrf": token, "body": " Pozdrav! "}).startswith("303"))
        self.assertEqual(self.fake.sent, [(7, "Pozdrav!")])
        self.assertEqual(self.notifications, [7])

    def test_chat_mutations_reject_bad_token_and_allow_moderation(self):
        token = hmac.new(self.secret.encode(), b"community:7", hashlib.sha256).hexdigest()
        self.assertTrue(self.post("/klepet/12/uredi", {"body": "Novo"}).startswith("403"))
        self.assertEqual(self.fake.edited, [])
        self.assertTrue(self.post("/klepet/12/uredi", {"csrf": token, "body": "Novo"}).startswith("303"))
        self.assertEqual(self.fake.edited, [(12, 7, "Novo")])
        self.user = {"id": 8, "roles": ["Predsednik"]}
        admin_token = hmac.new(self.secret.encode(), b"community:8", hashlib.sha256).hexdigest()
        self.assertTrue(self.post("/klepet/12/izbrisi", {"csrf": admin_token}).startswith("303"))
        self.assertEqual(self.fake.deleted, [(12, 8, True)])


if __name__ == "__main__":
    unittest.main()

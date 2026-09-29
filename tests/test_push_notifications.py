import base64
import json
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from Services.push_notifications import PushNotificationService, _valid_endpoint, _valid_key


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchall(self):
        return self.rows


class FakeDatabase:
    def __init__(self, rows):
        self.cursor_value = FakeCursor(rows)

    @contextmanager
    def cursor(self):
        yield self.cursor_value


class PushTests(unittest.TestCase):
    def test_subscription_rejects_private_endpoint_and_invalid_keys(self):
        self.assertTrue(_valid_endpoint('https://fcm.googleapis.com/fcm/send/abc'))
        self.assertFalse(_valid_endpoint('http://127.0.0.1/internal'))
        self.assertFalse(_valid_endpoint('https://fcm.googleapis.com:bad/fcm/send/abc'))
        self.assertFalse(_valid_endpoint('https://fcm.googleapis.com.evil.test/abc'))
        key = base64.urlsafe_b64encode(bytes(65)).decode().rstrip('=')
        self.assertTrue(_valid_key(key, 65))
        self.assertFalse(_valid_key(key + '!', 65))

    def test_notification_excludes_sender_and_sends_local_link(self):
        endpoint = 'https://fcm.googleapis.com/fcm/send/test'
        db = FakeDatabase([{'endpoint': endpoint, 'p256dh': 'public', 'auth': 'secret'}])
        service = PushNotificationService(type('Repo', (), {'db': db})())
        service.public_key = 'public'
        service.private_key_file = __file__
        with patch('Services.push_notifications.webpush') as sender:
            service._deliver(json.dumps({'title': 'Novo sporočilo', 'body': 'Živjo', 'url': '/klepet'}), 7)
        self.assertEqual(db.cursor_value.queries[0][1], (7, 7, None, None))
        self.assertEqual(sender.call_args.kwargs['subscription_info']['endpoint'], endpoint)
        self.assertEqual(json.loads(sender.call_args.kwargs['data'])['url'], '/klepet')
        with self.assertRaises(ValueError):
            service.notify('x', 'y', 'https://example.com')


if __name__ == '__main__':
    unittest.main()

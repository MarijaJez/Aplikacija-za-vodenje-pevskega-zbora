"""Run with NOTIFICATION_TEST_DSN against a local PostgreSQL database.
Only connection-local temporary tables are touched; Web Push is always mocked.
"""
import io
import json
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import psycopg2
from psycopg2.extras import RealDictCursor
from bottle import Bottle, HTTPError
from Services.push_notifications import PushNotificationService


@unittest.skipUnless(os.getenv("NOTIFICATION_TEST_DSN"), "Local PostgreSQL DSN required")
class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.connection = psycopg2.connect(os.environ["NOTIFICATION_TEST_DSN"])
        self.addCleanup(self.connection.close)
        with self.connection.cursor() as cur:
            cur.execute("CREATE TEMP TABLE users(id BIGINT PRIMARY KEY,person_id BIGINT)")
            cur.execute("INSERT INTO users(id) VALUES(1),(2),(3)")
            migration = (Path(__file__).resolve().parents[1] / "Data/migrations/007_notification_preferences.sql").read_text()
            cur.execute(migration.replace("CREATE TABLE IF NOT EXISTS", "CREATE TEMP TABLE"))
            cur.execute("CREATE TEMP TABLE events(id BIGINT PRIMARY KEY,event_date TIMESTAMPTZ)")
            cur.execute("CREATE TEMP TABLE attendance(event_id BIGINT,person_id BIGINT,status TEXT)")
            cur.execute("CREATE TEMP TABLE push_subscriptions(endpoint TEXT PRIMARY KEY,user_id BIGINT,p256dh TEXT,auth TEXT)")
            cur.execute("INSERT INTO push_subscriptions VALUES ('https://fcm.googleapis.com/1',1,'k','a'),('https://fcm.googleapis.com/2',2,'k','a'),('https://fcm.googleapis.com/3',2,'k','a'),('https://fcm.googleapis.com/4',3,'k','a')")
        self.connection.commit()
        outer = self
        class Database:
            @contextmanager
            def cursor(self):
                with outer.connection:
                    with outer.connection.cursor(cursor_factory=RealDictCursor) as cur:
                        yield cur
        self.db = Database()
        self.service = PushNotificationService(type('Repo', (), {'db': self.db})())
        self.sender = patch('Services.push_notifications.webpush').start()
        self.addCleanup(patch.stopall)
        self.app = Bottle()
        self.user = {'id': 2}
        def login(callback):
            def wrapped():
                if self.user is None:
                    raise HTTPError(401)
                return callback()
            return wrapped
        self.service.register_routes(self.app, lambda: self.user, login, 'https://choir.test')

    def api(self, method='GET', data=None, origin='https://choir.test'):
        raw = json.dumps(data).encode() if data is not None else b''
        environ = {'REQUEST_METHOD': method, 'PATH_INFO': '/api/push/preferences',
            'SERVER_NAME': 'choir.test', 'SERVER_PORT': '443', 'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.url_scheme': 'https', 'wsgi.input': io.BytesIO(raw), 'wsgi.errors': io.StringIO(),
            'CONTENT_TYPE': 'application/json', 'CONTENT_LENGTH': str(len(raw)), 'HTTP_ORIGIN': origin}
        status = []
        body = b''.join(self.app(environ, lambda code, headers, exc_info=None: status.append(code)))
        return int(status[0][:3]), body

    def sql(self, query, args=None):
        with self.db.cursor() as cur:
            cur.execute(query, args)

    def deliver(self, category, exclude=1):
        self.sender.reset_mock()
        self.service._deliver('{}', exclude_user_id=exclude, category=category)
        return {call.kwargs['subscription_info']['endpoint'] for call in self.sender.call_args_list}

    def test_identity_validation_and_persistence(self):
        self.assertEqual(json.loads(self.api()[1]), dict(events_enabled=True, chat_mode='limited', chat_interval_minutes=30))
        data = dict(events_enabled=False, chat_mode='off', chat_interval_minutes=60, user_id=3)
        self.assertEqual(self.api('POST', data)[0], 200)
        self.assertFalse(json.loads(self.api()[1])['events_enabled'])
        self.user = {'id': 3}
        self.assertTrue(json.loads(self.api()[1])['events_enabled'])
        for invalid in ([], {}, dict(data, events_enabled='false'), dict(data, chat_mode='invalid'), dict(data, chat_interval_minutes=True), dict(data, chat_interval_minutes=31)):
            self.assertEqual(self.api('POST', invalid)[0], 400)
        self.assertEqual(self.api('POST', data, 'https://evil.test')[0], 403)
        self.user = None
        self.assertEqual(self.api()[0], 401)
        self.assertEqual(self.api('POST', data)[0], 401)

    def test_independent_filters_cooldown_and_multiple_devices(self):
        self.assertEqual(len(self.deliver('chat')), 3)
        self.assertEqual(self.deliver('chat'), set())
        self.assertEqual(len(self.deliver('event')), 3)
        self.sql("UPDATE notification_preferences SET events_enabled=false,chat_mode='all' WHERE user_id=2")
        self.sql("UPDATE notification_preferences SET chat_mode='off' WHERE user_id=3")
        self.assertEqual(len(self.deliver('chat')), 2)
        self.assertEqual(len(self.deliver('chat')), 2)
        self.assertEqual(self.deliver('event'), {'https://fcm.googleapis.com/4'})
        self.sql("UPDATE notification_preferences SET chat_mode='limited',chat_interval_minutes=60,last_chat_notification_at=NOW()-INTERVAL '31 minutes' WHERE user_id=2")
        self.assertEqual(self.deliver('chat'), set())
        self.sql("UPDATE notification_preferences SET last_chat_notification_at=NOW()-INTERVAL '61 minutes' WHERE user_id=2")
        self.assertEqual(len(self.deliver('chat')), 2)
        self.assertEqual(self.deliver('chat'), set())
        # Targeted manual test remains available regardless of category preferences.
        self.sender.reset_mock()
        self.service._deliver('{}', recipient_user_id=3)
        self.assertEqual(self.sender.call_count, 1)

    def test_daily_reminders_preferences_and_durable_claim(self):
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 10, 25, 7, tzinfo=timezone.utc)
        self.sql("CREATE TEMP TABLE event_reminder_deliveries(event_id BIGINT,local_date DATE,endpoint TEXT,PRIMARY KEY(event_id,local_date,endpoint))")
        self.sql("INSERT INTO events VALUES(5,%s)", (now + timedelta(minutes=20),))
        self.sql("INSERT INTO notification_preferences(user_id,events_enabled) VALUES(3,false)")
        payload = json.dumps(dict(event_id=5, title='Reminder', body='Event', url='/dogodki/5'))
        self.sender.reset_mock()
        for _ in range(2):
            worker = PushNotificationService(type('Repo', (), {'db': self.db})())
            worker._deliver(payload, category='event', reminder_date=now.date(), now=now)
        self.assertEqual(self.sender.call_count, 3)
        self.assertTrue(all(call.kwargs['ttl'] == 1200 for call in self.sender.call_args_list))
        self.assertTrue(all(len(json.loads(call.kwargs['data'])['actions']) == 2 for call in self.sender.call_args_list))
        with self.db.cursor() as cur:
            cur.execute("SELECT COUNT(*) count FROM event_reminder_deliveries")
            self.assertEqual(cur.fetchone()['count'], 3)

    def test_concurrent_workers_claim_only_once(self):
        schema = 'notification_test_' + uuid.uuid4().hex
        self.sql('CREATE SCHEMA ' + schema)
        try:
            self.sql('CREATE TABLE ' + schema + '.notification_preferences (LIKE notification_preferences INCLUDING ALL)')
            self.sql('CREATE TABLE ' + schema + '.push_subscriptions (LIKE push_subscriptions INCLUDING ALL)')
            self.sql('CREATE TABLE ' + schema + '.users (LIKE users INCLUDING ALL)')
            self.sql('INSERT INTO ' + schema + '.users SELECT * FROM users')
            self.sql('CREATE TABLE ' + schema + '.events (LIKE events INCLUDING ALL)')
            self.sql('CREATE TABLE ' + schema + '.attendance (LIKE attendance INCLUDING ALL)')
            self.sql('INSERT INTO ' + schema + '.notification_preferences(user_id) VALUES(2)')
            self.sql('INSERT INTO ' + schema + '.push_subscriptions SELECT * FROM push_subscriptions WHERE user_id=2')
            barrier = Barrier(2)
            class ConcurrentDatabase:
                @contextmanager
                def cursor(inner):
                    conn = psycopg2.connect(os.environ['NOTIFICATION_TEST_DSN'])
                    try:
                        with conn:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                cur.execute('SET search_path TO ' + schema)
                                barrier.wait(timeout=10)
                                yield cur
                    finally:
                        conn.close()
            service = PushNotificationService(type('Repo', (), {'db': ConcurrentDatabase()})())
            self.sender.reset_mock()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(service._deliver, '{}', category='chat') for _ in range(2)]
                for future in futures:
                    future.result(timeout=15)
            self.assertEqual(self.sender.call_count, 2)  # One claim, both devices.
        finally:
            self.sql('DROP SCHEMA ' + schema + ' CASCADE')

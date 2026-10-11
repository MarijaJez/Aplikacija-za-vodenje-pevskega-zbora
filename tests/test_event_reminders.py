import json
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch
from Services.event_reminders import run_reminders, ZONE
from Services.push_notifications import PushNotificationService


class Database:
    def __init__(self, events=(), subscriptions=()):
        self.events = events
        self.subscriptions = subscriptions
        self.claims = set()
        self.result = None

    @contextmanager
    def cursor(self):
        yield self

    def execute(self, sql, params=None):
        if "SELECT id,name" in sql:
            self.rows = [e for e in self.events if params[0] < e['event_date'] < params[1]]
        elif "WITH eligible" in sql:
            self.rows = self.subscriptions
        elif "INSERT INTO event_reminder" in sql:
            self.result = None if params in self.claims else {'event_id': params[0]}
            self.claims.add(params)
        elif "INSERT INTO notification_preferences" in sql:
            pass
        else:
            raise AssertionError(sql)

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.result


class ReminderTests(unittest.TestCase):
    def test_morning_boundary_future_only_and_dst(self):
        for day, offset in [('2026-03-29', 2), ('2026-10-25', 1), ('2026-07-01', 2)]:
            now = datetime.fromisoformat(day + 'T08:00').replace(tzinfo=ZONE)
            self.assertEqual(now.utcoffset(), timedelta(hours=offset))
            events = [dict(id=i, name='Vaja', event_date=now + timedelta(hours=h))
                      for i, h in enumerate([-1, 0, 1, 15, 16, 25])]
            repo = SimpleNamespace(db=Database(events))
            push = Mock(configured=True)
            self.assertEqual(run_reminders(repo, push, now-timedelta(seconds=1)), 0)
            self.assertEqual(run_reminders(repo, push, now.astimezone(timezone.utc)), 2)
            self.assertEqual(push._deliver.call_count, 2)
            payload = json.loads(push._deliver.call_args_list[0].args[0])
            self.assertEqual(payload['url'], '/dogodki/2')
            self.assertIn('09:00', payload['body'])
            self.assertEqual(push._deliver.call_args.kwargs['category'], 'event')
            push.reset_mock()
            self.assertEqual(run_reminders(repo, push, now, dry_run=True), 2)
            push._deliver.assert_not_called()

    def test_restart_multiple_workers_and_attendance(self):
        now = datetime(2026, 10, 25, 8, tzinfo=ZONE)
        subs = [dict(endpoint=f'https://fcm.googleapis.com/{i}', p256dh='key', auth='key',
                     event_date=now+timedelta(hours=1), attendance_status=status)
                for i, status in enumerate([None, 'present', 'absent'])]
        db = Database(subscriptions=subs)
        repo = SimpleNamespace(db=db)
        payload = json.dumps(dict(event_id=5, title='Opomnik', body='Vaja', url='/dogodki/5'))
        with patch('Services.push_notifications.webpush') as send:
            for _ in range(2):
                service = PushNotificationService(repo)
                service._deliver(payload, reminder_date=now.date(), now=now)
            self.assertEqual(send.call_count, 3)
            self.assertEqual(len(json.loads(send.call_args_list[0].kwargs['data'])['actions']), 2)
            self.assertNotIn('actions', json.loads(send.call_args_list[1].kwargs['data']))
            self.assertEqual(len(db.claims), 3)
            service._deliver(payload, reminder_date=now.date(), now=now+timedelta(hours=1))
            self.assertEqual(send.call_count, 3)

    def test_unconfigured_fails_without_claims(self):
        with self.assertRaises(RuntimeError):
            run_reminders(SimpleNamespace(db=Database()), Mock(configured=False),
                          datetime(2026, 10, 11, 8, tzinfo=ZONE))


if __name__ == '__main__':
    unittest.main()

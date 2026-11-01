import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from Services.choir_service import ChoirService
from Services.google_calendar import GoogleCalendarService


class EventTimeTests(unittest.TestCase):
    def test_validation(self):
        for end in ('2026-12-01T17:00', '2026-12-01T18:00', '', None):
            with self.subTest(end=end), self.assertRaises(ValueError):
                ChoirService.validate_event({'event_date': '2026-12-01T18:00', 'event_end': end})
        ChoirService.validate_event({'event_date': '2026-12-01T18:00', 'event_end': '2026-12-02T01:00'})

    def test_display_and_calendar_use_actual_end(self):
        start = datetime(2026, 12, 1, 18, tzinfo=timezone.utc)
        end = datetime(2026, 12, 2, 1, tzinfo=timezone.utc)
        event = dict(id=1, event_date=start, event_end=end, name='Vaja')
        self.assertEqual(ChoirService.event_time(event), '18:00–02. 12. 2026 01:00')
        self.assertEqual(GoogleCalendarService.event_payload(event, 'test')['end']['dateTime'], end.isoformat())
        event['event_end'] = None
        self.assertEqual(ChoirService.event_time(event), '18:00')
        self.assertEqual(GoogleCalendarService.event_payload(event, 'test')['end']['dateTime'], '2026-12-01T20:00:00+00:00')

    def test_ongoing_events_stay_before_future_and_past_on_all_lists(self):
        now = datetime.now(timezone.utc)
        rows = [dict(id=i, event_date=now+timedelta(hours=start),
                     event_end=now+timedelta(hours=end), name='Vaja', event_type='Vaja')
                for i, start, end in [(1,-3,1), (2,2,3), (3,-5,-1), (4,-7,-4)]]
        repo = Mock()
        repo.list_events.return_value = rows
        repo.get_event.return_value = rows[0]
        repo.list_members.return_value = []
        repo.list_attendance.return_value = []
        service = ChoirService(repo)
        events = service.events()
        self.assertEqual([e['id'] for e in events], [1,2,3,4])
        self.assertEqual([e['status'] for e in events], ['upcoming','upcoming','past','past'])
        self.assertEqual(service.event(1)['status'], 'upcoming')
        self.assertEqual([e['id'] for e in service.attendance(service.school_year_start(now))['events']], [1,2,3,4])
        self.assertFalse(service.event_is_past(rows[0], rows[0]['event_end']))
        self.assertTrue(service.event_is_past(rows[0], rows[0]['event_end']+timedelta(seconds=1)))

    def test_legacy_events_use_two_hour_duration(self):
        now = datetime.now(timezone.utc)
        self.assertFalse(ChoirService.event_is_past(dict(event_date=now-timedelta(hours=1), event_end=None), now))
        self.assertTrue(ChoirService.event_is_past(dict(event_date=now-timedelta(hours=3)), now))

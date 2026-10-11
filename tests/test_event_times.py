import unittest
from datetime import datetime, timezone
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

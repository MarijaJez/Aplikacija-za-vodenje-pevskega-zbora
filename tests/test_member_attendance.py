import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock
from bottle import template
from Services.choir_service import ChoirService


class MemberAttendanceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.repo = Mock()
        self.repo.get_member.return_value = dict(id=7, first_name='Ana', last_name='Novak', birth_date=None, attendance=None, voice='Alt', email='', phone='', roles=[])
        self.rows = [dict(id=i, name=f'Dogodek {i}', event_type='Vaja', event_date=self.now+timedelta(days=days), status='unentered') for i, days in [(1,-20),(2,20),(3,-1),(4,1)]]
        self.repo.member_attendance.return_value = self.rows
        self.service = ChoirService(self.repo)

    def test_member_and_event_list_have_identical_order(self):
        self.repo.list_events.return_value = self.rows
        member = self.service.member(7)
        self.assertEqual([row['id'] for row in member['attendance_rows']], [4,2,3,1])
        self.assertEqual([row['id'] for row in member['attendance_rows']], [row['id'] for row in self.service.events()])
        self.assertTrue(all(row['status'] == 'unentered' for row in member['attendance_rows']))

    def test_controls_only_for_editable_rows(self):
        member = self.service.member(7)
        html = template('member_detail', template_lookup=[str(Path(__file__).resolve().parents[1]/'Presentation'/'views')], member=member, current_user=dict(person_id=7), permissions=set(), roles=[], avatar=lambda *args: 'AN', avatar_csrf='test', can_edit_attendance=lambda user, person, event: event['event_date'] > self.now)
        self.assertEqual(html.count('<select data-member-attendance'), 2)
        self.assertIn('data-event-id="4"', html)
        self.assertNotIn('data-event-id="3"', html)
        self.assertIn('value="unentered" selected disabled', html)
        self.assertLess(html.index('Dogodek 4'), html.index('Dogodek 2'))

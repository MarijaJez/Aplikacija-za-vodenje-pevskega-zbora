import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch
from bottle import template
import os
with patch.dict(os.environ, {"COOKIE_SECRET": "dashboard-unit-test-secret"}), patch("Data.repository.Database"):
    from Presentation.app import permission_set
from Services.choir_service import ChoirService

class DashboardTests(unittest.TestCase):
    def test_personal_data_roles_and_empty_calendar(self):
        repository = Mock()
        service = ChoirService(repository)
        member = dict(id=7, first_name='Eva', last_name='Novak', name='Eva Novak', initials='EN', voice='Alt', attendance=82)
        service.members = Mock(return_value=[member])
        service.member = Mock(return_value=member)
        service.songs = Mock(return_value=[])
        service.events = Mock(return_value=[])
        service.event = Mock()
        service.treasury = Mock(return_value=dict(transactions=[], income=10, expenses=3, balance=7, unsettled=2))
        views = str(Path(__file__).resolve().parents[1] / 'Presentation' / 'views')
        for roles in ([], ['Predsednik'], ['Zborovodja'], ['Notar'], ['Blagajnik'], ['Beleženje prisotnosti'], ['Notar', 'Blagajnik']):
            with self.subTest(roles=roles):
                user = dict(id=2, person_id=7, first_name='Eva', last_name='Novak', roles=roles)
                data = service.dashboard(user)
                service.member.assert_called_with(7)
                self.assertEqual(data['personal_member']['attendance'], 82)
                self.assertIsNone(data['next_event'])
                self.assertEqual(data['treasury'] is not None, 'Blagajnik' in roles)
                html = template('dashboard.tpl', template_lookup=[views], current_user=user, permissions=permission_set(user), data=data)
                self.assertIn('82%', html)
                self.assertIn('Trenutno ni napovedane', html)
                self.assertEqual('Upravljanje zbora</h3>' in html, bool(set(roles) & {'Predsednik', 'Zborovodja'}))
                self.assertEqual('Moja blagajna</h3>' in html, 'Blagajnik' in roles)
        service.treasury.assert_called()
        service.event.assert_not_called()
        upcoming = dict(id=9, event_date=datetime(2030, 1, 1, tzinfo=timezone.utc), status='upcoming', title='Naslednja vaja', date='1. jan. 2030', time='18:00', place='Dvorana', kind='Vaja', program=[dict(id=3, title='Pesem za vajo', author='Avtor')])
        service.events.return_value = [upcoming]
        service.event.return_value = upcoming
        data = service.dashboard(user)
        html = template('dashboard.tpl', template_lookup=[views], current_user=user, permissions=permission_set(user), data=data)
        self.assertIn('/program/3', html)
        self.assertIn('Pesem za vajo', html)
        service.event.assert_called_once_with(9)

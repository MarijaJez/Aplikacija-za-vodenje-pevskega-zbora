import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from bottle import template

with patch.dict(os.environ, {'COOKIE_SECRET': 'treasury-access-test'}), patch('Data.repository.Database'):
    import Presentation.app as web


class TreasuryAccessTests(unittest.TestCase):
    def test_navigation_and_direct_access_follow_treasury_permission(self):
        views = str(Path(__file__).resolve().parents[1] / 'Presentation' / 'views')
        for role, allowed in [('Član', False), ('Notar', False), ('Beleženje prisotnosti', False), ('Blagajnik', True), ('Predsednik', True), ('Zborovodja', True)]:
            with self.subTest(role=role):
                user = dict(id=1, person_id=1, first_name='Eva', last_name='Novak', email='eva@example.com', roles=[role], must_change_password=False)
                html = template('layout', template_lookup=[views], permissions=web.permission_set(user), current_user=user, active='roles', title='Vloge', view='roles', roles=[], avatar=web.avatar, message='', avatar_csrf='test', auth_method='google')
                self.assertEqual('href="/blagajna"' in html, allowed)
                env = {'REQUEST_METHOD':'GET', 'PATH_INFO':'/blagajna', 'SERVER_NAME':'localhost', 'SERVER_PORT':'80', 'SERVER_PROTOCOL':'HTTP/1.1', 'wsgi.url_scheme':'http', 'wsgi.input':io.BytesIO(), 'wsgi.errors':io.StringIO()}
                statuses = []
                with patch.object(web, 'current_user', return_value=user), patch.object(web, 'service') as service, patch.object(web, 'render', return_value='treasury'):
                    b''.join(web.app(env, lambda status, headers, exc_info=None: statuses.append(status)))
                    self.assertTrue(statuses[0].startswith('200' if allowed else '403'))
                    self.assertEqual(service.treasury.called, allowed)

import io
import os
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

with patch.dict(os.environ, {'COOKIE_SECRET': 'role-test-only'}), patch('Data.repository.Database'):
    import Presentation.app as web


class MemberRoleTests(unittest.TestCase):
    def test_unicode_roles_reach_repository_on_create_and_update(self):
        roles = ['\u010clan', 'Bele\u017eenje prisotnosti', 'Zborovodja']
        for path in ['/clani', '/clani/7/uredi']:
            with self.subTest(path=path):
                body = urlencode([('first_name', 'Ana'), ('last_name', 'Novak'),
                                  ('email', 'ana@example.com'), ('voice', 'Alt')]
                                 + [('roles', role) for role in roles]).encode()
                env = {'REQUEST_METHOD': 'POST', 'PATH_INFO': path, 'SERVER_NAME': 'localhost',
                       'SERVER_PORT': '80', 'SERVER_PROTOCOL': 'HTTP/1.1', 'wsgi.url_scheme': 'http',
                       'wsgi.input': io.BytesIO(body), 'wsgi.errors': io.StringIO(),
                       'CONTENT_TYPE': 'application/x-www-form-urlencoded', 'CONTENT_LENGTH': str(len(body))}
                result = {}
                def start(status, headers, exc_info=None):
                    result['status'] = int(status.split()[0])
                with patch.object(web, 'current_user', return_value=dict(id=1, person_id=1, roles=['Predsednik'], must_change_password=False)), patch.object(web, 'repository') as repo, patch.object(web, 'service') as service:
                    repo.get_member.return_value = {'email': 'ana@example.com'}
                    service.create_member.return_value = (7, 'ana.novak')
                    b''.join(web.app(env, start))
                    self.assertEqual(result['status'], 303)
                    saved = service.create_member.call_args.args[1] if path == '/clani' else repo.set_member_roles.call_args.args[1]
                    self.assertEqual(saved, roles)

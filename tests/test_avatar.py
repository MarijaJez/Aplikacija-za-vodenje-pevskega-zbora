import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import requests
from PIL import Image
with patch.dict(os.environ, {'COOKIE_SECRET': 'avatar-test-secret'}), patch('Data.repository.Database'):
    from Presentation import app as module

class AvatarTests(unittest.TestCase):
    def post(self, fields, data=None):
        files = {'avatar': ('picture.png', data, 'image/png')} if data is not None else None
        prepared = requests.Request('POST', 'https://example.org/profil/slika', data=fields, files=files).prepare()
        body = prepared.body
        if isinstance(body, str): body = body.encode()
        env = dict(REQUEST_METHOD='POST', PATH_INFO='/profil/slika', QUERY_STRING='', CONTENT_TYPE=prepared.headers['Content-Type'], CONTENT_LENGTH=str(len(body)), SERVER_NAME='example.org', SERVER_PORT='443', SERVER_PROTOCOL='HTTP/1.1', SCRIPT_NAME='')
        env.update({'wsgi.input': io.BytesIO(body), 'wsgi.errors': io.StringIO(), 'wsgi.url_scheme': 'https', 'wsgi.version': (1,0), 'wsgi.multithread': False, 'wsgi.multiprocess': False, 'wsgi.run_once': False})
        statuses=[]
        list(module.app(env, lambda status, headers, exc_info=None: statuses.append(status)))
        return statuses[0]

    def test_upload_replace_remove_and_invalid_image(self):
        user = dict(id=7, person_id=3, must_change_password=False)
        repository=Mock()
        repository.set_own_avatar.return_value=None
        image=io.BytesIO(); Image.new('RGB',(800,600),'red').save(image, format='PNG')
        token=module.avatar_token(user)
        with tempfile.TemporaryDirectory() as temp, patch.object(module,'UPLOADS',Path(temp)), patch.object(module,'current_user',return_value=user), patch.object(module,'repository',repository):
            self.assertTrue(self.post({'csrf': 'wrong'},image.getvalue()).startswith('403'))
            repository.set_own_avatar.assert_not_called()
            self.assertTrue(self.post({'csrf':token},image.getvalue()).startswith('303'))
            filename=repository.set_own_avatar.call_args.args[1]
            with Image.open(Path(temp)/'avatars'/filename) as clean:
                self.assertEqual(clean.format,'JPEG'); self.assertLessEqual(max(clean.size),512)
            repository.set_own_avatar.return_value=filename
            self.assertTrue(self.post({'csrf':token},b'not an image').startswith('303'))
            self.assertTrue((Path(temp)/'avatars'/filename).exists())
            self.assertTrue(self.post({'csrf':token},image.getvalue()).startswith('303'))
            replacement=repository.set_own_avatar.call_args.args[1]
            self.assertFalse((Path(temp)/'avatars'/filename).exists())
            repository.set_own_avatar.return_value=replacement
            self.assertTrue(self.post({'csrf':token,'remove':'1','person_id':'999'}).startswith('303'))
            repository.set_own_avatar.assert_called_with(7,None)
            self.assertFalse((Path(temp)/'avatars'/replacement).exists())

    def test_size_limit_and_fallback(self):
        from Services.community_service import normalize_photo, CommunityValidationError
        upload=Mock(file=io.BytesIO(b'x'*(8*1024*1024+1)),content_type='image/png')
        with self.assertRaises(CommunityValidationError): normalize_photo(upload,512)
        self.assertEqual(module.avatar(dict(first_name='Eva',last_name='Novak')),'EN')
        self.assertNotIn('<script>',module.avatar({},'<script>'))

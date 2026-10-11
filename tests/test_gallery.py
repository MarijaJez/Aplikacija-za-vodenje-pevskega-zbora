import io
import os
import re
import unittest

import requests
from PIL import Image


@unittest.skipUnless(os.getenv('GALLERY_TEST_BASE'), 'Requires isolated gallery test server')
class GalleryIntegrationTests(unittest.TestCase):
    def test_standalone_and_event_albums_permissions_and_persistence(self):
        from Data.database import Database
        from Data.community_repository import CommunityRepository
        base = os.environ['GALLERY_TEST_BASE']
        db = Database()
        store = CommunityRepository(db)
        admin = requests.Session()
        admin.post(base + '/prijava', data={'username': 'luka.mlakar', 'password': 'zbor2026'})
        page = admin.get(base + '/galerija')
        self.assertEqual(page.status_code, 200)
        token = re.search(r'name="csrf" value="([^"]+)"', page.text)[1]
        self.assertEqual(admin.post(base + '/galerija/albumi/dodaj', data={'name': 'test'}).status_code, 403)
        self.assertEqual(admin.post(base + '/galerija/albumi/dodaj', data={'csrf': token, 'name': ' '}).status_code, 400)
        created = admin.post(base + '/galerija/albumi/dodaj', data={'csrf': token, 'name': 'Samostojni utrinki'})
        self.assertEqual(created.status_code, 200)
        self.assertIn('Samostojni album', created.text)
        self.assertNotIn('Odpri dogodek', created.text)
        album_id = int(re.search(r'/albumi/(\d+)', created.url)[1])
        try:
            member = requests.Session()
            member.post(base + '/prijava', data={'username': 'ana.kovac', 'password': 'zbor2026'})
            self.assertEqual(member.post(base + '/galerija/albumi/dodaj', data={'csrf': token, 'name': 'Denied'}).status_code, 403)
            self.assertNotIn('Dodaj fotografijo', member.get(created.url).text)
            self.assertEqual(member.post(base + f'/galerija/albumi/{album_id}/dodaj').status_code, 403)
            self.assertNotEqual(requests.get(created.url, allow_redirects=False).status_code, 200)
            raw = io.BytesIO()
            Image.new('RGB', (12, 12), 'blue').save(raw, format='PNG')
            event_id = store.gallery_events()[0]['id']
            for path, standalone, target_id in [(f'albumi/{album_id}', True, album_id), (str(event_id), False, event_id)]:
                upload = admin.post(base + f'/galerija/{path}/dodaj', data={'csrf': token, 'alt_text': 'Testna slika'}, files={'photo': ('test.png', raw.getvalue(), 'image/png')})
                self.assertEqual(upload.status_code, 200, upload.text)
                photos = CommunityRepository(Database()).photos(target_id, standalone=standalone)
                photo = next(p for p in photos if p['alt_text'] == 'Testna slika')
                self.assertEqual(admin.get(base + f'/galerija/slika/{photo["id"]}').status_code, 200)
                self.assertEqual(member.post(base + f'/galerija/slika/{photo["id"]}/izbrisi', data={'csrf': token}).status_code, 403)
                deleted = admin.post(base + f'/galerija/slika/{photo["id"]}/izbrisi', data={'csrf': token})
                self.assertIn('/galerija/' + path, deleted.url)
                self.assertIsNone(store.photo(photo['id']))
            self.assertEqual(admin.get(base + '/galerija/albumi/999999').status_code, 404)
        finally:
            with db.cursor() as cur:
                cur.execute('DELETE FROM gallery_albums WHERE id=%s', (album_id,))

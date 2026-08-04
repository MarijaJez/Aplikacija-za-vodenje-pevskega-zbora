import re
import unittest
import uuid

import requests

from Data.database import Database


BASE = "http://127.0.0.1:8091"


class BackendSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()
        response = cls.session.post(f"{BASE}/prijava", data={"username": "luka.mlakar", "password": "zbor2026"})
        if response.url != f"{BASE}/":
            raise RuntimeError("Testni predsedniški račun se ni prijavil.")
        cls.db = Database()

    def test_all_pages_and_internal_links(self):
        queue = ["/", "/clani", "/vloge", "/program", "/dogodki", "/prisotnost", "/blagajna"]
        visited = set()
        while queue:
            path = queue.pop(0)
            if path in visited or path == "/odjava" or path.startswith("/uploads/"):
                continue
            visited.add(path)
            response = self.session.get(BASE + path, allow_redirects=False)
            self.assertLess(response.status_code, 400, f"Nedelujoča povezava: {path}")
            for href in re.findall(r'href="(/[^"]*)"', response.text):
                clean = href.split("?", 1)[0]
                if clean not in visited and not clean.startswith("/static/"):
                    queue.append(clean)

    def test_attendance_is_persisted(self):
        with self.db.cursor() as cur:
            cur.execute("SELECT event_id,person_id,status FROM attendance ORDER BY event_id,person_id LIMIT 1")
            row = dict(cur.fetchone())
        changed = "absent" if row["status"] != "absent" else "present"
        response = self.session.post(f"{BASE}/api/prisotnost", json={"event_id": row["event_id"], "person_id": row["person_id"], "status": changed})
        self.assertEqual(response.status_code, 200)
        with self.db.cursor() as cur:
            cur.execute("SELECT status FROM attendance WHERE event_id=%s AND person_id=%s", (row["event_id"], row["person_id"]))
            self.assertEqual(cur.fetchone()["status"], changed)
        self.session.post(f"{BASE}/api/prisotnost", json={**row})

    def test_attendance_filters_school_year_and_type(self):
        response=self.session.get(f"{BASE}/prisotnost",params={"leto":"2025","vrsta":"Vaje"})
        self.assertEqual(response.status_code,200)
        self.assertIn('value="Vaje" selected',response.text)
        self.assertIn('name="leto"',response.text)
        self.assertNotIn("Poletni večer pesmi",response.text)

    def test_create_flows_and_cleanup(self):
        marker = uuid.uuid4().hex[:8]
        member = self.session.post(f"{BASE}/clani", data={"first_name": "Test", "last_name": marker, "email": f"test.{marker}@example.si", "phone": "", "birth_date": "2000-01-01", "voice": "Alt"})
        self.assertEqual(member.status_code, 200)
        song = self.session.post(f"{BASE}/program", data={"title": f"Test {marker}", "author": "Test", "categories": "Ljudska"})
        self.assertIn("/program/", song.url)
        event = self.session.post(f"{BASE}/dogodki", data={"event_date": "2026-12-01T18:00", "event_type": "Vaja", "name": f"Test {marker}", "place": "Test"})
        self.assertIn("/dogodki/", event.url)
        treasury = self.session.post(f"{BASE}/blagajna", data={"date": "2026-08-03", "description": f"Test {marker}", "person_name": "Test", "kind": "Prihodek", "amount": "1.00", "settled": "1"})
        self.assertEqual(treasury.status_code, 200)
        with self.db.cursor() as cur:
            cur.execute("SELECT id FROM transactions WHERE description=%s",(f"Test {marker}",)); transaction_id=cur.fetchone()["id"]
        edited=self.session.post(f"{BASE}/blagajna/{transaction_id}/uredi",data={"date":"2026-08-04","description":f"Test edited {marker}","person_name":"Test Two","kind":"Odhodek","amount":"2.50"})
        self.assertEqual(edited.status_code,200)
        with self.db.cursor() as cur:
            cur.execute("SELECT kind,amount,settled FROM transactions WHERE id=%s",(transaction_id,)); changed=dict(cur.fetchone())
            self.assertEqual(changed["kind"],"Odhodek"); self.assertFalse(changed["settled"])
            cur.execute("DELETE FROM transactions WHERE id=%s", (transaction_id,))
            cur.execute("DELETE FROM events WHERE name=%s", (f"Test {marker}",))
            cur.execute("DELETE FROM songs WHERE title=%s", (f"Test {marker}",))
            cur.execute("DELETE FROM people WHERE email=%s", (f"test.{marker}@example.si",))

    def test_used_role_cannot_be_deleted(self):
        with self.db.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE name='Član'"); role_id=cur.fetchone()["id"]
        response=self.session.post(f"{BASE}/vloge/{role_id}/izbrisi")
        self.assertEqual(response.status_code,200)
        with self.db.cursor() as cur:
            cur.execute("SELECT COUNT(*) count FROM roles WHERE id=%s",(role_id,)); self.assertEqual(cur.fetchone()["count"],1)

    def test_unused_role_can_be_edited_and_deleted(self):
        marker=uuid.uuid4().hex[:8]
        self.session.post(f"{BASE}/vloge",data={"name":f"Test role {marker}","description":"Za test"})
        with self.db.cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE name=%s",(f"Test role {marker}",)); role_id=cur.fetchone()["id"]
        self.session.post(f"{BASE}/vloge/{role_id}/uredi",data={"name":f"Edited role {marker}","description":"Spremenjeno"})
        with self.db.cursor() as cur:
            cur.execute("SELECT description FROM roles WHERE id=%s",(role_id,)); self.assertEqual(cur.fetchone()["description"],"Spremenjeno")
        self.session.post(f"{BASE}/vloge/{role_id}/izbrisi")
        with self.db.cursor() as cur:
            cur.execute("SELECT COUNT(*) count FROM roles WHERE id=%s",(role_id,)); self.assertEqual(cur.fetchone()["count"],0)

    def test_category_crud_and_calendar_export(self):
        marker=uuid.uuid4().hex[:8]
        self.session.post(f"{BASE}/kategorije",data={"name":f"Test category {marker}","description":"Za test"})
        with self.db.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name=%s",(f"Test category {marker}",)); category_id=cur.fetchone()["id"]
        self.session.post(f"{BASE}/kategorije/{category_id}/uredi",data={"name":f"Edited category {marker}","description":"Spremenjeno"})
        self.session.post(f"{BASE}/kategorije/{category_id}/izbrisi")
        with self.db.cursor() as cur:
            cur.execute("SELECT COUNT(*) count FROM categories WHERE id=%s",(category_id,)); self.assertEqual(cur.fetchone()["count"],0)
        calendar=self.session.get(f"{BASE}/dogodki/koledar.ics")
        self.assertEqual(calendar.status_code,200); self.assertIn("BEGIN:VCALENDAR",calendar.text); self.assertIn("BEGIN:VEVENT",calendar.text)

    def test_performance_details_are_conductor_only(self):
        conductor_page=self.session.get(f"{BASE}/dogodki/1")
        self.assertIn("Oceni izvedbo",conductor_page.text)
        other=requests.Session(); other.post(f"{BASE}/prijava",data={"username":"ana.kovac","password":"zbor2026"})
        other_page=other.get(f"{BASE}/dogodki/1")
        self.assertNotIn("Oceni izvedbo",other_page.text)
        forbidden=other.post(f"{BASE}/dogodki/1/program/1",data={"rating":"5","comment":"Ne sme"},allow_redirects=False)
        self.assertEqual(forbidden.status_code,403)
        song_page=other.get(f"{BASE}/program/1")
        self.assertNotIn("Pretekle izvedbe",song_page.text)

    def test_member_cannot_administer_members(self):
        member_session = requests.Session()
        login = member_session.post(f"{BASE}/prijava", data={"username": "ana.kovac", "password": "zbor2026"}, allow_redirects=False)
        self.assertEqual(login.status_code, 303)
        self.assertTrue(login.headers["Location"].endswith("/"))
        response = member_session.post(f"{BASE}/clani", data={}, allow_redirects=False)
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)

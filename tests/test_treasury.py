import json
import os
import unittest
from contextlib import contextmanager
from pathlib import Path
from datetime import date
from unittest.mock import Mock
from bottle import template
from Data.import_treasury_2026 import import_rows
from Data.repository import ChoirRepository
from Services.choir_service import ChoirService

ROOT=Path(__file__).resolve().parents[1]
ROWS=json.loads((ROOT/'Data/treasury_opening_2026.json').read_text(encoding='utf-8'))

class TreasuryViewTests(unittest.TestCase):
    def test_optional_fields_and_render(self):
        repo=Mock()
        repo.list_transactions.return_value=[dict(id=1,transaction_date=date(2026,2,15),description='Koncert',person_name='Zbor',kind='Prihodek',amount=305,settled=False,category='koncert',notes='Opomba')]
        data=ChoirService(repo).treasury()
        html=template('treasury',template_lookup=[str(ROOT/'Presentation/views')],data=data)
        self.assertIn('name="category" value="koncert"',html)
        self.assertIn('<th>Kategorija</th>',html)
        self.assertIn('Opomba',html)
        repo.list_transactions.return_value[0].update(category=None,notes=None)
        self.assertEqual(ChoirService(repo).treasury()['transactions'][0]['category'],'')

@unittest.skipUnless(os.getenv('TREASURY_TEST_DSN'),'Isolated PostgreSQL temporary table DSN required')
class TreasuryDatabaseTests(unittest.TestCase):
    def test_import_and_repository_roundtrip(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn=psycopg2.connect(os.environ['TREASURY_TEST_DSN'])
        try:
            with conn.cursor() as cur:
                cur.execute('CREATE TEMP TABLE transactions(id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,transaction_date DATE,description TEXT,person_name TEXT,kind TEXT,amount NUMERIC(12,2),settled BOOLEAN,created_by BIGINT)')
                cur.execute('ALTER TABLE transactions ADD COLUMN IF NOT EXISTS category TEXT')
                cur.execute('ALTER TABLE transactions ADD COLUMN IF NOT EXISTS notes TEXT')
            self.assertEqual(import_rows(conn,ROWS),15)
            self.assertEqual(import_rows(conn,ROWS),0)
            with conn.cursor() as cur:
                cur.execute("SELECT count(*),sum(CASE WHEN kind='Prihodek' THEN amount ELSE -amount END),count(*) FILTER (WHERE settled) FROM transactions")
                count,balance,settled=cur.fetchone()
                self.assertEqual((count,str(balance),settled),(15,'1591.39',10))
            class DB:
                @contextmanager
                def cursor(self):
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:yield cur
            repo=ChoirRepository.__new__(ChoirRepository);repo.db=DB()
            values=dict(date='2026-10-18',description='Test',person_name='Test',kind='Odhodek',amount='1.23',category=' test ',notes=' opomba ',settled=False)
            tid=repo.create_transaction(values,None)
            found=next(r for r in repo.list_transactions() if r['id']==tid)
            self.assertEqual((found['category'],found['notes']),('test','opomba'))
            values.update(category='',notes='')
            repo.update_transaction(tid,values)
            found=next(r for r in repo.list_transactions() if r['id']==tid)
            self.assertEqual((found['category'],found['notes']),(None,None))
        finally:
            conn.rollback();conn.close()

if __name__=='__main__':unittest.main()

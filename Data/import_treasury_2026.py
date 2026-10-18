"""One-time, repeat-safe import of the supplied 2026 treasury ledger.
Dry run by default; --apply commits all rows atomically. Never sends notifications.
"""
import argparse
import json
import os
from decimal import Decimal
from pathlib import Path
import psycopg2


def import_rows(connection, rows):
    inserted = 0
    with connection.cursor() as cur:
        cur.execute('LOCK TABLE transactions IN SHARE ROW EXCLUSIVE MODE')
        for row in rows:
            key = (row['date'], row['description'], row['person_name'], row['kind'], Decimal(row['amount']))
            cur.execute('SELECT category,notes,settled FROM transactions WHERE transaction_date=%s AND description=%s AND person_name=%s AND kind=%s AND amount=%s', key)
            matches = cur.fetchall()
            if matches:
                expected = (row['category'], row['notes'], row['settled'])
                if len(matches) != 1 or tuple(matches[0]) != expected:
                    raise ValueError('Conflicting existing transaction: ' + row['description'])
                continue
            cur.execute('INSERT INTO transactions(transaction_date,description,person_name,kind,amount,category,notes,settled) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)', key + (row['category'],row['notes'],row['settled']))
            inserted += 1
    return inserted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    rows = json.loads(Path(__file__).with_name('treasury_opening_2026.json').read_text(encoding='utf-8'))
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    try:
        inserted = import_rows(conn, rows)
        if args.apply:
            conn.commit()
        else:
            conn.rollback()
        income = sum(Decimal(row['amount']) for row in rows if row['kind']=='Prihodek')
        expenses = sum(Decimal(row['amount']) for row in rows if row['kind']=='Odhodek')
        print(json.dumps(dict(applied=args.apply, inserted=inserted, existing=len(rows)-inserted, income=str(income), expenses=str(expenses), balance=str(income-expenses))))
    finally:
        conn.close()


if __name__ == '__main__':
    main()

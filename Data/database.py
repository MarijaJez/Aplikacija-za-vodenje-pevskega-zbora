"""PostgreSQL connection management for the data layer."""

import os
from pathlib import Path
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool


class Database:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            raise RuntimeError("Nastavi DATABASE_URL za povezavo s PostgreSQL.")
        self.timezone = os.getenv("APP_TIMEZONE", "Europe/Ljubljana")
        self._pool = ThreadedConnectionPool(1, 10, self.dsn, options=f"-c timezone={self.timezone}")
        with self.cursor() as cursor:

            cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS category TEXT")
            cursor.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS notes TEXT")
            cursor.execute("ALTER TABLE people ADD COLUMN IF NOT EXISTS avatar_path TEXT")
            cursor.execute((Path(__file__).parent / "migrations" / "007_notification_preferences.sql").read_text())
            cursor.execute("ALTER TABLE songs ADD COLUMN IF NOT EXISTS notes_comment TEXT NOT NULL DEFAULT ''")
            cursor.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_end TIMESTAMPTZ CHECK (event_end > event_date)")

            cursor.execute("""CREATE TABLE IF NOT EXISTS event_reminder_deliveries (
                event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                local_date DATE NOT NULL,
                endpoint TEXT NOT NULL,
                claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY(event_id, local_date, endpoint)
            )""")

    @contextmanager
    def connection(self):
        connection = self._pool.getconn()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            self._pool.putconn(connection)

    @contextmanager
    def cursor(self):
        with self.connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor

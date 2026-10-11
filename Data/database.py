"""PostgreSQL connection management for the data layer."""

import os
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

            cursor.execute("ALTER TABLE people ADD COLUMN IF NOT EXISTS avatar_path TEXT")
            cursor.execute("ALTER TABLE songs ADD COLUMN IF NOT EXISTS notes_comment TEXT NOT NULL DEFAULT ''")
            cursor.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_end TIMESTAMPTZ CHECK (event_end > event_date)")

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

import os
from collections.abc import Iterator
from contextlib import contextmanager

from psycopg2.extensions import connection as Connection, make_dsn
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

class Database:
    """PostgreSQL connection management for the data layer."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            password = os.getenv("DB_PASSWORD")
            if not password:
                raise RuntimeError(
                    "Nastavi DATABASE_URL ali okoljsko spremenljivko DB_PASSWORD."
                )
            self.dsn = make_dsn(
                dbname=os.getenv("DB_NAME", "opb2026_marijaj"),
                host=os.getenv("DB_HOST", "baza.fmf.uni-lj.si"),
                user=os.getenv("DB_USER", "marijaj"),
                password=password,
                port=os.getenv("DB_PORT", "5432"),
            )
        self._pool = ThreadedConnectionPool(1, 10, self.dsn)

    @contextmanager
    def connection(self) -> Iterator[Connection, None, None]:
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
    def cursor(self) -> Iterator[RealDictCursor, None, None]:
        with self.connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor

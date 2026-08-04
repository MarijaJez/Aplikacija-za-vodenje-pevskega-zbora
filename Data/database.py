import os
from collections.abc import Iterator
from contextlib import contextmanager

from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

DATABASE = "opb2026_marijaj"
HOST = "baza.fmf.uni-lj.si"
USER = "marijaj"
PASSWORD = "ldbp4hlh"
PORT = 5432

class Database:
    """PostgreSQL connection management for the data layer."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv(
            "DATABASE_URL",
            f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}",
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

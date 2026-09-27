"""Apply idempotent SQL migrations to an existing database."""

from pathlib import Path

from Data.database import Database


def apply_migrations(database: Database | None = None) -> None:
    db = database or Database()
    migrations = Path(__file__).with_name("migrations")
    for path in sorted(migrations.glob("*.sql")):
        with db.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(path.read_text(encoding="utf-8"))
        print(f"Uporabljena migracija: {path.name}")


if __name__ == "__main__":
    apply_migrations()

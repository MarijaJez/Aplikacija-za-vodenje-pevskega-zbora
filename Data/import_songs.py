"""Import the reviewed Drive catalogue, without duplicating existing songs.

Run from the project root: python -m Data.import_songs
The manifest and its prepared files in uploads must be present. File hashes are
checked before the single database transaction starts; existing songs are kept.
"""

import hashlib
import json
from pathlib import Path

from Data.database import Database


def import_songs() -> tuple[int, int]:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "Data/song_import_manifest.json").read_text(encoding="utf-8"))
    categories = manifest["categories"]
    identities = set()
    for song in manifest["songs"]:
        identity = (song["title"].casefold(), song["author"].casefold())
        if identity in identities:
            raise ValueError(f"Duplicate manifest song: {song['title']}")
        identities.add(identity)
        if not set(song["categories"]).issubset(categories):
            raise ValueError(f"Unknown category: {song['title']}")
        filename = song["notes_path"]
        if Path(filename).name != filename:
            raise ValueError("notes_path must be a filename")
        path = root / "uploads" / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != song["notes_sha256"]:
            raise ValueError(f"Score checksum mismatch: {song['title']}")
    added = skipped = 0
    database = Database()
    with database.cursor() as cursor:
        # Serialize imports, including concurrent executions of this command.
        cursor.execute("SELECT pg_advisory_xact_lock(781141011)")
        for name in categories:
            cursor.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))
        cursor.execute("SELECT id, name FROM categories")
        category_ids = {row["name"]: row["id"] for row in cursor.fetchall()}
        for song in manifest["songs"]:
            cursor.execute("SELECT id FROM songs WHERE lower(title) = lower(%s) AND lower(author) = lower(%s)", (song["title"], song["author"]))
            existing = cursor.fetchone()
            notes_comment = song.get("notes_comment", "")
            if existing:
                if notes_comment:
                    cursor.execute("UPDATE songs SET notes_comment=%s WHERE id=%s AND notes_comment=''", (notes_comment, existing["id"]))
                skipped += 1
                continue
            cursor.execute("INSERT INTO songs (title, author, notes_path, notes_comment) VALUES (%s, %s, %s, %s) RETURNING id", (song["title"], song["author"], song["notes_path"], notes_comment))
            song_id = cursor.fetchone()["id"]
            for name in song["categories"]:
                cursor.execute("INSERT INTO song_categories (song_id, category_id) VALUES (%s, %s)", (song_id, category_ids[name]))
            added += 1
    return added, skipped


if __name__ == "__main__":
    added, skipped = import_songs()
    print(f"Dodano: {added}; že v bazi: {skipped}.")

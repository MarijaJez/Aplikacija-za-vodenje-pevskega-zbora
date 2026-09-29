"""Persistence for the private event gallery and the choir group chat."""

from Data.database import Database


class CommunityRepository:
    def __init__(self, database: Database | None = None):
        self.db = database or Database()

    @staticmethod
    def _rows(cursor):
        return [dict(row) for row in cursor.fetchall()]

    def gallery_events(self):
        with self.db.cursor() as cur:
            cur.execute("""SELECT e.id, e.name, e.event_date, e.event_type,
                                  COUNT(p.id)::int AS photo_count
                           FROM events e LEFT JOIN event_photos p ON p.event_id=e.id
                           GROUP BY e.id ORDER BY e.event_date DESC LIMIT 200""")
            return self._rows(cur)

    def event(self, event_id):
        with self.db.cursor() as cur:
            cur.execute("SELECT id, name, event_date, event_type FROM events WHERE id=%s", (event_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def photos(self, event_id):
        with self.db.cursor() as cur:
            cur.execute("""SELECT p.id, p.event_id, p.caption, p.alt_text, p.uploaded_at,
                                  COALESCE(a.first_name || ' ' || a.last_name, 'Nekdanji član') AS uploader
                           FROM event_photos p LEFT JOIN users u ON u.id=p.uploaded_by
                           LEFT JOIN people a ON a.id=u.person_id
                           WHERE p.event_id=%s ORDER BY p.uploaded_at DESC, p.id DESC""", (event_id,))
            return self._rows(cur)

    def photo(self, photo_id):
        with self.db.cursor() as cur:
            cur.execute("SELECT id, event_id, file_name, caption, alt_text FROM event_photos WHERE id=%s", (photo_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def photo_count(self, event_id):
        with self.db.cursor() as cur:
            cur.execute("SELECT COUNT(*)::int AS count FROM event_photos WHERE event_id=%s", (event_id,))
            return cur.fetchone()["count"]

    def photo_files_for_event(self, event_id):
        """Capture paths before deleting an event (the FK cascades photo rows)."""
        with self.db.cursor() as cur:
            cur.execute("SELECT file_name FROM event_photos WHERE event_id=%s", (event_id,))
            return [row["file_name"] for row in cur.fetchall()]

    def add_photo(self, event_id, file_name, caption, alt_text, user_id):
        with self.db.cursor() as cur:
            cur.execute("""INSERT INTO event_photos(event_id,file_name,caption,alt_text,uploaded_by)
                           VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                        (event_id, file_name, caption, alt_text, user_id))
            return cur.fetchone()["id"]

    def delete_photo(self, photo_id):
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM event_photos WHERE id=%s RETURNING file_name", (photo_id,))
            row = cur.fetchone()
            return row["file_name"] if row else None

    def messages(self, limit=100):
        limit = max(1, min(int(limit), 100))
        with self.db.cursor() as cur:
            cur.execute("""SELECT q.id,q.author_id,q.body,q.created_at,q.edited_at,q.deleted_at,
                                  COALESCE(p.first_name || ' ' || p.last_name, 'Nekdanji član') author
                           FROM (SELECT * FROM chat_messages ORDER BY id DESC LIMIT %s) q
                           LEFT JOIN users u ON u.id=q.author_id LEFT JOIN people p ON p.id=u.person_id
                           ORDER BY q.id""", (limit,))
            return self._rows(cur)

    def add_message(self, user_id, body):
        with self.db.cursor() as cur:
            cur.execute("INSERT INTO chat_messages(author_id,body) VALUES(%s,%s) RETURNING id", (user_id, body))
            return cur.fetchone()["id"]

    def edit_message(self, message_id, actor_id, body):
        with self.db.cursor() as cur:
            cur.execute("""UPDATE chat_messages SET body=%s,edited_at=NOW()
                           WHERE id=%s AND author_id=%s AND deleted_at IS NULL RETURNING id""",
                        (body, message_id, actor_id))
            return bool(cur.fetchone())

    def delete_message(self, message_id, actor_id, moderator=False):
        with self.db.cursor() as cur:
            cur.execute("""UPDATE chat_messages SET body='[Sporočilo je izbrisano]',deleted_at=NOW(),deleted_by=%s
                           WHERE id=%s AND deleted_at IS NULL AND (author_id=%s OR %s) RETURNING id""",
                        (actor_id, message_id, actor_id, moderator))
            return bool(cur.fetchone())

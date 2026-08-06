"""PostgreSQL repository returning typed domain models."""

from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import TypeVar

from psycopg2.extensions import cursor as Cursor
from psycopg2.extras import RealDictCursor

from Data.database import Database
from Data.models import (
    AttendanceRecord,
    AttendanceStatus,
    Category,
    Event,
    EventInput,
    EventProgramSong,
    Member,
    MemberAttendance,
    MemberInput,
    Role,
    Song,
    SongInput,
    SongPerformance,
    SongReview,
    Transaction,
    TransactionInput,
    User,
)


ModelT = TypeVar("ModelT")


class ChoirRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.db = database or Database()

    @staticmethod
    def _one(cursor: Cursor, factory: Callable[..., ModelT]) -> ModelT | None:
        row = cursor.fetchone()
        return factory(**dict(row)) if row else None

    @staticmethod
    def _all(cursor: Cursor, factory: Callable[..., ModelT]) -> list[ModelT]:
        return [factory(**dict(row)) for row in cursor.fetchall()]

    def get_user_by_username(self, username: str) -> User | None:
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.person_id, u.username, u.password_hash, u.must_change_password,
                       p.first_name, p.last_name, p.email,
                       COALESCE(array_agg(r.name ORDER BY r.name) FILTER (WHERE r.id IS NOT NULL), '{}') roles
                FROM users u JOIN people p ON p.id=u.person_id
                LEFT JOIN person_roles pr ON pr.person_id=p.id LEFT JOIN roles r ON r.id=pr.role_id
                WHERE lower(u.username)=lower(%s)
                GROUP BY u.id,p.id
            """, (username,))
            return self._one(cur, User)

    def get_user_by_id(self, user_id: int) -> User | None:
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.person_id, u.username, u.password_hash, u.must_change_password,
                       p.first_name, p.last_name, p.email,
                       COALESCE(array_agg(r.name ORDER BY r.name) FILTER (WHERE r.id IS NOT NULL), '{}') roles
                FROM users u JOIN people p ON p.id=u.person_id
                LEFT JOIN person_roles pr ON pr.person_id=p.id LEFT JOIN roles r ON r.id=pr.role_id
                WHERE u.id=%s GROUP BY u.id,p.id
            """, (user_id,))
            return self._one(cur, User)

    def username_exists(self, username: str) -> bool:
        with self.db.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM users WHERE lower(username)=lower(%s)) present", (username,))
            return cur.fetchone()["present"]

    def record_login(self, user_id: int) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE users SET last_login=NOW() WHERE id=%s", (user_id,))

    def change_password(self, user_id: int, password_hash: str, must_change: bool = False) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE users SET password_hash=%s,must_change_password=%s WHERE id=%s", (password_hash, must_change, user_id))

    def list_members(self) -> list[Member]:
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT p.id,p.first_name,p.last_name,p.birth_date,p.email,p.phone,p.voice,u.username,
                  COALESCE(array_agg(DISTINCT r.name ORDER BY r.name) FILTER (WHERE r.id IS NOT NULL),'{}') roles,
                  COALESCE(ROUND(100.0 * COUNT(DISTINCT (a.event_id,a.person_id)) FILTER (WHERE a.status IN ('present','late_under','late_over') AND ae.event_date<NOW() AND ae.event_date>=date_trunc('year',NOW()-interval '8 months')+interval '8 months') / NULLIF(COUNT(DISTINCT (a.event_id,a.person_id)) FILTER (WHERE ae.event_date<NOW() AND ae.event_date>=date_trunc('year',NOW()-interval '8 months')+interval '8 months'),0)),0)::int attendance
                FROM people p JOIN users u ON u.person_id=p.id
                LEFT JOIN person_roles pr ON pr.person_id=p.id LEFT JOIN roles r ON r.id=pr.role_id
                LEFT JOIN attendance a ON a.person_id=p.id LEFT JOIN events ae ON ae.id=a.event_id
                WHERE p.active=TRUE GROUP BY p.id,u.username ORDER BY p.last_name,p.first_name
            """)
            return self._all(cur, Member)

    def get_member(self, person_id: int) -> Member | None:
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT p.id,p.first_name,p.last_name,p.birth_date,p.email,p.phone,p.voice,u.username,u.must_change_password,
                  COALESCE(array_agg(DISTINCT r.name ORDER BY r.name) FILTER (WHERE r.id IS NOT NULL),'{}') roles,
                  COALESCE(ROUND(100.0 * COUNT(DISTINCT (a.event_id,a.person_id)) FILTER (WHERE a.status IN ('present','late_under','late_over') AND ae.event_date<NOW() AND ae.event_date>=date_trunc('year',NOW()-interval '8 months')+interval '8 months') / NULLIF(COUNT(DISTINCT (a.event_id,a.person_id)) FILTER (WHERE ae.event_date<NOW() AND ae.event_date>=date_trunc('year',NOW()-interval '8 months')+interval '8 months'),0)),0)::int attendance
                FROM people p JOIN users u ON u.person_id=p.id
                LEFT JOIN person_roles pr ON pr.person_id=p.id LEFT JOIN roles r ON r.id=pr.role_id
                LEFT JOIN attendance a ON a.person_id=p.id LEFT JOIN events ae ON ae.id=a.event_id WHERE p.id=%s GROUP BY p.id,u.id
            """, (person_id,))
            return self._one(cur, Member)

    def create_member(
        self,
        person: MemberInput,
        username: str,
        password_hash: str,
        role_names: Sequence[str],
    ) -> int:
        with self.db.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""INSERT INTO people(first_name,last_name,birth_date,email,phone,voice)
                    VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (person["first_name"],person["last_name"],person.get("birth_date") or None,person["email"],person.get("phone",''),person["voice"]))
                person_id=cur.fetchone()["id"]
                cur.execute("INSERT INTO users(person_id,username,password_hash,must_change_password) VALUES(%s,%s,%s,TRUE)", (person_id,username,password_hash))
                selected=set(role_names)|{"Član"}
                cur.execute("INSERT INTO person_roles(person_id,role_id) SELECT %s,id FROM roles WHERE name=ANY(%s)", (person_id,list(selected)))
                return person_id

    def update_member(self, person_id: int, values: MemberInput) -> None:
        with self.db.cursor() as cur:
            cur.execute("""UPDATE people SET first_name=%s,last_name=%s,birth_date=%s,email=%s,phone=%s,voice=%s WHERE id=%s""",
                (values["first_name"],values["last_name"],values.get("birth_date") or None,values["email"],values.get("phone",''),values["voice"],person_id))

    def delete_member(self, person_id: int) -> None:
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM people WHERE id=%s", (person_id,))

    def set_member_roles(self, person_id: int, role_names: Sequence[str]) -> None:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM person_roles WHERE person_id=%s", (person_id,))
                selected=set(role_names)|{"Član"}
                cur.execute("INSERT INTO person_roles(person_id,role_id) SELECT %s,id FROM roles WHERE name=ANY(%s)", (person_id,list(selected)))

    def list_roles(self) -> list[Role]:
        with self.db.cursor() as cur:
            cur.execute("""SELECT r.id,r.name,r.description,COUNT(pr.person_id)::int count FROM roles r LEFT JOIN person_roles pr ON pr.role_id=r.id GROUP BY r.id ORDER BY r.id""")
            return self._all(cur, Role)

    def create_role(self, name: str, description: str) -> int:
        with self.db.cursor() as cur:
            cur.execute("INSERT INTO roles(name,description) VALUES(%s,%s) RETURNING id", (name,description)); return cur.fetchone()["id"]

    def delete_role(self, role_id: int) -> int:
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM roles r WHERE r.id=%s AND r.name<>'Član' AND NOT EXISTS(SELECT 1 FROM person_roles pr WHERE pr.role_id=r.id)", (role_id,))
            return cur.rowcount

    def update_role(self, role_id: int, name: str, description: str) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE roles SET name=CASE WHEN name='Član' THEN name ELSE %s END,description=%s WHERE id=%s", (name, description, role_id))

    def list_categories(self) -> list[Category]:
        with self.db.cursor() as cur:
            cur.execute("SELECT c.id,c.name,c.description,COUNT(sc.song_id)::int count FROM categories c LEFT JOIN song_categories sc ON sc.category_id=c.id GROUP BY c.id ORDER BY c.name")
            return self._all(cur, Category)

    def create_category(self, name: str, description: str) -> int:
        with self.db.cursor() as cur:
            cur.execute("INSERT INTO categories(name,description) VALUES(%s,%s) RETURNING id",(name,description)); return cur.fetchone()["id"]

    def update_category(self, category_id: int, name: str, description: str) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE categories SET name=%s,description=%s WHERE id=%s",(name,description,category_id))

    def delete_category(self, category_id: int) -> int:
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM categories c WHERE c.id=%s AND NOT EXISTS(SELECT 1 FROM song_categories sc WHERE sc.category_id=c.id)",(category_id,)); return cur.rowcount

    def list_songs(self) -> list[Song]:
        with self.db.cursor() as cur:
            cur.execute("""
              SELECT s.id,s.title,s.author,s.notes_path,s.audio_path,s.created_at,
                COALESCE(array_agg(DISTINCT c.name ORDER BY c.name) FILTER(WHERE c.id IS NOT NULL),'{}') categories,
                COALESCE(ROUND(AVG(sr.rating)::numeric,1),0)::float rating,COUNT(DISTINCT sr.person_id)::int ratings,
                MAX(e.event_date) last_performed
              FROM songs s LEFT JOIN song_categories sc ON sc.song_id=s.id LEFT JOIN categories c ON c.id=sc.category_id
              LEFT JOIN song_reviews sr ON sr.song_id=s.id LEFT JOIN event_program ep ON ep.song_id=s.id LEFT JOIN events e ON e.id=ep.event_id AND e.event_date<NOW()
              GROUP BY s.id ORDER BY s.created_at DESC
            """)
            return self._all(cur, Song)

    def get_song(self, song_id: int) -> Song | None:
        songs = [song for song in self.list_songs() if song.id == song_id]
        if not songs:return None
        song = songs[0]
        with self.db.cursor() as cur:
            cur.execute("""SELECT sr.rating,sr.comment,sr.updated_at,p.first_name||' '||p.last_name member,
              upper(left(p.first_name,1)||left(p.last_name,1)) initials,sr.person_id FROM song_reviews sr JOIN people p ON p.id=sr.person_id WHERE sr.song_id=%s ORDER BY sr.updated_at DESC""",(song_id,))
            reviews = self._all(cur, SongReview)
            cur.execute("""SELECT e.id,e.name,e.event_type,e.event_date,e.place,ep.performance_rating rating,ep.comment
              FROM event_program ep JOIN events e ON e.id=ep.event_id WHERE ep.song_id=%s AND e.event_date<NOW() ORDER BY e.event_date DESC""",(song_id,))
            performances = self._all(cur, SongPerformance)
        return replace(song, reviews=reviews, performances=performances)

    def upsert_review(self, person_id: int, song_id: int, rating: int, comment: str) -> None:
        with self.db.cursor() as cur:
            cur.execute("""INSERT INTO song_reviews(person_id,song_id,rating,comment) VALUES(%s,%s,%s,%s)
              ON CONFLICT(person_id,song_id) DO UPDATE SET rating=EXCLUDED.rating,comment=EXCLUDED.comment,updated_at=NOW()""",(person_id,song_id,rating,comment))

    def create_song(self, values: SongInput, categories: Sequence[str]) -> int:
        with self.db.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO songs(title,author,notes_path,audio_path) VALUES(%s,%s,%s,%s) RETURNING id", (values["title"], values["author"], values.get("notes_path"),values.get("audio_path")))
                song_id=cur.fetchone()["id"]
                cur.execute("INSERT INTO song_categories(song_id,category_id) SELECT %s,id FROM categories WHERE name=ANY(%s)", (song_id,list(categories)))
                return song_id

    def update_song(self, song_id: int, values: SongInput, categories: Sequence[str]) -> None:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE songs SET title=%s,author=%s,notes_path=COALESCE(%s,notes_path),audio_path=COALESCE(%s,audio_path) WHERE id=%s", (values["title"],values["author"],values.get("notes_path"),values.get("audio_path"),song_id))
                cur.execute("DELETE FROM song_categories WHERE song_id=%s",(song_id,))
                cur.execute("INSERT INTO song_categories(song_id,category_id) SELECT %s,id FROM categories WHERE name=ANY(%s)",(song_id,list(categories)))

    def delete_song(self, song_id: int) -> None:
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM songs WHERE id=%s",(song_id,))

    def list_events(self) -> list[Event]:
        with self.db.cursor() as cur:
            cur.execute("""SELECT e.id,e.event_date,e.event_type,e.name,e.place,COUNT(ep.song_id)::int songs FROM events e LEFT JOIN event_program ep ON ep.event_id=e.id GROUP BY e.id ORDER BY e.event_date DESC""")
            return self._all(cur, Event)

    def list_event_types(self) -> list[str]:
        with self.db.cursor() as cur:
            cur.execute("SELECT DISTINCT event_type FROM events ORDER BY event_type")
            return [row["event_type"] for row in cur.fetchall()]

    def get_event(self, event_id: int) -> Event | None:
        with self.db.cursor() as cur:
            cur.execute("SELECT e.*,COUNT(ep.song_id)::int songs FROM events e LEFT JOIN event_program ep ON ep.event_id=e.id WHERE e.id=%s GROUP BY e.id",(event_id,)); event=self._one(cur, Event)
            if not event:return None
            cur.execute("""SELECT s.id,s.title,s.author,s.audio_path,ep.performance_rating rating,ep.comment FROM event_program ep JOIN songs s ON s.id=ep.song_id WHERE ep.event_id=%s ORDER BY ep.position""",(event_id,))
            program = self._all(cur, EventProgramSong)
            return replace(event, program=program)

    def create_event(self, values: EventInput, song_ids: Sequence[int]) -> int:
        with self.db.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO events(event_date,event_type,name,place) VALUES(%s,%s,%s,%s) RETURNING id",(values["event_date"],values["event_type"],values["name"],values["place"]))
                event_id=cur.fetchone()["id"]
                for position,song_id in enumerate(song_ids,1): cur.execute("INSERT INTO event_program(event_id,song_id,position) VALUES(%s,%s,%s)",(event_id,song_id,position))
                return event_id

    def update_event(self, event_id: int, values: EventInput, song_ids: Sequence[int]) -> None:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE events SET event_date=%s,event_type=%s,name=%s,place=%s WHERE id=%s",(values["event_date"],values["event_type"],values["name"],values["place"],event_id))
                cur.execute("DELETE FROM event_program WHERE event_id=%s AND NOT(song_id=ANY(%s))",(event_id,song_ids))
                for position,song_id in enumerate(song_ids,1):
                    cur.execute("""INSERT INTO event_program(event_id,song_id,position) VALUES(%s,%s,%s)
                      ON CONFLICT(event_id,song_id) DO UPDATE SET position=EXCLUDED.position""",(event_id,song_id,position))

    def delete_event(self, event_id: int) -> None:
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id=%s",(event_id,))

    def update_performance(self, event_id: int, song_id: int, rating: int, comment: str) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE event_program SET performance_rating=%s,comment=%s WHERE event_id=%s AND song_id=%s",(rating,comment,event_id,song_id))

    def list_attendance(self) -> list[AttendanceRecord]:
        with self.db.cursor() as cur:
            cur.execute("SELECT event_id,person_id,status FROM attendance")
            return self._all(cur, AttendanceRecord)

    def member_attendance(self, person_id: int) -> list[MemberAttendance]:
        with self.db.cursor() as cur:
            cur.execute("""SELECT e.id,e.name,e.event_type,e.event_date,a.status FROM attendance a JOIN events e ON e.id=a.event_id
              WHERE a.person_id=%s AND e.event_date>=date_trunc('year',NOW()-interval '8 months')+interval '8 months'
              ORDER BY e.event_date DESC""",(person_id,))
            return self._all(cur, MemberAttendance)

    def upsert_attendance(
        self,
        event_id: int,
        person_id: int,
        status: AttendanceStatus,
        user_id: int,
    ) -> None:
        with self.db.cursor() as cur:
            cur.execute("""INSERT INTO attendance(event_id,person_id,status,updated_by) VALUES(%s,%s,%s,%s)
              ON CONFLICT(event_id,person_id) DO UPDATE SET status=EXCLUDED.status,updated_by=EXCLUDED.updated_by,updated_at=NOW()""",(event_id,person_id,status,user_id))

    def list_transactions(self) -> list[Transaction]:
        with self.db.cursor() as cur:
            cur.execute("SELECT id,transaction_date,description,person_name,kind,amount,settled FROM transactions ORDER BY transaction_date DESC,id DESC")
            return self._all(cur, Transaction)

    def create_transaction(self, values: TransactionInput, user_id: int) -> int:
        with self.db.cursor() as cur:
            cur.execute("""INSERT INTO transactions(transaction_date,description,person_name,kind,amount,settled,created_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",(values["date"],values["description"],values["person_name"],values["kind"],values["amount"],values.get("settled",False),user_id)); return cur.fetchone()["id"]

    def toggle_transaction(self, transaction_id: int) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE transactions SET settled=NOT settled WHERE id=%s",(transaction_id,))

    def set_transaction_settled(self, transaction_id: int, settled: bool) -> None:
        with self.db.cursor() as cur:
            cur.execute("UPDATE transactions SET settled=%s WHERE id=%s",(settled,transaction_id))

    def update_transaction(self, transaction_id: int, values: TransactionInput) -> None:
        with self.db.cursor() as cur:
            cur.execute("""UPDATE transactions SET transaction_date=%s,description=%s,person_name=%s,kind=%s,amount=%s,settled=%s WHERE id=%s""",
                (values["date"],values["description"],values["person_name"],values["kind"],values["amount"],values.get("settled",False),transaction_id))

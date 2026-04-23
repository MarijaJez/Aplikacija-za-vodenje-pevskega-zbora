import psycopg2
import auth_public as auth
from models import oseba

class Repository:

    def __init__(self):
        # Ko ustvarimo novo instanco definiramo objekt za povezavo in cursor
        self.conn = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def dobi_osebo(id: int) -> oseba:
        pass

    def dobi_osebe () -> list(oseba):
        pass
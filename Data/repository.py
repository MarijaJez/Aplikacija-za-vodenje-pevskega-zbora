import psycopg2
import psycopg2.extras
from Data import auth_public as auth

class Repository:

    def __init__(self):
        # Ko ustvarimo novo instanco definiramo objekt za povezavo in cursor
        self.conn = psycopg2.connect(
            database=auth.database,
            host=auth.host,
            user=auth.user,
            password=auth.password,
            port=auth.port
        )
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if hasattr(self, 'cur') and self.cur is not None:
            self.cur.close()
        if hasattr(self, 'conn') and self.conn is not None:
            self.conn.close()

    def _normalize_row(self, row):
        if row is None:
            return None
        normalized = {}
        for key, value in dict(row).items():
            if hasattr(value, 'isoformat'):
                normalized[key] = value.isoformat()
            else:
                normalized[key] = value
        return normalized

    def _fetch_one(self):
        row = self.cur.fetchone()
        return self._normalize_row(row)

    def _fetch_all(self):
        rows = self.cur.fetchall()
        return [self._normalize_row(row) for row in rows]

    def dobi_osebo(self, id_osebe: int):
        self.cur.execute(
            'SELECT * FROM public.oseba WHERE id_osebe = %s;',
            (id_osebe,)
        )
        return self._fetch_one()

    def dobi_osebe(self):
        self.cur.execute(
            'SELECT * FROM public.oseba ORDER BY priimek, ime;'
        )
        return self._fetch_all()

    def dobi_osebe_razsirjeno(self):
        self.cur.execute(
            'SELECT o.*, g.naziv_glasu AS glas, v.naziv AS vloga '
            'FROM public.oseba o '
            'LEFT JOIN public.glasovi g ON o.id_glasu = g.id_glasu '
            'LEFT JOIN public.vloge v ON o.id_vloge = v.id_vloge '
            'ORDER BY o.priimek, o.ime;'
        )
        return self._fetch_all()

    def dobi_dogodke(self):
        self.cur.execute(
            'SELECT * FROM public.dogodek ORDER BY datum DESC;'
        )
        return self._fetch_all()

    def dobi_dogodek(self, id_dogodka: int):
        self.cur.execute(
            'SELECT * FROM public.dogodek WHERE id_dogodka = %s;', (id_dogodka,)
        )
        return self._fetch_one()

    def dobi_program_dogodka(self, id_dogodka: int):
        self.cur.execute(
            'SELECT p.*, pesem.naslov, pesem.avtor, pesem.note '
            'FROM public.program p '
            'LEFT JOIN public.pesem pesem ON p.id_pesmi = pesem.id_pesmi '
            'WHERE p.id_dogodka = %s '
            'ORDER BY p.vrstni_red;',
            (id_dogodka,)
        )
        return self._fetch_all()

    def dobi_prisotnost_dogodka(self, id_dogodka: int):
        self.cur.execute(
            'SELECT pr.*, o.ime, o.priimek, o.id_glasu, o.id_vloge '
            'FROM public.prisotnost pr '
            'JOIN public.oseba o ON pr.id_osebe = o.id_osebe '
            'WHERE pr.id_dogodka = %s '
            'ORDER BY o.priimek, o.ime;',
            (id_dogodka,)
        )
        return self._fetch_all()

    def dobi_pesmi(self):
        self.cur.execute(
            'SELECT * FROM public.pesem ORDER BY naslov;'
        )
        return self._fetch_all()

    def dobi_pesmi_z_kategorijami(self):
        self.cur.execute(
            'SELECT p.*, '
            'string_agg(k.naziv, \' , \' ORDER BY k.naziv) AS kategorije '
            'FROM public.pesem p '
            'LEFT JOIN public.pesem_kategorija pk ON pk.id_pesmi = p.id_pesmi '
            'LEFT JOIN public.kategorije k ON k.id_kategorije = pk.id_kategorije '
            'GROUP BY p.id_pesmi '
            'ORDER BY p.naslov;'
        )
        return self._fetch_all()

    def dobi_pesmi_po_kategoriji(self, id_kategorije: int):
        self.cur.execute(
            'SELECT p.*, '
            'string_agg(k.naziv, \' , \' ORDER BY k.naziv) AS kategorije '
            'FROM public.pesem p '
            'LEFT JOIN public.pesem_kategorija pk ON pk.id_pesmi = p.id_pesmi '
            'LEFT JOIN public.kategorije k ON k.id_kategorije = pk.id_kategorije '
            'WHERE p.id_pesmi IN (SELECT id_pesmi FROM public.pesem_kategorija WHERE id_kategorije = %s) '
            'GROUP BY p.id_pesmi '
            'ORDER BY p.naslov;'
            , (id_kategorije,)
        )
        return self._fetch_all()

    def dobi_pesem(self, id_pesmi: int):
        self.cur.execute(
            'SELECT p.*, '
            'string_agg(k.naziv, \' , \' ORDER BY k.naziv) AS kategorije '
            'FROM public.pesem p '
            'LEFT JOIN public.pesem_kategorija pk ON pk.id_pesmi = p.id_pesmi '
            'LEFT JOIN public.kategorije k ON k.id_kategorije = pk.id_kategorije '
            'WHERE p.id_pesmi = %s '
            'GROUP BY p.id_pesmi;'
            , (id_pesmi,)
        )
        return self._fetch_one()

    def dobi_kategorije(self):
        self.cur.execute(
            'SELECT * FROM public.kategorije ORDER BY naziv;'
        )
        return self._fetch_all()

    def dobi_vloge(self):
        self.cur.execute(
            'SELECT * FROM public.vloge ORDER BY naziv;'
        )
        return self._fetch_all()

    def dobi_glasove(self):
        self.cur.execute(
            'SELECT * FROM public.glasovi ORDER BY naziv_glasu;'
        )
        return self._fetch_all()

    def dobi_prisotnost(self, id_dogodka: int = None):
        if id_dogodka is None:
            self.cur.execute('SELECT * FROM public.prisotnost ORDER BY id_dogodka, id_osebe;')
        else:
            self.cur.execute(
                'SELECT * FROM public.prisotnost WHERE id_dogodka = %s ORDER BY id_osebe;',
                (id_dogodka,)
            )
        return self._fetch_all()

    def dobi_program(self, id_dogodka: int = None):
        if id_dogodka is None:
            self.cur.execute('SELECT * FROM public.program ORDER BY id_dogodka, vrstni_red;')
        else:
            self.cur.execute(
                'SELECT * FROM public.program WHERE id_dogodka = %s ORDER BY vrstni_red;',
                (id_dogodka,)
            )
        return self._fetch_all()

    def dobi_ocene(self, id_pesmi: int = None):
        if id_pesmi is None:
            self.cur.execute('SELECT * FROM public.ocene_pesmi ORDER BY id_osebe, id_pesmi;')
        else:
            self.cur.execute(
                'SELECT * FROM public.ocene_pesmi WHERE id_pesmi = %s ORDER BY id_osebe;',
                (id_pesmi,)
            )
        return self._fetch_all()

    def shrani_prisotnost(self, id_dogodka: int, id_osebe: int, prisotnost: bool):
        self.cur.execute(
            'INSERT INTO public.prisotnost (id_dogodka, id_osebe, prisotnost) VALUES (%s, %s, %s) '
            'ON CONFLICT (id_dogodka, id_osebe) DO UPDATE SET prisotnost = EXCLUDED.prisotnost;',
            (id_dogodka, id_osebe, prisotnost)
        )
        self.conn.commit()

    def shrani_oceno_pesmi(self, id_osebe: int, id_pesmi: int, ocena: int, komentar: str):
        self.cur.execute(
            'INSERT INTO public.ocene_pesmi (id_osebe, id_pesmi, ocena, komentar) VALUES (%s, %s, %s, %s) '
            'ON CONFLICT (id_osebe, id_pesmi) DO UPDATE SET ocena = EXCLUDED.ocena, komentar = EXCLUDED.komentar;',
            (id_osebe, id_pesmi, ocena, komentar)
        )
        self.conn.commit()

    def shrani_osebo(self, oseba_data: dict):
        self.cur.execute(
            'INSERT INTO public.oseba (ime, priimek, datum_rojstva, eposta, telefonska_stevilka, id_glasu, id_vloge) '
            'VALUES (%(ime)s, %(priimek)s, %(datum_rojstva)s, %(eposta)s, %(telefonska_stevilka)s, %(id_glasu)s, %(id_vloge)s) '
            'RETURNING id_osebe;',
            oseba_data
        )
        new_id = self.cur.fetchone()[0]
        self.conn.commit()
        return new_id

    def posodobi_osebo(self, id_osebe: int, oseba_data: dict):
        self.cur.execute(
            'UPDATE public.oseba SET ime = %(ime)s, priimek = %(priimek)s, datum_rojstva = %(datum_rojstva)s, '
            'eposta = %(eposta)s, telefonska_stevilka = %(telefonska_stevilka)s, id_glasu = %(id_glasu)s, id_vloge = %(id_vloge)s '
            'WHERE id_osebe = %(id_osebe)s;',
            {**oseba_data, 'id_osebe': id_osebe}
        )
        self.conn.commit()
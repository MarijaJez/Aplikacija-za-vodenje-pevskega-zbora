-- Ta datoteka vsebuje vse potrebne create ukaze,
-- s katerimi lahko ustvarimo bazo od začetka.

-- Najprej izbrišemo obstoječe tabele, če obstajajo (v obratnem vrstnem redu odvisnosti)
DROP TABLE IF EXISTS public.ocene_pesmi CASCADE;
DROP TABLE IF EXISTS public.pesem_kategorija CASCADE;
DROP TABLE IF EXISTS public.program CASCADE;
DROP TABLE IF EXISTS public.prisotnost CASCADE;
DROP TABLE IF EXISTS public.dogodek CASCADE;
DROP TABLE IF EXISTS public.oseba CASCADE;
DROP TABLE IF EXISTS public.glasovi CASCADE;
DROP TABLE IF EXISTS public.vloge CASCADE;
DROP TABLE IF EXISTS public.kategorije CASCADE;
DROP TABLE IF EXISTS public.pesem CASCADE;

-- Tabela za vloge
CREATE TABLE IF NOT EXISTS public.vloge (
    id_vloge SERIAL PRIMARY KEY,
    naziv VARCHAR(100) NOT NULL,
    opis TEXT
);

-- Tabela za glasovi (šifrant)
CREATE TABLE IF NOT EXISTS public.glasovi (
    id_glasu SERIAL PRIMARY KEY,
    naziv_glasu VARCHAR(50) NOT NULL UNIQUE
);

-- Tabela za osebe
CREATE TABLE IF NOT EXISTS public.oseba (
    id_osebe SERIAL PRIMARY KEY,
    ime VARCHAR(100) NOT NULL,
    priimek VARCHAR(100) NOT NULL,
    datum_rojstva DATE,
    eposta VARCHAR(255),
    telefonska_stevilka VARCHAR(20),
    id_glasu INTEGER REFERENCES public.glasovi(id_glasu),
    delitev_na_3 INTEGER, -- kateri glas poje, če se spol te osebe deli na 3 dele
    delitev_na_4 INTEGER, -- kateri glas poje, če se spol te osebe deli na 4 dele
    id_vloge INTEGER REFERENCES public.vloge(id_vloge)
);

-- Tabela za dogodke
CREATE TABLE IF NOT EXISTS public.dogodek (
    id_dogodka SERIAL PRIMARY KEY,
    datum DATE NOT NULL,
    vrsta_dogodka VARCHAR(100),
    naziv_dogodka VARCHAR(255) NOT NULL
);

-- Tabela za prisotnost
CREATE TABLE IF NOT EXISTS public.prisotnost (
    id_dogodka INTEGER REFERENCES public.dogodek(id_dogodka),
    id_osebe INTEGER REFERENCES public.oseba(id_osebe),
    prisotnost BOOLEAN NOT NULL,
    PRIMARY KEY (id_dogodka, id_osebe)
);

-- Tabela za pesmi
CREATE TABLE IF NOT EXISTS public.pesem (
    id_pesmi SERIAL PRIMARY KEY,
    naslov VARCHAR(255) NOT NULL,
    avtor VARCHAR(255),
    note TEXT
);

-- Tabela za program dogodka (povezava med dogodki in pesmimi)
CREATE TABLE IF NOT EXISTS public.program (
    id_dogodka INTEGER REFERENCES public.dogodek(id_dogodka),
    id_pesmi INTEGER REFERENCES public.pesem(id_pesmi),
    ocena INTEGER,
    komentar TEXT,
    PRIMARY KEY (id_dogodka, id_pesmi)
);

-- Tabela za kategorije
CREATE TABLE IF NOT EXISTS public.kategorije (
    id_kategorije SERIAL PRIMARY KEY,
    naziv VARCHAR(100) NOT NULL,
    opis TEXT
);

-- Tabela za povezavo pesmi in kategorij (N:M)
CREATE TABLE IF NOT EXISTS public.pesem_kategorija (
    id_pesmi INTEGER REFERENCES public.pesem(id_pesmi),
    id_kategorije INTEGER REFERENCES public.kategorije(id_kategorije),
    PRIMARY KEY (id_pesmi, id_kategorije)
);

-- Tabela za ocene pesmi
CREATE TABLE IF NOT EXISTS public.ocene_pesmi (
    id_osebe INTEGER REFERENCES public.oseba(id_osebe),
    id_pesmi INTEGER REFERENCES public.pesem(id_pesmi),
    ocena INTEGER CHECK (ocena >= 1 AND ocena <= 5),
    komentar TEXT,
    PRIMARY KEY (id_osebe, id_pesmi)
);
# Aplikacija za vodenje pevskega zbora
Projekt pri predmetu Osnove podatkovnih baz.

## Namen aplikacije
Aplikacija upravlja pevskega zbora in podpira:
- zbiranje podatkov o članih zbora
- beleženje pevskih vaj, prisotnosti in nastopov
- baza programa zbora in beleženje dogodkov
- različne vloge uporabnikov z različnimi pravicami

## Struktura projekta
Projekt je razdeljen na tri glavne sloje, po načelih "clean architecture":

- `Data/` - podatkovni nivo
  - `create_database.sql` - SQL skripta za ustvarjanje sheme
  - `populate_database.sql` - skripta za vstavljanje začetnih (mock) podatkov
  - `models.py` - Python `dataclass` modeli, ki predstavljajo tabele
  - `repository.py` - repo sloj z metodami za poizvedbe in spremembe v bazi
  - `auth_public.py` - nastavitve za povezavo do PostgreSQL

- `Services/` - aplikacijski nivo
  - `oseba_service.py` - poslovna logika za osebe, vloge in glasove
  - `dogodek_service.py` - logika za dogodke, prisotnost, program in ocene
  - `pesem_service.py` - logika za pesmi, kategorije in ocene
  - `auth_service.py` - preproste metode za preverjanje vlog in avtorizacijo

- `Presentation/` - predstavitveni nivo
  - tukaj bo aplikacija prikazana uporabniku preko spletnega vmesnika
  - `views/` - HTML predloge za posamezne strani
  - `static/` - CSS/JS/ikonice

## Podatkovna baza in tabele
Aplikacija uporablja PostgreSQL bazo z naslednjimi tabelami:

- `vloge`
  - `id_vloge`, `naziv`, `opis`
  - primeri: `admin`, `pevec`, `skrbnik prisotnosti`

- `glasovi`
  - `id_glasu`, `naziv_glasu`
  - primeri: `sopran`, `alt`, `tenor`, `bas`

- `oseba`
  - `id_osebe`, `ime`, `priimek`, `datum_rojstva`, `eposta`, `telefonska_stevilka`, `id_glasu`, `id_vloge`
  - vsak član ima pripadajoč glas in vlogo

- `dogodek`
  - `id_dogodka`, `datum`, `vrsta_dogodka`, `naziv_dogodka`
  - vrste dogodkov: pevska vaja, letni koncert, zborov izlet

- `prisotnost`
  - `id_dogodka`, `id_osebe`, `prisotnost`
  - beleži prisotnost člana na dogodku

- `pesem`
  - `id_pesmi`, `naslov`, `avtor`, `note`
  - `note` vsebuje referenco na PDF notnega gradiva

- `program`
  - `id_dogodka`, `id_pesmi`, `ocena`, `komentar`
  - pove, katere pesmi so na programu posameznega dogodka

- `kategorije`
  - `id_kategorije`, `naziv`, `opis`
  - primeri: `slovenske ljudske`, `filmska glasba`, `sakralna glasba`, `popularna glasba`

- `pesem_kategorija`
  - `id_pesmi`, `id_kategorije`
  - N:M povezava med pesmimi in kategorijami

- `ocene_pesmi`
  - `id_osebe`, `id_pesmi`, `ocena`, `komentar`
  - člani ocenjujejo pesmi za interne potrebe

## Funkcionalnosti uporabniškega vmesnika
Front-end bo ponujal glavne strani (zavihke):

1. `Domov`
   - kratek pregled sistema in dostop do glavnih modulov

2. `Člani`
   - seznam vseh članov zbora
   - osnovni podatki: ime, priimek, e-pošta, telefon, glas, vloga
   - možnost ogleda podrobnosti posameznega člana
   - urejanje uporabniških vlog (to lahko ureja le tisti z vlogo "admin")
   - dodajanje novih članov in urejanje obstoječih omogočeno adminu in zborovodji

3. `Dogodki`
   - seznam (tabela) prihodnjih in preteklih dogodkov
   - vrsta, naziv dogodka in datum, program, povzetek statistik prisotnosti
   - klik na vrstico odpre podrobnosti
   - dodajanje novih dogodkov in urejanje obstoječih omogočeno adminu in zborovodji

4. `Pesmi`
   - baza repertoarja zbora
   - prikaz naslova, avtorja in reference na PDF note (pdf se odpre ločeno, desno od tabele, ki se zoži)
   - možnost vnosa ocene in komentarja za pesmi (vsak pevec lahko oceni in komentira vsako pesem)
   - dodajanje novih pesmi in urejanje obstoječih omogočeno adminu in zborovodji
   - urejanje šifranta kategorij pesmi:
     - pregled in urejanje kategorij pesmi (šifrant)
     - filtriranje pesmi po kategoriji (opcijsko)

5. `Prisotnost`
   - tabela prisotnosti članov na posameznem dogodku
   - omogoča vnos ali posodobitev prisotnosti osebam z vlogo "skrbnik prisotnosti"

   

## Delovanje tabel in povezav
- `oseba` je centralna entiteta, ki se povezuje z `glasovi` in `vloge`.
- `dogodek` je dogodek, na katerem se spremlja prisotnost in izvedba pesmi.
- `prisotnost` povezuje `oseba` in `dogodek` v odnosu 1:N.
- `program` povezuje `dogodek` in `pesem`, torej kaj se bo pel na dogodku.
- `pesem_kategorija` povezuje pesmi s kategorijami za enostavno filtriranje.
- `ocene_pesmi` beleži subjektivne ocene pevcev za pesmi.

## Kako aplikacija deluje
1. `Presentation` sprejme HTTP zahtevek iz brskalnika.
2. `app.py` izbere ustrezno stran in kliče ustrezni servis iz `Services/`.
3. `Services/` izvede poslovno logiko in pokliče `Repository`.
4. `Data/repository.py` dostopa do PostgreSQL baze preko `psycopg2`.
5. Rezultati vrne `Services/`, ki jih predstavi `Presentation` v HTML pogledih.

## Tek tehnologij
- Python 3
- `psycopg2` za PostgreSQL
- `dataclasses` + `dataclasses_json` za modele
- `bottle` za preprost spletni predstavitveni nivo
- PostgreSQL kot baza podatkov

## Namestitev in zagon
1. Aktiviraj virtualno okolje:
   - `venv\Scripts\activate`
2. Namesti odvisnosti:
   - `pip install -r requirenments.txt`
3. Ustvari in napolni bazo:
   - `psql -h <host> -U <user> -d <database> -f Data/create_database.sql`
   - `psql -h <host> -U <user> -d <database> -f Data/populate_database.sql`
4. Zaženi aplikacijo:
   - `python app.py`
5. Obišči `http://localhost:8080`

## Nadaljnji razvoj
- dodaj prijavo in pravice glede na vloge
- omogoči urejanje članov, dogodkov in pesmi preko UI
- dodaj filtriranje po kategoriji in datumu
- razširi `presentation` z boljšo obliko in Javascript interaktivnostjo


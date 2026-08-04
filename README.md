# Aplikacija za upravljanje pevskega zbora

Spletna aplikacija za upravljanje pevskega zbora, izdelana s Python/Bottle in PostgreSQL. Omogoča prijavo, upravljanje članov, vlog in kategorij, program z notami, zvočnimi posnetki ter zgodovino izvedb, dogodke z ocenami izvedb, zaporednim predvajanjem in Google Calendar izvozom, ocene pesmi, filtrirano evidenco prisotnosti ter blagajno. Dostop do urejanja se preverja tako v uporabniškem vmesniku kot na strežniku.

## Zagon

Potrebujete Python 3.11+ in Docker Desktop.

```powershell
python -m pip install -r requirements.txt
docker compose -p zborissimo up -d --wait
python app.py
```

Aplikacija je nato na `http://127.0.0.1:8091/prijava`.

Za ponastavitev lokalne baze in ponovno nalaganje začetnih podatkov:

```powershell
docker compose -p zborissimo down --volumes
docker compose -p zborissimo up -d --wait
```

## Testni računi

- Predsednik: `luka.mlakar` / `zbor2026`
- Blagajnik: `ana.kovac` / `zbor2026`
- Ostali začetni računi imajo uporabniško ime in začetno geslo v obliki `ime.priimek`; ob prvi prijavi morajo geslo zamenjati.

Predsednik ali zborovodja ob dodajanju člana samodejno ustvari račun. Če je `ime.priimek` že zasedeno, sistem doda naslednje prosto naravno število. Predsednik in zborovodja lahko ponastavita geslo na uporabniško ime.

## Pregled baze s pgAdmin

pgAdmin se zažene skupaj z ostalimi Docker servisi in je dosegljiv na
`http://127.0.0.1:5050`.

Prijava v pgAdmin:

- e-pošta: `admin@example.com`
- geslo: `pgadmin_dev`

Ob prvi prijavi registrirajte povezavo prek **Servers → Register → Server**:

- Name: `Zbor`
- Host name/address: `db`
- Port: `5432`
- Maintenance database: `zborissimo`
- Username: `zborissimo`
- Password: `zborissimo_dev`

Tabele so pod **Servers → Zbor → Databases → zborissimo → Schemas → public → Tables**.
Ker pgAdmin teče v Docker omrežju, mora biti gostitelj `db` in ne `localhost`.

## Struktura

- `Data/` — PostgreSQL povezava, shema, začetni podatki in repozitorij
- `Services/` — poslovna pravila, avtentikacija in priprava podatkov
- `Presentation/` — Bottle poti, dovoljenja, predloge ter CSS/JavaScript
- `tests/` — integracijski preizkusi prijave, povezav, shranjevanja in dovoljenj

Smer odvisnosti je `Presentation → Services → Data`; SQL je omejen na podatkovni sloj.

## Preizkusi

Ko aplikacija in baza tečeta:

```powershell
python -m unittest tests.test_backend -v
```

Preizkusi prehodijo notranje povezave, preverijo zapis prisotnosti, glavne ustvarjalne tokove in prepoved administracije za uporabnika brez ustrezne vloge. Začasne testne zapise po izvedbi odstranijo.

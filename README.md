# Aplikacija za vodenje pevskega zbora

Spletna aplikacija na enem mestu združuje podatke o članih, programu, dogodkih, prisotnosti in blagajni pevskega zbora. Napisana je v Pythonu z ogrodjem Bottle, uporablja PostgreSQL in ima prijavo z vlogami ter različnimi uporabniškimi pravicami.

## Funkcionalnosti

### Uporabniški računi in pravice

- Prijava in odjava z uporabniškim imenom in geslom.
- Ob prvi prijavi mora novi član zamenjati začasno geslo, ki je sprva enako uporabniškemu imenu.
- Vsak uporabnik lahko pozneje zamenja svoje geslo; predsednik ali zborovodja ga lahko članu ponastavi.
- Pravice izhajajo iz vlog člana:
  - **Predsednik** in **Zborovodja** imata skrbniške pravice nad celotno aplikacijo.
  - **Notar** ureja pesmi in njihove kategorije.
  - **Beleženje prisotnosti** ureja prisotnost vseh članov.
  - **Blagajnik** dodaja in ureja transakcije.
  - **Zborovodja** ocenjuje izvedbe pesmi na dogodkih.
- Član brez posebne vloge lahko ureja svoje osebne podatke, ocenjuje pesmi in za prihodnje dogodke označi svojo prisotnost. Ostale vsebine so mu na voljo le za ogled.

### Nadzorna plošča - vstopna stran aplikacije

- Število aktivnih članov, razporeditev po glasovih in število pesmi.
- Povprečna prisotnost v tekočem šolskem letu ter lestvici članov z najvišjo in najnižjo prisotnostjo.
- Število prihajajočih dogodkov in časovnica preteklih ter prihodnjih dogodkov.
- Pregled nazadnje dodanih pesmi.

### Člani in vloge

- Seznam in iskanje članov ter filtriranje po vlogi.
- Podrobnosti člana: ime, priimek, datum rojstva, e-pošta, telefon, glas, vloge, uporabniško ime in prisotnost.
- Skrbnik lahko doda člana; aplikacija samodejno ustvari enolično uporabniško ime in uporabniški račun.
- Član lahko ureja svoje podatke, skrbnik pa podatke in vloge vseh članov.
- Skrbnik lahko izbriše drugega člana ali mu ponastavi geslo.
- Pregled, dodajanje, urejanje in varno brisanje vlog. Osnovne vloge `Član` ni mogoče izbrisati ali preimenovati, uporabljene vloge pa ni mogoče izbrisati.

### Program zbora

- Seznam pesmi z iskanjem po naslovu ali avtorju in filtriranjem po eni ali več kategorijah.
- Podrobnosti pesmi, povprečna ocena, komentarji članov in zgodovina izvedb.
- Pooblaščeni uporabnik lahko pesem doda, uredi ali izbriše ter ji določi kategorije.
- Nalaganje not v oblikah PDF, JPG, JPEG in PNG ter zvočnih posnetkov MP3, WAV, M4A in OGG.
- Predvajanje naloženega zvočnega posnetka.
- Upravljanje kategorij; uporabljene kategorije ni mogoče izbrisati.
- Vsak član lahko pesem oceni od 1 do 5 in doda komentar. Za posamezno pesem ima eno oceno, ki jo lahko pozneje spremeni.

### Vaje in dogodki

- Časovnica vseh preteklih in prihodnjih vaj, koncertov, nastopov in drugih dogodkov.
- Podrobnosti dogodka: datum in ura, vrsta, naziv, kraj, program ter povzetek prisotnosti.
- Skrbnik lahko dogodek doda, uredi ali izbriše ter določi pesmi v programu.
- Iskanje pesmi in filtriranje po kategorijah pri sestavljanju programa dogodka.
- Predvajanje vseh razpoložljivih zvočnih posnetkov programa kot seznama predvajanja.
- Zborovodja lahko izvedbo posamezne pesmi oceni od 1 do 5 in ji doda komentar.
- Dodajanje posameznega dogodka v Google Koledar ter izvoz vseh dogodkov v datoteko iCalendar (`.ics`).

### Prisotnost

- Evidenčna tabela s člani v vrsticah in dogodki v stolpcih.
- Statusi: ni evidentirano, prisoten, zamudil manj kot 10 minut, zamudil več kot 10 minut, opravičeno odsoten in odsoten.
- Pooblaščena oseba ureja prisotnost vseh članov; drugi člani lahko označijo le svojo prisotnost na prihodnjih dogodkih.
- Samodejno shranjevanje sprememb brez ponovnega nalaganja strani.
- Filtriranje po šolskem letu in skupini dogodkov.
- Seštevki po članih in dogodkih, povprečna prisotnost, najbolj reden glas ter grafi prisotnosti po glasovih.

### Blagajna

- Pregled vseh prihodkov in odhodkov.
- Povzetek skupnih prihodkov, odhodkov, trenutnega stanja in odprtih obveznosti.
- Blagajnik oziroma skrbnik lahko transakcijo doda ali uredi in jo označi kot odprto oziroma poravnano.

## Lokalni zagon

Potrebujete Python 3.10 ali novejši in dostop do PostgreSQL baze.

### 1. Virtualno okolje in knjižnice

V PowerShellu v korenski mapi projekta izvedite:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

V Linuxu ali macOS uporabite `source venv/bin/activate` namesto ukaza za aktivacijo v PowerShellu.

### 2. Povezava z bazo in sejni ključ

Aplikacija privzeto uporablja bazo `opb2026_marijaj` na strežniku `baza.fmf.uni-lj.si` prek zahtevanega uporabnika `javnost`. V okolje vnesite geslo tega uporabnika in naključni sejni ključ; gesel ne zapisujte v repozitorij.

```powershell
$env:DB_PASSWORD = "GESLO_UPORABNIKA_JAVNOST"
$env:COOKIE_SECRET = "DOLG_NAKLJUCEN_NIZ"
```

Vrednost za `COOKIE_SECRET` lahko ustvarite z:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Po potrebi lahko posamezne privzete vrednosti spremenite:

```powershell
$env:DB_HOST = "baza.fmf.uni-lj.si"
$env:DB_PORT = "5432"
$env:DB_NAME = "opb2026_marijaj"
$env:DB_USER = "javnost"
```

Namesto spremenljivk `DB_*` lahko nastavite celoten povezovalni niz:

```powershell
$env:DATABASE_URL = "postgresql://javnost:GESLO@baza.fmf.uni-lj.si:5432/opb2026_marijaj"
```

### 3. Zagon aplikacije

```powershell
python app.py
```

Aplikacija je dosegljiva na [http://127.0.0.1:8080](http://127.0.0.1:8080). Gostitelja in vrata lahko spremenite s `APP_HOST` in `APP_PORT`. Razvojni način s samodejnim ponovnim zagonom vključite z:

```powershell
$env:APP_DEBUG = "true"
```

### Razvojna prijava

V aplikaciji so testni podatki, vključno z uporabniškimi računi. Za prijavo lahko uporabite uporabnika z vsemi pravicami:

- uporabniško ime: `luka.mlakar`
- geslo: `zbor2026`


## Struktura projekta

- `app.py` – vstopna točka aplikacije;
- `Presentation/` – spletne poti, predloge, JavaScript in slogi;
- `Services/` – poslovna pravila, prijava in dovoljenja;
- `Data/` – povezava z bazo, podatkovni modeli, poizvedbe ter SQL za shemo in razvojne podatke;
- `uploads/` – lokalno shranjene note in zvočni posnetki (vsebina ni vključena v Git);
- `shema.pdf` in `shema.drawio` – podatkovni model baze.

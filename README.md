# APLIKACIJA ZA VODENJE PEVSKEGA ZBORA
Aplikacija za vodenje pevskega zbora omogoča zbiranje in urejanje administrativnih podatkov, potrebnih za vodenje pevskega zbora, na enem mestu.

## ZAHTEVE:
Aplikacija omogoča naslednje funkcionalnosti:
- Vsak član zbora ima svoje uporabniško ime in geslo, s katerima lahko dostopa do aplikacije
- Pregled in urejanje baze članov zbora
- Pregled in urejanje baze programa zbora
- Pregled in urejanje baze vaj in dogodkov, na katerih je zbor sodeloval
- Pregled in beleženje prisotnosti članov zbora na dogodkih
- Vsak član zbora lahko oceni in komentira vsako pesem v bazi programa zbora


## STRUKTURA APLIKACIJE:

### Vstopna stran: Nadzorna plošča
Stran vsebuje več okvirčkov, ki vsebujejo naslednje podatke:
- Pregled osnovnih podatkov o članih zbora
    - Število članov zbora
    - Število članov posameznih glasov
    - Top 3 člani zbora glede na prisotnost v zadnjem mesecu in worst 3
- Pregled osnovnih podatkov o programu zbora
    - Število pesmi v programu
    - Zadnje 3 dodane pesmi v program
    - 3 pesmi, ki jih že najdlje nismo peli na dogodkih
- Časovnica:
    - Pregled zadnjih dogodkov (datum in naziv dogodka) - vizualno drugače od prihajajočih dogodkov
    - Pregled prihajajočih vaj in dogodkov (datum in naziv dogodka)
- Hiter pregled prisotnosti članov
    - Seznam vseh članov zbora s skupnim seštevkom prisotnosti v tekočem šolskem letu (od septembra naprej), urejeni padajoče

### Stran: Člani zbora

Modul omogoča pregled in urejanje baze članov.

Funkcionalnosti:

Seznam vseh članov
Dodajanje novega člana
Urejanje podatkov člana (vključno z določanjem ene ali več vlog člana v zboru)
Brisanje člana
Pregled podrobnosti posameznega člana
Pregled prisotnosti člana na dogodkih

Podatki:

Ime
Priimek
Datum rojstva
E-pošta
Telefonska številka
Glas
Vloga oziroma vloge v zboru

#### Funkcionalnost: Vloge v zboru

Modul za upravljanje vlog članov.

Funkcionalnosti:

Pregled vlog
Dodajanje nove vloge
Urejanje vloge
Brisanje vloge
Pregled članov z določeno vlogo

### Stran: Program zbora

Modul omogoča pregled in urejanje baze pesmi.

Funkcionalnosti:

Seznam vseh pesmi
Dodajanje nove pesmi
Urejanje pesmi (vključno z dodajanjem pdf/jpg/jpeg/png not, določanjem ene ali več kategorij pesmi, všečkanjem in komentiranjem pesmi)
Brisanje pesmi
Pregled podrobnosti pesmi
Pregled ocen in komentarjev članov
Filtriranje seznama glede na posamezno kategorijo pesmi

Podatki:

Naslov
Avtor
Note
Kategorija oziroma kategorije
Povprečna ocena
Komentarji članov

#### FUnkcionalnost: Ocene in komentarji pesmi

Modul omogoča članom zbora ocenjevanje in komentiranje pesmi.

Funkcionalnosti:

Pregled vseh pesmi
Ocena posamezne pesmi
Dodajanje komentarja
Urejanje lastne ocene in komentarja
Pregled povprečne ocene pesmi
Pregled komentarjev članov

Pravila:

Vsak član lahko posamezno pesem oceni največ enkrat.
Član lahko svojo oceno in komentar kasneje spremeni.
Ocena mora biti v vnaprej določenem območju, 1–5.
Pri vsaki pesmi se prikaže povprečna ocena vseh članov.

### Stran: Vaje in dogodki

Modul omogoča upravljanje vaj in dogodkov, na katerih sodeluje oziroma je sodeloval zbor.

Funkcionalnosti:

Pregled vseh vaj in dogodkov (časovnica)
Dodajanje novega dogodka
Urejanje dogodka (vključno z določanjem vrste dogodka in določanjem pesmi, ki so bile izvedene na dogodku)
Brisanje dogodka
Pregled podrobnosti dogodka
Pregled prisotnosti članov na dogodku

Podatki:

Datum
Vrsta dogodka
Naziv dogodka
Program dogodka

#### Program dogodka

Podmodul za določanje programa posameznega dogodka.

Funkcionalnosti:

Dodajanje pesmi na dogodek
Odstranjevanje pesmi z dogodka
Pregled pesmi, izvedenih na dogodku
Beleženje ocene izvedbe pesmi
Dodajanje komentarja k izvedbi pesmi

### Stran: Prisotnost

Modul za beleženje prisotnosti članov na vajah in dogodkih.

Funkcionalnosti:

Pregled prisotnosti : tabela z vrsticami člani in stolpci dogodki
Označevanje prisotnosti posameznega člana
Urejanje že zabeležene prisotnosti
Pregled statistike prisotnosti: po vrsti dogodka, glasu, osebi

Možne vrednosti:

Prisoten
Odsoten
Opravičeno odsoten
Zamudil manj kot 10 min
Zamudil več kot 10 min

### Stran: Blagajna zbora

Modul za beleženje transakcij v in iz zborovske blagajne.

Funkcionalnosti:

Pregled seznama transakcij.
Dodajanje novih in urejanje starih transakcij.
Hitro označevanje, ali je transakcija odprta ali poravnana.
Pregled povzetka stanja blagajne.

## ZAGON APLIKACIJE

### 1. Priprava virtualnega okolja

V PowerShellu v korenski mapi projekta izvedi:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirenments.txt
```

### 2. Nastavitev povezave z bazo in sejnega ključa

Geslo baze ni zapisano v kodi, ampak se aplikaciji poda z okoljsko spremenljivko. Za razvojno bazo z že nastavljenimi privzetimi podatki za ime baze, gostitelja in uporabnika zadošča:

```powershell
$env:DB_PASSWORD = "ldbp4hlh"
$env:COOKIE_SECRET = "DOLG_NAKLJUCEN_NIZ"
```

Naključni sejni ključ lahko ustvariš z ukazom:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Namesto `DB_PASSWORD` je mogoče nastaviti celoten povezovalni niz:

```powershell
$env:DATABASE_URL = "postgresql://UPORABNIK:GESLO@GOSTITELJ:5432/BAZA"
```

### 3. Priprava prazne baze

V novi prazni bazi najprej izvedi `Data/create_database.sql`, nato pa enkrat še `Data/populate_database.sql`, ki doda razvojne podatke.

### 4. Zagon

```powershell
python app.py
```

Aplikacija je nato dosegljiva na `http://127.0.0.1:8080`.

Za razvojni način s samodejnim ponovnim zagonom lahko pred zagonom nastaviš:

```powershell
$env:APP_DEBUG = "true"
```

### Razvojna prijava

- Uporabniško ime: `luka.mlakar`
- Geslo: `zbor2026`

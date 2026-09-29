# Aplikacija za upravljanje pevskega zbora

Spletna aplikacija Python/Bottle in PostgreSQL za člane, program, dogodke, prisotnost ter blagajno. Podpira obstoječo prijavo z uporabniškim imenom in geslom, prijavo z Googlom, enosmerno sinhronizacijo dogodkov v osebne Google Koledarje članov in namestitev na domači zaslon kot PWA.

## Lokalni zagon

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

Če baza že obstaja, pred zagonom nove različice uporabi migracijo (podatki članov, vloge in prisotnosti se ohranijo):

```powershell
python -m Data.migrate
```

Migracija pred spremembo preveri podvojene e-poštne naslove brez upoštevanja velikosti črk. Če jih najde, se varno ustavi; naslove je treba najprej popraviti. Nato obstoječe naslove normalizira in doda case-insensitive unikatno omejitev.

## Google Cloud nastavitev

Skrivnosti ne sodijo v repozitorij. Kopiraj `.env.example` v lokalno `.env` oziroma iste spremenljivke nastavi v okolju strežnika. Aplikacija `.env` ne nalaga sama; pri lokalnem zagonu jih lahko naloži upravljalnik procesa ali PowerShell.

1. V [Google Cloud Console](https://console.cloud.google.com/) ustvari ali izberi projekt.
2. V **APIs & Services → Library** omogoči **Google Calendar API**.
3. Nastavi **OAuth consent screen**. Med preizkušanjem dodaj zborovski račun in članske račune med testne uporabnike; za produkcijo dokončaj objavo oziroma preverjanje, ki ga zahteva Google.
4. Ustvari poverilnico **OAuth client ID → Web application**.
5. Med **Authorized redirect URIs** dodaj obe natančni poti:
   - lokalno: `http://127.0.0.1:8091/prijava/google/povratni-klic`
   - lokalno: `http://127.0.0.1:8091/nastavitve/google-koledar/povratni-klic`
   - za produkcijo dodaj isti poti na dejanski HTTPS domeni.
6. Na strežniku nastavi:

```text
APP_BASE_URL=https://zbor.example.si
APP_TIMEZONE=Europe/Ljubljana
COOKIE_SECURE=true
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_LOGIN_REDIRECT_URI=https://zbor.example.si/prijava/google/povratni-klic
GOOGLE_CALENDAR_REDIRECT_URI=https://zbor.example.si/nastavitve/google-koledar/povratni-klic
GOOGLE_TOKEN_ENCRYPTION_KEY=...
```

Ključ za šifriranje Google žetonov ustvari enkrat in ga varno shrani skupaj z drugimi produkcijskimi skrivnostmi:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Če ključ izgubiš ali ga zamenjaš, obstoječe koledarske povezave ni mogoče dešifrirati in jo mora pooblaščeni uporabnik povezati znova.

### Prijava članov z Googlom

Zborovodja ali predsednik člana najprej doda v aplikacijo z veljavnim in enoličnim e-poštnim naslovom. Ob prvi Google prijavi strežnik preveri podpis, izdajatelja, občinstvo, potek, nonce in Googlov podatek `email_verified`. Lokalni račun poišče izključno po normaliziranem potrjenem e-poštnem naslovu; imena in priimka ne uporablja. Google subject se nato trajno poveže z istim uporabnikom.

Če e-pošte ni med člani, se račun ne ustvari samodejno. Obstoječi uporabniki lahko še naprej uporabljajo svoja dosedanja uporabniška imena in gesla. Novi članski račun dobi naključno, uporabniku nerazkrito vrednost gesla in se prijavlja z Googlom; po Google prijavi si lahko član v uporabniškem meniju po želji nastavi tudi zasebno geslo za rezervno prijavo. Aplikacija ne ustvarja več gesel iz imena ali priimka.

### Osebni Google Koledarji članov

Vsak član odpre **Vaje in dogodki → Moj koledar** in poveže svoj Google račun. E-pošta Google računa se mora ujemati z e-pošto članskega računa. Odobri samo dovoljenje za dogodke na koledarjih v svoji lasti (`calendar.events.owned`); aplikacija ne izbira ali upravlja drugih koledarjev.

Po odobritvi se obstoječi zborovski dogodki dodajo v članov glavni Google Koledar. Nadaljnje ustvarjanje, urejanje in brisanje se prenese v koledarje vseh povezanih članov. Povezava starega zborovskega računa ni samodejno prenesena v osebne povezave; vsak član mora povezavo odobriti sam.

Sinhronizacija je samo v smeri aplikacija → Google; spremembe v Googlu se ne uvozijo nazaj. Vsak par člana in dogodka ima stabilen Google ID, zato ponovni poskus ne ustvari dvojnika. Trenutni podatkovni model nima ponavljajočih se dogodkov, zato se vsak zapis sinhronizira kot samostojen dvourni dogodek.

Če Google API začasno odpove ali član prekliče dovoljenje, sprememba v aplikaciji ostane shranjena. Napaka je vidna v nastavitvah in član lahko po ponovni povezavi sproži ponoven prenos. Neuspeli izbrisi so v čakalni vrsti. Prekinitev povezave ne izbriše že dodanih dogodkov iz Googla.

### Potisna obvestila

Član lahko obvestila o novih, spremenjenih in odpovedanih dogodkih ter o novih sporočilih v klepetu vključi v uporabniškem meniju. Tam lahko pošlje preizkusno obvestilo in naročnino pozneje izključi. Brskalnik mora podpirati Web Push, stran pa mora biti odprta prek HTTPS. Za strežnik nastavite `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY_FILE` (pot do zasebnega ključa PEM) in `VAPID_CONTACT_EMAIL`; brez teh nastavitev je stikalo za obvestila onemogočeno. Obvestila o klepetu ne vsebujejo besedila sporočila.

### Zasebna galerija in klepet

Vsak dogodek ima album, ki ga lahko vidijo prijavljeni člani. Fotografije nalagajo in brišejo pooblaščeni uporabniki; slika je omejena na 8 MB, pred shranjevanjem se pretvori v JPEG in odstrani metapodatke. Naložite samo fotografije z dovoljenjem za deljenje med člani. Skupinski klepet omogoča zadnjih 100 sporočil, urejanje in izbris lastnih sporočil ter skrbniško moderiranje. Novo sporočilo lahko naročenim članom pošlje splošno potisno obvestilo.

## Namestitev na telefon (PWA)

V brskalniku odpri produkcijsko HTTPS stran:

- Android/Chrome: meni → **Namesti aplikacijo** ali **Dodaj na začetni zaslon**.
- iPhone/Safari: **Deli** → **Add to Home Screen / Dodaj na domači zaslon**.

PWA ima samostojni prikaz, barve in ikono. Service worker predpomni statične datoteke aplikacijske lupine. Članski podatki, dogodki in prisotnost brez povezave niso na voljo; namesto zastarelih podatkov se pokaže jasen zaslon brez povezave.

## Testni računi za lokalne začetne podatke

- Predsednik: `luka.mlakar` / `zbor2026`
- Blagajnik: `ana.kovac` / `zbor2026`

To so samo lokalni začetni podatki iz `Data/seed.sql`, ne produkcijske poverilnice.

## Pregled baze s pgAdmin

pgAdmin je na `http://127.0.0.1:5050`. Lokalna prijava je `admin@example.com` / `pgadmin_dev`. Pri registraciji strežnika uporabi gostitelja `db`, vrata `5432`, bazo in uporabnika `zborissimo` ter lokalno geslo `zborissimo_dev`.

## Struktura

- `Data/` — PostgreSQL povezava, shema, migracije, začetni podatki in repozitorij
- `Services/` — poslovna pravila, preverjanje identitete in Google Calendar odjemalec
- `Presentation/` — Bottle poti, dovoljenja, predloge, PWA, CSS in JavaScript
- `tests/` — integracijski in enotski preizkusi

Smer odvisnosti ostaja `Presentation → Services → Data`; SQL je omejen na podatkovni sloj.

## Preizkusi

Ko aplikacija in baza tečeta:

```powershell
python -m unittest discover -s tests -v
```

Google enotski testi uporabljajo nadomestne odgovore in ne potrebujejo pravih Google skrivnosti. Integracijski testi prehodijo notranje povezave, preverijo zapis podatkov in dovoljenja ter začasne zapise odstranijo.

<!doctype html>
<html lang="sl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#163a45">
  <title>{{title}} · Upravljanje zbora</title>
  <meta name="description" content="Upravljanje zbora – spletna aplikacija Mladinskega pevskega zbora Homec za organizacijo članov, programa in dogodkov.">
  <link rel="icon" href="/static/icons/icon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/static/public.css?v=1">
</head>
<body class="public-page">
  <header class="public-header">
    <a class="public-brand" href="/o-aplikaciji"><span aria-hidden="true">𝄞</span> Upravljanje zbora</a>
    <nav aria-label="Javne informacije">
      <a class="{{'active' if section == 'about' else ''}}" href="/o-aplikaciji">O aplikaciji</a>
      <a class="{{'active' if section == 'privacy' else ''}}" href="/zasebnost">Zasebnost</a>
      <a class="{{'active' if section == 'terms' else ''}}" href="/pogoji-uporabe">Pogoji uporabe</a>
    </nav>
  </header>
  <main class="public-main">
  % if section == 'about':
    <p class="eyebrow">{{organization}}</p>
    <h1>Aplikacija za vodenje pevskega zbora</h1>
    <p class="lead">Eno mesto za delo zbora: člane, glasbeni program, vaje, nastope, prisotnost in blagajno.</p>
    <div class="public-actions"><a class="primary-link" href="/prijava">Prijava za člane</a><a href="mailto:{{contact_email}}">Pišite zboru</a></div>
    <section class="feature-grid" aria-label="Funkcije aplikacije">
      <article><h2>Člani in naloge</h2><p>Pooblaščeni uporabniki vodijo seznam članov, glasove in vloge. Vsak uporabnik vidi funkcije, do katerih ima dostop.</p></article>
      <article><h2>Glasbeni program</h2><p>Zbor zbira skladbe, kategorije, note in zvočne posnetke za svoje delo.</p></article>
      <article><h2>Vaje in dogodki</h2><p>Načrtovanje dogodkov, beleženje prisotnosti in izvoz koledarja. Dogodke je mogoče prenesti v izbrani zborovski Google Koledar.</p></article>
      <article><h2>Blagajna</h2><p>Pooblaščeni uporabniki beležijo prihodke, odhodke in poravnave.</p></article>
    </section>
    <section class="public-note"><h2>Dostop</h2><p>Vsebina zbora je namenjena njegovim članom in pooblaščenim osebam. Račun ustvari skrbnik zbora; prijava je mogoča z dodeljenim Google računom ali obstoječim uporabniškim računom.</p></section>
  % elif section == 'privacy':
    <p class="eyebrow">Informacije za uporabnike · 29. september 2026</p>
    <h1>Zasebnost</h1>
    <p class="lead">{{organization}} upravlja podatke, potrebne za organizacijo zbora. Vprašanja in zahteve glede podatkov pošljite na <a href="mailto:{{contact_email}}">{{contact_email}}</a>.</p>
    <section><h2>Katere podatke uporablja aplikacija</h2><p>Za člane se lahko hranijo ime, priimek, e-poštni naslov, glas, vloge, telefon in rojstni datum, če sta vpisana. Aplikacija beleži tudi dogodke, prisotnost, glasbeni program, ocene skladb, naložene note ali zvočne posnetke ter podatke o zborovski blagajni.</p></section>
    <section><h2>Prijava z Googlom</h2><p>Ob prijavi aplikacija od Googla prejme potrjeni e-poštni naslov in identifikator računa. Uporabi ju za povezavo z računom, ki ga je v aplikaciji že ustvaril skrbnik zbora. Google gesla aplikacija ne prejme.</p></section>
    <section><h2>Google Koledar</h2><p>Po izrecni odobritvi pooblaščene osebe aplikacija pridobi dovoljenje za ogled seznama koledarjev ter branje in urejanje dogodkov povezanega računa. Prikaže koledarje, ki jih ta račun lahko ureja. V izbrani koledar zapisuje ime, vrsto, kraj in čas zborovskih dogodkov ter jih ob spremembi ali izbrisu posodobi. Sprememb iz Googla ne prenaša nazaj. Dostopni žetoni so v bazi shranjeni šifrirano; povezavo lahko pooblaščena oseba prekine v nastavitvah Koledarja.</p></section>
    <section><h2>Dostop, hramba in zahteve</h2><p>Članske podatke vidijo uporabniki glede na dodeljene vloge. Podatki ostanejo v aplikaciji do spremembe ali izbrisa s strani pooblaščene osebe oziroma do obravnave upravičene zahteve. Za vpogled, popravek ali izbris podatkov pišite na <a href="mailto:{{contact_email}}">{{contact_email}}</a>.</p></section>
    <section><h2>Piškotki in lokalna nastavitev</h2><p>Aplikacija uporablja podpisane sejne piškotke za prijavo in kratkotrajne piškotke za varen potek prijave z Googlom. Izbira svetlega ali temnega prikaza se shrani v brskalnikovo lokalno shrambo. Ti podatki niso namenjeni oglaševanju.</p></section>
  % elif section == 'terms':
    <p class="eyebrow">Informacije za uporabnike · 29. september 2026</p>
    <h1>Pogoji uporabe</h1>
    <p class="lead">Aplikacija je namenjena organizaciji dela {{organization}}. Za vprašanja o uporabi pišite na <a href="mailto:{{contact_email}}">{{contact_email}}</a>.</p>
    <section><h2>Kdo lahko uporablja aplikacijo</h2><p>Dostop je namenjen članom zbora in pooblaščenim osebam. Račune in vloge dodelijo skrbniki zbora. Funkcije, ki spreminjajo podatke drugih članov, program, dogodke ali blagajno, so vezane na dodeljene pravice.</p></section>
    <section><h2>Odgovorna uporaba</h2><p>Uporabljajte svoj račun, varujte svoje prijavne podatke in vnašajte podatke za potrebe zbora. Naložite le gradiva, za katera imate pravico do uporabe in deljenja z zborom. Morebitne napake v podatkih sporočite pooblaščeni osebi zbora.</p></section>
    <section><h2>Zunanji storitvi</h2><p>Prijava z Googlom je ločena od dovoljenja za Google Koledar. Koledar poveže pooblaščena oseba; aplikacija nato sinhronizira dogodke samo v izbrani zborovski koledar. Povezavo je mogoče prekiniti v nastavitvah.</p></section>
    <section><h2>Podpora in spremembe</h2><p>Za pomoč, popravke podatkov ali vprašanja glede delovanja uporabite <a href="mailto:{{contact_email}}">{{contact_email}}</a>. Zbor lahko zaradi vzdrževanja spremeni način delovanja ali dostop do posameznih funkcij; posodobljeni pogoji bodo objavljeni na tej strani.</p></section>
  % end
  </main>
  <footer class="public-footer"><span>© {{organization}}</span><nav aria-label="Pravne informacije"><a href="/o-aplikaciji">O aplikaciji</a><a href="/zasebnost">Zasebnost</a><a href="/pogoji-uporabe">Pogoji uporabe</a><a href="/prijava">Prijava</a></nav></footer>
</body>
</html>

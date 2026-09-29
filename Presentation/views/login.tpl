<!doctype html>
<html lang="sl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="theme-color" content="#163a45">
  <title>Prijava · Upravljanje zbora</title>
  <link rel="manifest" href="/manifest.webmanifest">
  <link rel="icon" href="/static/icons/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/static/icons/icon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/styles.css?v=8">
  <link rel="stylesheet" href="/static/refinements.css?v=2">
  <link rel="stylesheet" href="/static/hotfix.css?v=2">
</head>
<body class="login-page">
  <div class="login-art"><div class="login-brand"><span class="brand-mark">𝄞</span>Upravljanje zbora</div><div class="quote"><span>“</span><h1>Skupaj ustvarjamo več kot le glasbo.</h1><p>Vse za usklajeno delo vašega zbora na enem mestu.</p></div><div class="music-lines">♪　♩　♫　♬</div></div>
  <main class="login-panel">
    <div class="login-card">
      <p class="eyebrow">Dobrodošli nazaj</p><h2>Prijava v zbor</h2><p class="muted">Uporabi Google račun z e-pošto, ki jo je vpisal zborovodja.</p>
      % if error:
      <p class="form-error">{{error}}</p>
      % end
      <a class="button google-button wide" href="/prijava/google"><span class="google-mark">G</span> Prijava z Googlom</a>
      % if not google_configured:
      <p class="configuration-note">Google prijava na tem strežniku še ni nastavljena.</p>
      % end
      <div class="login-divider"><span>ali z obstoječim računom</span></div>
      <form method="post" action="/prijava">
        <label>Uporabniško ime<input name="username" required autocomplete="username"></label>
        <label>Geslo<input name="password" type="password" required autocomplete="current-password"></label>
        <div class="login-options"><span></span><a href="#" data-toast="Za pomoč se obrni na predsednika ali zborovodjo.">Težave s prijavo?</a></div>
        <button class="button primary wide" type="submit">Prijava <span>→</span></button>
      </form>
    </div>
    <nav class="legal-links" aria-label="Informacije o aplikaciji"><a href="/o-aplikaciji">O aplikaciji</a><a href="/zasebnost">Zasebnost</a><a href="/pogoji-uporabe">Pogoji uporabe</a></nav>
  </main>
  <div id="toast" role="status"></div><script src="/static/app.js?v=7"></script>
</body></html>

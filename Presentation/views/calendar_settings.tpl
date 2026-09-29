<div class="settings-grid">
  <article class="card">
    <p class="eyebrow">Osebni koledar</p><h2>Moj Google Koledar</h2>
    % if not configured:
    <p class="form-error">Na strežniku manjkajo Google OAuth nastavitve ali ključ za šifriranje žetonov.</p>
    % elif connection and connection.get('active'):
    <p class="connection-account"><span class="status-dot connected"></span><strong>{{connection['google_email']}}</strong></p>
    <p>Zborovski dogodki se dodajo neposredno v glavni Google Koledar tega računa.</p>
    <div class="settings-actions"><a class="button secondary" href="/nastavitve/google-koledar/povezi">Poveži znova</a>
      <form method="post" action="/nastavitve/google-koledar/prekini"><button class="button danger" onclick="return confirm('Prekini povezavo? Dogodki v tvojem Googlovem koledarju se ne bodo izbrisali.')">Prekini povezavo</button></form></div>
    % else:
    <p>Poveži svoj Google račun. Njegov e-poštni naslov se mora ujemati s članskim računom. Povezava je prostovoljna.</p>
    <a class="button primary" href="/nastavitve/google-koledar/povezi">Poveži moj Google Koledar</a>
    % end
  </article>
  <article class="card">
    <p class="eyebrow">Sinhronizacija</p><h2>Moji dogodki</h2>
    <p>Uspešno posodobljeni: <strong>{{status['synced']}}</strong><br>Napake: <strong>{{status['errors']}}</strong><br>Čakajoči izbrisi: <strong>{{status['pending']}}</strong></p>
    % if connection and connection.get('active'):
    <form method="post" action="/nastavitve/google-koledar/sinhroniziraj"><button class="button secondary">Ponovi sinhronizacijo</button></form>
    % elif status['errors'] or status['pending']:
    <p>Poveži račun znova, da se poskusijo prenosi in izbrisi, ki niso uspeli.</p>
    % end
  </article>
</div>
<p class="permission-note calendar-note"><strong>Smer prenosa:</strong> aplikacija → tvoj glavni Google Koledar. Spremembe v Googlu se ne prenesejo nazaj. Vsak član sam odobri povezavo svojega računa.</p>

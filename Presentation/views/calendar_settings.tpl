<div class="settings-grid">
  <article class="card">
    <p class="eyebrow">En skupni koledar</p><h2>Google povezava</h2>
    % if not configured:
    <p class="form-error">Na strežniku manjkajo Google OAuth nastavitve ali ključ za šifriranje žetonov. Dopolni datoteko <code>.env</code> po navodilih v README.</p>
    % elif connection and connection.get('active'):
    <p class="connection-account"><span class="status-dot connected"></span><strong>{{connection['google_email']}}</strong></p><p>Povezavo je odobril pooblaščeni uporabnik. Članski Google računi s to povezavo niso povezani.</p>
    % else:
    <p>Poveži zborovski Google račun, ki ima pravico urejanja ciljnega koledarja.</p>
    % end
    % if configured and (not connection or not connection.get('active')):
    <a class="button primary" href="/nastavitve/google-koledar/povezi">Poveži Google račun</a>
    % elif configured:
    <div class="settings-actions"><a class="button secondary" href="/nastavitve/google-koledar/povezi">Poveži znova</a><form method="post" action="/nastavitve/google-koledar/prekini"><button class="button danger" onclick="return confirm('Prekini povezavo? Dogodki v Googlu se ne bodo izbrisali.')">Prekini povezavo</button></form></div>
    % end
  </article>
  <article class="card">
    <p class="eyebrow">Cilj sinhronizacije</p><h2>Skupni koledar</h2>
    % if calendar_error:
    <p class="form-error">{{calendar_error}}</p>
    % end
    % if connection and connection.get('active') and calendars and not connection.get('calendar_id'):
    <form method="post" action="/nastavitve/google-koledar/izberi"><label>Koledar<select name="calendar_id" required><option value="">Izberi koledar …</option>
      % for calendar in calendars:
      <option value="{{calendar['id']}}" {{'selected' if connection.get('calendar_id') == calendar['id'] else ''}}>{{calendar['name']}}{{' (glavni)' if calendar['primary'] else ''}}</option>
      % end
    </select></label><button class="button primary" type="submit">Shrani in sinhroniziraj vse dogodke</button></form>
    % elif not connection or not connection.get('active'):
    <p>Koledar bo mogoče izbrati po povezavi Google računa.</p>
    % end
    % if connection and connection.get('active') and connection.get('calendar_id'):
    <hr><p>Izbran: <strong>{{connection['calendar_name']}}</strong></p><form method="post" action="/nastavitve/google-koledar/sinhroniziraj"><button class="button secondary">Ponovi sinhronizacijo vseh dogodkov</button></form>
    % end
  </article>
</div>
<p class="permission-note calendar-note"><strong>Smer prenosa:</strong> aplikacija → Google Koledar. Spremembe, narejene neposredno v Googlu, se ne prenašajo nazaj.</p>

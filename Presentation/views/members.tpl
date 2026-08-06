<div class="page-tools"><div class="search"><span>⌕</span><input data-filter="members-table" placeholder="Poišči člana po imenu, glasu ali e-pošti …"></div><select data-role-filter aria-label="Filtriraj po vlogi"><option value="">Vse vloge</option>
% for role in roles:
<option value="{{role['name']}}" {{'selected' if selected_role == role['name'] else ''}}>{{role['name']}}</option>
% end
</select><button class="button secondary" onclick="location.href='/vloge'" data-permission="admin">Uredi vloge</button><button class="button primary" data-member-dialog data-create-dialog data-permission="admin">＋ Dodaj člana</button></div>
<article class="card table-card"><div class="table-meta"><p><strong>{{len(members)}} članov</strong><span>Aktivni člani zbora</span></p><div class="voice-pills">
% for voice in ('Sopran','Alt','Tenor','Bas'):
<span>{{voice}} <b>{{sum(1 for member in members if member['voice'] == voice)}}</b></span>
% end
</div></div><div class="table-wrap"><table id="members-table"><thead><tr><th>Član</th><th>Glas</th><th>Kontakt</th><th>Vloga</th><th>Prisotnost</th><th></th></tr></thead><tbody>
% for member in members:
<tr data-roles="{{'|'.join(member['roles'])}}"><td><a class="person" href="/clani/{{member['id']}}"><span class="avatar small">{{member['initials']}}</span><strong>{{member['name']}}</strong></a></td><td><span class="tag">{{member['voice']}}</span></td><td><span>{{member['email']}}</span><small>{{member['phone']}}</small></td><td>{{', '.join(member['roles'])}}</td><td><div class="progress"><i style="width:{{member['attendance']}}%"></i></div><b>{{member['attendance']}}%</b></td><td><a class="row-action" href="/clani/{{member['id']}}" aria-label="Odpri podrobnosti">→</a></td></tr>
% end
% if not members:
<tr><td colspan="6"><div class="empty-state"><span>♟</span><h3>Ni še nobenega člana</h3><p>Dodaj prvega člana in njegov uporabniški račun.</p><button class="button primary" data-member-dialog data-permission="admin">Dodaj člana</button></div></td></tr>
% end
</tbody></table></div></article>
<dialog id="member-dialog" class="member-dialog"><button class="member-dialog-close dialog-close" aria-label="Zapri dodajanje člana">×</button><form method="post" action="/clani"><p class="eyebrow">Nov član in uporabniški račun</p><h2>Dodaj novega člana</h2><p>Ob shranjevanju bo samodejno ustvarjen tudi uporabniški račun.</p><div class="form-grid"><label>Ime<input id="new-first-name" name="first_name" required autocomplete="off"></label><label>Priimek<input id="new-last-name" name="last_name" required autocomplete="off"></label><label>E-pošta<input name="email" type="email" required></label><label>Telefon<input name="phone"></label><label>Datum rojstva<input name="birth_date" type="date"></label><label>Glas<select name="voice" required><option>Sopran</option><option>Alt</option><option>Tenor</option><option>Bas</option></select></label></div><fieldset class="choice-section"><legend>Vloge</legend><div class="choice-grid">
% for role in roles:
% if role['name'] != 'Član':
<label class="check" title="{{role['description']}}"><input type="checkbox" name="roles" value="{{role['name']}}"><span>{{role['name']}}</span></label>
% end
% end
</div><p class="field-help">Vloga Član bo dodana samodejno. Za opis se pomakni nad posamezno vlogo.</p></fieldset><div class="account-preview"><span class="account-preview-icon">♙</span><div><small>SAMODEJNO USTVARJEN RAČUN</small><p>Uporabniško ime <strong id="generated-username">ime.priimek</strong></p><p>Začetno geslo <strong id="generated-password">ime.priimek</strong></p></div></div><p class="form-help">Če je uporabniško ime že zasedeno, sistem doda naslednje prosto naravno število. Ob prvi prijavi mora član izbrati novo geslo.</p><div class="dialog-actions"><button type="button" class="button secondary member-dialog-cancel">Prekliči</button><button type="submit" class="button primary">Dodaj člana in ustvari račun</button></div></form></dialog>

% status_labels={'present':'Prisoten','late_under':'Zamuda < 10 min','late_over':'Zamuda > 10 min','excused':'Opravičeno','absent':'Odsoten'}
<div class="back-row"><a href="/clani">← Nazaj na člane</a><div><button class="button secondary" data-password-reset="{{member['username']}}" data-reset-url="/clani/{{member['id']}}/geslo" data-permission="admin">Ponastavi geslo</button><button class="button secondary" data-member-edit data-permission="{{'self' if member['id'] == current_user['person_id'] else 'admin'}}">Uredi</button>
% if member['id'] != current_user['person_id']:
<form method="post" action="/clani/{{member['id']}}/izbrisi" class="inline-form" data-permission="admin"><button class="button danger" onclick="return confirm('Res želiš izbrisati člana?')">Izbriši</button></form>
% end
</div></div>
<div class="detail-grid"><article class="card profile-card"><div class="avatar xlarge">{{member['initials']}}</div><h2>{{member['name']}}</h2><span class="tag">{{member['voice']}}</span><dl><dt>E-pošta</dt><dd>{{member['email']}}</dd><dt>Telefon</dt><dd>{{member['phone']}}</dd><dt>Datum rojstva</dt><dd>{{member['birth']}}</dd><dt>Vloge</dt><dd>
% for role in member['roles']:
<span class="badge">{{role}}</span>
% end
</dd></dl></article><article class="card span-2"><div class="card-head"><div><p class="eyebrow">Tekoče šolsko leto</p><h3>Prisotnost na dogodkih</h3></div><strong class="big-percent">{{member['attendance']}}%</strong></div><div class="attendance-summary">
% for state in ('present','late_under','late_over','excused','absent'):
<span><b>{{member['attendance_totals'][state]}}</b>{{status_labels[state]}}</span>
% end
</div><div class="simple-list">
% for event in member['attendance_rows']:
<a href="/dogodki/{{event['id']}}"><span><strong>{{event['title']}}</strong><small>{{event['date']}} · {{event['kind']}}</small></span><span class="status {{event['status']}}">{{status_labels[event['status']]}}</span></a>
% end
% if not member['attendance_rows']:
<div class="empty-state compact"><p>Za tega člana še ni podatkov o prisotnosti v tekočem šolskem letu.</p><a class="button secondary" href="/dogodki?nov=1" data-permission="admin">Dodaj dogodek</a></div>
% end
</div></article></div>
<dialog id="member-edit-dialog"><button class="member-edit-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/clani/{{member['id']}}/uredi"><p class="eyebrow">Član zbora</p><h2>Uredi podatke</h2><div class="form-grid"><label>Ime<input name="first_name" value="{{member['first_name']}}" required></label><label>Priimek<input name="last_name" value="{{member['last_name']}}" required></label><label>E-pošta<input type="email" name="email" value="{{member['email']}}" required></label><label>Telefon<input name="phone" value="{{member['phone']}}"></label><label>Datum rojstva<input type="date" name="birth_date" value="{{member['birth_date'].isoformat() if member['birth_date'] else ''}}"></label><label>Glas<select name="voice">
% for voice in ('Sopran','Alt','Tenor','Bas'):
<option {{'selected' if member['voice'] == voice else ''}}>{{voice}}</option>
% end
</select></label></div>
% if 'admin' in permissions:
<fieldset class="choice-section"><legend>Vloge</legend><div class="choice-grid">
% for role in roles:
<label class="check" title="{{role['description']}}"><input type="checkbox" name="roles" value="{{role['name']}}" {{'checked' if role['name'] in member['roles'] else ''}}><span>{{role['name']}}</span></label>
% end
</div><p class="field-help">Za opis se pomakni nad posamezno vlogo.</p></fieldset>
% end
<div class="dialog-actions"><button type="button" class="button secondary member-edit-cancel">Prekliči</button><button type="submit" class="button primary">Shrani spremembe</button></div></form></dialog>

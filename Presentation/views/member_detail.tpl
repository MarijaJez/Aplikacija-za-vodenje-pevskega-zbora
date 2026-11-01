% status_labels={'present':'Prisoten','late_under':'Zamuda < 10 min','late_over':'Zamuda > 10 min','excused':'Opravičeno','absent':'Odsoten','unentered':'Še ni vneseno'}
<div class="back-row"><a href="/clani">← Nazaj na člane</a><div><button class="button secondary" data-member-edit data-permission="{{'self' if member['id'] == current_user['person_id'] else 'admin'}}">Uredi</button>
% if member['id'] != current_user['person_id']:
<form method="post" action="/clani/{{member['id']}}/izbrisi" class="inline-form" data-permission="admin"><button class="button danger" onclick="return confirm('Res želiš izbrisati člana?')">Izbriši</button></form>
% end
</div></div>
<div class="detail-grid member-profile"><article class="card profile-card">
% if current_user['person_id'] == member['id']:
<form class="avatar-upload" method="post" action="/profil/slika" enctype="multipart/form-data" data-avatar-upload>
<input type="hidden" name="csrf" value="{{avatar_csrf}}">
<input type="file" name="avatar" id="profile-avatar-file" accept="image/jpeg,image/png,image/webp" hidden required>
<button type="button" class="avatar xlarge avatar-edit" data-avatar-choose aria-label="Spremeni profilno sliko" aria-describedby="avatar-help">{{!avatar(member, member['initials'])}}<span class="avatar-edit-icon" aria-hidden="true">✎</span></button>
<p id="avatar-help" class="avatar-help">Klikni sliko za zamenjavo</p><p class="avatar-upload-status" role="status" aria-live="polite"></p>
<noscript><style>.avatar-upload input[type=file]{display:block!important}</style><button class="button secondary" type="submit">Shrani sliko</button></noscript>
</form>
% if member.get('avatar_path'):
<form method="post" action="/profil/slika" class="avatar-remove"><input type="hidden" name="csrf" value="{{avatar_csrf}}"><button type="submit" name="remove" value="1" class="text-link">Odstrani sliko</button></form>
% end
% else:
<div class="avatar xlarge">{{!avatar(member, member['initials'])}}</div>
% end
<h2>{{member['name']}}</h2><span class="tag">{{member['voice']}}</span><dl><dt>E-pošta</dt><dd>{{member['email']}}</dd><dt>Telefon</dt><dd>{{member['phone']}}</dd><dt>Datum rojstva</dt><dd>{{member['birth']}}</dd><dt>Vloge</dt><dd>
% for role in member['roles']:
<span class="badge">{{role}}</span>
% end
</dd></dl></article><article class="card span-2"><div class="card-head"><div><p class="eyebrow">Tekoče šolsko leto</p><h3>Prisotnost na dogodkih</h3></div><strong class="big-percent">{{str(member['attendance'])+'%' if member['attendance'] is not None else 'Še ni vneseno'}}</strong></div><div class="attendance-summary">
% for state in ('present','late_under','late_over','excused','absent','unentered'):
<span><b>{{member['attendance_totals'][state]}}</b>{{status_labels[state]}}</span>
% end
</div><div class="simple-list">
% for event in member['attendance_rows']:
<div class="member-attendance-row"><a href="/dogodki/{{event['id']}}"><strong>{{event['title']}}</strong><small>{{event['date']}} · {{event['kind']}}</small></a>
% if can_edit_attendance(current_user, member['id'], event):
<select data-member-attendance data-person-id="{{member['id']}}" data-event-id="{{event['id']}}" data-saved-status="{{event['status']}}" aria-label="Prisotnost: {{event['title']}}">
% for state, label in status_labels.items():
<option value="{{state}}" {{'selected' if state == event['status'] else ''}} {{'disabled' if state == 'unentered' else ''}}>{{label}}</option>
% end
</select>
% else:
<span class="status {{event['status']}}">{{status_labels[event['status']]}}</span>
% end
</div>
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

<script src="/static/avatar-upload.js?v=1" defer></script>
<script src="/static/member-attendance.js?v=1" defer></script>

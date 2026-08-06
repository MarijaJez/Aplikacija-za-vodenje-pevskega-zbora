<div class="page-tools"><a class="button secondary" href="/clani">← Nazaj na člane</a><span class="spacer"></span><button class="button primary" data-role-dialog data-create-dialog data-permission="admin">＋ Dodaj vlogo</button></div><div class="role-grid">
% for role in roles:
<article class="card role-card"><span class="role-icon">♙</span><div><h3>{{role['name']}}</h3><p>{{role['description']}}</p><a href="/clani?vloga={{role['name']}}">{{role['count']}} članov →</a></div><div class="role-actions" data-permission="admin"><button class="icon-button" data-role-edit="{{role['id']}}" aria-label="Uredi vlogo {{role['name']}}">✎</button>
% if role['count'] == 0 and role['name'] != 'Član':
<form method="post" action="/vloge/{{role['id']}}/izbrisi"><button class="icon-button danger-icon" aria-label="Izbriši vlogo {{role['name']}}" onclick="return confirm('Res želiš izbrisati vlogo?')">×</button></form>
% end
</div></article>
<dialog id="role-edit-{{role['id']}}"><button class="dialog-close role-edit-close" aria-label="Zapri">×</button><form method="post" action="/vloge/{{role['id']}}/uredi"><p class="eyebrow">Dostop</p><h2>Uredi vlogo</h2><label>Ime<input name="name" value="{{role['name']}}" required {{'readonly' if role['name'] == 'Član' else ''}}></label><label>Opis<textarea name="description" rows="3">{{role['description']}}</textarea></label><div class="dialog-actions"><button type="button" class="button secondary role-edit-cancel">Prekliči</button><button type="submit" class="button primary">Shrani spremembe</button></div></form></dialog>
% end
% if not roles:
<div class="empty-state card"><span>♙</span><h3>Ni še nobene vloge</h3><p>Dodaj prvo vlogo za določanje pravic članov.</p><button class="button primary" data-role-dialog data-permission="admin">Dodaj vlogo</button></div>
% end
</div><dialog id="role-dialog"><button class="role-dialog-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/vloge"><p class="eyebrow">Dostop</p><h2>Dodaj vlogo</h2><label>Ime<input name="name" required></label><label>Opis<textarea name="description" rows="3"></textarea></label><div class="dialog-actions"><button type="button" class="button secondary role-dialog-cancel">Prekliči</button><button type="submit" class="button primary">Shrani vlogo</button></div></form></dialog>

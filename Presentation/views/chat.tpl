<link rel="stylesheet" href="/static/gallery_chat.css?v=1">
<div class="community-heading"><div><p class="eyebrow">Samo za člane</p><h2>Skupinski klepet</h2><p>Sporočila so vidna prijavljenim članom. Piši spoštljivo in ne objavljaj osebnih podatkov brez dovoljenja.</p></div></div>
<section class="card community-chat"><div class="community-chat-head"><strong>Zborovski pogovor</strong><span>Osveževanje vsakih 10 sekund · prikazanih zadnjih 100 sporočil</span></div><ol class="community-messages" data-chat-list data-current-user="{{current_user['id']}}" data-admin="{{'1' if 'admin' in permissions else '0'}}" data-csrf="{{csrf}}">
% for item in messages:
<li class="community-message {{'is-deleted' if item['deleted_at'] else ''}}"><div class="community-message-meta"><strong>{{item['author']}}</strong><time datetime="{{item['created_at'].isoformat()}}">{{item['created_at'].strftime('%d. %m. %Y %H:%M')}}</time>{{' · urejeno' if item['edited_at'] else ''}}</div><p>{{item['body'] if not item['deleted_at'] else 'Sporočilo je izbrisano.'}}</p>
% if not item['deleted_at'] and item['author_id'] == current_user['id']:
<details><summary>Uredi</summary><form method="post" action="/klepet/{{item['id']}}/uredi"><input type="hidden" name="csrf" value="{{csrf}}"><label>Besedilo<textarea name="body" maxlength="2000" required>{{item['body']}}</textarea></label><button class="button secondary" type="submit">Shrani</button></form></details>
% end
% if not item['deleted_at'] and (item['author_id'] == current_user['id'] or 'admin' in permissions):
<form method="post" action="/klepet/{{item['id']}}/izbrisi" onsubmit="return confirm('Izbrišem sporočilo?')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="community-delete" type="submit">Izbriši</button></form>
% end
</li>
% end
</ol><form class="community-compose" method="post" action="/klepet"><input type="hidden" name="csrf" value="{{csrf}}"><label for="chat-body">Novo sporočilo</label><textarea id="chat-body" name="body" maxlength="2000" rows="3" required placeholder="Napiši sporočilo za člane zbora …"></textarea><button class="button primary" type="submit">Pošlji</button></form></section>
<script src="/static/gallery_chat.js?v=1" defer></script>

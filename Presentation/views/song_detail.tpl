<div class="back-row"><a href="/program">← Nazaj na program</a><div><button class="button secondary" data-song-edit data-permission="program">Uredi</button><form method="post" action="/program/{{song['id']}}/izbrisi" class="inline-form" data-permission="program"><button class="button danger" onclick="return confirm('Res želiš izbrisati pesem?')">Izbriši</button></form></div></div><div class="detail-grid"><article class="card profile-card song-profile"><div class="song-detail-icon">♫</div><h2>{{song['title']}}</h2><p>{{song['author']}}</p><div>
% for category in song['categories']:
<span class="tag">{{category}}</span>
% end
</div>
% if song.get('notes_path'):
<a class="button secondary wide" href="/uploads/{{song['notes_path']}}">Odpri note</a>
% end
% if song.get('audio_path'):
<audio controls preload="metadata" class="song-audio"><source src="/uploads/{{song['audio_path']}}">Brskalnik ne podpira predvajanja zvoka.</audio>
% end
</article><article class="card span-2"><div class="rating-hero"><div><strong>{{song['rating']}}</strong><span>★★★★★</span><small>{{song['ratings']}} ocen članov</small></div><button class="button primary" data-review-dialog>{{'Uredi svojo oceno' if song['my_review'] else 'Dodaj svojo oceno'}}</button></div><hr><div class="card-head"><h3>Komentarji članov</h3><span class="muted">Najnovejši najprej</span></div><div class="comments">
% for review in song['reviews']:
<div><span class="avatar small">{{review['initials']}}</span><p><strong>{{review['member']}} <span>{{'★' * review['rating']}}{{'☆' * (5-review['rating'])}}</span></strong><small>{{review['updated_at'].strftime('%d. %m. %Y')}}</small>{{review['comment']}}</p></div>
% end
% if not song['reviews']:
<p class="muted">Pesem še nima ocen.</p>
% end
</div></article></div>
% if conductor:
<article class="card song-performance-history"><div class="card-head"><div><p class="eyebrow">Zgodovina programa</p><h3>Pretekle izvedbe</h3></div><span class="muted">Vidno samo zborovodji</span></div>
% for performance in song['performances']:
<div class="performance-history-row"><div><a href="/dogodki/{{performance['id']}}"><strong>{{performance['title']}}</strong></a><small>{{performance['date']}} · {{performance['kind']}} · {{performance['place']}}</small></div><p class="performance-comment">{{performance['comment'] or 'Brez komentarja izvedbe.'}}</p><span class="rating">{{'★ '+str(performance['rating']) if performance['rating'] else 'Brez ocene'}}</span></div>
% end
% if not song['performances']:
<p class="muted">Pesem še nima zabeleženih preteklih izvedb.</p>
% end
</article>
% end
<dialog id="song-edit-dialog"><button class="song-edit-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/program/{{song['id']}}/uredi" enctype="multipart/form-data"><p class="eyebrow">Program</p><h2>Uredi pesem</h2><label>Naslov<input name="title" value="{{song['title']}}" required></label><label>Avtor<input name="author" value="{{song['author']}}" required></label><label>Zamenjaj note<input type="file" name="notes" accept=".pdf,.jpg,.jpeg,.png"></label><label>Zamenjaj zvočni posnetek<input type="file" name="audio" accept=".mp3,.wav,.m4a,.ogg,audio/*"></label><fieldset class="choice-section"><legend>Kategorije</legend><div class="choice-grid">
% for category in categories:
<label class="check"><input type="checkbox" name="categories" value="{{category['name']}}" {{'checked' if category['name'] in song['categories'] else ''}}><span>{{category['name']}}</span></label>
% end
</div></fieldset><div class="dialog-actions"><button type="button" class="button secondary song-edit-cancel">Prekliči</button><button type="submit" class="button primary">Shrani spremembe</button></div></form></dialog>
<dialog id="review-dialog"><button class="review-dialog-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/program/{{song['id']}}/ocena"><p class="eyebrow">Mnenje člana</p><h2>{{'Uredi svojo oceno' if song['my_review'] else 'Oceni pesem'}}</h2><label>Ocena<select name="rating" required>
% for value,label in ((5,'odlično'),(4,'zelo dobro'),(3,'dobro'),(2,'zadovoljivo'),(1,'slabo')):
<option value="{{value}}" {{'selected' if song['my_review'] and song['my_review']['rating'] == value else ''}}>{{value}} – {{label}}</option>
% end
</select></label><label>Komentar<textarea name="comment" rows="4" required>{{song['my_review']['comment'] if song['my_review'] else ''}}</textarea></label><div class="dialog-actions"><button type="button" class="button secondary review-dialog-cancel">Prekliči</button><button type="submit" class="button primary">Shrani oceno</button></div></form></dialog>

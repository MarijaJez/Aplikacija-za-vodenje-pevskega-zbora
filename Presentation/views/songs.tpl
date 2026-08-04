<div class="page-tools"><div class="search"><span>⌕</span><input data-filter="songs-grid" placeholder="Poišči pesem ali avtorja …"></div><details class="multi-filter"><summary>Kategorije <span data-category-count></span></summary><div class="multi-filter-panel">
% for category in categories:
<label class="check"><input type="checkbox" data-category-filter value="{{category['name']}}"><span>{{category['name']}}</span></label>
% end
</div></details><a class="button secondary" href="/kategorije" data-permission="program">Uredi kategorije</a><button class="button primary" data-song-dialog data-permission="program">＋ Dodaj pesem</button></div><div class="section-title"><div><strong>{{len(songs)}} pesmi</strong><span>v aktivnem programu</span></div></div><div class="songs-grid compact-song-grid" id="songs-grid">
% for song in songs:
<article class="song-card compact-song-card" data-categories="{{'|'.join(song['categories'])}}"><a href="/program/{{song['id']}}"><div class="song-body"><div class="rating">★ {{song['rating']}} <small>({{song['ratings']}})</small></div><h3>{{song['title']}}</h3><p>{{song['author']}}</p><div>
% for category in song['categories']:
<span class="tag">{{category}}</span>
% end
</div><small>Nazadnje izvedena: {{song['last']}}</small></div></a></article>
% end
</div><dialog id="song-dialog"><button class="song-dialog-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/program" enctype="multipart/form-data"><p class="eyebrow">Program</p><h2>Dodaj pesem</h2><label>Naslov<input name="title" required></label><label>Avtor<input name="author" required></label><label>Note (PDF, JPG ali PNG)<input type="file" name="notes" accept=".pdf,.jpg,.jpeg,.png"></label><label>Zvočni posnetek (MP3, WAV, M4A ali OGG)<input type="file" name="audio" accept=".mp3,.wav,.m4a,.ogg,audio/*"></label><fieldset class="choice-section"><legend>Kategorije</legend><div class="choice-grid">
% for category in categories:
<label class="check"><input type="checkbox" name="categories" value="{{category['name']}}"><span>{{category['name']}}</span></label>
% end
</div></fieldset><div class="dialog-actions"><button type="button" class="button secondary song-dialog-cancel">Prekliči</button><button type="submit" class="button primary">Shrani pesem</button></div></form></dialog>

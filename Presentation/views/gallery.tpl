<link rel="stylesheet" href="/static/gallery_chat.css?v=1">
% if album:
<div class="community-back"><a href="/galerija">← Vsi albumi</a><a href="/dogodki/{{album['id']}}">Odpri dogodek →</a></div>
<div class="community-heading"><div><p class="eyebrow">Album dogodka</p><h2>{{album['name']}}</h2><p>{{album['event_date'].strftime('%d. %m. %Y')}} · {{album['event_type']}}</p></div></div>
% if 'admin' in permissions:
<section class="card community-upload"><h3>Dodaj fotografijo</h3><p class="muted">Dodaj samo fotografije, za katere ima zbor dovoljenje za deljenje med člani. Lokacijski in drugi metapodatki se pred shranjevanjem odstranijo.</p><form method="post" action="/galerija/{{album['id']}}/dodaj" enctype="multipart/form-data"><input type="hidden" name="csrf" value="{{csrf}}"><label>Fotografija (JPEG, PNG ali WebP, do 8 MB)<input type="file" name="photo" accept="image/jpeg,image/png,image/webp" required></label><label>Opis slike za dostopnost<input name="alt_text" maxlength="160" required placeholder="Kdo ali kaj je na fotografiji"></label><label>Napis pod fotografijo (neobvezno)<input name="caption" maxlength="300"></label><button class="button primary" type="submit">Dodaj fotografijo</button></form></section>
% end
% if photos:
<div class="community-photo-grid">
% for photo in photos:
<figure class="card community-photo"><a href="/galerija/slika/{{photo['id']}}" target="_blank" rel="noopener"><img src="/galerija/slika/{{photo['id']}}" alt="{{photo['alt_text']}}" loading="lazy"></a><figcaption><strong>{{photo['caption'] or photo['alt_text']}}</strong><small>Dodano: {{photo['uploaded_at'].strftime('%d. %m. %Y')}} · {{photo['uploader']}}</small></figcaption>
% if 'admin' in permissions:
<form method="post" action="/galerija/slika/{{photo['id']}}/izbrisi" onsubmit="return confirm('Izbrišem fotografijo?')"><input type="hidden" name="csrf" value="{{csrf}}"><button class="button danger" type="submit">Izbriši</button></form>
% end
</figure>
% end
</div>
% else:
<div class="card community-empty">V tem albumu še ni fotografij.</div>
% end
% else:
<div class="community-heading"><div><p class="eyebrow">Zborovski utrinki</p><h2>Galerija dogodkov</h2><p>Fotografije lahko vidijo samo prijavljeni člani zbora.</p></div></div>
% if albums:
<div class="community-albums">
% for item in albums:
<a class="card community-album" href="/galerija/{{item['id']}}"><span class="community-album-icon" aria-hidden="true">▧</span><span><strong>{{item['name']}}</strong><small>{{item['event_date'].strftime('%d. %m. %Y')}} · {{item['event_type']}}</small></span><span class="tag">{{item['photo_count']}} fotografij</span></a>
% end
</div>
% else:
<div class="card community-empty">Dogodkov še ni.</div>
% end
% end

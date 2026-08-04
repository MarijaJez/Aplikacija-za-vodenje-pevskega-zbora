% selected_song_ids={song['id'] for song in event['program']}
% tracks=[{'title':song['title'],'url':'/uploads/'+song['audio_path']} for song in event['program'] if song.get('audio_path')]
<div class="back-row"><a href="/dogodki">← Nazaj na dogodke</a><div class="event-toolbar"><a class="button secondary" href="{{google_url}}" target="_blank" rel="noopener">Dodaj v Google Koledar</a><button class="button secondary" data-event-edit data-permission="admin">Uredi</button><form method="post" action="/dogodki/{{event['id']}}/izbrisi" class="inline-form" data-permission="admin"><button class="button danger" onclick="return confirm('Res želiš izbrisati dogodek?')">Izbriši</button></form></div></div><article class="event-hero {{event['status']}}"><div class="event-date large"><strong>{{event['date'].split('.')[0]}}</strong><span>{{event['date'].split(' ')[1].replace('.','').upper()}}</span></div><div><span class="badge">{{event['kind']}}</span><h2>{{event['title']}}</h2><p>◷ {{event['time']}}　⌖ {{event['place']}}</p></div></article><div class="detail-grid"><article class="card span-2"><div class="card-head"><div><p class="eyebrow">Program dogodka</p><h3>{{event['songs']}} izbranih pesmi</h3></div><button class="button primary" data-play-event {{'disabled' if not tracks else ''}}>▶ {{'Predvajaj pesmi dogodka' if tracks else 'Ni naloženih posnetkov'}}</button></div><p class="playlist-status" data-playlist-status></p><div class="simple-list numbered performance-list">
% for index, song in enumerate(event['program']):
<div><a href="/program/{{song['id']}}"><b>{{index + 1}}</b><span><strong>{{song['title']}}</strong><small>{{song['author']}}</small></span></a>
% if conductor:
<span><span class="rating">{{'★ '+str(song['rating']) if song['rating'] else 'Brez ocene'}}</span><small>{{song['comment'] or 'Brez komentarja.'}}</small></span><button class="button secondary small-button" data-performance-dialog="{{song['id']}}">{{'Uredi oceno izvedbe' if song['rating'] else 'Oceni izvedbo'}}</button>
% end
</div>
% if conductor:
<dialog id="performance-dialog-{{song['id']}}"><button class="dialog-close performance-close" aria-label="Zapri">×</button><form method="post" action="/dogodki/{{event['id']}}/program/{{song['id']}}"><p class="eyebrow">Izvedba pesmi</p><h2>{{song['title']}}</h2><label>Ocena izvedbe<select name="rating" required>
% for value in range(5,0,-1):
<option value="{{value}}" {{'selected' if song['rating'] == value else ''}}>{{value}}</option>
% end
</select></label><label>Komentar<textarea name="comment" rows="4">{{song['comment'] or ''}}</textarea></label><div class="dialog-actions"><button type="button" class="button secondary performance-cancel">Prekliči</button><button type="submit" class="button primary">Shrani oceno izvedbe</button></div></form></dialog>
% end
% end
</div></article><article class="card"><div class="card-head"><div><p class="eyebrow">Prisotnost</p><h3>Člani</h3></div><a href="/prisotnost">Odpri evidenco →</a></div>
% if attendance_summary:
<div class="event-attendance-overview"><strong>{{attendance_summary['attendance_rate']}}%</strong><span>udeležba</span><small>Evidentiranih {{attendance_summary['recorded']}} od {{attendance_summary['total_members']}} članov</small></div><div class="event-attendance-counts"><span><b>{{attendance_summary['totals']['present']}}</b>Prisotni</span><span><b>{{attendance_summary['totals']['late_under'] + attendance_summary['totals']['late_over']}}</b>Zamude</span><span><b>{{attendance_summary['totals']['excused']}}</b>Opravičeno</span><span><b>{{attendance_summary['totals']['absent']}}</b>Odsotni</span></div>
% else:
<p class="muted">Prisotnost za ta dogodek še ni bila urejena.</p>
% end
</article></div>
<script id="event-playlist" type="application/json">{{!json.dumps(tracks, ensure_ascii=False)}}</script>
<dialog id="event-edit-dialog" class="wide-dialog"><button class="event-edit-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/dogodki/{{event['id']}}/uredi"><p class="eyebrow">Koledar</p><h2>Uredi dogodek</h2><div class="form-grid"><label>Datum in ura<input type="datetime-local" name="event_date" value="{{event['event_date'].strftime('%Y-%m-%dT%H:%M')}}" required></label><label>Vrsta<input name="event_type" list="event-types-edit" value="{{event['event_type']}}" required><datalist id="event-types-edit">
% for event_type in event_types:
<option value="{{event_type}}">
% end
</datalist></label><label>Naziv<input name="name" value="{{event['name']}}" required></label><label>Kraj<input name="place" value="{{event['place']}}" required></label></div><fieldset class="choice-section program-lookup"><legend>Program dogodka</legend><div class="lookup-tools"><input type="search" data-program-search placeholder="Išči po naslovu ali avtorju …"><select data-program-category><option value="">Vse kategorije</option>
% for category in categories:
<option>{{category['name']}}</option>
% end
</select></div><div class="lookup-results">
% for song in songs:
<label class="lookup-song" data-search="{{song['title']}} {{song['author']}}" data-categories="{{'|'.join(song['categories'])}}"><input type="checkbox" name="songs" value="{{song['id']}}" {{'checked' if song['id'] in selected_song_ids else ''}}><span><strong>{{song['title']}}</strong><small>{{song['author']}} · {{', '.join(song['categories'])}}</small></span></label>
% end
</div></fieldset><div class="dialog-actions"><button type="button" class="button secondary event-edit-cancel">Prekliči</button><button type="submit" class="button primary">Shrani spremembe</button></div></form></dialog>

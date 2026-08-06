<div class="page-tools"><span class="spacer"></span><a class="button secondary" href="/dogodki/koledar.ics">Izvozi v Google Koledar</a><button class="button primary" data-event-dialog data-create-dialog data-permission="admin">＋ Dodaj dogodek</button></div><div class="event-page">
% for event in events:
<a class="event-card {{event['status']}}" href="/dogodki/{{event['id']}}"><div class="event-date"><strong>{{event['date'].split('.')[0]}}</strong><span>{{event['date'].split(' ')[1].replace('.','').upper()}}</span></div><div class="event-line"><i></i></div><div class="event-info"><span class="badge">{{event['kind']}}</span><h3>{{event['title']}}</h3><p>◷ {{event['time']}}　⌖ {{event['place']}}</p></div><div class="event-program"><small>PROGRAM</small><strong>{{event['songs']}} pesmi</strong></div><span class="arrow">→</span></a>
% end
% if not events:
<div class="empty-state card"><span>◷</span><h3>Ni še nobenega dogodka</h3><p>Dodaj prvo vajo, nastop ali drug zborovski dogodek.</p><button class="button primary" data-event-dialog data-permission="admin">Dodaj dogodek</button></div>
% end
</div><dialog id="event-dialog" class="wide-dialog"><button class="event-dialog-close dialog-close" aria-label="Zapri">×</button><form method="post" action="/dogodki"><p class="eyebrow">Koledar</p><h2>Dodaj dogodek</h2><div class="form-grid"><label>Datum in ura<input type="datetime-local" name="event_date" required></label><label>Vrsta<input name="event_type" list="event-types" placeholder="Izberi ali vnesi novo vrsto" required><datalist id="event-types">
% for event_type in event_types:
<option value="{{event_type}}">
% end
</datalist></label><label>Naziv<input name="name" required></label><label>Kraj<input name="place" required></label></div><fieldset class="choice-section program-lookup"><legend>Program dogodka</legend><div class="lookup-tools"><input type="search" data-program-search placeholder="Išči po naslovu ali avtorju …"><select data-program-category><option value="">Vse kategorije</option>
% for category in categories:
<option>{{category['name']}}</option>
% end
</select></div><div class="lookup-results">
% for song in songs:
<label class="lookup-song" data-search="{{song['title']}} {{song['author']}}" data-categories="{{'|'.join(song['categories'])}}"><input type="checkbox" name="songs" value="{{song['id']}}"><span><strong>{{song['title']}}</strong><small>{{song['author']}} · {{', '.join(song['categories'])}}</small></span></label>
% end
</div></fieldset><div class="dialog-actions"><button type="button" class="button secondary event-dialog-cancel">Prekliči</button><button type="submit" class="button primary">Shrani dogodek</button></div></form></dialog>

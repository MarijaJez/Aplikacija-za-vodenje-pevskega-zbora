% member = data['personal_member']
% next_event = data['next_event']
<div class="welcome"><div><h2>Živjo, {{current_user['first_name']}}.</h2><p>Tvoj pregled · {{', '.join(current_user['roles']) or 'Pevec'}}</p></div>
% if next_event:
<a class="button primary" href="/dogodki/{{next_event['id']}}">Naslednji dogodek →</a>
% end
</div>
<div class="dashboard-grid personal-dashboard">
<article class="card"><div class="card-head"><div><p class="eyebrow">Moja zasedba</p><h3>Moja prisotnost</h3></div></div>
% if member:
<p><strong>{{str(member['attendance'])+'%' if member['attendance'] is not None else 'Še ni vneseno'}}</strong> · {{member['voice']}}</p><p>Pregled tvoje evidence prisotnosti.</p><a class="text-link" href="/clani/{{member['id']}}">Moja evidenca →</a>
% else:
<p>Podatki o tvojem članstvu niso na voljo.</p>
% end
</article>
<article class="card span-2"><div class="card-head"><div><p class="eyebrow">Priprava</p><h3>{{next_event['title'] if next_event else 'Naslednja vaja ali nastop'}}</h3></div></div>
% if next_event:
<p>{{next_event['date']}} · {{next_event['time']}} · {{next_event['place']}}</p><div class="song-row">
% for song in next_event['program']:
<a href="/program/{{song['id']}}"><span class="song-icon">♫</span><span><strong>{{song['title']}}</strong><small>{{song['author']}}</small></span></a>
% end
</div>
% if not next_event['program']:
<p>Program za ta dogodek še ni določen.</p>
% end
% else:
<p>Trenutno ni napovedane vaje ali nastopa.</p>
% end
</article>
% if 'admin' in permissions:
<article class="card"><h3>Upravljanje zbora</h3><p>Člani, vloge in načrtovanje dogodkov.</p><a class="text-link" href="/clani">Upravljaj člane →</a><p><a href="/dogodki">Načrtuj dogodke →</a></p></article>
% end
% if 'Zborovodja' in current_user['roles'] or 'Notar' in current_user['roles']:
<article class="card"><h3>{{'Vodenje programa' if 'Zborovodja' in current_user['roles'] else 'Moja notna zbirka'}}</h3><p>Pripravi program, note in posnetke za naslednje dogodke.</p><a class="text-link" href="/program">Uredi program →</a></article>
% end
% if 'Beleženje prisotnosti' in current_user['roles']:
<article class="card"><h3>Beleženje prisotnosti</h3><p>Vnesi ali preveri prisotnost članov na vajah in nastopih.</p><a class="text-link" href="/prisotnost">Odpri evidenco →</a></article>
% end
% if data['treasury']:
<article class="card"><h3>Moja blagajna</h3><p>Stanje: <strong>{{'{:,.2f}'.format(data['treasury']['balance']).replace(',', ' ')}} €</strong></p><p>Neporavnano: {{'{:,.2f}'.format(data['treasury']['unsettled']).replace(',', ' ')}} €</p><a class="text-link" href="/blagajna">Uredi blagajno →</a></article>
% end
</div>
% if "admin" in permissions:
<div class="stat-grid">
  <article class="stat-card plum"><span class="stat-icon">♟</span><div><p>Člani zbora</p><strong>{{data['member_count']}}</strong><small>trenutna zasedba</small></div><a href="/clani">Preglej →</a></article>
  <article class="stat-card gold"><span class="stat-icon">♫</span><div><p>Pesmi v programu</p><strong>{{data['song_count']}}</strong><small>v notni zbirki</small></div><a href="/program">Preglej →</a></article>
  <article class="stat-card green"><span class="stat-icon">✓</span><div><p>Povprečna prisotnost</p><strong>{{str(data['average_attendance'])+'%' if data['average_attendance'] is not None else 'Še ni vneseno'}}</strong><small>tekoče šolsko leto</small></div><a href="/prisotnost">Preglej →</a></article>
  <article class="stat-card blue"><span class="stat-icon">◷</span><div><p>Prihajajoči dogodki</p><strong>{{data['upcoming_count']}}</strong><small>Na časovnici zbora</small></div><a href="/dogodki">Preglej →</a></article>
</div>
% end
<div class="dashboard-grid">
  <article class="card span-2"><div class="card-head"><div><p class="eyebrow">Koledar</p><h3>Časovnica dogodkov</h3></div><a href="/dogodki">Vsi dogodki →</a></div><div class="timeline">
% for event in data['events']:
    <a href="/dogodki/{{event['id']}}" class="timeline-row {{event['status']}}"><div class="date-block"><strong>{{event['date'].split('.')[0]}}</strong><span>{{event['date'].split(' ')[1].replace('.','').upper()}}</span></div><i></i><div><span class="badge">{{event['kind']}}</span><h4>{{event['title']}}</h4><p>{{event['time']}} · {{event['place']}}</p></div><span class="arrow">→</span></a>
% end
    % if not data["events"]:
    <p>Trenutno ni prihajajočih dogodkov.</p>
    % end
  </div></article>
% if "admin" in permissions:
  <article class="card"><div class="card-head"><div><p class="eyebrow">Evidenca zbora</p><h3>Najboljša prisotnost</h3></div></div><div class="rank-list">
% for index, member in enumerate(data['top_members']):
    <a href="/clani/{{member['id']}}"><span class="rank">{{index + 1}}</span><span class="avatar small">{{member['initials']}}</span><span><strong>{{member['name']}}</strong><small>{{member['voice']}}</small></span><b>{{str(member['attendance'])+'%' if member['attendance'] is not None else 'Še ni vneseno'}}</b></a>
% end
  </div><hr><p class="mini-title">Potrebujejo spodbudo</p><div class="compact-list">
% for member in data['low_members']:
    <a href="/clani/{{member['id']}}"><span>{{member['name']}}</span><b>{{str(member['attendance'])+'%' if member['attendance'] is not None else 'Še ni vneseno'}}</b></a>
% end
  </div></article>
  <article class="card"><div class="card-head"><div><p class="eyebrow">Zasedba</p><h3>Člani po glasovih</h3></div></div><div class="voice-chart">
% colors = ['#287080','#355C7D','#D09A45','#6E858C']
% for index, voice_stat in enumerate(data['voices']):
    <div><span><i style="background:{{colors[index]}}"></i>{{voice_stat['voice']}}</span><b>{{voice_stat['count']}}</b><div class="bar"><i style="width:{{voice_stat['count'] / max(data['member_count'], 1) * 100}}%;background:{{colors[index]}}"></i></div></div>
% end
  </div><a class="text-link" href="/clani">Odpri seznam članov →</a></article>
% end
  <article class="card span-2"><div class="card-head"><div><p class="eyebrow">Program</p><h3>Sveže v notni mapi</h3></div><a href="/program">Celoten program →</a></div><div class="song-row">
% for song in data['latest_songs']:
    <a href="/program/{{song['id']}}"><span class="song-icon">♫</span><span><strong>{{song['title']}}</strong><small>{{song['author']}}</small></span><span class="rating">★ {{song['rating']}}</span></a>
% end
  </div></article>
</div>

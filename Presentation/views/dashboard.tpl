<div class="welcome"><div><h2>Živjo, {{current_user['first_name']}}.</h2><p>Tukaj je današnji utrip vašega zbora.</p></div><a class="button primary" href="/dogodki/{{data['events'][0]['id']}}">Naslednji dogodek <span>→</span></a></div>
<div class="stat-grid">
  <article class="stat-card plum"><span class="stat-icon">♟</span><div><p>Člani zbora</p><strong>{{data['member_count']}}</strong><small><b>+2</b> v tej sezoni</small></div><a href="/clani">Preglej →</a></article>
  <article class="stat-card gold"><span class="stat-icon">♫</span><div><p>Pesmi v programu</p><strong>{{data['song_count']}}</strong><small><b>+3</b> ta mesec</small></div><a href="/program">Preglej →</a></article>
  <article class="stat-card green"><span class="stat-icon">✓</span><div><p>Povprečna prisotnost</p><strong>{{data['average_attendance']}}%</strong><small>tekoče šolsko leto</small></div><a href="/prisotnost">Preglej →</a></article>
  <article class="stat-card blue"><span class="stat-icon">◷</span><div><p>Prihajajoči dogodki</p><strong>{{data['upcoming_count']}}</strong><small>Na časovnici zbora</small></div><a href="/dogodki">Preglej →</a></article>
</div>
<div class="dashboard-grid">
  <article class="card span-2"><div class="card-head"><div><p class="eyebrow">Koledar</p><h3>Časovnica dogodkov</h3></div><a href="/dogodki">Vsi dogodki →</a></div><div class="timeline">
% for event in data['events']:
    <a href="/dogodki/{{event['id']}}" class="timeline-row {{event['status']}}"><div class="date-block"><strong>{{event['date'].split('.')[0]}}</strong><span>{{event['date'].split(' ')[1].replace('.','').upper()}}</span></div><i></i><div><span class="badge">{{event['kind']}}</span><h4>{{event['title']}}</h4><p>{{event['time']}} · {{event['place']}}</p></div><span class="arrow">→</span></a>
% end
  </div></article>
  <article class="card"><div class="card-head"><div><p class="eyebrow">Ta mesec</p><h3>Najboljša prisotnost</h3></div></div><div class="rank-list">
% for index, member in enumerate(data['top_members']):
    <a href="/clani/{{member['id']}}"><span class="rank">{{index + 1}}</span><span class="avatar small">{{member['initials']}}</span><span><strong>{{member['name']}}</strong><small>{{member['voice']}}</small></span><b>{{member['attendance']}}%</b></a>
% end
  </div><hr><p class="mini-title">Potrebujejo spodbudo</p><div class="compact-list">
% for member in data['low_members']:
    <a href="/clani/{{member['id']}}"><span>{{member['name']}}</span><b>{{member['attendance']}}%</b></a>
% end
  </div></article>
  <article class="card"><div class="card-head"><div><p class="eyebrow">Zasedba</p><h3>Člani po glasovih</h3></div></div><div class="voice-chart">
% colors = ['#287080','#355C7D','#D09A45','#6E858C']
% for index, voice_stat in enumerate(data['voices']):
    <div><span><i style="background:{{colors[index]}}"></i>{{voice_stat['voice']}}</span><b>{{voice_stat['count']}}</b><div class="bar"><i style="width:{{voice_stat['count'] / 12 * 100}}%;background:{{colors[index]}}"></i></div></div>
% end
  </div><a class="text-link" href="/clani">Odpri seznam članov →</a></article>
  <article class="card span-2"><div class="card-head"><div><p class="eyebrow">Program</p><h3>Sveže v notni mapi</h3></div><a href="/program">Celoten program →</a></div><div class="song-row">
% for song in data['latest_songs']:
    <a href="/program/{{song['id']}}"><span class="song-icon">♫</span><span><strong>{{song['title']}}</strong><small>{{song['author']}}</small></span><span class="rating">★ {{song['rating']}}</span></a>
% end
  </div></article>
</div>

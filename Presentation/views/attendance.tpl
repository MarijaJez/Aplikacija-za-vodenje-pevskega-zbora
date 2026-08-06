<form class="page-tools attendance-tools" method="get" action="/prisotnost"><select name="leto" aria-label="Šolsko leto" data-attendance-filter>
% for school_year in data['school_years']:
<option value="{{school_year['start']}}" {{'selected' if school_year['start'] == data['selected_year'] else ''}}>Šolsko leto {{school_year['label']}}</option>
% end
</select><select name="vrsta" aria-label="Vrsta dogodka" data-attendance-filter>
% for event_type in ('Vse','Vaje','Koncerti','Ostalo'):
<option value="{{event_type}}" {{'selected' if event_type == data['selected_type'] else ''}}>{{'Vse vrste dogodkov' if event_type == 'Vse' else event_type}}</option>
% end
</select><span class="autosave"><i></i> Spremembe se shranjujejo sproti</span></form>
% if data['events'] and data['members']:

<article class="card table-card attendance-card"><div class="table-meta"><p><strong>Evidenca prisotnosti</strong><span>Klikni ikono za spremembo statusa; za razlago se pomakni nadnjo.</span></p><div class="legend"><i class="gray"></i>Ni evidentirano <i class="green"></i>Prisoten <i class="blue"></i>Zamuda <i class="gold"></i>Opravičeno <i class="red"></i>Odsoten</div></div><div class="table-wrap attendance-scroll"><table class="attendance-table"><thead><tr><th class="sticky-member">Član</th>
% for event in data['events']:
<th class="event-column"><small>{{event['date'].split(' ')[0]}} {{event['date'].split(' ')[1]}}</small>{{event['title']}}</th>
% end
<th class="total-column"><small>SKUPAJ</small>Ni evidentirano</th><th class="total-column"><small>SKUPAJ</small>Prisoten</th><th class="total-column"><small>SKUPAJ</small>Zamudil &lt; 10</th><th class="total-column"><small>SKUPAJ</small>Zamudil &gt; 10</th><th class="total-column"><small>SKUPAJ</small>Opravičeno</th><th class="total-column"><small>SKUPAJ</small>Odsoten</th></tr></thead><tbody>
% labels = {'unrecorded': ('–', 'Še ni evidentirano'), 'present': ('✓', 'Prisoten'), 'late_under': ('<10', 'Zamudil manj kot 10 minut'), 'late_over': ('>10', 'Zamudil več kot 10 minut'), 'excused': ('O', 'Opravičeno odsoten'), 'absent': ('×', 'Odsoten')}
% for row, member in enumerate(data['members']):
<tr data-member-row="{{row}}"><td class="sticky-member"><a class="person" href="/clani/{{member['id']}}"><span class="avatar small">{{member['initials']}}</span><span><strong>{{member['name']}}</strong><small>{{member['voice']}}</small></span></a></td>
% for col, event in enumerate(data['events']):
% state = data['matrix'][row][col]
<td><button class="attendance-dot {{state}}" data-cycle data-row="{{row}}" data-col="{{col}}" data-person-id="{{member['id']}}" data-event-id="{{event['id']}}" data-status="{{state}}" data-tooltip="{{labels[state][1]}}" aria-label="{{member['name']}} – {{event['title']}}: {{labels[state][1]}}" data-permission="attendance" data-self-editable="{{'true' if member['id'] == current_user['person_id'] and event['status'] == 'upcoming' else 'false'}}">{{labels[state][0]}}</button></td>
% end
% for state in data['status_keys']:
<td class="member-total" data-member-total="{{row}}-{{state}}"><b>{{data['member_totals'][row][state]}}</b></td>
% end
</tr>
% end
</tbody><tfoot>
% summary_labels = [('unrecorded', 'Skupaj še neevidentiranih'), ('present', 'Skupaj prisotnih'), ('late_under', 'Skupaj zamud < 10 min'), ('late_over', 'Skupaj zamud > 10 min'), ('excused', 'Skupaj opravičeno odsotnih'), ('absent', 'Skupaj odsotnih')]
% for summary_state, summary_label in summary_labels:
<tr class="summary-row"><th class="sticky-member">{{summary_label}}</th>
% for col, event in enumerate(data['events']):
<td data-event-total="{{col}}-{{summary_state}}"><b>{{data['event_totals'][col][summary_state]}}</b></td>
% end
% for state in data['status_keys']:
<td class="grand-total {{'highlight' if state == summary_state else ''}}" data-grand-total="{{summary_state}}-{{state}}">{{sum(total[summary_state] for total in data['member_totals']) if state == summary_state else '—'}}</td>
% end
</tr>
% end
</tfoot></table></div></article>

<div class="attendance-kpis"><article><span class="stat-icon green">✓</span><div><p>Povprečna prisotnost na preteklih dogodkih</p><strong>{{data['average']}}%</strong></div></article><article><span class="stat-icon gold">◷</span><div><p>Preteklih dogodkov v statistiki</p><strong>{{data['event_count']}}</strong></div></article><article><span class="stat-icon blue">≋</span><div><p>Najbolj reden glas</p><strong>{{data['best_voice']}} · {{data['best_voice_rate']}}%</strong></div></article></div>
% if data['chart_data']['labels']:

<article class="card attendance-charts"><div class="card-head"><div><p class="eyebrow">Analitika po glasovih</p><h3>Prisotnost skozi šolsko leto</h3><p class="muted">Število članov po dogodkih; črte predstavljajo posamezne glasove.</p></div><div class="voice-legend"><span><i class="soprano"></i>Sopran</span><span><i class="alto"></i>Alt</span><span><i class="tenor"></i>Tenor</span><span><i class="bass"></i>Bas</span></div></div><div class="chart-grid">
  <section class="chart-all"><h4>Skupaj <small>seštevek vseh glasov na preteklih dogodkih</small></h4><canvas data-attendance-chart="all" height="200" aria-label="Skupni graf prisotnosti vseh glasov"></canvas><div class="status-chart-legend"><span><i class="unrecorded"></i>Ni evidentirano</span><span><i class="present"></i>Prisotni</span><span><i class="late-under"></i>Zamuda &lt; 10</span><span><i class="late-over"></i>Zamuda &gt; 10</span><span><i class="excused"></i>Opravičeno</span><span><i class="absent"></i>Odsotni</span></div></section>
  <section><h4>Prisotni</h4><canvas data-attendance-chart="present" height="180" aria-label="Graf prisotnih po glasovih"></canvas></section>
  <section><h4>Zamuda manj kot 10 min</h4><canvas data-attendance-chart="late_under" height="180" aria-label="Graf zamud manj kot 10 minut po glasovih"></canvas></section>
  <section><h4>Zamuda več kot 10 min</h4><canvas data-attendance-chart="late_over" height="180" aria-label="Graf zamud več kot 10 minut po glasovih"></canvas></section>
  <section><h4>Opravičeno odsotni</h4><canvas data-attendance-chart="excused" height="180" aria-label="Graf opravičeno odsotnih po glasovih"></canvas></section>
  <section><h4>Odsotni</h4><canvas data-attendance-chart="absent" height="180" aria-label="Graf odsotnih po glasovih"></canvas></section>
</div></article>
<script id="attendance-data" type="application/json">{{!json.dumps(dict(data['chart_data']), ensure_ascii=False)}}</script>
% else:
<div class="empty-state card"><span>≋</span><h3>Ni še preteklih dogodkov za analitiko</h3><p>Statistika se prikaže, ko je prvi dogodek zaključen.</p><a class="button secondary" href="/dogodki?nov=1" data-permission="admin">Dodaj dogodek</a></div>
% end
% else:
<div class="empty-state card"><span>✓</span>
% if not data['members']:
<h3>Ni še članov za evidenco</h3><p>Pred beleženjem prisotnosti dodaj vsaj enega člana.</p><a class="button primary" href="/clani?nov=1" data-permission="admin">Dodaj člana</a>
% else:
<h3>Ni še dogodkov za evidenco</h3><p>Pred beleženjem prisotnosti dodaj prvo vajo ali dogodek.</p><a class="button primary" href="/dogodki?nov=1" data-permission="admin">Dodaj dogodek</a>
% end
</div>
% end

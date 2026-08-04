const toast = document.querySelector('#toast');
function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
}

document.querySelectorAll('[data-toast]').forEach(el => el.addEventListener('click', event => {
  if (el.tagName === 'A') event.preventDefault();
  showToast(el.dataset.toast);
}));

if (toast?.dataset.message) showToast(toast.dataset.message);

document.querySelector('.mobile-menu')?.addEventListener('click', () => document.querySelector('.sidebar').classList.toggle('open'));

const accountDialog = document.querySelector('#account-dialog');
document.querySelectorAll('[data-account-modal]').forEach(button => button.addEventListener('click', () => accountDialog?.showModal()));
document.querySelector('.account-close')?.addEventListener('click', () => accountDialog.close());
const changePasswordDialog = document.querySelector('#change-password-dialog');
document.querySelector('[data-change-password]')?.addEventListener('click', () => { accountDialog?.close(); changePasswordDialog?.showModal(); });
document.querySelector('.change-password-close')?.addEventListener('click', () => changePasswordDialog.close());
document.querySelector('.change-password-cancel')?.addEventListener('click', () => changePasswordDialog.close());

const memberDialog = document.querySelector('#member-dialog');
const existingUsernames = new Set(['ana.kovac','maja.zupan','luka.mlakar','rok.kos','eva.horvat','miha.novak']);
function usernamePart(value) {
  return value.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '');
}
function updateGeneratedAccount() {
  const first = document.querySelector('#new-first-name')?.value || '';
  const last = document.querySelector('#new-last-name')?.value || '';
  const firstPart = usernamePart(first); const lastPart = usernamePart(last);
  const base = firstPart && lastPart ? `${firstPart}.${lastPart}` : 'ime.priimek';
  let username = base; let suffix = 1;
  while (existingUsernames.has(username)) username = `${base}${suffix++}`;
  document.querySelector('#generated-username')?.replaceChildren(username);
  document.querySelector('#generated-password')?.replaceChildren(username);
  return username;
}
document.querySelector('[data-member-dialog]')?.addEventListener('click', () => { updateGeneratedAccount(); memberDialog?.showModal(); });
document.querySelector('.member-dialog-close')?.addEventListener('click', () => memberDialog.close());
document.querySelector('.member-dialog-cancel')?.addEventListener('click', () => memberDialog.close());
document.querySelectorAll('#new-first-name,#new-last-name').forEach(input => input.addEventListener('input', updateGeneratedAccount));
const memberEditDialog = document.querySelector('#member-edit-dialog');
document.querySelector('[data-member-edit]')?.addEventListener('click', () => memberEditDialog?.showModal());
document.querySelector('.member-edit-close')?.addEventListener('click', () => memberEditDialog.close());
document.querySelector('.member-edit-cancel')?.addEventListener('click', () => memberEditDialog.close());

const resetPasswordDialog = document.querySelector('#reset-password-dialog');
let resetUsername = '';
document.querySelectorAll('[data-password-reset]').forEach(button => button.addEventListener('click', () => {
  resetUsername = button.dataset.passwordReset;
  document.querySelector('#reset-username').textContent = resetUsername;
  document.querySelector('#reset-password-form').action = button.dataset.resetUrl;
  resetPasswordDialog?.showModal();
}));
document.querySelector('.reset-password-close')?.addEventListener('click', () => resetPasswordDialog.close());
document.querySelector('.reset-password-cancel')?.addEventListener('click', () => resetPasswordDialog.close());

const reviewDialog = document.querySelector('#review-dialog');
document.querySelector('[data-review-dialog]')?.addEventListener('click', () => reviewDialog?.showModal());
document.querySelector('.review-dialog-close')?.addEventListener('click', () => reviewDialog.close());
document.querySelector('.review-dialog-cancel')?.addEventListener('click', () => reviewDialog.close());
const transactionDialog = document.querySelector('#transaction-dialog');
document.querySelector('[data-transaction-dialog]')?.addEventListener('click', () => transactionDialog?.showModal());
document.querySelector('.transaction-dialog-close')?.addEventListener('click', () => transactionDialog.close());
document.querySelector('.transaction-dialog-cancel')?.addEventListener('click', () => transactionDialog.close());
const roleDialog = document.querySelector('#role-dialog');
document.querySelector('[data-role-dialog]')?.addEventListener('click', () => roleDialog?.showModal());
document.querySelector('.role-dialog-close')?.addEventListener('click', () => roleDialog.close());
document.querySelector('.role-dialog-cancel')?.addEventListener('click', () => roleDialog.close());
document.querySelectorAll('[data-role-edit]').forEach(button => button.addEventListener('click', () => document.querySelector(`#role-edit-${button.dataset.roleEdit}`)?.showModal()));
document.querySelectorAll('.role-edit-close,.role-edit-cancel').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
const categoryDialog = document.querySelector('#category-dialog');
document.querySelector('[data-category-dialog]')?.addEventListener('click', () => categoryDialog?.showModal());
document.querySelector('.category-dialog-close')?.addEventListener('click', () => categoryDialog.close());
document.querySelector('.category-dialog-cancel')?.addEventListener('click', () => categoryDialog.close());
document.querySelectorAll('[data-category-edit]').forEach(button => button.addEventListener('click', () => document.querySelector(`#category-edit-${button.dataset.categoryEdit}`)?.showModal()));
document.querySelectorAll('.category-edit-close,.category-edit-cancel').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
const songDialog = document.querySelector('#song-dialog');
document.querySelector('[data-song-dialog]')?.addEventListener('click', () => songDialog?.showModal());
document.querySelector('.song-dialog-close')?.addEventListener('click', () => songDialog.close());
document.querySelector('.song-dialog-cancel')?.addEventListener('click', () => songDialog.close());
const songEditDialog = document.querySelector('#song-edit-dialog');
document.querySelector('[data-song-edit]')?.addEventListener('click', () => songEditDialog?.showModal());
document.querySelector('.song-edit-close')?.addEventListener('click', () => songEditDialog.close());
document.querySelector('.song-edit-cancel')?.addEventListener('click', () => songEditDialog.close());
const eventDialog = document.querySelector('#event-dialog');
document.querySelector('[data-event-dialog]')?.addEventListener('click', () => eventDialog?.showModal());
document.querySelector('.event-dialog-close')?.addEventListener('click', () => eventDialog.close());
document.querySelector('.event-dialog-cancel')?.addEventListener('click', () => eventDialog.close());
const eventEditDialog = document.querySelector('#event-edit-dialog');
document.querySelector('[data-event-edit]')?.addEventListener('click', () => eventEditDialog?.showModal());
document.querySelector('.event-edit-close')?.addEventListener('click', () => eventEditDialog.close());
document.querySelector('.event-edit-cancel')?.addEventListener('click', () => eventEditDialog.close());

const playlistSource = document.querySelector('#event-playlist');
const playlistButton = document.querySelector('[data-play-event]');
const playlistStatus = document.querySelector('[data-playlist-status]');
if (playlistSource && playlistButton) {
  const tracks = JSON.parse(playlistSource.textContent || '[]');
  const player = new Audio(); let trackIndex = 0;
  const playTrack = async index => {
    if (!tracks.length) return;
    trackIndex=index; player.src=tracks[index].url;
    if (playlistStatus) playlistStatus.textContent=`Predvaja se: ${tracks[index].title} (${index+1}/${tracks.length})`;
    try { await player.play(); playlistButton.textContent='❚❚ Premor'; } catch { if (playlistStatus) playlistStatus.textContent='Posnetka ni bilo mogoče predvajati.'; }
  };
  player.addEventListener('ended',()=> trackIndex+1<tracks.length ? playTrack(trackIndex+1) : (playlistStatus.textContent='Predvajanje dogodka je končano.'));
  player.addEventListener('error',()=> trackIndex+1<tracks.length ? playTrack(trackIndex+1) : (playlistStatus.textContent='Predvajanje je končano; nekaterih posnetkov ni bilo mogoče odpreti.'));
  playlistButton.addEventListener('click',()=>{ if(!player.src || player.ended) playTrack(0); else if(player.paused){player.play();playlistButton.textContent='❚❚ Premor';} else {player.pause();playlistButton.textContent='▶ Nadaljuj';} });
}

document.querySelectorAll('[data-performance-dialog]').forEach(button => button.addEventListener('click', () => document.querySelector(`#performance-dialog-${button.dataset.performanceDialog}`)?.showModal()));
document.querySelectorAll('.performance-close,.performance-cancel').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
document.querySelectorAll('[data-transaction-edit]').forEach(button => button.addEventListener('click', () => document.querySelector(`#transaction-edit-${button.dataset.transactionEdit}`)?.showModal()));
document.querySelectorAll('.transaction-edit-close,.transaction-edit-cancel').forEach(button => button.addEventListener('click', () => button.closest('dialog')?.close()));
document.querySelectorAll('[data-auto-submit]').forEach(input => input.addEventListener('change', () => input.form?.submit()));

document.querySelectorAll('dialog [required],.login-card [required]').forEach(field => {
  const label = field.closest('label');
  if (label && !label.querySelector('.required-mark')) { label.classList.add('required-field'); const mark=document.createElement('span'); mark.className='required-mark'; mark.textContent='obvezno'; label.appendChild(mark); }
});

function applyMemberFilters() {
  const query=(document.querySelector('[data-filter="members-table"]')?.value || '').toLowerCase();
  const role=document.querySelector('[data-role-filter]')?.value || '';
  document.querySelectorAll('#members-table tbody tr').forEach(row => row.hidden = !row.textContent.toLowerCase().includes(query) || (role && !(row.dataset.roles || '').split('|').includes(role)));
}
document.querySelector('[data-filter="members-table"]')?.addEventListener('input',applyMemberFilters);
document.querySelector('[data-role-filter]')?.addEventListener('change',applyMemberFilters);
applyMemberFilters();

function applySongFilters() {
  const query=(document.querySelector('[data-filter="songs-grid"]')?.value || '').toLowerCase();
  const selected=[...document.querySelectorAll('[data-category-filter]:checked')].map(item=>item.value);
  document.querySelectorAll('.song-card').forEach(card => { const categories=(card.dataset.categories || '').split('|'); card.hidden=!card.textContent.toLowerCase().includes(query) || (selected.length>0 && !selected.some(value=>categories.includes(value))); });
  const count=document.querySelector('[data-category-count]'); if(count) count.textContent=selected.length ? `(${selected.length})` : '';
}
document.querySelector('[data-filter="songs-grid"]')?.addEventListener('input',applySongFilters);
document.querySelectorAll('[data-category-filter]').forEach(item=>item.addEventListener('change',applySongFilters));

function applyProgramLookup(container) {
  const query=(container.querySelector('[data-program-search]')?.value || '').toLowerCase();
  const category=container.querySelector('[data-program-category]')?.value || '';
  container.querySelectorAll('.lookup-song').forEach(song => song.hidden=!(song.dataset.search || '').toLowerCase().includes(query) || (category && !(song.dataset.categories || '').split('|').includes(category)));
}
document.querySelectorAll('.program-lookup').forEach(container => {
  container.querySelector('[data-program-search]')?.addEventListener('input',()=>applyProgramLookup(container));
  container.querySelector('[data-program-category]')?.addEventListener('change',()=>applyProgramLookup(container));
});
document.querySelectorAll('[data-attendance-filter]').forEach(select=>select.addEventListener('change',()=>select.form?.submit()));

const userPermissions = new Set((document.documentElement.dataset.permissions || '').split(',').filter(Boolean));
document.querySelectorAll('[data-permission]').forEach(control => {
  const allowed = userPermissions.has(control.dataset.permission) || control.dataset.selfEditable === 'true';
  if (control.matches('.attendance-dot')) { control.disabled = !allowed; control.classList.toggle('readonly', !allowed); }
  else control.hidden = !allowed;
});

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.querySelectorAll('[data-theme-toggle]').forEach(button => {
    button.textContent = theme === 'dark' ? '☀' : '☾';
    button.setAttribute('aria-label', theme === 'dark' ? 'Preklopi svetli način' : 'Preklopi temni način');
  });
  localStorage.setItem('zborissimo-theme', theme);
  requestAnimationFrame(drawAttendanceCharts);
}
applyTheme(localStorage.getItem('zborissimo-theme') || 'light');
document.querySelectorAll('[data-theme-toggle]').forEach(button => button.addEventListener('click', () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark')));

const attendanceStates = [
  {name:'present', icon:'✓', label:'Prisoten'},
  {name:'late_under', icon:'<10', label:'Zamudil manj kot 10 minut'},
  {name:'late_over', icon:'>10', label:'Zamudil več kot 10 minut'},
  {name:'excused', icon:'O', label:'Opravičeno odsoten'},
  {name:'absent', icon:'×', label:'Odsoten'}
];
const attendanceButtons = [...document.querySelectorAll('[data-cycle]')];
function setAttendanceButton(button, stateName) {
  const state = attendanceStates.find(item => item.name === stateName) || attendanceStates[0];
  attendanceStates.forEach(item => button.classList.remove(item.name));
  button.classList.add(state.name);
  button.dataset.status = state.name;
  button.dataset.tooltip = state.label;
  button.textContent = state.icon;
  const parts = button.getAttribute('aria-label').split(':');
  button.setAttribute('aria-label', `${parts[0]}: ${state.label}`);
}
function updateAttendanceTotals() {
  const rows = [...new Set(attendanceButtons.map(button => button.dataset.row))];
  const cols = [...new Set(attendanceButtons.map(button => button.dataset.col))];
  rows.forEach(row => attendanceStates.forEach(state => {
    const count = attendanceButtons.filter(button => button.dataset.row === row && button.dataset.status === state.name).length;
    const target = document.querySelector(`[data-member-total="${row}-${state.name}"] b`);
    if (target) target.textContent = count;
  }));
  cols.forEach(col => attendanceStates.forEach(state => {
    const count = attendanceButtons.filter(button => button.dataset.col === col && button.dataset.status === state.name).length;
    const target = document.querySelector(`[data-event-total="${col}-${state.name}"] b`);
    if (target) target.textContent = count;
  }));
  attendanceStates.forEach(state => {
    const count = attendanceButtons.filter(button => button.dataset.status === state.name).length;
    const target = document.querySelector(`[data-grand-total="${state.name}-${state.name}"]`);
    if (target) target.textContent = count;
  });
}
updateAttendanceTotals();
attendanceButtons.forEach(button => button.addEventListener('click', async () => {
  const current = attendanceStates.findIndex(item => item.name === button.dataset.status);
  const next = attendanceStates[(current + 1) % attendanceStates.length];
  button.disabled = true;
  const result = await fetch('/api/prisotnost', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({event_id:Number(button.dataset.eventId), person_id:Number(button.dataset.personId), status:next.name})});
  button.disabled = false;
  if (!result.ok) { showToast('Prisotnosti ni bilo mogoče shraniti.'); return; }
  setAttendanceButton(button, next.name);
  updateAttendanceTotals();
  drawAttendanceCharts();
  showToast('Prisotnost je samodejno shranjena.');
}));

function currentAttendanceMatrix() {
  const matrix = [];
  attendanceButtons.forEach(button => {
    const row = Number(button.dataset.row); const col = Number(button.dataset.col);
    matrix[row] ||= []; matrix[row][col] = button.dataset.status;
  });
  return matrix;
}

function drawAttendanceCharts() {
  const source = document.querySelector('#attendance-data');
  if (!source) return;
  const data = JSON.parse(source.textContent);
  if (!data.labels.length) return;
  const matrix = currentAttendanceMatrix();
  const voiceNames = ['Sopran','Alt','Tenor','Bas'];
  const voiceColors = ['#287080','#355C7D','#D09A45','#6E858C'];
  const statusColors = ['#4F8174','#4E86A0','#7478A0','#D09A45','#B45F5A'];
  const dark = document.documentElement.dataset.theme === 'dark';
  document.querySelectorAll('[data-attendance-chart]').forEach(canvas => {
    const status = canvas.dataset.attendanceChart;
    const width = Math.max(canvas.parentElement.clientWidth - 28, 260);
    const height = status === 'all' ? 200 : 180; const ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio; canvas.height = height * ratio;
    canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
    const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio);
    const pad = {l:28,r:12,t:12,b:30}; const plotW = width-pad.l-pad.r; const plotH = height-pad.t-pad.b;
    const maxY = status === 'all' ? matrix.length : Math.max(...voiceNames.map(voice => data.voices.filter(item => item === voice).length), 1);
    ctx.font = '9px DM Sans'; ctx.lineWidth = 1; ctx.strokeStyle = dark ? '#44566a' : '#e2d8ca'; ctx.fillStyle = dark ? '#a8b4c0' : '#776d62';
    for(let y=0;y<=maxY;y++){const py=pad.t+plotH-(y/maxY)*plotH;ctx.beginPath();ctx.moveTo(pad.l,py);ctx.lineTo(width-pad.r,py);ctx.stroke();ctx.fillText(y,7,py+3)}
    data.labels.forEach((label,index)=>{const x=pad.l+(index/Math.max(data.labels.length-1,1))*plotW;ctx.fillText(label,x-13,height-9)});
    const series = status === 'all' ? attendanceStates.map(state => state.name) : voiceNames;
    series.forEach((seriesName,seriesIndex)=>{
      const values=data.labels.map((_,col)=>matrix.reduce((sum,row,rowIndex)=>sum+(status === 'all' ? row[col]===seriesName : data.voices[rowIndex]===seriesName&&row[col]===status?1:0),0));
      ctx.strokeStyle=(status === 'all' ? statusColors : voiceColors)[seriesIndex];ctx.fillStyle=(status === 'all' ? statusColors : voiceColors)[seriesIndex];ctx.lineWidth=2;ctx.beginPath();
      values.forEach((value,index)=>{const x=pad.l+(index/Math.max(values.length-1,1))*plotW;const y=pad.t+plotH-(value/maxY)*plotH;index?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();
      values.forEach((value,index)=>{const x=pad.l+(index/Math.max(values.length-1,1))*plotW;const y=pad.t+plotH-(value/maxY)*plotH;ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill()});
    });
  });
}
drawAttendanceCharts();
window.addEventListener('resize', drawAttendanceCharts);

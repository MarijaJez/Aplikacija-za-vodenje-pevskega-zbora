(() => {
  const list = document.querySelector('[data-chat-list]');
  if (!list) return;
  const currentUser = Number(list.dataset.currentUser);
  const admin = list.dataset.admin === '1';
  const csrf = list.dataset.csrf;
  let previous = '';

  function el(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  }

  function hiddenToken(form) {
    const field = el('input');
    field.type = 'hidden';
    field.name = 'csrf';
    field.value = csrf;
    form.append(field);
  }

  function draw(items) {
    const nearBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 90;
    const fragment = document.createDocumentFragment();
    for (const item of items) {
      const li = el('li', 'community-message' + (item.deleted ? ' is-deleted' : ''));
      const meta = el('div', 'community-message-meta');
      meta.append(el('strong', '', item.author));
      const date = new Date(item.created_at);
      const time = el('time', '', date.toLocaleString('sl-SI', {dateStyle:'short', timeStyle:'short'}));
      time.dateTime = item.created_at;
      meta.append(time);
      if (item.edited) meta.append(el('span', '', '· urejeno'));
      li.append(meta, el('p', '', item.body));
      if (!item.deleted && item.author_id === currentUser) {
        const details = el('details');
        details.append(el('summary', '', 'Uredi'));
        const form = el('form');
        form.method = 'post';
        form.action = `/klepet/${item.id}/uredi`;
        hiddenToken(form);
        const label = el('label', '', 'Besedilo');
        const textarea = el('textarea');
        textarea.name = 'body';
        textarea.maxLength = 2000;
        textarea.required = true;
        textarea.value = item.body;
        label.append(textarea);
        const save = el('button', 'button secondary', 'Shrani');
        save.type = 'submit';
        form.append(label, save);
        details.append(form);
        li.append(details);
      }
      if (!item.deleted && (item.author_id === currentUser || admin)) {
        const form = el('form');
        form.method = 'post';
        form.action = `/klepet/${item.id}/izbrisi`;
        form.addEventListener('submit', event => {
          if (!confirm('Izbrišem sporočilo?')) event.preventDefault();
        });
        hiddenToken(form);
        const button = el('button', 'community-delete', 'Izbriši');
        button.type = 'submit';
        form.append(button);
        li.append(form);
      }
      fragment.append(li);
    }
    list.replaceChildren(fragment);
    if (nearBottom) list.scrollTop = list.scrollHeight;
  }

  async function refresh() {
    if (document.hidden || list.contains(document.activeElement)) return;
    try {
      const result = await fetch('/api/klepet', {credentials:'same-origin', cache:'no-store'});
      if (!result.ok) return;
      const items = await result.json();
      if (!Array.isArray(items)) return;
      const signature = JSON.stringify(items);
      if (signature !== previous) { previous = signature; draw(items); }
    } catch (_) { /* The next scheduled refresh will retry. */ }
  }
  refresh();
  setInterval(refresh, 10000);
})();

(() => {
  const form = document.querySelector('#event-dialog form');
  if (!form) return;
  const dialog = form.closest('dialog');
  const buttons = [...dialog.querySelectorAll('button')];
  const originals = buttons.map(button => ({button, disabled: button.disabled, text: button.textContent}));
  const status = document.createElement('p');
  status.setAttribute('role', 'status');
  form.append(status);
  let saving = false;
  form.addEventListener('submit', event => {
    if (saving) {
      event.preventDefault();
      return;
    }
    if (event.defaultPrevented) return;
    saving = true;
    form.setAttribute('aria-busy', 'true');
    buttons.forEach(button => { button.disabled = true; });
    const submit = event.submitter || form.querySelector('button[type="submit"]');
    if (submit) submit.textContent = 'Shranjujem …';
    status.textContent = 'Dogodek se shranjuje. Počakaj na potrditev.';
  });
  dialog.addEventListener('cancel', event => {
    if (saving) event.preventDefault();
  });
  window.addEventListener('pageshow', () => {
    saving = false;
    form.removeAttribute('aria-busy');
    status.textContent = '';
    originals.forEach(({button, disabled, text}) => {
      button.disabled = disabled;
      button.textContent = text;
    });
  });
})();

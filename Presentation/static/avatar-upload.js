document.querySelectorAll('[data-avatar-upload]').forEach(form => {
  const input = form.querySelector('input[type="file"]');
  const button = form.querySelector('[data-avatar-choose]');
  const status = form.querySelector('[role="status"]');
  button.addEventListener('click', () => input.click());
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
      status.textContent = 'Slika je prevelika. Izberi sliko do 8 MB.';
      input.value = '';
      return;
    }
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
    status.textContent = 'Shranjujem sliko ...';
    form.requestSubmit();
  });
});

document.querySelectorAll('[data-member-attendance]').forEach(select => {
  select.addEventListener('change', async () => {
    select.disabled = true;
    const result = await fetch('/api/prisotnost', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({event_id: Number(select.dataset.eventId), person_id: Number(select.dataset.personId), status: select.value})
    }).catch(() => null);
    if (!result?.ok) {
      select.value = select.dataset.savedStatus;
      select.disabled = false;
      showToast('Prisotnosti ni bilo mogoče shraniti. Poskusi znova.');
      return;
    }
    window.location.reload();
  });
});

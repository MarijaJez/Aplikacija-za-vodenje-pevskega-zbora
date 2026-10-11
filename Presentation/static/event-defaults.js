(() => {
  const form = document.querySelector('#event-dialog form');
  if (!form) return;
  const start = form.elements.event_date;
  const end = form.elements.event_end;
  let manuallyEdited = Boolean(end.value);

  const updateEnd = () => {
    if (manuallyEdited) return;
    if (!start.value) {
      end.value = '';
      return;
    }
    // Use calendar arithmetic: datetime-local represents local wall time.
    const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(start.value);
    if (!match) return;
    const [, year, month, day, hour, minute] = match.map(Number);
    const date = new Date(0);
    date.setUTCFullYear(year, month - 1, day);
    date.setUTCHours(hour + 2, minute, 0, 0);
    end.value = date.toISOString().slice(0, 16);
  };

  start.addEventListener('input', updateEnd);
  start.addEventListener('change', updateEnd);
  const markEdited = () => { manuallyEdited = true; };
  end.addEventListener('input', markEdited);
  end.addEventListener('change', markEdited);
  form.addEventListener('reset', () => {
    manuallyEdited = Boolean(end.defaultValue);
  });
  updateEnd();
})();

const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../Presentation/static/event-defaults.js'), 'utf8');

function setup(initialEnd = '') {
  const field = (value = '') => ({value, defaultValue: value, listeners: {},
    addEventListener(type, handler) { this.listeners[type] = handler; },
    fire(type, value) { this.value = value; this.listeners[type](); }});
  const start = field();
  const end = field(initialEnd);
  const form = {elements: {event_date: start, event_end: end}, listeners: {},
    addEventListener(type, handler) { this.listeners[type] = handler; }};
  vm.runInNewContext(script, {document: {querySelector: () => form}, Date});
  return {start, end, form};
}

test('default follows start until end is edited', () => {
  const {start, end} = setup();
  start.fire('input', '2026-12-01T18:15');
  assert.equal(end.value, '2026-12-01T20:15');
  start.fire('change', '2026-12-01T19:30');
  assert.equal(end.value, '2026-12-01T21:30');
  end.fire('input', '2026-12-01T22:00');
  start.fire('input', '2026-12-01T20:00');
  assert.equal(end.value, '2026-12-01T22:00');
  end.fire('change', '');
  start.fire('change', '2026-12-01T21:00');
  assert.equal(end.value, '');
});

test('late starts roll over midnight, month and year', () => {
  const {start, end} = setup();
  for (const [value, expected] of [
    ['2026-12-01T23:30', '2026-12-02T01:30'],
    ['2026-12-31T23:00', '2027-01-01T01:00'],
    ['2028-02-29T23:00', '2028-03-01T01:00'],
    ['2026-03-29T01:30', '2026-03-29T03:30'],
  ]) {
    start.fire('input', value);
    assert.equal(end.value, expected);
  }
  start.fire('input', '');
  assert.equal(end.value, '');
});

test('preserves initial end and restores defaults after form reset', () => {
  const existing = setup('2026-12-01T22:00');
  existing.start.fire('input', '2026-12-01T19:00');
  assert.equal(existing.end.value, '2026-12-01T22:00');
  const {start, end, form} = setup();
  end.fire('input', '2026-12-01T22:00');
  form.listeners.reset();
  start.fire('input', '2026-12-02T18:00');
  assert.equal(end.value, '2026-12-02T20:00');
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { panelValues, OFFLINE_TEXT } from '../panel.js';

// Every counter (c-) and box card value (b-) on the page.
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const ids = [...html.matchAll(/id="([cb]-[a-z]+)"/g)].map((m) => m[1]);
const real = Object.fromEntries(ids.map((id, i) => [id, i % 2 ? i : `value ${i}`]));

test('the page has all six counters and all six box card values', () => {
  assert.equal(ids.filter((id) => id.startsWith('c-')).length, 6);
  assert.equal(ids.filter((id) => id.startsWith('b-')).length, 6);
});

test('hub offline shows "--" in every counter and box card value', () => {
  assert.equal(OFFLINE_TEXT, '--');
  const shown = panelValues(real, 'offline');
  assert.deepEqual(Object.keys(shown), ids);
  for (const id of ids) assert.equal(shown[id], '--', id);
});

test('hub connected shows the real values again', () => {
  assert.deepEqual(panelValues(real, 'connected'), real);
});

test('the first connect before any hub status shows the real values', () => {
  assert.deepEqual(panelValues(real, 'connecting'), real);
});

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { generateHomes, BOUNDS, REAL_BOX_ID } from '../homes.js';

test('the seeded generator returns the same homes every run', () => {
  assert.deepEqual(generateHomes(), generateHomes());
});

test('the first homes are pinned so a change to the generator shows up', () => {
  const [, h1, h2] = generateHomes();
  assert.deepEqual(
    [h1, h2].map((h) => [h.id, h.lat.toFixed(5), h.lon.toFixed(5), h.device, h.outcome]),
    PINNED,
  );
});

test('500 homes, unique ids, all inside the Richardson box', () => {
  const homes = generateHomes();
  assert.equal(homes.length, 500);
  assert.equal(new Set(homes.map((h) => h.id)).size, 500);
  for (const h of homes) {
    assert.ok(h.lat >= BOUNDS.latMin && h.lat <= BOUNDS.latMax, h.id);
    assert.ok(h.lon >= BOUNDS.lonMin && h.lon <= BOUNDS.lonMax, h.id);
  }
});

test('H000 is the real box, first, and has no scripted outcome', () => {
  const [h0] = generateHomes();
  assert.equal(h0.id, REAL_BOX_ID);
  assert.equal(h0.real, true);
  assert.equal(h0.outcome, null);
  assert.equal(generateHomes().filter((h) => h.real).length, 1);
});

test('most simulated homes answer ok, some no answer, some help', () => {
  const sims = generateHomes().filter((h) => !h.real);
  const count = (o) => sims.filter((h) => h.outcome === o).length;
  assert.ok(count('ok') > sims.length / 2);
  assert.ok(count('no_answer') > 0);
  assert.ok(count('help') > 0);
  assert.ok(sims.some((h) => h.skipped), 'some homes are missed so the coverage rule has work');
});

test('a battery clock exists exactly for homes with a device', () => {
  for (const h of generateHomes()) {
    assert.equal(h.battery_min === null, h.device === 'none', h.id);
  }
});

// Update only on a deliberate generator change.
const PINNED = [
  ['H001', '33.00168', '-96.79532', 'none', 'no_answer'],
  ['H002', '32.98607', '-96.78090', 'wheelchair', 'ok'],
];

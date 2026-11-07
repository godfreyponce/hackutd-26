import { test } from 'node:test';
import assert from 'node:assert/strict';
import { nextAttempts, coverageSweep, answerFor, MAX_TRIES } from '../sim.js';

const WINDOW = 1000;
const state = (id, over = {}) => [id, { id, real: false, skipped: false, hitAt: 0, attempts: 0, ...over }];
const world = () =>
  new Map([
    state('H000', { real: true }),
    state('H001'),
    state('H002', { skipped: true }),
    state('H003'),
    state('H004', { skipped: true }),
    state('H005', { hitAt: null }),
  ]);
const ranked = ['H004', 'H003', 'H002', 'H001', 'H000', 'H005'];

test('the dispatcher calls hit homes in rank order and passes over the skipped ones', () => {
  const w = world();
  assert.deepEqual(nextAttempts(ranked, w, 1), ['H003']);
  assert.deepEqual(nextAttempts(ranked, w, 9), ['H003', 'H001']);
});

test('coverage rule: nothing is forced before the window ends', () => {
  const w = world();
  for (const id of nextAttempts(ranked, w, 9)) w.get(id).attempts = 1;
  assert.deepEqual(coverageSweep(w, WINDOW - 1, WINDOW), []);
});

test('coverage rule: every untouched hit home gets a forced recheck, so all hit homes get a contact attempt', () => {
  const w = world();
  for (const id of nextAttempts(ranked, w, 9)) w.get(id).attempts = 1;
  const forced = coverageSweep(w, WINDOW, WINDOW);
  assert.deepEqual(forced.sort(), ['H002', 'H004']);
  for (const id of forced) w.get(id).attempts = 1;
  const simHit = [...w.values()].filter((s) => !s.real && s.hitAt !== null);
  assert.ok(simHit.every((s) => s.attempts > 0));
});

test('coverage rule: homes not hit and the real box are left alone', () => {
  const swept = coverageSweep(world(), 10 * WINDOW, WINDOW);
  assert.ok(!swept.includes('H005'));
  assert.ok(!swept.includes('H000'));
});

test('scripted answers per try', () => {
  assert.equal(answerFor({ outcome: 'ok' }, 1), 'ok');
  assert.equal(answerFor({ outcome: 'help' }, 1), 'help');
  assert.equal(answerFor({ outcome: 'no_answer' }, 1), 'no_answer');
  assert.equal(answerFor({ outcome: 'no_answer' }, MAX_TRIES), 'no_answer');
  assert.equal(answerFor({ outcome: 'late_ok' }, 1), 'no_answer');
  assert.equal(answerFor({ outcome: 'late_ok' }, 2), 'ok');
});

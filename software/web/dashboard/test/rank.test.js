import { test } from 'node:test';
import assert from 'node:assert/strict';
import { harmClock, rankHomes, queueMessage, checkMove, applyRerank, FACTOR_KEYS } from '../rank.js';
import { generateHomes } from '../homes.js';

const home = (id, over = {}) => ({
  id,
  device: 'none',
  battery_min: null,
  vulnerable: false,
  indoor_f: 70,
  presence: 'moving',
  stale: false,
  no_answer: 0,
  said_help: false,
  answered_ok: false,
  alarm: false,
  ...over,
});

const order = (homes) => rankHomes(homes).map((r) => r.id);

test('battery beats cold when its clock is lower', () => {
  const battery = home('H001', { device: 'o2', battery_min: 40 });
  const cold = home('H002', { vulnerable: true, indoor_f: 50 });
  assert.equal(harmClock(battery).harm_min, 40);
  assert.equal(harmClock(cold).harm_min, 135);
  assert.deepEqual(order([cold, battery]), ['H001', 'H002']);
});

test('cold beats battery when its clock is lower', () => {
  const battery = home('H001', { device: 'o2', battery_min: 200 });
  const cold = home('H002', { vulnerable: true, indoor_f: 40 });
  assert.deepEqual(order([battery, cold]), ['H002', 'H001']);
});

test('a home with both inputs takes the lower clock', () => {
  const h = home('H001', { device: 'o2', battery_min: 300, vulnerable: true, indoor_f: 40 });
  assert.equal(harmClock(h).harm_min, 60);
});

test('device class weight: life-sustaining x1, important x1.5, comfort x3', () => {
  assert.equal(harmClock(home('H1', { device: 'o2', battery_min: 80 })).harm_min, 80);
  assert.equal(harmClock(home('H2', { device: 'cpap', battery_min: 60 })).harm_min, 90);
  assert.equal(harmClock(home('H3', { device: 'wheelchair', battery_min: 100 })).harm_min, 300);
});

test('no device and warm: 720 min, or 240 if vulnerable', () => {
  assert.equal(harmClock(home('H1')).harm_min, 720);
  assert.equal(harmClock(home('H2', { vulnerable: true })).harm_min, 240);
});

test('said help goes to the top with clock 0', () => {
  const help = home('H009', { said_help: true });
  const urgent = home('H001', { device: 'dialysis', battery_min: 20 });
  assert.equal(harmClock(help).harm_min, 0);
  assert.deepEqual(order([urgent, help]), ['H009', 'H001']);
});

test('an alarm on the real box counts like help', () => {
  assert.equal(harmClock(home('H000', { alarm: true })).harm_min, 0);
});

test('unresponsive rises: one miss x0.75, two or more x0.5', () => {
  const quiet = home('H003');
  const once = home('H002', { no_answer: 1 });
  const twice = home('H001', { no_answer: 2 });
  assert.equal(harmClock(once).harm_min, 540);
  assert.equal(harmClock(twice).harm_min, 360);
  assert.equal(harmClock(home('H4', { no_answer: 3 })).harm_min, 360);
  assert.deepEqual(order([quiet, once, twice]), ['H001', 'H002', 'H003']);
});

test('still person x0.5, nobody home x2', () => {
  assert.equal(harmClock(home('H1', { presence: 'still' })).harm_min, 360);
  assert.equal(harmClock(home('H2', { presence: 'none' })).harm_min, 1440);
});

test('stale data x0.75, answered ok x1.5', () => {
  assert.equal(harmClock(home('H1', { stale: true })).harm_min, 540);
  assert.equal(harmClock(home('H2', { answered_ok: true })).harm_min, 1080);
});

test('factors carry exactly the contract keys', () => {
  const r = harmClock(home('H1', { device: 'o2', battery_min: 38, indoor_f: 51, no_answer: 1, presence: 'still', stale: true }));
  assert.deepEqual(Object.keys(r.factors).sort(), [...FACTOR_KEYS].sort());
  assert.deepEqual(r.factors, { battery_min: 38, indoor_f: 51, unresponsive: true, still: true, stale: true, said_help: false });
});

test('ties break by id so the order is stable', () => {
  assert.deepEqual(order([home('H003'), home('H001'), home('H002')]), ['H001', 'H002', 'H003']);
});

test('ranking 500 homes takes under a second', () => {
  const homes = generateHomes();
  const start = performance.now();
  const ranked = rankHomes(homes.map((h) => ({ ...h, no_answer: 0, said_help: false, answered_ok: false, alarm: false })));
  const ms = performance.now() - start;
  assert.equal(ranked.length, 500);
  assert.ok(ms < 1000, `took ${ms} ms`);
});

test('queue message holds the top 20 in contract shape', () => {
  const homes = Array.from({ length: 30 }, (_, i) => home(`H${String(i).padStart(3, '0')}`, { device: 'o2', battery_min: 100 + i }));
  const msg = queueMessage(rankHomes(homes));
  assert.equal(msg.type, 'queue');
  assert.equal(msg.homes.length, 20);
  assert.deepEqual(Object.keys(msg.homes[0]).sort(), ['factors', 'harm_min', 'id']);
  assert.equal(msg.homes[0].id, 'H000');
  assert.equal(msg.homes[0].harm_min, 100);
});

// Guardrail. Queue rows only need id, harm_min and factors.said_help.
const row = (id, harm_min, said_help = false) => ({ id, harm_min, factors: { said_help } });
const queue = () => [row('A', 0, true), row('B', 20), row('C', 45), row('D', 60), row('E', 90), row('F', 120)];
const ids = (q) => q.map((r) => r.id).join('');

test('guardrail: a valid move is applied', () => {
  const { queue: q, results } = applyRerank(queue(), [{ id: 'F', by: -2, factor: 'battery_min' }]);
  assert.equal(results[0].ok, true);
  assert.equal(ids(q), 'ABCFDE');
});

test('guardrail: a valid demotion of an unprotected home is applied', () => {
  const { queue: q, results } = applyRerank(queue(), [{ id: 'C', by: 2, factor: 'stale' }]);
  assert.equal(results[0].ok, true);
  assert.equal(ids(q), 'ABDECF');
});

test('guardrail: more than 3 places is rejected', () => {
  const reason = checkMove(queue(), { id: 'F', by: -4, factor: 'battery_min' });
  assert.match(reason, /3 places/);
});

test('guardrail: a move without a named factor is rejected', () => {
  assert.match(checkMove(queue(), { id: 'F', by: -1 }), /factor/);
  assert.match(checkMove(queue(), { id: 'F', by: -1, factor: 'vibes' }), /factor/);
});

test('guardrail: demoting a home under 30 min is rejected', () => {
  assert.match(checkMove(queue(), { id: 'B', by: 1, factor: 'stale' }), /under 30 min/);
});

test('guardrail: demoting a home that said help is rejected', () => {
  assert.match(checkMove(queue(), { id: 'A', by: 1, factor: 'still' }), /help/);
});

test('guardrail: a promotion that pushes a protected home down is rejected', () => {
  assert.match(checkMove(queue(), { id: 'D', by: -2, factor: 'still' }), /B/);
});

test('guardrail: unknown home and zero or fractional moves are rejected', () => {
  assert.match(checkMove(queue(), { id: 'Z', by: -1, factor: 'still' }), /not in the queue/);
  assert.ok(checkMove(queue(), { id: 'F', by: 0, factor: 'still' }));
  assert.ok(checkMove(queue(), { id: 'F', by: -1.5, factor: 'still' }));
});

test('guardrail: bad moves are dropped, good moves in the same batch still apply', () => {
  const { queue: q, results } = applyRerank(queue(), [
    { id: 'F', by: -9, factor: 'battery_min' },
    { id: 'E', by: -1, factor: 'unresponsive' },
  ]);
  assert.deepEqual(results.map((r) => r.ok), [false, true]);
  assert.equal(ids(q), 'ABCEDF');
});

test('guardrail: a move past the bottom stops at the last place', () => {
  const { queue: q, results } = applyRerank(queue(), [{ id: 'E', by: 3, factor: 'stale' }]);
  assert.equal(results[0].ok, true);
  assert.equal(ids(q), 'ABCDFE');
});

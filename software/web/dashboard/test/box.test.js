import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialBox, applyBoxEvent, boxRankInput, STALE_MS } from '../box.js';
import { generateHomes } from '../homes.js';
import { rankHomes } from '../rank.js';

const run = (msgs, t = 0) => msgs.reduce((s, m) => applyBoxEvent(s, m, t), initialBox(t));

function rankOfBox(box, now = 0) {
  const [, ...sims] = generateHomes();
  const homes = [boxRankInput(box, now), ...sims.map((h) => ({ ...h, no_answer: 0, said_help: false, answered_ok: false, alarm: false }))];
  return rankHomes(homes).findIndex((r) => r.id === 'H000') + 1;
}

test('presence moves the real box between moving, still and none', () => {
  assert.equal(run([{ type: 'presence', state: 'still' }]).presence, 'still');
  assert.equal(run([{ type: 'presence', state: 'still' }, { type: 'presence', state: 'moving' }]).presence, 'moving');
});

test('no answer counts tries once, even when checkin and heard both report it', () => {
  const s = run([
    { type: 'checkin', state: 'asking', try: 1 },
    { type: 'heard', answer: 'no_answer', transcript: '' },
    { type: 'checkin', state: 'no_answer', try: 1 },
    { type: 'checkin', state: 'asking', try: 2 },
    { type: 'heard', answer: 'no_answer', transcript: '' },
  ]);
  assert.equal(s.no_answer, 2);
});

test('help and alarm put the real box at clock 0; ok and clear bring it back', () => {
  assert.equal(run([{ type: 'heard', answer: 'help', transcript: 'help me' }]).said_help, true);
  assert.equal(run([{ type: 'checkin', state: 'alarm', try: 4 }]).alarm, true);
  const cleared = run([
    { type: 'checkin', state: 'no_answer', try: 3 },
    { type: 'checkin', state: 'alarm', try: 4 },
    { type: 'heard', answer: 'ok', transcript: "I'm okay" },
    { type: 'checkin', state: 'clear' },
  ]);
  assert.deepEqual([cleared.alarm, cleared.no_answer, cleared.said_help, cleared.answered_ok], [false, 0, false, true]);
});

test('the real box goes stale after 5 minutes without a sensor message', () => {
  const s = initialBox(0);
  assert.equal(boxRankInput(s, STALE_MS).stale, false);
  assert.equal(boxRankInput(s, STALE_MS + 1).stale, true);
  assert.equal(boxRankInput(applyBoxEvent(s, { type: 'heartbeat', battery_pct: 80 }, STALE_MS), STALE_MS + 1).stale, false);
});

test('when Rafael lies still and does not answer, his row climbs to the top', () => {
  const start = rankOfBox(initialBox(0));
  const still = run([{ type: 'presence', state: 'still' }]);
  const quiet = run([{ type: 'presence', state: 'still' }, { type: 'checkin', state: 'no_answer', try: 2 }]);
  const alarm = applyBoxEvent(quiet, { type: 'checkin', state: 'alarm', try: 4 }, 0);
  const ranks = [start, rankOfBox(still), rankOfBox(quiet), rankOfBox(alarm)];
  assert.ok(ranks[0] > ranks[1] && ranks[1] > ranks[2] && ranks[2] > ranks[3], ranks.join(' > '));
  assert.equal(ranks[3], 1);
});

test('reset returns the real box to its start state', () => {
  const s = run([{ type: 'presence', state: 'still' }, { type: 'checkin', state: 'alarm', try: 4 }]);
  assert.deepEqual(applyBoxEvent(s, { type: 'reset' }, 7), initialBox(7));
});

test('a handoff for H000 is kept until reset; one for another home is ignored', () => {
  const msg = {
    type: 'handoff', home: 'H000', note: 'No answer on 3 tries.', by: 'nemotron',
    contact: { id: 'godfrey', name: 'Godfrey', role: 'family contact, demo' }, why: ['Someone is there.'], why_by: 'template',
  };
  const s = run([{ type: 'checkin', state: 'alarm', try: 4 }, msg]);
  assert.deepEqual(s.handoff, { note: msg.note, contact: msg.contact, by: 'nemotron', why: msg.why, why_by: 'template' });
  assert.equal(run([{ ...msg, home: 'H042' }]).handoff, null);
  assert.equal(applyBoxEvent(s, { type: 'reset' }, 0).handoff, null);
});

test('a help sign is kept for the event line until reset', () => {
  const help = { type: 'help_gesture', source: 'camera' };
  assert.equal(initialBox(0).helpSign, false);
  assert.equal(run([help]).helpSign, true);
  assert.equal(run([help, { type: 'checkin', state: 'ok', try: 1 }]).helpSign, true);
  assert.equal(run([help, { type: 'reset' }]).helpSign, false);
});

test('a new check-in starts fresh: ok last time, no answer now is a no answer', () => {
  const s = run([
    { type: 'checkin', state: 'asking', try: 1 },
    { type: 'heard', answer: 'ok', transcript: "I'm okay" },
    { type: 'checkin', state: 'ok', try: 1 },
    { type: 'checkin', state: 'asking', try: 1 },
    { type: 'heard', answer: 'no_answer', transcript: '' },
    { type: 'checkin', state: 'no_answer', try: 1 },
  ]);
  assert.deepEqual([s.answered_ok, s.no_answer], [false, 1]);
});

test('a new check-in after a no-alarm no answer is still asking, with nothing heard yet', () => {
  const s = run([
    { type: 'checkin', state: 'asking', try: 1 },
    { type: 'checkin', state: 'no_answer', try: 1 },
    { type: 'checkin', state: 'asking', try: 1 },
  ]);
  assert.deepEqual([s.no_answer, s.said_help, s.answered_ok, s.heard], [0, false, false, null]);
});

test('the stand-up re-ask after an alarm keeps the alarm up', () => {
  const s = run([
    { type: 'checkin', state: 'no_answer', try: 3 },
    { type: 'checkin', state: 'alarm', try: 4 },
    { type: 'checkin', state: 'asking', try: 1 },
  ]);
  assert.deepEqual([s.alarm, s.no_answer], [true, 3]);
});

test('the alarm after 3 asks is not counted as a 4th try', () => {
  const asks = [1, 2, 3].flatMap((n) => [
    { type: 'checkin', state: 'asking', try: n },
    { type: 'checkin', state: 'no_answer', try: n },
  ]);
  const s = run([...asks, { type: 'checkin', state: 'alarm', try: 4 }]);
  assert.equal(s.try, 3, 'the box panel prints this as "Alarm, try N"');
  const late = applyBoxEvent(s, { type: 'heard', answer: 'no_answer', transcript: '' }, 0);
  assert.equal(late.no_answer, 3);
});

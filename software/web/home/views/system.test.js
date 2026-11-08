import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialHistory, record, LIVE_MS } from '../state.js';
import { systemModel } from './system.js';

const T = 1_000_000;
const up = (now, linkAt = T - 60_000) => ({ now, connected: true, linkAt });
const down = (now, linkAt) => ({ now, connected: false, linkAt });

// Each message arrives one second after the one before it.
function run(...msgs) {
  return msgs.reduce((h, m, i) => record(h, m, T + i * 1000), initialHistory());
}

const part = (model, id) => model.parts.find((p) => p.id === id);
const fact = (p, label) => p.facts.find((f) => f.label === label)?.value;
const allText = (model) => JSON.stringify(model);

test('the head says the hub is connected, with no final period', () => {
  const m = systemModel(initialHistory(), up(T));
  assert.match(m.detail, /^Hub connected/);
  assert.doesNotMatch(m.detail, /\.$/);
});

test('one card per part, in a fixed order, each with a role and a note', () => {
  const m = systemModel(initialHistory(), up(T));
  assert.deepEqual(m.parts.map((p) => p.id), ['hub', 'sensors', 'presence', 'camera', 'agent', 'voice']);
  for (const p of m.parts) {
    assert.ok(p.role, `${p.name} has a role line`);
    assert.ok(p.note, `${p.name} has a note`);
  }
});

test('the hub card shows when the link opened and the last message', () => {
  const h = run({ type: 'heartbeat', battery_pct: 100 });
  const hub = part(systemModel(h, up(T + 3000, T - 60_000)), 'hub');
  assert.deepEqual(hub.status, { text: 'Connected', tone: 'ok' });
  assert.ok(fact(hub, 'Connected since') && fact(hub, 'Connected since') !== '--');
  assert.equal(fact(hub, 'Last message'), '3 s ago');
});

test('with nothing heard yet, every time is a dash and nothing claims to be reporting', () => {
  const m = systemModel(initialHistory(), up(T));
  assert.equal(fact(part(m, 'hub'), 'Last message'), '--');
  for (const id of ['sensors', 'presence', 'camera', 'agent', 'voice']) {
    assert.deepEqual(part(m, id).status, { text: 'Not heard yet', tone: '' }, id);
  }
  const s = part(m, 'sensors');
  assert.deepEqual([fact(s, 'Last message'), fact(s, 'Battery'), fact(s, 'Power')], ['--', '--', '--']);
  assert.equal(m.detail, 'Hub connected. No heartbeat yet');
  assert.doesNotMatch(allText(m), /online/i);
});

test('box sensors are reporting while heartbeats arrive, with battery and power', () => {
  const h = run({ type: 'power', state: 'battery' }, { type: 'heartbeat', battery_pct: 87 });
  const s = part(systemModel(h, up(T + 2000)), 'sensors');
  assert.deepEqual(s.status, { text: 'Reporting', tone: 'ok' });
  assert.equal(fact(s, 'Last message'), '1 s ago');
  assert.equal(fact(s, 'Battery'), '87%');
  assert.equal(fact(s, 'Power'), 'On battery');
  assert.equal(fact(part(systemModel(run({ type: 'power', state: 'mains' }), up(T)), 'sensors'), 'Power'), 'Mains');
});

test('box sensors with no heartbeat for over 15 s are a warning', () => {
  const h = run({ type: 'heartbeat', battery_pct: 90 });
  const m = systemModel(h, up(T + LIVE_MS + 1000));
  assert.deepEqual(part(m, 'sensors').status, { text: 'No heartbeat', tone: 'warning' });
  assert.equal(fact(part(m, 'sensors'), 'Battery'), '90%');
  assert.equal(m.detail, 'Hub connected. Box sensors not reporting');
});

test('presence reports while updates arrive, and a quiet presence feed is not a warning', () => {
  const h = run({ type: 'presence', state: 'none' });
  const live = part(systemModel(h, up(T + 4000)), 'presence');
  assert.deepEqual(live.status, { text: 'Reporting', tone: 'ok' });
  assert.equal(fact(live, 'Last update'), '4 s ago');
  assert.equal(fact(live, 'Last state'), 'Nobody seen');
  const quiet = systemModel(h, up(T + LIVE_MS + 5000));
  assert.deepEqual(part(quiet, 'presence').status, { text: 'No recent update', tone: '' });
  assert.equal(fact(part(quiet, 'presence'), 'Last update'), '20 s ago');
  assert.doesNotMatch(quiet.detail, /not reporting/);
});

test('the head lists the parts that report', () => {
  const h = run({ type: 'heartbeat', battery_pct: 100 }, { type: 'presence', state: 'moving' });
  assert.equal(systemModel(h, up(T + 2000)).detail, 'Hub connected. Box sensors and presence reporting');
});

test('the help sign, agent and voice make no live claim: only whether they were heard', () => {
  const h = run({ type: 'help_gesture', source: 'camera' }, { type: 'checkin', state: 'asking', try: 1 }, { type: 'heard', answer: 'ok', transcript: 'fine' });
  const m = systemModel(h, up(T + LIVE_MS * 10));
  for (const id of ['camera', 'agent', 'voice']) {
    const p = part(m, id);
    assert.deepEqual(p.status, { text: 'Heard', tone: '' }, id);
    assert.notEqual(fact(p, 'Last message'), '--');
  }
  assert.equal(fact(part(systemModel(initialHistory(), up(T)), 'camera'), 'Last message'), '--');
});

test('when the hub link drops, the hub is offline and every part is unknown with last known times', () => {
  const h = run({ type: 'heartbeat', battery_pct: 80 }, { type: 'presence', state: 'still' }, { type: 'say', text: 'Are you okay?' });
  const m = systemModel(h, down(T + 5000, T + 4000));
  assert.equal(m.detail, 'Hub offline. Times below are last known');
  const hub = part(m, 'hub');
  assert.deepEqual(hub.status, { text: 'Offline', tone: 'warning' });
  assert.ok(fact(hub, 'Offline since') && fact(hub, 'Offline since') !== '--');
  for (const p of m.parts.filter((x) => x.id !== 'hub')) assert.deepEqual(p.status, { text: 'Unknown', tone: '' }, p.id);
  assert.equal(fact(part(m, 'sensors'), 'Last message'), '5 s ago');
  assert.equal(fact(part(m, 'sensors'), 'Battery'), '80%');
  assert.equal(fact(part(m, 'agent'), 'Last message'), '3 s ago');
});

test('a hub never reached claims nothing: no since time, no last known', () => {
  const m = systemModel(initialHistory(), down(T, null));
  assert.equal(m.detail, 'Hub offline. Nothing received yet');
  const hub = part(m, 'hub');
  assert.deepEqual(hub.status, { text: 'Offline', tone: 'warning' });
  assert.equal(fact(hub, 'Offline since'), '--');
  assert.doesNotMatch(allText(m), /last known/i);
  for (const p of m.parts) for (const f of p.facts) assert.equal(f.value, '--', `${p.id} ${f.label}`);
});

test('no wording breaks the team rules, connected or offline', () => {
  const h = run({ type: 'presence', state: 'moving' }, { type: 'fall_hint' }, { type: 'heartbeat', battery_pct: 50 }, { type: 'help_gesture' });
  const models = [
    systemModel(h, up(T + 3000)), systemModel(h, up(T + LIVE_MS * 3)),
    systemModel(h, down(T + 3000, T + 2500)), systemModel(initialHistory(), up(T)), systemModel(initialHistory(), down(T, null)),
  ];
  for (const m of models) {
    const text = allText(m);
    assert.doesNotMatch(text, /fall/i);
    assert.doesNotMatch(text, /911|—|·/);
  }
});

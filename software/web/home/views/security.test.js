import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialHistory, record, LIVE_MS, HISTORY_MAX } from '../state.js';
import { clockTime } from './common.js';
import { securityModel } from './security.js';

const T = 1_000_000;

// Each message arrives one second after the one before it. The screen is read one second after the last one.
function run(...msgs) {
  const history = msgs.reduce((h, m, i) => record(h, m, T + i * 1000), initialHistory());
  return { history, now: T + msgs.length * 1000 };
}
const view = (msgs, ctx = {}) => {
  const { history, now } = run(...msgs);
  return securityModel(history, { now, connected: true, linkAt: T - 5000, ...ctx });
};
const fact = (card, label) => card.facts.find((f) => f.label === label);

const moving = { type: 'presence', state: 'moving' };
const still = { type: 'presence', state: 'still' };
const nobody = { type: 'presence', state: 'none' };
const hint = { type: 'fall_hint' };
const help = { type: 'help_gesture', source: 'camera' };

test('with no data the screen is quiet and says so once', () => {
  const m = view([]);
  assert.equal(m.detail, 'No presence data yet');
  assert.equal(m.presence.word, '--');
  assert.equal(m.presence.muted, true);
  assert.equal(fact(m.presence, 'Since').text, '--');
  assert.equal(fact(m.presence, 'Feed').text, 'Waiting');
  for (const card of [m.help, m.still]) {
    assert.equal(card.value, '0');
    assert.equal(card.muted, true);
    assert.equal(fact(card, 'Last').text, '--');
  }
  assert.equal(m.events.count, null, 'the empty body says it once; no "0 events" in the head');
  assert.deepEqual(m.events.rows, []);
  assert.deepEqual(m.events.empty, { text: 'No events yet', sub: 'Presence changes and help signs show here.' });
});

test('the presence state reads as a word, since when it started, with a live feed', () => {
  const states = [[moving, 'Moving', 'Someone is moving'], [still, 'Still', 'Someone is still'], [nobody, 'Nobody seen', 'Nobody seen']];
  for (const [msg, word, detail] of states) {
    const m = view([msg]);
    assert.equal(m.presence.word, word);
    assert.equal(m.presence.muted, false);
    assert.equal(m.detail, detail);
    assert.equal(fact(m.presence, 'Since').text, clockTime(T));
    assert.deepEqual(fact(m.presence, 'Feed'), { label: 'Feed', text: 'Live', cls: 'ok', pill: true });
  }
});

test('a repeated state keeps its since time and keeps the feed live', () => {
  const { history } = run(moving, moving);
  const m = securityModel(history, { now: T + LIVE_MS + 1000, connected: true, linkAt: T });
  assert.equal(fact(m.presence, 'Since').text, clockTime(T));
  assert.equal(fact(m.presence, 'Feed').text, 'Live');
});

test('a quiet presence feed is not a warning: the state stands and the feed says when it last spoke', () => {
  const { history } = run(still);
  const m = securityModel(history, { now: T + 20_000, connected: true, linkAt: T });
  assert.deepEqual(fact(m.presence, 'Feed'), { label: 'Feed', text: 'Last update 20 s ago', cls: '', pill: true });
  assert.equal(m.presence.word, 'Still');
  assert.equal(m.presence.muted, false);
  assert.equal(m.detail, 'Someone is still');
});

test('with the hub link down after a session the data is last known', () => {
  const m = view([moving, help], { connected: false, linkAt: T + 1500 });
  assert.equal(m.detail, 'Hub offline. Last known: someone is moving');
  assert.equal(m.presence.word, 'Moving');
  assert.notEqual(fact(m.presence, 'Feed').text, 'Live');
  assert.equal(m.help.value, '1');
  assert.equal(m.events.rows.length, 2);
});

test('when the hub was never reached nothing is known: dashes, no zero counts, no empty log claim', () => {
  const m = view([], { connected: false, linkAt: null });
  assert.equal(m.detail, 'Hub offline. Nothing received yet');
  assert.equal(m.presence.word, '--');
  assert.equal(fact(m.presence, 'Feed').text, '--');
  for (const card of [m.help, m.still]) {
    assert.equal(card.value, '--');
    assert.equal(card.muted, true);
  }
  assert.equal(m.events.count, null);
  assert.deepEqual(m.events.empty, { text: 'Unavailable while the hub is offline', sub: '' });
});

test('help signs are counted for the session with the last one time, without alarm color', () => {
  const m = view([help, moving, help]);
  assert.equal(m.help.value, '2');
  assert.equal(m.help.muted, false);
  assert.equal(fact(m.help, 'Last').text, clockTime(T + 2000));
});

test('the counts cover the whole session, past the events the log keeps', () => {
  const flips = Array.from({ length: HISTORY_MAX }, (_, i) => (i % 2 ? moving : still));
  const m = view([help, hint, help, ...flips]);
  assert.equal(m.events.rows.length, HISTORY_MAX);
  assert.equal(m.help.value, '2');
  assert.equal(fact(m.help, 'Last').text, clockTime(T + 2000));
  assert.equal(m.still.value, '1');
  assert.equal(fact(m.still, 'Last').text, clockTime(T + 1000));
});

test('the help sign card never claims the camera is online', () => {
  const text = JSON.stringify(view([]).help).toLowerCase();
  assert.doesNotMatch(text, /online|live|watching|ready/);
});

test('still after moving is counted like help signs', () => {
  const m = view([moving, still, hint, moving, still, hint]);
  assert.equal(m.still.value, '2');
  assert.equal(fact(m.still, 'Last').text, clockTime(T + 5000));
});

test('the events log reads newest first; only help signs carry a tag', () => {
  const m = view([moving, still, hint, help, nobody]);
  assert.equal(m.events.count, 5);
  assert.deepEqual(m.events.rows.map((r) => [r.at, r.what, r.tag]), [
    [T + 4000, 'Nobody seen', null],
    [T + 3000, 'Help sign seen', { text: 'Help sign', cls: 'danger' }],
    [T + 2000, 'Still after moving', null],
    [T + 1000, 'Still', null],
    [T, 'Moving', null],
  ]);
});

test('still after moving never claims a check-in started, since the agent may ignore it or be down', () => {
  const m = view([moving, still, hint]);
  assert.doesNotMatch(JSON.stringify([m.still, m.events.rows[0]]), /checking in|asks if you are okay/i);
});

test('a reset empties the log and the counts', () => {
  const m = view([moving, help, hint, { type: 'reset' }]);
  assert.deepEqual(m.events.rows, []);
  assert.equal(m.help.value, '0');
  assert.equal(m.still.value, '0');
  assert.equal(m.presence.word, '--');
});

test('no wording on the screen says fall, 911 or uses an em dash or middle dot', () => {
  const msgs = [moving, still, hint, help, nobody];
  for (const ctx of [{}, { connected: false }, { connected: false, linkAt: null }]) {
    const text = JSON.stringify([view(msgs, ctx), view([], ctx)]);
    assert.doesNotMatch(text, /fall|911|—|·/i);
  }
});

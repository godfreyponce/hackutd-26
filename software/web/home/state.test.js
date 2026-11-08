import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialState, reduce, statusText, sourceLabel, activeAlert, alertChip } from './state.js';

const NOW = 1_000_000;

function run(...msgs) {
  return msgs.reduce((s, m) => reduce(s, m, NOW), initialState());
}

const quake = { type: 'quake', peak_g: 0.82 };
const asking = (n) => ({ type: 'checkin', state: 'asking', try: n });
const noAnswer = (n) => ({ type: 'checkin', state: 'no_answer', try: n });

test('starts PROTECTED with a white home dot and no alert or battery badge', () => {
  const s = initialState();
  assert.equal(s.status, 'PROTECTED');
  assert.equal(s.home, 'idle');
  assert.equal(s.alert, null);
  assert.equal(s.onBattery, false);
});

test('quake goes to CHECKING_IN, records the peak and marks the home hit', () => {
  const s = run(quake);
  assert.equal(s.status, 'CHECKING_IN');
  assert.deepEqual(s.quakes, [{ at: NOW, g: 0.82 }]);
  assert.equal(s.home, 'hit');
  assert.equal(s.areaHit, true);
});

test('fall_hint goes to CHECKING_IN without marking the neighborhood hit', () => {
  const s = run({ type: 'fall_hint' });
  assert.equal(s.status, 'CHECKING_IN');
  assert.equal(s.areaHit, false);
});

test('checkin asking goes to CHECKING_IN with the try number', () => {
  const s = run(asking(1));
  assert.equal(s.status, 'CHECKING_IN');
  assert.equal(s.tryNum, 1);
});

test('checkin no_answer goes to NO_RESPONSE', () => {
  assert.equal(run(quake, asking(1), noAnswer(1)).status, 'NO_RESPONSE');
});

test('a later ask keeps NO_RESPONSE and updates the try number', () => {
  const s = run(quake, asking(1), noAnswer(1), asking(2));
  assert.equal(s.status, 'NO_RESPONSE');
  assert.equal(s.tryNum, 2);
});

test('checkin alarm goes to CONTACTING_HELP', () => {
  assert.equal(run(quake, noAnswer(3), { type: 'checkin', state: 'alarm', try: 4 }).status, 'CONTACTING_HELP');
});

test('checkin help goes to CONTACTING_HELP', () => {
  assert.equal(run(quake, asking(1), { type: 'checkin', state: 'help', try: 1 }).status, 'CONTACTING_HELP');
});

test('a quake or a stand-up re-ask never hides CONTACTING_HELP', () => {
  const s = run({ type: 'checkin', state: 'alarm' }, quake, { type: 'fall_hint' }, asking(1));
  assert.equal(s.status, 'CONTACTING_HELP');
});

test('a first ask after a check-in that ended at no response, with no alarm, shows CHECKING_IN', () => {
  // Nobody home: the agent sends asking 1, no_answer 1, then clear, which this page missed. The next event starts a new check-in.
  const s = run(quake, asking(1), noAnswer(1), { type: 'fall_hint' }, asking(1));
  assert.equal(s.status, 'CHECKING_IN');
  assert.equal(s.tryNum, 1);
});

test('a first ask clears what was heard in the last check-in', () => {
  const s = run(asking(1), { type: 'heard', answer: 'ok', transcript: "I'm okay" }, { type: 'checkin', state: 'ok', try: 1 },
    { type: 'fall_hint' }, asking(1));
  assert.equal(s.heard, null);
});

test('the stand-up re-ask after an alarm keeps CONTACTING_HELP and clears what was heard before it', () => {
  const s = run(quake, asking(1), noAnswer(1), asking(2), noAnswer(2), asking(3),
    { type: 'heard', answer: 'no_answer', transcript: '' }, noAnswer(3), { type: 'checkin', state: 'alarm', try: 4 }, asking(1));
  assert.equal(s.status, 'CONTACTING_HELP');
  assert.equal(s.heard, null);
  assert.equal(reduce(s, noAnswer(1), NOW).status, 'CONTACTING_HELP');
});

for (const end of ['clear', 'ok']) {
  test(`checkin ${end} goes back to PROTECTED and turns the home dot green`, () => {
    const s = run(quake, noAnswer(3), { type: 'checkin', state: 'alarm' }, { type: 'checkin', state: end });
    assert.equal(s.status, 'PROTECTED');
    assert.equal(s.tryNum, null);
    assert.equal(s.home, 'ok');
  });
}

test('a clear that ends a check-in nobody answered keeps the home dot red', () => {
  const s = run(quake, asking(1), noAnswer(1), { type: 'checkin', state: 'clear', try: 1 });
  assert.equal(s.status, 'PROTECTED');
  assert.equal(s.home, 'hit');
});

const STATES = {
  PROTECTED: [],
  CHECKING_IN: [quake],
  NO_RESPONSE: [quake, noAnswer(1)],
  CONTACTING_HELP: [quake, { type: 'checkin', state: 'alarm' }],
};
for (const [name, msgs] of Object.entries(STATES)) {
  test(`reset from ${name} returns the start state`, () => {
    const before = run(...msgs, { type: 'alert', source: 'nws', event: 'Heat Advisory' }, { type: 'power', state: 'battery' });
    assert.equal(before.status, name);
    assert.deepEqual(reduce(before, { type: 'reset' }, NOW), initialState());
  });
}

test('say and heard are shown with the current try number', () => {
  const s = run(
    asking(2),
    { type: 'say', script_id: 'fall_q2', text: 'Are you okay?', listen_s: 6 },
    { type: 'heard', answer: 'no_answer', transcript: '' },
  );
  assert.deepEqual(s.say, { text: 'Are you okay?', tryNum: 2 });
  assert.deepEqual(s.heard, { answer: 'no_answer', transcript: '', tryNum: 2 });
});

test('alert sets the banner with the source shown', () => {
  const s = run({
    type: 'alert', source: 'usgs', event: 'Earthquake', severity: 'Severe', urgency: 'Immediate',
    certainty: 'Observed', area: 'Richardson, TX', headline: 'M5.1 near Richardson',
  });
  assert.deepEqual(s.alert, {
    source: 'USGS', event: 'Earthquake', severity: 'Severe', area: 'Richardson, TX', headline: 'M5.1 near Richardson', level: 'warning', at: NOW,
  });
  assert.equal(s.status, 'PROTECTED');
});

test('alert stores when it arrived, for the banner issue time', () => {
  const s = reduce(initialState(), { type: 'alert', source: 'nws', event: 'Heat Advisory' }, NOW);
  assert.equal(s.alert.at, NOW);
});

const alertAt = (level, extra = {}) => ({ type: 'alert', source: 'nws', event: 'Test', headline: level, level, ...extra });
const MIN = 60_000;

test('alert keeps the level the hub added', () => {
  for (const level of ['info', 'watch', 'warning', 'emergency']) {
    assert.equal(run(alertAt(level)).alert.level, level);
  }
});

test('an alert with a missing or unknown level shows as a warning', () => {
  assert.equal(run({ type: 'alert', source: 'nws', event: 'Old hub' }).alert.level, 'warning');
  assert.equal(run(alertAt('bogus')).alert.level, 'warning');
});

test('info shows for 2 minutes and watch for 30', () => {
  const info = run(alertAt('info'));
  assert.ok(activeAlert(info, NOW + 2 * MIN - 1));
  assert.equal(activeAlert(info, NOW + 2 * MIN), null);
  const watch = run(alertAt('watch'));
  assert.ok(activeAlert(watch, NOW + 30 * MIN - 1));
  assert.equal(activeAlert(watch, NOW + 30 * MIN), null);
});

test('warning and emergency show until reset', () => {
  for (const level of ['warning', 'emergency']) {
    const s = run(alertAt(level));
    assert.equal(activeAlert(s, NOW + 24 * 60 * MIN), s.alert);
    assert.equal(activeAlert(reduce(s, { type: 'reset' }, NOW + 1), NOW + 1), null);
  }
});

test('a lower level never replaces a higher one that is still showing', () => {
  const s = run(alertAt('emergency'), alertAt('info'), alertAt('watch'), alertAt('warning'));
  assert.equal(s.alert.level, 'emergency');
  assert.equal(reduce(run(alertAt('watch')), alertAt('info'), NOW + MIN).alert.level, 'watch');
});

test('the same or a higher level replaces the alert showing', () => {
  assert.equal(run(alertAt('watch'), alertAt('warning')).alert.level, 'warning');
  const s = run(alertAt('warning', { headline: 'first' }), alertAt('warning', { headline: 'second' }));
  assert.equal(s.alert.headline, 'second');
});

test('a lower level replaces a higher one after it expired', () => {
  const s = reduce(run(alertAt('watch')), alertAt('info'), NOW + 30 * MIN);
  assert.equal(s.alert.level, 'info');
  assert.equal(s.alert.at, NOW + 30 * MIN);
});

test('a demo alert headline starts with the demo prefix', () => {
  const s = run(alertAt('emergency', { demo: true, headline: 'M5.1 earthquake near Richardson, TX' }));
  assert.equal(s.alert.headline, 'DEMO, not a real alert. M5.1 earthquake near Richardson, TX');
  assert.equal(run(alertAt('info', { demo: true, headline: '' })).alert.headline, 'DEMO, not a real alert.');
  assert.equal(run(alertAt('info', { demo: 'yes', headline: 'x' })).alert.headline, 'x');
});

test('an alert never changes the home status word', () => {
  for (const level of ['info', 'watch', 'warning', 'emergency']) {
    assert.equal(run(alertAt(level)).status, 'PROTECTED');
    assert.equal(run(quake, alertAt(level)).status, 'CHECKING_IN');
  }
});

test('source labels cover NOAA, NWS, USGS, GDACS and sensor', () => {
  assert.deepEqual(['noaa', 'nws', 'usgs', 'gdacs', 'sensor'].map(sourceLabel), ['NOAA', 'NWS', 'USGS', 'GDACS', 'Sensor']);
});

test('power battery shows the badge and power mains hides it', () => {
  const on = run({ type: 'power', state: 'battery' });
  assert.equal(on.onBattery, true);
  assert.equal(reduce(on, { type: 'power', state: 'mains' }, NOW).onBattery, false);
});

test('heartbeat records the battery percent', () => {
  assert.equal(run({ type: 'heartbeat', battery_pct: 87 }).batteryPct, 87);
});

test('queue gives this home (H000) indoor temperature', () => {
  const s = run({ type: 'queue', homes: [{ id: 'H042', harm_min: 3, factors: { indoor_f: 40 } }, { id: 'H000', harm_min: 50, factors: { indoor_f: 71 } }] });
  assert.equal(s.indoorF, 71);
});

test('a queue reading records when it arrived', () => {
  assert.equal(run({ type: 'queue', homes: [{ id: 'H000', factors: { indoor_f: 71 } }] }).indoorAt, NOW);
  assert.equal(run({ type: 'queue', homes: [{ id: 'H000', factors: {} }] }).indoorAt, null);
});

test('unknown or malformed messages are ignored', () => {
  const s = run(quake);
  for (const m of [{ type: 'agent', step: 'PLAN', text: 'x' }, { type: 'bogus' }, {}, null, 'quake', { type: 'checkin', state: 'weird' }]) {
    assert.equal(reduce(s, m, NOW), s);
  }
});

test('quake trace keeps only the last minute', () => {
  let s = reduce(initialState(), quake, NOW);
  s = reduce(s, { type: 'quake', peak_g: 0.4 }, NOW + 61_000);
  assert.deepEqual(s.quakes, [{ at: NOW + 61_000, g: 0.4 }]);
});

test('status text never says "fall" and the alarm note says no emergency number is called', () => {
  for (const status of Object.keys(STATES)) {
    const { word, detail } = statusText(status);
    assert.doesNotMatch(`${word} ${detail}`, /fall/i);
  }
  assert.equal(statusText('NO_RESPONSE').detail, 'No response after an event. Asking again.');
  assert.match(statusText('CONTACTING_HELP').note, /demo/i);
  assert.match(statusText('CONTACTING_HELP').note, /no emergency number is called/i);
});

test('PROTECTED with an official alert says the alert is active', () => {
  assert.equal(statusText('PROTECTED', { alert: true }).detail, 'All okay at home. Official alert active.');
  assert.equal(statusText('PROTECTED').detail, 'No active events');
});

test('with the hub link down, a quiet home shows HUB OFFLINE instead of a live-looking PROTECTED', () => {
  const t = statusText('PROTECTED', { linked: false });
  assert.equal(t.word, 'HUB OFFLINE');
  assert.equal(t.detail, 'Live status unavailable. Reconnecting to hub.');
  assert.equal(statusText('PROTECTED').word, 'PROTECTED');
});

test('with the hub link down, an escalation keeps its word', () => {
  assert.equal(statusText('CONTACTING_HELP', { linked: false }).word, 'CONTACTING HELP');
  assert.equal(statusText('NO_RESPONSE', { linked: false }).word, 'NO RESPONSE');
});

test('a help sign goes to CHECKING_IN and the status line says the help sign was seen', () => {
  const s = run({ type: 'help_gesture', source: 'camera' });
  assert.equal(s.status, 'CHECKING_IN');
  assert.equal(s.home, 'hit');
  assert.equal(s.areaHit, false);
  assert.equal(s.helpSign, true);
  assert.equal(statusText(s.status, { helpSign: s.helpSign }).detail, 'Help sign seen. Asking if you are okay.');
  assert.equal(statusText('CHECKING_IN').detail, 'Event detected. Asking if you are okay.');
});

test('the help sign line stays for its check-in and goes when the home is okay again or on reset', () => {
  const help = { type: 'help_gesture', source: 'camera' };
  const ok = { type: 'checkin', state: 'ok', try: 1 };
  assert.equal(run(help, asking(1), quake).helpSign, true);
  assert.equal(run(help, asking(1), ok, quake).helpSign, false);
  // An alert or recheck check-in starts with only `checkin asking`, no event message.
  const later = run(help, asking(1), ok, asking(1));
  assert.equal(statusText(later.status, { helpSign: later.helpSign }).detail, 'Event detected. Asking if you are okay.');
  assert.equal(run(help, { type: 'reset' }).helpSign, false);
});

test('a check-in started by a help sign that ended at no response does not mark the next check-in', () => {
  const help = { type: 'help_gesture', source: 'camera' };
  const s = run(help, asking(1), noAnswer(1), quake, asking(1));
  assert.equal(statusText(s.status, { helpSign: s.helpSign }).detail, 'Event detected. Asking if you are okay.');
  // An alert check-in starts with only `checkin asking`, no event message.
  assert.equal(run(help, asking(1), noAnswer(1), asking(1)).helpSign, false);
  assert.equal(run(quake, asking(1), noAnswer(1), help, asking(1)).helpSign, true);
});

test('alert chip names source and level, but not a level the event title already says', () => {
  assert.equal(alertChip({ source: 'NOAA', level: 'warning', event: 'Earthquake Warning' }), 'NOAA');
  assert.equal(alertChip({ source: 'USGS', level: 'emergency', event: 'Earthquake' }), 'USGS EMERGENCY');
  assert.equal(alertChip({ source: '', level: 'watch', event: 'Flood' }), 'WATCH');
});

// Event-to-state logic for the home screen. Pure: no DOM, no clock (the caller passes `now`).

export const TRACE_WINDOW_MS = 60_000;

// Higher rank wins until checkin ok/clear, a new check-in's first ask, an event after an ended check-in, or reset,
// so a re-ask never hides an alarm.
const RANK = { PROTECTED: 0, CHECKING_IN: 1, NO_RESPONSE: 2, CONTACTING_HELP: 3 };

const CHECKIN_STATUS = {
  asking: 'CHECKING_IN',
  no_answer: 'NO_RESPONSE',
  alarm: 'CONTACTING_HELP',
  help: 'CONTACTING_HELP',
};

// The hub adds `level` to every alert (software/hub/alert_level.py). Warning and emergency stay until reset.
const ALERT_RANK = { info: 0, watch: 1, warning: 2, emergency: 3 };
const ALERT_TTL_MS = { info: 2 * 60_000, watch: 30 * 60_000, warning: Infinity, emergency: Infinity };
// An alert from a hub without levels errs high: orange, until reset.
const DEFAULT_ALERT_LEVEL = 'warning';
export const DEMO_PREFIX = 'DEMO, not a real alert.';

const SOURCE_LABELS = { noaa: 'NOAA', nws: 'NWS', usgs: 'USGS', gdacs: 'GDACS', sensor: 'Sensor' };

export function initialState() {
  return {
    status: 'PROTECTED',
    tryNum: null,
    say: null,
    heard: null,
    alert: null,
    onBattery: false,
    batteryPct: null,
    indoorF: null,
    indoorAt: null, // when the last indoor reading arrived
    quakes: [],
    areaHit: false, // neighborhood dots turn red after a quake
    home: 'idle', // node map dot: idle (white), hit (red), ok (green)
    helpSign: false, // the camera saw the HELP sign in this check-in
    trigger: null, // the first event since the last checkin message: the one the agent starts its next check-in on
    ended: false, // the check-in ended at NO_RESPONSE: nobody seen, no answer, no alarm
  };
}

export function activeAlert(state, now) {
  const a = state.alert;
  return a && now - a.at < ALERT_TTL_MS[a.level] ? a : null;
}

function onAlert(state, msg, now) {
  const level = Object.hasOwn(ALERT_RANK, msg.level) ? msg.level : DEFAULT_ALERT_LEVEL;
  const showing = activeAlert(state, now);
  if (showing && ALERT_RANK[level] < ALERT_RANK[showing.level]) return state;
  const headline = String(msg.headline ?? '');
  return {
    ...state,
    alert: {
      source: sourceLabel(msg.source),
      event: msg.event ?? 'Alert',
      severity: msg.severity ?? '',
      area: msg.area ?? '',
      headline: msg.demo === true ? [DEMO_PREFIX, headline].filter(Boolean).join(' ') : headline,
      level,
      at: now,
    },
  };
}

// The chip names the source and the level, like the dashboard header, unless the event title
// already says the level ("Earthquake Warning"); then the chip shows the source alone.
export function alertChip(a) {
  const levelInTitle = String(a.event ?? '').toLowerCase().includes(a.level);
  return (levelInTitle ? [a.source] : [a.source, a.level]).filter(Boolean).join(' ').toUpperCase();
}

export function sourceLabel(source) {
  return Object.hasOwn(SOURCE_LABELS, source) ? SOURCE_LABELS[source] : String(source ?? '').toUpperCase();
}

export const SAY_HINT = 'Say "okay" or "help".';

export function statusText(status, { alert = false, linked = true, helpSign = false, ended = false } = {}) {
  switch (status) {
    case 'CHECKING_IN':
      return { word: 'CHECKING IN', detail: `${helpSign ? 'Help sign seen' : 'Event detected'}. Asking if you are okay.`, note: SAY_HINT };
    case 'NO_RESPONSE':
      if (ended) return { word: 'NO RESPONSE', detail: 'Nobody seen at home. No alarm.' };
      return { word: 'NO RESPONSE', detail: 'No response after an event. Asking again.', note: SAY_HINT };
    case 'CONTACTING_HELP':
      return {
        word: 'DEMO ALARM',
        detail: 'Your contact would be told.',
        note: 'Demo alarm. No emergency number is called.',
      };
    default:
      if (!linked) return { word: 'HUB OFFLINE', detail: 'Live status unavailable. Reconnecting to hub.' };
      return { word: 'PROTECTED', detail: alert ? 'All okay at home. Official alert active.' : 'No active events' };
  }
}

// rule.MAX_TRIES in software/agent. The bus does not send it.
export const MAX_TRIES = 3;
const ANSWERS = { ok: 'I\'m okay', help: 'Help', no_answer: 'No answer' };

export const tryText = (tryNum) => (tryNum ? `try ${tryNum} of ${MAX_TRIES}` : '');

// A missed answer names its try, so it never reads as the try being asked now. Under the alarm the
// stand-up re-ask is sent as try 1, so no try shows there.
export function heardChip(heard, status) {
  if (!heard) return '';
  const label = ANSWERS[heard.answer] ?? heard.answer;
  return heard.answer === 'no_answer' && heard.tryNum && status !== 'CONTACTING_HELP' ? `${label}, try ${heard.tryNum}` : label;
}

function raise(state, status) {
  return RANK[status] > RANK[state.status] ? status : state.status;
}

// After an ended check-in the agent starts a new one on the next event, so the screen leaves NO_RESPONSE.
function onEvent(state, kind, extra = {}) {
  const status = state.ended ? 'CHECKING_IN' : raise(state, 'CHECKING_IN');
  return { ...state, status, ended: false, home: 'hit', trigger: state.trigger ?? kind, ...extra };
}

function onCheckin(state, msg) {
  const tryNum = msg.try ?? state.tryNum;
  if (msg.state === 'ok' || msg.state === 'clear') {
    // With nobody there, the agent sends clear right after a no answer. The check-in is over, but nobody said they were okay.
    if (msg.state === 'clear' && state.status === 'NO_RESPONSE') {
      return { ...state, ended: true, tryNum: null, helpSign: false, trigger: null };
    }
    return { ...state, status: 'PROTECTED', ended: false, tryNum: null, home: state.home === 'hit' ? 'ok' : state.home, helpSign: false, trigger: null };
  }
  const status = CHECKIN_STATUS[msg.state];
  if (!status) return state;
  // The agent sends asking try 1 only to start a check-in or for the stand-up re-ask after an alarm
  // (software/agent/checkin.py _speak). Its status reset also covers a check-in whose clear this screen missed.
  if (msg.state === 'asking' && msg.try === 1) {
    const standup = state.status === 'CONTACTING_HELP';
    return {
      ...state, status: standup ? state.status : status, ended: false, tryNum, heard: null, home: 'hit', trigger: null,
      helpSign: standup ? state.helpSign : state.trigger === 'help_gesture',
    };
  }
  return { ...state, status: raise(state, status), ended: false, tryNum, home: 'hit', trigger: null };
}

export function reduce(state, msg, now) {
  if (!msg || typeof msg !== 'object') return state;
  switch (msg.type) {
    case 'quake': {
      const quakes = [...state.quakes, { at: now, g: Number(msg.peak_g) || 0 }].filter((q) => now - q.at <= TRACE_WINDOW_MS);
      return onEvent(state, msg.type, { quakes, areaHit: true });
    }
    case 'fall_hint':
      return onEvent(state, msg.type);
    case 'help_gesture':
      return onEvent(state, msg.type, { helpSign: true });
    case 'checkin':
      return onCheckin(state, msg);
    case 'say':
      return { ...state, say: { text: String(msg.text ?? ''), tryNum: state.tryNum } };
    case 'heard':
      return { ...state, heard: { answer: msg.answer, transcript: String(msg.transcript ?? ''), tryNum: state.tryNum } };
    case 'alert':
      return onAlert(state, msg, now);
    case 'power':
      if (msg.state !== 'battery' && msg.state !== 'mains') return state;
      return { ...state, onBattery: msg.state === 'battery' };
    case 'heartbeat':
      return typeof msg.battery_pct === 'number' ? { ...state, batteryPct: msg.battery_pct } : state;
    case 'indoor':
      // the box's own BMP280 reading; it wins over the dashboard's simulated H000 value
      return typeof msg.temp_f === 'number' ? { ...state, indoorF: msg.temp_f, indoorAt: now, indoorLive: true } : state;
    case 'queue': {
      if (state.indoorLive) return state;
      const home = Array.isArray(msg.homes) && msg.homes.find((h) => h && h.id === 'H000');
      const f = home?.factors?.indoor_f;
      return typeof f === 'number' ? { ...state, indoorF: f, indoorAt: now } : state;
    }
    case 'reset':
      return initialState();
    default:
      return state;
  }
}

// ---------- session history for the Alerts, Disasters, Security and System screens ----------

// Guess: far more than one demo session makes. It bounds memory on a box left running for days.
export const HISTORY_MAX = 100;
// Three missed 5 s beats: the simulator heartbeat (software/hub/sim.py) and the presence repeat both run every 5 s.
export const LIVE_MS = 15_000;

const PRESENCE_STATES = ['moving', 'still', 'none'];
const CHECKIN_STATES = ['asking', 'ok', 'help', 'no_answer', 'alarm', 'clear'];
const TRIGGERS = ['quake', 'fall_hint', 'help_gesture'];
// ALERT_QUIET_S in software/agent/checkin.py: after a check-in starts on anything but a help sign, the agent
// ignores EQW alerts this long.
const ALERT_QUIET_MS = 300_000;
const alertQuiet = (h, now) => {
  const last = h.checkins.find((c) => c.trigger !== 'help_gesture');
  return last != null && now - last.at < ALERT_QUIET_MS;
};
// The agent starts a check-in on these and on an EQW emergency alert only (ALERT_TRIGGER in software/agent/checkin.py).
const isTrigger = (h, msg, now) => TRIGGERS.includes(msg.type)
  || (msg.type === 'alert' && msg.code === 'EQW' && msg.level === 'emergency' && !alertQuiet(h, now));
// Overview shows CONTACTING HELP for these; a later ok or clear must not hide that it happened.
const ESCALATED = ['help', 'alarm'];
// Which piece sent a message. The hub sim stands in for the box sensors and the camera.
const SENDER = {
  heartbeat: 'sensor', power: 'sensor', quake: 'sensor',
  presence: 'presence', fall_hint: 'presence',
  help_gesture: 'camera',
  agent: 'agent', checkin: 'agent', say: 'agent', handoff: 'agent', rerank: 'agent',
  heard: 'voice',
};

export function initialHistory() {
  return {
    alerts: [], // newest first
    checkins: [], // newest first; an open entry is still waiting for ok or clear
    quakes: [], // newest first, the whole session
    security: [], // newest first: presence changes, help signs, check-in hints
    presence: null, // { state, since, at }
    power: null, // { state, at }
    battery: null, // { pct, at }
    seen: {}, // sender -> when its last message arrived; survives reset
    trigger: null, // the last event that can start a check-in, until one starts
    // Whole-session counts: the security list is capped at HISTORY_MAX.
    helpSigns: { count: 0, last: null },
    stillHints: { count: 0, last: null },
  };
}

const push = (list, item) => [item, ...list].slice(0, HISTORY_MAX);
const tally = (c, now) => ({ count: c.count + 1, last: now });

function logAlert(h, msg, now) {
  const level = Object.hasOwn(ALERT_RANK, msg.level) ? msg.level : DEFAULT_ALERT_LEVEL;
  return push(h.alerts, {
    at: now,
    source: sourceLabel(msg.source),
    event: msg.event ?? 'Alert',
    level,
    severity: msg.severity ?? '',
    area: msg.area ?? '',
    headline: String(msg.headline ?? ''),
    code: msg.code ?? '',
    station: msg.station ?? '',
    distanceMi: typeof msg.distance_mi === 'number' ? msg.distance_mi : null,
    demo: msg.demo === true,
  });
}

// A check-in entry ends on ok or clear. A clear after a no answer with no alarm (nobody there) ends the entry
// at no response, since nobody said they were okay.
function logCheckin(h, msg, now) {
  const [open, ...rest] = h.checkins;
  const sent = typeof msg.try === 'number' ? msg.try : 1;
  // The agent sends the alarm as one try past the last ask.
  const tries = msg.state === 'alarm' ? Math.max(1, sent - 1) : sent;
  // After an okay to the stand-up question the agent sends clear at once (software/agent/checkin.py _apply_rule).
  const clearsLastOk = msg.state === 'clear' && open?.state === 'ok';
  // The agent ignores events while its check-in is open, which includes after the alarm until ok or clear.
  // A check-in left at no response with no alarm, then a first ask after a new event, means the agent ended it,
  // even if this screen missed its clear.
  const replaced = open?.state === 'no_answer' && !open.escalated && msg.state === 'asking' && tries === 1 && h.trigger && h.trigger.at > open.updatedAt;
  const fresh = !clearsLastOk && (!open?.open || replaced);
  if (fresh) {
    const entry = {
      at: now, trigger: h.trigger?.kind ?? null, state: msg.state, tries, heard: null, updatedAt: now, open: true, escalated: ESCALATED.includes(msg.state),
    };
    return { ...h, trigger: null, checkins: push(h.checkins, { ...entry, open: !['ok', 'clear'].includes(msg.state) }) };
  }
  const endsUnanswered = msg.state === 'clear' && open.state === 'no_answer' && !open.escalated;
  const entry = {
    ...open, state: endsUnanswered ? open.state : msg.state, tries: Math.max(open.tries, tries), updatedAt: now, open: !['ok', 'clear'].includes(msg.state),
    escalated: open.escalated || ESCALATED.includes(msg.state),
  };
  // The agent ignores events while a check-in runs, so one that came in meanwhile started nothing.
  return { ...h, trigger: null, checkins: [entry, ...rest] };
}

export function record(h, msg, now) {
  if (!msg || typeof msg !== 'object') return h;
  const sender = Object.hasOwn(SENDER, msg.type) ? SENDER[msg.type] : null;
  h = { ...h, seen: { ...h.seen, hub: now, ...(sender && { [sender]: now }) } };
  // The first event since the last check-in started is the one the agent acts on. One older than the newest
  // check-in update was ignored, so a newer event takes its place.
  const stale = h.trigger && h.trigger.at < (h.checkins[0]?.updatedAt ?? -Infinity);
  if (isTrigger(h, msg, now) && (!h.trigger || stale)) h = { ...h, trigger: { kind: msg.type, at: now } };
  switch (msg.type) {
    case 'alert':
      return { ...h, alerts: logAlert(h, msg, now) };
    case 'quake':
      return { ...h, quakes: push(h.quakes, { at: now, g: Number(msg.peak_g) || 0 }) };
    case 'checkin':
      return CHECKIN_STATES.includes(msg.state) ? logCheckin(h, msg, now) : h;
    case 'heard': {
      const [open, ...rest] = h.checkins;
      if (!open?.open) return h;
      return { ...h, checkins: [{ ...open, heard: { answer: msg.answer, transcript: String(msg.transcript ?? '') } }, ...rest] };
    }
    case 'presence': {
      if (!PRESENCE_STATES.includes(msg.state)) return h;
      if (h.presence?.state === msg.state) return { ...h, presence: { ...h.presence, at: now } };
      return {
        ...h,
        presence: { state: msg.state, since: now, at: now },
        security: push(h.security, { at: now, kind: 'presence', state: msg.state }),
      };
    }
    case 'fall_hint':
      return { ...h, security: push(h.security, { at: now, kind: msg.type }), stillHints: tally(h.stillHints, now) };
    case 'help_gesture':
      return { ...h, security: push(h.security, { at: now, kind: msg.type }), helpSigns: tally(h.helpSigns, now) };
    case 'power':
      return msg.state === 'battery' || msg.state === 'mains' ? { ...h, power: { state: msg.state, at: now } } : h;
    case 'heartbeat':
      return typeof msg.battery_pct === 'number' ? { ...h, battery: { pct: msg.battery_pct, at: now } } : h;
    case 'reset':
      return { ...initialHistory(), seen: h.seen };
    default:
      return h;
  }
}

export function liveness(seenAt, now) {
  if (seenAt == null) return 'unknown';
  return now - seenAt <= LIVE_MS ? 'live' : 'stale';
}

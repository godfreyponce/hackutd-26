// Event-to-state logic for the home screen. Pure: no DOM, no clock (the caller passes `now`).

export const TRACE_WINDOW_MS = 60_000;

// Higher rank wins until checkin ok/clear or reset, so a re-ask never hides an alarm.
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
const DEMO_PREFIX = 'DEMO, not a real alert.';

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

export function sourceLabel(source) {
  return SOURCE_LABELS[source] ?? String(source ?? '').toUpperCase();
}

export function statusText(status, { alert = false, linked = true } = {}) {
  switch (status) {
    case 'CHECKING_IN':
      return { word: 'CHECKING IN', detail: 'Event detected. Asking if you are okay.' };
    case 'NO_RESPONSE':
      return { word: 'NO RESPONSE', detail: 'No response after an event. Asking again.' };
    case 'CONTACTING_HELP':
      return {
        word: 'CONTACTING HELP',
        detail: 'Alerting your emergency contact',
        note: 'Demo alarm. No emergency number is called.',
      };
    default:
      if (!linked) return { word: 'HUB OFFLINE', detail: 'Live status unavailable. Reconnecting to hub.' };
      return { word: 'PROTECTED', detail: alert ? 'All okay at home. Official alert active.' : 'No active events' };
  }
}

function raise(state, status) {
  return RANK[status] > RANK[state.status] ? status : state.status;
}

function onEvent(state, extra = {}) {
  return { ...state, status: raise(state, 'CHECKING_IN'), home: 'hit', ...extra };
}

function onCheckin(state, msg) {
  const tryNum = msg.try ?? state.tryNum;
  if (msg.state === 'ok' || msg.state === 'clear') {
    return { ...state, status: 'PROTECTED', tryNum: null, home: state.home === 'hit' ? 'ok' : state.home };
  }
  const status = CHECKIN_STATUS[msg.state];
  if (!status) return state;
  return { ...state, status: raise(state, status), tryNum, home: 'hit' };
}

export function reduce(state, msg, now) {
  if (!msg || typeof msg !== 'object') return state;
  switch (msg.type) {
    case 'quake': {
      const quakes = [...state.quakes, { at: now, g: Number(msg.peak_g) || 0 }].filter((q) => now - q.at <= TRACE_WINDOW_MS);
      return onEvent(state, { quakes, areaHit: true });
    }
    case 'fall_hint':
      return onEvent(state);
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
    case 'queue': {
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

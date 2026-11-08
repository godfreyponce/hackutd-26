// The real box, H000, driven by bus events. Pure, no DOM.
import { generateHomes, REAL_BOX_ID } from './homes.js';

// Agent doc section 3: a node silent for more than 5 min is stale.
export const STALE_MS = 5 * 60 * 1000;
const SENSOR_TYPES = new Set(['quake', 'presence', 'fall_hint', 'power', 'heartbeat', 'indoor']);
const PROFILE = generateHomes().find((h) => h.id === REAL_BOX_ID);

export function initialBox(now) {
  return {
    presence: PROFILE.presence,
    no_answer: 0,
    said_help: false,
    answered_ok: false,
    alarm: false,
    checkin: null,
    try: 0,
    heard: null,
    event: false,
    power: 'mains',
    battery_pct: null,
    indoor_f: null,
    handoff: null,
    helpSign: false,
    lastSeen: now,
  };
}

function answered(s, answer) {
  if (answer === 'ok') return { ...s, answered_ok: true, no_answer: 0, said_help: false };
  if (answer === 'help') return { ...s, said_help: true };
  if (answer === 'no_answer') return { ...s, answered_ok: false, no_answer: Math.max(s.no_answer, s.try || s.no_answer + 1) };
  return s;
}

export function applyBoxEvent(state, msg, now) {
  if (msg.type === 'reset') return initialBox(now);
  let s = SENSOR_TYPES.has(msg.type) ? { ...state, lastSeen: now } : state;
  switch (msg.type) {
    case 'presence':
      return { ...s, presence: msg.state };
    case 'fall_hint':
    case 'quake':
      return { ...s, event: true };
    case 'help_gesture':
      return { ...s, helpSign: true };
    case 'power':
      return { ...s, power: msg.state };
    case 'heartbeat':
      return { ...s, battery_pct: msg.battery_pct };
    case 'indoor':
      // BMP280 on the box (hardware/sensors/sensors.py)
      return typeof msg.temp_f === 'number' ? { ...s, indoor_f: msg.temp_f } : s;
    case 'handoff':
      if (msg.home !== REAL_BOX_ID) return s;
      return { ...s, handoff: { note: msg.note, contact: msg.contact, by: msg.by, why: msg.why, why_by: msg.why_by } };
    case 'heard':
      // heard comes before its checkin no_answer, so s.try is still the try that was asked
      return answered({ ...s, heard: { answer: msg.answer, transcript: msg.transcript, try: s.try } }, msg.answer);
    case 'checkin': {
      // The agent sends alarm with try = tries + 1 and the home screen relies on that. Keep the last ask's try here.
      s = { ...s, checkin: msg.state, try: msg.state === 'alarm' ? s.try : msg.try ?? s.try };
      if (msg.state === 'ok' || msg.state === 'help' || msg.state === 'no_answer') return answered(s, msg.state);
      if (msg.state === 'alarm') return { ...s, alarm: true };
      // Try 1 opens a new check-in. Under an alarm it is the stand-up re-ask, which keeps the alarm's state.
      if (msg.state === 'asking' && msg.try === 1 && !s.alarm) {
        return { ...s, answered_ok: false, no_answer: 0, said_help: false, heard: null };
      }
      // With no alarm or help raised, a clear keeps the no-answer count, so a check-in nobody answered still shows it.
      if (msg.state === 'clear' && (s.alarm || s.said_help)) return { ...s, alarm: false, said_help: false, no_answer: 0 };
      return s;
    }
    default:
      return s;
  }
}

// rule.MAX_TRIES in software/agent. The bus does not send it.
export const MAX_TRIES = 3;
const CHECKIN_LABEL = { asking: 'Asking', ok: 'Okay', help: 'Said help', no_answer: 'No answer', alarm: 'Alarm', clear: 'Cleared' };
const ANSWER_LABEL = { ok: 'Okay', help: 'Help', no_answer: 'No answer' };

// Under an alarm the agent asks the stand-up question as try 1, so no bare try shows there.
export function checkinText(s) {
  if (!s.checkin) return 'None yet';
  if (s.alarm && s.checkin === 'asking') return 'Alarm, asking again';
  if (s.alarm && s.checkin === 'no_answer') return 'Alarm, no answer';
  if (s.checkin === 'alarm') return s.said_help ? 'Alarm, said help' : `Alarm after ${s.try} tries`;
  if (s.try && s.checkin === 'asking') return `Asking, try ${s.try} of ${MAX_TRIES}`;
  if (s.try && s.checkin === 'no_answer') return `No answer, try ${s.try}`;
  return CHECKIN_LABEL[s.checkin] ?? s.checkin;
}

export function heardText(s) {
  if (!s.heard) return 'None yet';
  const { answer, transcript } = s.heard;
  const tryNote = answer === 'no_answer' && s.heard.try && !s.alarm ? `, try ${s.heard.try}` : '';
  return `${ANSWER_LABEL[answer] ?? answer}${tryNote}${transcript ? `: "${transcript}"` : ''}`;
}

export function boxNote(s) {
  if (s.alarm) return 'Demo alarm. A fixed rule raised it.';
  if (s.said_help) return 'Said help. Escalated to the top.';
  if (s.no_answer > 0) return `No answer on try ${s.no_answer}.${s.checkin === 'asking' && s.try > s.no_answer ? ' Asking again.' : ''}`;
  return '';
}

export function boxRankInput(s, now) {
  return {
    ...PROFILE,
    presence: s.presence,
    indoor_f: s.indoor_f ?? PROFILE.indoor_f,
    stale: now - s.lastSeen > STALE_MS,
    no_answer: s.no_answer,
    said_help: s.said_help,
    answered_ok: s.answered_ok,
    alarm: s.alarm,
  };
}

// Time to harm, from docs/lifeline/HackUTD-Lifeline-Agent.md section 3.
// Pure math, no DOM. Lower minutes = more urgent.

export const FACTOR_KEYS = ['battery_min', 'indoor_f', 'unresponsive', 'still', 'stale', 'said_help'];

export const DEVICE_WEIGHT = { o2: 1, dialysis: 1.5, cpap: 1.5, insulin: 1.5, wheelchair: 3 };
const EXPOSURE_MIN = 720;
const EXPOSURE_MIN_VULNERABLE = 240;
// WHO minimum indoor temperature (18 C). Below it the exposure clock shrinks
// linearly to 0 at freezing; the doc leaves the curve open, this is our pick.
const COLD_START_F = 64;
const FREEZING_F = 32;
const PROTECTED_UNDER_MIN = 30;
const MAX_PLACES = 3;
const QUEUE_SIZE = 20;

function coldMinutes(h) {
  const full = h.vulnerable ? EXPOSURE_MIN_VULNERABLE : EXPOSURE_MIN;
  if (h.indoor_f >= COLD_START_F) return full;
  return (full * Math.max(0, h.indoor_f - FREEZING_F)) / (COLD_START_F - FREEZING_F);
}

function presenceFactor(presence) {
  if (presence === 'still') return 0.5;
  if (presence === 'none') return 2;
  return 1;
}

function responseFactor(h) {
  if (h.said_help || h.alarm) return 0;
  if (h.no_answer >= 2) return 0.5;
  if (h.no_answer === 1) return 0.75;
  if (h.answered_ok) return 1.5;
  return 1;
}

export function harmClock(h) {
  const device_min = h.device !== 'none' && h.battery_min !== null ? h.battery_min * DEVICE_WEIGHT[h.device] : null;
  const cold_min = coldMinutes(h);
  const base = device_min === null ? cold_min : Math.min(device_min, cold_min);
  const presence_x = presenceFactor(h.presence);
  const response_x = responseFactor(h);
  const stale_x = h.stale ? 0.75 : 1;
  return {
    id: h.id,
    harm_min: Math.round(base * presence_x * response_x * stale_x),
    factors: {
      battery_min: h.battery_min,
      indoor_f: h.indoor_f,
      unresponsive: h.no_answer > 0,
      still: h.presence === 'still',
      stale: h.stale,
      said_help: h.said_help,
    },
    parts: { device_min, cold_min: Math.round(cold_min), presence_x, response_x, stale_x },
  };
}

export function rankHomes(homes) {
  return homes.map(harmClock).sort((a, b) => a.harm_min - b.harm_min || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

export function queueMessage(ranked) {
  return {
    type: 'queue',
    homes: ranked.slice(0, QUEUE_SIZE).map(({ id, harm_min, factors }) => ({ id, harm_min, factors })),
  };
}

const isProtected = (r) => r.harm_min < PROTECTED_UNDER_MIN || r.factors.said_help;

function protectionReason(r) {
  return r.factors.said_help ? `${r.id} said help` : `${r.id} is under ${PROTECTED_UNDER_MIN} min`;
}

// Returns null when the move is allowed, else the reason it is rejected.
// `by` < 0 moves a home up (more urgent), `by` > 0 moves it down.
export function checkMove(queue, move) {
  const from = queue.findIndex((r) => r.id === move.id);
  if (from < 0) return `${move.id} is not in the queue`;
  if (!Number.isInteger(move.by) || move.by === 0) return `move must be a whole number of places, got ${move.by}`;
  if (Math.abs(move.by) > MAX_PLACES) return `moves ${Math.abs(move.by)} places, limit is ${MAX_PLACES} places`;
  if (!FACTOR_KEYS.includes(move.factor)) return `no named factor (got ${move.factor ?? 'none'})`;
  const to = Math.min(queue.length - 1, Math.max(0, from + move.by));
  const mover = queue[from];
  if (to > from && isProtected(mover)) return `cannot demote: ${protectionReason(mover)}`;
  if (to < from) {
    const pushedDown = queue.slice(to, from).find(isProtected);
    if (pushedDown) return `would push ${protectionReason(pushedDown)} down`;
  }
  return null;
}

export function applyRerank(queue, moves) {
  let q = [...queue];
  const results = moves.map((move) => {
    const reason = checkMove(q, move);
    if (reason) return { move, ok: false, reason };
    const from = q.findIndex((r) => r.id === move.id);
    const to = Math.min(q.length - 1, Math.max(0, from + move.by));
    const [r] = q.splice(from, 1);
    q.splice(to, 0, r);
    return { move, ok: true, reason: null };
  });
  return { queue: q, results };
}

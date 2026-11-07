// Simulated check-ins for the 499 sim homes. Pure, no DOM.
// The real box H000 is never dispatched here: the agent (#15) owns it.

export const MAX_TRIES = 2;

// Demo pacing, picked so the whole run fits in about a minute on stage.
export const PACE = {
  tickMs: 250,
  attemptsPerTick: 5,
  // Path C in the Agent doc: a simulated call returns its outcome after 4 s.
  resultMs: 4000,
  retryMs: 6000,
  coverageMs: 40000,
};

const waiting = (s) => !s.real && s.hitAt !== null && s.attempts === 0;

export function nextAttempts(rankedIds, states, n) {
  const out = [];
  for (const id of rankedIds) {
    if (out.length >= n) break;
    const s = states.get(id);
    if (s && waiting(s) && !s.skipped) out.push(id);
  }
  return out;
}

export function coverageSweep(states, now, windowMs) {
  const out = [];
  for (const s of states.values()) if (waiting(s) && now - s.hitAt >= windowMs) out.push(s.id);
  return out;
}

export function answerFor(home, tryN) {
  if (home.outcome === 'late_ok') return tryN >= 2 ? 'ok' : 'no_answer';
  return home.outcome;
}

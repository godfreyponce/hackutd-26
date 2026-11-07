import { generateHomes, BOUNDS, REAL_BOX_ID } from './homes.js';
import { rankHomes, applyRerank, queueMessage, DEVICE_WEIGHT } from './rank.js';
import { PACE, MAX_TRIES, nextAttempts, coverageSweep, answerFor } from './sim.js';
import { initialBox, applyBoxEvent, boxRankInput } from './box.js';
import { connectBus, hubUrl } from './bus.js';

const HOMES = generateHomes();
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const $ = (id) => document.getElementById(id);

// Stage timing for the wave, tuned by eye for the demo.
const WAVE_MS = 4000;
const FLASH_MS = 700;
const POP_MS = 450;
const WASH_FADE_MS = 1500;
// The agent reacts to queue changes; at most one queue message per 2 s keeps
// the bus readable during the wave, when the top 20 changes every frame.
const QUEUE_GAP_MS = 2000;
const QUEUE_ROWS = 40;
const TRACE_MAX = 200;

const EPICENTER = { lat: 32.962, lon: -96.788 };
const KX = Math.cos((((BOUNDS.latMin + BOUNDS.latMax) / 2) * Math.PI) / 180);
const KM_PER_DEG = 111.32;
const WORLD_W = (BOUNDS.lonMax - BOUNDS.lonMin) * KX;
const WORLD_H = BOUNDS.latMax - BOUNDS.latMin;
const toWorld = (p) => ({ x: (p.lon - BOUNDS.lonMin) * KX, y: BOUNDS.latMax - p.lat });
const EPI = toWorld(EPICENTER);
const HOME_XY = HOMES.map(toWorld);
const HOME_DIST = HOME_XY.map((p) => Math.hypot(p.x - EPI.x, p.y - EPI.y));
const MAX_HOME_DIST = Math.max(...HOME_DIST);

const COLOR = { white: '#f4f7fa', red: '#ff453a', green: '#32d74b', real: '#64d2ff', amber: '#ffb340' };
const DEVICE_LABEL = { o2: 'O2', cpap: 'CPAP', wheelchair: 'Wheelchair', insulin: 'Insulin', dialysis: 'Dialysis' };

// ---------- State ----------
let sim;
let box;
let boxHitAt;
let quake;
let waveAt;
let activeMoves;
let math;
let shown;
let moveById;
let attempts;
let forced;
let lastQueueJson;
let lastQueueAt;
let guardNote;
let eventHtml;
let alertHtml;

function freshSim() {
  return new Map(
    HOMES.filter((h) => !h.real).map((h) => [
      h.id,
      { ...h, hitAt: null, attempts: 0, no_answer: 0, said_help: false, answered_ok: false, alarm: false, pendingAt: null, pendingTry: 0, retryAt: null },
    ]),
  );
}

function resetAll(now) {
  sim = freshSim();
  box = initialBox(now);
  boxHitAt = null;
  quake = null;
  waveAt = null;
  activeMoves = [];
  math = [];
  shown = [];
  moveById = new Map();
  attempts = 0;
  forced = 0;
  lastQueueJson = '';
  lastQueueAt = -Infinity;
  guardNote = null;
  traceEntries.length = 0;
  $('trace-list').replaceChildren();
  $('queue-list').replaceChildren();
  rowEls.clear();
  eventHtml = '';
  alertHtml = '';
  renderEvent();
  renderAll();
}

// ---------- Status ----------
function stateOf(id) {
  return id === REAL_BOX_ID ? box : sim.get(id);
}

function hitAtOf(id) {
  return id === REAL_BOX_ID ? boxHitAt : sim.get(id).hitAt;
}

function statusOf(id) {
  const s = stateOf(id);
  if (hitAtOf(id) === null) return 'white';
  const escalated = s.said_help || s.alarm || (id !== REAL_BOX_ID && s.no_answer >= MAX_TRIES);
  if (escalated) return 'escalated';
  if (s.answered_ok) return 'ok';
  if (s.no_answer > 0) return 'noanswer';
  return 'hit';
}

const boxLit = () => box.alarm || box.said_help || box.no_answer > 0;

// ---------- Quake and wave ----------
function startQuake(now, peakG, from) {
  if (quake) return;
  quake = { at: now, peakG };
  waveAt = HOME_DIST.map((d) => now + (d / MAX_HOME_DIST) * WAVE_MS);
  const when = new Date().toLocaleTimeString();
  const peak = typeof peakG === 'number' ? `, peak ${peakG} g` : '';
  eventHtml = `<b>Earthquake</b>${peak}, ${when}. The wave is hitting 500 homes.`;
  renderEvent();
  addTrace('EVENT', `Quake${peak} from ${from}. Every home in the area gets a contact attempt.`, null, 'dashboard');
}

function advanceWave(now) {
  if (!quake) return;
  HOMES.forEach((h, i) => {
    if (waveAt[i] > now) return;
    if (h.real) {
      if (boxHitAt === null) boxHitAt = waveAt[i];
    } else {
      const s = sim.get(h.id);
      if (s.hitAt === null) s.hitAt = waveAt[i];
    }
  });
}

// ---------- Simulated check-ins ----------
function attempt(s, now, tryN) {
  s.attempts += 1;
  attempts += 1;
  s.pendingTry = tryN;
  s.pendingAt = now + PACE.resultMs;
  s.retryAt = null;
}

function resolve(s, now) {
  const answer = answerFor(s, s.pendingTry);
  s.pendingAt = null;
  if (answer === 'ok') {
    s.answered_ok = true;
    s.no_answer = 0;
  } else if (answer === 'help') {
    s.said_help = true;
  } else {
    s.no_answer = s.pendingTry;
    if (s.pendingTry < MAX_TRIES) s.retryAt = now + PACE.retryMs;
  }
}

function rank(now) {
  const inputs = [];
  if (boxHitAt !== null) inputs.push(boxRankInput(box, now));
  for (const s of sim.values()) if (s.hitAt !== null) inputs.push(s);
  math = rankHomes(inputs);
  const { queue, results } = applyRerank(math, activeMoves);
  shown = queue;
  moveById = new Map(results.filter((r) => r.ok).map((r) => [r.move.id, r.move]));
}

function tick() {
  const now = performance.now();
  if (quake) {
    for (const s of sim.values()) {
      if (s.pendingAt !== null && s.pendingAt <= now) resolve(s, now);
      if (s.retryAt !== null && s.retryAt <= now) attempt(s, now, s.pendingTry + 1);
    }
    rank(now);
    // Calls start once the wave has passed every home, so the ranking picks who goes first.
    if (now >= quake.at + WAVE_MS) {
      for (const id of nextAttempts(math.map((r) => r.id), sim, PACE.attemptsPerTick)) attempt(sim.get(id), now, 1);
    }
    const swept = coverageSweep(sim, now, PACE.coverageMs);
    if (swept.length) {
      for (const id of swept) attempt(sim.get(id), now, 1);
      forced += swept.length;
      const list = swept.slice(0, 6).join(', ') + (swept.length > 6 ? ` and ${swept.length - 6} more` : '');
      addTrace('COVERAGE', `Forced recheck on ${swept.length} untouched ${swept.length === 1 ? 'home' : 'homes'}: ${list}.`, 'schedule_recheck', 'dashboard');
    }
    maybeSendQueue(now);
  }
  renderAll();
}

function maybeSendQueue(now) {
  if (math.length === 0 || now - lastQueueAt < QUEUE_GAP_MS) return;
  const msg = queueMessage(math);
  const json = JSON.stringify(msg.homes);
  if (json === lastQueueJson) return;
  bus.send(msg);
  lastQueueJson = json;
  lastQueueAt = now;
}

// ---------- Agent rerank ----------
function onRerank(msg) {
  const moves = Array.isArray(msg.moves) ? msg.moves.filter((m) => m && typeof m === 'object') : [];
  const { results } = applyRerank(math, moves);
  activeMoves = results.filter((r) => r.ok).map((r) => r.move);
  for (const r of results) {
    if (r.ok) {
      const dir = r.move.by < 0 ? 'up' : 'down';
      addTrace('GUARD', `Rerank accepted: ${r.move.id} ${dir} ${Math.abs(r.move.by)}, factor ${r.move.factor}.`, null, 'guardrail');
    } else {
      addTrace('BLOCKED', `Override blocked: ${r.move.id ?? 'unknown home'}, ${r.reason}.`, null, 'guardrail');
    }
  }
  const blocked = results.filter((r) => !r.ok);
  const why = typeof msg.reason === 'string' && msg.reason ? ` Agent reason: ${msg.reason}` : '';
  guardNote = blocked.length
    ? { ok: false, text: `Override blocked: ${blocked.map((r) => `${r.move.id ?? '?'} ${r.reason}`).join('; ')}.${why}` }
    : { ok: true, text: `Agent moved ${results.length} ${results.length === 1 ? 'home' : 'homes'} within the guardrail.${why}` };
  rank(performance.now());
  renderAll();
}

// ---------- Bus ----------
const bus = connectBus(hubUrl(location.search), {
  onStatus(status) {
    const el = $('hub');
    el.dataset.status = status;
    $('hub-text').textContent =
      status === 'connected' ? `Hub ${hubUrl(location.search)}` : status === 'offline' ? 'Hub offline, retrying' : 'Connecting to hub';
  },
  onMessage(msg) {
    const now = performance.now();
    switch (msg.type) {
      case 'queue':
        return;
      case 'reset':
        resetAll(now);
        return;
      case 'agent':
        addTrace(String(msg.step ?? 'STEP'), String(msg.text ?? ''), msg.tool ? String(msg.tool) : null, 'agent');
        return;
      case 'rerank':
        onRerank(msg);
        return;
      case 'alert':
        alertHtml = `Official alert: ${esc(msg.headline || msg.event || 'alert')} (${esc(msg.source ?? 'unknown')}).`;
        renderEvent();
        return;
      case 'quake':
        startQuake(now, msg.peak_g, 'the box');
        break;
    }
    box = applyBoxEvent(box, msg, now);
    if (quake) rank(now);
    renderAll();
  },
});

addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const now = performance.now();
  if (e.key === 'q') startQuake(now, null, 'the q key on this page');
  if (e.key === 'r') resetAll(now);
});

// ---------- Rendering: text panels ----------
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function renderEvent() {
  const el = $('event');
  const html = [eventHtml, alertHtml].filter(Boolean).join(' ');
  el.innerHTML = html || 'No event yet. Waiting for the box.';
  el.classList.toggle('live', Boolean(html));
}

function setText(id, text) {
  const el = $(id);
  if (el.textContent !== String(text)) el.textContent = text;
}

function renderCounters() {
  let hit = 0;
  let checked = 0;
  let noAnswer = 0;
  let escalated = 0;
  for (const h of HOMES) {
    if (hitAtOf(h.id) === null) continue;
    hit += 1;
    const s = stateOf(h.id);
    if (s.answered_ok || s.said_help) checked += 1;
    if (s.no_answer > 0 && !s.answered_ok && !s.said_help) noAnswer += 1;
    if (statusOf(h.id) === 'escalated') escalated += 1;
  }
  setText('c-hit', hit);
  setText('c-checked', checked);
  setText('c-noanswer', noAnswer);
  setText('c-escalated', escalated);
  setText('c-attempts', attempts);
  setText('c-forced', forced);
}

const CHECKIN_LABEL = { asking: 'Asking', ok: 'Okay', help: 'Said help', no_answer: 'No answer', alarm: 'Alarm (demo only)', clear: 'Cleared' };
const PRESENCE_LABEL = { moving: 'Moving', still: 'Still', none: 'Nobody detected' };

function renderBox() {
  setText('b-presence', PRESENCE_LABEL[box.presence] ?? box.presence);
  setText('b-checkin', box.checkin ? `${CHECKIN_LABEL[box.checkin] ?? box.checkin}${box.try ? `, try ${box.try}` : ''}` : 'None yet');
  setText('b-heard', box.heard ? `${box.heard.answer}${box.heard.transcript ? `: "${box.heard.transcript}"` : ''}` : 'None yet');
  setText('b-power', `${box.power === 'battery' ? 'Battery' : 'Mains'}${box.battery_pct != null ? `, ${box.battery_pct}%` : ''}`);
  const idx = shown.findIndex((r) => r.id === REAL_BOX_ID);
  setText('b-rank', idx < 0 ? 'Not hit' : `#${idx + 1} of ${shown.length}`);
  setText('b-harm', idx < 0 ? 'None yet' : `${shown[idx].harm_min} min`);
  let note = '';
  if (box.alarm) note = 'Alarm raised by the agent. Demo only, no real call.';
  else if (box.said_help) note = 'Said help. Escalated to the top.';
  else if (box.no_answer > 0) note = `No response after an event, ${box.no_answer} ${box.no_answer === 1 ? 'try' : 'tries'}.`;
  const noteEl = $('box-note');
  noteEl.hidden = !note;
  setText('box-note', note);
  $('box-card').classList.toggle('lit', boxLit());
}

function chip(text, cls = '') {
  return `<span class="chip ${cls}">${esc(text)}</span>`;
}

function chipsFor(id, r) {
  const s = stateOf(id);
  const f = r.factors;
  const out = [];
  if (s.device === 'none' || f.battery_min === null) out.push(chip('no device'));
  else {
    const w = DEVICE_WEIGHT[s.device];
    out.push(chip(`${DEVICE_LABEL[s.device]} ${f.battery_min} min${w !== 1 ? ` ×${w}` : ''}`, r.parts.device_min < 60 ? 'bad' : 'on'));
  }
  out.push(chip(`${f.indoor_f}°F${r.parts.cold_min < (s.vulnerable ? 240 : 720) ? ' cold' : ''}${s.vulnerable ? ', vulnerable' : ''}`, f.indoor_f < 64 ? 'warn' : s.vulnerable ? 'on' : ''));
  if (s.presence === 'still') out.push(chip('still ×0.5', 'bad'));
  else if (s.presence === 'none') out.push(chip('nobody ×2', 'on'));
  else out.push(chip('moving'));
  if (s.alarm) out.push(chip('alarm, 0 min', 'bad'));
  else if (f.said_help) out.push(chip('help, 0 min', 'bad'));
  else if (s.no_answer >= 2) out.push(chip(`no answer ×${s.no_answer}, ×0.5`, 'bad'));
  else if (s.no_answer === 1) out.push(chip('no answer, ×0.75', 'warn'));
  else if (s.answered_ok) out.push(chip('okay ×1.5', 'good'));
  else if (s.pendingAt != null) out.push(chip('calling', 'on'));
  else out.push(chip('not reached'));
  out.push(f.stale ? chip('stale ×0.75', 'warn') : chip('fresh'));
  return out.join('');
}

const rowEls = new Map();

function fillRow(el, r, place) {
  const real = r.id === REAL_BOX_ID;
  el.className = `row s-${statusOf(r.id)}${real ? ' real' : ''}${real && boxLit() ? ' lit' : ''}`;
  const mv = moveById.get(r.id);
  const flags = [
    real ? '<span class="tag real">real box</span>' : '',
    mv ? `<span class="tag agent">agent ${mv.by < 0 ? '↑' : '↓'}${Math.abs(mv.by)} ${esc(mv.factor)}</span>` : '',
  ].join('');
  el.innerHTML =
    `<span class="rank">${place}</span><span class="sdot"></span><span class="id">${r.id}</span>` +
    `<span class="flag">${flags}</span><span class="harm"><b>${r.harm_min}</b> min</span>` +
    `<span class="chips">${chipsFor(r.id, r)}</span>`;
}

function renderQueue() {
  const list = $('queue-list');
  $('queue-empty').hidden = shown.length > 0;
  const top = shown.slice(0, QUEUE_ROWS);
  const before = new Map();
  for (const [id, el] of rowEls) before.set(id, el.getBoundingClientRect().top);
  const keep = new Set(top.map((r) => r.id));
  for (const [id, el] of rowEls) {
    if (!keep.has(id)) {
      el.remove();
      rowEls.delete(id);
    }
  }
  top.forEach((r, i) => {
    let el = rowEls.get(r.id);
    if (!el) {
      el = document.createElement('li');
      rowEls.set(r.id, el);
    }
    fillRow(el, r, i + 1);
    list.appendChild(el);
  });
  if (!reducedMotion.matches) {
    for (const r of top) {
      const old = before.get(r.id);
      if (old === undefined) continue;
      const el = rowEls.get(r.id);
      const dy = old - el.getBoundingClientRect().top;
      if (Math.abs(dy) > 1) el.animate([{ transform: `translateY(${dy}px)` }, { transform: 'none' }], { duration: 350, easing: 'cubic-bezier(.2,.8,.2,1)' });
    }
  }

  const pinned = $('pinned');
  const idx = shown.findIndex((r) => r.id === REAL_BOX_ID);
  if (idx >= QUEUE_ROWS) {
    let el = pinned.firstElementChild;
    if (!el) {
      el = document.createElement('div');
      pinned.appendChild(el);
    }
    fillRow(el, shown[idx], idx + 1);
  } else {
    pinned.replaceChildren();
  }

  const guard = $('guard');
  guard.hidden = !guardNote;
  if (guardNote) {
    guard.textContent = guardNote.text;
    guard.classList.toggle('ok', guardNote.ok);
  }
}

// ---------- Rendering: trace ----------
const traceEntries = [];
const TOOL_ICON =
  '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M10.5 1a4.5 4.5 0 0 0-4.3 5.8L1.3 11.7a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l4.9-4.9A4.5 4.5 0 0 0 15 5.5l-2.6 2.6-2.5-.6-.6-2.5 2.6-2.6A4.5 4.5 0 0 0 10.5 1z"/></svg>';

function addTrace(step, text, tool, who) {
  traceEntries.push({ step, tool, who });
  const li = document.createElement('li');
  li.className = `tr ${step.replace(/[^A-Z]/g, '')}`;
  li.innerHTML =
    `<span class="time">${esc(new Date().toLocaleTimeString())}</span><span class="step">${esc(step)}</span>` +
    `<span class="who">${esc(who)}</span>` +
    (tool ? `<span class="tool">${TOOL_ICON}${esc(tool)}</span>` : '<span></span>') +
    `<span class="text">${esc(text)}</span>`;
  const list = $('trace-list');
  list.prepend(li);
  while (list.children.length > TRACE_MAX) list.lastElementChild.remove();
  const agentSteps = traceEntries.filter((e) => e.who === 'agent');
  setText('trace-counts', `${agentSteps.length} agent steps, ${agentSteps.filter((e) => e.tool).length} tool calls`);
}

// ---------- Rendering: map ----------
const canvas = $('map');
const ctx = canvas.getContext('2d');
let view = null;
let backdrop = null;

function layout() {
  const rect = canvas.getBoundingClientRect();
  const dpr = devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  const pad = { t: 24, r: 24, b: 56, l: 24 };
  const scale = Math.min((rect.width - pad.l - pad.r) / WORLD_W, (rect.height - pad.t - pad.b) / WORLD_H);
  const ox = pad.l + (rect.width - pad.l - pad.r - WORLD_W * scale) / 2;
  const oy = pad.t + (rect.height - pad.t - pad.b - WORLD_H * scale) / 2;
  view = { w: rect.width, h: rect.height, dpr, scale, ox, oy, dot: Math.min(5, Math.max(2.4, scale * 0.0004)) };
  backdrop = drawBackdrop();
}

const px = (p) => [view.ox + p.x * view.scale, view.oy + p.y * view.scale];

function drawBackdrop() {
  const off = document.createElement('canvas');
  off.width = canvas.width;
  off.height = canvas.height;
  const c = off.getContext('2d');
  c.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
  c.fillStyle = '#0a0d12';
  c.fillRect(0, 0, view.w, view.h);
  const w = WORLD_W * view.scale;
  const h = WORLD_H * view.scale;
  c.fillStyle = '#0e131b';
  c.fillRect(view.ox, view.oy, w, h);
  c.strokeStyle = '#18202b';
  c.lineWidth = 1;
  c.beginPath();
  for (let lon = Math.ceil(BOUNDS.lonMin * 100) / 100; lon <= BOUNDS.lonMax; lon += 0.01) {
    const x = view.ox + (lon - BOUNDS.lonMin) * KX * view.scale;
    c.moveTo(x, view.oy);
    c.lineTo(x, view.oy + h);
  }
  for (let lat = Math.ceil(BOUNDS.latMin * 100) / 100; lat <= BOUNDS.latMax; lat += 0.01) {
    const y = view.oy + (BOUNDS.latMax - lat) * view.scale;
    c.moveTo(view.ox, y);
    c.lineTo(view.ox + w, y);
  }
  c.stroke();
  c.strokeStyle = '#263140';
  c.strokeRect(view.ox + 0.5, view.oy + 0.5, w - 1, h - 1);
  c.fillStyle = '#5b6878';
  c.font = '600 12px -apple-system, BlinkMacSystemFont, sans-serif';
  c.fillText('RICHARDSON, TX', view.ox + 12, view.oy + 20);
  const km = view.scale / KM_PER_DEG;
  const sx = view.ox + w - 12 - 2 * km;
  const sy = view.oy + h - 14;
  c.strokeStyle = '#5b6878';
  c.beginPath();
  c.moveTo(sx, sy - 4);
  c.lineTo(sx, sy);
  c.lineTo(sx + 2 * km, sy);
  c.lineTo(sx + 2 * km, sy - 4);
  c.stroke();
  c.font = '11px -apple-system, BlinkMacSystemFont, sans-serif';
  c.fillText('2 km', sx + km - 12, sy - 6);
  return off;
}

function drawWave(now) {
  const t = now - quake.at;
  const [ex, ey] = px(EPI);
  const motion = !reducedMotion.matches;
  if (motion) {
    const r = (t / WAVE_MS) * MAX_HOME_DIST * view.scale;
    const far = Math.max(...[[0, 0], [view.w, 0], [0, view.h], [view.w, view.h]].map(([x, y]) => Math.hypot(x - ex, y - ey)));
    if (t < FLASH_MS) {
      ctx.fillStyle = `rgba(255,69,58,${0.32 * (1 - t / FLASH_MS)})`;
      ctx.fillRect(0, 0, view.w, view.h);
    }
    const exitT = (far / (MAX_HOME_DIST * view.scale)) * WAVE_MS;
    const wash = t < exitT ? 0.16 : 0.16 * Math.max(0, 1 - (t - exitT) / WASH_FADE_MS);
    if (wash > 0) {
      ctx.fillStyle = `rgba(255,69,58,${wash})`;
      ctx.beginPath();
      ctx.arc(ex, ey, Math.min(r, far), 0, Math.PI * 2);
      ctx.fill();
    }
    if (r < far + 100) {
      const band = Math.max(40, view.scale * 0.006);
      const g = ctx.createRadialGradient(ex, ey, Math.max(0, r - band), ex, ey, r);
      g.addColorStop(0, 'rgba(255,69,58,0)');
      g.addColorStop(0.8, 'rgba(255,69,58,0.5)');
      g.addColorStop(1, 'rgba(255,69,58,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(ex, ey, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,140,130,0.9)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(ex, ey, r, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.strokeStyle = COLOR.red;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(ex - 7, ey - 7);
  ctx.lineTo(ex + 7, ey + 7);
  ctx.moveTo(ex + 7, ey - 7);
  ctx.lineTo(ex - 7, ey + 7);
  ctx.stroke();
  ctx.fillStyle = '#ff8a80';
  ctx.font = '600 11px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('EPICENTER', ex + 10, ey + 4);
}

function dotColor(status) {
  if (status === 'white') return COLOR.white;
  if (status === 'ok') return COLOR.green;
  return COLOR.red;
}

function drawDot(x, y, status, hitAt, now) {
  const motion = !reducedMotion.matches;
  let r = view.dot;
  if (motion && hitAt !== null && now - hitAt < POP_MS) {
    const p = (now - hitAt) / POP_MS;
    r *= 1 + 1.6 * Math.sin(Math.PI * p);
    ctx.strokeStyle = `rgba(255,69,58,${0.8 * (1 - p)})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(x, y, view.dot * (1 + 4 * p), 0, Math.PI * 2);
    ctx.stroke();
  }
  if (status === 'escalated') {
    const halo = view.dot * (motion ? 2.2 + 0.5 * Math.sin(now / 250) : 2.4);
    ctx.fillStyle = 'rgba(255,69,58,0.28)';
    ctx.beginPath();
    ctx.arc(x, y, halo, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = dotColor(status);
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function drawRealBox(now) {
  const i = 0;
  const [x, y] = px(HOME_XY[i]);
  const status = statusOf(REAL_BOX_ID);
  if (boxLit()) {
    const motion = !reducedMotion.matches;
    const halo = view.dot * (motion ? 4 + 1.5 * Math.sin(now / 200) : 4.5);
    ctx.fillStyle = 'rgba(255,69,58,0.3)';
    ctx.beginPath();
    ctx.arc(x, y, halo, 0, Math.PI * 2);
    ctx.fill();
  }
  drawDot(x, y, status === 'escalated' ? 'hit' : status, boxHitAt, now);
  ctx.strokeStyle = COLOR.real;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(x, y, view.dot * 2.6, 0, Math.PI * 2);
  ctx.stroke();
  const label = 'H000 real box';
  ctx.font = '700 11px ui-monospace, SF Mono, Menlo, monospace';
  const tw = ctx.measureText(label).width;
  const lx = x + view.dot * 3.4;
  ctx.fillStyle = 'rgba(10,13,18,0.85)';
  ctx.fillRect(lx - 4, y - 9, tw + 8, 18);
  ctx.fillStyle = COLOR.real;
  ctx.fillText(label, lx, y + 4);
}

function draw(now) {
  ctx.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
  ctx.drawImage(backdrop, 0, 0, view.w, view.h);
  if (quake) drawWave(now);
  HOMES.forEach((h, i) => {
    if (h.real) return;
    const [x, y] = px(HOME_XY[i]);
    drawDot(x, y, statusOf(h.id), sim.get(h.id).hitAt, now);
  });
  drawRealBox(now);
}

// ---------- Loop ----------
function renderAll() {
  renderCounters();
  renderBox();
  renderQueue();
}

function frame(now) {
  advanceWave(now);
  draw(now);
  renderCounters();
  requestAnimationFrame(frame);
}

new ResizeObserver(layout).observe(canvas);
layout();
resetAll(performance.now());
setInterval(tick, PACE.tickMs);
requestAnimationFrame(frame);

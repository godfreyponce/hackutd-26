import { generateHomes, BOUNDS, REAL_BOX_ID } from './homes.js';
import { rankHomes, applyRerank, queueMessage, DEVICE_WEIGHT } from './rank.js';
import { PACE, MAX_TRIES, nextAttempts, coverageSweep, answerFor } from './sim.js';
import { initialBox, applyBoxEvent, boxRankInput } from './box.js';
import { connectBus, hubUrl } from './bus.js';
import { initialCamera, cameraEvent, viewAt, arrivalAt, flying } from './camera.js';
import { PALETTE, loadBasemap, drawGlobe, drawCity, drawRedRoads, drawRoadLabels } from './basemap.js';

const HOMES = generateHomes();
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const $ = (id) => document.getElementById(id);

// Stage timing for the wave, tuned by eye for the demo.
const WAVE_MS = 4000;
const FLASH_MS = 700;
const POP_MS = 450;
const WASH_FADE_MS = 1500;
const PULSE_MS = 1100;
// The agent reacts to queue changes; at most one queue message per 2 s keeps
// the bus readable during the wave, when the top 20 changes every frame.
const QUEUE_GAP_MS = 2000;
const QUEUE_ROWS = 40;
const TRACE_MAX = 200;
// One coverage line per sweep instead of one per tick; the Agent doc's math
// cadence is 10 s, half that keeps the stage demo moving.
const COVERAGE_EVERY_MS = 5000;

const EPICENTER = { lat: 32.962, lon: -96.788 };
const KX = Math.cos((((BOUNDS.latMin + BOUNDS.latMax) / 2) * Math.PI) / 180);
const EARTH_KM = 6371;
const RAD = Math.PI / 180;
// Distances in degrees of latitude, so the wave reaches each home in order.
const flat = (p) => ({ x: (p.lon - BOUNDS.lonMin) * KX, y: BOUNDS.latMax - p.lat });
const EPI = flat(EPICENTER);
const HOME_DIST = HOMES.map(flat).map((p) => Math.hypot(p.x - EPI.x, p.y - EPI.y));
const MAX_HOME_DIST = Math.max(...HOME_DIST);
const CITY_CENTER = { lon: (BOUNDS.lonMin + BOUNDS.lonMax) / 2, lat: (BOUNDS.latMin + BOUNDS.latMax) / 2 };
// Camera framing, tuned by eye: the globe centers a little south of Texas so
// Texas sits above the middle; the home view shows about 1.5 km around H000.
const GLOBE_LAT = 22;
const GLOBE_FILL = 0.42;
const HOME_ZOOM = 6;
// The streets fade in between these shares of the city zoom.
const CITY_FADE = [0.02, 0.25];

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
let lastSweepAt;
let eventHtml;
let alertHtml;
let cam;
let boxAlarmed = false;

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
  lastSweepAt = -Infinity;
  traceEntries.length = 0;
  $('trace-list').replaceChildren();
  setText('trace-counts', '0 agent steps, 0 tool calls');
  $('trace-empty').hidden = false;
  $('queue-list').replaceChildren();
  rowEls.clear();
  eventHtml = '';
  alertHtml = '';
  boxAlarmed = false;
  cam = cam ? moveCamera('reset', now) : initialCamera(now, views, { reduced: reducedMotion.matches });
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
  cam = moveCamera('quake', now);
  // The wave plays once the camera lands on the street map.
  const waveStart = Math.max(now, arrivalAt(cam));
  quake = { at: now, waveStart, peakG };
  waveAt = HOME_DIST.map((d) => waveStart + (d / MAX_HOME_DIST) * WAVE_MS);
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
  const mathPlace = new Map(math.map((r, i) => [r.id, i]));
  moveById = new Map(
    results.filter((r) => r.ok && shown[mathPlace.get(r.move.id)]?.id !== r.move.id).map((r) => [r.move.id, r.move]),
  );
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
    if (now >= quake.waveStart + WAVE_MS) {
      for (const id of nextAttempts(math.map((r) => r.id), sim, PACE.attemptsPerTick)) attempt(sim.get(id), now, 1);
    }
    if (now - lastSweepAt >= COVERAGE_EVERY_MS) {
      lastSweepAt = now;
      forceRechecks(coverageSweep(sim, now, PACE.coverageMs), now);
    }
    maybeSendQueue(now);
  }
  renderAll();
}

function forceRechecks(ids, now) {
  if (ids.length === 0) return;
  for (const id of ids) attempt(sim.get(id), now, 1);
  forced += ids.length;
  const list = ids.slice(0, 6).join(', ') + (ids.length > 6 ? ` and ${ids.length - 6} more` : '');
  addTrace('COVERAGE', `Forced recheck on ${ids.length} untouched ${ids.length === 1 ? 'home' : 'homes'}: ${list}.`, 'schedule_recheck', 'dashboard');
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
  if (!Array.isArray(msg.moves)) {
    addTrace('BLOCKED', 'Override blocked: the rerank message has no moves list.', null, 'guardrail');
    guardNote = { ok: false, text: 'Override blocked: the rerank message has no moves list.' };
    renderAll();
    return;
  }
  const moves = msg.moves.filter((m) => m && typeof m === 'object');
  const { results } = applyRerank(math, moves);
  activeMoves = results.filter((r) => r.ok).map((r) => r.move);
  for (const r of results) {
    if (r.ok) {
      const dir = r.move.by < 0 ? 'up' : 'down';
      addTrace('GUARD', `Rerank accepted: ${r.move.id} ${dir} ${Math.abs(r.move.by)}, factor ${r.move.factor}.`, null, 'guardrail');
    } else {
      addTrace('BLOCKED', `Override blocked: ${r.reason}.`, null, 'guardrail');
    }
  }
  const blocked = results.filter((r) => !r.ok);
  const why = typeof msg.reason === 'string' && msg.reason ? ` Agent reason: ${msg.reason}` : '';
  guardNote = blocked.length
    ? { ok: false, text: `Override blocked: ${blocked.map((r) => r.reason).join('; ')}.${why}` }
    : { ok: true, text: `Agent moved ${results.length} ${results.length === 1 ? 'home' : 'homes'} within the guardrail.${why}` };
  rank(performance.now());
  renderAll();
}

// ---------- Bus ----------
const bus = connectBus(hubUrl(location.search), {
  onStatus(status) {
    const el = $('hub');
    el.dataset.status = status;
    el.title = hubUrl(location.search);
    document.body.dataset.hub = status;
    $('hub-text').textContent =
      status === 'connected' ? 'Hub connected' : status === 'offline' ? 'Hub offline, retrying' : 'Connecting to hub';
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
        alertHtml = alertLine(msg);
        renderEvent();
        return;
      case 'quake':
        startQuake(now, msg.peak_g, 'the box');
        break;
    }
    box = applyBoxEvent(box, msg, now);
    followBox(now);
    if (quake) rank(now);
    renderAll();
  },
});

addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const now = performance.now();
  if (e.key === 'q') startQuake(now, null, 'the q key on this page');
  if (e.key === 'r') resetAll(now);
  if (e.key === 'v') cam = moveCamera('v', now);
  if (e.key === '?') $('keys').hidden = !$('keys').hidden;
});

// ---------- Rendering: text panels ----------
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

const ALERT_LEVELS = ['info', 'watch', 'warning', 'emergency'];

function alertLine(msg) {
  const level = ALERT_LEVELS.includes(msg.level) ? msg.level : 'watch';
  const label = [msg.source ?? 'official', msg.level ?? 'alert'].map((s) => esc(String(s).toUpperCase())).join(' ');
  const demo = msg.demo === true ? 'DEMO, not a real alert. ' : '';
  return `<b class="lvl lvl-${level}">${label}</b> ${demo}${esc(msg.headline || msg.event || 'Alert')}`;
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
  for (const [id, n] of [['c-hit', hit], ['c-checked', checked], ['c-noanswer', noAnswer], ['c-escalated', escalated]]) {
    $(id).parentElement.classList.toggle('zero', n === 0);
  }
}

const CHECKIN_LABEL = { asking: 'Asking', ok: 'Okay', help: 'Said help', no_answer: 'No answer', alarm: 'Alarm (demo)', clear: 'Cleared' };
const ANSWER_LABEL = { ok: 'Okay', help: 'Help', no_answer: 'No answer' };
const PRESENCE_LABEL = { moving: 'Moving', still: 'Still', none: 'Nobody detected' };

function renderBox() {
  setText('b-presence', PRESENCE_LABEL[box.presence] ?? box.presence);
  const showTry = box.try && ['asking', 'no_answer', 'alarm'].includes(box.checkin);
  setText('b-checkin', box.checkin ? `${CHECKIN_LABEL[box.checkin] ?? box.checkin}${showTry ? `, try ${box.try}` : ''}` : 'None yet');
  setText('b-heard', box.heard ? `${ANSWER_LABEL[box.heard.answer] ?? box.heard.answer}${box.heard.transcript ? `: "${box.heard.transcript}"` : ''}` : 'None yet');
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
  $('trace-empty').hidden = true;
  setText('trace-counts', `${agentSteps.length} agent steps, ${agentSteps.filter((e) => e.tool).length} tool calls`);
}

// ---------- Rendering: map ----------
const { geoOrthographic, geoDistance } = globalThis.d3;
const canvas = $('map');
const ctx = canvas.getContext('2d');
const proj = geoOrthographic();
const REAL = HOMES[0];
let view = null;
let views = null;
let basemap = null;
let baseLayer = { canvas: document.createElement('canvas'), key: '' };
let redLayer = { canvas: document.createElement('canvas'), key: '' };

loadBasemap()
  .then((m) => {
    basemap = m;
  })
  .catch((err) => console.error('Map data did not load:', err));

function moveCamera(event, now) {
  return cameraEvent(cam, event, now, views, { reduced: reducedMotion.matches });
}

// The camera holds on H000 while its alarm or a "help" is up.
function followBox(now) {
  const alarmed = box.alarm || box.said_help;
  if (alarmed !== boxAlarmed) cam = moveCamera(alarmed ? 'alarm' : 'clear', now);
  boxAlarmed = alarmed;
}

function layout() {
  const rect = canvas.getBoundingClientRect();
  const dpr = devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  // Room for the stage switch on top and the legend below.
  const pad = { x: 24, t: 52, b: 64 };
  const w = rect.width;
  const h = rect.height;
  view = { w, h, dpr, cx: w / 2, cy: pad.t + (h - pad.t - pad.b) / 2 };
  const city = Math.min(
    (w - 2 * pad.x) / ((BOUNDS.lonMax - BOUNDS.lonMin) * KX * RAD),
    (h - pad.t - pad.b) / ((BOUNDS.latMax - BOUNDS.latMin) * RAD),
  );
  views = {
    world: { lon: CITY_CENTER.lon, lat: GLOBE_LAT, scale: Math.min(w, h) * GLOBE_FILL },
    city: { ...CITY_CENTER, scale: city },
    home: { lon: REAL.lon, lat: REAL.lat, scale: city * HOME_ZOOM },
  };
}

function aim(v) {
  proj
    .rotate([-v.lon, -v.lat])
    .scale(v.scale)
    .translate([view.cx, view.cy])
    .clipExtent([[0, 0], [view.w, view.h]]);
}

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const zoomOf = (v) => v.scale / views.city.scale;
const cityAlpha = (v) => smooth(Math.log(CITY_FADE[0]), Math.log(CITY_FADE[1]), Math.log(zoomOf(v)));
const facing = (p, v) => geoDistance([p.lon, p.lat], [v.lon, v.lat]) < Math.PI / 2 - 0.05;
const toScreen = (p) => proj([p.lon, p.lat]);

// Redraws an offscreen layer only when the view moved.
function cached(layer, key, paint) {
  const c = layer.canvas;
  if (layer.key === key) return c;
  if (c.width !== canvas.width || c.height !== canvas.height) {
    c.width = canvas.width;
    c.height = canvas.height;
  }
  const g = c.getContext('2d');
  g.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
  g.clearRect(0, 0, view.w, view.h);
  paint(g);
  layer.key = key;
  return c;
}

const viewKey = (v) => `${v.lon},${v.lat},${v.scale},${canvas.width},${canvas.height},${Boolean(basemap)}`;

function drawBase(v, cityA) {
  return cached(baseLayer, viewKey(v), (c) => {
    c.fillStyle = PALETTE.space;
    c.fillRect(0, 0, view.w, view.h);
    if (!basemap) return;
    if (cityA < 1) drawGlobe(c, basemap, proj, view.w, view.h, v.scale / views.world.scale);
    else {
      c.fillStyle = PALETTE.land;
      c.fillRect(0, 0, view.w, view.h);
    }
    if (cityA <= 0) return;
    drawCity(c, basemap, proj, view.dpr, cityA, zoomOf(v));
    c.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
    drawRoadLabels(c, basemap, proj, smooth(0.6, 1, cityA));
    drawScaleBar(c, v, smooth(0.6, 1, cityA));
  });
}

const SCALE_STEPS_KM = [0.25, 0.5, 1, 2, 5, 10, 20, 50];

function drawScaleBar(c, v, alpha) {
  const pxPerKm = v.scale / EARTH_KM;
  const km = SCALE_STEPS_KM.filter((k) => k * pxPerKm <= 120).pop() ?? SCALE_STEPS_KM[0];
  const len = km * pxPerKm;
  const x = view.w - 20 - len;
  const y = view.h - 18;
  c.save();
  c.globalAlpha = alpha;
  c.strokeStyle = '#6b7889';
  c.lineWidth = 1;
  c.beginPath();
  c.moveTo(x, y - 4);
  c.lineTo(x, y);
  c.lineTo(x + len, y);
  c.lineTo(x + len, y - 4);
  c.stroke();
  c.fillStyle = '#8794a3';
  c.font = '11px -apple-system, BlinkMacSystemFont, sans-serif';
  c.textAlign = 'center';
  c.fillText(km < 1 ? `${km * 1000} m` : `${km} km`, x + len / 2, y - 6);
  c.restore();
}

// ---------- Map: quake ----------
function drawPulse(x, y, t) {
  const motion = !reducedMotion.matches;
  if (motion) {
    for (let k = 0; k < 3; k++) {
      const p = ((t + (k * PULSE_MS) / 3) % PULSE_MS) / PULSE_MS;
      ctx.strokeStyle = `rgba(255,69,58,${0.75 * (1 - p)})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, 5 + 46 * p, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.fillStyle = 'rgba(255,69,58,0.35)';
  ctx.beginPath();
  ctx.arc(x, y, 9, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = COLOR.red;
  ctx.beginPath();
  ctx.arc(x, y, 4.5, 0, Math.PI * 2);
  ctx.fill();
}

// An uneven edge so the red reads as a stain spreading, not a perfect ring.
// The wobble stays within a few percent, so dots still turn red as it passes.
function stainPath(x, y, r, t) {
  const p = new Path2D();
  const n = 120;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    const k =
      1 +
      0.07 * (0.5 * Math.sin(3 * a + 1.3 + t * 0.0005) + 0.3 * Math.sin(7 * a + 0.4 - t * 0.0009) + 0.2 * Math.sin(13 * a + 2.1 + t * 0.0013));
    const px = x + Math.cos(a) * r * k;
    const py = y + Math.sin(a) * r * k;
    if (i === 0) p.moveTo(px, py);
    else p.lineTo(px, py);
  }
  p.closePath();
  return p;
}

function drawStain(ex, ey, t, v) {
  const pxPerDeg = v.scale * RAD;
  const r = (t / WAVE_MS) * MAX_HOME_DIST * pxPerDeg;
  const far = Math.max(...[[0, 0], [view.w, 0], [0, view.h], [view.w, view.h]].map(([x, y]) => Math.hypot(x - ex, y - ey)));
  if (t < FLASH_MS) {
    ctx.fillStyle = `rgba(255,69,58,${0.32 * (1 - t / FLASH_MS)})`;
    ctx.fillRect(0, 0, view.w, view.h);
  }
  const exitT = (far / (MAX_HOME_DIST * pxPerDeg)) * WAVE_MS;
  const fade = t < exitT ? 1 : Math.max(0, 1 - (t - exitT) / WASH_FADE_MS);
  if (fade <= 0 || r <= 0) return;
  const reach = Math.min(r, far * 1.1);
  const shape = stainPath(ex, ey, reach, t);
  ctx.save();
  ctx.globalAlpha = fade;
  ctx.fillStyle = 'rgba(255,69,58,0.15)';
  ctx.fill(shape);
  ctx.clip(shape);
  if (basemap) {
    ctx.globalAlpha = fade * 0.6;
    const red = cached(redLayer, viewKey(v), (c) => drawRedRoads(c, basemap, proj, view.dpr, zoomOf(v)));
    ctx.drawImage(red, 0, 0, view.w, view.h);
    ctx.globalAlpha = fade;
  }
  if (r < far * 1.1) {
    const band = Math.max(40, reach * 0.18);
    const g = ctx.createRadialGradient(ex, ey, Math.max(0, reach - band), ex, ey, reach * 1.08);
    g.addColorStop(0, 'rgba(255,69,58,0)');
    g.addColorStop(0.75, 'rgba(255,69,58,0.4)');
    g.addColorStop(1, 'rgba(255,110,100,0.6)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, view.w, view.h);
  }
  ctx.restore();
  if (r < far * 1.1) {
    ctx.strokeStyle = 'rgba(255,150,140,0.85)';
    ctx.lineWidth = 2;
    ctx.stroke(shape);
  }
}

function drawEpicenter(x, y, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = COLOR.red;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x - 7, y - 7);
  ctx.lineTo(x + 7, y + 7);
  ctx.moveTo(x + 7, y - 7);
  ctx.lineTo(x - 7, y + 7);
  ctx.stroke();
  ctx.fillStyle = '#ff8a80';
  ctx.font = '600 11px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('EPICENTER', x + 10, y + 4);
  ctx.restore();
}

function drawQuake(now, v, cityA) {
  const [ex, ey] = toScreen(EPICENTER);
  if (now < quake.waveStart) {
    if (facing(EPICENTER, v)) drawPulse(ex, ey, now - quake.at);
    return;
  }
  if (!reducedMotion.matches) drawStain(ex, ey, now - quake.waveStart, v);
  if (cityA > 0) drawEpicenter(ex, ey, cityA);
}

// ---------- Map: markers ----------
function drawCityMarker(v, alpha) {
  if (alpha <= 0 || !facing(CITY_CENTER, v)) return;
  const [x, y] = toScreen(CITY_CENTER);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = COLOR.real;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(x, y, 7, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = COLOR.white;
  ctx.beginPath();
  ctx.arc(x, y, 2.5, 0, Math.PI * 2);
  ctx.fill();
  const label = 'Richardson, TX';
  ctx.font = '600 12px -apple-system, BlinkMacSystemFont, sans-serif';
  const tw = ctx.measureText(label).width;
  ctx.fillStyle = 'rgba(6,9,14,0.8)';
  ctx.beginPath();
  ctx.roundRect(x + 13, y - 11, tw + 14, 22, 6);
  ctx.fill();
  ctx.fillStyle = '#d6dee8';
  ctx.fillText(label, x + 20, y + 4);
  ctx.restore();
}

function dotColor(status) {
  if (status === 'white') return COLOR.white;
  if (status === 'ok') return COLOR.green;
  return COLOR.red;
}

function drawDot(x, y, r0, status, hitAt, now) {
  const motion = !reducedMotion.matches;
  let r = r0;
  if (motion && hitAt !== null && now - hitAt < POP_MS && now >= hitAt) {
    const p = (now - hitAt) / POP_MS;
    r *= 1 + 1.6 * Math.sin(Math.PI * p);
    ctx.strokeStyle = `rgba(255,69,58,${0.8 * (1 - p)})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(x, y, r0 * (1 + 4 * p), 0, Math.PI * 2);
    ctx.stroke();
  }
  if (status === 'escalated') {
    const halo = r0 * (motion ? 2.2 + 0.5 * Math.sin(now / 250) : 2.4);
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

function drawRealBox(now, v, dot, labelled) {
  const [x, y] = toScreen(REAL);
  const status = statusOf(REAL_BOX_ID);
  const motion = !reducedMotion.matches;
  const zoom = zoomOf(v);
  if (zoom > 2) {
    // The block around the box: about 150 m.
    const block = (0.15 / EARTH_KM) * v.scale;
    ctx.strokeStyle = boxLit() ? 'rgba(255,69,58,0.55)' : 'rgba(100,210,255,0.45)';
    ctx.setLineDash([6, 5]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(x, y, block, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
  }
  if (boxLit()) {
    const halo = dot * (motion ? 4 + 1.5 * Math.sin(now / 200) : 4.5);
    ctx.fillStyle = 'rgba(255,69,58,0.3)';
    ctx.beginPath();
    ctx.arc(x, y, halo, 0, Math.PI * 2);
    ctx.fill();
  }
  drawDot(x, y, dot, status === 'escalated' ? 'hit' : status, boxHitAt, now);
  ctx.strokeStyle = COLOR.real;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(x, y, dot * 2.6, 0, Math.PI * 2);
  ctx.stroke();
  if (!labelled) return;
  const label = 'H000 real box';
  ctx.font = '700 11px ui-monospace, SF Mono, Menlo, monospace';
  const tw = ctx.measureText(label).width;
  const lx = x + dot * 3.4;
  ctx.fillStyle = 'rgba(10,13,18,0.85)';
  ctx.fillRect(lx - 4, y - 9, tw + 8, 18);
  ctx.fillStyle = COLOR.real;
  ctx.fillText(label, lx, y + 4);
}

// ---------- Map: overlays ----------
const STAGE_LABEL = { world: 'World', city: 'Richardson', home: 'H000' };

function renderOverlays(now, cityA) {
  const stageEl = $('stage');
  if (stageEl.dataset.stage !== cam.stage) stageEl.dataset.stage = cam.stage;
  setText('stage-now', STAGE_LABEL[cam.stage]);
  setText('attrib', cityA > 0.5 ? '© OpenStreetMap contributors' : 'Land: Natural Earth');

  const el = $('callout');
  const show = cam.stage === 'home' && !flying(cam, now);
  if (el.hidden === show) el.hidden = !show;
  if (!show) return;
  let title = 'H000, the real box';
  let text = `Presence: ${PRESENCE_LABEL[box.presence] ?? box.presence}. Check-in: ${$('b-checkin').textContent}.`;
  if (boxAlarmed) {
    title = box.said_help ? 'Said help' : 'No response after an event';
    text = box.alarm ? 'Alarm raised by the agent. Demo only, no real call.' : 'Escalated to the top.';
  }
  setText('callout-title', title);
  setText('callout-text', text);
  renderHandoff(boxAlarmed ? box.handoff : null);
  el.classList.toggle('alarm', boxAlarmed);
  const [x, y] = toScreen(REAL);
  const left = x + 340 > view.w;
  el.classList.toggle('left', left);
  el.style.transform = `translate(${Math.round(left ? x - 30 : x + 30)}px, ${Math.round(y)}px) translate(${left ? '-100%' : '0'}, -50%)`;
}

const BY_LABEL = { nemotron: 'Written by Nemotron', template: 'Template' };

function renderHandoff(h) {
  $('handoff').hidden = !h;
  $('callout').classList.toggle('has-handoff', !!h);
  if (!h) return;
  for (const [id, by] of [['handoff-by', h.by], ['handoff-why-by', h.why_by]]) {
    setText(id, BY_LABEL[by] ?? String(by));
    $(id).classList.toggle('template', by !== 'nemotron');
  }
  setText('handoff-note', h.note ?? '');
  setText('handoff-contact', h.contact ? `Contact first: ${h.contact.name} (${h.contact.role})` : '');
  const why = (Array.isArray(h.why) ? h.why : []).map((line) => `<li>${esc(line)}</li>`).join('');
  const list = $('handoff-why');
  if (list.dataset.html !== why) list.innerHTML = list.dataset.html = why;
}

function draw(now) {
  const v = viewAt(cam, now, views);
  aim(v);
  const cityA = cityAlpha(v);
  ctx.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
  ctx.drawImage(drawBase(v, cityA), 0, 0, view.w, view.h);
  if (quake) drawQuake(now, v, cityA);
  drawCityMarker(v, 1 - smooth(0, 0.5, cityA));
  if (cityA > 0) {
    const dot = Math.min(7, Math.max(1.5, 3 * Math.sqrt(zoomOf(v))));
    ctx.save();
    // Dots and labels come in after the streets, so a tiny city is not a smudge.
    ctx.globalAlpha = smooth(0.4, 1, cityA);
    HOMES.forEach((h) => {
      if (h.real) return;
      const [x, y] = toScreen(h);
      if (x < -10 || y < -10 || x > view.w + 10 || y > view.h + 10) return;
      drawDot(x, y, dot, statusOf(h.id), sim.get(h.id).hitAt, now);
    });
    drawRealBox(now, v, dot, cam.stage !== 'home');
    ctx.restore();
  }
  renderOverlays(now, cityA);
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

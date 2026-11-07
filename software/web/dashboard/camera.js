// Map camera: which stage the map shows (world globe, city streets, home H000)
// and the eased flight between them. Pure, no DOM.
//
// A view is { lon, lat, scale }: the point at the center of the screen and the
// orthographic projection scale in px. The page computes the three target
// views from the canvas size and passes them in.

export const STAGES = ['world', 'city', 'home'];

// Timings tuned by eye for the demo.
export const SPIN_DEG_PER_MS = 0.006;
const FAR_FLIGHT_MS = 4200;
const NEAR_FLIGHT_MS = 1600;
// Zooming in, the globe turns first and the zoom starts near the end of the
// turn; zooming out runs the same phases in reverse.
const TURN_SHARE = 0.4;
const ZOOM_FROM = 0.3;
const FAR_ZOOM_RATIO = 20;

const NEXT = {
  quake: { world: 'city' },
  alarm: { world: 'home', city: 'home' },
  clear: { home: 'city' },
  reset: { city: 'world', home: 'world' },
  v: { world: 'city', city: 'home', home: 'world' },
};

export function nextStage(stage, event) {
  return NEXT[event]?.[stage] ?? stage;
}

const spinRate = (reduced) => (reduced ? 0 : SPIN_DEG_PER_MS);

export function initialCamera(now, views, { reduced = false } = {}) {
  return { stage: 'world', from: null, at: now, ms: 0, spinLon: views.world.lon, spinAt: now, spin: spinRate(reduced) };
}

export function arrivalAt(cam) {
  return cam.at + cam.ms;
}

export function flying(cam, now) {
  return cam.from !== null && now < arrivalAt(cam);
}

export function cameraEvent(cam, event, now, views, { reduced = false } = {}) {
  const stage = nextStage(cam.stage, event);
  if (stage === cam.stage) return cam;
  const far = stage === 'world' || cam.stage === 'world';
  const ms = reduced ? 0 : far ? FAR_FLIGHT_MS : NEAR_FLIGHT_MS;
  return { stage, from: viewAt(cam, now, views), at: now, ms, spinLon: views.world.lon, spinAt: now + ms, spin: spinRate(reduced) };
}

function target(cam, now, views) {
  if (cam.stage !== 'world') return views[cam.stage];
  return { ...views.world, lon: cam.spinLon + Math.max(0, now - cam.spinAt) * cam.spin };
}

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const phase = (t, a, b) => ease(Math.min(1, Math.max(0, (t - a) / (b - a))));
const wrap180 = (d) => ((((d + 180) % 360) + 360) % 360) - 180;

export function viewAt(cam, now, views) {
  const to = target(cam, now, views);
  if (!flying(cam, now)) return to;
  const { from } = cam;
  const t = (now - cam.at) / cam.ms;
  const ratio = to.scale / from.scale;
  let turn = ease(t);
  let zoom = turn;
  if (ratio > FAR_ZOOM_RATIO) {
    turn = phase(t, 0, TURN_SHARE);
    zoom = phase(t, ZOOM_FROM, 1);
  } else if (ratio < 1 / FAR_ZOOM_RATIO) {
    zoom = phase(t, 0, 1 - ZOOM_FROM);
    turn = phase(t, 1 - TURN_SHARE, 1);
  }
  return {
    lon: from.lon + wrap180(to.lon - from.lon) * turn,
    lat: from.lat + (to.lat - from.lat) * turn,
    scale: Math.exp(Math.log(from.scale) + Math.log(ratio) * zoom),
  };
}

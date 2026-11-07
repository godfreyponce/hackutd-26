// Builds the map data files once, at build time. The page never fetches from
// the internet; it loads only data/world.json and data/richardson.json.
//
//   node data/build.mjs
//
// world.json: Natural Earth 50m land and country borders (public domain) from
// world-atlas 2.0.2, plus US state borders and Texas from us-atlas 3.0.1
// (US Census, public domain).
// richardson.json: OpenStreetMap roads, rail, water and parks through the
// Overpass API. © OpenStreetMap contributors, ODbL.
import { writeFile } from 'node:fs/promises';

const WORLD_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json';
const STATES_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/states-10m.json';
const OVERPASS_URL = 'https://overpass-api.de/api/interpreter';

// The homes bbox is 32.95,-96.80,33.02,-96.70. The city view is about square,
// so the street data runs past it to fill the frame on a tall or wide map.
const OSM_BBOX = [32.93, -96.815, 33.04, -96.685];
const OSM_ORIGIN = [-96.75, 32.985];
const OSM_UNITS = 1e5;
// Douglas-Peucker tolerances, tuned by eye at the zoom each layer is seen at.
// The coarse land is for the whole globe, where 0.15 degree is under 2 px and
// drawing the fine land every frame costs about 16 ms.
const WORLD_TOL_DEG = 0.03;
const GLOBE_TOL_DEG = 0.15;
const OSM_TOL_M = 2.5;

const out = new URL('.', import.meta.url);

async function getJson(url, init) {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  return res.json();
}

// ---------- Douglas-Peucker on [x, y] points ----------
function simplify(pts, tol) {
  if (pts.length < 3) return pts;
  const keep = new Uint8Array(pts.length);
  keep[0] = keep[pts.length - 1] = 1;
  const stack = [[0, pts.length - 1]];
  while (stack.length) {
    const [a, b] = stack.pop();
    const [ax, ay] = pts[a];
    const [bx, by] = pts[b];
    const dx = bx - ax;
    const dy = by - ay;
    const len = Math.hypot(dx, dy);
    let max = -1;
    let at = -1;
    for (let i = a + 1; i < b; i++) {
      const [px, py] = pts[i];
      const d = len === 0 ? Math.hypot(px - ax, py - ay) : Math.abs(dy * px - dx * py + bx * ay - by * ax) / len;
      if (d > max) {
        max = d;
        at = i;
      }
    }
    if (max > tol) {
      keep[at] = 1;
      stack.push([a, at], [at, b]);
    }
  }
  return pts.filter((_, i) => keep[i]);
}

const ringArea = (r) => r.reduce((s, [x, y], i) => {
  const [nx, ny] = r[(i + 1) % r.length];
  return s + x * ny - nx * y;
}, 0) / 2;

const round2 = (p) => [Math.round(p[0] * 100) / 100, Math.round(p[1] * 100) / 100];

function dedupe(pts) {
  return pts.filter((p, i) => i === 0 || p[0] !== pts[i - 1][0] || p[1] !== pts[i - 1][1]);
}

// ---------- TopoJSON (only what these two files use) ----------
function decodeArcs(topo, tol) {
  const { scale, translate } = topo.transform;
  return topo.arcs.map((arc) => {
    let x = 0;
    let y = 0;
    const pts = arc.map(([dx, dy]) => {
      x += dx;
      y += dy;
      return [x * scale[0] + translate[0], y * scale[1] + translate[1]];
    });
    return simplify(pts, tol);
  });
}

function ring(arcs, ids) {
  const pts = [];
  for (const id of ids) {
    const a = id < 0 ? arcs[~id].slice().reverse() : arcs[id];
    pts.push(...(pts.length ? a.slice(1) : a));
  }
  return pts;
}

// Drops rings that simplification collapsed or turned inside out: in d3-geo a
// flipped ring fills the whole globe.
function polygons(arcs, rawArcs, geom) {
  const polys = geom.type === 'Polygon' ? [geom.arcs] : geom.type === 'MultiPolygon' ? geom.arcs : [];
  return polys
    .map((poly) =>
      poly
        .map((ids) => {
          const simple = dedupe(ring(arcs, ids).map(round2));
          const before = ringArea(ring(rawArcs, ids));
          return simple.length >= 4 && Math.sign(ringArea(simple)) === Math.sign(before) ? simple : null;
        })
        .filter(Boolean),
    )
    .filter((poly) => poly.length);
}

function mesh(arcs, object) {
  const users = new Map();
  object.geometries.forEach((g, gi) => {
    const polys = g.type === 'Polygon' ? [g.arcs] : g.type === 'MultiPolygon' ? g.arcs : [];
    for (const ids of polys.flat(2)) {
      const k = ids < 0 ? ~ids : ids;
      if (!users.has(k)) users.set(k, new Set());
      users.get(k).add(gi);
    }
  });
  return [...users].filter(([, s]) => s.size > 1).map(([k]) => dedupe(arcs[k].map(round2))).filter((l) => l.length > 1);
}

async function buildWorld() {
  const world = await getJson(WORLD_URL);
  const states = await getJson(STATES_URL);
  const wArcs = decodeArcs(world, WORLD_TOL_DEG);
  const wCoarse = decodeArcs(world, GLOBE_TOL_DEG);
  const wRaw = decodeArcs(world, 0);
  const sArcs = decodeArcs(states, WORLD_TOL_DEG / 3);
  const sRaw = decodeArcs(states, 0);
  const land = world.objects.land.geometries.flatMap((g) => polygons(wArcs, wRaw, g));
  const texas = states.objects.states.geometries.find((g) => g.properties.name === 'Texas');
  const data = {
    source: 'Natural Earth 50m via world-atlas 2.0.2; US states via us-atlas 3.0.1. Public domain.',
    land: { type: 'MultiPolygon', coordinates: land },
    landCoarse: { type: 'MultiPolygon', coordinates: world.objects.land.geometries.flatMap((g) => polygons(wCoarse, wRaw, g)) },
    borders: { type: 'MultiLineString', coordinates: mesh(wArcs, world.objects.countries) },
    states: { type: 'MultiLineString', coordinates: mesh(sArcs, states.objects.states) },
    texas: { type: 'MultiPolygon', coordinates: polygons(sArcs, sRaw, texas) },
  };
  await writeFile(new URL('world.json', out), JSON.stringify(data));
  const n = (g) => JSON.stringify(g.coordinates).split('],[').length;
  console.log(`world.json: land ${n(data.land)} pts, coarse ${n(data.landCoarse)}, borders ${n(data.borders)}, states ${n(data.states)}, texas ${n(data.texas)}`);
}

// ---------- OpenStreetMap ----------
const ROAD_CLASS = {
  motorway: 'motorway', trunk: 'motorway',
  motorway_link: 'link', trunk_link: 'link', primary_link: 'link', secondary_link: 'link', tertiary_link: 'link',
  primary: 'major', secondary: 'major',
  tertiary: 'tertiary',
  residential: 'minor', unclassified: 'minor', living_street: 'minor',
};
const LABEL_REFS = ['US 75', 'PGBT'];

const M_PER_DEG = 111320;
const KX = Math.cos((OSM_ORIGIN[1] * Math.PI) / 180);
const toMeters = ({ lon, lat }) => [(lon - OSM_ORIGIN[0]) * KX * M_PER_DEG, (lat - OSM_ORIGIN[1]) * M_PER_DEG];
const toUnits = ([x, y]) => [Math.round((x / (KX * M_PER_DEG)) * OSM_UNITS), Math.round((y / M_PER_DEG) * OSM_UNITS)];

// One line as [x0, y0, dx1, dy1, ...] in 1e-5 degree units from OSM_ORIGIN.
function pack(geom) {
  const pts = dedupe(simplify(geom.map(toMeters), OSM_TOL_M).map(toUnits));
  const flat = [];
  pts.forEach(([x, y], i) => flat.push(i ? x - pts[i - 1][0] : x, i ? y - pts[i - 1][1] : y));
  return pts.length > 1 ? flat : null;
}

const key = (p) => `${p.lon},${p.lat}`;

// Multipolygon members come as open ways; join them end to end into rings.
function stitch(ways) {
  const rings = [];
  const open = ways.map((w) => w.slice());
  while (open.length) {
    let cur = open.shift();
    let grew = true;
    while (key(cur[0]) !== key(cur[cur.length - 1]) && grew) {
      grew = false;
      for (let i = 0; i < open.length; i++) {
        const w = open[i];
        const end = key(cur[cur.length - 1]);
        if (key(w[0]) === end) cur = cur.concat(w.slice(1));
        else if (key(w[w.length - 1]) === end) cur = cur.concat(w.slice().reverse().slice(1));
        else continue;
        open.splice(i, 1);
        grew = true;
        break;
      }
    }
    rings.push(cur);
  }
  return rings;
}

function areaRings(e) {
  if (e.type === 'way') return [e.geometry];
  return stitch(e.members.filter((m) => m.type === 'way' && m.geometry).map((m) => m.geometry));
}

function label(ways, ref) {
  const pts = ways.filter((w) => w.tags.ref === ref).flatMap((w) => w.geometry);
  const center = { lon: (OSM_BBOX[1] + OSM_BBOX[3]) / 2, lat: (OSM_BBOX[0] + OSM_BBOX[2]) / 2 };
  const dist = (p) => Math.hypot((p.lon - center.lon) * KX, p.lat - center.lat);
  const near = pts.reduce((best, p) => (dist(p) < dist(best) ? p : best));
  return { text: ref, lon: +near.lon.toFixed(5), lat: +near.lat.toFixed(5) };
}

async function buildRichardson() {
  const bb = OSM_BBOX.join(',');
  const query = `[out:json][timeout:120];(
    way["highway"~"^(${Object.keys(ROAD_CLASS).join('|')})$"](${bb});
    way["railway"="rail"](${bb});
    way["waterway"~"^(river|stream|canal)$"](${bb});
    way["natural"="water"](${bb});relation["natural"="water"](${bb});
    way["leisure"~"^(park|golf_course|nature_reserve)$"](${bb});relation["leisure"~"^(park|golf_course|nature_reserve)$"](${bb});
  );out geom;`;
  const osm = await getJson(OVERPASS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'hackutd-26-dashboard-build' },
    body: new URLSearchParams({ data: query }),
  });
  const roads = { motorway: [], link: [], major: [], tertiary: [], minor: [] };
  const data = {
    attribution: '© OpenStreetMap contributors',
    license: 'ODbL 1.0, https://www.openstreetmap.org/copyright',
    origin: OSM_ORIGIN,
    units: OSM_UNITS,
    bbox: OSM_BBOX,
    roads,
    rail: [],
    waterways: [],
    water: [],
    parks: [],
    labels: [],
  };
  const ways = osm.elements.filter((e) => e.type === 'way' && e.geometry);
  for (const e of osm.elements) {
    const t = e.tags ?? {};
    if (e.type === 'way' && ROAD_CLASS[t.highway]) roads[ROAD_CLASS[t.highway]].push(pack(e.geometry));
    else if (t.railway === 'rail') data.rail.push(pack(e.geometry));
    else if (t.waterway && e.type === 'way') data.waterways.push(pack(e.geometry));
    else if (t.natural === 'water') data.water.push(areaRings(e).map(pack).filter(Boolean));
    else if (t.leisure) data.parks.push(areaRings(e).map(pack).filter(Boolean));
  }
  for (const k of Object.keys(roads)) roads[k] = roads[k].filter(Boolean);
  for (const k of ['rail', 'waterways']) data[k] = data[k].filter(Boolean);
  for (const k of ['water', 'parks']) data[k] = data[k].filter((p) => p.length);
  data.labels = LABEL_REFS.map((ref) => label(ways, ref));
  const json = JSON.stringify(data);
  await writeFile(new URL('richardson.json', out), json);
  console.log(`richardson.json: ${(json.length / 1024).toFixed(0)} KB, ${osm.elements.length} OSM elements`);
}

await buildWorld();
await buildRichardson();

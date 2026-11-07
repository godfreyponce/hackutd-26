// Base map: the dark globe (Natural Earth) and the Richardson street map
// (OpenStreetMap). Loads only the vendored files in data/. Needs the vendored
// d3-geo, loaded as a classic script before the page module.
const { geoPath, geoGraticule10, geoCentroid, geoDistance } = globalThis.d3;

export const PALETTE = {
  space: '#04060a',
  ocean: '#0a111c',
  oceanEdge: '#05080e',
  land: '#141b25',
  coast: '#2a3647',
  border: 'rgba(120, 140, 165, 0.28)',
  state: 'rgba(120, 140, 165, 0.14)',
  texas: 'rgba(160, 185, 215, 0.5)',
  graticule: 'rgba(110, 140, 180, 0.07)',
  glow: '100, 160, 255',
  park: '#122119',
  water: '#0c1c2c',
  waterway: '#14314a',
  rail: '#2e3846',
  road: { minor: '#1f2834', tertiary: '#27313f', major: '#323f50', link: '#2d3949', motorway: '#46576d' },
};
// Road widths in px at the city view; they grow a little when zoomed in.
const ROAD_PX = { minor: 0.7, tertiary: 1.1, major: 1.6, link: 1, motorway: 2.6 };
const RED_ROAD_PX = { minor: 1.1, tertiary: 1.5, major: 2.2, link: 1.4, motorway: 3.2 };
const ROAD_ORDER = ['minor', 'tertiary', 'link', 'major', 'motorway'];
const RAD = Math.PI / 180;

async function getJson(name) {
  const res = await fetch(new URL(`data/${name}`, import.meta.url));
  if (!res.ok) throw new Error(`data/${name}: ${res.status}`);
  return res.json();
}

// The street data is stored in 1e-5 degree steps from an origin. Paths are
// built once in a flat local frame (x scaled by cos(lat) so 1 unit is the same
// length both ways) and placed on screen with one affine transform per frame.
// At city zoom the orthographic projection is flat to well under a pixel.
function cityPaths(city) {
  const kx = Math.cos(city.origin[1] * RAD);
  const addLine = (path, flat, close) => {
    let x = 0;
    let y = 0;
    for (let i = 0; i < flat.length; i += 2) {
      x += flat[i];
      y += flat[i + 1];
      if (i === 0) path.moveTo(x * kx, -y);
      else path.lineTo(x * kx, -y);
    }
    if (close) path.closePath();
  };
  const lines = (list) => {
    const p = new Path2D();
    for (const l of list) addLine(p, l, false);
    return p;
  };
  const areas = (list) => {
    const p = new Path2D();
    for (const poly of list) for (const ring of poly) addLine(p, ring, true);
    return p;
  };
  return {
    roads: Object.fromEntries(Object.entries(city.roads).map(([k, v]) => [k, lines(v)])),
    rail: lines(city.rail),
    waterways: lines(city.waterways),
    water: areas(city.water),
    parks: areas(city.parks),
  };
}

// Each fine land polygon with a bounding circle (radians), so a zoomed-in
// frame only sends the polygons near the view through d3.
function landParts(land) {
  return land.coordinates.map((poly) => {
    const center = geoCentroid({ type: 'Polygon', coordinates: poly });
    const radius = Math.max(...poly[0].map((p) => geoDistance(center, p)));
    return { poly, center, radius };
  });
}

export async function loadBasemap() {
  const [world, city] = await Promise.all([getJson('world.json'), getJson('richardson.json')]);
  return { world, city, landParts: landParts(world.land), paths: cityPaths(city), graticule: geoGraticule10() };
}

// Whole globe: the coarse land. Zoomed in: only the fine polygons in view.
function landInView(map, proj, w, h, globeZoom) {
  if (globeZoom < 3) return map.world.landCoarse;
  const [lon, lat] = proj.rotate();
  const center = [-lon, -lat];
  const reach = Math.asin(Math.min(1, Math.hypot(w, h) / 2 / proj.scale()));
  const coordinates = map.landParts.filter((p) => geoDistance(p.center, center) - p.radius < reach).map((p) => p.poly);
  return { type: 'MultiPolygon', coordinates };
}

// Screen px per stored unit, and where the origin lands, for this projection.
export function cityFrame(map, proj) {
  const [ax, ay] = proj(map.city.origin);
  return { ax, ay, s: (proj.scale() * RAD) / map.city.units };
}

// globeZoom: projection scale over the whole-globe view scale.
export function drawGlobe(c, map, proj, w, h, globeZoom) {
  const [cx, cy] = proj.translate();
  const r = proj.scale();
  const path = geoPath(proj, c);

  const glow = c.createRadialGradient(cx, cy, r * 0.98, cx, cy, r * 1.14);
  glow.addColorStop(0, `rgba(${PALETTE.glow}, 0.22)`);
  glow.addColorStop(1, `rgba(${PALETTE.glow}, 0)`);
  c.fillStyle = glow;
  c.fillRect(0, 0, w, h);

  const ocean = c.createRadialGradient(cx - r * 0.35, cy - r * 0.4, r * 0.1, cx, cy, r);
  ocean.addColorStop(0, PALETTE.ocean);
  ocean.addColorStop(1, PALETTE.oceanEdge);
  c.beginPath();
  path({ type: 'Sphere' });
  c.fillStyle = ocean;
  c.fill();

  // The graticule only reads on the whole globe; past that it costs time.
  if (globeZoom < 4) {
    c.beginPath();
    path(map.graticule);
    c.strokeStyle = PALETTE.graticule;
    c.lineWidth = 1;
    c.stroke();
  }

  c.beginPath();
  path(landInView(map, proj, w, h, globeZoom));
  c.fillStyle = PALETTE.land;
  c.fill();
  c.strokeStyle = PALETTE.coast;
  c.lineWidth = 0.8;
  c.stroke();

  c.beginPath();
  path(map.world.states);
  c.strokeStyle = PALETTE.state;
  c.lineWidth = 0.6;
  c.stroke();

  c.beginPath();
  path(map.world.borders);
  c.strokeStyle = PALETTE.border;
  c.lineWidth = 0.8;
  c.stroke();

  c.beginPath();
  path(map.world.texas);
  c.strokeStyle = PALETTE.texas;
  c.lineWidth = 1.2;
  c.stroke();

  // Light from the upper left, shade toward the limb: reads as a sphere.
  const shade = c.createRadialGradient(cx - r * 0.45, cy - r * 0.5, 0, cx, cy, r);
  shade.addColorStop(0, 'rgba(255, 255, 255, 0.05)');
  shade.addColorStop(0.6, 'rgba(0, 0, 0, 0)');
  shade.addColorStop(1, 'rgba(0, 0, 0, 0.45)');
  c.beginPath();
  path({ type: 'Sphere' });
  c.fillStyle = shade;
  c.fill();
}

function placeCity(c, map, proj, dpr) {
  const { ax, ay, s } = cityFrame(map, proj);
  c.setTransform(dpr * s, 0, 0, dpr * s, dpr * ax, dpr * ay);
  return s;
}

// zoomIn: projection scale over the city view scale (1 at the city view).
export function drawCity(c, map, proj, dpr, alpha, zoomIn) {
  const p = map.paths;
  c.save();
  c.globalAlpha = alpha;
  const s = placeCity(c, map, proj, dpr);
  const grow = Math.min(2.2, Math.max(0.6, Math.sqrt(zoomIn)));
  const px = (n) => (n * grow) / s;
  c.lineCap = 'round';
  c.lineJoin = 'round';
  c.fillStyle = PALETTE.park;
  c.fill(p.parks);
  c.fillStyle = PALETTE.water;
  c.fill(p.water);
  c.strokeStyle = PALETTE.waterway;
  c.lineWidth = px(1.2);
  c.stroke(p.waterways);
  c.strokeStyle = PALETTE.rail;
  c.lineWidth = px(1);
  c.setLineDash([px(4), px(3)]);
  c.stroke(p.rail);
  c.setLineDash([]);
  for (const k of ROAD_ORDER) {
    c.strokeStyle = PALETTE.road[k];
    c.lineWidth = px(ROAD_PX[k]);
    c.stroke(p.roads[k]);
  }
  c.restore();
}

export function drawRedRoads(c, map, proj, dpr, zoomIn) {
  c.save();
  const s = placeCity(c, map, proj, dpr);
  const grow = Math.min(2.2, Math.max(0.6, Math.sqrt(zoomIn)));
  c.lineCap = 'round';
  c.lineJoin = 'round';
  c.strokeStyle = '#ff5a4f';
  for (const k of ROAD_ORDER) {
    c.lineWidth = (RED_ROAD_PX[k] * grow) / s;
    c.stroke(map.paths.roads[k]);
  }
  c.restore();
}

export function drawRoadLabels(c, map, proj, alpha) {
  c.save();
  c.globalAlpha = alpha;
  c.font = '700 10px ui-monospace, "SF Mono", Menlo, monospace';
  c.textAlign = 'center';
  c.textBaseline = 'middle';
  for (const l of map.city.labels) {
    const [x, y] = proj([l.lon, l.lat]);
    const w = c.measureText(l.text).width + 10;
    c.fillStyle = '#1d2733';
    c.strokeStyle = PALETTE.road.motorway;
    c.lineWidth = 1;
    c.beginPath();
    c.roundRect(x - w / 2, y - 8, w, 16, 4);
    c.fill();
    c.stroke();
    c.fillStyle = '#b8c4d2';
    c.fillText(l.text, x, y + 0.5);
  }
  c.restore();
}

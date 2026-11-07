// 500 simulated homes around Richardson, TX. Seeded: same homes every run.
// Shares follow docs/lifeline/HackUTD-Lifeline-Agent.md section 5 where it
// gives them; the rest are demo weights, not real prevalence.

export const REAL_BOX_ID = 'H000';
export const HOME_COUNT = 500;
export const BOUNDS = { latMin: 32.95, latMax: 33.02, lonMin: -96.8, lonMax: -96.7 };
export const UTD = { lat: 32.9857, lon: -96.7502 };

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const DEVICES = [
  ['o2', 0.06, [60, 240]],
  ['cpap', 0.15, [95, 300]],
  ['wheelchair', 0.04, [240, 1440]],
  // No battery: the clock is how long a closed fridge stays cold (about 4 h).
  ['insulin', 0.08, [180, 300]],
  ['dialysis', 0.01, [30, 60]],
  ['none', 0.66, null],
];
const PRESENCE = [['moving', 0.62], ['still', 0.08], ['none', 0.3]];
// late_ok: no answer on the first try, ok on the retry.
const OUTCOMES = [['ok', 0.78], ['late_ok', 0.07], ['no_answer', 0.1], ['help', 0.05]];
const VULNERABLE_SHARE = 0.2;
const STALE_SHARE = 0.05;
const SKIPPED_SHARE = 0.03;
const COLD_HOME_SHARE = 0.15;
const CLUSTERS = 14;
const CLUSTERED_SHARE = 0.7;
const CLUSTER_SD_DEG = 0.006;

function pick(rand, table) {
  let r = rand();
  for (const row of table) {
    r -= row[1];
    if (r < 0) return row;
  }
  return table[table.length - 1];
}

const between = (rand, lo, hi) => lo + rand() * (hi - lo);
const inside = (lat, lon) => lat >= BOUNDS.latMin && lat <= BOUNDS.latMax && lon >= BOUNDS.lonMin && lon <= BOUNDS.lonMax;

function gaussian(rand) {
  const u = 1 - rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}

function realBox() {
  return {
    id: REAL_BOX_ID,
    real: true,
    lat: UTD.lat,
    lon: UTD.lon,
    device: 'none',
    battery_min: null,
    vulnerable: false,
    indoor_f: 70,
    presence: 'moving',
    stale: false,
    outcome: null,
    skipped: false,
  };
}

export function generateHomes(seed = 16) {
  const rand = mulberry32(seed);
  const centers = Array.from({ length: CLUSTERS }, () => ({
    lat: between(rand, BOUNDS.latMin, BOUNDS.latMax),
    lon: between(rand, BOUNDS.lonMin, BOUNDS.lonMax),
  }));
  const homes = [realBox()];
  for (let i = 1; i < HOME_COUNT; i++) {
    let lat;
    let lon;
    if (rand() < CLUSTERED_SHARE) {
      const c = centers[Math.floor(rand() * CLUSTERS)];
      do {
        lat = c.lat + gaussian(rand) * CLUSTER_SD_DEG;
        lon = c.lon + gaussian(rand) * CLUSTER_SD_DEG;
      } while (!inside(lat, lon));
    } else {
      lat = between(rand, BOUNDS.latMin, BOUNDS.latMax);
      lon = between(rand, BOUNDS.lonMin, BOUNDS.lonMax);
    }
    const [device, , range] = pick(rand, DEVICES);
    homes.push({
      id: `H${String(i).padStart(3, '0')}`,
      real: false,
      lat,
      lon,
      device,
      battery_min: range ? Math.round(between(rand, range[0], range[1])) : null,
      vulnerable: rand() < VULNERABLE_SHARE,
      indoor_f: Math.round(rand() < COLD_HOME_SHARE ? between(rand, 45, 62) : between(rand, 63, 74)),
      presence: pick(rand, PRESENCE)[0],
      stale: rand() < STALE_SHARE,
      outcome: pick(rand, OUTCOMES)[0],
      skipped: rand() < SKIPPED_SHARE,
    });
  }
  return homes;
}

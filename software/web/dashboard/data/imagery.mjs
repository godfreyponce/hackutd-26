// Downloads the aerial imagery tiles listed in imagery.js into imagery/, once,
// at build time. The page never fetches tiles from the internet.
//
//   node data/imagery.mjs
//
// Source: USGS The National Map, USGSImageryOnly tile service. Public domain
// (US Government work).
import { writeFile, mkdir } from 'node:fs/promises';
import { TILE_SETS, setTiles } from '../imagery.js';

const URL_OF = (t) => `https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/${t.z}/${t.y}/${t.x}`;
const root = new URL('../', import.meta.url);

await mkdir(new URL('imagery/', root), { recursive: true });
for (const set of TILE_SETS) {
  for (const t of setTiles(set)) {
    const res = await fetch(URL_OF(t));
    if (!res.ok) throw new Error(`${URL_OF(t)}: ${res.status}`);
    await writeFile(new URL(t.file, root), Buffer.from(await res.arrayBuffer()));
    console.log(t.file);
  }
}

# Data licence: ODbL 1.0

The **dataset** produced by this project is licensed under the Open Database License (ODbL) v1.0: https://opendatacommons.org/licenses/odbl/1-0/

It covers:
- the CityJSON release (`dist/**/*.city.json*`, `build/11-merge/`),
- the 3D Tiles and GLB tiles built from it (`dist/tiles/`),
- `search.json`, `labels.json`, and every table under `data/osm-derived/`,
- `data/registry/*.csv` and `*.json`,
- the per-building YAML under `buildings/` (they are a database of building facts).

Why ODbL: the dataset is a derivative database of OpenStreetMap (© OpenStreetMap contributors, ODbL). The lidar it also uses (USGS 3DEP) is public domain; the combination inherits ODbL.

Required attribution when you use it:

> Contains data from utd-3d (ODbL), © OpenStreetMap contributors (https://www.openstreetmap.org/copyright), and USGS 3DEP lidar (public domain).

Not covered by this file: the code (MIT, `LICENSE`), the owner's photographs and hand-made assets (CC BY 4.0, `LICENSE-ASSETS.md`), CC0 materials from ambientCG / Poly Haven, and third-party models listed in `NOTICE.md`.

City of Richardson GIS data is **not** part of this dataset unless `data/richardson/PERMISSION.md` records the city's written permission and its terms.

# NOTICE — attributions

This project combines the following data, tools and assets. Keep this list complete: every input added to the pipeline or `assets/` gets a line here.

## Data
- **USGS 3D Elevation Program (3DEP)** lidar, project `TX_Pecos_Dallas_2018_D19`, work unit `TX_Pecos_Dallas_B3_2018` (flown 2019). U.S. Government work, public domain. https://www.usgs.gov/3d-elevation-program
- **USGS 3DEP 1 m DEM** and **NHD** flowlines. Public domain.
- **OpenStreetMap** © OpenStreetMap contributors, Open Database License 1.0. https://www.openstreetmap.org/copyright
- **NAIP** orthoimagery (USDA Farm Service Agency), public domain; **StratMap / TxGIO** 2015 DFW orthoimagery, CC0 1.0. https://data.geographic.texas.gov/
- **UT Dallas / UT System public documents** (campus master plan 2018, parking map 2026, "Accessing UT Dallas Skybridges" 2015, Board of Regents agenda books, Capital Improvement Programs, UTD news) — used as sources of facts only (names, codes, storeys, dates). © The University of Texas at Dallas / UT System. "UT Dallas" and "UTD" are used descriptively; no marks or logos are reproduced.
- **City of Richardson GIS** — not used in the release unless `data/richardson/PERMISSION.md` exists; see `LICENSE-DATA.md`.

## Tools (run as separate programs; their licences do not extend to our outputs)
- roofer (3DBAG / TU Delft), GPL-3.0 — https://github.com/3DBAG/roofer
- PDAL, BSD-3 — https://pdal.io ; startinpy, MIT ; triangle (Shewchuk), via the `triangle` package ; shapely, BSD ; trimesh, MIT ; laspy, BSD ; pyproj, MIT ; cjio, MIT ; val3dity, GPL-3.0 (validation only)
- glTF-Transform, MIT ; meshoptimizer, MIT ; three.js, MIT ; React Three Fiber / drei, MIT ; 3DTilesRendererJS (NASA-AMMOS), Apache-2.0
- OSM2World (MIT) was consulted for its tag-interpretation rules; none of its output ships.

## Assets
- Materials: own, or ambientCG (CC0) / Poly Haven (CC0) — per file in `assets/SOURCES.md`.
- Tree and furniture archetypes: per file in `assets/SOURCES.md` (own, Kenney CC0, KayKit CC0, Quaternius CC0).
- Photographs and hand-made assets (including the palette): Rafael Amador, CC BY 4.0 (`LICENSE-ASSETS.md`).

## Code
- utd-3d code: MIT, Copyright (c) 2026 Rafael Amador (`LICENSE`).

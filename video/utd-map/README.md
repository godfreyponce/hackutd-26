# UTD 3D map for the demo video

Rafael's 3D model of the UT Dallas campus (from his utd-3d project, the "UTD Campus (test)" tab in ARIS 2.0), packed here so you and your agents can use it in the LAND video. Everything runs offline from this folder.

**Ready to use now:** `renders/utd-flythrough.mp4`. 1920x1080, 60 fps, 14.5 s. It opens on **TAGER Tower** (the radio tower on campus, the "signal tower"), flies across campus and settles on **Canyon Creek Heights South** (the student apartments). It has no labels and no audio, so you can add titles and sound in the editor.

## What is in here

| Path | What it is |
|---|---|
| `renders/utd-flythrough.mp4` | The finished shot. Drop it into the editor. |
| `viewer/` | The built 3D viewer and its data: 3D Tiles, trees, labels and search. About 18 MB, no internet needed. |
| `shot.json` | The camera path: keyframes for time, camera position and look-at point. Edit this to change the shot. |
| `record.mjs` | Renders `shot.json` to an MP4, one frame at a time. |
| `package.json` | Only dependency: Playwright, which provides the headless Chromium. |

## Run it

Needs Node 18+ and ffmpeg (with ffprobe) on PATH.

```
cd video/utd-map
npm install
npx playwright install chromium   # once
npm run serve      # fly around by hand: http://127.0.0.1:5190/
npm run preview    # fast check of shot.json: out/preview.mp4 (960x540, every 6th frame), ~15 s
npm run record     # full render: out/utd-flythrough.mp4 (1080p60), ~2 min on a laptop GPU
```

In `serve` mode you can drag to orbit, scroll to zoom and search for buildings (try "TAGER" or "CCHS").

## Why the video is smooth (keep it this way)

It is **not a screen recording**, so it cannot drop or skip frames, whatever the machine. For every frame, `record.mjs`:
1. places the camera exactly (`window.__utd3d.pose(position, target)`),
2. waits until every tile and tree for that view has loaded, with nothing in flight twice in a row,
3. grabs the canvas (`window.__utd3d.frame()`), then moves to the next frame.

What else it does:
- **`?record=1`** turns off the viewer's live render loop. Otherwise its auto-resolution would drop the pixel ratio when frames run slow, and the picture would change size mid-video. The script stops with an error if any frame's size differs.
- **Warm-up**: before frame 1 it visits every keyframe, so the whole route is already cached.
- **Path**: a non-uniform Catmull-Rom spline through the keys. The speed is continuous even with uneven key spacing, and a smootherstep ease makes the start and end come in and out at zero speed. Then it holds still for `hold` seconds.
- **Checks**: the run fails on any viewer or tile error. At the end ffprobe prints the frame count. Rafael's run: 871 frames at 1920x1080, 60 fps. An ffmpeg scene-change scan found no jump between any two frames.

If you want it slower or faster, change the key times in `shot.json` (and `fps` if needed). Don't screen-capture the live viewer for the final cut, because that is where stutter comes from.

## Coordinates (for editing `shot.json`)

Metres, in the viewer frame: **x = east, y = up, z = south** (north is −z). The origin is the campus centre.

| Place | Point | Notes |
|---|---|---|
| TAGER Tower | base (−7.4, 7.5, −167), top y = 94.7 | Lattice radio tower, about 87 m tall |
| Canyon Creek Heights South | centre (−448.5, 3, 832.5), roofs y ≈ 10.8 | Student apartments, about 1.1 km SSW of the tower |
| Canyon Creek Heights North | centre (−447.6, 3, 715) | Next door, to the north |

Any building or place: look it up in `viewer/search.json` (`bbox` = minX, minY, minZ, maxX, maxY, maxZ) or `viewer/labels.json`. To get the pose you are looking at in `serve` mode, run this in the browser console: `__utd3d.camera.position`.

A good path: keep the camera at 40 m or higher near buildings, keep look-at points near the ground or the tower, and space keys 1.5 s or more apart.

Labels: set `"labels": true` in `shot.json` to burn the viewer's building labels into the frames. They are off by default so titles can be added in the editor.

## For agents

- To change the shot, only edit `shot.json`. Run `npm run preview`, look at a few frames in `out/frames/`, then `npm run record`.
- Don't edit `viewer/`. It is a build output of Rafael's utd-3d repo. The `pose` / `frame` / `?record=1` hooks were added there for this video. If the viewer needs a change, ask Rafael.
- `window.__utd3d` API (in the page): `pose(pos, look)`, `frame(labels?, mime?)`, `pump(n)`, `ready()`, `find(q)`, `goto("F0".."F6")` (fixed framings), `camera`.

## Credits (required when it is shown)

> Contains data from utd-3d (ODbL), © OpenStreetMap contributors (openstreetmap.org/copyright), and USGS 3DEP lidar (public domain).

Licences: `viewer/LICENSE` (code, MIT), `viewer/LICENSE-DATA.md` (ODbL), `viewer/LICENSE-ASSETS.md`, `viewer/NOTICE.md`. Put the credit line in the video's end card or the Devpost description.

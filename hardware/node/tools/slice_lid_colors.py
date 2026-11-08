"""Slice out/final_lid.3mf with 4 filaments (black PLA-CF, white, green, red) in the Bambu Studio CLI, save a Bambu project
(out/final_lid_bambu.3mf, colours included) and report time, grams per filament and filament changes in the G-code."""
import json, re, shutil, subprocess, sys
from pathlib import Path
import slice_time as S

ROOT = Path(__file__).resolve().parent.parent
BASIC = "Bambu PLA Basic @BBL P1S 0.4 nozzle"     # P1S profile; PLA-CF has no P1S variant (the X1C one lists the P1S)
FILS = [("Bambu PLA-CF @BBL X1C", "#151517"), (BASIC, "#F2F2EE"), (BASIC, "#76B900"), (BASIC, "#EC0C21")]
TOWER = {"wipe_tower_x": ["10"], "wipe_tower_y": ["175"]}   # prime tower clear of the lid (x 53..203) and off the plate edge

shutil.rmtree(S.TMP, ignore_errors=True)
S.TMP.mkdir()
try:
    settings = S.write_profile("machine", S.MACHINE) + ";" + S.write_profile("process", S.PROCESS["0.20"], {**S.OVERRIDES, **TOWER})
    fpaths = []
    for i, (name, col) in enumerate(FILS):
        p = Path(S.write_profile("filament", name, {"filament_colour": [col]}))   # PLA Basic for the logo colours
        fpaths.append(str(p.rename(S.TMP / f"filament{i + 1}.json")))
    out = S.TMP / "lid"
    out.mkdir()
    proj = ROOT / "out" / "final_lid_bambu.3mf"
    cmd = [S.EXE, "--slice", "0", "--load-settings", settings, "--load-filaments", ";".join(fpaths),
           "--export-3mf", proj.name, "--outputdir", str(out), str(ROOT / "out" / "final_lid.3mf")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    g = out / "plate_1.gcode"
    if r.returncode or not g.exists():
        sys.exit(f"slice failed {r.returncode}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    shutil.copy(out / proj.name, proj)                                     # the CLI only writes the project into outputdir
    txt = g.read_text(encoding="utf-8", errors="replace")
    head = txt[:6000]
    secs = json.loads((out / "result.json").read_text())["sliced_plates"][0]["total_predication"]
    used = re.search(r"; filament used \[g\] = ([^\n]+)", txt)
    changes = re.findall(r"^M620 S(\d+)", txt, re.M)
    print("time", S.hms(secs), "| grams per filament:", used.group(1) if used else "?")
    print("filament changes (M620):", len(changes), "| sequence start:", changes[:12])
    print("project saved:", proj.exists(), proj)
finally:
    shutil.rmtree(S.TMP, ignore_errors=True)

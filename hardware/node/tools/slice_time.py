"""Print-time estimator: slices STLs with the Bambu Studio CLI and reports time + filament.

Fixed setup: Bambu Lab P1S, 0.4 mm nozzle, Bambu PLA-CF, 3 walls, 15% gyroid,
no supports, Textured PEI plate. Each file is sliced alone on its own plate.

Usage:
    python slice_time.py part.stl[:up|:flip] [more.stl[:flip] ...] [--layer 0.28]

    up   = as modelled (default)
    flip = rotated 180 deg about X before slicing
    --layer 0.20 (default) or 0.28: picks the matching @BBL X1C process profile
            (0.20mm Standard / 0.28mm Extra Draft; both list the P1S as compatible).

Example:
    python slice_time.py ../out/plate.stl ../out/back.stl ../out/front.stl ../out/cover.stl:flip

System profiles use "inherits"/"include" chains the CLI does not resolve on its
own, so they are flattened into _slice_tmp/ first. Temp files are deleted after.
Any slicing failure exits non-zero with the CLI's output and result.json.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

EXE = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
PROFILES = Path(r"C:\Program Files\Bambu Studio\resources\profiles\BBL")
TMP = Path(__file__).resolve().parent / "_slice_tmp"
MACHINE = "Bambu Lab P1S 0.4 nozzle"
FILAMENT = "Bambu PLA-CF @BBL X1C"
PROCESS = {"0.20": "0.20mm Standard @BBL X1C", "0.28": "0.28mm Extra Draft @BBL X1C"}
OVERRIDES = {"wall_loops": "3", "sparse_infill_density": "15%", "sparse_infill_pattern": "gyroid",
             "enable_support": "0", "curr_bed_type": "Textured PEI Plate"}


def flatten(kind, name):
    """Resolve a system profile's inherits/include chain into one dict."""
    own = json.loads((PROFILES / kind / f"{name}.json").read_text(encoding="utf-8"))
    out = flatten(kind, own["inherits"]) if "inherits" in own else {}
    for inc in own.get("include", []):
        out.update(flatten(kind, inc))
    out.update(own)
    out.pop("inherits", None)
    out.pop("include", None)
    return out


def write_profile(kind, name, extra=None):
    cfg = flatten(kind, name)
    cfg.update(extra or {})
    path = TMP / f"{kind}.json"
    path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    return str(path)


def hms(seconds):
    return f"{int(seconds // 3600)}:{int(seconds % 3600 // 60):02d}"


def slice_one(stl, orient, settings, filament):
    out = TMP / Path(stl).stem
    out.mkdir()
    cmd = [EXE, "--slice", "0", "--arrange", "1", "--load-settings", settings,
           "--load-filaments", filament, "--outputdir", str(out)]
    if orient == "flip":
        cmd += ["--rotate-x", "180", "--ensure-on-bed"]  # without ensure-on-bed the flipped part floats and slicing fails
    proc = subprocess.run(cmd + [str(stl)], capture_output=True, text=True)
    result = out / "result.json"
    gcode = out / "plate_1.gcode"
    if proc.returncode or not gcode.exists():
        sys.exit(f"Slicing {stl} failed (exit {proc.returncode}).\n"
                 f"cmd: {subprocess.list2cmdline(cmd + [str(stl)])}\n"
                 f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}\n"
                 f"result.json:\n{result.read_text() if result.exists() else '(none)'}")
    head = gcode.read_text(encoding="utf-8", errors="replace")[:4000]
    secs = json.loads(result.read_text())["sliced_plates"][0]["total_predication"]
    grams = float(re.search(r"total filament weight \[g\] : ([\d.]+)", head).group(1))
    return secs, grams


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="+", help="file.stl[:up|:flip]")
    ap.add_argument("--layer", default="0.20", choices=PROCESS)
    args = ap.parse_args()

    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir()
    try:
        settings = write_profile("machine", MACHINE) + ";" + write_profile("process", PROCESS[args.layer], OVERRIDES)
        filament = write_profile("filament", FILAMENT)
        total_s = total_g = 0
        print(f"P1S 0.4 | {FILAMENT} | {PROCESS[args.layer]} | 3 walls, 15% gyroid, no supports, Textured PEI")
        print(f"{'part':<16}{'orient':<8}{'time':>8}{'grams':>9}")
        for spec in args.parts:
            stl, _, orient = spec.rpartition(":") if spec.endswith((":up", ":flip")) else (spec, "", "up")   # Windows "C:\..." safe
            orient = orient or "up"
            if orient not in ("up", "flip"):
                sys.exit(f"bad orientation '{orient}' in {spec} (use up|flip)")
            s, g = slice_one(Path(stl).resolve(), orient, settings, filament)
            total_s += s
            total_g += g
            print(f"{Path(stl).name:<16}{orient:<8}{hms(s):>8}{g:>9.1f}")
        print(f"{'TOTAL':<24}{hms(total_s):>8}{total_g:>9.1f}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

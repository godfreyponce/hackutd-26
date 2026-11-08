"""Design system for the Lifeline node: one verified core (node_core.py), many looks.

A DESIGN may only change two things:
  1. the FACEPLATE: a decorative part sitting on the cover face (z = Z_TOP) up to Z_MAX, printed FACE-UP
     (so raised logos can change colour at a layer). The 4 cover screws (M3 x 12-16) clamp it through the pillars.
  2. SIDE_CUT: carving into the outer 2 mm DECOR band of the back + front deck walls (structure keeps 3 mm).
Everything functional (camera, light ring, fan, speaker, mics, radar, OLED, screws) is enforced by keep_open() and
validate(); a design that breaks a rule fails loudly.

Writing a design (designs/<group>.py):
    from node_design import *
    def my_face():
        f = fp_plate()                         # 3 mm octagon base on the cover face (or your own outline)
        f += ...                               # raised geometry, z >= Z_TOP; keep overhangs <= 45 deg (face-up print)
        f += logo("nvidia.svg", 60, at=(0, -60), z=f_top, h=0.8)   # raised logo (colour swap at that layer)
        return f
    DESIGNS = [Design("my-id", "MY NAME", "cyberpunk", "one line", faceplate=my_face, side_cut=None,
                      colors=dict(base="#111111", accent="#76b900"), swaps=[(Z_TOP + 4.0, "accent")])]
finalize() subtracts the keep-open zones and screw holes from your faceplate, so you never cut them yourself.
Run: python node_design.py   (validates every design in designs/*.py)"""
import importlib, math, pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from build123d import (Box, Cylinder, Cone, Pos, Rot, Part, Polygon, Compound, extrude, fillet, chamfer, Axis,
                       import_svg, loft, export_stl)
from node_core import *          # noqa: F401,F403  (geometry constants + helpers for designs)
import node_core as C

HERE = Path(__file__).parent
# Designs are authored on a FIXED face plane (z 75) so core changes never break them; assembly shifts them by FACE_DZ.
FACE_Z = 75.0
FACE_DZ = C.Z_TOP - FACE_Z
Z_TOP = FACE_Z                         # what designs see (overrides the core's value from the star import)
Z_MAX = C.Z_MAX - FACE_DZ              # face-frame ceiling for the 4 in envelope
FP_BASE_T = 3.0                  # faceplate base thickness around the screws (screw: M3 x 12 through 3 + 3 cover + 6 insert)
HALF = C.ENVELOPE / 2 - 0.2      # stay inside 152.4 x 152.4


@dataclass
class Design:
    id: str
    name: str
    group: str                    # nvidia | statefarm | sponsors | cyberpunk | premium
    blurb: str
    faceplate: Callable
    side_cut: Optional[Callable] = None
    colors: dict = field(default_factory=lambda: dict(base="#151515"))
    swaps: list = field(default_factory=list)      # [(z, colour key)] filament changes for the faceplate
    notes: str = ""


# ---------------- helpers designers use ----------------
def octagon_xy(af, z0, z1, r=3.0):
    """Octagon prism with flats on the axes (af = across flats), vertical edges filleted r."""
    return C.octagon(0, z0, z1, af=af) if r == C.EDGE_R else _poly_prism(8, af, z0, z1, r, 22.5)


def _poly_prism(n, af, z0, z1, r=0.0, a0=None):
    a = af / 2
    rc = a / math.cos(math.pi / n)
    a0 = 180.0 / n if a0 is None else a0
    pts = [(rc * math.cos(math.radians(a0 + 360 * k / n)), rc * math.sin(math.radians(a0 + 360 * k / n))) for k in range(n)]
    s = Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), z1 - z0)
    return fillet(s.edges().filter_by(Axis.Z), r) if r > 0 else s


def poly(n, af, z0, z1, r=0.0, a0=None):
    """Regular n-gon prism (across flats af); a0 = angle of the first vertex (deg). Keep it inside +-HALF."""
    return _poly_prism(n, af, z0, z1, r, a0)


def frustum_poly(n, af0, af1, z0, z1, a0=None):
    """n-gon loft from across-flats af0 at z0 to af1 at z1 (faceted bevels/visors). af1 < af0 leans in (no overhang face-up)."""
    def f(af, z):
        a = af / 2
        rc = a / math.cos(math.pi / n)
        aa = 180.0 / n if a0 is None else a0
        return Pos(0, 0, z) * Polygon(*[(rc * math.cos(math.radians(aa + 360 * k / n)), rc * math.sin(math.radians(aa + 360 * k / n))) for k in range(n)], align=None)
    return loft([f(af0, z0), f(af1, z1)])


def prism(pts, z0, z1):
    return Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), z1 - z0)


def bar(p, q, w, z0, z1):
    (x0, y0), (x1, y1) = p, q
    L = math.hypot(x1 - x0, y1 - y0)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Rot(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0))) * Box(L + w, w, z1 - z0)


def fp_plate(af=C.AF, t=FP_BASE_T, chamfer_top=1.0):
    """Default faceplate base: octagon matching the shell, t thick on the cover face, top edge chamfered."""
    p = C.octagon(0, FACE_Z, FACE_Z + t, af=af)
    return chamfer(p.edges().group_by(Axis.Z)[-1], chamfer_top) if chamfer_top else p


def logo_solid(svg, width, t=0.8):
    """Official SVG -> raised solid, width-scaled, centred at (0,0), z 0..t. Even-odd holes handled. Never redraw logos."""
    raw = import_svg(str(HERE / "logos" / svg))
    k = width / Compound(raw).bounding_box().size.X
    faces = [f.scale(k) for f in raw]
    bb = Compound(faces).bounding_box()
    off = Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2)
    g = Part()
    for f in sorted((off * f for f in faces), key=lambda f: -f.area):
        e = _extrude_valid(f, t)
        g = e if not g.solids() else (g - e if (g & e).volume > 0.9 * e.volume else g + e)
    return g


def _poly_face(w, step=0.03):
    """Wire -> fine polygon (within 0.03 mm of the official outline); only used to repair faces OCC flags invalid."""
    n = max(12, int(w.length / step))
    pts = []
    for k in range(n):
        p = w.position_at(k / n)
        if not pts or (p - pts[-1]).length > 1e-4:
            pts.append(p)
    while len(pts) > 3 and (pts[-1] - pts[0]).length < 1e-3:
        pts.pop()
    return Polygon(*[(p.X, p.Y) for p in pts], align=None)


def _extrude_valid(f, t):
    """Extrude an SVG/font face; faces with zero-length edges (the NVIDIA 'A', two State Farm faces) would vanish or
    invert in booleans, so rebuild them from their own outline. Same official geometry, never redrawn."""
    if f.is_valid:
        e = extrude(f, t)
        if e.is_valid:
            return e
    e = extrude(_poly_face(f.outer_wire()), t)
    for w in f.inner_wires():
        e -= extrude(_poly_face(w), t)
    if not e.is_valid:
        raise ValueError("logo glyph could not be repaired")
    return e


def logo(svg, width, at=(0.0, 0.0), z=None, h=0.8, rot=0.0):
    """Raised logo standing on a face at height z (default: the cover face + base). State Farm >= 55 mm wide, NVIDIA >= 40."""
    z = FACE_Z + FP_BASE_T if z is None else z
    return Pos(at[0], at[1], z) * Rot(0, 0, rot) * logo_solid(svg, width, h)


def text(s, size, at=(0.0, 0.0), z=None, h=0.8, rot=0.0, font="Bahnschrift"):
    from build123d import Text
    z = FACE_Z + FP_BASE_T if z is None else z
    return Pos(at[0], at[1], z) * Rot(0, 0, rot) * extrude(Text(s, font_size=size, font=font), h)


def deck_band():
    """The carve-able outer 2 mm of both decks (back + front), for side_cut designs."""
    return C.decor_band(C.Z_BACK0, C.Z_FRONT1)


# ---------------- what a faceplate must never cover ----------------
def _flare(shape_fn, h=Z_MAX - FACE_Z + 2):
    return shape_fn(h)


def keep_open():
    """Zones above the cover face that must stay open (45 deg flare so tall faceplates don't vignette or block)."""
    h = Z_MAX - FACE_Z + 2
    z0 = FACE_Z - 0.01
    k = Pos(0, 0, z0) * Cone(C.LED["od"] / 2 + 1.0, C.LED["od"] / 2 + 1.0 + h, h, align=None)          # lens + light ring
    fx, fy = C.FAN_C
    k += Pos(fx, fy, z0) * Cone(18.5, 18.5 + 0.6 * h, h, align=None)                                   # fan intake
    sx, sy = C.SPK["c"]
    k += Pos(sx, sy, z0) * Cone(C.SPK["grille_r"] + 1.0, C.SPK["grille_r"] + 1.0 + h, h, align=None)   # speaker
    for mx, my in C.MICS:
        k += Pos(mx, my, z0) * Cone(3.5, 3.5 + h, h, align=None)                                       # mic ports
    rx, ry = C.RADAR["c"]
    ow, oh = C.RADAR["open"]
    k += loft([Pos(rx, ry, z0) * Polygon((-ow / 2 - 1, -oh / 2 - 1), (ow / 2 + 1, -oh / 2 - 1), (ow / 2 + 1, oh / 2 + 1), (-ow / 2 - 1, oh / 2 + 1), align=None),
               Pos(rx, ry, z0 + h) * Polygon((-ow / 2 - 1 - h, -oh / 2 - 1 - h), (ow / 2 + 1 + h, -oh / 2 - 1 - h), (ow / 2 + 1 + h, oh / 2 + 1 + h), (-ow / 2 - 1 - h, oh / 2 + 1 + h), align=None)])
    ox, oy = C.OLED["c"]
    (wx0, wx1), (wy0, wy1) = C.OLED["win"]
    x0, y0 = ox - C.OLED["pcb"][0] / 2 + 0.2, oy - C.OLED["pcb"][1] / 2 + 0.2
    ax0, ax1, ay0, ay1 = x0 + wx0 - 2, x0 + wx1 + 2, y0 + wy0 - 2, y0 + wy1 + 2
    k += loft([Pos(0, 0, z0) * Polygon((ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1), align=None),
               Pos(0, 0, z0 + h) * Polygon((ax0 - h, ay0 - h), (ax1 + h, ay0 - h), (ax1 + h, ay1 + h), (ax0 - h, ay1 + h), align=None)])
    return k


def screw_cuts():
    s = Part()
    for x, y in C.PILLARS:
        s += cz(x, y, C.M3_CLR / 2, FACE_Z - 1, Z_MAX + 5) + cz(x, y, C.M3_HEAD / 2 + 0.2, FACE_Z + FP_BASE_T, Z_MAX + 5)
    return s


def finalize(d: Design):
    """Faceplate with the functional openings + screw holes cut; side cut confined to the decor band."""
    f = d.faceplate() & box(-HALF, HALF, -HALF, HALF, FACE_Z, Z_MAX)
    f -= keep_open() + screw_cuts()
    sc = (d.side_cut() & deck_band()) if d.side_cut else None
    return f, sc


def overhang_area(part, bed_z):
    """Down-facing area (mm^2) steeper than 45 deg, excluding the bed, for a face-up print."""
    import numpy as np, tempfile, os, trimesh
    fd, tmp = tempfile.mkstemp(suffix=".stl"); os.close(fd)
    export_stl(part, tmp, tolerance=0.05, angular_tolerance=0.3)
    mm = trimesh.load(tmp); os.remove(tmp)
    nz = mm.face_normals[:, 2]
    zc = mm.triangles_center[:, 2]
    off = zc > bed_z + 0.05
    steep = (nz < -0.72) & (nz > -0.985) & off
    flat = (nz <= -0.985) & off
    return float(mm.area_faces[steep].sum()), float(mm.area_faces[flat].sum())


def validate(d: Design, verbose=True):
    """Returns (ok, report). Fails on: envelope, keep-open intrusion, missing screw bosses, side cut outside band, overhangs."""
    f, sc = finalize(d)
    rep, ok = {}, True
    bb = f.bounding_box()
    rep["size"] = [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.max.Z - FACE_Z, 1)]
    if bb.min.Z > FACE_Z + 0.01 or abs(bb.min.Z - FACE_Z) > 0.01:
        ok = False; rep["err_bed"] = f"faceplate must sit on the cover face (min z {bb.min.Z:.2f})"
    if bb.max.Z > Z_MAX + 0.01 or max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y)) > C.ENVELOPE / 2:
        ok = False; rep["err_env"] = "outside the 6 x 6 x 4 in envelope"
    for x, y in C.PILLARS:            # a screw needs 3 mm of faceplate around it to clamp
        ring = cz(x, y, 5.0, FACE_Z, FACE_Z + FP_BASE_T) - cz(x, y, C.M3_HEAD / 2 + 0.3, FACE_Z - 1, FACE_Z + FP_BASE_T + 1)
        if (f & ring).volume < 0.8 * ring.volume:
            ok = False; rep.setdefault("err_screw", []).append((x, y))
    if sc is not None:
        rep["side_cut_cm3"] = round(sc.volume / 1000, 2)
    steep, flat = overhang_area(f, FACE_Z)
    rep["overhang_steep_mm2"], rep["bridges_mm2"] = round(steep), round(flat)
    if steep > 60:
        ok = False; rep["err_overhang"] = f"{steep:.0f} mm2 steeper than 45 deg (face-up print)"
    rep["faceplate_cm3"] = round(f.volume / 1000, 1)
    if verbose:
        print(f"{'OK ' if ok else 'FAIL'} {d.id:22} {rep}", flush=True)
    return ok, rep, f, sc


def all_designs(skip=()):
    """Every DESIGNS list in designs/*.py; `skip` names modules to leave out (e.g. one still being written)."""
    import designs, os
    skip = set(skip) | set(filter(None, os.environ.get("NODE_SKIP", "").split(",")))
    out = []
    for mod in pkgutil.iter_modules(designs.__path__):
        if mod.name not in skip:
            out += importlib.import_module(f"designs.{mod.name}").DESIGNS
    return out


if __name__ == "__main__":
    import sys
    want = set(sys.argv[1:])
    res = [validate(d) for d in all_designs() if not want or d.id in want]
    print(f"{sum(r[0] for r in res)}/{len(res)} designs pass")

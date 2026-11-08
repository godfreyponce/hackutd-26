"""Home monitor node v5: the single-layer case restyled. Straight square box, 45-degree chamfer round the top, 4 mm walls,
hexagon pattern V-cut into the walls (90-degree groove, like a V-gouge), hex vents/fan grille, sponsor-logo badges.
Same internals as node_single.py (Pi + AI HAT+, ports at the wall, 25 mm fan, slide-in camera).
Run: python node_v5.py [option ...]   -> out/v5_<opt>_{body,lid}.stl + badges"""
import math
import sys
from build123d import RectangleRounded, Box, Cylinder, Pos, Rot, Part, Polygon, extrude, chamfer, Axis, export_stl
import node_single as N
from node_single import box, cz, cy_, HALF, FLOOR

N.CUT, N.WALL = 20.0, 4.0                                   # straight walls, 45-degree corner cuts (Pi corner clears by ~8 mm)
N.LID_T, N.Z_LID = 5.0, N.Z_BODY + 5.0                      # thicker lid: room for the 45-degree top chamfer + badge pockets
N.COLS[:] = [(sx * 59.0, sy * 59.0) for sx in (-1, 1) for sy in (-1, 1)]   # columns merged into the corner cuts
# lid screws: M3 x 1/4" PC screws (6.35 mm). Counterbore leaves 2 mm of lid under the head -> 4.3 mm into the insert
N.LID_CB, N.LID_HEAD = N.LID_T - 2.0, 7.0
N.STYLE_FINS = N.STYLE_GRILLE = False
N.MERGE_PORTS = True                                        # one full opening for USB-C + HDMI
# Fan: the 30 mm 5 V PWM fan from the Argon40 POLY+ 5 case (MC 686314) [u: measure thickness + hole spacing; 3007 assumed]
N.FAN.update(size=30.0, pitch=24.0, depth=7.0, z=27.0)
N.FAN_SCREWS = False                                        # 1/4" screws can't pass 4 mm wall + 7 mm fan: press-fit guides + hot glue

# Speaker: HIBOX3070-K 3 W 4 ohm enclosed, assumed = Adafruit 3351 (30 x 70 x 17, 3.4 mm holes on 63 x 24) [u: measure]
SPK = dict(w=70.0, h=30.0, d=17.0, z=25.0, pitch=(63.0, 24.0), cl=0.3, frame=2.0, frame_d=8.0, skin=1.2)

# SDR cable: the USB extension's male plug goes in through the +x wall, straight into the Pi's outer USB stack (Pi y 47.0)
USB_SLOT = dict(u=N.P0[1] + 47.0, z0=N.PCB_TOP - 1.0, z1=N.PCB_TOP + 18.0, w=20.0)   # u = world y on the +x wall
GROOVE = 1.0                                                # V-groove depth (90 deg: width 2 x depth)
WALLS = {"-y": 0.0, "+x": 90.0, "+y": 180.0, "-x": 270.0}  # rotation that maps the -y wall frame onto each wall

OPTIONS = {
    "A": dict(name="Hex Facets", hex_r=12.0, band=(4.0, 44.0), vents="hex", grille="hex", chamfer=4.0,
              blurb="Full-height 12 mm hex lattice V-cut into every wall; side vents are through-cut hex cells; hex fan grille."),
    "B": dict(name="Hex Band", hex_r=8.0, band=(14.0, 36.0), vents="hex", grille="rings", chamfer=3.0,
              blurb="A belt of small hexagons round the middle between two clean V-lines; concentric-ring fan grille."),
    "C": dict(name="Macro Hex", hex_r=20.0, band=(3.0, 45.0), vents="slots", grille="turbine", chamfer=4.5,
              blurb="A few big hexagonal facets, grouped vertical vents, and a swept-blade 'turbine' fan grille."),
}


# ---------------- hex V-grooves ----------------
def hex_edges(r, u0, u1, v0, v1):
    """Edges of a pointy-top hex lattice (r = centre-to-vertex) covering u0..u1 x v0..v1, deduplicated."""
    w, h = math.sqrt(3) * r, 1.5 * r
    edges = set()
    j0, j1 = int(v0 // h) - 1, int(v1 // h) + 2
    for j in range(j0, j1):
        cy = j * h
        off = w / 2 if j % 2 else 0.0
        for i in range(int(u0 // w) - 2, int(u1 // w) + 3):
            cx = i * w + off
            vs = [(round(cx + r * math.cos(math.radians(90 + 60 * k)), 3), round(cy + r * math.sin(math.radians(90 + 60 * k)), 3)) for k in range(6)]
            for k in range(6):
                a, b = vs[k], vs[(k + 1) % 6]
                edges.add(tuple(sorted((a, b))))
    return edges


def vgroove(a, b, d):
    """90-degree V-groove of depth d along segment a->b drawn in the wall plane (u = x, v = z) at y = 0."""
    (u0, v0), (u1, v1) = a, b
    L = math.hypot(u1 - u0, v1 - v0)
    s = d * math.sqrt(2)
    ang = math.degrees(math.atan2(v1 - v0, u1 - u0))
    return Pos((u0 + u1) / 2, 0, (v0 + v1) / 2) * Rot(0, -ang, 0) * Rot(45, 0, 0) * Box(L + s, s, s)


def wall_pattern(o, u0, u1):
    """Groove set for one wall (in the -y wall frame: u along x, outer face at y = -HALF)."""
    v0, v1 = o["band"]
    g = Part()
    for a, b in hex_edges(o["hex_r"], u0, u1, v0, v1):
        g += vgroove(a, b, GROOVE)
    g = Pos(0, -HALF, 0) * g
    return g & box(u0, u1, -HALF - 2, -HALF + 2, v0, v1)


def masks():
    """Places the pattern must not cut (wall frame -y unless noted): ports, fan, vents, corners, chamfer zone."""
    yo = -HALF
    m = {}
    m["-y"] = box(N.P0[0] - 4, N.P0[0] + 92, yo - 3, yo + 3, 0, N.Z_BODY + 1)            # whole port-wall stretch (2 mm wall)
    m["+y"] = Rot(0, 0, 180) * (cy_(0, N.FAN["z"], N.FAN["size"] / 2 + 3.0, yo - 3, yo + 3))  # fan grille + guide field
    return m


def vents(o):
    """Through-cut intake on both side walls (frame -y, rotated onto +x / -x)."""
    yo = -HALF
    v = Part()
    if o["vents"] == "hex":
        r = 5.0
        w = math.sqrt(3) * r
        for j in range(3):
            for i in range(-4, 5):
                cx, cz_ = i * w + (w / 2 if j % 2 else 0), 16.0 + j * 1.5 * r
                if abs(cx) > 45:
                    continue
                pts = [(cx + (r - 1.2) * math.cos(math.radians(90 + 60 * k)), cz_ + (r - 1.2) * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
                v += Pos(0, yo + N.WALL + 1, 0) * Rot(90, 0, 0) * extrude(Polygon(*pts, align=None), N.WALL + 3)
    else:
        for i in range(-9, 10):
            x = i * 4.6
            v += box(x - 1.1, x + 1.1, yo - 1, yo + N.WALL + 1, 10.0, 38.0)
    return v


def grille(o):
    """Fan grille on the +y wall (drawn in the -y frame, rotated 180 deg)."""
    yo, R = -HALF, N.FAN["size"] * 0.45
    z = N.FAN["z"]
    g = Part()
    if o["grille"] == "hex":
        r = 2.6
        w = math.sqrt(3) * r
        for j in range(-4, 5):
            for i in range(-4, 5):
                cx, cz_ = i * w + (w / 2 if j % 2 else 0), z + j * 1.5 * r
                if math.hypot(cx, cz_ - z) > R - r * 0.6:
                    continue
                pts = [(cx + (r - 0.7) * math.cos(math.radians(90 + 60 * k)), cz_ + (r - 0.7) * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
                g += Pos(0, yo + N.WALL + 1, 0) * Rot(90, 0, 0) * extrude(Polygon(*pts, align=None), N.WALL + 3)
    elif o["grille"] == "rings":
        for rr in (3.0, 6.5, 10.0):
            g += cy_(0, z, rr + 1.0, yo - 1, yo + N.WALL + 1) - cy_(0, z, rr - 1.0, yo - 2, yo + N.WALL + 2)
        for a in (0, 120, 240):                                            # keep 3 spokes so the rings stay attached
            g -= Pos(0, yo, z) * Rot(0, -a, 0) * box(-0.8, 0.8, -3, N.WALL + 3, 0, R + 1)
    else:  # turbine: 7 swept blades
        for k in range(7):
            a0 = k * 360 / 7
            pts = []
            for t in [i / 10 for i in range(11)]:
                rr, aa = 3.0 + t * (R - 3.5), math.radians(a0 + 55 * t)
                pts.append((rr * math.cos(aa), z + rr * math.sin(aa)))
            for t in [i / 10 for i in range(10, -1, -1)]:
                rr, aa = 3.0 + t * (R - 3.5), math.radians(a0 + 55 * t + 22)
                pts.append((rr * math.cos(aa), z + rr * math.sin(aa)))
            g += Pos(0, yo + N.WALL + 1, 0) * Rot(90, 0, 0) * extrude(Polygon(*pts, align=None), N.WALL + 3)
    return Rot(0, 0, 180) * g


def speaker_proxy():
    """Speaker box against the -x wall, drawn in the -y frame (u along the wall)."""
    yi, s = -HALF + N.WALL, SPK
    return box(-s["w"] / 2, s["w"] / 2, yi, yi + s["d"], s["z"] - s["h"] / 2, s["z"] + s["h"] / 2)


def speaker_mount():
    """(add, cut) for the -x wall: shelf + side rails the speaker drops into, a hex sound grille,
    and 4 M3 holes thinned to a 1.2 mm skin from outside so a 1/4" screw reaches a nut IF the speaker's holes are a thin flange."""
    yo, yi, s = -HALF, -HALF + N.WALL, SPK
    w, h, c, f = s["w"] / 2 + s["cl"], s["h"] / 2 + s["cl"], s["cl"], s["frame"]
    # shelf from the floor + two side rails: the speaker drops in from above (no overhangs to print; dab of glue on top)
    add = box(-w - f, w + f, yi - 0.5, yi + s["frame_d"], FLOOR - 0.5, s["z"] + h)         - box(-w, w, yi - 1, yi + s["frame_d"] + 1, s["z"] - h, s["z"] + h + 1)
    cut = Part()
    r = 2.6
    wd = math.sqrt(3) * r
    for j in range(-3, 4):
        for i in range(-6, 7):
            cx, cz_ = i * wd + (wd / 2 if j % 2 else 0), s["z"] + j * 1.5 * r
            if abs(cx) > 24 or abs(cz_ - s["z"]) > 9.5:
                continue
            pts = [(cx + (r - 0.7) * math.cos(math.radians(90 + 60 * k)), cz_ + (r - 0.7) * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
            cut += Pos(0, yo + N.WALL + 1, 0) * Rot(90, 0, 0) * extrude(Polygon(*pts, align=None), N.WALL + 3)
    pu, pz = s["pitch"][0] / 2, s["pitch"][1] / 2
    for su in (-1, 1):
        for sz in (-1, 1):
            cut += cy_(su * pu, s["z"] + sz * pz, 1.7, yo - 1, yi + 1) + cy_(su * pu, s["z"] + sz * pz, 3.4, yo - 1, yi - s["skin"])
    return add, cut


def make_body(o):
    b = N.make_body()
    msk = masks()
    cuts = Part()
    for wall, rot in WALLS.items():
        u = HALF - N.CUT - 3.0                                             # flat face only: the corner cuts stay plain
        pat = wall_pattern(o, -u, u)
        if wall in msk:
            pat -= (Rot(0, 0, -rot) * msk[wall]) if wall == "+y" else msk[wall]
        if wall in ("+x", "-x"):
            pat -= Pos(0, 0, 0) * box(-46, 46, -HALF - 3, -HALF + 3, 8.0, 42.0)   # vent field stays plain
        cuts += Rot(0, 0, rot) * pat
    b -= cuts
    s = USB_SLOT                                                           # +x: vents, kept clear of the USB slot
    b -= Rot(0, 0, 90.0) * (vents(o) - box(s["u"] - s["w"] / 2 - 3, s["u"] + s["w"] / 2 + 3, -HALF - 3, -HALF + N.WALL + 3, 0, N.Z_BODY))
    b -= Rot(0, 0, 90.0) * (Pos(s["u"], -HALF + N.WALL / 2, (s["z0"] + s["z1"]) / 2) * Rot(90, 0, 0)
                            * extrude(RectangleRounded(s["w"], s["z1"] - s["z0"], 3.0), N.WALL + 4, both=True))
    add, cut = speaker_mount()                                             # -x: speaker
    b = b + Rot(0, 0, 270.0) * add - Rot(0, 0, 270.0) * cut
    b -= grille(o)
    return b


# ---------------- lid: 45-degree top edge + badge pockets ----------------
BADGES = {   # name: (centre, size) on the lid top; pockets 1.2 deep, badges press-fit (0.1 per side)
    "team": ((0.0, 46.0), (84.0, 24.0)),           # LAND (traced from Rafael's PNG -> logos/land.svg)
    "nvidia": ((-34.0, -42.0), (58.0, 18.0)),
    "statefarm": ((34.0, -42.0), (62.0, 16.0)),
}
POCKET = 1.2
INLAY = 0.6                                                 # logos inlaid flush in the lid top: 3 layers of colour at 0.2 mm
LOGO = {"team": ("land.svg", 78.0, "#f2f2ee"), "nvidia": ("nvidia.svg", 50.0, "#76b900"), "statefarm": ("state_farm.svg", 56.0, "#ec0c21")}


def logo_inlay(name, extra=0.0):
    """The logo as a solid filling the top INLAY mm of the lid (extra: grow upward, for cutting)."""
    import node_design as D
    (cx, cy), _ = BADGES[name]
    svg, lw, _ = LOGO[name]
    lg = D.logo(svg, lw, at=(cx, cy), z=N.Z_LID - INLAY, h=INLAY + extra)
    out = Part()                                                           # some glyph pieces (the (R) in State Farm) come out
    for sol in lg.solids():                                                # extruded downward: sit every piece on the same floor
        out += Pos(0, 0, N.Z_LID - INLAY - sol.bounding_box().min.Z) * sol
    return out
N.CAM["x"] = -45.0                                          # lid top, left to right: camera | LED ring (centre) | PIR
# NeoPixel Ring 12 (Adafruit 1643): OD 36.8, ID 23.3. Sits LEDs-up in a pocket round the lens, LED tops flush
# (1.6 PCB + 1.6 LED assumed) [u: measure]. Four through-pads near the rim (r ~17, from Adafruit's board image):
# IN 15, GND 135, PWR 195, OUT 315 deg clockwise. Ring sits dead centre; each pad gets a d4.4 wire hole (pad ~1.4)
# straight down through the lid. The centre hole (ID) is left open so the wires can also go through there.
RING = dict(od=36.8, id=23.3, t=3.4, cl=0.3, pad_r=16.6, hole=4.4, rot=0.0,
            pads={"IN": 15.0, "GND": 135.0, "PWR": 195.0, "OUT": 315.0})


def ring_holes(z0, z1):
    r, h = RING, Part()
    for a in r["pads"].values():
        t = math.radians(a + r["rot"])
        h += cz(r["pad_r"] * math.sin(t), r["pad_r"] * math.cos(t), r["hole"] / 2, z0, z1)
    return h


# PIR HC-SR501: PCB 32.4 x 24.1 (~1.2 thick) [u: measure], M2 holes 28 apart on the long axis, 23 mm lens dome on top.
# Sits in a 1.2 mm pocket so the PCB top is flush with the lid; it rests on two tabs under its holes and everything
# else on its underside (pots, jumper, header + plugs) drops through one big window. Wires plug in from inside.
PIR = dict(x=45.0, y=0.0, L=32.4, W=24.1, t=1.2, cl=0.4, hole_dx=14.0, tab=(4.6, 6.0), lens=23.0, lens_h=13.0, under=20.0)


def pir_cuts(zt):
    p = PIR
    L, W = p["L"] / 2 + p["cl"], p["W"] / 2 + p["cl"]
    cut = box(p["x"] - L, p["x"] + L, p["y"] - W, p["y"] + W, zt - p["t"], zt + 1)          # flush pocket
    win = box(p["x"] - L, p["x"] + L, p["y"] - W, p["y"] + W, N.Z_BODY - 1, zt)
    for s in (-1, 1):                                                       # keep the two tabs under the M2 holes
        tx0, tx1 = sorted((p["x"] + s * (p["hole_dx"] - p["tab"][0] / 2), p["x"] + s * (L + 1)))
        win -= box(tx0, tx1, p["y"] - p["tab"][1] / 2, p["y"] + p["tab"][1] / 2, N.Z_BODY - 2, zt + 1)
        cut += cz(p["x"] + s * p["hole_dx"], p["y"], 1.1, N.Z_BODY - 1, zt + 1)            # M2 / glue-pin hole
    return cut + win


def pir_proxy(zt):
    p = PIR
    L, W = p["L"] / 2, p["W"] / 2
    hw = box(p["x"] - L, p["x"] + L, p["y"] - W, p["y"] + W, zt - p["t"], zt)
    hw += cz(p["x"], p["y"], p["lens"] / 2, zt, zt + p["lens_h"])
    for s in (-1, 1):                                                       # underside parts + plugs, clear of the tabs
        hw += box(*sorted((p["x"] + s * 0.5, p["x"] + s * (p["hole_dx"] - p["tab"][0] / 2 - 0.3))), p["y"] - W, p["y"] + W, zt - p["t"] - p["under"], zt - p["t"])
    return hw


def vgroove_top(a, b, d, z):
    """90-degree V-groove of depth d along a->b on a horizontal face at height z."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    s = d * math.sqrt(2)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z) * Rot(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0))) * Rot(45, 0, 0) * Box(L + s, s, s)


def make_lid(o):
    N.LID_CHAMFER = o["chamfer"]
    l = N.make_lid()
    zt = N.Z_LID
    # lid top: the same hex lattice V-cut into the top, framed inside the chamfer, kept off the badges, lens and screws
    lim = HALF - o["chamfer"] - 3.0
    g = Part()
    for a, b in hex_edges(o["hex_r"], -lim, lim, -lim, lim):
        g += vgroove_top(a, b, GROOVE, zt)
    g &= N.body_shape(o["chamfer"] + 3.0, zt - 2, zt + 2)                 # follows the corner cuts
    camx = N.CAM["x"]
    keep = cz(0, 0, RING["od"] / 2 + 3.0, zt - 3, zt + 3)                  # plain border round the LED ring
    keep += cz(camx, 0, 11.0, zt - 3, zt + 3)                              # and round the lens
    keep += box(PIR["x"] - PIR["L"] / 2 - 3.5, PIR["x"] + PIR["L"] / 2 + 3.5, -PIR["W"] / 2 - 3.5, PIR["W"] / 2 + 3.5, zt - 3, zt + 3)
    for (cx, cy), (w, h) in BADGES.values():
        keep += box(cx - w / 2 - 2.5, cx + w / 2 + 2.5, cy - h / 2 - 2.5, cy + h / 2 + 2.5, zt - 3, zt + 3)
    for x, y in N.COLS:
        keep += cz(x, y, 6.5, zt - 3, zt + 3)
    l -= g - keep
    r = RING                                                               # LED ring pocket + pad holes, PIR pocket
    l -= cz(0, 0, r["od"] / 2 + r["cl"], zt - r["t"], zt + 1) - cz(0, 0, r["id"] / 2 - r["cl"], zt - r["t"] - 1, zt + 2)
    l -= ring_holes(N.Z_BODY - 1, zt + 1) + pir_cuts(zt)
    for nm in BADGES:                                                      # logos: cut flush, filled by the logo parts
        l -= logo_inlay(nm, extra=1.0)
    return l


def make_badge(name):
    """Badge plate (black) with the official logo raised 0.8 mm: pause at 1.2 mm and switch to the sponsor colour."""
    import node_design as D
    (cx, cy), (w, h) = BADGES[name]
    plate = box(cx - w / 2 + 0.1, cx + w / 2 - 0.1, cy - h / 2 + 0.1, cy + h / 2 - 0.1, N.Z_LID - POCKET, N.Z_LID)
    svg, lw = {"team": ("land.svg", w - 6), "nvidia": ("nvidia.svg", w - 10), "statefarm": ("state_farm.svg", w - 6)}[name]
    return plate + D.logo(svg, lw, at=(cx, cy), z=N.Z_LID, h=0.8)


if __name__ == "__main__":
    want = sys.argv[1:] or list(OPTIONS)
    hw = N.hardware() + Rot(0, 0, 270.0) * speaker_proxy() + pir_proxy(N.Z_LID)
    for k in want:
        o = OPTIONS[k]
        body, lid = make_body(o), make_lid(o)
        bad = 0
        for nm, p in (("body", body), ("lid", lid)):
            v = (p & hw).volume
            bad += (v > 0.001) + (len(p.solids()) != 1)
            print(f"{k} {nm:4} hw {v:.3f} solids {len(p.solids())} {p.volume/1000:.1f} cm3", flush=True)
            export_stl(p, str(N.OUT / f"v5_{k}_{nm}.stl"), tolerance=0.02, angular_tolerance=0.1)
        v = (body & lid).volume
        bad += v > 0.001
        print(f"{k} {o['name']}: body x lid {v:.3f}  problems {bad}", flush=True)
    for nm in BADGES:
        export_stl(make_badge(nm), str(N.OUT / f"v5_badge_{nm}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print("badges ok")

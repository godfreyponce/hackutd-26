"""13 outer-shell concepts for the Pi 5 + AI HAT+ case, HackUTD 2026 "Zero Day".
Every concept reuses the functional core in pi5_aihat_case.py unchanged (cavity, ports, inserts, stops, slots).
A skin can only ADD material outside the functional outline (never inside the I/O keep-outs) and CUT into what it
added, so fit, port access and wall thickness are identical across all concepts.
Run: python concepts.py <out_dir>  -> one JSON mesh file per concept + index.json (checks included)."""
import math, random
from dataclasses import dataclass
from typing import Callable, Optional
from build123d import Box, Cylinder, Pos, Rot, Part, Polygon, Ellipse, Text, extrude, fillet, chamfer, Axis
import pi5_aihat_case as m
from pi5_aihat_case import box, cz, OX0, OX1, OY0, OY1, SPLIT, LID_TOP, FAN_C, FAN_P, M3_CLR, TOWERS, FLOOR

TX0, TX1, TY0, TY1 = -4.3, 87.6, -4.6, 60.6   # tower centres = corners of every hull
ZB, ZT = -FLOOR, 60.0                          # env height (clipped per part)


@dataclass
class Skin:
    id: str
    name: str
    cat: str            # wild / modern / sleek
    blurb: str
    palette: tuple      # (base, lid, guard) suggested filament colours
    env: Optional[Callable] = None
    side_cut: Optional[Callable] = None
    deck: float = 0.0
    deck_cut: Optional[Callable] = None
    vents: Optional[Callable] = None
    guard: Optional[Callable] = None
    text: bool = True
    top_ch: float = 0.6


# ---------- geometry helpers ----------
def hull(R, z0=ZB, z1=ZT):  # rounded rectangle whose corner arcs are concentric with the insert towers
    return fillet(box(TX0 - R, TX1 + R, TY0 - R, TY1 + R, z0, z1).edges().filter_by(Axis.Z), R - 0.01)


def prism(pts, z0, z1, taper=0.0):
    return Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), z1 - z0, taper=taper)


def seg(p, q, w, z0, z1):  # bar from p to q (xy), width w
    (x0, y0), (x1, y1) = p, q
    L = math.hypot(x1 - x0, y1 - y0)
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Rot(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0))) * Box(L + w, w, z1 - z0)


def union(parts):
    out = Part()
    for p in parts:
        out += p
    return out


def back_face(R):   # outer y of a hull(R) back wall, etc.
    return TY1 + R


# ---------- guards (40 x 40 x 2, centred, z 0..2) ----------
def guard(pattern):
    frame = fillet(Box(40, 40, 2).edges().filter_by(Axis.Z), 3.0) - Cylinder(18.5, 3)
    g = frame + (pattern & Cylinder(18.7, 2))
    for sx in (-1, 1):
        for sy in (-1, 1):
            g -= Pos(sx * FAN_P, sy * FAN_P) * Cylinder(M3_CLR / 2, 3)
    return Pos(0, 0, 1) * g


def ring(r, w=1.6):
    return Cylinder(r + w / 2, 2) - Cylinder(r - w / 2, 3)


def bars(angle, pitch, w=1.6, n=6):
    return union(Rot(0, 0, angle) * Pos(0, k * pitch, 0) * Box(40, w, 2) for k in range(-n, n + 1))


# =============================== WILD (Zero Day) ===============================
def breach():
    rnd = random.Random(7)
    oct_b = [(-11, -9), (-4, -13), (88, -13), (96, -6), (96, 63), (89, 70), (-4, 70), (-11, 63)]
    env = lambda: prism(oct_b, ZB, SPLIT, taper=-6) + prism([(x * 1.0, y) for x, y in oct_b], SPLIT, ZT, taper=0) \
        .scale(1.0)
    def cracks(top):   # shatter lines radiating from an impact point on the front-right deck
        P, cut = (63.0, -7.0), Part()
        for a in (95, 120, 150, 170, 60, 30, 10):
            p, ang = P, math.radians(a)
            for _ in range(3):
                L = rnd.uniform(9, 17)
                ang += math.radians(rnd.uniform(-22, 22))
                q = (p[0] + L * math.cos(ang), p[1] + L * math.sin(ang))
                cut += seg(p, q, 1.1, top - 1.6, top + 1)
                p = q
        return cut + cz(*P, 2.6, top - 1.6, top + 1)
    def g():
        rnd2 = random.Random(3)
        pat = union(seg((1.5, -2), (19 * math.cos(math.radians(a)), 19 * math.sin(math.radians(a))), 1.8, -1, 1)
                    for a in (12, 70, 128, 200, 255, 318))
        pts = [(rnd2.uniform(8, 11) * math.cos(t), rnd2.uniform(8, 11) * math.sin(t)) for t in [i * math.pi / 4 for i in range(8)]]
        pat += union(seg(pts[i], pts[(i + 1) % 8], 1.8, -1, 1) for i in range(8))
        return guard(pat)
    return Skin("breach", "BREACH", "wild",
                "Stealth-octagon shell with a flared skirt. The deck carries shatter lines from an impact point, "
                "and the fan guard is a cracked-glass web.",
                ("#14161a", "#14161a", "#ff3b3b"), env=lambda: prism(oct_b, ZB, SPLIT, taper=-6) + prism(oct_b, SPLIT, ZT),
                deck=2.0, deck_cut=cracks, guard=g, top_ch=1.2)


def glitch():
    rnd = random.Random(11)
    H = 2.5

    def walk(n):   # outward offset per slab; a slab never sticks out more than 1.0 past the one printed before it
        e, out = rnd.uniform(1, 3), []
        for _ in range(n):
            out.append(e)
            e = min(max(e + rnd.uniform(-2.2, 1.0), 0.0), 4.0)
        return out

    def env():
        zs_b = [ZB + i * H for i in range(int((SPLIT - ZB) / H) + 1)]
        zs_l = [ZT - i * H for i in range(int((ZT - SPLIT) / H) + 1)]   # lid prints upside down: walk from the top
        part = Part()
        for zs, sgn in ((zs_b, 1), (zs_l, -1)):
            sides = [walk(len(zs)) for _ in range(4)]
            for i, z in enumerate(zs):
                l, r, f, b = (s[i] for s in sides)
                z0, z1 = (z, z + H) if sgn > 0 else (z - H, z)
                part += box(TX0 - 5 - l, TX1 + 5 + r, TY0 - 5 - f, TY1 + 5 + b, max(z0, ZB), z1)
        return part

    def bars_cut(top):
        r2, cut = random.Random(5), Part()
        for _ in range(26):
            x, y = r2.uniform(-8, 90), r2.uniform(-9, 64)
            cut += box(x, x + r2.uniform(4, 16), y, y + r2.choice((1.2, 1.2, 2.4)), top - 1.2, top + 1)
        return cut

    def g():
        r3 = random.Random(2)
        pat = bars(0, 6.0, 1.6) + bars(90, 6.0, 1.6)
        for _ in range(6):   # displaced pixel blocks
            x, y = r3.randint(-2, 2) * 6 + 3, r3.randint(-2, 2) * 6 + 3
            pat += Pos(x, y, 0) * Box(6.0, 6.0, 2)
        return guard(pat)
    return Skin("glitch", "GLITCH", "wild",
                "Datamosh shell built from 2.5 mm slabs, each shifted out of line like a corrupted frame. "
                "The deck has torn scanlines and the guard is a pixel grid with dead blocks.",
                ("#1b1d24", "#1b1d24", "#ff2bd6"), env=env, deck=1.6, deck_cut=bars_cut, guard=g, top_ch=0.4)


def ring0():
    def rings(top):
        return union(cz(*FAN_C, r + 0.6, top - 1.4, top + 1) - cz(*FAN_C, r - 0.6, top - 2, top + 2) for r in range(24, 76, 4))
    g = lambda: guard(ring(6.5) + ring(11.5) + ring(16.0) + union(Rot(0, 0, a) * Pos(9, 0, 0) * Box(18, 1.8, 2) for a in (90, 210, 330))
                      + Cylinder(2.5, 2))
    return Skin("ring0", "RING 0", "wild",
                "Named for ring 0, the kernel's privilege level. Concentric grooves ripple out from the fan "
                "like a shockwave, and the guard repeats the rings.",
                ("#101418", "#101418", "#35e0ff"), env=lambda: hull(7.0), deck=2.0, deck_cut=rings, guard=g, top_ch=1.0)


def code_rain():
    R = 6.0

    def columns(face):   # vertical dashes of random length on one outer face
        rnd, cut = random.Random(hash(face) % 999), Part()
        if face == "back":
            y = back_face(R)
            for x in [TX0 - 2 + 3.2 * i for i in range(30)]:
                z = rnd.uniform(-1, 8)
                while z < ZT - 25:
                    L = rnd.uniform(2, 7)
                    cut += box(x - 0.7, x + 0.7, y - 1.5, y + 1, z, z + L)
                    z += L + rnd.uniform(1.5, 5)
        if face == "left":
            x = TX0 - R
            for y in [41.5 + 3.2 * i for i in range(8)] + [-12 + 3.2 * i for i in range(6)]:
                z = rnd.uniform(-1, 8)
                while z < ZT - 25:
                    L = rnd.uniform(2, 7)
                    cut += box(x - 1, x + 1.5, y - 0.7, y + 0.7, z, z + L)
                    z += L + rnd.uniform(1.5, 5)
        return cut

    def deck_rain(top):
        rnd, cut = random.Random(9), Part()
        for x in [-8 + 3.0 * i for i in range(34)]:
            y = rnd.uniform(-10, 5)
            while y < 66:
                L = rnd.uniform(2, 8)
                cut += box(x - 0.6, x + 0.6, y, y + L, top - 1.2, top + 1)
                y += L + rnd.uniform(2, 6)
        return cut
    g = lambda: guard(union(Pos(x, 0, 0) * Box(1.6, 40, 2) for x in range(-15, 16, 5))
                      + union(Pos(x + 2.5, y, 0) * Box(5, 1.6, 2) for x in range(-15, 15, 5) for y in (-12, -3, 7, 13)[(x // 5) % 2::2]))
    return Skin("rain", "CODE RAIN", "wild",
                "A thick monolith with falling code columns cut into the back, the left side and the deck. "
                "The guard is a column grille.",
                ("#0d1210", "#0d1210", "#3dff8a"), env=lambda: hull(R),
                side_cut=lambda: columns("back") + columns("left"), deck=1.6, deck_cut=deck_rain, guard=g, top_ch=0.8)


def honeypot():
    R, rh = 6.0, 3.0

    def hexagon(r, z0, z1, rot=0):
        pts = [(r * math.cos(math.radians(60 * i + rot)), r * math.sin(math.radians(60 * i + rot))) for i in range(6)]
        return prism(pts, z0, z1)

    def side():   # pointy-top hex cells on the back face (60 deg roofs print without support)
        cut, y = Part(), back_face(R)
        pitch_x, pitch_z = 2 * rh * math.cos(math.radians(30)) + 1.8, 1.5 * rh + 1.6
        for j in range(8):
            for i in range(17):
                x = TX0 - 3 + i * pitch_x + (pitch_x / 2 if j % 2 else 0)
                z = 1.5 + j * pitch_z
                cut += Pos(x, y + 0.5, z) * Rot(90, 0, 0) * Pos(0, 0, -1) * Rot(0, 0, 30) * hexagon(rh, 0, 2.0)
        return cut

    def deck_hex(top):
        cut = Part()
        p = 2 * rh * math.cos(math.radians(30)) + 1.6
        for j in range(16):
            for i in range(20):
                x, y = -10 + i * p + (p / 2 if j % 2 else 0), -12 + j * 1.5 * (rh + 0.9)
                cut += Pos(x, y, top - 1.4) * hexagon(rh, 0, 3)
        return cut

    def g():
        disc, a = Cylinder(19, 2), 3.2
        p = 2 * a * math.cos(math.radians(30)) + 1.7
        for j in range(-6, 7):
            for i in range(-6, 7):
                disc -= Pos(i * p + (p / 2 if j % 2 else 0), j * 1.5 * (a + 0.98), -1.5) * hexagon(a, 0, 3, 30)
        return guard(disc)
    return Skin("honeypot", "HONEYPOT", "wild",
                "A honeypot is a trap set for attackers. Hex cells cover the back wall and the deck, "
                "and the guard is a honeycomb mesh.",
                ("#17140c", "#17140c", "#ffb627"), env=lambda: hull(R), side_cut=side, deck=2.0, deck_cut=deck_hex,
                guard=g, top_ch=0.8)


# =============================== MODERN ===============================
def console():
    R = 8.0
    groove = lambda: hull(R, SPLIT - 2.2, SPLIT - 1.0) - hull(R - 1.0, ZB - 5, ZT + 5)   # shadow line under the split
    g = lambda: guard(union(Pos(0, y, 0) * Box(40, 1.8, 2) for y in (-12, -6, 0, 6, 12)))
    return Skin("console", "CONSOLE", "modern",
                "A games-console slab with big 8 mm corner radii, a shadow line that floats the lid, "
                "a clean deck and a slatted guard.",
                ("#e9ecef", "#e9ecef", "#14161a"), env=lambda: hull(R), side_cut=groove, deck=1.2, guard=g, top_ch=1.0)


def blade():
    def env():
        return hull(5.0) + box(TX0 - 3, TX1 + 3, TY1, TY1 + 9, ZB, ZT)   # thick rear "rack" spine

    def grooves():   # horizontal server-rack grooves across the spine (1.2 tall, 2.5 deep: tiny bridges)
        y = TY1 + 9
        return union(box(TX0 - 5, TX1 + 5, y - 2.5, y + 1, z, z + 1.2) for z in [ZB + 2.0 + 2.6 * i for i in range(14)])

    def slots(top):
        return union(box(-8, 46, y, y + 1.4, top - 1.2, top + 1) for y in (-9.0, -6.6)) + \
            union(box(x, x + 1.4, -11, 66, top - 1.2, top + 1) for x in (-8.5, -6.1))
    g = lambda: guard(union(Rot(0, 0, 0) * Pos(0, y, 0) * Box(40, 1.6, 2) for y in range(-16, 17, 4)))
    return Skin("blade", "BLADE", "modern",
                "A rack-server look. A thick rear spine carries horizontal grooves, and long slots on the deck "
                "and a louvered guard complete it.",
                ("#2b2f36", "#2b2f36", "#c8ced6"), env=env, side_cut=grooves, deck=1.6, deck_cut=slots, guard=g, top_ch=0.8)


def terminal():
    def screen(top):   # recessed panel; letters stay at deck level (raised look without printing anything off the bed)
        panel = box(48.8, 68.0, 17.0, 48.4, top - 1.2, top + 1)
        t = extrude(Text("> ZERO_DAY_", font_size=4.4, font=m.FONT), 4) + Pos(0, -6.0, 0) * extrude(Text("HACKUTD 2026", font_size=3.4, font=m.FONT), 4)
        return panel - Pos(56.8, 32.7, top - 2) * Rot(0, 0, 90) * t
    g = lambda: guard(bars(0, 12.4, 1.8, 1) + bars(90, 12.4, 1.8, 1))
    return Skin("terminal", "TERMINAL", "modern",
                "The lid becomes a screen: a recessed bezel with the prompt standing proud inside it. "
                "The guard is a 3 x 3 window grid.",
                ("#22262b", "#22262b", "#7cff6b"), env=lambda: hull(5.5), deck=2.0, deck_cut=screen, guard=g, text=False,
                top_ch=1.0)


def waveform():
    R = 5.0

    def env():   # back ribs whose tops trace a signal
        y = back_face(R)
        ribs = union(box(x - 0.9, x + 0.9, y - 1, y + 3.0, ZB, 9.0 + 8.5 * abs(math.sin(x / 9.0)) * (0.6 + 0.4 * math.cos(x / 23.0)))
                     for x in [TX0 + 1 + 3.0 * i for i in range(31)])
        return hull(R) + ribs

    def trace(top):
        pts = [(x, -8.5 + 2.2 * math.sin(x / 3.2) * math.sin(x / 17.0) * 1.6) for x in [-6 + 0.8 * i for i in range(125)]]
        return union(seg(pts[i], pts[i + 1], 1.0, top - 1.0, top + 1) for i in range(len(pts) - 1))
    g = lambda: guard(union(seg((x, 8 * math.sin(x / 4.0) + k), (x + 1, 8 * math.sin((x + 1) / 4.0) + k), 1.6, -1, 1)
                            for x in range(-19, 19) for k in (-6, 6)) + Box(40, 1.6, 2))
    return Skin("waveform", "WAVEFORM", "modern",
                "Inference as a signal. Back ribs rise and fall like an audio meter, a waveform runs across "
                "the front of the deck, and the guard carries sine bars.",
                ("#1a1f2e", "#1a1f2e", "#8aa8ff"), env=env, deck=1.0, deck_cut=trace, guard=g, top_ch=0.8)


# =============================== SLEEK / EFFICIENT ===============================
def monolith():
    g = lambda: guard(ring(12.0, 1.8) + union(Rot(0, 0, a) * Pos(9.5, 0, 0) * Box(19, 1.8, 2) for a in (90, 210, 330)))
    return Skin("monolith", "MONOLITH", "sleek",
                "One smooth rounded block. The towers disappear into the hull and the only marks are the "
                "prompt and the fan. The guard has three spokes.",
                ("#0f1012", "#0f1012", "#0f1012"), env=lambda: hull(6.0), deck=1.0, guard=g, top_ch=1.2)


def airframe():
    def lattice():   # diagonal truss through the vent zones: about 2x the open area of the stock slots, 2.4 mm members
        cut = Part()
        for i in range(12):
            x = 6 + i * 6.6
            up = [(x + 0.0, 5.5), (x + 3.0, 19.5), (x - 3.0, 19.5)] if i % 2 else [(x - 3.0, 5.5), (x + 3.0, 5.5), (x, 19.5)]
            cut += Pos(0, 200, 0) * Rot(90, 0, 0) * prism(up, 0, 400)
        for y0 in (42.5, 49.0):
            cut += box(-99, 0, y0, y0 + 4.5, 7.5, 19.5)
        return cut
    g = lambda: guard(union(Rot(0, 0, a) * Pos(9.5, 0, 0) * Box(19, 1.6, 2) for a in (45, 135, 225, 315)))
    return Skin("airframe", "AIRFRAME", "sleek",
                "Efficiency first. Stock outline (least plastic), a triangulated truss in the vent zones with "
                "about twice the airflow, and an X guard that is mostly open.",
                ("#d9dde2", "#d9dde2", "#ff7a1a"), vents=lattice, guard=g, top_ch=0.6)


def jet():
    def env():   # crown narrows toward the top (35 deg, prints fine upside down); speed lines on the flanks
        return hull(4.0, ZB, SPLIT) + prism(_rr_pts(8.0), SPLIT, ZT, taper=0) & prism(_rr_pts(8.0), SPLIT, LID_TOP + 1.6, taper=0)

    def lines():
        y = back_face(4.0)
        return union(box(TX0 + 10 + 6 * k, TX1 - 2, y - 1, y + 1, z, z + 0.9) for k, z in enumerate((6, 10, 14, 18)))
    g = lambda: guard(union(seg((5 * math.cos(math.radians(a)), 5 * math.sin(math.radians(a))),
                                (19 * math.cos(math.radians(a + 38)), 19 * math.sin(math.radians(a + 38))), 1.7, -1, 1)
                            for a in range(0, 360, 40)) + ring(5.0, 1.8))
    return Skin("jet", "JET", "sleek",
                "Aero lines. A lid crown wider than the base with a 45 degree bevelled top, speed lines down "
                "the back, and a turbine guard with nine swept vanes.",
                ("#e6e8eb", "#2a2f38", "#2a2f38"), env=lambda: hull(4.0, ZB, SPLIT) + hull(7.5, SPLIT, ZT),
                side_cut=lines, deck=1.6, guard=g, top_ch=3.0)


def _rr_pts(R):
    return [(TX0 - R, TY0 - R), (TX1 + R, TY0 - R), (TX1 + R, TY1 + R), (TX0 - R, TY1 + R)]


def stealth():
    c = 7.0
    x0, x1, y0, y1 = -12.0, 95.5, -12.5, 68.5
    pts = [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    env = lambda: chamfer(prism(pts, ZB, ZT).edges().group_by(Axis.Z)[0], 2.5)   # 45 deg bottom facet on the bed face
    g = lambda: guard(union(seg((-19, y), (0, y + 9), 1.8, -1, 1) + seg((0, y + 9), (19, y), 1.8, -1, 1) for y in (-17, -9, -1, 7)))
    return Skin("stealth", "STEALTH", "sleek",
                "Faceted, low-observable. An octagonal hull with 45 degree corner cuts, a 2.5 mm bevelled "
                "base, a 3 mm bevelled lid and a chevron guard.",
                ("#2c2f2a", "#2c2f2a", "#2c2f2a"), env=env, deck=1.6, guard=g, top_ch=3.0)


SKINS = [breach, glitch, ring0, code_rain, honeypot, console, blade, terminal, waveform, monolith, airframe, jet, stealth]

"""Lifeline node v2: the shared FUNCTIONAL core every design uses. build123d, mm.
Frame: (0,0) = centre of the face (camera axis); z = 0 at the wall/ceiling, +z toward the room.

Parts (print orientation in brackets):
  plate      wall plate: twist-lock lugs, wall screws, cable grommet, accelerometer pocket (top face, nut traps below) [flat]
  back       back deck: UPS/battery board, ESP32 + LoRa bays, vents, deck-joint columns, keyholes for the lugs [upright]
  front      front deck: Pi 5 (+ Active Cooler, optional AI HAT+), cover pillars, floor pass-throughs, vents [upright]
  cover      functional face plate: camera (centre, heat-staked pins), LED ring + diffuser seat, fan socket + grille,
             speaker grille + clamp bosses, 2 mic ports, radar window seat + bracket bosses, OLED pocket + pin slot,
             sealed room-air sensor pocket [face-down]
  small parts: diffuser (translucent), radar_window (plain PLA/PETG, never CF), cam_plug (if no camera),
             spk_clamp, mic_clamp
  faceplate  decorative, per design (designs/*.py), printed face-up, clamped by the 4 cover screws.

Shell: octagon 150 across flats; walls 5 mm = 3 mm structural + 2 mm DECOR band that designs may carve.
Envelope: 152.4 x 152.4 x 101.6 mm (6 x 6 x 4 in): faceplates may rise to Z_MAX."""
import math
import sys
from pathlib import Path
from build123d import (Box, Cylinder, Cone, Pos, Rot, Part, Polygon, extrude, fillet, chamfer, Axis, export_stl)

CASE = next(p for p in (Path(__file__).resolve().parent.parent / d for d in ("Pi5-AI-HAT-Case", "case")) if (p / "pi5_aihat_case.py").exists())
sys.path.insert(0, str(CASE))
import pi5_aihat_case as m                                         # noqa: E402
from pi5_aihat_case import box, cz, INS_D, M3_CLR, M3_HEAD, HOLES   # noqa: E402

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# ---------------- envelope + shell ----------------
AF = 150.0                     # across flats
DECOR = 2.0                    # outer band designs may carve (walls keep >= 3 mm)
WALL = 3.0 + DECOR
EDGE_R = 3.0
FLOOR = 2.5
Z_MAX = 101.6                  # 4 in
ENVELOPE = 152.4               # 6 in
Z_PLATE1 = 6.0
Z_BACK0, Z_BACK1 = Z_PLATE1, 38.0          # +6: PiPower 5 board on tall standoffs over its 2-cell 18650 pack
Z_FRONT0 = Z_BACK1
Z_FRONT1 = Z_FRONT0 + 40.0
COVER_T = 3.0
Z_TOP = Z_FRONT1 + COVER_T     # 75.0: faceplates sit on this face

# ---------------- Pi stack (eccentric so the camera lands beside the fan) ----------------
P0 = (-64.0, -28.0)            # Pi PCB corner
PI_Z = Z_FRONT0 + FLOOR + 4.0
PCB_TOP = PI_Z + m.PCB_T
HAT_TOP = PCB_TOP + m.STACK + m.HAT_T          # stack height reserved even without the HAT
FAN_C = (P0[0] + 17.5, P0[1] + 28.0)          # (-46.5, 0): over the Hailo if fitted, over the cooler if not

# ---------------- fasteners ----------------
DECK_SCREWS = [(40.0, 52.0), (0.0, -63.0), (63.0, 0.0)]       # (40,52): clear of the battery pack
SDR = dict(x=(-40.0, 45.0), y=(-44.0, -18.0), h=16.0, cable=(66.5, -31.0, 20.0))  # Adafruit SDR stick #1497 (MC 656639) [u: measure]                 # front deck floor -> back deck (from inside)
PILLARS = [(sx * 48.0, sy * 48.0) for sx in (-1, 1) for sy in (-1, 1)]  # faceplate + cover -> front deck, M3 x 12
LUG_ANG, LUG_R = (30.0, 150.0, 250.0), 60.0     # outer ring: clear of the battery pack and the SDR bay

# ---------------- face layout (x, y on the face) ----------------
CAMERA = False                 # Rafael 2026-11-07 ~3 PM: camera OUT. Centre = full glowing status disc (LED ring behind it)
CAM = dict(w=25.0, d=23.86, pcb=1.12, lens_proud=7.4, hole=14.0, lens_y=9.5)
CAM_HOLES = [(-10.5, -7.5), (10.5, -7.5), (-10.5, 5.0), (10.5, 5.0)]   # Camera Module 3, from the lens [u: verify]
LED = dict(od=44.5, id=31.7, t=6.7)                                       # 16 x NeoPixel (MC #655358)
PCB_FRONT = Z_FRONT1 - LED["t"]                                            # camera PCB right behind the ring
SPK = dict(c=(47.5, 0.0), d=40.0, grille_r=16.0, boss=[(47.5, 25.0), (47.5, -25.0)])
MICS = [(-22.0, -55.0), (22.0, -55.0)]                                     # 44 mm apart, away from fan + speaker
MIC_BOARD = (17.5, 14.5)                                                   # fits SPH0645 16.7x12.7 or INMP441 d14
RADAR = dict(c=(0.0, 46.0), open=(40.0, 26.0), insert=(44.0, 30.0), t=0.9, boss=[(-27.0, 46.0), (27.0, 46.0)])   # 0.9 mm plain PLA/PETG window
# Hosyond 0.91" 128x32 SSD1306 (LCDwiki MC091GX): PCB 38 x 12, no holes, glass 30 x 11.5 at x 5..35 from the header end,
# active 22.38 x 5.58 at x 7.10..29.48 / y 2.43..8.01, straight pins out the back at x 1.5. Mounted from INSIDE behind a skin.
OLED = dict(c=(0.0, -38.0), pcb=(38.4, 12.4), skin=1.2, stack=2.8, win=((6.6, 30.0), (1.9, 8.5)), clamp=[(5.0, 10.5), (5.0, -10.5)])
ENV = dict(x=(-70.0, -47.0), y=(-17.0, 17.0))      # sealed room-air pocket in the BACK deck, behind the west rim vents


M25_NUT_AF, M25_NUT_T = 5.3, 2.4   # M2.5 hex nut trap (nut 5.0 AF x 2.0) for the Pi + UPS board holes (2.7 mm, M2.5 only)


def nut_trap(x, y, z_top):
    """Hex pocket opening at z_top (drop the M2.5 nut in, board on top, screw M2.5 x 6 down from above) + screw hole below."""
    r = M25_NUT_AF / 2 / math.cos(math.pi / 6)
    hexa = Pos(x, y, z_top - M25_NUT_T) * extrude(Polygon(*[(r * math.cos(math.radians(30 + 60 * k)), r * math.sin(math.radians(30 + 60 * k))) for k in range(6)], align=None), M25_NUT_T + 1)
    return hexa + cz(x, y, 1.45, z_top - M25_NUT_T - 4.5, z_top)


def octagon(inset, z0, z1, af=AF):
    a = af / 2 - inset
    rc = a / math.cos(math.pi / 8)
    pts = [(rc * math.cos(math.radians(22.5 + 45 * k)), rc * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    s = Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), z1 - z0)
    r = EDGE_R - inset if EDGE_R - inset > 0.4 else 0
    return fillet(s.edges().filter_by(Axis.Z), r) if r else s


def decor_band(z0, z1):
    """The outer 2 mm a design may carve into (deck sides)."""
    return octagon(0, z0, z1) - octagon(DECOR, z0 - 1, z1 + 1)


def pi_xy(x, y):
    return P0[0] + x, P0[1] + y


def ring_slots(ang0, ang1, z0, z1, r_in, r_out, w=2.2, pitch_deg=4.0):
    s, a = Part(), ang0
    while a <= ang1:
        t, rm = math.radians(a), (r_in + r_out) / 2
        s += Pos(rm * math.cos(t), rm * math.sin(t), (z0 + z1) / 2) * Rot(0, 0, a) * Box(r_out - r_in, w, z1 - z0)
        a += pitch_deg
    return s


def hex_holes(cx, cy, r_field, d, pitch, z0, z1):
    h = Part()
    n = int(r_field / pitch) + 2
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            x, y = cx + i * pitch + (pitch / 2 if j % 2 else 0), cy + j * pitch * 0.866
            if math.hypot(x - cx, y - cy) <= r_field:
                h += cz(x, y, d / 2, z0, z1)
    return h


# ================= WALL PLATE =================
ACC = dict(board=(21.5, 16.5), holes=[(-7.6, 0.0), (7.6, 0.0)], c=(-34.0, 28.0))   # MPU-6050 GY-521 (Rafael's kit) [u: hole spots]   # GY-521/GY-291 class [u: holes]


def make_plate():
    p = cz(0, 0, 66.0, 0, Z_PLATE1)
    p = chamfer(p.edges().group_by(Axis.Z)[-1], 1.0)
    p -= cz(0, 0, 7.0, -1, Z_PLATE1 + 1)                                   # cable grommet
    for a in (0.0, 90.0, 180.0, 270.0):                                    # wall screws (#8), countersunk
        x, y = 32 * math.cos(math.radians(a)), 32 * math.sin(math.radians(a))
        p -= cz(x, y, 2.3, -1, Z_PLATE1 + 1) + Pos(x, y, Z_PLATE1 - 2.0) * Cone(2.3, 4.6, 2.01, align=None)
    # accelerometer: pocket in the TOP face, screwed hard to the plate (plate is screwed to the wall) with M3 + nuts
    ax, ay = ACC["c"]
    bw, bh = ACC["board"]
    p -= box(ax - bw / 2 - 0.4, ax + bw / 2 + 0.4, ay - bh / 2 - 0.4, ay + bh / 2 + 0.4, Z_PLATE1 - 1.6, Z_PLATE1 + 1)
    for hx, hy in ACC["holes"]:
        x, y = ax + hx, ay + hy
        p -= cz(x, y, M3_CLR / 2, -1, Z_PLATE1 + 1)
        p -= Pos(x, y, 0) * extrude(Polygon(*[(3.2 * math.cos(math.radians(60 * k)), 3.2 * math.sin(math.radians(60 * k))) for k in range(6)], align=None), 2.6)
    for a in LUG_ANG:                                                      # twist-lock lugs (PLA-CF: 12 x 6 posts)
        lug = box(LUG_R - 3, LUG_R + 3, -6, 6, Z_PLATE1, Z_PLATE1 + FLOOR + 0.4)
        lip = box(LUG_R - 3, LUG_R + 6, -6, 6, Z_PLATE1 + FLOOR + 0.4, Z_PLATE1 + FLOOR + 3.4)
        lip = chamfer(lip.edges().filter_by(Axis.Y).group_by(Axis.Z)[0].group_by(Axis.X)[-1], 2.9)
        p += Rot(0, 0, a) * (lug + lip)
    return p


# ================= BACK DECK =================
BATT = dict(l=42.0, w=78.0, h=21.0, c=(0.0, 26.0))   # SunFounder 7.4 V 2 x 18650 pack, long axis along y, between the standoffs [u: measure]
UPS_DY = 12.0                                                               # board shifted +y to free the SDR bay
UPS_HOLES = [(sx * 29.0, sy * 24.5 + UPS_DY) for sx in (-1, 1) for sy in (-1, 1)]   # Pi-HAT pattern [u: check the UPS board]


def keyhole(a, twist=20.0):
    k = Rot(0, 0, a) * box(LUG_R - 3.6, LUG_R + 6.6, -6.6, 6.6, Z_BACK0 - 1, Z_BACK0 + FLOOR + 1)
    for d in range(0, int(twist) + 1, 3):
        k += Rot(0, 0, a - d) * box(LUG_R - 3.4, LUG_R + 3.4, -6.4, 6.4, Z_BACK0 - 1, Z_BACK0 + FLOOR + 1)
    return k


UPS_Z = Z_BACK0 + FLOOR + BATT["h"] + 1.0     # PiPower 5 board underside


def make_back():
    z0, z1 = Z_BACK0, Z_BACK1
    b = octagon(0, z0, z1) - octagon(WALL, z0 + FLOOR, z1 + 1)
    b -= cz(0, 0, 7.0, z0 - 1, z0 + FLOOR + 1)                             # cable in
    ax, ay = ACC["c"]
    b -= box(ax - 10, ax + 10, ay - 8, ay + 8, z0 - 1, z0 + FLOOR + 1)    # accelerometer window (wires up)
    for a in LUG_ANG:
        b -= keyhole(a)
    for x, y in UPS_HOLES:                                                 # PiPower 5 above the pack: M2.5 x 6 + nut traps
        b += cz(x, y, 4.0, z0, UPS_Z)
        b -= nut_trap(x, y, UPS_Z)
    bx, by = BATT["c"]                                                     # battery cradle: 5 mm walls + zip-tie slots
    bl, bw = BATT["l"] / 2 + 0.5, BATT["w"] / 2 + 0.5
    cr = box(bx - bl - 1.6, bx + bl + 1.6, by - bw - 1.6, by + bw + 1.6, z0, z0 + FLOOR + 5.0) - box(bx - bl, bx + bl, by - bw, by + bw, z0 + FLOOR, z0 + 40)
    for x in (bx - 20, bx + 20):
        cr -= box(x - 2.5, x + 2.5, by - bw - 3, by + bw + 3, z0 + FLOOR + 1.0, z0 + FLOOR + 3.0)
    b += cr
    for x, y in DECK_SCREWS:
        b += cz(x, y, 5.0, z0, z1)
        b -= m.ins_z(x, y, z1, 7.0)
    a_in, a_out = AF / 2 - WALL - 1, AF / 2 / math.cos(math.radians(16)) + 1
    b -= ring_slots(-14, 14, z0 + 7, z1 - 4, a_in, a_out)                  # battery-bay vents (east)
    # RTL-SDR stick (alert receiver): cradle rails + strap slots; antenna OUT through an SMA bulkhead (never inside CF)
    sx0, sx1, sy0, sy1 = SDR["x"][0], SDR["x"][1], SDR["y"][0], SDR["y"][1]
    for y0, y1 in ((sy0 - 1.6, sy0), (sy1, sy1 + 1.6)):
        b += box(sx0, sx1, y0, y1, z0, z0 + FLOOR + 6.0)
        for x in (sx0 + 15, sx1 - 15):
            b -= box(x - 2.5, x + 2.5, y0 - 1, y1 + 1, z0 + FLOOR + 1.0, z0 + FLOOR + 3.0)   # zip-tie / velcro slot
    bx, by, bz = SDR["cable"]
    b -= Pos(bx, by, bz) * Rot(0, 90, 0) * Cylinder(3.5, 14)                # 7 mm: antenna lead + MCX plug pass through
    b -= ring_slots(-50, -34, z0 + 7, z1 - 4, a_in, a_out)                 # air over the SDR stick (it runs warm)
    # room-air sensor pocket (SCD41 / CO / temp): walled off from the inside, open to the room through the west vents
    ex0, ex1 = ENV["x"]
    ey0, ey1 = ENV["y"]
    b += box(ex1, ex1 + 2.0, ey0 - 2, ey1 + 2, z0, z1) + box(ex0, ex1 + 2.0, ey0 - 2, ey0, z0, z1) + box(ex0, ex1 + 2.0, ey1, ey1 + 2, z0, z1)
    b += box(ex0, ex1 + 2.0, ey0 - 2, ey1 + 2, z1 - 2.0, z1)               # lid over the pocket (front-deck floor sits on it)
    b -= box(ex1 - 1, ex1 + 3, -3, 3, z0 + FLOOR + 2, z0 + FLOOR + 6)      # wire exit (seal with tape)
    b -= ring_slots(166, 194, z0 + 6, z1 - 5, a_in, a_out)                 # vents into the pocket
    return b


# ================= FRONT DECK =================
def make_front():
    z0, z1 = Z_FRONT0, Z_FRONT1
    f = octagon(0, z0, z1) - octagon(WALL, z0 + FLOOR, z1 + 1)
    for x, y in DECK_SCREWS:
        f += cz(x, y, 5.0, z0, z0 + FLOOR + 3.0)
        f -= cz(x, y, M3_CLR / 2, z0 - 1, z0 + 10) + cz(x, y, M3_HEAD / 2, z0 + 3.0, z0 + 10)
    for x, y in PILLARS:
        f += cz(x, y, 5.0, z0, z1)
        f -= m.ins_z(x, y, z1, 7.0)
    for hx, hy in HOLES:
        x, y = pi_xy(hx, hy)
        f += cz(x, y, 5.5, z0, PI_Z - 0.8) + cz(x, y, 4.3, z0, PI_Z)      # Pi 5: M2.5 x 6 nylon + nut traps
        f -= nut_trap(x, y, PI_Z)
    f -= box(-62, -48, -42, -34, z0 - 1, z0 + FLOOR + 1)                  # UPS -> Pi USB-C lead
    f -= box(-22, 2, 36, 44, z0 - 1, z0 + FLOOR + 1)                      # GPIO wires down (ESP32, LoRa, accel)
    f -= box(30, 54, 22, 30, z0 - 1, z0 + FLOOR + 1)                      # spare pass-through
    for x in range(-50, 16, 5):
        f -= box(x - 1.1, x + 1.1, -14, 14, z0 - 1, z0 + FLOOR + 1)       # floor vents under the Pi
    a_in, a_out = AF / 2 - WALL - 1, AF / 2 / math.cos(math.radians(25)) + 1
    f -= ring_slots(146, 214, z0 + 8, z1 - 5, a_in, a_out)                # exhaust beside the fan
    return f


# ================= COVER (functional face; prints face-down) =================
def ring_pts(r, n, a0=0.0):
    return [(r * math.cos(math.radians(a0 + 360 * k / n)), r * math.sin(math.radians(a0 + 360 * k / n))) for k in range(n)]


def make_cover():
    z0, z1 = Z_FRONT1, Z_TOP
    c = octagon(0, z0, z1)
    for x, y in PILLARS:
        c -= cz(x, y, M3_CLR / 2, z0 - 1, z1 + 1)
    if CAMERA:   # lens hole + PCB on 4 posts with 1.9 mm pins (heat-stake), translucent ring around it
        c -= cz(0, 0, CAM["hole"] / 2, z0 - 1, z1 + 1)
        for x, y in CAM_HOLES:
            c += cz(x, y, 2.2, PCB_FRONT, z0) + cz(x, y, 0.95, PCB_FRONT - CAM["pcb"] - 1.6, PCB_FRONT)
        c -= cz(0, 0, LED["od"] / 2, z0 - 1, z1 + 1) - cz(0, 0, LED["id"] / 2, z0 - 2, z1 + 2)
        c -= cz(0, 0, LED["od"] / 2 + 2.0, z0 - 1, z0 + 1.0) - cz(0, 0, LED["id"] / 2 - 1.5, z0 - 2, z0 + 2)
    else:        # full status disc: diffuser fills the whole centre, flange behind, LED ring presses it in
        c -= cz(0, 0, LED["od"] / 2, z0 - 1, z1 + 1)
        c -= cz(0, 0, LED["od"] / 2 + 2.0, z0 - 1, z0 + 1.0)
    c += cz(0, 0, LED["od"] / 2 + 4.0, z0 - 2.0, z0) - cz(0, 0, LED["od"] / 2 + 2.3, z0 - 3, z0 + 1)      # ring locator
    # --- fan: press-fit socket (40.4 for a 40.0 frame) + hex intake grille ---
    fx, fy = FAN_C
    c += box(fx - 22.2, fx + 22.2, fy - 22.2, fy + 22.2, z0 - 4.0, z0) - box(fx - 20.2, fx + 20.2, fy - 20.2, fy + 20.2, z0 - 5, z0 + 1)
    c -= hex_holes(fx, fy, 17.5, 3.0, 4.6, z0 - 1, z1 + 1)
    # --- speaker: grille + rim seat + 2 clamp bosses ---
    sx, sy = SPK["c"]
    c -= hex_holes(sx, sy, SPK["grille_r"], 2.2, 3.4, z0 - 1, z1 + 1)
    c -= cz(sx, sy, SPK["d"] / 2 + 0.4, z0 - 1, z0 + 0.8) - cz(sx, sy, SPK["grille_r"] + 1.5, z0 - 2, z0 + 2)
    for x, y in SPK["boss"]:                                               # clamp bosses, inserts from below
        c += cz(x, y, 4.0, z0 - 10.0, z0)
        c -= cz(x, y, INS_D / 2, z0 - 10.5, z0 - 3.5)
    # --- mics: 3 x d1.0 ports each, board pocket (port side to the cover, foam gasket), clamp boss ---
    for mx, my in MICS:
        for dx, dy in ((0, 0), (1.3, 0), (-1.3, 0)):
            c -= cz(mx + dx, my + dy, 0.5, z0 - 1, z1 + 1)
        bw, bh = MIC_BOARD
        c += box(mx - bw / 2 - 2.5, mx + bw / 2 + 2.5, my - bh / 2 - 2.5, my + bh / 2 + 2.5, z0 - 3.0, z0) - \
            box(mx - bw / 2, mx + bw / 2, my - bh / 2, my + bh / 2, z0 - 4, z0 + 0.01)
    # --- radar: window (plain PLA/PETG insert seats from inside), 2 bracket bosses ---
    rx, ry = RADAR["c"]
    ow, oh = RADAR["open"]
    iw, ih = RADAR["insert"]
    c -= box(rx - ow / 2, rx + ow / 2, ry - oh / 2, ry + oh / 2, z0 - 1, z1 + 1)
    c -= box(rx - iw / 2 - 0.2, rx + iw / 2 + 0.2, ry - ih / 2 - 0.2, ry + ih / 2 + 0.2, z0 - 1, z0 + COVER_T - RADAR["t"])
    for x, y in RADAR["boss"]:
        c += cz(x, y, 4.0, z0 - 8.0, z0)
        c -= cz(x, y, INS_D / 2, z0 - 8.5, z0 - 1.5)
    # --- OLED from inside: 1.2 skin with a window over the active area, pocket + frame behind, clamp-bar bosses ---
    ox, oy = OLED["c"]
    pw, ph = OLED["pcb"]
    x0, y0 = ox - pw / 2 + 0.2, oy - ph / 2 + 0.2                          # board origin (header end, -x)
    zs = z1 - OLED["skin"]
    c += box(ox - pw / 2 - 2, ox + pw / 2 + 2, oy - ph / 2 - 2, oy + ph / 2 + 2, zs - OLED["stack"], z0)   # frame below the cover
    c -= box(ox - pw / 2, ox + pw / 2, oy - ph / 2, oy + ph / 2, zs - OLED["stack"] - 1, zs)
    (wx0, wx1), (wy0, wy1) = OLED["win"]
    c -= box(x0 + wx0, x0 + wx1, y0 + wy0, y0 + wy1, zs - 1, z1 + 1)
    c -= box(x0 + wx0 - 1.0, x0 + wx1 + 1.0, y0 + wy0 - 1.0, y0 + wy1 + 1.0, z1 - 0.4, z1 + 1)          # 45-ish bevel step
    for dx, dy in OLED["clamp"]:                                           # above/below the board: clear of the header end
        c += cz(ox + dx, oy + dy, 4.0, zs - OLED["stack"] - 6.0, z0)
        c -= cz(ox + dx, oy + dy, INS_D / 2, zs - OLED["stack"] - 6.5, zs - OLED["stack"] + 0.5)
    # --- HAT stops (only touch something if the AI HAT+ is fitted) ---
    for (hx, hy), r, rp in (((3.5, 3.5), 4.0, 3.0), ((3.5, 52.5), 3.5, 2.6)):
        x, y = pi_xy(hx, hy)
        c += cz(x, y, r, HAT_TOP + 0.8, z0) - cz(x, y, rp, HAT_TOP, HAT_TOP + 3.3)
    return c


# ================= small parts =================
def make_diffuser():          # translucent white/clear PLA or PETG; flush with the face, flange held by the LED ring
    d = cz(0, 0, LED["od"] / 2 - 0.15, Z_FRONT1 + 1.0, Z_TOP) + cz(0, 0, LED["od"] / 2 + 1.8, Z_FRONT1, Z_FRONT1 + 1.0)
    return d - cz(0, 0, LED["id"] / 2 + 0.15, Z_FRONT1 - 1, Z_TOP + 1) if CAMERA else d


def make_radar_window():      # plain PLA/PETG only (carbon fibre detunes/blocks 24 GHz)
    rx, ry = RADAR["c"]
    iw, ih = RADAR["insert"]
    return box(rx - iw / 2, rx + iw / 2, ry - ih / 2, ry + ih / 2, Z_FRONT1, Z_FRONT1 + RADAR["t"])


def make_oled_clamp():         # bar across the OLED back (2 x M3 into the cover bosses); pad touches the PCB, notch clears the header
    ox, oy = OLED["c"]
    zb = Z_TOP - OLED["skin"] - OLED["stack"] - 6.0
    c = box(ox + 1, ox + 9, oy - 14.5, oy + 14.5, zb - 3.0, zb) + box(ox - 4, ox + 14, oy - 5, oy + 5, zb, zb + 6.0 - 0.3)
    for dx, dy in OLED["clamp"]:
        c -= cz(ox + dx, oy + dy, M3_CLR / 2, zb - 4, zb + 1)
    return c


def make_cam_plug():          # if the camera is left out
    return cz(0, 0, CAM["hole"] / 2 - 0.15, Z_FRONT1, Z_TOP) + cz(0, 0, CAM["hole"] / 2 + 2.0, Z_FRONT1 - 1.2, Z_FRONT1)


def make_spk_clamp():          # ring under the boss ends; its lip reaches up and presses the speaker rim (prints lip-up)
    sx, sy = SPK["c"]
    c = cz(sx, sy, 22.0, 0, 2.5) - cz(sx, sy, 17.5, -1, 4)
    for x, y in SPK["boss"]:
        c += cz(x, y, 4.5, 0, 2.5)
        c -= cz(x, y, M3_CLR / 2, -1, 4)
    c += cz(sx, sy, 20.3, 2.5, 10.0) - cz(sx, sy, 18.3, 2, 11)            # lip: up to the rim back (Z_FRONT1 - 2.5)
    return Pos(0, 0, Z_FRONT1 - 12.5) * c


# ================= hardware proxy (for checks + the viewer) =================
def hardware(with_hat=True):
    hw = Pos(P0[0], P0[1], PI_Z - m.PI_Z) * m.hardware() if with_hat else Pos(P0[0], P0[1], 0) * box(0, 85, 0, 56, PI_Z, PCB_TOP)
    fx, fy = FAN_C
    hw += box(fx - 20, fx + 20, fy - 20, fy + 20, Z_FRONT1 - 10.0, Z_FRONT1)
    if CAMERA:
        cam = box(-CAM["w"] / 2, CAM["w"] / 2, -CAM["lens_y"], CAM["d"] - CAM["lens_y"], PCB_FRONT - CAM["pcb"], PCB_FRONT)
        for x, y in CAM_HOLES:
            cam -= cz(x, y, 1.1, PCB_FRONT - 2, PCB_FRONT + 1)
        hw += cam + cz(0, 0, 4.5, PCB_FRONT, PCB_FRONT + CAM["lens_proud"])
    hw += cz(0, 0, LED["od"] / 2, PCB_FRONT + 0.01, Z_FRONT1) - cz(0, 0, LED["id"] / 2, PCB_FRONT - 1, Z_FRONT1 + 1)
    sx, sy = SPK["c"]
    hw += cz(sx, sy, 20.0, Z_FRONT1 - 2.5, Z_FRONT1 - 0.01) + cz(sx, sy, 13.0, Z_FRONT1 - 16, Z_FRONT1 - 2.5)
    for mx, my in MICS:
        hw += box(mx - 8.35, mx + 8.35, my - 6.35, my + 6.35, Z_FRONT1 - 2.6, Z_FRONT1 - 1.0)
    ox, oy = OLED["c"]
    zs = Z_TOP - OLED["skin"]
    hw += box(ox - 19.0, ox + 19.0, oy - 6.0, oy + 6.0, zs - 2.6, zs - 0.01)                       # OLED glass + PCB
    hw += box(ox - 19.0, ox - 15.0, oy - 5.6, oy + 5.6, zs - 2.6 - 17.0, zs - 2.6)                 # spacer + 4 Dupont housings
    hw += box(-44, 44, -28 + UPS_DY, 28 + UPS_DY, UPS_Z, UPS_Z + 1.6) + box(-40, 40, -28 + UPS_DY, 28 + UPS_DY, UPS_Z + 1.6, UPS_Z + 5.0)  # PiPower 5 + parts
    bx, by = BATT["c"]
    hw += box(bx - BATT["l"] / 2, bx + BATT["l"] / 2, by - BATT["w"] / 2, by + BATT["w"] / 2, Z_BACK0 + FLOOR, Z_BACK0 + FLOOR + BATT["h"])  # 18650 pack
    hw += box(SDR["x"][0] + 0.5, SDR["x"][1] - 0.5, SDR["y"][0] + 0.3, SDR["y"][1] - 0.3, Z_BACK0 + FLOOR, Z_BACK0 + FLOOR + 15.0)   # RTL-SDR
    ax, ay = ACC["c"]
    hw += box(ax - 10.75, ax + 10.75, ay - 8.25, ay + 8.25, Z_PLATE1 - 1.6, Z_PLATE1)          # accelerometer PCB
    return hw


CORE = dict(plate=make_plate, back=make_back, front=make_front, cover=make_cover, diffuser=make_diffuser,
            radar_window=make_radar_window, cam_plug=make_cam_plug, spk_clamp=make_spk_clamp, oled_clamp=make_oled_clamp)
PRINT_ORIENT = dict(plate="up", back="up", front="up", cover="flip", diffuser="flip", radar_window="up",
                    cam_plug="flip", spk_clamp="up", oled_clamp="up")

if __name__ == "__main__":
    built = {n: f() for n, f in CORE.items()}
    for n, p in built.items():
        bb = p.bounding_box()
        print(f"{n:12} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f}  z {bb.min.Z:5.1f}..{bb.max.Z:5.1f}  {p.volume/1000:6.1f} cm3  valid {p.is_valid}", flush=True)
    hw = hardware()
    bad = 0
    for n in ("plate", "back", "front", "cover", "spk_clamp", "oled_clamp"):
        v = (built[n] & hw).volume
        print(f"hw x {n}: {v:.3f}"); bad += v > 0.001
    names = [n for n in built if n != "cam_plug"]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (built[a] & built[b]).volume
            if v > 0.001:
                print(f"OVERLAP {a} x {b}: {v:.3f}"); bad += 1
    print("problems:", bad)
    for n, p in built.items():
        export_stl(p, str(OUT / f"core_{n}.stl"), tolerance=0.02, angular_tolerance=0.1)
    export_stl(hw, str(OUT / "core_hardware.stl"), tolerance=0.05)

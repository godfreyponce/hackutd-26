"""Pi 5 + AI HAT+ (26T) modular case. build123d. All mm. Frame: see PLAN.md.
Run: python pi5_aihat_case.py  -> STEP/STL per part + plate 3MF in ./out
"""
from pathlib import Path
from build123d import (Box, Cylinder, Cone, Pos, Rot, Part, fillet, chamfer, Axis, Ellipse, Text, extrude,
                       export_stl, export_step)

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# ---------- measured / sourced parameters (edit after measuring the real parts) ----------
PCB_T = 1.6            # Pi PCB thickness (drawing ~1.4-1.6, worst case)
STACK = 16.0           # HAT spacer length (HAT+ spec)
HAT_T = 1.6
PI_Z = 4.0             # Pi underside above floor (room for kit screw heads / nuts + cooler pins)
PCB_TOP = PI_Z + PCB_T
HAT_TOP = PCB_TOP + STACK + HAT_T
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]
FAN_C = (27.0, 28.0)   # fan centre: covers Hailo-8 (x 22.5-39.5, y 18-35), clears GPIO + camera notch
FAN_P = 16.0           # half of 32 mm hole pattern

# ---------- printing / fastener tolerances ----------
# Tuned for a Bambu P1S, 0.4 nozzle: printed holes come out ~0.1-0.2 small, so clearances are sized to the
# small end. Insert hole = insert OD - ~0.6 (for 4.6-4.7 OD M3 inserts); lead-in chamfer keeps them straight.
INS_D, M3_CLR, M3_HEAD = 4.0, 3.5, 6.6   # insert hole, M3 clearance (prints ~3.3-3.4), head counterbore (pan/socket/button)
M3_CLR_SIDE = 3.6                         # sideways M3 holes: bridged tops sag ~0.2
WALL, FLOOR = 2.0, 2.0
TOWER_R = 5.0          # 3.0 mm of plastic around every insert hole

# ---------- envelope ----------
IX0, IX1, IY0, IY1 = -2.5, 85.6, -2.4, 57.5      # inner cavity
OX0, OX1, OY0, OY1 = IX0 - WALL, 88.0, IY0 - WALL, IY1 + WALL  # right wall ends flush with port faces (x=88)
SPLIT = 24.5                                     # base/lid split, above HAT top (23.2)
PLATE_Z0 = HAT_TOP + 9.0                         # lid plate underside: header pins + FFC bend room
LID_TOP = PLATE_Z0 + 2.4
TOWERS = [(-4.3, -4.6), (87.6, -4.6), (-4.3, 60.6), (87.6, 60.6)]  # >=0.28 mm from a square PCB corner (1.4 from the real r3 corner)


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cz(x, y, r, z0, z1):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)


def cx(y, z, r, x0, x1):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def ins_z(x, y, top, depth):  # vertical insert hole opening at z=top, 0.5 mm 45-degree lead-in
    return cz(x, y, INS_D / 2, top - depth, top + 1) + Pos(x, y, top - 0.25) * Cone(INS_D / 2, INS_D / 2 + 0.5, 0.5)


def outline(z0, z1, bottom_ch=0.0, top_ch=0.0):  # chamfer the outer bed-face perimeter (also kills elephant foot)
    b = box(OX0, OX1, OY0, OY1, z0, z1)
    b = fillet(b.edges().filter_by(Axis.Z), 2.0)
    for x, y in TOWERS:
        b += cz(x, y, TOWER_R, z0, z1)
    if bottom_ch:
        b = chamfer(b.edges().group_by(Axis.Z)[0], bottom_ch)
    if top_ch:
        b = chamfer(b.edges().group_by(Axis.Z)[-1], top_ch)
    return b


# ---------- HackUTD 2026 "Zero Day" theme ----------
FONT = "Consolas"            # monospace, slashed zero
VENT_BITS = "0110000" + "1" + "1000100"   # back-wall vents spell ASCII '0' | 'D' (0-day): 1 = tall slot, 0 = short
ENGRAVE = 0.6                # 3 layers at 0.2; lid plate keeps 1.8 under the letters (non-structural zone)


def engraving(top=None):  # lid top, strip between fan and camera bracket, reads from the USB/Ethernet side
    top = LID_TOP if top is None else top
    t = Pos(0, 0, 0) * extrude(Text("> ZERO_DAY_", font_size=4.6, font=FONT), ENGRAVE + 1)
    t += Pos(0, -6.2, 0) * extrude(Text("HACKUTD 2026", font_size=3.6, font=FONT), ENGRAVE + 1)
    return Pos(58.5, 32.5, top - ENGRAVE) * Rot(0, 0, 90) * t


# ---------- style hooks (concepts.py): a skin may only ADD outside the functional outline and CUT into what it added ----------
KEEPOUT_Z = SPLIT + 3.0
WORLD = (-99, 199, -99, 199)


def keepouts():  # plug + finger access in front of every I/O face: no styling may enter these
    return (box(OX1, OX1 + 60, -1.5, 57.0, -FLOOR - 1, KEEPOUT_Z)      # USB/Ethernet + plug overmolds
            + box(0.0, 50.0, OY0 - 60, OY0, -FLOOR - 1, KEEPOUT_Z)      # USB-C + 2x micro-HDMI overmolds
            + box(OX0 - 60, OX0, 9.0, 41.0, -FLOOR - 1, KEEPOUT_Z))     # LED, power button, microSD + fingers


def deck_protect(text=True):  # lid-top areas that must stay flat: fan seat, camera bracket, screw/insert rims, slots
    p = box(FAN_C[0] - 21, FAN_C[0] + 21, FAN_C[1] - 21, FAN_C[1] + 21, -99, 199) + box(66.0, 80.0, 1.0, 57.0, -99, 199)
    p += box(5.0, 60.0, 48.4, 56.6, -99, 199) + box(46.5, 58.5, -0.5, 16.5, -99, 199)
    for x, y in TOWERS:
        p += cz(x, y, 6.0, -99, 199)
    return p + box(54.5, 67.5, 17.5, 48.0, -99, 199) if text else p


def _skin_add(part, skin, z0, z1):
    if skin and skin.env:
        part += (skin.env() & box(*WORLD, z0, z1)) - keepouts()
    if skin and skin.side_cut:
        part -= skin.side_cut() - outline(z0 - 1, z1 + 1)   # cuts never touch the functional walls
    return part


# ================= BASE =================
def make_base(skin=None):
    b = _skin_add(outline(-FLOOR, SPLIT, bottom_ch=0.8), skin, -FLOOR, SPLIT)
    b -= box(IX0, IX1, IY0, IY1, 0, SPLIT + 1)
    for x, y in TOWERS:  # re-add towers inside the cavity corners, then insert holes
        b += cz(x, y, TOWER_R, 0, SPLIT)          # inside the cavity only, so the bed chamfer survives
        b -= ins_z(x, y, SPLIT, 7.0)
    for x, y in HOLES:   # Pi bosses: pocket swallows the HAT-kit screw head or nut under the Pi
        b += cz(x, y, 5.5, 0, PI_Z - 0.8) + cz(x, y, 4.3, 0, PI_Z)   # wide foot; top collar stays inside the Pi's hole keep-out
        b -= cz(x, y, 3.3, PI_Z - 3.5, PI_Z + 1)   # d6.6 x 3.5: M2.5 head or nut (5.8 across corners)
        b -= cz(x, y, 1.5, -FLOOR - 1, PI_Z)
    # front: one I/O window for USB-C + 2x micro-HDMI (+ UART) so any cable overmold fits
    b -= box(4.5, 46.0, OY0 - 60, IY0 + 1, PCB_TOP - 1.0, PCB_TOP + 7.8)
    # right: open-top notches, ports flush with outer face; stack drops in vertically
    for y0, y1 in [(1.45, 18.95), (21.8, 36.4), (39.7, 54.3)]:
        b -= box(IX1 - 1, OX1 + 60, y0, y1, PCB_TOP - 0.6, SPLIT + 1)
    # left: microSD window (underside), power button, LED light hole
    b -= box(OX0 - 60, IX0 + 1, 20.9, 36.9, 0.6, PI_Z + 1.0)
    b -= cx(18.4, PCB_TOP + 1.2, 2.25, OX0 - 60, IX0 + 1)
    b -= cx(13.3, PCB_TOP + 1.0, 1.25, OX0 - 60, IX0 + 1)
    # vents: back wall, left wall (away from ports), floor under the board
    if skin and skin.vents:   # skin replaces the wall vents (through-cuts confined to the vent zones)
        b -= skin.vents() & (box(6.0, 82.0, IY1 - 1, OY1 + 60, 4.0, 21.0) + box(OX0 - 60, IX0 + 1, 41.0, 55.0, 6.0, 21.0))
    else:
        for x, bit in zip(range(10, 81, 5), VENT_BITS):
            b -= box(x - 1.1, x + 1.1, IY1 - 1, OY1 + 60, 6.0 if bit == "1" else 13.0, 21.0)
        for y in (41, 45, 49, 53):
            b -= box(OX0 - 60, IX0 + 1, y - 1.1, y + 1.1, 8.0, 21.0)
    for x in range(12, 77, 5):
        b -= box(x - 1.2, x + 1.2, 15.0, 41.0, -FLOOR - 1, 1)
    return b


# ================= LID =================
LID_INS = [(73.0, 13.0), (73.0, 45.0)]  # camera-bracket inserts
FAN_INS = [(FAN_C[0] + sx * FAN_P, FAN_C[1] + sy * FAN_P) for sx in (-1, 1) for sy in (-1, 1)]


def make_lid(skin=None):
    top = LID_TOP + (skin.deck if skin else 0.0)   # optional deck on top of the 2.4 plate (styling depth)
    l = _skin_add(outline(SPLIT, top, top_ch=skin.top_ch if skin else 0.6), skin, SPLIT, top)
    l -= box(IX0, IX1, IY0, IY1, SPLIT - 1, PLATE_Z0)
    for x, y in TOWERS:
        l += cz(x, y, TOWER_R, SPLIT, PLATE_Z0)
        l -= cz(x, y, M3_CLR / 2, SPLIT - 1, top + 1)
        l -= cz(x, y, M3_HEAD / 2, SPLIT + 4.5, top + 1)   # M3x10 -> ~5.5 mm into insert
    l -= cz(*FAN_C, 18.5, PLATE_Z0 - 1, top + 1)           # fan outlet (= blade diameter; keeps >=2 mm bars to the slots)
    for x, y in FAN_INS + LID_INS:
        l += cz(x, y, 5.0, PLATE_Z0 - 5.6, PLATE_Z0)
        l -= ins_z(x, y, top, 7.4)
    # stack stops, 0.8 mm above the HAT (stack-height tolerance): front posts pocketed for the top screw heads,
    # rear rib along the HAT's back edge, 0.85 mm behind the dupont housings
    for x, y in HOLES[:2]:
        l += cz(x, y, 4.5, HAT_TOP + 0.8, PLATE_Z0) - cz(x, y, 3.0, HAT_TOP, HAT_TOP + 3.3)
    l += box(0.5, 64.5, 55.9, IY1, HAT_TOP + 0.8, PLATE_Z0)
    # slots last, full depth, so no boss or post can narrow them
    l -= box(6.0, 59.0, 49.4, 55.6, SPLIT - 2, top + 1)    # GPIO pass-through: 2x20 dupont row + 1 mm
    l -= box(47.5, 57.5, 0.5, 15.5, SPLIT - 2, top + 1)    # camera ribbon slot over HAT notch
    text = skin.text if skin else True
    if skin and skin.deck_cut:   # recesses only inside the deck: the 2.4 plate underneath is never thinned
        l -= (skin.deck_cut(top) & box(*WORLD, LID_TOP, top + 1)) - deck_protect(text)
    if text:
        l -= engraving(top)
    return l


# ================= FAN GUARD =================
def make_guard():  # the grille is a slashed zero: Zero Day
    g = fillet(Box(40, 40, 2).edges().filter_by(Axis.Z), 3.0) - Cylinder(18.5, 3)
    zero = extrude(Ellipse(9.0, 14.0), 1, both=True) - extrude(Ellipse(7.0, 12.0), 2, both=True)   # 2.0 mm stroke
    slash = Rot(0, 0, 62) * Box(37.5, 2.4, 2)
    g += Rot(0, 0, 90) * (zero + slash)   # glyph "up" = case -x, same reading direction as the lid text
    for sx in (-1, 1):
        for sy in (-1, 1):
            g -= Pos(sx * FAN_P, sy * FAN_P) * Cylinder(M3_CLR / 2, 3)
    return Pos(0, 0, 1) * g


# ================= CAMERA (local frame: PCB in x/z, lens toward -y, pivot at y 2.5 z 12) =================
PIV_Y, PIV_Z = 2.5, 12.0


def make_cradle():
    c = Part()
    for s in (-1, 1):
        x0, x1 = sorted((s * 11.3, s * 15.5))
        c += box(x0, x1, -2.0, 6.5, -2.0, 23.9)   # front lip 1.8 thick, bottom stop 2.0
        bx0, bx1 = sorted((s * 15.5, s * 22.5))  # 7 mm boss: 5.7 insert + melt room
        boss = cx(PIV_Y, PIV_Z, 5.0, bx0, bx1) - box(bx0 - 1, bx1 + 1, -9, -2.0, 0, 30)   # flat on the print-bed face
        c += boss - cx(PIV_Y, PIV_Z, INS_D / 2, bx0 - 0.01, bx1 + 0.01)
    c += box(-15.5, 15.5, 4.5, 6.5, 13.0, 23.9)          # back bridge, high enough to clear the rear connector
    c -= box(-12.8, 12.8, -0.215, 1.335, 0, 30)          # PCB groove 25.6 x 1.55 for 25.0 x 1.12: prints ~1.4, slides
    return c


def make_bracket():
    k = box(-27.0, 27.0, -3, 9, -7, -4)
    for s in (-1, 1):
        x0, x1 = sorted((s * 23.0, s * 27.0))  # 0.5 mm gap each side; screw tension closes it = tilt friction
        k += box(x0, x1, -1.5, 6.5, -4, PIV_Z) + cx(PIV_Y, PIV_Z, 4.0, x0, x1)
        k -= cx(PIV_Y, PIV_Z, M3_CLR_SIDE / 2, x0 - 1, x1 + 1)
        k -= cz(s * 16.0, 3.0, M3_CLR / 2, -8, -3)
    return k


# ---------- simplified hardware for interference checks ----------
def hardware():
    h = box(0, 85, 0, 56, PI_Z, PCB_TOP)
    h += box(0, 65, 0, 56.5, PCB_TOP + STACK, HAT_TOP) - box(47.5, 57.5, 0, 16, 0, 60)
    h += box(66.2, 88, 2.2, 18.2, PCB_TOP, PCB_TOP + 13.9)                      # Ethernet
    for yc in (29.1, 47.0):
        h += box(68, 88, yc - 6.55, yc + 6.55, PCB_TOP, PCB_TOP + 16.4)          # USB stacks
    h += box(6.9, 15.5, -1.5, 6, PCB_TOP, PCB_TOP + 3.3)                        # USB-C
    for xc in (25.8, 39.2):
        h += box(xc - 3.25, xc + 3.25, -1.9, 6, PCB_TOP, PCB_TOP + 3.5)          # micro-HDMI
    h += box(-2.25, 12, 22.6, 35.2, PI_Z - 1.9, PI_Z)                           # microSD + card
    h += box(7.1, 57.9, 50, 55, HAT_TOP, HAT_TOP + 7)                           # header pins above HAT
    for x, y in HOLES:
        h += cz(x, y, 2.4, PI_Z - 2.0, PI_Z) + cz(x, y, 2.4, HAT_TOP, HAT_TOP + 2.0)  # M2.5 heads
    return h


def place_camera(part):
    # local -> case: local x -> case y, local -y (front) -> case +x, base plate underside on lid top
    return Pos(76.0, 29.0, LID_TOP + 7.0) * Rot(0, 0, 90) * part


if __name__ == "__main__":
    parts = {"base": make_base(), "lid": make_lid(), "fan_guard": make_guard(),
             "cam_bracket": make_bracket(), "cam_cradle": make_cradle()}
    hw = hardware()
    for n in ("base", "lid"):
        print(f"interference {n}: {(parts[n] & hw).volume:.3f} mm^3")
    cam = place_camera(parts["cam_bracket"]) + place_camera(parts["cam_cradle"])
    print(f"interference camera/lid: {(cam & parts['lid']).volume:.3f} mm^3")
    print(f"interference cradle/bracket: {(parts['cam_cradle'] & parts['cam_bracket']).volume:.3f} mm^3")
    for n, p in parts.items():
        bb = p.bounding_box()
        print(f"{n}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  vol {p.volume/1000:.1f} cm^3")
        export_step(p, str(OUT / f"{n}.step"))
        export_stl(p, str(OUT / f"{n}.stl"), tolerance=0.02, angular_tolerance=0.1)
    asm = parts["base"] + Pos(0, 0, 0) * parts["lid"] + Pos(*FAN_C, LID_TOP + 10) * parts["fan_guard"] + cam
    export_stl(asm, str(OUT / "_assembly_preview.stl"), tolerance=0.05)
    export_stl(hw, str(OUT / "_hardware_ghost.stl"), tolerance=0.05)

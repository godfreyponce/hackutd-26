"""Home monitor node, SINGLE-LAYER case (v4, 2026-11-07). Two printed parts: body + lid. Pi 5 + AI HAT+ 26T (HAT kit hardware).
  body  flat bottom (sticky strips). Pi 5 + Active Cooler on 4 posts (M2.5 nut traps) with its port edge AGAINST the -y
        wall (ports reach the outside like the first case): USB-C power opening + micro-HDMI opening, each centred on
        its port. 40 mm fan on the +y wall: 4 counterbored M3 holes (32 mm pattern, the fan's own M3x16 + nuts), corner
        guides, slot grille. Air fins (slots) across both side walls. 4 corner columns with M3 inserts for the lid.
  lid   flat, 4 x M3. Camera Module 3 slide-in holder underneath (no screws): rails from the test coupon, slot 0.5 mm
        wider (26.1); board slides in from the cable end to a stop; only the lens shows through a 12.5 mm hole.
Shape: 150 x 150 square with 25 mm 45-degree corner cuts (8 sides; long flats so the Pi's 85 mm port edge fits a wall).
Frame: (0,0) centre, z = 0 the flat bottom. All mm. Run: python node_single.py"""
import math
import sys
from pathlib import Path
from build123d import Box, Cylinder, Cone, Pos, Rot, Part, Polygon, extrude, fillet, chamfer, Axis, export_stl, export_step

CASE = next(p for p in (Path(__file__).resolve().parent.parent / d for d in ("Pi5-AI-HAT-Case", "case")) if (p / "pi5_aihat_case.py").exists())
sys.path.insert(0, str(CASE))
import pi5_aihat_case as m                                          # noqa: E402  (Pi geometry + tolerances of the first case)
from pi5_aihat_case import box, cz, INS_D, M3_CLR, M3_HEAD, HOLES    # noqa: E402

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

HALF, CUT = 75.0, 25.0          # outer square half-width, corner cut (45 deg)
WALL, PORT_WALL, FLOOR = 3.0, 2.0, 2.5
Z_BODY = 48.0                   # body top (lid seat)
LID_T = 3.0
Z_LID = Z_BODY + LID_T          # 51 total

# Pi 5: PCB port edge (Pi y = 0) at 4.4 mm inside the outer -y face, exactly as in the first case
P0 = (-42.5, -HALF + 4.4)       # PCB corner (Pi frame of the first case)
PI_Z = FLOOR + 4.0
PCB_TOP = PI_Z + m.PCB_T
# port centres on the Pi 5 drawing (x along the port edge); USB-C / micro-HDMI receptacles sit on the PCB, ~3.3 tall
USBC = dict(x=P0[0] + 11.2, z=PCB_TOP + 1.65, w=16.0, h=9.0)      # opening for a USB-C overmold (~12 x 6.5) + clearance all round
HDMI = dict(x0=P0[0] + 25.8 - 7.5, x1=P0[0] + 39.2 + 7.5, z=PCB_TOP + 1.75, h=9.0)   # both micro-HDMI, one opening (28.4 wide)

# Fan: ADDA AD0205DX-K59 (MC SKU 188631), 25 x 25 x 6 mm, 5 V [u: hole spacing 20 = the 25 mm standard; measure].
# Its ~2.4 mm holes take M2.5 (not M3): M2.5 x 10 from outside + nut, or self-tap; it also press-fits its frame.
FAN_SIZE, FAN_PITCH, FAN_DEPTH = 25.0, 20.0, 6.0
FAN_SCREW_D, FAN_HEAD_D = 2.8, 5.2     # M2.5 clearance + head counterbore
FAN = dict(z=30.0, pitch=FAN_PITCH, size=FAN_SIZE, depth=FAN_DEPTH)  # on the +y wall, centred x 0, high (hot air rises)
COLS = [(sx * 59.0, sy * 59.0) for sx in (-1, 1) for sy in (-1, 1)]  # lid columns, merged into the corner cuts
STYLE_FINS, STYLE_GRILLE, LID_CHAMFER = True, True, 1.0            # node_v5 switches these off and draws its own
FAN_SCREWS, LID_CB, LID_HEAD = True, 1.5, M3_HEAD                    # fan screw holes; lid screw counterbore depth + dia
MERGE_PORTS = False                                                  # True: one continuous opening for USB-C + both HDMI

CAM = dict(w=25.0, d=23.86, pcb=1.12, lens_proud=7.4, back=2.75, lens_from_top=9.5,
           slot_w=26.1, slot_t=1.55, rail_in=11.3, rail_out=15.5, hole=12.5)


def shape_pts(inset):
    a, c = HALF - inset, CUT - inset * math.tan(math.pi / 8)
    if CUT <= 0:
        return [(-a, -a), (a, -a), (a, a), (-a, a)]                        # plain square (v5)
    return [(-a + c, -a), (a - c, -a), (a, -a + c), (a, a - c), (a - c, a), (-a + c, a), (-a, a - c), (-a, -a + c)]


def body_shape(inset, z0, z1):
    return Pos(0, 0, z0) * extrude(Polygon(*shape_pts(inset), align=None), z1 - z0)


def nut_trap(x, y, z_top, af=5.3, t=2.4):   # M2.5 nut drops in, Pi on top, M2.5 x 6 from above
    r = af / 2 / math.cos(math.pi / 6)
    hexa = Pos(x, y, z_top - t) * extrude(Polygon(*[(r * math.cos(math.radians(30 + 60 * k)), r * math.sin(math.radians(30 + 60 * k))) for k in range(6)], align=None), t + 1)
    return hexa + cz(x, y, 1.45, z_top - t - 4.5, z_top)


def cy_(x, z, r, y0, y1):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, abs(y1 - y0))


def slot_y(xc, zc, w, h, y0, y1):          # rounded-end opening through a y wall (no wide flat ceilings)
    return box(xc - w / 2 + h / 2, xc + w / 2 - h / 2, y0, y1, zc - h / 2, zc + h / 2) + \
        cy_(xc - w / 2 + h / 2, zc, h / 2, y0, y1) + cy_(xc + w / 2 - h / 2, zc, h / 2, y0, y1)


# ================= BODY =================
def make_body():
    b = body_shape(0, 0, Z_BODY) - body_shape(WALL, FLOOR, Z_BODY + 1)
    b = chamfer(b.edges().group_by(Axis.Z)[0], 0.6)                       # bed edge: no elephant foot
    yo = -HALF                                                             # -y outer face
    # port wall: 2.0 thick behind the Pi (the first case's rule), so the plugs reach the ports
    b -= box(P0[0] - 3, P0[0] + 88, yo + PORT_WALL, yo + WALL + 0.01, FLOOR, Z_BODY + 1)
    if MERGE_PORTS:                                                        # one stadium from the USB-C to the far HDMI
        x0, x1 = USBC["x"] - USBC["w"] / 2, HDMI["x1"]
        b -= slot_y((x0 + x1) / 2, (USBC["z"] + HDMI["z"]) / 2, x1 - x0, max(USBC["h"], HDMI["h"]) + 0.5, yo - 1, yo + PORT_WALL + 1)
    else:
        b -= slot_y(USBC["x"], USBC["z"], USBC["w"], USBC["h"], yo - 1, yo + PORT_WALL + 1)
        b -= slot_y((HDMI["x0"] + HDMI["x1"]) / 2, HDMI["z"], HDMI["x1"] - HDMI["x0"], HDMI["h"], yo - 1, yo + PORT_WALL + 1)
    # Pi: no screws into the case. The HAT kit's screw heads under the Pi drop into cups (the board rests on the heads),
    # and four L-walls hug the PCB corners up to just under its top face, clear of the microSD and the overhanging ports.
    for hx, hy in HOLES:
        x, y = P0[0] + hx, P0[1] + hy
        b += cz(x, y, 4.0, 0, PI_Z - 1.0)
        b -= cz(x, y, 2.9, PI_Z - 2.2, PI_Z)                               # cup: d5.8 x 1.2 round a d4.8 x 2.0 head
    # x=0 edge and the y=56 edge rise 10 mm above the board (under the HAT, which starts 16 mm up); the x=85 edge stays
    # just under the board top because the USB/Ethernet jacks overhang it. microSD (x=0 edge, middle) is left open.
    c, t, L, hi, lo = 0.3, 2.0, 10.0, PCB_TOP + 10.0, PCB_TOP - 0.2
    hug = Part()
    hug += box(-c - t, -c, 0.0, L, 0, hi) + box(-c - t, -c, 56.0 - L, 56.0 + c + t, 0, hi)          # x=0 edge, both ends
    hug += box(-c - t, L, 56.0 + c, 56.0 + c + t, 0, hi)                                             # y=56 edge, x=0 end
    hug += box(85.0 - L, 85.0 + c, 56.0 + c, 56.0 + c + t, 0, hi)                                    # y=56 edge, x=85 end
    hug += box(85.0 + c, 85.0 + c + t, 0.0, L, 0, lo) + box(85.0 + c, 85.0 + c + t, 56.0 - L, 56.0 + c + t, 0, lo)
    b += Pos(P0[0], P0[1], 0) * hug                                        # the port wall closes the -y side
    # lid columns + inserts
    for x, y in COLS:
        b += cz(x, y, 5.0, 0, Z_BODY)
        b -= m.ins_z(x, y, Z_BODY, 7.0)
    # fan on the +y wall: counterbored M3 holes (heads outside), corner guides inside, slot grille
    yi = HALF - WALL
    for sx in (-1, 1) if FAN_SCREWS else ():
        for sz in (-1, 1):
            x, z = sx * FAN["pitch"] / 2, FAN["z"] + sz * FAN["pitch"] / 2
            b -= cy_(x, z, FAN_SCREW_D / 2, yi - 1, HALF + 1) + cy_(x, z, FAN_HEAD_D / 2, HALF - 1.2, HALF + 1)
    g = FAN["size"] / 2
    dep, zb, zt_ = FAN["depth"] - 1.5, FAN["z"] - g - 0.15, FAN["z"] + g    # 0.15 per side: snug; fan drops in from above
    for sx in (-1, 1):                                                     # everything grows from the floor: no overhangs
        b += box(*sorted((sx * (g + 0.15), sx * (g + 2.15))), yi - dep, yi + 0.5, FLOOR - 0.5, zt_)     # side rail
        b += box(*sorted((sx * (g - 7.0), sx * (g + 2.15))), yi - dep, yi + 0.5, FLOOR - 0.5, zb)      # seat block
    gr = FAN["size"] * 0.45                                                # grille radius (just inside the blade ring)
    for x in ([i * 4.0 for i in range(-int(gr // 4), int(gr // 4) + 1)] if STYLE_GRILLE else []):
        half = math.sqrt(max(0.0, gr ** 2 - x ** 2))
        b -= box(x - 1.1, x + 1.1, yi - 1, HALF + 1, FAN["z"] - half, FAN["z"] + half)
    # air fins: full-height intake slots across both side flats (+x / -x)
    for sx in ((-1, 1) if STYLE_FINS else ()):
        xw = sx * HALF
        for y in range(-40, 41, 4):
            b -= box(*sorted((xw - sx * (WALL + 1), xw + sx * 1)), y - 1.0, y + 1.0, FLOOR + 5, Z_BODY - 6)
    return b


# ================= LID (prints top-face down) =================
def make_lid():
    z0, z1 = Z_BODY, Z_LID
    l = body_shape(0, z0, z1)
    l = chamfer(l.edges().group_by(Axis.Z)[-1], LID_CHAMFER)
    for x, y in COLS:
        l -= cz(x, y, M3_CLR / 2, z0 - 1, z1 + 1) + cz(x, y, LID_HEAD / 2, z1 - LID_CB, z1 + 1)
    # lid locating lip (fits inside the body walls, 0.3 clearance)
    l += body_shape(WALL + 0.3, z0 - 2.0, z0) - body_shape(WALL + 2.3, z0 - 3, z0 + 1)
    for x, y in COLS:                                                      # lip notched around the columns
        l -= cz(x, y, 5.6, z0 - 3, z0)
    # camera: lens hole + slide-in rails (board slides in from -y, the cable end, until it hits the stop)
    c = CAM
    X = Pos(c.get("x", 0.0), 0, 0)                                         # camera can sit off-centre (v5: left of the PIR)
    l -= X * (cz(0, 0, c["hole"] / 2, z0 - 1, z1 + 1) + Pos(0, 0, z1 - 0.6) * Cone(c["hole"] / 2, c["hole"] / 2 + 0.6, 0.61, align=None))
    pcb_front = z1 - c["lens_proud"]                                       # lens tip flush with the lid face
    g0, g1 = pcb_front - c["pcb"] / 2 - c["slot_t"] / 2 - c["pcb"] / 2, None
    gz0 = pcb_front - c["pcb"] - (c["slot_t"] - c["pcb"]) / 2               # groove bottom
    gz1 = gz0 + c["slot_t"]
    ystop = c["lens_from_top"]                                             # board top edge at the stop
    ylo = ystop - c["d"] - 2.0
    rail_bot = gz0 - 2.0
    for s in (-1, 1):
        x0, x1 = sorted((s * c["rail_in"], s * c["rail_out"]))
        rail = box(x0, x1, ylo, ystop + 2.0, rail_bot, z0)
        rail -= box(*sorted((s * c["rail_in"] - s * 0.01, s * c["slot_w"] / 2)), ylo - 1, ystop + 0.3, gz0, gz1)
        l += X * rail
    l += X * box(-c["rail_out"], c["rail_out"], ystop + 0.3, ystop + 2.0, rail_bot, z0)          # stop wall
    return l


# ================= hardware (checks + viewer) =================
def hardware():
    P = Pos(P0[0], P0[1], PI_Z - m.PI_Z)
    hw = P * m.hardware()                                                  # Pi + AI HAT+ 26T stack, header pins, kit screw heads
    ports = box(66.2, 88, 2.2, 18.2, m.PCB_TOP, m.PCB_TOP + 13.9)
    for yc in (29.1, 47.0):
        ports += box(68, 88, yc - 6.55, yc + 6.55, m.PCB_TOP, m.PCB_TOP + 16.4)
    ports += box(6.9, 15.5, -1.5, 6, m.PCB_TOP, m.PCB_TOP + 3.3)
    for xc in (25.8, 39.2):
        ports += box(xc - 3.25, xc + 3.25, -1.9, 6, m.PCB_TOP, m.PCB_TOP + 3.5)
    ports += box(-2.25, 12, 22.6, 35.2, m.PI_Z - 1.6, m.PI_Z)
    hw += P * (ports + box(1.0, 64.0, 7.0, 49.0, m.PCB_TOP + 1.5, m.PCB_TOP + 10.5))
    # plugs going in from outside: USB-C overmold 12 x 6.5, micro-HDMI overmolds 11 x 7 (side by side)
    yo = -HALF
    hw += box(USBC["x"] - 6.0, USBC["x"] + 6.0, yo - 25, P0[1] - 1.5, USBC["z"] - 3.25, USBC["z"] + 3.25)
    for xc in (P0[0] + 25.8, P0[0] + 39.2):
        hw += box(xc - 5.5, xc + 5.5, yo - 25, P0[1] - 1.9, HDMI["z"] - 3.5, HDMI["z"] + 3.5)
    yi = HALF - WALL
    g = FAN["size"] / 2
    hw += box(-g, g, yi - FAN["depth"], yi, FAN["z"] - g, FAN["z"] + g)
    c = CAM
    pcb_front = Z_LID - c["lens_proud"]
    cam = box(-c["w"] / 2, c["w"] / 2, c["lens_from_top"] - c["d"], c["lens_from_top"], pcb_front - c["pcb"], pcb_front)
    cam += cz(0, 0, 4.5, pcb_front, pcb_front + c["lens_proud"]) + box(-4.3, 4.3, -4.3, 4.3, pcb_front, pcb_front + 3.0)
    cam += box(-8, 8, c["lens_from_top"] - c["d"], c["lens_from_top"] - c["d"] + 6, pcb_front - c["pcb"] - c["back"], pcb_front - c["pcb"])
    return hw + Pos(c.get("x", 0.0), 0, 0) * cam


PARTS = dict(body=make_body, lid=make_lid)

if __name__ == "__main__":
    built = {n: f() for n, f in PARTS.items()}
    hw = hardware()
    bad = 0
    for n, p in built.items():
        bb = p.bounding_box()
        v = (p & hw).volume
        bad += (v > 0.001) + (len(p.solids()) != 1)
        print(f"{n:5} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:5.1f}  z {bb.min.Z:5.1f}..{bb.max.Z:5.1f}  {p.volume/1000:6.1f} cm3  hw {v:.3f}  solids {len(p.solids())}")
        export_stl(p, str(OUT / f"single_{n}.stl"), tolerance=0.02, angular_tolerance=0.1)
        export_step(p, str(OUT / f"single_{n}.step"))
    v = (built["body"] & built["lid"]).volume
    if v > 0.001:
        print(f"OVERLAP body x lid: {v:.3f}"); bad += 1
    export_stl(hw, str(OUT / "single_hardware.stl"), tolerance=0.05)
    print("problems:", bad)

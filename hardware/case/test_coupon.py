"""Fit-test coupon for the Pi 5 case (P1S, 0.4 nozzle). Every feature is printed at its real size AND in the
same orientation as on the real part. Run: python test_coupon.py -> out/test_coupon.stl"""
from build123d import Text, extrude, Pos, Rot, export_stl
from pi5_aihat_case import box, cz, cx, ins_z, OUT

INSERTS = [3.8, 3.9, 4.0, 4.1, 4.2]


def label(s, x, y, z_top, size=3.2):  # engraved 0.5 mm into a top face
    return Pos(x, y, z_top - 0.5) * extrude(Text(s, font_size=size), 1.0)


# A. insert bar: 5 holes (7 mm deep, same lead-in as the case), sizes engraved on the front face
c = box(0, 47, -2, 9, 0, 8.5)   # 3.4 mm wall around each hole, like the case
for i, d in enumerate(INSERTS):
    x = 5.5 + 9 * i
    c -= ins_z(x, 3.5, 8.5, 7.0) - cz(x, 3.5, 2.0, -10, 20) + cz(x, 3.5, d / 2, 1.5, 9.5)  # chamfer + this diameter
    c -= Pos(x, -1.4, 4.0) * Rot(90, 0, 0) * extrude(Text(f"{d:.1f}", font_size=3.0), 1.2)

# B. plate (4 mm): M3 clearance + head counterbore (from below, like the upside-down lid),
#    Pi floor pocket, lid-post pocket, GPIO slot width
c += box(0, 47, 9, 28, 0, 4)
c -= cz(6, 16, 3.5 / 2, -1, 5) + cz(6, 16, 6.6 / 2, -1, 2.5)
c -= cz(17, 16, 6.6 / 2, 0.5, 5) + cz(17, 16, 1.5, -1, 5)
c -= cz(28, 16, 6.0 / 2, 0.7, 5)
c -= box(34, 44, 12.9, 19.1, -1, 5)
for s, x in (("M3", 6), ("NUT", 17), ("HD", 28), ("GPIO", 39)):
    c -= label(s, x, 24.5, 4, 3.0)

# C. sideways M3 hole (pivot), d3.6, printed horizontal like the bracket
c += box(47, 57, 20, 28, 0, 10) - cx(24, 6.5, 1.8, 46, 58)

# D. camera groove slice: the cradle's channels, printed face-down exactly as on the plate (groove = 1.55 tall)
gy0, gy1 = 28, 34
for s in (-1, 1):
    x0, x1 = sorted((s * 11.3, s * 15.5))
    c += Pos(23.5, 0, 0) * box(x0, x1, gy0, gy1, 0, 5.0)
c += Pos(23.5, 0, 0) * box(-15.5, 15.5, gy0, gy1, 0, 1.5)
c -= Pos(23.5, 0, 0) * box(-12.8, 12.8, gy0 - 1, gy1 + 1, 1.785, 3.335)

if __name__ == "__main__":
    bb = c.bounding_box()
    print(f"coupon {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, {c.volume/1000:.2f} cm^3")
    export_stl(c, str(OUT / "test_coupon.stl"), tolerance=0.02, angular_tolerance=0.1)

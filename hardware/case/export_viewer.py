"""Export case parts + hardware proxies, in assembled position, as JSON meshes for the 3D assembly viewer."""
import base64, json, sys
import numpy as np
from build123d import Pos, Rot, Part
import pi5_aihat_case as m
from pi5_aihat_case import box, cz, cx, PCB_TOP, PI_Z, HAT_TOP, STACK, HOLES, TOWERS, SPLIT, LID_TOP, FAN_C, FAN_P

items = []  # (name, step, color, explode_dz, part)


def add(name, step, color, dz, part):
    items.append((name, step, color, dz, part))


def cy(x, z, r, y0, y1):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder_(r, y1 - y0)


from build123d import Cylinder as Cylinder_


def screw_z(x, y, z_head_bottom, length):  # socket head pointing up, shank down
    return cz(x, y, 2.75, z_head_bottom, z_head_bottom + 3) + cz(x, y, 1.5, z_head_bottom - length, z_head_bottom)


CASE, PCB, SILVER, BLACK, BRASS, STEEL, RIBBON = "#cfd3d6", "#2f7d4a", "#b9bec4", "#26282b", "#c9a24a", "#55595e", "#d98a3a"
HAT_PCB = "#2a6f8f"

# 1. base
add("Base", 1, CASE, 0, m.make_base())
add("Base inserts", 1, BRASS, 0, sum((cz(x, y, 2.3, SPLIT - 5.7, SPLIT) for x, y in TOWERS), Part()))
# 2. Pi 5 + Active Cooler
D2 = 40
add("Pi 5 board", 2, PCB, D2, box(0, 85, 0, 56, PI_Z, PCB_TOP))
ports = box(66.2, 88, 2.2, 18.2, PCB_TOP, PCB_TOP + 13.9)
for yc in (29.1, 47.0):
    ports += box(68, 88, yc - 6.55, yc + 6.55, PCB_TOP, PCB_TOP + 16.4)
ports += box(6.9, 15.5, -1.5, 6, PCB_TOP, PCB_TOP + 3.3)
for xc in (25.8, 39.2):
    ports += box(xc - 3.25, xc + 3.25, -1.9, 6, PCB_TOP, PCB_TOP + 3.5)
ports += box(-2.25, 12, 22.6, 35.2, PI_Z - 1.6, PI_Z)  # microSD + card
add("Pi 5 ports", 2, SILVER, D2, ports)
add("GPIO header", 2, BLACK, D2, box(7.1, 57.9, 49.96, 55.04, PCB_TOP, PCB_TOP + 8.5))
add("Active Cooler", 2, "#3a3f46", D2, box(1.0, 64.0, 7.0, 49.0, PCB_TOP + 1.5, PCB_TOP + 10.5))
add("Kit screws (under Pi)", 2, STEEL, D2, sum((cz(x, y, 2.3, PI_Z - 2.0, PI_Z) for x, y in HOLES), Part()))
# 3. AI HAT+
D3 = 75
hat = box(0, 65, 0, 56.5, PCB_TOP + STACK, HAT_TOP) - box(47.5, 57.5, -1, 16, 0, 60) - box(-1, 5, 21, 39, 0, 60)
add("AI HAT+ board", 3, HAT_PCB, D3, hat)
add("Hailo-8", 3, BLACK, D3, box(22.5, 39.5, 18, 35, HAT_TOP, HAT_TOP + 1.3))
add("Stacking header", 3, BLACK, D3, box(7.1, 57.9, 49.96, 55.04, PCB_TOP + 8.5, PCB_TOP + STACK)
    + box(7.4, 57.6, 50.3, 54.7, HAT_TOP, HAT_TOP + 6.5))
add("16 mm spacers", 3, BRASS, D3, sum((cz(x, y, 2.5, PCB_TOP, PCB_TOP + STACK) for x, y in HOLES), Part())
    + sum((cz(x, y, 2.3, HAT_TOP, HAT_TOP + 1.8) for x, y in HOLES), Part()))
add("PCIe ribbon", 3, RIBBON, D3, box(1.6, 2.0, 25.5, 34.5, PCB_TOP + 1, HAT_TOP + 1.5) + box(1.6, 6.0, 25.5, 34.5, HAT_TOP + 1.1, HAT_TOP + 1.5))
# 4. lid
D4 = 115
add("Lid", 4, CASE, D4, m.make_lid())
add("Lid inserts", 4, BRASS, D4, sum((cz(x, y, 2.3, LID_TOP - 5.7, LID_TOP) for x, y in m.FAN_INS + m.LID_INS), Part()))
add("Lid screws M3x10", 4, STEEL, D4 + 25, sum((screw_z(x, y, SPLIT + 4.5, 10) for x, y in TOWERS), Part()))
# 5. fan + guard
D5 = 140
fan = box(FAN_C[0] - 20, FAN_C[0] + 20, FAN_C[1] - 20, FAN_C[1] + 20, LID_TOP, LID_TOP + 10) - cz(*FAN_C, 18.5, LID_TOP - 1, LID_TOP + 11)
fan += cz(*FAN_C, 9, LID_TOP + 0.5, LID_TOP + 9.5)
for sx in (-1, 1):
    for sy in (-1, 1):
        fan -= cz(FAN_C[0] + sx * FAN_P, FAN_C[1] + sy * FAN_P, 1.7, LID_TOP - 1, LID_TOP + 11)
add("52Pi 4010 fan", 5, "#1d1f22", D5, fan)
add("Fan guard", 5, CASE, D5 + 20, Pos(*FAN_C, LID_TOP + 10) * m.make_guard())
add("Fan screws M3x16", 5, STEEL, D5 + 45,
    sum((screw_z(x, y, LID_TOP + 12, 16) for x, y in m.FAN_INS), Part()))
# 6. camera (optional)
D6 = 150
P = m.place_camera
add("Camera bracket", 6, "#9aa9c9", D6, P(m.make_bracket()))
add("Bracket screws M3x8", 6, STEEL, D6 + 25, P(sum((cz(s * 16, 3, 2.75, -4, -1) + cz(s * 16, 3, 1.5, -12, -4) for s in (-1, 1)), Part())))
cam_c = 25
add("Camera cradle", 6, "#e0a35c", D6 + cam_c, P(m.make_cradle()))
add("Cradle inserts", 6, BRASS, D6 + cam_c, P(sum((cx(2.5, 12, 2.3, *sorted((s * 16.8, s * 22.5))) for s in (-1, 1)), Part())))
cam = box(-12.5, 12.5, 0, 1.12, 0, 23.86) + box(-5.4, 5.4, -4.5, 0, 9.0, 19.8) + cy(0, 14.4, 2.9, -7.4, -4.5) + box(-8, 8, 1.12, 3.87, 0, 5.71)
add("Camera Module 3", 6, PCB, D6 + cam_c + 20, P(cam))
add("Pivot screws M3x8", 6, STEEL, D6 + cam_c, P(sum((cx(2.5, 12, 2.75, *sorted((s * 27.0, s * 30.0))) + cx(2.5, 12, 1.5, *sorted((s * 19.0, s * 27.0))) for s in (-1, 1)), Part())))
# camera ribbon (illustrative route): camera -> over the lid -> down the slot -> CAM connector
rz = LID_TOP + 0.3
rib = box(72.5, 73.0, 21, 37, rz, LID_TOP + 7) + box(56, 73, 21, 37, rz, rz + 0.4) + box(54.8, 58, 2, 37, rz, rz + 0.4)
rib += box(54.8, 55.2, 2, 14, PCB_TOP + 1.5, rz + 0.4)
add("Camera ribbon", 6, RIBBON, D6, rib)


def enc(part, tol=0.04):
    v, t = part.tessellate(tol, 0.2)
    v = np.array([[p.X, p.Y, p.Z] for p in v], dtype=np.float32)
    tri = v[np.array(t, dtype=np.int64)].reshape(-1)
    return base64.b64encode(tri.astype(np.float32).tobytes()).decode()


out = [dict(name=n, step=s, color=c, dz=dz, pos=enc(p)) for n, s, c, dz, p in items]
json.dump(out, open(sys.argv[1], "w"))
print(len(out), "meshes", sum(len(o["pos"]) for o in out) // 1024, "KB b64")

"""Lay out print-oriented parts into one 3MF plate (run after pi5_aihat_case.py)."""
import numpy as np, trimesh
from trimesh.transformations import rotation_matrix as R
plate = {  # name: (rotation, xy offset of the part's min corner)
    "base": (np.eye(4), (5, 5)), "lid": (R(np.pi, [1, 0, 0]), (110, 5)),
    "fan_guard": (np.eye(4), (10, 90)), "cam_bracket": (np.eye(4), (60, 90)),
    "cam_cradle": (R(np.pi / 2, [1, 0, 0]), (120, 90)),
}
scene = trimesh.Scene()
for name, (rot, (x, y)) in plate.items():
    m = trimesh.load(f"out/{name}.stl"); m.apply_transform(rot)
    m.apply_translation([x, y, 0] - m.bounds[0]); scene.add_geometry(m, node_name=name, geom_name=name)
scene.export("out/Pi5-AIHAT-Case_plate.3mf")
print(scene.bounds)

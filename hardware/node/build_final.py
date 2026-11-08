"""Final print set for the home-monitor node (v5 option A, 'Hex Facets').
Builds body + lid + the three inlaid logos, checks fits, scans overhangs in print orientation, and writes:
  out/final_body.stl                 body, upright (bed = floor)
  out/final_lid.3mf                  lid flipped (top face on the bed) as ONE Bambu object with 4 parts:
                                     lid = filament 1 (black PLA-CF), LAND = 2 (white), NVIDIA = 3 (green), State Farm = 4 (red)
Run: python build_final.py"""
import uuid, zipfile
import numpy as np, trimesh
from build123d import Rot, export_stl
import node_v5 as V

N, O = V.N, V.OPTIONS["A"]
OUT = N.OUT


def mesh(part, name):
    path = OUT / f"_tmp_{name}.stl"
    export_stl(part, str(path), tolerance=0.01, angular_tolerance=0.1)
    return trimesh.load(path)


def overhangs(m, label, limit=0.71):
    """Down-facing triangles steeper than 45 deg, off the bed, grouped into 10 mm cells."""
    n, c, a = m.face_normals, m.triangles_center, m.area_faces
    sel = (n[:, 2] < -limit) & (c[:, 2] > 0.4)
    cells = {}
    for p, ar in zip(c[sel], a[sel]):
        k = tuple((p // 10).astype(int))
        cells[k] = cells.get(k, 0) + ar
    big = sorted(((v, k) for k, v in cells.items() if v > 2.0), reverse=True)
    print(f"{label}: {a[sel].sum():.0f} mm2 down-facing >45 deg in {len(big)} cells > 2 mm2")
    for v, k in big[:25]:
        print(f"   {v:6.1f} mm2 near x {k[0]*10:+4d} y {k[1]*10:+4d} z {k[2]*10:3d}")


def write_3mf(path, parts):
    """Bambu Studio project 3MF: one object made of one part per logo/lid, each part on its own filament slot.
    (Bambu ignores PrusaSlicer's volume config and merges the parts, so this writes Bambu's native layout.)"""
    ns = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    objs, comps, cfg_parts = "", "", ""
    for i, (name, m, ext) in enumerate(parts, start=1):
        vx = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in m.vertices)
        tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        objs += f'<object id="{i}" p:UUID="{uuid.uuid4()}" type="model"><mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>'
        comps += f'<component p:path="/3D/Objects/object_1.model" objectid="{i}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
        cfg_parts += (f'<part id="{i}" subtype="normal_part"><metadata key="name" value="{name}"/>'
                      f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><metadata key="extruder" value="{ext}"/></part>\n')
    oid = len(parts) + 1
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sub = xml + f'<model unit="millimeter" xml:lang="en-US" {ns}><metadata name="BambuStudio:3mfVersion">1</metadata><resources>{objs}</resources><build/></model>'
    main = (xml + f'<model unit="millimeter" xml:lang="en-US" {ns}>'
            '<metadata name="BambuStudio:3mfVersion">1</metadata>'
            f'<resources><object id="{oid}" p:UUID="{uuid.uuid4()}" type="model"><components>{comps}</components></object></resources>'
            f'<build p:UUID="{uuid.uuid4()}"><item objectid="{oid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/></build></model>')
    cfg = (xml + f'<config>\n<object id="{oid}"><metadata key="name" value="lid"/>'
           f'<metadata key="extruder" value="1"/>\n{cfg_parts}</object>\n</config>\n')
    ct = (xml + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rel = xml + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{}</Relationships>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rel.format('<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'))
        z.writestr("3D/_rels/3dmodel.model.rels", rel.format('<Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'))
        z.writestr("3D/3dmodel.model", main)
        z.writestr("3D/Objects/object_1.model", sub)
        z.writestr("Metadata/model_settings.config", cfg)


if __name__ == "__main__":
    hw = N.hardware() + Rot(0, 0, 270.0) * V.speaker_proxy() + V.pir_proxy(N.Z_LID)
    body, lid = V.make_body(O), V.make_lid(O)
    logos = {k: V.logo_inlay(k) for k in V.BADGES}
    bad = 0
    for nm, p in [("body", body), ("lid", lid)] + list(logos.items()):
        v, s = (p & hw).volume, len(p.solids())
        bad += (v > 0.001) + (nm in ("body", "lid") and s != 1)
        print(f"{nm:10} vs hardware {v:.3f} mm3, solids {s}")
    for a, b in [("body", "lid")] + [("lid", k) for k in logos]:
        pa = body if a == "body" else lid
        v = (pa & (lid if b == "lid" else logos[b])).volume
        bad += v > 0.001
        print(f"{a} x {b}: overlap {v:.3f} mm3")
    print("PROBLEMS", bad)

    mb = mesh(body, "body")
    mb.export(OUT / "final_body.stl")
    flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    parts = [("lid", mesh(lid, "lid"), 1)] + [(k, mesh(logos[k], k), e) for k, e in (("team", 2), ("nvidia", 3), ("statefarm", 4))]
    for _, m, _ in parts:
        m.apply_transform(flip)
    z0 = min(m.bounds[0][2] for _, m, _ in parts)
    for _, m, _ in parts:
        m.apply_translation([0, 0, -z0])
    overhangs(mb, "body (upright)")
    overhangs(parts[0][1], "lid (flipped)")
    write_3mf(OUT / "final_lid.3mf", parts)
    for f in OUT.glob("_tmp_*.stl"):
        f.unlink()
    print("wrote out/final_body.stl, out/final_lid.3mf")

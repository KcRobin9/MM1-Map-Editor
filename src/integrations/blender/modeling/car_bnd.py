"""
Car/trailer collision BND generator (Blender-free).

The engine collides cars against each other and against world objects using a
.BND collision hull (mmBoundTemplate, magic "BND2"). Every stock car body is an
8-vertex oriented box: a degenerate sentinel polygon followed by 6 quad faces,
plus 12 edges and 8 "hot" verts (== the box verts) used for edge-edge collision.

This is the SAME on-disk format as map polygon bounds, with two practical
differences that matter here:
  * map terrain bounds set XDim/YDim/ZDim != 0 and append a grid acceleration
    table (row/bucket offsets, fixed heights); car bounds set dims = 0 and have
    no grid.
  * car bounds ship with hot verts + a full edge list populated; the map
    editor's Bounds writer leaves those empty (fine for static props, but cars
    need edges for car-vs-car collision).

Custom cars previously copied VPMUSTANG99_BND.BND verbatim, so every custom car
collided as a Mustang-sized box. Here we size the collision box to the car's
actual body AABB (game space: x=lateral, y=up, z=front), matching BMS/DLP space.

PlaneEdges and the per-face projection axis are computed with the same routine
the map editor uses (src.core.geometry.planes.compute_edges), which reproduces
the stock byte layout exactly (verified against VPPANOZ_BND.BND).
"""
import struct
from pathlib import Path
from typing import List, Tuple

from src.core.geometry.planes import compute_edges, compute_normal

AABB = Tuple[Tuple[float, float, float], Tuple[float, float, float]]

MAGIC = b"BND2"

# Box vertex convention (matches stock car BNDs):
#   bit 2 (4): 0 -> max x, set -> min x
#   bit 1 (2): 0 -> min y, set -> max y
#   bit 0 (1): 0 -> min z, set -> max z
# Faces listed as 4 vertex indices in stock winding order (outward normal).
_FACES = [
    (1, 0, 2, 3),  # +X
    (6, 4, 5, 7),  # -X
    (4, 0, 1, 5),  # -Y  (bottom)
    (5, 1, 3, 7),  # +Z  (front)
    (7, 3, 2, 6),  # +Y  (top)
    (6, 2, 0, 4),  # -Z  (back)
]

# In-memory payload size only depends on counts, not coordinates. An 8-vert box
# (8 verts, 7 polys, 12 edges, 8 hot verts) always matches the stock car box.
_BOX_CACHE_SIZE = 1040


def _box_verts(aabb: AABB) -> List[Tuple[float, float, float]]:
    (mnx, mny, mnz), (mxx, mxy, mxz) = aabb
    verts = []
    for i in range(8):
        x = mnx if (i & 4) else mxx
        y = mxy if (i & 2) else mny
        z = mxz if (i & 1) else mnz
        verts.append((x, y, z))
    return verts


def _compute_edge_list(faces: List[Tuple[int, ...]]) -> Tuple[List[int], List[int]]:
    """Replicates mmBoundTemplate::ComputeEdges: undirected edges of the face rings."""
    e1: List[int] = []
    e2: List[int] = []

    def in_list(a: int, b: int) -> bool:
        for i in range(len(e1)):
            if (a == e1[i] and b == e2[i]) or (a == e2[i] and b == e1[i]):
                return True
        return False

    for face in faces:
        n = len(face)
        v1 = face[n - 1]
        for k in range(n):
            v2 = face[k]
            if not in_list(v1, v2):
                e1.append(v1)
                e2.append(v2)
            v1 = v2
    return e1, e2


def build_box_bnd(aabb: AABB, output_path: Path, offset=(0.0, 0.0, 0.0)) -> dict:
    """Write an 8-vertex box collision BND sized to `aabb`. Returns a summary dict."""
    verts = _box_verts(aabb)
    (mnx, mny, mnz), (mxx, mxy, mxz) = aabb
    center = ((mnx + mxx) * 0.5, (mny + mxy) * 0.5, (mnz + mxz) * 0.5)
    radius = max(
        ((v[0] - center[0]) ** 2 + (v[1] - center[1]) ** 2 + (v[2] - center[2]) ** 2) ** 0.5
        for v in verts
    )

    # Per-face: plane normal/distance, plane edges, projection-axis flag.
    face_normals = []
    face_records = []  # (flags, vidx(4), plane_edges(4x3), plane_n(3), plane_d)
    for face in _FACES:
        fv = [verts[i] for i in face]
        n = compute_normal(fv[0], fv[1], fv[2])  # unrounded, outward
        face_normals.append(n)
        plane_d = -(n.x * fv[0][0] + n.y * fv[0][1] + n.z * fv[0][2])
        # edge_pad=0.0: the city's seam padding is for gaps BETWEEN neighbouring polygons.
        # A car bound is a closed box, so padding would only inflate its hit-test.
        plane_edges, axis_flag = compute_edges(fv, edge_pad = 0.0)
        flags = 0x4 | axis_flag  # quad + projection axis
        pe = [(e.x, e.y, e.z) for e in plane_edges]
        face_records.append((flags, list(face), pe, (n.x, n.y, n.z), plane_d))

    edge_v1, edge_v2 = _compute_edge_list(_FACES)
    n_edges = len(edge_v1)

    # Edge plane normal = normalized sum of the two adjacent face normals;
    # edge plane distance = dot(edge_normal, one adjacent face normal).
    edge_pn: List[Tuple[float, float, float]] = []
    edge_pd: List[float] = []
    for a, b in zip(edge_v1, edge_v2):
        adj = [face_normals[fi] for fi, f in enumerate(_FACES) if a in f and b in f]
        s = adj[0] + adj[1] if len(adj) >= 2 else adj[0]
        ln = s.Mag()
        en = s / ln if ln > 1e-9 else s
        edge_pn.append((en.x, en.y, en.z))
        edge_pd.append(en.Dot(adj[0]))

    num_polys_field = len(_FACES)  # stored = real face count; file holds +1 (sentinel)

    buf = bytearray()
    buf += MAGIC
    buf += struct.pack("<3f", *offset)
    buf += struct.pack("<3l", 0, 0, 0)  # dims: no grid
    buf += struct.pack("<3f", *center)
    buf += struct.pack("<2f", radius, radius * radius)
    buf += struct.pack("<3f", mnx, mny, mnz)
    buf += struct.pack("<3f", mxx, mxy, mxz)
    buf += struct.pack("<2l", len(verts), num_polys_field)
    buf += struct.pack("<3l", 0, len(verts), n_edges)  # nhv1, nhv2(=verts), nedges
    buf += struct.pack("<2f", 0.0, 0.0)  # x_scale, z_scale
    buf += struct.pack("<lfl", 0, 0.0, _BOX_CACHE_SIZE)  # num_indices, height_scale, cache

    for v in verts:
        buf += struct.pack("<3f", *v)

    # Sentinel polygon (skipped by ComputeEdges; loops read Polygons[i+1]).
    buf += struct.pack("<HB", 0, 0)
    buf += struct.pack("<B", 0)
    buf += struct.pack("<4h", 0, 0, 0, 0)
    for _ in range(4):
        buf += struct.pack("<3f", 0.0, 0.0, 0.0)
    buf += struct.pack("<3f", 0.0, 1.0, 0.0)
    buf += struct.pack("<f", 0.0)

    for flags, vidx, pe, pn, pd in face_records:
        buf += struct.pack("<HB", 0, 0)
        buf += struct.pack("<B", flags)
        buf += struct.pack("<4h", *vidx)
        for e in pe:
            buf += struct.pack("<3f", *e)
        buf += struct.pack("<3f", *pn)
        buf += struct.pack("<f", pd)

    for v in verts:  # hot verts == verts
        buf += struct.pack("<3f", *v)
    buf += struct.pack(f"<{n_edges}I", *edge_v1)
    buf += struct.pack(f"<{n_edges}I", *edge_v2)
    for pn in edge_pn:
        buf += struct.pack("<3f", *pn)
    buf += struct.pack(f"<{n_edges}f", *edge_pd)

    Path(output_path).write_bytes(buf)
    return {
        "verts": len(verts),
        "polys": num_polys_field,
        "edges": n_edges,
        "center": center,
        "radius": radius,
        "bytes": len(buf),
    }


def generate_car_bnd(bms_dir: Path, output_path: Path, body_name: str = "BODY_H") -> dict:
    """Build a car-body box BND from the exported body BMS in bms_dir."""
    from src.integrations.blender.modeling.car_dlp import _bms_aabb_car_space

    body = Path(bms_dir) / f"{body_name}.BMS"
    aabb = _bms_aabb_car_space(body)
    return build_box_bnd(aabb, output_path)

import math
from typing import List

from src.core.vector.vector_3 import Vector3
from src.constants.misc import Shape, Default


# Default outward padding on each polygon's point-in-poly hit-test, in metres. Covers tiny
# seams and floating-point boundary gaps between adjacent polygons that would otherwise read
# as "outside every polygon" -> fall-through or no-cell. See compute_edges().
EDGE_PAD = 0.05


def ensure_ccw_order(vertex_coordinates: List) -> List:
    vertex_1, vertex_2, vertex_3 = vertex_coordinates
    normal = compute_normal(vertex_1, vertex_2, vertex_3)
    if normal.Dot(Vector3(0, 1, 0)) < 0:
        return [vertex_1, vertex_3, vertex_2]
    return [vertex_1, vertex_2, vertex_3]


def compute_normal(vertex_1, vertex_2, vertex_3) -> Vector3:
    v1 = Vector3(*vertex_2) - Vector3(*vertex_1)
    v2 = Vector3(*vertex_3) - Vector3(*vertex_1)
    n = v1.Cross(v2)
    mag = n.Mag()
    return n / mag if mag > 1e-9 else Vector3(0, 1, 0)


def ensure_quad_ccw_order(vertex_coordinates: List) -> List:
    normal = compute_normal(*vertex_coordinates[:3])

    verts = [Vector3(*v) for v in vertex_coordinates]
    diff = verts[1] - verts[0]
    basis_1 = (diff - normal * normal.Dot(diff)).Normalize()
    basis_2 = normal.Cross(basis_1)

    projections = [(basis_1.Dot(v), basis_2.Dot(v)) for v in verts]

    n = len(projections)
    cx = sum(p[0] for p in projections) / n
    cy = sum(p[1] for p in projections) / n

    angles = [math.atan2(p[1] - cy, p[0] - cx) for p in projections]
    sorted_indices = sorted(range(n), key=lambda i: angles[i])

    return [vertex_coordinates[i] for i in sorted_indices]


def compute_plane_edgenormals(vertex_1, vertex_2, vertex_3):
    plane_normal = compute_normal(vertex_1, vertex_2, vertex_3)
    plane_distance = -(plane_normal.x * vertex_1[0] + plane_normal.y * vertex_1[1] + plane_normal.z * vertex_1[2])
    # BOUNDS/COLLISION FIX (symptoms: SINK / BUMPY / some FALL-THROUGH):
    # Do NOT round the collision plane to 3 decimals. The plane is written to the BND as
    # float32 anyway, so rounding only ADDS error on top of the float32 quantization. The
    # plane error scales with distance from origin (height = -(nx*x + nz*z + d)/ny), so at
    # SF/London map edges (|xz| ~ 1000-1500) a 0.0005 normal-rounding error becomes ~0.5-0.75u
    # of vertical error -> the car sinks into / steps off the visual mesh, and because each
    # triangle rounds independently, adjacent coplanar tris land on inconsistent planes -> a
    # height step at every shared edge (the "bumpy" symptom). Keeping full precision makes the
    # stored plane solve to the visual vertex Y to ~float32 epsilon (~1cm) even at large |xz|.
    return plane_normal, plane_distance


def compute_edges(vertex_coordinates: List, edge_pad: float = EDGE_PAD) -> tuple:
    """Returns (plane_edges, axis_flag) where axis_flag is bits 0-1 of the polygon flags.

    edge_pad expands the polygon's point-in-poly hit-test outward by that many metres.
    Defaults to EDGE_PAD for city geometry; pass 0.0 for meshes where an exact boundary
    matters more than seam coverage (car collision BNDs).
    """
    plane_normal, _ = compute_plane_edgenormals(*vertex_coordinates[:3])

    num_verts = len(vertex_coordinates)
    plane_edges = []

    abs_plane_x = abs(plane_normal.x)
    abs_plane_y = abs(plane_normal.y)
    abs_plane_z = abs(plane_normal.z)

    negate = 1.0

    if abs_plane_x < abs_plane_y or abs_plane_x < abs_plane_z:
        if abs_plane_y < abs_plane_x or abs_plane_y < abs_plane_z:
            # Z-dominant: project onto XY plane (Flags & 0x3 = 0x1)
            axis_flag = 0x1
            if plane_normal.z < 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertex_coordinates[i]
                B = vertex_coordinates[(i + 1) % num_verts]
                ex = -(B[1] - A[1]) * negate
                ey =  (B[0] - A[0]) * negate
                ez = A[0] * ex + A[1] * ey
                plane_edges.append((ex, ey, ez))
        else:
            # Y-dominant: project onto XZ plane (Flags & 0x3 = 0x2)
            axis_flag = 0x2
            if plane_normal.y > 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertex_coordinates[i]
                B = vertex_coordinates[(i + 1) % num_verts]
                ex = -(B[2] - A[2]) * negate
                ey =  (B[0] - A[0]) * negate
                ez = A[0] * ex + A[2] * ey
                plane_edges.append((ex, ey, ez))
    else:
        # X-dominant: project onto YZ plane (Flags & 0x3 = 0x0)
        axis_flag = 0x0
        if plane_normal.x < 0.0:
            negate = -1.0
        for i in range(num_verts):
            A = vertex_coordinates[i]
            B = vertex_coordinates[(i + 1) % num_verts]
            ex = -(B[2] - A[2]) * negate
            ey =  (B[1] - A[1]) * negate
            ez = A[1] * ex + A[2] * ey
            plane_edges.append((ex, ey, ez))

    # Normalize all three components by the 2D magnitude of (ex, ey), then subtract
    # a small outward padding from ez. This expands each polygon's FullSegment hit-test
    # by edge_pad metres, covering tiny seams and floating-point boundary gaps that would
    # otherwise cause fall-through or no-cell. The padding shifts the edge threshold so a
    # probe up to edge_pad outside the exact boundary still registers as "inside". The
    # plane equation (PlaneN/PlaneD) and GetPlaneY are unaffected.
    # Safe for wall polygons: downward rays never cross near-vertical planes, so padded
    # wall edges are never reached by the FullSegment point-in-polygon test.
    for i in range(len(plane_edges)):
        ex, ey, ez = plane_edges[i]
        norm_val = math.hypot(ex, ey)
        if norm_val > 1e-9:
            plane_edges[i] = (ex / norm_val, ey / norm_val, ez / norm_val - edge_pad)

    edges = [Vector3(e[0], e[1], e[2]) for e in plane_edges]

    # All shapes must always have 4 vectors
    if len(vertex_coordinates) == Shape.TRIANGLE:
        edges.append(Default.VECTOR_3)

    return edges, axis_flag

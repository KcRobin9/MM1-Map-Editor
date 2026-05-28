import math
from typing import List

from src.core.vector.vector_3 import Vector3
from src.constants.misc import Shape, Default


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
    plane_normal = Vector3(round(plane_normal.x, 3), round(plane_normal.y, 3), round(plane_normal.z, 3))
    plane_distance = round(plane_distance, 3)
    return plane_normal, plane_distance


def compute_edges(vertex_coordinates: List) -> tuple:
    """Returns (plane_edges, axis_flag) where axis_flag is bits 0-1 of the polygon flags."""
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

    # Normalize all three components by the 2D magnitude of (ex, ey)
    for i in range(len(plane_edges)):
        ex, ey, ez = plane_edges[i]
        norm_val = math.hypot(ex, ey)
        if norm_val > 1e-9:
            plane_edges[i] = (ex / norm_val, ey / norm_val, ez / norm_val)

    edges = [Vector3(e[0], e[1], e[2]) for e in plane_edges]

    # All shapes must always have 4 vectors
    if len(vertex_coordinates) == Shape.TRIANGLE:
        edges.append(Default.VECTOR_3)

    return edges, axis_flag

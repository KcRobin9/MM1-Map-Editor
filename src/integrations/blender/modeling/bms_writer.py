from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

# bpy is only referenced in type annotations (lazy via __future__ annotations),
# so the binary writer (write_bms) can be imported and unit-tested outside
# Blender. Inside Blender the real module is present.
try:
    import bpy
except ImportError:
    bpy = None

from src.constants.file_formats import MeshFlags, Magic
from src.io.binary import write_pack, write_binary_name


# ── Coordinate helpers ────────────────────────────────────────────────────────

def _from_blender_pos(bpos) -> Tuple[float, float, float]:
    """Inverse of _to_blender_pos: Blender (-x, z, y) → game (x, y, z)."""
    bx, by, bz = bpos
    return (-bx, bz, by)


def _from_blender_uv(buv) -> Tuple[float, float]:
    """Inverse of _to_blender_uv: flip V axis back to game convention."""
    u, v = buv
    return (u, 1.0 - v)


# ── Bounding sphere ───────────────────────────────────────────────────────────

def _compute_radius(points: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    """
    Compute the radius field stored in the BMS header.

    Original BMS files store (bsphere, center_y, bsphere) where bsphere is the
    bounding-sphere radius sqrt(rx²+ry²+rz²) of the per-axis AABB half-extents.
    Body meshes (mesh_offset=0,0,0) use plain AABB half-extents instead.
    We detect which case applies: if mesh_offset is non-zero we use bsphere;
    otherwise fall back to AABB (used by body/combined meshes).
    """
    if not points:
        return (1.0, 1.0, 1.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    rx = (max(xs) - min(xs)) * 0.5
    ry = (max(ys) - min(ys)) * 0.5
    rz = (max(zs) - min(zs)) * 0.5
    return (rx, ry, rz)


def _compute_radius_bsphere(points: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    """Bounding-sphere radius for wheel/part meshes: (bsphere, ry, bsphere)."""
    if not points:
        return (1.0, 1.0, 1.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    rx = (max(xs) - min(xs)) * 0.5
    ry = (max(ys) - min(ys)) * 0.5
    rz = (max(zs) - min(zs)) * 0.5
    bsphere = math.sqrt(rx * rx + ry * ry + rz * rz)
    return (bsphere, ry, bsphere)


# ── Packed normal quantization ────────────────────────────────────────────────
# 198-entry lookup table from Open1560/code/midtown/agiworld/packnorm.cpp.
# Stored in game space (X=lateral, Y=up, Z=front).
_PACKED_NORMALS: List[Tuple[float, float, float]] = [
    ( 0.0000,  0.0000,  1.0000), ( 1.0000,  0.0000,  0.0000), ( 0.0000,  1.0000,  0.0000),
    (-1.0000,  0.0000,  0.0000), ( 0.0000, -1.0000,  0.0000), ( 0.0000,  0.0000, -1.0000),
    ( 0.2225,  0.0000,  0.9749), ( 0.4339,  0.0000,  0.9010), ( 0.6235,  0.0000,  0.7818),
    ( 0.7818,  0.0000,  0.6235), ( 0.9010,  0.0000,  0.4339), ( 0.9749,  0.0000,  0.2225),
    ( 0.0000,  0.2225,  0.9749), ( 0.0000,  0.4339,  0.9010), ( 0.0000,  0.6235,  0.7818),
    ( 0.0000,  0.7818,  0.6235), ( 0.0000,  0.9010,  0.4339), ( 0.0000,  0.9749,  0.2225),
    (-0.2225,  0.0000,  0.9749), (-0.4339,  0.0000,  0.9010), (-0.6235,  0.0000,  0.7818),
    (-0.7818,  0.0000,  0.6235), (-0.9010,  0.0000,  0.4339), (-0.9749,  0.0000,  0.2225),
    ( 0.0000, -0.2225,  0.9749), ( 0.0000, -0.4339,  0.9010), ( 0.0000, -0.6235,  0.7818),
    ( 0.0000, -0.7818,  0.6235), ( 0.0000, -0.9010,  0.4339), ( 0.0000, -0.9749,  0.2225),
    ( 0.2225,  0.0000, -0.9749), ( 0.4339,  0.0000, -0.9010), ( 0.6235,  0.0000, -0.7818),
    ( 0.7818,  0.0000, -0.6235), ( 0.9010,  0.0000, -0.4339), ( 0.9749,  0.0000, -0.2225),
    ( 0.0000,  0.2225, -0.9749), ( 0.0000,  0.4339, -0.9010), ( 0.0000,  0.6235, -0.7818),
    ( 0.0000,  0.7818, -0.6235), ( 0.0000,  0.9010, -0.4339), ( 0.0000,  0.9749, -0.2225),
    (-0.2225,  0.0000, -0.9749), (-0.4339,  0.0000, -0.9010), (-0.6235,  0.0000, -0.7818),
    (-0.7818,  0.0000, -0.6235), (-0.9010,  0.0000, -0.4339), (-0.9749,  0.0000, -0.2225),
    ( 0.0000, -0.2225, -0.9749), ( 0.0000, -0.4339, -0.9010), ( 0.0000, -0.6235, -0.7818),
    ( 0.0000, -0.7818, -0.6235), ( 0.0000, -0.9010, -0.4339), ( 0.0000, -0.9749, -0.2225),
    ( 0.9749,  0.2225,  0.0000), ( 0.9010,  0.4339,  0.0000), ( 0.7818,  0.6235,  0.0000),
    ( 0.6235,  0.7818,  0.0000), ( 0.4339,  0.9010,  0.0000), ( 0.2225,  0.9749,  0.0000),
    (-0.2225,  0.9749,  0.0000), (-0.4339,  0.9010,  0.0000), (-0.6235,  0.7818,  0.0000),
    (-0.7818,  0.6235,  0.0000), (-0.9010,  0.4339,  0.0000), (-0.9749,  0.2225,  0.0000),
    (-0.9749, -0.2225,  0.0000), (-0.9010, -0.4339,  0.0000), (-0.7818, -0.6235,  0.0000),
    (-0.6235, -0.7818,  0.0000), (-0.4339, -0.9010,  0.0000), (-0.2225, -0.9749,  0.0000),
    ( 0.2225, -0.9749,  0.0000), ( 0.4339, -0.9010,  0.0000), ( 0.6235, -0.7818,  0.0000),
    ( 0.7818, -0.6235,  0.0000), ( 0.9010, -0.4339,  0.0000), ( 0.9749, -0.2225,  0.0000),
    ( 0.2279,  0.2279,  0.9466), ( 0.4505,  0.2361,  0.8610), ( 0.2361,  0.4505,  0.8610),
    ( 0.6533,  0.2450,  0.7164), ( 0.4691,  0.4691,  0.7482), ( 0.2450,  0.6533,  0.7164),
    ( 0.8197,  0.2502,  0.5153), ( 0.6762,  0.4815,  0.5575), ( 0.4815,  0.6762,  0.5575),
    ( 0.2502,  0.8197,  0.5153), ( 0.9316,  0.2448,  0.2685), ( 0.8288,  0.4740,  0.2974),
    ( 0.6729,  0.6729,  0.3072), ( 0.4740,  0.8288,  0.2974), ( 0.2448,  0.9316,  0.2685),
    (-0.2279,  0.2279,  0.9466), (-0.2361,  0.4505,  0.8610), (-0.4505,  0.2361,  0.8610),
    (-0.2450,  0.6533,  0.7164), (-0.4691,  0.4691,  0.7482), (-0.6533,  0.2450,  0.7164),
    (-0.2502,  0.8197,  0.5153), (-0.4815,  0.6762,  0.5575), (-0.6762,  0.4815,  0.5575),
    (-0.8197,  0.2502,  0.5153), (-0.2448,  0.9316,  0.2685), (-0.4740,  0.8288,  0.2974),
    (-0.6729,  0.6729,  0.3072), (-0.8288,  0.4740,  0.2974), (-0.9316,  0.2448,  0.2685),
    (-0.2279, -0.2279,  0.9466), (-0.4505, -0.2361,  0.8610), (-0.2361, -0.4505,  0.8610),
    (-0.6533, -0.2450,  0.7164), (-0.4691, -0.4691,  0.7482), (-0.2450, -0.6533,  0.7164),
    (-0.8197, -0.2502,  0.5153), (-0.6762, -0.4815,  0.5575), (-0.4815, -0.6762,  0.5575),
    (-0.2502, -0.8197,  0.5153), (-0.9316, -0.2448,  0.2685), (-0.8288, -0.4740,  0.2974),
    (-0.6729, -0.6729,  0.3072), (-0.4740, -0.8288,  0.2974), (-0.2448, -0.9316,  0.2685),
    ( 0.2279, -0.2279,  0.9466), ( 0.2361, -0.4505,  0.8610), ( 0.4505, -0.2361,  0.8610),
    ( 0.2450, -0.6533,  0.7164), ( 0.4691, -0.4691,  0.7482), ( 0.6533, -0.2450,  0.7164),
    ( 0.2502, -0.8197,  0.5153), ( 0.4815, -0.6762,  0.5575), ( 0.6762, -0.4815,  0.5575),
    ( 0.8197, -0.2502,  0.5153), ( 0.2448, -0.9316,  0.2685), ( 0.4740, -0.8288,  0.2974),
    ( 0.6729, -0.6729,  0.3072), ( 0.8288, -0.4740,  0.2974), ( 0.9316, -0.2448,  0.2685),
    ( 0.2279,  0.2279, -0.9466), ( 0.2361,  0.4505, -0.8610), ( 0.4505,  0.2361, -0.8610),
    ( 0.2450,  0.6533, -0.7164), ( 0.4691,  0.4691, -0.7482), ( 0.6533,  0.2450, -0.7164),
    ( 0.2502,  0.8197, -0.5153), ( 0.4815,  0.6762, -0.5575), ( 0.6762,  0.4815, -0.5575),
    ( 0.8197,  0.2502, -0.5153), ( 0.2448,  0.9316, -0.2685), ( 0.4740,  0.8288, -0.2974),
    ( 0.6729,  0.6729, -0.3072), ( 0.8288,  0.4740, -0.2974), ( 0.9316,  0.2448, -0.2685),
    (-0.2279,  0.2279, -0.9466), (-0.4505,  0.2361, -0.8610), (-0.2361,  0.4505, -0.8610),
    (-0.6533,  0.2450, -0.7164), (-0.4691,  0.4691, -0.7482), (-0.2450,  0.6533, -0.7164),
    (-0.8197,  0.2502, -0.5153), (-0.6762,  0.4815, -0.5575), (-0.4815,  0.6762, -0.5575),
    (-0.2502,  0.8197, -0.5153), (-0.9316,  0.2448, -0.2685), (-0.8288,  0.4740, -0.2974),
    (-0.6729,  0.6729, -0.3072), (-0.4740,  0.8288, -0.2974), (-0.2448,  0.9316, -0.2685),
    (-0.2279, -0.2279, -0.9466), (-0.2361, -0.4505, -0.8610), (-0.4505, -0.2361, -0.8610),
    (-0.2450, -0.6533, -0.7164), (-0.4691, -0.4691, -0.7482), (-0.6533, -0.2450, -0.7164),
    (-0.2502, -0.8197, -0.5153), (-0.4815, -0.6762, -0.5575), (-0.6762, -0.4815, -0.5575),
    (-0.8197, -0.2502, -0.5153), (-0.2448, -0.9316, -0.2685), (-0.4740, -0.8288, -0.2974),
    (-0.6729, -0.6729, -0.3072), (-0.8288, -0.4740, -0.2974), (-0.9316, -0.2448, -0.2685),
    ( 0.2279, -0.2279, -0.9466), ( 0.4505, -0.2361, -0.8610), ( 0.2361, -0.4505, -0.8610),
    ( 0.6533, -0.2450, -0.7164), ( 0.4691, -0.4691, -0.7482), ( 0.2450, -0.6533, -0.7164),
    ( 0.8197, -0.2502, -0.5153), ( 0.6762, -0.4815, -0.5575), ( 0.4815, -0.6762, -0.5575),
    ( 0.2502, -0.8197, -0.5153), ( 0.9316, -0.2448, -0.2685), ( 0.8288, -0.4740, -0.2974),
    ( 0.6729, -0.6729, -0.3072), ( 0.4740, -0.8288, -0.2974), ( 0.2448, -0.9316, -0.2685),
]


def _quantize_normal(gx: float, gy: float, gz: float) -> int:
    """Return the _PACKED_NORMALS index (0-197) closest to (gx, gy, gz) by dot product."""
    best_dot = -2.0
    best_idx = 0
    for i, (nx, ny, nz) in enumerate(_PACKED_NORMALS):
        dot = gx * nx + gy * ny + gz * nz
        if dot > best_dot:
            best_dot = dot
            best_idx = i
    return best_idx


def _auto_normal_indices(mesh: bpy.types.Mesh) -> List[int]:
    """
    Compute per-loop packed normal indices from Blender face normals.
    Converts Blender space → game space via (-bx, bz, by), then quantizes.
    """
    import bmesh as _bmesh
    n_loops = len(mesh.loops)
    ni_flat = [0] * n_loops

    bm = _bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    for face in bm.faces:
        fn = face.normal
        gx, gy, gz = -fn.x, fn.z, fn.y
        ni = _quantize_normal(gx, gy, gz)
        for loop in face.loops:
            ni_flat[loop.index] = ni

    bm.free()
    return ni_flat


# ── Mesh → BMS data ───────────────────────────────────────────────────────────

def _cache_loop_data(mesh: bpy.types.Mesh, flags: int):
    """
    Pre-cache all per-loop data by round-tripping through a temporary bmesh.

    bmesh.from_mesh() is the same mechanism used by build_blender_mesh() on
    import, so it is guaranteed to expose UV and colour data correctly in
    Blender 4.3 even when the legacy mesh.uv_layers / mesh.vertex_colors APIs
    return empty collections for valid meshes.

    Returns (loop_verts, uv_flat, col_flat, ni_flat, flags_out) where:
      loop_verts – int list [n_loops]      vertex index per global loop
      uv_flat    – float list [n_loops*2]  (u, v) pairs, flattened
      col_flat   – float list [n_loops*4]  (r, g, b, a) quads, flattened
      ni_flat    – int list [n_loops]      packed normal index per loop
      flags_out  – original flags with any unavailable bits cleared
    """
    import bmesh as _bmesh

    n_loops = len(mesh.loops)

    loop_verts = [0]   * n_loops
    uv_flat    = [0.0] * (n_loops * 2)
    col_flat   = [1.0] * (n_loops * 4)   # white default
    ni_flat    = [0]   * n_loops

    # ── Build bmesh from mesh — reliable data access in all Blender versions ──
    bm = _bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    # ── Vertex index per loop (from bmesh loop → vert) ────────────────────────
    for face in bm.faces:
        for loop in face.loops:
            loop_verts[loop.index] = loop.vert.index

    # ── UV coordinates ────────────────────────────────────────────────────────
    if flags & MeshFlags.TEXCOORDS:
        uv_layer = bm.loops.layers.uv.active
        if uv_layer:
            for face in bm.faces:
                for loop in face.loops:
                    li = loop.index
                    uv = loop[uv_layer].uv
                    uv_flat[li * 2]     = uv.x
                    uv_flat[li * 2 + 1] = uv.y
        else:
            flags &= ~MeshFlags.TEXCOORDS  # no UV layer in mesh — drop TEXCOORDS flag

    # ── Vertex colours ────────────────────────────────────────────────────────
    if flags & MeshFlags.COLORS:
        col_layer = bm.loops.layers.color.get("Col")
        if col_layer is None and bm.loops.layers.color:
            col_layer = bm.loops.layers.color[0]
        if col_layer:
            for face in bm.faces:
                for loop in face.loops:
                    li = loop.index
                    c  = loop[col_layer]
                    col_flat[li * 4]     = c[0]
                    col_flat[li * 4 + 1] = c[1]
                    col_flat[li * 4 + 2] = c[2]
                    col_flat[li * 4 + 3] = c[3]
        else:
            flags &= ~MeshFlags.COLORS  # no colour layer — drop COLORS flag

    bm.free()

    # ── Packed normal indices (custom CORNER INT attribute on base mesh) ───────
    if flags & MeshFlags.NORMALS:
        ni_attr = mesh.attributes.get("bms_ni")
        if ni_attr is None:
            flags &= ~MeshFlags.NORMALS
        else:
            try:
                ni_attr.data.foreach_get("value", ni_flat)
            except Exception:
                flags &= ~MeshFlags.NORMALS

    return loop_verts, uv_flat, col_flat, ni_flat, flags


def mesh_to_bms_data(obj: bpy.types.Object, bake_location: bool = False) -> dict:
    """
    Extract BMS-compatible data from a Blender object.

    Uses foreach_get for all per-loop data to work reliably in Blender 4.3+,
    where item-by-item attribute access (mesh.uv_layers.active.data[i]) can
    silently return empty collections even for valid meshes.
    """
    mesh  = obj.data
    flags = int(mesh.get("bms_flags", 0))

    # PLANES (bit 4 = 0x10) is collision/BSP data written after vertices in the
    # original BMS.  We don't store or compute plane data, so we must clear this
    # flag — otherwise the reader skips 16×num_surfaces bytes that don't exist
    # and falls off the end of the file.
    flags &= ~MeshFlags.PLANES

    # If flags is 0 (missing property or loaded from a broken export),
    # auto-detect from actual mesh data as a fallback.
    if flags == 0:
        import bmesh as _bm_probe
        _bmp = _bm_probe.new()
        _bmp.from_mesh(mesh)
        if _bmp.loops.layers.uv.active:
            flags |= MeshFlags.TEXCOORDS
        if _bmp.loops.layers.color:
            flags |= MeshFlags.COLORS
        _bmp.free()
    # If a bms_ni attribute exists on the mesh, honour it now; otherwise normals
    # are auto-computed below (after _cache_loop_data) from face normals.
    if not (flags & MeshFlags.NORMALS) and mesh.attributes.get("bms_ni"):
        flags |= MeshFlags.NORMALS

    # ── Texture names from material slots ─────────────────────────────────────
    texture_names: List[str] = [
        mat.name for mat in mesh.materials if mat is not None
    ]
    if not texture_names:
        flags &= ~MeshFlags.TEXCOORDS
        flags &= ~MeshFlags.COLORS

    # ── World-space vertex positions ──────────────────────────────────────────
    # Always transform by matrix_world so scale, rotation, and parent transforms
    # are baked into the exported vertices.  This correctly handles imported
    # models (.dae/.fbx) whose scale/rotation lives in the object transform even
    # after a Blender "Apply" that didn't fully propagate through parents.
    mat_world = obj.matrix_world

    # ── Pre-cache all per-loop data via foreach_get ───────────────────────────
    loop_verts, uv_flat, col_flat, ni_flat, flags = _cache_loop_data(mesh, flags)

    # Cars always need NORMALS (agiMeshLighterTriple dereferences Normals[i] with
    # no null check → ACCESS_VIOLATION if the flag is absent).  Auto-compute from
    # face normals when no bms_ni attribute was stored on the mesh.
    if not (flags & MeshFlags.NORMALS):
        ni_flat = _auto_normal_indices(mesh)
        flags |= MeshFlags.NORMALS

    # Ensure COLORS is set; col_flat is already initialised to white (1.0) by
    # _cache_loop_data, so no additional data computation is required here.
    if not (flags & MeshFlags.COLORS):
        flags |= MeshFlags.COLORS

    # ── Build points (Blender vertices → game space) ──────────────────────────
    # Wheels (bake_location=True): vertices must be in the wheel's local space
    # (centred at the wheel hub).  We apply only the scale+rotation from
    # matrix_local; the translation (wheel hub position in body-local space)
    # is written separately as mesh_offset so the game places the wheel correctly.
    #
    # Body (bake_location=False): strip world translation from matrix_world so
    # verts are body-origin-relative; mesh_offset carries the world position.
    import mathutils as _mu

    if bake_location:
        mat_local = obj.matrix_local
        # Wheels: vertices must be in car-local space (hub-translated, not origin-centred).
        # GetMeshSet validates bms_offset against the offset passed by the caller (car body CG,
        # typically {0,0,0}).  If bms_offset != caller offset the BMS is rejected and null returned.
        # So mesh_offset must be {0,0,0}; the hub translation lives in the vertex positions.
        mesh_offset = (0.0, 0.0, 0.0)
        points: List[Tuple[float, float, float]] = [
            _from_blender_pos(tuple(mat_local @ v.co))
            for v in mesh.vertices
        ]
    else:
        wloc = mat_world.translation
        mesh_offset = _from_blender_pos((wloc.x, wloc.y, wloc.z))
        mat = mat_world.copy()
        mat.translation = _mu.Vector((0, 0, 0))
        points: List[Tuple[float, float, float]] = [
            _from_blender_pos(tuple(mat @ v.co))
            for v in mesh.vertices
        ]

    # ── Build adjuncts + surface/texture index arrays ─────────────────────────
    adjunct_map: dict    = {}
    adjuncts:    List[dict] = []
    surface_indices: List[int] = []
    texture_indices: List[int] = []

    for poly in mesh.polygons:
        loop_indices = list(poly.loop_indices)
        n = len(loop_indices)

        if n < 3:
            continue
        if n > 4:
            # Fan-triangulate n-gons (BMS supports only tris and quads).
            for fan_i in range(1, n - 1):
                slots = [loop_indices[0], loop_indices[fan_i], loop_indices[fan_i + 1]]
                pa = _make_adjuncts(slots, loop_verts, uv_flat, col_flat, ni_flat,
                                    flags, adjunct_map, adjuncts)
                surface_indices.extend([pa[0], pa[1], pa[2], 0])
                texture_indices.append(poly.material_index + 1)
            continue

        pa = _make_adjuncts(loop_indices, loop_verts, uv_flat, col_flat, ni_flat,
                            flags, adjunct_map, adjuncts)
        if n == 3:
            surface_indices.extend([pa[0], pa[1], pa[2], 0])
        else:
            surface_indices.extend([pa[0], pa[1], pa[2], pa[3]])
        texture_indices.append(poly.material_index + 1)

    num_surfaces = len(texture_indices)
    num_adjuncts = len(adjuncts)
    num_indices  = num_surfaces * 4

    return {
        "points":          points,
        "mesh_offset":     mesh_offset,
        "num_adjuncts":    num_adjuncts,
        "num_surfaces":    num_surfaces,
        "tex_coords":      [a["uv"]    for a in adjuncts],
        "vert_colors":     [a["color"] for a in adjuncts] if (flags & MeshFlags.COLORS)  else [],
        "normal_indices":  [a["ni"]    for a in adjuncts] if (flags & MeshFlags.NORMALS) else [],
        "vertex_indices":  [a["pt"]    for a in adjuncts],
        "texture_indices": texture_indices,
        "surface_indices": surface_indices,
        "texture_names":   texture_names,
        "flags":           flags,
    }


def _make_adjuncts(
    loop_indices: List[int],
    loop_verts:   List[int],
    uv_flat:      List[float],
    col_flat:     List[float],
    ni_flat:      List[int],
    flags:        int,
    adjunct_map:  dict,
    adjuncts:     List[dict],
) -> List[int]:
    """
    For each loop index, find-or-create an adjunct entry using pre-cached arrays.
    Returns adjunct indices (one per loop_index).
    """
    result = []
    for li in loop_indices:
        vert_idx = loop_verts[li]

        uv = (0.0, 0.0)
        if flags & MeshFlags.TEXCOORDS:
            uv = _from_blender_uv((uv_flat[li * 2], uv_flat[li * 2 + 1]))

        color = (1.0, 1.0, 1.0, 1.0)
        if flags & MeshFlags.COLORS:
            base  = li * 4
            color = (round(col_flat[base],     4),
                     round(col_flat[base + 1], 4),
                     round(col_flat[base + 2], 4),
                     round(col_flat[base + 3], 4))

        ni  = ni_flat[li] if (flags & MeshFlags.NORMALS) else 0
        key = (vert_idx, uv, color, ni)

        if key not in adjunct_map:
            adjunct_map[key] = len(adjuncts)
            adjuncts.append({"pt": vert_idx, "uv": uv, "color": color, "ni": ni})

        result.append(adjunct_map[key])
    return result


# ── Binary writer ─────────────────────────────────────────────────────────────

def _compute_cache_size(num_points: int, num_adjuncts: int, num_surfaces: int,
                        num_indices: int, flags: int) -> int:
    """Mirror of Meshes.calculate_cache_size() for the Blender-side writer."""
    def align(n: int) -> int:
        return (n + 7) & ~7

    size  = align(num_points * 12)  # 3 floats per vertex
    if num_points >= 16:
        size += align(8 * 12)       # 8 AABB corner sentinels

    if flags & MeshFlags.NORMALS:
        size += align(num_adjuncts)           # 1 byte per adjunct
    if flags & MeshFlags.TEXCOORDS:
        size += align(num_adjuncts * 8)       # 2 floats per adjunct
    if flags & MeshFlags.COLORS:
        size += align(num_adjuncts * 4)       # 4 bytes per adjunct (BGRA)

    size += align(num_adjuncts * 2)           # vertex_indices (uint16)

    if flags & MeshFlags.PLANES:
        size += align(num_surfaces * 16)      # 4 floats per surface
    size += align(num_indices * 2)            # surface_indices (uint16)
    size += align(num_surfaces)               # texture_indices (uint8)
    return size


def write_bms(bms_data: dict, output_path: Path) -> None:
    """
    Serialise a BMS data dict (same schema as read_bms() returns) to a binary
    BMS file.  The dict is produced by mesh_to_bms_data() or can be the raw
    dict from read_bms() (round-trip test).
    """
    points          = bms_data["points"]
    mesh_offset     = bms_data["mesh_offset"]
    num_adjuncts    = bms_data["num_adjuncts"]
    num_surfaces    = bms_data["num_surfaces"]
    num_indices     = num_surfaces * 4
    tex_coords      = bms_data.get("tex_coords",     [])
    vert_colors     = bms_data.get("vert_colors",    [])
    normal_indices  = bms_data.get("normal_indices", [])
    vertex_indices  = bms_data["vertex_indices"]
    texture_indices = bms_data["texture_indices"]
    surface_indices = bms_data["surface_indices"]
    texture_names   = bms_data.get("texture_names",  [])
    flags           = bms_data.get("flags", 0)

    num_points   = len(points)
    num_textures = len(texture_names)

    # Game header stores (Radius, RadiusSqr, BoundingBoxRadius) — three separate floats.
    # Radius     = sqrt(max vertex squared-distance from origin)
    # RadiusSqr  = Radius²  (used for fast culling comparisons)
    # BoundingBoxRadius = same as Radius (conservative; game computes from GetBoundInfo)
    if points:
        max_mag_sq = max(p[0] * p[0] + p[1] * p[1] + p[2] * p[2] for p in points)
    else:
        max_mag_sq = 1.0
    _r = math.sqrt(max_mag_sq)
    radius = (_r, max_mag_sq, _r)

    # Meshes with non-zero mesh_offset (wheels, fenders, lights) have their
    # vertices in local space.  MESH_SET_OFFSET tells the game NOT to subtract
    # the offset from vertex positions again (which would corrupt the geometry).
    if any(abs(v) > 1e-6 for v in mesh_offset):
        flags |= MeshFlags.OFFSET

    cache_size = _compute_cache_size(num_points, num_adjuncts, num_surfaces, num_indices, flags)

    # ── Validate consistency BEFORE touching the output file ─────────────────
    if len(vertex_indices) != num_adjuncts:
        raise ValueError(f"vertex_indices length {len(vertex_indices)} != num_adjuncts {num_adjuncts}")
    if (flags & MeshFlags.TEXCOORDS) and len(tex_coords) != num_adjuncts:
        raise ValueError(f"tex_coords length {len(tex_coords)} != num_adjuncts {num_adjuncts}")
    if (flags & MeshFlags.NORMALS) and len(normal_indices) != num_adjuncts:
        raise ValueError(f"normal_indices length {len(normal_indices)} != num_adjuncts {num_adjuncts}")
    if (flags & MeshFlags.COLORS) and len(vert_colors) != num_adjuncts:
        raise ValueError(f"vert_colors length {len(vert_colors)} != num_adjuncts {num_adjuncts}")
    if len(surface_indices) != num_indices:
        raise ValueError(f"surface_indices length {len(surface_indices)} != num_indices {num_indices}")
    if len(texture_indices) != num_surfaces:
        raise ValueError(f"texture_indices length {len(texture_indices)} != num_surfaces {num_surfaces}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        # ── Header ───────────────────────────────────────────────────────────
        write_binary_name(f, Magic.MESH, length = 4)
        write_pack(f, '<fff',  *mesh_offset)
        write_pack(f, '<4I',   num_points, num_adjuncts, num_surfaces, num_indices)
        write_pack(f, '<fff',  *radius)
        # agiMeshSet stores TextureCount and Flags as adjacent u8 fields
        # (meshset.h), so both are 1 byte. Writing flags as u16 here shifts the
        # 2-byte padding, cache_size, and every texture name 1 byte late, which
        # makes the game read garbage texture names and crash. Texture names must
        # begin at file offset 52 (0x34).
        write_pack(f, '<2B',   num_textures, flags)
        f.write(b'\x00' * 2)                                     # padding
        write_pack(f, '<I',    cache_size)

        # ── Texture names (32-byte name + 16-byte padding each) ──────────────
        for name in texture_names:
            write_binary_name(f, name, length = 32, padding = 16)

        # ── Vertex positions ──────────────────────────────────────────────────
        write_pack(f, f'<{num_points * 3}f', *[c for p in points for c in p])

        # Large meshes (≥16 pts) append 8 AABB corner sentinel vertices.
        if num_points >= 16:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            zs = [p[2] for p in points]
            mn, mx = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
            corners = [
                (mn[0], mn[1], mn[2]), (mx[0], mn[1], mn[2]),
                (mn[0], mx[1], mn[2]), (mx[0], mx[1], mn[2]),
                (mn[0], mn[1], mx[2]), (mx[0], mn[1], mx[2]),
                (mn[0], mx[1], mx[2]), (mx[0], mx[1], mx[2]),
            ]
            write_pack(f, '<24f', *[c for p in corners for c in p])

        # ── Per-adjunct data ──────────────────────────────────────────────────
        if flags & MeshFlags.NORMALS:
            write_pack(f, f'{num_adjuncts}B', *[ni & 0xFF for ni in normal_indices])

        if flags & MeshFlags.TEXCOORDS:
            write_pack(f, f'<{num_adjuncts * 2}f', *[c for uv in tex_coords for c in uv])

        if flags & MeshFlags.COLORS:  # BGRA byte order in file
            packed = []
            for r, g, b, a in vert_colors:
                packed += [int(round(b * 255)) & 0xFF,
                           int(round(g * 255)) & 0xFF,
                           int(round(r * 255)) & 0xFF,
                           int(round(a * 255)) & 0xFF]
            write_pack(f, f'{num_adjuncts * 4}B', *packed)

        # ── Adjunct → point mapping ───────────────────────────────────────────
        write_pack(f, f'<{num_adjuncts}H', *[vi & 0xFFFF for vi in vertex_indices])

        # ── Per-surface texture index ─────────────────────────────────────────
        write_pack(f, f'{num_surfaces}B', *[ti & 0xFF for ti in texture_indices])

        # ── Flat adjunct-index array (4 per surface) ──────────────────────────
        write_pack(f, f'<{num_indices}H', *[si & 0xFFFF for si in surface_indices])

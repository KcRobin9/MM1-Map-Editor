import struct
import math
import bpy
from pathlib import Path
from typing import List, Tuple


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
    if flags & 1:
        uv_layer = bm.loops.layers.uv.active
        if uv_layer:
            for face in bm.faces:
                for loop in face.loops:
                    li = loop.index
                    uv = loop[uv_layer].uv
                    uv_flat[li * 2]     = uv.x
                    uv_flat[li * 2 + 1] = uv.y
        else:
            flags &= ~1  # no UV layer in mesh — drop TEXCOORDS flag

    # ── Vertex colours ────────────────────────────────────────────────────────
    if flags & 4:
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
            flags &= ~4  # no colour layer — drop COLORS flag

    bm.free()

    # ── Packed normal indices (custom CORNER INT attribute on base mesh) ───────
    if flags & 2:
        ni_attr = mesh.attributes.get("bms_ni")
        if ni_attr is None:
            flags &= ~2
        else:
            try:
                ni_attr.data.foreach_get("value", ni_flat)
            except Exception:
                flags &= ~2

    return loop_verts, uv_flat, col_flat, ni_flat, flags


def mesh_to_bms_data(obj: bpy.types.Object) -> dict:
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
    flags &= ~16

    # If flags is 0 (missing property or loaded from a broken export),
    # auto-detect from actual mesh data as a fallback.
    if flags == 0:
        import bmesh as _bm_probe
        _bmp = _bm_probe.new()
        _bmp.from_mesh(mesh)
        if _bmp.loops.layers.uv.active:
            flags |= 1
        if _bmp.loops.layers.color:
            flags |= 4
        _bmp.free()
    # NORMALS: only set if bms_ni attribute actually exists (never auto-invent it).
    if not (flags & 2) and mesh.attributes.get("bms_ni"):
        flags |= 2

    # ── Texture names from material slots ─────────────────────────────────────
    texture_names: List[str] = [
        mat.name for mat in mesh.materials if mat is not None
    ]
    if not texture_names:
        flags &= ~1
        flags &= ~4

    # ── mesh_offset from current object location ──────────────────────────────
    loc = obj.location
    mesh_offset = _from_blender_pos((loc.x, loc.y, loc.z))

    # ── Pre-cache all per-loop data via foreach_get ───────────────────────────
    loop_verts, uv_flat, col_flat, ni_flat, flags = _cache_loop_data(mesh, flags)

    # ── Build points (Blender vertices → game space) ──────────────────────────
    points: List[Tuple[float, float, float]] = [
        _from_blender_pos(v.co) for v in mesh.vertices
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
        "vert_colors":     [a["color"] for a in adjuncts] if (flags & 4) else [],
        "normal_indices":  [a["ni"]    for a in adjuncts] if (flags & 2) else [],
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
        if flags & 1:
            uv = _from_blender_uv((uv_flat[li * 2], uv_flat[li * 2 + 1]))

        color = (1.0, 1.0, 1.0, 1.0)
        if flags & 4:
            base  = li * 4
            color = (round(col_flat[base],     4),
                     round(col_flat[base + 1], 4),
                     round(col_flat[base + 2], 4),
                     round(col_flat[base + 3], 4))

        ni  = ni_flat[li] if (flags & 2) else 0
        key = (vert_idx, uv, color, ni)

        if key not in adjunct_map:
            adjunct_map[key] = len(adjuncts)
            adjuncts.append({"pt": vert_idx, "uv": uv, "color": color, "ni": ni})

        result.append(adjunct_map[key])
    return result


# ── Binary writer ─────────────────────────────────────────────────────────────

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
    tex_coords      = bms_data.get("tex_coords",      [])
    vert_colors     = bms_data.get("vert_colors",     [])
    normal_indices  = bms_data.get("normal_indices",  [])
    vertex_indices  = bms_data["vertex_indices"]
    texture_indices = bms_data["texture_indices"]
    surface_indices = bms_data["surface_indices"]
    texture_names   = bms_data.get("texture_names",   [])
    flags           = bms_data.get("flags", 0)

    num_points    = len(points)
    num_textures  = len(texture_names)
    # Use bounding-sphere radius for part meshes that have a non-zero mesh_offset
    # (wheels, fenders, lights).  Body/combined meshes use plain AABB half-extents.
    _nonzero_offset = any(abs(v) > 1e-6 for v in mesh_offset)
    radius = (_compute_radius_bsphere(points) if _nonzero_offset
              else _compute_radius(points))
    num_indices   = num_surfaces * 4

    # ── Validate consistency BEFORE touching the output file ──────────────────
    if len(vertex_indices) != num_adjuncts:
        raise ValueError(
            f"vertex_indices length {len(vertex_indices)} != num_adjuncts {num_adjuncts}"
        )
    if (flags & 1) and len(tex_coords) != num_adjuncts:
        raise ValueError(
            f"tex_coords length {len(tex_coords)} != num_adjuncts {num_adjuncts}"
        )
    if (flags & 2) and len(normal_indices) != num_adjuncts:
        raise ValueError(
            f"normal_indices length {len(normal_indices)} != num_adjuncts {num_adjuncts}"
        )
    if (flags & 4) and len(vert_colors) != num_adjuncts:
        raise ValueError(
            f"vert_colors length {len(vert_colors)} != num_adjuncts {num_adjuncts}"
        )
    if len(surface_indices) != num_indices:
        raise ValueError(
            f"surface_indices length {len(surface_indices)} != num_indices {num_indices}"
        )
    if len(texture_indices) != num_surfaces:
        raise ValueError(
            f"texture_indices length {len(texture_indices)} != num_surfaces {num_surfaces}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        # ── Header ───────────────────────────────────────────────────────────
        f.write(struct.pack("<L",   0x4D534833))               # magic
        f.write(struct.pack("<fff", *mesh_offset))             # mesh origin
        f.write(struct.pack("<LLLL",                           # counts
                            num_points, num_adjuncts, num_surfaces, num_indices))
        f.write(struct.pack("<fff", *radius))                  # bounding half-extents
        f.write(struct.pack("<B",  num_textures))
        f.write(struct.pack("<B",  flags))
        f.write(b"\x00" * 6)                                   # padding + cache_size

        # ── Texture names (32 bytes + 16 bytes padding each) ─────────────────
        for name in texture_names:
            raw = name.encode("ascii")[:31]
            f.write(raw.ljust(32, b"\x00"))
            f.write(b"\x00" * 16)

        # ── Vertex positions ──────────────────────────────────────────────────
        for px, py, pz in points:
            f.write(struct.pack("<fff", px, py, pz))

        # Large meshes (≥16 pts) expect 8 bounding-box corner sentinel vertices.
        if num_points >= 16:
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                zs = [p[2] for p in points]
                mn = (min(xs), min(ys), min(zs))
                mx = (max(xs), max(ys), max(zs))
                corners = [
                    (mn[0], mn[1], mn[2]), (mx[0], mn[1], mn[2]),
                    (mn[0], mx[1], mn[2]), (mx[0], mx[1], mn[2]),
                    (mn[0], mn[1], mx[2]), (mx[0], mn[1], mx[2]),
                    (mn[0], mx[1], mx[2]), (mx[0], mx[1], mx[2]),
                ]
            else:
                corners = [(0.0, 0.0, 0.0)] * 8
            for cx, cy, cz in corners:
                f.write(struct.pack("<fff", cx, cy, cz))

        # ── Per-adjunct data ──────────────────────────────────────────────────
        if flags & 2:  # NORMALS
            for ni in normal_indices:
                f.write(struct.pack("<B", ni & 0xFF))

        if flags & 1:  # TEXCOORDS
            for u, v in tex_coords:
                f.write(struct.pack("<ff", u, v))

        if flags & 4:  # COLORS (BGRA order in file)
            for r, g, b, a in vert_colors:
                br = int(round(b * 255)) & 0xFF
                bg = int(round(g * 255)) & 0xFF
                bb = int(round(r * 255)) & 0xFF
                ba = int(round(a * 255)) & 0xFF
                f.write(struct.pack("4B", br, bg, bb, ba))

        # ── Adjunct → point mapping ───────────────────────────────────────────
        for vi in vertex_indices:
            f.write(struct.pack("<H", vi & 0xFFFF))

        # ── Per-surface texture index ─────────────────────────────────────────
        for ti in texture_indices:
            f.write(struct.pack("<B", ti & 0xFF))

        # ── Flat adjunct-index array (4 per surface) ──────────────────────────
        for si in surface_indices:
            f.write(struct.pack("<H", si & 0xFFFF))

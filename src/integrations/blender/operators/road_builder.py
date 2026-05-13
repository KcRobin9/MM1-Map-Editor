import bpy
import math
from mathutils import Vector
from typing import List, NamedTuple

from src.constants.file_formats import Material, Room
from src.constants.color import Color
from src.constants.textures import Texture
from src.integrations.blender.utils import (
    get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties,
)


RS_PREFIX    = "RS_"
RS_BAKED_TAG = "rs_baked_from"  # custom prop on baked polygons, value = spine name

_RS_SPINE_COLLECTION = "Road Spines"
_RS_BAKED_COLLECTION = "Road Meshes"


# ── Collections ────────────────────────────────────────────────────────────────

def _get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


# ── Spine helpers ──────────────────────────────────────────────────────────────

def get_all_road_spines() -> List[bpy.types.Object]:
    return [o for o in bpy.data.objects
            if o.type == 'CURVE' and o.name.startswith(RS_PREFIX)]


def is_road_spine(obj) -> bool:
    return obj is not None and obj.type == 'CURVE' and obj.name.startswith(RS_PREFIX)


def get_spine_vertices(obj: bpy.types.Object) -> List[Vector]:
    if not obj.data.splines:
        return []
    verts = []
    for i, spline in enumerate(obj.data.splines):
        if i == 0:
            verts.append(obj.matrix_world @ Vector(spline.points[0].co[:3]))
        verts.append(obj.matrix_world @ Vector(spline.points[1].co[:3]))
    return verts


def _rebuild_spine_from_verts(obj: bpy.types.Object, world_verts: List[Vector]) -> None:
    mw_inv = obj.matrix_world.inverted()
    curve  = obj.data
    curve.splines.clear()
    for i in range(len(world_verts) - 1):
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        for k, wv in enumerate(world_verts[i : i + 2]):
            lv = mw_inv @ wv
            spline.points[k].co = (lv.x, lv.y, lv.z, 1.0)
    _apply_spine_color(obj)


def _build_spine_object(name: str, points: List[Vector], context) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions  = '3D'
    curve_data.resolution_u = 1
    curve_data.bevel_depth  = 0.3

    for i in range(len(points) - 1):
        spline = curve_data.splines.new('POLY')
        spline.points.add(1)
        p0, p1 = points[i], points[i + 1]
        spline.points[0].co = (p0.x, p0.y, p0.z, 1.0)
        spline.points[1].co = (p1.x, p1.y, p1.z, 1.0)

    obj = bpy.data.objects.new(name, curve_data)
    _get_or_create_collection(_RS_SPINE_COLLECTION).objects.link(obj)
    return obj


_SPINE_COLORS = [
    (1.00, 0.55, 0.00, 1.0),   # orange
    (1.00, 0.95, 0.00, 1.0),   # bright yellow
    (0.00, 0.70, 1.00, 1.0),   # cyan
    (0.75, 0.30, 1.00, 1.0),   # purple
    (1.00, 0.20, 0.50, 1.0),   # hot pink
    (0.10, 0.85, 0.35, 1.0),   # bright green-teal
]

_SPINE_START_COLOR = (0.05, 0.85, 0.15, 1.0)   # green — marks spine start (vertex 0)
_SPINE_END_COLOR   = (0.90, 0.10, 0.10, 1.0)   # red   — marks spine end (last vertex)
_SPINE_MARKER_NAME_START = "_RS_MARKER_START"
_SPINE_MARKER_NAME_END   = "_RS_MARKER_END"


def _apply_spine_color(obj: bpy.types.Object) -> None:
    """Assign alternating colors per spline segment so extensions are visually distinct."""
    splines = obj.data.splines
    # Build / reuse one material per color slot
    mats = []
    for k, rgba in enumerate(_SPINE_COLORS):
        mat_name = f"_RS_SPINE_{k}"
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
        mat.diffuse_color = rgba
        mats.append(mat)

    obj.data.materials.clear()
    for m in mats:
        obj.data.materials.append(m)

    for i, spline in enumerate(splines):
        spline.material_index = i % len(_SPINE_COLORS)

    # Update endpoint markers so they stay at the correct positions
    _update_spine_markers(obj)


def _update_spine_markers(obj: bpy.types.Object) -> None:
    """Create or move colored sphere-like marker objects at each end of the spine."""
    verts = get_spine_vertices(obj)
    if len(verts) < 2:
        return

    _place_marker(obj, verts[0],  is_end=False)
    _place_marker(obj, verts[-1], is_end=True)


def _place_marker(spine_obj: bpy.types.Object, world_pos: Vector, is_end: bool) -> None:
    import bmesh as _bm

    color    = _SPINE_END_COLOR   if is_end else _SPINE_START_COLOR
    tag_key  = "_rs_marker_end"   if is_end else "_rs_marker_start"
    mat_name = _SPINE_MARKER_NAME_END if is_end else _SPINE_MARKER_NAME_START
    obj_name = ("_RSM_END_"   if is_end else "_RSM_START_") + spine_obj.name

    existing = bpy.data.objects.get(obj_name)
    if existing is None:
        # Build a tiny icosphere mesh without touching the active object
        bm = _bm.new()
        _bm.ops.create_icosphere(bm, subdivisions=1, radius=0.6)
        mesh = bpy.data.meshes.new(obj_name)
        bm.to_mesh(mesh)
        bm.free()

        existing = bpy.data.objects.new(obj_name, mesh)
        existing[tag_key] = spine_obj.name
        col = _get_or_create_collection(_RS_SPINE_COLLECTION)
        col.objects.link(existing)

    # Apply material
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.diffuse_color = color
    existing.data.materials.clear()
    existing.data.materials.append(mat)

    existing.location = world_pos


def remove_spine_markers(spine_obj: bpy.types.Object) -> None:
    for suffix in ("_RSM_START_", "_RSM_END_"):
        o = bpy.data.objects.get(suffix + spine_obj.name)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)


def _next_spine_name(scene) -> str:
    existing = {
        obj.name[len(RS_PREFIX):]
        for obj in scene.objects
        if obj.type == 'CURVE' and obj.name.startswith(RS_PREFIX)
    }
    i = 1
    while f"road_{i}" in existing:
        i += 1
    return f"road_{i}"


# ── Cross-section zones ────────────────────────────────────────────────────────

# Reference dimensions for the "Fix Tile" toggles. The tile values entered in
# the panel are the correct tiling AT these reference dimensions; auto-scaling
# multiplies by (actual_dim / REF_dim) so density stays constant as geometry
# grows.  REF_LENGTH = 10 matches the user-specified ROAD_2L defaults
# (e.g. sidewalk tile_x = 5 at seg_length = 10).
REF_WIDTH  = 8.0
REF_LENGTH = 10.0


class ZoneSpec(NamedTuple):
    left_off:     float   # lateral offset from spine centre (left = negative)
    right_off:    float
    height_left:  float   # Z added above spine at left edge
    height_right: float   # Z added above spine at right edge
    texture:      str
    material:     int
    hud_color:    str
    tile_x:       float   # used as-is at bake time (already scaled by preset apply)
    tile_y:       float
    angle_offset: float


def _resolve_road_texture(spine_obj) -> str:
    """`rs_road_texture == 'AUTO'` picks R2/R4/R6 by lane count."""
    sel = spine_obj.rs_road_texture
    if sel and sel != "AUTO":
        return sel
    return {
        1: Texture.ROAD_1_LANE,
        2: Texture.ROAD_2_LANE,
        3: Texture.ROAD_3_LANE,
    }.get(spine_obj.rs_lane_count, Texture.ROAD_2_LANE)


def _cross_section_zones(spine_obj) -> List[ZoneSpec]:
    lanes  = spine_obj.rs_lane_count
    lw     = spine_obj.rs_lane_width

    # Toggleable component flags
    road_on     = spine_obj.rs_road_enabled
    curb_on     = spine_obj.rs_curb_enabled     and spine_obj.rs_curb_width     > 0.0
    sidewalk_on = spine_obj.rs_sidewalk_enabled and spine_obj.rs_sidewalk_width > 0.0
    median_on   = spine_obj.rs_median_enabled   and spine_obj.rs_median_width   > 0.0

    cw, ch = spine_obj.rs_curb_width,     spine_obj.rs_curb_height
    sw, sh = spine_obj.rs_sidewalk_width, spine_obj.rs_sidewalk_height
    mw     = spine_obj.rs_median_width

    # Per-zone tile / angle
    r_tx, r_ty, r_ang = spine_obj.rs_road_tile_x,     spine_obj.rs_road_tile_y,     spine_obj.rs_road_angle
    c_tx, c_ty, c_ang = spine_obj.rs_curb_tile_x,     spine_obj.rs_curb_tile_y,     spine_obj.rs_curb_angle
    s_tx, s_ty, s_ang = spine_obj.rs_sidewalk_tile_x, spine_obj.rs_sidewalk_tile_y, spine_obj.rs_sidewalk_angle

    # Textures (dropdown overrides)
    road_tex     = _resolve_road_texture(spine_obj)
    curb_tex     = spine_obj.rs_curb_texture     or Texture.SIDEWALK
    sidewalk_tex = spine_obj.rs_sidewalk_texture or Texture.SIDEWALK
    median_tex   = spine_obj.rs_median_texture   or Texture.GRASS

    median_mat   = Material.GRASS if median_tex == Texture.GRASS else Material.DEFAULT
    median_color = Color.GRASS    if median_tex == Texture.GRASS else Color.ROAD

    half = lanes * lw / 2.0

    zones: List[ZoneSpec] = []

    sw_side = spine_obj.rs_sidewalk_side  # "BOTH" / "LEFT" / "RIGHT"

    # "LEFT" = positive-X side (left when facing +Y / road direction).
    # "RIGHT" = negative-X side.
    if sidewalk_on:
        if sw_side in ("BOTH", "RIGHT"):
            zones.append(ZoneSpec(
                -(half + (cw if curb_on else 0) + sw), -(half + (cw if curb_on else 0)), sh, sh,
                sidewalk_tex, Material.DEFAULT, Color.ROAD, s_tx, s_ty, s_ang,
            ))
        if sw_side in ("BOTH", "LEFT"):
            zones.append(ZoneSpec(
                half + (cw if curb_on else 0), half + (cw if curb_on else 0) + sw, sh, sh,
                sidewalk_tex, Material.DEFAULT, Color.ROAD, s_tx, s_ty, -s_ang,
            ))

    if curb_on:
        if sw_side in ("BOTH", "RIGHT"):
            zones.append(ZoneSpec(
                -(half + cw), -half, ch, 0.0,
                curb_tex, Material.DEFAULT, Color.ROAD, c_tx, c_ty, c_ang,
            ))
        if sw_side in ("BOTH", "LEFT"):
            zones.append(ZoneSpec(
                half, half + cw, 0.0, ch,
                curb_tex, Material.DEFAULT, Color.ROAD, c_tx, c_ty, -c_ang,
            ))

    if road_on:
        if median_on and mw < lanes * lw:
            mh         = mw / 2.0
            half_w     = half - mh
            split_frac = half_w / (2.0 * half)
            r_tx_half  = r_tx * split_frac
            zones.append(ZoneSpec(-half, -mh, 0.0, 0.0,
                road_tex, Material.DEFAULT, Color.ROAD, r_tx_half, r_ty, r_ang))
            zones.append(ZoneSpec(mh, half, 0.0, 0.0,
                road_tex, Material.DEFAULT, Color.ROAD, r_tx_half, r_ty, r_ang))
            zones.append(ZoneSpec(-mh, mh, 0.05, 0.05,
                median_tex, median_mat, median_color, 1.0, 2.0, 0.0))
        else:
            zones.append(ZoneSpec(
                -half, half, 0.0, 0.0,
                road_tex, Material.DEFAULT, Color.ROAD, r_tx, r_ty, r_ang,
            ))

    return zones


# ── Geometry ───────────────────────────────────────────────────────────────────

def _horiz_fwd(p0: Vector, p1: Vector) -> Vector:
    d = Vector((p1.x - p0.x, p1.y - p0.y, 0.0))
    return d.normalized() if d.length > 1e-6 else Vector((1.0, 0.0, 0.0))


def _horiz_right(fwd: Vector) -> Vector:
    return Vector((-fwd.y, fwd.x, 0.0))


def _banking_deg(fwd_prev: Vector, fwd_curr: Vector, max_deg: float) -> float:
    """Positive angle = left side banked up (curving left)."""
    cross_z = fwd_prev.x * fwd_curr.y - fwd_prev.y * fwd_curr.x
    dot     = max(-1.0, min(1.0, fwd_prev.dot(fwd_curr)))
    turn    = math.degrees(math.acos(dot))
    bank    = max_deg * min(turn / 90.0, 1.0)
    return bank * (1.0 if cross_z > 0 else -1.0)


def _apply_banking(right: Vector, fwd: Vector, deg: float) -> Vector:
    """Rotate right vector around fwd axis by deg (Rodrigues)."""
    angle = math.radians(deg)
    k = fwd.normalized()
    return (right * math.cos(angle)
            + k.cross(right) * math.sin(angle)
            + k * k.dot(right) * (1.0 - math.cos(angle)))


def _compute_rights(verts: List[Vector], spine_obj) -> List[Vector]:
    """Per-vertex right vectors, optionally banked on curves."""
    n    = len(verts)
    fwds = [_horiz_fwd(verts[i], verts[i + 1]) for i in range(n - 1)]

    # Average direction at interior vertices for smooth joins
    avg_fwds = [fwds[0]]
    for i in range(1, n - 1):
        avg = (fwds[i - 1] + fwds[i])
        avg_fwds.append(avg.normalized() if avg.length > 1e-6 else fwds[i])
    avg_fwds.append(fwds[-1])

    banking_auto = spine_obj.rs_banking_auto
    banking_max  = spine_obj.rs_banking_max_deg

    rights = []
    for i in range(n):
        fwd   = avg_fwds[i]
        right = _horiz_right(fwd)
        if banking_auto and 0 < i < n - 1:
            bank  = _banking_deg(avg_fwds[i - 1], avg_fwds[i], banking_max)
            right = _apply_banking(right, fwd, bank)
        rights.append(right)
    return rights


def _create_quad_object(name: str, quad_verts: List[Vector], uvs=None) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    _get_or_create_collection(_RS_BAKED_COLLECTION).objects.link(obj)
    mesh.from_pydata([(v.x, v.y, v.z) for v in quad_verts], [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    if uvs:
        for loop_idx, uv in zip(mesh.polygons[0].loop_indices, uvs):
            uv_layer.data[loop_idx].uv = uv
    return obj


def _clear_baked(spine_obj: bpy.types.Object) -> None:
    spine_name = spine_obj.name
    for o in [o for o in bpy.data.objects if o.get(RS_BAKED_TAG) == spine_name]:
        bpy.data.objects.remove(o, do_unlink=True)


def _bake_road(spine_obj, context) -> int:
    from src.integrations.blender.modeling import uv_mapping as _uvm
    from src.integrations.blender.operators.polygon_presets import _apply_material
    _texture_folder = _uvm._texture_folder

    verts = get_spine_vertices(spine_obj)
    if len(verts) < 2:
        return 0

    _clear_baked(spine_obj)

    zones  = _cross_section_zones(spine_obj)
    rights = _compute_rights(verts, spine_obj)
    used   = get_used_bound_numbers(context.scene)
    count  = 0

    # Cumulative arc length along the spine — used to drive curve-following
    # UVs so textures flow smoothly through bends.  These UVs are written
    # to each polygon's UV layer (for Blender preview) and ALSO exported
    # verbatim as a literal `tex_coords=[...]` list in the polygon's
    # save_mesh() call — bypassing the game's `compute_uv()` flat tiling.
    # That keeps Blender and the game perfectly in sync, even on curves.
    arc = [0.0]
    for i in range(len(verts) - 1):
        arc.append(arc[-1] + (verts[i + 1] - verts[i]).length)

    for i in range(len(verts) - 1):
        p0, p1 = verts[i], verts[i + 1]
        r0, r1 = rights[i], rights[i + 1]
        s0, s1 = arc[i], arc[i + 1]

        fwd        = _horiz_fwd(p0, p1)
        seg_angle  = math.degrees(math.atan2(fwd.x, fwd.y))
        seg_length = (p1 - p0).length

        for zone in zones:
            lo, ro = zone.left_off, zone.right_off
            hl, hr = zone.height_left, zone.height_right

            # Quad winding picked so the face normal points UP (+Z).
            # With `right` = +X for a north-bound spine and `lo` negative:
            #   v0 = bottom-left, v1 = top-left, v2 = top-right, v3 = bottom-right
            # Going v0→v1→v2→v3 is clockwise from above → normal +Z (visible
            # from above, which is how the game viewport sees ground polys).
            v0 = p0 + r0 * lo + Vector((0, 0, hl))   # bottom-left
            v1 = p1 + r1 * lo + Vector((0, 0, hl))   # top-left
            v2 = p1 + r1 * ro + Vector((0, 0, hr))   # top-right
            v3 = p0 + r0 * ro + Vector((0, 0, hr))   # bottom-right

            num = next_available_bound_number(used)
            used.add(num)

            zone_width = abs(zone.right_off - zone.left_off)
            eff_tx, eff_ty = zone.tile_x, zone.tile_y

            # UVs match new winding [BL, TL, TR, BR]:
            uvs = [(0.0, 0.0), (0.0, eff_ty), (eff_tx, eff_ty), (eff_tx, 0.0)]
            poly_obj = _create_quad_object(f"P{num}", [v0, v1, v2, v3], uvs=uvs)
            poly_obj[RS_BAKED_TAG] = spine_obj.name

            assign_map_editor_properties(poly_obj)
            poly_obj["material_index"] = str(zone.material)
            poly_obj["cell_type"]      = str(Room.DEFAULT)
            poly_obj["hud_color"]      = zone.hud_color
            poly_obj.tile_x            = eff_tx
            poly_obj.tile_y            = eff_ty
            poly_obj.angle_degrees     = seg_angle + zone.angle_offset

            if _texture_folder:
                _apply_material(poly_obj, zone.texture, _texture_folder)

            # Overwrite the flat UVs that update_uv_tiling just wrote with
            # arc-length-based UVs (curve-following). Mark the polygon as
            # carrying custom UVs so the exporter knows to emit a literal
            # tex_coords=[...] list instead of compute_uv(...).
            d_v = eff_ty / seg_length if seg_length > 1e-6 else 0.0
            d_u = eff_tx / zone_width if zone_width > 1e-6 else 0.0
            _write_curve_uvs(
                poly_obj,
                v_at_p0=s0 * d_v, v_at_p1=s1 * d_v,
                u_at_lo=0.0,       u_at_ro=zone_width * d_u,
                angle_offset=zone.angle_offset,
            )
            poly_obj["rs_custom_uvs"] = 1

            count += 1

        # ── Wall: vertical quads on the outer side, facing inward ──────────
        if spine_obj.rs_wall_enabled:
            count += _bake_wall_pair(
                spine_obj, p0, p1, r0, r1, used, _texture_folder,
                seg_angle, seg_length, s0, s1,
            )

    return count


def _write_curve_uvs(
    poly_obj, *,
    v_at_p0: float, v_at_p1: float,
    u_at_lo: float, u_at_ro: float,
    angle_offset: float,
) -> None:
    """Overwrite a road-spine quad's UV layer with arc-length-based coords.

    Quad vertex order (matches _bake_road, winding picked for +Z face normal):
      v0 = p0 + lo  (bottom-left)
      v1 = p1 + lo  (top-left)
      v2 = p1 + ro  (top-right)
      v3 = p0 + ro  (bottom-right)

      v1 ──── v2       (u_lo, v_p1)       (u_ro, v_p1)
      │       │
      │       │        spine runs p0 → p1 (V axis); cross-section runs lo → ro (U axis)
      │       │
      v0 ──── v3       (u_lo, v_p0)       (u_ro, v_p0)

    `angle_offset` rotates the UV layout around its centre so zones whose
    texture is meant to run across (e.g. sidewalks at ±90°) come out right.
    """
    base = [
        (u_at_lo, v_at_p0),  # v0
        (u_at_lo, v_at_p1),  # v1
        (u_at_ro, v_at_p1),  # v2
        (u_at_ro, v_at_p0),  # v3
    ]
    cx = (u_at_lo + u_at_ro) * 0.5
    cy = (v_at_p0 + v_at_p1) * 0.5
    rad = math.radians(angle_offset)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    final = []
    for u, v in base:
        du, dv = u - cx, v - cy
        ru = du * cos_a - dv * sin_a
        rv = du * sin_a + dv * cos_a
        final.append((cx + ru, cy + rv))

    uv_layer = poly_obj.data.uv_layers.active
    if uv_layer is None:
        return
    for loop_idx, uv in zip(poly_obj.data.polygons[0].loop_indices, final):
        uv_layer.data[loop_idx].uv = uv
    poly_obj.data.update()


def _bake_wall_pair(
    spine_obj, p0, p1, r0, r1, used, texture_folder, seg_angle, seg_length,
    arc0: float, arc1: float,
) -> int:
    """Spawn vertical wall quads (left and/or right) for one road segment.

    The wall sits at the OUTER edge of the sidewalk+curb stack and stands
    vertically with its inner face pointing toward the road centre.
    """
    from src.integrations.blender.operators.polygon_presets import _apply_material

    lanes  = spine_obj.rs_lane_count
    lw     = spine_obj.rs_lane_width
    half   = lanes * lw / 2.0
    cw     = spine_obj.rs_curb_width     if spine_obj.rs_curb_enabled     else 0.0
    sw     = spine_obj.rs_sidewalk_width if spine_obj.rs_sidewalk_enabled else 0.0
    outer  = half + cw + sw
    wh     = spine_obj.rs_wall_height
    wtex   = spine_obj.rs_wall_texture or Texture.WALL
    w_tx   = spine_obj.rs_wall_tile_x
    w_ty   = spine_obj.rs_wall_tile_y
    w_ang  = spine_obj.rs_wall_angle
    wall_side = spine_obj.rs_wall_side  # "BOTH" / "LEFT" / "RIGHT"

    sh = spine_obj.rs_sidewalk_height if spine_obj.rs_sidewalk_enabled else 0.0

    count = 0
    sides = []
    if wall_side in ("BOTH", "RIGHT"):
        sides.append(-1)
    if wall_side in ("BOTH", "LEFT"):
        sides.append(+1)

    for sign in sides:
        base0 = p0 + r0 * (sign * outer) + Vector((0, 0, sh))
        base1 = p1 + r1 * (sign * outer) + Vector((0, 0, sh))
        top0  = base0 + Vector((0, 0, wh))
        top1  = base1 + Vector((0, 0, wh))

        # Wall UV: tile_x runs along road length, tile_y runs up wall height.
        # NOTE: the polygon's UVs are rewritten at bake time by
        # `update_uv_tiling` (triggered when we set poly_obj.tile_x), which
        # always assumes quad winding order [bl, br, tr, tl] in UV-space and
        # applies (tile_x, tile_y, angle_degrees).
        # So we MUST use the same quad winding order on both walls — otherwise
        # update_uv_tiling maps the texture differently per side. We pick the
        # winding that gives U=along-road, V=up-wall, then accept that one
        # side's normal will face outward (visually invisible with no
        # backface culling).
        eff_tx = w_tx
        eff_ty = w_ty

        # Both sides: [base0, base1, top1, top0]
        # loop order base0→base1 = along road (U axis in update_uv_tiling)
        # loop order base0→top0  = up the wall (V axis)
        quad = [base0, base1, top1, top0]

        # Custom UVs — will be rewritten by update_uv_tiling when we set
        # poly_obj.tile_x below; supplied as a fallback / for any direct readers.
        uvs = [(0.0, 0.0), (eff_tx, 0.0), (eff_tx, eff_ty), (0.0, eff_ty)]

        num = next_available_bound_number(used)
        used.add(num)
        poly_obj = _create_quad_object(f"P{num}", quad, uvs=uvs)
        poly_obj[RS_BAKED_TAG] = spine_obj.name

        assign_map_editor_properties(poly_obj)
        poly_obj["material_index"] = str(Material.DEFAULT)
        poly_obj["cell_type"]      = str(Room.DEFAULT)
        poly_obj["hud_color"]      = Color.ROAD
        poly_obj.tile_x            = eff_tx
        poly_obj.tile_y            = eff_ty
        poly_obj.angle_degrees     = seg_angle + w_ang

        if texture_folder:
            _apply_material(poly_obj, wtex, texture_folder)

        # Curve-following UVs for walls. Quad winding [base0, base1, top1, top0]:
        #   v0 (base0) → (u_p0, 0)
        #   v1 (base1) → (u_p1, 0)
        #   v2 (top1)  → (u_p1, eff_ty)
        #   v3 (top0)  → (u_p0, eff_ty)
        u_density = eff_tx / seg_length if seg_length > 1e-6 else 0.0
        u_p0 = arc0 * u_density
        u_p1 = arc1 * u_density
        uv_layer = poly_obj.data.uv_layers.active
        if uv_layer is not None:
            curve_uvs = [(u_p0, 0.0), (u_p1, 0.0), (u_p1, eff_ty), (u_p0, eff_ty)]
            for loop_idx, uv in zip(poly_obj.data.polygons[0].loop_indices, curve_uvs):
                uv_layer.data[loop_idx].uv = uv
            poly_obj.data.update()
        poly_obj["rs_custom_uvs"] = 1

        count += 1
    return count


# ── Road-type quick presets ────────────────────────────────────────────────────

# Tile values in presets are calibrated at REF_LENGTH=10 (one segment of that
# length). When the user applies a preset to a spine, _scale_tiles_for_length()
# multiplies the length-axis tile values so what's shown in the panel already
# reflects the actual spine length — no hidden math at bake time.
#
# Which axis is the "length" axis depends on angle_offset:
#   Road / curb  (angle=90 → U across road, V along): V=ty is the length axis
#   Sidewalk     (angle=90 → texture rotated):         U=tx is the length axis
#   Wall         (vertical, U along road):             U=tx is the length axis

def _road_defaults(**over) -> dict:
    d = dict(
        rs_lane_count=2,          rs_lane_width=5.0,
        rs_road_enabled=True,     rs_road_texture="AUTO",
        rs_road_tile_x=1.0,       rs_road_tile_y=1.0,   rs_road_angle=90.0,
        rs_curb_enabled=True,     rs_curb_texture=Texture.SIDEWALK,
        rs_curb_width=0.01,       rs_curb_height=0.15,
        rs_curb_tile_x=1.0,       rs_curb_tile_y=5.0,   rs_curb_angle=0.0,
        rs_sidewalk_enabled=True, rs_sidewalk_texture=Texture.SIDEWALK,
        rs_sidewalk_width=2.5,    rs_sidewalk_height=0.15,
        rs_sidewalk_tile_x=1.0,   rs_sidewalk_tile_y=5.0, rs_sidewalk_angle=90.0,
        rs_sidewalk_side="BOTH",
        rs_wall_enabled=False,    rs_wall_texture=Texture.WALL,
        rs_wall_height=10.0,
        rs_wall_tile_x=1.0,       rs_wall_tile_y=2.0,   rs_wall_angle=0.0,
        rs_wall_side="BOTH",
        rs_median_enabled=False,  rs_median_texture=Texture.GRASS,
        rs_median_width=1.0,
    )
    d.update(over)
    return d


# Tile values are the "reference" at REF_LENGTH=10.
# _TILE_LENGTH_KEYS lists which props scale with spine length when Apply/Reset is used.
_TILE_LENGTH_KEYS = {
    "rs_road_tile_y",
    "rs_curb_tile_y",
    "rs_sidewalk_tile_x",
    "rs_wall_tile_x",
}


def _spine_total_length(spine_obj) -> float:
    verts = get_spine_vertices(spine_obj)
    total = 0.0
    for i in range(len(verts) - 1):
        total += (verts[i + 1] - verts[i]).length
    return total if total > 1e-6 else REF_LENGTH


def _scale_tiles_for_length(defaults: dict, spine_obj) -> dict:
    """Return a copy of defaults with length-axis tile values scaled to the
    spine's actual total length, so the panel shows honest bake-time values."""
    length = _spine_total_length(spine_obj)
    scale  = length / REF_LENGTH
    out = dict(defaults)
    for key in _TILE_LENGTH_KEYS:
        if key in out:
            out[key] = round(out[key] * scale, 4)
    return out


ROAD_TYPE_DEFAULTS = {
    "ROAD_TEST": _road_defaults(
        rs_road_texture=Texture.ROAD_3_LANE,
        rs_banking_auto=False, rs_banking_max_deg=15.0,
    ),
    "FREEWAY": _road_defaults(
        rs_lane_count=4,        rs_lane_width=5.0,
        rs_road_tile_x=1.0,     rs_road_tile_y=2.0,
        rs_curb_enabled=False,
        rs_sidewalk_width=3.0,  rs_sidewalk_height=0.0,
        rs_sidewalk_tile_x=5.0, rs_sidewalk_tile_y=1.0,
        rs_sidewalk_angle=-90.0,
        rs_wall_enabled=True,   rs_wall_height=1.5,
        rs_wall_tile_x=1.0,     rs_wall_tile_y=2.0,    rs_wall_angle=0.0,
        rs_median_enabled=True, rs_median_width=2.0,
        rs_banking_auto=False,  rs_banking_max_deg=15.0,
    ),
    "CUSTOM": {},
}

ROAD_TYPE_ITEMS = [
    ("ROAD_TEST", "Road Test", "Test road with R6 texture"),
    ("FREEWAY",   "Freeway",   "4-lane highway with shoulder + jersey wall + median"),
    ("CUSTOM",    "Custom",    "Manually configure all cross-section values"),
]


# ── Operators ──────────────────────────────────────────────────────────────────

class OBJECT_OT_CreateRoadSpine(bpy.types.Operator):
    bl_idname      = "object.create_road_spine"
    bl_label       = "New Road Spine"
    bl_description = "Create a road spine at the 3D cursor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        cursor = context.scene.cursor.location
        name   = _next_spine_name(context.scene)
        length = context.scene.rd_extend_length
        pts    = [
            Vector((cursor.x, cursor.y,          cursor.z)),
            Vector((cursor.x, cursor.y + length, cursor.z)),
        ]
        obj = _build_spine_object(f"{RS_PREFIX}{name}", pts, context)

        vals = _scale_tiles_for_length(ROAD_TYPE_DEFAULTS.get("ROAD_TEST", {}), obj)
        for prop, val in vals.items():
            setattr(obj, prop, val)

        _apply_spine_color(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        self.report({"INFO"}, f"Created {obj.name}")
        return {"FINISHED"}


class OBJECT_OT_ApplyRoadTypePreset(bpy.types.Operator):
    bl_idname      = "object.apply_road_type_preset"
    bl_label       = "Apply Type"
    bl_description = "Fill cross-section values from the selected road type"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        obj  = context.active_object
        base = ROAD_TYPE_DEFAULTS.get(context.scene.rd_road_type, {})
        vals = _scale_tiles_for_length(base, obj)
        for prop, val in vals.items():
            setattr(obj, prop, val)
        self.report({"INFO"}, f"Applied: {context.scene.rd_road_type}")
        return {"FINISHED"}


class OBJECT_OT_ResetRoadSpine(bpy.types.Operator):
    bl_idname      = "object.reset_road_spine"
    bl_label       = "Reset to Preset"
    bl_description = "Reset all cross-section values to the currently selected road type preset"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        obj  = context.active_object
        base = ROAD_TYPE_DEFAULTS.get(context.scene.rd_road_type, {})
        vals = _scale_tiles_for_length(base, obj)
        for prop, val in vals.items():
            setattr(obj, prop, val)
        self.report({"INFO"}, f"Reset to: {context.scene.rd_road_type}")
        return {"FINISHED"}


class OBJECT_OT_ExtendRoadSpine(bpy.types.Operator):
    bl_idname      = "object.extend_road_spine"
    bl_label       = "Extend Road Spine"
    bl_description = "Add vertex(es) to the road spine by length and angle"
    bl_options     = {"REGISTER", "UNDO"}

    to_end: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        from src.integrations.blender.operators.ai_streets import (
            _terrain_follow_points, _apply_terrain_snap,
        )

        obj    = context.active_object
        scene  = context.scene
        verts  = get_spine_vertices(obj)
        length = scene.rd_extend_length
        angle  = scene.rd_extend_angle
        elev   = scene.rd_extend_elevation
        snap   = scene.rd_snap_to_terrain

        if len(verts) < 2:
            return {"CANCELLED"}

        if self.to_end:
            base    = verts[-1]
            ref_fwd = (verts[-1] - verts[-2]).normalized()
        else:
            base    = verts[0]
            ref_fwd = (verts[0] - verts[1]).normalized()

        a = math.radians(angle)
        # Use only the horizontal (XY) component of the previous segment direction
        # so a steep spine doesn't collapse h_dir to zero
        hx = ref_fwd.x * math.cos(a) + ref_fwd.y * math.sin(a)
        hy = -ref_fwd.x * math.sin(a) + ref_fwd.y * math.cos(a)
        h_vec = Vector((hx, hy, 0.0))
        if h_vec.length < 1e-6:
            h_vec = Vector((0.0, 1.0, 0.0))  # fallback: north
        h_dir = h_vec.normalized()

        if snap:
            new_verts = _terrain_follow_points(base, h_dir, length, context)
        else:
            # length = horizontal distance; slope = angle from horizontal
            # new point is `length` units ahead in XY, rising by length*tan(slope)
            e = math.radians(max(-89.0, min(89.0, elev)))
            z_rise = length * math.tan(e)
            new_verts = [base + h_dir * length + Vector((0.0, 0.0, z_rise))]

        all_verts = (verts + new_verts) if self.to_end else (list(reversed(new_verts)) + verts)
        _rebuild_spine_from_verts(obj, all_verts)
        return {"FINISHED"}


class OBJECT_OT_AppendRoadSpineVertex(bpy.types.Operator):
    bl_idname      = "object.append_road_spine_vertex"
    bl_label       = "Cursor → Spine"
    bl_description = "Extend road spine toward the 3D cursor"
    bl_options     = {"REGISTER", "UNDO"}

    to_end: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        from src.integrations.blender.operators.ai_streets import _apply_terrain_snap

        obj    = context.active_object
        cursor = context.scene.cursor.location.copy()
        verts  = get_spine_vertices(obj)

        if context.scene.rd_snap_to_terrain:
            cursor = _apply_terrain_snap(cursor, context)

        all_verts = (verts + [cursor]) if self.to_end else ([cursor] + verts)
        _rebuild_spine_from_verts(obj, all_verts)
        return {"FINISHED"}


class OBJECT_OT_BakeRoadMesh(bpy.types.Operator):
    bl_idname      = "object.bake_road_mesh"
    bl_label       = "Bake Road"
    bl_description = "Generate polygon mesh objects from road spine and cross-section settings"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        count = _bake_road(context.active_object, context)
        self.report({"INFO"}, f"Baked {count} polygon(s)")
        return {"FINISHED"}


class OBJECT_OT_RebakeRoadMesh(bpy.types.Operator):
    bl_idname      = "object.rebake_road_mesh"
    bl_label       = "Re-bake"
    bl_description = "Clear previously baked polygons and regenerate from spine"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        obj   = context.active_object
        _clear_baked(obj)
        count = _bake_road(obj, context)
        self.report({"INFO"}, f"Re-baked {count} polygon(s)")
        return {"FINISHED"}


class OBJECT_OT_ClearBakedRoad(bpy.types.Operator):
    bl_idname      = "object.clear_baked_road"
    bl_label       = "Clear Baked"
    bl_description = "Delete all polygon objects baked from this spine"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        _clear_baked(context.active_object)
        self.report({"INFO"}, "Baked polygons cleared")
        return {"FINISHED"}


class OBJECT_OT_DeleteRoadSpine(bpy.types.Operator):
    bl_idname      = "object.delete_road_spine"
    bl_label       = "Delete Spine"
    bl_description = "Delete this road spine and all its baked polygons"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        obj = context.active_object
        _clear_baked(obj)
        remove_spine_markers(obj)
        bpy.data.objects.remove(obj, do_unlink=True)
        self.report({"INFO"}, "Spine and baked polygons deleted")
        return {"FINISHED"}


_RS_LIFT_KEY  = "rs_lift_z"   # custom prop storing current visual lift offset
_RS_LIFT_STEP = 2.0
_RS_LIFT_MIN  = -2.0
_RS_LIFT_MAX  =  2.0


class OBJECT_OT_LiftRoadSpine(bpy.types.Operator):
    bl_idname      = "object.lift_road_spine"
    bl_label       = "Lift Spine"
    bl_description = "Move the spine up or down for easier editing (visual only, revert with reset)"
    bl_options     = {"REGISTER", "UNDO"}

    delta: bpy.props.FloatProperty(default=_RS_LIFT_STEP)

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        obj       = context.active_object
        current   = obj.get(_RS_LIFT_KEY, 0.0)
        new_lift  = max(_RS_LIFT_MIN, min(_RS_LIFT_MAX, current + self.delta))
        actual    = new_lift - current          # how much we actually move (respects clamp)
        if abs(actual) < 1e-6:
            return {"CANCELLED"}
        verts = get_spine_vertices(obj)
        _rebuild_spine_from_verts(obj, [v + Vector((0, 0, actual)) for v in verts])
        obj[_RS_LIFT_KEY] = round(new_lift, 4)
        return {"FINISHED"}


class OBJECT_OT_RemoveRoadSpineVertex(bpy.types.Operator):
    bl_idname      = "object.remove_road_spine_vertex"
    bl_label       = "Remove Vertex"
    bl_description = "Remove the last (or first) vertex from the spine"
    bl_options     = {"REGISTER", "UNDO"}

    from_end: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_road_spine(obj) and len(get_spine_vertices(obj)) > 2

    def execute(self, context):
        obj   = context.active_object
        verts = get_spine_vertices(obj)
        new_verts = verts[:-1] if self.from_end else verts[1:]
        _rebuild_spine_from_verts(obj, new_verts)
        return {"FINISHED"}


ROAD_BUILDER_CLASSES = [
    OBJECT_OT_CreateRoadSpine,
    OBJECT_OT_ApplyRoadTypePreset,
    OBJECT_OT_ResetRoadSpine,
    OBJECT_OT_LiftRoadSpine,
    OBJECT_OT_RemoveRoadSpineVertex,
    OBJECT_OT_ExtendRoadSpine,
    OBJECT_OT_AppendRoadSpineVertex,
    OBJECT_OT_BakeRoadMesh,
    OBJECT_OT_RebakeRoadMesh,
    OBJECT_OT_ClearBakedRoad,
    OBJECT_OT_DeleteRoadSpine,
]

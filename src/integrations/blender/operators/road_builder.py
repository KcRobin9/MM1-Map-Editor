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


def _apply_spine_color(obj: bpy.types.Object) -> None:
    mat = bpy.data.materials.get("_RS_SPINE") or bpy.data.materials.new("_RS_SPINE")
    mat.diffuse_color = (1.0, 0.5, 0.0, 1.0)  # orange — distinct from green/blue AI streets
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for spline in obj.data.splines:
        spline.material_index = 0


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

class ZoneSpec(NamedTuple):
    left_off:     float   # lateral offset from spine centre (left = negative)
    right_off:    float
    height_left:  float   # Z added above spine at left edge
    height_right: float   # Z added above spine at right edge
    texture:      str
    material:     int
    hud_color:    str
    tile_x:       float
    tile_y:       float
    angle_offset: float   # added to segment direction angle for texture alignment


def _cross_section_zones(spine_obj) -> List[ZoneSpec]:
    lanes = spine_obj.rs_lane_count
    lw    = spine_obj.rs_lane_width
    cw    = spine_obj.rs_curb_width
    ch    = spine_obj.rs_curb_height
    sw    = spine_obj.rs_sidewalk_width
    sh    = spine_obj.rs_sidewalk_height
    tx    = spine_obj.rs_road_tile_x
    ty    = spine_obj.rs_road_tile_y

    half = lanes * lw / 2.0
    road_tex = {
        1: Texture.ROAD_1_LANE,
        2: Texture.ROAD_2_LANE,
        3: Texture.ROAD_3_LANE,
    }.get(lanes, Texture.ROAD_2_LANE)

    zones: List[ZoneSpec] = []

    # Left sidewalk
    if sw > 0.0:
        zones.append(ZoneSpec(
            -(half + cw + sw), -(half + cw), sh, sh,
            Texture.SIDEWALK, Material.DEFAULT, Color.ROAD, 2.0, 1.0, 0.0,
        ))
    # Left curb — sloped: outer edge at curb height, inner edge at road level
    if cw > 0.0:
        zones.append(ZoneSpec(
            -(half + cw), -half, ch, 0.0,
            Texture.SIDEWALK, Material.DEFAULT, Color.ROAD, 1.0, 1.0, 0.0,
        ))
    # Road surface (all lanes as one wide quad per segment)
    zones.append(ZoneSpec(
        -half, half, 0.0, 0.0,
        road_tex, Material.DEFAULT, Color.ROAD, tx, ty, 90.0,
    ))
    # Right curb — sloped: inner edge at road level, outer edge at curb height
    if cw > 0.0:
        zones.append(ZoneSpec(
            half, half + cw, 0.0, ch,
            Texture.SIDEWALK, Material.DEFAULT, Color.ROAD, 1.0, 1.0, 0.0,
        ))
    # Right sidewalk
    if sw > 0.0:
        zones.append(ZoneSpec(
            half + cw, half + cw + sw, sh, sh,
            Texture.SIDEWALK, Material.DEFAULT, Color.ROAD, 2.0, 1.0, 0.0,
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
    from src.integrations.blender.modeling.uv_mapping import _texture_folder
    from src.integrations.blender.operators.polygon_presets import _apply_material

    verts = get_spine_vertices(spine_obj)
    if len(verts) < 2:
        return 0

    _clear_baked(spine_obj)

    zones  = _cross_section_zones(spine_obj)
    rights = _compute_rights(verts, spine_obj)
    used   = get_used_bound_numbers(context.scene)
    count  = 0

    for i in range(len(verts) - 1):
        p0, p1 = verts[i], verts[i + 1]
        r0, r1 = rights[i], rights[i + 1]

        # Texture angle: direction of travel relative to +Y (north)
        fwd        = _horiz_fwd(p0, p1)
        seg_angle  = math.degrees(math.atan2(fwd.x, fwd.y))
        seg_length = (p1 - p0).length

        for zone in zones:
            lo, ro = zone.left_off, zone.right_off
            hl, hr = zone.height_left, zone.height_right

            v0 = p0 + r0 * lo + Vector((0, 0, hl))
            v1 = p0 + r0 * ro + Vector((0, 0, hr))
            v2 = p1 + r1 * ro + Vector((0, 0, hr))
            v3 = p1 + r1 * lo + Vector((0, 0, hl))

            num = next_available_bound_number(used)
            used.add(num)

            # UVs: road direction = V axis, cross-road = U axis
            # loop order matches quad_verts: v0=start-left, v1=start-right, v2=end-right, v3=end-left
            zone_width = zone.right_off - zone.left_off
            uvs = [
                (0.0,          0.0         ),  # v0 start-left
                (zone.tile_x,  0.0         ),  # v1 start-right
                (zone.tile_x,  zone.tile_y ),  # v2 end-right
                (0.0,          zone.tile_y ),  # v3 end-left
            ]
            poly_obj = _create_quad_object(f"P{num}", [v0, v1, v2, v3], uvs=uvs)
            poly_obj[RS_BAKED_TAG] = spine_obj.name

            assign_map_editor_properties(poly_obj)
            poly_obj["material_index"] = str(zone.material)
            poly_obj["cell_type"]      = str(Room.DEFAULT)
            poly_obj["hud_color"]      = zone.hud_color
            poly_obj.tile_x            = zone.tile_x
            poly_obj.tile_y            = zone.tile_y
            poly_obj.angle_degrees     = seg_angle + zone.angle_offset

            if _texture_folder:
                _apply_material(poly_obj, zone.texture, _texture_folder)

            count += 1

    return count


# ── Road-type quick presets ────────────────────────────────────────────────────

ROAD_TYPE_DEFAULTS = {
    # 1 lane, narrow — back-alley or service road
    "ALLEY":     dict(rs_lane_count=1, rs_lane_width=6.0,
                      rs_curb_width=0.0,  rs_curb_height=0.0,
                      rs_sidewalk_width=0.0, rs_sidewalk_height=0.0,
                      rs_road_tile_x=1.0, rs_road_tile_y=2.0),
    # 2 lanes, standard city street with curb + sidewalk
    "ROAD_2L":   dict(rs_lane_count=2, rs_lane_width=4.0,
                      rs_curb_width=0.8,  rs_curb_height=0.15,
                      rs_sidewalk_width=2.5, rs_sidewalk_height=0.15,
                      rs_road_tile_x=2.0, rs_road_tile_y=2.0),
    # 3 lanes, wide boulevard with generous sidewalks
    "BOULEVARD": dict(rs_lane_count=3, rs_lane_width=4.0,
                      rs_curb_width=1.0,  rs_curb_height=0.2,
                      rs_sidewalk_width=3.5, rs_sidewalk_height=0.2,
                      rs_road_tile_x=3.0, rs_road_tile_y=2.0),
    # 4 lanes, highway — no curb, flat paved shoulder
    "FREEWAY":   dict(rs_lane_count=4, rs_lane_width=5.0,
                      rs_curb_width=0.0,  rs_curb_height=0.0,
                      rs_sidewalk_width=3.0, rs_sidewalk_height=0.0,
                      rs_road_tile_x=4.0, rs_road_tile_y=2.0),
    "CUSTOM":    {},
}

ROAD_TYPE_ITEMS = [
    ("ALLEY",     "Alley",     "Narrow 1-lane road, no curb or sidewalk"),
    ("ROAD_2L",   "Road 2L",   "Standard 2-lane with curb + sidewalk"),
    ("BOULEVARD", "Boulevard", "Wide 3-lane with curb + sidewalk"),
    ("FREEWAY",   "Freeway",   "4-lane highway with paved shoulder"),
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
        pts    = [
            Vector((cursor.x, cursor.y,        cursor.z)),
            Vector((cursor.x, cursor.y + 20.0, cursor.z)),
        ]
        obj = _build_spine_object(f"{RS_PREFIX}{name}", pts, context)

        obj.rs_lane_count      = 2
        obj.rs_lane_width      = 4.0
        obj.rs_curb_width      = 0.8
        obj.rs_curb_height     = 0.15
        obj.rs_sidewalk_width  = 2.5
        obj.rs_sidewalk_height = 0.15
        obj.rs_banking_auto    = False
        obj.rs_banking_max_deg = 15.0
        obj.rs_road_tile_x     = 2.0
        obj.rs_road_tile_y     = 2.0

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
        vals = ROAD_TYPE_DEFAULTS.get(context.scene.rd_road_type, {})
        for prop, val in vals.items():
            setattr(obj, prop, val)
        self.report({"INFO"}, f"Applied: {context.scene.rd_road_type}")
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
        bpy.data.objects.remove(obj, do_unlink=True)
        self.report({"INFO"}, "Spine and baked polygons deleted")
        return {"FINISHED"}


ROAD_BUILDER_CLASSES = [
    OBJECT_OT_CreateRoadSpine,
    OBJECT_OT_ApplyRoadTypePreset,
    OBJECT_OT_ExtendRoadSpine,
    OBJECT_OT_AppendRoadSpineVertex,
    OBJECT_OT_BakeRoadMesh,
    OBJECT_OT_RebakeRoadMesh,
    OBJECT_OT_ClearBakedRoad,
    OBJECT_OT_DeleteRoadSpine,
]

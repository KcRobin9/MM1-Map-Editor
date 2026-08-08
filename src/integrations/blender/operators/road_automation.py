"""Road Builder automation — turn a road spine into AI traffic lanes and place
street props along its sidewalks.

Both features read the spine (a CURVE in Blender world space) and reuse existing
systems: AI streets are built with the AI-Streets curve helpers (same coordinate
space as the spine, so no conversion), and props are emitted as fixed-prop configs
fed through the Prop Editor's own placement so they inherit its full export/BNG
round-trip. This is a leaf module (nothing imports it), so imports stay at the top.
"""
import bpy
import math
from mathutils import Vector, Matrix

from src.constants.color import Color
from src.constants.folder import Folder
from src.constants.textures import Texture
from src.constants.props import Prop, BangerFlags
from src.constants.facades import Facade, FcdFlags
from src.constants.file_formats import Material, Room
from src.constants.props_orientation import PROP_ORIENTATION_OFFSET
from src.integrations.blender.operators import facades as fac
from src.integrations.blender.modeling.props import place_props_in_scene
from src.integrations.blender.operators.ai_street_presets import _lane_offsets
from src.integrations.blender.utils import (
    get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties,
)
from src.integrations.blender.operators.props import (
    get_unique_groups, _rebuild_lists, blender_to_game, BANGER_FLAG_ITEMS,
)
from src.integrations.blender.operators.road_builder import (
    RS_PREFIX, ROAD_TYPE_DEFAULTS, is_road_spine, get_spine_vertices, _compute_rights,
    _create_quad_object, _resolve_road_texture, _build_spine_object, _next_spine_name,
    _apply_spine_color, _scale_tiles_for_length,
)
from src.integrations.blender.operators.ai_streets import (
    ST_PREFIX, INTERSECTION_TYPE_ITEMS, get_street_vertices, _build_curve_object,
    _set_street_defaults, apply_street_color, _next_street_name, _get_or_create_ai_streets_collection,
)


# Re-exported for inits.py EnumProperty registration.
RD_AI_INTERSECTION_ITEMS = INTERSECTION_TYPE_ITEMS
RD_PROP_FLAG_ITEMS = [("AUTO", "Auto (lights glow, else breakable)", "Pick flags by prop type")] + BANGER_FLAG_ITEMS

# Curated building/wall fronts that read well lining a street (game id, label).
RD_FACADE_ITEMS = [
    (Facade.BUILDING_OLDTOWN_1,    "Old Town Building 1", ""),
    (Facade.BUILDING_OLDTOWN_2,    "Old Town Building 2", ""),
    (Facade.BUILDING_OLDTOWN_3,    "Old Town Building 3", ""),
    (Facade.SHOP_OLDTOWN_1,        "Old Town Shop",       ""),
    (Facade.BROWNSTONE_OLDTOWN_1,  "Old Town Brownstone", ""),
    (Facade.BUILDING_DOWNTOWN_1,   "Downtown Building",   ""),
    (Facade.BUILDING_THELOOP_1,    "The Loop Building",   ""),
    (Facade.BUILDING_HILLSIDE_1,   "Hillside Building",   ""),
    (Facade.SHOP_HILLSIDE_1,       "Hillside Shop",       ""),
    (Facade.BUILDING_RESIDENTIAL_1, "Residential Building", ""),
    (Facade.BUILDING_INDUSTRIAL_1, "Industrial Building", ""),
    (Facade.WALL_HILLSIDE_1,       "Hillside Wall",       "Plain wall"),
    (Facade.WALL_INDUSTRIAL_1,     "Industrial Wall",     "Plain wall"),
]


# Curated street-furniture for the Road Builder prop dropdown (game id, label).
RD_PROP_ITEMS = [
    (Prop.LIGHT_BLUE_SIDEWALK,  "Street Light (Blue)",  "Tall colored street light"),
    (Prop.LIGHT_GREEN_SIDEWALK, "Street Light (Green)", "Tall colored street light"),
    (Prop.LIGHT_RED_SIDEWALK,   "Street Light (Red)",   "Tall colored street light"),
    (Prop.LIGHT_SIDEWALK,       "Street Light (Short)", "Short old-style lamp"),
    (Prop.LIGHT_HIGHWAY,        "Highway Light",        "Tall highway light"),
    (Prop.TELEPHONE_POLE,       "Telephone Pole",       "Wooden utility pole"),
    (Prop.TREE_SLIM,            "Tree (Slim)",          "Billboard tree"),
    (Prop.TREE_WIDE,            "Tree (Wide)",          "Wide billboard tree"),
    (Prop.FIRE_HYDRANT,         "Fire Hydrant",         ""),
    (Prop.BENCH,                "Bench",                "Park bench"),
    (Prop.MAILBOX,              "Mailbox",              ""),
    (Prop.PARKING_METER,        "Parking Meter",        ""),
    (Prop.BIN,                  "Trash Can",            ""),
]

_LIGHT_PROPS = {
    Prop.LIGHT_BLUE_SIDEWALK, Prop.LIGHT_GREEN_SIDEWALK, Prop.LIGHT_RED_SIDEWALK,
    Prop.LIGHT_SIDEWALK, Prop.LIGHT_HIGHWAY,
}


# ── AI street generation ──────────────────────────────────────────────────────

class OBJECT_OT_GenerateAIStreet(bpy.types.Operator):
    bl_idname      = "object.generate_ai_street"
    bl_label       = "Generate AI Street"
    bl_description = ("Create AI traffic lanes that follow this road spine, so traffic "
                      "and cops can drive it. Lane count/width come from the spine")
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        scene = context.scene
        spine = context.active_object

        verts = get_spine_vertices(spine)
        if len(verts) < 2:
            self.report({"ERROR"}, "Spine needs at least 2 vertices.")
            return {"CANCELLED"}

        rights   = _compute_rights(verts, spine)
        n_lanes  = spine.rs_lane_count
        offsets  = _lane_offsets(n_lanes, spine.rs_lane_width)
        two_way  = scene.rd_ai_two_way
        divided  = "YES" if spine.rs_median_enabled else "NO"
        group    = f"rb_{spine.name}"
        ai_col   = _get_or_create_ai_streets_collection()

        start_t  = scene.rd_ai_intersection_start
        end_t    = scene.rd_ai_intersection_end

        created = 0
        for off in offsets:
            pts = [verts[k] + rights[k] * off for k in range(len(verts))]

            # Two-way: lanes left of centre run the opposite direction (reversed).
            reversed_lane = two_way and off < 0
            if reversed_lane:
                pts = list(reversed(pts))

            name = _next_street_name(scene)
            obj  = _build_curve_object(f"{ST_PREFIX}{name}", pts, context, collection=ai_col)
            _set_street_defaults(obj)
            obj.st_group_name   = group
            obj.st_road_divided = divided
            obj.st_alley        = scene.rd_ai_alley

            # Intersection types are set per SPINE end; a reversed lane swaps them
            # so its endpoints still match the physical road ends.
            obj.st_intersection_0 = end_t if reversed_lane else start_t
            obj.st_intersection_1 = start_t if reversed_lane else end_t
            obj.st_traffic_blocked_0 = obj.st_traffic_blocked_1 = scene.rd_ai_traffic_blocked
            obj.st_ped_blocked_0     = obj.st_ped_blocked_1     = scene.rd_ai_ped_blocked

            apply_street_color(obj)
            created += 1

        mode = "two-way" if two_way else "one-way"
        self.report({"INFO"}, f"Generated {created} AI lane(s) ({mode}) from {spine.name}.")
        return {"FINISHED"}


# ── Sidewalk prop placement ───────────────────────────────────────────────────

def _sidewalk_offset(spine) -> float:
    """Lateral distance from the spine centre to the sidewalk centre line."""
    half = spine.rs_lane_count * spine.rs_lane_width / 2.0
    curb = spine.rs_curb_width if spine.rs_curb_enabled else 0.0
    return half + curb + spine.rs_sidewalk_width / 2.0


def _toward_road_angle(right: Vector, sign: float, name: str) -> float:
    """User angle (deg) so the prop faces the road from its sidewalk side."""
    d = right * (-sign)   # Blender direction from sidewalk back toward the centre
    effective = math.degrees(math.atan2(-d.y, d.x))   # → game face angle
    return round(effective - PROP_ORIENTATION_OFFSET.get(name, 0), 2)


def _side_signs(side: str):
    if side == "LEFT":
        return (1.0,)
    if side == "RIGHT":
        return (-1.0,)
    return (1.0, -1.0)


class OBJECT_OT_PlaceRoadProps(bpy.types.Operator):
    bl_idname      = "object.place_road_props"
    bl_label       = "Place Street Props"
    bl_description = ("Place the chosen prop along this road's sidewalk(s) at a fixed "
                      "interval, facing the road. Adds to the Prop Editor")
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        scene = context.scene
        spine = context.active_object

        verts = get_spine_vertices(spine)
        if len(verts) < 2:
            self.report({"ERROR"}, "Spine needs at least 2 vertices.")
            return {"CANCELLED"}

        name      = scene.rd_prop_name
        interval  = max(0.5, scene.rd_prop_interval)
        base_off  = _sidewalk_offset(spine) + scene.rd_prop_offset
        height    = spine.rs_sidewalk_height + scene.rd_prop_height_offset
        angle_adj = scene.rd_prop_angle_offset

        if scene.rd_prop_flags == "AUTO":
            flags = BangerFlags.BREAKABLE_GLOW if name in _LIGHT_PROPS else BangerFlags.BREAKABLE
        else:
            flags = int(scene.rd_prop_flags)

        rights = _compute_rights(verts, spine)

        # One line-group per spine segment per side: each segment is straight, so a
        # line (offset→end + separator) follows the polyline and faces perpendicular.
        new_cfgs = []
        for sign in _side_signs(scene.rd_prop_side):
            # Stagger offsets the right side by half an interval so both rows alternate.
            start_shift = interval / 2.0 if (scene.rd_prop_stagger and sign < 0) else 0.0

            for k in range(len(verts) - 1):
                p0 = verts[k]     + rights[k]     * (sign * base_off) + Vector((0.0, 0.0, height))
                p1 = verts[k + 1] + rights[k + 1] * (sign * base_off) + Vector((0.0, 0.0, height))

                seg = p1 - p0
                if start_shift and seg.length > 1e-6:
                    p0 = p0 + seg.normalized() * start_shift
                    seg = p1 - p0
                if seg.length < interval:
                    continue

                offset_game = blender_to_game(p0.x, p0.y, p0.z)
                end_game    = blender_to_game(p1.x, p1.y, p1.z)
                angle       = round(_toward_road_angle(rights[k], sign, name) + angle_adj, 2)

                new_cfgs.append({
                    "name":      name,
                    "offset":    tuple(round(v, 2) for v in offset_game),
                    "end":       tuple(round(v, 2) for v in end_game),
                    "separator": round(interval, 2),
                    "angle":     angle,
                    "flags":     flags,
                })

        if not new_cfgs:
            self.report({"WARNING"}, "No segments long enough for the chosen interval.")
            return {"CANCELLED"}

        groups = get_unique_groups()
        prop_list_raw, random_props_raw = _rebuild_lists(groups)
        prop_list_raw.extend(new_cfgs)

        try:
            from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights
            place_props_in_scene(
                prop_list_raw, random_props_raw,
                prop_bms_folder,
                texture_folder=Folder.Resources.Editor.Textures,
                car_wheels=prop_car_wheels,
                car_lights=prop_car_lights,
            )
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Prop placement failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Placed street props along {len(new_cfgs)} sidewalk run(s).")
        return {"FINISHED"}


# ── Facade placement ──────────────────────────────────────────────────────────

def _facade_offset(spine) -> float:
    """Lateral distance from the spine centre to the OUTER sidewalk edge (where a
    building wall sits)."""
    half = spine.rs_lane_count * spine.rs_lane_width / 2.0
    curb = spine.rs_curb_width if spine.rs_curb_enabled else 0.0
    return half + curb + spine.rs_sidewalk_width


class OBJECT_OT_PlaceRoadFacades(bpy.types.Operator):
    bl_idname      = "object.place_road_facades"
    bl_label       = "Place Facades"
    bl_description = ("Line a building-facade wall along this road behind the sidewalk(s). "
                      "Adds to the Facade Editor")
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        scene = context.scene
        spine = context.active_object

        verts = get_spine_vertices(spine)
        if len(verts) < 2:
            self.report({"ERROR"}, "Spine needs at least 2 vertices.")
            return {"CANCELLED"}

        name     = scene.rd_facade_name
        panel_w  = max(1.0, scene.rd_facade_width)
        base_off = _facade_offset(spine) + scene.rd_facade_offset
        flags    = int(FcdFlags.FRONT) | (int(FcdFlags.BRIGHT) if scene.rd_facade_bright else 0)
        flip     = scene.rd_facade_flip

        rights = _compute_rights(verts, spine)

        # One SINGLE-panel facade config per sub-panel: a 1-panel config places its
        # mesh from offset→end verbatim (the axis tiler only steps multi-panel runs),
        # so this follows diagonal/curved walls correctly.
        new_cfgs = []
        for sign in _side_signs(scene.rd_facade_side):
            for k in range(len(verts) - 1):
                a = verts[k]     + rights[k]     * (sign * base_off) + Vector((0.0, 0.0, scene.rd_facade_height_offset))
                b = verts[k + 1] + rights[k + 1] * (sign * base_off) + Vector((0.0, 0.0, scene.rd_facade_height_offset))
                seg_len = (b - a).length
                if seg_len < 0.5:
                    continue

                n = max(1, round(seg_len / panel_w))
                for i in range(n):
                    w0 = a.lerp(b, i / n)
                    w1 = a.lerp(b, (i + 1) / n)
                    og = blender_to_game(w0.x, w0.y, w0.z)
                    eg = blender_to_game(w1.x, w1.y, w1.z)

                    # Facade front faces perpendicular to offset→end; reversing the
                    # endpoints flips which side faces the road.
                    if flip ^ (sign < 0):
                        og, eg = eg, og

                    cfg = {
                        "name":       name,
                        "flags":      flags,
                        "offset":     tuple(round(v, 2) for v in og),
                        "end":        tuple(round(v, 2) for v in eg),
                        "axis":       fac._detect_dominant_axis(og, eg),
                        "separator":  round((w1 - w0).length + 0.1, 2),
                        "scale_auto": True,
                    }
                    fac._ensure_gid(cfg)
                    new_cfgs.append(cfg)

        if not new_cfgs:
            self.report({"WARNING"}, "No segments long enough to place facades.")
            return {"CANCELLED"}

        try:
            existing = list(fac.get_unique_groups().values())
            fac.place_facades_in_scene(existing + new_cfgs)
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Facade placement failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Placed {len(new_cfgs)} facade panel(s) along {spine.name}.")
        return {"FINISHED"}


# ── One-click build ───────────────────────────────────────────────────────────

class OBJECT_OT_BuildRoadAll(bpy.types.Operator):
    bl_idname      = "object.build_road_all"
    bl_label       = "Build All"
    bl_description = ("Run the enabled steps for this spine in one go: bake geometry, "
                      "generate AI lanes, place street props and facades")
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        scene = context.scene
        spine = context.active_object
        done  = []

        steps = [
            (scene.rd_build_bake,    "object.bake_road_mesh",     "bake"),
            (scene.rd_build_ai,      "object.generate_ai_street", "AI"),
            (scene.rd_build_props,   "object.place_road_props",   "props"),
            (scene.rd_build_facades, "object.place_road_facades", "facades"),
        ]
        for enabled, op_id, label in steps:
            if not enabled:
                continue
            # Keep the spine active — prop/facade placement rebuilds other collections.
            context.view_layer.objects.active = spine
            op_callable = _op_from_id(op_id)
            if op_callable("EXEC_DEFAULT") == {"FINISHED"}:
                done.append(label)

        if not done:
            self.report({"WARNING"}, "No build steps enabled.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Built: {', '.join(done)}.")
        return {"FINISHED"}


def _op_from_id(op_id: str):
    """Resolve 'object.foo' → bpy.ops.object.foo."""
    module, name = op_id.split(".")
    return getattr(getattr(bpy.ops, module), name)


# ── Junctions + ground fill ───────────────────────────────────────────────────

def _bake_ground_quad(scene, name_kind: str, corners, texture: str, material: int,
                      hud_color: str, tile_x: float, tile_y: float):
    """Bake one ground polygon (junction surface / grass patch) like the road baker:
    a P-named quad in the Road Meshes collection, exportable, tagged rb_auto_kind."""
    from src.integrations.blender.operators.polygon_presets import _apply_material
    from src.integrations.blender.modeling import uv_mapping as _uvm

    used = get_used_bound_numbers(scene)
    num  = next_available_bound_number(used)
    uvs  = [(0.0, 0.0), (0.0, tile_y), (tile_x, tile_y), (tile_x, 0.0)]

    obj = _create_quad_object(f"P{num}", list(corners), uvs=uvs)
    assign_map_editor_properties(obj)
    obj["material_index"] = str(material)
    obj["cell_type"]      = str(Room.DEFAULT)
    obj["hud_color"]      = hud_color
    obj["rb_auto_kind"]   = name_kind
    obj.tile_x        = tile_x
    obj.tile_y        = tile_y
    obj.angle_degrees = 0.0

    tex_folder = getattr(_uvm, "_texture_folder", None) or Folder.Resources.Editor.Textures
    if tex_folder:
        _apply_material(obj, texture, tex_folder)
    return obj


def _wire_ai_at(center, jtype: str, reach: float) -> int:
    """Set the intersection type on any AI lane whose endpoint lands within `reach`."""
    wired = 0
    for st in bpy.data.objects:
        if st.type != "CURVE" or not st.name.startswith(ST_PREFIX):
            continue
        verts = get_street_vertices(st)
        if not verts:
            continue
        if (verts[0] - center).length <= reach:
            st.st_intersection_0 = jtype; wired += 1
        if (verts[-1] - center).length <= reach:
            st.st_intersection_1 = jtype; wired += 1
    return wired


def _place_junction_lights(center, h: float) -> None:
    name = Prop.TRAFFIC_LIGHT_SINGLE
    new_cfgs = []
    for cx, cy in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
        corner = center + Vector((cx * h * 0.9, cy * h * 0.9, 0.0))
        d = center - corner   # face the junction centre
        angle = round(math.degrees(math.atan2(-d.y, d.x)) - PROP_ORIENTATION_OFFSET.get(name, 0), 2)
        og = blender_to_game(corner.x, corner.y, corner.z)
        new_cfgs.append({
            "name": name, "offset": tuple(round(v, 2) for v in og),
            "angle": angle, "flags": BangerFlags.BREAKABLE,
        })

    groups = get_unique_groups()
    prop_list_raw, random_props_raw = _rebuild_lists(groups)
    prop_list_raw.extend(new_cfgs)
    from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights
    place_props_in_scene(
        prop_list_raw, random_props_raw, prop_bms_folder,
        texture_folder=Folder.Resources.Editor.Textures,
        car_wheels=prop_car_wheels, car_lights=prop_car_lights,
    )


def _place_crosswalks(scene, center, reach: float) -> int:
    """Lay a zebra-crossing quad across each road approaching the junction."""
    depth = 3.0   # crosswalk depth along the road
    made  = 0
    for spine in bpy.data.objects:
        if not is_road_spine(spine):
            continue
        verts = get_spine_vertices(spine)
        if len(verts) < 2:
            continue
        for end_idx, in_idx in ((0, 1), (-1, -2)):
            ep = verts[end_idx]
            if (ep - center).length > reach:
                continue
            fwd = (verts[in_idx] - ep)            # into the road, away from the junction
            fwd.z = 0.0
            if fwd.length < 1e-6:
                continue
            fwd = fwd.normalized()
            right = Vector((-fwd.y, fwd.x, 0.0))
            hw    = spine.rs_lane_count * spine.rs_lane_width / 2.0
            a     = ep + fwd * (depth * 0.25)     # start just past the junction mouth
            b     = a + fwd * depth
            hz    = Vector((0.0, 0.0, 0.02))
            corners = [a + right * (-hw) + hz, b + right * (-hw) + hz,
                       b + right * hw + hz,     a + right * hw + hz]
            _bake_ground_quad(scene, "junction", corners, Texture.ZEBRA_CROSSING,
                              Material.DEFAULT, Color.ROAD, max(2.0, round(hw)), 1.0)
            made += 1
    return made


def _make_junction(scene, center, size: float, jtype: str, lights: bool,
                   crosswalk: bool, texture: str) -> int:
    """Bake a junction patch at `center`, wire AI ends, optionally add lights/crosswalks.
    Returns the number of AI lane ends wired."""
    h = max(1.0, size) / 2.0
    corners = [
        center + Vector((-h, -h, 0.0)), center + Vector((-h, h, 0.0)),
        center + Vector(( h,  h, 0.0)), center + Vector(( h, -h, 0.0)),
    ]
    _bake_ground_quad(scene, "junction", corners, texture, Material.DEFAULT, Color.ROAD, 2.0, 2.0)
    wired = _wire_ai_at(center, jtype, h * 1.6)
    if crosswalk:
        _place_crosswalks(scene, center, h * 1.6)
    if lights:
        _place_junction_lights(center, h)
    return wired


class OBJECT_OT_CreateRoadJunction(bpy.types.Operator):
    bl_idname      = "object.create_road_junction"
    bl_label       = "Create Junction"
    bl_description = ("Bake a road-surface junction patch at the 3D cursor and set the "
                      "intersection type on any AI lanes ending there")
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene  = context.scene
        active = context.active_object
        tex    = _resolve_road_texture(active) if is_road_spine(active) else Texture.ROAD_2_LANE
        wired  = _make_junction(scene, scene.cursor.location.copy(), scene.rd_junction_size,
                                scene.rd_junction_type, scene.rd_junction_lights,
                                scene.rd_junction_crosswalk, tex)
        self.report({"INFO"}, f"Junction baked; wired {wired} AI lane end(s).")
        return {"FINISHED"}


class OBJECT_OT_AutoJunctions(bpy.types.Operator):
    bl_idname      = "object.auto_junctions"
    bl_label       = "Auto Junctions"
    bl_description = ("Find where road-spine endpoints from different roads meet and bake a "
                      "junction (patch + AI wiring + optional lights) at each")
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        thr   = scene.rd_snap_threshold

        # Gather every spine endpoint (start + end) with its owning spine.
        endpoints = []   # (spine_name, world_vert)
        for spine in bpy.data.objects:
            if not is_road_spine(spine):
                continue
            verts = get_spine_vertices(spine)
            if len(verts) >= 2:
                endpoints.append((spine.name, verts[0]))
                endpoints.append((spine.name, verts[-1]))

        used = [False] * len(endpoints)
        made = 0
        for i in range(len(endpoints)):
            if used[i]:
                continue
            group = [i]
            used[i] = True
            for j in range(i + 1, len(endpoints)):
                if not used[j] and (endpoints[j][1] - endpoints[i][1]).length <= thr:
                    group.append(j); used[j] = True

            # A junction needs ends from at least two different roads meeting.
            if len(group) < 2 or len({endpoints[g][0] for g in group}) < 2:
                continue

            centroid = sum((endpoints[g][1] for g in group), Vector((0.0, 0.0, 0.0))) / len(group)
            _make_junction(scene, centroid, scene.rd_junction_size,
                           scene.rd_junction_type, scene.rd_junction_lights,
                           scene.rd_junction_crosswalk, Texture.ROAD_2_LANE)
            made += 1

        self.report({"INFO"}, f"Created {made} auto-junction(s).")
        return {"FINISHED"}


class OBJECT_OT_FillGrassPatch(bpy.types.Operator):
    bl_idname      = "object.fill_grass_patch"
    bl_label       = "Fill Grass Patch"
    bl_description = "Bake a rectangular grass polygon at the 3D cursor (park / verge / median)"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene  = context.scene
        center = scene.cursor.location.copy()
        hw, hl = max(1.0, scene.rd_fill_width) / 2.0, max(1.0, scene.rd_fill_length) / 2.0
        rot    = Matrix.Rotation(math.radians(scene.rd_fill_rotation), 4, "Z")

        corners = [
            center + rot @ Vector((-hw, -hl, 0.0)),
            center + rot @ Vector((-hw,  hl, 0.0)),
            center + rot @ Vector(( hw,  hl, 0.0)),
            center + rot @ Vector(( hw, -hl, 0.0)),
        ]
        tile_x = max(1.0, round(scene.rd_fill_width / 10.0))
        tile_y = max(1.0, round(scene.rd_fill_length / 10.0))
        _bake_ground_quad(scene, "grass", corners, Texture.GRASS, Material.GRASS, Color.GRASS, tile_x, tile_y)

        self.report({"INFO"}, "Grass patch baked.")
        return {"FINISHED"}


_JUNCTION_PRESETS = {
    "CROSS": [0.0, 90.0, 180.0, 270.0],
    "T":     [90.0, 180.0, 270.0],
    "Y":     [0.0, 120.0, 240.0],
}
RD_JUNCTION_PRESET_ITEMS = [
    ("CROSS",  "4-Way Cross", "Four arms at 90°"),
    ("T",      "T-Junction",  "Three arms (T)"),
    ("Y",      "Y-Junction",  "Three arms at 120°"),
    ("CUSTOM", "Custom N-Way", "Evenly-spaced arms (count + rotation)"),
]


def _preset_angles(scene) -> list:
    if scene.rd_junction_preset == "CUSTOM":
        n = max(1, scene.rd_junction_arms)
        return [scene.rd_junction_rotation + i * (360.0 / n) for i in range(n)]
    return _JUNCTION_PRESETS[scene.rd_junction_preset]


class OBJECT_OT_SpawnJunctionPreset(bpy.types.Operator):
    bl_idname      = "object.spawn_junction_preset"
    bl_label       = "Spawn Junction Preset"
    bl_description = ("Spawn a set of road spines radiating from the 3D cursor plus a "
                      "junction patch — a ready-to-bake intersection skeleton")
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene   = context.scene
        center  = scene.cursor.location.copy()
        angles  = _preset_angles(scene)
        arm_len = max(2.0, scene.rd_junction_arm_length)
        gap     = max(1.0, scene.rd_junction_size) / 2.0

        last = None
        for deg in angles:
            rad = math.radians(deg)
            d   = Vector((math.sin(rad), math.cos(rad), 0.0))   # 0°=+Y(N), 90°=+X(E)
            p0  = center + d * gap
            p1  = center + d * (gap + arm_len)

            name = _next_spine_name(scene)
            obj  = _build_spine_object(f"{RS_PREFIX}{name}", [p0, p1], context)
            for prop, val in _scale_tiles_for_length(ROAD_TYPE_DEFAULTS.get("ROAD_TEST", {}), obj).items():
                setattr(obj, prop, val)
            _apply_spine_color(obj)
            last = obj

        h = gap
        corners = [
            center + Vector((-h, -h, 0.0)), center + Vector((-h, h, 0.0)),
            center + Vector(( h,  h, 0.0)), center + Vector(( h, -h, 0.0)),
        ]
        _bake_ground_quad(scene, "junction", corners, Texture.ROAD_2_LANE,
                          Material.DEFAULT, Color.ROAD, 2.0, 2.0)

        if last is not None:
            bpy.ops.object.select_all(action="DESELECT")
            last.select_set(True)
            context.view_layer.objects.active = last

        self.report({"INFO"}, f"Spawned {len(angles)}-arm junction skeleton.")
        return {"FINISHED"}


class OBJECT_OT_PlaceGrassVerge(bpy.types.Operator):
    bl_idname      = "object.place_grass_verge"
    bl_label       = "Grass Verge"
    bl_description = "Bake a grass strip alongside the road, beyond the sidewalk"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_road_spine(context.active_object)

    def execute(self, context):
        scene = context.scene
        spine = context.active_object

        verts = get_spine_vertices(spine)
        if len(verts) < 2:
            self.report({"ERROR"}, "Spine needs at least 2 vertices.")
            return {"CANCELLED"}

        rights = _compute_rights(verts, spine)
        inner  = _facade_offset(spine) + scene.rd_verge_offset
        width  = max(0.5, scene.rd_verge_width)
        hgt    = Vector((0.0, 0.0, scene.rd_verge_height))
        tile_x = max(1.0, round(width / 10.0))

        baked = 0
        for sign in _side_signs(scene.rd_verge_side):
            lo, ro = (inner, inner + width) if sign > 0 else (-(inner + width), -inner)
            for k in range(len(verts) - 1):
                r0, r1 = rights[k], rights[k + 1]
                p0, p1 = verts[k], verts[k + 1]
                seg_len = (p1 - p0).length
                if seg_len < 0.5:
                    continue
                corners = [p0 + r0 * lo + hgt, p1 + r1 * lo + hgt,
                           p1 + r1 * ro + hgt, p0 + r0 * ro + hgt]
                _bake_ground_quad(scene, "grass", corners, Texture.GRASS, Material.GRASS,
                                  Color.GRASS, tile_x, max(1.0, round(seg_len / 10.0)))
                baked += 1

        if not baked:
            self.report({"WARNING"}, "No segments long enough for a verge.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Baked {baked} grass verge quad(s).")
        return {"FINISHED"}


class OBJECT_OT_ClearRoadExtras(bpy.types.Operator):
    bl_idname      = "object.clear_road_extras"
    bl_label       = "Clear Junctions & Fills"
    bl_description = "Delete all junction patches and grass fills made by the Road Builder"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        removed = 0
        for o in [o for o in bpy.data.objects if o.get("rb_auto_kind") in ("junction", "grass")]:
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
        self.report({"INFO"}, f"Removed {removed} junction/fill polygon(s).")
        return {"FINISHED"}


class OBJECT_OT_BuildRoadNetwork(bpy.types.Operator):
    bl_idname      = "object.build_road_network"
    bl_label       = "Build Network"
    bl_description = ("Build every road spine (bake/AI/props/facades per the Build toggles), "
                      "then auto-wire junctions where roads meet. Selected spines only if any "
                      "are selected, else all")
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene  = context.scene
        spines = [o for o in context.selected_objects if is_road_spine(o)] \
                 or [o for o in bpy.data.objects if is_road_spine(o)]
        if not spines:
            self.report({"ERROR"}, "No road spines in the scene.")
            return {"CANCELLED"}

        steps = [
            (scene.rd_build_bake,    "object.bake_road_mesh"),
            (scene.rd_build_ai,      "object.generate_ai_street"),
            (scene.rd_build_props,   "object.place_road_props"),
            (scene.rd_build_facades, "object.place_road_facades"),
        ]
        for spine in spines:
            context.view_layer.objects.active = spine
            for enabled, op_id in steps:
                if enabled:
                    _op_from_id(op_id)("EXEC_DEFAULT")

        junctions = ""
        if scene.rd_build_junctions:
            bpy.ops.object.auto_junctions("EXEC_DEFAULT")
            junctions = " + junctions"

        self.report({"INFO"}, f"Built {len(spines)} spine(s){junctions}.")
        return {"FINISHED"}


ROAD_AUTOMATION_CLASSES = [
    OBJECT_OT_GenerateAIStreet,
    OBJECT_OT_PlaceRoadProps,
    OBJECT_OT_PlaceRoadFacades,
    OBJECT_OT_BuildRoadAll,
    OBJECT_OT_CreateRoadJunction,
    OBJECT_OT_AutoJunctions,
    OBJECT_OT_FillGrassPatch,
    OBJECT_OT_SpawnJunctionPreset,
    OBJECT_OT_PlaceGrassVerge,
    OBJECT_OT_BuildRoadNetwork,
    OBJECT_OT_ClearRoadExtras,
]

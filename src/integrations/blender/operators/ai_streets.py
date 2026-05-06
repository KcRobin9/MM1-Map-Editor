import bpy
import time
import pyautogui
from pathlib import Path
from typing import List
from mathutils import Vector

from src.constants.folder import Folder
from src.constants.file_formats import FileType
from src.constants.constants import CURRENT_TIME_FORMATTED, YES, NO
from src.constants.keyboard import Key
from src.constants.props import Prop
from src.game.races.constants_2 import IntersectionType
from src.core.geometry.main import transform_coordinate_system
from src.misc.main import open_with_notepad_plus


ST_PREFIX = "ST_"

INTERSECTION_TYPE_ITEMS = [
    (str(IntersectionType.CONTINUE),   "Continue",   "No stop required"),
    (str(IntersectionType.YIELD),      "Yield",      "Yield to traffic"),
    (str(IntersectionType.STOP),       "Stop",       "Full stop required"),
    (str(IntersectionType.STOP_LIGHT), "Stop Light", "Controlled by traffic light"),
]

STOP_LIGHT_NAME_ITEMS = [
    ("NONE",                    "Not set",             ""),
    (Prop.SIGN_STOP,            "Stop Sign",           ""),
    (Prop.TRAFFIC_LIGHT_SINGLE, "Stop Light (Single)", ""),
    (Prop.TRAFFIC_LIGHT_DUAL,   "Stop Light (Dual)",   ""),
]

INTERSECTION_TYPE_TO_CONST = {
    str(IntersectionType.STOP):       "IntersectionType.STOP",
    str(IntersectionType.STOP_LIGHT): "IntersectionType.STOP_LIGHT",
    str(IntersectionType.YIELD):      "IntersectionType.YIELD",
    str(IntersectionType.CONTINUE):   "IntersectionType.CONTINUE",
}

STOP_LIGHT_TO_CONST = {
    Prop.SIGN_STOP:         "Prop.SIGN_STOP",
    Prop.TRAFFIC_LIGHT_SINGLE: "Prop.TRAFFIC_LIGHT_SINGLE",
    Prop.TRAFFIC_LIGHT_DUAL:   "Prop.TRAFFIC_LIGHT_DUAL",
}

# Color per intersection type — applied to curve material
INTERSECTION_COLORS = {
    str(IntersectionType.CONTINUE):   (0.0, 0.5, 1.0, 1.0),  # Blue
    str(IntersectionType.YIELD):      (1.0, 0.5, 0.0, 1.0),  # Orange
    str(IntersectionType.STOP):       (1.0, 0.0, 0.0, 1.0),  # Red
    str(IntersectionType.STOP_LIGHT): (1.0, 1.0, 0.0, 1.0),  # Yellow
}


# When True, st_tl_update / st_intersection_update skip BMS placement.
# Set during batch load so we can rebuild all TLs once at the end instead of once per property assignment.
_tl_update_suppressed: bool = False

_AI_STREETS_COLLECTION = "AI Streets"


def _get_or_create_ai_streets_collection() -> bpy.types.Collection:
    if _AI_STREETS_COLLECTION in bpy.data.collections:
        return bpy.data.collections[_AI_STREETS_COLLECTION]
    col = bpy.data.collections.new(_AI_STREETS_COLLECTION)
    bpy.context.scene.collection.children.link(col)
    return col


def get_all_streets() -> List[bpy.types.Object]:
    return [obj for obj in bpy.data.objects
            if obj.type == 'CURVE' and obj.name.startswith(ST_PREFIX)]


def is_street(obj) -> bool:
    return obj is not None and obj.type == 'CURVE' and obj.name.startswith(ST_PREFIX)


def get_street_vertices(obj: bpy.types.Object) -> List[Vector]:
    if not obj.data.splines:
        return []
    verts = []
    for i, spline in enumerate(obj.data.splines):
        if i == 0:
            verts.append(obj.matrix_world @ Vector(spline.points[0].co[:3]))
        verts.append(obj.matrix_world @ Vector(spline.points[1].co[:3]))
    return verts



# Shared materials — created once, reused across all streets
_ST_MAT_RED   = None
_ST_MAT_GREEN = None
_ST_MAT_BLUE  = None

def _get_segment_materials():
    global _ST_MAT_RED, _ST_MAT_GREEN, _ST_MAT_BLUE

    def _mat(name, color):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.diffuse_color = color
        return m

    _ST_MAT_RED   = _mat("_ST_RED",   (1.0, 0.0, 0.0, 1.0))
    _ST_MAT_GREEN = _mat("_ST_GREEN", (0.0, 0.8, 0.2, 1.0))
    _ST_MAT_BLUE  = _mat("_ST_BLUE",  (0.0, 0.4, 1.0, 1.0))
    return _ST_MAT_RED, _ST_MAT_GREEN, _ST_MAT_BLUE


def apply_street_color(obj: bpy.types.Object) -> None:
    num_splines = len(obj.data.splines)
    if num_splines == 0:
        return

    red_mat, green_mat, blue_mat = _get_segment_materials()

    obj.data.materials.clear()
    obj.data.materials.append(red_mat)    # index 0
    obj.data.materials.append(green_mat)  # index 1
    obj.data.materials.append(blue_mat)   # index 2

    for idx, spline in enumerate(obj.data.splines):
        if idx == 0 or idx == num_splines - 1:
            spline.material_index = 0  # red — intersection endpoints
        else:
            # Alternating green/blue for interior segments
            spline.material_index = 1 if (idx - 1) % 2 == 0 else 2


def _next_street_name(scene) -> str:
    existing = {
        obj.name[len(ST_PREFIX):]
        for obj in scene.objects
        if obj.type == 'CURVE' and obj.name.startswith(ST_PREFIX)
    }
    i = 1
    while f"street_{i}" in existing:
        i += 1
    return f"street_{i}"


def _build_curve_object(name: str, points, context,
                        collection: bpy.types.Collection = None) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 1
    curve_data.bevel_depth = 0.5

    # One spline per segment — enables per-segment coloring
    for i in range(len(points) - 1):
        spline = curve_data.splines.new('POLY')
        spline.points.add(1)  # 2 points per spline
        p0, p1 = points[i], points[i + 1]
        spline.points[0].co = (p0[0], p0[1], p0[2], 1.0)
        spline.points[1].co = (p1[0], p1[1], p1[2], 1.0)

    obj = bpy.data.objects.new(name, curve_data)
    target = collection if collection is not None else _get_or_create_ai_streets_collection()
    target.objects.link(obj)
    return obj



def _set_street_defaults(obj: bpy.types.Object) -> None:
    obj.st_intersection_0    = str(IntersectionType.CONTINUE)
    obj.st_intersection_1    = str(IntersectionType.CONTINUE)
    obj.st_stop_light_name_0 = Prop.TRAFFIC_LIGHT_SINGLE
    obj.st_stop_light_name_1 = Prop.TRAFFIC_LIGHT_SINGLE
    obj.st_traffic_blocked_0 = "NO"
    obj.st_traffic_blocked_1 = "NO"
    obj.st_ped_blocked_0     = "NO"
    obj.st_ped_blocked_1     = "NO"
    obj.st_road_divided      = "NO"
    obj.st_alley             = "NO"
    obj.st_group_name        = ""


class OBJECT_OT_CreateAIStreet(bpy.types.Operator):
    bl_idname      = "object.create_ai_street"
    bl_label       = "New Street"
    bl_description = "Create a new AI street curve at the 3D cursor with two default vertices"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        cursor = context.scene.cursor.location
        name   = _next_street_name(context.scene)

        points = [
            (cursor.x, cursor.y,        cursor.z),
            (cursor.x, cursor.y + 20.0, cursor.z),
        ]
        obj = _build_curve_object(f"{ST_PREFIX}{name}", points, context)
        _set_street_defaults(obj)
        apply_street_color(obj)

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({"INFO"}, f"Created street: {name}")
        return {"FINISHED"}


class OBJECT_OT_DuplicateAIStreet(bpy.types.Operator):
    bl_idname      = "object.duplicate_ai_street"
    bl_label       = "Duplicate Street"
    bl_description = "Duplicate the selected street with a new unique name and all properties copied"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_street(context.object)

    def execute(self, context: bpy.types.Context) -> set:
        source  = context.object
        new_name = _next_street_name(context.scene)

        bpy.ops.object.duplicate(linked=False)
        new_obj = context.object
        new_obj.name = f"{ST_PREFIX}{new_name}"
        new_obj.data = new_obj.data.copy()
        new_obj.data.name = f"{ST_PREFIX}{new_name}"

        apply_street_color(new_obj)
        self.report({"INFO"}, f"Duplicated {source.name} → {new_obj.name}")
        return {"FINISHED"}


class OBJECT_OT_LoadAIStreetsFromData(bpy.types.Operator):
    bl_idname      = "object.load_ai_streets_from_data"
    bl_label       = "Load from ai_streets.py"
    bl_description = "Import street_list from ai_streets.py as editable Blender curves"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        global _tl_update_suppressed

        try:
            from src.USER.ai_streets import street_list
        except ImportError as e:
            self.report({"ERROR"}, f"Could not import street_list: {str(e)}")
            return {"CANCELLED"}

        created = 0
        traffic_lights = []  # collected across all streets for one batch placement

        _tl_update_suppressed = True
        try:
            for data in street_list:
                street_name = data.get("street_name", f"street_{created + 1}")

                if "vertices" in data:
                    lanes_dict = {"lane_1": data["vertices"]}
                elif "lanes" in data:
                    lanes_dict = data["lanes"]
                else:
                    self.report({"WARNING"}, f"Skipped '{street_name}' — no vertices or lanes found")
                    continue

                itypes    = data.get("intersection_types",  [IntersectionType.CONTINUE, IntersectionType.CONTINUE])
                sl_names  = data.get("stop_light_names",    [Prop.TRAFFIC_LIGHT_SINGLE, Prop.TRAFFIC_LIGHT_DUAL])
                t_blocked = data.get("traffic_blocked",     [NO, NO])
                p_blocked = data.get("ped_blocked",         [NO, NO])
                sl_pos    = data.get("stop_light_positions", [])

                is_grouped = len(lanes_dict) > 1
                lane_items = list(lanes_dict.items())

                for lane_idx, (lane_key, raw_verts) in enumerate(lane_items):
                    blender_verts = [
                        transform_coordinate_system(Vector(v), game_to_blender=True)
                        for v in raw_verts
                    ]

                    if is_grouped:
                        obj_name = f"{ST_PREFIX}{street_name}_{lane_key}"
                    else:
                        obj_name = f"{ST_PREFIX}{street_name}"

                    obj = _build_curve_object(obj_name, blender_verts, context)

                    # Store sl_pos on the object FIRST so update callbacks read correct values later
                    if len(sl_pos) >= 2:
                        obj.st_sl_pos_0_offset = sl_pos[0]
                        obj.st_sl_pos_0_dir    = sl_pos[1]
                    if len(sl_pos) >= 4:
                        obj.st_sl_pos_1_offset = sl_pos[2]
                        obj.st_sl_pos_1_dir    = sl_pos[3]

                    obj.st_intersection_0    = str(itypes[0])
                    obj.st_intersection_1    = str(itypes[1])
                    obj.st_stop_light_name_0 = sl_names[0]
                    obj.st_stop_light_name_1 = sl_names[1]
                    obj.st_traffic_blocked_0 = "YES" if t_blocked[0] == YES else "NO"
                    obj.st_traffic_blocked_1 = "YES" if t_blocked[1] == YES else "NO"
                    obj.st_ped_blocked_0     = "YES" if p_blocked[0] == YES else "NO"
                    obj.st_ped_blocked_1     = "YES" if p_blocked[1] == YES else "NO"
                    obj.st_road_divided      = "YES" if data.get("road_divided", NO) == YES else "NO"
                    obj.st_alley             = "YES" if data.get("alley",        NO) == YES else "NO"

                    if is_grouped:
                        obj.st_group_name = street_name

                    apply_street_color(obj)

                created += 1

                # Collect traffic light props for endpoints that have a light set
                for endpoint_idx in range(2):
                    pos_base = endpoint_idx * 2
                    if len(sl_pos) < pos_base + 2:
                        continue
                    offset = sl_pos[pos_base]
                    dir_pt = sl_pos[pos_base + 1]
                    face   = (dir_pt[0] - offset[0], dir_pt[1] - offset[1], dir_pt[2] - offset[2])
                    name   = sl_names[endpoint_idx] if endpoint_idx < len(sl_names) else Prop.TRAFFIC_LIGHT_SINGLE
                    if name == "NONE":
                        continue
                    traffic_lights.append({
                        "name":   name,
                        "offset": offset,
                        "face":   face,
                        "tl_key": f"{street_name}_{endpoint_idx}",
                    })
        finally:
            _tl_update_suppressed = False

        # Spawn all traffic light models in one pass
        tl_placed = 0
        if traffic_lights:
            try:
                from src.USER.settings.blender import prop_bms_folder
                from src.integrations.blender.modeling.props import place_traffic_lights_in_scene
                from src.constants.folder import Folder
                tl_placed = place_traffic_lights_in_scene(
                    traffic_lights,
                    Path(prop_bms_folder),
                    texture_folder=Folder.Resources.Editor.Textures,
                )
            except Exception as e:
                self.report({"WARNING"}, f"Traffic lights could not be placed: {e}")

        tl_msg = f", {tl_placed} traffic light(s)" if traffic_lights else ""
        self.report({"INFO"}, f"Loaded {created} street(s){tl_msg} from ai_streets.py")
        return {"FINISHED"}


class OBJECT_OT_LoadExternalBAI(bpy.types.Operator):
    bl_idname      = "object.load_external_bai"
    bl_label       = "Load External BAI"
    bl_description = "Load AI streets directly from a .BAI binary file and visualize them in Blender"
    bl_options     = {"REGISTER", "UNDO"}

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.BAI;*.bai", options={"HIDDEN"})

    def invoke(self, context, event):
        from src.constants.folder import Folder
        self.filepath = str(Folder.BASE) + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        from pathlib import Path
        from src.file_formats.ai.read_write import read_ai
        from src.constants.props import Prop
        from src.game.races.constants_2 import IntersectionType

        bai_path = Path(self.filepath)
        if not bai_path.exists():
            self.report({"ERROR"}, f"File not found: {bai_path}")
            return {"CANCELLED"}

        try:
            ai_map, streets = read_ai(bai_path)
        except Exception as e:
            self.report({"ERROR"}, f"Failed to parse BAI: {e}")
            return {"CANCELLED"}

        valid_sl = {Prop.SIGN_STOP, Prop.TRAFFIC_LIGHT_SINGLE, Prop.TRAFFIC_LIGHT_DUAL}

        def _sl_name(raw: str) -> str:
            name = raw.rstrip("\x00")
            return name if name in valid_sl else Prop.TRAFFIC_LIGHT_SINGLE

        def _to_blender(v):
            return transform_coordinate_system(Vector((v.x, v.y, v.z)), game_to_blender=True)

        def _extract_lanes(path):
            """Return list of lane vertex lists — only driving lanes, not sidewalks."""
            N = path.num_vertexes
            lanes = []
            for lane_idx in range(path.num_lanes):
                start = lane_idx * N
                lanes.append(path.lane_vertices[start : start + N])
            return lanes

        def _apply_props(obj, path_fwd, path_rev):
            itype_start = str(path_rev.intersection_type)
            itype_end   = str(path_fwd.intersection_type)
            obj.st_intersection_0    = itype_start
            obj.st_intersection_1    = itype_end
            obj.st_stop_light_name_0 = _sl_name(path_rev.stop_light_name)
            obj.st_stop_light_name_1 = _sl_name(path_fwd.stop_light_name)
            obj.st_traffic_blocked_0 = "YES" if path_rev.blocked else "NO"
            obj.st_traffic_blocked_1 = "YES" if path_fwd.blocked else "NO"
            obj.st_ped_blocked_0     = "YES" if path_rev.ped_blocked else "NO"
            obj.st_ped_blocked_1     = "YES" if path_fwd.ped_blocked else "NO"
            obj.st_road_divided      = "YES" if path_fwd.divided else "NO"
            obj.st_alley             = "YES" if path_fwd.alley else "NO"
            # Stop light positions (game convention: fwd=end/index-1, rev=start/index-0)
            if len(path_rev.stop_light_pos) >= 2:
                bp0 = _to_blender(path_rev.stop_light_pos[0])
                bp1 = _to_blender(path_rev.stop_light_pos[1])
                obj.st_sl_pos_0_offset = tuple(bp0)
                obj.st_sl_pos_0_dir    = tuple(bp1)
            if len(path_fwd.stop_light_pos) >= 2:
                bp0 = _to_blender(path_fwd.stop_light_pos[0])
                bp1 = _to_blender(path_fwd.stop_light_pos[1])
                obj.st_sl_pos_1_offset = tuple(bp0)
                obj.st_sl_pos_1_dir    = tuple(bp1)

        def _collect_tl(path, street_name, endpoint_idx, out_list):
            """Append a traffic-light dict if this endpoint has a non-CONTINUE intersection with a real position."""
            if path.intersection_type == IntersectionType.CONTINUE:
                return
            if len(path.stop_light_pos) < 2:
                return
            pos0 = path.stop_light_pos[0]
            pos1 = path.stop_light_pos[1]
            # Skip if position is all zeros (unset)
            if pos0.x == 0.0 and pos0.y == 0.0 and pos0.z == 0.0:
                return
            name = _sl_name(path.stop_light_name)
            face = (pos1.x - pos0.x, pos1.y - pos0.y, pos1.z - pos0.z)
            out_list.append({
                "name":   name,
                "offset": (pos0.x, pos0.y, pos0.z),
                "face":   face,
                "tl_key": f"{street_name}_{endpoint_idx}",
            })

        global _tl_update_suppressed
        _tl_update_suppressed = True
        created = 0
        traffic_lights = []

        try:
            for street_name, (path_fwd, path_rev) in streets:
                fwd_lanes = _extract_lanes(path_fwd)
                rev_lanes = _extract_lanes(path_rev)
                all_lanes = fwd_lanes + rev_lanes
                total_lanes = len(all_lanes)
                is_multi = total_lanes > 1

                for lane_idx, raw_verts in enumerate(all_lanes):
                    blender_verts = [_to_blender(v) for v in raw_verts]

                    if is_multi:
                        direction = "fwd" if lane_idx < len(fwd_lanes) else "rev"
                        local_idx = lane_idx if lane_idx < len(fwd_lanes) else lane_idx - len(fwd_lanes)
                        obj_name = f"{ST_PREFIX}{street_name}_{direction}_lane{local_idx}"
                    else:
                        obj_name = f"{ST_PREFIX}{street_name}"

                    obj = _build_curve_object(obj_name, blender_verts, context)
                    _apply_props(obj, path_fwd, path_rev)

                    if is_multi:
                        obj.st_group_name = street_name

                    apply_street_color(obj)

                # Collect traffic lights — path_rev = start (index 0), path_fwd = end (index 1)
                _collect_tl(path_rev, street_name, 0, traffic_lights)
                _collect_tl(path_fwd, street_name, 1, traffic_lights)
                created += 1
        finally:
            _tl_update_suppressed = False

        tl_placed = 0
        if traffic_lights:
            try:
                from src.USER.settings.blender import prop_bms_folder
                from src.integrations.blender.modeling.props import place_traffic_lights_in_scene
                tl_placed = place_traffic_lights_in_scene(
                    traffic_lights,
                    Path(prop_bms_folder),
                    texture_folder=Folder.Resources.Editor.Textures,
                )
            except Exception as e:
                self.report({"WARNING"}, f"Traffic lights could not be placed: {e}")

        tl_msg = f", {tl_placed} traffic light(s)" if tl_placed else ""
        self.report({"INFO"}, f"Loaded {created} street(s){tl_msg} from {bai_path.name}")
        return {"FINISHED"}


class OBJECT_OT_ExportAIStreets(bpy.types.Operator):
    bl_idname      = "object.export_ai_streets"
    bl_label       = "Export Streets"
    bl_description = "Export AI streets to a Python dict format compatible with the editor"
    bl_options     = {"REGISTER", "UNDO"}

    export_all: bpy.props.BoolProperty(default=True)

    def execute(self, context: bpy.types.Context) -> set:
        streets = get_all_streets() if self.export_all else [
            obj for obj in context.selected_objects if is_street(obj)
        ]

        if not streets:
            self.report({"WARNING"}, "No street objects found.")
            return {"CANCELLED"}

        export_file = Folder.Blender.Polygons / f"Streets_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"

        try:
            with open(export_file, "w") as f:
                f.write("from src.constants.props import Prop\n")
                f.write("from src.constants.constants import YES, NO\n")
                f.write("from src.game.races.constants_2 import IntersectionType\n\n\n")

                # Separate grouped (multi-lane) streets from solo streets
                from collections import OrderedDict
                groups: dict = OrderedDict()
                solo  : list = []
                for obj in streets:
                    gname = obj.st_group_name
                    if gname:
                        groups.setdefault(gname, []).append(obj)
                    else:
                        solo.append(obj)

                def _optional_lines(obj) -> list:
                    itype_0 = obj.st_intersection_0
                    itype_1 = obj.st_intersection_1
                    sl_0    = obj.st_stop_light_name_0
                    sl_1    = obj.st_stop_light_name_1
                    tb_0    = YES if obj.st_traffic_blocked_0 == "YES" else NO
                    tb_1    = YES if obj.st_traffic_blocked_1 == "YES" else NO
                    pb_0    = YES if obj.st_ped_blocked_0     == "YES" else NO
                    pb_1    = YES if obj.st_ped_blocked_1     == "YES" else NO
                    divided = YES if obj.st_road_divided      == "YES" else NO
                    alley   = YES if obj.st_alley             == "YES" else NO
                    i0s = INTERSECTION_TYPE_TO_CONST.get(itype_0, itype_0)
                    i1s = INTERSECTION_TYPE_TO_CONST.get(itype_1, itype_1)
                    s0s = STOP_LIGHT_TO_CONST.get(sl_0, f'"{sl_0}"')
                    s1s = STOP_LIGHT_TO_CONST.get(sl_1, f'"{sl_1}"')
                    sl_pos = [
                        tuple(obj.st_sl_pos_0_offset), tuple(obj.st_sl_pos_0_dir),
                        tuple(obj.st_sl_pos_1_offset), tuple(obj.st_sl_pos_1_dir),
                    ]
                    # Stop lights are considered "set" only when a position has a meaningful value
                    sl_active = any(
                        any(abs(c) > 0.05 for c in v) for v in sl_pos
                    )
                    lines = []
                    if itype_0 != str(IntersectionType.CONTINUE) or itype_1 != str(IntersectionType.CONTINUE):
                        lines.append(f'    "intersection_types": [{i0s}, {i1s}],')
                    if sl_active:
                        if sl_0 != Prop.TRAFFIC_LIGHT_SINGLE or sl_1 != Prop.TRAFFIC_LIGHT_SINGLE:
                            lines.append(f'    "stop_light_names": [{s0s}, {s1s}],')
                        pos_str = ",\n        ".join(f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})" for p in sl_pos)
                        lines.append(f'    "stop_light_positions": [\n        {pos_str}\n    ],')
                    if obj.st_traffic_blocked_0 == "YES" or obj.st_traffic_blocked_1 == "YES":
                        lines.append(f'    "traffic_blocked": [{tb_0}, {tb_1}],')
                    if obj.st_ped_blocked_0 == "YES" or obj.st_ped_blocked_1 == "YES":
                        lines.append(f'    "ped_blocked": [{pb_0}, {pb_1}],')
                    if obj.st_road_divided == "YES":
                        lines.append(f'    "road_divided": {divided},')
                    if obj.st_alley == "YES":
                        lines.append(f'    "alley": {alley},')
                    return lines

                def _fmt(c: float) -> str:
                    s = f"{c:.2f}"
                    return "0.00" if s == "-0.00" else s

                def _game_verts_str(obj, indent="        ") -> str:
                    verts = get_street_vertices(obj)
                    gv    = [transform_coordinate_system(v, blender_to_game=True) for v in verts]
                    return f",\n{indent}".join(
                        f"({_fmt(v[0])}, {_fmt(v[1])}, {_fmt(v[2])})" for v in gv
                    )

                street_names = []

                # ── Solo streets (single vertex list) ─────────────────────────
                for obj in solo:
                    street_name = obj.name[len(ST_PREFIX):]
                    street_names.append(street_name)
                    verts = get_street_vertices(obj)
                    if not verts:
                        continue
                    verts_str    = _game_verts_str(obj)
                    opt          = _optional_lines(obj)
                    optional_str = ("\n" + "\n".join(opt)) if opt else ""
                    f.write(f"{street_name} = {{\n")
                    f.write(f'    "street_name": "{street_name}",\n')
                    f.write(f'    "vertices": [\n        {verts_str}\n    ],{optional_str}\n}}\n\n')

                # ── Grouped streets (multi-lane format) ───────────────────────
                for gname, lane_objs in groups.items():
                    var_name = gname.replace(" ", "_").replace("-", "_")
                    street_names.append(var_name)
                    ref_obj = lane_objs[0]   # use first lane for street-level properties

                    f.write(f"{var_name} = {{\n")
                    f.write(f'    "street_name": "{var_name}",\n')
                    f.write(f'    "lanes": {{\n')
                    for i, lane_obj in enumerate(lane_objs):
                        verts_str = _game_verts_str(lane_obj, indent="            ")
                        f.write(f'        "lane_{i + 1}": [\n            {verts_str}\n        ],\n')
                    f.write(f'    }},\n')
                    opt = _optional_lines(ref_obj)
                    for line in opt:
                        f.write(f'{line}\n')
                    f.write(f'}}\n\n')

                names_str = ", ".join(street_names)
                f.write(f"\nstreet_list = [{names_str}]\n")

            open_with_notepad_plus(export_file)
            time.sleep(1.0)
            pyautogui.hotkey(Key.CTRL, Key.A)
            pyautogui.hotkey(Key.CTRL, Key.C)

            self.report({"INFO"}, f"Exported {len(streets)} street(s)")

        except Exception as e:
            self.report({"ERROR"}, f"Export failed: {str(e)}")
            return {"CANCELLED"}

        return {"FINISHED"}


def _sample_terrain_z(x: float, y: float, context) -> float | None:
    """
    Raycast straight down from (x, y, 10000) and return the Z of the first
    mesh surface hit.  ST_ curve objects are CURVE type so they are never hit.
    Returns None when nothing is below.
    """
    try:
        depsgraph = context.evaluated_depsgraph_get()
        hit, loc, _norm, _idx, _obj, _mat = context.scene.ray_cast(
            depsgraph, Vector((x, y, 10000.0)), Vector((0.0, 0.0, -1.0))
        )
        return loc.z if hit else None
    except Exception:
        return None


def _apply_terrain_snap(pt: Vector, context) -> Vector:
    """Return pt with Z replaced by terrain height if snap is enabled."""
    if not context.scene.st_snap_to_terrain:
        return pt
    z = _sample_terrain_z(pt.x, pt.y, context)
    return Vector((pt.x, pt.y, z)) if z is not None else pt


def _terrain_follow_points(base: Vector, horiz_dir: Vector, length: float,
                           context, sample_step: float = 1.0) -> List[Vector]:
    """
    Sample terrain along (base + horiz_dir * t) for t in (0, length].
    Returns a list of world-space Vectors (NOT including base).

    When terrain snap is off: single endpoint, no terrain sampling.
    When on: inserts extra vertices wherever the slope changes significantly
    so that short bumps (smaller than `length`) are captured.
    """
    if not context.scene.st_snap_to_terrain:
        return [base + horiz_dir * length]

    steps = max(2, int(length / sample_step) + 1)
    ts    = [i * length / (steps - 1) for i in range(steps)]

    # Sample terrain Z at each t; fall back to base.z if nothing hit
    pts = []
    for t in ts:
        xy = base + horiz_dir * t
        z  = _sample_terrain_z(xy.x, xy.y, context)
        pts.append(Vector((xy.x, xy.y, z if z is not None else base.z)))

    # Compute slope (dz per horizontal unit) for each interval
    slopes = []
    for i in range(len(pts) - 1):
        dh = (pts[i + 1] - pts[i])
        dh.z = 0.0
        horiz_dist = dh.length
        dz = pts[i + 1].z - pts[i].z
        slopes.append(dz / horiz_dist if horiz_dist > 1e-4 else 0.0)

    # Collect indices where the slope changes by more than ~3°
    MIN_SLOPE_DELTA = 0.05   # ≈ 3°
    result_indices  = set()
    prev_slope      = slopes[0]
    for i in range(1, len(slopes)):
        if abs(slopes[i] - prev_slope) > MIN_SLOPE_DELTA:
            result_indices.add(i)   # vertex at start of new slope segment
            prev_slope = slopes[i]
    result_indices.add(len(pts) - 1)   # always include the endpoint

    return [pts[i] for i in sorted(result_indices)]


def _terrain_follow_ts(base: Vector, horiz_dir: Vector, length: float,
                       context, sample_step: float = 1.0) -> List[float]:
    """
    Like _terrain_follow_points but returns normalised t values (0..1) instead
    of absolute Vectors.  Used by group extend so each lane can apply its own
    perpendicular offset while sharing the same inflection timing.
    Returns [1.0] when snap is off.
    """
    if not context.scene.st_snap_to_terrain:
        return [1.0]

    steps = max(2, int(length / sample_step) + 1)
    ts    = [i / (steps - 1) for i in range(steps)]   # normalised 0..1

    z_vals = []
    for t in ts:
        xy = base + horiz_dir * (t * length)
        z  = _sample_terrain_z(xy.x, xy.y, context)
        z_vals.append(z if z is not None else base.z)

    MIN_SLOPE_DELTA = 0.05
    slopes = []
    for i in range(len(ts) - 1):
        dt       = (ts[i + 1] - ts[i]) * length
        dz       = z_vals[i + 1] - z_vals[i]
        slopes.append(dz / dt if dt > 1e-4 else 0.0)

    inflection_ts = []
    prev_slope    = slopes[0]
    for i in range(1, len(slopes)):
        if abs(slopes[i] - prev_slope) > MIN_SLOPE_DELTA:
            inflection_ts.append(ts[i])
            prev_slope = slopes[i]
    inflection_ts.append(1.0)
    return inflection_ts


def _rebuild_street_from_verts(obj: bpy.types.Object, world_verts: List[Vector]) -> None:
    """Rebuild a street's curve data from a list of world-space Vector positions."""
    mat_inv = obj.matrix_world.inverted()
    curve   = obj.data
    curve.splines.clear()
    for i in range(len(world_verts) - 1):
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        p0 = mat_inv @ world_verts[i]
        p1 = mat_inv @ world_verts[i + 1]
        spline.points[0].co = (p0.x, p0.y, p0.z, 1.0)
        spline.points[1].co = (p1.x, p1.y, p1.z, 1.0)
    apply_street_color(obj)


def get_street_vertex_count(obj: bpy.types.Object) -> int:
    """Return the logical vertex count (number of splines + 1)."""
    n = len(obj.data.splines)
    return n + 1 if n > 0 else 0


class OBJECT_OT_AppendStreetVertex(bpy.types.Operator):
    bl_idname      = "object.append_street_vertex"
    bl_label       = "Append Vertex"
    bl_description = "Add a new vertex at the 3D cursor to the start or end of the street"
    bl_options     = {"REGISTER", "UNDO"}

    to_end: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return is_street(context.active_object)

    def execute(self, context):
        obj    = context.active_object
        verts  = get_street_vertices(obj)
        cursor = context.scene.cursor.location.copy()

        if self.to_end:
            verts.append(cursor)
            context.scene.st_vertex_index = len(verts) - 1
        else:
            verts.insert(0, cursor)
            context.scene.st_vertex_index = 0

        _rebuild_street_from_verts(obj, verts)
        self.report({"INFO"}, f"Vertex {'appended to end' if self.to_end else 'prepended to start'}")
        return {"FINISHED"}


class OBJECT_OT_InsertStreetVertex(bpy.types.Operator):
    bl_idname      = "object.insert_street_vertex"
    bl_label       = "Insert After Active (Cursor)"
    bl_description = "Insert a new vertex at the 3D cursor after the active vertex index"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and get_street_vertex_count(obj) >= 2

    def execute(self, context):
        obj   = context.active_object
        verts = get_street_vertices(obj)
        idx   = max(0, min(context.scene.st_vertex_index, len(verts) - 2))
        cursor = context.scene.cursor.location.copy()

        verts.insert(idx + 1, cursor)
        _rebuild_street_from_verts(obj, verts)
        context.scene.st_vertex_index = idx + 1
        self.report({"INFO"}, f"Inserted vertex after index {idx}")
        return {"FINISHED"}


class OBJECT_OT_InsertStreetVertexMidpoint(bpy.types.Operator):
    bl_idname      = "object.insert_street_vertex_midpoint"
    bl_label       = "Insert Midpoint"
    bl_description = "Insert a new vertex at the midpoint between the active vertex and the next"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and get_street_vertex_count(obj) >= 2

    def execute(self, context):
        obj   = context.active_object
        verts = get_street_vertices(obj)
        idx   = max(0, min(context.scene.st_vertex_index, len(verts) - 2))
        mid   = (verts[idx] + verts[idx + 1]) / 2.0

        verts.insert(idx + 1, mid)
        _rebuild_street_from_verts(obj, verts)
        context.scene.st_vertex_index = idx + 1
        self.report({"INFO"}, f"Inserted midpoint between {idx} and {idx + 1}")
        return {"FINISHED"}


class OBJECT_OT_DeleteStreetVertex(bpy.types.Operator):
    bl_idname      = "object.delete_street_vertex"
    bl_label       = "Delete Active Vertex"
    bl_description = "Delete the active vertex from the street (minimum 2 vertices required)"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and get_street_vertex_count(obj) > 2

    def execute(self, context):
        obj   = context.active_object
        verts = get_street_vertices(obj)
        idx   = max(0, min(context.scene.st_vertex_index, len(verts) - 1))

        verts.pop(idx)
        _rebuild_street_from_verts(obj, verts)
        context.scene.st_vertex_index = min(idx, len(verts) - 1)
        self.report({"INFO"}, f"Deleted vertex {idx}")
        return {"FINISHED"}


class OBJECT_OT_MoveStreetVertexToCursor(bpy.types.Operator):
    bl_idname      = "object.move_street_vertex_to_cursor"
    bl_label       = "Move Active to Cursor"
    bl_description = "Move the active vertex to the 3D cursor position"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_street(context.active_object)

    def execute(self, context):
        obj    = context.active_object
        verts  = get_street_vertices(obj)
        idx    = max(0, min(context.scene.st_vertex_index, len(verts) - 1))
        verts[idx] = context.scene.cursor.location.copy()

        _rebuild_street_from_verts(obj, verts)
        self.report({"INFO"}, f"Moved vertex {idx} to cursor")
        return {"FINISHED"}


class OBJECT_OT_ReverseStreetDirection(bpy.types.Operator):
    bl_idname      = "object.reverse_street_direction"
    bl_label       = "Reverse Street Direction"
    bl_description = "Reverse the vertex order so start and end are swapped"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_street(context.active_object)

    def execute(self, context):
        obj   = context.active_object
        verts = get_street_vertices(obj)
        verts.reverse()
        _rebuild_street_from_verts(obj, verts)
        self.report({"INFO"}, f"Reversed direction of {obj.name}")
        return {"FINISHED"}


class OBJECT_OT_ExtendStreetAngle(bpy.types.Operator):
    bl_idname      = "object.extend_street_angle"
    bl_label       = "Extend by Direction"
    bl_description = "Extend the street by a fixed length, optionally rotating the direction"
    bl_options     = {"REGISTER", "UNDO"}

    to_end:       bpy.props.BoolProperty(default=True)
    angle_offset: bpy.props.FloatProperty(default=0.0)   # degrees

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and get_street_vertex_count(obj) >= 2

    def execute(self, context):
        import math
        obj    = context.active_object
        verts  = get_street_vertices(obj)
        length = context.scene.st_extend_length

        if self.to_end:
            raw_dir = (verts[-1] - verts[-2]).normalized()
            base    = verts[-1]
        else:
            raw_dir = (verts[0] - verts[1]).normalized()
            base    = verts[0]

        # Horizontal direction with angle rotation
        horiz_dir = raw_dir
        if self.angle_offset != 0.0:
            a     = math.radians(self.angle_offset)
            cos_a = math.cos(a)
            sin_a = math.sin(a)
            horiz_dir = Vector((
                horiz_dir.x * cos_a - horiz_dir.y * sin_a,
                horiz_dir.x * sin_a + horiz_dir.y * cos_a,
                0.0,
            )).normalized()

        snap = context.scene.st_snap_to_terrain
        if snap:
            # Multi-vertex terrain following — elevation param ignored when snap is on
            new_verts = _terrain_follow_points(base, horiz_dir, length, context)
        else:
            # Single vertex with optional elevation tilt
            direction = horiz_dir
            elev = context.scene.st_extend_elevation
            if elev != 0.0:
                e     = math.radians(elev)
                cos_e = math.cos(e)
                sin_e = math.sin(e)
                direction = Vector((direction.x * cos_e, direction.y * cos_e, sin_e))
            new_verts = [base + direction * length]

        added = len(new_verts)
        if self.to_end:
            verts.extend(new_verts)
            context.scene.st_vertex_index = len(verts) - 1
        else:
            for nv in reversed(new_verts):
                verts.insert(0, nv)
            context.scene.st_vertex_index = 0

        _rebuild_street_from_verts(obj, verts)
        angle_label = f" ({self.angle_offset:+.0f}°)" if self.angle_offset != 0.0 else ""
        snap_label  = f" [terrain, {added}v]"         if snap                      else ""
        elev        = context.scene.st_extend_elevation
        elev_label  = f" elev {elev:+.0f}°"           if (elev != 0.0 and not snap) else ""
        self.report({"INFO"}, f"Extended {'end' if self.to_end else 'start'} by {length:.1f}{angle_label}{elev_label}{snap_label}")
        return {"FINISHED"}


class OBJECT_OT_CursorToStreetVertex(bpy.types.Operator):
    bl_idname      = "object.cursor_to_street_vertex"
    bl_label       = "Cursor to Active Vertex"
    bl_description = "Snap the 3D cursor to the active vertex position"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_street(context.active_object)

    def execute(self, context):
        obj   = context.active_object
        verts = get_street_vertices(obj)
        idx   = max(0, min(context.scene.st_vertex_index, len(verts) - 1))
        context.scene.cursor.location = verts[idx].copy()
        self.report({"INFO"}, f"Cursor → V{idx}")
        return {"FINISHED"}


class OBJECT_OT_DeleteAllStreets(bpy.types.Operator):
    bl_idname      = "object.delete_all_streets"
    bl_label       = "Delete All Streets"
    bl_description = "Delete every AI street object in the scene"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        streets = get_all_streets()
        n = len(streets)
        for obj in streets:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data.users == 0:
                bpy.data.curves.remove(data)
        self.report({"INFO"}, f"Deleted {n} street(s)")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


def _get_street_tl_lights(obj: bpy.types.Object) -> tuple:
    """Return (street_name, lights_list) from an street object's current properties."""
    street_name = obj.name[len(ST_PREFIX):]
    sl_pos = [
        tuple(obj.st_sl_pos_0_offset), tuple(obj.st_sl_pos_0_dir),
        tuple(obj.st_sl_pos_1_offset), tuple(obj.st_sl_pos_1_dir),
    ]
    lights = []
    for endpoint_idx in range(2):
        pos_base = endpoint_idx * 2
        offset   = sl_pos[pos_base]
        dir_pt   = sl_pos[pos_base + 1]
        face     = (dir_pt[0] - offset[0], dir_pt[1] - offset[1], dir_pt[2] - offset[2])
        name     = getattr(obj, f"st_stop_light_name_{endpoint_idx}", Prop.TRAFFIC_LIGHT_SINGLE)
        if name == "NONE":
            continue
        lights.append({
            "name":   name,
            "offset": offset,
            "face":   face,
            "tl_key": f"{street_name}_{endpoint_idx}",
        })
    return street_name, lights


def _rebuild_street_tl(obj: bpy.types.Object) -> None:
    """Refresh the traffic light props in the scene for one street object."""
    try:
        from src.USER.settings.blender import prop_bms_folder
        from src.integrations.blender.modeling.props import refresh_one_street_traffic_lights
        from src.constants.folder import Folder
        street_name, lights = _get_street_tl_lights(obj)
        refresh_one_street_traffic_lights(
            street_name, lights,
            Path(prop_bms_folder),
            texture_folder=Folder.Resources.Editor.Textures,
        )
    except Exception as e:
        print(f"[TL] Could not refresh traffic lights for {obj.name}: {e}")


def st_intersection_update(self, context) -> None:
    if not _tl_update_suppressed and is_street(self):
        _rebuild_street_tl(self)


def st_tl_update(self, context) -> None:
    """Update callback for stop-light name and position properties."""
    if not _tl_update_suppressed and is_street(self):
        _rebuild_street_tl(self)


# ── Group helpers ──────────────────────────────────────────────────────────────

def _get_group_streets(obj: bpy.types.Object) -> List[bpy.types.Object]:
    """Return all streets sharing obj's group name, sorted by object name."""
    gname = getattr(obj, "st_group_name", "") if obj else ""
    if not gname:
        return []
    return sorted(
        [o for o in bpy.data.objects if is_street(o) and o.st_group_name == gname],
        key=lambda o: o.name,
    )


def _rotate_z(v: Vector, deg: float) -> Vector:
    import math
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return Vector((c * v.x - s * v.y, s * v.x + c * v.y, v.z))


# ── Group operators ────────────────────────────────────────────────────────────

class OBJECT_OT_SelectStreetGroup(bpy.types.Operator):
    bl_idname      = "object.select_street_group"
    bl_label       = "Select Group"
    bl_description = "Select all streets in the same group as the active street"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and bool(getattr(obj, "st_group_name", ""))

    def execute(self, context):
        lanes = _get_group_streets(context.active_object)
        bpy.ops.object.select_all(action='DESELECT')
        for o in lanes:
            o.select_set(True)
        if lanes:
            context.view_layer.objects.active = lanes[0]
        self.report({"INFO"}, f"Selected {len(lanes)} streets in group")
        return {"FINISHED"}


class OBJECT_OT_ExtendStreetGroupAngle(bpy.types.Operator):
    """
    Extend all lanes in a group by the same direction and length.
    Direction comes from the CENTER lane's endpoint segment so every lane
    extends in parallel — the separator is preserved automatically.
    """
    bl_idname      = "object.extend_street_group_angle"
    bl_label       = "Extend Group by Direction"
    bl_description = "Extend every lane in the group by the same direction (centre lane drives the angle)"
    bl_options     = {"REGISTER", "UNDO"}

    to_end:       bpy.props.BoolProperty(default=True)
    angle_offset: bpy.props.FloatProperty(default=0.0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and bool(getattr(obj, "st_group_name", ""))

    def execute(self, context):
        import math as _math
        lanes  = _get_group_streets(context.active_object)
        length = context.scene.st_extend_length

        # Centre lane drives the shared direction
        centre  = lanes[len(lanes) // 2]
        c_verts = get_street_vertices(centre)
        if self.to_end:
            raw_dir = (c_verts[-1] - c_verts[-2]).normalized()
            c_tip   = c_verts[-1]
        else:
            raw_dir = (c_verts[0] - c_verts[1]).normalized()
            c_tip   = c_verts[0]

        # Horizontal direction after angle rotation
        horiz_dir = _rotate_z(raw_dir, self.angle_offset)

        snap = context.scene.st_snap_to_terrain
        n       = len(lanes)
        sep     = context.scene.st_preset_lane_separator
        offsets = [(-(n - 1) / 2.0 + i) * sep for i in range(n)]

        if snap:
            # Sample terrain along centre lane, collect inflection t values (0..1)
            inflection_ts = _terrain_follow_ts(c_tip, horiz_dir, length, context)
            # Perpendicular stays horizontal
            new_perp = Vector((-horiz_dir.y, horiz_dir.x, 0.0)).normalized()

            for i, street in enumerate(lanes):
                verts = get_street_vertices(street)
                lane_tip = c_tip + new_perp * offsets[i]
                new_pts = []
                for t in inflection_ts:
                    xy  = lane_tip + horiz_dir * (t * length)
                    z   = _sample_terrain_z(xy.x, xy.y, context)
                    new_pts.append(Vector((xy.x, xy.y, z if z is not None else lane_tip.z)))
                if self.to_end:
                    verts.extend(new_pts)
                    context.scene.st_vertex_index = len(verts) - 1
                else:
                    for nv in reversed(new_pts):
                        verts.insert(0, nv)
                    context.scene.st_vertex_index = 0
                _rebuild_street_from_verts(street, verts)
            added = len(inflection_ts)
        else:
            # Single vertex with optional elevation tilt
            direction = horiz_dir
            elev = context.scene.st_extend_elevation
            if elev != 0.0:
                e     = _math.radians(elev)
                cos_e = _math.cos(e)
                sin_e = _math.sin(e)
                direction = Vector((direction.x * cos_e, direction.y * cos_e, sin_e))

            new_perp  = Vector((-direction.y, direction.x, 0.0)).normalized()
            c_new_tip = c_tip + direction * length

            for i, street in enumerate(lanes):
                verts  = get_street_vertices(street)
                new_pt = c_new_tip + new_perp * offsets[i]
                if self.to_end:
                    verts.append(new_pt)
                    context.scene.st_vertex_index = len(verts) - 1
                else:
                    verts.insert(0, new_pt)
                    context.scene.st_vertex_index = 0
                _rebuild_street_from_verts(street, verts)
            added = 1

        label      = f" (+{self.angle_offset:.0f}°)" if self.angle_offset != 0.0 else ""
        snap_label = f" [terrain, {added}v]"          if snap                      else ""
        self.report({"INFO"}, f"Extended {n}-lane group {'end' if self.to_end else 'start'} by {length:.1f}{label}{snap_label}")
        return {"FINISHED"}


class OBJECT_OT_AppendStreetGroupVertex(bpy.types.Operator):
    """
    Extend all lanes in a group toward the 3D cursor while keeping each lane's
    perpendicular offset from the centre lane constant.

    The cursor defines where the CENTRE lane's new endpoint goes.
    All other lanes get new endpoints offset perpendicular to the extension
    direction by their current distance from the centre lane.
    """
    bl_idname      = "object.append_street_group_vertex"
    bl_label       = "Extend Group at Cursor"
    bl_description = "Extend every lane toward the cursor, maintaining lane separator"
    bl_options     = {"REGISTER", "UNDO"}

    to_end: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and bool(getattr(obj, "st_group_name", ""))

    def execute(self, context):
        lanes  = _get_group_streets(context.active_object)
        cursor = context.scene.cursor.location.copy()

        centre  = lanes[len(lanes) // 2]
        c_verts = get_street_vertices(centre)
        c_tip   = c_verts[-1] if self.to_end else c_verts[0]

        # Extension direction: cursor → centre tip
        ext = cursor - c_tip
        ext_len = ext.length
        if ext_len < 0.001:
            self.report({"WARNING"}, "Cursor is too close to the centre lane endpoint")
            return {"CANCELLED"}
        fwd  = ext / ext_len
        perp = Vector((-fwd.y, fwd.x, 0.0)).normalized()

        # Use configured separator so changing the value takes effect immediately
        n       = len(lanes)
        sep     = context.scene.st_preset_lane_separator
        offsets = [(-(n - 1) / 2.0 + i) * sep for i in range(n)]

        for i, street in enumerate(lanes):
            verts  = get_street_vertices(street)
            new_pt = _apply_terrain_snap(cursor + perp * offsets[i], context)

            if self.to_end:
                verts.append(new_pt)
                context.scene.st_vertex_index = len(verts) - 1
            else:
                verts.insert(0, new_pt)
                context.scene.st_vertex_index = 0
            _rebuild_street_from_verts(street, verts)

        snap_label = " [terrain]" if context.scene.st_snap_to_terrain else ""
        self.report({"INFO"}, f"Extended {len(lanes)}-lane group {'end' if self.to_end else 'start'} to cursor{snap_label}")
        return {"FINISHED"}

class OBJECT_OT_RefreshStreetColors(bpy.types.Operator):
    bl_idname      = "object.refresh_street_colors"
    bl_label       = "Refresh Colors"
    bl_description = "Reapply colors to all streets based on their intersection type"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        streets = get_all_streets()
        for obj in streets:
            apply_street_color(obj)
        self.report({"INFO"}, f"Refreshed {len(streets)} street(s)")
        return {"FINISHED"}


class OBJECT_OT_InsertStreetGroupVertex(bpy.types.Operator):
    """
    Insert a vertex into every lane of a group at the same logical position.

    at_cursor=True  — cursor defines where the CENTRE lane's new vertex goes;
                      other lanes are offset perpendicular by the configured separator.
    at_cursor=False — each lane independently takes the midpoint between its own
                      V[idx] and V[idx+1] (no cursor needed).
    """
    bl_idname      = "object.insert_street_group_vertex"
    bl_label       = "Insert Group Vertex"
    bl_description = "Insert a vertex in every lane of the group at the active vertex position"
    bl_options     = {"REGISTER", "UNDO"}

    at_cursor: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return is_street(obj) and bool(getattr(obj, "st_group_name", ""))

    def execute(self, context):
        lanes  = _get_group_streets(context.active_object)
        idx    = context.scene.st_vertex_index
        n      = len(lanes)
        sep    = context.scene.st_preset_lane_separator
        offsets = [(-(n - 1) / 2.0 + i) * sep for i in range(n)]

        if self.at_cursor:
            cursor  = context.scene.cursor.location.copy()
            # Determine perpendicular from the centre lane's segment at idx
            centre  = lanes[n // 2]
            c_verts = get_street_vertices(centre)
            c_idx   = max(0, min(idx, len(c_verts) - 2))
            seg_dir = (c_verts[c_idx + 1] - c_verts[c_idx]).normalized()
            perp    = Vector((-seg_dir.y, seg_dir.x, 0.0)).normalized()

        for i, street in enumerate(lanes):
            verts   = get_street_vertices(street)
            ins_idx = max(0, min(idx, len(verts) - 2))

            if self.at_cursor:
                new_pt = cursor + perp * offsets[i]
            else:
                new_pt = (verts[ins_idx] + verts[ins_idx + 1]) * 0.5

            verts.insert(ins_idx + 1, new_pt)
            _rebuild_street_from_verts(street, verts)

        context.scene.st_vertex_index = idx + 1
        mode = "cursor" if self.at_cursor else "midpoint"
        self.report({"INFO"}, f"Inserted {mode} vertex after V{idx} in {n} lanes")
        return {"FINISHED"}


AI_STREET_CLASSES = [
    OBJECT_OT_CreateAIStreet,
    OBJECT_OT_DuplicateAIStreet,
    OBJECT_OT_LoadAIStreetsFromData,
    OBJECT_OT_LoadExternalBAI,
    OBJECT_OT_ExportAIStreets,
    OBJECT_OT_AppendStreetVertex,
    OBJECT_OT_InsertStreetVertex,
    OBJECT_OT_InsertStreetVertexMidpoint,
    OBJECT_OT_DeleteStreetVertex,
    OBJECT_OT_MoveStreetVertexToCursor,
    OBJECT_OT_ReverseStreetDirection,
    OBJECT_OT_ExtendStreetAngle,
    OBJECT_OT_CursorToStreetVertex,
    OBJECT_OT_DeleteAllStreets,
    OBJECT_OT_SelectStreetGroup,
    OBJECT_OT_ExtendStreetGroupAngle,
    OBJECT_OT_AppendStreetGroupVertex,
    OBJECT_OT_InsertStreetGroupVertex,
]
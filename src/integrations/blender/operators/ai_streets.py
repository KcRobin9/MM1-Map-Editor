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
    (Prop.SIGN_STOP,            "Stop Sign",          ""),
    (Prop.TRAFFIC_LIGHT_SINGLE, "Stop Light (Single)", ""),
    (Prop.TRAFFIC_LIGHT_DUAL,   "Stop Light (Dual)",  ""),
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
        try:
            from src.USER.ai_streets import street_list
        except ImportError as e:
            self.report({"ERROR"}, f"Could not import street_list: {str(e)}")
            return {"CANCELLED"}

        created = 0
        for data in street_list:
            street_name = data.get("street_name", f"street_{created + 1}")

            if "vertices" in data:
                raw_verts = data["vertices"]
            elif "lanes" in data:
                raw_verts = list(data["lanes"].values())[0]
            else:
                self.report({"WARNING"}, f"Skipped '{street_name}' — no vertices or lanes found")
                continue

            blender_verts = [
                transform_coordinate_system(Vector(v), game_to_blender=True)
                for v in raw_verts
            ]

            obj = _build_curve_object(f"{ST_PREFIX}{street_name}", blender_verts, context)

            itypes    = data.get("intersection_types",  [IntersectionType.CONTINUE, IntersectionType.CONTINUE])
            sl_names  = data.get("stop_light_names",    [Prop.TRAFFIC_LIGHT_SINGLE, Prop.TRAFFIC_LIGHT_DUAL])
            t_blocked = data.get("traffic_blocked",     [NO, NO])
            p_blocked = data.get("ped_blocked",         [NO, NO])

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

            apply_street_color(obj)
            created += 1

        self.report({"INFO"}, f"Loaded {created} street(s) from ai_streets.py")
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
                    lines = []
                    if itype_0 != str(IntersectionType.CONTINUE) or itype_1 != str(IntersectionType.CONTINUE):
                        lines.append(f'    "intersection_types": [{i0s}, {i1s}],')
                    if sl_0 != Prop.TRAFFIC_LIGHT_SINGLE or sl_1 != Prop.TRAFFIC_LIGHT_SINGLE:
                        lines.append(f'    "stop_light_names": [{s0s}, {s1s}],')
                    sl_pos = [
                        tuple(obj.st_sl_pos_0_offset), tuple(obj.st_sl_pos_0_dir),
                        tuple(obj.st_sl_pos_1_offset), tuple(obj.st_sl_pos_1_dir),
                    ]
                    if any(v != (0.0, 0.0, 0.0) for v in sl_pos):
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

                def _game_verts_str(obj, indent="        ") -> str:
                    verts = get_street_vertices(obj)
                    gv    = [transform_coordinate_system(v, blender_to_game=True) for v in verts]
                    return f",\n{indent}".join(f"({v[0]:.2f}, {v[1]:.2f}, {v[2]:.2f})" for v in gv)

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
            direction = (verts[-1] - verts[-2]).normalized()
            base      = verts[-1]
        else:
            direction = (verts[0] - verts[1]).normalized()
            base      = verts[0]

        if self.angle_offset != 0.0:
            a     = math.radians(self.angle_offset)
            cos_a = math.cos(a)
            sin_a = math.sin(a)
            direction = Vector((
                direction.x * cos_a - direction.y * sin_a,
                direction.x * sin_a + direction.y * cos_a,
                direction.z,
            ))

        new_vert = base + direction * length

        if self.to_end:
            verts.append(new_vert)
            context.scene.st_vertex_index = len(verts) - 1
        else:
            verts.insert(0, new_vert)
            context.scene.st_vertex_index = 0

        _rebuild_street_from_verts(obj, verts)
        angle_label = f" (+{self.angle_offset:.0f}°)" if self.angle_offset != 0.0 else ""
        self.report({"INFO"}, f"Extended {'end' if self.to_end else 'start'} by {length:.1f}{angle_label}")
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


def st_intersection_update(self, context) -> None:
    pass  # Color is now segment-based, not intersection-type-based

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


AI_STREET_CLASSES = [
    OBJECT_OT_CreateAIStreet,
    OBJECT_OT_DuplicateAIStreet,
    OBJECT_OT_LoadAIStreetsFromData,
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
]
import bpy
from pathlib import Path

from src.constants.folder import Folder

from src.integrations.blender.waypoints.create import create_waypoint, create_gold_bar
from src.integrations.blender.waypoints.export import export_selected_waypoints
from src.integrations.blender.waypoints.helpers import get_all_waypoints, update_waypoint_colors
from src.integrations.blender.waypoints.load import (
    load_cops_and_robbers_waypoints,
    load_waypoints_from_csv,
    load_waypoints_from_race_data,
)

from src.USER.races.races import race_data


# ── Key prefix for each race type enum value ──────────────────────────────────
# CHECKPOINT races are stored under "RACE_N" keys in race_data
_RACE_TYPE_KEY = {
    "BLITZ":      "BLITZ",
    "CIRCUIT":    "CIRCUIT",
    "CHECKPOINT": "RACE",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Legacy operators (kept for keyboard-shortcut compatibility)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CREATE_SINGLE_WAYPOINT_OT_operator(bpy.types.Operator):
    bl_idname = "create.single_waypoint"
    bl_label  = "Create Single Waypoint"

    def execute(self, context):
        create_waypoint(name="WP_")
        self.report({"INFO"}, "Created Waypoint")
        return {"FINISHED"}


class EXPORT_SELECTED_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints"
    bl_label  = "Export selected Waypoints"

    def execute(self, context):
        export_selected_waypoints(export_all=False, add_brackets=False)
        self.report({"INFO"}, "Exported Selected Waypoints")
        return {"FINISHED"}


class EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints_with_brackets"
    bl_label  = "Export selected Waypoints with Brackets"

    def execute(self, context):
        export_selected_waypoints(export_all=False, add_brackets=True)
        self.report({"INFO"}, "Exported Selected Waypoints with Brackets")
        return {"FINISHED"}


class EXPORT_ALL_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints"
    bl_label  = "Export All Waypoints"

    def execute(self, context):
        export_selected_waypoints(export_all=True, add_brackets=False)
        self.report({"INFO"}, "Exported All Waypoints")
        return {"FINISHED"}


class EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints_with_brackets"
    bl_label  = "Export All Waypoints with Brackets"

    def execute(self, context):
        export_selected_waypoints(export_all=True, add_brackets=True)
        self.report({"INFO"}, "Exported All Waypoints with Brackets")
        return {"FINISHED"}


# Short labels for naming  WP_BLZ_0-1, WP_CIR_0-1, WP_CHK_0-1
_RACE_TYPE_SHORT = {
    "BLITZ":      "BLZ",
    "CIRCUIT":    "CIR",
    "CHECKPOINT": "CHK",
}


def _parse_wp_index(name: str) -> int:
    """Extract the trailing numeric index from a WP_XXX_N-INDEX name."""
    try:
        return int(name.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def _next_incomplete_set_number(role: str) -> int:
    """
    For Gold/Robber: find the lowest set that is missing this role.
    If all sets have this role (or no sets exist), return next new set number.
    """
    existing_names = [o.name for o in bpy.data.objects if o.name.startswith("CR_")]
    sets_with_role: set = set()
    all_sets: set = set()
    for name in existing_names:
        for r in ("Bank", "Gold", "Robber"):
            if r in name:
                num_str = name.replace(f"CR_{r}", "")
                try:
                    n = int(num_str)
                    all_sets.add(n)
                    if r == role:
                        sets_with_role.add(n)
                except ValueError:
                    pass
    incomplete = sorted(all_sets - sets_with_role)
    if incomplete:
        return incomplete[0]
    return (max(all_sets) + 1) if all_sets else 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Waypoint Editor panel operators
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WP_OT_LoadFromRaceData(bpy.types.Operator):
    """Load player waypoints for the selected race type and index from races.py"""
    bl_idname  = "waypoint.load_from_race_data"
    bl_label   = "Load Race Waypoints from races.py"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene      = context.scene
        race_type  = scene.wp_race_type
        key_prefix = _RACE_TYPE_KEY[race_type]
        race_index = int(scene.wp_race_index_enum)

        race_key = f"{key_prefix}_{race_index}"
        if race_key not in race_data:
            available = [k for k in race_data if k.startswith(key_prefix)]
            self.report({"ERROR"},
                f"No '{race_key}' in races.py. "
                f"Available: {', '.join(available) or 'none'}"
            )
            return {"CANCELLED"}

        load_waypoints_from_race_data(race_data, key_prefix, race_index)
        wp_count = len(race_data[race_key]["player_waypoints"])
        self.report({"INFO"}, f"Loaded {wp_count} waypoints for {race_key}")
        return {"FINISHED"}


class WP_OT_CreateObject(bpy.types.Operator):
    """Create a waypoint or CnR object at the 3D cursor or a specified position"""
    bl_idname  = "waypoint.create_object"
    bl_label   = "Create Waypoint / CnR Object"
    bl_options = {"REGISTER", "UNDO"}

    use_position: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        from src.constants.color import Color

        scene    = context.scene
        obj_type = scene.wp_create_type

        if self.use_position:
            x, y, z = scene.wp_create_x, scene.wp_create_y, scene.wp_create_z
        else:
            # Snap to road: raycast downward from 100 units above cursor
            from mathutils import Vector as _Vec
            cursor = context.scene.cursor.location.copy()
            depsgraph = context.evaluated_depsgraph_get()
            ray_origin = cursor + _Vec((0.0, 0.0, 100.0))
            hit, loc, _n, _i, hit_obj, _m = context.scene.ray_cast(
                depsgraph, ray_origin, _Vec((0.0, 0.0, -1.0))
            )
            if hit and hit_obj and not hit_obj.name.startswith(("WP_", "CR_")):
                x, y, z = loc.x, loc.y, loc.z
            else:
                x = y = z = None   # fall back to raw cursor

        if obj_type == "WAYPOINT":
            race_type  = scene.wp_race_type
            race_index = int(scene.wp_race_index_enum) if scene.wp_race_index_enum.isdigit() else 0
            short      = _RACE_TYPE_SHORT[race_type]
            prefix     = f"WP_{short}_{race_index}-"

            # Sorted existing waypoints for this race
            existing = sorted(
                [o for o in bpy.data.objects if o.name.startswith(prefix)],
                key=lambda o: _parse_wp_index(o.name),
            )

            insert_at = scene.wp_insert_index
            if insert_at < 0 or insert_at >= len(existing):
                # Append at end
                new_obj = create_waypoint(x, y, z, name=f"{prefix}{len(existing)}")
                self.report({"INFO"}, f"Created {new_obj.name}")
            else:
                # Create with a temp name, then renumber the whole set
                new_obj = create_waypoint(x, y, z, name="WP_TEMP_INSERT")
                # Build ordered list with new object inserted
                ordered = existing[:insert_at] + [new_obj] + existing[insert_at:]
                # Rename with temp prefix first to avoid collisions
                for i, obj in enumerate(ordered):
                    obj.name = f"WP_TEMP_{i}"
                for i, obj in enumerate(ordered):
                    obj.name = f"{prefix}{i}"
                self.report({"INFO"}, f"Inserted at index {insert_at}, renumbered {len(ordered)} waypoints")

        elif obj_type == "BANK":
            set_num = _next_incomplete_set_number("Bank")
            name    = f"CR_Bank{set_num}"
            create_waypoint(x, y, z, name=name, flag_color=Color.PURPLE)
            self.report({"INFO"}, f"Created {name} (set {set_num})")

        elif obj_type == "GOLD":
            set_num  = _next_incomplete_set_number("Gold")
            name     = f"CR_Gold{set_num}"
            loc      = (x, y, z) if (x is not None) else tuple(bpy.context.scene.cursor.location)
            create_gold_bar(loc, scale=3.0)
            bpy.context.object.name = name
            self.report({"INFO"}, f"Created {name} (set {set_num})")

        elif obj_type == "ROBBER":
            set_num = _next_incomplete_set_number("Robber")
            name    = f"CR_Robber{set_num}"
            create_waypoint(x, y, z, name=name, flag_color=Color.GREEN)
            self.report({"INFO"}, f"Created {name} (set {set_num})")

        return {"FINISHED"}


class WP_OT_LoadFromCSV(bpy.types.Operator):
    """Open a file browser to load waypoints from an external CSV file"""
    bl_idname   = "waypoint.load_from_csv"
    bl_label    = "Load Waypoints from File"
    bl_options  = {"REGISTER", "UNDO"}

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.csv;*.CSV", options={"HIDDEN"})

    def invoke(self, context, event):
        import os
        self.filepath = os.getcwd() + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        p = Path(self.filepath)
        if not p.exists():
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}
        try:
            load_waypoints_from_csv(p)
            self.report({"INFO"}, f"Loaded waypoints from {p.name}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to load {p.name}: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class WP_OT_LoadCnRFromData(bpy.types.Operator):
    """Load Cops & Robbers waypoints from cops_and_robbers.py"""
    bl_idname  = "waypoint.load_cnr_from_data"
    bl_label   = "Load CnR from cops_and_robbers.py"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from itertools import cycle
        from mathutils import Vector
        from src.constants.color import Color
        from src.game.races.constants_2 import CopsAndRobbers
        from src.core.geometry.main import transform_coordinate_system
        from src.USER.races.cops_and_robbers import cops_and_robbers_waypoints

        if not cops_and_robbers_waypoints:
            self.report({"WARNING"}, "cops_and_robbers_waypoints is empty in cops_and_robbers.py.")
            return {"CANCELLED"}

        waypoint_types = cycle([
            CopsAndRobbers.BANK_HIDEOUT,
            CopsAndRobbers.GOLD_POSITION,
            CopsAndRobbers.ROBBER_HIDEOUT,
        ])
        set_count = 1

        for entry in cops_and_robbers_waypoints:
            x, y, z = transform_coordinate_system(Vector(entry[:3]), game_to_blender=True)
            waypoint_type = next(waypoint_types)

            if waypoint_type == CopsAndRobbers.BANK_HIDEOUT:
                create_waypoint(x, y, z, name=f"CR_Bank{set_count}", flag_color=Color.PURPLE)
            elif waypoint_type == CopsAndRobbers.GOLD_POSITION:
                create_gold_bar((x, y, z), scale=3.0)
                bpy.context.object.name = f"CR_Gold{set_count}"
            elif waypoint_type == CopsAndRobbers.ROBBER_HIDEOUT:
                create_waypoint(x, y, z, name=f"CR_Robber{set_count}", flag_color=Color.GREEN)
                set_count += 1

        total_sets = len(cops_and_robbers_waypoints) // 3
        self.report({"INFO"}, f"Loaded {total_sets} CnR set(s) from cops_and_robbers.py")
        return {"FINISHED"}


class WP_OT_LoadCnRFromCSV(bpy.types.Operator):
    """Open a file browser to load Cops & Robbers waypoints from a CSV file"""
    bl_idname   = "waypoint.load_cnr_from_csv"
    bl_label    = "Load CnR from File"
    bl_options  = {"REGISTER", "UNDO"}

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.csv;*.CSV", options={"HIDDEN"})

    def invoke(self, context, event):
        import os
        self.filepath = os.getcwd() + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        p = Path(self.filepath)
        if not p.exists():
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}
        try:
            load_cops_and_robbers_waypoints(p)
            self.report({"INFO"}, f"Loaded CnR waypoints from {p.name}")
        except Exception as e:
            self.report({"ERROR"}, f"Failed to load {p.name}: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class WP_OT_Export(bpy.types.Operator):
    """Export waypoints to a text file (opened in Notepad++)"""
    bl_idname  = "waypoint.export"
    bl_label   = "Export Waypoints"
    bl_options = {"REGISTER"}

    export_all:   bpy.props.BoolProperty(default=True)
    add_brackets: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        # Check that there is something to export (WP_ or CR_)
        all_exportable = [
            o for o in bpy.data.objects
            if o.name.startswith("WP_") or o.name.startswith("CR_")
        ]
        if not all_exportable:
            self.report({"WARNING"}, "No waypoints or CnR objects found in scene.")
            return {"CANCELLED"}

        if not self.export_all:
            selected = [o for o in all_exportable if o.select_get()]
            if not selected:
                self.report({"WARNING"}, "No waypoints or CnR objects selected.")
                return {"CANCELLED"}

        export_selected_waypoints(export_all=self.export_all, add_brackets=self.add_brackets)
        label = "all" if self.export_all else "selected"
        self.report({"INFO"}, f"Exported {label} waypoints")
        return {"FINISHED"}


class WP_OT_ClearWaypoints(bpy.types.Operator):
    """Delete all WP_ race waypoint objects from the scene"""
    bl_idname  = "waypoint.clear_waypoints"
    bl_label   = "Clear Race Waypoints"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        wps = get_all_waypoints()
        count = len(wps)
        for obj in wps:
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        _remove_wp_collection_if_empty()
        self.report({"INFO"}, f"Removed {count} waypoint(s)")
        return {"FINISHED"}


class WP_OT_ClearCnR(bpy.types.Operator):
    """Delete all CR_ Cops & Robbers objects from the scene"""
    bl_idname  = "waypoint.clear_cnr"
    bl_label   = "Clear CnR Objects"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        cnr_objs = [o for o in bpy.data.objects if o.name.startswith("CR_")]
        count = len(cnr_objs)
        for obj in cnr_objs:
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        _remove_wp_collection_if_empty()
        self.report({"INFO"}, f"Removed {count} CnR object(s)")
        return {"FINISHED"}


def _remove_wp_collection_if_empty() -> None:
    col = bpy.data.collections.get("Waypoints")
    if col is not None and len(col.objects) == 0:
        bpy.data.collections.remove(col)


# ── All classes exported ──────────────────────────────────────────────────────

WAYPOINT_CLASSES = [
    # Legacy (keyboard shortcuts still work)
    CREATE_SINGLE_WAYPOINT_OT_operator,
    EXPORT_SELECTED_WAYPOINTS_OT_operator,
    EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator,
    EXPORT_ALL_WAYPOINTS_OT_operator,
    EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator,
    # Panel operators
    WP_OT_LoadFromRaceData,
    WP_OT_LoadFromCSV,
    WP_OT_LoadCnRFromData,
    WP_OT_LoadCnRFromCSV,
    WP_OT_CreateObject,
    WP_OT_Export,
    WP_OT_ClearWaypoints,
    WP_OT_ClearCnR,
]

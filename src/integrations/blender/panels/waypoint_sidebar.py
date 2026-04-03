import math
import bpy

from src.integrations.blender.waypoints.helpers import get_all_waypoints
from src.USER.races.races import race_data

WP_PREFIX = "WP_"
CR_PREFIX = "CR_"

_RACE_TYPE_KEY = {
    "BLITZ":      "BLITZ",
    "CIRCUIT":    "CIRCUIT",
    "CHECKPOINT": "RACE",
}

# Short labels used in waypoint names  WP_BLZ_0-1 / WP_CIR_0-1 / WP_CHK_0-1
_RACE_TYPE_SHORT = {
    "BLITZ":      "BLZ",
    "CIRCUIT":    "CIR",
    "CHECKPOINT": "CHK",
}


def _is_waypoint(obj) -> bool:
    return obj is not None and obj.name.startswith(WP_PREFIX)


def _is_cnr(obj) -> bool:
    return obj is not None and obj.name.startswith(CR_PREFIX)


def _get_cnr_objects():
    return [o for o in bpy.data.objects if o.name.startswith(CR_PREFIX)]


def _waypoint_index(obj) -> int:
    all_wps = get_all_waypoints()
    try:
        return all_wps.index(obj)
    except ValueError:
        return -1


def _available_race_items(race_type: str):
    """Return sorted list of (index_str, label, "") for races defined in race_data."""
    prefix = _RACE_TYPE_KEY.get(race_type, race_type)
    indices = sorted(
        int(k.split("_")[1])
        for k in race_data
        if k.startswith(prefix + "_") and k.split("_")[1].isdigit()
    )
    if not indices:
        return [("0", "No races defined", "")]
    return [(str(i), f"{prefix}_{i}", "") for i in indices]


def _get_available_race_items(self, context):
    return _available_race_items(context.scene.wp_race_type)


# ── CnR grouping helpers ──────────────────────────────────────────────────────

def _cnr_groups():
    """
    Return a list of dicts, one per set:
      {"set": int, "bank": obj|None, "gold": obj|None, "robber": obj|None}
    Sets are determined by the highest set number seen across all CR_ objects.
    """
    all_cr = _get_cnr_objects()
    groups: dict = {}
    for obj in all_cr:
        # Names: CR_Bank1, CR_Gold2, CR_Robber3 — number is the set index
        for role in ("Bank", "Gold", "Robber"):
            if role in obj.name:
                num_str = obj.name.replace(f"CR_{role}", "")
                try:
                    num = int(num_str)
                except ValueError:
                    continue
                if num not in groups:
                    groups[num] = {"set": num, "Bank": None, "Gold": None, "Robber": None}
                groups[num][role] = obj
    return [groups[k] for k in sorted(groups)]


class VIEW3D_PT_WaypointEditorPanel(bpy.types.Panel):
    bl_label       = "Waypoint"
    bl_idname      = "VIEW3D_PT_waypoint_editor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Waypoint Editor"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        all_wps = get_all_waypoints()
        groups  = _cnr_groups()

        # ── Visualization toggle ──────────────────────────────────────────────
        if hasattr(context.scene, "wp_show_paths"):
            row  = layout.row(align=True)
            icon = 'HIDE_OFF' if context.scene.wp_show_paths else 'HIDE_ON'
            row.prop(context.scene, "wp_show_paths", text="Show Path Lines", icon=icon, toggle=True)
            layout.separator()

        # ── Scene status ──────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        wp_icon = 'SEQUENCE_COLOR_04' if all_wps else 'SEQUENCE_COLOR_01'
        col.label(text=f"Race waypoints: {len(all_wps)}", icon=wp_icon)
        if groups:
            complete   = sum(1 for g in groups if g["Bank"] and g["Gold"] and g["Robber"])
            incomplete = len(groups) - complete
            cnr_icon   = 'SEQUENCE_COLOR_04' if not incomplete else 'ERROR'
            col.label(
                text=f"CnR sets: {complete} complete"
                     + (f", {incomplete} incomplete" if incomplete else ""),
                icon=cnr_icon,
            )
            # Show which sets are incomplete
            for g in groups:
                missing = [r for r in ("Bank", "Gold", "Robber") if not g[r]]
                if missing:
                    row = col.row()
                    row.alert = True
                    row.label(text=f"  Set {g['set']}: missing {', '.join(missing)}", icon='ERROR')

        layout.separator()

        if not _is_waypoint(obj) and not _is_cnr(obj):
            layout.label(text="Select a waypoint to inspect", icon='INFO')
            return

        # ── Active race waypoint ──────────────────────────────────────────────
        if _is_waypoint(obj):
            wp_idx   = _waypoint_index(obj)
            wp_count = len(all_wps)

            if wp_count == 1:
                role, role_icon = "Only waypoint", 'SEQUENCE_COLOR_05'
            elif wp_idx == 0:
                role, role_icon = "Start", 'SEQUENCE_COLOR_08'
            elif wp_idx == wp_count - 1:
                role, role_icon = "End", 'SEQUENCE_COLOR_04'
            else:
                role, role_icon = f"#{wp_idx + 1} of {wp_count}", 'SEQUENCE_COLOR_05'

            layout.label(text=obj.name, icon='ARROW_LEFTRIGHT')
            layout.label(text=role, icon=role_icon)

            layout.separator()
            col = layout.column(align=True)
            col.label(text="Position:")
            # Display X/Y/Z remapped so Y=height (Blender Z) and Z=horizontal (Blender Y)
            row = col.row(align=True)
            row.label(text="X")
            row.prop(obj, "location", index=0, text="")
            row = col.row(align=True)
            row.label(text="Y")
            row.prop(obj, "location", index=2, text="")
            row = col.row(align=True)
            row.label(text="Z")
            row.prop(obj, "location", index=1, text="")

            layout.separator()
            col = layout.column(align=True)
            row = col.row(align=True)
            row.label(text="Rotation")
            row.prop(obj, "rotation_euler", index=2, text="")

            layout.separator()
            col = layout.column(align=True)
            row = col.row(align=True)
            row.label(text="Width")
            row.prop(obj, "scale", index=0, text="")

        # ── Active CnR object ─────────────────────────────────────────────────
        elif _is_cnr(obj):
            if "Bank" in obj.name:
                role, icon = "Bank / Blue Team Hideout", 'HOME'
            elif "Gold" in obj.name:
                role, icon = "Gold Position", 'SOLO_ON'
            else:
                role, icon = "Robber / Red Team Hideout", 'DECORATE_DRIVER'

            layout.label(text=obj.name, icon='COMMUNITY')
            layout.label(text=role, icon=icon)

            layout.separator()
            col = layout.column(align=True)
            col.label(text="Position:")
            row = col.row(align=True)
            row.label(text="X")
            row.prop(obj, "location", index=0, text="")
            row = col.row(align=True)
            row.label(text="Y")
            row.prop(obj, "location", index=2, text="")
            row = col.row(align=True)
            row.label(text="Z")
            row.prop(obj, "location", index=1, text="")


class VIEW3D_PT_WaypointEditorTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_waypoint_editor_tools"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Waypoint Editor"

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Race Waypoints ────────────────────────────────────────────────────
        layout.label(text="Race Waypoints", icon='ARROW_LEFTRIGHT')
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "wp_race_type", text="Type")
        col.prop(scene, "wp_race_index_enum", text="Race")
        col.operator("waypoint.load_from_race_data",  text="Load from races.py",       icon='FILE_SCRIPT')
        col.operator("waypoint.load_from_csv",        text="Load Waypoints from File", icon='FILEBROWSER')

        # ── CnR Waypoints ─────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Cops & Robbers", icon='COMMUNITY')
        box = layout.box()
        col = box.column(align=True)
        col.operator("waypoint.load_cnr_from_data", text="Load from cops_and_robbers.py", icon='FILE_SCRIPT')
        col.operator("waypoint.load_cnr_from_csv",  text="Load CnR from File",            icon='FILEBROWSER')

        # ── Create ────────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Create", icon='ADD')
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "wp_create_type", text="Type")
        # Index field only relevant for race waypoints
        if scene.wp_create_type == "WAYPOINT":
            row = col.row(align=True)
            row.prop(scene, "wp_insert_index", text="At Index  (-1 = end)")
        row = col.row(align=True)
        row.operator("waypoint.create_object",          text="At Cursor",   icon='PIVOT_CURSOR').use_position = False
        row.operator("waypoint.create_object",          text="At Position", icon='OBJECT_ORIGIN').use_position = True
        col2 = col.column(align=True)
        col2.prop(scene, "wp_create_x", text="X")
        col2.prop(scene, "wp_create_z", text="Y")
        col2.prop(scene, "wp_create_y", text="Z")

        # ── Manage ────────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Manage", icon='TOOL_SETTINGS')
        row = layout.row(align=True)
        row.operator("waypoint.clear_waypoints", text="Clear Waypoints", icon='TRASH')
        row.operator("waypoint.clear_cnr",       text="Clear CnR",       icon='TRASH')

        # ── Export ────────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Export", icon='EXPORT')
        box = layout.box()
        box.prop(scene, "wp_export_brackets", text="Add brackets  [ ]")
        row = box.row(align=True)
        op = row.operator("waypoint.export", text="Selected", icon='RESTRICT_SELECT_OFF')
        op.export_all   = False
        op.add_brackets = scene.wp_export_brackets
        op = row.operator("waypoint.export", text="All", icon='WORLD')
        op.export_all   = True
        op.add_brackets = scene.wp_export_brackets


WAYPOINT_EDITOR_CLASSES = [
    VIEW3D_PT_WaypointEditorPanel,
    VIEW3D_PT_WaypointEditorTools,
]

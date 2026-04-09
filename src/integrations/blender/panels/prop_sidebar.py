import bpy
import json

from src.integrations.blender.operators.props import (
    is_prop_obj, get_prop_objects, get_unique_groups,
    rotation_label, separator_label, prop_name_to_const, prop_name_to_friendly,
    blender_to_game,
)

_PANEL_CATEGORY = "Prop Editor"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_active_prop_config(obj):
    """Return (group_id, prop_type, config_dict) or (None, None, None)."""
    if not is_prop_obj(obj):
        return None, None, None
    gid   = obj.get("mm_prop_group_id", "")
    ptype = obj.get("mm_prop_type", "fixed")
    raw   = obj.get("mm_prop_config_json", "")
    try:
        cfg = json.loads(raw)
    except Exception:
        cfg = {}
    return gid, ptype, cfg


def _friendly_name_display(name_val) -> str:
    """Show friendly label(s) for the prop name value stored in config."""
    if isinstance(name_val, list):
        if len(name_val) <= 3:
            return ", ".join(prop_name_to_friendly(n) for n in name_val)
        return f"{len(name_val)} props"
    return prop_name_to_friendly(name_val) if isinstance(name_val, str) else str(name_val)


def _count_group_instances(gid: str) -> int:
    return sum(1 for o in get_prop_objects() if o.get("mm_prop_group_id") == gid)


# ── Panel: Inspector ──────────────────────────────────────────────────────────

class VIEW3D_PT_PropEditorPanel(bpy.types.Panel):
    bl_label      = "Prop Inspector"
    bl_idname     = "VIEW3D_PT_prop_editor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category   = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        # ── Scene status ──────────────────────────────────────────────────────
        groups      = get_unique_groups()
        n_instances = len(get_prop_objects())

        box = layout.box()
        col = box.column(align=True)
        icon = "SEQUENCE_COLOR_04" if n_instances else "SEQUENCE_COLOR_01"
        col.label(text=f"{n_instances} prop instances in scene", icon=icon)

        layout.separator()

        if not is_prop_obj(obj):
            layout.label(text="Select a prop to inspect", icon="INFO")
            return

        gid, ptype, cfg = _get_active_prop_config(obj)
        instance_count  = _count_group_instances(gid)

        # ── Group summary ─────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)

        type_icon = "PARTICLE_POINT" if ptype == "random" else "OBJECT_DATA"
        type_label = "Random Group" if ptype == "random" else (
            "Row Prop" if "end" in cfg else "Single Prop"
        )

        name_val = cfg.get("name", obj.name)
        col.label(text=_friendly_name_display(name_val), icon="MESH_DATA")
        col.label(text=f"{type_label}  ·  {instance_count} instance(s)", icon=type_icon)

        # ── Action buttons ────────────────────────────────────────────────────
        layout.separator()
        row = layout.row(align=True)
        row.operator("props.select_group", text="Select Group", icon="RESTRICT_SELECT_OFF")
        row.operator("props.load_into_form", text="Edit",       icon="GREASEPENCIL")
        layout.operator("props.export_group_code", text="Copy Group as Code", icon="COPYDOWN")


# ── Panel: Edit Form ──────────────────────────────────────────────────────────

class VIEW3D_PT_PropEditorForm(bpy.types.Panel):
    bl_label      = "Edit Prop Group"
    bl_idname     = "VIEW3D_PT_prop_editor_form"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category   = _PANEL_CATEGORY
    bl_options    = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        group_id = scene.pe_active_group_id
        ptype    = scene.pe_active_group_type

        if not group_id:
            layout.label(text="Select a prop and click 'Edit'", icon="INFO")
            return

        layout.label(text=f"Editing: {group_id}", icon="GREASEPENCIL")
        layout.separator()

        # ── Prop name dropdown ────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Prop:", icon="MESH_DATA")
        col.prop(scene, "pe_prop_name", text="")

        layout.separator()

        if ptype == "fixed":
            self._draw_fixed_form(layout, scene)
        elif ptype == "random":
            self._draw_random_form(layout, scene)

    def _draw_fixed_form(self, layout, scene):
        # ── Offset ────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset (game coords):", icon="TRANSFORM_ORIGINS")
        row = col.row(align=True)
        row.prop(scene, "pe_offset_x", text="X")
        row.prop(scene, "pe_offset_y", text="Y")
        row.prop(scene, "pe_offset_z", text="Z")

        # ── End ───────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pe_has_end", text="Row Prop (has End)")
        if scene.pe_has_end:
            col.separator()
            col.label(text="End (game coords):", icon="CURVE_PATH")
            row = col.row(align=True)
            row.prop(scene, "pe_end_x", text="X")
            row.prop(scene, "pe_end_y", text="Y")
            row.prop(scene, "pe_end_z", text="Z")

        # ── Angle ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pe_has_angle", text="Has Angle")
        if scene.pe_has_angle:
            col.prop(scene, "pe_angle", text="Angle (degrees)")
            col.label(text=f"  {rotation_label(scene.pe_angle)}", icon="DRIVER_ROTATIONAL_DIFFERENCE")

    def _draw_random_form(self, layout, scene):
        # ── Area ──────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Area Min (game):", icon="WORLD")
        row = col.row(align=True)
        row.prop(scene, "pe_area_x1", text="X")
        row.prop(scene, "pe_area_y1", text="Y")
        row.prop(scene, "pe_area_z1", text="Z")
        col.separator()
        col.label(text="Area Max (game):", icon="WORLD")
        row = col.row(align=True)
        row.prop(scene, "pe_area_x2", text="X")
        row.prop(scene, "pe_area_y2", text="Y")
        row.prop(scene, "pe_area_z2", text="Z")

        # ── Seed / Count ──────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pe_seed",       text="Seed")
        col.prop(scene, "pe_rand_count", text="Count / Num Props")


# ── Panel: Tools ──────────────────────────────────────────────────────────────

class VIEW3D_PT_PropEditorTools(bpy.types.Panel):
    bl_label      = "Tools"
    bl_idname     = "VIEW3D_PT_prop_editor_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category   = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout

        # ── Load / Reload ─────────────────────────────────────────────────────
        layout.label(text="Load", icon="IMPORT")
        layout.operator("props.reload", text="Reload from props.py", icon="FILE_REFRESH")

        layout.separator()

        # ── Export ────────────────────────────────────────────────────────────
        layout.label(text="Export", icon="EXPORT")
        box = layout.box()
        col = box.column(align=True)
        col.operator("props.export_code",       text="Export All Groups",   icon="WORLD")
        col.operator("props.export_group_code", text="Export Active Group", icon="RESTRICT_SELECT_OFF")

        layout.separator()

        # ── Props collection info ─────────────────────────────────────────────
        layout.label(text="Scene", icon="SCENE_DATA")
        box = layout.box()
        col = box.column(align=True)

        n_objs = len(get_prop_objects())
        groups = get_unique_groups()
        n_fixed  = sum(1 for t, _ in groups.values() if t == "fixed")
        n_random = sum(1 for t, _ in groups.values() if t == "random")

        icon = "SEQUENCE_COLOR_04" if n_objs else "SEQUENCE_COLOR_01"
        col.label(text=f"{n_objs} prop objects in 'Props' collection", icon=icon)
        col.label(text=f"{n_fixed} fixed  /  {n_random} random group(s)")

        # ── Group list ────────────────────────────────────────────────────────
        if groups:
            layout.separator()
            layout.label(text="Prop Groups", icon="LINENUMBERS_ON")
            box = layout.box()
            col = box.column(align=True)

            for gid, (ptype, cfg) in sorted(groups.items()):
                name_val = cfg.get("name", "?")
                n_inst   = sum(1 for o in get_prop_objects() if o.get("mm_prop_group_id") == gid)
                icon     = "PARTICLE_POINT" if ptype == "random" else "OBJECT_DATA"
                label    = f"{gid}  ({n_inst}×)  {_friendly_name_display(name_val)}"
                col.label(text=label, icon=icon)


# ── Registration ──────────────────────────────────────────────────────────────

PROP_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_PropEditorPanel,
    VIEW3D_PT_PropEditorForm,
    VIEW3D_PT_PropEditorTools,
]

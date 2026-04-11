import bpy
import json

from src.integrations.blender.operators.props import (
    is_prop_obj, get_prop_objects, get_unique_groups,
    rotation_label, separator_label, prop_name_to_const, prop_name_to_friendly,
    blender_to_game, load_form_from_obj,
)

# Track the last-loaded group so we only refresh the form when selection changes
_last_loaded_group_id: str = ""

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
    # Infer type from config keys when the tag is missing or wrong
    if ptype != "random" and "area" in cfg:
        ptype = "random"
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

        # Auto-populate the Edit form whenever the selected prop changes.
        # Must be deferred via a timer — draw() is a read-only context in Blender.
        global _last_loaded_group_id
        if gid != _last_loaded_group_id:
            _last_loaded_group_id = gid
            scene_name = context.scene.name
            obj_name   = obj.name
            def _deferred_load():
                import bpy as _bpy
                scene = _bpy.data.scenes.get(scene_name)
                ob    = _bpy.data.objects.get(obj_name)
                if scene and ob:
                    load_form_from_obj(scene, ob)
            bpy.app.timers.register(_deferred_load, first_interval=0.0)

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
        row = box.row(align=True)
        row.label(text="Prop:", icon="MESH_DATA")
        row.prop(scene, "pe_prop_name", text="")

        layout.separator()

        if ptype == "fixed":
            self._draw_fixed_form(layout, scene)
        elif ptype == "random":
            self._draw_random_form(layout, scene)

    def _draw_fixed_form(self, layout, scene):
        # ── Offset ────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset:", icon="TRANSFORM_ORIGINS")
        row = col.row(align=True)
        row.prop(scene, "pe_offset_x", text="X")
        row.prop(scene, "pe_offset_y", text="Y")
        row.prop(scene, "pe_offset_z", text="Z")

        # ── Angle ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pe_angle", text="Angle (degrees)")

        # ── End ───────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pe_has_end", text="Row Prop (Offset + End)")
        if scene.pe_has_end:
            col.separator()
            col.label(text="End:", icon="CURVE_PATH")
            row = col.row(align=True)
            row.prop(scene, "pe_end_x", text="X")
            row.prop(scene, "pe_end_y", text="Y")
            row.prop(scene, "pe_end_z", text="Z")

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


# ── Panel: Prop Groups (collapsible sub-panel) ────────────────────────────────

class VIEW3D_PT_PropEditorGroups(bpy.types.Panel):
    bl_label       = "Prop Groups"
    bl_idname      = "VIEW3D_PT_prop_editor_groups"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        groups = get_unique_groups()

        if not groups:
            layout.label(text="No prop groups in scene", icon="INFO")
            return

        box = layout.box()
        col = box.column(align=True)

        for gid, (ptype, cfg) in sorted(groups.items()):
            name_val = cfg.get("name", "?")
            n_inst   = sum(1 for o in get_prop_objects() if o.get("mm_prop_group_id") == gid)
            icon     = "PARTICLE_POINT" if ptype == "random" else "OBJECT_DATA"
            label    = f"{gid}  ({n_inst}×)  {_friendly_name_display(name_val)}"
            col.label(text=label, icon=icon)


# ── Panel: Create Prop ────────────────────────────────────────────────────────

class VIEW3D_PT_PropEditorCreate(bpy.types.Panel):
    bl_label       = "Create Prop"
    bl_idname      = "VIEW3D_PT_prop_editor_create"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Type selector ─────────────────────────────────────────────────────
        box = layout.box()
        box.prop(scene, "pc_prop_type", expand=True)

        layout.separator()

        # ── Prop name ─────────────────────────────────────────────────────────
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Prop:", icon="MESH_DATA")
        row.prop(scene, "pc_prop_name", text="")

        layout.separator()

        if scene.pc_prop_type == "fixed":
            self._draw_fixed(layout, scene)
        else:
            self._draw_random(layout, scene)

        layout.separator()
        layout.operator("props.create_prop_group", text="Create Prop", icon="ADD")

    def _draw_fixed(self, layout, scene):
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset:", icon="TRANSFORM_ORIGINS")
        row = col.row(align=True)
        row.prop(scene, "pc_offset_x", text="X")
        row.prop(scene, "pc_offset_y", text="Y")
        row.prop(scene, "pc_offset_z", text="Z")

        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pc_angle", text="Angle (degrees)")

        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pc_has_end", text="Row Prop (Offset + End)")
        if scene.pc_has_end:
            col.separator()
            col.label(text="End:", icon="CURVE_PATH")
            row = col.row(align=True)
            row.prop(scene, "pc_end_x", text="X")
            row.prop(scene, "pc_end_y", text="Y")
            row.prop(scene, "pc_end_z", text="Z")

    def _draw_random(self, layout, scene):
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Area Min:", icon="WORLD")
        row = col.row(align=True)
        row.prop(scene, "pc_area_x1", text="X")
        row.prop(scene, "pc_area_y1", text="Y")
        row.prop(scene, "pc_area_z1", text="Z")
        col.separator()
        col.label(text="Area Max:", icon="WORLD")
        row = col.row(align=True)
        row.prop(scene, "pc_area_x2", text="X")
        row.prop(scene, "pc_area_y2", text="Y")
        row.prop(scene, "pc_area_z2", text="Z")

        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "pc_seed",       text="Seed")
        col.prop(scene, "pc_rand_count", text="Count")


# ── Registration ──────────────────────────────────────────────────────────────

PROP_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_PropEditorPanel,
    VIEW3D_PT_PropEditorForm,
    VIEW3D_PT_PropEditorCreate,
    VIEW3D_PT_PropEditorTools,
    VIEW3D_PT_PropEditorGroups,
]

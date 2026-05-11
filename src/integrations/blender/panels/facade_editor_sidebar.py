"""
Facade Editor sidebar panels.  Tab: "Facade Editor"  (VIEW_3D → N-panel)

Panels:
  1. Facade Inspector   – scene status + selected facade details
  2. Edit Facade Group  – live-edit all parameters of the active group
  3. Create Facade      – form to create a new facade group
  4. Tools              – Load / Export / Save FCD
  5. Facade Groups      – collapsible overview of all groups + statistics
"""
import bpy

from src.integrations.blender.operators.facades import (
    is_facade_obj, get_facade_objects, get_unique_groups,
    facade_name_to_friendly, flags_to_const,
    load_form_from_obj, _panel_positions,
    is_dt_cfg, _resolve_scale, _to_tagged_parent,
)

_PANEL_CATEGORY = "Facades"

# Track last-loaded group so we defer form refresh only when selection changes.
_last_loaded_group_id: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _flags_label(flags_val: int) -> str:
    return flags_to_const(flags_val).replace("FcdFlags.", "")


def _count_panels(cfg: dict) -> int:
    return len(_panel_positions(cfg))


def _count_group_instances(gid: str) -> int:
    return sum(1 for o in get_facade_objects() if o.get("mm_facade_group_id") == gid)


def _draw_xyz_row(layout, scene, prefix: str, field: str, labels=("X", "Y", "Z")):
    row = layout.row(align=True)
    for axis_letter, axis in zip(labels, "xyz"):
        row.prop(scene, f"{prefix}_{field}_{axis}", text=axis_letter)


# ── Panel 1: Inspector ────────────────────────────────────────────────────────

class VIEW3D_PT_FacadeEditorPanel(bpy.types.Panel):
    bl_label       = "Facade Inspector"
    bl_idname      = "VIEW3D_PT_facade_editor"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        groups      = get_unique_groups()
        n_instances = len(get_facade_objects())

        box = layout.box()
        col = box.column(align=True)
        icon = "SEQUENCE_COLOR_04" if n_instances else "SEQUENCE_COLOR_01"
        col.label(text=f"{n_instances} facade instance(s)  ·  {len(groups)} group(s)", icon=icon)

        layout.separator()

        if not is_facade_obj(obj):
            layout.label(text="Select a facade to inspect", icon="INFO")
            return

        tagged = _to_tagged_parent(obj)
        gid    = tagged.get("mm_facade_group_id", "") if tagged else ""
        if not gid:
            layout.label(text="Selected object is not part of a facade group", icon="ERROR")
            return

        # Auto-populate edit form when selection changes (deferred timer).
        global _last_loaded_group_id
        if gid != _last_loaded_group_id:
            _last_loaded_group_id = gid
            scene_name  = context.scene.name
            tagged_name = tagged.name
            def _deferred():
                import bpy as _bpy
                sc = _bpy.data.scenes.get(scene_name)
                ob = _bpy.data.objects.get(tagged_name)
                if sc and ob:
                    load_form_from_obj(sc, ob)
            bpy.app.timers.register(_deferred, first_interval=0.0)

        try:
            import json
            cfg = json.loads(tagged.get("mm_facade_config_json", "{}"))
        except Exception:
            cfg = {}

        name_val       = cfg.get("name", tagged.get("mm_facade_name", "?"))
        flags_val      = int(cfg.get("flags", 1))
        n_panels_group = _count_group_instances(gid)
        dt             = is_dt_cfg(cfg)

        box = layout.box()
        col = box.column(align=True)
        title = facade_name_to_friendly(name_val)
        if dt:
            title += "  · DT"
        col.label(text=title, icon="HOME" if dt else "MESH_DATA")
        col.label(text=f"{_flags_label(flags_val)}  ·  {n_panels_group} panel(s)", icon="MOD_LATTICE")

        sides = cfg.get("sides", [0.0, 0.0, 0.0])
        if dt:
            sides_str = f"({sides[0]:.1f}, {sides[1]:.1f}, {sides[2]:.1f})  3D point"
        else:
            sides_str = f"L={sides[0]:.1f}  R={sides[1]:.1f}  D={sides[2]:.1f}"
        col.label(text=f"Sides: {sides_str}", icon="BLANK1")

        scale_auto = cfg.get("scale_auto", True)
        if scale_auto:
            scale_str = f"auto = {_resolve_scale(cfg):.2f}"
        else:
            scale_str = f"{cfg.get('scale', 1.0):.3f}"
        col.label(text=f"Scale: {scale_str}  ·  Sep: {cfg.get('separator', 10.0):.2f}", icon="BLANK1")

        layout.separator()
        row = layout.row(align=True)
        row.operator("facades.select_group",  text="Select Group", icon="RESTRICT_SELECT_OFF")
        row.operator("facades.load_into_form", text="Edit",        icon="GREASEPENCIL")
        row = layout.row(align=True)
        row.operator("facades.duplicate_group", text="Duplicate",  icon="DUPLICATE")
        row.operator("facades.delete_group",    text="Delete",     icon="TRASH")
        row = layout.row(align=True)
        row.operator("facades.export_group_code", text="Copy as Code", icon="COPYDOWN")


# ── Panel 2: Edit Form ────────────────────────────────────────────────────────

class VIEW3D_PT_FacadeEditorForm(bpy.types.Panel):
    bl_label       = "Edit Facade Group"
    bl_idname      = "VIEW3D_PT_facade_editor_form"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout   = self.layout
        scene    = context.scene
        group_id = scene.fe_active_group_id

        if not group_id:
            layout.label(text="Select a facade and click 'Edit'", icon="INFO")
            return

        groups = get_unique_groups()
        cfg    = groups.get(group_id, {})
        dt     = is_dt_cfg(cfg)

        layout.label(text=f"Editing: {group_id}", icon="GREASEPENCIL")
        if dt:
            layout.label(text="DT building (mmBuildingInstance render path)", icon="HOME")
        layout.separator()

        # ── Facade name ───────────────────────────────────────────────────────
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Facade:", icon="MESH_DATA")
        row.prop(scene, "fe_facade_name", text="")

        layout.separator()

        # ── Flags ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Flags:", icon="MOD_LATTICE")
        col.prop(scene, "fe_flags", text="")

        layout.separator()

        # ── Offset / End ──────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset (start):", icon="TRANSFORM_ORIGINS")
        _draw_xyz_row(col, scene, "fe", "offset")
        op = col.operator("facades.bake_from_cursor", text="Use 3D Cursor", icon="PIVOT_CURSOR")
        op.target = "offset"; op.form = "edit"

        col.separator()
        col.label(text="End:", icon="CURVE_PATH")
        _draw_xyz_row(col, scene, "fe", "end")
        op = col.operator("facades.bake_from_cursor", text="Use 3D Cursor", icon="PIVOT_CURSOR")
        op.target = "end"; op.form = "edit"

        layout.separator()

        # ── Axis / Separator (irrelevant for DT) ─────────────────────────────
        if not dt:
            box = layout.box()
            col = box.column(align=True)
            row = col.row(align=True)
            row.label(text="Axis:", icon="ORIENTATION_GLOBAL")
            row.prop(scene, "fe_axis", expand=True)
            col.separator()
            col.prop(scene, "fe_separator", text="Separator (panel width)")
            layout.separator()

        # ── Sides ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        if dt:
            col.label(text="Sides  (3D point — third corner):", icon="MOD_BUILD")
            row = col.row(align=True)
            row.prop(scene, "fe_sides_x", text="X")
            row.prop(scene, "fe_sides_y", text="Y")
            row.prop(scene, "fe_sides_z", text="Z")
        else:
            col.label(text="Sides  (Left, Right, Depth):", icon="MOD_SOLIDIFY")
            row = col.row(align=True)
            row.prop(scene, "fe_sides_x", text="L")
            row.prop(scene, "fe_sides_y", text="R")
            row.prop(scene, "fe_sides_z", text="D")

        layout.separator()

        # ── Scale ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        if dt:
            col.label(text="Scale: not used by DT renderer", icon="INFO")
        col.prop(scene, "fe_scale_auto", text="Auto Scale  (from FCD scales.txt)")
        sub = col.row()
        sub.enabled = not scene.fe_scale_auto
        sub.prop(scene, "fe_scale", text="Manual Scale")
        if scene.fe_scale_auto and not dt:
            col.label(text=f"Resolved: {_resolve_scale(cfg):.3f}", icon="DRIVER")


# ── Panel 3: Create Facade ────────────────────────────────────────────────────

class VIEW3D_PT_FacadeEditorCreate(bpy.types.Panel):
    bl_label       = "Create Facade"
    bl_idname      = "VIEW3D_PT_facade_editor_create"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        try:
            flags_int = int(scene.fc_flags)
        except (ValueError, TypeError):
            flags_int = 0
        creating_dt = bool(flags_int & 0x004)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Facade:", icon="MESH_DATA")
        row.prop(scene, "fc_facade_name", text="")

        layout.separator()

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Flags:", icon="MOD_LATTICE")
        col.prop(scene, "fc_flags", text="")
        if creating_dt:
            col.label(text="DT building (3D footprint mode)", icon="HOME")

        layout.separator()

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset (start):", icon="TRANSFORM_ORIGINS")
        _draw_xyz_row(col, scene, "fc", "offset")
        op = col.operator("facades.bake_from_cursor", text="Use 3D Cursor", icon="PIVOT_CURSOR")
        op.target = "offset"; op.form = "create"

        col.separator()
        col.label(text="End:", icon="CURVE_PATH")
        _draw_xyz_row(col, scene, "fc", "end")
        op = col.operator("facades.bake_from_cursor", text="Use 3D Cursor", icon="PIVOT_CURSOR")
        op.target = "end"; op.form = "create"

        layout.separator()

        if not creating_dt:
            box = layout.box()
            col = box.column(align=True)
            row = col.row(align=True)
            row.label(text="Axis:", icon="ORIENTATION_GLOBAL")
            row.prop(scene, "fc_axis", expand=True)
            col.separator()
            col.prop(scene, "fc_separator", text="Separator (panel width)")
            layout.separator()

        box = layout.box()
        col = box.column(align=True)
        if creating_dt:
            col.label(text="Sides  (3D point — third corner):", icon="MOD_BUILD")
            row = col.row(align=True)
            row.prop(scene, "fc_sides_x", text="X")
            row.prop(scene, "fc_sides_y", text="Y")
            row.prop(scene, "fc_sides_z", text="Z")
        else:
            col.label(text="Sides  (Left, Right, Depth):", icon="MOD_SOLIDIFY")
            row = col.row(align=True)
            row.prop(scene, "fc_sides_x", text="L")
            row.prop(scene, "fc_sides_y", text="R")
            row.prop(scene, "fc_sides_z", text="D")

        layout.separator()

        if not creating_dt:
            box = layout.box()
            col = box.column(align=True)
            col.prop(scene, "fc_scale_auto", text="Auto Scale  (from FCD scales.txt)")
            sub = col.row()
            sub.enabled = not scene.fc_scale_auto
            sub.prop(scene, "fc_scale", text="Manual Scale")

        layout.separator()
        layout.operator("facades.create_group", text="Create Facade", icon="ADD")


# ── Panel 4: Tools ────────────────────────────────────────────────────────────

class VIEW3D_PT_FacadeEditorTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_facade_editor_tools"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout

        layout.label(text="Load", icon="IMPORT")
        row = layout.row(align=True)
        row.operator("facades.reload",        text="Reload from facades.py", icon="FILE_REFRESH")
        row.operator("facades.clear",         text="Clear",                   icon="X")
        layout.operator("facades.load_external", text="Load External FCD",   icon="FILEBROWSER")

        layout.separator()

        layout.label(text="Export", icon="EXPORT")
        box = layout.box()
        col = box.column(align=True)
        col.operator("facades.export_code",       text="Export All as Code",    icon="WORLD")
        col.operator("facades.export_group_code", text="Export Active as Code", icon="RESTRICT_SELECT_OFF")
        col.separator()
        col.operator("facades.save_fcd",          text="Save FCD File",         icon="FILE")


# ── Panel 5: Facade Groups (collapsible) ─────────────────────────────────────

class VIEW3D_PT_FacadeEditorGroups(bpy.types.Panel):
    bl_label       = "Facade Groups"
    bl_idname      = "VIEW3D_PT_facade_editor_groups"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        groups = get_unique_groups()

        if not groups:
            layout.label(text="No facade groups in scene", icon="INFO")
            return

        type_counts: dict = {}
        total_panels = 0
        n_dt = 0
        for gid, cfg in groups.items():
            n = _count_panels(cfg)
            total_panels += n
            if is_dt_cfg(cfg):
                n_dt += 1
            label = facade_name_to_friendly(cfg.get("name", "?"))
            type_counts[label] = type_counts.get(label, 0) + n

        stats_box = layout.box()
        stats_col = stats_box.column(align=True)
        stats_col.label(
            text=f"{total_panels} panels  ·  {len(groups)} groups  ·  {len(type_counts)} types",
            icon="INFO",
        )
        if n_dt:
            stats_col.label(text=f"  {n_dt} DT-mode group(s)", icon="HOME")
        for label, cnt in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
            stats_col.label(text=f"  {cnt}×  {label}")
        if len(type_counts) > 10:
            stats_col.label(text=f"  … and {len(type_counts) - 10} more types")


FACADE_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_FacadeEditorPanel,
    VIEW3D_PT_FacadeEditorForm,
    VIEW3D_PT_FacadeEditorCreate,
    VIEW3D_PT_FacadeEditorTools,
    VIEW3D_PT_FacadeEditorGroups,
]

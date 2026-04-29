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
    FACADE_FLAGS_ITEMS,
)

_PANEL_CATEGORY = "Facade Editor"

# Track last-loaded group so we defer form refresh only when selection changes.
_last_loaded_group_id: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _flags_label(flags_val: int) -> str:
    """Return a short human label for a flags integer."""
    return flags_to_const(flags_val).replace("FcdFlags.", "")


def _count_panels(cfg: dict) -> int:
    return len(_panel_positions(cfg))


def _count_group_instances(gid: str) -> int:
    return sum(1 for o in get_facade_objects() if o.get("mm_facade_group_id") == gid)


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

        # ── Scene status ──────────────────────────────────────────────────────
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

        # Resolve to tagged parent if user clicked a child mesh
        tagged = obj if "mm_facade_group_id" in obj else obj.parent
        gid = tagged.get("mm_facade_group_id", "") if tagged else ""

        # Auto-populate edit form when selection changes (deferred timer).
        global _last_loaded_group_id
        if gid != _last_loaded_group_id:
            _last_loaded_group_id = gid
            scene_name = context.scene.name
            tagged_name = tagged.name if tagged else obj.name
            def _deferred():
                import bpy as _bpy
                sc = _bpy.data.scenes.get(scene_name)
                ob = _bpy.data.objects.get(tagged_name)
                if sc and ob:
                    load_form_from_obj(sc, ob)
            bpy.app.timers.register(_deferred, first_interval=0.0)

        # ── Group summary ─────────────────────────────────────────────────────
        try:
            import json
            cfg = json.loads(tagged.get("mm_facade_config_json", "{}") if tagged else "{}")
        except Exception:
            cfg = {}

        name_val       = cfg.get("name", tagged.get("mm_facade_name", "?") if tagged else "?")
        flags_val      = int(cfg.get("flags", 1))
        n_panels_group = _count_group_instances(gid)

        box = layout.box()
        col = box.column(align=True)
        col.label(text=facade_name_to_friendly(name_val), icon="MESH_DATA")
        col.label(text=f"{_flags_label(flags_val)}  ·  {n_panels_group} panel(s)", icon="MOD_LATTICE")

        sides = cfg.get("sides", [0.0, 0.0, 0.0])
        sides_str = f"L={sides[0]:.1f}  R={sides[1]:.1f}  D={sides[2]:.1f}"
        col.label(text=f"Sides: {sides_str}", icon="BLANK1")

        scale_auto = cfg.get("scale_auto", True)
        scale_str  = "auto" if scale_auto else f"{cfg.get('scale', 1.0):.3f}"
        col.label(text=f"Scale: {scale_str}  ·  Sep: {cfg.get('separator', 10.0):.2f}", icon="BLANK1")

        # ── Action buttons ────────────────────────────────────────────────────
        layout.separator()
        row = layout.row(align=True)
        row.operator("facades.select_group",  text="Select Group", icon="RESTRICT_SELECT_OFF")
        row.operator("facades.load_into_form", text="Edit",        icon="GREASEPENCIL")
        row = layout.row(align=True)
        row.operator("facades.export_group_code", text="Copy as Code", icon="COPYDOWN")
        row.operator("facades.delete_group",      text="Delete",       icon="TRASH")


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

        layout.label(text=f"Editing: {group_id}", icon="GREASEPENCIL")
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
        row = col.row(align=True)
        row.prop(scene, "fe_offset_x", text="X")
        row.prop(scene, "fe_offset_y", text="Y")
        row.prop(scene, "fe_offset_z", text="Z")
        col.separator()
        col.label(text="End:", icon="CURVE_PATH")
        row = col.row(align=True)
        row.prop(scene, "fe_end_x", text="X")
        row.prop(scene, "fe_end_y", text="Y")
        row.prop(scene, "fe_end_z", text="Z")

        layout.separator()

        # ── Axis / Separator ──────────────────────────────────────────────────
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
        col.label(text="Sides  (Left, Right, Depth):", icon="MOD_SOLIDIFY")
        row = col.row(align=True)
        row.prop(scene, "fe_sides_x", text="L")
        row.prop(scene, "fe_sides_y", text="R")
        row.prop(scene, "fe_sides_z", text="D")

        layout.separator()

        # ── Scale ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "fe_scale_auto", text="Auto Scale  (from FCD scales.txt)")
        sub = col.row()
        sub.enabled = not scene.fe_scale_auto
        sub.prop(scene, "fe_scale", text="Manual Scale")


# ── Panel 3: Create Facade ────────────────────────────────────────────────────

class VIEW3D_PT_FacadeEditorCreate(bpy.types.Panel):
    bl_label       = "Create Facade"
    bl_idname      = "VIEW3D_PT_facade_editor_create"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Name ──────────────────────────────────────────────────────────────
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Facade:", icon="MESH_DATA")
        row.prop(scene, "fc_facade_name", text="")

        layout.separator()

        # ── Flags ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Flags:", icon="MOD_LATTICE")
        col.prop(scene, "fc_flags", text="")

        layout.separator()

        # ── Offset / End ──────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset (start):", icon="TRANSFORM_ORIGINS")
        row = col.row(align=True)
        row.prop(scene, "fc_offset_x", text="X")
        row.prop(scene, "fc_offset_y", text="Y")
        row.prop(scene, "fc_offset_z", text="Z")
        col.separator()
        col.label(text="End:", icon="CURVE_PATH")
        row = col.row(align=True)
        row.prop(scene, "fc_end_x", text="X")
        row.prop(scene, "fc_end_y", text="Y")
        row.prop(scene, "fc_end_z", text="Z")

        layout.separator()

        # ── Axis / Separator ──────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="Axis:", icon="ORIENTATION_GLOBAL")
        row.prop(scene, "fc_axis", expand=True)
        col.separator()
        col.prop(scene, "fc_separator", text="Separator (panel width)")

        layout.separator()

        # ── Sides ─────────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Sides  (Left, Right, Depth):", icon="MOD_SOLIDIFY")
        row = col.row(align=True)
        row.prop(scene, "fc_sides_x", text="L")
        row.prop(scene, "fc_sides_y", text="R")
        row.prop(scene, "fc_sides_z", text="D")

        layout.separator()

        # ── Scale ─────────────────────────────────────────────────────────────
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

        # ── Load / Reload ─────────────────────────────────────────────────────
        layout.label(text="Load", icon="IMPORT")
        row = layout.row(align=True)
        row.operator("facades.reload",        text="Reload from facades.py", icon="FILE_REFRESH")
        row.operator("facades.clear",         text="Clear",                   icon="X")
        layout.operator("facades.load_external", text="Load External FCD",   icon="FILEBROWSER")

        layout.separator()

        # ── Export ────────────────────────────────────────────────────────────
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

        # ── Summary ───────────────────────────────────────────────────────────
        all_objs     = get_facade_objects()
        type_counts: dict = {}
        total_panels = 0
        for gid, cfg in groups.items():
            n = _count_panels(cfg)
            total_panels += n
            label = facade_name_to_friendly(cfg.get("name", "?"))
            type_counts[label] = type_counts.get(label, 0) + n

        stats_box = layout.box()
        stats_col = stats_box.column(align=True)
        stats_col.label(
            text=f"{total_panels} panels  ·  {len(groups)} groups  ·  {len(type_counts)} types",
            icon="INFO",
        )
        for label, cnt in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
            stats_col.label(text=f"  {cnt}×  {label}")
        if len(type_counts) > 10:
            stats_col.label(text=f"  … and {len(type_counts) - 10} more types")


# ── Registration ──────────────────────────────────────────────────────────────

FACADE_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_FacadeEditorPanel,
    VIEW3D_PT_FacadeEditorForm,
    VIEW3D_PT_FacadeEditorCreate,
    VIEW3D_PT_FacadeEditorTools,
    VIEW3D_PT_FacadeEditorGroups,
]

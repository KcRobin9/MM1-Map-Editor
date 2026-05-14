"""
Bridge Editor sidebar panels.  Tab: "Bridges"  (VIEW_3D → N-panel)

Panels:
  1. Bridge Inspector  — scene status + selected bridge entry summary
  2. Edit Bridge Entry — live-edit offset / angle / prop type of one entry
  3. Create Bridge     — quick form to spawn a full bridge group
  4. Tools             — Load/Save/Reload/Export/Clear
  5. Bridge Groups     — overview of all groups in the scene
"""
import bpy

from src.integrations.blender.modeling.bridges import (
    TAG_GROUP_ID, TAG_ENTRY_IDX, TAG_ROLE, TAG_NAME,
    get_bridge_objects, get_unique_groups, is_bridge_obj,
)
from src.integrations.blender.operators.bridges import (
    bridge_name_to_friendly, load_form_from_obj,
)


_PANEL_CATEGORY = "Bridges"
_last_loaded_obj_name: str = ""


# ── Panel 1: Inspector ────────────────────────────────────────────────────────

class VIEW3D_PT_BridgeInspector(bpy.types.Panel):
    bl_label       = "Bridge Inspector"
    bl_idname      = "VIEW3D_PT_bridge_inspector"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        groups = get_unique_groups()
        n_objs = len(get_bridge_objects())

        box = layout.box()
        col = box.column(align=True)
        icon = "SEQUENCE_COLOR_04" if n_objs else "SEQUENCE_COLOR_01"
        col.label(text=f"{n_objs} entries  ·  {len(groups)} bridge(s)", icon=icon)

        layout.separator()

        if not is_bridge_obj(obj):
            layout.label(text="Select a bridge to inspect", icon="INFO")
            return

        # Auto-populate edit form when selection changes
        global _last_loaded_obj_name
        if obj.name != _last_loaded_obj_name:
            _last_loaded_obj_name = obj.name
            scene_name = context.scene.name
            obj_name   = obj.name
            def _deferred():
                sc = bpy.data.scenes.get(scene_name)
                ob = bpy.data.objects.get(obj_name)
                if sc and ob:
                    load_form_from_obj(sc, ob)
            bpy.app.timers.register(_deferred, first_interval=0.0)

        gid       = obj.get(TAG_GROUP_ID, "?")
        role      = obj.get(TAG_ROLE, "?")
        entry_idx = obj.get(TAG_ENTRY_IDX, 0)
        name      = obj.get(TAG_NAME, "?")

        box = layout.box()
        c   = box.column(align=True)
        role_icon = "MOD_BUILD" if role == "drawbridge" else "OUTLINER_OB_LATTICE"
        c.label(text=bridge_name_to_friendly(name), icon="MESH_DATA")
        c.label(text=f"{gid}  ·  entry #{entry_idx}  ·  {role}", icon=role_icon)

        layout.separator()
        row = layout.row(align=True)
        row.operator("bridges.select_group",   text="Select Group", icon="RESTRICT_SELECT_OFF")
        row.operator("bridges.load_into_form", text="Edit",         icon="GREASEPENCIL")
        row = layout.row(align=True)
        row.operator("bridges.delete_group",   text="Delete Group", icon="TRASH")


# ── Panel 2: Edit ─────────────────────────────────────────────────────────────

class VIEW3D_PT_BridgeEditForm(bpy.types.Panel):
    bl_label       = "Edit Bridge Entry"
    bl_idname      = "VIEW3D_PT_bridge_edit_form"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        if not scene.be_active_obj_name:
            layout.label(text="Select a bridge and click Edit", icon="INFO")
            return

        layout.label(text=f"Editing: {scene.be_active_obj_name}", icon="GREASEPENCIL")
        layout.separator()

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Prop:", icon="MESH_DATA")
        row.prop(scene, "be_prop_name", text="")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Offset:", icon="TRANSFORM_ORIGINS")
        row = col.row(align=True)
        row.prop(scene, "be_offset_x", text="X")
        row.prop(scene, "be_offset_y", text="Y")
        row.prop(scene, "be_offset_z", text="Z")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Rotation:", icon="DRIVER_ROTATIONAL_DIFFERENCE")
        col.prop(scene, "be_angle", text="Angle (degrees)")


# ── Panel 3: Create ───────────────────────────────────────────────────────────

class VIEW3D_PT_BridgeCreate(bpy.types.Panel):
    bl_label       = "Create Bridge"
    bl_idname      = "VIEW3D_PT_bridge_create"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Centre offset (game):", icon="TRANSFORM_ORIGINS")
        row = col.row(align=True)
        row.prop(scene, "bc_offset_x", text="X")
        row.prop(scene, "bc_offset_y", text="Y")
        row.prop(scene, "bc_offset_z", text="Z")

        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "bc_angle",     text="Angle (deg)")
        col.prop(scene, "bc_span",      text="Span (between halves)")
        col.prop(scene, "bc_gate_offset", text="Gate Offset")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Prop types:", icon="MESH_DATA")
        col.prop(scene, "bc_drawbridge_name", text="Drawbridge")
        col.prop(scene, "bc_crossgate_name",  text="Crossgate")

        layout.separator()
        layout.operator("bridges.create_bridge", text="Create Bridge", icon="ADD")


# ── Panel 4: Tools ────────────────────────────────────────────────────────────

class VIEW3D_PT_BridgeTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_bridge_tools"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout

        layout.label(text="Load", icon="IMPORT")
        row = layout.row(align=True)
        row.operator("bridges.reload_from_py", text="Reload bridges.py", icon="FILE_REFRESH")
        row.operator("bridges.clear",          text="Clear",             icon="X")
        layout.operator("bridges.load_external", text="Load External GIZMO", icon="FILEBROWSER")

        layout.separator()

        layout.label(text="Export", icon="EXPORT")
        box = layout.box()
        col = box.column(align=True)
        col.operator("bridges.export_code", text="Export as Code", icon="COPYDOWN")
        col.operator("bridges.save_gizmo",  text="Save GIZMO File", icon="FILE")


# ── Panel 5: Groups summary ───────────────────────────────────────────────────

class VIEW3D_PT_BridgeGroups(bpy.types.Panel):
    bl_label       = "Bridge Groups"
    bl_idname      = "VIEW3D_PT_bridge_groups"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        groups = get_unique_groups()
        if not groups:
            layout.label(text="No bridges in scene", icon="INFO")
            return

        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"{len(groups)} bridge(s)", icon="INFO")
        for gid in sorted(groups.keys(),
                          key=lambda g: int(g.split("_")[-1]) if g.split("_")[-1].isdigit() else 0):
            objs = groups[gid]
            n_db = sum(1 for o in objs if o.get(TAG_ROLE) == "drawbridge")
            n_cg = sum(1 for o in objs if o.get(TAG_ROLE) == "attribute")
            col.label(text=f"  {gid}: {n_db} drawbridge(s) + {n_cg} crossgate(s)")


BRIDGE_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_BridgeInspector,
    VIEW3D_PT_BridgeEditForm,
    VIEW3D_PT_BridgeCreate,
    VIEW3D_PT_BridgeTools,
    VIEW3D_PT_BridgeGroups,
]

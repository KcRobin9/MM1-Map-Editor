"""Dash Editor sidebar panels.  Tab: "Dash Editor"  (VIEW_3D → N-panel)

Panels:
  1. Dash      – pick car, load/clear, part list, new-from-template
  2. Gauges    – needle sweep (min/max), max speed/rpm, wheel-fact, live preview
  3. Placement – per-part selection + move hint, sync note
  4. Camera    – cockpit POV camera (FOV/pitch/offset/clip) + look-through
  5. Customize – swap a part from another car, reskin a texture
  6. Export    – write to SHOP + pack override AR + start game
"""
import bpy

from src.integrations.blender.operators.dash_editor import (
    get_dash_objects, get_dash_root, _DASH_TAG,
)

_CATEGORY = "Dash Editor"

_PART_LABEL = {
    "dash":          "Dashboard",
    "roof":          "Roof",
    "wheel":         "Steering Wheel",
    "gear":          "Gear Indicator",
    "speed_needle":  "Speed Needle",
    "tach_needle":   "Tach Needle",
    "damage_needle": "Damage Needle",
}
_PART_ICON = {
    "dash":          "MESH_PLANE",
    "roof":          "MESH_PLANE",
    "wheel":         "MESH_CIRCLE",
    "gear":          "SMALL_CAPS",
    "speed_needle":  "EMPTY_SINGLE_ARROW",
    "tach_needle":   "EMPTY_SINGLE_ARROW",
    "damage_needle": "EMPTY_SINGLE_ARROW",
}


def _has_dash() -> bool:
    return get_dash_root() is not None


# ── Panel 1: Dash ───────────────────────────────────────────────────────────────

class VIEW3D_PT_DashEditorDash(bpy.types.Panel):
    bl_label       = "Dash"
    bl_idname      = "VIEW3D_PT_dash_editor_dash"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        obj    = context.active_object

        layout.prop(scene, "de_dash_car", text="Car")
        row = layout.row(align=True)
        row.operator("dash.load_dash", text="Load Dash", icon="FILE_FOLDER")
        row.operator("dash.clear_dash", text="Clear", icon="X")

        root = get_dash_root()
        if root is not None:
            layout.separator(factor=0.5)
            box = layout.box()
            box.label(text=f"{root['mm_car_name']} dash", icon="AUTO")

            col = box.column(align=True)
            for o in sorted(get_dash_objects(), key=lambda x: x.get(_DASH_TAG, "")):
                tag = o.get(_DASH_TAG, "?")
                if tag in ("root", "pov_camera"):
                    continue
                r  = col.row(align=True)
                op = r.operator("dash.select_part",
                                text=_PART_LABEL.get(tag, tag),
                                icon=_PART_ICON.get(tag, "OBJECT_DATA"),
                                depress=(o == obj))
                op.part_tag = tag

        layout.separator(factor=0.5)
        nbox = layout.box()
        nbox.label(text="New From Template:", icon="ADD")
        nrow = nbox.row(align=True)
        nrow.prop(scene, "de_new_car", text="")
        nrow.operator("dash.new_dash", text="Create")


# ── Panel 2: Gauges ─────────────────────────────────────────────────────────────

class VIEW3D_PT_DashEditorGauges(bpy.types.Panel):
    bl_label       = "Gauges"
    bl_idname      = "VIEW3D_PT_dash_editor_gauges"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    @classmethod
    def poll(cls, context):
        return _has_dash()

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        box = layout.box()
        box.label(text="Live Preview", icon="PLAY")
        box.prop(scene, "de_preview", text="Value", slider=True)
        box.operator("dash.reset_preview", text="Reset Gauges", icon="LOOP_BACK")

        col = layout.column(align=True)
        col.label(text="Needle Sweep (radians):")
        for label, lo, hi in (
            ("Speed",  "de_speed_rot_min",  "de_speed_rot_max"),
            ("RPM",    "de_rpm_rot_min",    "de_rpm_rot_max"),
            ("Damage", "de_damage_rot_min", "de_damage_rot_max"),
        ):
            row = col.row(align=True)
            row.label(text=label)
            row.prop(scene, lo, text="Min")
            row.prop(scene, hi, text="Max")

        layout.separator(factor=0.5)
        sbox = layout.box()
        sbox.label(text="Scale:")
        sbox.prop(scene, "de_max_speed", text="Max Speed")
        sbox.prop(scene, "de_max_rpm",   text="Max RPM")
        sbox.prop(scene, "de_min_speed", text="Min Speed")
        sbox.prop(scene, "de_wheel_fact", text="Wheel Factor")


# ── Panel 3: Placement ──────────────────────────────────────────────────────────

class VIEW3D_PT_DashEditorPlacement(bpy.types.Panel):
    bl_label       = "Placement"
    bl_idname      = "VIEW3D_PT_dash_editor_placement"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _has_dash()

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        layout.label(text="Move parts in the viewport;", icon="ORIENTATION_GLOBAL")
        layout.label(text="positions are read on export.")

        if obj is not None and obj.get(_DASH_TAG) not in (None, "root", "pov_camera"):
            box = layout.box()
            box.label(text=_PART_LABEL.get(obj[_DASH_TAG], obj[_DASH_TAG]),
                      icon="OBJECT_DATA")
            box.prop(obj, "location", text="")
            if obj.get(_DASH_TAG) in ("speed_needle", "tach_needle", "damage_needle"):
                box.label(text="(needle angle set in Gauges)", icon="INFO")
        else:
            layout.label(text="Select a dash part.", icon="RESTRICT_SELECT_ON")


# ── Panel 4: Camera ─────────────────────────────────────────────────────────────

class VIEW3D_PT_DashEditorCamera(bpy.types.Panel):
    bl_label       = "Camera"
    bl_idname      = "VIEW3D_PT_dash_editor_camera"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _has_dash()

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        layout.operator("dash.look_through_camera", text="Look Through Camera", icon="CAMERA_DATA")
        col = layout.column(align=True)
        col.prop(scene, "de_cam_fov", text="FOV")
        col.prop(scene, "de_cam_pitch", text="Pitch")
        col.prop(scene, "de_cam_offset", text="Offset")

        clip = layout.column(align=True)
        clip.prop(scene, "de_cam_near", text="Near Clip")
        clip.prop(scene, "de_cam_far", text="Far Clip")


# ── Panel 5: Customize ──────────────────────────────────────────────────────────

class VIEW3D_PT_DashEditorCustomize(bpy.types.Panel):
    bl_label       = "Customize"
    bl_idname      = "VIEW3D_PT_dash_editor_customize"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return _has_dash()

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        obj    = context.active_object

        sbox = layout.box()
        sbox.label(text="Swap Part From Another Car:", icon="UV_SYNC_SELECT")
        sbox.prop(scene, "de_swap_car", text="Source")
        sbox.operator("dash.swap_part", text="Swap Steering Wheel", icon="MESH_CIRCLE").part_tag = "wheel"

        sel_tag = obj.get(_DASH_TAG) if obj is not None else None
        if sel_tag not in (None, "root", "pov_camera"):
            sbox.operator("dash.swap_part",
                          text=f"Swap Selected ({_PART_LABEL.get(sel_tag, sel_tag)})",
                          icon="IMPORT").part_tag = sel_tag

        rbox = layout.box()
        rbox.label(text="Reskin Texture:", icon="TEXTURE")

        active_dash = sel_tag not in (None, "root", "pov_camera")
        col = rbox.column()
        col.enabled = active_dash
        col.prop(scene, "de_reskin_texture", text="")
        if active_dash:
            slot = obj.active_material_index
            mats = obj.data.materials
            slot_name = mats[slot].name if 0 <= slot < len(mats) and mats[slot] else "?"
            rbox.label(text=f"Active slot: {slot_name}", icon="MATERIAL")
        else:
            rbox.label(text="Select a dash part first.", icon="INFO")

        rbox.separator()
        rbox.label(text="Or a custom .DDS:")
        crow = rbox.row(align=True)
        crow.prop(scene, "de_reskin_image", text="")
        crow.operator("dash.reskin_part", text="", icon="BRUSH_DATA")


# ── Panel 6: Export ─────────────────────────────────────────────────────────────

class VIEW3D_PT_DashEditorExport(bpy.types.Panel):
    bl_label       = "Export"
    bl_idname      = "VIEW3D_PT_dash_editor_export"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    @classmethod
    def poll(cls, context):
        return _has_dash()

    def draw(self, context):
        layout = self.layout

        layout.operator("dash.export_dash", text="Export Dash", icon="EXPORT")
        layout.operator("dash.pack_and_start_game", text="Create AR + Start Game", icon="PLAY")
        layout.label(text="Packs !!!…{car}_DASH.ar (override).", icon="INFO")


DASH_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_DashEditorDash,
    VIEW3D_PT_DashEditorGauges,
    VIEW3D_PT_DashEditorPlacement,
    VIEW3D_PT_DashEditorCamera,
    VIEW3D_PT_DashEditorCustomize,
    VIEW3D_PT_DashEditorExport,
]

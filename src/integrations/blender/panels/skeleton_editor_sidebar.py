"""Skeleton Editor sidebar panels. Tab: "Skel Editor" (VIEW_3D N-panel)"""
import bpy
from src.integrations.blender.operators.skeleton_editor import (CHAR_ITEMS, _REX, _get_armature, _get_mesh, _load_var)
from src.integrations.blender.modeling.skeleton_mod import parse_mod, get_all_material_names

_CATEGORY = "Skel Editor"


class VIEW3D_PT_SkelEditorSkeleton(bpy.types.Panel):
    bl_label       = "Skeleton"
    bl_idname      = "VIEW3D_PT_ske_skeleton"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        layout.prop(scene, "ske_char_name", text="Character")

        row = layout.row(align=True)
        row.operator("ske.load_skeleton", icon="ARMATURE_DATA")
        row.operator("ske.load_mesh",     icon="MESH_DATA")
        layout.operator("ske.clear_skeleton", icon="TRASH")

        arm_obj = _get_armature(scene.ske_char_name)

        if arm_obj:
            arm = arm_obj.data
            layout.label(text=f"Bones: {len(arm.bones)}", icon="INFO")


class VIEW3D_PT_SkelEditorAnimation(bpy.types.Panel):
    bl_label       = "Animation"
    bl_idname      = "VIEW3D_PT_ske_animation"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        layout.prop(scene, "ske_anim_name", text="Animation")

        row = layout.row(align=True)
        row.operator("ske.load_animation",   icon="PLAY")
        row.operator("ske.export_animation", icon="EXPORT")

        layout.separator()
        row2 = layout.row(align=True)
        row2.operator("ske.export_skel", icon="ARMATURE_DATA")
        row2.operator("ske.export_mod",  icon="MATERIAL_DATA")

        is_playing = bpy.context.screen.is_animation_playing

        layout.operator(
            "screen.animation_play",
            text="Stop" if is_playing else "Play",
            icon="PAUSE" if is_playing else "PLAY",
            depress=is_playing,
        )

        layout.separator()
        layout.prop(scene, "ske_ar_name", text="AR Name")
        layout.operator("ske.pack_ar", icon="FILE_ARCHIVE")

        arm_obj = _get_armature(scene.ske_char_name)
        
        if arm_obj and arm_obj.animation_data and arm_obj.animation_data.action:
            action = arm_obj.animation_data.action
            fc = int(action.frame_range[1] - action.frame_range[0]) + 1
            layout.label(text=f"Action: {action.name}  ({fc} frames)", icon="ACTION")
            layout.operator("ske.debug_anim", icon="CONSOLE")


class VIEW3D_PT_SkelEditorAnimTools(bpy.types.Panel):
    bl_label       = "Anim Tools"
    bl_idname      = "VIEW3D_PT_ske_anim_tools"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── New Animation ─────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="New Animation", icon="ACTION_TWEAK")
        box.prop(scene, "ske_new_anim_name", text="Name")
        box.prop(scene, "ske_new_anim_frames", text="Frames")
        box.operator("ske.new_animation", icon="ADD")

        layout.separator()

        # ── Edit helpers ──────────────────────────────────────────────────────
        box2 = layout.box()
        box2.label(text="Edit Helpers", icon="ARMATURE_DATA")
        col = box2.column(align=True)
        col.operator("ske.bake_pose_key", icon="KEY_HLT")
        col.operator("ske.fix_loop",      icon="FILE_REFRESH")
        col.operator("ske.mirror_pose",   icon="MOD_MIRROR")

        layout.separator()
        layout.operator("ske.export_all_actions", icon="EXPORT")

        layout.separator()

        # ── Procedural generator ──────────────────────────────────────────────
        box3 = layout.box()
        box3.label(text="Generate", icon="SHADERFX")
        box3.prop(scene, "ske_gen_style",   text="Style")
        box3.prop(scene, "ske_walk_speed",  text="Speed")
        box3.operator("ske.generate_anim", icon="PLAY")


class VIEW3D_PT_SkelEditorClothing(bpy.types.Panel):
    bl_label       = "Clothing Variants"
    bl_idname      = "VIEW3D_PT_ske_clothing"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout  = self.layout
        scene   = context.scene
        char    = scene.ske_char_name
        variant = scene.ske_var_variant

        var_data = _load_var(char)
        if not var_data:
            layout.label(text="No VAR file for this character", icon="INFO")
            layout.label(text="(COP_INIT has no VAR — uses base MOD colors)")
            return

        # Variant selector — changing it auto-applies via update callback
        layout.prop(scene, "ske_var_variant", text="Variant")

        # Load MOD material names (all materials, 1:1 with VAR color indices)
        mod_path = _REX / f"{char}.MOD"
        mat_names = []

        if mod_path.exists():
            try:
                mod_data  = parse_mod(mod_path)
                mat_names = get_all_material_names(mod_data)
            except Exception:
                pass

        # Friendly label: use the part before ":" or the full name
        def _label(name):
            return name.split(":")[0].split("/")[0].title()

        colors = var_data["variants"][min(variant, var_data["count"] - 1)]
        box = layout.box()
        box.label(text=f"Variant {variant} — {var_data['count']} total:", icon="COLOR")

        for i, (r, g, b) in enumerate(colors):
            raw_name = mat_names[i] if i < len(mat_names) else f"Color {i}"
            mat      = bpy.data.materials.get(raw_name)
            col_row  = box.row(align=True)
            col_row.label(text=_label(raw_name))

            if mat and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        col_row.prop(node.inputs["Base Color"], "default_value",
                                     text="", icon_only=True)
                        break
            else:
                col_row.label(text=f"#{r:02X}{g:02X}{b:02X}")

        layout.separator()
        col = layout.column(align=True)
        row2 = col.row(align=True)
        row2.operator("ske.save_variant",         icon="COPYDOWN")
        row2.operator("ske.export_var",           icon="EXPORT")
        col.operator("ske.override_all_variants", icon="DUPLICATE")


SKELETON_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_SkelEditorSkeleton,
    VIEW3D_PT_SkelEditorAnimation,
    VIEW3D_PT_SkelEditorClothing,
    VIEW3D_PT_SkelEditorAnimTools,
]
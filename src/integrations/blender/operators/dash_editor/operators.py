"""Dash Editor — Blender operators (idname namespace: ``dash.*``)."""
import bpy
import shutil

from src.constants.folder import Folder

from src.integrations.blender.operators.dash_editor.packing import (
    export_dash_to_shop, pack_dash_ar, launch_game,
)
from src.integrations.blender.operators.dash_editor.constants import (
    _POV_CAMERA_NAME, DEFAULT_TEMPLATE_CAR, DASH_PARTS, _DASH_TAG,
)
from src.integrations.blender.operators.dash_editor.common import (
    load_dash, clear_dash, get_dash_root, get_dash_part, apply_preview,
    swap_part, reskin_part, resolve_dash_dir, resolve_mmdashview, resolve_povcamcs,
)


class DASH_OT_LoadDash(bpy.types.Operator):
    bl_idname  = "dash.load_dash"
    bl_label   = "Load Dash"
    bl_description = "Load the selected car's cockpit dash (meshes + gauges + POV camera)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        car = scene.de_dash_car
        if not car:
            self.report({"ERROR"}, "No car selected.")
            return {"CANCELLED"}

        root, msg = load_dash(scene, car)
        if root is None:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        self.report({"INFO"}, msg)
        return {"FINISHED"}


class DASH_OT_ClearDash(bpy.types.Operator):
    bl_idname  = "dash.clear_dash"
    bl_label   = "Clear"
    bl_description = "Remove the loaded dash assembly from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        clear_dash()
        self.report({"INFO"}, "Dash cleared.")
        return {"FINISHED"}


class DASH_OT_SelectPart(bpy.types.Operator):
    bl_idname  = "dash.select_part"
    bl_label   = "Select Part"
    bl_description = "Select this dash part"
    bl_options = {"REGISTER", "UNDO"}

    part_tag: bpy.props.StringProperty()

    def execute(self, context):
        obj = get_dash_part(self.part_tag)
        if obj is None:
            return {"CANCELLED"}

        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class DASH_OT_ResetPreview(bpy.types.Operator):
    bl_idname  = "dash.reset_preview"
    bl_label   = "Reset Gauges"
    bl_description = "Return the gauge needles to their rest position"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.scene.de_preview = 0.0
        apply_preview(context.scene)
        return {"FINISHED"}


class DASH_OT_LookThroughCamera(bpy.types.Operator):
    bl_idname  = "dash.look_through_camera"
    bl_label   = "Look Through Camera"
    bl_description = "Switch the viewport to the cockpit POV camera"
    bl_options = {"REGISTER"}

    def execute(self, context):
        cam = bpy.data.objects.get(_POV_CAMERA_NAME)
        if cam is None:
            self.report({"ERROR"}, "No POV camera — load a dash first.")
            return {"CANCELLED"}

        context.scene.camera = cam
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.region_3d.view_perspective = "CAMERA"
        self.report({"INFO"}, "Viewing through cockpit camera.")
        return {"FINISHED"}


class DASH_OT_ExportDash(bpy.types.Operator):
    bl_idname  = "dash.export_dash"
    bl_label   = "Export Dash"
    bl_description = "Write the dash meshes + .MMDASHVIEW + .POVCAMCS to SHOP"
    bl_options = {"REGISTER"}

    def execute(self, context):
        root = get_dash_root()
        if root is None:
            self.report({"ERROR"}, "No dash loaded.")
            return {"CANCELLED"}

        written, msgs, _ = export_dash_to_shop(context.scene)
        for m in msgs:
            print(f"[Dash Editor] {m}")
        if written == 0:
            self.report({"ERROR"}, msgs[0] if msgs else "Nothing exported.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Exported {written} dash meshes + config to SHOP.")
        return {"FINISHED"}


class DASH_OT_PackAndStartGame(bpy.types.Operator):
    bl_idname  = "dash.pack_and_start_game"
    bl_label   = "Create AR + Start Game"
    bl_description = "Export, pack the dash into its override AR, and launch the game"
    bl_options = {"REGISTER"}

    def execute(self, context):
        root = get_dash_root()
        if root is None:
            self.report({"ERROR"}, "No dash loaded.")
            return {"CANCELLED"}

        car = root["mm_car_name"]

        written, msgs, tex_names = export_dash_to_shop(context.scene)
        for m in msgs:
            print(f"[Dash Editor] {m}")
        if written == 0:
            self.report({"ERROR"}, msgs[0] if msgs else "Export failed.")
            return {"CANCELLED"}

        if not pack_dash_ar(car, tex_names):
            self.report({"ERROR"}, "AR packing failed — check the system console.")
            return {"CANCELLED"}

        ok, msg = launch_game()
        if not ok:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        self.report({"INFO"}, f"Packed {car}_DASH.ar — {msg}.")
        return {"FINISHED"}


class DASH_OT_NewDash(bpy.types.Operator):
    bl_idname  = "dash.new_dash"
    bl_label   = "New Dash From Template"
    bl_description = "Seed a custom car's dash from the template, then load it for editing"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        car = (scene.de_new_car or "").strip().upper()
        if not car:
            self.report({"ERROR"}, "Enter a car name first.")
            return {"CANCELLED"}

        src_dir = resolve_dash_dir(DEFAULT_TEMPLATE_CAR)
        if src_dir is None:
            self.report({"ERROR"}, "Template dash meshes not found.")
            return {"CANCELLED"}

        dst_dir = Folder.Shop.Meshes / f"{car}_DASH"
        dst_dir.mkdir(parents=True, exist_ok=True)
        for _, filename in DASH_PARTS:
            src = src_dir / filename
            if src.is_file():
                shutil.copy2(src, dst_dir / filename)

        Folder.Shop.Tune.mkdir(parents=True, exist_ok=True)
        mmview = resolve_mmdashview(DEFAULT_TEMPLATE_CAR)
        if mmview:
            shutil.copy2(mmview, Folder.Shop.Tune / f"{car}.MMDASHVIEW")
        pov = resolve_povcamcs(DEFAULT_TEMPLATE_CAR)
        if pov:
            shutil.copy2(pov, Folder.Shop.Tune / f"{car}_DASH.POVCAMCS")

        root, msg = load_dash(scene, car)
        if root is None:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        self.report({"INFO"}, f"New dash for {car} seeded from {DEFAULT_TEMPLATE_CAR}.")
        return {"FINISHED"}


class DASH_OT_SwapPart(bpy.types.Operator):
    bl_idname  = "dash.swap_part"
    bl_label   = "Swap Part"
    bl_description = "Replace this part's mesh with the same part from another car"
    bl_options = {"REGISTER", "UNDO"}

    part_tag: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        obj = get_dash_part(self.part_tag)
        if obj is None:
            self.report({"ERROR"}, "Part not loaded.")
            return {"CANCELLED"}

        ok, msg = swap_part(scene, obj, scene.de_swap_car)
        if not ok:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        self.report({"INFO"}, msg)
        return {"FINISHED"}


class DASH_OT_ReskinPart(bpy.types.Operator):
    bl_idname  = "dash.reskin_part"
    bl_label   = "Apply Reskin"
    bl_description = "Replace the active part's active texture with a custom DDS image"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        if obj is None or obj.get(_DASH_TAG) in (None, "root", "pov_camera"):
            self.report({"ERROR"}, "Select a dash part first.")
            return {"CANCELLED"}

        image = (scene.de_reskin_image or "").strip()
        if not image:
            self.report({"ERROR"}, "Choose a DDS image first.")
            return {"CANCELLED"}

        ok, msg = reskin_part(scene, obj, image)
        if not ok:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        self.report({"INFO"}, msg)
        return {"FINISHED"}


DASH_EDITOR_CLASSES = [
    DASH_OT_LoadDash,
    DASH_OT_ClearDash,
    DASH_OT_SelectPart,
    DASH_OT_ResetPreview,
    DASH_OT_LookThroughCamera,
    DASH_OT_SwapPart,
    DASH_OT_ReskinPart,
    DASH_OT_ExportDash,
    DASH_OT_PackAndStartGame,
    DASH_OT_NewDash,
]

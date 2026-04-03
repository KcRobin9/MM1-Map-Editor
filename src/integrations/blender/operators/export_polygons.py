import bpy
import time
import pyautogui
from typing import Set

from src.constants.constants import CURRENT_TIME_FORMATTED
from src.constants.file_formats import FileType
from src.constants.keyboard import Key
from src.constants.folder import Folder

from src.integrations.blender.export_polygons import export_formatted_polygons
from src.integrations.blender.utils import has_invalid_polygon_names

from src.misc.main import open_with_notepad_plus


import re as _re


def _popup_error(context: bpy.types.Context, title: str, lines: list) -> None:
    """Show a multi-line error popup in Blender's UI."""
    def draw(self, _ctx):
        for line in lines:
            self.layout.label(text=line)
    context.window_manager.popup_menu(draw, title=title, icon='ERROR')


def _bound_number_from_name(name: str):
    """Return the integer bound number from a polygon name like 'P67', or None."""
    m = _re.match(r"^P(\d+)$", name)
    return int(m.group(1)) if m else None


class OBJECT_OT_ExportPolygons(bpy.types.Operator):
    bl_idname = "object.export_polygons"
    bl_label = "Export Blender Polygons"

    select_all: bpy.props.BoolProperty(default = True)

    def execute(self, context: bpy.types.Context) -> Set[set]:
        export_file = Folder.Blender.Polygons / f"Polygons_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"

        # Select Mesh Objects based on the "select_all" property
        if self.select_all:
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        else:
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]

        if not mesh_objects:
            self.report({"WARNING"}, "No mesh objects found for export.")
            return {"CANCELLED"}

        if self.select_all:
            # ── Full-scene export: strict validation ──────────────────────────
            invalid = has_invalid_polygon_names(context.scene)
            if invalid:
                _popup_error(context, "Cannot Export — Invalid Names", [
                    "Some polygons have duplicate (.001-style) names:",
                    ", ".join(invalid),
                    "",
                    "Use 'Fix Poly Names' in the Map Editor panel to resolve.",
                ])
                return {"CANCELLED"}

            names_in_scene = {obj.name for obj in mesh_objects}

            if "P1" not in names_in_scene:
                _popup_error(context, "Cannot Export — P1 Missing", [
                    "No 'P1' polygon found in the scene.",
                    "Every map must have at least one polygon",
                    "with bound_number = 1 (named 'P1').",
                    "",
                    "Use 'Fix Poly Names' to assign P1 automatically.",
                ])
                return {"CANCELLED"}

            if "P200" in names_in_scene:
                _popup_error(context, "Cannot Export — P200 Reserved", [
                    "P200' is a reserved bound_number.",
                    "Rename it to a value between 1–199 or 201–32766.",
                    "",
                    "Use 'Fix Poly Names' to fix this automatically.",
                ])
                return {"CANCELLED"}

        else:
            # ── Selected export: only validate the polygons being exported ────
            for obj in mesh_objects:
                num = _bound_number_from_name(obj.name)
                if num is None:
                    _popup_error(context, "Cannot Export — Invalid Name", [
                        f"'{obj.name}' is not a valid polygon name.",
                        "Polygon names must be P followed by a number (e.g. P67).",
                    ])
                    return {"CANCELLED"}
                if num <= 0:
                    _popup_error(context, "Cannot Export — Invalid Bound Number", [
                        f"'{obj.name}' has bound_number = {num}.",
                        "Bound numbers must be greater than 0.",
                    ])
                    return {"CANCELLED"}
                if num == 200:
                    _popup_error(context, "Cannot Export — P200 Reserved", [
                        "'P200' is a reserved bound_number (CELL_TYPE_SWITCH).",
                        "Rename it to a value between 1–199 or 201–32766.",
                        "",
                        "Use 'Fix Poly Names' to fix this automatically.",
                    ])
                    return {"CANCELLED"}



        # Set the first mesh object as the active object and apply transformations (to get Global coordinates)
        context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    
        try:
            with open(export_file, "w") as f:
                for obj in mesh_objects:
                    export_script = export_formatted_polygons(obj) 
                    f.write(export_script + "\n\n")
                    
            # Open the file with Notepad++ and simulate copy to clipboard
            open_with_notepad_plus(export_file)                                
            time.sleep(1.0)  # Give Notepad++ time to load the file
            pyautogui.hotkey(Key.CTRL, Key.A)
            pyautogui.hotkey(Key.CTRL, Key.A)
            
            self.report({"INFO"}, f"Saved data to {export_file}")
            bpy.ops.object.select_all(action = "DESELECT")
            
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export polygons: {str(e)}")
            return {"CANCELLED"}
        
        return {"FINISHED"}
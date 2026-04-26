import re
import bpy
import time
import pyautogui
from pathlib import Path
from typing import Set

from src.constants.constants import CURRENT_TIME_FORMATTED
from src.constants.file_formats import FileType
from src.constants.keyboard import Key
from src.constants.folder import Folder

from src.integrations.blender.export_polygons import export_formatted_polygons
from src.integrations.blender.utils import has_invalid_polygon_names

from src.misc.main import open_with_notepad_plus


_START_MARKER        = "#! ==============================START MAP POLYGONS============================== #*"
_START_MARKER_LEGACY = "#! ==============================MAIN AREA============================== #*"
_END_MARKER          = "#! ==============================END MAP POLYGONS============================== #*"
_END_MARKER_LEGACY   = "#! ======================= CELLS ======================= !#"


def _replace_polygons_in_script(new_content: str) -> None:
    script_path: Path = Folder.BASE / "MAP_EDITOR_ALPHA_v1.py"
    text = script_path.read_text(encoding="utf-8")

    start_idx = text.find(_START_MARKER)
    if start_idx == -1:
        start_idx = text.find(_START_MARKER_LEGACY)

    end_idx = text.find(_END_MARKER)
    if end_idx == -1:
        end_idx = text.find(_END_MARKER_LEGACY)

    if start_idx == -1 or end_idx == -1:
        raise ValueError(
            f"Searched: {script_path} (exists={script_path.exists()}) | "
            f"start={'found' if start_idx != -1 else 'NOT FOUND'} | "
            f"end={'found' if end_idx != -1 else 'NOT FOUND'}"
        )

    from datetime import datetime
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    after_start = text.index("\n", start_idx) + 1  # keep the start marker line

    # Back up the existing polygon block before overwriting
    old_block = text[after_start:end_idx].strip()
    if old_block:
        backup_file = Folder.Blender.Polygons / f"MAP_EDITOR_ALPHA_v1_BACKUP_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_text(old_block, encoding="utf-8")

    new_text = text[:after_start] + f"# Last exported: {timestamp}\n\n" + new_content + "\n" + text[end_idx:]
    script_path.write_text(new_text, encoding="utf-8")


def _popup_error(context: bpy.types.Context, title: str, lines: list) -> None:
    """Show a multi-line error popup in Blender's UI."""
    def draw(self, _ctx):
        for line in lines:
            self.layout.label(text=line)
    context.window_manager.popup_menu(draw, title=title, icon='ERROR')


def _bound_number_from_name(name: str):
    m = re.match(r"^P(\d+)$", name)
    return int(m.group(1)) if m else None


class OBJECT_OT_ExportPolygons(bpy.types.Operator):
    bl_idname = "object.export_polygons"
    bl_label = "Export Blender Polygons"

    select_all: bpy.props.BoolProperty(default = True)

    @property
    def _replace_in_script(self) -> bool:
        try:
            return bpy.context.scene.replace_in_script
        except AttributeError:
            return False

    def execute(self, context: bpy.types.Context) -> Set[set]:
        export_file = Folder.Blender.Polygons / f"Polygons_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"

        # Select Mesh Objects based on the "select_all" property
        if self.select_all:
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("P")]
        else:
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH" and obj.name.startswith("P")]

        if not mesh_objects:
            self.report({"WARNING"}, "No mesh objects found for export.")
            return {"CANCELLED"}

        if self.select_all:
            invalid = has_invalid_polygon_names(context.scene)
            if invalid:
                _popup_error(context, "Cannot Export — Invalid Names", [
                    "Some polygons have duplicate (.001-style) names:",
                    ", ".join(invalid),
                    "\nUse 'Fix Poly Names' in the Map Editor panel to resolve.",
                ])
                return {"CANCELLED"}

            names_in_scene = {obj.name for obj in mesh_objects}

            if "P1" not in names_in_scene:
                _popup_error(context, "Cannot Export — P1 Missing", [
                    "No 'P1' polygon found in the scene.",
                    "Every map must have at least one polygon",
                    "with bound_number = 1 (named 'P1').\n",
                    "Use 'Fix Poly Names' to assign P1 automatically.",
                ])
                return {"CANCELLED"}

            if "P200" in names_in_scene:
                _popup_error(context, "Cannot Export — P200 Reserved", [
                    "P200' is a reserved bound_number.",
                    "Rename it to a value between 1–199 or 201–32766.\n",
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
                        "'P200' is a reserved bound_number.",
                        "Rename it to a value between 1–199 or 201–32766.\n",
                        "Use 'Fix Poly Names' to fix this automatically.",
                    ])
                    return {"CANCELLED"}


        # Set the first mesh object as the active object and apply transformations (to get Global coordinates)
        context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    
        polygon_blocks = []
        try:
            with open(export_file, "w") as f:
                for obj in mesh_objects:
                    export_script = export_formatted_polygons(obj)
                    f.write(export_script + "\n")
                    polygon_blocks.append(export_script)

            # Replace polygons inside MAP_EDITOR_ALPHA_v1.py when the toggle is on (Export All only)
            if self.select_all and self._replace_in_script:
                combined = "\n\n".join(polygon_blocks)
                try:
                    _replace_polygons_in_script(combined)
                    self.report({"INFO"}, f"Polygons replaced in MAP_EDITOR_ALPHA_v1.py and saved to {export_file}")
                except Exception as e:
                    self.report({"WARNING"}, f"Exported to file, but script replace failed: {e}")
            else:
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
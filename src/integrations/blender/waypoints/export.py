import math
import time 
import pyautogui

from src.constants.keyboard import Key
from src.constants.folder import Folder
from src.constants.file_formats import FileType
from src.constants.constants import CURRENT_TIME_FORMATTED

from src.misc.main import open_with_notepad_plus
from src.game.waypoints.constants import Rotation
from src.core.geometry.main import transform_coordinate_system
from src.integrations.blender.waypoints.helpers import get_all_waypoints


def _get_race_waypoints(export_all: bool):
    import bpy as _bpy
    objs = sorted(
        (o for o in _bpy.data.objects if o.name.startswith("WP_")),
        key=lambda o: o.name,
    )
    if export_all:
        return objs
    return [o for o in objs if o.select_get()]


def _get_cnr_sets():
    """Return sorted list of (set_num, bank_obj|None, gold_obj|None, robber_obj|None)."""
    import bpy as _bpy
    sets: dict = {}
    for obj in _bpy.data.objects:
        if not obj.name.startswith("CR_"):
            continue
        for role in ("Bank", "Gold", "Robber"):
            if role in obj.name:
                num_str = obj.name.replace(f"CR_{role}", "")
                try:
                    num = int(num_str)
                except ValueError:
                    continue
                if num not in sets:
                    sets[num] = {"Bank": None, "Gold": None, "Robber": None}
                sets[num][role] = obj
    return [(n, sets[n]["Bank"], sets[n]["Gold"], sets[n]["Robber"]) for n in sorted(sets)]


def _obj_to_line(obj, add_brackets: bool) -> str:
    vertex = obj.matrix_world.to_translation()
    vertex.x, vertex.y, vertex.z = transform_coordinate_system(vertex, blender_to_game=True)
    rotation_degrees = math.degrees(obj.rotation_euler.z) % Rotation.FULL_CIRCLE
    if rotation_degrees > Rotation.HALF_CIRCLE:
        rotation_degrees -= Rotation.FULL_CIRCLE
    line = f"{vertex.x:.2f}, {vertex.y:.2f}, {vertex.z:.2f}, {rotation_degrees:.2f}, {obj.scale.x:.2f}"
    if add_brackets:
        line = f"\t\t\t[{line}],"
    return line


_ZERO_LINE          = "0.00, 0.00, 0.00, 0.00, 0.00"
_ZERO_LINE_BRACKETS = "\t\t\t[0.00, 0.00, 0.00, 0.00, 0.00],"


def export_selected_waypoints(export_all: bool = False, add_brackets: bool = False) -> None:
    race_wps = _get_race_waypoints(export_all)
    cnr_sets = _get_cnr_sets()

    export_file = Folder.Blender.Waypoints / f"Waypoints_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"

    with open(export_file, "w") as f:
        # ── Race waypoints ────────────────────────────────────────────────────
        if race_wps:
            if not add_brackets:
                f.write("# Race waypoints: x, y, z, rotation, scale\n")
            for wp in race_wps:
                line = _obj_to_line(wp, add_brackets)
                f.write(line + "\n")
                print(line)

        # ── CnR waypoints (always in groups of 3) ────────────────────────────
        if cnr_sets:
            if not add_brackets:
                f.write("\n# CnR waypoints: Bank, Gold, Robber (per set)\n")
            for set_num, bank, gold, robber in cnr_sets:
                if not add_brackets:
                    f.write(f"# Set {set_num}\n")
                for role_name, obj in (("Bank", bank), ("Gold", gold), ("Robber", robber)):
                    if obj is not None:
                        line = _obj_to_line(obj, add_brackets)
                    else:
                        line = _ZERO_LINE_BRACKETS if add_brackets else f"# {role_name} missing — {_ZERO_LINE}"
                    f.write(line + "\n")
                    print(line)

    # Open the file with Notepad++ and simulate copy to clipboard
    open_with_notepad_plus(export_file)
    time.sleep(1.0)
    pyautogui.hotkey(Key.CTRL, Key.A)
    pyautogui.hotkey(Key.CTRL, Key.C)
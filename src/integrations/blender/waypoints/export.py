import math
import time 
import pyautogui

from src.constants.keyboard import Key
from src.constants.misc import Folder
from src.constants.file_formats import FileType
from src.constants.constants import CURRENT_TIME_FORMATTED

from src.misc.main import open_with_notepad_plus
from src.game.waypoints.constants import Rotation
from src.core.geometry.main import transform_coordinate_system
from src.integrations.blender.waypoints.helpers import get_all_waypoints


def export_selected_waypoints(export_all: bool = False, add_brackets: bool = False) -> None:
    if export_all:
        waypoints = get_all_waypoints()
    else:
        waypoints = [wp for wp in get_all_waypoints() if wp.select_get()]

    export_file = Folder.BLENDER_EXPORT_WAYPOINTS / f"Waypoints_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"

    with open(export_file, "w") as f:
        print("")
        f.write("# x, y, z, rotation, scale \n")
        
        for waypoint in waypoints:
            vertex = waypoint.matrix_world.to_translation()
            vertex.x, vertex.y, vertex.z = transform_coordinate_system(vertex, blender_to_game = True)
            
            rotation_euler = waypoint.rotation_euler
            rotation_degrees = math.degrees(rotation_euler.z) % Rotation.FULL_CIRCLE
            
            if rotation_degrees > Rotation.HALF_CIRCLE:
                rotation_degrees -= Rotation.FULL_CIRCLE
                
            wp_line = f"{vertex.x:.2f}, {vertex.y:.2f}, {vertex.z:.2f}, {rotation_degrees:.2f}, {waypoint.scale.x:.2f}"
            
            if add_brackets:
                wp_line = f"\t\t\t[{wp_line}],"

            f.write(wp_line + "\n")
            print(wp_line)
            
    # Open the file with Notepad++ and simulate copy to clipboard
    open_with_notepad_plus(export_file)                                
    time.sleep(1.0)  # Give Notepad++ time to load the file
    pyautogui.hotkey(Key.CTRL, Key.A)
    pyautogui.hotkey(Key.CTRL, Key.C)
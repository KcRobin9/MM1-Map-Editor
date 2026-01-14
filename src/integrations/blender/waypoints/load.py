import bpy
import csv
import math
from pathlib import Path
from itertools import cycle
from mathutils import Vector

from src.constants.file_formats import FileType
from src.constants.misc import Color

from src.game.races.constants import RACE_TYPE_INITIALS
from src.game.races.constants_2 import CopsAndRobbers
from src.game.waypoints.constants import Rotation, Width

from src.helpers.main import is_float

from src.integrations.blender.waypoints.helpers import update_waypoint_colors
from src.integrations.blender.waypoints.create import create_waypoint, create_gold_bar

from src.core.geometry.main import transform_coordinate_system


def get_waypoint_name(race_type: str, race_number: int, wp_idx: int) -> str:    
    return f"WP_{RACE_TYPE_INITIALS[race_type]}{race_number}_{wp_idx}"


def calculate_waypoint_rotation(x1: float, z1: float, x2: float, z2: float) -> float:
    dx = x2 - x1
    dz = z2 - z1
    rotation_rad = math.atan2(dx, dz) 
    return math.degrees(rotation_rad)


def load_waypoints_from_race_data(race_data: dict, race_type_input: str, race_number_input: int) -> None:
    race_key = f"{race_type_input}_{race_number_input}"  
    
    if race_key in race_data:
        waypoints = race_data[race_key]["waypoints"]
        
        for index, waypoint_data in enumerate(waypoints):
            x, y, z, rotation, scale = waypoint_data
            x, y, z = transform_coordinate_system(Vector((x, y, z)), game_to_blender = True)
            waypoint_name = get_waypoint_name(race_type_input, race_number_input, index)
            create_waypoint(x, y, z, rotation, scale, waypoint_name)
            
        update_waypoint_colors()
    else:
        print("Race data not found for the specified race type and number.")
        

def load_waypoints_from_csv(waypoint_file: Path) -> None:
    file_info = str(waypoint_file).replace(FileType.CSV, "").replace("WAYPOINTS", "")
    
    race_type = "".join(filter(str.isalpha, file_info))
    race_number = "".join(filter(str.isdigit, file_info))
    
    waypoints_data = []

    with open(waypoint_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if len(row) < 5:
                continue  
            
            waypoints_data.append([float(value) for value in row[:5]])

    for wp_idx, waypoint in enumerate(waypoints_data):
        x, y, z, rotation, width = waypoint
        x, y, z = transform_coordinate_system(Vector((x, y, z)), game_to_blender = True)
        waypoint_name = get_waypoint_name(race_type, race_number, wp_idx)
        
        if rotation == Rotation.AUTO and wp_idx < len(waypoints_data) - 1:
            next_waypoint = waypoints_data[wp_idx + 1]
            rotation = calculate_waypoint_rotation(x, z, next_waypoint[0], next_waypoint[2]) 

        if width == Width.AUTO:
            width = Width.DEFAULT

        waypoint = create_waypoint(x, y, z, -rotation, width, waypoint_name)
        
    update_waypoint_colors()
    
    
def load_cops_and_robbers_waypoints(input_file: Path) -> None:    
    waypoint_types = cycle([CopsAndRobbers.BANK_HIDEOUT, CopsAndRobbers.GOLD_POSITION, CopsAndRobbers.ROBBER_HIDEOUT])
    set_count = 1

    with open(input_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header 

        for row in reader:
            if len(row) < 3 or not all(is_float(val) for val in row[:3]):
                raise ValueError("\nCSV file can't be parsed. Each row must have at least 3 floats or integer values.\n")
            
            x, y, z = transform_coordinate_system(Vector(map(float, row[:3])), game_to_blender = True)                           
            waypoint_type = next(waypoint_types)

            if waypoint_type == CopsAndRobbers.BANK_HIDEOUT:
                create_waypoint(x, y, z, name = f"CR_Bank{set_count}", flag_color = Color.PURPLE)
                
            elif waypoint_type == CopsAndRobbers.GOLD_POSITION:
                create_gold_bar((x, y, z), scale = 3.0) 
                bpy.context.object.name = f"CR_Gold{set_count}"
                
            elif waypoint_type == CopsAndRobbers.ROBBER_HIDEOUT:
                create_waypoint(x, y, z, name = f"CR_Robber{set_count}", flag_color = Color.GREEN)  
                
            if waypoint_type == CopsAndRobbers.ROBBER_HIDEOUT:
                set_count += 1  # Increase the set count after completing each set of three
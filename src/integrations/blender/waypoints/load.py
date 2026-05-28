import bpy
import csv
import math
from pathlib import Path
from itertools import cycle
from mathutils import Vector

from src.helpers.main import is_float
from src.game.races.constants import RACE_TYPE_INITIALS
from src.game.races.constants_2 import CopsAndRobbers
from src.game.waypoints.constants import Rotation, Width, RACE_TYPE_SHORT
from src.core.geometry.main import transform_coordinate_system
from src.integrations.blender.waypoints.constants import FlagUV
from src.integrations.blender.waypoints.create import create_waypoint, create_gold_bar
from src.integrations.blender.waypoints.helpers import update_waypoint_colors



def get_waypoint_name(race_type: str, race_number: int, wp_idx: int) -> str:
    short = RACE_TYPE_SHORT.get(race_type.upper(), race_type.upper())
    return f"WP_{short}_{race_number}-{wp_idx}"


def calculate_waypoint_rotation(x1: float, z1: float, x2: float, z2: float) -> float:
    dx = x2 - x1
    dz = z2 - z1
    return math.degrees(math.atan2(dx, dz))


def load_waypoints_from_race_data(race_data: dict, race_type_input: str, race_number_input: int) -> None:
    race_key = f"{race_type_input}_{race_number_input}"

    if race_key not in race_data:
        print("Race data not found for the specified race type and number.")
        return

    waypoints = race_data[race_key]["player_waypoints"]

    for index, waypoint_data in enumerate(waypoints):
        x, y, z, rotation, scale = waypoint_data
        x, y, z      = transform_coordinate_system(Vector((x, y, z)), game_to_blender=True)
        waypoint_name = get_waypoint_name(race_type_input, race_number_input, index)
        create_waypoint(x, y, z, rotation, scale, waypoint_name)

    update_waypoint_colors()


def load_waypoints_from_csv(waypoint_file: Path) -> None:
    file_info    = waypoint_file.stem.replace("WAYPOINTS", "")
    race_type    = "".join(filter(str.isalpha, file_info))
    race_number  = "".join(filter(str.isdigit, file_info))
    waypoints_data = []

    with open(waypoint_file, "r") as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if len(row) < 5:
                continue
            waypoints_data.append([float(value) for value in row[:5]])

    for wp_idx, waypoint in enumerate(waypoints_data):
        x, y, z, rotation, width = waypoint
        x, y, z      = transform_coordinate_system(Vector((x, y, z)), game_to_blender=True)
        waypoint_name = get_waypoint_name(race_type, race_number, wp_idx)

        if rotation == Rotation.AUTO and wp_idx < len(waypoints_data) - 1:
            next_wp  = waypoints_data[wp_idx + 1]
            rotation = calculate_waypoint_rotation(x, z, next_wp[0], next_wp[2])

        if width == Width.AUTO:
            width = Width.DEFAULT

        create_waypoint(x, y, z, -rotation, width, waypoint_name)

    update_waypoint_colors()


def load_cops_and_robbers_waypoints(input_file: Path) -> None:
    waypoint_types = cycle([CopsAndRobbers.BANK_HIDEOUT, CopsAndRobbers.GOLD_POSITION, CopsAndRobbers.ROBBER_HIDEOUT])
    set_count = 1

    with open(input_file, "r") as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if len(row) < 3 or not all(is_float(val) for val in row[:3]):
                raise ValueError("\nCSV file can't be parsed. Each row must have at least 3 floats or integer values.\n")

            x, y, z       = transform_coordinate_system(Vector(map(float, row[:3])), game_to_blender=True)
            waypoint_type  = next(waypoint_types)

            if waypoint_type == CopsAndRobbers.BANK_HIDEOUT:
                create_waypoint(x, y, z, name=f"CR_Bank{set_count}",   flag_type=FlagUV.BANK)

            elif waypoint_type == CopsAndRobbers.GOLD_POSITION:
                create_gold_bar((x, y, z), scale=3.0)
                bpy.context.object.name = f"CR_Gold{set_count}"

            elif waypoint_type == CopsAndRobbers.ROBBER_HIDEOUT:
                create_waypoint(x, y, z, name=f"CR_Robber{set_count}", flag_type=FlagUV.HIDEOUT)

            if waypoint_type == CopsAndRobbers.ROBBER_HIDEOUT:
                set_count += 1
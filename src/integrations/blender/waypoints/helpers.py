import bpy 
from typing import List

from constants.misc import Color


def get_all_waypoints() -> List[bpy.types.Object]:
    return [obj for obj in bpy.data.objects if obj.name.startswith("WP_")]


def update_waypoint_colors() -> None:
    waypoints = get_all_waypoints()

    if not waypoints:
        return

    waypoints[0].data.materials[0].diffuse_color = Color.WHITE      # First Waypoint
    waypoints[-1].data.materials[0].diffuse_color = Color.GREEN     # Last Waypoint

    for waypoint in waypoints[1:-1]:
        waypoint.data.materials[0].diffuse_color = Color.BLUE       # Intermediate Waypoints
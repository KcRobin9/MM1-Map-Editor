import bpy
import math
from mathutils import Vector
from typing import Optional, Tuple

from src.constants.misc import Color
from src.game.waypoints.constants import Rotation, Width

from src.integrations.blender.waypoints.helpers import update_waypoint_colors
from src.integrations.blender.waypoints.constants import POLE_HEIGHT, POLE_DIAMETER, FLAG_HEIGHT, FLAG_HEIGHT_OFFSET  


def create_waypoint_material(name: str, color: str) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = Color.to_rgba(color)
    return material


def create_waypoint_pole(height: float, diameter: float, location: Tuple[float, float, float],
                         color: Tuple[float, float, float, float]) -> bpy.types.Object:
    
    bpy.ops.mesh.primitive_cylinder_add(radius = diameter / 2, depth = height, location = location)
    pole = bpy.context.object
    pole_material = create_waypoint_material("PoleMaterial", color) 
    pole.data.materials.append(pole_material)
    return pole


def create_waypoint_flag(width: float, height: float, cursor_z: float, flag_height_offset: float, 
                         location: Tuple[float, float, float], 
                         color: Tuple[float, float, float, float]) -> bpy.types.Object:
    
    bpy.ops.mesh.primitive_plane_add(size = 1, location = location)
    flag = bpy.context.object
    flag.scale.x = width 
    flag.scale.y = height 
    flag.rotation_euler.x = math.pi / 2  # Rotate 90 degrees around x-axis
    flag.location.z = cursor_z + flag_height_offset + height / 2 
    
    flag_material = create_waypoint_material("FlagMaterial", color)
    flag.data.materials.append(flag_material)
    
    return flag


def create_gold_bar(location: Tuple[float, float, float], scale: float = 1.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size = 1, location = location)
    gold = bpy.context.object
    gold.scale *= scale  
    
    gold_material = create_waypoint_material("GoldMaterial", Color.YELLOW)  
    gold.data.materials.append(gold_material)
    gold.name = "Gold_Default"
    
    return gold

  
def create_waypoint(x: Optional[float] = None, y: Optional[float] = None, z: Optional[float] = None, 
                    rotation: float = Rotation.NORTH, width: float = Width.DEFAULT, name: Optional[str] = None, 
                    flag_color: Tuple[float, float, float, float] = Color.BLUE) -> bpy.types.Object:                
    
    if x is None or y is None or z is None:  # If (x, y, z) is NOT provided, use the current cursor position
        cursor_location = bpy.context.scene.cursor.location.copy()
    else:
        cursor_location = Vector((x, y, z))  # If (x, y, z) ARE provided, create a new location vector
  
    pole_one_location = (cursor_location.x - width / 2, cursor_location.y, cursor_location.z + POLE_HEIGHT / 2)
    pole_two_location = (cursor_location.x + width / 2, cursor_location.y, cursor_location.z + POLE_HEIGHT / 2)
    
    pole_one = create_waypoint_pole(POLE_HEIGHT, POLE_DIAMETER, pole_one_location, Color.WHITE) 
    pole_two = create_waypoint_pole(POLE_HEIGHT, POLE_DIAMETER, pole_two_location, Color.WHITE) 

    flag = create_waypoint_flag(width, FLAG_HEIGHT, cursor_location.z, FLAG_HEIGHT_OFFSET, cursor_location, flag_color)

    # Select and join the pole and flag objects
    bpy.ops.object.select_all(action = "DESELECT")
    pole_one.select_set(True)
    pole_two.select_set(True)
    flag.select_set(True)
    bpy.context.view_layer.objects.active = flag
    bpy.ops.object.join()

    waypoint = bpy.context.object    
    waypoint.rotation_euler.z = math.radians(rotation)
    waypoint.name = name if name else "WP_Default"
    
    # Set the origin to the midpoint of the poles
    midpoint = ((pole_one_location[0] + pole_two_location[0]) / 2, 
                (pole_one_location[1] + pole_two_location[1]) / 2, 
                cursor_location.z)
    
    bpy.context.scene.cursor.location = midpoint
    bpy.ops.object.origin_set(type = "ORIGIN_CURSOR")

    # Reset the cursor location if coordinates were not provided
    if x is None or y is None or z is None:
        bpy.context.scene.cursor.location = cursor_location
        
    update_waypoint_colors() 

    return waypoint
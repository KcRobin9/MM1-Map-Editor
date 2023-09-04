
    #! =====================================================================
    #! ================= Midtown Madness 1 Map Editor Alpha ================
    #? 
    #? This Map Editor allows users to create new maps for Midtown Madness 1
    #                                           Copyright (C) May 2023 Robin
    #? 
    #? This program is free software: you can redistribute it and/or modify
    #? it under the terms of the GNU General Public License as published by
    #? the Free Software Foundation, either version 3 of the License, or
    #? (at your option) any later version.
    #? 
    #? This program is distributed in the hope that it will be useful, but
    #? WITHOUT ANY WARRANTY; without even the implied warranty of
    #? MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
    #? General Public License for more details.
    #? 
    #? For more information about GNU see <http://www.gnu.org/licenses/>.
    #! =====================================================================
    #! =====================================================================


import os
import re
import csv
import bpy
import math
import struct
import shutil
import random
import textwrap
import subprocess
import numpy as np
import matplotlib.pyplot as plt                 
import matplotlib.transforms as mtransforms
from pathlib import Path  
from typing import List, Dict, Union, Tuple, Optional, BinaryIO


#! SETUP I (Names and directory)                Control + F    "city=="  to jump to The City Creation section
city_name = "USER"                              # One word (no spaces)  --- name of the .ar file
race_locale_name = "My First City"              # Can be multiple words --- name of the city in the Race Locale Menu
mm1_folder = r"C:\Users\robin\Desktop\MM1_game" # Path to your MM1 folder (Open1560 is automatically copied to this folder)


#* SETUP II (Map Creation)
play_game = True                # start the game immediately after the Map is created
delete_shop = True              # delete the raw city files after the .ar file has been created

set_facade = True               # change to "True" if you want FACADES
set_props = True                # change to "True" if you want PROPS

set_anim = True                 # change to "True" if you want ANIM (plane and eltrain)
set_bridges = False             # change to "True" if you want BRIDGES // (unfinished)

ai_map = True                   # change both to "True" if you want AI paths // (do not change this to "False")
ai_streets = True               # change both to "True" if you want AI paths // (do not change this to "False")

random_textures =               ["T_WATER", "T_GRASS", "T_WOOD", "T_WALL", "R4", "R6", "OT_BAR_BRICK", "FXLTGLOW"]
randomize_textures = False      # change to "True" if you want to randomize all textures in your Map

# Debug
debug_bounds = False            # change to "True" if you want a BND Debug text file
debug_props = False             # change to "True" if you want a BNG Debug text file
debug_facades = False           # change to "True" if you want a FCD Debug text file
DEBUG_BMS = False               # change to "True" if you want BMS Debug text files (in directory "_Debug_BMS")

# HUD
shape_outline_color = None      # change to any other color (e.g. 'Red'), if you don't want any color, set to 'None'         
debug_hud = False               # change to "True" if you want a HUD Debug jpg file
debug_hud_bound_id = True       # change to "True" if you want to see the Bound ID in the HUD Debug jpg file

# Blender
# textures_directory = r"C:\Users\robin\Desktop\Blender_Script\DDS" // (under construction)  

#* SETUP III (optional, Race Editor)
# Weather and Time constants
MORNING, NOON, EVENING, NIGHT = 0, 1, 2, 3  
CLEAR, CLOUDY, RAIN, SNOW = 0, 1, 2, 3      

# AI Cop behavior constants
FOLLOW, ROADBLOCK, SPINOUT, PUSH, MIX = 0, 3, 4, 8, 15      

# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints, the number of waypoints for Circuits and Checkpoints is unlimited
# Waypoint Structure: (x, y, z, rotation, width)

# Race names
blitz_race_names = ["Dading's Blitz", "Target Car 2024"]
circuit_race_names = ["Tigerhawk's Brb"]
checkpoint_race_names = ["Giga's Scream"]

# Blitzes
blz_0 = [
    [0.0, 0.0, 0.1, 5.0, 15.0], # your notes here
    [0.0, 0.0, -20, 5.0, 15.0], # your notes here
    [0.0, 0.0, -40, 5.0, 15.0],
    [0.0, 0.0, -60, 5.0, 15.0],
    [0.0, 0.0, -80, 5.0, 15.0],
    [0.0, 0.0, -99, 5.0, 15.0], 
    [MORNING, CLEAR, 0, 0, 0, 99999, NIGHT, SNOW, 1, 1, 1, 99999]] 
    #* time, weather, cops, ambient, peds, timelimit (Amateur first, Pro second)    

blz_1 = [
    [0.0, 0.0, 0.1, 5.0, 15.0],
    [0.0, 0.0, -20, 5.0, 15.0],
    [0.0, 0.0, -40, 5.0, 15.0],
    [MORNING, CLOUDY, 0, 0, 0, 2024, EVENING, RAIN, 1, 1, 1, 2024]]

# Circuits
cir_0 = [
    [20.0, 0.0, 0.0, 180.0, 8.0],
    [0.0, 0.0, 50.0, 90, 8.0],
    [50.0, 0.0, 0.0, 0.01, 8.0],
    [0.0, 0.0, -75.0, -90, 8.0],
    [NOON, CLEAR, 3, 0, 0, 0, EVENING, SNOW, 3, 0, 0, 0]] 
    #* time, weather, number of laps, cops, ambient, peds (Amateur first, Pro second) 

# Checkpoints   
race_0 = [
    [0.0, 0.0, 0.0, 0.0, 15.0],
    [0.0, 0.0, 50.0, 0.0, 15.0],  
    [MORNING, RAIN, 0, 0, 0, NIGHT, SNOW, 0, 0, 0]] 
    #* time, weather, cops, ambient, peds (Amateur first, Pro second) 

# Packing all the race configurations
blitz_races = [blz_0, blz_1]
circuit_races = [cir_0]
checkpoint_races = [race_0]


#* SETUP IV (optional, Cops and Robbers)
cnr_waypoints = [                          # set Cops and Robbers Waypoints manually and concisely
    ## 1st set, Name: ... ## 
    (20.0,1.0,80.0),                       #? Bank / Blue Team Hideout
    (80.0,1.0,20.0),                       #? Gold
    (20.0,1.0,80.0),                       #? Robber / Red Team Hideout
    ## 2nd set, Name: ... ## 
    (-90.0,1.0,-90.0),
    (90.0,1.0,90.0),
    (-90.0,1.0,-90.0)]


#* SETUP V (optional, Animations)
anim_data = {
    'plane': [                  # you can only use "plane" and "eltrain", other objects won't work
        (450, 30.0, -450),      # you can only have one Plane and/or one Eltrain
        (450, 30.0, 450),       # you can set any number of coordinates for your path(s)
        (-450, 30.0, -450),     
        (-450, 30.0, 450)], 
    'eltrain': [
        (180, 25.0, -180),
        (180, 25.0, 180), 
        (-180, 25.0, -180),
        (-180, 25.0, 180)]}


#* SETUP VI (optional, Bridges, unfinished)
bridge_slim = "tpdrawbridge04"      #* dimension: x: 30.0 y: 5.9 z: 32.5
bridge_wide = "tpdrawbridge06"      #* dimension: x: 40.0 y: 5.9 z: 32.5
bridge_crossgate = "tpcrossgate06"
bridge_object = "vpmustang99"       # you can pass any object

# Structure: (x,y,z, orientation, bridge_number, bridge_object)
bridges = [
    ((-30.0, 5.0, 50.0), "V", 2, bridge_slim)] 

# Possible orientations
f"""Please choose from 'V', 'V.F', 'H.E', 'H.W', 'N.E', 'N.W', 'S.E', or 'S.W'."
    Where 'V' is vertical, 'H' is horizontal, 'F' is flipped, and e.g. 'N.E' is (diagonal) North East."""

# AIMAP Race data (currently applies to all races, will customizable per race in future versions)
aimap_ambient_density = 0.5
aimap_num_opponents = 8 
aimap_opponent_car = "vppanozgt" 
aimap_cop_car = "vpcop"
aimap_cop_data = "-30.1 0.0 30.0 0.0 2 0"

################################################################################################################               
################################################################################################################     
 
def to_do_list(x):
            """
            ! FIX:
            BRIDGE --> setting bridges currently crashes the game
            BAI --> path setting works, but AI (cops, traffic, peds, etc) still do not spawn/drive/work
            
            TEXTURES --> replacing textures with edited vanilla textures works, but adding new textures crashes the game
            TEXTURES --> fix wall textures not appearing in game (FIX -> add +0.01 or -0.01 to one of the x or z coordinates)
            
            ? ADD SHORT-TERM:
            SHAPES --> implement "double_wall" (i.e. duplicating the polygon with both "wall sides") & improve general wall setting
            
            FCD --> test and document flag behavior
            FCD --> test and document Sides and Scales behavior
            FCD --> screenshot each vanilla facade for user reference
            FCD --> implement diagonal facades
            
            SCRIPT --> update Installation Instructions (e.g. guide for VS Code and Blender interaction)
                                
            ? ADD LONG-TERM:
            SHAPES --> triangles with slopes currently causes issues
            
            PROPS --> investigate breakable parts in (see {}.MMBANGERDATA)
            PROPS --> investigate creating custom texturized props from scatch
            
            RACES --> customize AIMAP data for each race 
            
            TEXTURES --> will other textures also "drift" if they contain the string "T_WATER{}"?
            TEXTURES --> evaluate 'rotating_repeating' and 'custom'
                       
            HUDMAP --> correctly align the HUD map in the game

            OPEN1560 --> add custom updated Open1560
            """               
            
################################################################################################################               
################################################################################################################        

# Simplify Struct usage
def read_unpack(file, fmt):
    return struct.unpack(fmt, file.read(struct.calcsize(fmt)))

def write_pack(file, fmt, *args):
    file.write(struct.pack(fmt, *args))


# VECTOR2 CLASS
class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def read(file):
        return Vector2(*read_unpack(file, '<2f'))

    def readn(file, count):
        return [Vector2.read(file) for _ in range(count)]

    def write(self, file):
        write_pack(file, '<2f', self.x, self.y)

    def __repr__(self):
        return '{{{:f},{:f}}}'.format(self.x, self.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vector2(self.x / other, self.y / other)

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def tuple(self):
        return (self.x, self.y)

    def Cross(self, rhs=None):
        if rhs is None:
            return Vector2(self.y, -self.x)

        return (self.x*rhs.y) - (self.y*rhs.x)

    def Dot(self, rhs):
        return (self.x * rhs.x) + (self.y * rhs.y)

    def Mag2(self):
        return (self.x * self.x) + (self.y * self.y)

    def Normalize(self):
        return self * (self.Mag2() ** -0.5)

    def Dist2(self, other):
        return (other - self).Mag2()

    def Dist(self, other):
        return self.Dist2(other) ** 0.5
    
    
# VECTOR3 CLASS
class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self._data = {"x": x, "y": y, "z": z}
        
    def read(file):
        return Vector3(*read_unpack(file, '<3f'))

    def readn(file, count):
        return [Vector3.read(file) for _ in range(count)]

    def write(self, file):
        write_pack(file, '<3f', self.x, self.y, self.z)
        
    def to_bytes(self):
        return struct.pack('<3f', self.x, self.y, self.z)
    
    def copy(self):
        return Vector3(self.x, self.y, self.z)
    
    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if key in self._data:
            self._data[key] = value
            setattr(self, key, value)
        else:
            raise ValueError("Invalid key: {}. Use 'x', 'y', or 'z'.".format(key))
        
    def __repr__(self, round_values = True):
        if round_values:
            return '{{{:.2f},{:.2f},{:.2f}}}'.format(round(self.x, 2), round(self.y, 2), round(self.z, 2))
        else:
            return '{{{:f},{:f},{:f}}}'.format(self.x, self.y, self.z)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return Vector3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        return Vector3(self.x / other, self.y / other, self.z / other)

    def __eq__(self, other):
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def tuple(self):
        return (self.x, self.y, self.z)

    def Cross(self, rhs):
        return Vector3(self.y * rhs.z - self.z * rhs.y, self.z * rhs.x - self.x * rhs.z, self.x * rhs.y - self.y * rhs.x)

    def Dot(self, rhs):
        return (self.x * rhs.x) + (self.y * rhs.y) + (self.z * rhs.z)

    def Mag2(self):
        return (self.x * self.x) + (self.y * self.y) + (self.z * self.z)

    def Normalize(self):
        return self * (self.Mag2() ** -0.5)

    def Dist2(self, other):
        return (other - self).Mag2()

    def Dist(self, other):
        return self.Dist2(other) ** 0.5
    
    def Negate(self):
        return Vector3(-self.x, -self.y, -self.z)

    def Set(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
       
       
# Calculate BND center, min, max, radius, radius squared    
def calculate_max(vertices: List[Vector3]):
    max_ = Vector3(vertices[0].x, vertices[0].y, vertices[0].z)
    for vertex in vertices:
        max_.x = max(max_.x, vertex.x)
        max_.y = max(max_.y, vertex.y)
        max_.z = max(max_.z, vertex.z)
    return max_

def calculate_min(vertices: List[Vector3]):
    min_ = Vector3(vertices[0].x, vertices[0].y, vertices[0].z)
    for vertex in vertices:
        min_.x = min(min_.x, vertex.x)
        min_.y = min(min_.y, vertex.y)
        min_.z = min(min_.z, vertex.z)
    return min_

def calculate_center(vertices: List[Vector3]):
    center = Vector3(0, 0, 0)
    for vertex in vertices:
        center.x += vertex.x
        center.y += vertex.y
        center.z += vertex.z
    center.x /= len(vertices)
    center.y /= len(vertices)
    center.z /= len(vertices)
    return center

def calculate_center_tuples(vertices: List[Tuple[float, float, float]]):
    center = [0, 0, 0]
    for vertex in vertices:
        center[0] += vertex[0]
        center[1] += vertex[1]
        center[2] += vertex[2]
    center[0] /= len(vertices)
    center[1] /= len(vertices)
    center[2] /= len(vertices)
    return center

def calculate_radius(vertices: List[Vector3], center: Vector3):
    radius_sqr = 0
    for vertex in vertices:
        diff = Vector3(vertex.x - center.x, vertex.y - center.y, vertex.z - center.z)
        radius_sqr = max(radius_sqr, diff.x ** 2 + diff.y ** 2 + diff.z ** 2)
    return radius_sqr ** 0.5


# POLYGON CLASS
class Polygon:
    def __init__(self, cell_id: int, mtl_index: int, flags: int, vert_indices: List[int],
                 plane_edges: List[Vector3], plane_n: Vector3, plane_d: float, cell_type: int = 0) -> None:
        self.cell_id = cell_id
        self.mtl_index = mtl_index
        self.flags = flags
        self.vert_indices = vert_indices
        self.plane_edges = plane_edges
        self.plane_n = plane_n
        
        if isinstance(plane_d, list) and len(plane_d) == 1:
            plane_d = plane_d[0]
        elif isinstance(plane_d, np.float64):
            plane_d = float(plane_d)
            
        self.plane_d = plane_d
        self.cell_type = cell_type
        
    @property
    def is_quad(self) -> bool:
        return bool(self.flags & 4)

    @property
    def num_verts(self) -> int:
        return 4 if self.is_quad else 3
          
    @classmethod
    def read(cls, f: BinaryIO) -> 'Polygon':
        cell_id, mtl_index, flags, *vert_indices = read_unpack(f, '<HBB4H')
        plane_edges = [Vector3.read(f) for _ in range(4)]
        plane_n = Vector3.read(f)
        plane_d = read_unpack(f, '<f')
        return cls(cell_id, mtl_index, flags, vert_indices, plane_edges, plane_n, plane_d)
            
    def to_file(self, f: BinaryIO) -> None:
        
        # Each polygon (here triangles), still require four vertex indices
        if len(self.vert_indices) < 4: 
            self.vert_indices += (0,) * (4 - len(self.vert_indices))
        
        write_pack(f, '<HBB4H', self.cell_id, self.mtl_index, self.flags, *self.vert_indices)

        for edge in self.plane_edges:
            edge.write(f)
            
        self.plane_n.write(f)
        write_pack(f, '<f', self.plane_d)
   
    def __repr__(self, bnd_instance, round_values = True):
        vertices_coordinates = [bnd_instance.vertices[index] for index in self.vert_indices]
        plane_d_str = f'{round(self.plane_d, 2):.2f}' if round_values else f'{self.plane_d:f}'
        
        return (
            f"Polygon\n"
            f"Bound Number: {self.cell_id}\n"
            f"Material Index: {self.mtl_index}\n"
            f"Flags: {self.flags}\n"
            f"Vertices Indices: {self.vert_indices}\n"
            f"Vertices Coordinates: {vertices_coordinates}\n"
            f"Plane Edges: {self.plane_edges}\n"
            f"Plane N: {self.plane_n}\n"
            f"Plane D: [{plane_d_str}]\n"
        )
        
        
# BND CLASS
class BND:
    def __init__(self, magic: str, offset: Vector3, x_dim: int, y_dim: int, z_dim: int, 
                 center: Vector3, radius: float, radius_sqr: float, bb_min: Vector3, bb_max: Vector3, 
                 num_verts: int, num_polys: int, num_hot_verts1: int, num_hot_verts2: int, num_edges: int, 
                 x_scale: float, z_scale: float, num_indices: int, height_scale: float, cache_size: int, 
                 vertices: List[Vector3], polys: List[Polygon],
                 hot_verts: List[Vector3], edges_0: List[int], edges_1: List[int], 
                 edge_normals: List[Vector3], edge_floats: List[float],
                 row_offsets: Optional[List[int]], row_shorts: Optional[List[int]], 
                 row_indices: Optional[List[int]], row_heights: Optional[List[int]]) -> None:
        self.magic = magic
        self.offset = offset    
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.z_dim = z_dim
        self.center = center    
        self.radius = radius
        self.radius_sqr = radius_sqr
        self.bb_min = bb_min         
        self.bb_max = bb_max        
        self.num_verts = num_verts
        self.num_polys = num_polys
        self.num_hot_verts1 = num_hot_verts1
        self.num_hot_verts2 = num_hot_verts2
        self.num_edges = num_edges
        self.x_scale = x_scale
        self.z_scale = z_scale
        self.num_indices = num_indices
        self.height_scale = height_scale
        self.cache_size = cache_size
        
        self.vertices = vertices              
        self.polys = polys   
        
        self.hot_verts = hot_verts
        self.edges_0 = edges_0
        self.edges_1 = edges_1
        self.edge_normals = edge_normals
        self.edge_floats = edge_floats
        self.row_offsets = row_offsets
        self.row_shorts = row_shorts
        self.row_indices = row_indices
        self.row_heights = row_heights
                  
    @classmethod
    def read_bnd(cls, f: BinaryIO) -> 'BND':        
        magic = read_unpack(f, '<4s')[0]
        offset = Vector3.read(f)
        x_dim, y_dim, z_dim = read_unpack(f, '<3l')
        center = Vector3.read(f)
        radius, radius_sqr = read_unpack(f, '<2f')
        bb_min = Vector3.read(f)
        bb_max = Vector3.read(f)
        num_verts, num_polys, num_hot_verts1, num_hot_verts2, num_edges = read_unpack(f, '<5l')
        x_scale, z_scale, num_indices, height_scale, cache_size = read_unpack(f, '<2f3l')
        vertices = [Vector3.read(f) for _ in range(num_verts)]
        polys = [Polygon.read(f) for _ in range(num_polys + 1)] 
        
        hot_verts = Vector3.readn(f, num_hot_verts2)
        edges_0 = read_unpack(f, '<{}I'.format(num_edges))
        edges_1 = read_unpack(f, '<{}I'.format(num_edges))
        edge_normals = Vector3.readn(f, num_edges)
        edge_floats = read_unpack(f, '<{}f'.format(num_edges))
        
        row_offsets = None
        row_shorts = None
        row_indices = None
        row_heights = None

        if x_dim and y_dim:
            row_offsets = read_unpack(f, '<{}I'.format(z_dim))
            row_shorts = read_unpack(f, '<{}H'.format(x_dim * z_dim))
            row_indices = read_unpack(f, '<{}H'.format(num_indices))
            row_heights = read_unpack(f, '<{}B'.format(x_dim * x_dim))

        return cls(magic, offset, x_dim, y_dim, z_dim, center, radius, radius_sqr, bb_min, bb_max, 
                   num_verts, num_polys, num_hot_verts1, num_hot_verts2, num_edges, 
                   x_scale, z_scale, num_indices, height_scale, cache_size, vertices, polys,
                   hot_verts, edges_0, edges_1, edge_normals, edge_floats,
                   row_offsets, row_shorts, row_indices, row_heights)
    
    def write_bnd(self, f: BinaryIO) -> None:
        write_pack(f, '<4s', self.magic)
        self.offset.write(f)         
        write_pack(f, '<3l', self.x_dim, self.y_dim, self.z_dim)
        self.center.write(f) 
        write_pack(f, '<2f', self.radius, self.radius_sqr)
        self.bb_min.write(f)
        self.bb_max.write(f)
        write_pack(f, '<5l', self.num_verts, self.num_polys, self.num_hot_verts1, self.num_hot_verts2, self.num_edges)
        write_pack(f, '<2f', self.x_scale, self.z_scale)
        write_pack(f, '<3l', self.num_indices, self.height_scale, self.cache_size)
 
        for vertex in self.vertices:       
            vertex.write(f)   
        
        for poly in self.polys:           
            poly.to_file(f)              
                
    def write_bnd_debug(self, file_name: str, debug_bounds: bool) -> None:
        if debug_bounds:
            with open(file_name, 'w') as f:
                f.write(str(self))
                
    def __repr__(self) -> str:
        polys_representation = '\n'.join([poly.__repr__(self) for poly in self.polys])
        return (
            f"BND\n"
            f"Magic: 2DNB\n"
            f"Offset: {self.offset}\n"
            f"XDim: {self.x_dim}\n"
            f"YDim: {self.y_dim}\n"
            f"ZDim: {self.z_dim}\n"
            f"Center: {self.center}\n"
            f"Radius: {self.radius:.2f}\n" 
            f"Radius_sqr: {self.radius_sqr:.2f}\n"  
            f"BBMin: {self.bb_min}\n"
            f"BBMax: {self.bb_max}\n"
            f"Num Verts: {self.num_verts}\n"
            f"Num Polys: {self.num_polys}\n"
            f"Num Hot Verts1: {self.num_hot_verts1}\n"
            f"Num Hot Verts2: {self.num_hot_verts2}\n"
            f"Num Edges: {self.num_edges}\n"
            f"XScale: {self.x_scale}\n"
            f"ZScale: {self.z_scale}\n"
            f"Num Indices: {self.num_indices}\n"
            f"Height Scale: {self.height_scale}\n"
            f"Cache Size: {self.cache_size}\n\n"
            f"Vertices:\n{self.vertices}\n\n"
            f"======= Polys =======\n\n{polys_representation}\n"
        )


# BMS CLASS
class BMS:
    def __init__(self, magic: str, vertex_count: int, adjunct_count: int, surface_count: int, indices_count: int,
                 radius: float, radius_sq: float, bounding_box_radius: float,
                 texture_count: int, flags: int, string_name: List[str], coordinates: List[Vector3],
                 texture_darkness: List[int], tex_coords: List[float], enclosed_shape: List[int],
                 surface_sides: List[int], indices_sides: List[List[int]]) -> None:

        self.magic = magic
        self.vertex_count = vertex_count
        self.adjunct_count = adjunct_count
        self.surface_count = surface_count
        self.indices_count = indices_count
        self.radius = radius
        self.radius_sq = radius_sq
        self.bounding_box_radius = bounding_box_radius
        self.texture_count = texture_count
        self.flags = flags
        self.string_name = string_name
        self.coordinates = coordinates
        self.texture_darkness = texture_darkness
        self.tex_coords = tex_coords  
        self.enclosed_shape = enclosed_shape  
        self.surface_sides = surface_sides
        self.indices_sides = indices_sides
        
    @classmethod
    def read_bms(cls, file_name: str):
        with open(file_name, 'rb') as f:
            magic = read_unpack(f, '16s')[0].decode('utf-8').rstrip('\x00')            
            vertex_count, adjunct_count, surface_count, indices_count = read_unpack(f, '4I')
            radius, radius_sq, bounding_box_radius = read_unpack(f, '3f')
            texture_count, flags = read_unpack(f, 'bb')
            
            f.read(6)  
            string_name = read_unpack(f, '32s')[0].decode('utf-8').rstrip('\x00')
            f.read(16) 

            coordinates = []
            for _ in range(vertex_count):
                x, y, z = read_unpack(f, '3f')
                coordinates.append(Vector3(x, y, z))

            texture_darkness = list(read_unpack(f, str(adjunct_count) + 'b'))
            tex_coords = list(read_unpack(f, str(adjunct_count * 2) + 'f'))
            enclosed_shape = list(read_unpack(f, str(adjunct_count) + 'H'))
            surface_sides = list(read_unpack(f, str(surface_count) + 'b'))

            indices_sides = []
            for _ in range(surface_count):
                indices_side = list(read_unpack(f, str(indices_count) + 'H'))
                indices_sides.append(indices_side)

        return cls(magic, vertex_count, adjunct_count, surface_count, indices_count, 
                   radius, radius_sq, bounding_box_radius, 
                   texture_count, flags, string_name, coordinates, 
                   texture_darkness, tex_coords, enclosed_shape, surface_sides, indices_sides)
        
    def write_bms(self, file_name: str) -> None:
        with open(file_name, 'wb') as f:
            write_pack(f, '16s', self.magic.encode('utf-8').ljust(16, b'\x00'))
            write_pack(f, '4I', self.vertex_count, self.adjunct_count, self.surface_count, self.indices_count)
            write_pack(f, '3f', self.radius, self.radius_sq, self.bounding_box_radius)
            write_pack(f, 'bb', self.texture_count, self.flags)
            f.write(b'\x00' * 6) 

            for name in self.string_name:
                write_pack(f, '32s', name.encode('utf-8').ljust(32, b'\x00'))
                f.write(b'\x00' * (4 * 4))

            for coordinate in self.coordinates:
                write_pack(f, '3f', coordinate.x, coordinate.y, coordinate.z)

            write_pack(f, str(self.adjunct_count) + 'b', *self.texture_darkness)
                        
            # Temporary hack, ensuring tex_coords is not longer than adjunct_count * 2
            if len(self.tex_coords) > self.adjunct_count * 2:
                self.tex_coords = self.tex_coords[:self.adjunct_count * 2] 
                
            write_pack(f, str(self.adjunct_count * 2) + 'f', *self.tex_coords)            
            write_pack(f, str(self.adjunct_count) + 'H', *self.enclosed_shape)
            write_pack(f, str(self.surface_count) + 'b', *self.surface_sides)

            # Even with three vertices, we still require four indices (indices_sides: [[0, 1, 2, 0]])
            for indices_side in self.indices_sides:
                while len(indices_side) < 4:
                    indices_side.append(0)
                write_pack(f, str(len(indices_side)) + 'H', *indices_side)
                                    
    def write_bms_debug(self, file_name: str, debug_dir = "_Debug_BMS") -> None:
        Path(debug_dir).mkdir(parents = True, exist_ok = True)

        if DEBUG_BMS:
            with open(debug_dir / Path(file_name), 'w') as f:
                f.write(str(self))
                
    def __repr__(self):
        return f'''
BMS
Magic: {self.magic}
VertexCount: {self.vertex_count}
AdjunctCount: {self.adjunct_count}
SurfaceCount: {self.surface_count}
IndicesCount: {self.indices_count}
Radius: {self.radius}
Radiussq: {self.radius_sq}
BoundingBoxRadius: {self.bounding_box_radius}
TextureCount: {self.texture_count}
Flags: {self.flags}
StringName: {self.string_name}
Coordinates: {self.coordinates}
TextureDarkness: {self.texture_darkness}
TexCoords: {self.tex_coords}
Enclosed_shape: {self.enclosed_shape}
SurfaceSides: {self.surface_sides}
IndicesSides: {self.indices_sides}
        '''


################################################################################################################               
################################################################################################################       

# SCRIPT CONSTANTS
BASE_DIR = Path.cwd()
SHOP = BASE_DIR / 'SHOP'
SHOP_CITY = SHOP / 'CITY'
MOVE = shutil.move

# INITIALIZATIONS | do not change
vertices = []
hudmap_vertices = []
hudmap_properties = {}
polygons_data = []
stored_texture_names = []
poly_filler = Polygon(0, 0, 0, [0, 0, 0, 0], [Vector3(0, 0, 0) for _ in range(4)], Vector3(0, 0, 0), [0.0], 0)
polys = [poly_filler]

################################################################################################################ 
################################################################################################################               

# Texture Mapping for BMS files
def compute_tex_coords(mode: str = "H", repeat_x: int = 1, repeat_y: int = 1, tilt: float = 0,
                       angle_degrees: Union[float, Tuple[float, float]] = (45, 45),
                       custom: Optional[List[float]] = None) -> List[float]:
    
    def tex_coords_rotating_repeating(repeat_x: int, repeat_y: int, 
                                      angle_degrees: Tuple[float, float]) -> List[float]:
        
        angle_radians = [math.radians(angle) for angle in angle_degrees]

        def rotate(x: float, y: float, angle_idx: int) -> Tuple[float, float]:
            new_x = x * math.cos(angle_radians[angle_idx]) - y * math.sin(angle_radians[angle_idx])
            new_y = x * math.sin(angle_radians[angle_idx]) + y * math.cos(angle_radians[angle_idx])
            return new_x, new_y

        coords = [
            (0, 0),
            (repeat_x, 0),
            (repeat_x, repeat_y),
            (0, repeat_y)]

        rotated_coords = [rotate(x, y, 0) if i < 2 else rotate(x, y, 1) for i, (x, y) in enumerate(coords)]
        return [coord for point in rotated_coords for coord in point]
        
    # Vertical
    if mode == "V" or mode == "vertical":
        return [0, 0, 0, 1, 1, 1, 1, 0]
    elif mode == "V.f" or mode == "vertical_flipped":
        return [0, 1, 0, 0, 1, 0, 1, 1]
    
    # Horizontal
    elif mode == "H" or mode == "horizontal":
        return [0, 0, 1, 0, 1, 1, 0, 1]
    elif mode == "H.f" or mode == "horizontal_flipped":
        return [1, 0, 0, 0, 0, 1, 1, 1]
    
    # Vertical Repeated
    elif mode == "r.V" or mode == "repeating_vertical":
        return [0, 0, 0, repeat_x, repeat_y, repeat_x, repeat_y, 0]
    elif mode == "r.V.f" or mode == "repeating_vertical_flipped":
        return [0, repeat_x, 0, 0, repeat_y, 0, repeat_y, repeat_x]
    
    # Horizontal Repeated
    elif mode == "r.H" or mode == "repeating_horizontal":
        return [0, 0, repeat_x, 0, repeat_x, repeat_y, 0, repeat_y]
    elif mode == "r.H.f" or mode == "repeating_horizontal_flipped":
        return [repeat_x, 0, 0, 0, 0, repeat_y, repeat_x, repeat_y]
    
    # TODO
    elif mode == "r.r" or mode == "rotating_repeating":
        return tex_coords_rotating_repeating(repeat_x, repeat_y, angle_degrees)
    elif mode == "custom":
        if custom is None:
            raise ValueError("Custom TexCoords must be provided for mode 'custom'")
        return custom
    elif mode == "combined":
        return [0, 0, 1, 0, 1, 1 + tilt, 0, 2]
    else:
        raise ValueError(textwrap.dedent(f"""
                         Invalid mode '{mode}'.
                         Allowed values are: 
                         'H', 'horizontal', 'H.f', 'horizontal_flipped',
                         'V', 'vertical', 'V.f', 'vertical_flipped', 'r.H', 'repeating_horizontal',
                         'r.H.f', 'repeating_horizontal_flipped', 'r.V', 'repeating_vertical',
                         'r.V.f', 'repeating_vertical_flipped', 'r.r', 'rotating_repeating',
                         'custom', and 'combined'
                         """))
           
# SAVE BMS
def save_bms(
    texture_name, texture_indices = [1], vertices = vertices, polys = polys, 
    texture_darkness = None, tex_coords = None, tex_coord_mode = None, tex_coord_params = None, 
    randomize_textures = randomize_textures, random_texture_exclude = False, random_textures = random_textures):
        
    poly = polys[-1]  # Get the last polygon added
    bound_number = poly.cell_id
    
    # Randomize Textures
    if randomize_textures and not random_texture_exclude:
        texture_name = [random.choice(random_textures)]
        
    stored_texture_names.append(texture_name[0])
    
    # Create correct BMS file for Water textures
    if any(name.startswith("T_WATER") for name in texture_name):
        bms_filename = "CULL{:02d}_A2.bms".format(bound_number)
    else:
        bms_filename = "CULL{:02d}_H.bms".format(bound_number)
        
    if tex_coord_mode is not None:
        if tex_coord_params is None:
            tex_coord_params = {}
        tex_coords = compute_tex_coords(tex_coord_mode, **tex_coord_params)
        
    single_poly = [poly_filler, poly]
    
    bms = create_bms(vertices, single_poly, texture_indices, texture_name, texture_darkness, tex_coords)
    bms.write_bms(bms_filename)
    
    if DEBUG_BMS:
        bms.write_bms_debug(bms_filename + ".txt")
             
# Create BMS      
def create_bms(vertices, polys, texture_indices, texture_name: List[str], texture_darkness = None, tex_coords = None):
    shapes = []
    
    for poly in polys[1:]: # Skip the first filler polygon
        vertex_coordinates = [vertices[i] for i in poly.vert_indices]
        shapes.append(vertex_coordinates)
    
    # Default BMS values | do not change
    magic, flags, radius, radiussq, bounding_box_radius = "3HSM", 3, 0.0, 0.0, 0.0  
    texture_count = len(texture_name)
    coordinates = [coord for shape in shapes for coord in shape]
    vertex_count = len(coordinates)
    adjunct_count = len(coordinates)
    surface_count = len(texture_indices)   
    
    # Even with three vertices, we still require four indices (indices_sides: [[0, 1, 2, 0]])
    if len(coordinates) == 4:
        indices_count = surface_count * 4
    elif len(coordinates) == 3:
        indices_count = surface_count * 4
                     
    enclosed_shape = list(range(adjunct_count))

    # Texture Darkness and TexCoords        
    if texture_darkness is None:
        texture_darkness = [2] * adjunct_count # 2 is default texture brightness
        
    if tex_coords is None:
        tex_coords = [0.0 for _ in range(adjunct_count * 2)]

    # Create a list of Indices Sides, one for each shape
    indices_sides = []
    index_start = 0
    for shape in shapes:
        shape_indices = list(range(index_start, index_start + len(shape)))
        indices_sides.append(shape_indices)
        index_start += len(shape)
        
    return BMS(magic, vertex_count, adjunct_count, surface_count, indices_count, 
               radius, radiussq, bounding_box_radius, 
               texture_count, flags, texture_name, coordinates, texture_darkness, tex_coords, enclosed_shape, texture_indices, indices_sides)

################################################################################################################               
################################################################################################################  

def initialize_bnd(vertices, polys):
    magic = b'2DNB\0'
    offset = Vector3(0.0, 0.0, 0.0)
    x_dim, y_dim, z_dim = 0, 0, 0
    center = calculate_center(vertices)
    radius = calculate_radius(vertices, center)
    radius_sqr = radius ** 2
    bb_min = calculate_min(vertices)
    bb_max = calculate_max(vertices)
    num_hot_verts1, num_hot_verts2, num_edges = 0, 0, 0
    x_scale, z_scale = 0.0, 0.0
    num_indices, height_scale, cache_size = 0, 0, 0
    
    hot_verts = [Vector3(0.0, 0.0, 0.0)]  
    edges_0, edges_1 = [0], [1] 
    edge_normals = [Vector3(0.0, 0.0, 0.0)] 
    edge_floats = [0.0]  
    row_offsets, row_shorts, row_indices, row_heights = [0], [0], [0], [0]  

    return BND(magic, offset, x_dim, y_dim, z_dim, 
               center, radius, radius_sqr, bb_min, bb_max, 
               len(vertices), len(polys) - 1,
               num_hot_verts1, num_hot_verts2, num_edges, 
               x_scale, z_scale, 
               num_indices, height_scale, cache_size,
               vertices, polys,
               hot_verts, edges_0, edges_1, edge_normals, edge_floats,
               row_offsets, row_shorts, row_indices, row_heights)

def compute_plane_edgenormals(p1, p2, p3): # only 3 vertices are being used  
    v1 = np.subtract(p2, p1)
    v2 = np.subtract(p3, p1)

    planeN = np.cross(v1, v2)
    planeN = planeN / np.linalg.norm(planeN)

    planeD = -np.dot(planeN, p1)

    planeN = np.round(planeN, 3)
    planeD = round(planeD, 3)

    return planeN, planeD

def compute_edges(vertex_coordinates):
    vertices = [np.array([vertex[0], 0, vertex[2]]) for vertex in vertex_coordinates]
    planeN, _ = compute_plane_edgenormals(*vertices[:3]) 

    num_verts = len(vertices) # 3 for triangle, 4 for quad
    plane_edges = []

    abs_plane_x = abs(planeN[0])
    abs_plane_y = abs(planeN[1])
    abs_plane_z = abs(planeN[2])

    negate = 1.0

    if abs_plane_x < abs_plane_y or abs_plane_x < abs_plane_z:
        if abs_plane_y < abs_plane_x or abs_plane_y < abs_plane_z:
            if planeN[2] < 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[1] * negate, D[0] * negate, -np.dot([-D[1], D[0]], [A[0], A[1]])]))
        else:
            if planeN[1] > 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[2] * negate, D[0] * negate, -np.dot([-D[2], D[0]], [A[0], A[2]])]))
    else:
        if planeN[0] < 0.0:
            negate = -1.0
        for i in range(num_verts):
            A = vertices[i]
            B = vertices[(i+1) % num_verts]
            D = B - A
            plane_edges.append(np.array([-D[2] * negate, D[1] * negate, -np.dot([-D[2], D[1]], [A[1], A[2]])]))

    # Normalize edges
    for i in range(len(plane_edges)):
        norm_val = np.linalg.norm(plane_edges[i][:2]) # only first two components
        plane_edges[i][:2] /= norm_val
        plane_edges[i][2] /= norm_val

    edges = [Vector3(edge[0], edge[1], edge[2]) for edge in plane_edges]
    
    return edges

# Sort BND Vertices
def sort_coordinates(vertex_coordinates):
    max_x_coord = max(vertex_coordinates, key = lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key = lambda coord: coord[0])
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]

def create_polygon(
    bound_number, vertex_coordinates, 
    vertices = vertices, polys = polys,
    material_index = 0, cell_type = 0, 
    flags = None, plane_edges = None, wall_side = None, sort_vertices = False,
    hud_color = None, shape_outline_color = shape_outline_color):

    # Vertex indices
    base_vertex_index = len(vertices)
       
    # Flags
    if flags is None:
        if len(vertex_coordinates) == 4:
            flags = 6
        elif len(vertex_coordinates) == 3:
            flags = 3
        else:
            raise ValueError("Unsupported number of Vertices. You must either set 3 or 4 coordinates.")
        
    if sort_vertices: 
        vertex_coordinates = sort_coordinates(vertex_coordinates)
        
    new_vertices = [Vector3(*coord) for coord in vertex_coordinates]
    vertices.extend(new_vertices)
    vert_indices = [base_vertex_index + i for i in range(len(new_vertices))]
    
    # if len(new_vertices) == 3:
    #    vert_indices.append(0)
    
    # Plane Edges    
    if plane_edges is None:
        plane_edges = compute_edges(vertex_coordinates) 
    
    # Plane Normals
    if wall_side is None:
        plane_n, plane_d = compute_plane_edgenormals(*vertex_coordinates[:3])
    else:
        # Wall with varying X and Y coordinates
        if (max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates) > 0.1 and
            max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
            abs(max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates)) <= 0.15):

            
            if wall_side == "outside":
                corners = [0, 0, -1, max(coord[2] for coord in vertex_coordinates)]
            elif wall_side == "inside":
                corners = [0, 0, 1, -max(coord[2] for coord in vertex_coordinates)]
            
            plane_n, plane_d = corners[:3], corners[3]
            
        # Wall with varying Z and Y coordinates                               
        elif (abs(max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates)) <= 0.15 and
              max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
              max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates) > 0.1):
                    
            if wall_side == "outside":
                corners = [-1, 0, 0, min(coord[0] for coord in vertex_coordinates)]
            elif wall_side == "inside":
                corners = [1, 0, 0, -min(coord[0] for coord in vertex_coordinates)]
                
            plane_n, plane_d = corners[:3], corners[3]

    if isinstance(plane_n, np.ndarray):
        plane_n = Vector3(*plane_n.tolist())
    elif isinstance(plane_n, list):
        plane_n = Vector3(*plane_n)
            
    # Finalize Polygon
    poly = Polygon(bound_number, material_index, flags, vert_indices, plane_edges, plane_n, plane_d, cell_type)
    polys.append(poly)
        
    # Create JPG (for the HUD)
    hud_fill = hud_color is not None
    hudmap_vertices.append(vertex_coordinates)
    hudmap_properties[len(hudmap_vertices) - 1] = (hud_fill, hud_color, shape_outline_color, str(bound_number))
    
    # Store the polygon data (for Blender)
    polygon_info = {
        "vertex_coordinates": vertex_coordinates,
        "bound_number": bound_number,
        "material_index": material_index,
    }
    polygons_data.append(polygon_info)
    
def apply_dds_to_object(obj, texture_path):
    mat = bpy.data.materials.new(name = "DDS_Material")
    obj.data.materials.append(mat)
    obj.active_material = mat
    
    # Enable 'Use nodes':
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    
    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Add a diffuse shader and connect the texture to it:
    diffuse_shader = nodes.new(type = 'ShaderNodeBsdfPrincipled')
    texture_node = nodes.new(type = 'ShaderNodeTexImage')

    # Load texture
    texture_node.image = bpy.data.images.load(texture_path)

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    # Add the shader to the material's surface
    output_node = nodes.new(type = 'ShaderNodeOutputMaterial')
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])
    
    # UV unwrap the object (simple version)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.editmode_toggle()
    
# Create Meshes from Coordinates using 'polygon_data'
def create_mesh_from_polygon_data(polygon_data, textures_directory = None):
    coords = polygon_data["vertex_coordinates"]
    name = f"P{polygon_data['bound_number']}_M{polygon_data['material_index']}"

    edges = []
    faces = [range(len(coords))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    mesh.from_pydata(coords, edges, faces)
    mesh.update()

    if textures_directory:
        apply_dds_to_object(obj, textures_directory)

    return obj        
        
def create_blender_meshes():
    texture_paths = [os.path.join(textures_directory, f"{texture_name}.DDS") for texture_name in stored_texture_names]

    for polygon, texture_path in zip(polygons_data, texture_paths):
        create_mesh_from_polygon_data(polygon, texture_path)
           
################################################################################################################               
################################################################################################################ 

#? ==================CREATING YOUR CITY================== #?

def user_notes(x):
    f""" 
    Please find some example Polygons and BMS below this text.
    You can already run this the script with these Polygons and BMS to see how it works.
    
    If you're creating a Flat Surface, you should pass this structure to "vertex_coordinates:"
        max_x,max_z 
        min_x,max_z 
        max_x,min_z 
        min_x,min_z 
    
    For the Material Index, you can use the constants under 'Material types'. 
    You can also omit the Material Index, it will then default to 0 (which is a regular road).       
    Note that you can also set custom Materials properties elsewhere in the script (search for: 'set_material_index')
    
    Texture (UV) mapping examples:
    tex_coords = compute_tex_coords(mode = "v")
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 4, repeat_y = 2))
    tex_coords = compute_tex_coords(mode = "r.r", repeat_x = 3, repeat_y = 3, angle_degrees = (45, 45))) // unfinished
    
    Allowed values are: 
    'H', 'horizontal', 'H.f', 'horizontal_flipped',
    'V', 'vertical', 'V.f', 'vertical_flipped', 'r.H', 'repeating_horizontal',
    'r.H.f', 'repeating_horizontal_flipped', 'r.V', 'repeating_vertical',
    'r.V.f', 'repeating_vertical_flipped', 'r.r', 'rotating_repeating',
    'custom', and 'combined'
    
    You can set "texture_darkness" in the function "save_bms()" making texture edges darker or lighter at the corners. 
    If there are four vertices, you can then use it as follows: "texture_darkness = [40,2,50,1]"
    Where 2 is the default value. I recommend trying out different values to get an idea of the result in-game.
        
    Once functional AI is implemented, the road_type / bound_number might matter, here is the list:
    Open Areas: 0-199
    Roads: 201-859
    Intersections: 860+
    """
    
# Material types
GRASS_MTL = 87
WATER_MTL = 91
CUSTOM_MTL_NO_FRIC = 98 
 
# Cell types
TUNNEL = 1
INDOORS = 2
WATER_DRIFT = 4     # only works with 'T_WATER' textures
NO_SKIDS = 200 

# HUD map colors (feel free to add more)
WOOD = '#7b5931'
SNOW = '#cdcecd'
WATER = '#5d8096' 
R6_ROAD = '#414441'  
GRASS_24 = '#396d18'
        
# Start Area
create_polygon(
    bound_number = 1,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
        (50.0, 0.0, 70.0),
        (50.0, 0.0, -70.0),
        (-50.0, 0.0, -70.0)],
        hud_color = R6_ROAD)

save_bms(
    texture_name = ["R6"],
    texture_darkness = [40,2,50,1],
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Grass Area    
create_polygon(
	bound_number = 2,
	material_index = GRASS_MTL,
	vertex_coordinates = [
		(-50.0, 0.0, -70.0),
		(50.0, 0.0, -70.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)],
        hud_color = GRASS_24)

save_bms(
    texture_name = ["24_GRASS"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Snow Area (no friction)
create_polygon(
	bound_number = 3,
    material_index = CUSTOM_MTL_NO_FRIC,
    cell_type = NO_SKIDS,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)],
         hud_color = SNOW)

save_bms(
    texture_name = ["SNOW"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Wood Area
create_polygon(
	bound_number = 4,
	vertex_coordinates = [
		(50.0, 0.0, 70.0),
		(140.0, 0.0, 70.0),
		(140.0, 0.0, -70.0),
		(50.0, 0.0, -70.0)],
        hud_color = WOOD)

save_bms(
    texture_name = ["T_WOOD"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Barricade Area  
create_polygon(
	bound_number = 5,
    cell_type = TUNNEL,
	vertex_coordinates = [
		(50.0, 0.0, -70.0),
		(140.0, 0.0, -70.0),
		(140.0, 0.0, -140.0),
		(50.0, 0.0, -140.0)],
        hud_color = '#af0000')

save_bms(
    texture_name = ["T_BARRICADE"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 50, repeat_y = 50))

# Water Area
create_polygon(
	bound_number = 6,
    cell_type = WATER_DRIFT,
	material_index = WATER_MTL,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)],
        hud_color = WATER)    

save_bms(
    texture_name = ["VPSEMIRED_BK_VL"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Hill
create_polygon(
	bound_number = 7,
    cell_type = WATER_DRIFT,
	vertex_coordinates = [
		(-50.0, 0.0, -210.0),
		(50.0, 0.0, -210.0),
		(50.0, 300.0, -1000.0),
		(-50.0, 300.0, -1000.0)],
        hud_color = WATER)

save_bms(
    texture_name = ["T_WATER"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 100))

# Wall "inside"
create_polygon(
    bound_number = 8,
    vertex_coordinates = [
        (-10.0, 0.0, -50.00),
        (-10.0, 15.0, -49.99),
        (10.0, 15.0, -49.99),
        (10.0, 0.0, -50.00)], wall_side = "inside")

save_bms(
    texture_name = ["SNOW"], 
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Diagonal Road I
create_polygon(
    bound_number = 9,
    vertex_coordinates = [
        (-50.0, 0.0, 130.0),
        (-50.0, 0.0, 140.0),
        (140.0, 0.0, 70.0),
        (120.0, 0.0, 70.0)],
        hud_color = GRASS_24)

save_bms(
    texture_name = ["24_GRASS"],
    tex_coords=compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Triangle I
create_polygon(
    bound_number = 50,
    cell_type = NO_SKIDS,
    vertex_coordinates = [
        (-130.0, 0.0, 70.0),
        (-50.0, 0.0, 70.0),
        (-50.0, 0.0, 0.0),
        (-50.0, 0.0, -0.1)],
        hud_color = '#ffffe0')

save_bms(
    texture_name = ["OT_MALL_BRICK"],
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

# Triangle II
create_polygon(
    bound_number = 51,
    cell_type = NO_SKIDS,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
        (-130.0, 0.0, 70.0),
        (-50.0, 0.0, 140.0)],
        hud_color = '#ffffe0')

save_bms(
    texture_name = ["OT_MALL_BRICK"],
    tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

#! Same triangle as above, but with four vertices (backup)
# # Triangle II
# create_polygon(
#     bound_number = 51,
#     cell_type = NO_SKIDS,
#     vertex_coordinates = [
#         (-50.0, 0.0, 70.0),
#         (-130.0, 0.0, 70.0),
#         (-50.0, 0.0, 140.0),
#         (-50.0, 0.0, 139.9)],
#         hud_color = '#ffffe0')

# save_bms(
#     texture_name = ["OT_MALL_BRICK"],
#     tex_coords = compute_tex_coords(mode = "r.V", repeat_x = 10, repeat_y = 10))

################################################################################################################               
################################################################################################################ 

# Create BND file
def create_bnd(vertices, polys, city_name, debug_bounds):
    bnd = initialize_bnd(vertices, polys)
    
    with open(f"{city_name}_HITID.BND", "wb") as f:
        bnd.write_bnd(f)
        bnd.write_bnd_debug(f"{city_name}_HITID_debug.txt", debug_bounds) 
  
# Create SHOP and FOLDER structure   
def create_folders(city_name):
    FOLDER_STRUCTURE = [
        BASE_DIR / "build", 
        SHOP / "BMP16", 
        SHOP / "TEX16O", 
        SHOP / "TUNE", 
        SHOP / "MTL", 
        SHOP / "CITY" / city_name,
        SHOP / "RACE" / city_name,
        SHOP / "BMS" / f"{city_name}CITY",
        SHOP / "BMS" / f"{city_name}LM",
        SHOP / "BND" / f"{city_name}CITY",
        SHOP / "BND" / f"{city_name}LM"]
    
    for path in FOLDER_STRUCTURE:
        os.makedirs(path, exist_ok=True)
        
    # Write City Info file    
    with open(SHOP / 'TUNE' / f"{city_name}.CINFO", "w") as f:
        localized_name = race_locale_name
        map_name = city_name.lower()
        race_dir = city_name.lower()
        blitz_race_names_str = '|'.join(blitz_race_names)
        circuit_race_names_str = '|'.join(circuit_race_names)
        checkpoint_race_names_str = '|'.join(checkpoint_race_names)

        f.write(f"""
LocalizedName={localized_name}
MapName={map_name}
RaceDir={race_dir}
BlitzCount={len(blitz_races)}
CircuitCount={len(circuit_races)}
CheckpointCount={len(checkpoint_races)}
BlitzNames={blitz_race_names_str}
CircuitNames={circuit_race_names_str}
CheckpointNames={checkpoint_race_names_str}
""")
                    
def move_custom_textures(): 
    custom_textures_path = BASE_DIR / "Custom Textures"
    destination_tex16o_path = BASE_DIR / "SHOP" / "TEX16O"

    for custom_texs in custom_textures_path.iterdir():
        shutil.copy(custom_texs, destination_tex16o_path / custom_texs.name)
        
def move_core_tune(bangerdata_properties):
    editor_tune_dir = Path(BASE_DIR) / 'Core AR' / 'TUNE'
    shop_tune_dir = Path(BASE_DIR) / 'SHOP' / 'TUNE'

    tune_files = list(editor_tune_dir.glob('*'))

    for file in tune_files:
        shutil.copy(file, shop_tune_dir)  

        if file.stem.lower() in bangerdata_properties:
            shop_file = shop_tune_dir / file.name  

            with open(shop_file, 'r') as f:
                lines = f.readlines()
            
            properties = bangerdata_properties[file.stem.lower()]

            for i, line in enumerate(lines):
                if 'ImpulseLimit2' in properties and line.strip().startswith('ImpulseLimit2'):
                    new_value = properties['ImpulseLimit2']
                    lines[i] = f'\tImpulseLimit2 {new_value}\n'
                elif 'Mass' in properties and line.strip().startswith('Mass'):
                    new_value = properties['Mass']
                    lines[i] = f'\tMass {new_value}\n'
                elif 'AudioId' in properties and line.strip().startswith('AudioId'):
                    new_value = properties['AudioId']
                    lines[i] = f'\tAudioId {new_value}\n'
                elif 'Size' in properties and line.strip().startswith('Size'):
                    new_value = properties['Size']
                    lines[i] = f'\tSize {new_value}\n'
                elif 'CG' in properties and line.strip().startswith('CG'):
                    new_value = properties['CG']
                    lines[i] = f'\tCG {new_value}\n'
            
            with open(shop_file, 'w') as f:
                f.writelines(lines)
            
def move_dev_folder(destination_folder, city_name):
    dev_folder_path = BASE_DIR / 'dev'
    destination_path = Path(destination_folder) / 'dev'
    
    shutil.rmtree(destination_path, ignore_errors=True)
    shutil.copytree(dev_folder_path, destination_path)
    
    # Delete City's AI files after they have been moved to the user's MM1 folder
    city_folder_path = dev_folder_path / 'CITY' / city_name
    shutil.rmtree(city_folder_path, ignore_errors=True)
    
def move_open1560(destination_folder):
    open1560_folder_path = BASE_DIR / 'Installation Instructions' / 'Open1560'
    destination_folder = Path(destination_folder)
    
    for open1560_files in open1560_folder_path.iterdir():
        destination_file_path = destination_folder / open1560_files.name

        # If the source file doesn't exist or it isn't a file, skip to the next iteration
        if not open1560_files.is_file():
            continue

        # If the destination file doesn't exist or the source file is newer than the destination file, we will copy the file
        if not destination_file_path.exists() or open1560_files.stat().st_mtime > destination_file_path.stat().st_mtime:
            shutil.copy2(open1560_files, destination_file_path)
                             
# Distribute generated files
def distribute_files(city_name, bnd_hit_id, num_blitz, blitz_races, num_circuit, 
                               circuit_races, num_checkpoint, checkpoint_races, 
                               all_races_files = True):

    bms_files = []
    bms_a2_files = set()
     
    for file in BASE_DIR.iterdir():
        if file.name.endswith(".bms"):
            bound_number = int(re.findall(r'\d+', file.name)[0])
            bms_files.append(bound_number)
            if file.name.endswith("_A2.bms"):
                bms_a2_files.add(bound_number)
            if bound_number < 200:
                MOVE(file, SHOP / "BMS" / f"{city_name}LM" / file.name)
            else:
                MOVE(file, SHOP / "BMS" / f"{city_name}CITY" / file.name)
        
    for file in BASE_DIR.iterdir():
        if file.name.endswith(".bnd"):
            MOVE(file, SHOP / "BND" / file.name)
    MOVE(bnd_hit_id, SHOP / "BND" / bnd_hit_id)
        
    # Create WAYPOINTS files
    race_prefixes = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]
    if num_checkpoint > len(race_prefixes):
        raise ValueError("Number of Checkpoint races cannot be more than 12")
    
    for race_type, race_desc, prefix, num_files, race_waypoints in [("BLITZ", "Blitz", "ABL", num_blitz, blitz_races), 
                                                                    ("CIRCUIT", "Circuit", "CIR", num_circuit, circuit_races), 
                                                                    ("RACE", "Checkpoint", "RACE", num_checkpoint, checkpoint_races)]:
        
        for i in range(num_files):
            file_name = f"{race_type}{i}WAYPOINTS.CSV"

            with open(file_name, "w") as f:
                ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[((n//10%10!=1)*(n%10<4)*n%10)::4])
                f.write(f"# This is your {ordinal(i)} {race_desc} race Waypoint file\n")

                for waypoint in race_waypoints[i][:-1]:  # Exclude the last item, which are other parameters
                    waypoint_line = ', '.join(map(str, waypoint))
                    waypoint_line += ",0,0,\n"
                    f.write(waypoint_line)

            MOVE(file_name, os.path.join("SHOP", "RACE", f"{city_name}", file_name)) #! do not change

        # Create MM_DATA files
        mm_data_csv = f"MM{race_type}DATA.CSV"
        mm_data_comment_line = "Description, CarType, TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit, Difficulty, CarType, TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit, Difficulty\n"
        car_type_na, difficulty_na, opponent_na, num_laps_checkpoint_na, time_limit_na = 0, 1, 99, 99, 99

        with open(mm_data_csv, "w") as f:
            f.write(mm_data_comment_line)

            for i in range(num_files):
                other_parameters = race_waypoints[i][-1]
                num_laps_blitz = len(race_waypoints[i]) - 2 

                if race_type == "BLITZ":
                    a_timeofday, a_weather, a_cops, a_ambient, a_peds, a_timelimit, p_timeofday, p_weather, p_cops, p_ambient, p_peds, p_timelimit = other_parameters
                    
                    race_data = [car_type_na, a_timeofday, a_weather, opponent_na, a_cops, a_ambient, a_peds, num_laps_blitz, a_timelimit, opponent_na, car_type_na, p_timeofday, p_weather, opponent_na, p_cops, p_ambient, p_peds, num_laps_blitz, p_timelimit, difficulty_na]

                elif race_type == "CIRCUIT":
                    a_timeofday, a_weather, a_num_circuit_laps, a_cops, a_ambient, a_peds, p_timeofday, p_weather, p_num_circuit_laps, p_cops, p_ambient, p_peds = other_parameters
                    
                    race_data = [car_type_na, a_timeofday, a_weather, opponent_na, a_cops, a_ambient, a_peds, a_num_circuit_laps, time_limit_na, difficulty_na, car_type_na, p_timeofday, p_weather, opponent_na, p_cops, p_ambient, p_peds, p_num_circuit_laps, time_limit_na, difficulty_na]

                elif race_type == "RACE":
                    a_timeofday, a_weather, a_cops, a_ambient, a_peds, p_timeofday, p_weather, p_cops, p_ambient, p_peds = other_parameters
                    
                    race_data = [car_type_na, a_timeofday, a_weather, opponent_na, a_cops, a_ambient, a_peds, num_laps_checkpoint_na, time_limit_na, difficulty_na, car_type_na, p_timeofday, p_weather, opponent_na, p_cops, p_ambient, p_peds, num_laps_checkpoint_na, time_limit_na, difficulty_na]

                race_data_str = ', '.join(map(str, race_data))

                if race_type == "RACE":
                    f.write(f"{race_prefixes[i]}, {race_data_str}\n")
                else:
                    f.write(f"{prefix}{i}, {race_data_str}\n")

        MOVE(mm_data_csv, SHOP / "RACE" / city_name / mm_data_csv)

        # Create COPSWAYPOINTS.CSV file
        cnr_csv_file = "COPSWAYPOINTS.CSV"
        cnr_comment_line = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"
        cnr_filler = ",0,0,0,0,0,\n"
        
        with open(cnr_csv_file, "w") as f:
            f.write(cnr_comment_line)
            for i in range(0, len(cnr_waypoints), 3):
                f.write(", ".join(map(str, cnr_waypoints[i])) + cnr_filler) 
                f.write(", ".join(map(str, cnr_waypoints[i+1])) + cnr_filler)
                f.write(", ".join(map(str, cnr_waypoints[i+2])) + cnr_filler)

        MOVE(cnr_csv_file, SHOP / "RACE" / city_name / cnr_csv_file)

    # Create OPPONENT files
    if all_races_files:
        for race_type, prefix, num_files in [("BLITZ", "B", num_blitz), ("CIRCUIT", "C", num_circuit), ("RACE", "R", num_checkpoint)]:
            for race_index in range(num_files):
                for opp_index in range(1, aimap_num_opponents + 1):
                    opp_file_name = f"OPP{opp_index}{race_type}{race_index}.{prefix}{race_index}"
                    
                    opp_comment_line = f"# This is your Opponent file for opponent number {opp_index}, in race {race_type}{race_index}"
                    with open(opp_file_name, "w") as f:
                        f.write(opp_comment_line)
                        
                    MOVE(opp_file_name, SHOP / "RACE" / city_name / opp_file_name)
                    
               # Create AIMAP_P files
                aimap_file_name = f"{race_type}{race_index}.AIMAP_P"
                with open(aimap_file_name, "w") as f:
                    
                    aimap_content = f"""
                    # Ambient Traffic Density 
                    [Density] 
                    {aimap_ambient_density}

                    # Default Road Speed Limit 
                    [Speed Limit] 
                    45 

                    # Ambient Traffic Exceptions
                    # Rd Id, Density, Speed Limit 
                    [Exceptions] 
                    0 

                    # Police Init 
                    # Geo File, StartLink, Start Dist, Start Mode, Start Lane, Patrol Route 
                    [Police] 
                    1 
                    {aimap_cop_car} {aimap_cop_data}

                    # Opponent Init, Geo File, WavePoint File 
                    [Opponent] 
                    {aimap_num_opponents}
                    """

                    f.write(textwrap.dedent(aimap_content.strip()))
                    
                    for opp_index in range(1, aimap_num_opponents + 1):
                        f.write(f"{aimap_opponent_car} OPP{opp_index}{race_type}{race_index}.{prefix}{opp_index}\n")
                        
                MOVE(aimap_file_name, SHOP / "RACE" / city_name / aimap_file_name)
    
    # Create CELLS file
    with open(SHOP_CITY / f"{city_name}.CELLS", "w") as f:
        f.write(f"{len(bms_files)}\n")              # total number of cells
        f.write(str(max(bms_files) + 1000) + "\n")  # max cell number + 1000 (mandatory)

        sorted_bms_files = sorted(bms_files)
        for bound_number in sorted_bms_files:
            
            facade_room_fix = "1,1"
            
            # Retrieve polygon's cell type
            cell_type = None
            for poly in polys:
                if poly.cell_id == bound_number:
                    cell_type = poly.cell_type
                    break

            if cell_type is None:
                cell_type = 0
            
            # Write cells data
            if bound_number in bms_a2_files:
                row = f"{bound_number},32,{cell_type},{facade_room_fix}\n"
            else:
                row = f"{bound_number},8,{cell_type},{facade_room_fix}\n"
            f.write(row)
    
    for file in Path("angel").iterdir():
        if file.name in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(file, SHOP / file.name)

# Create Animations                              
def create_anim(city_name: str, anim_data: Dict[str, List[Tuple]], set_anim: bool = False) -> None: 
    if set_anim:
        output_folder_anim = SHOP_CITY / city_name
        main_anim_file = output_folder_anim / "ANIM.CSV"

        # Create ANIM.CSV file and write anim names
        with open(main_anim_file, 'w', newline = '') as file:
            writer = csv.writer(file)
            for obj in anim_data.keys():
                writer.writerow([f"anim_{obj}"])

        # Create individual anim files and write coordinates
        for obj, coordinates in anim_data.items():
            file_name = output_folder_anim / f"ANIM_{obj.upper()}.CSV"
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                if coordinates:
                    for coordinate in coordinates:
                        writer.writerow(coordinate)
                        
# Create AR file and delete folders
def create_ar(city_name, destination_folder, delete_shop = False) -> None:
    os.chdir(SHOP)
    ar_command = f"CMD.EXE /C run !!!!!{city_name}_City"
    subprocess.run(ar_command, shell=True)
    os.chdir(BASE_DIR)  
    
    build_dir = BASE_DIR / 'build'
    for file in build_dir.iterdir():
        if file.name.endswith(".ar") and file.name.startswith(f"!!!!!{city_name}_City"):
            MOVE(file, Path(destination_folder) / file.name)
            
    # Delete the build folder
    try:
        shutil.rmtree(build_dir)
    except Exception as e:
        print(f"Failed to delete the build directory. Reason: {e}")
    
    # Delete the SHOP folder
    if delete_shop:
        try:
            shutil.rmtree(SHOP)
        except Exception as e:
            print(f"Failed to delete the SHOP directory. Reason: {e}")

def create_hudmap(debug_hud, debug_hud_bound_id, shape_outline_color, 
                  export_jpg = True, x_offset = 0, y_offset = 0, line_width = 1, background_color = 'black') -> None:

    global hudmap_vertices
    global hudmap_properties
    output_bmp_folder = SHOP / 'BMP16'

    def draw_polygon(ax, polygon, shape_outline_color, 
                     label = None, add_label = False, hud_fill = False, hud_color = None) -> None:
        
        xs, ys = zip(*[(point[0], point[2]) for point in polygon])
        xs, ys = xs + (xs[0],), ys + (ys[0],) # the commas after [0] cannot be removed
        
        if shape_outline_color:
            ax.plot(xs, ys, color = shape_outline_color, linewidth = line_width)
        
        if hud_fill:
            ax.fill(xs, ys, hud_color)
            
        if add_label: 
            center = calculate_center_tuples(polygon)
            ax.text(center[0], center[2], label, color = 'white', ha = 'center', va = 'center', fontsize = 4.0)

    if export_jpg:
        # Regular Export (320 and 640 versions)
        _, ax = plt.subplots()
        ax.set_facecolor(background_color)
        
        for i, polygon in enumerate(hudmap_vertices):
            hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))
            draw_polygon(ax, polygon, shape_outline_color, add_label = False, hud_fill = hud_fill, hud_color = hud_color)
            
        ax.set_aspect('equal', 'box')
        ax.axis('off')
        trans = mtransforms.Affine2D().translate(x_offset, y_offset) + ax.transData
        for line in ax.lines:
            line.set_transform(trans)

        # Save JPG 640 and 320 Pictures            
        plt.savefig(output_bmp_folder / f"{city_name}640.JPG", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.1, facecolor = background_color)
        plt.savefig(output_bmp_folder / f"{city_name}320.JPG", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.1, facecolor = background_color)

    # Debug Export
    if debug_hud:
        _, ax_debug = plt.subplots()
        ax_debug.set_facecolor('black')

        for i, polygon in enumerate(hudmap_vertices):
            hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))
            draw_polygon(ax_debug, polygon, shape_outline_color, 
                         label = bound_label if debug_hud_bound_id else None, 
                         add_label = True, hud_fill = hud_fill, hud_color = hud_color)

        ax_debug.set_aspect('equal', 'box')
        ax_debug.axis('off')
                
        plt.savefig(BASE_DIR / f"{city_name}_HUD_debug.jpg", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.01, facecolor = 'black')

# Create EXT file            
def create_ext(city_name, polygons):
    x_coords = [vertex[0] for poly in polygons for vertex in poly]
    z_coords = [vertex[2] for poly in polygons for vertex in poly]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_z, max_z = min(z_coords), max(z_coords)

    with open(SHOP_CITY / f"{city_name}.EXT", 'w') as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")
               
# Create Bridges       
def create_bridges(all_bridges, set_bridges = set_bridges):
    for bridge in all_bridges:
        bridge_offset, bridge_orientation, bridge_number, bridge_object = bridge
        
        # Vertical
        if bridge_orientation == "V":
            bridge_facing = [bridge_offset[0] - 10, bridge_offset[1], bridge_offset[2]]
        elif bridge_orientation == "V.F":
            bridge_facing = [bridge_offset[0] + 10, bridge_offset[1], bridge_offset[2]]
            
        # Horizontal
        elif bridge_orientation == "H.E":
            bridge_facing = [bridge_offset[0], bridge_offset[1], bridge_offset[2] + 10]
        elif bridge_orientation == "H.W":
            bridge_facing = [bridge_offset[0], bridge_offset[1], bridge_offset[2] - 10]
            
        # Diagonal North    
        elif bridge_orientation == "N.E":
            bridge_facing = [bridge_offset[0] + 10, bridge_offset[1], bridge_offset[2] + 10]
        elif bridge_orientation == "N.W":
            bridge_facing = [bridge_offset[0] + 10, bridge_offset[1], bridge_offset[2] - 10]
            
        # Diagonal South   
        elif bridge_orientation == "S.E":
            bridge_facing = [bridge_offset[0] - 10, bridge_offset[1], bridge_offset[2] + 10]
        elif bridge_orientation == "S.W":
            bridge_facing = [bridge_offset[0] - 10, bridge_offset[1], bridge_offset[2] - 10]
            
        else:
            ValueError(f"""
                  Invalid Bridge Orientation. 
                  Please choose from 'V', 'V.F', 'H.E', 'H.W', 'N.E', 'N.W', 'S.E', or 'S.W'."
                  Where 'V' is vertical, 'H' is horizontal, 'F' is flipped, and e.g. 'N.E' is (diagonal) North East.
                  """)
            return
           
        drawbridge_values = f"{bridge_object},0,{bridge_offset[0]},{bridge_offset[1]},{bridge_offset[2]},{bridge_facing[0]},{bridge_facing[1]},{bridge_facing[2]}"
        bridge_filler = "tpsone,0,-9999.99,0.0,-9999.99,-9999.99,0.0,-9999.99"

        bridge_data = f"""DrawBridge{bridge_number}
    {drawbridge_values}
    {bridge_filler}
    {bridge_filler}
    {drawbridge_values}
    {bridge_filler}
    {bridge_filler}
DrawBridge{bridge_number}"""
        
        if set_bridges:            
            bridge_gizmo = SHOP_CITY / f"{city_name}.GIZMO"
            with bridge_gizmo.open("w") as f:
                if bridge_data is not None:
                    f.write(bridge_data)
                     
#!########### Modified Code by 0x1F9F1 Start ############      
                 
MIN_Y = -20
MAX_Y = 50
COLINEAR_FUDGE = 0.00001
MERGE_COLINEAR = True
RADIUS_FUDGE = 1
TANGENT_ANGLE_FUDGE = 0.999
TANGENT_DIST_FUDGE = 0.1
CORNER_FUDGE = 0.1
LENGTH_FUDGE = 1
STRICT_EDGES = False

if MERGE_COLINEAR:
    assert not STRICT_EDGES
    
# EDGE CLASS    
class Edge:
    def __init__(self, v1, v2):
        A = Vector2(v1.y - v2.y, v2.x - v1.x)
        assert A == (v1 - v2).Cross()

        c = A.Dot(v1)
        d = A.Mag2()

        if d > 0.00001:
            line = Vector3(A.x, A.y, -c) * (d ** -0.5)
        else:
            line = Vector3(0, 0, 1000000)

        self.v1 = v1
        self.v2 = v2

        self.line = line

        self.v1p = self.line_pos(self.v1, 0)
        self.v2p = self.line_pos(self.v2, 0)

        assert self.v1p < self.v2p

        self.length = d ** 0.5

        assert abs(self.length - self.v1.Dist(self.v2)) < 0.0001
        delta = self.v1p + self.length - self.v2p
        assert abs(delta) < 0.0001, delta

    # Distance tangential to the line
    def tangent_dist(self, point):
        return (point.x * self.line.x) + (point.y * self.line.y) + self.line.z

    # Distance along the line
    def line_pos(self, point, dist):
        x = point.x + self.line.x * dist
        y = point.y + self.line.y * dist
        return (x * self.line.y) - (y * self.line.x)

    def pos_to_point(self, pos):
        return Vector2(
             (self.line.y * pos) - (self.line.x * self.line.z),
            -(self.line.x * pos) - (self.line.y * self.line.z))


# CELL CLASS
class Cell:
    def __init__(self, id):
        self.id = id
        self.edges = []

    def add_edge(self, v1, v2):
        # Discard the Y (height) coordinate
        v1 = Vector2(v1.x, v1.z)
        v2 = Vector2(v2.x, v2.z)

        if v1.Dist2(v2) < 0.00001:
            return

        self.edges.append(Edge(v1, v2))

    def merge_colinear(self):
        i = 0

        while i < len(self.edges):
            edge1 = self.edges[i]

            j = i + 1

            while j < len(self.edges):
                edge2 = self.edges[j]
                j += 1

                angle = (edge1.line.x * edge2.line.x) + (edge1.line.y * edge2.line.y)

                if abs(angle) < 0.999:
                    continue

                v1p = edge1.tangent_dist(edge2.v1)
                if abs(v1p) > COLINEAR_FUDGE:
                    continue

                v2p = edge1.tangent_dist(edge2.v2)
                if abs(v2p) > COLINEAR_FUDGE:
                    continue

                v1p = edge1.line_pos(edge2.v1, v1p)
                v2p = edge1.line_pos(edge2.v2, v2p)

                v1p, v2p = min(v1p, v2p), max(v1p, v2p)

                if (v2p < edge1.v1p + CORNER_FUDGE) or (v1p > edge1.v2p - CORNER_FUDGE):
                    continue

                edge1.v1p = min(edge1.v1p, v1p)
                edge1.v2p = max(edge1.v2p, v2p)

                edge1.v1 = edge1.pos_to_point(edge1.v1p)
                edge1.v2 = edge1.pos_to_point(edge1.v2p)

                del self.edges[j - 1]
                j = i + 1

            i += 1

    def process(self):
        if MERGE_COLINEAR:
            self.merge_colinear()

        bb_min = Vector2( 10000000,  10000000)
        bb_max = Vector2(-10000000, -10000000)

        for edge in self.edges:
            for vert in (edge.v1,edge.v2):
                bb_min.x = min(bb_min.x, vert.x)
                bb_min.y = min(bb_min.y, vert.y)

                bb_max.x = max(bb_max.x, vert.x)
                bb_max.y = max(bb_max.y, vert.y)

        self.bb_min = bb_min
        self.bb_max = bb_max
        self.center = (self.bb_min + self.bb_max) * 0.5
        self.radius = (self.bb_min.Dist(self.bb_max) * 0.5)

    def check_radius(self, other, fudge):
        return self.center.Dist2(other.center) < (self.radius + other.radius + fudge) ** 2

# Prepare PTL
def prepare_ptl(polys, vertices):
    cells = {}

    for poly in polys:
        if poly.cell_id in cells: 
            cell = cells[poly.cell_id]
        else:
            cell = Cell(poly.cell_id)
            cells[poly.cell_id] = cell

        for i in range(poly.num_verts):
            j = (i + 1) % poly.num_verts
            cell.add_edge(vertices[poly.vert_indices[i]], vertices[poly.vert_indices[j]]) 

    for cell in cells.values():
        cell.process()

    portals = set()

    cell_vs_cell = 0
    edge_vs_edge = 0

    for cell1 in cells.values():
        for cell2 in cells.values():
            if cell1.id >= cell2.id:
                continue

            if not cell1.check_radius(cell2, RADIUS_FUDGE):
                continue

            cell_vs_cell += 1

            for edge1 in cell1.edges:
                for edge2 in cell2.edges:
                    edge_vs_edge += 1

                    v1p = edge1.tangent_dist(edge2.v1)
                    if abs(v1p) > TANGENT_DIST_FUDGE:
                        continue

                    v2p = edge1.tangent_dist(edge2.v2)
                    if abs(v2p) > TANGENT_DIST_FUDGE:
                        continue

                    v1p = edge1.line_pos(edge2.v1, v1p)
                    v2p = edge1.line_pos(edge2.v2, v2p)

                    v1p, v2p = min(v1p, v2p), max(v1p, v2p)

                    # Check whether any parts of the two edges are touching
                    if (v2p < edge1.v1p + CORNER_FUDGE) or (v1p > edge1.v2p - CORNER_FUDGE):
                        continue

                    if STRICT_EDGES:
                        # Check whether these two edges match
                        if (abs((v1p - edge1.v1p)) > CORNER_FUDGE) or (abs(v2p - edge1.v2p) > CORNER_FUDGE):
                            continue
                    else:
                        if (v2p - v1p) < LENGTH_FUDGE:
                            continue
                        pass

                    v1p = max(edge1.v1p, v1p)
                    v2p = min(edge1.v2p, v2p)

                    assert v1p < v2p

                    # TODO: Preserve y-height
                    p1 = edge1.pos_to_point(v1p)
                    p2 = edge1.pos_to_point(v2p)

                    portals.add((cell1.id, cell2.id, p1, p2))
                    
    return cells, portals

# Create PTL
def create_ptl(city_name, polys, vertices):
    _, portals = prepare_ptl(polys, vertices)

    with open(SHOP_CITY / f"{city_name}.PTL", 'wb') as f:
        
        write_pack(f, '<I', 0)
        write_pack(f, '<I', len(portals))

        for cell_1, cell_2, v1, v2 in portals:
            flags = 0x2
            edge_count = 2
            write_pack(f, '<BB', flags, edge_count)
            write_pack(f, '<H', 101)
            write_pack(f, '<HH', cell_2, cell_1)

            # TODO: Change height
            height = MAX_Y - MIN_Y
            write_pack(f, '<f', height)

            Vector3(v1.x, 0, v1.y).write(f)
            Vector3(v2.x, 0, v2.y).write(f)
            
#!########### Modified Code by 0x1F9F1 / Brick End ############                    
                    
                               
# BINARYBANGER CLASS                            
class BinaryBanger:
    def __init__(self, start: Vector3, end: Vector3, name: str, room: int = 4, flags: int = 0x800):
        self.room = room
        self.flags = flags
        self.start = start
        self.end = end
        self.name = name
        
    @classmethod
    def read_bng(cls, f):
        room, flags = read_unpack(f, '<HH')
        start_x, start_y, start_z = read_unpack(f, '<3f')
        end_x, end_y, end_z = read_unpack(f, '<3f')
        
        name = ''
        char = f.read(1).decode('utf8')
        while char != "\x00":
            name += char
            char = f.read(1).decode('utf8')
            
        start = Vector3(start_x, start_y, start_z)
        end = Vector3(end_x, end_y, end_z)
        
        return cls(start, end, name, room, flags)
        
    def __repr__(self):
        return f'''
BinaryBanger
Room: {self.room}
Flags: {self.flags}
Start: {self.start}
End: {self.end}
Name: {self.name}
    '''
  
class Prop_Editor:
    def __init__(self, city_name: str, debug_props: bool = False, input_bng_file: bool = False):
        self.objects = []
        self.debug_props = debug_props
        self.input_bng_file = input_bng_file
        self.filename = SHOP_CITY / f"{city_name}.BNG" if not input_bng_file else BASE_DIR / f"{city_name}"
        self.debug_filename = f"{city_name}_BNG_debug.txt"
        self.prop_file_path = BASE_DIR / "EditorResources" / "Prop Dimensions.txt"
        self.prop_data = self.load_prop_dimensions()    
          
    def load_prop_dimensions(self):
        prop_data = {}
        with open(self.prop_file_path, "r") as f:
            for line in f:
                name, value_x, value_y, value_z = line.split()
                prop_data[name] = Vector3(float(value_x), float(value_y), float(value_z))
        return prop_data
    
    def read_bng_file(self):
        with open(self.filename, mode = "rb") as f:
            num_objects = read_unpack(f, '<I')[0]
            
            for _ in range(num_objects):
                self.objects.append(BinaryBanger.read_bng(f))
            
    def write_bng_file(self, set_props: bool = False):
        if not set_props:
            return

        with open(self.filename, mode = "wb") as f:
            write_pack(f, '<I', len(self.objects))

            for index, obj in enumerate(self.objects, 1):
                if self.debug_props:
                    self.write_debug_info(index, obj)

                self.write_object_data(f, obj)

    def write_object_data(self, f, obj):
        write_pack(f, '<HH3f3f', obj.room, obj.flags, obj.start.x, obj.start.y, obj.start.z, obj.end.x, obj.end.y, obj.end.z)
        for char in obj.name:
            write_pack(f, '<s', bytes(char, encoding='utf8'))

    def write_debug_info(self, index, obj):
        with open(self.debug_filename, "a") as debug_f:
            debug_f.write(textwrap.dedent(f'''
                Prop {index} Data:
                Start: {obj.start}
                End: {obj.end}
                Name: {obj.name}
            '''))
                      
    def add_props(self, new_objects: List[Dict[str, Union[int, float, str]]]):
        default_separator_value = 10.0
        
        for obj in new_objects:
            offset = Vector3(obj['offset_x'], obj['offset_y'], obj['offset_z'])
            face = Vector3(obj['face_x'], obj['face_y'], obj['face_z'])
            name = obj['name']
            
            # separator = obj.get('separator', name)
            separator = obj.get('separator', default_separator_value)
            axis = obj.get('axis', 'x') # default is 'x' if 'axis' not provided

            # Check if Separator is a string (object name) or a numeric value
            if isinstance(separator, str):
                if separator not in self.prop_data:
                    raise ValueError(f"Separator {separator} not found in prop data.")
                separator_value = self.prop_data[separator][axis]
            else:
                separator_value = separator # separator is a numeric value

            self.objects.append(BinaryBanger(offset, face, name + "\x00"))

            if name in self.prop_data:
                if 'end_offset_' + axis in obj:
                    num_props = int(abs(obj['end_offset_' + axis] - obj['offset_' + axis]) / separator_value)

                    for i in range(1, num_props):
                        new_offset = Vector3(offset.x, offset.y, offset.z) # create a new instance with the same coordinates
                        new_offset[axis] = obj['offset_' + axis] + i * separator_value
                        self.objects.append(BinaryBanger(new_offset, face, name + "\x00"))

    def get_prop_dimension(self, prop_name: str, dimension: str) -> float:
        if prop_name in self.prop_data:
            if dimension == 'x':
                return self.prop_data[prop_name].x
            elif dimension == 'y':
                return self.prop_data[prop_name].y
            elif dimension == 'z':
                return self.prop_data[prop_name].z
            else:
                raise ValueError("Invalid dimension: {}. Use 'x', 'y', or 'z'.".format(dimension))
        else:
            raise ValueError("Prop {} not found in prop data.".format(prop_name))
        
    def place_props_randomly(self, seed, num_objects, object_dict, x_range, z_range):

        new_objects = []
        
        if isinstance(object_dict['name'], str):
            object_dict['name'] = [object_dict['name']]
            
        random.seed(seed)  

        for name in object_dict['name']:
            for _ in range(num_objects):
                x = random.uniform(*x_range)
                z = random.uniform(*z_range)

            # Create a new object dictionary with the random x and z coordinates
            new_object_dict = dict(object_dict) # Copy the original dictionary
            new_object_dict['offset_x'] = x
            new_object_dict['offset_z'] = z
            new_object_dict['name'] = name
            
            # Generate random face_x, face_y, and face_z values if they are not provided in the object dictionary
            if 'face_x' not in new_object_dict:
                new_object_dict['face_x'] = random.uniform(-179.0, 179.0)
            if 'face_y' not in new_object_dict:
                new_object_dict['face_y'] = random.uniform(-179.0, 179.0)
            if 'face_z' not in new_object_dict:
                new_object_dict['face_z'] = random.uniform(-179.0, 179.0)

            # Add the new object
            new_objects.append(new_object_dict)
            
        return new_objects

#################################################################################
#################################################################################

# MATERIALEDITOR CLASS
class Material_Editor:
    def __init__(self, name, friction, elasticity, drag, bump_height, bump_width, bump_depth, sink_depth, type, sound, velocity, ptx_color):
        self.name = name
        self.friction = friction
        self.elasticity = elasticity
        self.drag = drag
        self.bump_height = bump_height
        self.bump_width = bump_width
        self.bump_depth = bump_depth
        self.sink_depth = sink_depth
        self.type = type
        self.sound = sound
        self.velocity = velocity
        self.ptx_color = ptx_color 

    @staticmethod
    def read_materials(f):
        name = f.read(32).decode("latin-1").rstrip('\x00')
        params = read_unpack(f, '>7f2I')
        velocity = Vector2.read(f)
        ptx_color = Vector3.read(f)
        return Material_Editor(name, *params, velocity, ptx_color)

    @staticmethod
    def readn(f, count):
        return [Material_Editor.read_materials(f) for _ in range(count)]

    def write_materials(self, f):        
        write_pack(f, '>32s', self.name.encode("latin-1").ljust(32, b'\x00'))
        write_pack(f, '>7f2I', self.friction, self.elasticity, self.drag, self.bump_height, self.bump_width, self.bump_depth, self.sink_depth, self.type, self.sound)
        self.velocity.write(f)
        self.ptx_color.write(f)

    @staticmethod
    def write_materials_file(file_name, agi_phys_parameters):
        with open(file_name, 'wb') as f:
            write_pack(f, '>I', len(agi_phys_parameters))
            for param in agi_phys_parameters:                
                param.write_materials(f)
                
    @classmethod
    def edit_materials(cls, new_properties, set_material_index, physics_output_file):
        input_file = BASE_DIR / "EditorResources" / "PHYSICS.DB"
        output_folder = SHOP / "MTL"
        
        with input_file.open('rb') as file:
            count = read_unpack(file, '>I')[0]
            read_material_file = cls.readn(file, count)
            
        for prop in ["friction", "elasticity", "drag"]:
            setattr(read_material_file[set_material_index - 1], prop, new_properties[prop])
            
        cls.write_materials_file(physics_output_file, read_material_file)
        MOVE(physics_output_file, output_folder / physics_output_file)
  
    def __repr__(self):
        cleaned_name = self.name.rstrip()
        return f"""
AgiPhysParameters
    name        = '{cleaned_name}',
    friction    = {self.friction:.2f},
    elasticity  = {self.elasticity:.2f},
    drag        = {self.drag:.2f},
    bump_height = {self.bump_height:.2f},
    bump_width  = {self.bump_width:.2f},
    bump_depth  = {self.bump_depth:.2f},
    sink_depth  = {self.sink_depth:.2f},
    type        = {self.type},
    sound       = {self.sound},
    velocity    = {self.velocity},
    ptx_color   = {self.ptx_color}
        """
        
###################################################################################################################
###################################################################################################################

# Intersection types
STOP = 0 
STOP_LIGHT = 1 
YIELD = 2
CONTINUE = 3

# True or False for e.g. "traffic_blocked"
NO = 0
YES = 1

# Stop Light names
STOP_SIGN = "tpsstop"
STOP_LIGHT_SINGLE = "tplttrafc"
STOP_LIGHT_DUAL = "tplttrafcdual"

# BAI EDITOR CLASS
class BAI_Editor:
    def __init__(self, city_name, streets, ai_map = True):
        self.city_name = f"{city_name}"
        self.streets = streets
        
        self.ai_dir = BASE_DIR / "dev" / "CITY" / self.city_name
                
        if ai_map:
            self.write_map()

    def write_map(self):        
        self.ai_map_file = self.ai_dir / f"{self.city_name}.map"
        self.ai_dir.mkdir(parents = True, exist_ok = True)
        
        with open(self.ai_map_file, 'w') as file:
            file.write(self.map_template())
    
    def map_template(self):
        streets_representation = '\n\t\t'.join([f'"{street}"' for street in self.streets])

        bai_map_template = f"""
mmMapData :0 {{
    NumStreets {len(self.streets)}
    Street [
        {streets_representation}
    ]
}}
        """
        return textwrap.dedent(bai_map_template).strip()
       
# STREETFILE CLASS
class StreetFile_Editor:    
    def __init__(self, city_name, street_data, ai_streets = False, reverse = False):
        self.street_name = street_data["street_name"]
        self.reverse = reverse

        if "lanes" in street_data:
            self.original_lanes = street_data["lanes"]
            if self.reverse:
                self.lanes = {key: values + values[::-1] for key, values in self.original_lanes.items()}  
                # append reversed vertices to original vertices
            else:
                self.lanes = self.original_lanes
        elif "vertices" in street_data:
            self.original_lanes = {"lane_1": street_data["vertices"]}
            if self.reverse:
                self.lanes = {"lane_1": street_data["vertices"] + street_data["vertices"][::-1]}  
                # append reversed vertices to original vertices
            else:
                self.lanes = self.original_lanes

        self.intersection_types = street_data.get("intersection_types", [CONTINUE, CONTINUE])
        self.stop_light_positions = street_data.get("stop_light_positions", [(0.0, 0.0, 0.0)] * 4)
        self.stop_light_names = street_data.get("stop_light_names", [STOP_LIGHT_SINGLE, STOP_LIGHT_SINGLE])
        self.traffic_blocked = street_data.get("traffic_blocked", [NO, NO])
        self.ped_blocked =  street_data.get("ped_blocked", [NO, NO])
        self.road_divided = street_data.get("road_divided", NO)
        self.alley = street_data.get("alley", NO)

        if ai_streets:
            self.write_streets()

    def write_streets(self):
        self.filepath = BASE_DIR / "dev" / "CITY" / city_name / f"{self.street_name}.road"
        self.filepath.parent.mkdir(parents = True, exist_ok = True)
        
        with self.filepath.open('w') as file:
            file.write(self.street_template())

    def street_template(self):
        lane_1_key = list(self.lanes.keys())[0]  # Assuming all lanes have the same number of vertices
        num_vertex_per_lane = len(self.original_lanes[lane_1_key])
        num_total_vertex = num_vertex_per_lane * len(self.lanes) * (2 if self.reverse else 1)
        vertex_string = '\n\t\t'.join('\n\t\t'.join(f'{vertex[0]} {vertex[1]} {vertex[2]}' for vertex in vertices) for vertices in self.lanes.values())
        normals_string = '\n\t\t'.join('0.0 1.0 0.0' for _ in range(num_total_vertex))
        stop_light_positions_strings = '\n\t'.join(f'StopLightPos[{i}] {pos[0]} {pos[1]} {pos[2]}' for i, pos in enumerate(self.stop_light_positions))

        street_template = f"""
mmRoadSect :0 {{
    NumVertexs {num_vertex_per_lane}
    NumLanes[0] {len(self.lanes)}
    NumLanes[1] {len(self.lanes) if self.reverse else 0}
    NumSidewalks[0] 0
    NumSidewalks[1] 0
    TotalVertexs {num_total_vertex}
    Vertexs [
        {vertex_string}
    ]
    Normals [
        {normals_string}
    ]
    IntersectionType[0] {self.intersection_types[0]}
    IntersectionType[1] {self.intersection_types[1]}
    {stop_light_positions_strings}
    Blocked[0] {self.traffic_blocked[0]}
    Blocked[1] {self.traffic_blocked[1]}
    PedBlocked[0] {self.ped_blocked[0]}
    PedBlocked[1] {self.ped_blocked[1]}
    StopLightName [
        "{self.stop_light_names[0]}"
        "{self.stop_light_names[1]}"
    ]
    Divided {self.road_divided}
    Alley {self.alley}
}}
        """
        
        return textwrap.dedent(street_template).strip()
    
    def create_streets(city_name, street_data, ai_streets, reverse, ai_map = True):
        street_names = [StreetFile_Editor(city_name, data, ai_streets, reverse).street_name for data in street_data]
        return BAI_Editor(city_name, street_names, ai_map)

###################################################################################################################
################################################################################################################### 

# FACADE CLASS
class Facade_Editor:
    def __init__(self, flags, start, end, sides, scale, name):
        self.room = 0x1
        self.flags = flags
        self.start = start
        self.end = end
        self.sides = sides
        self.scale = scale
        self.name = name

    @classmethod
    def read_fcd(cls, f):
        _, flags = read_unpack(f, '2H')
        start = Vector3.read(f)
        end = Vector3.read(f)
        sides = Vector3.read(f)
        scale = read_unpack(f, 'f')[0]

        name_data = bytearray()
        while True:
            char = f.read(1)
            if char == b'\x00':
                break
            name_data.extend(char)
        name = name_data.decode('utf-8')
        
        return cls(flags, start, end, sides, scale, name)

    def write_fcd(self, f):
        write_pack(f, '2H', self.room, self.flags)
        write_pack(f, '6f', *self.start, *self.end)
        write_pack(f, '3f', *self.sides)
        write_pack(f, 'f', self.scale)
        f.write(self.name.encode('utf-8'))
        f.write(b'\x00')
        
    def __repr__(self):
        return f"""
Facade Editor
    Room: {self.room}
    Flags: {self.flags}
    Start: {self.start}
    End: {self.end}
    Sides: {self.sides}
    Scale: {self.scale}
    Name: {self.name}
    """
      
def read_fcd_scales(scales_file):
    scales = {}
    with open(scales_file, 'r') as f:
        for line in f:
            facade_name, scale = line.strip().split(": ")
            scales[facade_name] = float(scale)
    return scales
      
def get_coord_from_tuple(coord_tuple, axis):
    axis_dict = {'x': 0, 'y': 1, 'z': 2}
    return coord_tuple[axis_dict[axis]]  
    
def create_fcd(filename, facade_params, target_fcd_dir, set_facade = False, debug_facades = False):
    if set_facade:
        facades = []
        axis_dict = {'x': 0, 'y': 1, 'z': 2}
        
        scales = read_fcd_scales(BASE_DIR / "EditorResources" / 'FCD scales.txt')

        for params in facade_params:
            num_facades = math.ceil(abs(
                get_coord_from_tuple(params['end'], params['axis']) - get_coord_from_tuple(params['start'], params['axis'])) / params['separator'])

            for i in range(num_facades): 
                flags = params['flags']
                current_start = list(params['start'])
                current_end = list(params['end'])

                shift = params['separator'] * i
                current_start[axis_dict[params['axis']]] = get_coord_from_tuple(params['start'], params['axis']) + shift
                current_end[axis_dict[params['axis']]] = current_start[axis_dict[params['axis']]] + params['separator']

                current_start = tuple(current_start)
                current_end = tuple(current_end)

                sides = params['sides']
                scale = scales.get(params['facade_name'], params.get('scale', 1.0))
                name = params['facade_name']

                facade = Facade_Editor(flags, current_start, current_end, sides, scale, name)
                facades.append(facade)

        with open(filename, mode = 'wb') as f: 
            write_pack(f, '<I', len(facades))
            for facade in facades:
                facade.write_fcd(f)

        MOVE(filename, target_fcd_dir / filename)

        if debug_facades:
            debug_filename = filename.replace('.FCD', '_FCD_debug.txt')
            with open(debug_filename, mode = 'w', encoding = 'utf-8') as f:
                for facade in facades:
                    f.write(str(facade))
                
###################################################################################################################
###################################################################################################################  

# Create commandline
def create_commandline(city_name: str, destination_folder: Path):
    city_name = city_name.lower()
    cmd_file = "commandline.txt"
    cmd_params = f"-path ./dev -allrace -allcars -f -heapsize 499 -multiheap -maxcops 100 -speedycops -l {city_name}"
    cmd_file_path = destination_folder / cmd_file
    
    with cmd_file_path.open("w") as file:
        file.write(cmd_params)
        
# Start game
def start_game(destination_folder, play_game = False):
    if play_game:
        subprocess.run(str(Path(destination_folder) / "Open1560.exe"), cwd = str(destination_folder), shell = True)
        
################################################################################################################### 

#* FACADE NOTES
#* The "room" should match the bound_number in which the Facade is located.
#* Separator: (max_x - min_x) / separator(value) = number of facades
#* Sides: unknown, but leave it as is
#* Scale: unknown value, behavior: stretch each facade or thin it out
#* Facade_name: name of the facade in the game files

#* For a list of facades, check out the /__Useful Documents/CHICAGO_unique_FCD_SCALES.txt
#* Here you will also find the Scale values for each facade that was used in the original game.

#* Few Facade name examples: ofbldg02, dt11_front, tunnel01, t_rail01, ramp01, tunnel02
   
fcd_one = {
	'flags': 1057,
	'start': (-10, 0.0, -50.0),
	'end': (10, 0.0, -50.0),
	'sides': (27.84,0.00,0.00),
	'separator': 10.0, 
	'facade_name': "ofbldg02",
	'axis': 'x'}

# Pack all Facades for processing
fcd_list = [fcd_one]

###################################################################################################################

# SET AI PATHS

f"""
# The following variables are OPTIONAL: 

# Intersection_types, defaults to: "CONTINUE"
(possbile types: "STOP", "STOP_LIGHT", "YIELD", "CONTINUE")

# Stop_light_names, defaults to: "STOP_LIGHT_SINGLE"
(possbile names: "STOP_SIGN", "STOP_LIGHT_SINGLE", "STOP_LIGHT_DUAL")

# Stop_light_positions, defaults to: (0,0,0)
# Traffic_blocked, Ped_blocked, Road_divided, and Alley, all default to: "NO"
(possbile values: "YES", "NO")

Note:
# Stop lights will only show if the Intersection_type is "stoplight"
# Each lane will automatically have an identical reversed lane  
"""

#! Do not delete this Street
street_0 = {
    "street_name": "path_filler",
    "vertices": [
        (0,0,0),    # keep this
        (30,0,30)]} # starting position in Cruise mode

#! Do not delete this Street
street_1 = {
     "street_name": "path_1",
     "vertices": [
         (0.0, 0.0, 15.0),
         (10.0, 0.0, -20.0),
         (10.0, 0.0, -40.0),
         (10.0, 0.0, -60.0),
         (10.0, 0.0, -80.0)]}

#! Do not delete this Street
street_2 = {
    "street_name": "path_2",
    "lanes": {
        "lane_1": [
            (-30.0, 1.0, -20.0),
            (-30.0, 1.0, -50.0),
            (-30.0, 1.0, -80.0),
            (-30.0, 1.0, -110.0),
            (-30.0, 1.0, -140.0),
            (-30.0, 1.0, -145.0)
        ],
        "lane_2": [
            (-40.0, 1.0, -20.0),
            (-40.0, 1.0, -50.0),
            (-40.0, 1.0, -80.0),
            (-40.0, 1.0, -110.0),
            (-40.0, 1.0, -140.0),
            (-40.0, 1.0, -145.0)
        ],
        "lane_3": [
            (-50.0, 1.0, -20.0),
            (-50.0, 1.0, -50.0),
            (-50.0, 1.0, -80.0),
            (-50.0, 1.0, -110.0),
            (-50.0, 1.0, -140.0),
            (-50.0, 1.0, -145.0)
        ]
    },
    "intersection_types": [STOP_LIGHT, STOP_LIGHT],
    "stop_light_names": [STOP_LIGHT_DUAL, STOP_LIGHT_DUAL],
    "stop_light_positions": [
         (10.0, 0.0, -20.0),
         (10.01, 0.0, -20.0),
         (-10.0, 0.0, -20.0),
         (-10.0, 0.0, -20.1)],
    "traffic_blocked": [NO, NO],
    "ped_blocked": [NO, NO],
    "road_divided": NO,
    "alley": NO}

# Pack all AI paths for processing
street_list = [street_0, street_1, street_2]

################################################################################################################               

# SET PROPS
# Single Prop (China Gate)
prop_1 = {'offset_x': 0, 
          'offset_y': 0.0, 
          'offset_z': -20, 
          'face_x': 10000, 
          'face_y': 0.0, 
          'face_z': -80, 
          'name': 'cpgate'}

# Multiple props (TP Trailer)
prop_2 = {'offset_x': 60, 
          'offset_y': 0.0, 
          
          'offset_z': -50, 
          'end_offset_z': 70, 
          'separator': 16.34,
          'name': 'tp_trailer', 
          'axis': 'z',

          'face_x': 10, 
          'face_y': 0.0, 
          'face_z': -40000}

# Put your non-randomized props here
prop_list = [prop_1, prop_2] 

# Put your randomized props here (you will add them to a list "random_parameters")
prop_3 = {'offset_y': 0.0,
          'name': ["tp_tree10m"]*20}

prop_4 = {'offset_y': 0.0,
          'separator': 10.0,
          'name': ["vpbug", "vpbus", "caddie", "vpcop", "vpford", "vpbullet", "vpmustang99", "vppanoz", "vppanozgt", "vpsemi"]}

# Configure your random props here
random_parameters = [
    {"seed": 123, "num_objects": 1, "object_dict": prop_3, "x_range": (65, 135), "z_range": (-65, 65)},
    {"seed": 2, "num_objects": 10, "object_dict": prop_4, "x_range": (50, 140), "z_range": (-140, -70)}]

# ImpulseLimit
TREE = 1E+30

# AudioIds
MALLDOOR_ = 1
POLE_ = 3           
SIGN_ = 4          
MAIL_ = 5              
METER_ = 6
TRASH_ = 7          
BENCH_ = 8         
TREE_ = 11         
BOXES_ = 12         # also used for "bridge crossgate"
NO_NAME_ = 13       # difficult to describe
BARREL_ = 15        # also used for "dumpster"
PHONEBOOTH_ = 20
CONE_ = 22 
NO_NAME_2 = 24      # sounds a bit similar to "glass"
NEWS_ = 25
GLASS_ = 27

# Set additional Prop Properties here (currently only possible for cars)
# The Size does affect how the prop moves after impact. CG stands for Center of Gravity. 
bangerdata_properties = {
    'vpbug': {'ImpulseLimit2': TREE, 'AudioId': GLASS_},
    'vpbus': {'ImpulseLimit2': 50, 'Mass': 50, 'AudioId': POLE_, 'Size': '18 6 5', 'CG': '0 0 0'}}

# Props
f"""    Player Cars:
        vpbug, vpbus, caddie, vpcop, vpford, vpbullet, vpmustang99, vppanoz, vppanoz, vpsemi

        Traffic Cars:
        vaboeing_small, vabus, vacompact, vadelivery, vadiesels, valimo, valimoangel
        valimoblack, vapickup, vasedanl, vasedans, vataxi, vataxicheck, vavan       
        
        Other:
        vaboeing            (very large plane, no collision)
        r_l_train           (el train)
        tp_trailer          (trailer)
        tpdrawbridge04      (drawbridge small)
        tpdrawbridge06      (drawbridge large)
        ...                 (many more) 
        """

################################################################################################################     

# SET MATERIAL PROPERTIES
# available numbers: 94, 95, 96, 97, 98, also see: https://tinyurl.com/y2d56pa6
set_material_index = 98

# See: /Useful documents/PHYSICS.DB_extracted.txt for more information
new_properties = {"friction": 0.1, "elasticity": 0.01, "drag": 0.0}

################################################################################################################   

# Call FUNCTIONS
print("\n===============================================\n")
print("Generating " + f"{race_locale_name}...")
print("\n===============================================\n")

create_folders(city_name)
create_bnd(vertices, polys, city_name, debug_bounds)
distribute_files(city_name, f"{city_name}_HITID.BND", 
                           len(blitz_races), blitz_races, len(circuit_races), 
                           circuit_races, len(checkpoint_races), checkpoint_races, all_races_files = True)

Material_Editor.edit_materials(new_properties, set_material_index, "physics.db")
StreetFile_Editor.create_streets(city_name, street_list, ai_streets, ai_map)

prop_editor = Prop_Editor(city_name, debug_props = debug_props, input_bng_file = False)

for i in random_parameters:
    randomized_objects = prop_editor.place_props_randomly(**i)
    prop_list.extend(randomized_objects)
    
prop_editor.add_props(prop_list)
prop_editor.write_bng_file(set_props)

move_open1560(mm1_folder)
move_dev_folder(mm1_folder, city_name)
move_core_tune(bangerdata_properties)
move_custom_textures()

create_ext(city_name, hudmap_vertices) 
create_anim(city_name, anim_data, set_anim)   
create_bridges(bridges, set_bridges) 
create_fcd(f"{city_name}.FCD", fcd_list, BASE_DIR / SHOP_CITY, set_facade, debug_facades)

create_hudmap(debug_hud, debug_hud_bound_id, shape_outline_color, export_jpg = True, 
              x_offset = -0.0, y_offset = -0.0, line_width = 0.7, 
              background_color = 'black')

create_ptl(city_name, polys, vertices)
create_ar(city_name, mm1_folder, delete_shop)
create_commandline(city_name, Path(mm1_folder))

print("\n===============================================\n")
print("Succesfully created " + f"{race_locale_name}!")
print("\n===============================================\n")

start_game(mm1_folder, play_game)

# W.I.P.
# create_blender_meshes()

#? ============ For Reference ============

# # Print the contents of a BNG file in the current working directory
# prop_editor = Prop_Editor("CHICAGO.BNG", debug_props = debug_props, input_bng_file = True)
# prop_editor.read_bng_file()
# for objects in prop_editor.objects:
#    print(objects)
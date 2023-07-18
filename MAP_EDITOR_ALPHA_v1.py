
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
import math
import glob
import struct
import shutil
import random
import textwrap
import subprocess
import numpy as np
import matplotlib.pyplot as plt                 
import matplotlib.transforms as mtransforms  
from collections import defaultdict
from typing import List, Dict, Union, Tuple, Optional, BinaryIO


#! SETUP I (mandatory)                          Control + F    "city=="  to jump to The City Creation section
city_name = "USER"                              # One word (no spaces)  --- name of the .ar file
race_locale_name = "My First City"              # Can be multiple words --- name of the city in Race Locale Menu
mm1_folder = r"C:\Users\robin\Desktop\MM1_game" # Path to your MM1 folder (Open1560 is automatically copied to this folder)


#* SETUP II (optional, Map Creation)
play_game=True                  # boot the game immediately after the Map is created
delete_shop=True                # delete the raw city files after the .ar file has been created

set_facade=False                # change to "True" if you want FACADES
set_props=False                 # change to "True" if you want PROPS // (currently broken)

set_anim=False                  # change to "True" if you want ANIM (plane and eltrain
set_bridges=False               # change to "True" if you want BRIDGES // (currently broken)

ai_map=True                    # change both to "True" if you want AI paths
ai_streets=True                # change both to "True" if you want AI paths
cruise_start_position=          (20.0, 0.0, 20.0) # x, y, z // both ai_map and ai_streets must be "True" 

randomize_textures=False        # change to "True" if you want randomize all textures in your Map (see below for a selection)
randomize_texture_names = ["T_WATER", "T_GRASS", "T_WOOD", "IND_WALL", "EXPLOSION", "OT_BAR_BRICK", "R4", "R6", "T_WALL", "FXLTGLOW"]

debug_bnd=False                 # change to "True" if you want a BND/collision Debug text file
debug_facade=False              # change to "True" if you want a Facade Debug text file
debug_props=False               # change to "True" if you want a BNG Debug text file
debug_hud=False                 # change to "True" if you want a HUD Debug jpg file


#* SETUP II (optional, Blender)
export_blender=debug_bnd=False  # change to "True" if you want to export the Map vertices to Blender
run_blender=False               # change to "True" if you want to run Blender after Map vertices have been exported
bnd_blender_data = "SCRIPT_EXPORT_vertices.txt" 
blender_exe = r"C:\\Program Files\Blender Foundation\Blender 3.3\blender.exe" # change if necessary


#* SETUP III (optional, Race Editor)
morning, noon, evening, night = 0, 1, 2, 3  # do not change
clear, cloudy, rain, snow = 0, 1, 2, 3      # do not change

# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints, the number of waypoints for Circuits and Checkpoints is unlimited
# Waypoint Structure: (x, y, z, rotation, width)

# Race names
blitz_race_names = ["Tigerhawk's BRB", "Target Car 2024"]
circuit_race_names = ["Dading's Circuit"]
checkpoint_race_names = ["Giga's Madness"]

# Blitzes
blz_0 = [
    [0.0, 0.0, 0.1, 5.0, 15.0], # your notes here
    [0.0, 0.0, -20, 5.0, 15.0], # your notes here
    [0.0, 0.0, -40, 5.0, 15.0],
    [0.0, 0.0, -60, 5.0, 15.0],
    [0.0, 0.0, -80, 5.0, 15.0],
    [0.0, 0.0, -99, 5.0, 15.0], 
    [morning, clear, 0, 0, 0, 99999, night, snow, 1, 1, 1, 99999]] 
#* time, weather, cops, ambient, peds, timelimit (Amateur first, Pro second)    

blz_1 = [
    [0.0, 0.0, 0.1, 5.0, 15.0],
    [0.0, 0.0, -20, 5.0, 15.0],
    [0.0, 0.0, -40, 5.0, 15.0],
    [morning, cloudy, 0, 0, 0, 2024, evening, rain, 1, 1, 1, 2024]]

# Circuits
cir_0 = [
    [20.0, 0.0, 0.0, 180.0, 8.0],
    [0.0, 0.0, 50.0, 90, 8.0],
    [50.0, 0.0, 0.0, 0.01, 8.0],
    [0.0, 0.0, -75.0, -90, 8.0],
    [noon, clear, 3, 0, 0, 0, evening, snow, 3, 0, 0, 0]] 
#* time, weather, number of laps, cops, ambient, peds (Amateur first, Pro second) 

# Checkpoints   
race_0 = [
    [0.0, 0.0, 0.0, 0.0, 15.0],
    [0.0, 0.0, 50.0, 0.0, 15.0],  
    [morning, rain, 0, 0, 0, night, snow, 0, 0, 0]] 
#* time, weather, cops, ambient, peds (Amateur first, Pro second) 

# Packing all the race configurations
blitz_waypoints = [blz_0, blz_1]
circuit_waypoints = [cir_0]
checkpoint_waypoints = [race_0]


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
        (250, 40.0, -250),      # you can only have one Plane and/or one Eltrain
        (250, 40.0, 250),       # you can set any number of coordinates for your path(s)
        (-250, 40.0, -250),     
        (-250, 40.0, 250)], 
    'eltrain': [
        (80, 25.0, -80),
        (80, 25.0, 80), 
        (-80, 25.0, -80),
        (-80, 25.0, 80)]}


#* SETUP VI (optional, Bridges, experimental)
slim_bridge = "tpdrawbridge04"  #* dimension: x: 30.0 y: 5.9 z: 32.5
wide_bridge = "tpdrawbridge06"  #* dimension: x: 40.0 y: 5.9 z: 32.5
new_bridge_object = "..."       # you can pass any object, for example: vpmustang99

#! I: only ONE bridge can be present in ONE cull room (otherwise the game will crash)
#! II: Bridges currently only work in MULTIPLAYER, in SINGLEPLAYER the game will crash if you enable bridges (will be fixed later)

# Structure: (x,y,z, orientation, bridge_number, bridge_object)
bridges = [
    ((-50.0, 0.0, -150.0), "V", 1, slim_bridge),  
    ((-200.0, 0.0, -200.0), "H.E.", 2, wide_bridge)] 

# Possible orientations
f"""Please choose from 'V', 'V.F', 'H.E', 'H.W', 'N.E', 'N.W', 'S.E', or 'S.W'."
    Where 'V' is vertical, 'H' is horizontal, 'F' is flipped, and e.g. 'N.E' is (diagonal) North East."""

# AIMAP data (applies to all races, will be improved later)
aimap_ambient_density = 0.5
aimap_num_opponents = 8 
aimap_opponent_car = "vppanozgt" 
aimap_cop_car = "vpcop"
aimap_cop_data = "-30.1 0.0 30.0 0.0 2 0"

################################################################################################################               
################################################################################################################     
 
def to_do_list(x):
            """
            TEXCOORDS --> investigate/improve "rotating_repeating" (angles)
            TEXCOORDS --> fix wall textures not appearing in game (add +0.01 or -0.01 to one of the x or z coordinates)
            TEXTURES --> add TEX16A and TEX16O from existing custom cities and create a folder with suitable/common textures
            TEXTURES --> replacing textures with edited vanilla textures works, but adding new textures crashes the game for unknown reasons
            TEXTURES --> will other textures also "drift" if they contain the string "T_WATER..."? (code has beenimplemented, needs to be tested)
            WALL --> is there a way to enable collision on both sides of a wall? (probably not)
            WALL --> re-implement "wall_side"
            BRIDGE --> fix Bridge setting                   
            HUDMAP --> fix/automate (correct) polygon alignment
            HUDMAP --> color fill certain Polygons (e.g. Blue for Water, Green for Grass) - need to retrieve/match polygon Bound Number
            HUDMAP --> debug JPG should be based on the Bound Number, not on standard enumeration
            BAI --> fix AI, path setting is working, but AI (cops, traffic, etc) still does not spawn/work (Open1560 related)
            BMS --> export "cache_size" variable correctly
            BMS --> add flashing texturs (e.g. airport lights at Meigs Field, "fxltglow") see notes: GLOW AIRPORT.txt (didn't work so far)
            FCD --> test and document flag behavior
            FCD --> investigate Sides and Scales effect
            FCD --> make a screenshot of each facade in the game for reference for the Useful Documents folder
            FCD --> enable diagonal Facade setting
            BNG --> add more prop pictures in Useful Documents (e.g. bridge04, brigdebuild, etc)
            BNG --> investigate Custom Prop Editor
            BNG --> investigate breakable parts in .MMBANGERDATA
            RACES --> the current max number of races per type is 15, can we increase this?
            DEBUG --> add debug BMS (textures)
            OPEN1560 --> add (forked) updated Open1560
            """               
            
################################################################################################################               
################################################################################################################        

# Simplify Struct Library Usage
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
        
    def __repr__(self, round_values=True):
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
        write_pack(f, '<HBB4H', self.cell_id, self.mtl_index, self.flags, *self.vert_indices)

        for edge in self.plane_edges:
            edge.write(f)
            
        self.plane_n.write(f)
        write_pack(f, '<f', self.plane_d)
   
    def __repr__(self, round_values=True):
        vertices_coordinates = [bnd.vertices[index] for index in self.vert_indices]
        plane_d_str = f'{round(self.plane_d, 2):.2f}' if round_values else f'{self.plane_d:f}'

        return f'''
Polygon
Cell ID: {self.cell_id}
Material Index: {self.mtl_index}
Flags: {self.flags}
Vertices Indices: {self.vert_indices}
Vertices Coordinates: {vertices_coordinates}
Plane Edges: {self.plane_edges}
Plane N: {self.plane_n}
Plane D: [{plane_d_str}]
        '''
        
        
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
    def read(cls, f: BinaryIO) -> 'BND':        
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
    
    def to_file(self, f: BinaryIO) -> None:
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
                
    # Write BND TEXT data
    def write_to_file(self, file_name: str, debug_bnd: bool = False) -> None:
        if debug_bnd:
            with open(file_name, 'w') as f:
                f.write(str(self))
                
    def __repr__(self) -> str:
        return f'''

BND
Magic: {self.magic}
Offset: {self.offset}
XDim: {self.x_dim}
YDim: {self.y_dim}
ZDim: {self.z_dim}
Center: {self.center}
Radius: {self.radius}
Radius_sqr: {self.radius_sqr}
BBMin: {self.bb_min}
BBMax: {self.bb_max}
Num Verts: {self.num_verts}
Num Polys: {self.num_polys}
Num Hot Verts1: {self.num_hot_verts1}
Num Hot Verts2: {self.num_hot_verts2}
Num Edges: {self.num_edges}
XScale: {self.x_scale}
ZScale: {self.z_scale}
Num Indices: {self.num_indices}
Height Scale: {self.height_scale}
Cache Size: {self.cache_size}
Vertices: {self.vertices}
Polys: {self.polys}
    '''


class BMS:
    def __init__(self, Magic: str, VertexCount: int, AdjunctCount: int, SurfaceCount: int, IndicesCount: int,
                 Radius: float, Radiussq: float, BoundingBoxRadius: float,
                 TextureCount: int, Flags: int, StringName: List[str], Coordinates: List[Vector3],
                 TextureDarkness: List[int], TexCoords: List[float], Enclosed_shape: List[int],
                 SurfaceSides: List[int], IndicesSides: List[List[int]]) -> None:

        self.Magic = Magic
        self.VertexCount = VertexCount
        self.AdjunctCount = AdjunctCount
        self.SurfaceCount = SurfaceCount
        self.IndicesCount = IndicesCount
        self.Radius = Radius
        self.Radiussq = Radiussq
        self.BoundingBoxRadius = BoundingBoxRadius
        self.TextureCount = TextureCount
        self.Flags = Flags
        self.StringName = StringName
        self.Coordinates = Coordinates
        self.TextureDarkness = TextureDarkness
        self.TexCoords = TexCoords  
        self.Enclosed_shape = Enclosed_shape  
        self.SurfaceSides = SurfaceSides
        self.IndicesSides = IndicesSides
        
    def to_file(self, file_name: str) -> None:
        with open(file_name, 'wb') as f:
            write_pack(f, '16s', self.Magic.encode('utf-8').ljust(16, b'\x00'))
            write_pack(f, '4I', self.VertexCount, self.AdjunctCount, self.SurfaceCount, self.IndicesCount)
            write_pack(f, '3f', self.Radius, self.Radiussq, self.BoundingBoxRadius)
            write_pack(f, 'bb', self.TextureCount, self.Flags)
            f.write(b'\x00' * 6) # cache?

            for StringName in self.StringName:
                write_pack(f, '32s', StringName.encode('utf-8').ljust(32, b'\x00'))
                f.write(b'\x00' * (4 * 4))

            for coordinate in self.Coordinates:
                write_pack(f, '3f', coordinate.x, coordinate.y, coordinate.z)

            write_pack(f, str(self.AdjunctCount) + 'b', *self.TextureDarkness)
            write_pack(f, str(self.AdjunctCount * 2) + 'f', *self.TexCoords)            
            write_pack(f, str(self.AdjunctCount) + 'H', *self.Enclosed_shape)
            write_pack(f, str(self.SurfaceCount) + 'b', *self.SurfaceSides)

            for indices_side in self.IndicesSides:
                write_pack(f, str(len(indices_side)) + 'H', *indices_side)

################################################################################################################               
################################################################################################################       
   
#! INITIALIZATIONS | do not change
vertices = []
all_polygons_picture = []
poly_filler = Polygon(0, 0, 0, [0, 0, 0, 0], [Vector3(0, 0, 0) for _ in range(4)], Vector3(0, 0, 0), [0.0], 0)
polys = [poly_filler]

target_fcd_dir = os.path.join(os.getcwd(), "SHOP", "CITY")

resources_folder = os.path.join(os.getcwd(), "RESOURCES")
physics_folder = os.path.join(os.getcwd(), "SHOP", "MTL")
os.makedirs(physics_folder, exist_ok=True)
input_physics_file = os.path.join(resources_folder, "input_PHYSICS.DB")
output_physics_file = "physics.db"

################################################################################################################               

# Handle Texture Mapping for BMS files
def compute_tex_coords(mode: str = "H", repeat_x: int = 1, repeat_y: int = 1, tilt: float = 0,
                       angle_degrees: Union[float, Tuple[float, float]] = (45, 45),
                       custom: Optional[List[float]] = None) -> List[float]:
    
    def tex_coords_rotating_repeating(repeat_x: int, repeat_y: int, angle_degrees: Tuple[float, float]) -> List[float]:
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
    
    # Horizontal
    if mode == "H" or mode == "horizontal":
        return [0, 0, 0, 1, 1, 1, 1, 0]
    elif mode == "H.f" or mode == "horizontal_flipped":
        return [0, 1, 0, 0, 1, 0, 1, 1]
    
    # Vertical
    elif mode == "V" or mode == "vertical":
        return [0, 0, 1, 0, 1, 1, 0, 1]
    elif mode == "V.f" or mode == "vertical_flipped":
        return [1, 0, 0, 0, 0, 1, 1, 1]
    
    # Horizontal Repeated
    elif mode == "r.H" or mode == "repeating_horizontal":
        return [0, 0, 0, repeat_y, repeat_x, repeat_y, repeat_x, 0]
    elif mode == "r.H.f" or mode == "repeating_horizontal_flipped":
        return [0, repeat_y, 0, 0, repeat_x, 0, repeat_x, repeat_y]
    
    # Vertical Repeated
    elif mode == "r.V" or mode == "repeating_vertical":
        return [0, 0, repeat_y, 0, repeat_y, repeat_x, 0, repeat_x]
    elif mode == "r.V.f" or mode == "repeating_vertical_flipped":
        return [repeat_y, 0, 0, 0, 0, repeat_x, repeat_y, repeat_x]
    
    # Check
    elif mode == "r.r" or mode == "rotating_repeating":
        return tex_coords_rotating_repeating(repeat_x, repeat_y, angle_degrees)
    elif mode == "custom":
        if custom is None:
            raise ValueError("Custom TexCoords must be provided for mode 'custom'")
        return custom
    elif mode == "combined":
        return [0, 0, 1, 0, 1, 1 + tilt, 0, 2]
    else:
        raise ValueError(f"""
                         Invalid mode '{mode}'.
                         Allowed values are: 
                         'H', 'horizontal', 'H.f', 'horizontal_flipped',
                         'V', 'vertical', 'V.f', 'vertical_flipped', 'r.H', 'repeating_horizontal',
                         'r.H.f', 'repeating_horizontal_flipped', 'r.V', 'repeating_vertical',
                         'r.V.f', 'repeating_vertical_flipped', 'r.r', 'rotating_repeating',
                         'custom', and 'combined'
                         """)
        
# SAVE BMS
def save_bms(
    texture_name, texture_indices=[1], vertices=vertices, polys=polys, 
    texture_darkness=None, TexCoords=None, exclude=False, tex_coord_mode=None, 
    tex_coord_params=None, randomize_textures=randomize_textures, 
    randomize_texture_names=randomize_texture_names):
        
    poly = polys[-1]  # Get the last polygon added
    bound_number = poly.cell_id
    
    # Randomize Textures (optional)
    if randomize_textures and not exclude:
        texture_name = [random.choice(randomize_texture_names)]
    
    # Create correct Water BMS
    if any(name.startswith("T_WATER") for name in texture_name):
        bms_filename = "CULL{:02d}_A2.bms".format(bound_number)
    else:
        bms_filename = "CULL{:02d}_H.bms".format(bound_number)
        
    if tex_coord_mode is not None:
        if tex_coord_params is None:
            tex_coord_params = {}
        TexCoords = compute_tex_coords(tex_coord_mode, **tex_coord_params)
        
    single_poly = [poly_filler, poly]
    
    # Create BMS
    bms = create_bms(vertices, single_poly, texture_indices, texture_name, texture_darkness, TexCoords)
    bms.to_file(bms_filename)
             
# Create BMS      
def create_bms(vertices, polys, texture_indices, texture_name: List[str], texture_darkness=None, TexCoords=None):
    shapes = []
    for poly in polys[1:]:  # Skip the first filler polygon
        vertex_coordinates = [vertices[idx] for idx in poly.vert_indices]
        shapes.append(vertex_coordinates)
    
    # DEFAULT BMS VALUES, do not change
    magic, flags, radius, radiussq, bounding_box_radius = "3HSM", 3, 0.0, 0.0, 0.0  
    texture_count = len(texture_name)
    coordinates = [coord for shape in shapes for coord in shape]
    vertex_count = len(coordinates)
    adjunct_count = len(coordinates)
    surface_count = len(texture_indices)            
    indices_count = surface_count * 4
    enclosed_shape = list(range(adjunct_count))

    # Texture Darkness and TexCoords        
    if texture_darkness is None:
        texture_darkness = [2] * adjunct_count # 2 is normal texture brightness 
    if TexCoords is None:
        TexCoords = [0.0 for _ in range(adjunct_count * 2)]

    # Create list of Indices Sides, one for each shape
    indices_sides = []
    index_start = 0
    for shape in shapes:
        shape_indices = list(range(index_start, index_start + len(shape)))
        indices_sides.append(shape_indices)
        index_start += len(shape)
        
    return BMS(magic, vertex_count, adjunct_count, surface_count, indices_count, 
               radius, radiussq, bounding_box_radius, 
               texture_count, flags, texture_name, coordinates, texture_darkness, TexCoords, enclosed_shape, texture_indices, indices_sides)

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

# Sort BND Vertices Coordinates
def sort_coordinates(vertex_coordinates):
    max_x_coord = max(vertex_coordinates, key=lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key=lambda coord: coord[0])
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key=lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key=lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key=lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key=lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]

def compute_plane_edges(vertex_coordinates):
    dir_coord_1 = Vector3(-1, 0, -vertex_coordinates[0][0])
    dir_coord_2 = Vector3(0, 1, vertex_coordinates[1][2])
    dir_coord_3 = Vector3(1, 0, vertex_coordinates[2][0])
    dir_coord_4 = Vector3(0, -1, -vertex_coordinates[3][2])

    return [dir_coord_1, dir_coord_2, dir_coord_3, dir_coord_4]

def compute_plane_params(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, p4: np.ndarray) -> Tuple[np.ndarray, float]:
    v1 = np.subtract(p2, p1)
    v2 = np.subtract(p3, p1)

    planeN = np.cross(v1, v2)
    planeN = planeN / np.linalg.norm(planeN)

    planeD = -np.dot(planeN, p1)

    planeN = np.round(planeN, 3)
    planeD = round(planeD, 3)

    return planeN, planeD

#TODO re-implement WALL_SIDE
# Create and Append Polygons
def create_polygon(
    bound_number, material_index, vertex_coordinates, 
    plane_edges=None, flags=None, 
    vertices=vertices, polys=polys, sort_vertices=True, cell_type=0):
            
    # Flags
    if flags is None:
        flags = 6 if len(vertex_coordinates) == 4 else (3 if len(vertex_coordinates) == 3 else None)
        if flags is None:
            raise ValueError("Unsupported number of Vertices. You must either set 3 or 4 coordinates.")
        elif flags == 3:
            raise ValueError("Triangles are not supported yet. This feature is currently under construction.")

    # # Vertex indices
    base_vertex_index = len(vertices)

    # Sorting (currently desired for all polygons)
    if sort_vertices: 
        sorted_vertices = sort_coordinates(vertex_coordinates)
    else:              
        sorted_vertices = vertex_coordinates 

    new_vertices = [Vector3(*coord) for coord in sorted_vertices]
    vertices.extend(new_vertices)
    vert_indices = [base_vertex_index + i for i in range(len(new_vertices))]
    
    # Plane parameters
    plane_n, plane_d = compute_plane_params(*vertex_coordinates[:4])
    plane_n = Vector3(*plane_n)
    
    if plane_edges is None:
        plane_edges = compute_plane_edges(sorted_vertices)  
        
    # Finalize Polygon
    poly = Polygon(bound_number, material_index, flags, vert_indices, plane_edges, plane_n, plane_d, cell_type)
    polys.append(poly)
    
    # Create JPG (for the HUD)
    all_polygons_picture.append(vertex_coordinates)
           
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
    
    For the Material Index, keep in mind: 0 = Road, 87 = Grass, 91 (Water)        
    Note that you can also set custom Materials properties elsewhere in the script
    
    Texture (UV) mapping examples:
    TexCoords=compute_tex_coords(mode="v")
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=4, repeat_y=2))
    TexCoords=compute_tex_coords(mode="r.r", repeat_x=3, repeat_y=3, angle_degrees=(45, 45))) // unfinished
    
    Allowed values are: 
    'H', 'horizontal', 'H.f', 'horizontal_flipped',
    'V', 'vertical', 'V.f', 'vertical_flipped', 'r.H', 'repeating_horizontal',
    'r.H.f', 'repeating_horizontal_flipped', 'r.V', 'repeating_vertical',
    'r.V.f', 'repeating_vertical_flipped', 'r.r', 'rotating_repeating',
    'custom', and 'combined'
    
    Cell types:
    1 = Tunnel (Echo, No Lighting, No Reflections, No Ptx)
    2 = Indoors
    200 = No Skids
    
    Once functional AI is implemented, the road_type / bound_number might matter, here is the list:
    Open Areas: 0-199
    Roads: 201-859
    Intersections: 860+
    """
        
# Start_Area
create_polygon(
    bound_number = 1,
    material_index = 0,
    cell_type = 1,
    vertex_coordinates=[
        (-50.0, 0.0, 70.0),
        (50.0, 0.0, 70.0),
        (50.0, 0.0, -70.0),
        (-50.0, 0.0, -70.0)])

save_bms(
    texture_name = ["R6"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=10, repeat_y=10))

# Grass_Area    
create_polygon(
	bound_number = 2,
	material_index = 87,
	vertex_coordinates=[
		(-50.0, 0.0, -70.0),
		(50.0, 0.0, -70.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)])

save_bms(
    texture_name = ["24_GRASS"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=10, repeat_y=10))

# No_Friction
create_polygon(
	bound_number = 3,
	material_index = 98,
	vertex_coordinates=[
		(-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)])

save_bms(
    texture_name = ["SNOW"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=10, repeat_y=10))

# Wood_Area
create_polygon(
	bound_number = 4,
	material_index = 0,
	vertex_coordinates=[
		(50.0, 0.0, 70.0),
		(140.0, 0.0, 70.0),
		(140.0, 0.0, -70.0),
		(50.0, 0.0, -70.0)])

save_bms(
    texture_name = ["T_WOOD"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=10, repeat_y=10))

# Barricades_Area  
create_polygon(
	bound_number = 5,
	material_index = 0,
	vertex_coordinates=[
		(50.0, 0.0, -70.0),
		(140.0, 0.0, -70.0),
		(140.0, 0.0, -140.0),
		(50.0, 0.0, -140.0)])

save_bms(
    texture_name = ["T_BARRICADE"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=50, repeat_y=50))

# Water_Area
create_polygon(
	bound_number = 6,
	material_index = 91,
	vertex_coordinates=[
		(50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)])

save_bms(
    texture_name = ["T_WATER"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=10, repeat_y=10))

# Hill
create_polygon(
	bound_number = 7,
	material_index = 0,
	vertex_coordinates=[
		(-50.0, 0.0, -210.0),
		(50.0, 0.0, -210.0),
		(50.0, 300.0, -1000.0),
		(-50.0, 300.0, -1000.0)])

save_bms(
    texture_name = ["T_WATER"], 
    TexCoords=compute_tex_coords(mode="r.V", repeat_x=10, repeat_y=100))

################################################################################################################               
################################################################################################################ 

# Create BND file
bnd_hit_id = f"{city_name}_HITID.BND"
bnd_hit_id_text = f"{city_name}_HITID_debug.txt"

def create_bnd(vertices, polys, city_name, debug_bnd):
    bnd = initialize_bnd(vertices, polys)
    
    with open(bnd_hit_id, "wb") as f:
        bnd.to_file(f)
        
    bnd.write_to_file(bnd_hit_id_text, debug_bnd)
    
# Create SHOP and FOLDER structure   
def create_folders(city_name):
    os.makedirs("build", exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BMP16"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "TEX16O"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "TUNE"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "MTL"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BMS", f"{city_name}CITY"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BMS", f"{city_name}LM"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BND", f"{city_name}CITY"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BND", f"{city_name}LM"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "CITY", f"{city_name}"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "RACE", f"{city_name}"), exist_ok=True)
    
    # Write City Info file
    with open(os.path.join("SHOP", "TUNE", f"{city_name}.CINFO"), "w") as f:
        localized_name = race_locale_name
        map_name = city_name.lower()
        race_dir = city_name.lower()        
        f.write(f"LocalizedName={localized_name}\n")
        f.write(f"MapName={map_name}\n")
        f.write(f"RaceDir={race_dir}\n")
        f.write(f"BlitzCount={len(blitz_waypoints)}\n")
        f.write(f"CircuitCount={len(circuit_waypoints)}\n")
        f.write(f"CheckpointCount={len(checkpoint_waypoints)}\n")
        blitz_race_names_str = '|'.join(blitz_race_names)
        circuit_race_names_str = '|'.join(circuit_race_names)
        checkpoint_race_names_str = '|'.join(checkpoint_race_names)
        f.write(f"BlitzNames={blitz_race_names_str}\n")
        f.write(f"CircuitNames={circuit_race_names_str}\n")
        f.write(f"CheckpointNames={checkpoint_race_names_str}\n")
        
def move_custom_textures(): 
    # Move Custom Textures to TEX16O folder
    custom_textures_path = os.path.join(os.getcwd(), "ADD_Custom_Textures")
    if os.path.exists(custom_textures_path):
        destination_tex16o_path = os.path.join(os.getcwd(), "SHOP", "TEX16O")
        os.makedirs(destination_tex16o_path, exist_ok=True)

        files = os.listdir(custom_textures_path)
        for custom_texs in files:
            source = os.path.join(custom_textures_path, custom_texs)
            destination = os.path.join(destination_tex16o_path, custom_texs)
            shutil.copy(source, destination)
        
# Move contents of 'dev' folder to user's MM1 folder     
def move_dev(destination_folder, city_name):
    current_folder = os.getcwd()
    dev_folder_path = os.path.join(current_folder, 'dev')
    
    if os.path.exists(dev_folder_path):
        destination_path = os.path.join(destination_folder, 'dev')
        
        if os.path.exists(destination_path):
            shutil.rmtree(destination_path)
            
        shutil.copytree(dev_folder_path, destination_path)
        
    # Delete City's AI .map and .roads files after they have been moved to the user's MM1 folder
    city_folder_path = os.path.join(dev_folder_path, 'CITY', city_name)
    if os.path.exists(city_folder_path):
        shutil.rmtree(city_folder_path)

# Move Open1560 files to the user's MM1 folder                       
def move_open1560(destination_folder):
    current_folder = os.getcwd()
    open1560_folder_path = os.path.join(current_folder, 'Installation_Instructions', 'Open1560')
    
    if os.path.exists(open1560_folder_path):
        
        for file_name in os.listdir(open1560_folder_path):
            source_file_path = os.path.join(open1560_folder_path, file_name)
            destination_file_path = os.path.join(destination_folder, file_name)
            
            if os.path.isfile(source_file_path):
                if os.path.isfile(destination_file_path):
                    
                    # Compare last modified time of source and mm1 folder
                    if os.path.getmtime(source_file_path) != os.path.getmtime(destination_file_path):
                        shutil.copy2(source_file_path, destination_file_path)
                else:
                    # If destination file does not exist, copy the file.
                    shutil.copy2(source_file_path, destination_file_path)
                                      
# Distribute generated files
def distribute_files(city_name, bnd_hit_id, num_blitz, blitz_waypoints, num_circuit, 
                               circuit_waypoints, num_checkpoint, checkpoint_waypoints, all_races_files=True):

    bms_files = []
    bms_a2_files = set()
    for file in os.listdir():
        if file.endswith(".bms"):
            bound_number = int(re.findall(r'\d+', file)[0])
            bms_files.append(bound_number)
            if file.endswith("_A2.bms"):
                bms_a2_files.add(bound_number)
            if bound_number < 200:
                shutil.move(file, os.path.join("SHOP", "BMS", f"{city_name}LM", file))
            else:
                shutil.move(file, os.path.join("SHOP", "BMS", f"{city_name}CITY", file))
        
    for file in os.listdir():
        if file.endswith(".bnd"):
            shutil.move(file, os.path.join("SHOP", "BND", file))
    shutil.move(bnd_hit_id, os.path.join("SHOP", "BND", bnd_hit_id))       
        
    # Create WAYPOINTS files
    race_prefixes = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]
    if num_checkpoint > len(race_prefixes):
        raise ValueError("Number of Checkpoint races cannot be more than 12")
    
    for race_type, race_description, prefix, num_files, race_waypoints in [("BLITZ", "Blitz", "ABL", num_blitz, blitz_waypoints), 
                                                                           ("CIRCUIT", "Circuit", "CIR", num_circuit, circuit_waypoints), 
                                                                           ("RACE", "Checkpoint", "RACE", num_checkpoint, checkpoint_waypoints)]:
        
        for i in range(num_files):
            file_name = f"{race_type}{i}WAYPOINTS.CSV"

            with open(file_name, "w") as f:
                ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[((n//10%10!=1)*(n%10<4)*n%10)::4])
                f.write(f"# This is your {ordinal(i)} {race_description} race Waypoint file\n")

                for waypoint in race_waypoints[i][:-1]:  # Exclude the last item, which are other parameters
                    waypoint_line = ', '.join(map(str, waypoint))
                    waypoint_line += ",0,0,\n"
                    f.write(waypoint_line)

            shutil.move(file_name, os.path.join("SHOP", "RACE", f"{city_name}", file_name))

        # Create MM_DATA files
        mm_file_name = f"MM{race_type}DATA.CSV"
        mm_data_comment_line = "Description, CarType, TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit, Difficulty, CarType, TimeofDay, Weather, Opponents,       Cops, Ambient, Peds, NumLaps, TimeLimit, Difficulty\n"
        car_type_na, difficulty_na, opponent_na, num_laps_checkpoint_na, time_limit_na = 0, 1, 99, 99, 99

        with open(mm_file_name, "w") as f:
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
                    # Write the RACE prefixes (ASP1", "ASP2", "ASP3", "ASU1", "ASU2" ... etc)
                    f.write(f"{race_prefixes[i]}, {race_data_str}\n")
                else:
                    f.write(f"{prefix}{i}, {race_data_str}\n")

        destination_path = os.path.join("SHOP", "RACE", city_name, mm_file_name)
        shutil.move(mm_file_name, destination_path)

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

        shutil.move(cnr_csv_file, os.path.join("SHOP", "RACE", f"{city_name}", cnr_csv_file))

    # Create OPPONENT files
    if all_races_files:
        for race_type, prefix, num_files in [("BLITZ", "B", num_blitz), ("CIRCUIT", "C", num_circuit), ("RACE", "R", num_checkpoint)]:
            for race_index in range(num_files):
                for opp_index in range(1, aimap_num_opponents + 1):
                    opp_file_name = f"OPP{opp_index}{race_type}{race_index}.{prefix}{race_index}"
                    
                    opp_comment_line = f"# This is your Opponent file for opponent number {opp_index}, in race {race_type}{race_index}"
                    with open(opp_file_name, "w") as f:
                        f.write(opp_comment_line)
                    shutil.move(opp_file_name, os.path.join("SHOP", "RACE", f"{city_name}", opp_file_name)) 
                    
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

                    f.write(aimap_content.strip())
                    
                    for opp_index in range(1, aimap_num_opponents + 1):
                        f.write(f"{aimap_opponent_car} OPP{opp_index}{race_type}{race_index}.{prefix}{opp_index}\n")
                        
                shutil.move(aimap_file_name, os.path.join("SHOP", "RACE", f"{city_name}", aimap_file_name))
    
    # Create CELLS file
    cells_file = os.path.join("SHOP", "CITY", f"{city_name}.CELLS")
    with open(cells_file, "w") as f:
        f.write(f"{len(bms_files)}\n")  # total number of cells
        f.write(str(max(bms_files) + 1000) + "\n")  # max cell number + 1000 (mandatory)

        sorted_bms_files = sorted(bms_files)
        for bound_number in sorted_bms_files:
            
            # Retrieve corresponding polygon's cell type
            cell_type = None
            for poly in polys:
                if poly.cell_id == bound_number:
                    cell_type = poly.cell_type
                    break

            if cell_type is None:
                cell_type = 0
            
            # Write CELLS data
            if bound_number in bms_a2_files:
                row = f"{bound_number},32,{cell_type},0\n"
            else:
                row = f"{bound_number},8,{cell_type},0\n"
            f.write(row)
    
    # Copy CMD.exe, RUN.bat, and SHIP.bat to SHOP folder
    for file in os.listdir("angel"):
        if file in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(os.path.join("angel", file), os.path.join("SHOP", file))
                
# Create ANIM (plane and eltrain)
def create_anim(city_name, anim_data, set_anim=False):
    if set_anim:
        output_folder_anim = os.path.join("SHOP", "CITY", f"{city_name}")
        main_anim_file = os.path.join(output_folder_anim, "ANIM.CSV")

        # Create ANIM.CSV file and write anim names
        with open(main_anim_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for obj in anim_data.keys():
                writer.writerow([f"anim_{obj}"])

        # Create Individual ANIM files and write Coordinates
        for obj, coordinates in anim_data.items():
            file_name = os.path.join(output_folder_anim, f"ANIM_{obj.upper()}.CSV")
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                if coordinates:
                    for coordinate in coordinates:
                        writer.writerow(coordinate)
              
# Create AR file and delete folders
def create_ar(city_name, destination_folder, delete_shop=False):
    os.chdir("SHOP")
    ar_command = f"CMD.EXE /C run !!!!!{city_name}_City"
    subprocess.run(ar_command, shell=True)
    os.chdir("..")  
    
    for file in os.listdir("build"):
        if file.endswith(".ar") and file.startswith(f"!!!!!{city_name}_City"):
            shutil.move(os.path.join("build", file), os.path.join(destination_folder, file))
            
    # Delete the build folder
    try:
        shutil.rmtree("build")
    except Exception as e:
        print(f"Failed to delete the build directory. Reason: {e}")
    
    # Delete the SHOP folder
    if delete_shop:
        try:
            shutil.rmtree("SHOP")
        except Exception as e:
            print(f"Failed to delete the SHOP directory. Reason: {e}")
                    
# Create JPG of all Polygon shapes
def plot_polygons(show_label=False, plot_picture=False, export_jpg=False, 
                  x_offset=0, y_offset=0, line_width=1, background_color='black', debug_hud=False):
    
    # Setup
    output_folder_city = os.path.join("SHOP", "BMP16")
    output_folder_cwd = os.getcwd() 
    
    global all_polygons_picture
    
    def draw_polygon(ax, polygon, color, label=None, add_label=False):
        xs, ys = zip(*[(point[0], point[2]) for point in polygon])
        xs, ys = xs + (xs[0],), ys + (ys[0],)
        ax.plot(xs, ys, color=color, linewidth=line_width)
        
        if add_label: # control label addition
            center = calculate_center_tuples(polygon)
            ax.text(center[0], center[2], label, color='white', ha='center', va='center', fontsize=4.0)

    if plot_picture or export_jpg:
        fig, ax = plt.subplots()
        ax.set_facecolor(background_color)

        # Sort the vertex_coordinates in all_polygons_picture
        all_polygons_picture = [sort_coordinates(polygon) for polygon in all_polygons_picture]

        # Enumeration should be based on the bound_number
        for i, polygon in enumerate(all_polygons_picture):
            draw_polygon(ax, polygon, color=f'C{i}', label=f'{i+1}' if show_label else None, add_label=False) # note: do not remove "C" from "C{i}"
        ax.set_aspect('equal', 'box')
        
        if show_label:
            plt.legend()
            
        if plot_picture:
            plt.show()
        
        if export_jpg:
            ax.axis('off')
            trans = mtransforms.Affine2D().translate(x_offset, y_offset) + ax.transData
            for line in ax.lines:
                line.set_transform(trans)
                      
            # Save JPG 640 and 320 Pictures
            plt.savefig(os.path.join(output_folder_city, f"{city_name}.640.JPG"), dpi=1000, bbox_inches='tight', pad_inches=0.01, facecolor=background_color)
            plt.savefig(os.path.join(output_folder_city, f"{city_name}.320.JPG"), dpi=1000, bbox_inches='tight', pad_inches=0.01, facecolor=background_color)

            if debug_hud:
                ax.cla()
                ax.set_facecolor(background_color)
                for i, polygon in enumerate(all_polygons_picture):
                    draw_polygon(ax, polygon, color=f'C{i}', label=f'{i+1}' if show_label else None, add_label=True)
                plt.savefig(os.path.join(output_folder_cwd, f"{city_name}_HUD_debug.jpg"), dpi=1000, bbox_inches='tight', pad_inches=0.01, facecolor='white')

# Create EXT file            
def create_ext(city_name, polygonz):
    min_x = min(point[0] for polygon in polygonz for point in polygon)
    max_x = max(point[0] for polygon in polygonz for point in polygon)
    min_z = min(point[2] for polygon in polygonz for point in polygon)
    max_z = max(point[2] for polygon in polygonz for point in polygon)

    output_folder_ext = os.path.join("SHOP", "CITY")       
    ext_file = city_name + ".EXT"
    ext_file_path = os.path.join(output_folder_ext, ext_file)
    os.makedirs(output_folder_ext, exist_ok=True)

    with open(ext_file_path, 'w') as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")
       
# Create Bridges       
def create_bridges(all_bridges, set_bridges=False):
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
        
        drawbridge_values = f"""
{bridge_object}, 0, {bridge_offset[0]}, {bridge_offset[1]}, {bridge_offset[2]}, {bridge_facing[0]}, {bridge_facing[1]}, {bridge_facing[2]})
        """
        
        bridge_filler = "tpsone,0,-9999.99,0.0,-9999.99,-9999.99,0.0,-9999.99"

        bridge_data = f"""
DrawBridge{bridge_number}
{','.join(map(str, drawbridge_values))}
    {bridge_filler}
    {bridge_filler}
    {bridge_filler}
    {bridge_filler}
    {bridge_filler}
DrawBridge{bridge_number}
        """
        
        if set_bridges:
            bridge_gizmo = os.path.join("SHOP", "CITY", f"{city_name}.GIZMO")
            with open(bridge_gizmo, "a") as f:
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
    cells, portals = prepare_ptl(polys, vertices)

    with open(f'SHOP/CITY/{city_name}.PTL', 'wb') as f:
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
    def __init__(self, start: Vector3, end: Vector3, name: str):
        self.room = 4       
        self.flags = 0x800  
        self.start = start
        self.end = end
        self.name = name
        
    def __repr__(self):
        return f'''
BinaryBanger
Room: {self.Room}
Flags: {self.Flags}
Start: {self.Start}
End: {self.End}
Name: {self.Name}
    '''
  
class Prop_Editor:
    def __init__(self, filename: str, city_name: str, debug_bng: bool = False):
        self.filename = filename
        self.objects = []
        self.debug_props = debug_props  
        self.debug_filename = f"{city_name}_BNG_debug.txt"
        resources_folder = os.path.join(os.getcwd(), "RESOURCES")
        self.prop_file_path = os.path.join(resources_folder, "Prop_Dimensions_Extracted.txt")
        self.prop_data = self.load_prop_data()            
        
    def load_prop_data(self):
        prop_data = {}
        with open(self.prop_file_path, "r") as f:
            for line in f:
                name, value_x, value_y, value_z = line.split()
                prop_data[name] = Vector3(float(value_x), float(value_y), float(value_z))
        return prop_data
        
    def write_props(self, set_props: bool = False):
        if set_props:
            with open(self.filename, mode="wb") as f:
                write_pack(f, '<I', len(self.objects))
            
                for index, obj in enumerate(self.objects, 1):
                    if self.debug_props:
                        with open(self.debug_filename, "a") as debug_f:
                            debug_f.write(f'''
Prop {index} Data:
Start: {obj.start}
End: {obj.end}
Name: {obj.name}
''')
                        write_pack(
                            f, '<HH3f3f', obj.room, obj.flags, obj.start.x, obj.start.y, obj.start.z, obj.end.x, obj.end.y, obj.end.z)

                        for char in obj.name: 
                            write_pack(f, '<s', bytes(char, encoding='utf8')) 
                        
    # IN DEVELOPMENT      
    def add_props(self, new_objects: List[Dict[str, Union[int, float, str]]]):
        for obj in new_objects:
            offset = Vector3(obj['offset_x'], obj['offset_y'], obj['offset_z'])
            face = Vector3(obj['face_x'], obj['face_y'], obj['face_z'])
            name = obj['name']
            
            separator = obj.get('separator', name)  # default is the name of the object itself if 'separator' not provided
            axis = obj.get('axis', 'x')             # default is 'x' if 'axis' not provided

            # Check if Separator is a string (object name) or a numeric value
            if isinstance(separator, str):
                if separator not in self.prop_data:
                    raise ValueError(f"Separator {separator} not found in prop data.")
                separator_value = self.prop_data[separator][axis]
            else:
                separator_value = separator  # separator is a numeric value

            self.objects.append(BinaryBanger(offset, face, name + "\x00"))

            if name in self.prop_data:
                if 'end_offset_' + axis in obj:
                    num_props = int(abs(obj['end_offset_' + axis] - obj['offset_' + axis]) / separator_value)

                    for i in range(1, num_props):
                        new_offset = Vector3(offset.x, offset.y, offset.z)  # create a new instance with the same coordinates
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
   
prop_file = os.path.join("SHOP", "CITY", f"{city_name}.BNG")  
prop_writer = Prop_Editor(prop_file, city_name, debug_props) 

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
    def from_file(f):
        name = f.read(32).decode("latin-1").rstrip('\x00')
        params = read_unpack(f, '>7f2I')
        velocity = Vector2.read(f)
        ptx_color = Vector3.read(f)

        return Material_Editor(name, *params, velocity, ptx_color)

    @staticmethod
    def readn(f, count):
        return [Material_Editor.from_file(f) for _ in range(count)]

    def to_file(self, f):
        write_pack(f, '>32s', self.name.encode("latin-1").ljust(32, b'\x00'))
        write_pack(f, '>7f2I', self.friction, self.elasticity, self.drag, self.bump_height, self.bump_width, self.bump_depth, self.sink_depth, self.type, self.sound)
        self.velocity.write(f)
        self.ptx_color.write(f)

    @staticmethod
    def read_physics_db(file_name):
        with open(file_name, 'rb') as file:
            count = read_unpack(file, '>I')[0]
            return Material_Editor.readn(file, count)

    @classmethod
    def read_binary(cls, file_name):
        return cls.read_physics_db(file_name)

    @staticmethod
    def write_physics_db(file_name, agi_phys_parameters):
        with open(file_name, 'wb') as f:
            write_pack(f, '>I', len(agi_phys_parameters))
            for param in agi_phys_parameters:
                param.to_file(f)
                
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

# BAI EDITOR CLASS
class BAI_Editor:
    def __init__(self, city_name, streets, ai_map=False):
        self.city_name = f"{city_name}"
        self.streets = streets
                       
        if ai_map:
            self.write_to_file()

    def write_to_file(self):
        self.filepath = os.path.join("dev", "CITY", self.city_name, self.city_name + ".map")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        with open(self.filepath, 'w') as file:
            file.write(self.construct_template())
    
    def construct_template(self):
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
    
    
# Intersection Type Mapping
INTERSECTION_TYPE_MAP = {
    "stop": 0,
    "stoplight": 1,
    "yield": 2,
    "continue": 3}

# Yes/No Mapping
YES_NO_MAP = {
    "no": 0,
    "yes": 1}

# Street File Editor CLASS
class StreetFile_Editor:
    def __init__(self, city_name, street_data, ai_streets=False, reverse=False):
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

        self.intersection_types = [INTERSECTION_TYPE_MAP[typ] for typ in street_data.get("intersection_types", ["continue", "continue"])]
        self.stop_light_positions = street_data.get("stop_light_positions", [(0.0, 0.0, 0.0)] * 4)
        self.stop_light_names = street_data.get("stop_light_names", ["tplttrafc", "tplttrafc"])
        self.traffic_blocked = [YES_NO_MAP[val] for val in street_data.get("traffic_blocked", ["no", "no"])]
        self.ped_blocked = [YES_NO_MAP[val] for val in street_data.get("ped_blocked", ["no", "no"])]
        self.road_divided = YES_NO_MAP[street_data.get("road_divided", "no")]
        self.alley = YES_NO_MAP[street_data.get("alley", "no")]

        if ai_streets:
            self.write_to_file()

    def write_to_file(self):
        self.filepath = os.path.join("dev", "CITY", city_name, self.street_name + ".road")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as file:
            file.write(self.construct_template())

    def construct_template(self):
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

###################################################################################################################
################################################################################################################### 

# FACADE CLASS
class Facade_Editor:
    def __init__(self, room, flags, start, end, sides, scale, name):
        self.room = room
        self.flags = flags
        self.start = start
        self.end = end
        self.sides = sides
        self.scale = scale
        self.name = name

    @classmethod
    def from_file(cls, f):
        room, flags = read_unpack(f, '2H')
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
        return cls(room, flags, start, end, sides, scale, name)

    def to_file(self, f):
        write_pack(f, '2H', self.room, self.flags)
        write_pack(f, '6f', *self.start, *self.end)
        write_pack(f, '3f', *self.sides)
        write_pack(f, 'f', self.scale)
        f.write(self.name.encode('utf-8'))
        f.write(b'\x00')
        
    def __repr__(self):
        return f"""
Facade_Editor
    Room: {self.room}
    Flags: {self.flags}
    Start: {self.start}
    End: {self.end}
    Sides: {self.sides}
    Scale: {self.scale}
    Name: {self.name}
    """
      
def read_facade_scales(file_path):
    scales = {}
    with open(file_path, 'r') as f:
        for line in f:
            facade_name, scale = line.strip().split(": ")
            scales[facade_name] = float(scale)
    return scales
      
def get_coord_from_tuple(coord_tuple, axis):
    axis_dict = {'x': 0, 'y': 1, 'z': 2}
    return coord_tuple[axis_dict[axis]]  
    
def create_facades(filename, facade_params, target_fcd_dir, set_facade=False, debug_facade=False):
    if set_facade:
        facades = []
        axis_dict = {'x': 0, 'y': 1, 'z': 2}
        
        
        cwd = os.getcwd()  # Get the current working directory
        
        scales = read_facade_scales(os.path.join(cwd, 'RESOURCES/FCD_scales.txt')) 
        
        #scales = read_facade_scales('/RESOURCES/FCD_scales.txt')

        for params in facade_params:
            num_facades = math.ceil(abs(get_coord_from_tuple(params['end'], params['axis']) - get_coord_from_tuple(params['start'], params['axis'])) / params['separator'])

            for i in range(num_facades):
                room = params['room']
                flags = params['flags']
                current_start = list(params['start'])
                current_end = list(params['end'])

                shift = params['separator'] * i
                current_start[axis_dict[params['axis']]] += shift
                current_end[axis_dict[params['axis']]] += shift

                current_start = tuple(current_start)
                current_end = tuple(current_end)

                sides = params['sides']
                scale = scales.get(params['facade_name'], params.get('scale', 1.0))
                name = params['facade_name']

                facade = Facade_Editor(room, flags, current_start, current_end, sides, scale, name)
                facades.append(facade)

        with open(filename, mode='wb') as f:
            write_pack(f, '<I', len(facades))
            for facade in facades:
                facade.to_file(f)

        shutil.move(filename, os.path.join(target_fcd_dir, filename))

        if debug_facade:
            debug_filename = filename.replace('.FCD', '_FCD_debug.txt')
            with open(os.path.join(os.getcwd(), debug_filename), mode='w', encoding='utf-8') as f:
                for facade in facades:
                    f.write(str(facade))

###################################################################################################################
################################################################################################################### 
                            
def export_city_vertices(input_bnd: str, output_file_name: str, export_blender: bool = False, run_blender: bool = False) -> None:
    if export_blender: 
        pattern_flags = r"Flags: (\d+)"
        pattern_coords = r"Vertices Coordinates: \[{.*?}\]"

        def all_identical(coords):
            return all(coord == coords[0] for coord in coords)

        flag_counter = defaultdict(int)

        with open(output_file_name, "w") as output_file:
            for txt_file in glob.glob(input_bnd):
                
                with open(txt_file, "r") as input_file:
                    lines = input_file.readlines()

                    flag_value = None

                    for i, line in enumerate(lines):
                        match_flags = re.search(pattern_flags, line)
                        if match_flags:
                            flag_value = int(match_flags.group(1))
                        else:
                            match_coords = re.search(pattern_coords, line)
                            if match_coords:
                                coords = re.findall(r"{.*?}", match_coords.group(0))

                                if flag_value in (0, 1, 2, 8, 9, 10):
                                    coords = coords[:3]
                                elif flag_value in (4, 5, 6):
                                    coords = coords[:4]
                                else:
                                    flag_counter[flag_value] += 1
                                    flag_value = None
                                    continue

                                if not all_identical(coords):
                                    new_line = f"Vertices Coordinates: {', '.join(coords)}"
                                    output_file.write(new_line + "\n")
                                flag_value = None    
        if run_blender:                  
            # After the loop, look for any Blender file in the cwd
            for file in os.listdir():
                if file.endswith(".blend"):
                    print(f"Opening {file} with Blender...")
                    subprocess.run([blender_exe, file])
                    break
            else:
                print("No Blender file found in the current directory.")
                
###################################################################################################################
###################################################################################################################  

# Write COMMANDLINE
def create_commandline(city_name: str, destination_folder: str):
    city_name = city_name.lower()
    cmd_file = "commandline.txt"
    cmd_params = f"-path ./dev -allrace -allcars -f -heapsize 499 -multiheap -maxcops 100 -speedycops -l {city_name}"
    with open(cmd_file, "w") as file:
        file.write(cmd_params)

    shutil.move(cmd_file, os.path.join(destination_folder, cmd_file))
        
# Start GAME
def start_game(destination_folder, play_game=False):
    mm1_exe = "Open1560.exe"
    game_path = os.path.join(destination_folder, mm1_exe)
    if play_game:
        subprocess.run(game_path, cwd=destination_folder, shell=True)
        
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
   
# SET FACADES
fcd_one = {
	'room': 1,
	'flags': 1,
	'start': (-80, 0.0, -30.0),
	'end': (80, 0.0, -30.0),
	'sides': (0,0,0.000000),
	'separator': 80, 
	'facade_name': "dfhotel01",
	'scale': 30.0, # can be omitted in later versions (i.e. use scale of input object)
	'axis': 'x'}

# Pack all Facades for processing
fcd_list = [fcd_one]

###################################################################################################################

# SET AI PATHS

# The following variables are optional: 
# Intersection_type, defaults to: "continue"
# Stop_light_names, defaults to: "tplttrafc"
# Stop_light_positions, defaults to: (0,0,0)
# Traffic_blocked, Ped_blocked, Road_divided, and Alley, all default to: "No"

# Stop lights will only show if the Intersection_type is "stoplight"
# Each lane will automatically have a revered lane added

street_0 = {
    "street_name": "cruise_start",
    "vertices": [
        cruise_start_position,  # you must keep the "second position", otherwise the game will crash
        cruise_start_position]} 
 
street_1 = {
     "street_name": "path_1",
     "vertices": [
         (10.0, 0.0, -20.0),
         (10.0, 0.0, -40.0),
         (10.0, 0.0, -60.0),
         (10.0, 0.0, -80.0)]}

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
    "intersection_types": ["stoplight", "stoplight"],
    "stop_light_names": ["tplttrafcdual", "tplttrafcdual"],
    "stop_light_positions": [
         (-30.0, 0.0, -20.0),
         (-30.0, 0.0, -20.1),
         (-10.0, 0.0, -20.0),
         (-10.0, 0.0, -20.1)
         ],
    "traffic_blocked": ["no", "no"],
    "ped_blocked": ["no", "no"],
    "road_divided": "no",
    "alley": "no"
}

# Pack all AI paths for processing
street_data = [street_0, street_1, street_2]

################################################################################################################               

# SET PROPS
# Single Prop (China Gate)
prop_1 = {'offset_x': 10, 
          'offset_y': 0.0, 
          'offset_z': -80, 
          'face_x': 10000, 
          'face_y': 0.0, 
          'face_z': -80, 
          'name': 'cpgate'}

# Multiple props (TP Trailer)
prop_2 = {'offset_x': -10, 
          'offset_y': 0.0, 
          'offset_z': -40, 
          'name': 'tp_trailer', 
          
          'end_offset_z': 40, 
          'separator': 5, 
          'axis': 'z',

          'face_x': 10, 
          'face_y': 0.0, 
          'face_z': -40000}

# Pack all Props for processing
prop_list = [prop_1, prop_2]

################################################################################################################     

# SET MATERIAL PROPERTIES
# available numbers: 94, 95, 96, 97, 98, also see: https://tinyurl.com/y2d56pa6
set_material_index = 98

# See: /Useful documents/PHYSICS.DB_extracted.txt for more information
new_properties = {
    "friction": 0.01, 
    "elasticity": 0.01, 
    "drag": 0.01}

################################################################################################################   

# Call FUNCTIONS
print("\n===============================================\n")
print("Generating " + f"{race_locale_name}...")
print("\n===============================================\n")

# Material related
output_physics_file = "physics.db"
read_materials = Material_Editor.read_binary(input_physics_file)
for prop in ["friction", "elasticity", "drag"]:
    setattr(read_materials[set_material_index - 1], prop, new_properties[prop])
Material_Editor.write_physics_db(output_physics_file, read_materials)
shutil.move(output_physics_file, os.path.join(physics_folder, output_physics_file))

# AI related
street_names = []
for data in street_data:
    creator = StreetFile_Editor(city_name, data, ai_streets, reverse=True)
    street_names.append(data["street_name"])
BAI_Editor(city_name, street_names, ai_map)

# Main functions
create_folders(city_name)
create_bnd(vertices, polys, city_name, debug_bnd)
distribute_files(city_name, bnd_hit_id, 
                           len(blitz_waypoints), blitz_waypoints, len(circuit_waypoints), 
                           circuit_waypoints, len(checkpoint_waypoints), checkpoint_waypoints, all_races_files=True)

move_open1560(mm1_folder)
move_dev(mm1_folder, city_name)
move_custom_textures()

create_ext(city_name, all_polygons_picture) 
create_anim(city_name, anim_data, set_anim)   
create_bridges(bridges, set_bridges) 
create_facades(f"{city_name}.FCD", fcd_list, target_fcd_dir, set_facade, debug_facade)
prop_writer.add_props(prop_list)
prop_writer.write_props(set_props)    

# Blender
export_city_vertices(bnd_hit_id_text, bnd_blender_data, export_blender, run_blender)     

# HUD offset for Moronville is approx., x=-22.4, y=-40.7; automated alignment is not implemented yet
plot_polygons(debug_hud=debug_hud, show_label=False, plot_picture=False, export_jpg=True, 
              x_offset=-0.0, y_offset=-0.0, line_width=0.7, 
              background_color='black')

create_ptl(city_name, polys, vertices)
create_ar(city_name, mm1_folder, delete_shop)
create_commandline(city_name, mm1_folder)

print("\n===============================================\n")
print("Succesfully created " + f"{race_locale_name}!")
print("\n===============================================\n")

start_game(mm1_folder, play_game)
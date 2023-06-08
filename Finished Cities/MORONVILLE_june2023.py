def program_introduction(x):
    """
    =====================================================================
    ================= Midtown Madness 1 Map Editor Alpha ================
    
    This Map Editor allows users to create new maps for Midtown Madness 1
                                             Copyright (C) May 2023 Robin

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
    General Public License for more details.

    For more information about GNU see <http://www.gnu.org/licenses/>.
    =====================================================================
    """
    
def moronville(x):
    """
    =====================================================================
    ==================== Midtown Madness 1 Moronville ===================
    
    This is the script input data for the city Moronville in Midtown 
    Madness 1 that was made by Dading. 
    
    Hopefully this gives some insight of how to make your own City.
    
    Feel free to extend or modify the map, or use parts of it in your 
    own city.
    =====================================================================
    """
    

import os
import re
import csv
import math
import struct
import shutil
import random
import subprocess
from typing import List, Dict, Union, Tuple
import matplotlib.pyplot as plt                 
import matplotlib.transforms as mtransforms     


# SETUP I (mandatory)                       Control + F    "city=="  to jump to The City Creation section
city_name = "MoronVille"                    # One word (no spaces)  --- name of the .ar file
race_locale_name = "MoronVille"             # Can be multiple words --- name of the city in Game Menu
shortcut_or_exe_name = "Midtown.exe"        # or Open1560.exe or Midtown.exe
mm1_folder = r"C:\Users\Midtown_Madness_1_Folder" # Path to your MM1 folder

# SETUP II (handy)
play_game=True                 # boot the game immediately after the map is created
delete_shop=False            # shop folder contains all the files that are used to create the .ar (gets deleted ONLY after the .ar is created)

set_facade=True                # change to "True" if you want FACADE
set_props=True                 # change to "True" if you want PROPS

set_anim=False                  # change to "True" if you want ANIM
set_bridges=False               # change to "True" if you want BRIDGES (currently not recommended)

ai_map=False                    # change both to "True" if you want AI paths
ai_streets=True                 # change both to "True" if you want AI paths

debug_bnd=False                 # change to "True" if you want a BND/collision Debug text file
debug_facade=False              # change to "True" if you want a Facade Debug text file
debug_hud=False                 # change to "True" if you want a HUD Debug jpg file

# SETUP III (optional)
# RACE EDITOR | Race names (max is 15 for Blitz & Circuit, and 12 for Checkpoint)
blitz_race_names = ["Just in Time", "The Great Escape"]
circuit_race_names = ["Happy Jumping", "Ice Drift", "Explosion't"]
checkpoint_race_names = ["filler_race"]

# WAYPOINTS          Tabbing / spacing out the Coordinates is optional, but recommended for readability and editing
# Maximum number of blue checkpoints for Blitzes is 11 (including the start and finish checkpoints)
# Blitz 0 WP         x:      y:      z:     rot:    width:  ,0,0, 
blz_0_WP_start =    "0.0,   0.0,    0.1,    5.0,    15.0    ,0,0,"
blz_0_WP_ch1 =      "0.0,   0.0,    -20,    5.0,    15.0    ,0,0,"
blz_0_WP_ch2 =      "0.0,   0.0,    -40,    5.0,    15.0    ,0,0,"
blz_0_WP_ch3 =      "0.0,   0.0,    -60,    5.0,    15.0    ,0,0,"
blz_0_WP_ch4 =      "0.0,   0.0,    -80,    5.0,    15.0    ,0,0,"
blz_0_WP_finish =   "0.0,   0.0,    -99,    5.0,    15.0    ,0,0,"
blz_0_ALL = [blz_0_WP_start, blz_0_WP_ch1, blz_0_WP_ch2, blz_0_WP_ch3, blz_0_WP_ch4, blz_0_WP_finish]

# Blitz 1 WP        x:       y:      z:      rot:     width:  ,0,0, 
blz_1_WP_start =    "0.1,    0.0,    0.1,    90.0,    10.0    ,0,0,"
blz_1_WP_ch1 =      "20.0,   0.0,    0.1,    90.0,    10.0    ,0,0,"
blz_1_WP_ch2 =      "40.0,   0.0,    0.1,    90.0,    10.0    ,0,0,"
blz_1_WP_ch3 =      "60.0,   0.0,    0.1,    90.0,    10.0    ,0,0,"
blz_1_WP_ch4 =      "80.0,   0.0,    0.1,    90.0,    10.0    ,0,0,"
blz_1_WP_finish =   "99.0,   0.0,    0.1,    90.0,    10.0    ,0,0,"
blz_1_ALL = [blz_1_WP_start, blz_1_WP_ch1, blz_1_WP_ch2, blz_1_WP_ch3, blz_1_WP_ch4, blz_1_WP_finish]

# Circuit 0         x:           y:       z:          rot:       width:     ,0,0,
cir_0_start =       "-101.5,    11.5,       0.01,       -180.0,     8.0     ,0,0,"
cir_0_ch1 =         "0.01,      11.5,       101.5,      90,         8.0     ,0,0,"
cir_0_ch2 =         "101.5,     11.5,       0.01,       0.01,       8.0     ,0,0,"
cir_0_ch3 =         "0.01,      11.5,       -101.5,     -90,        8.0     ,0,0,"
cir_0_ALL = [cir_0_start,cir_0_ch1,cir_0_ch2,cir_0_ch3]

# Circuit 1         x:           y:       z:          rot:       width:     ,0,0,
cir_1_start =       "0.01,      15.0,       -55.0,      180.0,      8.0     ,0,0,"
cir_1_ch1 =         "-11.0,     15.0,       0.01,       -90,        8.0     ,0,0,"
cir_1_ch2 =         "-45.0,     25.0,       49.0,       180,        4.0     ,0,0,"
cir_1_ch3 =         "-30.0,     15.0,       85.0,       90,         4.0     ,0,0,"
cir_1_ch4 =         "0.01,      15.0,       70.0,       0.01,       8.0     ,0,0,"
cir_1_ch5 =         "16.0,      15.0,       -4.0,       30.0,       6.0     ,0,0,"
cir_1_ch6 =         "15.0,      15.0,       -85.0,     -90,         4.0     ,0,0,"
cir_1_ALL = [cir_1_start,cir_1_ch1,cir_1_ch2,cir_1_ch3,cir_1_ch4,cir_1_ch5,cir_1_ch6]

# Circuit 2         x:           y:       z:          rot:       width:     ,0,0,
cir_2_start =       "-75.0,     15.0,       0.01,       -90,        8.0     ,0,0,"
cir_2_ch1 =         "-113.0,    6.0,        30.0,       180,        4.0     ,0,0,"
cir_2_ch2 =         "-39.0,     25.0,       45.0,       90,         4.0     ,0,0,"
cir_2_ch3 =         "55.0,      15.0,       45.0,       90,         4.0     ,0,0,"
cir_2_ch4 =         "75.0,      15.0,       0.01,       -90,        8.0     ,0,0,"
cir_2_ch5 =         "13.0,      15.0,       -18.0,      -90,        6.0     ,0,0,"
cir_2_ALL = [cir_2_start,cir_2_ch1,cir_2_ch2,cir_2_ch3,cir_2_ch4,cir_2_ch5]

#######################################################################################
morning, noon, evening, night = 0, 1, 2, 3; clear, cloudy, rain, snow = 0, 1, 2, 3
filler_WP_1 = "0.0, 0.0, 0.0, 0.0, 15.0, 0, 0,"; filler_WP_2 = "0.0, 0.0, 50.0, 0.0, 15.0, 0, 0,"
filler_ALL = [filler_WP_1, filler_WP_2]
#######################################################################################

# Blitz WP file, Time of Day, Weather, Time Limit, Number of Checkpoints (5 arguments)
blitz_waypoints = [(blz_0_ALL, morning, clear, 60, len(blz_0_ALL)-1),   
                   (blz_1_ALL, night, snow, 40, len(blz_1_ALL)-1)]

# Circuit WP file, Time of Day, Weather, Laps Amateur, Laps Pro (5 arguments)
circuit_waypoints = [(cir_0_ALL, night, snow, 3, 3),
                     (cir_1_ALL, noon, cloudy, 4, 4),
                     (cir_2_ALL, evening, rain, 4, 4)]

# Checkpoint WP file, Time of Day, Weather (3 arguments)
checkpoint_waypoints = [(filler_ALL, noon, cloudy)] # feel free to change

# COPS AND ROBBERS
cnr_waypoints = [
    ## 1st set, Name: ... ## 
    (85.0,14.5,0.0),                                     
    (0.0,15.5,-85.0),                                  
    (-85.0,14.5,0.0),
    ## 2nd set, Name: ... ## 
    (0.0,14.5,-85.0),
    (-85,15.5,0.0),                                  
    (0.0,14.5,85.0),
    ## 3rd set, Name: ... ##
    (-85,14.5,0.0),
    (0,15.5,85.0),
    (85.0,14.5,0.0),
    #4
    (0.0,14.5,85.0),
    (85.0,15.5,0.0),
    (0,14.5,-85.0),
    #5
    (85.0,7.0,-110.0),
    (-48,25.5,45),
    (110.0,7.0,-85.0),
    #6
    (-110,7.0,-85.0),
    (45.0,15.5,45.0),
    (-85.0,7.0,-110.0),
    #7
    (-13,24.5,45.0),
    (38.0,15.5,-45.0),
    (-13,29.5,45.0),
    #8
    (35,14.5,-45.0),
    (-57,6.5,112),
    (60,14.5,0.0),
    #9
    (-45,22.0,63.0),
    (57,6.5,112),
    (-45,22.0,27.0),   
    #10
    (-85,14.5,85.0),
    (-8.5,15.5,-55.0),
    (85.0,14.5,85.0), 
    #11
    (88,14.5,-88.0),
    (0,15.5,50.0),
    (-88.0,14.5,-88.0), 
    #12
    (-85,14.5,-85.0),
    (0,15.5,0.0),
    (85.0,14.5,85.0), ]

# ANIM
anim_data = {
    'plane': [                  # you can only use "plane" and "eltrain". other objects won't work
        (250, 40.0, -250),      # you can only have one Plane and one Eltrain
        (250, 40.0, 250),       # you can set any number of coordinates for your path
        (-250, 40.0, -250),     
        (-250, 40.0, 250)], 
    'eltrain': [
        (80, 25.0, -80),
        (80, 25.0, 80), 
        (-80, 25.0, -80),
        (-80, 25.0, 80)]}

# BRIDGES
slim_bridge = "tpdrawbridge04"  # dimension: x: 30.0 y: 5.9 z: 32.5
wide_bridge = "tpdrawbridge06"  # dimension: x: 40.0 y: 5.9 z: 32.5
other_object = "..." # you can pass any object, for example: vpmustang99

# I: only ONE bridge can be present in ONE cull room (otherwise the game will crash)
# II: Bridges currently only work in MULTIPLAYER, in SINGLEPLAYER the game will crash if you enable bridges
# Therefore, be cautious with changing setting "create_bridges()" to True at the end of the script

# format: (x,y,z, orientation, bridge number, object)
bridges = [
    ((-50.0, 0.0, -150.0), "vertical", 1, slim_bridge), 
    ((-200.0, 0.0, -200.0), "horizontal_east", 2, wide_bridge)]

# Possible orientations
# 'vertical', 'vertical_flipped', 'horizontal_east', 'horizontal_west', 'north_east', 'north_west', 'south_east', or 'south_west'

# Not applicable yet
ambient_density = 0.5 # AIMAP_P
num_opponents = 8 # gen. 8 opponents all race types, and put the created opponent file names in the correct AIMAP_P files
opponent_car = "vppanozgt" 

# OTHER
randomize_string_names = ["T_WATER", "T_GRASS", "T_WOOD", "IND_WALL", "EXPLOSION", "OT_BAR_BRICK", "R4", "R6", "T_WALL", "FXLTGLOW"] 
common_textures_1 = []

################################################################################################################               
################################################################################################################     
 
def to_do_list(x):
            """
            TexCoords --> flip "repeated_horizontal" and flip "vertical". Because tested "R2" example is actually at x=0, y=-200 (and not y=200)
            TexCoords --> check "rotating_repeating" (angles)
            TexCoords --> find way to account for Walls (is the opposite for flat surfaces?)
            TEXTURES --> add TEX16A and TEX16O from existing custom cities
            TEXTURES --> replacing textures with custom ones works, adding textures crashes for unknown reasons
            TEXTURES --> will other textures also move if they contain "T_WATER..."? | code implemented, needs to be tested
            Corners --> figure out Triangles
            Corners --> figure out Hills    
            WALL --> is there a way to enable collision on both sides of the wall?
            WALL --> walls are infinite in height (fix this)
            BRIDGE --> cont.                   
            HUDMAP --> fix/automate (correct) alignment
            HUDMAP --> color fill some Polygons (e.g. Blue for Water, Green for Grass), need to correctly retrieve/match Bound Number first (hard)
            SCRIPT --> split "distribute_generated_files" into smaller components    
            SCRIPT --> split City Settings (coordinates) into separate file
            SCRIPT --> "repeating_horizontal_flipped" shorten (?) (e.g. "rhf" or "r-hf)
            SCRIPT --> is Vector2 class really necessary? (maybe remove it)
            BAI --> retrieve Center from all set Polygons
            BAI --> path conflicts, no functional AI yet
            PTL --> reinvestigate at some point
            BMS --> export "cache_size" variable correctly
            BMS --> add shifting texture (like the airport lights, "fxltglow") see: GLOW AIRPORT.txt (didn't work so far)
            BMS --> BMS vertices should be sorted until the script is further improved (?)
            BMS --> walls are invisible, user must +/- 0.01 to make them visible (fix this) (add type: facing direction)
            FCD --> test and document flags
            FCD --> enable diagonal Facade setting
            BNG --> improve prop functionality (facing)
            BNG --> add prop list (+ description) -- where is my folder with all Prop Pictures?
            BNG --> investigate CustomProp_Editor (?)
            AIMAP --> allow cop & ambient setting for each individual race
            CELLS --> implement Cell type
            CELLS --> # Max 256 characters per row --> add Error Handling/warning
            RACES --> investigate why max 15?
            BLENDER --> [...]
            USER --> collect a folder with suitable TEX16O / TEX16A textures
            GITHUB --> add Readme
            OPEN1560 --> add (forked) updated Open1560
            """
            
################################################################################################################               
################################################################################################################        

# VECTOR2 CLASS
class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"x = {self.x}, y = {self.y})"

# VECTOR3 CLASS
class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self._data = {"x": x, "y": y, "z": z}

    @classmethod
    def from_file(cls, file):
        x, y, z = struct.unpack('<3f', file.read(12))
        return cls(x, y, z)
    
    def to_file(self, file):
        data = struct.pack('<3f', self.x, self.y, self.z)
        file.write(data)
        
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
       
       
# Calculate BND: center, radius, min and max      
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


# POLYGON CLASS [BND]
class Polygon:
    def __init__(self, word0, mtl_index, flags, vert_indices, some_vecs, corners):
        self.word0 = word0
        self.mtl_index = mtl_index  
        self.flags = flags          
        self.vert_indices = vert_indices
        self.some_vecs = some_vecs
        self.corners = corners

    @classmethod
    def from_file(cls, file):
        word0, mtl_index, flags, *vert_indices = struct.unpack('<HBB4H', file.read(12))
        some_vecs = [Vector3.from_file(file) for _ in range(4)]
        corners = list(struct.unpack('<4f', file.read(16)))
        
        return cls(word0, mtl_index, flags, vert_indices, some_vecs, corners)
    
    def to_file(self, file):
        data = struct.pack('<HBB4H', self.word0, self.mtl_index, self.flags, *self.vert_indices)
        file.write(data)
    
        for vec in self.some_vecs: 
            data = struct.pack('<3f', vec.x, vec.y, vec.z)
            file.write(data)
 
        data = struct.pack('<4f', self.corners[0], self.corners[1], self.corners[2], self.corners[3])
        file.write(data)
        
    def __repr__(self, round_values=True):
        vertices_coordinates = []
        for index in self.vert_indices:
            vertices_coordinates.append(bnd.vertices[index])

        if round_values:
            corners_str = '[{}]'.format(', '.join(['{:.2f}'.format(round(corner, 2)) for corner in self.corners]))
        else:
            corners_str = '[{}]'.format(', '.join(['{:f}'.format(corner) for corner in self.corners]))

        return '\n Polygon \n Bound number: {}\n Material Index: {}\n Flags: {}\n Vertices Indices: {}\n Vertices Coordinates: {}\n Directional Coordinates: {}\n Corners: {}\n'.format(self.word0, self.mtl_index, self.flags, self.vert_indices, vertices_coordinates, self.some_vecs, corners_str)
    

# BND CLASS    
class BND:
    def __init__(self, magic, offset, width, row_count, height, center, radius, radius_sqr, min_, max_, num_verts, num_polys, num_hot_verts, num_vertices_unk, edge_count, scaled_dist_x, z_dist, num_indexs, height_scale, unk12, vertices, polys):
        self.magic = magic
        self.offset = offset    
        self.width = width
        self.row_count = row_count
        self.height = height
        self.center = center    
        self.radius = radius
        self.radius_sqr = radius_sqr
        self.min = min_         
        self.max = max_        
        self.num_verts = num_verts
        self.num_polys = num_polys
        self.num_hot_verts = num_hot_verts
        self.num_vertices_unk = num_vertices_unk
        self.edge_count = edge_count
        self.scaled_dist_x = scaled_dist_x
        self.z_dist = z_dist
        self.num_indexs = num_indexs
        self.height_scale = height_scale
        self.unk12 = unk12
        self.vertices = vertices              
        self.polys = polys                      

    @classmethod
    def from_file(cls, file):
        magic = struct.unpack('<4s', file.read(4))[0]
        offset = Vector3.from_file(file)
        width, row_count, height = struct.unpack('<3l', file.read(12)) 
        center = Vector3.from_file(file)
        radius, radius_sqr = struct.unpack('<2f', file.read(8))
        min_ = Vector3.from_file(file)
        max_ = Vector3.from_file(file)
        num_verts, num_polys, num_hot_verts, num_vertices_unk, edge_count = struct.unpack('<5l', file.read(20))
        scaled_dist_x, z_dist, num_indexs, height_scale, unk12 = struct.unpack('<fflfl', file.read(20))
        vertices = [Vector3.from_file(file) for _ in range(num_verts)]
        polys = [Polygon.from_file(file) for _ in range(num_polys + 1)] 

        return cls(magic, offset, width, row_count, height, center, radius, radius_sqr, min_, max_, num_verts, num_polys, num_hot_verts, num_vertices_unk, edge_count, scaled_dist_x, z_dist, num_indexs, height_scale, unk12, vertices, polys)
    
    def to_file(self, file):
        data = struct.pack('<4s', self.magic)
        file.write(data)
        self.offset.to_file(file)         
        data = struct.pack('<3l', self.width, self.row_count, self.height)
        file.write(data)     
        self.center.to_file(file) 
        data = struct.pack('<ff', self.radius, self.radius_sqr)
        file.write(data)
        self.min.to_file(file)
        self.max.to_file(file)
        data = struct.pack('<5l', self.num_verts, self.num_polys, self.num_hot_verts, self.num_vertices_unk, self.edge_count)
        file.write(data)
        data = struct.pack('<fflfl', self.scaled_dist_x, self.z_dist, self.num_indexs, self.height_scale, self.unk12)
        file.write(data)

        for vertex in self.vertices:       
            vertex.to_file(file)            

        for poly in self.polys:           
            poly.to_file(file)              
                
    # Write BND TEXT data
    def write_to_file(self, file_name, debug_bnd=False):
        if debug_bnd:
            with open(file_name, 'w') as f:
                f.write(str(self))
                
    def __repr__(self):
        return 'BND\n Magic: {}\n Offset: {}\n Width: {}\n Row_count: {}\n Height: {}\n Center: {}\n Radius: {}\n Radius_sqr: {}\n min: {}\n max: {}\n Num Verts: {}\n Num Polys: {}\n Num Hot Verts: {}\n Num Vertices Unk: {}\n Edge count: {}\n Scaled Dist. X: {}\n Z Dist.: {}\n Num Indexs: {}\n Height Scale: {}\n Unk12: {}\n Vertices: {}\n\n Polys: {}\n\n'.format(
            self.magic, self.offset, self.width, self.row_count, self.height, self.center, self.radius, self.radius_sqr, self.min, self.max, self.num_verts, self.num_polys, self.num_hot_verts, self.num_vertices_unk, self.edge_count, self.scaled_dist_x, self.z_dist, self.num_indexs, self.height_scale, self.unk12, self.vertices, self.polys)


# BMS CLASS  
class BMS:
    def __init__(self, Magic, VertexCount, AdjunctCount, SurfaceCount, IndicesCount, Radius, Radiussq, BoundingBoxRadius, TextureCount, Flags, StringName, Coordinates, TextureDarkness, TexCoords, enclosed_shape, SurfaceSides, IndicesSides):
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
        self.enclosed_shape = enclosed_shape  
        self.SurfaceSides = SurfaceSides
        self.IndicesSides = IndicesSides
        
    def to_file(self, file_name: str) -> None:
        with open(file_name, 'wb') as file:
            file.write(struct.pack('<16s', self.Magic.encode('utf-8').ljust(16, b'\x00')))
            file.write(struct.pack('<IIII', self.VertexCount, self.AdjunctCount, self.SurfaceCount, self.IndicesCount))
            file.write(struct.pack('<fff', self.Radius, self.Radiussq, self.BoundingBoxRadius))
            file.write(struct.pack('<bb', self.TextureCount, self.Flags))

            file.write(b'\x00' * 2) 
            file.write(b'\x00' * 4)

            for StringName in self.StringName:
                file.write(struct.pack('<32s', StringName.encode('utf-8').ljust(32, b'\x00')))
                file.write(b'\x00' * (4 * 4))

            for coordinate in self.Coordinates:
                file.write(struct.pack('<3f', coordinate.x, coordinate.y, coordinate.z))

            file.write(struct.pack('<' + str(self.AdjunctCount) + 'b', *self.TextureDarkness))
            file.write(struct.pack('<' + str(self.AdjunctCount + self.AdjunctCount) + 'f', *self.TexCoords))            
            file.write(struct.pack('<' + str(self.AdjunctCount) + 'H', *self.enclosed_shape))
            file.write(struct.pack('<' + str(self.SurfaceCount) + 'b', *self.SurfaceSides))

            for indices_side in self.IndicesSides:
                file.write(struct.pack('<' + str(len(indices_side)) + 'H', *indices_side))
      
################################################################################################################               
################################################################################################################       
   
# INITIALIZATIONS | do not change
# BND related
bnd_hit_id = f"{city_name}_HITID.BND"
bnd_hit_id_text = f"{city_name}_HITID.txt"
poly_filler = Polygon(0, 0, 0, [0, 0, 0, 0], [Vector3(0, 0, 0) for _ in range(4)], [0.0, 0.0, 0.0, 0.0])
vertices = []
polys = [poly_filler]
all_polygons_picture = []

# Bridge related
filler_object_xyz = "tpsone,0,-9999.99,0.0,-9999.99,-9999.99,0.0,-9999.99" # Bridge related

# Race related
num_blitz = len(blitz_waypoints)
num_circuit = len(circuit_waypoints)
num_checkpoint = len(checkpoint_waypoints)

# FCD related
created_fcd_file = city_name + ".FCD"
target_fcd_dir = os.path.join(os.getcwd(), "SHOP", "CITY")

# Physics related
resources_folder = os.path.join(os.getcwd(), "RESOURCES")
physics_folder = os.path.join(os.getcwd(), "SHOP", "MTL")
os.makedirs(physics_folder, exist_ok=True)
input_physics_file = os.path.join(resources_folder, "input_PHYSICS.DB")
output_physics_file = "physics.db"

################################################################################################################               
 
# Handle Texture Mapping for BMS files
def generate_tex_coords(mode="horizontal", repeat_x=1, repeat_y=1, tilt=0, angle_degrees=(45, 45), custom=None):
    
    def tex_coords_rotating_repeating(repeat_x, repeat_y, angle_degrees):
        angle_radians = [math.radians(angle) for angle in angle_degrees]

        def rotate(x, y, angle_idx):
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
    if mode == "horizontal":
        return [0, 0, 0, 1, 1, 1, 1, 0]
    elif mode == "horizontal_flipped":
        return [0, 1, 0, 0, 1, 0, 1, 1]
   # Vertical 
    elif mode == "vertical":
        return [0, 0, 1, 0, 1, 1, 0, 1]    
    elif mode == "vertical_flipped":
        return [1, 0, 0, 0, 0, 1, 1, 1]
    # Horizontal Repeated
    elif mode == "repeating_horizontal":
        return [0, 0, 0, repeat_y, repeat_x, repeat_y, repeat_x, 0]
    elif mode == "repeating_horizontal_flipped":
        return [0, repeat_y, 0, 0, repeat_x, 0, repeat_x, repeat_y]
    # Vertical Repeated
    elif mode == "repeating_vertical":
        return [0, 0, repeat_y, 0, repeat_y, repeat_x, 0, repeat_x]
    elif mode == "repeating_vertical_flipped":
        return [repeat_y, 0, 0, 0, 0, repeat_x, repeat_y, repeat_x]

    # Check
    elif mode == "rotating_repeating":
        return tex_coords_rotating_repeating(repeat_x, repeat_y, angle_degrees)
    elif mode == "custom":
        if custom is None:
            raise ValueError("Custom TexCoords must be provided for mode 'custom'")
        return custom
    elif mode == "combined":
        return [0, 0, 1, 0, 1, 1 + tilt, 0, 2]
    else:
        raise ValueError(f"Invalid mode '{mode}'. Allowed values are 'horizontal', 'vertical', 'horizontal_flipped', 'vertical_flipped', 'repeating_horizontal', 'repeating_vertical', 'repeating_horizontal_flipped', 'repeating_vertical_flipped', 'rotating_repeating', 'custom', and 'combined'")

# HELPER BMS
def generate_and_save_bms_file(
    string_names, texture_indices=[1], vertices=vertices, polys=polys, texture_darkness=None, TexCoords=None, randomized_string_name=False, exclude=False, tex_coord_mode=None, tex_coord_params=None):
    
    poly = polys[-1]  # Get the last polygon added
    bound_number = poly.word0
    
    # Randomize BMS/Graphic Strings
    if randomized_string_name and not exclude:
        string_names = [random.choice(randomize_string_names)]
    
    # Create correct Water BMS
    # if "T_WATER" is (partially) in string_names:
    if any(name.startswith("T_WATER") for name in string_names):
        bms_filename = "CULL{:02d}_A2.bms".format(bound_number)
    else:
        bms_filename = "CULL{:02d}_H.bms".format(bound_number)
        
    if tex_coord_mode is not None:
        if tex_coord_params is None:
            tex_coord_params = {}
        TexCoords = generate_tex_coords(tex_coord_mode, **tex_coord_params)
        
    single_poly = [poly_filler, poly]
    bms = generate_bms(vertices, single_poly, texture_indices, string_names, texture_darkness, TexCoords)
    bms.to_file(bms_filename)
    # print(f"Successfully created BMS file: {bms_filename}")
             
# GENERATE BMS         
def generate_bms(vertices, polys, texture_indices, string_names: List[str], texture_darkness=None, TexCoords=None):
    shapes = []
    for poly in polys[1:]:  # Skip the first filler polygon
        vertex_coordinates = [vertices[idx] for idx in poly.vert_indices]
        shapes.append(vertex_coordinates)
    
    # DEFAULT BMS VALUES, do not change
    magic, flags, radius, radiussq, bounding_box_radius = "3HSM", 3, 0.0, 0.0, 0.0  
    texture_count = len(string_names)
    coordinates = [coord for shape in shapes for coord in shape]
    vertex_count = len(coordinates)
    adjunct_count = len(coordinates)
    surface_count = len(texture_indices)            
    indices_count = surface_count * 4
    enclosed_shape = list(range(adjunct_count))

    # Texture Darkness and TexCoords        
    if texture_darkness is None:
        texture_darkness = [2] * adjunct_count
    if TexCoords is None:
        TexCoords = [0.0 for _ in range(adjunct_count * 2)]

    # Create list of Indices Sides, one for each shape
    indices_sides = []
    index_start = 0
    for shape in shapes:
        shape_indices = list(range(index_start, index_start + len(shape)))
        indices_sides.append(shape_indices)
        index_start += len(shape)
        
    return BMS(magic, vertex_count, adjunct_count, surface_count, indices_count, radius, radiussq, bounding_box_radius, texture_count, flags, string_names, coordinates, texture_darkness, TexCoords, enclosed_shape, texture_indices, indices_sides)

################################################################################################################               
################################################################################################################  

# Initialize BND   
def initialize_bnd(vertices, polys):
    magic, width, row_count, height = b'2DNB\0', 0, 0, 0
    num_hot_verts, num_vertices_unk, edge_count, scaled_dist_x, z_dist = 0, 0, 0, 0.0, 0.0
    num_indexs, height_scale, unk12, edge_count = 0, 0.0, 0, 0
    offset = Vector3(0.0, 0.0, 0.0)
    center = calculate_center(vertices)
    min_ = calculate_min(vertices)
    max_ = calculate_max(vertices)
    radius = calculate_radius(vertices, center)
    radius_sqr = radius ** 2

    return BND(magic, offset, width, row_count, height, center, radius, radius_sqr, min_, max_, len(vertices), len(polys) - 1, num_hot_verts, num_vertices_unk, edge_count, scaled_dist_x, z_dist, num_indexs, height_scale, unk12, vertices, polys)
    
# Sort BND Vertices Coordinates
def sort_coordinates(vertex_coordinates):
    max_x_coord = max(vertex_coordinates, key=lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key=lambda coord: coord[0])
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key=lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key=lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key=lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key=lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]

# Sort BND Directional Coordinates
def calculate_directional_coordinates(vertex_coordinates):
    dir_coord_1 = (-1, 0, -vertex_coordinates[0][0])
    dir_coord_2 = (0, 1, vertex_coordinates[1][2])
    dir_coord_3 = (1, 0, vertex_coordinates[2][0])
    dir_coord_4 = (0, -1, -vertex_coordinates[3][2])

    return [dir_coord_1, dir_coord_2, dir_coord_3, dir_coord_4]

# Create Polygon       
def create_polygon(bound_number, material_index, flags, vert_indices, some_vecs, corners):
    return Polygon(bound_number, material_index, flags, vert_indices, some_vecs, corners)
     
# Create and Append Polygon
def create_and_append_polygon(
    bound_number, material_index, vertex_coordinates, corners=None, base_vertex_index=None, flags=None, 
    vertices=vertices, polys=polys, wall_side="outside"):
        
    if base_vertex_index is None:
        base_vertex_index = len(vertices)

    # Handle CORNERS                
    # case 1: FLAT Surface
    if all(vertex[1] == vertex_coordinates[0][1] for vertex in vertex_coordinates):
        corners = [0.0, 1.0, 0.0, -vertex_coordinates[0][1]]
    
    # case 2: WALL with varying X and Y coordinates
    elif (max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates) > 0.1 and
          max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
          abs(max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates)) <= 0.15):
        
        if wall_side == "outside":
            corners = [0, 0, -1, max(coord[2] for coord in vertex_coordinates)]
        elif wall_side == "inside":
            corners = [0, 0, 1, -max(coord[2] for coord in vertex_coordinates)]
    
    # case 3: WALL with varying Z and Y coordinates                               
    elif (abs(max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates)) <= 0.15 and
          max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
          max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates) > 0.1):
                
        if wall_side == "outside":
            corners = [-1, 0, 0, min(coord[0] for coord in vertex_coordinates)]
        elif wall_side == "inside":
            corners = [1, 0, 0, -min(coord[0] for coord in vertex_coordinates)]
            
    # Hills (TO DO)
    # case 4: HILL with varying X, Y and Z coordinates      (1e 3e regels moet kloppen)
    # elif (max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates) > 0.1 and
          # max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
          # max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates) > 0.1):

        # corners = [0, 0, -1, max(coord[2] for coord in vertex_coordinates)]
    
    # TO DO: 
    # case 5: triangles
    elif corners is None:
        raise ValueError("Corners method not implemented yet, please specify Corners manually")
    
    # Handle FLAGS    
    num_vertex_coordinates = len(vertex_coordinates)
    if flags is None:
        if num_vertex_coordinates == 4:
            flags = 6           # flag 4 and 5 should also work for rectangles
        elif num_vertex_coordinates == 3:
            flags = 3           # flag 0, 1, 2, 8, 9, 10 should also work for triangles
            print("WARNING: Triangles are not supported yet")
        else:
            raise ValueError("Unsupported number of coordinates in 'vertex_coordinates'")
    
    sorted_vertex_coordinates = sort_coordinates(vertex_coordinates)
    new_vertices = [Vector3(*coord) for coord in sorted_vertex_coordinates]
    vertices.extend(new_vertices)
    vert_indices = [base_vertex_index + i for i in range(len(new_vertices))]

    directional_vectors = calculate_directional_coordinates(sorted_vertex_coordinates)
    some_vecs = [Vector3(*vec) for vec in directional_vectors]

    poly = create_polygon(bound_number, material_index, flags, vert_indices, some_vecs, corners)
    polys.append(poly)
    
    # Create picture of all shapes
    all_polygons_picture.append(vertex_coordinates)
        
################################################################################################################               
################################################################################################################ 

# ==================CREATING YOUR CITY================== #

def user_notes(x):
    """ 
    NOTES:
    Please find some example Polygons and BMS below this text.
    You can already run this the script with these Polygons and BMS to see how it works.
    
    If you're creating a Flat Surface, you should pass this structure to "vertex_coordinates:"
        max_x,max_z 
        min_x,max_z 
        max_x,min_z 
        min_x,min_z 
            
    Material Index: 0 = Road, 87 = Grass, 91 (Water, {Sleep with the Fishes})

    Usage examples of TexCoods:
    TexCoords=generate_tex_coords(mode="vertical")
    TexCoords=generate_tex_coords(mode="repeating_vertical", repeat_x=4, repeat_y=2))
    TexCoords=generate_tex_coords(mode="rotating_repeating", repeat_x=3, repeat_y=3, angle_degrees=(45, 45))) {unfinished}
    
    Usage example of Randomize String Names
    In the function DEFINITION (roughly line 364), i.e. "def generate_and_save_bms_file()" you can:
    Set "randomized_string_name=False" to disable
    Set "randomized_string_name=True" to enable (for all Strings)

    See below to Exclude random string name for specified Polygon, while randomizing the rest
    generate_and_save_bms_file(
           string_names=["T_WALL"], exclude=True))
    """

# Polygon 1 | BND floor
create_and_append_polygon(
    bound_number = 1,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),
        (-10, 15.0, -80),	
        (-80, 15.0, -80),
        (-80, 15.0, -10)])

# Polygon 1 | Texture
generate_and_save_bms_file(
    string_names = ["T_WALL"])

        # Polygon 2 | BND WALL1 1
create_and_append_polygon(
    bound_number = 2,
    material_index = 0,
    vertex_coordinates=[
        (-80, 35.0, -79.99),	
        (-80, 15.0, -80),
        (-10, 15.0, -80),
        (-10, 35.0, -79.99)], wall_side="outside")      

    # Generate BMS for Polygon 2 WALL1 1
generate_and_save_bms_file(
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0]) 
 
        # Polygon 3 | BND WALL1 2
create_and_append_polygon(
    bound_number = 3,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),		
        (-10.01, 35.0, -10),
        (-10.01, 35.0, -80),
        (-10, 15.0, -80)], wall_side="inside")

generate_and_save_bms_file( 
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0])     
    
  
        # Polygon 4 | BND WALL1 3
create_and_append_polygon(
    bound_number = 4,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, -10),		
        (-80, 35.0, -10.01),
        (-10, 35.0, -10.01),
        (-10, 15.0, -10)],wall_side="inside")
    
    # Generate BMS for Polygon 4 WALL1 3
generate_and_save_bms_file(
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0])         
    
        # Polygon 5 | BND WALL1 4
create_and_append_polygon(
    bound_number = 5,
    material_index = 0,
    vertex_coordinates=[
        (-79.99, 35.0, -80),		
        (-80, 15.0, -80),
        (-80, 15.0, -10),
        (-79.99, 35.0, -10)],wall_side="outside")
    
    # Generate BMS for Polygon 5 WALL1 4
generate_and_save_bms_file( 
    string_names = ["T_WOOD"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,0,5,5,5,0])     
    
        # Polygon 12 | BND road floor
create_and_append_polygon(
    bound_number = 12,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -10),
        (40, 15.0, -80),	
        (80, 15.0, -80),
        (80, 15.0, -10)])
    
    # Generate BMS for Polygon 12
generate_and_save_bms_file(
    string_names = ["T_WALL"])   

        # Polygon 13 | BND WALL2 1
create_and_append_polygon(
    bound_number = 13,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -80),
        (40, 25.0, -79.99),
        (80, 25.0, -79.99),
        (80, 15.0, -80)], wall_side="outside")
    
    # Generate BMS for Polygon 13 WALL2 1
generate_and_save_bms_file(
    string_names=["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=5,repeat_y=5))

        # Polygon 14 | BND WALL2 2
create_and_append_polygon(
    bound_number = 14,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),
        (79.99, 25.0, -80),
        (79.99, 25.0, -10),
        (80, 15.0, -10)], wall_side="inside")
    
    # Generate BMS for Polygon 14 WALL2 2
generate_and_save_bms_file(
    string_names = ["IND_WALL"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 15 | BND WALL2 3
create_and_append_polygon(
    bound_number = 15,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -10),
        (40, 25.0, -10.01),
        (80, 25.0, -10.01),
        (80, 15.0, -10)],wall_side="inside")
    
    # Generate BMS for Polygon 15 WALL2 3
generate_and_save_bms_file(
    string_names=["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=5,repeat_y=5))

        # Polygon 16 | BND WALL2 4
create_and_append_polygon(
    bound_number = 16,
    material_index = 0,
    vertex_coordinates=[
        (40, 15.0, -10),
        (40.01, 25.0, -10),
        (40.01, 25.0, -80),
        (40, 15.0, -80)], wall_side="outside")
    
    # Generate BMS for Polygon 16 WALL2 4
generate_and_save_bms_file(
    string_names=["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal",repeat_x=5,repeat_y=5))

    # Polygon 21 | BND floor
create_and_append_polygon(
    bound_number = 21,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),		
        (10, 15.0, 40),
        (80, 15.0, 40),
        (80, 15.0, 10)])
    
    # Generate BMS for Polygon 21 floor
generate_and_save_bms_file(
    string_names = ["T_WALL"])        

        # Polygon 22 | BND WALL3 1
create_and_append_polygon(
    bound_number = 22,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),
        (10, 25.0, 10.01),
        (80, 25.0, 10.01),
        (80, 15.0, 10)], wall_side="outside")
    
    # Generate BMS for Polygon 22 WALL3 1
generate_and_save_bms_file(
    string_names=["OT_BAR_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 23 | BND WALL3 2
create_and_append_polygon(
    bound_number = 23,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 40),
        (79.99, 25.0, 40),
        (79.99, 25.0, 10),
        (80, 15.0, 10)], wall_side="inside")
    
    # Generate BMS for Polygon 23 WALL3 2
generate_and_save_bms_file(
    string_names = ["OT_BAR_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 24 | BND WALL3 3
create_and_append_polygon(
    bound_number = 24,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 40),
        (10, 25.0, 39.99),
        (80, 25.0, 39.99),
        (80, 15.0, 40)], wall_side="inside")
    
    # Generate BMS for Polygon 24 WALL3 3
generate_and_save_bms_file(
    string_names=["OT_BAR_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 25 | BND WALL3 4
create_and_append_polygon(
    bound_number = 25,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),
        (10.01, 25.0, 10),
        (10.01, 25.0, 40),
        (10, 15.0, 40)], wall_side="outside")
    
    # Generate BMS for Polygon 25 WALL3 4
generate_and_save_bms_file(
    string_names = ["OT_BAR_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 26 | BND
create_and_append_polygon(
    bound_number = 26,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 40),		
        (10, 15.0, 50),
        (80, 15.0, 50),
        (80, 15.0, 40)])
    
    # Generate BMS for Polygon 26
generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))

    # Polygon 27 | BND floor
create_and_append_polygon(
    bound_number = 27,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 50),		
        (10, 15.0, 80),
        (80, 15.0, 80),
        (80, 15.0, 50)])
    
    # Generate BMS for Polygon 27 floor
generate_and_save_bms_file(
    string_names = ["T_WALL"])  

        # Polygon 28 | BND WALL4 1
create_and_append_polygon(
    bound_number = 28,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 50),
        (10, 25.0, 50.01),
        (80, 25.0, 50.01),
        (80, 15.0, 50)], wall_side="outside")
    
    # Generate BMS for Polygon 28 WALL4 1
generate_and_save_bms_file(
    string_names=["CT_SHOP_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 29| BND WALL4 2
create_and_append_polygon(
    bound_number = 29,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 50),
        (79.99, 25.0, 50),
        (79.99, 25.0, 80),
        (80, 15.0, 80)], wall_side="inside")
    
    # Generate BMS for Polygon 29 WALL4 2
generate_and_save_bms_file(
    string_names = ["CT_SHOP_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 30| BND WALL4 3
create_and_append_polygon(
    bound_number = 30,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 80),
        (80, 25.0, 79.99),
        (10, 25.0, 79.99),
        (10, 15.0, 80)], wall_side="inside")
    
    # Generate BMS for Polygon 30 WALL4 3
generate_and_save_bms_file(
    string_names=["CT_SHOP_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=12,repeat_y=5))

        # Polygon 31| BND WALL4 4
create_and_append_polygon(
    bound_number = 31,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 80),
        (10.01, 25.0, 80),
        (10.01, 25.0, 50),
        (10, 15.0, 50)], wall_side="outside")
    
    # Generate BMS for Polygon 31 WALL4 4
generate_and_save_bms_file(
    string_names = ["CT_SHOP_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 50 | BND
create_and_append_polygon(
    bound_number = 50,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),		
        (-10, 15.0, 80),
        (-80, 15.0, 80),
        (-80, 15.0, 10)])
    
    # Generate BMS for Polygon 50
generate_and_save_bms_file(
    string_names = ["T_WALL"])      

        # Polygon 6 | BND spawn
create_and_append_polygon(
    bound_number = 6,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),
        (-10, 15.0, 10),	
        (10, 15.0, 10),
        (10, 15.0, -10)])
    
    # Generate BMS for Polygon 6 spawn
generate_and_save_bms_file(
    string_names=["Rinter"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="horizontal"))
     
    # Polygon 7 | BND
create_and_append_polygon(
    bound_number = 7,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, -10),
        (-10, 15.0, -80),	
        (10, 15.0, -80),
        (10, 15.0, -10)])
    
    # Generate BMS for Polygon 7
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical_flipped",repeat_x=2,repeat_y=10))

        # Polygon 8 | BND
create_and_append_polygon(
    bound_number = 8,
    material_index = 98,
    vertex_coordinates=[
        (10, 15.0, -10),
        (10, 15.0, -80),	
        (40, 15.0, -80),
        (40, 15.0, -10)])
    
    # Generate BMS for Polygon 8
generate_and_save_bms_file(
    string_names = ["CHECK04"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])       

# Polygon 9 | BND
create_and_append_polygon(
    bound_number = 9,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),              
        (-80, 15.0, -80),		
        (-80, 15.0, -90),
        (80, 15.0, -90)])
    
    # Generate BMS for Polygon 9
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal_flipped",repeat_x=7,repeat_y=1))


    # Polygon 10 | BND
create_and_append_polygon(
    bound_number = 10,
    material_index = 87,
    vertex_coordinates=[
        (90, 15.0, -90),              
        (90, 4.0, -115),		
        (-90, 4.0, -115),
        (-90, 15.0, -90)], corners=[0.0, 1.0, -0.44, -54.6])
    
    # Generate BMS for Polygon 10
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])
    
    # Polygon 11 | BND 
create_and_append_polygon(
    bound_number = 11,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, -115),		
        (-115, 4.0, -115),
        (-115, 4.0, -500),
        (115, 4.0, -500)])
    
    # Generate BMS for Polygon 11
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])     
    
# Polygon 17 | BND
create_and_append_polygon(
    bound_number = 17,
    material_index = 0,
    base_vertex_index=len(vertices),
    vertex_coordinates=[
        (10, 15.0, -10),
        (80, 15.0, -10),
        (80, 15.0, 10),
        (10, 15.0, 10)])

    # Generate BMS for Polygon 17
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal_flipped",repeat_x=10,repeat_y=2))

    # Polygon 18 | BND
create_and_append_polygon(
    bound_number = 18,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),		
        (80, 15.0, 80),
        (90, 15.0, 80),
        (90, 15.0, -80)])
    
    # Generate BMS for Polygon 18
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=1,repeat_y=7))

    # Polygon 19 | BND
create_and_append_polygon(
    bound_number = 19,
    material_index = 87,
    vertex_coordinates=[
        (90, 15.0, 90),		
        (115, 4.0, 90),
        (115, 4.0, -90),
        (90, 15.0, -90)],corners=[0.44, 1, 0.0, -54.6])
    
    # Generate BMS for Polygon 19
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])     

    # Polygon 20 | BND 
create_and_append_polygon(
    bound_number = 20,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, 115),		
        (115, 4.0, -115),
        (500, 4.0, -115),
        (500, 4.0, 115)])
    
    # Generate BMS for Polygon 20
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])     

    # Polygon 32 | BND
create_and_append_polygon(
    bound_number = 32,
    material_index = 0,
    vertex_coordinates=[
        (10, 15.0, 10),		
        (-10, 15.0, 10),
        (-10, 15.0, 80),
        (10, 15.0, 80)])
    
    # Generate BMS for Polygon 32
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical_flipped",repeat_x=2,repeat_y=10))      
    
     # Polygon 47 | BND
create_and_append_polygon(
    bound_number = 47,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 80),		
        (80, 15.0, 90),
        (-80, 15.0, 90),
        (-80, 15.0, 80),])
    
    # Generate BMS for Polygon 47
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal",repeat_x=7,repeat_y=1))

     # Polygon 48 | BND
create_and_append_polygon(
    bound_number = 48,
    material_index = 87,
    vertex_coordinates=[
        (-90, 15.0, 90),
        (-90, 4.0, 115),
        (90, 4.0, 115),
        (90, 15.0, 90)], corners=[0.0, 1.0, 0.44, -54.6])
    
    # Generate BMS for Polygon 48
generate_and_save_bms_file( 
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])   

    # Polygon 49 | BND
create_and_append_polygon(
    bound_number = 49,
    material_index = 91,
    vertex_coordinates=[
        (-115, 4.0, 115),		
        (-115, 4.0, 500),
        (115, 4.0, 500),
        (115, 4.0, 115)])
    
    # Generate BMS for Polygon 49
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

# Polygon 33 | BND
create_and_append_polygon(
    bound_number = 33,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),		
        (-10, 15.0, -10),
        (-80, 15.0, -10),
        (-80, 15.0, 10),])

    # Generate BMS for Polygon 33
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_horizontal_flipped",repeat_x=10,repeat_y=2))

        # Polygon 35| BND WALL5 1
create_and_append_polygon(
    bound_number = 35,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),
        (-10, 40.0, 10.01),
        (-40, 40.0, 10.01),
        (-40, 15.0, 10)], wall_side="outside")
    
    # Generate BMS for Polygon 35 WALL5 1
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 36| BND WALL5 2
create_and_append_polygon(
    bound_number = 36,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 10),
        (-10.01, 40.0, 10),
        (-10.01, 40.0, 40),
        (-10, 15.0, 40)],wall_side="inside")
    
    # Generate BMS for Polygon 36 WALL5 2
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 37| BND WALL5 3
create_and_append_polygon(
    bound_number = 37,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 40),
        (-10, 40.0, 39.99),
        (-40, 40.0, 39.99),
        (-40, 15.0, 40)],wall_side="inside")
    
    # Generate BMS for Polygon 37 WALL5 3
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 38| BND WALL5 4
create_and_append_polygon(
    bound_number = 38,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 10),
        (-39.99, 40.0, 10),
        (-39.99, 40.0, 40),
        (-40, 15.0, 40)],wall_side="outside")
    
    # Generate BMS for Polygon 38 WALL5 4
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 43| BND WALL7 1
create_and_append_polygon(
    bound_number = 43,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 50),
        (-10, 40.0, 50.01),
        (-40, 40.0, 50.01),
        (-40, 15.0, 50)],wall_side="outside")
    
    # Generate BMS for Polygon 43 WALL7 1
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 44| BND WALL7 2
create_and_append_polygon(
    bound_number = 44,
    material_index = 0,
    vertex_coordinates=[
        (-10, 15.0, 80),
        (-10.01, 40.0, 80),
        (-10.01, 40.0, 50),
        (-10, 15.0, 50)],wall_side="inside")
    
    # Generate BMS for Polygon 44 WALL7 2
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 45| BND WALL7 3
create_and_append_polygon(
    bound_number = 45,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 80),
        (-40, 40.0, 79.99),
        (-10, 40.0, 79.99),
        (-10, 15.0, 80)],wall_side="inside")
    
    # Generate BMS for Polygon 45 WALL7 3
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 51 | BND WALL6 1
create_and_append_polygon(
    bound_number = 51,
    material_index = 0,
    vertex_coordinates=[
        (-50, 15.0, 10),		
        (-50, 35.0, 10.01),
        (-80, 35.0, 10.01),
        (-80, 15.0, 10)],wall_side="outside")
    
    # Generate BMS for Polygon 51 WALL6 1
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])     

        # Polygon 52 | BND WALL6 2
create_and_append_polygon(
    bound_number = 52,
    material_index = 0,
    vertex_coordinates=[
        (-50, 15.0, 80),		
        (-50.01, 35.0, 80),
        (-50.01, 35.0, 10.),
        (-50, 15.0, 10)],wall_side="inside")
    
    # Generate BMS for Polygon 52 WALL6 2
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

        # Polygon 53 | BND WALL6 3
create_and_append_polygon(
    bound_number = 53,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, 80),		
        (-80, 35.0, 79.99),
        (-50, 35.0, 79.99),
        (-50, 15.0, 80)],wall_side="inside")
    
    # Generate BMS for Polygon 53 WALL6 3
generate_and_save_bms_file( 
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

        # Polygon 54 | BND WALL6 4
create_and_append_polygon(
    bound_number = 54,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, 10),		
        (-79.99, 35.0, 10),
        (-79.99, 35.0, 80),
        (-80, 15.0, 80)],wall_side="outside")
    
    # Generate BMS for Polygon 54 WALL6 4
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 55 | BND
create_and_append_polygon(
    bound_number = 55,
    material_index = 0,
    vertex_coordinates=[
        (-90, 15.0, 80),		
        (-80, 15.0, -80),
        (-80, 15.0, 80),
        (-90, 15.0, -80)])
    
    # Generate BMS for Polygon 55
generate_and_save_bms_file(
    string_names=["R4"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical_flipped",repeat_x=1,repeat_y=7))

        # Polygon 56 | BND
create_and_append_polygon(
    bound_number = 56,
    material_index = 87,
    vertex_coordinates=[
        (-90, 15.0, 90),	
        (-115, 4.0, 90),
        (-115, 4.0, -90),
        (-90, 15.0, -90)],corners=[-0.44, 1, 0.0, -54.6])
    
    # Generate BMS for Polygon 56
generate_and_save_bms_file(
    string_names = ["T_GRASS"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5])

        # Polygon 57 | BND
create_and_append_polygon(
    bound_number = 57,
    material_index = 91,
    vertex_coordinates=[
        (-115, 4.0, -115),	
        (-115, 4.0, 115),
        (-500, 4.0, 115),
        (-500, 4.0, -115)])
    
    # Generate BMS for Polygon 57
generate_and_save_bms_file( 
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])

    # Polygon 58 | BND
create_and_append_polygon(
    bound_number = 58,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, -80),		
        (90, 15.0, -80),
        (90, 15.0, -90),
        (80, 15.0, -90)])
    
    # Generate BMS for Polygon 58
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(0,-45)))
         
    # Polygon 59 | BND
create_and_append_polygon(
    bound_number = 59,
    material_index = 0,
    vertex_coordinates=[
        (80, 15.0, 80),		
        (80, 15.0, 90),
        (90, 15.0, 90),
        (90, 15.0, 80)])
    
    # Generate BMS for Polygon 59
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(0,90)))      

        # Polygon 60 | BND
create_and_append_polygon(
    bound_number = 60,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, 80),		
        (-90, 15.0, 80),
        (-90, 15.0, 90),
        (-80, 15.0, 90)])
    
    # Generate BMS for Polygon 60
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(-90,-45)))    

        # Polygon 61 | BND
create_and_append_polygon(
    bound_number = 61,
    material_index = 0,
    vertex_coordinates=[
        (-80, 15.0, -80),	
        (-90, 15.0, -80),
        (-90, 15.0, -90),
        (-80, 15.0, -90)])
    
    # Generate BMS for Polygon 61
generate_and_save_bms_file(
    string_names = ["R2"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="rotating_repeating",repeat_x=1,repeat_y=1,angle_degrees=(0,135)))      
         
        # Polygon 39 | BND
create_and_append_polygon(
    bound_number = 39,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 10),		
        (-50, 15.0, 10),
        (-50, 25.0, 40),
        (-40, 25.0, 40)],corners=[0.0, 1.0, -0.33, -11.8])
      
    # Generate BMS for Polygon 39
generate_and_save_bms_file( 
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0]) 

        # Polygon 62 | BND
create_and_append_polygon(
    bound_number = 62,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 80),		
        (-50, 15.0, 80),
        (-50, 25.0, 50),
        (-40, 25.0, 50)],corners=[0.0, 1.0, 0.33, -41.5])
      
    # Generate BMS for Polygon 62
generate_and_save_bms_file( 
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0])     

        # Polygon 63| BND WALL7 4
create_and_append_polygon(
    bound_number = 63,
    material_index = 0,
    vertex_coordinates=[
        (-40, 15.0, 80),
        (-39.99, 40.0, 80),
        (-39.99, 40.0, 50),
        (-40, 15.0, 50)],wall_side="outside")
    
    # Generate BMS for Polygon 63 WALL7 4
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,5,0,-5,-5,-5,-5,5]) 

        # Polygon 40 | BND
create_and_append_polygon(
    bound_number = 40,
    material_index = 0,
    vertex_coordinates=[
        (-50, 25.0, 40),		
        (-25, 25.0, 40),
        (-50, 25.0, 50),
        (-25, 25.0, 50)])
    
    # Generate BMS for Polygon 40
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0])    
    
# Polygon 41 | BND
create_and_append_polygon(
    bound_number = 41,
    material_index = 0,
    vertex_coordinates=[
        (-25, 25.0, 40),		
        (-25, 25.0, 50),
        (-10, 30.0, 50),
        (-10, 30.0, 40)],corners=[-0.33, 1.0, 0.0, -33.2])
    
    # Generate BMS for Polygon 41
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[0, 1, 2, 3], TexCoords = [0,10,0,0,10,10,10,0])   

        # Polygon 34 | BND
create_and_append_polygon(
    bound_number = 34,
    material_index = 0,
    vertex_coordinates=[
        (-10.01, 30.0, 40),		
        (-10.0, 15.0, 40),
        (-10.0, 15.0, 50),
        (-10.01, 30.0, 50)],wall_side="inside")
    
    # Generate BMS for Polygon 34
generate_and_save_bms_file(
    string_names=["R_BLDG1_DOOR_01"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="vertical")) 

    # Polygon 90 | BND | Water Missing Part 1
create_and_append_polygon(
    bound_number = 90,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, 500),		
        (500, 4.0, 500),
        (500, 4.0, 115),
        (115, 4.0, 115)])
    
    # Generate BMS for Polygon 90
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 91 | BND | Water Missing Part 2
create_and_append_polygon(
    bound_number = 91,
    material_index = 91,
    vertex_coordinates=[
        (-115, 4.0, -500),		
        (-500, 4.0, -500),
        (-500, 4.0, -115),
        (-115, 4.0, -115)])
    
    # Generate BMS for Polygon 91
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 92 | BND | Water Missing Part 3
create_and_append_polygon(
    bound_number = 92,
    material_index = 91,
    vertex_coordinates=[
        (115, 4.0, -115),		
        (115, 4.0, -500),
        (500, 4.0, -500),
        (500, 4.0, -115)])
    
    # Generate BMS for Polygon 92
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

    # Polygon 93 | BND | Water Missing Part 4
create_and_append_polygon(
    bound_number = 93,
    material_index = 91,
    vertex_coordinates=[
         (-115, 4.0, 115),                 
         (-115, 4.0, 500),                 
         (-500, 4.0, 500),                 
         (-500, 4.0, 115)]), 

    # Generate BMS for Polygon 93
generate_and_save_bms_file(
    string_names = ["T_WATER"],
    texture_darkness=[2, 2, 2, 2], TexCoords = [0,5,0,-5,-5,-5,-5,5])    

# Polygon 991 | BND floor roof
create_and_append_polygon(
    bound_number = 991,
    material_index = 0,
    vertex_coordinates=[
        (-10, 35.0, -10),
        (-10, 35.0, -80),	
        (-80, 35.0, -80),
        (-80, 35.0, -10)])

# Polygon 991 | Texture roof
generate_and_save_bms_file(
    string_names = ["T_WOOD"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=7,repeat_y=7)) 

        # Polygon 992 | BND road floor roof
create_and_append_polygon(
    bound_number = 992,
    material_index = 0,
    vertex_coordinates=[
        (40, 25.0, -10),
        (40, 25.0, -80),	
        (80, 25.0, -80),
        (80, 25.0, -10)])
    
    # Generate BMS for Polygon 992 roof
generate_and_save_bms_file(
    string_names = ["IND_WALL"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=4,repeat_y=7))   

    # Polygon 993 | BND floor roof
create_and_append_polygon(
    bound_number = 993,
    material_index = 0,
    vertex_coordinates=[
        (10, 25.0, 10),		
        (10, 25.0, 40),
        (80, 25.0, 40),
        (80, 25.0, 10)])
    
    # Generate BMS for Polygon 993 floor roof
generate_and_save_bms_file(
    string_names = ["OT_BAR_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=7,repeat_y=3))  

    # Polygon 994 | BND floor roof
create_and_append_polygon(
    bound_number = 994,
    material_index = 0,
    vertex_coordinates=[
        (10, 25.0, 50),		
        (10, 25.0, 80),
        (80, 25.0, 80),
        (80, 25.0, 50)])
    
    # Generate BMS for Polygon 994 floor roof
generate_and_save_bms_file(
    string_names = ["CT_SHOP_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=7,repeat_y=3))  

    # Polygon 995 | BND floor roof
create_and_append_polygon(
    bound_number = 995,
    material_index = 0,
    vertex_coordinates=[
        (-10, 40.0, 10),		
        (-40, 40.0, 10),
        (-40, 40.0, 40),
        (-10, 40.0, 40)])
    
    # Generate BMS for Polygon 995 floor roof
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=3,repeat_y=3))   

    # Polygon 996 | BND floor roof
create_and_append_polygon(
    bound_number = 996,
    material_index = 0,
    vertex_coordinates=[
        (-10, 40.0, 50),		
        (-40, 40.0, 50),
        (-40, 40.0, 80),
        (-10, 40.0, 80)])
    
    # Generate BMS for Polygon 996 floor roof
generate_and_save_bms_file(
    string_names = ["OT_MALL_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=4,repeat_y=3))   

    # Polygon 997 | BND floor roof
create_and_append_polygon(
    bound_number = 997,
    material_index = 0,
    vertex_coordinates=[
        (-50, 35.0, 80),		
        (-80, 35.0, 80),
        (-80, 35.0, 10),
        (-50, 35.0, 10)])
    
    # Generate BMS for Polygon 997 floor roof
generate_and_save_bms_file(
    string_names = ["OT_MARKT_BRICK"],
    texture_darkness=[1,1,1,1],
    TexCoords=generate_tex_coords(mode="repeating_vertical",repeat_x=3,repeat_y=7))   

# Polygon 999 BND Garage
create_and_append_polygon(
    bound_number=999,
    material_index=0,
    vertex_coordinates=[
        (90,0,-90),
        (90,0,90),
        (-90,0,90),
        (-90,0,-90)]),

generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1], TexCoords=generate_tex_coords(mode="horizontal"))  

# Polygon 998 BND Garage HILL
create_and_append_polygon(
    bound_number=998,
    material_index=0,
    vertex_coordinates=[
        (-10,-0.5,-10),
        (-10,15,-60),
        (10,15,-60),
        (10,-0.5,-10)],corners=[0.0, 1, 0.297, 3])

generate_and_save_bms_file(
    string_names=["ROAD"],
    texture_darkness=[1,1,1,1], TexCoords=generate_tex_coords(mode="horizontal"))  
################################################################################################################               
################################################################################################################ 

# Initialize and write BND file
bnd = initialize_bnd(vertices, polys)

with open(bnd_hit_id, "wb") as f:
    bnd.to_file(f)
    bnd.write_to_file(bnd_hit_id_text, debug_bnd)

# Create SHOP and FOLDER structure   
def create_folder_structure(city_name):
    os.makedirs("build", exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BMP16"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "TEX16O"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "TUNE"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BMS", f"{city_name}CITY"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BMS", f"{city_name}LM"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BND", f"{city_name}CITY"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "BND", f"{city_name}LM"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "CITY", f"{city_name}"), exist_ok=True)
    os.makedirs(os.path.join("SHOP", "RACE", f"{city_name}"), exist_ok=True)
    
    with open(os.path.join("SHOP", "CITY", f"{city_name}.PTL"), "w") as f:
        pass
    
    with open(os.path.join("SHOP", "TUNE", f"{city_name}.CINFO"), "w") as f:
        localized_name = race_locale_name
        map_name = city_name.lower()
        race_dir = city_name.lower()        
        f.write(f"LocalizedName={localized_name}\n")
        f.write(f"MapName={map_name}\n")
        f.write(f"RaceDir={race_dir}\n")
        f.write(f"BlitzCount={num_blitz}\n")
        f.write(f"CircuitCount={num_circuit}\n")
        f.write(f"CheckpointCount={num_checkpoint}\n")
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
        
# Move contents of dev folder to MM1 destination folder      
def move_dev(destination_folder, city_name):
    current_folder = os.getcwd()
    dev_folder_path = os.path.join(current_folder, 'dev')
    
    if os.path.exists(dev_folder_path):
        destination_path = os.path.join(destination_folder, 'dev')
        
        if os.path.exists(destination_path):
            shutil.rmtree(destination_path)
            
        shutil.copytree(dev_folder_path, destination_path)
        
    # Delete Custom City .map and .roads files after they have been moved to the MM1 folder
    city_folder_path = os.path.join(dev_folder_path, 'CITY', city_name)
    if os.path.exists(city_folder_path):
        shutil.rmtree(city_folder_path)
        
# Distribute generated files
def distribute_generated_files(city_name, bnd_hit_id, num_blitz, blitz_waypoints, num_circuit, 
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
                
                for waypoint in race_waypoints[i][0]:
                    f.write(waypoint + "\n")
            shutil.move(file_name, os.path.join("SHOP", "RACE", f"{city_name}", file_name))
            
        # Set MMDATA.CSV values           
        car_type, difficulty, opponent, num_laps_checkpoint = 0, 1, 99, 99
        cops_x = 0.0        # will be customizable later
        ambient_x = 1.0     # will be customizable later
        peds_x = 1.0        # will be customizable later
                
        # Create MMDATA.CSV files
        mm_file_name = f"MM{race_type}DATA.CSV"
        with open(mm_file_name, "w") as f:
            
            f.write("Description, CarType, TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit, Difficulty, CarType, TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit, Difficulty\n")
            
            for i in range(num_files):
                if race_type == "BLITZ":
                    blitz_waypoints, timeofday, weather, timelimit, num_laps_blitz = race_waypoints[i]  
                    
                    race_data = car_type, timeofday, weather, opponent, cops_x, ambient_x, peds_x, num_laps_blitz, timelimit, difficulty, car_type, timeofday, weather, opponent, cops_x, ambient_x, peds_x, num_laps_blitz, timelimit, difficulty

                elif race_type == "CIRCUIT":
                    circuit_waypoints, timeofday, weather, num_laps_a, num_laps_p = race_waypoints[i]  
                    
                    race_data = car_type, timeofday, weather, opponent, cops_x, ambient_x, peds_x, num_laps_a, timelimit, difficulty, car_type, timeofday, weather, opponent, cops_x, ambient_x, peds_x, num_laps_p, timelimit, difficulty
                    
                elif race_type == "RACE":
                    checkpoint_waypoints, timeofday, weather = race_waypoints[i] 
                    
                    race_data = car_type, timeofday, weather, opponent, cops_x, ambient_x, peds_x, num_laps_checkpoint, timelimit, difficulty, car_type, timeofday, weather, opponent, cops_x, ambient_x, peds_x, num_laps_checkpoint, timelimit, difficulty
                    
                # Race prefixes    
                if race_type == "RACE":
                    race_data_str = ', '.join(map(str, race_data))
                    f.write(f"{race_prefixes[i]}, {race_data_str}\n") 
                else:
                    race_data_str = ', '.join(map(str, race_data))
                    f.write(f"{prefix}{i}, {race_data_str}\n") 
                                    
        destination_path = os.path.join("SHOP", "RACE", city_name, mm_file_name)
        shutil.move(mm_file_name, destination_path)
        
    # Create COPSWAYPOINTS.CSV file
    cnr_csv_file = "COPSWAYPOINTS.CSV"
    with open(cnr_csv_file, "w") as f:
        f.write("This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n")
        for i in range(0, len(cnr_waypoints), 3):
            f.write(", ".join(map(str, cnr_waypoints[i])) + ",0,0,0,0,0,\n") 
            f.write(", ".join(map(str, cnr_waypoints[i+1])) + ",0,0,0,0,0,\n")
            f.write(", ".join(map(str, cnr_waypoints[i+2])) + ",0,0,0,0,0,\n")
        
    shutil.move(cnr_csv_file, os.path.join("SHOP", "RACE", f"{city_name}", cnr_csv_file))

    # Create OPPONENT files
    if all_races_files:
        for race_type, prefix, num_files in [("BLITZ", "B", num_blitz), ("CIRCUIT", "C", num_circuit), ("RACE", "R", num_checkpoint)]:
            for race_index in range(num_files):
                for opp_index in range(1, num_opponents + 1):
                    opp_file_name = f"OPP{opp_index}{race_type}{race_index}.{prefix}{race_index}"
                    with open(opp_file_name, "w") as f:
                        f.write("# This your Opponent file for opponent number #..., in race ...")
                    shutil.move(opp_file_name, os.path.join("SHOP", "RACE", f"{city_name}", opp_file_name)) 
                    
               # Create AIMAP_P files
                aimap_file_name = f"{race_type}{race_index}.AIMAP_P"
                with open(aimap_file_name, "w") as f:
                    f.write("# Ambient Traffic Density \n[Density] \n" + str(ambient_density) + "\n\n")
                    f.write("# Default Road Speed Limit \n[Speed Limit] \n45 \n\n")
                    f.write("# Ambient Traffic Exceptions\n# Rd Id, Density, Speed Limit \n[Exceptions] \n0 \n\n")
                    f.write("# Police Init \n# Geo File, StartLink, Start Dist, Start Mode, Start Lane, Patrol Route \n")
                    f.write("[Police] \n1 \nvpcop 50.0 0.0 30.0 -90.0 0 4 \n\n")
                    
                    f.write("# Opponent Init, Geo File, WavePoint File \n[Opponent] \n") 
                    f.write(str(num_opponents) + "\n")
                    
                    for opp_index in range(1, num_opponents + 1):
                        f.write(f"{opponent_car} OPP{opp_index}{race_type}{race_index}.{prefix}{opp_index}\n")
                        
                shutil.move(aimap_file_name, os.path.join("SHOP", "RACE", f"{city_name}", aimap_file_name))
    
    # Create CELLS file
    cells_file_path = os.path.join("SHOP", "CITY", f"{city_name}.CELLS")
    with open(cells_file_path, "w") as cells_file:
        set_max_cell = 1000
        bms_count = len(bms_files)
        cells_file.write(f"{bms_count}\n")
        cells_file.write(str(set_max_cell) + "\n")

        sorted_bms_files = sorted(bms_files)
        for bound_number in sorted_bms_files:
            remaining_bound_numbers = [num for num in sorted_bms_files if num != bound_number]
            count_past_4th = len(remaining_bound_numbers)
            
            # Implement Cell type here
            if bound_number in bms_a2_files:
                row = f"{bound_number},32,4,{count_past_4th}"
            else:
                row = f"{bound_number},8,0,{count_past_4th}"
                
            '''
            1 = tunnel      Is Tunnel (Echo, No Lighting, No Reflections, No Ptx) 
            2 = indoors     (?)
            3 = tunnel      (same as 1?)
            4 = water       (water will "move") if we we make BMS_A2, add a buffer of 32, and the name of the texture is (or starts with (?)) "T_WATER"
            20 = Zenable    (?)
            80 = FogValue wll be 0.25   (?)
            200 = No Skids              (actually: any value above (?) will disable skids)
            '''
            
            for num in remaining_bound_numbers:
                row += f",{num}"
            row += "\n"
            
            # Max 256 characters per row
            row = row[:256]
            cells_file.write(row)
    
    # Copy CMD.exe, RUN.bat, and SHIP.bat to SHOP folder
    for file in os.listdir("angel"):
        if file in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(os.path.join("angel", file), os.path.join("SHOP", file))
                
# Create ANIM
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
def create_ar_file(city_name, destination_folder, delete_shop=False):
    os.chdir("SHOP")
    command = f"CMD.EXE /C run !!!!!{city_name}_City"
    subprocess.run(command, shell=True)
    os.chdir("..")  
    
    for file in os.listdir("build"):
        if file.endswith(".ar") and file.startswith(f"!!!!!{city_name}_City"):
            shutil.move(os.path.join("build", file), os.path.join(destination_folder, file))
    try:
        shutil.rmtree("build")
    except Exception as e:
        print(f"Failed to delete the build directory. Reason: {e}")
    
    if delete_shop:
        try:
            shutil.rmtree("SHOP")
        except Exception as e:
            print(f"Failed to delete the SHOP directory. Reason: {e}")
                    
# Create JPG Picture of Polygon shapes
def plot_polygons(show_label=False, plot_picture=False, export_jpg=False, 
                  x_offset=0, y_offset=0, line_width=1, background_color='black', debug_hud=False):
    
    # Setup
    output_folder_city = os.path.join("SHOP", "BMP16")
    output_folder_cwd = os.getcwd() 
    
    hudmap_picture640 = city_name + "640.JPG"
    hudmap_picture320 = city_name + "320.JPG"
    hudmap_debug = city_name + "_HUD_DEBUG.JPG"
    
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
            plt.savefig(os.path.join(output_folder_city, hudmap_picture640), dpi=1000, bbox_inches='tight', pad_inches=0.01, facecolor=background_color)
            plt.savefig(os.path.join(output_folder_city, hudmap_picture320), dpi=1000, bbox_inches='tight', pad_inches=0.01, facecolor=background_color)

            if debug_hud:
                ax.cla()
                ax.set_facecolor(background_color)
                for i, polygon in enumerate(all_polygons_picture):
                    draw_polygon(ax, polygon, color=f'C{i}', label=f'{i+1}' if show_label else None, add_label=True)
                plt.savefig(os.path.join(output_folder_cwd, hudmap_debug), dpi=1000, bbox_inches='tight', pad_inches=0.01, facecolor='white')

# Create EXT file            
def create_ext_file(city_name, polygonz):
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
        drawbridge_offset, bridge_orientation, bridge_number, bridge_object = bridge
        # Vertical
        if bridge_orientation == "vertical":
            drawbridge_facing = [drawbridge_offset[0] - 10, drawbridge_offset[1], drawbridge_offset[2]]
        elif bridge_orientation == "vertical_flipped":
            drawbridge_facing = [drawbridge_offset[0] + 10, drawbridge_offset[1], drawbridge_offset[2]]
        # Horizontal
        elif bridge_orientation == "horizontal_east":
            drawbridge_facing = [drawbridge_offset[0], drawbridge_offset[1], drawbridge_offset[2] + 10]
        elif bridge_orientation == "horizontal_west":
            drawbridge_facing = [drawbridge_offset[0], drawbridge_offset[1], drawbridge_offset[2] - 10]
        # Diagonal North    
        elif bridge_orientation == "north_east":
            drawbridge_facing = [drawbridge_offset[0] + 10, drawbridge_offset[1], drawbridge_offset[2] + 10]
        elif bridge_orientation == "north_west":
            drawbridge_facing = [drawbridge_offset[0] + 10, drawbridge_offset[1], drawbridge_offset[2] - 10]
        # Diagonal South   
        elif bridge_orientation == "south_east":
            drawbridge_facing = [drawbridge_offset[0] - 10, drawbridge_offset[1], drawbridge_offset[2] + 10]
        elif bridge_orientation == "south_west":
            drawbridge_facing = [drawbridge_offset[0] - 10, drawbridge_offset[1], drawbridge_offset[2] - 10]
        else:
            print("Invalid Bridge Orientation. Please choose from 'vertical', 'vertical flipped', 'horizontal_east', 'horizontal_west', 'north_east', 'north_west', 'south_east', or 'south_west'.")
            return

        drawbridge_values = (bridge_object, 0) + drawbridge_offset + tuple(drawbridge_facing)
        bridge_data = f"DrawBridge{bridge_number}\n" + '\t' + ','.join(map(str,drawbridge_values)) + '\n' + ('\t'+ filler_object_xyz + '\n') * 5 + f"DrawBridge{bridge_number}\n"
                
        if set_bridges:
            bridge_file_path = os.path.join("SHOP", "CITY", f"{city_name}.GIZMO")
            with open(bridge_file_path, "a") as f:
                if bridge_data is not None:
                    f.write(bridge_data)
  
# BINARYBANGER CLASS                            
class BinaryBanger:
    def __init__(self, start: Vector3, end: Vector3, name: str):
        self.room = 4       
        self.flags = 0x800  
        self.start = start
        self.end = end
        self.name = name

    def __repr__(self):
        return 'BinaryBanger\n Room: {}\n Flags: {}\n Start: {}\n End: {}\n Name: {}\n\n'.format(
            self.Room, self.Flags, self.Start, self.End, self.Name)
        
class BNGFileWriter:
    def __init__(self, filename: str):
        self.filename = filename
        self.objects = []
        resources_folder = os.path.join(os.getcwd(), "RESOURCES")
        self.prop_file_path = os.path.join(resources_folder, "Prop_Dimensions_Extracted.txt")
        self.prop_data = self.load_prop_data()            
        
    def load_prop_data(self):
        """Load prop dimensions from file."""
        prop_data = {}
        with open(self.prop_file_path, "r") as f:
            for line in f:
                name, value_x, value_y, value_z = line.split()
                prop_data[name] = Vector3(float(value_x), float(value_y), float(value_z))
        return prop_data
        
    def write_props(self, set_props: bool = False):
        if set_props:
            """Write object data to a file."""
            with open(self.filename, mode="wb") as f:
                f.write(struct.pack('<I', len(self.objects)))
            
                for obj in self.objects:
                    f.write(struct.pack(
                        '<HH3f3f', obj.room, obj.flags, obj.start.x, obj.start.y, obj.start.z, obj.end.x, obj.end.y, obj.end.z))

                    for char in obj.name: 
                        f.write(struct.pack('<s', bytes(char, encoding='utf8'))) 
                        
    # IN DEVELOPMENT      
    def add_props(self, new_objects: List[Dict[str, Union[int, float, str]]]):
        """Add props to the object datalist."""
        for obj in new_objects:
            offset = Vector3(obj['offset_x'], obj['offset_y'], obj['offset_z'])
            face = Vector3(obj['face_x'], obj['face_y'], obj['face_z'])
            name = obj['name']
            
            separator = obj.get('separator', name)  # default is the name of the object itself if 'separator' not provided
            axis = obj.get('axis', 'x')  # default is 'x' if 'axis' not provided

            if separator not in self.prop_data:
                raise ValueError(f"Separator {separator} not found in prop data.")

            self.objects.append(BinaryBanger(offset, face, name + "\x00"))

            if name in self.prop_data:
                if 'end_offset_' + axis in obj:
                    num_props = int(abs(obj['end_offset_' + axis] - obj['offset_' + axis]) / self.prop_data[separator][axis])

                    for i in range(1, num_props):
                        new_offset = Vector3(offset.x, offset.y, offset.z)  # create a new instance with the same coordinates
                        new_offset[axis] = obj['offset_' + axis] + i * self.prop_data[separator][axis]
                        self.objects.append(BinaryBanger(new_offset, face, name + "\x00"))


    def get_prop_dimension(self, prop_name: str, dimension: str) -> float:
        """Get the dimension (x, y, or z) of a prop."""
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
   
bng_file_path = os.path.join("SHOP", "CITY", f"{city_name}.BNG")  
bng_writer = BNGFileWriter(bng_file_path)

#################################################################################
#################################################################################

# MATERIALEDITOR CLASS
class MaterialEditor:
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
    def read_physics_db(file_name):
        with open(file_name, 'rb') as file:
            count_data = file.read(4)
            count = struct.unpack(">I", count_data)[0]

            agi_phys_parameters = []

            for _ in range(count):
                name_data = file.read(32)
                name = name_data.decode("latin-1").rstrip('\x00')

                params_data = file.read(36)
                params = struct.unpack(">7f2I", params_data)

                velocity_data = file.read(8)
                velocity = Vector2(*struct.unpack(">2f", velocity_data))

                ptx_color_data = file.read(12)
                ptx_color = Vector3(*struct.unpack(">3f", ptx_color_data))

                agi_phys_param = MaterialEditor(name, *params, velocity, ptx_color)
                agi_phys_parameters.append(agi_phys_param)

        return agi_phys_parameters

    @classmethod
    def read_binary(cls, file_name):
        return cls.read_physics_db(file_name)

    @staticmethod
    def write_physics_db(file_name, agi_phys_parameters):
        with open(file_name, 'wb') as file:
            count = len(agi_phys_parameters)
            count_data = struct.pack(">I", count)
            file.write(count_data)

            for param in agi_phys_parameters:
                name_data = param.name.encode("latin-1").ljust(32, b'\x00')
                file.write(name_data)

                params_data = struct.pack(">7f2I", param.friction, param.elasticity, param.drag, param.bump_height, param.bump_width, param.bump_depth, param.sink_depth, param.type, param.sound)
                file.write(params_data)

                velocity_data = struct.pack(">2f", param.velocity.x, param.velocity.y)
                file.write(velocity_data)

                ptx_color_data = struct.pack(">3f", param.ptx_color.x, param.ptx_color.y, param.ptx_color.z)
                file.write(ptx_color_data)

    @classmethod
    def change_physics_db(cls, input_file_name, output_file_name, properties, index=None):
        agi_phys_parameters = cls.read_binary(input_file_name)

        if index is not None:
            for prop, value in properties.items():
                setattr(agi_phys_parameters[index], prop, value)
        else:
            for param in agi_phys_parameters:
                for prop, value in properties.items():
                    setattr(param, prop, value)

        cls.write_physics_db(output_file_name, agi_phys_parameters)

    @staticmethod
    def create_from_scratch(output_file_name, agi_phys_parameters):
        MaterialEditor.write_physics_db(output_file_name, agi_phys_parameters)
        
    def __repr__(self):
        cleaned_name = self.name.rstrip()
        return (f"AgiPhysParameters(\n"
                f"  name        = '{cleaned_name}',\n"
                f"  friction    = {self.friction:.2f},\n"
                f"  elasticity  = {self.elasticity:.2f},\n"
                f"  drag        = {self.drag:.2f},\n"
                f"  bump_height = {self.bump_height:.2f},\n"
                f"  bump_width  = {self.bump_width:.2f},\n"
                f"  bump_depth  = {self.bump_depth:.2f},\n"
                f"  sink_depth  = {self.sink_depth:.2f},\n"
                f"  type        = {self.type},\n"
                f"  sound       = {self.sound},\n"
                f"  velocity    = {self.velocity},\n"
                f"  ptx_color   = {self.ptx_color}\n\n")
        
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
        tab = '\t'
        template = 'mmMapData :0 {\n'
        template += f'{tab}NumStreets {len(self.streets) + 5}\n'
        template += f'{tab}Street [\n'
        
        for street in self.streets:
            template += f'{tab*2}"{street}"\n'
        template += f'{tab}]\n'
        template += '}'
        return template

# Street File Editor CLASS
class StreetFileEditor:
    def __init__(self, city_name, street_data, ai_streets=False):
        self.street_name = street_data["street_name"]
        self.vertices = street_data["vertices"]
        self.intersection_types = street_data.get("intersection_types", [3, 3])
        self.stop_light_positions = street_data.get("stop_light_positions", [(0.0, 0.0, 0.0)] * 4)
        self.stop_light_names = street_data.get("stop_light_names", ["tplttrafc", "tplttrafc"])
        self.traffic_blocked = street_data.get("traffic_blocked", [0, 0])
        self.ped_blocked = street_data.get("ped_blocked", [0, 0])
        self.road_divided = street_data.get("road_divided", 0)
        self.alley = street_data.get("alley", 0)
          
        if ai_streets:
            self.write_to_file()

    def write_to_file(self):
        self.filepath = os.path.join("dev", "CITY", city_name, self.street_name + ".road")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as file:
            file.write(self.construct_template())
            
    def construct_template(self):
        tab = '\t'
        template = 'mmRoadSect :0 {\n'
        template += f'{tab}NumVertexs {len(self.vertices)}\n'
        template += f'{tab}NumLanes[0] 1\n'
        template += f'{tab}NumLanes[1] 0\n'
        template += f'{tab}NumSidewalks[0] 0\n'
        template += f'{tab}NumSidewalks[1] 0\n'
        template += f'{tab}TotalVertexs {len(self.vertices)}\n'
        template += f'{tab}Vertexs [\n'
        
        for vertex in self.vertices:
            template += f'{tab*2}{vertex[0]} {vertex[1]} {vertex[2]}\n'
            
        template += f'{tab}]\n'
        template += f'{tab}Normals [\n'
        template += f'{tab*2}0.0 1.0 0.0\n' * len(self.vertices)
        template += f'{tab}]\n'
        
        template += f'{tab}IntersectionType[0] {self.intersection_types[0]}\n'
        template += f'{tab}IntersectionType[1] {self.intersection_types[1]}\n'
            
        for i, pos in enumerate(self.stop_light_positions):
            template += f'{tab}StopLightPos[{i}] {pos[0]} {pos[1]} {pos[2]}\n'
            
        template += f'{tab}Blocked[0] {self.traffic_blocked[0]}\n'
        template += f'{tab}Blocked[1] {self.traffic_blocked[1]}\n'
        template += f'{tab}PedBlocked[0] {self.ped_blocked[0]}\n'
        template += f'{tab}PedBlocked[1] {self.ped_blocked[1]}\n'
        
        template += f'{tab}StopLightName [\n'
        template += f'{tab*2}"{self.stop_light_names[0]}"\n'
        template += f'{tab*2}"{self.stop_light_names[1]}"\n'
        template += f'{tab}]\n'
        
        template += f'{tab}Divided {self.road_divided}\n'
        template += f'{tab}Alley {self.alley}\n'
        template += '}'
        return template
    
###################################################################################################################
################################################################################################################### 

# FACADE CLASS
class BinaryFacade:
    def __init__(self, room, flags, start, end, sides, scale, name):
        self.room = room
        self.flags = flags
        self.start = start
        self.end = end
        self.sides = sides
        self.scale = scale
        self.name = name

    @classmethod
    def from_file(cls, file):
        room, flags = struct.unpack('<2H', file.read(4))
        start = Vector3.from_file(file)
        end = Vector3.from_file(file)
        sides = Vector3.from_file(file)
        scale = struct.unpack('<f', file.read(4))[0]

        out = bytearray()
        while True:
            c = file.read(1)
            if c == b'\x00':
                break
            out.extend(c)

        name = out.decode('utf-8')
        return cls(room, flags, start, end, sides, scale, name)

    def to_bytes(self):
        b_room = struct.pack('<H', self.room)
        b_flags = struct.pack('<H', self.flags)
        b_start = self.start.to_bytes()
        b_end = self.end.to_bytes()
        b_sides = self.sides.to_bytes()
        b_scale = struct.pack('<f', self.scale)
        b_name = self.name.encode('utf-8')
        b_null = struct.pack('<B', 0)

        return b_room + b_flags + b_start + b_end + b_sides + b_scale + b_name + b_null
    
    def __repr__(self):
        return 'BinaryFacade\n Room: {}\n Flags: {}\n Start: {}\n End: {}\n Sides: {}\n Scale: {}\n Name: {}\n\n'.format(
            self.room, self.flags, self.start, self.end, self.sides, self.scale, self.name)

def create_facades(filename, facade_params, target_fcd_dir, set_facade=False, debug_facade=False):
    if set_facade:
        facades = []

        for params in facade_params:
            num_facades = math.ceil(abs(getattr(params['end'], params['axis']) - getattr(params['start'], params['axis'])) / params['separator'])
            
            for i in range(num_facades):
                room = params['room']
                flags = params['flags']
                current_start = params['start'].copy()
                current_end = params['end'].copy()

                if params['axis'] == 'x':
                    current_start.x = getattr(params['start'], params['axis']) + params['separator'] * i
                    current_end.x = getattr(params['start'], params['axis']) + params['separator'] * (i + 1)
                elif params['axis'] == 'y':
                    current_start.y = getattr(params['start'], params['axis']) + params['separator'] * i
                    current_end.y = getattr(params['start'], params['axis']) + params['separator'] * (i + 1)
                elif params['axis'] == 'z':
                    current_start.z = getattr(params['start'], params['axis']) + params['separator'] * i
                    current_end.z = getattr(params['start'], params['axis']) + params['separator'] * (i + 1)

                sides = params['sides']
                scale = params['scale']
                name = params['facade_name']

                facade = BinaryFacade(room, flags, current_start, current_end, sides, scale, name)
                facades.append(facade)
        
        with open(filename, mode='wb') as f:
            f.write(struct.pack('<I', len(facades)))
            for facade in facades:
                f.write(facade.to_bytes())
        shutil.move(filename, os.path.join(target_fcd_dir, filename))
        
        if debug_facade:
            debug_filename = filename.replace('.FCD', '_FCD_debug.txt')
            with open(os.path.join(os.getcwd(), debug_filename), mode='w', encoding='utf-8') as f:
                for facade in facades:
                    f.write(str(facade))
                        
##########################################################################################
################################################################################################################### 

# Write COMMANDLINE
def write_commandline(city_name: str, destination_folder: str):
    city_name = city_name.lower()
    cmd_file = "commandline.txt"
    with open(cmd_file, "w") as file:
        file.write(f"-path ./dev -allrace -allcars -f -heapsize 499 -multiheap -maxcops 100 -speedycops -l {city_name}")

    shutil.move(cmd_file, os.path.join(destination_folder, cmd_file))
        
# Start GAME
def start_game(destination_folder, play_game=False):
    game_path = os.path.join(destination_folder, shortcut_or_exe_name)
    if play_game:
        subprocess.run(game_path, cwd=destination_folder, shell=True)
        
##########################################################################################  

# FACADE NOTES
# The "room" should match the bound_number in which the Facade is located.
# Separator: (max_x - min_x) / separator(value) = number of facades
# Sides: unknown, but leave it as is
# Scale: unknown, stretch each facade or thin it oute
# Facade_name: name of the facade in the game files

# For a list of facades, check out the /__Useful Documents/CHICAGO_unique_FCD_SCALES.txt
# Here you will also find the Scale values for each facade that was used in the original game.
   
# SET FCD
fcd_one = {
	'room': 1,
	'flags': 35,
	'start': Vector3(-60, 0.0, -30.0),
	'end': Vector3(-25, 0.0, -30.0),
	'sides': Vector3(28.465626,28.465626,0),
	'separator': 10, 
	'facade_name': "dfhotel01",
	'scale': 30.0,
	'axis': 'y'}

fcd_two = {
	'room': 1,
	'flags': 35,
	'start': Vector3(10, 0.0, -30.0),
	'end': Vector3(10, 0.0, -60.0),
	'sides': Vector3(28.465626,28.465626,0),
	'separator': 10, 
	'facade_name': "ofbldg02",
	'scale': 9,
	'axis': 'y'}

fcd_list = [fcd_one, fcd_two]

# Few examples:
# ofbldg02
# dt11_front
# tunnel01
# t_rail01
# ramp01
# tunnel02

###################################################################################################################
###################################################################################################################

# AI PATH NOTES
# Intersection Types: 
# 0 = Stop, 1 = Traffic Light, 2 = Yield, 3 = Continue

# Other Types:
# 0 = No, 1 = Yes

data_street_1 = {
    "street_name": "shortcut1",
    "vertices": [
        (0, 16.0, 0.0),
        (0, 16.0, -10.0),
        (0, 16.0, -15.0),
        (0, 16.0, -45.0),
        (0, 16.0, -75.0),
        (0, 16.0, -80.0),
        (0, 16.0, -85.0)]}

data_street_2 = {
    "street_name": "shortcut2",
    "vertices": [
        (0, 16.0, 0.0),
        (0, 16.0, 10.0),
        (0, 16.0, 15.0),
        (0, 16.0, 45.0),
        (0, 16.0, 75.0),
        (0, 16.0, 80.0),
        (0, 16.0, 85.0)]}

data_street_3 = {
    "street_name": "shortcut3",
    "vertices": [
        (0, 16.0, 0.0),
        (-10, 16.0, 0.0),
        (-15, 16.0, 0.0),
        (-45, 16.0, 0.0),
        (-75, 16.0, 0.0),
        (-80, 16.0, 0.0),
        (-85, 16.0, 0.0)]}

data_street_4 = {
    "street_name": "shortcut4",
    "vertices": [
        (0, 16.0, 0.0),
        (10, 16.0, 0.0),
        (15, 16.0, 0.0),
        (45, 16.0, 0.0),
        (75, 16.0, 0.0),
        (80, 16.0, 0.0),
        (85, 16.0, 0.0)]}

# Put all your created Streets in this list
street_data = [data_street_1, data_street_2, data_street_3, data_street_4]

# Example of passing all parameters
# data_street_something = {
#     "street_name": "highway_path_1",
#     "vertices": [
#         (-80.1, 11.2, 760.0),
#         (-40.6, 9.8, 730.7),
#         (-10.3, 10.1, 690.8),
#         (5.5, 7.3, 650.6),
#         (20.2, 6.0, 620.7)],
#     "intersection_types": [1, 1],
#     "stop_light_names": ["tplttrafcdual", "tplttrafcdual"],
#     "stop_light_positions": [
#         (-80.1, 11.2, 760.0),
#         (-40.6, 9.8, 730.7),
#         (-10.3, 10.1, 690.8),
#         (5.5, 7.3, 650.6)],
#         "traffic_blocked": [0, 0],
#         "ped_blocked": [0, 0],
#         "road_divided": 0,
#         "alley": 0}

################################################################################################################               

# Multiple props, "tp_barricade"
#prop_2 = {'offset_x': -30, 
#          'offset_y': 0.0, 
#          'offset_z': -10, 
#          'name': 'tp_barricade', 
#          
#          'end_offset_z': -100, 
#          'separator': 'tp_trailer', 
#          'axis': 'z',
#
#          'face_x': 10, 
#          'face_y': 0.0, 
#          'face_z': -40000,
#          
#          'rounding': 'up'}

# Single Prop tree
prop_1 = {'offset_x': 11, 
          'offset_y': 15.0, 
          'offset_z': -11, 
          'face_x': 11, 
          'face_y': 15.0, 
          'face_z': -12, 
          'name': 'tp_tree15m'}

prop_2 = {'offset_x': 11, 
          'offset_y': 15.0, 
          'offset_z': -79, 
          'face_x': 11, 
          'face_y': 15.0, 
          'face_z': -78, 
          'name': 'tp_tree15m'}

prop_3 = {'offset_x': 39.4, 
          'offset_y': 15.0, 
          'offset_z': -12, 
          'face_x': 39.4, 
          'face_y': 15.0, 
          'face_z': -16, 
          'name': 'tpbench_mall'}

prop_4 = {'offset_x': 39.4, 
          'offset_y': 15.0, 
          'offset_z': -15, 
          'face_x': 39.4, 
          'face_y': 15.0, 
          'face_z': -19, 
          'name': 'tpbench_mall'}

prop_5 = {'offset_x': 39.4, 
          'offset_y': 15.0, 
          'offset_z': -17.5, 
          'face_x': 39, 
          'face_y': 15.0, 
          'face_z': -22, 
          'name': 'tpplanter_mall'}

prop_6 = {'offset_x': 39.4, 
          'offset_y': 15.0, 
          'offset_z': -78, 
          'face_x': 39.4, 
          'face_y': 15.0, 
          'face_z': -77, 
          'name': 'tpbench_mall'}

prop_7 = {'offset_x': 39.4, 
          'offset_y': 15.0, 
          'offset_z': -75, 
          'face_x': 39.4, 
          'face_y': 15.0, 
          'face_z': -77, 
          'name': 'tpbench_mall'}

prop_8 = {'offset_x': 39.4, 
          'offset_y': 15.0, 
          'offset_z': -72.5, 
          'face_x': 39, 
          'face_y': 15.0, 
          'face_z': -77, 
          'name': 'tpplanter_mall'}

prop_list = [prop_1, prop_2, prop_3, prop_4, prop_5, prop_6, prop_7, prop_8]

################################################################################################################     

# SET MATERIALS
# Set Material Index (available numbers: 94, 95, 96, 97, 98), also see: https://tinyurl.com/y2d56pa6
set_material_index = 98

# See folder: /Useful documents/PHYSICS.DB_extracted.txt for more information
properties = {"friction": 0.12, 
              "elasticity": 10, 
              "drag": 10.01}

################################################################################################################   

# Call FUNCTIONS
print("\n===============================================")
print("\nGenerating " + f"{race_locale_name}... \n")
print("===============================================\n")

# Material related
materials = MaterialEditor.read_binary(input_physics_file)
MaterialEditor.change_physics_db(input_physics_file, output_physics_file, properties, set_material_index - 1)
new_physics_path = os.path.join(physics_folder, output_physics_file)
shutil.move(output_physics_file, new_physics_path)

# AI related
street_names = []
for data in street_data:
    creator = StreetFileEditor(city_name, data, ai_streets)
    street_names.append(data["street_name"])
BAI_Editor(city_name, street_names, ai_map)

# Main functions
create_folder_structure(city_name)
distribute_generated_files(city_name, bnd_hit_id, 
                           num_blitz, blitz_waypoints, num_circuit, circuit_waypoints, num_checkpoint, checkpoint_waypoints, all_races_files=True)

move_dev(mm1_folder, city_name)
move_custom_textures()

create_ext_file(city_name, all_polygons_picture) 
create_anim(city_name, anim_data, set_anim)   
create_bridges(bridges, set_bridges) 
create_facades(created_fcd_file, fcd_list, target_fcd_dir, set_facade, debug_facade)
bng_writer.add_props(prop_list)
bng_writer.write_props(set_props)        

# HUD offset for Moronville is approx., x=-22.4, y=-40.7; automated alignment is not implemented yet
plot_polygons(debug_hud=debug_hud, show_label=False, plot_picture=False, export_jpg=True, 
              x_offset=-22.4, y_offset=-40.7, line_width=0.3, 
              background_color='black')


create_ar_file(city_name, mm1_folder, delete_shop)
write_commandline(city_name, mm1_folder)

print("\n===============================================")
print("\nSuccesfully created " + f"{race_locale_name}!\n")
print("===============================================\n")

start_game(mm1_folder, play_game)
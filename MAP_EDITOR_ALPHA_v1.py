
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
import bpy
import csv
import math
import shutil
import struct
import random
import textwrap
import subprocess
import numpy as np            
from pathlib import Path  
from typing import List, Dict, Union, Tuple, Optional, BinaryIO
import matplotlib.pyplot as plt                
import matplotlib.transforms as mtransforms    


#! SETUP I (Map Name and Directory)             Control + F    "city=="  to jump to The City Creation section
city_name = "First_City"                        # One word (no spaces)  --- name of the .ar file
race_locale_name = "My First City"              # Can be multiple words --- name of the city in the Race Locale Menu
mm1_folder = r"C:\Users\robin\Desktop\MM1_game" # Path to your MM1 folder (A custom Open1560 version is automatically copied to this folder)


#* SETUP II (Map Creation)      
play_game = True                # change to "True" to immediately start the game after the Map is created (defaults to False when importing to Blender)
delete_shop = True              # change to "True" to delete the raw city files after the .ar file has been created
no_ui = False                   # change to "True" if you want skip the game's menu and go straight into Cruise mode
no_ui_type = "cruise"           # other race types are currently not supported by the game in custom maps

set_props = True                # change to "True" if you want PROPS
set_facades = True              # change to "True" if you want FACADES

set_anim = True                 # change to "True" if you want ANIMATIONS (plane and eltrain)
set_bridges = True              # change to "True" if you want BRIDGES

set_minimap = True              # change to "True" if you want a MINIMAP (defaults to False when importing to Blender) ## w.i.p.

ai_map = True                   # change both to "True" if you want AI paths ## (do not change this to "False")
ai_streets = True               # change both to "True" if you want AI paths ## (do not change this to "False")
ai_reverse = False              # change to "True" if you want to automatically add a reverse AI path for each lane
lars_race_maker = False         # change to "True" if you want to create "lars race maker" 

# You can add multiple Cruise Start positions here (as backup), only the last one will be used
cruise_start_pos = (35.0, 31.0, 10.0) 
cruise_start_pos = (60.0, 27.0, 330.0)
cruise_start_pos = (0.0, 0.0, 0.0)

randomize_textures = False      # change to "True" if you want to randomize all textures in your Map
random_textures = ["T_WATER", "T_GRASS", "T_WOOD", "T_WALL", "R4", "R6", "OT_BAR_BRICK", "FXLTGLOW"]

# Blender
import_to_blender = False
dds_directory = Path.cwd() / 'DDS' # w.i.p., this folder contains all the DDS textures

# Debug
debug_bounds = False            # change to "True" if you want a BOUNDS Debug text file
debug_props = False             # change to "True" if you want a PROPS Debug text file
debug_facades = False           # change to "True" if you want a FACADES Debug text file
debug_physics = False           # change to "True" if you want a PHYSICS Debug text file
debug_portals = False           # change to "True" if you want a PORTALS Debug text file
DEBUG_BMS = False               # change to "True" if you want BMS Debug text files (in folder "_Debug_BMS")
round_debug_values = True       # change to "True" if you want to round (some) debug values to 2 decimals

# HUD
shape_outline_color = None      # change to any other color (e.g. 'Red'), if you don't want any color, set to 'None'         
debug_hud = False               # change to "True" if you want a HUD Debug jpg file (defaults to True when "lars_race_maker" is set to True)
debug_hud_bound_id = False      # change to "True" if you want to see the Bound ID in the HUD Debug jpg file

# Advanced
quiet_logs = False              # change to "True" if you want to hide most logs, the game prints a ton of warnings and errors if e.g. an AI car can't find its path, causing FPS drops
empty_portals = False           # change to "True" if you want to create an empty portal file (used for testing very large cities)
truncate_cells = False			# change to "True" if you want to truncate the characters in the cells file (used for testing very large cities)

################################################################################################################               
################################################################################################################

# Race Data Constants
# Time & Weather
MORNING, NOON, EVENING, NIGHT = 0, 1, 2, 3  
CLEAR, CLOUDY, RAIN, SNOW = 0, 1, 2, 3     

# Opponent Count
MAX_OPP_8 = 8 
MAX_OPP_128 = 128 

# Cop Behavior
FOLLOW, ROADBLOCK, SPINOUT, PUSH, MIX = 0, 3, 4, 8, 15   

# Cop Start Lane
STATIONARY = 0 
IN_TRAFFIC = 2

# Waypoint Rotation
ROT_S = 179.99
ROT_W = -90
ROT_E = 90
ROT_N = 0.01
ROT_AUTO = 0

# Waypoint Width
LANE_4 = 15
LANE_6 = 19
LANE_ALLEY = 3

# Circuit Laps
LAPS_2 = 2
LAPS_3 = 3
LAPS_5 = 5
LAPS_10 = 10

# Race Types
CRUISE = "ROAM"
BLITZ = "BLITZ"
RACE = "RACE"
CIRCUIT = "CIRCUIT"
COPS_N_ROBBERS = "COPSANDROBBERS"

# Modes
SINGLE = "SINGLE"
MULTI = "MULTI"
ALL_MODES = "All Modes"

# Misc
HUGE = 100000000000

# Player Cars (also usable as Opponent cars, Cop cars, and Props)
VW_BEETLE = "vpbug"
CITY_BUS = "vpbus"
CADILLAC = "vpcaddie"
CRUISER = "vpcop"
FORD_F350 = "vpford"
FASTBACK = "vpbullet"
MUSTANG99 = "vpmustang99"
ROADSTER = "vppanoz"
PANOZ_GTR1 = "vppanozgt"
SEMI = "vpsemi"

# Ambient Cars (also usable as Opponent cars, Cop cars, and Props)
TINY_CAR = "vacompact"
SEDAN_SMALL = "vasedans"
SEDAN_LARGE = "vasedanl"

SMALL_VAN = "vavan"
PICKUP = "vapickup"
DELIVERY_VAN = "vadelivery"
LARGE_TRUCK = "vadiesels"

YELLOW_TAXI = "vataxi"
GREEN_TAXI = "vataxicheck"

WHITE_LIMO = "valimo"
BLACK_LIMO = "valimoangel"

TRAFFIC_BUS = "vabus"
PLANE_SMALL = "vaboeing_small"

# Props
BRIDGE_SLIM = "tpdrawbridge04"      #* dimension: x: 30.0 y: 5.9 z: 32.5
BRIDGE_WIDE = "tpdrawbridge06"      #* dimension: x: 40.0 y: 5.9 z: 32.5
CROSSGATE = "tpcrossgate06"
BRIDGE_BUILDING = "tpbridgebuild"

TRAILER = "tp_trailer"
BARRICADE = "tp_barricade"
TREE_SLIM = "tp_tree10m"
TREE_WIDE = "tp_tree15m"
SAILBOAT = "tpsailboat"
CHINATOWN_GATE = "cpgate"

BIN = "tptcanc"
CONE = "tpcone"
BENCH = "tpbench"
DUMPSTER = "tpdmpstr"
CRASH_CAN = "tpcrshcan"
TRASH_BOXES = "tptrashalley02"

PLANT = "tpplanter_mall"
MAILBOX = "tpmail"
BUS_STOP = "tpsbus"
PHONE_BOOTH = "optbooth"

SIDEWALK_LIGHT = "opstlite"
HIGHWAY_LIGHT = "tpltst"

GLASS = "dp01wina"
WALL = "dp24walla"

STOP_SIGN = "tpsstop"
WRONG_WAY = "tpwrongway"
DO_NOT_ENTER = "tpswrng"
STOP_LIGHT_SINGLE = "tplttrafc"
STOP_LIGHT_DUAL = "tplttrafcdual"

CRANE = "dp60crane"
ELTRAIN = "r_l_train"
ELTRAIN_SUPPORT_SLIM = "dp_left"
ELTRAIN_SUPPORT_WIDE = "dp_left6"

PLANE_LARGE = "vaboeing" # no collision
 
################################################################################################################               
################################################################################################################

#* SETUP III (optional, Race Editor)
# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints (including the start position), the number of waypoints for Circuits and Checkpoints is unlimited
# The max number of laps in Circuit races is 10

# Race Names
blitz_race_names = ["Chaotic Tower"]
circuit_race_names = ["City Lapper"]
checkpoint_race_names = ["Photo Finish"]

# Races
race_data = {
    BLITZ: {
        0: {
            'waypoints': [
                #! (x, y, z, rotation, width)
                [0.0, 0.0, 55.0, ROT_N, 12.0], 
                [0.0, 0.0, 15.0, ROT_N, 12.0], 
                [0.0, 0.0, -40.0, ROT_N, 12.0], 
                [0.0, 0.0, -130.0, ROT_N, 12.0], 
                ],
            'mm_data': {
                #! TimeofDay, Weather, Opponents, Cops, Ambient, Peds, Checkpoints, TimeLimit (s) (8 arguments)
                #* N.B.: if you set 4 'waypoints', you should set 3 'Checkpoints' (n - 1)
                'ama': [NOON, CLOUDY, MAX_OPP_8, 1.0, 1.0, 1.0, 3, 999],        
                'pro': [EVENING, CLOUDY, MAX_OPP_8, 1.0, 1.0, 1.0, 3, 999], 
            },
            'aimap': {
                'density': 0.25,
                'num_of_police': 2,
                'police_data': [
                    #! (x, y, z, rotation, start lane, behavior)
                    f'{CRUISER} 10.0 0.0 65.0 {ROT_N} {STATIONARY} {PUSH}',
                    f'{CRUISER} -10.0 0.0 65.0 {ROT_N} {IN_TRAFFIC} {MIX}',
                ],
                'num_of_opponents': 1,
            },
            'opponent_cars': {
                VW_BEETLE:      [[5.0, 0.0, 35.0], 
                                 [5.0, 0.0, -130.0]], 
            }
        }
    },
    RACE: {
        0: {
            'waypoints': [
                # [-83.0, 18.0, -114.0, ROT_N, 12.0],
                [0.0, 245, -850, ROT_S, LANE_4], 
                [0.0, 110, -500, ROT_S, 30.0],    
                [25.0, 45.0, -325, ROT_S, 25.0],   
                [35.0, 12.0, -95.0, ROT_S, LANE_4], 
                [35.0, 30.0, 0.0, ROT_S, LANE_4], 
                [35.0, 30.0, 40.0, ROT_S, LANE_4], 
                ],
            'mm_data': {
                #! TimeofDay, Weather, Opponents, Cops, Ambient, Peds (6 arguments)
                'ama': [NOON, CLEAR, MAX_OPP_8, 1.0, 1.0, 1.0],
                'pro': [NOON, CLOUDY, MAX_OPP_8, 0.0, 0.0, 0.0],
            },
            'aimap': {
                'density': 0.2,
                'num_of_police': 0,
                'police_data': [
                    f'{CRUISER} 15.0 0.0 75.0 {ROT_N} {STATIONARY} {ROADBLOCK}',
                ],
                'num_of_opponents': 2,
            },
            'opponent_cars': {
                WHITE_LIMO:      [[-10.0, 245, -850], 
                                [0.0, 0.0, -100],
                                [-10.0, 0.0, -75.0]],
                
                BLACK_LIMO:    [[10.0, 245, -850],
                                [0.0, 0.0, -100],
                                [10.0, 0.0, -75.0]],
            }
        }
    },
    CIRCUIT: {
        0: {
            'waypoints': [
                [0.0, 0.0, 40.0, ROT_AUTO, LANE_4], 
                [10.0, 0.0, 20.0, ROT_AUTO, LANE_4], 
                [20.0, 0.0, 0.0, ROT_AUTO, LANE_4], 
                [30.0, 0.0, -20.0, ROT_AUTO, LANE_4], 
                ],
            'mm_data': {
                #! TimeofDay, Weather, Opponents, Cops, Ambient, Peds, Laps (7 arguments)
                'ama': [NIGHT, RAIN, MAX_OPP_8, 1.0, 1.0, 1.0, LAPS_2],
                'pro': [NIGHT, SNOW, MAX_OPP_8, 1.0, 1.0, 1.0, LAPS_3],
            },
            'aimap': {
                'density': 0.75,
                'num_of_police': 1,
                'police_data': [
                    f'{CRUISER} 0.0 0.0 50.0 {ROT_N} {STATIONARY} {SPINOUT}',
                ],
                'num_of_opponents': 1,
            },
            'opponent_cars': {
                CADILLAC:      [[5.0, 0.0, 35.0], 
                                [5.0, 0.0, -130.0]], 
            }
        }
    }
}


#* SETUP IV (optional, Cops and Robbers)
cnr_waypoints = [                           # set Cops and Robbers Waypoints 
    ## 1st set, Name: ... ## 
    (20.0, 1.0, 80.0),                      #? Bank / Blue Team Hideout
    (80.0, 1.0, 20.0),                      #? Gold
    (20.0, 1.0, 80.0),                      #? Robber / Red Team Hideout
    ## 2nd set, Name: ... ## 
    (-90.0, 1.0, -90.0),
    (90.0, 1.0, 90.0),
    (-90.0, 1.0, -90.0)]


#* SETUP V (optional, Animations)
anim_data = {
    'plane': [                  # you can only use "plane" and "eltrain", other objects will not work
        (450, 30.0, -450),      # you can only have one Plane and/or one Eltrain
        (450, 30.0, 450),       # you can set any number of coordinates for your path(s)
        (-450, 30.0, -450),     
        (-450, 30.0, 450)], 
    'eltrain': [
        (180, 25.0, -180),
        (180, 25.0, 180), 
        (-180, 25.0, -180),
        (-180, 25.0, 180)]}


#* SETUP VI (optional, Bridges)
bridge_object = "vpmustang99"       # you can pass any object

#! Structure: (x,y,z, orientation, bridge number, bridge object)
# N.B.: you can set a maximum of 1 bridge per cull room, which may have up to 5 attributes
bridges = [
    ((-50.0, 0.01, -100.0), 270, 2, BRIDGE_WIDE, [
    ((-50.0, 0.15, -115.0), 270, 2, CROSSGATE),
    ((-50.0, 0.15, -85.0), -270, 2, CROSSGATE)
    ]),  
    ((-119.0, 0.01, -100.0), "H.E", 3, BRIDGE_WIDE, [
    ((-119.0, 0.15, -115.0), 270, 3, CROSSGATE),
    ((-119.0, 0.15, -85.0), -270, 3, CROSSGATE)
    ]),
] 

# Here's how you set a bridge without any attributes
# ((-119.01, 0.01, -100.0), "H.E", 3, BRIDGE_WIDE, [])

# Supported orientations
f"""
    'V', 'V.F', 'H.E', 'H.W', 'N.E', 'N.W', 'S.E', or 'S.W'.
    Where 'V' is vertical, 'H' is horizontal, 'F' is flipped, and e.g. 'N.E' is (diagonal) North East.
    Or you can manually set the orientation in degrees (0 - 360).
"""


#* SETUP VII (optional, Custom Bridge Configs)
bridge_race_0 = {
    "RaceType": RACE, 
    "RaceNum": "0", 
    "BridgeOffGoal": 0.50, 
    "BridgeOnGoal": 0.50,
    "GateDelta": 0.40,
    "GateOffGoal": -1.57,
    "GateOnGoal": 0.0,
    "BridgeOnDelay": 7.79,
    "GateOffDelay": 5.26 ,
    "BridgeOffDelay": 0.0,
    "GateOnDelay": 5.0,
    "Mode": SINGLE
}

bridge_cnr = {
    "RaceType": COPS_N_ROBBERS,
    "BridgeDelta": 0.20,
    "BridgeOffGoal": 0.33,
    "BridgeOnGoal": 0.33,
    "Mode": MULTI
}

# Pack all Custom Bridge Configs. for processing
bridge_configs = [bridge_race_0, bridge_cnr]

################################################################################################################               
################################################################################################################     
 
def to_do_list(x):
            """            
            SHORT-TERM:                                            
            SHAPES --> wall setting
            
            FCD --> implement diagonal facades
            
            BLENDER --> implement custom UI
            
            BAI --> improve AI paths setting
                  
            LONG-TERM:      
            TEXTURES --> UV mapping  
            
            PROPS --> investigate breakable parts in (see {}.MMBANGERDATA)
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
                
    def __repr__(self, round_values = round_debug_values):
        if round_values:
            return '{:.2f}, {:.2f}'.format(round(self.x, 2), round(self.y, 2))
        else:
            return '{:f}, {:f}'.format(self.x, self.y)

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
        
    def __repr__(self, round_values = round_debug_values):
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
    
    def Mag(self):
        return self.Mag2() ** 0.5
    
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
                 plane_edges: List[Vector3], plane_n: Vector3, plane_d: float, cell_type: int = 0, always_visible: bool = False) -> None:
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
        self.always_visible = always_visible
        
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
        if len(self.vert_indices) < 4:  # each polygon requires four vertex indices
            self.vert_indices += (0,) * (4 - len(self.vert_indices))
        
        write_pack(f, '<HBB4H', self.cell_id, self.mtl_index, self.flags, *self.vert_indices)

        for edge in self.plane_edges:
            edge.write(f)
            
        self.plane_n.write(f)
        write_pack(f, '<f', self.plane_d)
   
    def __repr__(self, bnd_instance, round_values = round_debug_values):
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
            f"Plane D: [{plane_d_str}]\n")
        
        
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
                
    def write_bnd_debug(self, debug_filename: str, debug_bounds: bool) -> None:
        if debug_bounds:
            with open(debug_filename, 'w') as f:
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
            f"======= Polys =======\n\n{polys_representation}\n")


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
        
    def write_bms(self, path: Path) -> None:
        with open(path, 'wb') as f:
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
SHOP_CITY = BASE_DIR / 'SHOP' / 'CITY'
MOVE = shutil.move

# INITIALIZATIONS | do not change
vertices = []
hudmap_vertices = []
hudmap_properties = {}
polygons_data = []
stored_texture_names = []
texcoords_data = {}
poly_filler = Polygon(0, 0, 0, [0, 0, 0, 0], [Vector3(0, 0, 0) for _ in range(4)], Vector3(0, 0, 0), [0.0], 0)
polys = [poly_filler]

################################################################################################################ 
################################################################################################################               

# Texture Mapping for BMS files
def compute_uv(bound_number: int, mode: str = "H", tile_x: int = 1, tile_y: int = 1, tilt: float = 0,
                       angle_degrees: Union[float, Tuple[float, float]] = (45, 45),
                       custom: Optional[List[float]] = None) -> List[float]:
    
    global texcoords_data
    
    def tex_coords_rotating_repeating(tile_x: int, tile_y: int, 
                                      angle_degrees: Tuple[float, float]) -> List[float]:
        
        angle_radians = [math.radians(angle) for angle in angle_degrees]

        def rotate(x: float, y: float, angle_idx: int) -> Tuple[float, float]:
            new_x = x * math.cos(angle_radians[angle_idx]) - y * math.sin(angle_radians[angle_idx])
            new_y = x * math.sin(angle_radians[angle_idx]) + y * math.cos(angle_radians[angle_idx])
            return new_x, new_y

        coords = [
            (0, 0),
            (tile_x, 0),
            (tile_x, tile_y),
            (0, tile_y)]

        rotated_coords = [rotate(x, y, 0) if i < 2 else rotate(x, y, 1) for i, (x, y) in enumerate(coords)]
        return [coord for point in rotated_coords for coord in point]
    
    if 'entries' not in texcoords_data:
        texcoords_data['entries'] = {}
    texcoords_data['entries'][bound_number] = {'tile_x': tile_x, 'tile_y': tile_y}
    
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
        return [0, 0, 0, tile_x, tile_y, tile_x, tile_y, 0]
    elif mode == "r.V.f" or mode == "repeating_vertical_flipped":
        return [0, tile_x, 0, 0, tile_y, 0, tile_y, tile_x]
    
    # Horizontal Repeated
    elif mode == "r.H" or mode == "repeating_horizontal":
        return [0, 0, tile_x, 0, tile_x, tile_y, 0, tile_y]
    elif mode == "r.H.f" or mode == "repeating_horizontal_flipped":
        return [tile_x, 0, 0, 0, 0, tile_y, tile_x, tile_y]
    
    # TODO
    elif mode == "r.r" or mode == "rotating_repeating":
        return tex_coords_rotating_repeating(tile_x, tile_y, angle_degrees)
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
    
    # Determine the target directory
    if bound_number < 200:
        target_dir = SHOP / "BMS" / f"{city_name}LM"
    else:
        target_dir = SHOP / "BMS" / f"{city_name}CITY"
    target_dir.mkdir(parents = True, exist_ok = True)  # Ensure the directory exists
    
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
        tex_coords = compute_uv(tex_coord_mode, **tex_coord_params)
        
    single_poly = [poly_filler, poly]
    
    bms = create_bms(vertices, single_poly, texture_indices, texture_name, texture_darkness, tex_coords)
    bms.write_bms(target_dir / bms_filename)
    
    if DEBUG_BMS:
        bms.write_bms_debug(bms_filename + ".txt")
            
             
# Create BMS      
def create_bms(vertices: List[Vector3], polys: List[Polygon], texture_indices: List[int], 
               texture_name: List[str], texture_darkness: List[int] = None, tex_coords: List[float] = None):
    shapes = []
    
    for poly in polys[1:]:  # Skip the first filler polygon
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
        texture_darkness = [2] * adjunct_count  # 2 is default texture "brightness"
        
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

def initialize_bounds(vertices: List[Vector3], polys: List[Polygon]):
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


def ensure_ccw_order(vertex_coordinates: List[Vector3]):
    v1, v2, v3 = vertex_coordinates
    
    edge1 = np.subtract(v2, v1)
    edge2 = np.subtract(v3, v1)
    
    normal = np.cross(edge1, edge2)
    reference_up = np.array([0, 1, 0])
    
    dot_product = np.dot(normal, reference_up)
    
    if dot_product < 0:
        # If it's clockwise, swap the order of the vertices
        return [v1, v3, v2]
    else:
        # If it's counterclockwise, no changes needed
        return [v1, v2, v3]
    
    
def compute_normal(p1, p2, p3):
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)
    return np.cross(v1, v2)


def ensure_quad_ccw_order(vertex_coordinates):
    normal = compute_normal(*vertex_coordinates[:3])
    normal /= np.linalg.norm(normal)
    
    # Use Gram-Schmidt process to get two orthogonal vectors on the plane
    basis1 = np.array(vertex_coordinates[1]) - np.array(vertex_coordinates[0])
    basis1 -= np.dot(basis1, normal) * normal
    basis1 /= np.linalg.norm(basis1)
    basis2 = np.cross(normal, basis1)

    # Project vertices onto the plane defined by the normal
    projections = [
        (np.dot(vertex, basis1), np.dot(vertex, basis2))
        for vertex in vertex_coordinates]

    # Compute the centroid of the projected points
    centroid = np.mean(projections, axis = 0)
    
    # Compute angles of vertices relative to centroid
    delta = np.array(projections) - centroid
    angles = np.arctan2(delta[:, 1], delta[:, 0])
    
    # Sort vertices based on these angles
    sorted_indices = np.argsort(angles)
    
    return [vertex_coordinates[i] for i in sorted_indices]


def compute_plane_edgenormals(p1, p2, p3):  # Only 3 vertices are being used  
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

    num_verts = len(vertices)  # 3 for triangle, 4 for quad
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
        norm_val = np.linalg.norm(plane_edges[i][:2])  # Only first two components
        plane_edges[i][:2] /= norm_val
        plane_edges[i][2] /= norm_val
        
    edges = [Vector3(edge[0], edge[1], edge[2]) for edge in plane_edges]
    
    # Add a required empty edge for triangles to match the BND binary structure
    if len(vertices) == 3:
        edges.append(Vector3(0.0, 0.0, 0.0))
    
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
    hud_color = None, shape_outline_color = shape_outline_color,
    rotate = 0, always_visible = True, fix_faulty_quad = False):

    # Vertex indices
    base_vertex_index = len(vertices)
    
    # Store the polygon data for Blender (before any manipulation)
    polygon_info = {
        "vertex_coordinates": vertex_coordinates,
        "bound_number": bound_number,
        "material_index": material_index,
        "always_visible": always_visible,
        "rotate": rotate,
        "sort_vertices": sort_vertices,
        "cell_type": cell_type,
        "hud_color": hud_color}
    
    polygons_data.append(polygon_info)
    
    # Ensure 3 or 4 vertices
    if len(vertex_coordinates) != 3 and len(vertex_coordinates) != 4:
        error_message = f"""\n
        ***ERROR***
        Unsupported number of vertices.
        You must either set 3 or 4 coordinates per polgyon.
        """
        raise ValueError(error_message)

    if bound_number == 0 or bound_number == 200 or bound_number >= 32768:
        error_message = f"""\n
        ***ERROR***
        Bound Number must be between 1 and 199, and 201 and 32767.
        """
        raise ValueError(error_message)
    
    # Ensure Counterclockwise Winding
    if len(vertex_coordinates) == 3:
        vertex_coordinates = ensure_ccw_order(vertex_coordinates)
        
    elif len(vertex_coordinates) == 4 and fix_faulty_quad:
        vertex_coordinates = ensure_quad_ccw_order(vertex_coordinates)
           
    # Flags
    if flags is None:
        if len(vertex_coordinates) == 4:
            flags = 6
        elif len(vertex_coordinates) == 3:
            flags = 3

    # Sorting        
    if sort_vertices: 
        vertex_coordinates = sort_coordinates(vertex_coordinates)
        
    new_vertices = [Vector3(*coord) for coord in vertex_coordinates]
    vertices.extend(new_vertices)
    vert_indices = [base_vertex_index + i for i in range(len(new_vertices))]
        
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
    poly = Polygon(bound_number, material_index, flags, vert_indices, plane_edges, plane_n, plane_d, cell_type, always_visible)
    polys.append(poly)
        
    # Create JPG (for the HUD)
    hud_fill = hud_color is not None
    hudmap_vertices.append(vertex_coordinates)
    hudmap_properties[len(hudmap_vertices) - 1] = (hud_fill, hud_color, shape_outline_color, str(bound_number))
    
################################################################################################################               
################################################################################################################  

# Blender
def enable_developer_extras():
    prefs = bpy.context.preferences
    view = prefs.view
    
    # Set "Developer Extra's" if not already enabled
    if not view.show_developer_ui:
        view.show_developer_ui = True
        bpy.ops.wm.save_userpref()
        print("Developer Extras enabled!")
    else:
        print("Developer Extras already enabled!")
        
           
def adjust_3D_view_settings():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    
                    # Clip distance
                    space.clip_end = 5000.0
                    
                    # Set the shading mode to Solid
                    shading = space.shading
                    shading.type = 'SOLID'
                    
                    # Uniform Lighting
                    shading.light = 'FLAT'
                    shading.color_type = 'TEXTURE'

              
def load_all_dds_to_blender(dds_directory):
    for file_name in os.listdir(dds_directory):
        if file_name.lower().endswith(".dds"):
            texture_path = os.path.join(dds_directory, file_name)
            if texture_path not in bpy.data.images:
                bpy.data.images.load(texture_path)


def preload_all_dds_materials(dds_directory):
    for file_name in os.listdir(dds_directory):
        if file_name.lower().endswith(".dds"):
            texture_path = os.path.join(dds_directory, file_name)

            # Load the DDS texture into Blender
            if texture_path not in bpy.data.images:
                texture_image = bpy.data.images.load(texture_path)
            else:
                texture_image = bpy.data.images[texture_path]

            # Create a material using the DDS texture
            material_name = os.path.splitext(os.path.basename(texture_path))[0]
            if material_name not in bpy.data.materials:
                create_material_from_texture(material_name, texture_image)


def create_material_from_texture(material_name, texture_image):
    mat = bpy.data.materials.new(name = material_name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type = 'ShaderNodeBsdfPrincipled')
    texture_node = nodes.new(type = 'ShaderNodeTexImage')
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type = 'ShaderNodeOutputMaterial')
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])      

      
def update_uv_tiling(self, context):
    tile_x = self.tile_x
    tile_y = self.tile_y
    rotate_angle = self.rotate 

    bpy.ops.object.select_all(action = 'DESELECT')
    self.select_set(True)
    bpy.context.view_layer.objects.active = self

    # Update the UV mapping of the object based on its custom properties
    tile_uvs(self, tile_x, tile_y)
    rotate_uvs(self, rotate_angle)
    
    
def apply_dds_to_object(obj, texture_path):
    # Extract the filename (without extension) from the texture_path
    material_name = os.path.splitext(os.path.basename(texture_path))[0]
    
    # Check if the material with this name already exists
    if material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
    else:
        mat = bpy.data.materials.new(name = material_name)

    obj.data.materials.append(mat)
    obj.active_material = mat

    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type = 'ShaderNodeBsdfPrincipled')
    texture_node = nodes.new(type = 'ShaderNodeTexImage')

    texture_image = bpy.data.images.load(texture_path)
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type = 'ShaderNodeOutputMaterial')
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])

    # UV unwrap the object to fit the texture's aspect ratio
    unwrap_to_aspect_ratio(obj, texture_image)

        
def rotate_uvs(obj, angle_degrees):    
    bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Get the active UV layer of the object
    uv_layer = obj.data.uv_layers.active.data
    
    angle_rad = math.radians(angle_degrees)

    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)

    # Rotate each UV coordinate around the UV center (0.5, 0.5)
    for uv_data in uv_layer:
        u, v = uv_data.uv
        u -= 0.5
        v -= 0.5
        rotated_u = u * cos_angle - v * sin_angle
        rotated_v = u * sin_angle + v * cos_angle
        uv_data.uv = (rotated_u + 0.5, rotated_v + 0.5)


def unwrap_to_aspect_ratio(obj, image):
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Enter edit mode and select all
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    
    # Perform UV unwrap
    bpy.ops.uv.unwrap(method = 'ANGLE_BASED', margin = 0.001)
    
    # Enter UV edit mode
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj.data.uv_layers.active.active = True

    # Normalize the UVs to ensure they use the entire texture
    bbox = [obj.data.uv_layers.active.data[i].uv for i in range(len(obj.data.uv_layers.active.data))]
    uvs_min = [min(co[0] for co in bbox), min(co[1] for co in bbox)]
    uvs_max = [max(co[0] for co in bbox), max(co[1] for co in bbox)]
    
    for uv_loop in obj.data.uv_layers.active.data:
        uv_loop.uv[0] = (uv_loop.uv[0] - uvs_min[0]) / (uvs_max[0] - uvs_min[0])
        uv_loop.uv[1] = (uv_loop.uv[1] - uvs_min[1]) / (uvs_max[1] - uvs_min[1])
    
    bpy.ops.object.mode_set(mode = 'OBJECT')


def tile_uvs(obj, tile_x = 1, tile_y = 1):
    bpy.ops.object.mode_set(mode = 'OBJECT')

    # Get the active UV layer of the object
    uv_layer = obj.data.uv_layers.active.data

    # Restore original UVs
    original_uvs = obj["original_uvs"]
    for i, uv_data in enumerate(uv_layer):
        uv_data.uv[0] = original_uvs[i][0]
        uv_data.uv[1] = original_uvs[i][1]

    # Loop over each UV coordinate and scale it
    for uv_data in uv_layer:
        uv_data.uv[0] *= tile_x
        uv_data.uv[1] *= tile_y


def create_mesh_from_polygon_data(polygon_data, dds_directory = None):
    name = f"P{polygon_data['bound_number']}"
    coords = polygon_data["vertex_coordinates"]

    edges = []
    faces = [range(len(coords))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(coords, edges, faces)
    mesh.update()
    
    custom_properties = ["sort_vertices", "cell_type", "hud_color", "material_index", "always_visible"]
    for prop in custom_properties:
        if prop in polygon_data:
            obj[prop] = polygon_data[prop]
    
    if not obj.data.uv_layers:
        obj.data.uv_layers.new()

    # Retrieve the original UVs after creating the object and before tiling
    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in obj.data.uv_layers.active.data]
    obj["original_uvs"] = original_uvs
    
    bpy.types.Object.tile_x = bpy.props.FloatProperty(name = "Tile X", default = 2.0, update = update_uv_tiling)
    bpy.types.Object.tile_y = bpy.props.FloatProperty(name = "Tile Y", default = 2.0, update = update_uv_tiling)
    bpy.types.Object.rotate = bpy.props.FloatProperty(name = "Rotate", default = 0.0, update = update_uv_tiling)
    
    bound_number = polygon_data['bound_number']
    tile_x, tile_y = 1, 1  

    if bound_number in texcoords_data.get('entries', {}):
        
        tile_x = texcoords_data['entries'][bound_number].get('tile_x', 1)
        tile_y = texcoords_data['entries'][bound_number].get('tile_y', 1)
        
    obj.tile_x = tile_x
    obj.tile_y = tile_y
    
    obj.rotate = polygon_data.get('rotate', 0)

    if dds_directory:
        apply_dds_to_object(obj, dds_directory)    
        rotate_angle = polygon_data.get('rotate', 0) 

        tile_uvs(obj, tile_x, tile_y)
        rotate_uvs(obj, rotate_angle)  

        obj.data.update()
        
    # Rotate the created Blender model to match the game's coordinate system
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.transform.rotate(value = math.radians(-90), orient_axis = 'X')
    
    return obj


class UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            
            # Check if the object has the necessary custom properties
            if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "rotate"]):
                tile_x = obj["tile_x"]
                tile_y = obj["tile_y"]
                rotate_angle = obj["rotate"]

                # Update the UV mapping of the object based on its custom properties
                tile_uvs(obj, tile_x, tile_y)
                rotate_uvs(obj, rotate_angle)

        return {"FINISHED"}
    
    
class AssignCustomProperties(bpy.types.Operator):
    bl_idname = "object.assign_custom_properties"
    bl_label = "Assign Custom Properties to Polygons"
    bl_description = "Assign Custom Properties to polygons that do not have them yet"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                
                if "cell_type" not in obj:
                    obj["cell_type"] = 0
                    
                if "hud_color" not in obj:
                    obj["hud_color"] = 0
                    
                if "material_index" not in obj:
                    obj["material_index"] = 0
                
                if "sort_vertices" not in obj:
                    obj["sort_vertices"] = 0

                if "always_visible" not in obj:
                    obj["always_visible"] = 0

                if "rotate" not in obj:
                    obj["rotate"] = 0.0
                
                if "tile_x" not in obj:
                    obj["tile_x"] = 2.0
                if "tile_y" not in obj:
                    obj["tile_y"] = 2.0
                
                if "original_uvs" not in obj:
                    # Check if the object has an active UV layer, and if not, create one
                    uv_layer = obj.data.uv_layers.active
                    if uv_layer is None:
                        uv_layer = obj.data.uv_layers.new(name = "UVMap")

                    # Now save the original UVs
                    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in uv_layer.data]
                    obj["original_uvs"] = original_uvs
                    
        self.report({'INFO'}, "Assigned Custom Properties")
        return {"FINISHED"}


def create_blender_meshes(import_to_blender: bool = False):
    if import_to_blender:
        enable_developer_extras()
        adjust_3D_view_settings()
        
        load_all_dds_to_blender(dds_directory)
        preload_all_dds_materials(dds_directory)
                    
        texture_paths = [os.path.join(dds_directory, f"{texture_name}.DDS") for texture_name in stored_texture_names]

        bpy.ops.object.select_all(action = 'SELECT')
        bpy.ops.object.delete()

        for polygon, texture_path in zip(polygons_data, texture_paths):
            create_mesh_from_polygon_data(polygon, texture_path)
            
            
def extract_polygon_data(obj):
    if obj.name.startswith("P"):
        bound_number = int(obj.name[1:])
    elif obj.name.startswith("Shape_"):
        bound_number = int(obj.name.split("_")[1])
    else:
        raise ValueError(f"Unrecognized object name format: {obj.name}")
    
    data = {
        "bound_number": bound_number,
        "material_index": obj["material_index"],
        "cell_type": obj["cell_type"],
        "always_visible": obj["always_visible"], 
        "sort_vertices": obj["sort_vertices"],
        "vertex_coordinates": obj.data.vertices,
        "hud_color": obj["hud_color"],
        "rotate": obj["rotate"]
        }
    
    return data


def get_dds_from_polygon(obj):
    if obj.material_slots:
        mat = obj.material_slots[0].material
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    return os.path.splitext(node.image.name)[0].replace('.DDS', '').replace('.dds', '')
    return "CHECK04"  # if no texture is applied to the polygon, use CHECK04 as a placeholder


def format_decimal(val):
    if val == int(val): 
        return f"{val:.1f}"
    else: 
        return f"{val:.2f}"


def generate_export_script(obj):
    data = extract_polygon_data(obj)
    texture_name = get_dds_from_polygon(obj)

    vertex_str = ',\n\t\t'.join(['(' + ', '.join(format_decimal(comp) for comp in vert.co) + ')' for vert in data['vertex_coordinates']])
        
    tile_x = obj.get("tile_x", 1)
    tile_y = obj.get("tile_y", 1)
    
    optional_attrs = []
    
    material_index = data['material_index']
    if material_index not in [0, '0']:
        material_str = f"material_index = {MATERIAL_MAP.get(material_index, material_index)}"
        optional_attrs.append(material_str) 

    if data['sort_vertices'] == 1:
        optional_attrs.append("sort_vertices = True")
        
    cell_type = data['cell_type']
    if cell_type in CELL_MAP:
        optional_attrs.append(f"cell_type = {CELL_MAP[cell_type]}")
    elif cell_type != 0:
        optional_attrs.append(f"cell_type = {cell_type}")
        
    if data['always_visible'] == 1:
        optional_attrs.append(f"always_visible = True")
    if data['rotate'] != 0.0:
        optional_attrs.append(f"rotate = {data['rotate']}")

    hud_color = data['hud_color']
    if hud_color not in [0, '0']:
        if hud_color in HUD_MAP:
            hud_color_str = f"hud_color = {HUD_MAP[hud_color]}"
        else:
            hud_color_str = f"hud_color = '{hud_color}'"
        optional_attrs.append(hud_color_str)
    
    optional_strs = ",\n\t".join(optional_attrs)

    # Construct export string
    export_data = f"""
create_polygon(
    bound_number = {data['bound_number']},
    {optional_strs},
    vertex_coordinates = [
        {vertex_str}])

save_bms(
    texture_name = ["{texture_name}"],
    tex_coords = compute_uv(bound_number = {data['bound_number']}, mode = "r.H", tile_x = {tile_x}, tile_y = {tile_y}))
"""

    return export_data


class ExportBlenderPolygons(bpy.types.Operator):
    bl_idname = "script.export_blender_polygons"
    bl_label = "Export Blender Polygons"
    
    select_all: bpy.props.BoolProperty(default = True)

    def execute(self, context):
        output_folder = "Blender_Export"
        
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
        
        base_file_name = "Map_Editor_Blender_Export.txt"
        export_file = os.path.join(output_folder, base_file_name)
        
        count = 1
        while os.path.exists(export_file):
            export_file = os.path.join(output_folder, f"{count}_{base_file_name}")
            count += 1
        
        # Conditionally select all meshes or use selected ones based on the 'select_all' property
        if self.select_all:
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        else:
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        
        if mesh_objects:
            context.view_layer.objects.active = mesh_objects[0]

            # Apply location transformation (to get Global coordinates)
            bpy.ops.object.transform_apply(location = True, rotation = False, scale = True)
    
        try:
            with open(export_file, 'w') as file:
                for obj in mesh_objects:
                    export_script = generate_export_script(obj) 
                    file.write(export_script + '\n\n')
                    
            subprocess.Popen(["notepad.exe", export_file])
            self.report({'INFO'}, f"Saved data to {export_file}")
            bpy.ops.object.select_all(action = 'DESELECT')
            
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
                
def set_blender_keybinding(import_to_blender: bool = False):
    if import_to_blender:
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = wm.keyconfigs.addon.keymaps.new(name = 'Object Mode', space_type = 'EMPTY')
            
            # Shift + E to export all polygons
            kmi_export_all = km.keymap_items.new("script.export_blender_polygons", 'E', 'PRESS', shift = True)
            kmi_export_all.properties.select_all = True
            
            # Ctrl + E to export selected polygons
            kmi_export_selected = km.keymap_items.new("script.export_blender_polygons", 'E', 'PRESS', ctrl = True)
            kmi_export_selected.properties.select_all = False
            
            # Shift + P to assign custom properties
            kmi_assign_properties = km.keymap_items.new("object.assign_custom_properties", 'P', 'PRESS', shift = True)

################################################################################################################               
################################################################################################################ 

#? ==================CREATING YOUR CITY================== #?

def user_notes(x):
    f""" 
    Please find some Polygons and Texture examples below this text.
    You can already run this the script and create the Test Map yourself
    
    If you're setting a (flat) Quad, make sure the vertices are in the correct order (both clockwise and counterclockwise are accepted)
    If you're unsure, set "sort_vertices = True" in the "create_polygon()" function
    
    For the Material Index (optional variable, defaults to 0), you can use the constants under 'Material types'.    
    Note that you can also set custom Material / Physics  Properties (search for: 'new_physics_properties' in the script)
    
    Texture (UV) mapping examples:
    tex_coords = compute_uv(mode = "r.V", tile_x = 4, tile_y = 2))
    tex_coords = compute_uv(mode = "r.r", tile_x = 3, tile_y = 3, angle_degrees = (45, 45))) // unfinished
    
    Allowed values are: 
    'H', 'horizontal', 'H.f', 'horizontal_flipped',
    'V', 'vertical', 'V.f', 'vertical_flipped', 'r.H', 'repeating_horizontal',
    'r.H.f', 'repeating_horizontal_flipped', 'r.V', 'repeating_vertical',
    'r.V.f', 'repeating_vertical_flipped', 'r.r', 'rotating_repeating',
    'custom', and 'combined'
    
    The variable "texture_darkness" in the function "save_bms()" makes the texture edges darker / lighter. 
    If there are four vertices, you can for example set: "texture_darkness = [40,2,50,1]"
    Where 2 is the default value. I recommend trying out different values to get an idea of the result in-game.
        
    To properly set up the AI, adhere to the following for 'bound_number = x':
    Open Areas: 0-199
    Roads: 201-859
    Intersections: 860+
    """
    
# Material types
GRASS_MTL = 87
WATER_MTL = 91
STICKY_MTL = 97
NO_FRICTION_MTL = 98 

# Cell / Room types
TUNNEL = 1
INDOORS = 2
WATER_DRIFT = 4         # only works with 'T_WATER{}' textures
NO_SKIDS = 200 

# HUD map colors (feel free to add more)
WOOD_HUD = '#7b5931'
SNOW_HUD = '#cdcecd'
WATER_HUD = '#5d8096' 
ROAD_HUD = '#414441'  
GRASS_HUD = '#396d18'
DARK_RED = '#af0000'
ORANGE = "#ffa500"
LIGHT_RED = "#ff7f7f"
LIGHT_YELLOW = '#ffffe0'


# Road types
LANDMARK = 0
STREET = 201
INTERSECTION = 860

# Blender Export Mapping
MATERIAL_MAP = {
    GRASS_MTL: "GRASS_MTL",
    WATER_MTL: "WATER_MTL",
    NO_FRICTION_MTL: "NO_FRICTION_MTL"}

CELL_MAP = {
    TUNNEL: "TUNNEL",
    INDOORS: "INDOORS",
    WATER_DRIFT: "WATER_DRIFT",
    NO_SKIDS: "NO_SKIDS"}

HUD_MAP = {
    WOOD_HUD: "WOOD_HUD",
    SNOW_HUD: "SNOW_HUD",
    WATER_HUD: "WATER_HUD",
    ROAD_HUD: "ROAD_HUD",
    GRASS_HUD: "GRASS_HUD",
    DARK_RED: "DARK_RED",
    ORANGE: "ORANGE",
    LIGHT_RED: "LIGHT_RED",
    LIGHT_YELLOW: "LIGHT_YELLOW"}
    
    
#! N.B.:
#! The 'bound_number' can not be equal to 0, 200, be negative, or be greater than 32767

#! ======================== MAIN AREA ======================== #*

# Main Area Colored Checkpoints
create_polygon(
    bound_number = 30000,
    always_visible = True, 
    vertex_coordinates = [
        (-25.0, 0.0, 85.0),
        (25.0, 0.0, 85.0),
        (25.0, 0.0, 70.0),
        (-25.0, 0.0, 70.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["CHECK04"],
    tex_coords = compute_uv(bound_number = 30000, mode = "r.H", tile_x = 4, tile_y = 1))

# Main Area w/ Building | Road
create_polygon(
    bound_number = 201,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
        (50.0, 0.0, 70.0),
        (50.0, 0.0, -70.0),
        (-50.0, 0.0, -70.0)],
        rotate = 120,
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"],
    texture_darkness = [40, 2, 50, 1],
    tex_coords = compute_uv(bound_number = 201, mode = "r.V", tile_x = 10, tile_y = 10))

# Main Grass Area | Intersection 
create_polygon(
	bound_number = 861,
	material_index = GRASS_MTL,
    sort_vertices = True,
	vertex_coordinates = [
		(10.0, 0.0, -70.0),
		(-50.0, 0.0, -70.0),
		(-50.0, 0.0, -130.0),
		(10.0, 0.0, -130.0)],
        hud_color = GRASS_HUD)

save_bms(
    texture_name = ["24_GRASS"], 
    tex_coords = compute_uv(bound_number = 861, mode = "r.V", tile_x = 7, tile_y = 10))

# Main Grass Area Brown | Road
create_polygon(
	bound_number = 202,
	material_index = GRASS_MTL,
    sort_vertices = True,
	vertex_coordinates = [
		(50.0, 0.0, -70.0),
		(10.0, 0.0, -70.0),
		(10.0, 0.0, -130.0),
		(50.0, 0.0, -130.0)],
        hud_color = WATER_HUD)

save_bms(
    texture_name = ["T_GRASS_WIN"], 
    tex_coords = compute_uv(bound_number = 202, mode = "r.V", tile_x = 3, tile_y = 10))

# Main Snow Area | Landmark (change?)
create_polygon(
	bound_number = 1,
    material_index = NO_FRICTION_MTL,
    cell_type = NO_SKIDS,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)],
         hud_color = SNOW_HUD)

save_bms(
    texture_name = ["SNOW"], 
    tex_coords = compute_uv(bound_number = 1, mode = "r.V", tile_x = 10, tile_y = 10))

# Main Barricade Area | Intersection 
create_polygon(
	bound_number = 862,
    cell_type = TUNNEL,
	vertex_coordinates = [
		(50.0, 0.0, -70.0),
		(140.0, 0.0, -70.0),
		(140.0, 0.0, -140.0),
		(50.0, 0.0, -140.0)],
        hud_color = DARK_RED)

save_bms(
    texture_name = ["T_BARRICADE"], 
    tex_coords = compute_uv(bound_number = 862, mode = "r.V", tile_x = 50, tile_y = 50))

# Main Wood Area | Road
create_polygon(
	bound_number = 203,
	vertex_coordinates = [
		(50.0, 0.0, 70.0),
		(140.0, 0.0, 70.0),
		(140.0, 0.0, -70.0),
		(50.0, 0.0, -70.0)],
        hud_color = WOOD_HUD)

save_bms(
    texture_name = ["T_WOOD"], 
    tex_coords = compute_uv(bound_number = 203, mode = "r.V", tile_x = 10, tile_y = 10))

# Main Water Area | Landmark
create_polygon(
	bound_number = 2,
    cell_type = WATER_DRIFT,
	material_index = WATER_MTL,
    sort_vertices = True,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)],
        hud_color = WATER_HUD)

save_bms(
    texture_name = ["T_WATER_WIN"], 
    tex_coords = compute_uv(bound_number = 2, mode = "r.V", tile_x = 10, tile_y = 10))

# Main Diagonal Grass Road 
create_polygon(
    bound_number = 863,
    vertex_coordinates = [
        (-50.0, 0.0, 110.0),
        (-50.0, 0.0, 140.0),
        (220.0, 0.0, 70.0),
        (110.0, 0.0, 70.0)],
        hud_color = GRASS_HUD)

save_bms(
    texture_name = ["24_GRASS"],
    tex_coords=compute_uv(bound_number = 863, mode = "r.V", tile_x = 10, tile_y = 10))

# Triangle Brick I | Intersecton (to do)
create_polygon(
    bound_number = 204,
    cell_type = NO_SKIDS,
    always_visible = True,
    vertex_coordinates = [
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0),
        (-50.0, 0.0, 0.0)],
        hud_color = LIGHT_YELLOW)

save_bms(
    texture_name = ["OT_MALL_BRICK"],
    tex_coords = compute_uv(bound_number = 204, mode = "r.V", tile_x = 10, tile_y = 10))

# Triangle Brick II | to be decided
create_polygon(
    bound_number = 205,
    cell_type = NO_SKIDS,
    always_visible = True,
    vertex_coordinates = [
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 140.0),
        (-50.0, 0.0, 70.0)],
        hud_color = LIGHT_YELLOW)

save_bms(
    texture_name = ["OT_MALL_BRICK"],
    tex_coords = compute_uv(bound_number = 205, mode = "r.V", tile_x = 10, tile_y = 10))

# Main Orange Hill | Landmark (change?)
create_polygon(
	bound_number = 3,
    cell_type = WATER_DRIFT,
	vertex_coordinates = [
		(-50.0, 0.0, -210.0),
		(50.0, 0.0, -210.0),
		(50.0, 300.0, -1000.0),
		(-50.0, 300.0, -1000.0)],
        hud_color = ORANGE)

save_bms(
    texture_name = ["T_WATER"], 
    tex_coords = compute_uv(bound_number = 3, mode = "r.V", tile_x = 10, tile_y = 100))



#! ======================== ORANGE BUILDING ======================== #*

# Orange Building Wall "South" | Landmark
create_polygon(
    bound_number = 4,
    vertex_coordinates = [
        (-10.0, 0.0, -50.0),
        (10.0, 0.0, -50.0),
        (10.0, 30.0, -50.11),
        (-10.0, 30.0, -50.11)])

save_bms(
    texture_name = ["SNOW"], # N/A
    tex_coords = compute_uv(bound_number = 4, mode = "r.V", tile_x = 1, tile_y = 1))

# Orange Building Wall "North" | Landmark
create_polygon(
    bound_number = 5,
    vertex_coordinates = [
        (-10.0, 0.0, -70.00),
        (-10.0, 30.0, -69.99),
        (10.0, 30.0, -69.99),
        (10.0, 0.0, -70.00)])

save_bms(
    texture_name = ["SNOW"], # N/A
    tex_coords = compute_uv(bound_number = 5, mode = "r.V", tile_x = 1, tile_y = 1))

# Orange Building Wall "West" | Landmark
create_polygon(
    bound_number = 6,
    sort_vertices = True,
    vertex_coordinates = [
        (-10.0, 0.0, -70.0),
        (-9.99, 30.0, -70.0),
        (-9.99, 30.0, -50.0),
        (-10.0, 0.0, -50.0)])

save_bms(
    texture_name = ["SNOW"], # N/A
    tex_coords = compute_uv(bound_number = 6, mode = "r.V", tile_x = 1, tile_y = 1))

# Orange Building Wall "East" | Landmark
create_polygon(
    bound_number = 7,
    vertex_coordinates = [
        (10.0, 0.0, -70.0),
        (9.9, 30.0, -70.0),
        (9.9, 30.0, -50.0),
        (10.0, 0.0, -50.0)])

save_bms(
    texture_name = ["SNOW"], # N/A
    tex_coords = compute_uv(bound_number = 7, mode = "r.V", tile_x = 1, tile_y = 1))

# Orange Building Rooftop | Intersection
create_polygon(
    bound_number = 900,
    vertex_coordinates = [
        (10.0, 30.0, -70.0),
        (-10.0, 30.0, -70.0),
        (-10.0, 30.0, -50.0),
        (10.0, 30.0, -50.0)])

save_bms(
    texture_name = ["SNOW"], # N/A
    tex_coords = compute_uv(bound_number = 900, mode = "r.V", tile_x = 1, tile_y = 1))



#! ======================== BRIDGES AND FREEWAY ======================== #*

# Bridge I East | Road
create_polygon(
	bound_number = 250,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-82.6, 0.0, -80.0),
		(-50.0, 0.0, -80.0),
		(-50.0, 0.0, -120.0),
		(-82.6, 0.0, -120.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RINTER"], 
    tex_coords = compute_uv(bound_number = 250, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge II West | Road
create_polygon(
	bound_number = 251,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-119.01, 0.0, -80.0),
		(-90.0, 0.0, -80.0),
		(-90.0, 0.0, -120.0),
		(-119.01, 0.0, -120.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["T_GRASS"], 
    tex_coords = compute_uv(bound_number = 251, mode = "r.V", tile_x = 5, tile_y = 5))

# Road West of West Bridge | Road
create_polygon(
	bound_number = 252,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-119.1, 0.0, -80.0),
		(-160.0, 0.0, -80.0),
		(-160.0, 0.0, -120.0),
		(-119.1, 0.0, -120.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 252, mode = "r.V", tile_x = 3, tile_y = 5))

# Intersection West of Bridges | Intersection
create_polygon(
	bound_number = 950,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-160.0, 0.0, -80.0),
		(-200.0, 0.0, -80.0),
		(-200.0, 0.0, -120.0),
		(-160.0, 0.0, -120.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RINTER"], 
    tex_coords = compute_uv(bound_number = 950, mode = "r.V", tile_x = 5, tile_y = 5))

# Far West Freeway | Road
create_polygon(
	bound_number = 253,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-164.0, 0.0, -80.0),
		(-196.0, 0.0, -80.0),
		(-196.0, 0.0, 320.0),
		(-164.0, 0.0, 320.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["FREEWAY2"], 
    tex_coords = compute_uv(bound_number = 253, mode = "r.H", tile_x = 15, tile_y = 2))

# West Freeway Sidewalk I | Road
create_polygon(
	bound_number = 254,
    always_visible = True,
	vertex_coordinates = [
		(-164.0, 0.0, -80.0),
		(-164.0, 0.0, 320.0),
		(-160.0, 0.0, 320.0),
        (-160.0, 0.0, -80.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["SDWLK2"], 
    tex_coords = compute_uv(bound_number = 254, mode = "r.H", tile_x = 50, tile_y = 1))

# West Freeway Sidewalk II | Road
create_polygon(
	bound_number = 255,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-196.0, 0.0, -80.0),
		(-200.0, 0.0, -80.0),
		(-200.0, 0.0, 320.0),
		(-196.0, 0.0, 320.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["SDWLK2"], 
    tex_coords = compute_uv(bound_number = 255, mode = "r.H", tile_x = 50, tile_y = 1))

# West Freeway South Intersection | Intersection
create_polygon(
	bound_number = 951,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-160.0, 0.0, 320.0),
		(-200.0, 0.0, 320.0),
		(-200.0, 0.0, 360.0),
		(-160.0, 0.0, 360.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RINTER"], 
    tex_coords = compute_uv(bound_number = 951, mode = "r.H", tile_x = 5, tile_y = 5))

# Hill South West | Road
create_polygon(
	bound_number = 256,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-160.0, 0.0, 320.0),
		(-160.0, 0.0, 360.0),
        (0.0, 26.75, 360.0),
		(0.0, 26.75, 320.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 256, mode = "r.V", tile_x = 4, tile_y = 10))



#! ======================== BRIDGE SPLIT SOUTH SECTION ======================== #*

# Bridge Road Split | Intersection
create_polygon(
	bound_number = 925,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-79.0, 14.75, -80.0),
		(-90.0, 14.75, -80.0),
		(-90.0, 14.75, -120.0),
		(-79.0, 14.75, -120.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RINTER"], 
    tex_coords = compute_uv(bound_number = 925, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge Road South | Road
create_polygon(
	bound_number = 226,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-79.0, 14.75, -80.0),
		(-90.0, 14.75, -80.0),
		(-90.0, 14.75, -35.0),
		(-79.0, 14.75, -35.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RWALK"], 
    tex_coords = compute_uv(bound_number = 226, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge Road South Intersection | Intersection
create_polygon(
	bound_number = 926,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(-79.0, 14.75, -35.0),
		(-90.0, 14.75, -35.0),
		(-90.0, 14.75, -15.0),
		(-79.0, 14.75, -15.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RINTER"], 
    tex_coords = compute_uv(bound_number = 926, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge Road South Hill UP I | Road
create_polygon(
	bound_number = 227,
    always_visible = True,
	vertex_coordinates = [
		(-79.0, 14.75, -15.0),
		(-90.0, 14.75, -15.0),
		(-80.0, 26.75, 85.0),
		(-69.0, 26.75, 85.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RWALK"], 
    tex_coords = compute_uv(bound_number = 227, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge Road South Hill UP II | Road
create_polygon(
	bound_number = 228,
    always_visible = True,
	vertex_coordinates = [
		(-160.0, 0.0, 20.0),
		(-160.0, 0.0, 40.0),
		(-110.0, 10.0, 20.0),
        (-110.0, 10.0, 0.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["OT_SHOP03_BRICK"], 
    tex_coords = compute_uv(bound_number = 228, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge Road South Hill Freeway I | Road
create_polygon(
	bound_number = 233,
    always_visible = True,
	vertex_coordinates = [
		(-69.0, 26.75, 85.0),
		(-80.0, 26.75, 85.0),
		(0.0, 26.75, 320.0),
		(11.0, 26.75, 320.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RWALK"], 
    tex_coords = compute_uv(bound_number = 233, mode = "r.V", tile_x = 5, tile_y = 5))

# Bridge Road South Hill Freeway II | Road
create_polygon(
	bound_number = 234,
    always_visible = True,
	vertex_coordinates = [
		(-90.0, 14.75, -15.0),
		(-90.0, 14.75, -40.0),
		(-110.0, 10.0, 0.0),
		(-110.0, 10.0, 20.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RWALK"], 
    tex_coords = compute_uv(bound_number = 234, mode = "r.V", tile_x = 5, tile_y = 5))



#! ======================== ELEVATED SECTION ======================== #*

# Elevated South South Intersection | Intersection
create_polygon(
	bound_number = 952,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(80.0, 26.75, 320.0),
		(80.0, 26.75, 360.0),
		(0.0, 26.75, 360.0),
        (0.0, 26.75, 320.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["RINTER"], 
    tex_coords = compute_uv(bound_number = 952, mode = "r.V", tile_x = 5, tile_y = 5))

# Elevated South Horizontal | Road
create_polygon(
	bound_number = 300,
    sort_vertices = True,
    always_visible = True,
	vertex_coordinates = [
		(50.0, 26.75, 320.0),
		(80.0, 26.75, 320.0),
        (80.0, 26.75, 200.0),
		(50.0, 26.75, 200.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 300, mode = "r.H", tile_x = 15, tile_y = 5))

# Elevated South East Intersection | Intersection
create_polygon(
	bound_number = 953,
    always_visible = True,
	vertex_coordinates = [
		(50.0, 26.75, 200.0),
		(80.0, 26.75, 200.0),
		(50.0, 26.75, 50.0),
		(20.0, 26.75, 50.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 953, mode = "r.V", tile_x = 5, tile_y = 15))

# Elevated South East Road | Road
create_polygon(
	bound_number = 301,
    always_visible = True,
	vertex_coordinates = [
		(50.0, 26.75, 200.0),
		(80.0, 26.75, 200.0),
		(50.0, 26.75, 50.0),
		(20.0, 26.75, 50.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 301, mode = "r.V", tile_x = 5, tile_y = 15))

# Elevated East Road | Road
create_polygon(
	bound_number = 302,
    always_visible = True,
    sort_vertices = True,
	vertex_coordinates = [
		(50.0, 26.75, 50.0),
		(20.0, 26.75, 50.0),
		(20.0, 30.0, 40.0),
        (50.0, 30.0, 40.0),],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 302, mode = "r.H", tile_x = 2, tile_y = 5))



#! ======================== ORANGE BUILDING ROADS AND CONNECTION TO ELEVATED PART ======================== #*

# Building Bridge Hill | Road
create_polygon(
	bound_number = 501,
    always_visible = True,
    sort_vertices = True,
	vertex_coordinates = [
		(20.0, 12.0, -69.9),
        (50.0, 12.0, -69.9),
        (50.0, 30.0, 0.0),
        (20.0, 30.0, 0.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R6"], 
    tex_coords = compute_uv(bound_number = 232, mode = "r.H", tile_x = 2, tile_y = 3))

# Intersection Orange Building
create_polygon(
	bound_number = 1100,
    always_visible = True,
    sort_vertices = True,
	vertex_coordinates = [
		(20.0, 30.0, 0.0),
        (50.0, 30.0, 0.0),
        (50.0, 30.0, 40.0),
        (20.0, 30.0, 40.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["CT_FOOD_BRICK"], 
    tex_coords = compute_uv(bound_number = 232, mode = "r.H", tile_x = 10, tile_y = 10))

# Road To Orange Building I | Road
create_polygon(
	bound_number = 502,
    always_visible = True,
    sort_vertices = True,
	vertex_coordinates = [
		(-10.0, 30.0, 0.0),
        (20.0, 30.0, 0.0),
        (20.0, 30.0, 40.0),
        (-10.0, 30.0, 40.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["VPBUSRED_TP_BK"], 
    tex_coords = compute_uv(bound_number = 232, mode = "r.H", tile_x = 10, tile_y = 10))

# Road To Orange Building I | Road
create_polygon(
	bound_number = 503,
    always_visible = True,
    sort_vertices = True,
	vertex_coordinates = [
		(-10.0, 30.0, 0.0),
        (10.0, 30.0, 0.0),
        (10.0, 30.0, -50.0),
        (-10.0, 30.0, -50.0)],
        hud_color = ROAD_HUD)

save_bms(
    texture_name = ["R_WIN_01"], 
    tex_coords = compute_uv(bound_number = 232, mode = "r.H", tile_x = 5, tile_y = 5))



#! ======================== SPEEDBUMPS ======================== #*

# Speed Bump I | N/A
create_polygon(
	bound_number = 206,
    sort_vertices = True,
	vertex_coordinates = [
		(-50.0, 3.0, -135.0),
		(50.0, 3.0, -135.0),
		(50.0, 0.0, -130.0),
		(-50.0, 0.0, -130.0)],
         hud_color = LIGHT_RED)

save_bms(
    texture_name = ["T_STOP"], 
    tex_coords = compute_uv(bound_number = 206, mode = "r.V", tile_x = 10, tile_y = 1))

# Speed Bump II | N/A
create_polygon(
	bound_number = 207,
	vertex_coordinates = [
		(-50.0, 3.0, -135.0),
		(50.0, 3.0, -135.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)],
         hud_color = LIGHT_RED)

save_bms(
    texture_name = ["T_STOP"], 
    tex_coords = compute_uv(bound_number = 207, mode = "r.V", tile_x = 1, tile_y = 10))

# Speed Bump Triangle I | N/A
create_polygon(
	bound_number = 208,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(-50.01, 0.0, -130.0),
		(-50.0, 3.0, -135.0)])

save_bms(
    texture_name = ["T_STOP"], 
    tex_coords = compute_uv(bound_number = 207, mode = "r.V", tile_x = 30, tile_y = 30))

# Speed Bump Triangle II | N/A
create_polygon(
	bound_number = 209,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(50.01, 0.0, -130.0),
		(50.0, 3.0, -135.0)])

save_bms(
    texture_name = ["T_STOP"], 
    tex_coords = compute_uv(bound_number = 208, mode = "r.V", tile_x = 30, tile_y = 30))

# Faulty Quad for illustration purposes
create_polygon(
    bound_number = 777,
    material_index = 0,
    fix_faulty_quad = True,
    vertex_coordinates = [
        (-89.09, 0.41, -43.12),
        (-89.09, 0.41, -55.62),
        (-107.73, 0.41, -40.53),
        (-111.22, 0.41, -52.36)],
    hud_color = None)

save_bms(
    texture_name = ["CHECK04"],
    tex_coords = compute_uv(bound_number = 777, mode = "r.H", tile_x = 4, tile_y = 1))



#! ======================== HIGHWAY TUNNEL ======================== #* 

create_polygon(
	bound_number = 2220,
	vertex_coordinates = [
		(-160.0, -0.00, -120.0),
		(-200.0, -0.00, -120.0),
		(-160.0, -3.0, -160.0)],
	hud_color = ROAD_HUD)

save_bms(texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2220, mode = "r.H", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2221,
	vertex_coordinates = [
		(-200.0, -0.00, -120.0),
        (-160.0, -3.0, -160.0),
		(-200.0, -3.0, -160.0)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2221, mode = "r.V", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2222,
	vertex_coordinates = [
		(-160.0, -3.0, -160.0),
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2222, mode = "r.H", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2223,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0),
		(-191.82, -6.00, -223.82)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2223, mode = "r.V", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2224,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2224, mode = "r.H", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2225,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82),
		(-165.59, -9.00, -260.54)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2225, mode = "r.V", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2226,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2226, mode = "r.H", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2227,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54),
		(-127.21, -12.00, -286.30)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2240, mode = "r.V", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 2228,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2227, mode = "r.H", tile_x = 3.0, tile_y = 3.0))


create_polygon(
	bound_number = 2229,
	vertex_coordinates = [
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30),
		(-90.0, -15.00, -294.48)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["FREEWAY2"],
	tex_coords = compute_uv(bound_number = 2228, mode = "r.V", tile_x = 3.0, tile_y = 3.0))

create_polygon(
	bound_number = 924,
    # fix_faulty_quad = True,
    sort_vertices = True,
	always_visible = True,
	vertex_coordinates = [
		(-79.0, -15.00, -254.51),
        (-90.0, -15.00, -254.51),
        (-90.0, -15.00, -294.48),
		(-79.0, -15.00, -294.48)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["RINTER"],
	tex_coords = compute_uv(bound_number = 924, mode = "r.H", tile_x = 5.0, tile_y = 5.0))

create_polygon(
	bound_number = 923,
    fix_faulty_quad = True,
	always_visible = True,
	vertex_coordinates = [
		(-79.0, -15.00, -254.51),
		(-90.0, -15.00, -254.51),
         (-90.0, 14.75, -120.0),
		(-79.0, 14.75, -120.0)],
	hud_color = ROAD_HUD)

save_bms(
	texture_name = ["RWALK"],
	tex_coords = compute_uv(bound_number = 923, mode = "r.H", tile_x = 5.0, tile_y = 5.0))

################################################################################################################               
################################################################################################################ 

# # Create BND file
def create_bounds(vertices: List[Vector3], polys: List[Polygon], city_name: str, debug_bounds: bool = False):    
    bnd = initialize_bounds(vertices, polys)
    
    bnd_folder = SHOP / "BND"
    bnd_file = f"{city_name}_HITID.BND"
        
    with open(bnd_folder / bnd_file, "wb") as f:
        bnd.write_bnd(f)
        
    bnd.write_bnd_debug("BOUNDS_debug.txt", debug_bounds)
  
  
# Create SHOP and FOLDER structure   
def create_folders(city_name: str):
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
        os.makedirs(path, exist_ok = True)
        
        
def create_city_info(): 
    cinfo_folder = SHOP / "TUNE"
    cinfo_file = f"{city_name}.CINFO"
    
    with open(cinfo_folder / cinfo_file, "w") as f:
        localized_name = race_locale_name
        map_name = city_name.lower()
        race_dir = city_name.lower()
        blitz_names = '|'.join(blitz_race_names)
        circuit_names = '|'.join(circuit_race_names)
        checkpoint_names = '|'.join(checkpoint_race_names)

        f.write(f"""
LocalizedName={localized_name}
MapName={map_name}
RaceDir={race_dir}
BlitzCount={len(blitz_race_names)}
CircuitCount={len(circuit_race_names)}
CheckpointCount={len(circuit_race_names)}
BlitzNames={blitz_names}
CircuitNames={circuit_names}
CheckpointNames={checkpoint_names}
""")
        
                    
def copy_custom_textures(): 
    custom_texs_folder = BASE_DIR / "Custom Textures"
    dest_tex16o_folder = SHOP / "TEX16O"

    for custom_texs in custom_texs_folder.iterdir():
        shutil.copy(custom_texs, dest_tex16o_folder / custom_texs.name)


def edit_and_copy_mmbangerdata(bangerdata_properties):
    editor_tune_folder = Path(BASE_DIR) / 'Core AR' / 'TUNE'
    shop_tune_folder = Path(SHOP) / 'TUNE'

    for file in editor_tune_folder.glob('*.MMBANGERDATA'):
        if file.stem not in bangerdata_properties:
            shutil.copy(file, shop_tune_folder)
            
    for prop_key, properties in bangerdata_properties.items():
        file = editor_tune_folder / f"{prop_key}.MMBANGERDATA"
        
        if file.exists():
            with open(file, 'r') as f: 
                lines = f.readlines()

            for i, line in enumerate(lines):
                for key, new_value in properties.items():
                    if line.strip().startswith(key):
                        lines[i] = f'\t{key} {new_value}\n'
            
            tweaked_tune_files = shop_tune_folder / file.name
            with open(tweaked_tune_files, 'w') as f:
                f.writelines(lines)
                
                
def copy_core_tune_files():
    editor_tune_folder = Path(BASE_DIR) / 'Core AR' / 'TUNE'
    shop_tune_folder = Path(SHOP) / 'TUNE'
    
    non_mmbangerdata_files = [f for f in editor_tune_folder.glob('*') if not f.name.endswith('.MMBANGERDATA')]
    
    for file in non_mmbangerdata_files:
        shutil.copy(file, shop_tune_folder)
                
                
def copy_dev_folder(dest_folder, city_name):
    dev_folder = BASE_DIR / 'dev'
    dest_folder = Path(dest_folder) / 'dev'
    
    shutil.rmtree(dest_folder, ignore_errors = True)  # remove any existing AI files in the dev folder
    shutil.copytree(dev_folder, dest_folder)
    
    # Delete AI files in CWD
    ai_files = dev_folder / 'CITY' / city_name
    shutil.rmtree(ai_files, ignore_errors = True)
    
    
def copy_open1560(dest_folder):
    dest_folder = Path(dest_folder)
    open1560_folder = BASE_DIR / 'Installation Instructions' / 'Open1560'
    
    for files in open1560_folder.iterdir():
        dest_file_path = dest_folder / files.name

        # If the source file doesn't exist, skip to the next iteration
        if not files.is_file():
            continue

        # If the dest file doesn't exist or the source file is newer than the dest file, copy the files
        if not dest_file_path.exists() or files.stat().st_mtime > dest_file_path.stat().st_mtime:
            shutil.copy2(files, dest_file_path)

################################################################################################################               
################################################################################################################ 

def ordinal(n):
    if 10 <= n % 100 <= 13:
        return f"{n}th"
    return {
        1: f"{n}st",
        2: f"{n}nd",
        3: f"{n}rd",
}.get(n % 10, f"{n}th")
    
    
# List for CHECKPOINT prefixes
checkpoint_prefixes = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]

race_type_to_prefix = {
    'BLITZ': 'ABL',
    'CIRCUIT': 'CIR',
    'RACE': checkpoint_prefixes}

race_type_to_extension = {
    'RACE': '.R_',
    'CIRCUIT': '.C_',
    'BLITZ': '.B_'}


def fill_mm_date_values(race_type, user_values):
    # Default values that are common to all modes.
    default_values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    # default_values = [44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44] ## Debug
    
    # Mappings to determine which positions in default_values are replaced by user values.
    replace_positions = {
        'BLITZ': [1, 2, 3, 4, 5, 6, 7, 8],  # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit
        'CIRCUIT': [1, 2, 3, 4, 5, 6, 7],   # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps
        'RACE': [1, 2, 3, 4, 5, 6]}         # TimeofDay, Weather, Opponents, Cops, Ambient, Peds

    filled = default_values.copy()
    
    for idx, value in zip(replace_positions[race_type], user_values):
        filled[idx] = value

    # Return only the needed portion of the filled list (i.e. removing the repeated "Difficulty")
    return filled[:10]  


def write_waypoints(opp_wp_file, waypoints, race_desc, race_index, opponent_num = None):
    with open(opp_wp_file, "w") as f:
        if opponent_num is not None:
            # Opponent waypoint header
            f.write(f"This is your Opponent file for opponent number {opponent_num}, in {race_desc} race {race_index}\n")
            
            # Writing waypoints for Opponents and adding the filler values
            for waypoint in waypoints:
                waypoint_line = ', '.join(map(str, waypoint[:3])) + f", {LANE_4}, {ROT_AUTO}, 0, 0,\n"
                f.write(waypoint_line)
        else:
            # Player waypoint header
            f.write(f"# This is your {ordinal(race_index)} {race_desc} race Waypoint file\n")
            
            # Writing waypoints for players and adding the filler values
            for waypoint in waypoints:
                waypoint_line = ', '.join(map(str, waypoint)) + ",0,0,\n"
                f.write(waypoint_line)

    MOVE(opp_wp_file, SHOP / "RACE" / city_name / opp_wp_file)
    
    
def write_mm_data(mm_data_file, configs, race_type, prefix):
    with open(mm_data_file, 'w') as f:
        header = ",".join(["Description"] + 2 * ["CarType", "TimeofDay", "Weather", "Opponents", "Cops", "Ambient", "Peds", "NumLaps", "TimeLimit", "Difficulty"])
        f.write(header + "\n")
        
        for race_index, config in configs.items():
            if race_type == 'RACE':
                race_desc = prefix  
            else:
                race_desc = prefix + str(race_index)
            
            ama_filled_values = fill_mm_date_values(race_type, config['mm_data']['ama'])
            pro_filled_values = fill_mm_date_values(race_type, config['mm_data']['pro'])
                        
            data_string = race_desc + "," + ",".join(map(str, ama_filled_values)) + "," + ",".join(map(str, pro_filled_values))
            
            f.write(data_string + "\n") # Write the data string to file
            
    MOVE(mm_data_file, SHOP / "RACE" / city_name / mm_data_file)


def write_aimap(city_name, race_type, race_index, aimap_config, opponent_cars, num_of_opponents):
    aimap_file_name = f"{race_type}{race_index}.AIMAP_P"
    with open(aimap_file_name, "w") as f:
        
        aimap_content = f"""
# Ambient Traffic Density 
[Density] 
{aimap_config['density']}

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
{aimap_config['num_of_police']}
"""
        f.write(aimap_content)
        for police in aimap_config['police_data']:
            f.write(f"{police}\n")

        opp_content = f"""
# Opponent Init, Geo File, WavePoint File 
[Opponent] 
{num_of_opponents}
"""
        f.write(opp_content)
        for idx, opp_car in enumerate(opponent_cars):
            f.write(f"{opp_car} OPP{idx}{race_type}{race_index}{race_type_to_extension[race_type]}{race_index}\n")
            
    MOVE(aimap_file_name, SHOP / "RACE" / city_name / aimap_file_name)

    
    
def create_races(city_name, race_data):
    for race_type, race_configs in race_data.items():
        if race_type == 'RACE':  # For Checkpoint races
            if len(race_configs) > len(checkpoint_prefixes):
                raise ValueError("Number of Checkpoint races cannot be more than 12")
            for idx, (race_index, config) in enumerate(race_configs.items()):
                prefix = checkpoint_prefixes[race_index]
                
                # Player Waypoints with Checkpoint prefix
                write_waypoints(f"{race_type}{race_index}WAYPOINTS.CSV", config['waypoints'], race_type, race_index)
                
                # Opponent-specific Waypoints
                for opp_idx, (opp_car, opp_waypoints) in enumerate(config['opponent_cars'].items()):
                    write_waypoints(
                        f"OPP{opp_idx}{race_type}{race_index}{race_type_to_extension[race_type]}{race_index}", 
                        opp_waypoints, race_type, race_index, opponent_num=opp_idx)
                
                write_mm_data(f"MM{race_type}DATA.CSV", {race_index: config}, race_type, prefix)
                write_aimap(city_name, race_type, race_index, 
                            config['aimap'], config['opponent_cars'], 
                            num_of_opponents = config['aimap'].get('num_of_opponents', len(config['opponent_cars'])))
                
        else:  # For other race types
            prefix = race_type_to_prefix[race_type]  # Directly assign the prefix string
            for idx, config in race_configs.items():
                
                # Player Waypoints for Blizes and Circuits
                write_waypoints(f"{race_type}{idx}WAYPOINTS.CSV", config['waypoints'], race_type, idx)
                
                # Opponent-specific Waypoints
                for opp_idx, (opp_car, opp_waypoints) in enumerate(config['opponent_cars'].items()):
                    write_waypoints(
                        f"OPP{opp_idx}{race_type}{idx}{race_type_to_extension[race_type]}{idx}", 
                        opp_waypoints, race_type, idx, opponent_num=opp_idx)
                
                write_mm_data(f"MM{race_type}DATA.CSV", race_configs, race_type, prefix)
                write_aimap(city_name, race_type, idx, 
                            config['aimap'], config['opponent_cars'],
                            num_of_opponents = config['aimap'].get('num_of_opponents', len(config['opponent_cars'])))

                
def create_cnr(city_name, cnr_waypoints):
        cnr_csv_file = "COPSWAYPOINTS.CSV"
        cnr_header = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"
        cnr_filler = ",0,0,0,0,0,\n"
        
        with open(cnr_csv_file, "w") as f:
            f.write(cnr_header)
            for i in range(0, len(cnr_waypoints), 3):
                f.write(", ".join(map(str, cnr_waypoints[i])) + cnr_filler) 
                f.write(", ".join(map(str, cnr_waypoints[i+1])) + cnr_filler)
                f.write(", ".join(map(str, cnr_waypoints[i+2])) + cnr_filler)

        MOVE(cnr_csv_file, SHOP / "RACE" / city_name / cnr_csv_file)
  
_H = 8
_A2 = 32                    
                                
def create_cells(city_name: str, truncate_cells: bool = False):
    bms_files = []
    bms_a2_files = set()
    
    lm_folder = SHOP / "BMS" / f"{city_name}LM"
    city_folder = SHOP / "BMS" / f"{city_name}CITY"
    
    cells_folder = SHOP_CITY
    cells_file = cells_folder / f"{city_name}.CELLS"

    for folder in [lm_folder, city_folder]:
        for file in folder.iterdir():
            if file.name.endswith(".bms"):
                bound_number = int(re.findall(r'\d+', file.name)[0])
                bms_files.append(bound_number)
                if file.name.endswith("_A2.bms"):
                    bms_a2_files.add(bound_number)
    
    # Create the CELLS file
    with open(cells_file, "w") as f:
        f.write(f"{len(bms_files)}\n")
        f.write(str(max(bms_files) + 1000) + "\n")
        
        sorted_bms_files = sorted(bms_files)
        
        # Collect all polygons with 'always_visible' set to True
        always_visible_bound_numbers = [poly.cell_id for poly in polys if poly.always_visible]
        if 1 not in always_visible_bound_numbers:  # Ensure that 1 is always in the list
            always_visible_bound_numbers.insert(0, 1)
        always_visible_count = len(always_visible_bound_numbers)
        
        max_warning_count = 0  
        max_error_count = 0  
        
        for bound_number in sorted_bms_files:
            # Get cell type
            cell_type = None
            for poly in polys:
                if poly.cell_id == bound_number:
                    cell_type = poly.cell_type
                    break

            if cell_type is None:
                cell_type = 0
            
            # Write cells data
            if always_visible_count:
                always_visible_data = f",{always_visible_count},{','.join(map(str, always_visible_bound_numbers))}"
            else:
                always_visible_data = ",0"

            if bound_number in bms_a2_files:
                row = f"{bound_number},{_A2},{cell_type}{always_visible_data}\n"
            else:
                row = f"{bound_number},{_H},{cell_type}{always_visible_data}\n"
            
            # Check for row length and update the max warning/error count
            row_length = len(row)
            
            if truncate_cells and row_length >= 254:
                # Truncate the always_visible_bound_numbers until the row length is less than 254
                while len(row) >= 254:
                    # Remove the last element from the list
                    always_visible_bound_numbers.pop()
                    
                    # Reconstruct the always_visible_data string
                    always_visible_count = len(always_visible_bound_numbers)
                    always_visible_data = f",{always_visible_count},{','.join(map(str, always_visible_bound_numbers))}"
                    
                    # Reconstruct the row string
                    if bound_number in bms_a2_files:
                        row = f"{bound_number},{_A2},{cell_type}{always_visible_data}\n"
                    else:
                        row = f"{bound_number},{_H},{cell_type}{always_visible_data}\n"
                    
                    # Update the row length
                    row_length = len(row)

            # Update the max warning/error count based on the new row length
            if 200 <= row_length < 254:
                max_warning_count = max(max_warning_count, row_length)
            elif row_length >= 254:
                max_error_count = max(max_error_count, row_length)
            
            f.write(row)
        
        if max_error_count >= 254:
            error_message = f"""
            ***ERROR***
            Character limit of 254 exceeded in .CELLS file.
            Maximum character count encountered is {max_error_count}.
            To solve the problem, set 'always_visible' to False for some polygons.
            If the 'bound_number' is 99 (2 charachters), then it consumes 3 characters in the CELLS file.
            """
            raise ValueError(error_message)
        
        elif 200 <= max_warning_count < 254:
            warning_message = f"""
            ***WARNING***
            Close to row character limit 254 in .CELLS file. 
            Maximum character count encountered is {max_warning_count}.
            To reduce the charachter count, consider setting 'always_visible' to False for some polygons.
            If the 'bound_number' is 99 (2 charachters), then it consumes 3 characters in the CELLS file.
            *************\n
            """
            print(warning_message)
                        

# Create Animations                              
def create_animations(city_name: str, anim_data: Dict[str, List[Tuple]], set_anim: bool = False) -> None: 
    if set_anim:
        anim_folder = SHOP_CITY / city_name

        # Create ANIM.CSV file and write anim names
        with open(anim_folder / "ANIM.CSV", 'w', newline = '') as f:
            writer = csv.writer(f)
            for obj in anim_data.keys():
                writer.writerow([f"anim_{obj}"])

        # Create the individual anim files and write coordinates
        for obj, coordinates in anim_data.items():
            unique_anims = anim_folder / f"ANIM_{obj.upper()}.CSV"
            with open(unique_anims, 'w', newline = '') as file:
                writer = csv.writer(file)
                if coordinates:
                    for coordinate in coordinates:
                        writer.writerow(coordinate)
                        
                        
# Create AR file and delete folders
def create_ar(city_name: str, mm1_folder: str, delete_shop: bool = False) -> None:
    for file in Path("angel").iterdir():
        if file.name in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(file, SHOP / file.name)
    
    os.chdir(SHOP)
    ar_command = f"CMD.EXE /C run !!!!!{city_name}_City"
    subprocess.run(ar_command, shell = True)
    os.chdir(BASE_DIR)  
    
    build_dir = BASE_DIR / 'build'
    for file in build_dir.iterdir():
        if file.name.endswith(".ar") and file.name.startswith(f"!!!!!{city_name}_City"):
            MOVE(file, Path(mm1_folder) / file.name)
            
    # Delete the build folder
    try:
        shutil.rmtree(build_dir)
    except Exception as e:
        print(f"Failed to delete the BUILD directory. Reason: {e}")
    
    # Delete the SHOP folder
    if delete_shop:
        try:
            shutil.rmtree(SHOP)
        except Exception as e:
            print(f"Failed to delete the SHOP directory. Reason: {e}")


def create_hudmap(set_minimap, debug_hud, debug_hud_bound_id, shape_outline_color, import_to_blender,
                        x_offset = 0, y_offset = 0, line_width = 1, background_color = 'black') -> None:

    if set_minimap and not import_to_blender:
        global hudmap_vertices
        global hudmap_properties
        bmp_folder = SHOP / 'BMP16'
        
        min_x = min(point[0] for polygon in hudmap_vertices for point in polygon)
        max_x = max(point[0] for polygon in hudmap_vertices for point in polygon)
        min_z = min(point[2] for polygon in hudmap_vertices for point in polygon)
        max_z = max(point[2] for polygon in hudmap_vertices for point in polygon)

        width = int(max_x - min_x)
        height = int(max_z - min_z)

        def draw_polygon(ax, polygon, shape_outline_color, 
                        label = None, add_label = False, hud_fill = False, hud_color = None) -> None:
            
            xs, ys = zip(*[(point[0], point[2]) for point in polygon])
            xs, ys = xs + (xs[0],), ys + (ys[0],)  # the commas after [0] should not be removed
            
            if shape_outline_color:
                ax.plot(xs, ys, color = shape_outline_color, linewidth = line_width)
            
            if hud_fill:
                ax.fill(xs, ys, hud_color)
                
            if add_label: 
                center = calculate_center_tuples(polygon)
                ax.text(center[0], center[2], label, color = 'white', ha = 'center', va = 'center', fontsize = 4.0)

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
        plt.savefig(bmp_folder / f"{city_name}640.JPG", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.02, facecolor = background_color)
        plt.savefig(bmp_folder / f"{city_name}320.JPG", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.02, facecolor = background_color) 
            
        if debug_hud or lars_race_maker:
            fig, ax_debug = plt.subplots(figsize = (width, height), dpi = 1)
            ax_debug.set_facecolor('black')
            
            for i, polygon in enumerate(hudmap_vertices):
                hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))
                draw_polygon(ax_debug, polygon, shape_outline_color, 
                            label = bound_label if debug_hud_bound_id else None, 
                            add_label = True, hud_fill = hud_fill, hud_color = hud_color)
            
            ax_debug.axis('off')
            ax_debug.set_xlim([min_x, max_x])
            ax_debug.set_ylim([max_z, min_z])  # flip the image vertically
            ax_debug.set_position([0, 0, 1, 1])

            plt.savefig(BASE_DIR / f"{city_name}_HUD_debug.jpg", dpi = 1, bbox_inches = None, pad_inches = 0, facecolor = 'purple')


# Create EXT file                      
def create_ext(city_name, polygons):
    x_coords = [vertex[0] for poly in polygons for vertex in poly]
    z_coords = [vertex[2] for poly in polygons for vertex in poly]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_z, max_z = min(z_coords), max(z_coords)

    ext_folder = SHOP_CITY
    ext_file = f"{city_name}.EXT"

    with open(ext_folder / ext_file, 'w') as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")
        
    return min_x, max_x, min_z, max_z


def create_bridges(all_bridges, set_bridges):
    bridge_folder = SHOP_CITY
    bridge_file = f"{city_name}.GIZMO"
    
    if set_bridges:
        bridge_gizmo = bridge_folder / bridge_file
        
        if bridge_gizmo.exists():
            os.remove(bridge_gizmo)

        def calculate_facing(offset, orientation):
            if isinstance(orientation, (float, int)): 
                angle_radians = math.radians(orientation)  
                return [
                    offset[0] + 10 * math.cos(angle_radians), 
                    offset[1], 
                    offset[2] + 10 * math.sin(angle_radians)
                ]
            elif isinstance(orientation, str):
                mappings = {
                    "V": (-10, 0, 0),
                    "V.F": (10, 0, 0),
                    "H.E": (0, 0, 10),
                    "H.W": (0, 0, -10),
                    "N.E": (10, 0, 10),
                    "N.W": (10, 0, -10),
                    "S.E": (-10, 0, 10),
                    "S.W": (-10, 0, -10)
                }
                try:
                    return [offset[i] + mappings[orientation][i] for i in range(3)]
                except KeyError:
                    raise ValueError(f"""
                    Invalid Bridge Orientation.
                    Please choose from 'V', 'V.F', 'H.E', 'H.W', 'N.E', 'N.W', 'S.E', or 'S.W'.
                    Where 'V' is vertical, 'H' is horizontal, 'F' is flipped, and e.g. 'N.E' is (diagonal) North East.
                    Or set the orientation using a numeric value between 0 and 360 degrees.
                    """)
            else:
                raise TypeError("Invalid type for bridge orientation. Expected a string or a number.")

        with bridge_gizmo.open("a") as f: 
            for bridge in all_bridges:
                bridge_offset, bridge_orientation, bridge_number, bridge_object, additional_objects = bridge
                bridge_facing = calculate_facing(bridge_offset, bridge_orientation)

                drawbridge_values = f"{bridge_object},0,{bridge_offset[0]},{bridge_offset[1]},{bridge_offset[2]},{bridge_facing[0]},{bridge_facing[1]},{bridge_facing[2]}"
                
                additional_objects_lines = ""
                for obj in additional_objects:
                    obj_offset, obj_orientation, obj_id, obj_type = obj
                    obj_facing = calculate_facing(obj_offset, obj_orientation)
                    
                    additional_objects_lines += f"\t{obj_type},{obj_id},{obj_offset[0]},{obj_offset[1]},{obj_offset[2]},{obj_facing[0]},{obj_facing[1]},{obj_facing[2]}\n"

                num_fillers = 5 - len(additional_objects)
                bridge_filler = f"{CROSSGATE},0,-999.99,0.00,-999.99,-999.99,0.00,-999.99"
                bridge_fillers = "".join([f"\t{bridge_filler}\n" for _ in range(num_fillers)])
                
                bridge_data = f"""DrawBridge{bridge_number}
\t{drawbridge_values} 
{additional_objects_lines}{bridge_fillers}DrawBridge{bridge_number}"""

                if bridge_data:
                    f.write(bridge_data)
                    f.write("\n")
                    
                    
def custom_bridge_config(configs, set_bridges, tune_folder = SHOP / 'TUNE'):    
    bridge_config_template = """
mmBridgeMgr :076850a0 {{
    BridgeDelta {BridgeDelta}
    BridgeOffGoal {BridgeOffGoal}
    BridgeOnGoal {BridgeOnGoal}
    GateDelta {GateDelta}
    GateOffGoal {GateOffGoal}
    GateOnGoal {GateOnGoal}
    BridgeOnDelay {BridgeOnDelay}
    GateOffDelay {GateOffDelay}
    BridgeOffDelay {BridgeOffDelay}
    GateOnDelay {GateOnDelay}
    }}
    """

    default_config = {
        "BridgeDelta": 0.20,
        "BridgeOffGoal": 0.0,
        "BridgeOnGoal": 0.47,
        "GateDelta": 0.40,
        "GateOffGoal": -1.57,
        "GateOnGoal": 0.0,
        "BridgeOnDelay": 7.79,
        "GateOffDelay": 5.26,
        "BridgeOffDelay": 0.0,
        "GateOnDelay": 5.0,
        "Mode": SINGLE,
    }
    
    if set_bridges:
        for config in configs:
            final_config = {**default_config, **config}
            config_str = bridge_config_template.format(**final_config)
            
            race_type = final_config["RaceType"]
            filenames = []

            if race_type in [CRUISE, COPS_N_ROBBERS]:
                base_name = CRUISE if race_type == CRUISE else COPS_N_ROBBERS
                if final_config["Mode"] in [SINGLE, ALL_MODES]:
                    filenames.append(f"{base_name}.MMBRIDGEMGR")
                if final_config["Mode"] in [MULTI, ALL_MODES]:
                    filenames.append(f"{base_name}M.MMBRIDGEMGR")
            else:
                if race_type not in [RACE, CIRCUIT, BLITZ]:
                    raise ValueError(f"Invalid RaceType. Must be one of {RACE}, {CIRCUIT}, {BLITZ}, {CRUISE}, or {COPS_N_ROBBERS}.")

                if final_config["Mode"] in [SINGLE, ALL_MODES]:
                    filenames.append(f"{race_type}{final_config['RaceNum']}.MMBRIDGEMGR")
                if final_config["Mode"] in [MULTI, ALL_MODES]:
                    filenames.append(f"{race_type}{final_config['RaceNum']}M.MMBRIDGEMGR")
            
            for filename in filenames:
                (tune_folder / filename).write_text(config_str)
                
                
#!########### Code by 0x1F9F1 / Brick (Modified) ############      
                 
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
            line = Vector3(0, 0, HUGE)

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

        bb_min = Vector2( HUGE,  HUGE)
        bb_max = Vector2(-HUGE, -HUGE)

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
def prepare_portals(polys, vertices):
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
def create_portals(city_name, polys, vertices, empty_portals = False, debug_portals = False):
    portals_folder = SHOP_CITY
    portals_file = f"{city_name}.PTL"
    
    if debug_portals:
        debug_filename = "PORTALS_debug.txt"
        
        if os.path.exists(debug_filename):
            os.remove(debug_filename)
            
        debug_file = open(debug_filename, "a")
        debug_file.write("Portal Debug File\n")
        debug_file.write("=================\n")
    
    if empty_portals:
        with open(portals_folder / portals_file, 'wb') as f:
            pass
        
    else:
        _, portals = prepare_portals(polys, vertices)    
        with open(portals_folder / portals_file, 'wb') as f:
            
            write_pack(f, '<I', 0)
            write_pack(f, '<I', len(portals))    
            
            if debug_portals:
                debug_file.write(f"{len(portals)} portals prepared.\n\n")
            
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
                
                if debug_portals:
                    debug_file.write(f"Portal between Cell {cell_1} and Cell {cell_2}\n")
                    debug_file.write(f"Vertices ({v1}), ({v2})\n\n")
                    
    if debug_portals:
        debug_file.close()

#!########### Code by 0x1F9F1 / Brick (Modified) ############                   
                    
                               
# BINARYBANGER CLASS                            
class BinaryBanger:
    def __init__(self, start: Vector3, end: Vector3, name: str, room: int = 4, flags: int = 0x800):
        self.room = room
        self.flags = flags
        self.start = start
        self.end = end
        self.name = name
        
    @classmethod
    def read_bng_main(cls, f):
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
        self.debug_filename = "PROPS_debug.txt"
        self.prop_file_path = BASE_DIR / "EditorResources" / "Prop Dimensions.txt"
        self.prop_data = self.load_prop_dimensions()    
          
    def load_prop_dimensions(self):
        prop_data = {}
        
        with open(self.prop_file_path, "r") as f:
            for line in f:
                name, value_x, value_y, value_z = line.split()
                prop_data[name] = Vector3(float(value_x), float(value_y), float(value_z))
        return prop_data
    
    def read_bng_count(self):
        with open(self.filename, mode = "rb") as f:
            num_objects = read_unpack(f, '<I')[0]
            
            for _ in range(num_objects):
                self.objects.append(BinaryBanger.read_bng_main(f))
            
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
            write_pack(f, '<s', bytes(char, encoding = 'utf8'))

    def write_debug_info(self, index, obj):
        cleaned_name = obj.name.rstrip('\x00')
        
        with open(self.debug_filename, "a") as debug_f:
            debug_f.write(textwrap.dedent(f'''
                Prop {index}
                Start: {obj.start}
                End: {obj.end}
                Name: {cleaned_name}
            '''))
                      
    def add_props(self, new_objects):
        default_separator_value = 10.0
    
        for obj in new_objects:
            offset = Vector3(*obj['offset'])
            end = Vector3(*obj.get('end', obj['offset']))  
            face = obj.get('face')  
            name = obj['name']

            # Compute diagonal and its length
            diagonal = end - offset
            diagonal_length = diagonal.Mag()
            
            separator = obj.get('separator', default_separator_value)
            if isinstance(separator, str) and separator.lower() in ["x", "y", "z"]:
                prop_dims = self.prop_data.get(name, Vector3(1, 1, 1))
                separator = getattr(prop_dims, separator.lower())
                
            elif not isinstance(separator, (int, float)):
                separator = default_separator_value

            if face is None:
                # Create a facing vector that points from offset to end
                face = (Vector3(diagonal.x * 1e6, diagonal.y * 1e6, diagonal.z * 1e6))
            else:
                face = Vector3(*face)

            self.objects.append(BinaryBanger(offset, face, name + "\x00"))

            # Number of props is determined by the length of the diagonal and separator
            num_props = int(diagonal_length / separator)

            # Add objects along the diagonal
            for i in range(1, num_props):
                # Compute new offset along the diagonal
                new_offset = offset + (diagonal.Normalize() * (i * separator))
                self.objects.append(BinaryBanger(new_offset, face, name + "\x00"))
  
    def place_props_randomly(self, seed, num_objects, object_dict, x_range, z_range):
        new_objects = []

        # Ensure 'name' is a list for consistent handling later
        if isinstance(object_dict.get('name'), str):
            object_dict['name'] = [object_dict['name']]
            
        random.seed(seed)

        for name in object_dict['name']:
            for _ in range(num_objects):
                x = random.uniform(*x_range)
                z = random.uniform(*z_range)
                y = object_dict.get('offset_y', 0.0)  

                # Creating a new object dict, ensuring the name is not a list
                new_object_dict = {
                    'name': name,
                    'offset': (x, y, z)
                }

                # If face is not defined, create random face vector
                if 'face' not in object_dict:
                    face_x = random.uniform(-1e6, 1e6)
                    face_y = random.uniform(-1e6, 1e6)  # N / A
                    face_z = random.uniform(-1e6, 1e6)
                    new_object_dict['face'] = (face_x, face_y, face_z)
                else:
                    new_object_dict['face'] = object_dict['face']

                # Copy additional properties from object_dict if they exist
                for key, value in object_dict.items():
                    if key not in new_object_dict:
                        new_object_dict[key] = value

                new_objects.append(new_object_dict)
        
        return new_objects


#################################################################################
#################################################################################

# MATERIALEDITOR CLASS
class Material_Editor:
    def __init__(self, name: str, friction: float, elasticity: float, drag: float, bump_height: float, bump_width: float, bump_depth: float, sink_depth: float, 
                 type: int, sound: int, velocity: Vector2, ptx_color: Vector3):
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
    def edit_materials(cls, materials_properties, physics_output_file, debug_physics):
        physics_input_file = BASE_DIR / "EditorResources" / "PHYSICS.DB"
        physics_folder = SHOP / "MTL"
        
        with physics_input_file.open('rb') as file:
            count = read_unpack(file, '>I')[0]
            read_material_file = cls.readn(file, count)
            
        # Loop through material properties dictionary
        for material_index, properties in materials_properties.items():
            for prop, value in properties.items():
                setattr(read_material_file[material_index - 1], prop, value)
            
        cls.write_materials_file(physics_output_file, read_material_file)
        MOVE(physics_output_file, physics_folder / physics_output_file)
        
        if debug_physics:
            cls.write_debug_file("PHYSICS_DB_debug.txt", read_material_file)
   
    @classmethod
    def write_debug_file(cls, debug_filename, material_list):
        with open(debug_filename, 'w') as debug_file:
            for idx, material in enumerate(material_list):
                debug_file.write(material.__repr__(idx))
                debug_file.write("\n")

    def __repr__(self, idx = None):
        cleaned_name = self.name.rstrip("\x00 Í")
        formatted_velocity = f"x = {self.velocity.x:.2f}, y = {self.velocity.y:.2f}"
        
        header = f"AgiPhysParameters (# {idx + 1})" if idx is not None else "AgiPhysParameters"
        
        return f"""
{header}
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
    velocity    = {formatted_velocity},
    ptx_color   = {self.ptx_color}
    """


###################################################################################################################
###################################################################################################################

# AI constants
# Intersection types
STOP = 0 
STOP_LIGHT = 1 
YIELD = 2
CONTINUE = 3

# True or False for e.g. "traffic_blocked"
NO = 0
YES = 1


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

        map_data = f"""
mmMapData :0 {{
    NumStreets {len(self.streets)}
    Street [
        {streets_representation}
    ]
}}
        """
        return textwrap.dedent(map_data).strip()
       
       
# STREETFILE CLASS
class StreetFile_Editor:    
    def __init__(self, city_name, street_data, ai_reverse = False, ai_streets = ai_streets): # do not change
        self.street_name = street_data["street_name"]
        self.ai_reverse = ai_reverse

        if "lanes" in street_data:
            self.original_lanes = street_data["lanes"]
            
            if self.ai_reverse:
                self.lanes = {key: values + values[::-1] for key, values in self.original_lanes.items()}  
            else:
                self.lanes = self.original_lanes
                
        elif "vertices" in street_data:
            self.original_lanes = {"lane_1": street_data["vertices"]}
            if self.ai_reverse:
                self.lanes = {"lane_1": street_data["vertices"] + street_data["vertices"][::-1]}  
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
        num_total_vertex = num_vertex_per_lane * len(self.lanes) * (2 if self.ai_reverse else 1)
        vertex_string = '\n\t\t'.join('\n\t\t'.join(f'{vertex[0]} {vertex[1]} {vertex[2]}' for vertex in vertices) for vertices in self.lanes.values())
        
        normals_string = '\n\t\t'.join('0.0 1.0 0.0' for _ in range(num_vertex_per_lane))
        stop_light_positions_strings = '\n\t'.join(f'StopLightPos[{i}] {pos[0]} {pos[1]} {pos[2]}' for i, pos in enumerate(self.stop_light_positions))

        street_template = f"""
mmRoadSect :0 {{
    NumVertexs {num_vertex_per_lane}
    NumLanes[0] {len(self.lanes)}
    NumLanes[1] {len(self.lanes) if self.ai_reverse else 0}
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
    
    def create_streets(city_name, street_data, ai_streets, ai_reverse, ai_map):
        street_names = [StreetFile_Editor(city_name, data, ai_reverse, ai_streets).street_name for data in street_data]
        return BAI_Editor(city_name, street_names, ai_map)
        
        
def get_first_and_last_street_vertices(street_list, process_vertices = False):
    vertices_set = set()
    
    for street in street_list:
        vertices = street["vertices"]
        if vertices: # Check if the list is not empty
            vertices_set.add(vertices[0])
            vertices_set.add(vertices[-1])

    result = list(vertices_set)

    if process_vertices:
        processed_vertices = []

        for vertex in result:
            # Take x, y, z from the vertex and expand it with filler data
            processed = [vertex[0], vertex[1], vertex[2], 0, 20.0, 0.0, 0.0, 0.0, 0.0]
            processed_vertices.append(processed)
        
        return processed_vertices

    return result


def create_lars_race_maker(city_name, street_list, lars_race_maker = False, process_vertices = True):
    #!########### Code by Lars (Modified) ############    
    vertices_processed = get_first_and_last_street_vertices(street_list, process_vertices)
    
    polygons = hudmap_vertices
    min_x, max_x, min_z, max_z = create_ext(city_name, polygons)
    
    canvas_width = int(max_x - min_x)
    canvas_height = int(max_z - min_z)

    html_start = f"""
<!DOCTYPE html>
<html>

<head>
    <style>
        body {{
            background-color: #2b2b2b;
        }}

        #myCanvas {{
            background-color: #2b2b2b;
        }}

        #out {{
            color: white;
        }}
    </style>
</head>

<img id = "scream" width = "{canvas_width}" height = {canvas_height} src = "{city_name}_HUD_debug.jpg" alt = "The Scream" style = "display:none;">

<canvas id = "myCanvas" width = "{canvas_width}" height = "{canvas_height} style = "background-color: #2b2b2b;">
Your browser does not support the HTML5 canvas tag.

</canvas>

<div id = "out"></div>

<script>

var MIN_X = {min_x};
var MAX_X = {max_x};
var MIN_Z = {min_z};
var MAX_Z = {max_z};

var coords = [
"""

    html_end = """
];

function mapRange(value, in_min, in_max, out_min, out_max) {
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
"""

    html_end += """
window.onload = function() {
    var canvas = document.getElementById("myCanvas");
    var ctx = canvas.getContext("2d");
    var img = document.getElementById("scream");
    
    // Draw the image onto the canvas
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    for (var i = 0; i < coords.length; i++) {
        ctx.lineWidth = "10";
        ctx.strokeStyle = "blue";
        ctx.beginPath();
"""

    html_end += """
        // Mapping the coordinates to fit within the canvas dimensions
        let mappedX = mapRange(coords[i][0], MIN_X, MAX_X, 0, canvas.width);
        let mappedZ = mapRange(coords[i][2], MIN_Z, MAX_Z, 0, canvas.height);

        ctx.arc(mappedX, mappedZ, 5, 0, 2 * Math.PI);
        ctx.fill();
"""

    html_end += """
    }
};
"""

    html_end += f"""
let last = null;

function getCursorPosition(canvas, event) {{
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    console.log("x: " + x + " y: " + y);
    let closest = [-1, 10000000000];
    for (var i = 0; i < coords.length; i++) {{
        let mappedX = mapRange(coords[i][0], MIN_X, MAX_X, 0, canvas.width);
        let mappedZ = mapRange(coords[i][2], MIN_Z, MAX_Z, 0, canvas.height);
        
        let dist = (x - mappedX)**2 + (y - mappedZ)**2;
        if (closest[1] > dist) {{
            closest = [i, dist];
        }}
    }}
    if (closest[1] < 500) {{
        document.getElementById("out").innerHTML += coords[closest[0]].join(',');
        document.getElementById("out").innerHTML += '<br/>';
        if (last) {{
            var canvas = document.getElementById("myCanvas");
            var ctx = canvas.getContext("2d");
            ctx.lineWidth = "5";
            ctx.strokeStyle = "blue";
            ctx.beginPath();
            ctx.moveTo(last[0], last[1]);
            ctx.lineTo(x, y);
            ctx.stroke();
        }}
        last = [x,y];
    }}
}}
    """

    html_end += f"""
const canvas = document.getElementById('myCanvas');
canvas.addEventListener('mousedown', function(e) {{
    getCursorPosition(canvas, e);
}});
</script>
</body>
</html>
    """

    coords_string = ",\n".join([str(coord) for coord in vertices_processed])
    new_html_content = html_start + coords_string + html_end
        
    if lars_race_maker:
        with open("Lars_Race_Maker.html", "w") as file:
            file.write(new_html_content)

    return new_html_content

#!########### Code by Lars (Modified) ############   

###################################################################################################################
################################################################################################################### 

# FACADE CLASS
class Facade_Editor:
    def __init__(self, flags: int, start: Vector3, end: Vector3, sides: Vector3, scale: float, name: str) -> None:
        self.room = 0x1
        self.flags = flags
        self.start = start
        self.end = end
        self.sides = sides
        self.scale = scale
        self.name = name

    @classmethod
    def read_facades(cls, f):
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

    def write_facades(self, f):
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
    
    
def read_facade_scales(scales_file):
    scales = {}
    
    with open(scales_file, 'r') as f:
        for line in f:
            facade_name, scale = line.strip().split(": ")
            scales[facade_name] = float(scale)
    return scales

    
def create_facades(filename, facade_params, target_fcd_dir, set_facades = False, debug_facades = False):
    if set_facades:
        facades = []
        axis_dict = {'x': 0, 'y': 1, 'z': 2}

        scales = read_facade_scales(BASE_DIR / "EditorResources" / 'FCD scales.txt')

        for params in facade_params:
            axis_idx = axis_dict[params['axis']]
            start_coord = params['start'][axis_idx]
            end_coord = params['end'][axis_idx]

            # Determine the direction in which to move along the axis.
            direction = 1 if start_coord < end_coord else -1

            num_facades = math.ceil(abs(end_coord - start_coord) / params['separator'])
            
            for i in range(num_facades):
                flags = params['flags']
                current_start = list(params['start'])
                current_end = list(params['end'])

                # Apply the separator in the appropriate direction.
                shift = direction * params['separator'] * i
                current_start[axis_idx] = start_coord + shift
                
                # Make sure the next end doesn't overshoot the given end.
                if direction == 1:
                    current_end[axis_idx] = min(start_coord + shift + params['separator'], end_coord)
                else:
                    current_end[axis_idx] = max(start_coord + shift - params['separator'], end_coord)

                current_start = tuple(current_start)
                current_end = tuple(current_end)

                sides = params.get('sides', (0.0, 0.0, 0.0))
                scale = scales.get(params['facade_name'], params.get('scale', 1.0))
                name = params['facade_name']

                facade = Facade_Editor(flags, current_start, current_end, sides, scale, name)
                facades.append(facade)

        with open(filename, mode = 'wb') as f:
            write_pack(f, '<I', len(facades))
            for facade in facades:
                facade.write_facades(f)

        MOVE(filename, target_fcd_dir / filename)

        if debug_facades:
            with open("FACADES_debug.txt", mode = 'w', encoding = 'utf-8') as f:
                for facade in facades:
                    f.write(str(facade))
                
###################################################################################################################
###################################################################################################################  

def create_commandline(city_name: str, dest_folder: Path, no_ui: bool = False, no_ui_type: str = "", quiet_logs: bool = False):
    city_name = city_name.lower()
    cmd_file = "commandline.txt"
    
    base_cmd = f"-path ./dev -allrace -allcars -f -heapsize 499 -multiheap -maxcops 100 -speedycops -l {city_name}"
    
    if quiet_logs:
        base_cmd += " -quiet"
    
    if no_ui:
        if not no_ui_type or no_ui_type.lower() == "cruise":
            base_cmd += f" -noui -keyboard"
        else:
            race_type, race_index = no_ui_type.split()
            if race_type not in ["circuit", "race", "blitz"]:
                raise ValueError("Invalid race type provided. Available types are 'circuit, 'race, and 'blitz'.")
            if not 0 <= int(race_index) <= 14:
                raise ValueError("The race index should be between 0 and 14.")
            base_cmd += f" -noui -{race_type} {race_index} -keyboard"
    
    processed_cmd = base_cmd
        
    cmd_file_path = dest_folder / cmd_file
    
    with cmd_file_path.open("w") as file:
        file.write(processed_cmd)

        
# Start game
def start_game(dest_folder: str, play_game: bool = False, import_to_blender: bool = False) -> None:
    if play_game and not import_to_blender:
        subprocess.run(str(Path(dest_folder) / "Open1560.exe"), cwd = str(dest_folder), shell = True)
        
################################################################################################################### 

#* FACADE NOTES
#* Separator: (max_x - min_x) / separator(value) = number of facades
#* Sides --> omitted by default, but can be set (relates to lighting, but behavior is not clear)
#* Scale --> enlarges or shrinks non-fixed facades
#* Facade name --> name of the facade in the game files

#* All relevant Facade information can be found in: /UserResources/FACADES.
#* Each facade is photographed and documented (see: "FACADE_DATA.txt")

#* A few Facade_name examples are: ofbldg02, dt11_front, tunnel01, t_rail01, ramp01

# Flags (if applicable, consult the documentation for more info)
FRONT = 1 # sometimes 1 is also used for the full model
FRONT_BRIGHT = 3

FRONT_LEFT = 9
FRONT_BACK = 25
FRONT_ROOFTOP = 33
FRONT_LEFT = 41 # value 73 is also commonly used for this
FRONT_RIGHT = 49

FRONT_LEFT_ROOF = 105 
FRONT_RIGHT_ROOF = 145 # value 177 is also commonly used for this
FRONT_LEFT_RIGHT = 217
FRONT_LEFT_RIGHT_ROOF = 249

FRONT_BACK_ROOF = 1057
FRONT_RIGHT_BACK = 1073
FRONT_LEFT_ROOF_BACK = 1129
FRONT_RIGHT_ROOF_BACK = 1201
ALL_SIDES = 1273


fcd_orange_building_1 = {
	'flags': FRONT_BRIGHT,
	'start': (-10.0, 0.0, -50.0),
	'end': (10, 0.0, -50.0),
	# 'sides': (27.8, 0.0, 0.0),
	'separator': 10.0,
	'facade_name': "ofbldg02",
	'axis': 'x'}

fcd_orange_building_2 = {
	'flags': FRONT_BRIGHT,
	'start': (10.0, 0.0, -70.0),
	'end': (-10, 0.0, -70.0),
	'separator': 10.0,
	'facade_name': "ofbldg02",
	'axis': 'x'}

fcd_orange_building_3 = {
	'flags': FRONT_BRIGHT,
	'start': (-10.0, 0.0, -70.0),
	'end': (-10.0, 0.0, -50.0),
	'separator': 10.0,
	'facade_name': "ofbldg02",
	'axis': 'z'}

fcd_orange_building_4 = {
	'flags': FRONT_BRIGHT,
	'start': (10.0, 0.0, -50.0),
	'end': (10.0, 0.0, -70.0),
	'facade_name': "ofbldg02",
    'axis': 'z',
    'separator': 10.0}

fcd_white_hotel_long_road = {
    'flags': FRONT_BRIGHT,
	'start': (-160.0, 0.0, -80.0),
	'end': (-160.0, 0.0, 20.0),
	'separator': 25.0, 
	'facade_name': "rfbldg05",
	'axis': 'z'}

fcd_red_hotel_long_road = {
    'flags': FRONT_BRIGHT,
	'start': (-160.0, 0.0, 40.0),
	'end': (-160.0, 0.0, 140.0),
	'separator': 20.0, 
	'facade_name': "dfbldg06",
	'axis': 'z'}

# Pack all Facades for processing
fcd_list = [
    fcd_orange_building_1, fcd_orange_building_2, fcd_orange_building_3, fcd_orange_building_4, 
    fcd_white_hotel_long_road, fcd_red_hotel_long_road]

###################################################################################################################

# SET AI PATHS

f"""
# The following variables are OPTIONAL: 

# Intersection_types, defaults to: "CONTINUE"
(possbile types: "STOP", "STOP_LIGHT", "YIELD", "CONTINUE")

# Stop_light_names, defaults to: "STOP_LIGHT_SINGLE"
(possbile names: "STOP_SIGN", "STOP_LIGHT_SINGLE", "STOP_LIGHT_DUAL")

# Stop_light_positions, defaults to: (0, 0, 0)
# Traffic_blocked, Ped_blocked, Road_divided, and Alley, all default to: "NO"
(possbile values: "YES", "NO")

Note:
# Stop lights will only show if the Intersection_type is "stoplight"
# Each lane will automatically have an identical reversed lane  
"""

#! Do not delete this Street
cruise_start = {
    "street_name": "cruise_start",
    "vertices": [
        (0,0,0),            # keep this
        cruise_start_pos]}  # starting position in Cruise mode

main_west_path = {
     "street_name": "main_west_path",
     "vertices": [
         (0.0, 0.0, 77.5),
         (0.0, 0.0, 70.0),
         (0.0, 0.0, 10.0),
         (0.0, 0.0, 0.0),
         (0.0, 0.0, -10.0),
         (0.0, 0.0, -70.0),
         (0.0, 0.0, -70.0),
         (0.0, 0.0, -100.0)]}

main_grass_horz_path = {
     "street_name": "main_grass_horz_path",
     "vertices": [
         (0.0, 0.0, -100.0),
         (20.0, 0.0, -100.0),
         (25.0, 0.0, -100.0),
         (30.0, 0.0, -100.0),
         (35.0, 0.0, -100.0),
         (40.0, 0.0, -100.0),
         (45.0, 0.0, -100.0),
         (50.0, 0.0, -100.0),
         (95.0, 0.0, -110.0)]}

main_barricade_wood_path = {
     "street_name": "east_path",
     "vertices": [
         (95.0, 0.0, -110.0),
         (95.0, 0.0, -70.0),
         (100.0, 0.0, -50.0),
         (105.0, 0.0, -30.0),
         (110.0, 0.0, -10.0),
         (115.0, 0.0, 10.0),
         (120.0, 0.0, 30.0),
         (125.0, 0.0, 50.0),
         (130.0, 0.0, 70.0),
         (40.0, 0.0, 100.0)]}

# perfect angled grass path:    (40.0, 0.0, 102.5)

main_double_triangle_path = {
    "street_name": "main_double_triangle_path",
    "vertices": [
        (40.0, 0.0, 100.0),
        (-50.0, 0.0, 135.0),
        (-59.88, 3.04, 125.52),
        (-84.62, 7.67, 103.28),
        (-89.69, 8.62, 62.57),
        (-61.94, 3.42, 32.00),
        (-20, 0.0, 70.0),
        (0.0, 0.0, 77.5)]}

orange_hill_path = {
    "street_name": "orange_hill_path",
    "vertices": [
        (0.0, 245.0, -850.0),
        (0.0, 0.0, -210.0),
        (0.0, 0.0, -155.0),
        (0.0, 0.0, -100.0)]}

# Street examples with multiple lanes and all optional settings
street_example = {
    "street_name": "example_path",
    "lanes": {
        "lane_1": [
            (-40.0, 1.0, -20.0),
            (-30.0, 1.0, -30.0),
            (-30.0, 1.0, -50.0),
        ],
        "lane_2": [
            (-40.0, 1.0, -20.0),
            (-40.0, 1.0, -30.0),
            (-40.0, 1.0, -50.0),
        ],
        "lane_3": [
            (-40.0, 1.0, -20.0),
            (-50.0, 1.0, -30.0),
            (-50.0, 1.0, -50.0),
        ]
    },
    "intersection_types": [STOP_LIGHT, STOP_LIGHT],
    "stop_light_names": [STOP_LIGHT_DUAL, STOP_LIGHT_DUAL],
    "stop_light_positions": [
         (10.0, 0.0, -20.0),        # offset 1
         (10.01, 0.0, -20.0),       # direction 1
         (-10.0, 0.0, -20.0),       # offset 2
         (-10.0, 0.0, -20.1)],      # direction 2
    "traffic_blocked": [NO, NO],
    "ped_blocked": [NO, NO],
    "road_divided": NO,
    "alley": NO}

# Pack all AI paths for processing
street_list = [cruise_start, 
               main_west_path, main_grass_horz_path, main_barricade_wood_path, main_double_triangle_path, 
               orange_hill_path]

################################################################################################################               

# SET PROPS
china_gate = {'offset': (0, 0.0, -20), 
              'face': (1 * HUGE, 0.0, -20), 
              'name': CHINATOWN_GATE}

trailer_set = {'offset': (60, 0.0, 70), 
               'end': (60, 0.0, -50), 
               'name': TRAILER, 
               'separator': 'x'} # Use the {}-axis dimension of the object as the spacing between each prop

bridge_orange_buildling = {          
          'offset': (35, 12.0, -70),
          'face': (35 * HUGE, 12.0, -70),
          'name': BRIDGE_SLIM}

# Put your non-randomized props here
prop_list = [china_gate, trailer_set, bridge_orange_buildling] 

# # Put your randomized props here (you will add them to the list "random_parameters")
random_trees = {
        'offset_y': 0.0,
        'name': [TREE_SLIM] * 20}

random_sailboats = {
        'offset_y': 0.0,
        'name': [SAILBOAT] * 19}

random_cars = {
        'offset_y': 0.0,
          'separator': 10.0,
          'name': [VW_BEETLE, CITY_BUS, CADILLAC, CRUISER, FORD_F350, FASTBACK, MUSTANG99, ROADSTER, PANOZ_GTR1, SEMI]}

# Configure your random props here
random_parameters = [
    {"seed": 123, "num_objects": 1, "object_dict": random_trees, "x_range": (65, 135), "z_range": (-65, 65)},
    {"seed": 99, "num_objects": 1, "object_dict": random_sailboats, "x_range": (55, 135), "z_range": (-145, -205)},
    {"seed": 1, "num_objects": 2, "object_dict": random_cars, "x_range": (52, 138), "z_range": (-136, -68)}]

# AudioIds
MALLDOOR_AUD = 1
POLE_AUD = 3           
SIGN_AUD = 4          
MAIL_AUD = 5              
METER_AUD = 6
TRASH_AUD = 7          
BENCH_AUD = 8         
TREE_AUD = 11         
BOXES_AUD = 12         # also used for "bridge crossgate"
NO_NAME_AUD = 13       # difficult to describe
BARREL_AUD = 15        # also used for "dumpster"
PHONEBOOTH_AUD = 20
CONE_AUD = 22 
NO_NAME_2_AUD = 24     # sounds a bit similar to "glass"
NEWS_AUD = 25
GLASS_AUD = 27

# Set additional Prop Properties here (currently only possible for cars)
# The Size does affect how the prop moves after impact. CG stands for Center of Gravity. 
bangerdata_properties = {
    VW_BEETLE: {'ImpulseLimit2': HUGE, 'AudioId': GLASS_AUD},
    CITY_BUS:  {'ImpulseLimit2': 50, 'Mass': 50, 'AudioId': POLE_AUD, 'Size': '18 6 5', 'CG': '0 0 0'}}

################################################################################################################     

# SET MATERIAL PROPERTIES
# available indices: 94, 95, 96, 97, 98,
# see: /UserResources/PHYSICS/PHYSICS.DB.txt for more information

new_physics_properties = {
    97: {"friction": 20.0, "elasticity": 0.01, "drag": 0.0},  # sticky
    98: {"friction": 0.1, "elasticity": 0.01, "drag": 0.0},   # slippery
}

################################################################################################################   

# Call FUNCTIONS
print("\n===============================================\n")
print("Generating " + f"{race_locale_name}...")
print("\n===============================================\n")

create_folders(city_name)
create_city_info()
create_bounds(vertices, polys, city_name, debug_bounds)
create_cells(city_name, truncate_cells)
create_races(city_name, race_data)
create_cnr(city_name, cnr_waypoints)

Material_Editor.edit_materials(new_physics_properties, "physics.db", debug_physics)
StreetFile_Editor.create_streets(city_name, street_list, ai_streets, ai_reverse, ai_map)

prop_editor = Prop_Editor(city_name, debug_props, input_bng_file = False)

for i in random_parameters:
    randomized_objects = prop_editor.place_props_randomly(**i)
    prop_list.extend(randomized_objects)
    
prop_editor.add_props(prop_list)
prop_editor.write_bng_file(set_props)

copy_open1560(mm1_folder)
copy_dev_folder(mm1_folder, city_name)
edit_and_copy_mmbangerdata(bangerdata_properties)
copy_core_tune_files()
copy_custom_textures()

create_ext(city_name, hudmap_vertices)
create_animations(city_name, anim_data, set_anim)   
create_bridges(bridges, set_bridges) 
custom_bridge_config(bridge_configs, set_bridges, SHOP / 'TUNE')
create_facades(f"{city_name}.FCD", fcd_list, BASE_DIR / SHOP_CITY, set_facades, debug_facades)
create_portals(city_name, polys, vertices, empty_portals, debug_portals)

create_hudmap(set_minimap, debug_hud, debug_hud_bound_id, shape_outline_color, import_to_blender,
               x_offset = 0.0, y_offset = 0.0, line_width = 0.7, background_color = 'black')

create_lars_race_maker(city_name, street_list, lars_race_maker, process_vertices = True)

create_ar(city_name, mm1_folder, delete_shop)
create_commandline(city_name, Path(mm1_folder), no_ui, no_ui_type, quiet_logs)

print("\n===============================================\n")
print("Succesfully created " + f"{race_locale_name}!")
print("\n===============================================\n")

start_game(mm1_folder, play_game, import_to_blender)

# Blender (w.i.p.)
create_blender_meshes(import_to_blender)
bpy.utils.register_class(UpdateUVMapping)
bpy.utils.register_class(ExportBlenderPolygons)
bpy.utils.register_class(AssignCustomProperties)
set_blender_keybinding(import_to_blender)

#? ============ For Reference ============

# # Print the contents of a BNG file in the current working directory
# prop_editor = Prop_Editor("CHICAGO.BNG", debug_props = debug_props, input_bng_file = True)
# prop_editor.read_bng_file()
# for objects in prop_editor.objects:
#    print(objects)
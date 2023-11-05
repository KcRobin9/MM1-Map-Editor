
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
import time
import pickle
import shutil
import struct
import random
import textwrap
import threading
import subprocess
import numpy as np   
from pathlib import Path 
import matplotlib.pyplot as plt                
import matplotlib.transforms as mtransforms  
from colorama import Fore, Style, init
from typing import List, Dict, Union, Tuple, Optional, BinaryIO
  

#! SETUP I (Map Name and Directory)             Control + F    "map=="  to jump to The Map Creation section
map_name = "My First City"                      # Can be multiple words --- name of the Map in the Race Menu
map_filename = "First_City"                     # One word (no spaces)  --- name of the .AR file
mm1_folder = Path.cwd() / 'MidtownMadness'      # The Editor will use the MM game that comes with the repo download (the name can not have any spaces)


#* SETUP II (Map Creation)      
play_game = True                # change to "True" to start the game after the Map is created (defaults to False when Blender is running)
delete_shop = True              # change to "True" to delete the raw city files after the .AR file has been created

set_anim = True                 # change to "True" if you want ANIMATIONS (plane and eltrain)
set_bridges = True              # change to "True" if you want BRIDGES
set_facades = True              # change to "True" if you want FACADES

# PROPS
set_props = True                # change to "True" if you want PROPS
append_props = False            # change to "True" if you want to append props
input_props_f = Path.cwd() / "EditorResources" / "CHICAGO.BNG"  # feel free to change this to any other .BNG file
appended_props_f = "NEW_CHICAGO.BNG"  # the appended props file will be saved in the main folder

# HUD
set_minimap = True              # change to "True" if you want a MINIMAP (defaults to False when Blender is running)
shape_outline_color = None      # change the outline of the minimap shapes to any color (e.g. 'Red'), if you don't want any color, set to None

# AI
set_ai_map = True               # create the Map file          keep both set to "True" if you want functional AI
set_streets = True              # create the Streets files     keep both set to "True" if you want functional AI
set_reverse_streets = False     # change to "True" if you want to automatically add a reverse AI path for each lane
lars_race_maker = False         # change to "True" if you want to create "lars race maker" 

# You can add multiple Cruise Start positions here (as backup), only the last one will be used
cruise_start_pos = (35.0, 31.0, 10.0) 
cruise_start_pos = (60.0, 27.0, 330.0)
cruise_start_pos = (0.0, 0.0, 0.0)
cruise_start_pos = (-83.0, 18.0, -114.0)
cruise_start_pos = (40.0, 30.0, -40.0)

# Misc
randomize_textures = False      # change to "True" if you want to randomize all textures in your Map
random_textures = ["T_WATER", "T_GRASS", "T_WOOD", "T_WALL", "R4", "R6", "OT_BAR_BRICK", "FXLTGLOW"]

# Blender
load_tex_materials = False      # change to "True" if you want to load all texture materials (they will be available regardless) (takes a few extra seconds to load)
texture_dir = Path.cwd() / 'EditorResources' / 'Textures'

# Debug
debug_bounds = False            # change to "True" if you want a BOUNDS Debug text file
debug_props = False             # change to "True" if you want a PROPS Debug text file
debug_facades = False           # change to "True" if you want a FACADES Debug text file
debug_physics = False           # change to "True" if you want a PHYSICS Debug text file
debug_portals = False           # change to "True" if you want a PORTALS Debug text file
DEBUG_BMS = False               # change to "True" if you want BMS Debug text files (in the folder "Debug BMS")
debug_hud = False               # change to "True" if you want a HUD Debug jpg file (defaults to True when "lars_race_maker" is set to True)
debug_hud_bound_id = False      # change to "True" if you want to see the Bound ID in the HUD Debug jpg file
round_debug_values = True       # change to "True" if you want to round (some) debug values to 2 decimals

# Advanced
no_ui = False                   # change to "True" if you want skip the game's menu and go straight into Cruise mode
no_ui_type = "cruise"           # other race types are currently not supported by the game in custom maps
no_ai = False                   # change to "True" if you want to disable the AI
quiet_logs = False              # change to "True" if you want to hide most logs. The game e.g. prints a ton of messages if an AI car can't find its path, causing FPS drops
more_logs = False               # change to "True" if you want to see additional logs and open a logging console
empty_portals = False           # change to "True" if you want to create an empty portal file (useful for testing very large cities)
truncate_cells = False			# change to "True" if you want to truncate the characters in the cells file (useful for testing very large cities)
fix_faulty_quads = False        # change to "True" if you want to fix faulty quads (e.g. self-intersecting quads)

disable_progress_bar = False    # change to "True" if you want to disable the progress bar (this will properly display Errors and Warnings again)

################################################################################################################               
################################################################################################################

# Progress Bar, Colors, & Run Time
init(autoreset = True)

colors_one = [
    Fore.RED, Fore.LIGHTRED_EX, 
    Fore.YELLOW, Fore.LIGHTYELLOW_EX, 
    Fore.GREEN, Fore.LIGHTGREEN_EX, 
    Fore.CYAN, Fore.LIGHTCYAN_EX, 
    Fore.BLUE, Fore.LIGHTBLUE_EX, 
    Fore.MAGENTA, Fore.LIGHTMAGENTA_EX
    ]

colors_two = [    
    Fore.LIGHTGREEN_EX, Fore.GREEN,
    Fore.CYAN, Fore.LIGHTCYAN_EX,
    Fore.BLUE, Fore.LIGHTBLUE_EX
]

def create_divider(colors):
    divider = "=" * 60  
    color_divider = ''.join(colors[i % len(colors)] + char for i, char in enumerate(divider))
    return "\n" + color_divider + "\n"

# Set the progress bar colors
top_divider = create_divider(colors_one)
bottom_divider = create_divider(colors_one)
buffer = top_divider + "\n" + " " * 60 + "\n" + bottom_divider


def clear_screen(disable_progress_bar: bool):
    if not disable_progress_bar:
        print("\033[H\033[J", end = '')


def update_progress_bar(progress, map_name, buffer, top_divider, bottom_divider):
    if progress < 33:
        color = Style.BRIGHT + Fore.RED
    elif progress < 66:
        color = Style.BRIGHT + Fore.YELLOW
    else:
        color = Style.BRIGHT + Fore.GREEN
    
    prog_int = int(progress)
    prog_line = color + f"   Creating.. {map_name} [{'#' * (prog_int // 5)}{'.' * (20 - prog_int // 5)}] {prog_int}%" + Style.RESET_ALL

    buffer = top_divider + "\n" + prog_line + "\n" + bottom_divider + "\n"
    clear_screen(disable_progress_bar)
    print(buffer, end = '')


def continuous_progress_bar(duration, map_name, buffer, top_divider, bottom_divider, disable_progress_bar):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        progress = (elapsed_time / duration) * 100
        progress = min(100, max(0, progress))  
        update_progress_bar(progress, map_name, buffer, top_divider, bottom_divider)
        if progress >= 100:
            break
        time.sleep(0.025)  # Update every 0.025 seconds


def save_run_time(run_time):
    os.chdir(Path.cwd().parent)
    with open("last_editor_run_time.pkl", "wb") as f:
        pickle.dump(run_time, f)


def load_last_run_time():
    if os.path.exists("last_editor_run_time.pkl"):
        try:
            with open("last_editor_run_time.pkl", "rb") as f:
                return pickle.load(f)
        except EOFError:
            return 3  # Default to 3.0 seconds if the file is empty or corrupted
    return 3  # Default to 3.0 seconds if no previous data


# Load the Last Run Time, Start the Progress Bar Thread, Start the Time
last_run_time = load_last_run_time()

progress_thread = threading.Thread(
    target = continuous_progress_bar, 
    args = (last_run_time, map_name, buffer, top_divider, bottom_divider, disable_progress_bar))

progress_thread.start()
start_time = time.time()

################################################################################################################               
################################################################################################################

##### CONSTANTS & INITIALIZATIONS #####

# Editor
BASE_DIR = Path.cwd()
SHOP = BASE_DIR / 'SHOP'
SHOP_CITY = BASE_DIR / 'SHOP' / 'CITY'
MOVE = shutil.move

# Variables
vertices = []
hudmap_vertices = []
hudmap_properties = {}
polygons_data = []
stored_texture_names = []
texcoords_data = {}

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

# Circuit Laps
LAPS_2 = 2
LAPS_3 = 3
LAPS_5 = 5
LAPS_10 = 10

# Race Data
ZERO_COPS, FULL_COPS = 0.0, 1.0  # The game only supports 0.0 and 1.0 for Cops
ZERO_PED, HALF_PED, FULL_PED = 0.0, 0.5, 1.0
ZERO_AMBIENT, HALF_AMBIENT, FULL_AMBIENT = 0.0, 0.5, 1.0

# Waypoint Width
LANE_4 = 15
LANE_6 = 19
LANE_ALLEY = 3

# Waypoint Rotation
ROT_S = 179.99
ROT_W = -90
ROT_E = 90
ROT_N = 0.01
ROT_AUTO = 0

# Race Types
ROAM = "ROAM"
CRUISE = "CRUISE"
BLITZ = "BLITZ"
RACE = "RACE"
CIRCUIT = "CIRCUIT"
COPS_N_ROBBERS = "COPSANDROBBERS"

# Modes
SINGLE = "SINGLE"
MULTI = "MULTI"
ALL_MODES = "All Modes"

# AI Intersection types
STOP = 0 
STOP_LIGHT = 1 
YIELD = 2
CONTINUE = 3

# AI Road properties, e.g. set True/False for the variable "traffic_blocked"
NO = 0
YES = 1

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

PLANE_LARGE = "vaboeing"  # No collision
 
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
                'ama': [NOON, CLOUDY, MAX_OPP_8, FULL_COPS, FULL_AMBIENT, FULL_PED, 3, 999],        
                'pro': [EVENING, CLOUDY, MAX_OPP_8, FULL_COPS, FULL_AMBIENT, FULL_PED, 3, 999], 
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
                'ama': [NOON, CLEAR, MAX_OPP_8, ZERO_COPS, ZERO_AMBIENT, ZERO_PED],
                'pro': [NOON, CLOUDY, MAX_OPP_8, ZERO_COPS, ZERO_AMBIENT, ZERO_PED],
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
                WHITE_LIMO:    [[-10.0, 245, -850], 
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
                'ama': [NIGHT, RAIN, MAX_OPP_8, ZERO_COPS, HALF_AMBIENT, HALF_PED, LAPS_2],
                'pro': [NIGHT, SNOW, MAX_OPP_8, ZERO_COPS, HALF_AMBIENT, HALF_PED, LAPS_3],
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
        (450, 30.0, -450),      # you can not have multiple Planes or Eltrains
        (450, 30.0, 450),       # you can set any number of coordinates for your path(s)
        (-450, 30.0, -450),     
        (-450, 30.0, 450)], 
    'eltrain': [
        (180, 25.0, -180),
        (180, 25.0, 180), 
        (-180, 25.0, -180),
        (-180, 25.0, 180)]}


#* SETUP VI (optional, Bridges)
f"""
    INFO
    1) You can set a maximum of 1 bridge per cull room, which may have up to 5 attributes
    2) You can set a bridge without any attributes like this:
        (-50.0, 0.01, -100.0), 270, 2, BRIDGE_WIDE, [])
    
    
    3) Supported orientations:
    NORTH, SOUTH, EAST, WEST, NORTH_EAST, NORTH_WEST, SOUTH_EAST, SOUTH_WEST
    Or you can manually set the orientation in degrees (0.0 - 360.0).
"""

bridge_object = "vpmustang99"  # you pass any prop/car

#! Structure: (x,y,z, orientation, bridge number, bridge object)
bridges = [
    ((-50.0, 0.01, -100.0), 270, 2, BRIDGE_WIDE, [
    ((-50.0, 0.15, -115.0), 270, 2, CROSSGATE),
    ((-50.0, 0.15, -85.0), -270, 2, CROSSGATE)
    ]),  
    ((-119.0, 0.01, -100.0), "EAST", 3, BRIDGE_WIDE, [
    ((-119.0, 0.15, -115.0), 270, 3, CROSSGATE),
    ((-119.0, 0.15, -85.0), -270, 3, CROSSGATE)
    ])] 


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
    "Mode": SINGLE}

bridge_cnr = {
    "RaceType": COPS_N_ROBBERS,
    "BridgeDelta": 0.20,
    "BridgeOffGoal": 0.33,
    "BridgeOnGoal": 0.33,
    "Mode": MULTI}

# Pack all Custom Bridge Configs. for processing
bridge_configs = [bridge_race_0, bridge_cnr]

################################################################################################################               
################################################################################################################     
 
def to_do_list(x): # this list only contains a small number of main topics, many smaller tasks are excluded
            """            
            Correctly set walls (currently they are infinite in height collision-wise)
            Improve Facades setting (e.g. diagonal facades)
            Develop Blender BAI importer/exporter
            Investigate Breakable Parts (see {}.MMBANGERDATA)
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

    def Cross(self, rhs = None):
        if rhs is None:
            return Vector2(self.y, -self.x)

        return (self.x*rhs.y) - (self.y*rhs.x)

    def Dot(self, rhs):
        return (self.x * rhs.x) + (self.y * rhs.y)

    def Mag2(self):
        return (self.x * self.x) + (self.y * self.y)

    def Dist2(self, other):
        return (other - self).Mag2()

    def Dist(self, other):
        return self.Dist2(other) ** 0.5
    
    def Normalize(self):
        return self * (self.Mag2() ** -0.5)
    
    def __repr__(self, round_values = round_debug_values):
        if round_values:
            return '{:.2f}, {:.2f}'.format(round(self.x, 2), round(self.y, 2))
        else:
            return '{:f}, {:f}'.format(self.x, self.y)


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
        
    def __repr__(self, round_values = round_debug_values):
        if round_values:
            return '{{{:.2f},{:.2f},{:.2f}}}'.format(round(self.x, 2), round(self.y, 2), round(self.z, 2))
        else:
            return '{{{:f},{:f},{:f}}}'.format(self.x, self.y, self.z)
       
################################################################################################################               
################################################################################################################  
       
# POLYGON CLASS
class Polygon:
    def __init__(self, cell_id: int, mtl_index: int, flags: int, vert_indices: List[int],
                 plane_edges: List[Vector3], plane_n: Vector3, plane_d: float, 
                 cell_type: int = 0, always_visible: bool = False) -> None:
        
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
            
    def write(self, f: BinaryIO) -> None:
        # Each polygon requires four vertex indices
        if len(self.vert_indices) < 4:  
            self.vert_indices += (0,) * (4 - len(self.vert_indices))
        
        write_pack(f, '<HBB4H', self.cell_id, self.mtl_index, self.flags, *self.vert_indices)

        for edge in self.plane_edges:
            edge.write(f)
            
        self.plane_n.write(f)
        write_pack(f, '<f', self.plane_d)
   
    def __repr__(self, bnd_instance):
        vertices_coordinates = [bnd_instance.vertices[index] for index in self.vert_indices]
        plane_d_str = ', '.join(f'{d:.2f}' for d in self.plane_d)
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
    
################################################################################################################               
################################################################################################################     

DEFAULT_VECTOR2 = Vector2(0.0, 0.0)  
DEFAULT_VECTOR3 = Vector3(0.0, 0.0, 0.0) 
poly_filler = Polygon(0, 0, 0, [0, 0, 0, 0], [DEFAULT_VECTOR3 for _ in range(4)], DEFAULT_VECTOR3, [0.0], 0)
polys = [poly_filler]
        
################################################################################################################               
################################################################################################################          
        
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
    
    @classmethod
    def initialize(cls, vertices: List[Vector3], polys: List[Polygon]) -> 'BND':
        magic = b'2DNB\0'
        offset = DEFAULT_VECTOR3
        x_dim, y_dim, z_dim = 0, 0, 0
        center = calculate_center(vertices)
        radius = calculate_radius(vertices, center)
        radius_sqr = radius ** 2
        bb_min = calculate_min(vertices)
        bb_max = calculate_max(vertices)
        num_hot_verts1, num_hot_verts2, num_edges = 0, 0, 0
        x_scale, z_scale = 0.0, 0.0
        num_indices, height_scale, cache_size = 0, 0, 0
        
        hot_verts = [DEFAULT_VECTOR3]  
        edges_0, edges_1 = [0], [1] 
        edge_normals = [DEFAULT_VECTOR3] 
        edge_floats = [0.0]  
        row_offsets, row_shorts, row_indices, row_heights = [0], [0], [0], [0]  

        return BND(magic, offset, x_dim, y_dim, z_dim, center, radius, radius_sqr, bb_min, bb_max, 
                len(vertices), len(polys) - 1, num_hot_verts1, num_hot_verts2, num_edges, x_scale, z_scale, 
                num_indices, height_scale, cache_size, vertices, polys,
                hot_verts, edges_0, edges_1, edge_normals, edge_floats,
                row_offsets, row_shorts, row_indices, row_heights)
            
    def write(self, f: BinaryIO) -> None:
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
            poly.write(f)    
            
    @staticmethod
    def create(vertices: List[Vector3], polys: List[Polygon], map_filename: str, debug_bounds: bool) -> None:
        bnd = BND.initialize(vertices, polys)
    
        bnd_folder = SHOP / "BND"
        bnd_file = f"{map_filename}_HITID.BND"
    
        with open(bnd_folder / bnd_file, "wb") as f:
            bnd.write(f)
        bnd.debug("BOUNDS_debug.txt", debug_bounds)          
                
    def debug(self, filename: str, debug_bounds: bool) -> None:
        if debug_bounds:
            with open(filename, 'w') as f:
                f.write(str(self))
                
    @staticmethod
    def debug_file(input_file: Path, output_file: Path) -> None:
        with open(input_file, 'rb') as in_f:
            bnd = BND.read(in_f)
            
        with open(output_file, 'w') as out_f:
            out_f.write(repr(bnd))
            
    @staticmethod
    def debug_directory(input_dir: Path, output_dir: Path) -> None:
        if not input_dir.exists():
            print(f"The directory {dir} does not exist.")
            return
        
        if not output_dir.exists():
            print(f"The output directory {output_dir} does not exist. Creating it.")
            output_dir.mkdir(parents = True, exist_ok = True)
            
        for file_path in input_dir.glob('*.BND'):
            output_file_path = output_dir / (file_path.stem + '.txt')  
            BND.debug_file(file_path, output_file_path)
            print(f"Processed {file_path.name} to {output_file_path.name}")
                
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
        
################################################################################################################               
################################################################################################################  

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
    def read(cls, file_name: str):
        with open(file_name, 'rb') as f:
            magic = read_unpack(f, '16s')[0].decode('utf-8').rstrip('\x00')  
            vertex_count, adjunct_count, surface_count, indices_count = read_unpack(f, '4I')
            radius, radius_sq, bounding_box_radius = read_unpack(f, '3f')
            texture_count, flags = read_unpack(f, 'bb')
            f.read(6)
                        
            string_names = []
            for _ in range(texture_count):
                string_name = read_unpack(f, '32s')[0].decode('utf-8').rstrip('\x00')
                string_names.append(string_name)
                f.read(16)   
                    
            if vertex_count <= 15:
                coordinates = Vector3.readn(f, vertex_count)
            else:
                coordinates = Vector3.readn(f, vertex_count + 8)
            
            texture_darkness = list(read_unpack(f, str(adjunct_count) + 'b'))
            tex_coords = list(read_unpack(f, str(adjunct_count * 2) + 'f'))
            enclosed_shape = list(read_unpack(f, str(adjunct_count) + 'H'))
            surface_sides = list(read_unpack(f, str(surface_count) + 'b'))

            indices_per_surface = indices_count // surface_count
            indices_sides = []

            for _ in range(surface_count):
                indices_side_format = f"<{indices_per_surface}H"
                indices_side = list(read_unpack(f, indices_side_format))
                indices_sides.append(indices_side)

        return cls(magic, vertex_count, adjunct_count, surface_count, indices_count, 
                   radius, radius_sq, bounding_box_radius, 
                   texture_count, flags, string_names, coordinates, 
                   texture_darkness, tex_coords, enclosed_shape, surface_sides, indices_sides)
        
    def write(self, path: Path) -> None:
        with open(path, 'wb') as f:
            write_pack(f, '16s', self.magic.encode('utf-8').ljust(16, b'\x00'))
            write_pack(f, '4I', self.vertex_count, self.adjunct_count, self.surface_count, self.indices_count)
            write_pack(f, '3f', self.radius, self.radius_sq, self.bounding_box_radius)
            write_pack(f, 'bb', self.texture_count, self.flags)
            f.write(b'\x00' * 6) 

            for name in self.string_name:
                write_pack(f, '32s', name.encode('utf-8').ljust(32, b'\x00'))
                f.write(b'\x00' * 16)
                            
            for coordinate in self.coordinates:
                coordinate.write(f)

            if self.vertex_count >= 16:
                for _ in range(8):
                    DEFAULT_VECTOR3.write(f)
                    
            write_pack(f, str(self.adjunct_count) + 'b', *self.texture_darkness)
                        
            # Temporary solution - ensuring tex_coords is not longer than adjunct_count * 2
            if len(self.tex_coords) > self.adjunct_count * 2:
                self.tex_coords = self.tex_coords[:self.adjunct_count * 2] 
                
            write_pack(f, str(self.adjunct_count * 2) + 'f', *self.tex_coords)            
            write_pack(f, str(self.adjunct_count) + 'H', *self.enclosed_shape)
            write_pack(f, str(self.surface_count) + 'b', *self.surface_sides)

            # A triangle still requires 4 indices ([0, 1, 2, 0])
            for indices_side in self.indices_sides:
                while len(indices_side) < 4:
                    indices_side.append(0)
                write_pack(f, str(len(indices_side)) + 'H', *indices_side)
                        
    def debug(self, file_name: str, debug_dir = "Debug BMS") -> None:
        Path(debug_dir).mkdir(parents = True, exist_ok = True)

        if DEBUG_BMS:
            with open(debug_dir / Path(file_name), 'w') as f:
                f.write(str(self))
                
    def __repr__(self):
        rounded_tex_coords = ', '.join(f'{coord:.2f}' for coord in self.tex_coords)
        return f'''
BMS
Magic: {self.magic}
VertexCount: {self.vertex_count}
AdjunctCount: {self.adjunct_count}
SurfaceCount: {self.surface_count}
IndicesCount: {self.indices_count}
Radius: {self.radius:.2f}
RadiusSq: {self.radius_sq:.2f}
BoundingBoxRadius: {self.bounding_box_radius:.2f}
TextureCount: {self.texture_count}
Flags: {self.flags}
StringName: {self.string_name}
Coordinates: {self.coordinates}
TextureDarkness: {self.texture_darkness}
TexCoords: {rounded_tex_coords}
Enclosed Shape: {self.enclosed_shape}
SurfaceSides: {self.surface_sides}
IndicesSides: {self.indices_sides}
        '''
             
################################################################################################################               
################################################################################################################   

# DLP CLASSES
class DLPVertex: 
    def __init__(self, id: int, normal: Vector3, uv: Vector2, color: int):
        self.id = id
        self.normal = normal
        self.uv = uv
        self.color = color
        
    @classmethod
    def read(cls, f):
        id = read_unpack(f, '>H')
        normal = Vector3.read(f)
        uv = Vector2.read(f)
        color = read_unpack(f, '>I')       
        return cls(id, normal, uv, color)
    
    def write(self, f):
        write_pack(f, '>H', self.id)
        write_pack(f, '>3f', *self.normal)       
        write_pack(f, '>ff', *self.uv)
        write_pack(f, '>I', self.color)
           
    def __repr__(self):
        return f'''
DLPVertex
Id: {self.id}
Normal: {self.normal}
UV: {self.uv}
Color: {self.color}
        '''
        
        
class DLPPatch:
    def __init__(self, s_res: int, t_res: int, flags: int, r_opts: int, mtl_idx: int, tex_idx: int, phys_idx: int, 
                 vertices: List[DLPVertex], name: str):
        self.s_res = s_res
        self.t_res = t_res
        self.flags = flags
        self.r_opts = r_opts
        self.mtl_idx = mtl_idx
        self.tex_idx = tex_idx
        self.phys_idx = phys_idx
        self.vertices = vertices
        self.name = name
        
    @classmethod
    def read(cls, f):
        s_res, t_res = read_unpack(f, '>HH')
        flags, r_opts = read_unpack(f, '>HH')
        mtl_idx, tex_idx, phys_idx = read_unpack(f, '>3H')        
        vertices = [DLPVertex.read(f) for _ in range(s_res * t_res)]
        name_length = read_unpack(f, '>I')[0]
        name = read_unpack(f, f'>{name_length}s')[0].decode()        
        return cls(s_res, t_res, flags, r_opts, mtl_idx, tex_idx, phys_idx, vertices, name)
    
    def write(self, f):
        write_pack(f, '>HH', self.s_res, self.t_res) 
        write_pack(f, '>HH', self.flags, self.r_opts)
        write_pack(f, '>3H', self.mtl_idx, self.tex_idx, self.phys_idx)
        
        for vertex in self.vertices:
            vertex.write(f)
            
        write_pack(f, '>I', len(self.name))
        write_pack(f, f'>{len(self.name)}s', self.name.encode())
        
    def __repr__(self):
        return f'''
DLPPatch
S Res: {self.s_res}
T Res: {self.t_res}
Flags: {self.flags}
R Opts: {self.r_opts}
Mtl Idx: {self.mtl_idx}
Tex Idx: {self.tex_idx}
Phys Idx: {self.phys_idx}
Verticesfff: {self.vertices}
Name: {self.name}
        '''


class DLPGroup:
    def __init__(self, name: str, num_vertices: int, num_patches: int, 
                 vertex_indices: tuple[int, ...], patch_indices: tuple[int, ...]):
        self.name = name
        self.num_vertices = num_vertices
        self.num_patches = num_patches
        self.vertex_indices = vertex_indices
        self.patch_indices = patch_indices
        
    @classmethod
    def read(cls, f):
        name_length = read_unpack(f, '>B')[0]
        name = read_unpack(f, f'>{name_length}s')[0].decode()
        num_vertices, num_patches = read_unpack(f, '>II')        
        vertex_indices = [read_unpack(f, '>H')[0] for _ in range(num_vertices)]
        patch_indices = [read_unpack(f, '>H')[0] for _ in range(num_patches)]     
        return cls(name, num_vertices, num_patches, vertex_indices, patch_indices)

    def write(self, f):
        write_pack(f, '>B', len(self.name))
        write_pack(f, f'>{len(self.name)}s', self.name.encode())
        write_pack(f, '>II', self.num_vertices, self.num_patches)
        write_pack(f, f'>{self.num_vertices}H', *self.vertex_indices)
        write_pack(f, f'>{self.num_patches}H', *self.patch_indices)
        
    def __repr__(self):
        return f'''
DLPGroup
Name: {self.name}
Num Vertices: {self.num_vertices}
Num Patches: {self.num_patches}
Vertex Indices: {self.vertex_indices}
Patch Indices: {self.patch_indices}
        '''


class DLP:
    def __init__(self, magic: str, num_groups: int, num_patches: int, num_vertices: int, 
                 groups: List[DLPGroup], patches: List[DLPPatch], vertices: List[Vector3]):
        self.magic = magic
        self.num_groups = num_groups
        self.num_patches = num_patches
        self.num_vertices = num_vertices
        self.groups = groups
        self.patches = patches
        self.vertices = vertices 
        
    @classmethod
    def read(cls, f):
        magic = read_unpack(f, '>4s')[0].decode()              
        num_groups, num_patches, num_vertices = read_unpack(f, '>3I')
        groups = [DLPGroup.read(f) for _ in range(num_groups)]
        patches = [DLPPatch.read(f) for _ in range(num_patches)]
        vertices = [Vector3(*read_unpack(f, '>3f')) for _ in range(num_vertices)]    
        return cls(magic, num_groups, num_patches, num_vertices, groups, patches, vertices)

    def write(self, file):
        with open(file, 'wb') as f:
            write_pack(f, '>4s', self.magic.encode())
            write_pack(f, '>3I', self.num_groups, self.num_patches, self.num_vertices)

            for group in self.groups:
                group.write(f) 

            for patch in self.patches:
                patch.write(f)        
                                        
    def __repr__(self):
        return f'''
DLP
Magic: {self.magic}
Num Groups: {self.num_groups}
Num Patches: {self.num_patches}
Num Vertices: {self.num_vertices}
Groups: {self.groups}
Patches: {self.patches}
Vertices: {self.vertices}
        '''
        
################################################################################################################               
################################################################################################################     
        
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
    center = Vector3(0.0, 0.0, 0.0)  # Do not change
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

################################################################################################################ 
################################################################################################################               

def compute_uv(
    bound_number: int, tile_x: int = 1, tile_y: int = 1, 
    angle_degrees: Union[float, Tuple[float, float]] = 0.0) -> List[float]:

    def rotate_point(x: float, y: float, angle: float) -> Tuple[float, float]:
        rad = math.radians(angle)
        rotated_x = x * math.cos(rad) - y * math.sin(rad)
        rotated_y = x * math.sin(rad) + y * math.cos(rad)
        return rotated_x, rotated_y

    center_x = 0.5
    center_y = 0.5

    coords = [
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1)
    ]

    def adjust_and_rotate_coords(coords: List[Tuple[float, float]], angle: float) -> List[float]:
        adjusted_coords = []
        for x, y in coords:
            x, y = rotate_point(x - center_x, y - center_y, angle)
            adjusted_coords.extend([(x + center_x) * tile_x, (y + center_y) * tile_y])
        return adjusted_coords
    
    if 'entries' not in texcoords_data:
        texcoords_data['entries'] = {}
    texcoords_data['entries'][bound_number] = {'tile_x': tile_x, 'tile_y': tile_y, 'angle_degrees': angle_degrees}

    return adjust_and_rotate_coords(coords, angle_degrees)
        
               
# SAVE BMS
def save_bms(
    texture_name: str, texture_indices: List[int] = [1], vertices = vertices, polys = polys, 
    texture_darkness: List[int] = None, tex_coords: List[float] = None, tex_coord_mode = None, tex_coord_params = None, 
    randomize_textures = randomize_textures, random_texture_exclude: bool = False, random_textures = random_textures):
        
    poly = polys[-1]  # Get the last polygon added
    bound_number = poly.cell_id
        
    # Determine the target directory
    if bound_number < 200:
        target_dir = SHOP / "BMS" / f"{map_filename}LM"
    else:
        target_dir = SHOP / "BMS" / f"{map_filename}CITY"
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
    bms.write(target_dir / bms_filename)
    
    if DEBUG_BMS:
        bms.debug(bms_filename + ".txt")
            
             
# Create BMS      
def create_bms(
    vertices: List[Vector3], polys: List[Polygon], texture_indices: List[int], 
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

def ensure_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    v1, v2, v3 = vertex_coordinates
    
    edge1 = np.subtract(v2, v1)
    edge2 = np.subtract(v3, v1)
    
    normal = np.cross(edge1, edge2)
    reference_up = np.array([0, 1, 0])
    
    dot_product = np.dot(normal, reference_up)
    
    if dot_product < 0:  # If clockwise, swap the order of the vertices
        return [v1, v3, v2]
    else:  # If counterclockwise, no changes needed
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


def compute_edges(vertex_coordinates: List[Vector3]) -> List[Vector3]:
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
        edges.append(DEFAULT_VECTOR3)
    
    return edges


# Sort BND Vertices
def sort_coordinates(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    max_x_coord = max(vertex_coordinates, key = lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key = lambda coord: coord[0])
    
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]


def create_polygon(
    bound_number: int, vertex_coordinates: List[Vector3], 
    vertices = vertices, polys = polys,
    material_index: int = 0, cell_type: int = 0, 
    flags: int = None, plane_edges: List[Vector3] = None, wall_side: str = None, sort_vertices: bool = False,
    hud_color: str = '#414441', shape_outline_color: str = shape_outline_color,  # '#414441' is the ROAD_HUD defined later in the script
    always_visible: bool = True, fix_faulty_quads: bool = fix_faulty_quads):

    # Vertex indices
    base_vertex_index = len(vertices)
    
    # Store the polygon data for Blender (before any manipulation)
    polygon_info = {
        "vertex_coordinates": vertex_coordinates,
        "bound_number": bound_number,
        "material_index": material_index,
        "always_visible": always_visible,
        "sort_vertices": sort_vertices,
        "cell_type": cell_type,
        "hud_color": hud_color
    }
    
    polygons_data.append(polygon_info)
    
    # Ensure 3 or 4 vertices
    if len(vertex_coordinates) != 3 and len(vertex_coordinates) != 4:
        error_message = f"""\n
        ***ERROR***
        Unsupported number of vertices.
        You must either set 3 or 4 coordinates per polgyon.
        """
        raise ValueError(error_message)

    if bound_number == 0 or bound_number == 200 or bound_number >= 32767:
        error_message = """
        ***ERROR***
        Possible problems:
        - Bound Number must be between 1 and 199, and 201 and 32766.
        - There must be at least one polygon with Bound Number 1.
        """
        raise ValueError(error_message)

    
    # Ensure Counterclockwise Winding
    if len(vertex_coordinates) == 3:
        vertex_coordinates = ensure_ccw_order(vertex_coordinates)
        
    elif len(vertex_coordinates) == 4 and fix_faulty_quads:
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

#? ==================CREATING YOUR MAP================== #?

def user_notes(x):
    f""" 
    Please find some Polygons and Texture examples below this text.
    You can already run this the script and create the Test Map yourself
    
    If you're setting a (flat) Quad, make sure the vertices are in the correct order (both clockwise and counterclockwise are acceptable)
    If you're unsure, set "sort_vertices = True" in the "create_polygon()" function
    
    The Material Index (optional variable, defaults to 0). You can use the constants under 'Material types'.    
    Note that you can also set custom Material / Physics  Properties (search for: 'new_physics_properties' in the script)
    
    Texture (UV) mapping examples:
    "tex_coords = compute_uv(bound_number = 1, tile_x = 4, tile_y = 2, angle_degrees = 0)"
    "tex_coords = compute_uv(bound_number = 2, tile_x = 5, tile_y = 2, angle_degrees = 90)"
        
    The variable "texture_darkness" in the function "save_bms()" makes the texture edges darker / lighter. 
    If there are four vertices, you can for example set: "texture_darkness = [40, 2, 50, 1]"
    Where 2 is the default value. I recommend trying out different values to get an idea of the result in-game.
        
    To properly set up the AI, adhere to the following for 'bound_number = x':
    Open Areas: 1-199
    Roads: 201-859
    Intersections: 860+
    """

#! Extra notes:
#! The 'bound_number' can not be equal to 0, 200, be negative, or be greater than 32767
#! There must exist a polygon with 'bound_number = 1'
    
#! If you wish to modify or add Material, Cell or HUD constants you are importing/exporting to Blender
#! then you must also modify the respective IMPORTS and EXPORTS
#! For Cells, this would be "CELL_IMPORT" and "CELL_EXPORT"

# Cell / Room types 
DEFAULT = 0   
TUNNEL = 1
INDOORS = 2
WATER_DRIFT = 4         
NO_SKIDS = 200 
                  
# Material types
DEFAULT_MTL = 0 
GRASS_MTL = 87
WATER_MTL = 91
STICKY_MTL = 97
NO_FRICTION_MTL = 98 

# Textures
SNOW_TX = "SNOW"
WOOD_TX = "T_WOOD"
WATER_TX = "T_WATER"
WATER_WINTER_TX = "T_WATER_WIN"
GRASS_TX = "T_GRASS"
GRASS_WINTER_TX = "T_GRASS_WIN"
GRASS_BASEBALL_TX = "24_GRASS"

SIDEWALK_TX = "SDWLK2"
ZEBRA_CROSSING_TX = "RWALK"
INTERSECTION_TX = "RINTER"

FREEWAY_TX = "FREEWAY2"
ROAD_1_LANE_TX = "R2"
ROAD_2_LANE_TX = "R4"
ROAD_3_LANE_TX = "R6"

BRICKS_MALL_TX = "OT_MALL_BRICK"
BRICKS_SAND_TX = "OT_SHOP03_BRICK"
BRICKS_GREY_TX = "CT_FOOD_BRICK"

GLASS_TX = "R_WIN_01"
STOP_SIGN_TX = "T_STOP"
BARRICADE_TX = "T_BARRICADE"
CHECKPOINT_TX = "CHECK04"
BUS_RED_TOP = "VPBUSRED_TP_BK"
             
# HUD map colors
WOOD_HUD = '#7b5931'
SNOW_HUD = '#cdcecd'
WATER_HUD = '#5d8096'
ROAD_HUD = '#414441'
GRASS_HUD = '#396d18'
DARK_RED = '#af0000'
ORANGE = "#ffa500"
LIGHT_RED = "#ff7f7f"
LIGHT_YELLOW = '#ffffe0'


#! ======================== MAIN AREA ======================== #*
# Main Area Colored Checkpoints
create_polygon(
    bound_number = 9999,
    vertex_coordinates = [
        (-25.0, 0.0, 85.0),
        (25.0, 0.0, 85.0),
        (25.0, 0.0, 70.0),
        (-25.0, 0.0, 70.0)])

save_bms(texture_name = [CHECKPOINT_TX],
         tex_coords = compute_uv(bound_number = 9999, tile_x = 5, tile_y = 1, angle_degrees = 0))

# Main Area w/ Building | Road
create_polygon(
    bound_number = 201,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
        (50.0, 0.0, 70.0),
        (50.0, 0.0, -70.0),
        (-50.0, 0.0, -70.0)])

save_bms(
    texture_name = [ROAD_3_LANE_TX], texture_darkness = [40, 2, 50, 1],
    tex_coords = compute_uv(bound_number = 201, tile_x = 10, tile_y = 10, angle_degrees = 45))

# Main Grass Area | Intersection 
create_polygon(
	bound_number = 861,
	material_index = GRASS_MTL,
	vertex_coordinates = [
        (-50.0, 0.0, -70.0),
		(10.0, 0.0, -70.0),
        (10.0, 0.0, -130.0),
		(-50.0, 0.0, -130.0)],
        hud_color = GRASS_HUD)

save_bms(
    texture_name = [GRASS_BASEBALL_TX], 
    tex_coords = compute_uv(bound_number = 861, tile_x = 7, tile_y = 7, angle_degrees = 90))

# Main Grass Area Brown | Road
create_polygon(
	bound_number = 202,
	material_index = GRASS_MTL,
	vertex_coordinates = [
		(10.0, 0.0, -70.0),
        (50.0, 0.0, -70.0),
		(50.0, 0.0, -130.0),
        (10.0, 0.0, -130.0)],
        hud_color = WATER_HUD)

save_bms(
    texture_name = [GRASS_WINTER_TX], 
    tex_coords = compute_uv(bound_number = 202, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Main Snow Area | Landmark (change?)
create_polygon(
	bound_number = 1,
    cell_type = NO_SKIDS,
    material_index = NO_FRICTION_MTL,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)],
         hud_color = SNOW_HUD)

save_bms(
    texture_name = [SNOW_TX], 
    tex_coords = compute_uv(bound_number = 1, tile_x = 10, tile_y = 10, angle_degrees = 90))

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
    texture_name = [BARRICADE_TX], 
    tex_coords = compute_uv(bound_number = 862, tile_x = 50, tile_y = 50, angle_degrees = 0))

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
    texture_name = [WOOD_TX], 
    tex_coords = compute_uv(bound_number = 203, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Main Water Area | Landmark
create_polygon(
	bound_number = 2,
    cell_type = WATER_DRIFT,
	material_index = WATER_MTL,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)],
        hud_color = WATER_HUD)

save_bms(
    texture_name = [WATER_WINTER_TX], 
    tex_coords = compute_uv(bound_number = 2, tile_x = 10, tile_y = 10, angle_degrees = 0))

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
    texture_name = [GRASS_BASEBALL_TX],
    tex_coords=compute_uv(bound_number = 863, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Triangle Brick I |
create_polygon(
    bound_number = 204,
    cell_type = NO_SKIDS,
    vertex_coordinates = [
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0),
        (-50.0, 0.0, 0.0)],
        hud_color = LIGHT_YELLOW)

save_bms(
    texture_name = [BRICKS_MALL_TX],
    tex_coords = compute_uv(bound_number = 204, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Triangle Brick II | to be decided
create_polygon(
    bound_number = 205,
    cell_type = NO_SKIDS,
    vertex_coordinates = [
        (-50.0, 0.0, 140.0),
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0)],
        hud_color = LIGHT_YELLOW)

save_bms(
    texture_name = [BRICKS_MALL_TX],
    tex_coords = compute_uv(bound_number = 205, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Main Orange Hill | 
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
    texture_name = [WATER_TX], 
    tex_coords = compute_uv(bound_number = 3, tile_x = 10, tile_y = 100, angle_degrees = 90))


#! ======================== ORANGE BUILDING ======================== #*
# Orange Building Wall "South" | Landmark
create_polygon(
    bound_number = 4,
    always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -50.0),
        (10.0, 0.0, -50.0),
        (10.0, 30.0, -50.11),
        (-10.0, 30.0, -50.11)])

save_bms(
    texture_name = [SNOW_TX],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 4, tile_x = 1, tile_y = 1, angle_degrees = 0))

# Orange Building Wall "North" | Landmark
create_polygon(
    bound_number = 5,
    always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -70.00),
        (-10.0, 30.0, -69.99),
        (10.0, 30.0, -69.99),
        (10.0, 0.0, -70.00)])

save_bms(
    texture_name = [SNOW_TX],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 5, tile_x = 1, tile_y = 1, angle_degrees = 0))

# Orange Building Wall "West" | Landmark
create_polygon(
    bound_number = 6,
    always_visible = False,
    vertex_coordinates = [
        (-9.99, 30.0, -50.0),
        (-9.99, 30.0, -70.0),
        (-10.0, 0.0, -70.0),
        (-10.0, 0.0, -50.0)])

save_bms(
    texture_name = [SNOW_TX],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 6, tile_x = 1, tile_y = 1, angle_degrees = 0))

# Orange Building Wall "East" | Landmark
create_polygon(
    bound_number = 7,
    always_visible = False,
    vertex_coordinates = [
        (10.0, 0.0, -70.0),
        (9.9, 30.0, -70.0),
        (9.9, 30.0, -50.0),
        (10.0, 0.0, -50.0)])

save_bms(
    texture_name = [SNOW_TX],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 7, tile_x = 1, tile_y = 1, angle_degrees = 0))

# Orange Building Rooftop | Intersection
create_polygon(
    bound_number = 900,
    cell_type = NO_SKIDS,
    material_index = NO_FRICTION_MTL,
    vertex_coordinates = [
        (10.0, 30.0, -70.0),
        (-10.0, 30.0, -70.0),
        (-10.0, 30.0, -50.0),
        (10.0, 30.0, -50.0)])

save_bms(
    texture_name = [SNOW_TX],
    tex_coords = compute_uv(bound_number = 900, tile_x = 1, tile_y = 1, angle_degrees = 0))


#! ======================== BRIDGES AND FREEWAY ======================== #*
# Bridge I East | Road
create_polygon(
	bound_number = 250,
	vertex_coordinates = [
		(-82.6, 0.0, -80.0),
		(-50.0, 0.0, -80.0),
		(-50.0, 0.0, -120.0),
		(-82.6, 0.0, -120.0)])
save_bms(
    texture_name = [INTERSECTION_TX], 
    tex_coords = compute_uv(bound_number = 250, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Bridge II West | Road
create_polygon(
	bound_number = 251,
	vertex_coordinates = [
		(-119.01, 0.0, -80.0),
		(-90.0, 0.0, -80.0),
		(-90.0, 0.0, -120.0),
		(-119.01, 0.0, -120.0)])

save_bms(
    texture_name = [GRASS_TX], 
    tex_coords = compute_uv(bound_number = 251, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Road West of West Bridge | Road
create_polygon(
	bound_number = 252,
	vertex_coordinates = [
        (-160.0, 0.0, -80.0),
		(-119.1, 0.0, -80.0),
        (-119.1, 0.0, -120.0),
		(-160.0, 0.0, -120.0)])

save_bms(
    texture_name = [ROAD_3_LANE_TX], 
    tex_coords = compute_uv(bound_number = 252, tile_x = 5, tile_y = 3, angle_degrees = 0))

# Intersection West of Bridges | Intersection
create_polygon(
	bound_number = 950,
	vertex_coordinates = [
        (-200.0, 0.0, -80.0),
		(-160.0, 0.0, -80.0),
        (-160.0, 0.0, -120.0),
		(-200.0, 0.0, -120.0)])

save_bms(
    texture_name = [INTERSECTION_TX], 
    tex_coords = compute_uv(bound_number = 950, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Far West Freeway | Road
create_polygon(
	bound_number = 253,
	vertex_coordinates = [
		(-196.0, 0.0, 320.0),
		(-164.0, 0.0, 320.0),
		(-164.0, 0.0, -80.0),
		(-196.0, 0.0, -80.0)])

save_bms(
    texture_name = [FREEWAY_TX], 
    tex_coords = compute_uv(bound_number = 253, tile_x = 15, tile_y = 2, angle_degrees = 90))

# West Freeway Sidewalk I | Road
create_polygon(
	bound_number = 254,
	vertex_coordinates = [
        (-164.0, 0.0, 320.0),
        (-160.0, 0.0, 320.0),
        (-160.0, 0.0, -80.0),
		(-164.0, 0.0, -80.0)])

save_bms(
    texture_name = [SIDEWALK_TX], 
    tex_coords = compute_uv(bound_number = 254, tile_x = 50, tile_y = 1, angle_degrees = 90))

# West Freeway Sidewalk II | Road
create_polygon(
	bound_number = 255,
	vertex_coordinates = [
        (-200.0, 0.0, 320.0),
        (-196.0, 0.0, 320.0),
        (-196.0, 0.0, -80.0),
        (-200.0, 0.0, -80.0)])

save_bms(
    texture_name = [SIDEWALK_TX], 
    tex_coords = compute_uv(bound_number = 255, tile_x = 50, tile_y = 1, angle_degrees = 270))

# West Freeway South Intersection | Intersection
create_polygon(
	bound_number = 951,
	vertex_coordinates = [
        (-200.0, 0.0, 360.0),
        (-160.0, 0.0, 360.0),
        (-160.0, 0.0, 320.0),
        (-200.0, 0.0, 320.0)])

save_bms(
    texture_name = [INTERSECTION_TX], 
    tex_coords = compute_uv(bound_number = 951, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Road Hill South West | Road
create_polygon(
	bound_number = 256,
	vertex_coordinates = [
        (-160.0, 0.0, 360.0),
        (0.0, 26.75, 360.0),
        (0.0, 26.75, 320.0),
        (-160.0, 0.0, 320.0)])

save_bms(
    texture_name = [ROAD_2_LANE_TX], 
    tex_coords = compute_uv(bound_number = 256, tile_x = 10, tile_y = 4, angle_degrees = 0))


#! ======================== BRIDGE SPLIT SOUTH SECTION ======================== #*
# Bridge Road Split | Intersection
create_polygon(
	bound_number = 925,
	vertex_coordinates = [
		(-90.0, 14.75, -80.0),
		(-79.0, 14.75, -80.0),
		(-79.0, 14.75, -120.0),
		(-90.0, 14.75, -120.0)])

save_bms(
    texture_name = [INTERSECTION_TX], 
    tex_coords = compute_uv(bound_number = 925, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Striped Bridge Road South | Road
create_polygon(
	bound_number = 226,
	vertex_coordinates = [
		(-90.0, 14.75, -35.0),
		(-79.0, 14.75, -35.0),
		(-79.0, 14.75, -80.0),
		(-90.0, 14.75, -80.0)])

save_bms(
    texture_name = [ZEBRA_CROSSING_TX], 
    tex_coords = compute_uv(bound_number = 226, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Bridge Road South Intersection | Intersection
create_polygon(
	bound_number = 926,
	vertex_coordinates = [
		(-90.0, 14.75, -15.0),
		(-79.0, 14.75, -15.0),
		(-79.0, 14.75, -35.0),
		(-90.0, 14.75, -35.0)])

save_bms(
    texture_name = [INTERSECTION_TX], 
    tex_coords = compute_uv(bound_number = 926, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Striped Bridge Road South Hill UP I | Road
create_polygon(
	bound_number = 227,
	vertex_coordinates = [
		(-79.0, 14.75, -15.0),
		(-90.0, 14.75, -15.0),
		(-80.0, 26.75, 85.0),
		(-69.0, 26.75, 85.0)])

save_bms(
    texture_name = [ZEBRA_CROSSING_TX], 
    tex_coords = compute_uv(bound_number = 227, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Striped Bridge Road South Hill UP II | Road
create_polygon(
	bound_number = 228,
	vertex_coordinates = [
		(-160.0, 0.0, 20.0),
		(-160.0, 0.0, 40.0),
		(-110.0, 10.0, 20.0),
        (-110.0, 10.0, 0.0)])

save_bms(
    texture_name = [BRICKS_SAND_TX], 
    tex_coords = compute_uv(bound_number = 228, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Bridge Road South Hill Freeway I | Road
create_polygon(
	bound_number = 233,
	vertex_coordinates = [
		(-69.0, 26.75, 85.0),
		(-80.0, 26.75, 85.0),
		(0.0, 26.75, 320.0),
		(11.0, 26.75, 320.0)])

save_bms(
    texture_name = [ZEBRA_CROSSING_TX], 
    tex_coords = compute_uv(bound_number = 233, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Bridge Road South Hill Freeway II | Road
create_polygon(
	bound_number = 234,
	vertex_coordinates = [
		(-90.0, 14.75, -15.0),
		(-90.0, 14.75, -40.0),
		(-110.0, 10.0, 0.0),
		(-110.0, 10.0, 20.0)])

save_bms(
    texture_name = [ZEBRA_CROSSING_TX], 
    tex_coords = compute_uv(bound_number = 234, tile_x = 5, tile_y = 5, angle_degrees = 90))


#! ======================== ELEVATED SECTION ======================== #*

# Elevated South South Intersection I | Intersection
create_polygon(
	bound_number = 952,
	vertex_coordinates = [
		(0.0, 26.75, 360.0),
		(80.0, 26.75, 360.0),
		(80.0, 26.75, 320.0),
		(0.0, 26.75, 320.0)])

save_bms(
    texture_name = [INTERSECTION_TX], 
    tex_coords = compute_uv(bound_number = 952, tile_x = 4, tile_y = 5, angle_degrees = 90))

# Elevated South East Intersection I | Road
create_polygon(
	bound_number = 300,
	vertex_coordinates = [
		(50.0, 26.75, 320.0),
		(80.0, 26.75, 320.0),
        (80.0, 26.75, 200.0),
		(50.0, 26.75, 200.0)])

save_bms(
    texture_name = [ROAD_2_LANE_TX], 
    tex_coords = compute_uv(bound_number = 300, tile_x = 15, tile_y = 4, angle_degrees = 90))

# Elevated South East Road I | Road
create_polygon(
	bound_number = 953,
	vertex_coordinates = [
		(50.0, 26.75, 200.0),
		(80.0, 26.75, 200.0),
		(50.0, 26.75, 50.0),
		(20.0, 26.75, 50.0)])

save_bms(
    texture_name = [ROAD_2_LANE_TX], 
    tex_coords = compute_uv(bound_number = 953, tile_x = 5, tile_y = 15, angle_degrees = 90))

# Elevated South East Road I | Road
create_polygon(
	bound_number = 301,
	vertex_coordinates = [
		(50.0, 26.75, 200.0),
		(80.0, 26.75, 200.0),
		(50.0, 26.75, 50.0),
		(20.0, 26.75, 50.0)])

save_bms(
    texture_name = [ROAD_2_LANE_TX], 
    tex_coords = compute_uv(bound_number = 301, tile_x = 15, tile_y = 4, angle_degrees = 90))

# Bump to Elevated Building Rooftop Section | Road
create_polygon(
	bound_number = 302,
	vertex_coordinates = [
		(20.0, 26.75, 50.0),
		(50.0, 26.75, 50.0),
		(50.0, 30.00, 40.0),
		(20.0, 30.30, 40.0)])

save_bms(
    texture_name = [ROAD_2_LANE_TX], 
    tex_coords = compute_uv(bound_number = 302, tile_x = 2, tile_y = 4, angle_degrees = 90))


#! ======================== ORANGE BUILDING ROADS AND CONNECTION TO ELEVATED PART ======================== #*
# Hill Connected to Bridge Prop (Jump) | Road
create_polygon(
	bound_number = 501,
	vertex_coordinates = [
		(20.0, 30.0, 0.0),
        (50.0, 30.0, 0.0),
        (50.0, 12.0, -69.9),
        (20.0, 12.0, -69.9)])

save_bms(
    texture_name = [ROAD_3_LANE_TX], 
    tex_coords = compute_uv(bound_number = 501, tile_x = 3, tile_y = 2, angle_degrees = 90))

# Intersection Orange Building
create_polygon(
	bound_number = 1100,
	vertex_coordinates = [
		(20.0, 30.0, 40.0),
        (50.0, 30.0, 40.0),
        (50.0, 30.0, 0.0),
        (20.0, 30.0, 0.0)])

save_bms(
    texture_name = [BRICKS_GREY_TX], 
    tex_coords = compute_uv(bound_number = 1100, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Road To Rooftop (Red Bus Color) | Road
create_polygon(
	bound_number = 502,
	vertex_coordinates = [
		(-10.0, 30.0, 40.0),
        (20.0, 30.0, 40.0),
        (20.0, 30.0, 0.0),
        (-10.0, 30.0, 0.0)])

save_bms(
    texture_name = [BUS_RED_TOP], 
    tex_coords = compute_uv(bound_number = 502, tile_x = 4, tile_y = 3, angle_degrees = 0))

# Road To Orange Building I | Road
create_polygon(
	bound_number = 503,
	vertex_coordinates = [
		(-10.0, 30.0, 0.0),
        (10.0, 30.0, 0.0),
        (10.0, 30.0, -50.0),
        (-10.0, 30.0, -50.0)])

save_bms(
    texture_name = [GLASS_TX], 
    tex_coords = compute_uv(bound_number = 503, tile_x = 5, tile_y = 12, angle_degrees = 0))


#! ======================== SPEEDBUMPS ======================== #*
# Speed Bump Front | No Type
create_polygon(
	bound_number = 206,
	vertex_coordinates = [ 
     (50.00,0.00,-130.00), 
     (50.00,3.00,-135.00), 
     (-50.00,3.00,-135.00), 
     (-50.00,0.00,-130.00)],
    hud_color = LIGHT_RED)

save_bms(
    texture_name = [STOP_SIGN_TX], 
    tex_coords = compute_uv(bound_number = 206, tile_x = 15, tile_y = 1, angle_degrees = 90))

# Speed Bump Front | No Type
create_polygon(
	bound_number = 207,
	vertex_coordinates = [
		(-50.0, 3.0, -135.0),
		(50.0, 3.0, -135.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)],
         hud_color = LIGHT_RED)

save_bms(
    texture_name = [STOP_SIGN_TX], 
    tex_coords = compute_uv(bound_number = 207, tile_x = 1, tile_y = 10, angle_degrees = 0))

# Speed Bump Triangle Side I | No Type
create_polygon(
	bound_number = 208,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(-50.01, 0.0, -130.0),
		(-50.0, 3.0, -135.0)])

save_bms(
    texture_name = [STOP_SIGN_TX], 
    tex_coords = compute_uv(bound_number = 208, tile_x = 30, tile_y = 30, angle_degrees = 90))

# Speed Bump Triangle Side II | No Type
create_polygon(
	bound_number = 209,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(50.01, 0.0, -130.0),
		(50.0, 3.0, -135.0)])

save_bms(
    texture_name = [STOP_SIGN_TX], 
    tex_coords = compute_uv(bound_number = 209, tile_x = 30, tile_y = 30, angle_degrees = 90))


#! ======================== HIGHWAY CURVED TUNNEL ======================== #* 
create_polygon(
	bound_number = 2220,
	vertex_coordinates = [
		(-160.0, -0.00, -120.0),
		(-200.0, -0.00, -120.0),
		(-160.0, -3.0, -160.0)])

save_bms(texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2220, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2221,
	vertex_coordinates = [
		(-200.0, -0.00, -120.0),
        (-160.0, -3.0, -160.0),
		(-200.0, -3.0, -160.0)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2221, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2222,
	vertex_coordinates = [
		(-160.0, -3.0, -160.0),
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2222, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2223,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0),
		(-191.82, -6.00, -223.82)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2223, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2224,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2224, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2225,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82),
		(-165.59, -9.00, -260.54)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2225, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2226,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2226, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2227,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54),
		(-127.21, -12.00, -286.30)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2227, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2228,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2228, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2229,
	vertex_coordinates = [
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30),
		(-90.0, -15.00, -294.48)])

save_bms(
	texture_name = [FREEWAY_TX],
	tex_coords = compute_uv(bound_number = 2229, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

# Hill Downwards from Bridges | Road
create_polygon(
	bound_number = 923,
	vertex_coordinates = [
		(-79.0, -15.00, -254.51),
		(-90.0, -15.00, -254.51),
        (-90.0, 14.75, -120.0),
		(-79.0, 14.75, -120.0)],
	hud_color = LIGHT_YELLOW)

save_bms(
	texture_name = [ZEBRA_CROSSING_TX],
	tex_coords = compute_uv(bound_number = 923, tile_x = 5.0, tile_y = 5.0, angle_degrees = 0))

# Slim Intersection connected to Downwards Hill
create_polygon(
	bound_number = 924,
	vertex_coordinates = [
        (-90.0, -15.00, -254.51),
        (-79.0, -15.00, -254.51),
        (-79.0, -15.00, -294.48),
        (-90.0, -15.00, -294.48)])

save_bms(
	texture_name = [INTERSECTION_TX],
	tex_coords = compute_uv(bound_number = 924, tile_x = 5.0, tile_y = 5.0, angle_degrees = 0))

################################################################################################################               
################################################################################################################ 

# Create SHOP and FOLDER structure   
def create_folders(map_filename: str) -> None:
    FOLDER_STRUCTURE = [
        BASE_DIR / "build", 
        SHOP / "BMP16", 
        SHOP / "TEX16O", 
        SHOP / "TUNE", 
        SHOP / "MTL", 
        SHOP / "CITY" / map_filename,
        SHOP / "RACE" / map_filename,
        SHOP / "BMS" / f"{map_filename}CITY",
        SHOP / "BMS" / f"{map_filename}LM",
        SHOP / "BND" / f"{map_filename}CITY",
        SHOP / "BND" / f"{map_filename}LM"]
    
    for path in FOLDER_STRUCTURE:
        os.makedirs(path, exist_ok = True)
        
        
def create_city_info(map_name: str, map_filename: str) -> None: 
    cinfo_folder = SHOP / "TUNE"
    cinfo_file = f"{map_filename}.CINFO"
    
    with open(cinfo_folder / cinfo_file, "w") as f:
        blitz_names = '|'.join(blitz_race_names)
        circuit_names = '|'.join(circuit_race_names)
        checkpoint_names = '|'.join(checkpoint_race_names)

        f.write(f"""
LocalizedName={map_name}
MapName={map_filename}
RaceDir={map_filename.lower()}
BlitzCount={len(blitz_race_names)}
CircuitCount={len(circuit_race_names)}
CheckpointCount={len(circuit_race_names)}
BlitzNames={blitz_names}
CircuitNames={circuit_names}
CheckpointNames={checkpoint_names}
""")
        
                    
def copy_custom_textures() -> None: 
    input_folder = BASE_DIR / "Custom Textures"
    output_folder = SHOP / "TEX16O"

    for custom_texs in input_folder.iterdir():
        shutil.copy(custom_texs, output_folder / custom_texs.name)


def edit_and_copy_mmbangerdata(bangerdata_properties) -> None:
    input_folder = BASE_DIR / 'Core AR' / 'TUNE'
    output_folder = SHOP / 'TUNE'

    for file in input_folder.glob('*.MMBANGERDATA'):
        if file.stem not in bangerdata_properties:
            shutil.copy(file, output_folder)
            
    for prop_key, properties in bangerdata_properties.items():
        banger_files = input_folder / f"{prop_key}.MMBANGERDATA"
        
        if banger_files.exists():
            with open(banger_files, 'r') as f: 
                lines = f.readlines()

            for i, line in enumerate(lines):
                for key, new_value in properties.items():
                    if line.strip().startswith(key):
                        lines[i] = f'\t{key} {new_value}\n'
            
            tweaked_banger_files = output_folder / banger_files.name
            with open(tweaked_banger_files, 'w') as f:
                f.writelines(lines)
                
                
def copy_core_tune_files() -> None:
    input_folder = BASE_DIR / 'Core AR' / 'TUNE'
    output_folder = SHOP / 'TUNE'
    
    non_mmbangerdata_files = [f for f in input_folder.glob('*') if not f.name.endswith('.MMBANGERDATA')]
    
    for file in non_mmbangerdata_files:
        shutil.copy(file, output_folder)
                
                
def copy_dev_folder(mm1_folder: Path, map_filename: str) -> None:
    dev_folder = BASE_DIR / 'dev'
    mm1_folder = Path(mm1_folder) / 'dev'
    
    shutil.rmtree(mm1_folder, ignore_errors = True)  
    shutil.copytree(dev_folder, mm1_folder)
    
    mm1_dev_ai_files = dev_folder / 'CITY' / map_filename
    shutil.rmtree(mm1_dev_ai_files, ignore_errors = True)
    
################################################################################################################               
################################################################################################################ 

#! ================== THIS SECTION IS RELATED TO RACE FILES ================== !#

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


def fill_mm_date_values(race_type: str, user_values):
    # Default values that are common to all modes.
    default_values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # Debug: [44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44]
    
    # Mappings to determine which positions in default_values are replaced by user values.
    replace_values = {        
        BLITZ: [1, 2, 3, 4, 5, 6, 7, 8],  # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit
        CIRCUIT: [1, 2, 3, 4, 5, 6, 7],   # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps
        RACE: [1, 2, 3, 4, 5, 6]          # TimeofDay, Weather, Opponents, Cops, Ambient, Peds
    }
        
    modified_list = default_values.copy()
    
    for idx, value in zip(replace_values[race_type], user_values):
        modified_list[idx] = value

    # Return only the needed portion of the filled list (i.e. removing the repeated "Difficulty")
    return modified_list[:10]  


def write_waypoints(opp_wp_file, waypoints, race_desc, race_index, opponent_num = None):
    with open(opp_wp_file, "w") as f:
        if opponent_num is not None:  # Opponent waypoint header
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

    MOVE(opp_wp_file, SHOP / "RACE" / map_filename / opp_wp_file)
    
    
def write_mm_data(mm_data_file, configs, race_type, prefix):
    header = ",".join(["Description"] + 2 * ["CarType", "TimeofDay", "Weather", "Opponents", "Cops", "Ambient", "Peds", "NumLaps", "TimeLimit", "Difficulty"])
    
    with open(mm_data_file, 'w') as f:
        f.write(header + "\n")
        
        for race_index, config in configs.items():
            if race_type == 'RACE':
                race_desc = prefix  
            else:
                race_desc = prefix + str(race_index)
            
            ama_filled_values = fill_mm_date_values(race_type, config['mm_data']['ama'])
            pro_filled_values = fill_mm_date_values(race_type, config['mm_data']['pro'])
                        
            data_string = race_desc + "," + ",".join(map(str, ama_filled_values)) + "," + ",".join(map(str, pro_filled_values))
            
            f.write(data_string + "\n")  # Write the data string to file
            
    MOVE(mm_data_file, SHOP / "RACE" / map_filename / mm_data_file)


def write_aimap(map_filename: str, race_type: str, race_index: int, aimap_config, opponent_cars, num_of_opponents: int):
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
            
    MOVE(aimap_file_name, SHOP / "RACE" / map_filename / aimap_file_name)

    
def create_races(map_filename: str, race_data) -> None:
    for race_type, race_configs in race_data.items():
        if race_type == 'RACE':  # For Checkpoint races
            if len(race_configs) > len(checkpoint_prefixes):
                race_num_error = """
                ***ERROR***
                Number of Checkpoint races cannot be more than 12
                """
                raise ValueError(race_num_error)
                        
            for idx, (race_index, config) in enumerate(race_configs.items()):
                prefix = checkpoint_prefixes[race_index]
                
                # Player Waypoints with Checkpoint prefix
                write_waypoints(f"{race_type}{race_index}WAYPOINTS.CSV", config['waypoints'], race_type, race_index)
                
                # Opponent-specific Waypoints
                for opp_idx, (opp_car, opp_waypoints) in enumerate(config['opponent_cars'].items()):
                    write_waypoints(
                        f"OPP{opp_idx}{race_type}{race_index}{race_type_to_extension[race_type]}{race_index}", 
                        opp_waypoints, race_type, race_index, opponent_num = opp_idx)
                
                write_mm_data(f"MM{race_type}DATA.CSV", {race_index: config}, race_type, prefix)
                write_aimap(map_filename, race_type, race_index, 
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
                write_aimap(map_filename, race_type, idx, 
                            config['aimap'], config['opponent_cars'],
                            num_of_opponents = config['aimap'].get('num_of_opponents', len(config['opponent_cars'])))

                
def create_cnr(map_filename: str, cnr_waypoints: List[Tuple[float, float, float]]) -> None:
        cnr_file = "COPSWAYPOINTS.CSV"
        header = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"
        filler = ",0,0,0,0,0,\n"
        
        with open(cnr_file, "w") as f:
            f.write(header)
            for i in range(0, len(cnr_waypoints), 3):
                f.write(", ".join(map(str, cnr_waypoints[i])) + filler) 
                f.write(", ".join(map(str, cnr_waypoints[i+1])) + filler)
                f.write(", ".join(map(str, cnr_waypoints[i+2])) + filler)

        MOVE(cnr_file, SHOP / "RACE" / map_filename / cnr_file)
  
################################################################################################################               
################################################################################################################              

_H = 8
_A2 = 32

# Create Cells                     
def create_cells(map_filename: str, truncate_cells: bool) -> None:
    bms_files = []
    bms_a2_files = set()
    
    landmark_folder = SHOP / "BMS" / f"{map_filename}LM"
    city_folder = SHOP / "BMS" / f"{map_filename}CITY"
    
    for folder in [landmark_folder, city_folder]:
        for file in folder.iterdir():
            if file.name.endswith(".bms"):
                bound_number = int(re.findall(r'\d+', file.name)[0])
                bms_files.append(bound_number)
                if file.name.endswith("_A2.bms"):
                    bms_a2_files.add(bound_number)
    
    cells_folder = SHOP_CITY
    cells_file = f"{map_filename}.CELLS"
    
    with open(cells_folder / cells_file, "w") as f:
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
            
        if 200 <= max_warning_count < 254:
            warning_message = f"""
            ***WARNING***
            Close to row character limit 254 in .CELLS file. 
            Maximum character count encountered is {max_warning_count}.
            To reduce the charachter count, consider setting 'always_visible' to False for some polygons.
            If the 'bound_number' is 99 (2 charachters), then it consumes 3 characters in the CELLS file.
            *************\n
            """
            print(warning_message)
        
        elif max_error_count >= 254:
            error_message = f"""
            ***ERROR***
            Character limit of 254 exceeded in .CELLS file.
            Maximum character count encountered is {max_error_count}.
            To solve the problem, set 'always_visible' to False for some polygons.
            If the 'bound_number' is 99 (2 charachters), then it consumes 3 characters in the CELLS file.
            """
            raise ValueError(error_message)
        

# Create EXT file                      
def create_ext(map_filename: str, polygons: List[Vector3]) -> Tuple[float, float, float, float]:
    x_coords = [vertex[0] for poly in polygons for vertex in poly]
    z_coords = [vertex[2] for poly in polygons for vertex in poly]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_z, max_z = min(z_coords), max(z_coords)

    ext_folder = SHOP_CITY
    ext_file = f"{map_filename}.EXT"

    with open(ext_folder / ext_file, 'w') as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")
        
    return min_x, max_x, min_z, max_z


def create_hudmap(set_minimap: bool, debug_hud: bool, debug_hud_bound_id: bool, shape_outline_color: str,
                        x_offset: float, y_offset: float, line_width: float, background_color: str) -> None:

    if set_minimap and not is_blender_running():
        global hudmap_vertices
        global hudmap_properties
                
        min_x = min(point[0] for polygon in hudmap_vertices for point in polygon)
        max_x = max(point[0] for polygon in hudmap_vertices for point in polygon)
        min_z = min(point[2] for polygon in hudmap_vertices for point in polygon)
        max_z = max(point[2] for polygon in hudmap_vertices for point in polygon)
        
        width = int(max_x - min_x)
        height = int(max_z - min_z)

        def draw_polygon(ax, polygon, shape_outline_color: str, 
                        label = None, add_label = False, hud_fill = False, hud_color = None) -> None:
            
            xs, ys = zip(*[(point[0], point[2]) for point in polygon])
            xs, ys = xs + (xs[0],), ys + (ys[0],)  # the commas after [0] should not be removed
            
            if shape_outline_color:
                ax.plot(xs, ys, color = shape_outline_color, linewidth = line_width)
            
            if hud_fill:
                ax.fill(xs, ys, hud_color)
                
            if add_label: 
                center = calculate_center_tuples(polygon)
                ax.text(center[0], center[2], label, color = 'white', 
                        ha = 'center', va = 'center', fontsize = 4.0)

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
        output_folder = SHOP / 'BMP16'
                  
        plt.savefig(output_folder / f"{map_filename}640.JPG", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.02, facecolor = background_color)
        plt.savefig(output_folder / f"{map_filename}320.JPG", dpi = 1000, bbox_inches = 'tight', pad_inches = 0.02, facecolor = background_color) 
            
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
            ax_debug.set_ylim([max_z, min_z])  # Flip the image vertically
            ax_debug.set_position([0, 0, 1, 1])

            plt.savefig(BASE_DIR / f"{map_filename}_HUD_debug.jpg", dpi = 1, bbox_inches = None, pad_inches = 0, facecolor = 'purple')


# Create Animations                              
def create_animations(map_filename: str, anim_data: Dict[str, List[Tuple]], set_anim: bool) -> None: 
    if set_anim:
        anim_folder = SHOP_CITY / map_filename
        anim_file = "ANIM.CSV"
        
        # List the Plane and Eltrain in the ANIM.CSV file
        with open(anim_folder / anim_file, 'w', newline = '') as main_f:
            for obj in anim_data:
                csv.writer(main_f).writerow([f"anim_{obj}"])
                
                unique_anims = anim_folder / f"ANIM_{obj.upper()}.CSV"
                
                # Write their coordinates to the individual anim files
                with open(unique_anims, 'w', newline = '') as anim_f:                    
                    for coordinates in anim_data[obj]:
                        csv.writer(anim_f).writerow(coordinates)
                        
                        
def create_bridges(map_filename: str, all_bridges, set_bridges: bool):
    if not set_bridges:
        return
    
    ORIENTATION_MAPPINGS = {
        "NORTH": (-10, 0, 0),
        "SOUTH": (10, 0, 0),
        "EAST": (0, 0, 10),
        "WEST": (0, 0, -10),
        "NORTH_EAST": (10, 0, 10),
        "NORTH_WEST": (10, 0, -10),
        "SOUTH_EAST": (-10, 0, 10),
        "SOUTH_WEST": (-10, 0, -10)
    }

    bridge_file = SHOP_CITY / f"{map_filename}.GIZMO"

    # Remove any existing bridge files since we append to the file
    if bridge_file.exists():
        os.remove(bridge_file)

    def calculate_facing(offset: Tuple[float, float, float], orientation: Union[str, float]) -> List[float]:
        if isinstance(orientation, (float, int)):
            angle_radians = math.radians(orientation)
            return [
                offset[0] + 10 * math.cos(angle_radians),
                offset[1],
                offset[2] + 10 * math.sin(angle_radians)
            ]

        if orientation in ORIENTATION_MAPPINGS:
            return [offset[i] + ORIENTATION_MAPPINGS[orientation][i] for i in range(3)]
         
        orientation_error = f"""
        ***ERROR***
        Invalid Bridge Orientation.
        Please choose from one of the following: NORTH, SOUTH, EAST, WEST,
        NORTH_EAST, NORTH_WEST, SOUTH_EAST, SOUTH_WEST or set the orientation
        using a numeric value between 0 and 360 degrees.
        """
        raise ValueError(orientation_error)
        
    def generate_attribute_lines(bridge_attributes):
        lines = ""
        for attr in bridge_attributes:
            attr_offset, attr_orientation, attr_id, attr_type = attr
            attr_facing = calculate_facing(attr_offset, attr_orientation)
            
            line = f"\t{attr_type},{attr_id},{','.join(map(str, attr_offset))},{','.join(map(str, attr_facing))}\n"
            lines += line
        return lines

    bridge_data = []  

    for bridge in all_bridges:
        offset, orientation, id, drawbridge, bridge_attributes = bridge

        face = calculate_facing(offset, orientation)
        drawbridge_values = f"{drawbridge},0,{','.join(map(str, offset))},{','.join(map(str, face))}"
        attributes = generate_attribute_lines(bridge_attributes)

        num_fillers = 5 - len(bridge_attributes)
        filler = f"\t{CROSSGATE},0,-999.99,0.00,-999.99,-999.99,0.00,-999.99\n"     
        fillers = filler * num_fillers

        data = (
            f"DrawBridge{id}\n"
            f"\t{drawbridge_values}\n"
            f"{attributes}"
            f"{fillers}"
            f"DrawBridge{id}\n"  
            )

        bridge_data.append(data)

    with open(bridge_file, "a") as f:
        f.writelines(bridge_data)


def custom_bridge_config(configs, set_bridges, output_folder):    
    config_template = """
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
        "Mode": SINGLE
        }
    
    if set_bridges:
        for config in configs:
            final_config = {**default_config, **config}
            config_str = config_template.format(**final_config)
            
            race_type = final_config["RaceType"]
            filenames = []

            if race_type in [ROAM, COPS_N_ROBBERS]:
                base_name = ROAM if race_type == ROAM else COPS_N_ROBBERS
                
                if final_config["Mode"] in [SINGLE, ALL_MODES]:
                    filenames.append(f"{base_name}.MMBRIDGEMGR")
                if final_config["Mode"] in [MULTI, ALL_MODES]:
                    filenames.append(f"{base_name}M.MMBRIDGEMGR")
            else:
                if race_type not in [RACE, CIRCUIT, BLITZ]:                
                    type_error_message = f"""\n
                    ***ERROR***
                    Invalid RaceType. 
                    Must be one of {ROAM}, {BLITZ}, {RACE}, {CIRCUIT}, or {COPS_N_ROBBERS}.
                    """
                    raise ValueError(type_error_message)
                
                if final_config["Mode"] in [SINGLE, ALL_MODES]:
                    filenames.append(f"{race_type}{final_config['RaceNum']}.MMBRIDGEMGR")
                if final_config["Mode"] in [MULTI, ALL_MODES]:
                    filenames.append(f"{race_type}{final_config['RaceNum']}M.MMBRIDGEMGR")
            
            for filename in filenames:
                (output_folder / filename).write_text(config_str)
                
################################################################################################################               
################################################################################################################

#! ================== THIS SECTION IS RELATED TO PORTALS ================== !#

#! ########### Code by 0x1F9F1 / Brick (Modified) ############ !#      
                 
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
def prepare_portals(polys: List[Polygon], vertices: List[Vector3]):
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
def create_portals(
    map_filename: str, polys: List[Polygon], vertices: List[Vector3], 
    empty_portals: bool, debug_portals: bool) -> None:
    
    portals_folder = SHOP_CITY
    portals_file = f"{map_filename}.PTL"
    
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

#! ########### Code by 0x1F9F1 / Brick (Modified) ############ !#                   

################################################################################################################               
################################################################################################################            
                               
# BINARYBANGER CLASS                            
class BinaryBanger:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, name: str):
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.name = name
        
    @classmethod
    def readn(cls, f):
        return read_unpack(f, '<I')[0]
            
    @classmethod
    def read(cls, f):
        room, flags = read_unpack(f, '<HH')
        offset = Vector3.read(f)
        face = Vector3.read(f)  
        name = cls.read_name(f)
        return cls(room, flags, offset, face, name)
    
    @staticmethod
    def read_name(f):
        name_data = bytearray()
        while True:
            char = f.read(1)
            if char == b'\x00':
                break
            name_data.extend(char)
        return name_data.decode('utf-8')
                
    def __repr__(self):
        return f'''
BinaryBanger
Room: {self.room}
Flags: {self.flags}
Start: {self.offset}
Face: {self.face}
Prop Name: {self.name}
    '''

# PROP EDITOR CLASS
class PropEditor:
    def __init__(self, map_filename: str, debug_props: bool, append_props: bool = False, output_prop_f: str = None):  # Do not change
        self.objects = []  
        self.map_filename = map_filename  

        if append_props:
            self.filename = map_filename 
        else:
            self.filename = SHOP_CITY / f"{map_filename}.BNG"
                    
        self.debug_props = debug_props
        self.debug_filename = "PROPS_debug.txt"
        
        self.prop_dim_file = BASE_DIR / "EditorResources" / "Prop Dimensions.txt"
        self.loaded_prop_dimension = self.load_dimensions()   
                    
        self.output_prop_f = output_prop_f or self.filename
        
    def process_props(self, props: list):
        per_race_props = {'DEFAULT': []}  

        for prop in props:
            race_mode = prop.get('race_mode', 'DEFAULT')
            race_num = prop.get('race_num', '')
            
            race_key = f"{race_mode}_{race_num}" if race_mode != 'DEFAULT' else 'DEFAULT'
            per_race_props.setdefault(race_key, []).append(prop)

        current_filename = self.filename
        
        for race_key, race_props in per_race_props.items():
            self._reset_objects()  
            self.add_props(race_props)
            
            # Update the filename based on the race key
            current_filename = self._set_filename_suffix(race_key, current_filename)
            
            self.write_bangers(True, current_filename)

    def read_bangers(self, filename = None):
        if filename is None:
            filename = self.filename
            
        with open(filename, mode = "rb") as f:
            num_props = BinaryBanger.readn(f)
            for _ in range(num_props):
                prop_data = BinaryBanger.read(f)
                self.objects.append(prop_data)
                
    def write_bangers(self, set_props: bool, filename = None):
        target_filename = filename or self.filename

        if set_props:
            with open(target_filename, mode = "wb") as f:
                write_pack(f, '<I', len(self.objects))

                for idx, obj in enumerate(self.objects, 1):
                    if self.debug_props:
                        self.write_banger_debug(idx, obj)
            
                    write_pack(f, '<HH', 4, 0x800)  # Hardcoded Room and Flags values to ensure player's car can collide with props                  
                    obj.offset.write(f)		
                    obj.face.write(f)		
                    for char in obj.name:
                        write_pack(f, '<s', bytes(char, encoding = 'utf8'))

    def write_banger_debug(self, idx, obj):
        cleaned_prop_name = obj.name.rstrip('\x00')
        
        with open(self.debug_filename, "a") as debug_f:
            debug_f.write(textwrap.dedent(f'''
                Prop {idx}
                Room: {obj.room}
                Flags: {obj.flags}
                Offset: {obj.offset}
                Face: {obj.face}
                Name: {cleaned_prop_name}
            '''))
                      
    def add_props(self, new_props):    
        for prop in new_props:
            offset = Vector3(*prop['offset'])
            end = Vector3(*prop.get('end', prop['offset']))  
            face = prop.get('face')  
            name = prop['name']

            # Compute diagonal and its length
            diagonal = end - offset
            diagonal_length = diagonal.Mag()
            
            separator = prop.get('separator', 10.0)  # Use 10.0 as default separator
            if isinstance(separator, str) and separator.lower() in ["x", "y", "z"]:
                prop_dims = self.loaded_prop_dimension.get(name, Vector3(1, 1, 1))
                separator = getattr(prop_dims, separator.lower())
            elif not isinstance(separator, (int, float)):
                separator = 10.0

            if face is None:  # Create a facing vector that points from offset to end
                face = (Vector3(diagonal.x * 1e6, diagonal.y * 1e6, diagonal.z * 1e6))
            else:
                face = Vector3(*face)  # Transform the user-input face to a Vector3

            self.objects.append(BinaryBanger(4, 0x800, offset, face, name + "\x00"))

            # The number of props is determined by the length of the diagonal and separator
            num_props = int(diagonal_length / separator)

            # Add objects along the diagonal
            for i in range(1, num_props):
                # Compute new offset along the diagonal
                new_offset = offset + (diagonal.Normalize() * (i * separator))
                self.objects.append(BinaryBanger(4, 0x800, new_offset, face, name + "\x00"))
  
    def place_props_randomly(self, seed: int, num_props: int, props_dict: dict, x_range: float, z_range: float):
        new_objects = []

        # Ensure 'name' is a list for consistent handling later
        if isinstance(props_dict.get('name'), str):
            props_dict['name'] = [props_dict['name']]
            
        random.seed(seed)

        for name in props_dict['name']:
            for _ in range(num_props):
                x = random.uniform(*x_range)
                z = random.uniform(*z_range)
                y = props_dict.get('offset_y', 0.0)  

                new_prop_dict = {
                    'name': name,
                    'offset': (x, y, z)}
                
                if 'face' not in props_dict:  # If face is not defined, create random face vectors
                    face_x = random.uniform(-1e6, 1e6)
                    face_y = random.uniform(-1e6, 1e6)  # Not applicable
                    face_z = random.uniform(-1e6, 1e6)
                    new_prop_dict['face'] = (face_x, face_y, face_z)
                else:
                    new_prop_dict['face'] = props_dict['face']

                # Copy additional prop properties if they exist
                for key, value in props_dict.items():
                    if key not in new_prop_dict:
                        new_prop_dict[key] = value

                new_objects.append(new_prop_dict)
        
        return new_objects
    
    def append_props(self, new_objects, append_props):
        if not append_props:
            return
        
        if not self.objects:  
            self.read_bangers()
            
        original_count = len(self.objects)
        self.add_props(new_objects)

        new_count = len(self.objects)

        with open(self.filename, mode = "rb") as in_f:
            current_count = read_unpack(in_f, '<I')[0]
                    
            with open(self.output_prop_f, mode = "wb") as out_f:
                write_pack(out_f, '<I', current_count + new_count - original_count)
                out_f.write(in_f.read())
                self.write_bangers(set_props = True, filename = self.output_prop_f)    
                    
        if self.debug_props:
            for idx, obj in enumerate(self.objects[original_count:], original_count + 1):
                self.write_banger_debug(idx, obj)
                                        
    def _race_mode_to_short(self, race_mode: str) -> str:
        mode_mapping = {
            CIRCUIT: 'C',
            RACE: 'R',
            BLITZ: 'B'}
        return mode_mapping.get(race_mode, race_mode)
    
    def _reset_objects(self):
        self.objects.clear()

    def _set_filename_suffix(self, race_key, current_filename):        
        if race_key == 'DEFAULT':
            return current_filename

        race_parts = race_key.split('_')
        if len(race_parts) == 2:
            race_mode, race_num = race_parts
            short_race_mode = self._race_mode_to_short(race_mode)
            return current_filename.parent / f"{current_filename.stem}_{short_race_mode}{race_num}{current_filename.suffix}"
                                                                     
    def load_dimensions(self):
        extracted_prop_dim = {}
        
        with open(self.prop_dim_file, "r") as f:
            for line in f:
                prop_name, value_x, value_y, value_z = line.split()
                extracted_prop_dim[prop_name] = Vector3(float(value_x), float(value_y), float(value_z))
        return extracted_prop_dim

#################################################################################
#################################################################################

# MATERIALEDITOR CLASS
class MaterialEditor:
    def __init__(self, name: str, friction: float, elasticity: float, drag: float, 
                 bump_height: float, bump_width: float, bump_depth: float, sink_depth: float, 
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
    def readn(f, count):
        return [MaterialEditor.read(f) for _ in range(count)]

    @staticmethod
    def read(f):
        name = f.read(32).decode("latin-1").rstrip('\x00')
        params = read_unpack(f, '>7f2I')
        velocity = Vector2.read(f)
        ptx_color = Vector3.read(f)
        return MaterialEditor(name, *params, velocity, ptx_color)

    def write(self, f):        
        write_pack(f, '>32s', self.name.encode("latin-1").ljust(32, b'\x00'))
        write_pack(f, '>7f2I', 
                   self.friction, self.elasticity, self.drag, 
                   self.bump_height, self.bump_width, self.bump_depth, 
                   self.sink_depth, self.type, self.sound)
        self.velocity.write(f)
        self.ptx_color.write(f)

    @staticmethod
    def write_all(physics_db, physics_params):
        with open(physics_db, 'wb') as f:
            write_pack(f, '>I', len(physics_params))
            for param in physics_params:                
                param.write(f)
                
    @classmethod    
    def edit(cls, materials_properties, physics_output_f, debug_physics):
        physics_input_f = Path.cwd() / "EditorResources" / "PHYSICS.DB"
        
        with open(physics_input_f, 'rb') as f:
            count = read_unpack(f, '>I')[0]
            physics_data = cls.readn(f, count)
          
        # Loop through material properties dictionary
        for material_index, properties in materials_properties.items():
            for prop, value in properties.items():
                setattr(physics_data[material_index - 1], prop, value)
            
        cls.write_all(physics_output_f, physics_data)
        MOVE(physics_output_f, SHOP / "MTL" / physics_output_f)
        
        if debug_physics:
            cls.debug("PHYSICS_DB_debug.txt", physics_data)
            
    @classmethod
    def debug(cls, debug_filename, material_list):
        with open(debug_filename, 'w') as debug_f:
            for idx, material in enumerate(material_list):
                debug_f.write(material.__repr__(idx))
                debug_f.write("\n")

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

# BAI EDITOR CLASS
class BAI_Editor:
    def __init__(self, map_filename, streets, set_ai_map):
        self.map_filename = map_filename
        self.streets = streets
        self.output_dir = BASE_DIR / "dev" / "CITY" / self.map_filename
                
        if set_ai_map:
            self.write_map()

    def write_map(self):        
        self.output_dir.mkdir(parents = True, exist_ok = True)
        
        with open(self.output_dir / f"{self.map_filename}.map", 'w') as f:
            f.write(self.map_template())
    
    def map_template(self):
        streets_representation = '\n\t\t'.join(
            [f'"{street}"' for street in self.streets])

        map_data = f"""
mmMapData :0 {{
    NumStreets {len(self.streets)}
    Street [
        {streets_representation}
    ]
}}
        """
        return textwrap.dedent(map_data).strip()
       
       
# STREET CLASS
class StreetEditor:
    def __init__(self, map_filename, data, set_streets, set_reverse_streets):
        self.map_filename = map_filename
        self.street_name = data["street_name"]
        self.set_reverse_streets = set_reverse_streets
        self.process_lanes(data)
        self.set_properties(data)

        if set_streets:
            self.write()
                    
    @classmethod
    def create(cls, map_filename, dataset, set_ai_map, set_streets, set_reverse_streets):
        street_editors = [StreetEditor(map_filename, data, set_streets, set_reverse_streets) for data in dataset]
        street_names = [editor.street_name for editor in street_editors]
        return BAI_Editor(map_filename, street_names, set_ai_map)

    def process_lanes(self, data):
        if "lanes" in data:
            self.original_lanes = data["lanes"]
        elif "vertices" in data:
            self.original_lanes = {"lane_1": data["vertices"]}
        else:
            raise ValueError("Street data must have either 'lanes' or 'vertices'")

        # Add reverse lanes if set by the user
        self.lanes = self.original_lanes.copy()
        if self.set_reverse_streets:
            for key, values in self.original_lanes.items():
                self.lanes[key].extend(values[::-1])

    def set_properties(self, data):
        self.intersection_types = data.get("intersection_types", [CONTINUE, CONTINUE])
        self.stop_light_positions = data.get("stop_light_positions", [(0.0, 0.0, 0.0)] * 4)
        self.stop_light_names = data.get("stop_light_names", [STOP_LIGHT_SINGLE, STOP_LIGHT_SINGLE])
        self.traffic_blocked = data.get("traffic_blocked", [NO, NO])
        self.ped_blocked = data.get("ped_blocked", [NO, NO])
        self.road_divided = data.get("road_divided", NO)
        self.alley = data.get("alley", NO)

    def write(self):
        output_folder = BASE_DIR / "dev" / "CITY" / self.map_filename        
        output_folder.mkdir(parents = True, exist_ok = True)
    
        with open(output_folder / f"{self.street_name}.road", 'w') as f:
            f.write(self.set_template())

    def set_template(self):
        lane_one = list(self.lanes.keys())[0]  # Assuming all lanes have the same number of vertices
        num_vertices_per_lane = len(self.original_lanes[lane_one])
        num_total_vertices = num_vertices_per_lane * len(self.lanes) * (2 if self.set_reverse_streets else 1)
        
        vertices = '\n\t\t'.join('\n\t\t'.join(
            f'{vertex[0]} {vertex[1]} {vertex[2]}' for vertex in vertices) for vertices in self.lanes.values())
        
        normals = '\n\t\t'.join(
            '0.0 1.0 0.0' for _ in range(num_vertices_per_lane))
        
        stop_light_positions = '\n\t'.join(
            f"""StopLightPos[{i}] {pos[0]} {pos[1]} {pos[2]}"""
            for i, pos in enumerate(self.stop_light_positions))

        street_template = f"""
mmRoadSect :0 {{
    NumVertexs {num_vertices_per_lane}
    NumLanes[0] {len(self.lanes)}
    NumLanes[1] {len(self.lanes) if self.set_reverse_streets else 0}
    NumSidewalks[0] 0
    NumSidewalks[1] 0
    TotalVertexs {num_total_vertices}
    Vertexs [
        {vertices}
    ]
    Normals [
        {normals}
    ]
    IntersectionType[0] {self.intersection_types[0]}
    IntersectionType[1] {self.intersection_types[1]}
    {stop_light_positions}
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
    
################################################################################################################               
################################################################################################################    
        
def get_first_and_last_street_vertices(street_list, process_vertices = False):
    vertices_set = set()
    
    for street in street_list:
        vertices = street["vertices"]
        if vertices:  # Check if the list is not empty
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


def create_lars_race_maker(map_filename: str, street_list, lars_race_maker: bool, process_vertices: bool = True):
    #!########### Code by Lars (Modified) ############    
    vertices_processed = get_first_and_last_street_vertices(street_list, process_vertices)
    
    polygons = hudmap_vertices
    min_x, max_x, min_z, max_z = create_ext(map_filename, polygons)
    
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

<img id = "scream" width = "{canvas_width}" height = {canvas_height} src = "{map_filename}_HUD_debug.jpg" alt = "The Scream" style = "display:none;">

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
        with open("Lars_Race_Maker.html", "w") as f:
            f.write(new_html_content)

    return new_html_content

#!########### Code by Lars (Modified) ############   

###################################################################################################################
################################################################################################################### 

# FACADE CLASS
class Facade_Editor:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, sides: Vector3, scale: float, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.sides = sides
        self.scale = scale
        self.name = name

    @classmethod
    def read(cls, f):
        room, flags = read_unpack(f, '2H')
        offset = Vector3.read(f)
        face = Vector3.read(f)
        sides = Vector3.read(f)
        scale = read_unpack(f, 'f')[0]
        name = cls.read_name(f)
        return cls(room, flags, offset, face, sides, scale, name)
    
    @staticmethod
    def read_name(f):
        name_data = bytearray()
        while True:
            char = f.read(1)
            if char == b'\x00':
                break
            name_data.extend(char)
        return name_data.decode('utf-8')
    
    @staticmethod
    def read_scales(scales_file):
        scales = {}
        with open(scales_file, 'r') as f:
            for line in f:
                name, scale = line.strip().split(": ")
                scales[name] = float(scale)
        return scales

    def write(self, f):
        write_pack(f, '2H', 0x1, self.flags)  # Hardcoded the Room value such that all facades are visible in the game       
        write_pack(f, '3f', *self.offset)
        write_pack(f, '3f', *self.face)
        write_pack(f, '3f', *self.sides)
        write_pack(f, 'f', self.scale)
        f.write(self.name.encode('utf-8'))
        f.write(b'\x00')
                
    @classmethod
    def create(cls, filename, packed_facades, output_dir, set_facades = False, debug_facades = False):
        if set_facades:
            facades = cls.build(packed_facades)
            cls.finalize(filename, facades)
            MOVE(filename, output_dir / filename)

            if debug_facades:
                cls.debug(facades)

    @classmethod
    def build(cls, packed_facades):
        facades = []
        axis_dict = {'x': 0, 'y': 1, 'z': 2}
        scales = cls.read_scales(BASE_DIR / "EditorResources" / 'FCD scales.txt')

        for params in packed_facades:
            axis = axis_dict[params['axis']]
            start_coord = params['offset'][axis]
            end_coord = params['end'][axis]
            
            direction = 1 if start_coord < end_coord else -1
            
            num_facades = math.ceil(abs(end_coord - start_coord) / params['separator'])

            for i in range(num_facades):
                flags = params['flags']
                
                current_start, current_end = cls.calculate_start_end(params, axis, direction, start_coord, i)
                
                sides = params.get('sides', (0.0, 0.0, 0.0))
                scale = scales.get(params['name'], params.get('scale', 1.0))
                name = params['name']

                facade = Facade_Editor(0x1, flags, current_start, current_end, sides, scale, name)
                facades.append(facade)

        return facades

    @staticmethod
    def calculate_start_end(params, axis, direction, start_coord, i):
        current_start = list(params['offset'])
        current_end = list(params['end'])
        
        shift = direction * params['separator'] * i
        
        current_start[axis] = start_coord + shift
        end_coord = params['end'][axis]
        
        if direction == 1:
            current_end[axis] = min(start_coord + shift + params['separator'], end_coord)
        else:
            current_end[axis] = max(start_coord + shift - params['separator'], end_coord)
            
        return tuple(current_start), tuple(current_end)

    @staticmethod
    def finalize(filename, facades):
        with open(filename, mode = 'wb') as f:
            write_pack(f, '<I', len(facades))
            for facade in facades:
                facade.write(f)

    @staticmethod
    def debug(facades):
        with open("FACADES_debug.txt", mode = 'w', encoding = 'utf-8') as f:
            for facade in facades:
                f.write(str(facade))
        
    def __repr__(self):
        return f"""
Facade Editor
    Room: {self.room}
    Flags: {self.flags}
    Start: {self.offset}
    Face: {self.face}
    Sides: {self.sides}
    Scale: {self.scale}
    Name: {self.name}
    """
    
###################################################################################################################
###################################################################################################################
    
class LightingEditor:
    def __init__(self, time_of_day: int, weather: int, 
                 sun_heading: float, sun_pitch: float, sun_color: Tuple[float, float, float], 
                 fill1_heading: float, fill1_pitch: float, fill1_color: Tuple[float, float, float], 
                 fill2_heading: float, fill2_pitch: float, fill2_color: Tuple[float, float, float], 
                 ambient_color: Tuple[float, float, float],  
                 fog_end: float, fog_color: Tuple[float, float, float], 
                 shadow_alpha: float, shadow_color: Tuple[float, float, float]):
        
        self.time_of_day = time_of_day
        self.weather = weather
        self.sun_heading = sun_heading
        self.sun_pitch = sun_pitch
        self.sun_color = sun_color
        self.fill1_heading = fill1_heading
        self.fill1_pitch = fill1_pitch
        self.fill1_color = fill1_color
        self.fill2_heading = fill2_heading
        self.fill2_pitch = fill2_pitch
        self.fill2_color = fill2_color
        self.ambient_color = ambient_color
        self.fog_end = fog_end
        self.fog_color = fog_color
        self.shadow_alpha = shadow_alpha
        self.shadow_color = shadow_color
        
    @classmethod
    def read_rows(cls, row):
        return cls(
            time_of_day = int(row[0]),
            weather = int(row[1]),
            sun_heading = float(row[2]),
            sun_pitch = float(row[3]),
            sun_color = (float(row[4]), float(row[5]), float(row[6])),
            fill1_heading = float(row[7]),
            fill1_pitch = float(row[8]),
            fill1_color = (float(row[9]), float(row[10]), float(row[11])),
            fill2_heading = float(row[12]),
            fill2_pitch = float(row[13]),
            fill2_color = (float(row[14]), float(row[15]), float(row[16])),
            ambient_color = (float(row[17]), float(row[18]), float(row[19])),
            fog_end = float(row[20]),
            fog_color = (float(row[21]), float(row[22]), float(row[23])),
            shadow_alpha = float(row[24]),
            shadow_color = (float(row[25]), float(row[26]), float(row[27]))
        )
    
    @classmethod
    def read_file(cls, filename: Path):
        instances = []
        with open(filename, newline = '') as f:
            reader = csv.reader(f)
            next(reader)  
            for data in reader:
                instance = cls.read_rows(data)
                instances.append(instance)
        return instances
        
    def apply_changes(self, changes):
        for attribute, new_value in changes.items():
            if hasattr(self, attribute):
                current_value = getattr(self, attribute)
                if isinstance(current_value, tuple) and isinstance(new_value, tuple):
                    # Update only the specified components for tuple attributes
                    updated_value = tuple(new_value[i] if i < len(new_value) else current_value[i] for i in range(len(current_value)))
                    setattr(self, attribute, updated_value)
                else:
                    setattr(self, attribute, new_value)
            
    @staticmethod
    def process_changes(instances, config_list):
        for config in config_list:
            for instance in instances:
                if instance.time_of_day == config['time_of_day'] and instance.weather == config['weather']:
                    instance.apply_changes(config)
        return instances
                
    def write_rows(self):
        def format_value(value):
            return int(value) if isinstance(value, float) and value.is_integer() else value

        return [
            format_value(self.time_of_day),
            format_value(self.weather),
            format_value(self.sun_heading),
            format_value(self.sun_pitch),
            *map(format_value, self.sun_color),
            format_value(self.fill1_heading),
            format_value(self.fill1_pitch),
            *map(format_value, self.fill1_color),
            format_value(self.fill2_heading),
            format_value(self.fill2_pitch),
            *map(format_value, self.fill2_color),
            *map(format_value, self.ambient_color),
            format_value(self.fog_end),
            *map(format_value, self.fog_color),
            format_value(self.shadow_alpha),
            *map(format_value, self.shadow_color)
        ]
        
    @classmethod
    def write_file(cls, instances, filename: Path):
        with open(filename, mode = 'w', newline = '') as f:
            writer = csv.writer(f)
        
            header = ['TimeOfDay', ' Weather', ' Sun Heading', ' Sun Pitch', ' Sun Red', ' Sun Green', ' Sun Blue',
                    ' Fill-1 Heading', ' Fill-1 Pitch', ' Fill-1 Red', ' Fill-1 Green', ' Fill-1 Blue',
                    ' Fill-2 Heading', ' Fill-2 Pitch', ' Fill-2 Red', ' Fill-2 Green', ' Fill-2 Blue',
                    ' Ambient Red', ' Ambient Green', ' Ambient Blue', 
                    ' Fog End', ' Fog Red', ' Fog Green', ' Fog Blue', 
                    ' Shadow Alpha', ' Shadow Red', ' Shadow Green', ' Shadow Blue']

            writer.writerow(header)
            for instance in instances:
                writer.writerow(instance.write_rows())
                
    @classmethod
    def debug(cls, instances, filename):
        with open(filename, 'w') as f:
            for instance in instances:
                f.write(instance.__repr__())
                f.write("\n")
                
    def __repr__(self):
        return f'''
LightingEditor
Time of Day: {self.time_of_day}
Weather: {self.weather}
Sun Heading: {self.sun_heading:.2f}
Sun Pitch: {self.sun_pitch:.2f}
Sun Color: {self.sun_color}
Fill1 Heading: {self.fill1_heading:.2f}
Fill1 Pitch: {self.fill1_pitch:.2f}
Fill1 Color: {self.fill1_color}
Fill2 Heading: {self.fill2_heading:.2f}
Fill2 Pitch: {self.fill2_pitch:.2f}
Fill2 Color: {self.fill2_color}
Ambient Color: {self.ambient_color}
Fog End: {self.fog_end:.2f}
Fog Color: {self.fog_color}
Shadow Alpha: {self.shadow_alpha:.2f}
Shadow Color: {self.shadow_color}
'''

###################################################################################################################
###################################################################################################################  

def create_ar(map_filename: str) -> None:
    for file in Path("angel").iterdir():
        if file.name in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(file, SHOP / file.name)

    os.chdir(SHOP)
    ar_command = f"run !!!!!{map_filename}"

    subprocess.Popen(f"cmd.exe /c {ar_command}", creationflags = subprocess.CREATE_NO_WINDOW)


def post_ar_cleanup(delete_shop: bool) -> None:
    if delete_shop:
        build_dir = BASE_DIR / 'build'
        shop_dir = BASE_DIR / 'SHOP'

        os.chdir(BASE_DIR)
        
        time.sleep(1)  # Make sure the SHOP folder is no longer in use (i.e. an .ar file is still being created)
        
        try:  
            shutil.rmtree(build_dir)
        except Exception as e:
            print(f"Failed to delete the BUILD directory. Reason: {e}")
        
        try:
            shutil.rmtree(shop_dir)
        except Exception as e:
            print(f"Failed to delete the SHOP directory. Reason: {e}")

   
def create_commandline(
    map_filename: str, mm1_folder: Path, no_ui: bool, no_ui_type: str, 
    no_ai: bool, quiet_logs: bool, more_logs: bool) -> None:
    
    map_filename = map_filename.lower()
    cmd_file = "commandline.txt"
    
    base_cmd = f"-path ./dev -allrace -allcars -f -heapsize 499 -multiheap -maxcops 100 -mousemode 1 -speedycops -l {map_filename}"
    
    if quiet_logs and more_logs:    
        log_error_message = f"""\n
        ***ERROR***
        You can't have both 'quiet' and 'more logs' enabled. Please choose one."
        """
        raise ValueError(log_error_message)
    
    if quiet_logs:
        base_cmd += " -quiet"
        
    if more_logs:
        base_cmd += " -logopen -agiVerbose -console"
    
    if no_ai:
        base_cmd += " -noai"
    
    if no_ui:
        if not no_ui_type or no_ui_type.lower() == "cruise":
            base_cmd += f" -noui -keyboard"
        else:
            race_type, race_index = no_ui_type.split()
            if race_type not in ["circuit", "race", "blitz"]:
                type_error_message = f"""\n
                ***ERROR***
                Invalid Race Type provided. Available types are {BLITZ}, {RACE}, and {CIRCUIT}.
                """
                raise ValueError(type_error_message)
                                            
            if not 0 <= int(race_index) <= 14:
                index_error_message = """\n
                ***ERROR***
                Invalid Race Index provided. It should be between 0 and 14.
                """
                raise ValueError(index_error_message)
            
            base_cmd += f" -noui -{race_type} {race_index} -keyboard"
    
    processed_cmd = base_cmd
    
    with open(mm1_folder / cmd_file, "w") as f:
        f.write(processed_cmd)
        
        
# Start game
def start_game(mm1_folder: str, play_game: bool) -> None:
    if play_game and not is_blender_running():
        subprocess.run(mm1_folder / "Open1560.exe", cwd = mm1_folder)
        
###################################################################################################################
################################################################################################################### 

#! ================== THIS SECTION IS RELATED TO BLENDER SETUP / PRELOADING ================== !#

def enable_developer_extras() -> None:
    prefs = bpy.context.preferences
    view = prefs.view
    
    # Set "Developer Extra's" if not already enabled
    if not view.show_developer_ui:
        view.show_developer_ui = True
        bpy.ops.wm.save_userpref()
        print("Developer Extras enabled!")
    else:
        print("Developer Extras already enabled!")
        
           
def adjust_3D_view_settings() -> None:
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

              
def load_dds_resources(texture_dir: Path, load_tex_materials: bool) -> None:
    for file_name in os.listdir(texture_dir):
        if file_name.lower().endswith(".dds"):
            texture_path = os.path.join(texture_dir, file_name)

            if texture_path not in bpy.data.images:
                texture_image = bpy.data.images.load(texture_path)
            else:
                texture_image = bpy.data.images[texture_path]

            if load_tex_materials:
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
    
###################################################################################################################
###################################################################################################################

#! ================== THIS SECTION IS RELATED TO BLENDER UV MAPPING ================== !#

def unwrap_uv_to_aspect_ratio(obj, image):
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
    
    
# UV MAPPING OPERATOR
class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            
            # Check if the object has the necessary custom properties
            if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "angle_degrees"]):
                tile_x = obj["tile_x"]
                tile_y = obj["tile_y"]
                rotate_angle = obj["angle_degrees"]

                # Update the UV mapping of the object based on its custom properties
                tile_uvs(obj, tile_x, tile_y)
                rotate_uvs(obj, rotate_angle)

        return {"FINISHED"}
    
###################################################################################################################
###################################################################################################################

#! ================== THIS SECTION IS RELATED TO CREATING BLENDER POLYGONS ================== !#

def apply_texture_to_object(obj, texture_path):
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

    unwrap_uv_to_aspect_ratio(obj, texture_image)
    
    
def create_mesh_from_polygon_data(polygon_data, texture_dir = None):
    name = f"P{polygon_data['bound_number']}"
    coords = polygon_data["vertex_coordinates"]

    edges = []
    faces = [range(len(coords))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    obj["cell_type"] = str(polygon_data["cell_type"])
    obj["material_index"] = str(polygon_data["material_index"])
        
    set_hud_checkbox(polygon_data["hud_color"], obj)
    
    for coord in coords:
        vertex_item = obj.vertex_coords.add()
        vertex_item.x, vertex_item.y, vertex_item.z = coord
    
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
        obj.rotate = texcoords_data['entries'][bound_number].get('angle_degrees', 5)
        
    obj.tile_x = tile_x
    obj.tile_y = tile_y
    
    if texture_dir:
        apply_texture_to_object(obj, texture_dir)    
        rotate_angle = obj.rotate

        tile_uvs(obj, tile_x, tile_y)
        rotate_uvs(obj, rotate_angle)  
        
        obj.data.update()
        
    # Rotate the created Blender model to match the game's coordinate system
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.transform.rotate(value = math.radians(-90), orient_axis = 'X')
    
    return obj


def create_blender_meshes() -> None:
    if is_blender_running():
        enable_developer_extras()
        adjust_3D_view_settings()
        
        load_dds_resources(texture_dir, load_tex_materials)
                    
        texture_paths = [os.path.join(texture_dir, f"{texture_name}.DDS") for texture_name in stored_texture_names]

        bpy.ops.object.select_all(action = 'SELECT')
        bpy.ops.object.delete()

        for polygon, texture_path in zip(polygons_data, texture_paths):
            create_mesh_from_polygon_data(polygon, texture_path)

###################################################################################################################
###################################################################################################################

#! ================== THIS SECTION IS RELATED TO BLENDER PANELS ================== !#

# CELL PANEL
CELL_IMPORT = [
    (str(DEFAULT), "Default", "", "", DEFAULT),
    (str(TUNNEL), "Tunnel", "", "", TUNNEL),
    (str(INDOORS), "Indoors", "", "", INDOORS),
    (str(WATER_DRIFT), "Water Drift", "", "", WATER_DRIFT),
    (str(NO_SKIDS), "No Skids", "", "", NO_SKIDS)]

bpy.types.Object.cell_type = bpy.props.EnumProperty(
    items = CELL_IMPORT,
    name = "Cell Type",
    description = "Select the type of cell")

CELL_EXPORT = {
    # We do not want to export the Default Cell Type
    str(TUNNEL): "TUNNEL",
    str(INDOORS): "INDOORS",
    str(WATER_DRIFT): "WATER_DRIFT",
    str(NO_SKIDS): "NO_SKIDS"}

class OBJECT_PT_CellTypePanel(bpy.types.Panel):
    bl_label = "Cell Type"
    bl_idname = "OBJECT_PT_cell_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj:
            layout.prop(obj, "cell_type", text = "Cell Type")
        else:
            layout.label(text = "No active object")
            

# MATERIAL PANEL
MATERIAL_IMPORT = [
    (str(DEFAULT_MTL), "Road", "", "", DEFAULT_MTL),
    (str(GRASS_MTL), "Grass", "", "", GRASS_MTL),
    (str(WATER_MTL), "Water", "", "", WATER_MTL),
    (str(STICKY_MTL), "Sticky", "", "", STICKY_MTL),
    (str(NO_FRICTION_MTL), "No Friction", "", "", NO_FRICTION_MTL)]

bpy.types.Object.material_index = bpy.props.EnumProperty(
    items = MATERIAL_IMPORT,
    name = "Material Type",
    description = "Select the type of material")

MATERIAL_EXPORT = {
    # We do not want to export the Default Material Type
    str(GRASS_MTL): "GRASS_MTL",
    str(WATER_MTL): "WATER_MTL",
    str(STICKY_MTL): "STICKY_MTL",
    str(NO_FRICTION_MTL): "NO_FRICTION_MTL"}

class OBJECT_PT_MaterialTypePanel(bpy.types.Panel):
    bl_label = "Material Type"
    bl_idname = "OBJECT_PT_material_index"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj:
            layout.prop(obj, "material_index", text = "Material")
        else:
            layout.label(text = "No active object")


# HUD PANEL
HUD_IMPORT = [
    (ROAD_HUD, "Road", "", "", 1),
    (GRASS_HUD, "Grass", "", "", 2),
    (WATER_HUD, "Water", "", "", 3),
    (SNOW_HUD, "Snow", "", "", 4),
    (WOOD_HUD, "Wood", "", "", 5),
    (ORANGE, "Orange", "", "", 6),
    (LIGHT_RED, "Light Red", "", "", 7),
    (DARK_RED, "Dark Red", "", "", 8),
    (LIGHT_YELLOW, "Light Yellow", "", "", 9)]

def set_hud_checkbox(color, obj):
    for i, (color_value, _, _, _, _) in enumerate(HUD_IMPORT):
        if color_value == color:
            obj.hud_colors[i] = True
            break

bpy.types.Object.hud_colors = bpy.props.BoolVectorProperty(
    name = "HUD Colors",
    description = "Select the color of the HUD",
    size = 9, 
    default = (False, False, False, False, False, False, False, False, False))

HUD_EXPORT = {
    '#7b5931': "WOOD_HUD",
    '#cdcecd': "SNOW_HUD",
    '#5d8096': "WATER_HUD",
    # '#414441': "ROAD_HUD",
    '#396d18': "GRASS_HUD",
    '#af0000': "DARK_RED",
    '#ffa500': "ORANGE",
    '#ff7f7f': "LIGHT_RED",
    '#ffffe0': "LIGHT_YELLOW"}

class OBJECT_PT_HUDColorPanel(bpy.types.Panel):
    bl_label = "HUD Type"
    bl_idname = "OBJECT_PT_hud_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj:
            row = layout.row(align = True)
            col = row.column(align = True)
            half_length = len(HUD_IMPORT) // 2 + len(HUD_IMPORT) % 2
            
            for i, (_, name, _, _, _) in enumerate(HUD_IMPORT):
                if i == half_length:
                    col = row.column(align = True)
                
                col.prop(obj, "hud_colors", index = i, text = name, toggle = True)
        else:
            layout.label(text = "No active object")

        
# MISC PANEL
bpy.types.Object.always_visible = bpy.props.BoolProperty(
    name = "Always Visible",
    description = "If true, the polygon is always visible",
    default = False)

bpy.types.Object.sort_vertices = bpy.props.BoolProperty(
    name = "Sort Vertices",
    description = "If true, sort the vertices",
    default = False)

class OBJECT_PT_PolygonMiscOptionsPanel(bpy.types.Panel):
    bl_label = "Polygon Options"
    bl_idname = "OBJECT_PT_polygon_options"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj:
            layout.prop(obj, "always_visible", text = "Always Visible")
            layout.prop(obj, "sort_vertices", text = "Sort Vertices")
        else:
            layout.label(text = "No active object")
            
            
# VERTEX COORDINATES PANEL
def update_vertex_coordinates(self, context):
    obj = self.id_data
    if obj and hasattr(obj.data, "vertices"):
        for i, coord in enumerate(obj.vertex_coords):
            if len(obj.data.vertices) > i:
                obj.data.vertices[i].co = (coord.x, coord.y, coord.z)
        obj.data.update()

class VertexGroup(bpy.types.PropertyGroup):
    x: bpy.props.FloatProperty(name = "X", update = update_vertex_coordinates)
    y: bpy.props.FloatProperty(name = "Y", update = update_vertex_coordinates)
    z: bpy.props.FloatProperty(name = "Z", update = update_vertex_coordinates)
    
bpy.utils.register_class(VertexGroup)

bpy.types.Object.vertex_coords = bpy.props.CollectionProperty(type = VertexGroup)

class OBJECT_PT_VertexCoordinates(bpy.types.Panel):
    bl_label = "Vertices"
    bl_idname = "OBJECT_PT_vertex_coordinates"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        if obj:
            for vertex in obj.vertex_coords:
                col = layout.column(align = True)
                col.prop(vertex, "x")
                col.prop(vertex, "y")
                col.prop(vertex, "z")
        else:
            layout.label(text = "No active object")
            
###################################################################################################################
################################################################################################################### 

#! ================== THIS SECTION IS RELATED TO BLENDER EXPORTING ================== !#

def format_decimal(value):
    if value == int(value): 
        return f"{value:.1f}"
    else: 
        return f"{value:.2f}"
    
    
def get_editor_script_path():
    try:
        return Path(__file__).parent
    except NameError:
        print("Warning: Unable to return editor script path.")
        return None

    
def extract_polygon_data(obj):
    if obj.name.startswith("P"):
        bound_number = int(obj.name[1:])
    elif obj.name.startswith("Shape_"):
        bound_number = int(obj.name.split("_")[1])
    else:
        raise ValueError(f"Unrecognized object name format: {obj.name}")
    
    extracted_polygon_data = {
        "bound_number": bound_number,
        "material_index": obj["material_index"],
        "cell_type": obj["cell_type"],
        "always_visible": obj["always_visible"], 
        "sort_vertices": obj["sort_vertices"],
        "vertex_coordinates": obj.data.vertices,
        "hud_color": obj["hud_color"],
        "rotate": obj["rotate"]}
    
    return extracted_polygon_data


def extract_texture_from_polygon(obj):
    if obj.material_slots:
        mat = obj.material_slots[0].material
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    return os.path.splitext(node.image.name)[0].replace('.DDS', '').replace('.dds', '')
    return "CHECK04"  # If no texture is applied to the polygon, use CHECK04 as a placeholder
    

def export_blender_polygon_data(obj) -> str:
    data = extract_polygon_data(obj)
    texture_name = extract_texture_from_polygon(obj)
    vertex_export = ',\n\t\t'.join(['(' + ', '.join(format_decimal(comp) for comp in vert.co) + ')' for vert in data['vertex_coordinates']])

    optional_variables = []
    
    cell_type = CELL_EXPORT.get(str(data['cell_type']), None)
    if cell_type:
        optional_variables.append(f"cell_type = {cell_type}")
    
    material_index = MATERIAL_EXPORT.get(str(data['material_index']), None)
    if material_index:
        optional_variables.append(f"material_index = {material_index}")

    hud_color = HUD_EXPORT.get(next((HUD_IMPORT[i][0] for i, checked in enumerate(obj.hud_colors) if checked), None), None)
    if hud_color:
        optional_variables.append(f"hud_color = {hud_color}")

    if data['sort_vertices']:
        optional_variables.append("sort_vertices = True")
    if not data['always_visible']:
        optional_variables.append("always_visible = False")
        
    # Combining optional variables
    optional_variables_str = ",\n\t".join(optional_variables)
    if optional_variables_str:
        optional_variables_str = "\n\t" + optional_variables_str + ","

    tile_x = obj.get("tile_x", 1)
    tile_y = obj.get("tile_y", 1)
    rotate = data.get('rotate', 999.0)  

    polygon_export = f"""
create_polygon(
    bound_number = {data['bound_number']},{optional_variables_str}
    vertex_coordinates = [
        {vertex_export}])

save_bms(
    texture_name = ["{texture_name}"],
    tex_coords = compute_uv(bound_number = {data['bound_number']}, tile_x = {tile_x}, tile_y = {tile_y}, angle_degrees = {rotate}))"""

    return polygon_export


# EXPORT POLYGONS OPERATOR
class OBJECT_OT_ExportPolygons(bpy.types.Operator):
    bl_idname = "object.export_polygons"
    bl_label = "Export Blender Polygons"
    
    select_all: bpy.props.BoolProperty(default = True)

    def execute(self, context):
        script_path = get_editor_script_path()
        if script_path:
            output_folder = script_path / 'Blender Export'
        else:
            print("Warning: Falling back to directory: Desktop / Blender Export")
            # Path.cwd() "incorrectly" returns the user's desktop directory 
            output_folder = Path.cwd() / 'Blender Export'
        
        if not output_folder.exists():
            os.mkdir(output_folder)
        
        base_file_name = "Map_Editor_Blender_Export.txt"
        export_file = output_folder / base_file_name
        
        count = 1
        while os.path.exists(export_file):
            export_file = output_folder / f"{count}_{base_file_name}"
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
                    export_script = export_blender_polygon_data(obj) 
                    file.write(export_script + '\n\n')
                    
            subprocess.Popen(["notepad.exe", export_file])
            self.report({'INFO'}, f"Saved data to {export_file}")
            bpy.ops.object.select_all(action = 'DESELECT')
            
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
###################################################################################################################   
###################################################################################################################    
    
#! ================== THIS SECTION IS RELATED TO MISC BLENDER FUNCTIONS / CLASSES ================== !#

# CLASS ASSIGN CUSTOM PROPERTIES
class OBJECT_OT_AssignCustomProperties(bpy.types.Operator):
    bl_idname = "object.assign_custom_properties"
    bl_label = "Assign Custom Properties to Polygons"
    bl_description = "Assign Custom Properties to polygons that do not have them yet"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                
                # Cell & Material & HUD Color
                if "cell_type" not in obj:
                    obj["cell_type"] = 0
                if "material_index" not in obj:
                    obj["material_index"] = 0
                if "hud_color" not in obj:
                    obj["hud_color"] = ROAD_HUD
                    
                # Misc
                if "sort_vertices" not in obj:
                    obj["sort_vertices"] = 0
                if "always_visible" not in obj:
                    obj["always_visible"] = 1
                                
                # UV mapping
                if "tile_x" not in obj:
                    obj["tile_x"] = 2.0
                if "tile_y" not in obj:
                    obj["tile_y"] = 2.0
                if "rotate" not in obj:
                    obj["rotate"] = 0.01
                
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
    
    
def is_blender_running() -> bool:
    try:
        import bpy
        # Trying to access a bpy.context attribute to see if we get an exception
        _ = bpy.context.window_manager
        return True
    except (AttributeError, ImportError):
        return False
  
  
def set_blender_keybinding() -> None:
    if is_blender_running():
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = wm.keyconfigs.addon.keymaps.new(name = 'Object Mode', space_type = 'EMPTY')
            
            # Shift + E to export all polygons
            kmi_export_all = km.keymap_items.new("object.export_polygons", 'E', 'PRESS', shift = True)
            kmi_export_all.properties.select_all = True
            
            # Ctrl + E to export selected polygons
            kmi_export_selected = km.keymap_items.new("object.export_polygons", 'E', 'PRESS', ctrl = True)
            kmi_export_selected.properties.select_all = False
            
            # Shift + P to assign custom properties
            kmi_assign_properties = km.keymap_items.new("object.assign_custom_properties", 'P', 'PRESS', shift = True)

###################################################################################################################   
################################################################################################################### 

#* FACADE NOTES
#* Separator: (max_x - min_x) / separator(value) = number of facades
#* Sides --> omitted by default, but can be set (relates to lighting, but behavior is not clear)
#* Scale --> enlarges or shrinks non-fixed facades
#* Name --> name of the facade in the game files

#* All relevant Facade information can be found in: /UserResources/FACADES.
#* Each facade is photographed and documented (see: "FACADE_DATA.txt")

# Flags (if applicable, consult the documentation for more info)
FRONT = 1  # Sometimes 1 is also used for the full model
FRONT_BRIGHT = 3

FRONT_LEFT = 9
FRONT_BACK = 25
FRONT_ROOFTOP = 33
FRONT_LEFT = 41  # Value 73 is also commonly used for this
FRONT_RIGHT = 49

FRONT_LEFT_ROOF = 105 
FRONT_RIGHT_ROOF = 145  # Value 177 is also commonly used for this
FRONT_LEFT_RIGHT = 217
FRONT_LEFT_RIGHT_ROOF = 249

FRONT_BACK_ROOF = 1057
FRONT_RIGHT_BACK = 1073
FRONT_LEFT_ROOF_BACK = 1129
FRONT_RIGHT_ROOF_BACK = 1201
ALL_SIDES = 1273

# Facade names (feel free to add more)
ORANGE_W_WINDOWS = "ofbldg02"  
WALL_FREEWAY = "freewaywall02"
SUIT_STORE = "dfsuitstore"
PIZZA_PLACE = "hfpizza"   
RAIL_WATER = "t_rail01"  

orange_building_1 = {
	'flags': FRONT_BRIGHT,
	'offset': (-10.0, 0.0, -50.0),
	'end': (10, 0.0, -50.0),
	'separator': 10.0,
	'name': ORANGE_W_WINDOWS,
	'axis': 'x'}

orange_building_2 = {
	'flags': FRONT_BRIGHT,
	'offset': (10.0, 0.0, -70.0),
	'end': (-10, 0.0, -70.0),
	'separator': 10.0,
	'name': ORANGE_W_WINDOWS,
	'axis': 'x'}

orange_building_3 = {
	'flags': FRONT_BRIGHT,
	'offset': (-10.0, 0.0, -70.0),
	'end': (-10.0, 0.0, -50.0),
	'separator': 10.0,
	'name': ORANGE_W_WINDOWS,
	'axis': 'z'}

orange_building_4 = {
	'flags': FRONT_BRIGHT,
	'offset': (10.0, 0.0, -50.0),
	'end': (10.0, 0.0, -70.0),
	'name': ORANGE_W_WINDOWS,
    'axis': 'z',
    'separator': 10.0}

white_hotel_highway = {
    'flags': FRONT_BRIGHT,
	'offset': (-160.0, 0.0, -80.0),
	'end': (-160.0, 0.0, 20.0),
	'separator': 25.0, 
	'name': "rfbldg05",
	'axis': 'z'}

red_hotel_highway = {
    'flags': FRONT_BRIGHT,
	'offset': (-160.0, 0.0, 40.0),
	'end': (-160.0, 0.0, 140.0),
	'separator': 20.0, 
	'name': "dfbldg06",
	'axis': 'z'}

# Pack all Facades for processing
fcd_list = [
    orange_building_1, orange_building_2, orange_building_3, orange_building_4, 
    white_hotel_highway, red_hotel_highway]

###################################################################################################################   
###################################################################################################################

# SET AI PATHS

f"""
# The following variables are OPTIONAL: 

# Intersection_types, defaults to: {CONTINUE}
(possbile types: {STOP}, {STOP_LIGHT}, {YIELD}, {CONTINUE}

# Stop_light_names, defaults to: {STOP_LIGHT_SINGLE}
(possbile names: {STOP_SIGN}, {STOP_LIGHT_SINGLE}, {STOP_LIGHT_DUAL}

# Stop_light_positions, defaults to: {(0, 0, 0)}
# Traffic_blocked, Ped_blocked, Road_divided, and Alley, all default to: {NO}
(possbile values: {YES}, {NO}

Note:
# Stop lights will only show if the Intersection_type is {STOP_LIGHT}
"""

#! Do not delete this Street
cruise_start = {
    "street_name": "cruise_start",
    "vertices": [
        (0,0,0),            # keep this
        cruise_start_pos]}  # starting position in Cruise mode

main_west = {
     "street_name": "main_west",
     "vertices": [
         (0.0, 0.0, 77.5),
         (0.0, 0.0, 70.0),
         (0.0, 0.0, 10.0),
         (0.0, 0.0, 0.0),
         (0.0, 0.0, -10.0),
         (0.0, 0.0, -70.0),
         (0.0, 0.0, -70.0),
         (0.0, 0.0, -100.0)]}

main_grass_horz = {
     "street_name": "main_grass_horz",
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

main_barricade_wood = {
     "street_name": "barricade_wood",
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

double_triangle = {
    "street_name": "double_triangle",
    "vertices": [
        (40.0, 0.0, 100.0),
        (-50.0, 0.0, 135.0),
        (-59.88, 3.04, 125.52),
        (-84.62, 7.67, 103.28),
        (-89.69, 8.62, 62.57),
        (-61.94, 3.42, 32.00),
        (-20, 0.0, 70.0),
        (0.0, 0.0, 77.5)]}

orange_hill = {
    "street_name": "orange_hill",
    "vertices": [
        (0.0, 245.0, -850.0),
        (0.0, 0.0, -210.0),
        (0.0, 0.0, -155.0),
        (0.0, 0.0, -100.0)]}

# Street examples with multiple lanes and all optional settings
street_example = {
    "street_name": "example",
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
        "lane_3": [  # Add more lanes if desired
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

# Pack all AI streets for processing
street_list = [cruise_start, 
               main_west, main_grass_horz, main_barricade_wood, double_triangle, 
               orange_hill]

###################################################################################################################   
###################################################################################################################               

# ADD PROPS
china_gate = {'offset': (0, 0.0, -20), 
              'face': (1 * HUGE, 0.0, -20), 
              'name': CHINATOWN_GATE,
              'race_mode': CIRCUIT,
              'race_num': 0}

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
random_props = [
    {"seed": 123, "num_props": 1, "props_dict": random_trees, "x_range": (65, 135), "z_range": (-65, 65)},
    {"seed": 99, "num_props": 1, "props_dict": random_sailboats, "x_range": (55, 135), "z_range": (-145, -205)},
    {"seed": 1, "num_props": 2, "props_dict": random_cars, "x_range": (52, 138), "z_range": (-136, -68)}]

# APPEND PROPS
app_panoz_gtr = {
    'offset': (5, 2, 5),
    'end': (999, 2, 999),
    'name': PANOZ_GTR1}

appended_props = [app_panoz_gtr]


# AudioIDs
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

###################################################################################################################   
###################################################################################################################   

lighting_configs = [
    {
        # Actual lighting data for Evening and Cloudy
        'time_of_day': EVENING,
        'weather': CLOUDY,
        'sun_heading': 3.14,
        'sun_pitch': 0.65,
        'sun_color': (1.0, 0.6, 0.3),
        'fill1_heading': -2.5,
        'fill1_pitch': 0.45,
        'fill1_color': (0.8, 0.9, 1.0),
        'fill2_heading': 0.0,
        'fill2_pitch': 0.45,
        'fill2_color': (0.75, 0.8, 1.0),
        'ambient_color': (0.1, 0.1, 0.2),
        'fog_end': 600.0,
        'fog_color': (230.0, 100.0, 35.0),
        'shadow_alpha': 180.0,
        'shadow_color': (15.0, 20.0, 30.0)
    },
    {
        'time_of_day': NIGHT,
        'weather': CLEAR,
        'sun_pitch': 10.0,
        'sun_color': (40.0, 0.0, 40.0),
        'fill1_pitch': 10.0,
        'fill1_color': (40.0, 0.0, 40.0),
        'fill2_pitch': 10.0,
        'fill2_color': (40.0, 0.0, 40.0),
    },
]

###################################################################################################################   
################################################################################################################### 

# SET MATERIAL PROPERTIES
# available indices: 94, 95, 96, 97, 98,
# see: /UserResources/PHYSICS/PHYSICS.DB.txt for more information

new_physics_properties = {
    97: {"friction": 20.0, "elasticity": 0.01, "drag": 0.0},  # sticky
    98: {"friction": 0.1, "elasticity": 0.01, "drag": 0.0}}   # slippery

###################################################################################################################   
###################################################################################################################  

# Call FUNCTIONS
create_folders(map_filename)
create_city_info(map_name, map_filename)
BND.create(vertices, polys, map_filename, debug_bounds)
create_cells(map_filename, truncate_cells)
create_races(map_filename, race_data)
create_cnr(map_filename, cnr_waypoints)

StreetEditor.create(map_filename, street_list, set_ai_map, set_streets, set_reverse_streets)

MaterialEditor.edit(new_physics_properties, "physics.db", debug_physics)
Facade_Editor.create(f"{map_filename}.FCD", fcd_list, BASE_DIR / SHOP_CITY, set_facades, debug_facades)

# Not efficient, but a concise one-liner
PropEditor(input_props_f, debug_props, append_props, appended_props_f).append_props(appended_props, append_props) 
PropEditor(map_filename, debug_props).process_props(prop_list + [prop for i in random_props for prop in PropEditor(map_filename, debug_props).place_props_randomly(**i)])

#instances = LightingEditor.read_file(Path("EditorResources") / "LIGHTING.CSV")
#LightingEditor.process_changes(instances, lighting_configs)
#LightingEditor.write_file(instances, SHOP / "TUNE" / "LIGHTING.CSV")
# LightingEditor.debug(instances, "LIGHTING_DATA.txt")

copy_dev_folder(mm1_folder, map_filename)
edit_and_copy_mmbangerdata(bangerdata_properties)
copy_core_tune_files()
copy_custom_textures()

create_ext(map_filename, hudmap_vertices)
create_animations(map_filename, anim_data, set_anim)   
create_bridges(map_filename, bridges, set_bridges) 
custom_bridge_config(bridge_configs, set_bridges, SHOP / 'TUNE')
create_portals(map_filename, polys, vertices, empty_portals, debug_portals)

create_hudmap(set_minimap, debug_hud, debug_hud_bound_id, shape_outline_color,
               x_offset = 0.0, y_offset = 0.0, line_width = 0.7, background_color = 'black')

create_lars_race_maker(map_filename, street_list, lars_race_maker, process_vertices = True)

create_ar(map_filename)
create_commandline(map_filename, mm1_folder, no_ui, no_ui_type, no_ai, quiet_logs, more_logs)

end_time = time.time()
editor_time = end_time - start_time

save_run_time(editor_time)
progress_thread.join()

print("\n" + create_divider(colors_two))
print(Fore.LIGHTCYAN_EX  + "   Successfully created " + Fore.LIGHTYELLOW_EX  + f"{map_name}!" + Fore.MAGENTA + f" (in {editor_time:.4f} s)" + Fore.RESET)
print(create_divider(colors_two))

start_game(mm1_folder, play_game)

bpy.utils.register_class(OBJECT_PT_CellTypePanel)
bpy.utils.register_class(OBJECT_PT_MaterialTypePanel)
bpy.utils.register_class(OBJECT_PT_PolygonMiscOptionsPanel)
bpy.utils.register_class(OBJECT_PT_HUDColorPanel)
bpy.utils.register_class(OBJECT_PT_VertexCoordinates)

create_blender_meshes()
bpy.utils.register_class(OBJECT_OT_UpdateUVMapping)
bpy.utils.register_class(OBJECT_OT_ExportPolygons)
bpy.utils.register_class(OBJECT_OT_AssignCustomProperties)
set_blender_keybinding()

post_ar_cleanup(delete_shop)

###################################################################################################################   
################################################################################################################### 

#? Extra
# Read any BMS file in the current directory
# print(BMS.read("CULL17_H2.BMS"))

# Read any DLP file in the current directory
# print((lambda f: DLP.read(f))((open("VPCADDIE_BND.DLP", 'rb'))))

# Read the contents of existing BND files
# BND.debug_file(Path.cwd() / "UserResources" / "BOUNDS" / "CHICAGO_HITID.BND", Path.cwd() / "UserResources" / "BOUNDS" / "CHICAGO_HIT_ID.txt")
# BND.debug_directory(Path.cwd() / "UserResources" / "BOUNDS" / "Raw files", Path.cwd() / "UserResources" / "BOUNDS" / "Text files")
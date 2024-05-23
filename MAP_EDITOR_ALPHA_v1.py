
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
import psutil
import shutil
import struct
import random
import datetime
import textwrap
import pyautogui
import threading
import subprocess
import numpy as np
from pathlib import Path
from itertools import cycle
import matplotlib.pyplot as plt                
from colorama import Fore, Style, init
from typing import List, Dict, Set, Any, Union, Tuple, Optional, BinaryIO


#! SETUP 0 (Map Name)                           Control + F    "map=="  to jump to The Map Creation section
MAP_NAME = "My First City"                      # Can be multiple words --- name of the Map in the Race Locale Menu
MAP_FILENAME = "First_City"                     # One word (no spaces)  --- name of the .AR file and the folder in the SHOP folder


#! SETUP I (Folder Paths)  
class Folder:
    BASE = Path(__file__).parent.resolve()
    SHOP = BASE / "SHOP"
    SHOP_CITY = SHOP / "CITY"
    SHOP_RACE = SHOP / "RACE"   
    SHOP_TUNE = SHOP / "TUNE"
    SHOP_RACE_MAP = SHOP_RACE / f"{MAP_FILENAME}" 
    SHOP_MESH_LANDMARK = SHOP / "BMS" / f"{MAP_FILENAME}LM"
    SHOP_MESH_CITY = SHOP / "BMS" / f"{MAP_FILENAME}CITY"
    
    MIDTOWNMADNESS = BASE / "MidtownMadness"
    USER_RESOURCES = BASE / "Resources" / "UserResources"
    EDITOR_RESOURCES = BASE / "Resources" / "EditorResources"
    DEBUG_RESOURCES = BASE / "Resources" / "Debug" 
    
    
#* SETUP II (Map Creation)      
play_game = True                # Change to "True" to start the game after the Map is created (defaults to False when Blender is running)
delete_shop = True              # Change to "True" to delete the raw city files after the .AR file has been created

# Map Attributes
set_props = True                # Change to "True" if you want PROPS
set_bridges = True              # Change to "True" if you want BRIDGES
set_facades = True              # Change to "True" if you want FACADES
set_physics = True              # Change to "True" if you want PHYSICS (custom)
set_animations = True           # Change to "True" if you want ANIMATIONS (plane and eltrain)
set_texture_sheet = True        # Change to "True" if you want a TEXTURE SHEET (this will enable Custom Textures and modified existing Textures)

# Minimap
set_minimap = True              # Change to "True" if you want a MINIMAP (defaults to False when Blender is running)
minimap_outline_color = None    # Change the outline of the minimap shapes to any color (e.g. "Red"), if you don't want any color, set to None

# AI
set_ai_streets = True           # Change to "True" if you want AI streets
set_reverse_ai_streets = False  # Change to "True" if you want to add reverse AI streets
set_lars_race_maker = False     # Change to "True" if you want to create "Lars Race Maker" 
visualize_ai_paths = False      # Change to "True" if you want to visualize the AI streets in the Blender 

# Car Start Position in Cruise (if no polygon has the option "base = True")
cruise_start_position = (40.0, 30.0, -40.0)

round_vector_values = True      
disable_progress_bar = False    # Change to "True" if you want to disable the progress bar (this will display Errors and Warnings again)

################################################################################################################

# Misc
set_dlp = False                 # Change to "True" if you want to create a DLP file 

append_props = False            # Change to "True" if you want to append props
append_input_props_file = Folder.EDITOR_RESOURCES / "PROPS" / "CHICAGO.BNG"  
append_output_props_file = Folder.USER_RESOURCES / "PROPS" / "APP_CHICAGO.BNG"  

randomize_textures = False      # Change to "True" if you want to randomize all textures in your Map
random_textures = ["T_WATER", "T_GRASS", "T_WOOD", "T_WALL", "R6", "OT_BAR_BRICK", "FXLTGLOW"]

################################################################################################################

# Blender          
load_all_texures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# Input waypoint file
waypoint_file = Folder.EDITOR_RESOURCES / "RACE" / "RACE2WAYPOINTS.CSV"  

# Waypoints from the Editor ("race_data")
waypoint_number_input = "0", 
waypoint_type_input = "RACE"

################################################################################################################

# Advanced
no_ui = False                   # Change to "True" if you want skip the game's menu and go straight into Cruise mode
no_ui_type = "cruise"           # Other race types are currently not supported by the game in custom maps
no_ai = False                   # Change to "True" if you want to disable the AI and AI paths

less_logs = False               # Change to "True" if you want to hide most logs. This may prevent frame rate drops if the game is printing tons of errors or warnings
more_logs = False               # Change to "True" if you want additional logs and open a logging console when running the game

lower_portals = False           # Change to "True" if you want to lower the portals. This may be useful when you're "truncating" the cells file, and have cells below y = 0. This however may lead to issues with the AI
empty_portals = False           # Change to "True" if you want to create an empty portals file. This may be useful if you're testing a city with tens of thousands of polygons, which the portals file cannot handle. Nevertheless, we can still test the city by creating an empty portals file (this will compromise game visiblity)
truncate_cells = False			# Change to "True" if you want to truncate the characters in the cells file. This may be useful for testing large cities. A maximum of 254 characters is allowed per row in the cells file (~80 polygons). To avoid crashing the game, truncate any charachters past 254 (may compromise game visibility - lowering portals may mitigate this issue)

fix_faulty_quads = False        # Change to "True" if you want to fix faulty quads (e.g. self-intersecting quads)

################################################################################################################

# Editor Debugging
debug_props = False             # Change to "True" if you want a PROPS Debug text file
debug_meshes = False            # Change to "True" if you want MESH Debug text files 
debug_bounds = False            # Change to "True" if you want a BOUNDS Debug text file
debug_facades = False           # Change to "True" if you want a FACADES Debug text file
debug_physics = False           # Change to "True" if you want a PHYSICS Debug text file
debug_portals = False           # Change to "True" if you want a PORTALS Debug text file
debug_lighting = False          # Change to "True" if you want a LIGHTING Debug text file
debug_minimap = False           # Change to "True" if you want a HUD Debug JPG file (defaults to "True" when "set_lars_race_maker" is set to "True")
debug_minimap_id = False        # Change to "True" if you want to display the Bound IDs in the HUD Debug JPG file

# File Debugging | The Output Files are written to: "Resources / Debug / ..."
debug_props_file = False
debug_props_file_to_csv = False

debug_facades_file = False
debug_portals_file = False
debug_ai_file = False

debug_meshes_file = False
debug_meshes_folder = False

debug_bounds_file = False
debug_bounds_folder = False

debug_dlp_file = False
debug_dlp_folder = False

debug_props_data_file = Folder.EDITOR_RESOURCES / "PROPS" / "CHICAGO.BNG"          # Change the input Prop file here
debug_facades_data_file = Folder.EDITOR_RESOURCES / "FACADES" / "CHICAGO.FCD"      # Change the input Facade file here
debug_portals_data_file = Folder.EDITOR_RESOURCES / "PORTALS" / "CHICAGO.PTL"      # Change the input Portal file here
debug_ai_data_file = Folder.EDITOR_RESOURCES / "AI" / "CHICAGO.BAI"                # Change the input AI file here

debug_meshes_data_file = Folder.EDITOR_RESOURCES / "MESHES" / "CULL01_H.BMS"       # Change the input Mesh file here
debug_meshes_data_folder = Folder.EDITOR_RESOURCES / "MESHES" / "MESH FILES"       # Change the input Mesh folder here

debug_bounds_data_file = Folder.EDITOR_RESOURCES / "BOUNDS" / "CHICAGO_HITID.BND"  # Change the input Bound file here
debug_bounds_data_folder = Folder.EDITOR_RESOURCES / "BOUNDS" / "BND FILES"        # Change the input Bound folder here

debug_dlp_data_file = Folder.EDITOR_RESOURCES / "DLP" / "VPFER_L.DLP"              # Change the input DLP file here
debug_dlp_data_folder = Folder.EDITOR_RESOURCES / "DLP" / "DLP FILES"              # Change the input DLP folder here

################################################################################################################               
################################################################################################################
#! ======================= PROGRESS BAR, RUN TIME ======================= !#


def create_bar_divider(colors: List[str]) -> str:
    divider = "=" * 60  
    color_divider = ''.join(colors[i % len(colors)] + char for i, char in enumerate(divider))
    return "\n" + color_divider + "\n"


def clear_command_prompt_screen() -> None:
    print("\033[H\033[J", end = '')


def update_progress_bar(progress: float, buffer: str, top_divider: str, bottom_divider: str, disable_progress_bar: bool) -> None:
    if progress < 33:
        color = Style.BRIGHT + Fore.RED
    elif progress < 66:
        color = Style.BRIGHT + Fore.YELLOW
    else:
        color = Style.BRIGHT + Fore.GREEN
    
    progress = int(progress)
    progress_line = color + f"   Creating.. {MAP_NAME} [{'#' * (progress // 5)}{'.' * (20 - progress // 5)}] {progress}%" + Style.RESET_ALL
    buffer = top_divider + "\n" + progress_line + "\n" + bottom_divider + "\n"
    
    if not disable_progress_bar:
        clear_command_prompt_screen()
        
    print(buffer, end = "")


def continuous_progress_bar(duration: float, buffer: str, top_divider: str, bottom_divider: str, disable_progress_bar: bool) -> None:
    start_time = time.time()
    
    while True:
        elapsed_time = time.time() - start_time
        progress = (elapsed_time / duration) * 100
        progress = min(100, max(0, progress))  
        
        update_progress_bar(progress, buffer, top_divider, bottom_divider, disable_progress_bar)
        
        if progress >= 100:
            break

        if disable_progress_bar:
            time.sleep(5.0)
        else:
            time.sleep(0.025)


def save_editor_run_time(run_time: float, output_file: Path) -> None:
    with open(output_file, "wb") as f:
        pickle.dump(run_time, f)


def load_last_editor_run_time(input_file: Path):
    if input_file.exists():
        try:
            with open(input_file, "rb") as f:
                return pickle.load(f)
        except EOFError:
            return 2.0  # Default to 2.0 seconds if the file is empty or corrupted
    return 2.0          # Default to 2.0 seconds if no run time file exists

################################################################################################################
#! ======================= COLORS, SETUP PROGRESS BAR ======================= !#


init(autoreset = True)

colors_one = [
    Fore.RED, Fore.LIGHTRED_EX, Fore.YELLOW, Fore.LIGHTYELLOW_EX, Fore.GREEN, Fore.LIGHTGREEN_EX, 
    Fore.CYAN, Fore.LIGHTCYAN_EX, Fore.BLUE, Fore.LIGHTBLUE_EX, Fore.MAGENTA, Fore.LIGHTMAGENTA_EX
    ]

colors_two = [Fore.LIGHTGREEN_EX, Fore.GREEN,Fore.CYAN, Fore.LIGHTCYAN_EX,Fore.BLUE, Fore.LIGHTBLUE_EX]


progress_thread = threading.Thread(
    target = continuous_progress_bar, 
    args = (
        load_last_editor_run_time(Folder.EDITOR_RESOURCES / "last_run_time.pkl"), 
        create_bar_divider(colors_one) + "\n" + " " * 60 + "\n" + create_bar_divider(colors_one), 
        create_bar_divider(colors_one), 
        create_bar_divider(colors_one), 
        disable_progress_bar)
    )

progress_thread.start()
start_time = time.time()

################################################################################################################               
################################################################################################################
#! ======================= INITIALIZATIONS & CONSTANTS ======================= !#


vertices = [] 
texture_names = []
texcoords_data = {}

polygons_data = []

hudmap_vertices = []
hudmap_properties = {}

NO = 0  # For example, AI Street Properties ("traffic_blocked = YES")
YES = 1 
HUGE = 100000000000
PROP_COLLIDE_FLAG = 0x800


class Shape:
    LINE = 2
    TRIANGLE = 3
    QUAD = 4


class TimeOfDay:
    MORNING = 0
    NOON = 1
    EVENING = 2
    NIGHT = 3


class Weather:
    CLEAR = 0
    CLOUDY = 1
    RAIN = 2
    SNOW = 3
    
    
class RaceMode:
    ROAM = "ROAM"
    CRUISE = "CRUISE"
    BLITZ = "BLITZ"
    CHECKPOINT = "RACE"
    CIRCUIT = "CIRCUIT"
    COPS_AND_ROBBERS = "COPSANDROBBERS"
    
    
class NetworkMode:
    SINGLE = "SINGLE"
    MULTI = "MULTI"
    SINGLE_AND_MULTI = "All Modes"


class Threshold:
    BLITZ_WAYPOINT_COUNT = 11
    CHECKPOINT_RACE_COUNT = 12
    BLITZ_AND_CIRCUIT_RACE_COUNT = 15
    MESH_VERTEX_COUNT = 16
    CELL_TYPE_SWITCH = 200
    CELL_CHARACTER_WARNING = 200
    CELL_CHARACTER_LIMIT = 0xFF    
    VERTEX_INDEX_COUNT = 0x8000
    

class Portal:
    ACTIVE = 0x1
    OPEN_AREA = 0x2         # Reset Clip MinX, MaxX, MinY, MaxY 
    HALF_OPEN_AREA = 0x4    # Reset MinX or MaxX depending on direction
    PLANE = 0x8             # Must be infront (or behind?) portal plane
    
    
class agiMeshSet:
    TEXCOORDS = 0x1
    NORMALS = 0x2
    COLORS = 0x4
    OFFSET = 0x8
    PLANES = 0x10
    
    TEXCOORDS_AND_NORMALS = TEXCOORDS | NORMALS
    TEXCOORDS_AND_COLORS = TEXCOORDS | COLORS
    NORMALS_AND_COLORS = NORMALS | COLORS
    OFFSET_AND_PLANES = OFFSET | PLANES
    TEXCOORDS_AND_OFFSET = TEXCOORDS | OFFSET
    NORMALS_AND_PLANES = NORMALS | PLANES
    
    FENDERS = TEXCOORDS | NORMALS | OFFSET | PLANES  # Used for Fenders (Panoz Roadster)
    
    ALL_FEATURES = TEXCOORDS | NORMALS | COLORS | OFFSET | PLANES
        
        
class LevelOfDetail:
    UNKNOWN_1 = 0x1    # A
    LOW = 0x2          # L
    MEDIUM = 0x4       # M
    HIGH = 0x8         # H
    DRIFT = 0x20       # A2
    UNKNOWN_2 = 0x40   # L2
    UNKNOWN_3 = 0x80   # M2
    UNKNOWN_4 = 0x100  # H2
    
    
class PlaneEdgesWinding:
    TRIANGLE = 0x0
    QUAD = 0x4
    FLIP_WINDING = 0x8

    TRIANGLE_X_AXIS = 0x0  # PlaneEdges are projected along X axis
    TRIANGLE_Y_AXIS = 0x1  # PlaneEdges are projected along Y axis
    TRIANGLE_Z_AXIS = 0x2  # PlaneEdges are projected along Z axis

    QUAD_X_AXIS = 0x4        # Is Quad and PlaneEdges are projected along X axis
    QUAD_Y_AXIS = 0x4 | 0x1  # Is Quad and PlaneEdges are projected along Y axis
    QUAD_Z_AXIS = 0x4 | 0x2  # Is Quad and PlaneEdges are projected along Z axis

    FLIP_WINDING_X_AXIS = 0x8        # Flip Winding and PlaneEdges are projected along X axis
    FLIP_WINDING_Y_AXIS = 0x8 | 0x1  # Flip Winding and PlaneEdges are projected along Y axis
    FLIP_WINDING_Z_AXIS = 0x8 | 0x2  # Flip Winding and PlaneEdges are projected along Z axis

    FLIP_WINDING_QUAD_X_AXIS = 0x8 | 0x4        # Is Quad, Flip Winding, and PlaneEdges are projected along X axis
    FLIP_WINDING_QUAD_Y_AXIS = 0x8 | 0x4 | 0x1  # Is Quad, Flip Winding, and PlaneEdges are projected along Y axis
    FLIP_WINDING_QUAD_Z_AXIS = 0x8 | 0x4 | 0x2  # Is Quad, Flip Winding, and PlaneEdges are projected along Z axis


class IntersectionType:
    STOP = 0
    STOP_LIGHT = 1
    YIELD = 2
    CONTINUE = 3
    
        
class CopBehavior:
    FOLLOW = 0x1      # Follow, only following the player
    ROADBLOCK = 0x2   # Attempt to create roadblocks
    SPINOUT = 0x4     # Try to spin the player out
    PUSH = 0x8        # Pushing behavior, ramming from the back

    MIX = FOLLOW | ROADBLOCK | SPINOUT | PUSH     # Mix of all behaviors

    FOLLOW_AND_SPINOUT = FOLLOW | SPINOUT         # Follow and try to spin out
    FOLLOW_AND_PUSH = FOLLOW | PUSH               # Follow and push
    ROADBLOCK_AND_SPINOUT = ROADBLOCK | SPINOUT   # Attempt roadblocks and spin out
    ROADBLOCK_AND_PUSH = ROADBLOCK | PUSH         # Attempt roadblocks and push
    SPINOUT_AND_PUSH = SPINOUT | PUSH             # Spin out and push
    
    AGGRESSIVE = ROADBLOCK | SPINOUT | PUSH       # All behaviors except follow
    DEFENSIVE = FOLLOW | ROADBLOCK                # More passive, keeping distance
    CUNNING = FOLLOW | SPINOUT                    # Following and occasionally spinning out
    PERSISTENT = FOLLOW | PUSH                    # Persistently following and pushing
    UNPREDICTABLE = ROADBLOCK | FOLLOW | SPINOUT  # Unpredictable mix of behaviors
    

class CopDensity:
    _0 = 0.0
    _100 = 1.0  # The game only supports 0.0 and 1.0
    
    
class CopStartLane:
    STATIONARY = 0 
    PED = 1  # Broken, do not use (this feature was never finished by the game's developers)
    IN_TRAFFIC = 2    
    
    
class Density:
    _0 = 0.0
    _10 = 0.1
    _20 = 0.2
    _30 = 0.3
    _40 = 0.4
    _50 = 0.5
    _60 = 0.6
    _70 = 0.7
    _80 = 0.8
    _90 = 0.9
    _100 = 1.0


class PedDensity(Density):
    pass
    
    
class AmbientDensity(Density):
    pass
    

class Rotation:
    AUTO = 0
    NORTH = 0.01
    NORTH_EAST = 45
    EAST = 90
    SOUTH_EAST = 135
    SOUTH = 179.99
    SOUTH_WEST = -135
    WEST = -90
    NORTH_WEST = -45
    AUTO = 0
    
    FULL_CIRCLE = 360
    HALF_CIRCLE = 180
    
    
class Width:
    AUTO = 0
    DEFAULT = 15
    ALLEY = 3
    SMALL = 11
    MEDIUM = 15
    LARGE = 19
    

class NumericOptions:
    _0 = 0
    _1 = 1
    _2 = 2
    _3 = 3
    _4 = 4
    _5 = 5
    _6 = 6
    _7 = 7
    _8 = 8

class MaxOpponents(NumericOptions):
    # The game can (likely) support more than 128 opponents, however the game's "MAX_MOVERS" is capped at 128
    # (see: Open1560 / code / midtown / mmphysics / phys.cpp)
    _128 = 128  


class Laps(NumericOptions):
     # The game can load races with 1000+ laps, however the game's menu caps the number to 10
    _9 = 9
    _10 = 10
    
    
class Color:
    RED = (1, 0, 0, 1)
    GREEN = (0, 1, 0, 1)
    BLUE = (0, 0, 1, 1)
    PURPLE = (0.5, 0, 0.5, 1)
    YELLOW = (1, 1, 0, 1)
    GOLD = (1, 0.843, 0, 1)
    WHITE = (1, 1, 1, 1)
    
    WOOD = "#7b5931"
    SNOW = "#cdcecd"
    WATER = "#5d8096"
    ROAD = "#414441"
    GRASS = "#396d18"

    ORANGE = "#ffa500"
    RED_DARK = "#af0000"
    RED_LIGHT = "#ff7f7f"
    YELLOW_LIGHT = "#ffffe0"

################################################################################################################               
################################################################################################################
#! ======================= CARS & PROPS ======================= !#


# Player Cars and Traffic Cars can be used as Opponent cars, Cop cars, and Props
class PlayerCar:
    VW_BEETLE = "vpbug"
    CITY_BUS = "vpbus"
    CADILLAC = "vpcaddie"
    CRUISER = "vpcop"
    FORD_F350 = "vpford"
    FASTBACK = "vpbullet"
    MUSTANG99 = "vpmustang99"
    ROADSTER = "vppanoz"
    PANOZ_GTR_1 = "vppanozgt"
    SEMI = "vpsemi"


class TrafficCar:
    TINY_CAR = "vacompact"
    SEDAN_SMALL = "vasedans"
    SEDAN_LARGE = "vasedanl"
    YELLOW_TAXI = "vataxi"
    GREEN_TAXI = "vataxicheck"
    WHITE_LIMO = "valimo"
    BLACK_LIMO = "valimoangel"
    PICKUP = "vapickup"
    SMALL_VAN = "vavan"
    DELIVERY_VAN = "vadelivery"
    LARGE_TRUCK = "vadiesels"
    TRAFFIC_BUS = "vabus"
    PLANE_SMALL = "vaboeing_small"


class Anim:
    PLANE = "plane"
    ELTRAIN = "eltrain"


class Prop:
    BRIDGE_SLIM = "tpdrawbridge04"      # Dimension: x: 30.0 y: 5.9 z: 32.5
    BRIDGE_WIDE = "tpdrawbridge06"      # Dimension: x: 40.0 y: 5.9 z: 32.5
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
    
    
class AudioProp:
    MALLDOOR = 1
    POLE = 3
    SIGN = 4
    MAILBOX = 5
    METER = 6
    TRASHCAN = 7
    BENCH = 8
    TREE = 11
    TRASH_BOXES = 12    # Also used for "bridge crossgate"
    NO_NAME_1 = 13      # Difficult to describe
    BARREL = 15         # Also used for "dumpster"
    PHONEBOOTH = 20
    CONE = 22
    NO_NAME_2 = 24      # Sounds a bit similar to "glass"
    NEWSBOX = 25
    GLASS = 27
 
################################################################################################################   
################################################################################################################
#! ======================= RACE EDITOR ======================= !#


#* SETUP III (optional, Race Editor)
# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints (including the start position), the number of waypoints for Circuits and Checkpoints is unlimited
# The max number of laps in Circuit races is 10

# Race Names
blitz_race_names = ["Chaotic Tower"]
circuit_race_names = ["Circuit Race"] 
checkpoint_race_names = ["Photo Finish"]

# Races
race_data = {
    "BLITZ_0": {
        "player_waypoints": [
            [0.0, 0.0, 55.0, Rotation.NORTH, 12.0], 
            [0.0, 0.0, 15.0, Rotation.NORTH, 12.0], 
            [0.0, 0.0, -40.0, Rotation.NORTH, 12.0], 
            [0.0, 0.0, -130.0, Rotation.NORTH, 12.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 999],        
            "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 999], 
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 2,
            "police": [
                f"{PlayerCar.CRUISER} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.CRUISER} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
            ],
            "num_of_opponents": 1,
            "opponents": {
                PlayerCar.CADILLAC: [
                    [5.0, 0.0, 35.0], 
                    [5.0, 0.0, -130.0],
                ],
            },
            "num_of_exceptions": None,
            "exceptions": [
                [4, 0.0, 45],
                [5, 0.0, 45],
            ], 
        },
    },
    "RACE_0": {
        "player_waypoints": [
            [0.0, 245, -850, Rotation.SOUTH, Width.MEDIUM], 
            [0.0, 110, -500, Rotation.SOUTH, Width.MEDIUM],  
            [0.0, 110, -497, Rotation.SOUTH, Width.MEDIUM],   
            [25.0, 45.0, -325, Rotation.SOUTH, 25.0],   
            [35.0, 12.0, -95.0, Rotation.SOUTH, Width.MEDIUM], 
            [35.0, 30.0, 0.0, Rotation.SOUTH, Width.MEDIUM], 
            [35.0, 30.0, 40.0, Rotation.SOUTH, Width.MEDIUM], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 1,
            "opponents": {
                PlayerCar.PANOZ_GTR_1: [[5.0, 0.0, 35.0], [5.0, 0.0, -130.0]], 
            },
        },
    },
    "CIRCUIT_0": {
        "player_waypoints": [
            [0.0, 245, -850, Rotation.SOUTH, Width.MEDIUM], 
            [0.0, 110, -500, Rotation.SOUTH, 30.0],    
            [25.0, 45.0, -325, Rotation.SOUTH, 25.0],   
            [35.0, 12.0, -95.0, Rotation.SOUTH, Width.MEDIUM], 
            [35.0, 30.0, 0.0, Rotation.SOUTH, Width.MEDIUM], 
            [35.0, 30.0, 40.0, Rotation.SOUTH, Width.MEDIUM], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._2],
            "pro": [TimeOfDay.NIGHT, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 2,
            "opponents": {
            TrafficCar.WHITE_LIMO: [
                [-10.0, 245, -850], 
                [0.0, 0.0, -100],
                [-10.0, 0.0, -75.0]
            ],
            TrafficCar.BLACK_LIMO: [
                [10.0, 245, -850],
                [0.0, 0.0, -100],
                [10.0, 0.0, -75.0],
            ],
            }
        },
    }
}


#* SETUP IV (optional, Cops and Robbers)
cnr_waypoints = [                           
    ## 1st set, Name: ... ## 
    (20.0, 1.0, 80.0),                      #? Bank / Blue Team Hideout
    (80.0, 1.0, 20.0),                      #? Gold
    (20.0, 1.0, 80.0),                      #? Robber / Red Team Hideout
    ## 2nd set, Name: ... ## 
    (-90.0, 1.0, -90.0),
    (90.0, 1.0, 90.0),
    (-90.0, 1.0, -90.0)]

################################################################################################################   
################################################################################################################
#! ======================= ANIMATIONS & BRIDGES ======================= !#


#* SETUP V (optional, Animations)
animations_data = {
    Anim.PLANE: [               # You can not have multiple Planes or Eltrains
        (450, 30.0, -450),      # You can set any number of coordinates for your path(s)
        (450, 30.0, 450),       
        (-450, 30.0, -450),     
        (-450, 30.0, 450)], 
    Anim.ELTRAIN: [
        (180, 25.0, -180),
        (180, 25.0, 180), 
        (-180, 25.0, -180),
        (-180, 25.0, 180)]}


#* SETUP VI (optional, Bridges)
"""
INFO
    1) You can set a maximum of 1 bridge per cull room, which may have up to 5 attributes
    2) You can set a bridge without any attributes like this:
        (-50.0, 0.01, -100.0), 270, 2, BRIDGE_WIDE, [])
        
    3) Supported orientations:
    NORTH, NORTH_EAST, EAST, SOUTH_EAST SOUTH, SOUTH WEST, WEST, NORTH_WEST
    Or you can manually set the orientation in degrees (0.0 - 360.0).
"""

# Structure: (x, y, z, rotation, bridge ID, bridge object)
bridge_list = [
    ((-50.0, 0.01, -100.0), Rotation.WEST, 2, Prop.BRIDGE_WIDE, [
    ((-50.0, 0.15, -115.0), Rotation.WEST, 2, Prop.CROSSGATE),
    ((-50.0, 0.15, -85.0), Rotation.EAST, 2, Prop.CROSSGATE)
    ]),  
    ((-119.0, 0.01, -100.0), Rotation.EAST, 3, Prop.BRIDGE_WIDE, [
    ((-119.0, 0.15, -115.0), Rotation.WEST, 3, Prop.CROSSGATE),
    ((-119.0, 0.15, -85.0), Rotation.EAST, 3, Prop.CROSSGATE)
    ])] 


#* SETUP VII (optional, Custom Bridge Configs)
bridge_race_0 = {
    "RaceType": RaceMode.CHECKPOINT, 
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
    "Mode": NetworkMode.SINGLE}

bridge_cnr = {
    "RaceType": RaceMode.COPS_AND_ROBBERS,
    "BridgeDelta": 0.20,
    "BridgeOffGoal": 0.33,
    "BridgeOnGoal": 0.33,
    "Mode": NetworkMode.MULTI}

# Pack all Custom Bridge Configurations for processing
bridge_config_list = [bridge_race_0, bridge_cnr]

################################################################################################################               
################################################################################################################     
#! ======================= STRUCT & VECTOR CLASSES ======================= !#


def read_unpack(file: BinaryIO, fmt: str) -> Tuple:
    return struct.unpack(fmt, file.read(calc_size(fmt)))


def write_pack(file: BinaryIO, fmt: str, *args: object) -> None:
    file.write(struct.pack(fmt, *args))


def calc_size(fmt: str) -> int:
    return struct.calcsize(fmt)


class Vector2:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
            
    @staticmethod
    def read(file: BinaryIO, byte_order: str = '<') -> 'Vector2':
        return Vector2(*read_unpack(file, f'{byte_order}2f'))

    @staticmethod
    def readn(file: BinaryIO, count: int, byte_order: str = '<') -> List['Vector2']:
        return [Vector2.read(file, byte_order) for _ in range(count)]
            
    def write(self, file: BinaryIO, byte_order: str = '<') -> None:
        write_pack(file, f'{byte_order}2f', self.x, self.y)
        
    @staticmethod
    def binary_size() -> int:
        return calc_size('2f')
                
    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float) -> 'Vector2':
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other: float) -> 'Vector2':
        return Vector2(self.x / other, self.y / other)

    def __eq__(self, other: 'Vector2') -> bool:
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def Cross(self, rhs: 'Vector2' = None) -> 'Vector2':
        if rhs is None:
            return Vector2(self.y, -self.x)

        return Vector2((self.x*rhs.y) - (self.y*rhs.x))

    def Dot(self, rhs: 'Vector2') -> float:
        return (self.x * rhs.x) + (self.y * rhs.y)

    def Mag2(self) -> float:
        return (self.x * self.x) + (self.y * self.y)

    def Dist2(self, other: 'Vector2') -> float:
        return (other - self).Mag2()

    def Dist(self, other: 'Vector2') -> float:
        return self.Dist2(other) ** 0.5
    
    def Normalize(self) -> 'Vector2':
        return self * (self.Mag2() ** -0.5)
    
    def __repr__(self, round_vector_values: bool = round_vector_values) -> str:
        if round_vector_values:
            return f'{round(self.x, 2):.2f}, {round(self.y, 2):.2f}'
        else:
            return f'{self.x:f}, {self.y:f}'


class Vector3:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z
        self._data = {"x": x, "y": y, "z": z}
        
    @staticmethod
    def read(file: BinaryIO, byte_order: str = '<') -> 'Vector3':
        return Vector3(*read_unpack(file, f'{byte_order}3f'))

    @staticmethod
    def readn(file: BinaryIO, count: int, byte_order: str = '<') -> List['Vector3']:
        return [Vector3.read(file, byte_order) for _ in range(count)]
    
    def write(self, file: BinaryIO, byte_order: str = '<') -> None:
        write_pack(file, f'{byte_order}3f', self.x, self.y, self.z)
        
    @staticmethod
    def binary_size() -> int:
        return calc_size('3f')
        
    @classmethod
    def from_tuple(cls, vertex_tuple: Tuple[float, float, float]) -> 'Vector3':
        return cls(*vertex_tuple)

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
        
    def copy(self) -> 'Vector3':
        return Vector3(self.x, self.y, self.z)
    
    def __getitem__(self, key: str) -> float:
        return self._data[key]

    def __setitem__(self, key: str, value: float) -> None:
        if key in self._data:
            self._data[key] = value
            setattr(self, key, value)
        else:
            raise ValueError(f"Invalid key: {key}. Use 'x', 'y', or 'z'.")

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other: float) -> 'Vector3':
        return Vector3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other: float) -> 'Vector3':
        return Vector3(self.x / other, self.y / other, self.z / other)

    def __eq__(self, other: 'Vector3') -> bool:
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))
    
    def Cross(self, rhs: 'Vector3') -> 'Vector3':
        return Vector3(self.y * rhs.z - self.z * rhs.y, self.z * rhs.x - self.x * rhs.z, self.x * rhs.y - self.y * rhs.x)

    def Dot(self, rhs: 'Vector3') -> float:
        return (self.x * rhs.x) + (self.y * rhs.y) + (self.z * rhs.z)
    
    def Mag(self) -> float:
        return self.Mag2() ** 0.5
    
    def Mag2(self) -> float:
        return (self.x * self.x) + (self.y * self.y) + (self.z * self.z)

    def Normalize(self) -> 'Vector3':
        return self * (self.Mag2() ** -0.5)

    def Dist2(self, other: 'Vector3') -> float:
        return (other - self).Mag2()

    def Dist(self, other: 'Vector3') -> float:
        return self.Dist2(other) ** 0.5
        
    def Angle(self, rhs: 'Vector3') -> float:
        return math.acos(self.Dot(rhs) * ((self.Mag2() * rhs.Mag2()) ** -0.5))
    
    def Negate(self) -> 'Vector3':
        return Vector3(-self.x, -self.y, -self.z)

    def Set(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z
                
    def __repr__(self, round_vector_values: bool = round_vector_values) -> str:
        if round_vector_values:
            return f'{{ {round(self.x, 2):.2f}, {round(self.y, 2):.2f}, {round(self.z, 2):.2f} }}'
        else:
            return f'{{ {self.x:f}, {self.y:f}, {self.z:f} }}'
        
        
class Vector4:
    def __init__(self, x: float, y: float, z: float, w: float) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w
        
    @staticmethod
    def binary_size() -> int:
        return calc_size('4f')  

################################################################################################################               
################################################################################################################ 
#! ======================= POLYGON CLASS ======================= !#


class Polygon:
    def __init__(self, cell_id: int, material_index: int, flags: int, vertex_index: List[int],
                 plane_edges: List[Vector3], plane_normal: Vector3, plane_distance: float, 
                 cell_type: int = 0, always_visible: bool = False) -> None:
        
        self.cell_id = cell_id
        self.material_index = material_index
        self.flags = flags
        self.vertex_index = vertex_index
        self.plane_edges = plane_edges
        self.plane_normal = plane_normal
        
        if isinstance(plane_distance, list) and len(plane_distance) == 1:
            plane_distance = plane_distance[0]
        elif isinstance(plane_distance, np.float64):
            plane_distance = float(plane_distance)
            
        self.plane_distance = plane_distance
        
        self.cell_type = cell_type
        self.always_visible = always_visible
        
    @property
    def is_quad(self) -> bool:
        return bool(self.flags & Shape.QUAD)

    @property
    def num_verts(self) -> int:
        return Shape.QUAD if self.is_quad else Shape.TRIANGLE
          
    @classmethod
    def read(cls, f: BinaryIO) -> 'Polygon':
        cell_id, material_index, = read_unpack(f, '<HB')
        flags = read_unpack(f, '<B')
        vertex_index = read_unpack(f, '<4H') 
        plane_edges = Vector3.readn(f, Shape.QUAD, '<')
        plane_normal = Vector3.read(f, '<')
        plane_distance = read_unpack(f, '<f')
        return cls(cell_id, material_index, flags, vertex_index, plane_edges, plane_normal, plane_distance)
            
    def write(self, f: BinaryIO) -> None:            
        if len(self.vertex_index) == Shape.TRIANGLE:  # Each polygon requires four vertex indices
            self.vertex_index += (0,)
        
        write_pack(f, '<HB', self.cell_id, self.material_index)
        write_pack(f, '<B', self.flags)
        write_pack(f, '<4H', *self.vertex_index)

        for edge in self.plane_edges:
            edge.write(f, '<')
            
        self.plane_normal.write(f, '<')
        write_pack(f, '<f', self.plane_distance)
    
    def __repr__(self, bnd_instance) -> str:
        vertices_coordinates = [bnd_instance.vertices[idx] for idx in self.vertex_index]
        # plane_d = ', '.join(f'{d:.2f}' for d in self.plane_d)
        return f"""
POLYGON
    Cell ID: {self.cell_id}
    Material Index: {self.material_index}
    Flags: {self.flags}
    Vertex Indices: {self.vertex_index}
    Vertices Coordinates: {vertices_coordinates}
    Plane Edges: {self.plane_edges}
    Plane N: {self.plane_normal}
    Plane D: {self.plane_distance}
    """
    
################################################################################################################               
################################################################################################################     


class Default:
    ROOM = 1
    VECTOR_2 = Vector2(0, 0)
    VECTOR_3 = Vector3(0, 0, 0)


Default.POLYGON = Polygon(0, 0, 0, [0, 0, 0, 0], [Default.VECTOR_3 for _ in range(4)], Default.VECTOR_3, [0.0], 0)
polys = [Default.POLYGON]
        
################################################################################################################               
################################################################################################################          
#! ======================= BOUNDS CLASS ======================= !#


class Bounds:
    def __init__(self, magic: str, offset: Vector3, x_dim: int, y_dim: int, z_dim: int, 
                 center: Vector3, radius: float, radius_sqr: float, bb_min: Vector3, bb_max: Vector3, 
                 num_verts: int, num_polys: int, num_hot_verts_1: int, num_hot_verts_2: int, num_edges: int, 
                 x_scale: float, z_scale: float, num_indices: int, height_scale: float, cache_size: int, 
                 vertices: List[Vector3], polys: List[Polygon],
                 hot_verts: List[Vector3], edge_verts_1: List[int], edge_verts_2: List[int], 
                 edge_plane_normal: List[Vector3], edge_plane_distance: List[float],
                 row_offsets: Optional[List[int]], bucket_offsets: Optional[List[int]], 
                 row_buckets: Optional[List[int]], fixed_heights: Optional[List[int]]) -> None:
        
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
        self.num_hot_verts_1 = num_hot_verts_1
        self.num_hot_verts_2 = num_hot_verts_2
        self.num_edges = num_edges
        self.x_scale = x_scale
        self.z_scale = z_scale
        self.num_indices = num_indices
        self.height_scale = height_scale
        self.cache_size = cache_size
        
        self.vertices = vertices              
        self.polys = polys   
        
        self.hot_verts = hot_verts
        self.edge_verts_1 = edge_verts_1
        self.edge_verts_2 = edge_verts_2
        self.edge_plane_normal = edge_plane_normal
        self.edge_plane_distance = edge_plane_distance
        self.row_offsets = row_offsets
        self.bucket_offsets = bucket_offsets
        self.row_buckets = row_buckets
        self.fixed_heights = fixed_heights
                  
    @classmethod
    def read(cls, f: BinaryIO) -> 'Bounds':  
        magic = read_binary_name(f, 4)      
        offset = Vector3.read(f, '<')
        x_dim, y_dim, z_dim = read_unpack(f, '<3l')
        center = Vector3.read(f, '<')
        radius, radius_sqr = read_unpack(f, '<2f')
        bb_min = Vector3.read(f, '<')
        bb_max = Vector3.read(f, '<')
        num_verts, num_polys = read_unpack(f, '<2l')
        num_hot_verts_1, num_hot_verts_2, = read_unpack(f, '<2l')
        num_edges = read_unpack(f, '<l')
        x_scale, z_scale = read_unpack(f, '<2f')
        num_indices, = read_unpack(f, '<l')
        height_scale, = read_unpack(f, '<f')
        cache_size, = read_unpack(f, '<l')
        
        vertices = Vector3.readn(f, num_verts, '<')
        polys = [Polygon.read(f) for _ in range(num_polys + 1)] 

        hot_verts = Vector3.readn(f, num_hot_verts_2, '<')
        edge_verts_1 = read_unpack(f, f'<{num_edges}I')
        edge_verts_2 = read_unpack(f, f'<{num_edges}I')
        edge_plane_normal = Vector3.readn(f, num_edges, '<')
        edge_plane_distance = read_unpack(f, f'<{num_edges}f')

        row_offsets = None
        bucket_offsets = None
        row_buckets = None
        fixed_heights = None

        if x_dim and y_dim and z_dim:
            row_offsets = read_unpack(f, f'<{z_dim}I')
            bucket_offsets = read_unpack(f, f'<{x_dim * z_dim}H')
            row_buckets = read_unpack(f, f'<{num_indices}H')
            fixed_heights = read_unpack(f, f'<{x_dim * z_dim}B')

        return cls(
            magic, offset, x_dim, y_dim, z_dim, center, radius, radius_sqr, bb_min, bb_max, 
            num_verts, num_polys, num_hot_verts_1, num_hot_verts_2, num_edges, 
            x_scale, z_scale, num_indices, height_scale, cache_size, vertices, polys,
            hot_verts, edge_verts_1, edge_verts_2, edge_plane_normal, edge_plane_distance,
            row_offsets, bucket_offsets, row_buckets, fixed_heights
            )
    
    @classmethod
    def initialize(cls, vertices: List[Vector3], polys: List[Polygon]) -> 'Bounds':
        magic = "2DNB"
        offset = Default.VECTOR_3
        x_dim, y_dim, z_dim = 0, 0, 0
        center = calculate_center(vertices)
        radius = calculate_radius(vertices, center)
        radius_sqr = calculate_radius_squared(vertices, center)
        bb_min = calculate_min(vertices)
        bb_max = calculate_max(vertices)
        num_hot_verts_1, num_hot_verts_2 = 0, 0
        num_edges = 0
        x_scale, z_scale = 0.0, 0.0
        num_indices = 0
        height_scale = 0.0
        cache_size = 0
        
        hot_verts = [Default.VECTOR_3]  
        edge_verts_1, edge_verts_2 = [0], [1] 
        edge_plane_normal = [Default.VECTOR_3] 
        edge_plane_distance = [0.0]  
        row_offsets, bucket_offsets, row_buckets, fixed_heights = [0], [0], [0], [0]  

        return cls(
            magic, offset, x_dim, y_dim, z_dim, 
            center, radius, radius_sqr, bb_min, bb_max, 
            len(vertices), len(polys) - 1, 
            num_hot_verts_1, num_hot_verts_2, num_edges, 
            x_scale, z_scale, num_indices, height_scale, cache_size, 
            vertices, polys, 
            hot_verts, edge_verts_1, edge_verts_2, 
            edge_plane_normal, edge_plane_distance,
            row_offsets, bucket_offsets, row_buckets, fixed_heights
            )
            
    def write(self, f: BinaryIO) -> None:
        write_binary_name(f, self.magic)        
        self.offset.write(f, '<')         
        write_pack(f, '<3l', self.x_dim, self.y_dim, self.z_dim)
        self.center.write(f, '<') 
        write_pack(f, '<2f', self.radius, self.radius_sqr)
        self.bb_min.write(f, '<')
        self.bb_max.write(f, '<')
        write_pack(f, '<2l', self.num_verts, self.num_polys)
        write_pack(f, '<2l', self.num_hot_verts_1, self.num_hot_verts_2)
        write_pack(f, '<l', self.num_edges)
        write_pack(f, '<2f', self.x_scale, self.z_scale) 
        write_pack(f, '<l', self.num_indices)
        write_pack(f, '<f', self.height_scale)
        write_pack(f, '<I', self.cache_size)
 
        for vertex in self.vertices:       
            vertex.write(f, '<')   
        
        for poly in self.polys:           
            poly.write(f)
                    
    @staticmethod
    def create(output_file: Path, vertices: List[Vector3], polys: List[Polygon], debug_file: Path, debug_bounds: bool) -> None:
        bnd = Bounds.initialize(vertices, polys)
                
        with open (output_file, "wb") as f:
            bnd.write(f)
            
            if debug_bounds:
                bnd.debug(debug_file)
                
    def debug(self, output_file: Path) -> None:
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)
        
        with open(output_file, 'w') as out_f:
            out_f.write(str(self))
            
    @staticmethod
    def debug_file(input_file: Path, output_file: Path, debug_bounds_file: bool) -> None:
        if not debug_bounds_file:
            return
        
        if not input_file.exists():
            raise FileNotFoundError(f"The file {input_file} does not exist.")
        
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)
        
        with open(input_file, "rb") as in_f:
            bnd = Bounds.read(in_f)

        with open(output_file, "w") as out_f:
            out_f.write(repr(bnd))
            
    @staticmethod
    def debug_folder(input_folder: Path, output_folder: Path, debug_bounds_folder: bool) -> None:
        if not debug_bounds_folder:
            return

        if not input_folder.exists():
            raise FileNotFoundError(f"The folder {input_folder} does not exist.")

        bnd_files = list(input_folder.glob("*.BND"))
        
        if not bnd_files:
            raise FileNotFoundError(f"No .BND files found in {input_folder}.")

        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        for file in bnd_files:
            output_file = output_folder / file.with_suffix(".txt").name
            Bounds.debug_file(file, output_file, debug_bounds_folder)
            print(f"Processed {file.name} to {output_file.name}")
                    
    def __repr__(self) -> str:
        polygon_polys = '\n'.join([poly.__repr__(self) for poly in self.polys])
        return f"""
BOUND
    Magic: {self.magic}
    Offset: {self.offset}
    X Dim: {self.x_dim}
    Y Dim: {self.y_dim}
    Z Dim: {self.z_dim}
    Center: {self.center}
    Radius: {self.radius:.2f}
    Radius Sqr: {self.radius_sqr:.2f}
    BB Min: {self.bb_min}
    BB Max: {self.bb_max}
    Num Verts: {self.num_verts}
    Num Polys: {self.num_polys}
    Num Hot Verts 1: {self.num_hot_verts_1}
    Num Hot Verts 2: {self.num_hot_verts_2}
    Num Edges: {self.num_edges}
    X Scale: {self.x_scale:.5f}
    Z Scale: {self.z_scale:.5f}
    Num Indices: {self.num_indices}
    Height Scale: {self.height_scale:.5f}
    Cache Size: {self.cache_size}\n
    Vertices:
    {self.vertices}\n
    ======= Polys =======
    {polygon_polys}\n
    ======= Split =======\n
    Hot Verts: {self.hot_verts}
    Edge Verts 1: {self.edge_verts_1}
    Edge Verts 2: {self.edge_verts_2}
    Edge Plane N: {self.edge_plane_normal}
    Edge Plane D: {', '.join(f'{d:.2f}' for d in self.edge_plane_distance)}\n  
    ======= Split =======\n
    Row Offsets: {self.row_offsets}\n
    ======= Split =======\n
    Bucket Offsets: {self.bucket_offsets}\n
    ======= Split =======\n
    Row Buckets: {self.row_buckets}\n
    ======= Split =======\n
    Fixed Heights: {self.fixed_heights}\n
    """
    
################################################################################################################               
################################################################################################################  
#! ======================= MESHES CLASS ======================= !#


class Meshes:
    def __init__(self, magic: str, vertex_count: int, adjunct_count: int, surface_count: int, indices_count: int,
                 radius: float, radius_sqr: float, bounding_box_radius: float,
                 texture_count: int, flags: int, cache_size: int,
                 texture_names: List[str], vertices: List[Vector3],
                 normals: List[int], tex_coords: List[float], enclosed_shape: List[int],
                 surface_sides: List[int], indices_sides: List[List[int]]) -> None:

        self.magic = magic
        self.vertex_count = vertex_count
        self.adjunct_count = adjunct_count
        self.surface_count = surface_count
        self.indices_count = indices_count
        self.radius = radius
        self.radius_sqr = radius_sqr
        self.bounding_box_radius = bounding_box_radius
        self.texture_count = texture_count
        self.flags = flags
        self.cache_size = cache_size
        self.texture_names = texture_names
        self.vertices = vertices
        self.normals = normals
        self.tex_coords = tex_coords  
        self.enclosed_shape = enclosed_shape  
        self.surface_sides = surface_sides
        self.indices_sides = indices_sides
        
    @classmethod
    def read(cls, input_file: Path) -> 'Meshes':
        with open(input_file, "rb") as f:
            magic = read_binary_name(f, 16)
            vertex_count, adjunct_count, surface_count, indices_count = read_unpack(f, '<4I')
            radius, radius_sqr, bounding_box_radius = read_unpack(f, '<3f')
            texture_count, flags = read_unpack(f, '<2B')
            
            f.read(2)  # Padding
            cache_size, = read_unpack(f, '<I')
                                      
            texture_names = [read_binary_name(f, 32, 'ascii', 16) for _ in range(texture_count)]
            
            if vertex_count < Threshold.MESH_VERTEX_COUNT:
                vertices = Vector3.readn(f, vertex_count, '<')
            else:
                vertices = Vector3.readn(f, vertex_count + 8, '<')
                                        
            normals = list(read_unpack(f, f"{adjunct_count}B"))
            tex_coords = list(read_unpack(f, f"{adjunct_count * 2}f"))
            enclosed_shape = list(read_unpack(f, f"{adjunct_count}H"))
            surface_sides = list(read_unpack(f, f"{surface_count}B"))
            
            indices_per_surface = indices_count // surface_count
            indices_sides = [list(read_unpack(f, f"<{indices_per_surface}H")) for _ in range(surface_count)]
            
        return cls(
            magic, vertex_count, adjunct_count, surface_count, indices_count, 
            radius, radius_sqr, bounding_box_radius, 
            texture_count, flags, cache_size, texture_names, vertices, 
            normals, tex_coords, enclosed_shape, surface_sides, indices_sides
            )
                    
    def write(self, output_file: Path) -> None: 
        self.calculate_cache_size()
               
        with open(output_file, "wb") as f:
            write_binary_name(f, self.magic, 16) 
            write_pack(f, '<4I', self.vertex_count, self.adjunct_count, self.surface_count, self.indices_count)
            write_pack(f, '<3f', self.radius, self.radius_sqr, self.bounding_box_radius)
            write_pack(f, '<2B', self.texture_count, self.flags)
            
            f.write(b'\0' * 2)  # Padding
            write_pack(f, '<I', self.cache_size)
            
            for texture_name in self.texture_names:
                write_binary_name(f, texture_name, length = 32, padding = 16) 
                            
            for vertex in self.vertices:
                vertex.write(f, '<')

            if self.vertex_count >= Threshold.MESH_VERTEX_COUNT:
                for _ in range(8):
                    Default.VECTOR_3.write(f, '<')
                                                                        
            write_pack(f, f"{self.adjunct_count}B", *self.normals)
                        
            # Ensure Tex Coords is not larger than (Adjunct Count * 2)
            if len(self.tex_coords) > self.adjunct_count * 2:
                self.tex_coords = self.tex_coords[:self.adjunct_count * 2] 
                
            write_pack(f, f"{self.adjunct_count * 2}f", *self.tex_coords)
            write_pack(f, f"{self.adjunct_count}H", *self.enclosed_shape)
            write_pack(f, f"{self.surface_count}B", *self.surface_sides)

            # Each polygon requires four vertex indices (add the value 0 as the 4th index in case of a triangle)
            for indices_side in self.indices_sides:
                while len(indices_side) == Shape.TRIANGLE:
                    indices_side.append(0)
                write_pack(f, f"{len(indices_side)}H", *indices_side)

    @staticmethod       
    def align_size(value: int) -> int:
        return (value + 7) & ~7
    
    def calculate_cache_size(self) -> None:
        self.cache_size = 0
        
        self.cache_size += self.align_size(self.vertex_count * Vector3.binary_size())

        if self.vertex_count >= Threshold.MESH_VERTEX_COUNT:
            self.cache_size += self.align_size(8 * Vector3.binary_size())

        if self.flags & agiMeshSet.NORMALS:
            self.cache_size += self.align_size(self.adjunct_count * 3 * calc_size('B'))

        if self.flags & agiMeshSet.TEXCOORDS:
            self.cache_size += self.align_size(self.adjunct_count * Vector2.binary_size())

        if self.flags & agiMeshSet.COLORS:
            self.cache_size += self.align_size(self.adjunct_count * calc_size('I'))

        self.cache_size += self.align_size(self.adjunct_count * calc_size('H'))

        if self.flags & agiMeshSet.PLANES:
            self.cache_size += self.align_size(self.surface_count * Vector4.binary_size())

        self.cache_size += self.align_size(self.indices_count * calc_size('H'))
        self.cache_size += self.align_size(self.surface_count * calc_size('B'))
                                       
    def debug(self, output_file: Path, debug_folder: Path, debug_meshes: bool) -> None:
        if not debug_meshes:
            return
            
        if not debug_folder.exists():
            print(f"The output folder {debug_folder} does not exist. Creating it.")
            debug_folder.mkdir(parents = True, exist_ok = True)

        with open(debug_folder / output_file, "w") as f:
            f.write(str(self))
            
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_meshes_file: bool) -> None:
        if not debug_meshes_file:
            return
        
        if not input_file.exists():
            raise FileNotFoundError(f"The file {input_file} does not exist.")
            
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(output_file, "w") as out_f:
            out_f.write(str(cls.read(input_file)))
                
    @classmethod
    def debug_folder(cls, input_folder: Path, output_folder: Path, debug_meshes_folder: bool) -> None:
        if not debug_meshes_folder:
            return
        
        if not input_folder.exists():
            raise FileNotFoundError(f"The folder {input_folder} does not exist.")

        mesh_files = list(input_folder.glob("*.BMS"))
        
        if not mesh_files:
            raise FileNotFoundError(f"No .BMS files found in {input_folder}.")
            
        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        for file in mesh_files:
            output_file = output_folder / file.with_suffix('.txt').name
            cls.debug_file(file, output_file, debug_meshes_folder)
                                
    def __repr__(self) -> str:
        return f"""
MESH
    Magic: {self.magic}
    Vertex Count: {self.vertex_count}
    Adjunct Count: {self.adjunct_count}
    Surface Count: {self.surface_count}
    Indices Count: {self.indices_count}
    Radius: {self.radius:.2f}
    Radius Sqr: {self.radius_sqr:.2f}
    BoundingBox Radius: {self.bounding_box_radius:.2f}
    Texture Count: {self.texture_count}
    Flags: {self.flags}
    Cache Size: {self.cache_size}\n
    Texture Names: {self.texture_names}\n
    Vertices: {self.vertices}\n
    Normals: {self.normals}\n
    Tex Coords: {', '.join(f'{coord:.2f}' for coord in self.tex_coords)}\n
    Enclosed Shape: {self.enclosed_shape}\n
    Surface Sides: {self.surface_sides}\n
    Indices Sides: {self.indices_sides}\n
    """
             
################################################################################################################               
################################################################################################################   
#! ======================= DLP CLASSES ======================= !#


class DLPVertex: 
    def __init__(self, id: int, normal: Vector3, uv: Vector2, color: int) -> None:
        self.id = id
        self.normal = normal
        self.uv = uv
        self.color = color
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLPVertex':
        id, = read_unpack(f, '>H')
        normal = Vector3.read(f, '>')
        uv = Vector2.read(f, '>')
        color, = read_unpack(f, '>I')       
        return cls(id, normal, uv, color)
    
    def write(self, f: BinaryIO) -> None:
        write_pack(f, '>H', self.id)
        self.normal.write(f, '>')    
        self.uv.write(f, '>')       
        write_pack(f, '>I', self.color)
           
    def __repr__(self) -> str:
        return f"""
            Id: {self.id}
            Normal: {self.normal}
            UV: {self.uv}
            Color: {self.color}
            """
    
            
class DLPPatch:
    def __init__(self, s_res: int, t_res: int, flags: int, r_opts: int, 
                 material_index: int, texture_index: int, physics_index: int, 
                 vertices: List[DLPVertex], name: str) -> None:
        
        self.s_res = s_res
        self.t_res = t_res
        self.flags = flags
        self.r_opts = r_opts
        self.material_index = material_index
        self.texture_index = texture_index
        self.physics_index = physics_index
        self.vertices = vertices
        self.name = name
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLPPatch':
        s_res, t_res = read_unpack(f, '>2H')
        flags, r_opts = read_unpack(f, '>2H')
        material_index, texture_index, physics_index = read_unpack(f, '>3H')        
        vertices = [DLPVertex.read(f) for _ in range(s_res * t_res)]
        name_length, = read_unpack(f, '>I')
        name = read_binary_name(f, name_length)
        return cls(s_res, t_res, flags, r_opts, material_index, texture_index, physics_index, vertices, name)
    
    def write(self, f: BinaryIO) -> None:
        write_pack(f, '>2H', self.s_res, self.t_res) 
        write_pack(f, '>2H', self.flags, self.r_opts)
        write_pack(f, '>3H', self.material_index, self.texture_index, self.physics_index)
        
        for vertex in self.vertices:
            vertex.write(f)
            
        write_pack(f, '>I', len(self.name))        
        write_binary_name(f, self.name)
        
    def __repr__(self) -> str:
        return f"""
    Patch:
        S Res: {self.s_res}
        T Res: {self.t_res}
        Flags: {self.flags}
        R Opts: {self.r_opts}
        Material Index: {self.material_index}
        Texture Index: {self.texture_index}
        Physics Index: {self.physics_index}
        Name: {self.name}
        Vertex: {self.vertices}
        """


class DLPGroup:
    def __init__(self, name: str, num_vertices: int, num_patches: int, 
                 vertex_indices: tuple[int, ...], patch_indices: tuple[int, ...]) -> None:
        
        self.name = name
        self.num_vertices = num_vertices
        self.num_patches = num_patches
        self.vertex_indices = vertex_indices
        self.patch_indices = patch_indices
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLPGroup':
        name_length, = read_unpack(f, '>B')
        name = read_binary_name(f, name_length)        
        num_vertices, num_patches = read_unpack(f, '>2I')        
        vertex_indices = [read_unpack(f, '>H')[0] for _ in range(num_vertices)]
        patch_indices = [read_unpack(f, '>H')[0] for _ in range(num_patches)]     
        return cls(name, num_vertices, num_patches, vertex_indices, patch_indices)

    def write(self, f: BinaryIO) -> None:
        write_pack(f, '>B', len(self.name))
        write_binary_name(f, self.name)        
        write_pack(f, '>2I', self.num_vertices, self.num_patches)
        write_pack(f, f'>{self.num_vertices}H', *self.vertex_indices)
        write_pack(f, f'>{self.num_patches}H', *self.patch_indices)
        
    def __repr__(self) -> str:
        return f"""
    Group:
        Name: {self.name}
        Num Vertices: {self.num_vertices}
        Num Patches: {self.num_patches}
        Vertex Indices: {self.vertex_indices}
        Patch Indices: {self.patch_indices}
        """


class DLP:
    def __init__(self, magic: str, num_groups: int, num_patches: int, num_vertices: int, 
                 groups: List[DLPGroup], patches: List[DLPPatch], vertices: List[Vector3]) -> None:
        
        self.magic = magic
        self.num_groups = num_groups
        self.num_patches = num_patches
        self.num_vertices = num_vertices
        self.groups = groups
        self.patches = patches
        self.vertices = vertices 
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLP':
        magic = read_binary_name(f, 4)  # DLP7          
        num_groups, num_patches, num_vertices = read_unpack(f, '>3I')
        groups = [DLPGroup.read(f) for _ in range(num_groups)]
        patches = [DLPPatch.read(f) for _ in range(num_patches)]
        vertices = Vector3.readn(f, num_vertices, '>')
        return cls(magic, num_groups, num_patches, num_vertices, groups, patches, vertices)

    def write(self, output_file: str, set_dlp: bool) -> None:
        if not set_dlp:
            return
        
        with open(output_file, "wb") as f:
            write_binary_name(f, self.magic) 
            write_pack(f, '>3I', self.num_groups, self.num_patches, self.num_vertices)      
            
            for group in self.groups:
                group.write(f)
                      
            for patch in self.patches:
                patch.write(f)    

            for vertex in self.vertices: 
                vertex.write(f, '>') 
                                    
    @staticmethod          
    def debug_file(input_file: Path, output_file: Path, debug_dlp_file: bool) -> None:
        if not debug_dlp_file:
            return
        
        if not input_file.exists():
            raise FileNotFoundError(f"The file {input_file} does not exist.")

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)
        
        with open(input_file, "rb") as in_f:
            dlp_data = DLP.read(in_f)

        with open(output_file, "w") as out_f:
            out_f.write(repr(dlp_data))
            
        print(f"Processed {input_file.name} to {output_file.name}")
             
    @staticmethod
    def debug_folder(input_folder: Path, output_folder: Path, debug_dlp_folder: bool) -> None:
        if not debug_dlp_folder:
            return
        
        if not input_folder.exists():
            raise FileNotFoundError(f"The folder {input_folder} does not exist.")

        dlp_files = list(input_folder.glob("*.DLP"))
        
        if not dlp_files:
            raise FileNotFoundError(f"No .DLP files found in {input_folder}.")
        
        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        for file in dlp_files:
            output_file = output_folder / file.with_suffix(".txt").name
            DLP.debug_file(file, output_file, debug_dlp_folder)     

            print(f"Processed {file.name} to {output_file.name}")    
                                                        
    def __repr__(self) -> str:
        return f"""
DLP
    Magic: {self.magic}
    Num Groups: {self.num_groups}
    Num Patches: {self.num_patches}
    Num Vertices: {self.num_vertices}\n
    {self.groups}\n
    {self.patches}\n
    Vertices: 
        {self.vertices}
    """
            
################################################################################################################               
################################################################################################################     
#! ======================= COMMON HELPER FUNCTIONS ======================= !#


def calculate_min(vertices: List[Vector3]) -> Vector3:
    return Vector3(
        min(vertex.x for vertex in vertices),
        min(vertex.y for vertex in vertices),
        min(vertex.z for vertex in vertices)
    )


def calculate_max(vertices: List[Vector3]) -> Vector3:
    return Vector3(
        max(vertex.x for vertex in vertices), 
        max(vertex.y for vertex in vertices), 
        max(vertex.z for vertex in vertices)
        )


def calculate_center(vertices: List[Vector3]) -> Vector3:
    return sum(vertices, Vector3(0, 0, 0)) / len(vertices)


def calculate_center_tuples(vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    return (sum((Vector3.from_tuple(vertex) for vertex in vertices), Vector3(0, 0, 0)) / len(vertices)).to_tuple()


def calculate_radius(vertices: List[Vector3], center: Vector3) -> float:
    return max(vertex.Dist(center) for vertex in vertices)


def calculate_radius_squared(vertices: List[Vector3], center: Vector3) -> float:
    return max(vertex.Dist2(center) for vertex in vertices)


def calculate_extrema(vertices, coord_indexes = (0, 2)) -> Tuple[float, float, float, float]:
    min_values = [min(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    max_values = [max(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    return min_values + max_values


def calculate_bounding_box_radius(vertices: List[Vector3]) -> float:
    return (calculate_max(vertices) - calculate_min(vertices)).Mag() / 2  


def calc_normal(a: Vector3, b: Vector3, c: Vector3) -> Vector3:
    try:
        return (c - b).Cross(a - b).Normalize()
    except:
        return Vector3(0, 1, 0)


def sort_coordinates(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    max_x_coord = max(vertex_coordinates, key = lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key = lambda coord: coord[0])
    
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]

################################################################################################################? 

def read_binary_name(f, length: int = None, encoding: str = "ascii", padding: int = 0) -> str:
    name_data = bytearray()
    
    if length is None:
        while True:
            char = f.read(1)
            if char == b"\0" or not char:
                break
            name_data.extend(char)
            
    else:
        name_data = bytearray(f.read(length))
        null_pos = name_data.find(b'\0')
        
        if null_pos != -1:
            name_data = name_data[:null_pos]
        
        if padding > 0:
            f.read(padding)
    
    return name_data.decode(encoding)


def write_binary_name(f, name: str, length: int = None, encoding: str = "ascii", padding: int = 0, terminate: bool = False) -> None:
    name_data = name.encode(encoding)
    
    if length is not None:
        name_data = name_data[:length].ljust(length, b"\0")
        
    elif terminate:
        name_data += b'\0'
    
    f.write(name_data)
    
    if padding > 0:
        f.write(b"\0" * padding)


def transform_coordinate_system(vertex: Vector3, blender_to_game: bool = False, game_to_blender: bool = False) -> Tuple[float, float, float]:
    if blender_to_game and game_to_blender:
        raise ValueError("Both transformation modes cannot be 'True' at the same time.")
 
    elif blender_to_game:
        x, y, z = vertex.x, vertex.z, -vertex.y
        
    elif game_to_blender:
        x, y, z = vertex.x, -vertex.z, vertex.y
        
    else:
        raise ValueError("One of the transformation modes must be 'True'.")
    
    return x, y, z


def open_with_notepad_plus(filename: Path) -> None:
    possible_paths = [
        r"C:\Program Files\Notepad++\notepad++.exe",
        r"C:\Program Files (x86)\Notepad++\notepad++.exe"
    ]

    # Check if Notepad++ is in the PATH
    notepad_plus_exe = shutil.which("notepad++.exe")
    
    if notepad_plus_exe:
        subprocess.Popen([notepad_plus_exe, filename])
        print("Opening file with Notepad++ from PATH.")
        return

    # If Notepad++ is not in PATH, try the hardcoded paths
    for path in possible_paths:
        subprocess.Popen([path, filename])
        print(f"Opening file with Notepad++ from hardcoded path: {path}")
        return

    # Final fallback to classic Notepad
    subprocess.Popen(["notepad.exe", filename])
    print("Notepad++ not found, opening file with Notepad.")

################################################################################################################ 
################################################################################################################               
#! ======================= CREATE MESH ======================= !#


def compute_uv(bound_number: int, tile_x: int = 1, tile_y: int = 1, angle_degrees: float = 0.0) -> List[float]:
    
    center_x, center_y = 0.5, 0.5

    coords = [
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1)
    ]

    def rotate_point(x: float, y: float, angle: float) -> Tuple[float, float]:
        rad = math.radians(angle)
        rotated_x = x * math.cos(rad) - y * math.sin(rad)
        rotated_y = x * math.sin(rad) + y * math.cos(rad)
        return rotated_x, rotated_y
    
    def adjust_and_rotate_coords(coords: List[Tuple[float, float]], angle: float) -> List[float]:
        adjusted_coords = []
        for x, y in coords:
            x, y = rotate_point(x - center_x, y - center_y, angle)
            adjusted_coords.extend([(x + center_x) * tile_x, (y + center_y) * tile_y])
        return adjusted_coords
    
    if "entries" not in texcoords_data:
        texcoords_data["entries"] = {}
        
    texcoords_data["entries"][bound_number] = {"tile_x": tile_x, "tile_y": tile_y, "angle_degrees": angle_degrees}

    return adjust_and_rotate_coords(coords, angle_degrees)
        

def determine_mesh_folder_and_filename(cell_id: int, texture_name: List[str]) -> Tuple[Path, str]:
    if cell_id < Threshold.CELL_TYPE_SWITCH:
        target_folder = Folder.SHOP_MESH_LANDMARK
    else:
        target_folder = Folder.SHOP_MESH_CITY
                
    target_folder.mkdir(parents = True, exist_ok = True)
        
    if any(name.startswith(Texture.WATER) for name in texture_name):
        mesh_filename = f"CULL{cell_id:02d}_A2.bms"
    else:
        mesh_filename = f"CULL{cell_id:02d}_H.bms"

    return target_folder, mesh_filename

           
def save_mesh(
    texture_name: str, texture_indices: List[int] = [1], 
    vertices: List[Vector3] = vertices, polys: List[Polygon] = polys, 
    normals: List[int] = None, tex_coords: List[float] = None, 
    randomize_textures: bool = randomize_textures, random_textures: List[str] = random_textures, 
    debug_meshes: bool = debug_meshes) -> None:
            
    poly = polys[-1]  # Get the last polygon added
    
    cell_id = poly.cell_id
    target_folder, mesh_filename = determine_mesh_folder_and_filename(cell_id, texture_name)
    
    if randomize_textures:
        texture_name = [random.choice(random_textures)] 
        
    texture_names.append(texture_name[0])
    
    mesh = initialize_mesh(vertices, [poly], texture_indices, texture_name, normals, tex_coords)
    mesh.write(target_folder / mesh_filename)
    
    if debug_meshes:
        mesh.debug(Path(mesh_filename).with_suffix(".txt"), Folder.DEBUG_RESOURCES / "MESHES" / MAP_FILENAME, debug_meshes)


def initialize_mesh(
    vertices: List[Vector3], polys: List[Polygon], texture_indices: List[int], 
    texture_name: List[str], normals: List[int] = None, tex_coords: List[float] = None) -> Meshes:
    
    magic = "3HSM"    
    flags = agiMeshSet.TEXCOORDS_AND_NORMALS
    cache_size = 0
       
    shapes = [[vertices[i] for i in poly.vertex_index] for poly in polys] 
    coordinates = [coord for shape in shapes for coord in shape]
        
    radius = calculate_radius(coordinates, Default.VECTOR_3)  # Use Local Offset for the Center (this is not the case for the Bound files)
    radiussq = calculate_radius_squared(coordinates, Default.VECTOR_3)
    bounding_box_radius = calculate_bounding_box_radius(coordinates)    
    
    vertex_count = len(coordinates)
    adjunct_count = len(coordinates)
    surface_count = len(texture_indices)   
    texture_count = len(texture_name)
    
    # Each polygon requires four indices 
    if len(coordinates) in [Shape.QUAD, Shape.TRIANGLE]: 
        indices_count = surface_count * 4

    enclosed_shape = list(range(adjunct_count))
    normals = normals or [2] * adjunct_count  # 2 is the default value
    tex_coords = tex_coords or [1.0 for _ in range(adjunct_count * 2)]  # tile x and y once if no tex coords are provided
    indices_sides = [list(range(i, i + len(shape))) for i, shape in enumerate(shapes, start = 0)]
  
    return Meshes(
        magic, vertex_count, adjunct_count, surface_count, indices_count, 
        radius, radiussq, bounding_box_radius, 
        texture_count, flags, cache_size,
        texture_name, coordinates, normals, tex_coords, 
        enclosed_shape, texture_indices, indices_sides
        )

################################################################################################################               
################################################################################################################  
#! ======================= ADVANCED VECTOR CALCULATIONS ======================= !#


def ensure_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    vertex_1, vertex_2, vertex_3 = vertex_coordinates
    
    normal = compute_normal(vertex_1, vertex_2, vertex_3)
    reference_up = np.array([0, 1, 0])
    
    dot_product = np.dot(normal, reference_up)
    
    if dot_product < 0: # Clockwise --> swap the order of the vertices
        return [vertex_1, vertex_3, vertex_2]
    else:               # Counterclockwise --> no changes needed
        return [vertex_1, vertex_2, vertex_3]
    
    
def compute_normal(vertex_1: Vector3, vertex_2: Vector3, vertex_3: Vector3) -> np.ndarray:
    v1 = np.array(vertex_2) - np.array(vertex_1)
    v2 = np.array(vertex_3) - np.array(vertex_1)
    normal = np.cross(v1, v2)
    return normal / np.linalg.norm(normal)


def ensure_quad_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    normal = compute_normal(*vertex_coordinates[:3])
    
    # Use Gram-Schmidt process to get two orthogonal vectors on the plane
    basis_1 = np.array(vertex_coordinates[1]) - np.array(vertex_coordinates[0])
    basis_1 -= np.dot(basis_1, normal) * normal
    basis_1 /= np.linalg.norm(basis_1)
    basis_2 = np.cross(normal, basis_1)

    # Project vertices onto the plane defined by the normal
    projections = [
        (np.dot(vertex, basis_1), np.dot(vertex, basis_2))
        for vertex in vertex_coordinates
        ]

    # Compute the centroid of the projected points
    centroid = np.mean(projections, axis = 0)
    
    # Compute angles of vertices relative to centroid
    delta = np.array(projections) - centroid
    angles = np.arctan2(delta[:, 1], delta[:, 0])
    
    # Sort vertices based on these angles
    sorted_indices = np.argsort(angles)
    
    return [vertex_coordinates[i] for i in sorted_indices]


def compute_plane_edgenormals(vertex_1: Vector3, vertex_2: Vector3, vertex_3: Vector3):     
    plane_normal = compute_normal(vertex_1, vertex_2, vertex_3)
    
    plane_distance = -np.dot(plane_normal, vertex_1)

    plane_normal = np.round(plane_normal, 3)
    plane_distance = round(plane_distance, 3)

    return plane_normal, plane_distance


def compute_edges(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    vertices = [np.array([vertex[0], 0, vertex[2]]) for vertex in vertex_coordinates]
    plane_normal, _ = compute_plane_edgenormals(*vertices[:3]) 

    num_verts = len(vertices)  
        
    plane_edges = []

    abs_plane_x = abs(plane_normal[0])
    abs_plane_y = abs(plane_normal[1])
    abs_plane_z = abs(plane_normal[2])

    negate = 1.0

    # TODO: Refactor
    if abs_plane_x < abs_plane_y or abs_plane_x < abs_plane_z:
        if abs_plane_y < abs_plane_x or abs_plane_y < abs_plane_z:
            if plane_normal[2] < 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[1] * negate, D[0] * negate, -np.dot([-D[1], D[0]], [A[0], A[1]])]))
        else:
            if plane_normal[1] > 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[2] * negate, D[0] * negate, -np.dot([-D[2], D[0]], [A[0], A[2]])]))
    else:
        if plane_normal[0] < 0.0:
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
    
    # All shapes must always have 4 vectors
    if len(vertices) == Shape.TRIANGLE:
        edges.append(Default.VECTOR_3)
    
    return edges

################################################################################################################               
################################################################################################################ 
#! ======================= CREATE POLYGON ======================= !#


def check_bound_numbers(polys: List[Polygon]) -> None:
    found_one = False
    
    for poly in polys[1:]:  # Skip the filler Polygon with Bound Number 0 
        if poly.cell_id <= 0 or poly.cell_id == Threshold.CELL_TYPE_SWITCH or poly.cell_id >= Threshold.VERTEX_INDEX_COUNT:
            error_message = f"""
            ***ERROR***
            - Polygon with "bound_number =  {poly.cell_id}" is not valid. 
            - Bound Number must be between 1 and 199, and 201 and 32766.
            """
            raise ValueError(error_message)
        
        if poly.cell_id == 1:
            found_one = True

    if not found_one:
        error_message = f"""
        ***ERROR***
        - There must be at least one Polygon with Bound Number 1 (this was not found).
        """
        raise ValueError(error_message)

    
def check_shape_type(vertex_coordinates: List[Vector3]) -> None:
    if vertex_coordinates is None:
        error_message = """
        ***ERROR***
        Vertex Coordinates cannot be None.
        A valid list of vertex coordinates must be provided for polygon creation.
        """
        raise ValueError(error_message)

    if len(vertex_coordinates) not in (Shape.TRIANGLE, Shape.QUAD):
        error_message = """
        ***ERROR***
        Unsupported number of vertices.
        You must either set 3 or 4 vertex coordinates per polygon.
        """
        raise ValueError(error_message)


def process_winding(vertex_coordinates: List[Vector3], fix_faulty_quads: bool) -> List[Vector3]:
    if len(vertex_coordinates) == Shape.TRIANGLE:
        return ensure_ccw_order(vertex_coordinates)
    
    elif len(vertex_coordinates) == Shape.QUAD and fix_faulty_quads:
        return ensure_quad_ccw_order(vertex_coordinates)
    
    return vertex_coordinates  


def process_flags(vertex_coordinates: List[Vector3], flags: int) -> int:
    if flags is not None:
        return flags  
    
    if len(vertex_coordinates) == Shape.QUAD:
        return PlaneEdgesWinding.QUAD_Z_AXIS
    
    elif len(vertex_coordinates) == Shape.TRIANGLE:
        return PlaneEdgesWinding.TRIANGLE_Z_AXIS
    
    
    
def update_cruise_start_position(vertex_coordinates: List[Vector3]) -> None:
    global cruise_start_position
    x, y, z = calculate_center_tuples(vertex_coordinates)
    cruise_start_position = (x, y + 15, z)
    
    
def create_polygon(
    bound_number: int, vertex_coordinates: List[Vector3], 
    material_index: int = 0, cell_type: int = 0, flags: int = None, 
    plane_edges: List[Vector3] = None, wall_side: str = None, sort_vertices: bool = False,
    hud_color: str = Color.ROAD, minimap_outline_color: str = minimap_outline_color, 
    always_visible: bool = True, fix_faulty_quads: bool = fix_faulty_quads, base: bool = False) -> None:

    # Vertex indices
    base_vertex_index = len(vertices)
    
    # Store the Polygon Data for Blender (before any manipulation)
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
    
    check_shape_type(vertex_coordinates)

    # Winding & Flags
    vertex_coordinates = process_winding(vertex_coordinates, fix_faulty_quads)
    flags = process_flags(vertex_coordinates, flags)
     
    # Sorting        
    if sort_vertices: 
        vertex_coordinates = sort_coordinates(vertex_coordinates)
        
    # Base polygon               
    if base:
        update_cruise_start_position(vertex_coordinates)
          
    # Plane Edges    
    if plane_edges is None:
        plane_edges = compute_edges(vertex_coordinates) 
        
    # Plane Normals
    if wall_side is None:
        plane_normal, plane_distance = compute_plane_edgenormals(*vertex_coordinates[:3])
    else:
        # Wall with varying X and Y coordinates
        if (max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates) > 0.1 and
            max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
            abs(max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates)) <= 0.15):

            if wall_side == "outside":
                corners = [0, 0, -1, max(coord[2] for coord in vertex_coordinates)]
            elif wall_side == "inside":
                corners = [0, 0, 1, -max(coord[2] for coord in vertex_coordinates)]
            
            plane_normal, plane_distance = corners[:3], corners[3]
            
        # Wall with varying Z and Y coordinates                               
        elif (abs(max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates)) <= 0.15 and
              max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
              max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates) > 0.1):

            if wall_side == "outside":
                corners = [-1, 0, 0, min(coord[0] for coord in vertex_coordinates)]
            elif wall_side == "inside":
                corners = [1, 0, 0, -min(coord[0] for coord in vertex_coordinates)]
                
            plane_normal, plane_distance = corners[:3], corners[3]

    if isinstance(plane_normal, np.ndarray):
        plane_normal = Vector3(*plane_normal.tolist())
        
    elif isinstance(plane_normal, list):
        plane_normal = Vector3(*plane_normal)
        
    # Finalize Polygon
    new_vertices = [Vector3(*coord) for coord in vertex_coordinates]
    vertices.extend(new_vertices)
    
    vertex_indices = [base_vertex_index + i for i in range(len(new_vertices))]
            
    poly = Polygon(
        bound_number, material_index, flags, vertex_indices, 
        plane_edges, plane_normal, plane_distance, 
        cell_type, always_visible
        )
    
    polys.append(poly)
        
    # Save HUD data
    hud_fill = hud_color is not None
    hudmap_vertices.append(vertex_coordinates)
    hudmap_properties[len(hudmap_vertices) - 1] = (hud_fill, hud_color, minimap_outline_color, str(bound_number))
    
################################################################################################################               
################################################################################################################  
#! =======================CREATING YOUR MAP======================= !#


def user_notes():
    """ 
    Find some Polygons and Textures examples below this text
    You can already run the script and create the Test Map yourself
    
    If you're setting a Quad, make sure the vertices are in the correct order (both clockwise and counterclockwise are OK)
    If you're unsure, set "sort_vertices = True" in the "create_polygon()" function
    
    The Material Index (an optional variable) defaults to 0 (normal road friction). You can use the Material class constants    
    Note: you can also set custom Material / Physics Properties (search for: "custom_physics" in this script)
    
    Texture (UV) mapping examples:
    "tex_coords = compute_uv(bound_number = 1, tile_x = 5, tile_y = 2, angle_degrees = 0)"
    "tex_coords = compute_uv(bound_number = 2, tile_x = 4, tile_y = 8, angle_degrees = 90)"
        
    The variable "normals" (an optional variable) in the function "save_mesh()" makes the texture edges darker / lighter 
    If you're setting a Quad, you can for example do: "normals = [40, 2, 50, 1]"
    Where 2 is the default value. It is recommended to try different values to get an idea of the result in-game
        
    To properly set up the AI paths, adhere to the following for "bound_number = x":
    Open Areas: 1 - 199
    Roads: 201 - 859
    Intersections: 860 +
    
    IMPORTANT:
    The "bound_number" can not be equal to 0, 200, be negative, or be greater than 32767
    In addition, there must always exist one polygon with "bound_number = 1"
    
    If you wish to modify or add a Cell, Material, Texture or HUD constant and you are importing / exporting to Blender,
    then you must also modify the respective IMPORTS and EXPORTS. For Cells, this would be "CELL_IMPORT" and "CELL_EXPORT"
    """
    
    
class Room:
    DEFAULT = 0x0
    TUNNEL = 0x1
    INDOORS = 0x2
    DRIFT = 0x4
    UNKNOWN_8 = 0x8
    UNKNOWN_10 = 0x10
    FORCE_Z_BUFFER = 0x20
    NO_SKIDS = 0x40
    FOG = 0x80
    UNKNOWN_100 = 0x100
    
    
class Material:
    DEFAULT = 0
    GRASS = 87
    WATER = 91
    STICKY = 97         # Custom
    NO_FRICTION = 98    # Custom
    

class Texture:
    SNOW = "SNOW"
    WOOD = "T_WOOD"
    WATER = "T_WATER"
    WATER_WINTER = "T_WATER_WIN"
    GRASS = "T_GRASS"
    GRASS_WINTER = "T_GRASS_WIN"
    GRASS_BASEBALL = "24_GRASS"

    SIDEWALK = "SDWLK2"
    ZEBRA_CROSSING = "RWALK"
    INTERSECTION = "RINTER"

    FREEWAY = "FREEWAY2"
    ROAD_1_LANE = "R2"
    ROAD_2_LANE = "R4"
    ROAD_3_LANE = "R6"

    BRICKS_MALL = "OT_MALL_BRICK"
    BRICKS_SAND = "OT_SHOP03_BRICK"
    BRICKS_GREY = "CT_FOOD_BRICK"

    GLASS = "R_WIN_01"
    STOP_SIGN = "T_STOP"
    BARRICADE = "T_BARRICADE"
    CHECKPOINT = "CHECK04"
    BUS_RED_TOP = "VPBUSRED_TP_BK"
    
    # Custom Textures (see: MM1-Map-Editor \ Custom Textures)
    LAVA = "T_WATER_LAVA"
    BARRICADE_RED_BLACK = "T_RED_BLACK_BARRICADE"


#! ==============================TEST_CITY============================== #*
#! ==============================MAIN AREA============================== #*

# Colored Checkpoints
create_polygon(
    bound_number = 99,
    vertex_coordinates = [
        (-25.0, 0.0, 85.0),
        (25.0, 0.0, 85.0),
        (25.0, 0.0, 70.0),
        (-25.0, 0.0, 70.0)])

save_mesh(
    texture_name = [Texture.CHECKPOINT],
    tex_coords = compute_uv(bound_number = 99, tile_x = 5, tile_y = 1, angle_degrees = 0))

# Road with Buildings
create_polygon(
    bound_number = 201,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
        (50.0, 0.0, 70.0),
        (50.0, 0.0, -70.0),
        (-50.0, 0.0, -70.0)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE], normals = [40, 2, 50, 1],
    tex_coords = compute_uv(bound_number = 201, tile_x = 10, tile_y = 10, angle_degrees = 45))

# Grass Area 
create_polygon(
	bound_number = 861,
	material_index = Material.GRASS,
	vertex_coordinates = [
        (-50.0, 0.0, -70.0),
		(10.0, 0.0, -70.0),
        (10.0, 0.0, -130.0),
		(-50.0, 0.0, -130.0)],
        hud_color = Color.GRASS)

save_mesh(
    texture_name = [Texture.GRASS_BASEBALL], 
    tex_coords = compute_uv(bound_number = 861, tile_x = 7, tile_y = 7, angle_degrees = 90))

# Brown Grass Area
create_polygon(
	bound_number = 202,
	material_index = Material.GRASS,
	vertex_coordinates = [
		(10.0, 0.0, -70.0),
        (50.0, 0.0, -70.0),
		(50.0, 0.0, -130.0),
        (10.0, 0.0, -130.0)],
        hud_color = Color.GRASS)

save_mesh(
    texture_name = [Texture.GRASS_WINTER], 
    tex_coords = compute_uv(bound_number = 202, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Snow Area
create_polygon(
	bound_number = 1,
    cell_type = Room.NO_SKIDS,
    material_index = Material.NO_FRICTION,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)],
         hud_color = Color.SNOW)

save_mesh(
    texture_name = [Texture.SNOW], 
    tex_coords = compute_uv(bound_number = 1, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Barricade (Car) Area
create_polygon(
	bound_number = 862,
    cell_type = Room.TUNNEL,
	vertex_coordinates = [
		(50.0, 0.0, -70.0),
		(140.0, 0.0, -70.0),
		(140.0, 0.0, -140.0),
		(50.0, 0.0, -140.0)],
        hud_color = Color.RED_DARK)

save_mesh(
    texture_name = [Texture.BARRICADE_RED_BLACK], 
    tex_coords = compute_uv(bound_number = 862, tile_x = 50, tile_y = 50, angle_degrees = 0))

# Wood (Tree) Area
create_polygon(
	bound_number = 203,
	vertex_coordinates = [
		(50.0, 0.0, 70.0),
		(140.0, 0.0, 70.0),
		(140.0, 0.0, -70.0),
		(50.0, 0.0, -70.0)],
        hud_color = Color.WOOD)

save_mesh(
    texture_name = [Texture.WOOD], 
    tex_coords = compute_uv(bound_number = 203, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Water (Sailboat) Area
create_polygon(
	bound_number = 2,
    cell_type = Room.DRIFT,
	material_index = Material.WATER,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)],
        hud_color = Color.WATER)

save_mesh(
    texture_name = [Texture.WATER_WINTER], 
    tex_coords = compute_uv(bound_number = 2, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Diagonal Grass Road 
create_polygon(
    bound_number = 863,
	hud_color = Material.GRASS,
    vertex_coordinates = [
        (-50.0, 0.0, 110.0),
		(-50.0, 0.0, 140.0),
		(140.0, 0.0, 70.0),
		(93.01, 0.0, 70.0)])

save_mesh(
    texture_name = [Texture.GRASS_BASEBALL],
    tex_coords = compute_uv(bound_number = 863, tile_x = 10.0, tile_y = 10.0, angle_degrees = 90.0))

# Triangle Brick I 
create_polygon(
    bound_number = 204,
    cell_type = Room.NO_SKIDS,
    vertex_coordinates = [
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0),
        (-50.0, 0.0, 0.0)],
        hud_color = Color.YELLOW_LIGHT)

save_mesh(
    texture_name = [Texture.BRICKS_MALL],
    tex_coords = compute_uv(bound_number = 204, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Triangle Brick II
create_polygon(
    bound_number = 205,
    cell_type = Room.NO_SKIDS,
    vertex_coordinates = [
        (-50.0, 0.0, 140.0),
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0)],
        hud_color = Color.YELLOW_LIGHT)

save_mesh(
    texture_name = [Texture.BRICKS_MALL],
    tex_coords = compute_uv(bound_number = 205, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Huge Orange Hill 
create_polygon(
	bound_number = 3,
    cell_type = Room.DRIFT,
	vertex_coordinates = [
		(-50.0, 0.0, -210.0),
		(50.0, 0.0, -210.0),
		(50.0, 300.0, -1000.0),
		(-50.0, 300.0, -1000.0)],
        hud_color = Color.ORANGE)

save_mesh(
    texture_name = [Texture.LAVA], 
    tex_coords = compute_uv(bound_number = 3, tile_x = 10, tile_y = 100, angle_degrees = 90))


#! ============================== ORANGE BUILDING ============================== #*
# South Wall
create_polygon(
    bound_number = 4,
    always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -50.0),
        (10.0, 0.0, -50.0),
        (10.0, 30.0, -50.11),
        (-10.0, 30.0, -50.11)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 4, tile_x = 1, tile_y = 1, angle_degrees = 0))

# North Wall
create_polygon(
    bound_number = 5,
    always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -70.00),
        (-10.0, 30.0, -70.0),
        (10.0, 30.0, -70.0),
        (10.0, 0.0, -70.00)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 5, tile_x = 1, tile_y = 1, angle_degrees = 0))

# West Wall
create_polygon(
    bound_number = 6,
    always_visible = False,
    vertex_coordinates = [
        (-9.99, 30.0, -50.0),
        (-9.99, 30.0, -70.0),
        (-10.0, 0.0, -70.0),
        (-10.0, 0.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 6, tile_x = 1, tile_y = 1, angle_degrees = 0))

# East Wall
create_polygon(
    bound_number = 7,
    always_visible = False,
    vertex_coordinates = [
        (10.0, 0.0, -70.0),
        (9.9, 30.0, -70.0),
        (9.9, 30.0, -50.0),
        (10.0, 0.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 7, tile_x = 1, tile_y = 1, angle_degrees = 0))

# Rooftop
create_polygon(
    bound_number = 900,
    cell_type = Room.NO_SKIDS,
    material_index = Material.NO_FRICTION,
    vertex_coordinates = [
        (10.0, 30.0, -70.0),
        (-10.0, 30.0, -70.0),
        (-10.0, 30.0, -50.0),
        (10.0, 30.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 900, tile_x = 1, tile_y = 1, angle_degrees = 0))


#! ============================== BRIDGES ============================== #*
# Bridge I East
create_polygon(
	bound_number = 250,
	vertex_coordinates = [
		(-82.6, 0.0, -80.0),
		(-50.0, 0.0, -80.0),
		(-50.0, 0.0, -120.0),
		(-82.6, 0.0, -120.0)])
save_mesh(
    texture_name = [Texture.INTERSECTION], 
    tex_coords = compute_uv(bound_number = 250, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Road split
create_polygon(
	bound_number = 925,
	vertex_coordinates = [
		(-90.0, 14.75, -80.0),
		(-79.0, 14.75, -80.0),
		(-79.0, 14.75, -120.0),
		(-90.0, 14.75, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION], 
    tex_coords = compute_uv(bound_number = 925, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Bridge II West
create_polygon(
	bound_number = 251,
	vertex_coordinates = [
		(-119.01, 0.0, -80.0),
		(-90.0, 0.0, -80.0),
		(-90.0, 0.0, -120.0),
		(-119.01, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.GRASS], 
    tex_coords = compute_uv(bound_number = 251, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Road West of Bridge
create_polygon(
	bound_number = 252,
	vertex_coordinates = [
        (-160.0, 0.0, -80.0),
		(-119.1, 0.0, -80.0),
        (-119.1, 0.0, -120.0),
		(-160.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE], 
    tex_coords = compute_uv(bound_number = 252, tile_x = 5, tile_y = 3, angle_degrees = 0))

# Intersection West of Bridge
create_polygon(
	bound_number = 950,
	vertex_coordinates = [
        (-200.0, 0.0, -80.0),
		(-160.0, 0.0, -80.0),
        (-160.0, 0.0, -120.0),
		(-200.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION], 
    tex_coords = compute_uv(bound_number = 950, tile_x = 5, tile_y = 5, angle_degrees = 90))


#! ============================== ELEVATED AREA ============================== #*
# Road connected to Bridge Prop
create_polygon(
	bound_number = 501,
    base = False,
	vertex_coordinates = [
		(20.0, 30.0, 0.0),
        (50.0, 30.0, 0.0),
        (50.0, 12.0, -69.9),
        (20.0, 12.0, -69.9)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE], 
    tex_coords = compute_uv(bound_number = 501, tile_x = 3, tile_y = 2, angle_degrees = 90))

# Bricks Intersection
create_polygon(
	bound_number = 1100,
	vertex_coordinates = [
		(20.0, 30.0, 40.0),
        (50.0, 30.0, 40.0),
        (50.0, 30.0, 0.0),
        (20.0, 30.0, 0.0)])

save_mesh(
    texture_name = [Texture.BRICKS_GREY], 
    tex_coords = compute_uv(bound_number = 1100, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Red Bus Color
create_polygon(
	bound_number = 502,
	vertex_coordinates = [
		(-10.0, 30.0, 40.0),
        (20.0, 30.0, 40.0),
        (20.0, 30.0, 0.0),
        (-10.0, 30.0, 0.0)])

save_mesh(
    texture_name = [Texture.BUS_RED_TOP], 
    tex_coords = compute_uv(bound_number = 502, tile_x = 4, tile_y = 3, angle_degrees = 0))

create_polygon(
	bound_number = 503,
	vertex_coordinates = [
		(-10.0, 30.0, 0.0),
        (10.0, 30.0, 0.0),
        (10.0, 30.0, -50.0),
        (-10.0, 30.0, -50.0)])

save_mesh(
    texture_name = [Texture.GLASS], 
    tex_coords = compute_uv(bound_number = 503, tile_x = 5, tile_y = 12, angle_degrees = 0))


#! ============================== SPEEDBUMPS ============================== #*
# Speed Bump South
create_polygon(
	bound_number = 206,
	vertex_coordinates = [ 
     (50.00,0.00,-130.00), 
     (50.00,3.00,-135.00), 
     (-50.00,3.00,-135.00), 
     (-50.00,0.00,-130.00)],
    hud_color = Color.RED_LIGHT)

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 206, tile_x = 15, tile_y = 1, angle_degrees = 90))

# Speed Bump North
create_polygon(
	bound_number = 207,
	vertex_coordinates = [
		(-50.0, 3.0, -135.0),
		(50.0, 3.0, -135.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)],
         hud_color = Color.RED_LIGHT)

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 207, tile_x = 1, tile_y = 10, angle_degrees = 0))

# Triangle Side I
create_polygon(
	bound_number = 208,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(-50.01, 0.0, -130.0),
		(-50.0, 3.0, -135.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 208, tile_x = 30, tile_y = 30, angle_degrees = 90))

# Triangle Side II
create_polygon(
	bound_number = 209,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(50.01, 0.0, -130.0),
		(50.0, 3.0, -135.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 209, tile_x = 30, tile_y = 30, angle_degrees = 90))


#! ============================== CURVED FREEWAY ============================== #* 
create_polygon(
	bound_number = 2220,
	vertex_coordinates = [
		(-160.0, -0.00, -120.0),
		(-200.0, -0.00, -120.0),
		(-160.0, -3.0, -160.0)])

save_mesh(texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2220, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2221,
	vertex_coordinates = [
		(-200.0, -0.00, -120.0),
        (-160.0, -3.0, -160.0),
		(-200.0, -3.0, -160.0)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2221, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2222,
	vertex_coordinates = [
		(-160.0, -3.0, -160.0),
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2222, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2223,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0),
		(-191.82, -6.00, -223.82)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2223, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2224,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2224, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2225,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82),
		(-165.59, -9.00, -260.54)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2225, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2226,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2226, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2227,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54),
		(-127.21, -12.00, -286.30)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2227, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2228,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2228, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2229,
	vertex_coordinates = [
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30),
		(-90.0, -15.00, -294.48)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2229, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

# Intersection
create_polygon(
	bound_number = 924,
	vertex_coordinates = [
        (-90.0, -15.00, -254.51),
        (-79.0, -15.00, -254.51),
        (-79.0, -15.00, -294.48),
        (-90.0, -15.00, -294.48)])

save_mesh(
	texture_name = [Texture.INTERSECTION],
	tex_coords = compute_uv(bound_number = 924, tile_x = 5.0, tile_y = 5.0, angle_degrees = 0))

# Hill
create_polygon(
	bound_number = 923,
	vertex_coordinates = [
		(-79.0, -15.00, -254.51),
		(-90.0, -15.00, -254.51),
        (-90.0, 14.75, -120.0),
		(-79.0, 14.75, -120.0)],
	hud_color = Color.YELLOW_LIGHT)

save_mesh(
	texture_name = [Texture.ZEBRA_CROSSING],
	tex_coords = compute_uv(bound_number = 923, tile_x = 5.0, tile_y = 5.0, angle_degrees = 0))

################################################################################################################               
################################################################################################################ 
#! ======================= SETUP PREPARATION ======================= !#


def create_folders() -> None:
    FOLDER_STRUCTURE = [
        Folder.BASE / "build", 
        Folder.SHOP / "BMP16", 
        Folder.SHOP / "TEX16O", 
        Folder.SHOP / "TUNE", 
        Folder.SHOP / "MTL",
        Folder.SHOP / "CITY" / MAP_FILENAME,
        Folder.SHOP / "RACE" / MAP_FILENAME,
        Folder.SHOP / "BMS" / f"{MAP_FILENAME}CITY",
        Folder.SHOP / "BMS" / f"{MAP_FILENAME}LM",
        Folder.SHOP / "BND" / f"{MAP_FILENAME}CITY",
        Folder.SHOP / "BND" / f"{MAP_FILENAME}LM",
        Folder.BASE / "dev" / "CITY" / MAP_FILENAME,
        ]
    
    for path in FOLDER_STRUCTURE:
        path.mkdir(parents = True, exist_ok = True)

        
def create_map_info(output_file: Path, blitz_race_names: List[str], circuit_race_names: List[str], checkpoint_race_names: List[str]) -> None:
    with open (output_file, "w") as f:
        
        f.write(f"""
LocalizedName={MAP_NAME}
MapName={MAP_FILENAME}
RaceDir={MAP_FILENAME.lower()}
BlitzCount={len(blitz_race_names)}
CircuitCount={len(circuit_race_names)}
CheckpointCount={len(circuit_race_names)}
BlitzNames={'|'.join(blitz_race_names)}
CircuitNames={'|'.join(circuit_race_names)}
CheckpointNames={'|'.join(checkpoint_race_names)}
""")

    
def copy_custom_textures(input_folder: Path, output_folder: Path) -> None: 
    for custom_tex in input_folder.iterdir():
        shutil.copy(custom_tex, output_folder / custom_tex.name)
        
        
def copy_tune_mmcarsim_files(input_folder: Path, output_folder: Path) -> None:
    for file in input_folder.glob("*.MMCARSIM"):
        shutil.copy(file, output_folder)

            
def copy_dev_folder(input_folder: Path, output_folder: Path) -> None:
    shutil.rmtree(output_folder, ignore_errors = True)  
    shutil.copytree(input_folder, output_folder)
    
    dev_ai_files = input_folder / "CITY" / MAP_FILENAME
    shutil.rmtree(dev_ai_files, ignore_errors = True)
        
         
def edit_and_copy_mmbangerdata(bangerdata_properties: Dict[str, Dict[str, Union[int, str]]], 
                               input_folder: Path, output_folder: Path) -> None:
    
    for file in input_folder.glob("*.MMBANGERDATA"):
        if file.stem not in bangerdata_properties:
            shutil.copy(file, output_folder)
            
    for prop_key, properties in bangerdata_properties.items():
        banger_files = input_folder / f"{prop_key}.MMBANGERDATA"
        
        if banger_files.exists():
            with open(banger_files, "r") as f: 
                lines = f.readlines()

            for i, line in enumerate(lines):
                for key, new_value in properties.items():
                    if line.strip().startswith(key):
                        lines[i] = f'\t{key} {new_value}\n'
            
            tweaked_banger_files = output_folder / banger_files.name
            with open(tweaked_banger_files, "w") as f:
                f.writelines(lines)
                   
################################################################################################################               
################################################################################################################
#! ======================= EXT ======================= !#


def create_ext(output_file: Path, polygons: List[Vector3]) -> None:
    min_x, min_z, max_x, max_z = calculate_extrema(polygons)

    with open(output_file, "w") as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")
        
################################################################################################################               
################################################################################################################
#! ======================= ANIMATIONS ======================= !#

                             
def create_animations(output_file_main: Path, output_file_sub: Path,
                      animations_data: Dict[str, List[Tuple]], set_animations: bool) -> None: 
    
    if not set_animations:    
        return
    
    with open(output_file_main, "w", newline = "") as main_f:
        for anim in animations_data:
            csv.writer(main_f).writerow([f"anim_{anim}"])

            with open(output_file_sub / f"ANIM_{anim.upper()}.CSV", "w", newline = "") as anim_f:                    
                for coord in animations_data[anim]:
    
                    csv.writer(anim_f).writerow(coord)
                    
################################################################################################################               
################################################################################################################ 
#! ======================= RACES ======================= !#


CHECKPOINT_PREFIXES = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]

RACE_TYPE_TO_PREFIX = {
    RaceMode.BLITZ: "ABL",
    RaceMode.CIRCUIT: "CIR",
    RaceMode.CHECKPOINT: CHECKPOINT_PREFIXES
    }

RACE_TYPE_TO_EXTENSION = {
    RaceMode.BLITZ: ".B_",
    RaceMode.CIRCUIT: ".C_",
    RaceMode.CHECKPOINT: ".R_",
    }

REPLACE_VALUES = {        
    RaceMode.BLITZ:      [1, 2, 3, 4, 5, 6, 7, 8],   # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit
    RaceMode.CIRCUIT:    [1, 2, 3, 4, 5, 6, 7],      # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps
    RaceMode.CHECKPOINT: [1, 2, 3, 4, 5, 6]          # TimeofDay, Weather, Opponents, Cops, Ambient, Peds
}


def ordinal(n) -> str:
    if 10 <= n % 100 <= 13:
        return f"{n}th"
    
    return {
        1: f"{n}st",
        2: f"{n}nd",
        3: f"{n}rd",
}.get(n % 10, f"{n}th")


def write_mm_data_header():
    header = ",".join(
        ["Description"] + 2 * [
            "CarType", "TimeofDay", "Weather", "Opponents", "Cops", "Ambient", "Peds", "NumLaps", "TimeLimit", "Difficulty"
            ]
        )
    return header + "\n"


def determine_race_prefix(race_type: str, prefix: str, race_index: Optional[int] = None) -> str:
    if race_type == RaceMode.CHECKPOINT:
        return prefix
    else:
        return f"{prefix}{race_index}"
    
    
def fill_mm_data_values(race_type: str, custom_mm_data: List[Union[int, float]]) -> List[Union[int, float]]:
    default_values = [1] * 11
    replace_indices = REPLACE_VALUES.get(race_type, [])
    
    for index, custom_value in zip(replace_indices, custom_mm_data):
        default_values[index] = custom_value
        
    return default_values[:10]


def generate_mm_data_string(prefix: str, ama_filled_values: List[Union[int, float]], pro_filled_values: List[Union[int, float]]) -> str:
    ama_data = ",".join(map(str, ama_filled_values))
    pro_data = ",".join(map(str, pro_filled_values))
    return f"{prefix},{ama_data},{pro_data}\n"


def write_mm_data(output_file: str, configs: Dict[str, Dict], race_type: str, prefix: str) -> None:    
    with open(output_file, "w") as f:
        header = write_mm_data_header() 
        f.write(header)
        
        for race_index, config in configs.items():
            final_prefix = determine_race_prefix(race_type, prefix, race_index)     
                       
            ama_filled_values = fill_mm_data_values(race_type, config["mm_data"]["ama"])
            pro_filled_values = fill_mm_data_values(race_type, config["mm_data"]["pro"])
                        
            mm_data = generate_mm_data_string(final_prefix, ama_filled_values, pro_filled_values)
            f.write(mm_data)


def write_waypoints(output_file, waypoints, race_type: str, race_index: int, opp_num: int = None):
    with open(output_file, "w") as f:
        if opp_num is not None:
                        
            opp_waypoint_header = (f"This is your Opponent file for opponent number {opp_num}, in {race_type} race {race_index}\n")
            f.write(opp_waypoint_header)

            for waypoint in waypoints:
                opp_waypoints = ', '.join(map(str, waypoint[:3])) + f", {Width.MEDIUM}, {Rotation.AUTO}, 0, 0,\n"
                f.write(opp_waypoints)
                
        else:
            player_waypoint_header = (f"# This is your {ordinal(race_index)} {race_type} race Waypoint file\n")
            f.write(player_waypoint_header)
            
            for waypoint in waypoints:
                player_waypoints = ', '.join(map(str, waypoint)) + ", 0, 0,\n"
                f.write(player_waypoints)
                
                  
def write_section(f, title: str, data: str) -> None:
    f.write(f"\n{title}\n{data}\n")


def format_police_data(police_data: List[str], num_of_police: int) -> str:
    return "\n".join([str(num_of_police)] + police_data)


def format_opponent_data(opp_cars: Dict, race_type: str, race_index: int) -> str:
    return "\n".join(
        [f"{opp_car} OPP{opp_index}{race_type}{race_index}{RACE_TYPE_TO_EXTENSION[race_type]}{race_index}" for opp_index, opp_car in enumerate(opp_cars)]
        )


def format_exceptions(exceptions: Optional[List[List[Union[int, float]]]] = None, exceptions_count: Optional[int] = None) -> str:
    if exceptions is None:
        exceptions = []
        
    if exceptions_count is None:
        exceptions_count = len(exceptions)
        
    formatted_exceptions = "\n".join(" ".join(map(str, exception)) for exception in exceptions)
    
    return f"{exceptions_count}\n{formatted_exceptions}"


def prepare_aimap_data(config, race_type: str, race_index: int, opponents) -> tuple:
    traffic_density = config.get("traffic_density", 0.0)
        
    police_data = config["police"]
    num_of_police = config["num_of_police"]
    
    exceptions = config.get("exceptions", [])
    exception_count = config.get("num_of_exceptions", len(exceptions))

    exceptions_data_formatted = format_exceptions(exceptions, exception_count)
    police_data_formatted = format_police_data(police_data, num_of_police)
    opponent_data_formatted = format_opponent_data(opponents, race_type, race_index)
    
    return (traffic_density, exceptions_data_formatted, police_data_formatted, opponent_data_formatted)


def write_aimap(output_file: Path, traffic_density: float, exceptions_data_formatted, police_data_formatted, opponent_data_formatted, num_of_opponents: int) -> None:
    with open(output_file, "w") as f:
        
        template = f"""
# Ambient Traffic Density 
[Density] 
{traffic_density}

# Default Road Speed Limit 
[Speed Limit] 
45 

# Ambient Traffic Exceptions
# Rd Id, Density, Speed Limit 
"""
        f.write(template)
            
        write_section(f, "[Exceptions]", exceptions_data_formatted)
        write_section(f, "[Police]", police_data_formatted)
        write_section(f, "[Opponent]", f"{num_of_opponents}\n{opponent_data_formatted}")

            
def check_race_count(race_type: str, config) -> None:
    if race_type == RaceMode.CHECKPOINT:  
        if len(config) > Threshold.CHECKPOINT_RACE_COUNT:
            checkpoint_race_count_error = """
            ***ERROR***
            Number of Checkpoint races cannot be more than 12
            """
            raise ValueError(checkpoint_race_count_error)
    
    elif race_type == RaceMode.BLITZ or race_type == RaceMode.CIRCUIT:
        if len(config) > Threshold.BLITZ_AND_CIRCUIT_RACE_COUNT:
            race_count_error = """
            ***ERROR***
            Number of Blitz races and/or Circuit races cannot be more than 15
            """ 
            raise ValueError(race_count_error)
        
        
def check_waypoint_count(race_type: str, waypoints) -> None:
    if race_type == RaceMode.BLITZ:
        if len(waypoints) > Threshold.BLITZ_WAYPOINT_COUNT:
            blitz_waypoint_count_error = """
            ***ERROR***
            Number of waypoints for Blitz race cannot be more than 10
            """
            raise ValueError(blitz_waypoint_count_error)

              
def create_races(race_data: dict) -> None:
    for race_key, config in race_data.items():
        race_type, race_index = race_key.split("_", 1)
        race_index = int(race_index)
        
        player_waypoints = config["player_waypoints"]
        ai_map = config["aimap"]
        
        opponents = ai_map["opponents"]
        num_of_opponents = ai_map.get("num_of_opponents", len(opponents))  
                
        prepared_aimap_data = prepare_aimap_data(ai_map, race_type, race_index, opponents)
                                    
        file_prefix = f"{race_type}{race_index}"
        
        ai_map_file = Folder.SHOP_RACE_MAP / f"{file_prefix}.AIMAP_P"
        player_waypoint_file = Folder.SHOP_RACE_MAP / f"{file_prefix}WAYPOINTS.CSV"
        mm_data_file = Folder.SHOP_RACE_MAP / f"MM{race_type}DATA.CSV"
        
        # Safety Checks
        check_race_count(race_type, config)
        check_waypoint_count(race_type, player_waypoints)
        
        # Player Waypoints
        write_waypoints(player_waypoint_file, player_waypoints, race_type, race_index)
        
        # Opponent Waypoints
        for opp_index, opp_waypoints in enumerate(opponents.values()):
            opp_file_name = f"OPP{opp_index}{file_prefix}{RACE_TYPE_TO_EXTENSION[race_type]}{race_index}"
            opp_waypoint_file = Folder.SHOP_RACE_MAP / opp_file_name
            write_waypoints(opp_waypoint_file, opp_waypoints, race_type, race_index, opp_index)
        
        # MM DATA
        if race_type == RaceMode.CHECKPOINT:
            write_mm_data(mm_data_file, {race_index: config}, race_type, CHECKPOINT_PREFIXES[race_index])
        else:
            write_mm_data(mm_data_file, {race_index: config}, race_type, RACE_TYPE_TO_PREFIX[race_type])
            
        # AI MAP                
        write_aimap(ai_map_file, *prepared_aimap_data, num_of_opponents)

       
def create_cops_and_robbers(output_file: Path, cnr_waypoints: List[Tuple[float, float, float]]) -> None:
        filler = ",0,0,0,0,0,\n"
        header = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"
        
        with open(output_file, "w") as f:
            f.write(header)
            
            for i in range(0, len(cnr_waypoints), 3):
                f.write(", ".join(map(str, cnr_waypoints[i])) + filler) 
                f.write(", ".join(map(str, cnr_waypoints[i + 1])) + filler)
                f.write(", ".join(map(str, cnr_waypoints[i + 2])) + filler)
  
################################################################################################################               
################################################################################################################              
#! ======================= CELLS ======================= !#


def update_max_counts(row_length: int, max_warning_count: int, max_error_count: int) -> Tuple[int, int]:
    if Threshold.CELL_CHARACTER_WARNING <= row_length < Threshold.CELL_CHARACTER_LIMIT:
        max_warning_count = max(max_warning_count, row_length)
        
    elif row_length >= Threshold.CELL_CHARACTER_LIMIT:
        max_error_count = max(max_error_count, row_length)
        
    return max_warning_count, max_error_count


def check_row_size(max_warning_count: int, max_error_count: int) -> None:
    if Threshold.CELL_CHARACTER_WARNING <= max_warning_count < Threshold.CELL_CHARACTER_LIMIT:
        warning_message = f"""
        ***WARNING***
        Close to row character limit 254 in .CELLS file. 
        Maximum character count encountered is {max_warning_count}.
        To reduce the character count, consider setting "always_visible" to False for a few polygons.
        If the "cell_id" is e.g. 99 (2 characters), then it consumes 3 characters (2 + 1) in the CELLS file.
        *************\n
        """
        print(warning_message)
        
    elif max_error_count >= Threshold.CELL_CHARACTER_LIMIT:
        error_message = f"""
        ***ERROR***
        Character limit of 254 exceeded in .CELLS file.
        Maximum character count encountered is {max_error_count}.
        To solve the problem, set "always_visible" to False for a few polygons.
        If the "cell_id" is e.g. 99 (2 characters), then it consumes 3 characters (2 + 1) in the CELLS file.
        *************\n
        """
        raise ValueError(error_message)


def get_cell_ids(landmark_folder: Path, city_folder: Path) -> Tuple[List[int], Set[int]]:
    meshes_regular = []
    meshes_water_drift = set()

    files = [file for folder in [landmark_folder, city_folder] for file in folder.iterdir()]
    
    for file in files:
        cell_id = int(re.findall(r'\d+', file.name)[0])

        if file.name.endswith("_A2.bms"):
            meshes_water_drift.add(cell_id)

        if file.name.endswith(".bms"):
            meshes_regular.append(cell_id)
            
    return meshes_regular, meshes_water_drift


def get_cell_visiblity(polys: List[Polygon]) -> List[int]:
    always_visible_cell_ids = [poly.cell_id for poly in polys if poly.always_visible]
    
    if Default.ROOM not in always_visible_cell_ids:
        always_visible_cell_ids.insert(0, Default.ROOM)
        
    return always_visible_cell_ids


def get_cell_type(cell_id: int, polys: List[Polygon]) -> int:  
    for poly in polys:
        if poly.cell_id == cell_id:
            return poly.cell_type
    return Room.DEFAULT


def write_cell_row(cell_id: int, cell_type: int, always_visible_data: str, mesh_a2_files: Set[int]) -> str:       
    model = LevelOfDetail.DRIFT if cell_id in mesh_a2_files else LevelOfDetail.HIGH
    return f"{cell_id},{model},{cell_type}{always_visible_data}\n"


def truncate_always_visible(always_visible_cell_ids: List[int], cell_id: int, cell_type: int, mesh_a2_files: Set[int]) -> Tuple[str, int]:
    always_visible_count = len(always_visible_cell_ids)
    always_visible_data = f",{always_visible_count},{','.join(map(str, always_visible_cell_ids))}"
    cell_row = write_cell_row(cell_id, cell_type, always_visible_data, mesh_a2_files)

    while len(cell_row) >= Threshold.CELL_CHARACTER_LIMIT:
        always_visible_cell_ids.pop()
        always_visible_count = len(always_visible_cell_ids)
        always_visible_data = f",{always_visible_count},{','.join(map(str, always_visible_cell_ids))}"
        cell_row = write_cell_row(cell_id, cell_type, always_visible_data, mesh_a2_files)
        
    return cell_row, len(cell_row) 
        
        
def create_cells(output_file: Path, polys: List[Polygon], truncate_cells: bool) -> None:
    mesh_files, mesh_a2_files = get_cell_ids(Folder.SHOP_MESH_LANDMARK, Folder.SHOP_MESH_CITY)

    with open(output_file, "w") as f:    
        f.write(f"{len(mesh_files)}\n")
        f.write(str(max(mesh_files) + 1000) + "\n")

        always_visible_cell_ids = get_cell_visiblity(polys)
        always_visible_cell_count = len(always_visible_cell_ids)

        max_warning_count = max_error_count = 0

        for cell_id in sorted(mesh_files):
            cell_type = get_cell_type(cell_id, polys)
            always_visible_data = ",0" if always_visible_cell_count == 0 else f",{always_visible_cell_count},{','.join(map(str, always_visible_cell_ids))}"
            row = write_cell_row(cell_id, cell_type, always_visible_data, mesh_a2_files)
            row_length = len(row)
            
            if truncate_cells and row_length >= Threshold.CELL_CHARACTER_LIMIT:
                row, row_length = truncate_always_visible(always_visible_cell_ids.copy(), cell_id, cell_type, mesh_a2_files)
                    
            max_warning_count, max_error_count = update_max_counts(row_length, max_warning_count, max_error_count)
            
            f.write(row)

        check_row_size(max_warning_count, max_error_count)
        
################################################################################################################               
################################################################################################################
#! ======================= MINIMAP ======================= !#


def create_minimap(set_minimap: bool, debug_minimap: bool, debug_minimap_id: bool, 
                  minimap_outline_color: str, line_width: float, background_color: str) -> None:
    
    if not set_minimap or is_blender_running():
        return
    
    global hudmap_vertices
    global hudmap_properties

    min_x, min_z, max_x, max_z = calculate_extrema(hudmap_vertices)

    width = int(max_x - min_x)
    height = int(max_z - min_z) 
    
    def draw_polygon(ax, polygon, minimap_outline_color: str, 
                    label = None, add_label = False, hud_fill = False, hud_color = None) -> None:

        xs, ys = zip(*[(point[0], point[2]) for point in polygon])
        xs, ys = xs + (xs[0],), ys + (ys[0],)  # The commas after [0] should not be removed

        if minimap_outline_color:
            ax.plot(xs, ys, minimap_outline_color, line_width)

        if hud_fill:
            ax.fill(xs, ys, hud_color)

        if add_label: 
            center = calculate_center_tuples(polygon)
            ax.text(center[0], center[2], label, color = "white", 
                    ha = "center", va = "center", fontsize = 4.0)   
            
    # Regular Export (320 and 640 versions)
    _, ax = plt.subplots()
    ax.set_facecolor(background_color)

    for i, polygon in enumerate(hudmap_vertices):
        hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))

        draw_polygon(ax, polygon, minimap_outline_color, 
                     add_label = False, hud_fill = hud_fill, hud_color = hud_color)

    ax.set_aspect("equal", "box")
    ax.axis("off")

    # Save JPG 640 and 320 Pictures                    
    plt.savefig(Folder.SHOP / "BMP16" / f"{MAP_FILENAME}640.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color)
    plt.savefig(Folder.SHOP / "BMP16" / f"{MAP_FILENAME}320.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color) 

    if debug_minimap or set_lars_race_maker:
        _, ax_debug = plt.subplots(figsize = (width, height), dpi = 1)
        ax_debug.set_facecolor("black")

        for i, polygon in enumerate(hudmap_vertices):
            hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))

            draw_polygon(ax_debug, polygon, minimap_outline_color, 
                        label = bound_label if debug_minimap_id else None, 
                        add_label = True, hud_fill = hud_fill, hud_color = hud_color)

        ax_debug.axis("off")
        ax_debug.set_xlim([min_x, max_x])
        ax_debug.set_ylim([max_z, min_z])  # Flip the image vertically
        ax_debug.set_position([0, 0, 1, 1]) 
        plt.savefig(Folder.BASE / f"{MAP_FILENAME}_HUD_debug.jpg", dpi = 1, bbox_inches = None, pad_inches = 0, facecolor = "purple")
                            
################################################################################################################               
################################################################################################################
#! ======================= BRIDGES ======================= !#  

    
BRIDGE_CONFIG_DEFAULT = {
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
    "Mode": NetworkMode.SINGLE
    }
    
    
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
   
BRIDGE_ATTRIBUTE_FILLER = f"\t{Prop.CROSSGATE},0,-999.99,0.00,-999.99,-999.99,0.00,-999.99\n"  

                               
def create_bridges(all_bridges, set_bridges: bool, output_file: Path):
    if not set_bridges:
        return
        
    if output_file.exists():
        os.remove(output_file)
    
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
        
    def generate_attribute_lines(bridge_attributes) -> str:
        lines = ""
        
        # For example, Crossgates
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
        fillers = BRIDGE_ATTRIBUTE_FILLER * num_fillers

        template = (
            f"DrawBridge{id}\n"
            f"\t{drawbridge_values}\n"
            f"{attributes}"
            f"{fillers}"
            f"DrawBridge{id}\n"  
            )
        
        bridge_data.append(template)

    with open(output_file, "a") as f:
        f.writelines(bridge_data)


def create_bridge_config(configs: List[Dict[str, Union[float, int, str]]], set_bridges: bool, output_folder: Path) -> None:
    if not set_bridges:
        return
    
    for config in configs:
        final_config = merge_bridge_configs (BRIDGE_CONFIG_DEFAULT, config)
        config_str = generate_bridge_config_string(final_config)
        filenames = determine_bridge_filenames(final_config)
        write_bridge_config_to_files(filenames, config_str, output_folder)


def merge_bridge_configs(default_config: Dict[str, Union[float, int, str]], custom_config: Dict[str, Union[float, int, str]]) -> Dict[str, Union[float, int, str]]:
    return {**default_config, **custom_config}


def generate_bridge_config_string(config: Dict[str, Union[float, int, str]]) -> str:
    template = """
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
    return template.format(**config)


def determine_bridge_filenames(config: Dict[str, Union[float, int, str]]) -> List[str]:
    filenames = []
    race_type = config["RaceType"]

    if race_type in [RaceMode.ROAM, RaceMode.COPS_AND_ROBBERS]:
        base_name = race_type
        filenames += get_bridge_mode_filenames(base_name, config["Mode"])
    elif race_type in [RaceMode.CHECKPOINT, RaceMode.CIRCUIT, RaceMode.BLITZ]:
        filenames += get_bridge_race_type_filenames(race_type, config["RaceNum"], config["Mode"])
    else:
        raise ValueError(f"Invalid RaceType. Must be one of {RaceMode.ROAM}, {RaceMode.BLITZ}, {RaceMode.CHECKPOINT}, {RaceMode.CIRCUIT}, or {RaceMode.COPS_AND_ROBBERS}.")

    return filenames


def get_bridge_mode_filenames(base_name: str, mode: str) -> List[str]:
    filenames = []
    if mode in [NetworkMode.SINGLE, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{base_name}.MMBRIDGEMGR")
    if mode in [NetworkMode.MULTI, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{base_name}M.MMBRIDGEMGR")
    return filenames


def get_bridge_race_type_filenames(race_type: str, race_num: str, mode: str) -> List[str]:
    filenames = []
    if mode in [NetworkMode.SINGLE, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{race_type}{race_num}.MMBRIDGEMGR")
    if mode in [NetworkMode.MULTI, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{race_type}{race_num}M.MMBRIDGEMGR")
    return filenames


def write_bridge_config_to_files(filenames: List[str], config_str: str, output_folder: Path) -> None:
    for filename in filenames:
        file_path = output_folder / filename
        file_path.write_text(config_str)

################################################################################################################               
################################################################################################################
#! ======================= PORTAL GENERATION ======================= !#

#! ############ Code by 0x1F9F1 (Modified) // start ############ !#   

                 
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
        
################################################################################################################?               

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
    
################################################################################################################?  

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
            cell.add_edge(vertices[poly.vertex_index[i]], vertices[poly.vertex_index[j]]) 

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

#! ############ Code by 0x1F9F1 (Modified) // end ############ !# 

################################################################################################################               
################################################################################################################
#! ======================= PORTALS II ======================= !#


class Portals:
    def __init__(self, flags: int, edge_count: int, gap_2: int, cell_1: int, cell_2: int, height: float, 
                 _min: Vector3, _max: Vector3, vertex_c: Vector3 = None) -> None:
        
        self.flags = flags
        self.edge_count = edge_count
        self.gap_2 = gap_2
        self.cell_1 = cell_1
        self.cell_2 = cell_2
        self.height = height
        self._min = _min 
        self._max = _max
        self.vertex_c = vertex_c
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        magic = read_binary_name(f, 4)
        count, = read_unpack(f, '<I')
        return count
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'Portals':
        flags, edge_count, = read_unpack(f, '<2B')
        gap_2, = read_unpack(f, '<H')
        cell_1, cell_2, = read_unpack(f, '<2H')  
        height, = read_unpack(f, '<f')   
        _min = Vector3.read(f, '<')
        _max = Vector3.read(f, '<')
        
        vertex_c = None
        if edge_count == Shape.TRIANGLE:
            vertex_c = Vector3.read(f, '<')

        return cls(flags, edge_count, gap_2, cell_1, cell_2, height, _min, _max, vertex_c)
        
    @classmethod
    def read_all(cls, f: BinaryIO) -> 'List[Portals]':
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, portals: 'List[Portals]') -> None:
        write_pack(f, '<I', 0) 
        write_pack(f, '<I', len(portals))
                
    @classmethod
    def write_all(cls, output_file: Path,
                  polys: List[Polygon], vertices: List[Vector3], 
                  lower_portals: bool, empty_portals: bool, debug_portals: bool) -> None:    
            
        with open(output_file, "wb") as f:
            if empty_portals:
                pass
            
            else:
                _, portal_tuples = prepare_portals(polys, vertices)
                
                portals = []
                
                cls.write_n(f, portal_tuples)

                for cell_1, cell_2, v1, v2 in portal_tuples:
                    flags = Portal.ACTIVE
                    edge_count = Shape.LINE
                    gap_2 = 101
                    height = MAX_Y - MIN_Y
                    _min = Vector3(v1.x, -50 if lower_portals else 0, v1.y)
                    _max = Vector3(v2.x, -50 if lower_portals else 0, v2.y)

                    portal = Portals(flags, edge_count, gap_2, cell_1, cell_2, height, _min, _max)
                    portals.append(portal)
                    
                    write_pack(f, '<2B', flags, edge_count)
                    write_pack(f, '<H', gap_2)
                    write_pack(f, '<2H', cell_2, cell_1)
                    write_pack(f, '<f', height)
                    _min.write(f, '<')
                    _max.write(f, '<')
                    
                if debug_portals:  
                    cls.debug(portals, Folder.DEBUG_RESOURCES / "PORTALS" / f"{MAP_FILENAME}_PTL.txt")            
    @classmethod
    def debug(cls, portals: 'List[Portals]', output_file: Path) -> None:
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(output_file, 'w') as out_f:
            for portal in portals:
                out_f.write(repr(portal))
                
        print(f"Processed portal data to {output_file.name}")
                            
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_portals_file: bool) -> None:
        if not debug_portals_file:
            return
        
        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, "rb") as in_f:
            portals = cls.read_all(in_f)

        if not portals:
            print(f"No portals found in {input_file.name}")
            return

        with open(output_file, "w") as out_f:
            for portal in portals:
                out_f.write(repr(portal))

        print(f"Processed {input_file.name} to {output_file.name}")
            
    def __repr__(self):
            return f"""
PORTAL
    Flags: {self.flags}
    EdgeCount: {self.edge_count}
    Gap 2: {self.gap_2}
    Cell 1: {self.cell_1}
    Cell 2: {self.cell_2}
    Height: {self.height:.2f}
    Min: {self._min}
    Max: {self._max}
    {'Vertex C ' + str(self.vertex_c) if self.vertex_c is not None else ''}
    """
    
################################################################################################################               
################################################################################################################            
#! ======================= BANGERS CLASS ======================= !#

                                                  
class Bangers:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.name = name
                
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '<I')[0]
            
    @classmethod
    def read(cls, f: BinaryIO) -> 'Bangers':
        room, flags = read_unpack(f, '<2H')
        offset = Vector3.read(f, '<')
        face = Vector3.read(f, '<')  
        name = read_binary_name(f)
        return cls(room, flags, offset, face, name)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> 'List[Bangers]':
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, bangers: List['Bangers']) -> None:
        write_pack(f, '<I', len(bangers))
    
    @classmethod
    def write_all(cls, output_file: Path, bangers: List['Bangers'], debug_props: bool) -> None:
        with open(output_file, mode = "wb") as f:
            
            cls.write_n(f, bangers)
        
            for banger in bangers:
                write_pack(f, '<2H', Default.ROOM, PROP_COLLIDE_FLAG)  
                banger.offset.write(f, '<')
                banger.face.write(f, '<')
                f.write(banger.name.encode('utf-8'))
                    
            if debug_props:
                cls.debug(Folder.DEBUG_RESOURCES / "PROPS" / f"{output_file}.txt", bangers)
                                    
    @classmethod
    def debug(cls, output_file: Path, bangers: List['Bangers']) -> None:
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(output_file, 'w') as out_f:
            for banger in bangers:
                out_f.write(repr(banger))
        print(f"Processed banger data to {output_file.name}")
                    
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_props_file: bool) -> None:
        if not debug_props_file:
            return

        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, 'rb') as in_f:
            bangers = cls.read_all(in_f)

        with open(output_file, 'w') as out_f:
            for banger in bangers:
                out_f.write(repr(banger))
        print(f"Processed {input_file.name} to {output_file.name}")
        
    @classmethod
    def debug_file_to_csv(cls, input_file: Path, output_file: Path, debug_props_file_to_csv: bool) -> None:
        if not debug_props_file_to_csv:
            return
        
        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, 'rb') as in_f:
            bangers = cls.read_all(in_f)

        with open(output_file, 'w') as out_f:
            out_f.write(f"{len(bangers)}\n")  # Count
            
            for banger in bangers:
                formatted_line = f"{banger.room},{banger.flags}," \
                                 f"{banger.offset.x:.2f},{banger.offset.y:.2f},{banger.offset.z:.2f}," \
                                 f"{banger.face.x:.2f},{banger.face.y:.2f},{banger.face.z:.2f}," \
                                 f"{banger.name}\n"
                                 
                out_f.write(formatted_line)
        print(f"Processed {input_file.name} to {output_file.name} in CSV format")
                                    
    def __repr__(self):
        return f"""
BANGER
    Room: {self.room}
    Flags: {self.flags}
    Start: {self.offset}
    Face: {self.face}
    Name: {self.name}
    """
    
################################################################################################################               
###############################################################################################################
#! ======================= BANGERS EDITOR ======================= !#


class BangerEditor:
    def __init__(self) -> None:  
        self.map_filename = Path(MAP_FILENAME)                      
        self.props = [] 
        
    def process_all(self, user_set_props: list, set_props: bool):
        if not set_props:
            return
        
        per_race_props = {}

        for prop in user_set_props:
            race_mode = prop.get('race_mode', 'DEFAULT')
            race_num = prop.get('race_num', '')
            race_key = f"{race_mode}_{race_num}" if race_mode != 'DEFAULT' else 'DEFAULT'
            per_race_props.setdefault(race_key, []).append(prop)

        for race_key, race_props in per_race_props.items():                
            self.props.clear()
            self.add_multiple(race_props)
            current_filename = self._filename_with_suffix(race_key)
            Bangers.write_all(Folder.SHOP_CITY / current_filename, self.props, debug_props) 
            
    def add_multiple(self, user_set_props):    
        for prop in user_set_props:
            offset = Vector3(*prop['offset']) 
            end = Vector3(*prop['end']) if 'end' in prop else None
            face = Vector3(*prop.get('face', (HUGE, HUGE, HUGE)))
            name = prop['name']
            
            if end is not None:
                diagonal = end - offset
                diagonal_length = diagonal.Mag()
                normalized_diagonal = diagonal.Normalize()
                
                if face == Vector3(HUGE, HUGE, HUGE):
                    face = normalized_diagonal * HUGE
                
                separator = prop.get('separator', 10.0)
            
                if isinstance(separator, str) and separator.lower() in ["x", "y", "z"]:
                    prop_dims = self.load_dimensions(Folder.EDITOR_RESOURCES / "PROPS" / "Prop Dimensions.txt").get(name, Vector3(1, 1, 1))
                    separator = getattr(prop_dims, separator.lower())
                elif not isinstance(separator, (int, float)):
                    separator = 10.0
                                            
                num_props = int(diagonal_length / separator)
                
                for i in range(0, num_props):
                    dynamic_offset = offset + normalized_diagonal * (i * separator)
                    self.props.append(Bangers(Default.ROOM, PROP_COLLIDE_FLAG, dynamic_offset, face, name + "\x00"))

            else:
                self.props.append(Bangers(Default.ROOM, PROP_COLLIDE_FLAG, offset, face, name + "\x00"))
                
    def append_to_file(self, input_props_f: Path, props_to_append: list, appended_props_f: Path, append_props: bool):
        if not append_props:
            return
            
        with open(input_props_f, "rb") as f:
            original_props = Bangers.read_all(f)
              
        self.props = original_props
        self.add_multiple(props_to_append)
        
        Bangers.write_all(appended_props_f, self.props, debug_props)
                            
    def place_randomly(self, seed: int, num_props: int, props_dict: dict, x_range: tuple, z_range: tuple):
        assert len(x_range) == 2 and len(z_range) == 2, "x_range and z_range must each contain exactly two values."

        random.seed(seed)
        names = props_dict.get("name", [])
        names = names if isinstance(names, list) else [names]
        
        random_props = []
        
        for name in names:
            for _ in range(num_props):
                x = random.uniform(*x_range)
                z = random.uniform(*z_range)
                y = props_dict.get("offset_y", 0.0)
                new_prop = {
                    "name": name,
                    "offset": (x, y, z)
                } 

                if "face" not in props_dict:
                    new_prop["face"] = (
                        random.uniform(-HUGE, HUGE),
                        random.uniform(-HUGE, HUGE), 
                        random.uniform(-HUGE, HUGE)
                    )
                else:
                    new_prop["face"] = props_dict["face"]

                new_prop.update({k: v for k, v in props_dict.items() if k not in new_prop})
                random_props.append(new_prop)
                
        return random_props
    
    def _filename_with_suffix(self, race_key):        
        if race_key == "DEFAULT":
            return self.map_filename.with_suffix(".BNG")
            
        race_mode, race_num = race_key.split("_")
        short_race_mode = {RaceMode.CIRCUIT: "C", RaceMode.CHECKPOINT: "R", RaceMode.BLITZ: "B"}.get(race_mode, race_mode)
        race_num = race_num or "0"        
        return self.map_filename.parent / f"{self.map_filename.stem}_{short_race_mode}{race_num}.BNG"
                                                                            
    @staticmethod  
    def load_dimensions(input_file: Path) -> dict:
        extracted_prop_dim = {}
        
        with open(input_file, "r") as f:
            for line in f:
                prop_name, value_x, value_y, value_z = line.split()
                extracted_prop_dim[prop_name] = Vector3(float(value_x), float(value_y), float(value_z))
        return extracted_prop_dim

################################################################################################################               
################################################################################################################
#! ======================= FACADES CLASS ======================= !#


class Facades:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, sides: Vector3, scale: float, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.sides = sides
        self.scale = scale
        self.name = name
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '<I')[0]

    @classmethod
    def read(cls, f: BinaryIO) -> 'Facades':
        room, flags = read_unpack(f, '<2H')
        offset = Vector3.read(f, '<')
        face = Vector3.read(f, '<')
        sides = Vector3.read(f, '<')
        scale, = read_unpack(f, '<f')
        name = read_binary_name(f)
        return cls(room, flags, offset, face, sides, scale, name)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['Facades']:
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, facades: List['Facades']) -> None:
        return write_pack(f, '<I', len(facades))
        
    def write(self, f: BinaryIO) -> None: 
        write_pack(f, '<2H', Default.ROOM, self.flags)  # Hardcode the Room value such that all Facades are visible in the game    
        write_pack(f, '<3f', *self.offset)  
        write_pack(f, '<3f', *self.face)
        write_pack(f, '<3f', *self.sides)
        write_pack(f, '<f', self.scale)
        write_binary_name(f, self.name, terminate = True) 
        
    @classmethod
    def write_all(cls, output_file: Path, facades: List['Facades']) -> None:
        with open(output_file, mode = "wb") as f:
            
            cls.write_n(f, facades)
            
            for facade in facades:
                facade.write(f)
                                 
    @staticmethod
    def debug(facades: List['Facades'], output_file: Path) -> None:
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(output_file, mode = 'w') as f:
            for facade in facades:
                f.write(str(facade))
        print(f"Processed facade data to {output_file.name}")
                                           
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_facade_file: bool) -> None:
        if not debug_facade_file:
            return

        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, "rb") as in_f:
            facades = cls.read_all(in_f)

        with open(output_file, "w") as out_f:
            for facade in facades:
                out_f.write(repr(facade))
        print(f"Processed {input_file.name} to {output_file.name}")
        
    def __repr__(self):
        return f"""
FACADE
    Room: {self.room}
    Flags: {self.flags}
    Offset: {self.offset}
    Face: {self.face}
    Sides: {self.sides}
    Scale: {self.scale:.2f}
    Name: {self.name}
    """
    
################################################################################################################               
################################################################################################################
#! ======================= FACADE EDITOR ======================= !#


class FacadeEditor:    
    @classmethod
    def create(cls, output_file: str, user_set_facades, set_facades: bool, debug_facades: bool):
        if not set_facades:
            return
        
        facades = cls.process(user_set_facades)
        Facades.write_all(output_file, facades)

        if debug_facades:
            Facades.debug(facades, Folder.DEBUG_RESOURCES / "FACADES" / f"{MAP_FILENAME}.txt")

    @staticmethod
    def read_scales(input_file: Path):
        with open(input_file, 'r') as f:
            return {name: float(scale) for name, scale in (line.strip().split(": ") for line in f)}

    @classmethod
    def process(cls, user_set_facades):
        axis_dict = {'x': 0, 'y': 1, 'z': 2}
        scales = cls.read_scales(Folder.EDITOR_RESOURCES / "FACADES" / "FCD scales.txt")

        facades = []
        for params in user_set_facades:
            axis = axis_dict[params['axis']]
            start_coord = params['offset'][axis]
            end_coord = params['end'][axis]

            direction = 1 if start_coord < end_coord else -1

            num_facades = math.ceil(abs(end_coord - start_coord) / params['separator'])

            for i in range(num_facades):
                current_start, current_end = cls.calculate_start_end(params, axis, direction, start_coord, i)
                sides = params.get('sides', (0.0, 0.0, 0.0))
                scale = scales.get(params['name'], params.get('scale', 1.0))
                facades.append(Facades(Default.ROOM, params['flags'], current_start, current_end, sides, scale, params['name']))

        return facades
    
    @staticmethod
    def calculate_start_end(params, axis, direction, start_coord, i):
        shift = direction * params['separator'] * i
        current_start = list(params['offset'])
        current_end = list(params['end'])

        current_start[axis] = start_coord + shift
        end_coord = params['end'][axis]
        
        if direction == 1:
            current_end[axis] = min(start_coord + shift + params['separator'], end_coord)
        else:
            current_end[axis] = max(start_coord + shift - params['separator'], end_coord)

        return tuple(current_start), tuple(current_end)
    
################################################################################################################               
################################################################################################################
#! ======================= PHYSICS ======================= !#


class PhysicsEditor:
    def __init__(self, name: str, friction: float, elasticity: float, drag: float, 
                 bump_height: float, bump_width: float, bump_depth: float, sink_depth: float, 
                 type: int, sound: int, velocity: Vector2, ptx_color: Vector3) -> None:
        
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
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '>I')[0]

    @staticmethod
    def read(f: BinaryIO) -> 'PhysicsEditor':
        name = read_binary_name(f, 32, 'latin-1')
        friction, elasticity, drag = read_unpack(f, '>3f')
        bump_height, bump_width, bump_depth, sink_depth = read_unpack(f, '>4f')
        type, sound = read_unpack(f, '>2I')
        velocity = Vector2.read(f, '>')
        ptx_color = Vector3.read(f, '>')
        return PhysicsEditor(name, friction, elasticity, drag, bump_height, bump_width, bump_depth, sink_depth, type, sound, velocity, ptx_color)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['PhysicsEditor']:
        return [cls.read(f) for _ in range(cls.readn(f))]

    def write(self, f: BinaryIO) -> None:        
        write_binary_name(f, self.name, length = 32, encoding = "latin-1", terminate = True)
        write_pack(f, '>3f', self.friction, self.elasticity, self.drag)
        write_pack(f, '>4f', self.bump_height, self.bump_width, self.bump_depth, self.sink_depth)
        write_pack(f, '>2I', self.type, self.sound)
        self.velocity.write(f, '>')
        self.ptx_color.write(f, '>')

    @staticmethod
    def write_all(output_file: Path, custom_params: List['PhysicsEditor']) -> None:
        with open(output_file, "wb") as f:
            write_pack(f, '>I', len(custom_params))
            
            for param in custom_params:                
                param.write(f)
                
    @classmethod    
    def edit(cls, input_file: Path, output_file: Path, user_set_properties: dict, set_physics: bool, debug_physics: bool) -> None:
        if not set_physics:
            return
        
        with open(input_file, "rb") as f:
            original_data = cls.read_all(f)   
             
        for phys_index, properties in user_set_properties.items():
            physics_obj = original_data[phys_index - 1]
            
            for attr , value in properties.items():
                setattr(physics_obj, attr, value)
                    
        cls.write_all(output_file, original_data)
        
        if debug_physics:
            os.makedirs(Folder.DEBUG_RESOURCES / "PHYSICS", exist_ok = True)
            cls.debug(Folder.DEBUG_RESOURCES / "PHYSICS" / "PHYSICS_DB.txt", original_data)
                        
    @classmethod
    def debug(cls, debug_filename: Path, physics_params: List['PhysicsEditor']) -> None: 
        with open(debug_filename, 'w') as debug_f:
            for idx, physics_param in enumerate(physics_params):
                debug_f.write(physics_param.__repr__(idx))
                debug_f.write("\n")

    def __repr__(self, idx = None) -> str:
        header = f"PHYSICS (# {idx + 1})" if idx is not None else "PHYSICS"
        name = self.name.rstrip('\x00' + 'Í')
        
        return f"""
{header}
    Name: '{name}',
    Friction: {self.friction:.2f},
    Elasticity: {self.elasticity:.2f},
    Drag: {self.drag:.2f},
    Bump height: {self.bump_height:.2f},
    Bump width: {self.bump_width:.2f},
    Bump depth: {self.bump_depth:.2f},
    Sink Depth: {self.sink_depth:.2f},
    Type: {self.type},
    Sound: {self.sound},
    Velocity: {self.velocity},
    Ptx color: {self.ptx_color}
    """

################################################################################################################               
################################################################################################################
#! ======================= LIGHTING ======================= !#


LIGHTING_HEADER = [
    "TimeOfDay", "Weather", "Sun Heading", "Sun Pitch", "Sun Red", "Sun Green", "Sun Blue",
    "Fill-1 Heading", "Fill-1 Pitch", "Fill-1 Red", "Fill-1 Green", "Fill-1 Blue",
    "Fill-2 Heading", "Fill-2 Pitch", "Fill-2 Red", "Fill-2 Green", "Fill-2 Blue",
    "Ambient Red", "Ambient Green", "Ambient Blue", 
    "Fog End", "Fog Red", "Fog Green", "Fog Blue", 
    "Shadow Alpha", "Shadow Red", "Shadow Green", "Shadow Blue"
]


class LightingEditor:
    def __init__(self, time_of_day: int, weather: int, 
                 sun_heading: float, sun_pitch: float, sun_color: Tuple[float, float, float], 
                 fill_1_heading: float, fill_1_pitch: float, fill_1_color: Tuple[float, float, float], 
                 fill_2_heading: float, fill_2_pitch: float, fill_2_color: Tuple[float, float, float], 
                 ambient_color: Tuple[float, float, float],  
                 fog_end: float, fog_color: Tuple[float, float, float], 
                 shadow_alpha: float, shadow_color: Tuple[float, float, float]) -> None:
        
        self.time_of_day = time_of_day
        self.weather = weather
        self.sun_heading = sun_heading
        self.sun_pitch = sun_pitch
        self.sun_color = sun_color
        self.fill_1_heading = fill_1_heading
        self.fill_1_pitch = fill_1_pitch
        self.fill_1_color = fill_1_color
        self.fill_2_heading = fill_2_heading
        self.fill_2_pitch = fill_2_pitch
        self.fill_2_color = fill_2_color
        self.ambient_color = ambient_color
        self.fog_end = fog_end
        self.fog_color = fog_color
        self.shadow_alpha = shadow_alpha
        self.shadow_color = shadow_color
        
    @classmethod
    def read_rows(cls, row: list[Union[int, float, str]]) -> 'LightingEditor':
        return cls(
            time_of_day = int(row[0]),
            weather = int(row[1]),
            sun_heading = float(row[2]),
            sun_pitch = float(row[3]),
            sun_color = (float(row[4]), float(row[5]), float(row[6])),
            fill_1_heading = float(row[7]),
            fill_1_pitch = float(row[8]),
            fill_1_color = (float(row[9]), float(row[10]), float(row[11])),
            fill_2_heading = float(row[12]),
            fill_2_pitch = float(row[13]),
            fill_2_color = (float(row[14]), float(row[15]), float(row[16])),
            ambient_color = (float(row[17]), float(row[18]), float(row[19])),
            fog_end = float(row[20]),
            fog_color = (float(row[21]), float(row[22]), float(row[23])),
            shadow_alpha = float(row[24]),
            shadow_color = (float(row[25]), float(row[26]), float(row[27]))
        )
    
    @classmethod
    def read_file(cls, filename: Path):
        instances = []
        
        with open(filename, newline = "") as f:
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
                if instance.time_of_day == config["time_of_day"] and instance.weather == config["weather"]:
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
            format_value(self.fill_1_heading),
            format_value(self.fill_1_pitch),
            *map(format_value, self.fill_1_color),
            format_value(self.fill_2_heading),
            format_value(self.fill_2_pitch),
            *map(format_value, self.fill_2_color),
            *map(format_value, self.ambient_color),
            format_value(self.fog_end),
            *map(format_value, self.fog_color),
            format_value(self.shadow_alpha),
            *map(format_value, self.shadow_color)
        ]
        
    @classmethod
    def write_file(cls, instances, lighting_configs, filename: Path):
        cls.process_changes(instances, lighting_configs)
        
        with open(filename, mode = "w", newline = "") as f:
            writer = csv.writer(f)        
            writer.writerow(LIGHTING_HEADER)
            
            for instance in instances:
                writer.writerow(instance.write_rows())
                
    @classmethod
    def debug(cls, instances, debug_file: str, debug_lighting: bool) -> None:
        if not debug_lighting:
            return

        with open(debug_file, "w") as debug_f:
            for instance in instances:
                debug_f.write(instance.__repr__())
                debug_f.write("\n")
                
    def __repr__(self):
        return f"""
LIGHTING
    Time of Day: {self.time_of_day}
    Weather: {self.weather}
    Sun Heading: {self.sun_heading:.2f}
    Sun Pitch: {self.sun_pitch:.2f}
    Sun Color: {self.sun_color}
    Fill 1 Heading: {self.fill_1_heading:.2f}
    Fill 1 Pitch: {self.fill_1_pitch:.2f}
    Fill 1 Color: {self.fill_1_color}
    Fill 2 Heading: {self.fill_2_heading:.2f}
    Fill 2 Pitch: {self.fill_2_pitch:.2f}
    Fill 2 Color: {self.fill_2_color}
    Ambient Color: {self.ambient_color}
    Fog End: {self.fog_end:.2f}
    Fog Color: {self.fog_color}
    Shadow Alpha: {self.shadow_alpha:.2f}
    Shadow Color: {self.shadow_color}
    """

###################################################################################################################
###################################################################################################################
#! ======================= TEXTURESHEET ======================= !#

TEXTURESHEET_HEADER = ["name", "neighborhood", "h", "m", "l", "flags", "alternate", "sibling", "xres", "yres", "hexcolor"]

TEXTURESHEET_MAPPING = {
    "neighborhood": 1,
    "lod_high": 2,
    "lod_medium": 3,
    "lod_low": 4,
    "flags": 5,
    "alternate": 6,
    "sibling": 7,
    "x_res": 8,
    "y_res": 9,
    "hex_color": 10
}

class AgiTexParameters:
    TRANSPARENT = "t"
    SNOWABLE = "w"
    DULL_OR_DAMAGED = "d"    
    ALPHA_GLOW = "g"
    NOT_LIT = "n"
    ROAD_FLOOR_CEILING = "e"
    CHROMAKEY = "k"
    LIGHTMAP = "l"
    SHADOW = "s"
    
    ALWAYS_MODULATE = "m"
    ALWAYS_PERSP_CORRECT = "p"
    
    CLAMP_U_OR_BOTH = "u"
    CLAMP_V_OR_BOTH = "v"
    CLAMP_BOTH = "c"
    CLAMP_U_OR_NEITHER = "U"
    CLAMP_V_OR_NEITHER = "V"


class TextureSheet:
    def __init__(self, name: str = "", neighborhood: int = 0, 
                 lod_high: int = 0, lod_medium: int = 0, lod_low: int = 1, 
                 flags: str = "", alternate: str = "", sibling: str = "", 
                 x_res: int = 64, y_res: int = 64, hex_color: str = "000000") -> None:
        
        self.name = name
        self.neighborhood = neighborhood
        self.lod_high = lod_high
        self.lod_medium = lod_medium
        self.lod_low = lod_low
        self.flags = flags
        self.alternate = alternate
        self.sibling = sibling
        self.x_res = x_res
        self.y_res = y_res
        self.hex_color = hex_color
        
    @staticmethod
    def read_sheet(input_file: Path) -> Dict[str, List[str]]:
        with open(input_file, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            return {row[0]: row for row in reader}

    @staticmethod
    def get_custom_texture_filenames(input_textures: Path) -> List[str]:
         return [f.stem for f in input_textures.glob("*.DDS")]
     
    @staticmethod
    def parse_flags(flags: List[str]) -> str:
        flag_str = "".join(flags)
        print(f"Parsing flags {flags} to {flag_str}")  
        return flag_str

    @classmethod
    def append_custom_textures(cls, input_file: Path, input_textures: Path, output_file: Path, set_texture_sheet: bool) -> None:
        if not set_texture_sheet:
            return
              
        with open(input_file, "r") as in_f:
            texturesheet_lines = in_f.readlines()
                    
        existing_texture_names = set(line.split(',')[0].strip() for line in texturesheet_lines)
        custom_texture_names = TextureSheet.get_custom_texture_filenames(input_textures)
        
        with open(output_file, "w") as out_f: 
            out_f.writelines(texturesheet_lines)  # Write the existing texturesheet lines first
                    
            for custom_tex in custom_texture_names:
                if custom_tex not in existing_texture_names:
                    out_f.write(f"{custom_tex},0,0,0,1,,{custom_tex},,64,64,000000\n")  # TODO: Add support for custom flags
                    
    @staticmethod
    def write(textures: Dict[str, List[str]], output_file: Path):
        with open(output_file, "w", newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(TEXTURESHEET_HEADER)
            
            for row in textures.values():
                writer.writerow(row)

    @classmethod
    def write_tweaked(cls, input_file: Path, output_file: Path, texture_changes: List[dict]):
        textures = cls.read_sheet(input_file)

        for changes in texture_changes:
            target = changes.get("name")
            
            if not target or target not in textures:
                print(f"Texture '{target}' not found or not specified.")
                continue

            texture = textures[target]
            
            for key, value in changes.items():
                if key == "name":
                    continue 
                
                if key == "flags":
                    value = cls.parse_flags(value)  
                    
                if key in TEXTURESHEET_MAPPING:
                    texture[TEXTURESHEET_MAPPING[key]] = str(value)

        cls.write(textures, output_file)
                    
###################################################################################################################
###################################################################################################################
#! ======================= AI ======================= !#


#! ############ Code by 0x1F9F1 (Modified) // start ############ !#   

class aiStreet:                  
    def load(self, f: BinaryIO) -> None:
        self.id, = read_unpack(f, '<H')
        self.num_vertexes, = read_unpack(f, '<H')
        self.num_lanes, = read_unpack(f, '<H')
        self.num_sidewalks, = read_unpack(f, '<H')
        self.stop_light_index, = read_unpack(f, '<H')
        self.intersection_type, = read_unpack(f, '<H')
        self.blocked, = read_unpack(f, '<H')
        self.ped_blocked, = read_unpack(f, '<H')
        self.divided, = read_unpack(f, '<H')
        self.is_flat, = read_unpack(f, '<H')
        self.has_bridge, = read_unpack(f, '<H')
        self.alley, = read_unpack(f, '<H')
        self.road_length, = read_unpack(f, '<f')
        self.speed_limit, = read_unpack(f, '<f')
        self.stop_light_name = read_binary_name(f, 32)
        self.oncoming_path, = read_unpack(f, '<I')
        self.edge_index, = read_unpack(f, '<I')
        self.path_index, = read_unpack(f, '<I')
        self.sub_section_offsets = read_unpack(f, f'<{self.num_vertexes * (self.num_lanes + self.num_sidewalks)}f')
        self.center_offsets = read_unpack(f, f'<{self.num_vertexes}f')
        self.intersection_ids = read_unpack(f, '<2I')
        self.lane_vertices = Vector3.readn(f, self.num_vertexes * (self.num_lanes + self.num_sidewalks))

        # Center / Dividing line between the two sides of the road
        self.center_vertices = Vector3.readn(f, self.num_vertexes, '<')
        self.vert_x_dirs = Vector3.readn(f, self.num_vertexes, '<')
        self.normals = Vector3.readn(f, self.num_vertexes, '<')
        self.vert_z_dirs = Vector3.readn(f, self.num_vertexes, '<')
        self.sub_section_dirs = Vector3.readn(f, self.num_vertexes, '<')

        # Outer Edges, Inner Edges (Curb)
        self.boundaries = Vector3.readn(f, self.num_vertexes * 2, '<')

        # Inner Edges on the opposite side of the road
        self.l_boundaries = Vector3.readn(f, self.num_vertexes, '<')
        self.stop_light_pos = Vector3.readn(f, 2, '<')
        self.lane_widths = read_unpack(f, '<5f')
        self.lane_lengths = read_unpack(f, '<10f')

    def read(f: BinaryIO) -> 'aiStreet':
        result = aiStreet()
        result.load(f)
        return result

###################################################################################################################?

class aiIntersection:
    def load(self, f: BinaryIO) -> None:
        self.id, = read_unpack(f, '<H')
        self.position = Vector3.read(f, '<')

        num_sinks, = read_unpack(f, '<H')
        self.sinks = read_unpack(f, f'<{num_sinks}I')

        num_sources, = read_unpack(f, '<H')
        self.sources = read_unpack(f, f'<{num_sources}I')

        self.paths = read_unpack(f, f'<{num_sinks + num_sources}I')
        self.directions = read_unpack(f, f'<{num_sinks + num_sources}f')

    @staticmethod
    def read(f: BinaryIO) -> 'aiIntersection':
        result = aiIntersection()
        result.load(f)
        return result

###################################################################################################################?

def read_array_list(f) -> List[int]:
    num_items, = read_unpack(f, '<I')
    return read_unpack(f, f'<{num_items}I')


class aiMap:
    def __init__(self):
        self.paths = []
        self.intersections = []
        self.ambient_roads = []
        self.ped_roads = []

    def load(self, f: BinaryIO) -> None:
        num_isects, num_paths = read_unpack(f, '<2H')

        print(f"{num_paths} roads, {num_isects} isects")

        for _ in range(num_paths):
            self.paths.append(aiStreet.read(f))

        for _ in range(num_isects):
            self.intersections.append(aiIntersection.read(f))

        num_cells, = read_unpack(f, '<I')

        for _ in range(num_cells):
            self.ambient_roads.append(read_array_list(f))

        for _ in range(num_cells):
            self.ped_roads.append(read_array_list(f))


    def read(f: BinaryIO) -> 'aiMap':
        result = aiMap()
        result.load(f)
        return result
    
###################################################################################################################?

class MiniParser:
    def __init__(self, file):
        self.file = file
        self.indent = 0
        self.newline = False

    def print(self, data):
        if self.newline:
            self.file.write(' ' * (self.indent * 4))
            self.newline = False

        self.file.write(data)
        if data.endswith('\n'):
            self.newline = True

    def begin_class(self, name):
        self.print(f'{name} :0 {{\n')
        self.indent += 1

    def value(self, value):
        if isinstance(value, list):
            self.print('[\n')
            self.indent += 1
            for val in value:
                self.value(val)
                self.print('\n')
            self.indent -= 1
            self.print(']')
            
        elif isinstance(value, str):            
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            self.print(f'"{escaped_value}"')
            
        elif isinstance(value, int):
            self.print(str(value))
            
        elif isinstance(value, float):
            self.print(f"{value:.2f}")
                    
        elif isinstance(value, tuple):
            formatted_values = ', '.join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in value)
            self.print(f'({formatted_values})')
                                
        elif isinstance(value, Vector3):
            self.print(f'{value.x:.2f} {value.y:.2f} {value.z:.2f}')
            
        else:
            raise Exception(f'Invalid Value Type {type(value)}')

    def field(self, name, value):
        self.print(f'{name} ')
        self.value(value)
        self.print('\n')

    def end_class(self):
        self.indent -= 1
        self.print('}\n')

###################################################################################################################?

def read_ai(input_file: Path):
    ai_map = aiMap()

    with open(input_file, "rb") as f:
        ai_map.load(f)

        here = f.tell()
        f.seek(0, 2)
        assert here == f.tell()

    streets = []
    
    for i, path in enumerate(ai_map.paths):
        assert i == path.id  # ID matches path index      
        assert path.id != path.oncoming_path  # A path should not be its own oncoming
        assert ai_map.paths[path.oncoming_path].oncoming_path == path.id  # A path should be properly linked with its oncoming
        assert path.num_sidewalks in [0, 1]  # No more than 1 sidewalk per road-side

        assert path.intersection_type in [
            IntersectionType.STOP, 
            IntersectionType.STOP_LIGHT, 
            IntersectionType.YIELD, 
            IntersectionType.CONTINUE
            ]  
        
        # TODO: adjust or remove this (i.e. get the actual object name)
        if path.intersection_type == IntersectionType.STOP:
            assert path.stop_light_name == Prop.STOP_SIGN  
        else:
            assert path.stop_light_name in [Prop.STOP_LIGHT_SINGLE, Prop.STOP_LIGHT_DUAL]   

        sink_isect = path.lane_vertices[0]
        source_isect = path.lane_vertices[path.num_vertexes - 1]

        for lane in range(1, path.num_lanes):
            here = lane * path.num_vertexes
            assert path.lane_vertices[here] == sink_isect
            assert path.lane_vertices[here + path.num_vertexes - 1] == source_isect

        if path.num_sidewalks == 0:  # Only custom paths should have no sidewalks
            assert all(v == Vector3(0, 1, 0) for v in path.normals)  # If there are no sidewalks, all normals are straight up

        isect_id = path.intersection_ids[0]
        isect = ai_map.intersections[isect_id]

        has_sink = False
        for isect_path in isect.paths:
            if isect_path != path.id:
                isect_path = ai_map.paths[isect_path]
                if isect_path.intersection_ids[0] != isect_id and isect_path.oncoming_path != path.id:
                    has_sink = True
                    break
                
        if not has_sink:
            print(f"No eligible roads identified to turn onto from road: {path.id}.")

        if path.id < path.oncoming_path:
            streets.append((f"Street{len(streets)}", (path, ai_map.paths[path.oncoming_path])))

    assert len(streets) * 2 == len(ai_map.paths)
    
    return ai_map, streets


def write_ai_map_txt(streets, output_map_file: Path) -> None:
    with open(output_map_file, "w") as f:  
        
        parser = MiniParser(f)

        parser.begin_class("mmMapData")

        parser.field("NumStreets", len(streets))
        parser.field("Street", ["Street" + str(paths[0].id) for _, paths in streets])

        parser.end_class() 
        
        
def write_ai_intersections_txt(ai_map, file_path_pattern: Path) -> None:
    for intersection in ai_map.intersections:        
        
        output_files = Path(file_path_pattern.format(intersection_id = intersection.id))
        
        with open(output_files, 'w') as f: 
                    
            parser = MiniParser(f)
    
            parser.begin_class("mmIntersection")

            parser.field("ID", intersection.id)
            parser.field("Position", intersection.position)

            parser.field("NumSinks", len(intersection.sinks))
            parser.field("Sinks", intersection.sinks)

            parser.field("NumSources", len(intersection.sources))
            parser.field("Sources", intersection.sources)

            parser.field("Paths", intersection.paths)
            parser.field("Directions", intersection.directions)

            parser.end_class()

 
        
def validate_and_prepare_ai_paths(streets) -> List[Any]:
    prepared_data = []

    for _, paths in streets:
        assert paths[0].num_vertexes == paths[1].num_vertexes
        assert paths[0].num_sidewalks == paths[1].num_sidewalks
        assert paths[0].divided == paths[1].divided
        assert paths[0].alley == paths[1].alley
        assert paths[0].normals == list(reversed(paths[1].normals))
        assert paths[0].normals[0] == Vector3(0, 1, 0)
        assert paths[0].normals[-1] == Vector3(0, 1, 0)

        if paths[0].num_sidewalks != 0:
            for n in range(1, len(paths[0].normals) - 1):
                target = paths[0].normals[n]

                a = paths[0].lane_vertices[n]
                b = paths[0].boundaries[paths[0].num_vertexes + n - 1]
                c = paths[0].boundaries[paths[0].num_vertexes + n]

                normal = calc_normal(a, b, c)
                angle = math.degrees(target.Angle(normal))

                if angle > 0.01:
                    print(f"Road {paths[0].id} has suspicious normal {n}: Expected {target}, Calculated {normal} ({angle:.2f} degrees error)")

            for road in range(2):
                path = paths[road]

                assert path.boundaries[path.num_vertexes:] == list(reversed(paths[road ^ 1].l_boundaries))

                for i in range(path.num_vertexes):
                    a = path.lane_vertices[i + (path.num_lanes * path.num_vertexes)]
                    b = (path.boundaries[i] + path.boundaries[i + path.num_vertexes]) * 0.5
                    assert a.Dist2(b) < 0.00001
        
        prepared_data.append(paths)
    
    return prepared_data



def write_ai_paths(prepared_data: List[Any], file_path_pattern: Path) -> None:
    for paths in prepared_data:
        output_road_files = Path(file_path_pattern.format(paths = paths[0].id))
                
        with open(output_road_files, "w") as f:
            parser = MiniParser(f)
    
            parser.begin_class("mmRoadSect")

            parser.field("NumVertexs", paths[0].num_vertexes)

            parser.field("NumLanes[0]", paths[0].num_lanes)
            parser.field("NumLanes[1]", paths[1].num_lanes)

            parser.field("NumSidewalks[0]", paths[0].num_sidewalks * 2)
            parser.field("NumSidewalks[1]", paths[1].num_sidewalks * 2)

            all_vertexs = []

            for road in range(2):
                path = paths[road]
                split = path.num_lanes * path.num_vertexes
                all_vertexs += path.lane_vertices[0:split]

            if path.num_sidewalks:
                for road in range(2):
                    path = paths[road]
                    all_vertexs += path.boundaries

            expected_count = paths[0].num_vertexes * (paths[0].num_lanes + paths[1].num_lanes + (paths[0].num_sidewalks + paths[1].num_sidewalks) * 2)

            assert len(all_vertexs) == expected_count

            parser.field("TotalVertexs", len(all_vertexs))
            parser.field("Vertexs", all_vertexs)
            parser.field("Normals", paths[0].normals)

            # Yes, these are "supposed" to be backwards
            parser.field("IntersectionType[0]", paths[1].intersection_type)
            parser.field("IntersectionType[1]", paths[0].intersection_type)
            parser.field("StopLightPos[0]", paths[1].stop_light_pos[0])
            parser.field("StopLightPos[1]", paths[1].stop_light_pos[1])
            parser.field("StopLightPos[2]", paths[0].stop_light_pos[0])
            parser.field("StopLightPos[3]", paths[0].stop_light_pos[1])
            
            parser.field("StopLightIndex", paths[0].stop_light_index)
        
            parser.field("Blocked[0]", paths[0].blocked)
            parser.field("Blocked[1]", paths[1].blocked)

            parser.field("PedBlocked[0]", paths[0].ped_blocked)
            parser.field("PedBlocked[1]", paths[1].ped_blocked)

            # Yes, these are "supposed" to be backwards
            parser.field("StopLightName", [paths[1].stop_light_name, paths[0].stop_light_name])

            parser.field("Divided", paths[0].divided)       
            parser.field("Alley", paths[0].alley)
            parser.field("IsFlat", paths[0].is_flat)
            parser.field("HasBridge", paths[0].has_bridge)
            parser.field("SpeedLimit", paths[0].speed_limit)
            
            parser.field("ID", paths[0].id)
            parser.field("OncomingPath", paths[0].oncoming_path)
            parser.field("PathIndex", paths[0].path_index)
            parser.field("EdgeIndex", paths[0].edge_index)
            parser.field("IntersectionIds", paths[0].intersection_ids)
                        
            parser.field("VertXDirs", paths[0].vert_x_dirs)
            parser.field("VertZDirs", paths[0].vert_z_dirs)
            parser.field("SubSectionDirs", paths[0].sub_section_dirs)
            
            parser.field("CenterOffsets", paths[0].center_offsets)
            parser.field("SubSectionOffsets", paths[0].sub_section_offsets)
                    
            parser.field("RoadLength", paths[0].road_length)
            parser.field("LaneWidths", paths[0].lane_widths)
            parser.field("LaneLengths", paths[0].lane_lengths)
            
            parser.end_class()

            
                    
def debug_ai(input_file: Path, debug_file: bool, output_map_file: Path, output_int_files: Path, output_road_files: Path) -> None:
    if not debug_file:
        return
        
    ai_map, streets = read_ai(input_file)
    
    write_ai_map_txt(streets, output_map_file)
    
    paths = validate_and_prepare_ai_paths(streets)
    write_ai_paths(paths, output_road_files)
    
    write_ai_intersections_txt(ai_map, output_int_files)
        
#! ############ Code by 0x1F9F1 (Modified) // end ############ !#         

###################################################################################################################
###################################################################################################################
#! ======================= BAI MAP ======================= !#


class BaiMap:
    def __init__(self, street_names):
        self.map_filename = MAP_FILENAME
        self.street_names = street_names
        self.write_map()
             
    def write_map(self):           
        with open(Folder.BASE / "dev" / "CITY" / self.map_filename / f"{self.map_filename}.map", 'w') as f:
            f.write(self.map_template())
    
    def map_template(self):
        map_streets = '\n\t\t'.join([f'"{street}"' for street in self.street_names])
        
        map_data = f"""
mmMapData :0 {{
    NumStreets {len(self.street_names)}
    Street [
        {map_streets}
    ]
}}
        """
        return textwrap.dedent(map_data).strip()
       
###################################################################################################################
###################################################################################################################
#! ======================= AI STREET EDITOR ======================= !#


class aiStreetEditor:
    def __init__(self, data, set_reverse_ai_streets: bool):
        self.map_filename = MAP_FILENAME
        self.street_name = data["street_name"]
        self.set_reverse_ai_streets = set_reverse_ai_streets
        self.process_lanes(data)
        self.set_properties(data)
                    
    def process_lanes(self, data):
        if "lanes" in data:
            self.original_lanes = data["lanes"]
        elif "vertices" in data:
            self.original_lanes = {"lane_1": data["vertices"]}
        else:
            raise ValueError("Street data must have either 'lanes' or 'vertices'")

        # Add reverse lanes if set by the user
        self.lanes = self.original_lanes.copy()
        if self.set_reverse_ai_streets:
            for key, values in self.original_lanes.items():
                self.lanes[key].extend(values[::-1])
                        
    def set_properties(self, data):
        default_values = {
            "intersection_types": [IntersectionType.CONTINUE, IntersectionType.CONTINUE],
            "stop_light_positions": [(0.0, 0.0, 0.0)] * 4,
            "stop_light_names": [Prop.STOP_LIGHT_SINGLE, Prop.STOP_LIGHT_SINGLE],
            "traffic_blocked": [NO, NO],
            "ped_blocked": [NO, NO],
            "road_divided": NO,
            "alley": NO,
        }

        for key, default in default_values.items():
            setattr(self, key, data.get(key, default))
            
    @classmethod
    def create(cls, dataset, set_ai_streets: bool, set_reverse_ai_streets: bool):
        if not set_ai_streets:
            return None

        street_names = []
        
        for data in dataset:
            editor = cls(data, set_reverse_ai_streets)
            editor.write()
            street_names.append(editor.street_name)

        return BaiMap(street_names)

    def write(self):    
        with open(Folder.BASE / "dev" / "CITY" / self.map_filename  / f"{self.street_name}.road", 'w') as f:
            f.write(self.set_template())

    def set_template(self):
        lane_one = list(self.lanes.keys())[0]  # Assuming all lanes have the same number of vertices
        num_vertices_per_lane = len(self.original_lanes[lane_one])
        num_total_vertices = num_vertices_per_lane * len(self.lanes) * (2 if self.set_reverse_ai_streets else 1)
        
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
    NumLanes[1] {len(self.lanes) if self.set_reverse_ai_streets else 0}
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
#! ======================= LARS RACE MAKER ======================= !#


def get_first_and_last_street_vertices(street_list):
    processed_vertices = []
    
    for street in street_list:
        vertices = street["vertices"]
        if vertices: 
            for vertex in (vertices[0], vertices[-1]):
                processed = [vertex[0], vertex[1], vertex[2], Rotation.AUTO, Width.LARGE, 0.0, 0.0, 0.0, 0.0]
                processed_vertices.append(processed)  


    vertices_set = set(tuple(v) for v in processed_vertices)
    unique_processed_vertices = [list(v) for v in vertices_set]
    
    return unique_processed_vertices


#! ############ Code by Lars (Modified) // start ############ !# 

def create_lars_race_maker(output_file: Path, street_list, hudmap_vertices: List[Vector3], set_lars_race_maker: bool) -> None:  
    if not set_lars_race_maker:
        return

    min_x, max_x, min_z, max_z = calculate_extrema(hudmap_vertices)
    
    canvas_width = int(max_x - min_x)
    canvas_height = int(max_z - min_z)

    vertices_processed = get_first_and_last_street_vertices(street_list)
    vertices_string = ",\n".join([str(coord) for coord in vertices_processed])

    template = f"""
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
<body>
    <img id = "scream" width = "{canvas_width}" height = "{canvas_height}" src = "{MAP_FILENAME}_HUD_debug.jpg" alt = "The Scream" style = "display:none;">
    <canvas id = "myCanvas" width = "{canvas_width}" height = "{canvas_height}" style = "background-color: #2b2b2b;">
        Your browser does not support the HTML5 canvas tag.
    </canvas>
    <div id="out"></div>

    <script>
    var MIN_X = {min_x};
    var MAX_X = {max_x};
    var MIN_Z = {min_z};
    var MAX_Z = {max_z};
    var coords = [{vertices_string}];

    function mapRange(value, in_min, in_max, out_min, out_max) {{
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
    }}

    window.onload = function() {{
        var canvas = document.getElementById("myCanvas");
        var ctx = canvas.getContext("2d");
        var img = document.getElementById("scream");
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        for (var i = 0; i < coords.length; i++) {{
            ctx.lineWidth = "10";
            ctx.strokeStyle = "blue";
            ctx.beginPath();
            let mappedX = mapRange(coords[i][0], MIN_X, MAX_X, 0, canvas.width);
            let mappedZ = mapRange(coords[i][2], MIN_Z, MAX_Z, 0, canvas.height);
            ctx.arc(mappedX, mappedZ, 5, 0, 2 * Math.PI);
            ctx.fill();
        }}
    }};

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

    const canvas = document.getElementById('myCanvas');
    canvas.addEventListener('mousedown', function(e) {{
        getCursorPosition(canvas, e);
    }});
    </script>
</body>
</html>
    """

    with open(output_file, "w") as f:
        f.write(template)

#! ################# Code by Lars (Modified) // end ################# !# 

###################################################################################################################
###################################################################################################################  
#! ======================= FINALIZING FUNCTIONS ======================= !#


def create_ar(shop_folder: Path) -> None:
    for file in Path("angel").iterdir():
        if file.name in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(file, shop_folder / file.name)
            
    subprocess.Popen(f"cmd.exe /c run !!!!!{MAP_FILENAME}", cwd = shop_folder, creationflags = subprocess.CREATE_NO_WINDOW)


def post_editor_cleanup(delete_shop: bool) -> None:
    if not delete_shop:
        return
    
    os.chdir(Folder.BASE)
    time.sleep(1)  # Make sure the SHOP folder is no longer in use (i.e. an .ar file is still being created)

    try:  
        shutil.rmtree(Folder.BASE / "build")
    except Exception as e:
        print(f"Failed to delete the BUILD directory. Reason: {e}")

    try:
        shutil.rmtree(Folder.SHOP)
    except Exception as e:
        print(f"Failed to delete the SHOP directory. Reason: {e}")

   
def create_commandline(
    mm1_folder: Path, no_ui: bool, no_ui_type: str, 
    no_ai: bool, less_logs: bool, more_logs: bool) -> None:

    base_cmd = f"-path ./dev -allrace -allcars -f -heapsize 499 -multiheap -maxcops 100 -mousemode 1 -speedycops -l {MAP_FILENAME.lower()}"

    if less_logs and more_logs:    
        log_error_message = f"""\n
        ***ERROR***
        You can't have both 'quiet' and 'more logs' enabled. Please choose one."
        """
        raise ValueError(log_error_message)
    
    if less_logs:
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
                Invalid Race Type provided. Available types are {RaceMode.BLITZ}, {RaceMode.CHECKPOINT}, and {RaceMode.CIRCUIT}.
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
    
    with open(mm1_folder / "commandline.txt", "w") as f:
        f.write(processed_cmd)
        
        
def is_game_running(process_name: str) -> bool:
    for proc in psutil.process_iter(["name"]):
        if process_name.lower() in proc.info["name"].lower():
            return True
    return False
      

def start_game(mm1_folder: str, executable: str, play_game: bool) -> None:    
    if not play_game or is_blender_running() or is_game_running(executable):  # This order is important
        return
    
    subprocess.run(mm1_folder / executable, cwd = mm1_folder)

###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER SETUP ======================= !#


def is_blender_running() -> bool:
    try:
        import bpy   
        _ = bpy.context.window_manager
        return True 
    except (AttributeError, ImportError):
        return False
    
    
def delete_existing_meshes() -> None:
    bpy.ops.object.select_all(action = "SELECT")
    bpy.ops.object.delete()


def enable_developer_extras() -> None:
    prefs = bpy.context.preferences
    view = prefs.view
    
    if not view.show_developer_ui:
        view.show_developer_ui = True
        bpy.ops.wm.save_userpref()
        print("Developer Extras enabled!")
    else:
        print("Developer Extras already enabled!")
        
        
def enable_vertex_snapping() -> None:
    bpy.context.tool_settings.use_snap = True
    bpy.context.tool_settings.snap_elements = {"VERTEX"}
    bpy.context.tool_settings.snap_target = "CLOSEST"  
        
           
def adjust_3D_view_settings() -> None:
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    
                    # Clip distance
                    space.clip_end = 5000.0
                    
                    # Set the shading mode to Solid
                    shading = space.shading
                    shading.type = "SOLID"
                    
                    # Uniform Lighting
                    shading.light = "FLAT"
                    shading.color_type = "TEXTURE"
                    
                    
def initialize_depsgraph_update_handler() -> None:    
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)


def setup_blender() -> None:
    if not is_blender_running():
        return
    
    delete_existing_meshes()
    enable_developer_extras()
    enable_vertex_snapping()
    adjust_3D_view_settings()
    initialize_depsgraph_update_handler()
    
###################################################################################################################
###################################################################################################################
#! ======================= BLENDER CREATE MODEL ======================= !#                   
                    
                        
def load_textures(input_folder: Path, load_all_textures: bool) -> None:
    for texture in input_folder.glob("*.dds"):
        texture_str = str(texture)
        
        if texture_str not in bpy.data.images:
            texture_image = bpy.data.images.load(texture_str)
        else:
            texture_image = bpy.data.images[texture_str]

        if load_all_textures:
            material_name = texture.stem
            if material_name not in bpy.data.materials:
                create_material_from_texture(material_name, texture_image)


def create_material_from_texture(material_name, texture_image):
    mat = bpy.data.materials.new(name = material_name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type = "ShaderNodeBsdfPrincipled")
    texture_node = nodes.new(type = "ShaderNodeTexImage")
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type = "ShaderNodeOutputMaterial")
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])     
    
    
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

    diffuse_shader = nodes.new(type = "ShaderNodeBsdfPrincipled")
    texture_node = nodes.new(type = "ShaderNodeTexImage")
    
    texture_image = bpy.data.images.load(str(texture_path))  # Converting to String is necessary    
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type = "ShaderNodeOutputMaterial")
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])

    unwrap_uv_to_aspect_ratio(obj, texture_image)
    
       
def create_mesh_from_polygon_data(polygon_data, texture_folder = None):
    name = f"P{polygon_data['bound_number']}"
    bound_number = polygon_data["bound_number"]
    script_vertices = polygon_data["vertex_coordinates"]

    transformed_vertices = [transform_coordinate_system(Vector3.from_tuple(vertex), game_to_blender = True) for vertex in script_vertices]
    
    edges = []
    faces = [range(len(transformed_vertices))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    obj["cell_type"] = str(polygon_data["cell_type"])
    obj["material_index"] = str(polygon_data["material_index"])
    
    set_hud_checkbox(polygon_data["hud_color"], obj)
    
    for vertex in transformed_vertices:
        vertex_item = obj.vertex_coords.add()
        vertex_item.x, vertex_item.y, vertex_item.z = vertex
    
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(transformed_vertices, edges, faces)
    mesh.update()
    
    custom_properties = ["sort_vertices", "cell_type", "hud_color", "material_index", "always_visible"]
    
    for custom_prop in custom_properties:
        if custom_prop in polygon_data:
            obj[custom_prop] = polygon_data[custom_prop]
    
    if not obj.data.uv_layers:
        obj.data.uv_layers.new()

    # Retrieve the original UVs after creating the object and before tiling
    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in obj.data.uv_layers.active.data]
    obj["original_uvs"] = original_uvs
    
    bpy.types.Object.tile_x = bpy.props.FloatProperty(name = "Tile X", default = 2.0, update = update_uv_tiling)
    bpy.types.Object.tile_y = bpy.props.FloatProperty(name = "Tile Y", default = 2.0, update = update_uv_tiling)
    bpy.types.Object.rotate = bpy.props.FloatProperty(name = "Rotate", default = 0.0, update = update_uv_tiling)
    
    if bound_number in texcoords_data.get("entries", {}):
        obj.tile_x = texcoords_data["entries"][bound_number].get("tile_x", 1)
        obj.tile_y = texcoords_data["entries"][bound_number].get("tile_y", 1)
        obj.rotate = texcoords_data["entries"][bound_number].get("angle_degrees", 5)
    else:
        obj.tile_x = 2
        obj.tile_y = 2
        obj.rotate = 0.1
        
    if texture_folder:
        apply_texture_to_object(obj, texture_folder)    
        tile_uvs(obj, obj.tile_x, obj.tile_y)
        rotate_uvs(obj, obj.rotate)  
        
        obj.data.update()
            
    return obj


def create_blender_meshes(texture_folder: Path, load_all_textures: bool) -> None:
    if not is_blender_running():
        return

    load_textures(texture_folder, load_all_textures)

    textures = [texture_folder / f"{texture_name}.DDS" for texture_name in texture_names]

    for poly, texture in zip(polygons_data, textures):
        create_mesh_from_polygon_data(poly, texture)
    
###################################################################################################################
###################################################################################################################
#! ======================= BLENDER UV MAPPING ======================= !#


def unwrap_uv_to_aspect_ratio(obj, image):
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    
    bpy.ops.uv.unwrap(method = 'ANGLE_BASED', margin = 0.001)
    
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

     
def update_uv_tiling(self, context: bpy.types.Context) -> None:
    bpy.ops.object.select_all(action = 'DESELECT')
    self.select_set(True)
    bpy.context.view_layer.objects.active = self

    tile_uvs(self, self.tile_x, self.tile_y)
    rotate_uvs(self, self.rotate)

    
# UV MAPPING OPERATOR
class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            
            # Check if the object has the necessary custom properties
            if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "angle_degrees"]):
                
                tile_uvs(obj, obj["tile_x"], obj["tile_y"])
                rotate_uvs(obj, obj["angle_degrees"])

        return {"FINISHED"}
                        
###################################################################################################################
###################################################################################################################

TEXTURE_EXPORT = {
    "SNOW": Texture.SNOW,
    "T_WOOD": Texture.WOOD,
    "T_WATER": Texture.WATER,
    "T_WATER_WIN": Texture.WATER_WINTER,
    "T_GRASS": Texture.GRASS,
    "T_GRASS_WIN": Texture.GRASS_WINTER,
    "24_GRASS": Texture.GRASS_BASEBALL,
    "SDWLK2": Texture.SIDEWALK,
    "RWALK": Texture.ZEBRA_CROSSING,
    "RINTER": Texture.INTERSECTION,
    "FREEWAY2": Texture.FREEWAY,
    "R2": Texture.ROAD_1_LANE,
    "R4": Texture.ROAD_2_LANE,
    "R6": Texture.ROAD_3_LANE,
    "OT_MALL_BRICK": Texture.BRICKS_MALL,
    "OT_SHOP03_BRICK": Texture.BRICKS_SAND,
    "CT_FOOD_BRICK": Texture.BRICKS_GREY,
    "R_WIN_01": Texture.GLASS,
    "T_STOP": Texture.STOP_SIGN,
    "T_BARRICADE": Texture.BARRICADE,
    "CHECK04": Texture.CHECKPOINT,
    "VPBUSRED_TP_BK": Texture.BUS_RED_TOP,
}

###################################################################################################################
###################################################################################################################
#! ======================= BLENDER PANELS ======================= !#


CELL_IMPORT = [
    (str(Room.DEFAULT), "Default", "", "", Room.DEFAULT),
    (str(Room.TUNNEL), "Tunnel", "", "", Room.TUNNEL),
    (str(Room.INDOORS), "Indoors", "", "", Room.INDOORS),
    (str(Room.DRIFT), "Drift", "", "", Room.DRIFT),
    (str(Room.NO_SKIDS), "No Skids", "", "", Room.NO_SKIDS)
    ]

bpy.types.Object.cell_type = bpy.props.EnumProperty(
    items = CELL_IMPORT,
    name = "Cell Type",
    description = "Select the type of cell"
    )

CELL_EXPORT = {
    str(Room.TUNNEL): "Room.TUNNEL",
    str(Room.INDOORS): "Room.INDOORS",
    str(Room.DRIFT): "Room.DRIFT",
    str(Room.NO_SKIDS): "Room.NO_SKIDS"
}

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
            
###################################################################################################################?

MATERIAL_IMPORT = [
    (str(Material.DEFAULT), "Road", "", "", Material.DEFAULT),
    (str(Material.GRASS), "Grass", "", "", Material.GRASS),
    (str(Material.WATER), "Water", "", "", Material.WATER),
    (str(Material.STICKY), "Sticky", "", "", Material.STICKY),
    (str(Material.NO_FRICTION), "No Friction", "", "", Material.NO_FRICTION)
    ]

bpy.types.Object.material_index = bpy.props.EnumProperty(
    items = MATERIAL_IMPORT,
    name = "Material Type",
    description = "Select the type of material"
    )

MATERIAL_EXPORT = {
    str(Material.GRASS): "Material.GRASS",
    str(Material.WATER): "Material.WATER",
    str(Material.STICKY): "Material.STICKY",
    str(Material.NO_FRICTION): "Material.NO_FRICTION"
    }

class OBJECT_PT_MaterialTypePanel(bpy.types.Panel):
    bl_label = "Material Type"
    bl_idname = "OBJECT_PT_material_index"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context) -> None:
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "material_index", text = "Material")
        else:
            layout.label(text = "No active object")

###################################################################################################################?

HUD_IMPORT = [
    (Color.ROAD, "Road", "", "", 1),
    (Color.GRASS, "Grass", "", "", 2),
    (Color.WATER, "Water", "", "", 3),
    (Color.SNOW, "Snow", "", "", 4),
    (Color.WOOD, "Wood", "", "", 5),
    (Color.ORANGE, "Orange", "", "", 6),
    (Color.RED_LIGHT, "Light Red", "", "", 7),
    (Color.RED_DARK, "Dark Red", "", "", 8),
    (Color.YELLOW_LIGHT, "Light Yellow", "", "", 9)
    ]

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
    # '#414441': "Color.ROAD",
    '#7b5931': "Color.WOOD",
    '#cdcecd': "Color.SNOW",
    '#5d8096': "Color.WATER",
    '#396d18': "Color.GRASS",
    '#af0000': "Color.RED_DARK",
    '#ffa500': "Color.ORANGE",
    '#ff7f7f': "Color.RED_LIGHT",
    '#ffffe0': "Color.YELLOW_LIGHT"
    }

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

###################################################################################################################?

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
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "always_visible", text = "Always Visible")
            layout.prop(obj, "sort_vertices", text = "Sort Vertices")
        else:
            layout.label(text = "No active object")
            
###################################################################################################################?
            
def update_vertex_coordinates(self, context):
    obj = self.id_data
    if obj and hasattr(obj.data, "vertices"):
        for index, coord in enumerate(obj.vertex_coords):
            if len(obj.data.vertices) > index:
                obj.data.vertices[index].co = (coord.x, coord.y, coord.z)
        obj.data.update()


class VertexGroup(bpy.types.PropertyGroup):
    x: bpy.props.FloatProperty(name = "X", update = update_vertex_coordinates)
    y: bpy.props.FloatProperty(name = "Y", update = update_vertex_coordinates)
    z: bpy.props.FloatProperty(name = "Z", update = update_vertex_coordinates)
    
    
class OBJECT_PT_VertexCoordinates(bpy.types.Panel):
    bl_label = "Vertices"
    bl_idname = "OBJECT_PT_vertex_coordinates"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
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
#! ======================= BLENDER POLYGON EXPORT ======================= !#


def format_decimal(value: Union[int, float]) -> str:
    if value == int(value): 
        return f"{value:.1f}"
    else: 
        return f"{value:.2f}"

    
def validate_and_extract_bound_number(name: str) -> int:
    if name.startswith("P"):
        return int(name[1:])
    elif name.startswith("Shape_"):
        return int(name.split("_")[1])
    else:
        raise ValueError(f"Unrecognized Polygon Name Format: {name}")
    
    
def extract_polygon_data(obj: bpy.types.Object) -> Dict[str, Union[int, str, bool, list]]:
    bound_number = validate_and_extract_bound_number(obj.name)
    
    extracted_polygon_data = {
        "bound_number": bound_number,
        "material_index": obj["material_index"],
        "cell_type": obj["cell_type"],
        "always_visible": obj["always_visible"], 
        "sort_vertices": obj["sort_vertices"],
        "vertex_coordinates": obj.data.vertices,
        "hud_color": obj["hud_color"],
        "rotate": obj["rotate"]
        }
    
    return extracted_polygon_data


def extract_polygon_texture(obj) -> str:
    if obj.material_slots:
        mat = obj.material_slots[0].material
        
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    return os.path.splitext(node.image.name)[0].replace(".DDS", "").replace(".dds", "")
                
    return Texture.CHECKPOINT  # Default value


def format_texture_name(texture_name: str) -> str:
    texture_constant = TEXTURE_EXPORT.get(texture_name, texture_name)
    return next((f'Texture.{name}' for name, value in vars(Texture).items() if value == texture_constant), f'"{texture_name}"')


def format_vertices(vertices: List[bpy.types.MeshVertex]) -> str:
    formatted_vertices = []
    
    for vertex in vertices:
        transformed_vertex = transform_coordinate_system(vertex.co, blender_to_game = True)
        formatted_vertex = f"({', '.join(format_decimal(comp) for comp in transformed_vertex)})"
        formatted_vertices.append(formatted_vertex)
        
    return ",\n\t\t".join(formatted_vertices)


def gather_optional_variables(poly_data: Dict[str, Union[int, str, bool, list]], obj: bpy.types.Object) -> str:
    optional_vars = []
    
    cell_type = CELL_EXPORT.get(str(poly_data["cell_type"]), None)
    material_index = MATERIAL_EXPORT.get(str(poly_data["material_index"]), None)
    hud_color = HUD_EXPORT.get(next((HUD_IMPORT[index][0] for index, checked in enumerate(obj.hud_colors) if checked), None), None)
        
    if cell_type:
        optional_vars.append(f"cell_type = {cell_type}")
    
    if material_index:
        optional_vars.append(f"material_index = {material_index}")
    
    if hud_color:
        optional_vars.append(f"hud_color = {hud_color}")

    if poly_data["sort_vertices"]:
        optional_vars.append("sort_vertices = True")
        
    if not poly_data["always_visible"]:
        optional_vars.append("always_visible = False")
        
    return ",\n\t".join(optional_vars) + ("," if optional_vars else "")


def export_formatted_polygons(obj: bpy.types.Object) -> str:
    poly_data = extract_polygon_data(obj)
    texture_name = extract_polygon_texture(obj).upper()
    formatted_texture = format_texture_name(texture_name)
    formatted_vertices = format_vertices(poly_data["vertex_coordinates"])
    optional_variables_str = gather_optional_variables(poly_data, obj)

    tile_x = obj.get("tile_x", 1)
    tile_y = obj.get("tile_y", 1)
    rotation = poly_data.get("rotate", 999.0)
    
    if optional_variables_str:
        optional_variables_str = f"\n\t{optional_variables_str}"
    
    template = f"""
create_polygon(
    bound_number = {poly_data['bound_number']},{optional_variables_str}
    vertex_coordinates = [
        {formatted_vertices}])

save_mesh(
    texture_name = [{formatted_texture}],
    tex_coords = compute_uv(bound_number = {poly_data['bound_number']}, tile_x = {tile_x:.2f}, tile_y = {tile_y:.2f}, angle_degrees = {rotation:.2f}))
"""

    return template


class OBJECT_OT_ExportPolygons(bpy.types.Operator):
    bl_idname = "object.export_polygons"
    bl_label = "Export Blender Polygons"
    
    select_all: bpy.props.BoolProperty(default = True)

    def execute(self, context: bpy.types.Context) -> Set[set]:            
        output_folder = Folder.BASE / "Polygon Export"
        output_folder.mkdir(exist_ok = True)
                
        current_time = datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
        export_file = output_folder / f"Polygons_{current_time}.txt"
                            
        # Select Mesh Objects based on the "select_all" property
        if self.select_all:
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        else:
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
            
        if not mesh_objects:
            self.report({"WARNING"}, "No mesh objects found for export.")
            return {"CANCELLED"}
        
        # Set the first mesh object as the active object and apply transformations (to get Global coordinates)
        context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    
        try:
            with open(export_file, "w") as f:
                for obj in mesh_objects:
                    export_script = export_formatted_polygons(obj) 
                    f.write(export_script + "\n\n")
                    
            # Open the file with Notepad++ and simulate copy to clipboard
            open_with_notepad_plus(export_file)                                
            time.sleep(1.0)  # Give Notepad++ time to load the file
            pyautogui.hotkey("ctrl", "a")
            pyautogui.hotkey("ctrl", "c")
            
            self.report({"INFO"}, f"Saved data to {export_file}")
            bpy.ops.object.select_all(action = "DESELECT")
            
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export polygons: {str(e)}")
            return {"CANCELLED"}
        
        return {"FINISHED"}
    
###################################################################################################################   
###################################################################################################################    
#! ======================= BLENDER MISC OPERATORS ======================= !#


CUSTOM_PROPERTIES_CONFIG_DEFAULT = {
    "cell_type": Room.DEFAULT,
    "material_index": Material.DEFAULT,
    "hud_color": Color.ROAD,
    "sort_vertices": NO,
    "always_visible": YES,
    "tile_x": 2.0,
    "tile_y": 2.0,
    "rotate": 0.01
}


class OBJECT_OT_AssignCustomProperties(bpy.types.Operator):
    bl_idname = "object.assign_custom_properties"
    bl_label = "Assign Custom Properties to Polygons"
    bl_description = "Assign Custom Properties to polygons that do not have them yet"
    bl_options = {"REGISTER", "UNDO"}

    def assign_defaults(self, obj: bpy.types.Object, property_name: str, default_value: any) -> None:
        if property_name not in obj:
            obj[property_name] = default_value

    def execute(self, context: bpy.types.Context) -> set:
        for obj in context.scene.objects:
            if obj.type == "MESH":
                for prop_name, default_value in CUSTOM_PROPERTIES_CONFIG_DEFAULT.items():
                    self.assign_defaults(obj, prop_name, default_value)

                uv_layer = obj.data.uv_layers.active
                
                if uv_layer is None:
                    uv_layer = obj.data.uv_layers.new(name = "UVMap")
                    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in uv_layer.data]
                    obj["original_uvs"] = original_uvs

        self.report({"INFO"}, "Assigned Custom Properties")
        return {"FINISHED"}
    
###################################################################################################################?

class OBJECT_OT_ProcessPostExtrude(bpy.types.Operator):
    bl_idname = "object.process_post_extrude"
    bl_label = "Process Post Extrude"
    bl_options = {"REGISTER", "UNDO"}
    
    triangulate: bpy.props.BoolProperty(name = "Triangulate", default = False)

    def execute(self, context: bpy.types.Context) -> set:
        if context.object and context.object.type == "MESH":
            bpy.ops.object.mode_set(mode = "EDIT")
            bpy.ops.mesh.select_all(action = "SELECT")
            
            if self.triangulate:
                bpy.ops.mesh.quads_convert_to_tris()
            
            bpy.ops.mesh.edge_split()
            bpy.ops.mesh.separate(type = "LOOSE")
            bpy.ops.object.mode_set(mode = "OBJECT")
            self.report({"INFO"}, "Processed Post Extrude")
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, "No mesh object selected")
            return {"CANCELLED"}
    
    
###################################################################################################################? 

class OBJECT_OT_RenameChildren(bpy.types.Operator):
    bl_idname = "object.auto_rename_children"
    bl_label = "Auto Rename Children Objects"

    def execute(self, context: bpy.types.Context) -> set:
        polygons = [obj for obj in context.scene.objects if re.match(r"^P\d+$", obj.name)]

        polygons.sort(key = lambda x: int(re.search(r"\d+", x.name).group(0)))

        new_index = 1
        for obj in polygons:
            if new_index == Threshold.CELL_TYPE_SWITCH:  # Skip the index 200
                new_index += 1
            obj.name = f"P{new_index}"
            new_index += 1

        self.report({"INFO"}, "Renamed Polygons")
        return {"FINISHED"}
            
###################################################################################################################   
################################################################################################################### 
#! ======================= BLENDER WAYPOINT OBJECTS / FUNCTIONS ======================= !#


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
        
         
def depsgraph_update_handler(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    if not is_blender_running():
        return
    
    if any(obj.name.startswith("WP_") for obj in bpy.data.objects):
        update_waypoint_colors()


def create_waypoint_material(name: str, color: Tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
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
                    rotation_deg: float = Rotation.NORTH, scale: float = Width.DEFAULT, name: Optional[str] = None, 
                    flag_color: Tuple[float, float, float, float] = Color.BLUE) -> bpy.types.Object:                
    
    if x is None or y is None or z is None:  # If x, y, or z is not provided, use the current cursor position
        cursor_location = bpy.context.scene.cursor.location.copy()
    else:
        cursor_location = Vector((x, y, z))  # If x, y, and z are provided, create a new location vector

    pole_height, pole_diameter = 3.0, 0.2 
    flag_width = scale            
  
    pole_one_location = (cursor_location.x - flag_width / 2, cursor_location.y, cursor_location.z + pole_height / 2)
    pole_two_location = (cursor_location.x + flag_width / 2, cursor_location.y, cursor_location.z + pole_height / 2)
    
    pole_one = create_waypoint_pole(pole_height, pole_diameter, pole_one_location, Color.WHITE) 
    pole_two = create_waypoint_pole(pole_height, pole_diameter, pole_two_location, Color.WHITE) 

    flag_height, flag_height_offset, flag_location =  0.8, 2.2, cursor_location

    flag = create_waypoint_flag(flag_width, flag_height, cursor_location.z, flag_height_offset, flag_location, flag_color)

    bpy.ops.object.select_all(action = 'DESELECT')
    pole_one.select_set(True)
    pole_two.select_set(True)
    flag.select_set(True)
    bpy.context.view_layer.objects.active = flag
    bpy.ops.object.join()

    waypoint = bpy.context.object    
    waypoint.rotation_euler.z = math.radians(rotation_deg)
    
    if name:
        waypoint.name = name
    else:
        waypoint.name = "WP_Default"

    # Calculate and set the midpoint as the origin
    midpoint = ((pole_one_location[0] + pole_two_location[0]) / 2, 
                (pole_one_location[1] + pole_two_location[1]) / 2, 
                cursor_location.z)
    
    bpy.context.scene.cursor.location = midpoint
    bpy.ops.object.origin_set(type = 'ORIGIN_CURSOR')

    # Reset the cursor location if x, y, z were not provided
    if x is None or y is None or z is None:
        bpy.context.scene.cursor.location = cursor_location
        
    update_waypoint_colors() 

    return waypoint


##############################################################################################################################################?


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def calculate_waypoint_rotation(x1: float, z1: float, x2: float, z2: float) -> float:
    dx = x2 - x1
    dz = z2 - z1
    rotation_rad = math.atan2(dx, dz) 
    return math.degrees(rotation_rad)


def get_waypoint_name(race_type: str, race_number: int, wp_idx: int) -> str:
    if race_type == RaceMode.CHECKPOINT:
        race_type_initial = 'R'
    elif race_type == RaceMode.CIRCUIT:
        race_type_initial = 'C'
    else:
        race_type_initial = 'B'
    return f"WP_{race_type_initial}{race_number}_{wp_idx}"


def load_waypoints_from_race_data(race_data: dict, race_type_input: str, race_number_input: int) -> None:
    race_key = f"{race_type_input}_{race_number_input}"  
    
    if race_key in race_data:
        waypoints = race_data[race_key]['waypoints']
        
        for index, waypoint_data in enumerate(waypoints):
            x, y, z, rotation, scale = waypoint_data
            
            x, y, z = transform_coordinate_system(Vector((x, y, z)), game_to_blender = True)
            waypoint_name = get_waypoint_name(race_type_input, race_number_input, index)
                
            create_waypoint(x, y, z, rotation, scale, waypoint_name)
            
        update_waypoint_colors()
    else:
        print("Race data not found for the specified race type and number.")
        

def load_waypoints_from_csv(waypoint_file: Path) -> None:
    file_info = str(waypoint_file).replace('.CSV', '').replace('WAYPOINTS', '')

    race_type = ''.join(filter(str.isalpha, file_info))
    race_number = ''.join(filter(str.isdigit, file_info))
    
    waypoints_data = []

    with open(waypoint_file, 'r') as f:
        reader = csv.reader(f)
        next(reader) 

        for row in reader:
            if len(row) < 5:
                continue  
            waypoints_data.append([float(value) for value in row[:5]])

    for wp_idx, waypoint in enumerate(waypoints_data):
        x, y, z, rotation_deg, scale = waypoint
        
        x, y, z = transform_coordinate_system(Vector((x, y, z)), game_to_blender = True)
        waypoint_name = get_waypoint_name(race_type, race_number, wp_idx)
        
        if rotation_deg == Rotation.AUTO and wp_idx < len(waypoints_data) - 1:
            next_waypoint = waypoints_data[wp_idx + 1]
            rotation_deg = calculate_waypoint_rotation(x, z, next_waypoint[0], next_waypoint[2]) 

        if scale == Width.AUTO:
            scale = Width.DEFAULT

        waypoint = create_waypoint(x, y, z, -rotation_deg, scale, waypoint_name)
        
    update_waypoint_colors()
    
    
def load_cops_and_robbers_waypoints(input_file: Path) -> None:    
    waypoint_types = cycle(["Bank Hideout", "Gold Position", "Robber Hideout"])
    set_count = 1

    with open(input_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  

        for row in reader:
            if len(row) < 3 or not all(is_float(val) for val in row[:3]):
                raise ValueError("\nCSV file can't be parsed. Each row must have at least 3 floats or integer values.\n")
            
            x, y, z = transform_coordinate_system(Vector(map(float, row[:3])), game_to_blender = True)
                                              
            waypoint_type = next(waypoint_types)

            if waypoint_type == "Bank Hideout":
                create_waypoint(x, y, z, name = f"CR_Bank{set_count}", flag_color = Color.PURPLE)
                
            elif waypoint_type == "Gold Position":
                create_gold_bar((x, y, z), scale = 3.0) 
                bpy.context.object.name = f"CR_Gold{set_count}"
                
            elif waypoint_type == "Robber Hideout":
                create_waypoint(x, y, z, name = f"CR_Robber{set_count}", flag_color = Color.GREEN)  
                
            if waypoint_type == "Robber Hideout":
                set_count += 1  # Increase the set count after completing each set of three
    
    
def export_selected_waypoints(export_all: bool = False, add_brackets: bool = False) -> None:
    if export_all:
        waypoints = get_all_waypoints()
    else:
        waypoints = [wp for wp in get_all_waypoints() if wp.select_get()]
            
    output_folder = Folder.BASE / "Waypoint Export"
    output_folder.mkdir(exist_ok = True)

    now = datetime.datetime.now()
    date_time_str = now.strftime("%Y_%d_%m_%H%M_%S")

    base_file_name = f"Waypoints_{date_time_str}.txt"
    export_file = output_folder / base_file_name

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
                        
    open_with_notepad_plus(export_file)                    

    time.sleep(1.0)  # Wait for Notepad to open and load the file   
    
    # Simulate CTRL + A and CTRL + C
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "c")
            
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER WAYPOINT OPERATORS ======================= !#


class CREATE_SINGLE_WAYPOINT_OT_operator(bpy.types.Operator):
    bl_idname = "create.single_waypoint"
    bl_label = "Create Single Waypoint"

    def execute(self, context: bpy.types.Context) -> set:
        create_waypoint(name = "WP_")  
        self.report({"INFO"}, "Created Waypoint")
        return {"FINISHED"}


class LOAD_WAYPOINTS_FROM_CSV_OT_operator(bpy.types.Operator):
    bl_idname = "load.waypoints_from_csv"
    bl_label = "Load Waypoints from CSV"

    def execute(self, context: bpy.types.Context) -> set:
        load_waypoints_from_csv(waypoint_file)
        self.report({"INFO"}, "Loaded Waypoints from CSV")
        return {"FINISHED"}


class LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator(bpy.types.Operator):
    bl_idname = "load.waypoints_from_race_data"
    bl_label = "Load Waypoints from Race Data"

    def execute(self, context: bpy.types.Context) -> set:
        load_waypoints_from_race_data(race_data, waypoint_type_input, waypoint_number_input)
        self.report({"INFO"}, "Loaded Waypoints from Race Data")
        return {"FINISHED"}
    
    
class LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator(bpy.types.Operator):
    bl_idname = "load.cnr_from_csv"
    bl_label = "Load CnR Waypoints from CSV"

    def execute(self, context: bpy.types.Context) -> set:
        Folder.BASE
        load_cops_and_robbers_waypoints("COPSWAYPOINTS.CSV")
        self.report({"INFO"}, "Loaded Cops & Robber Waypoints from CSV")
        return {"FINISHED"}


class EXPORT_SELECTED_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints"
    bl_label = "Export selected Waypoints"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = False, add_brackets = False)
        self.report({"INFO"}, "Exported Selected Waypoints")
        return {"FINISHED"}
    
    
class EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints_with_brackets"
    bl_label = "Export selected Waypoints with Brackets"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = False, add_brackets = True)
        self.report({"INFO"}, "Exported Selected Waypoints with Brackets")
        return {"FINISHED"}
    
    
class EXPORT_ALL_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints"
    bl_label = "Export All Waypoints"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = True, add_brackets = False)
        self.report({"INFO"}, "Exported All Waypoints")
        return {"FINISHED"}


class EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints_with_brackets"
    bl_label = "Export All Waypoints with Brackets"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = True, add_brackets = True)
        self.report({"INFO"}, "Exported All Waypoints with Brackets")
        return {"FINISHED"}
        
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER INIT ======================= !#
        
                
def initialize_blender_panels() -> None:
    if not is_blender_running():
        return
    
    bpy.utils.register_class(VertexGroup)
    bpy.types.Object.vertex_coords = bpy.props.CollectionProperty(type = VertexGroup)
    bpy.utils.register_class(OBJECT_PT_CellTypePanel)
    bpy.utils.register_class(OBJECT_PT_MaterialTypePanel)
    bpy.utils.register_class(OBJECT_PT_PolygonMiscOptionsPanel)
    bpy.utils.register_class(OBJECT_PT_HUDColorPanel)
    bpy.utils.register_class(OBJECT_PT_VertexCoordinates)
        
        
def initialize_blender_operators() -> None:
    if not is_blender_running():
        return
    
    bpy.utils.register_class(OBJECT_OT_UpdateUVMapping)
    bpy.utils.register_class(OBJECT_OT_ExportPolygons)
    bpy.utils.register_class(OBJECT_OT_AssignCustomProperties)
    bpy.utils.register_class(OBJECT_OT_ProcessPostExtrude)
    bpy.utils.register_class(OBJECT_OT_RenameChildren)
    

def initialize_blender_waypoint_editor() -> None:
    if not is_blender_running():
        return
    
    bpy.utils.register_class(CREATE_SINGLE_WAYPOINT_OT_operator)
    bpy.utils.register_class(LOAD_WAYPOINTS_FROM_CSV_OT_operator)
    bpy.utils.register_class(LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator)
    bpy.utils.register_class(LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator)
    bpy.utils.register_class(EXPORT_SELECTED_WAYPOINTS_OT_operator)
    bpy.utils.register_class(EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator)
    bpy.utils.register_class(EXPORT_ALL_WAYPOINTS_OT_operator)
    bpy.utils.register_class(EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator)
    
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER KEYBINDINGS ======================= !#
      
      
def set_blender_keybinding() -> None:
    if not is_blender_running():
        return
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name = "Object Mode", space_type = "EMPTY")

        #? === Workflow Automation === ?#
        # Ctrl + E to export selected polygon(s)
        kmi_export_selected = km.keymap_items.new("object.export_polygons", "E", "PRESS", ctrl = True)
        kmi_export_selected.properties.select_all = False

        # Shift + E to export all polygons
        kmi_export_all = km.keymap_items.new("object.export_polygons", "E", "PRESS", shift = True)
        kmi_export_all.properties.select_all = True

        # Shift + P to assign custom properties to newly created polygon(s)
        km.keymap_items.new("object.assign_custom_properties", "P", "PRESS", shift = True)

        # Shift + X to process an extruded mesh without triangulation
        kmi_custom_extrude_no_triangulate = km.keymap_items.new("object.process_post_extrude", "X", "PRESS", shift = True)
        kmi_custom_extrude_no_triangulate.properties.triangulate = False    
        
        # Ctrl + Shift + X to process an extruded mesh with triangulation
        kmi_custom_extrude_triangulate = km.keymap_items.new("object.process_post_extrude", "X", "PRESS", ctrl = True, shift = True)
        kmi_custom_extrude_triangulate.properties.triangulate = True

        # Ctrl + Shift + Q to rename children objects
        km.keymap_items.new("object.auto_rename_children", "Q", "PRESS", ctrl = True, shift = True)
        
        #? === Waypoints === ?#
        # Shift + Y to create a single aypoint
        km.keymap_items.new("create.single_waypoint", "Y", "PRESS", shift = True)  
                
        # Shift + C to load waypoints from CSV
        km.keymap_items.new("load.waypoints_from_csv", "C", "PRESS", shift = True) 

        # Shift + R to load waypoints from "race_data" dictionary
        km.keymap_items.new("load.waypoints_from_race_data", "R", "PRESS", shift = True)  
        
        # Shift + W to export selected waypoint(s)
        km.keymap_items.new("export.selected_waypoints", "W", "PRESS", shift = True)
        
        # Ctrl + W to export selected waypoint(s) with brackets
        km.keymap_items.new("export.selected_waypoints_with_brackets", "W", "PRESS", ctrl = True)
        
        # Ctrl + Shift + W to export all waypoints
        km.keymap_items.new("export.all_waypoints", "W", "PRESS", ctrl = True, shift = True)
        
        # Ctrl + Alt + W to export all waypoins with brackets
        km.keymap_items.new("export.all_waypoints_with_brackets", "W", "PRESS", ctrl = True, alt = True)
        
        # Alt + C to load CnR waypoints from CSV
        km.keymap_items.new("load.cnr_from_csv", "O", "PRESS", alt = True)
###################################################################################################################   
################################################################################################################### 
#! ======================= SET FACADES ======================= !#


#* NOTES:
#* Separator: (max_x - min_x) / separator(value) = number of facades
#* Sides: omitted by default, but can be set (relates to lighting, but behavior is not clear)
#* Scale: enlarges or shrinks non-fixed facades

#* All information about Facades (including pictures) can be found in: 
# ... / UserResources / FACADES / ...        
# ... / UserResources / FACADES / FACADE pictures

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


class Facade:
    BUILDING_ORANGE_WITH_WINDOWS = "ofbldg02"
    
    WALL_FREEWAY = "freewaywall02"
    RAIL_WATER = "t_rail01"
    
    SHOP_SUIT = "dfsuitstore"
    SHOP_PIZZA = "hfpizza"
    SHOP_SODA = "ofsodashop"
    SHOP_LIQUOR = "cfliquor"
    
    HOME_ONE = "OFHOME01"
    HOME_TWO = "OFHOME02"
    HOME_THREE = "OFHOME03"
        
    RAIL_WATER = "t_rail01"
    
    
orange_building_one = {
	"flags": FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -50.0),
	"end": (10, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "x"}

orange_building_two = {
	"flags": FRONT_BRIGHT,
	"offset": (10.0, 0.0, -70.0),
	"end": (-10, 0.0, -70.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "x"}

orange_building_three = {
	"flags": FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -70.0),
	"end": (-10.0, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "z"}

orange_building_four = {
	"flags": FRONT_BRIGHT,
	"offset": (10.0, 0.0, -50.0),
	"end": (10.0, 0.0, -70.0),
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "z",
    "separator": 10.0}


# Pack all Facades for processing
facade_list = [orange_building_one, orange_building_two, orange_building_three, orange_building_four]

###################################################################################################################   
###################################################################################################################
#! ======================= SET AI STREETS ======================= !#


f"""
The following variables are OPTIONAL: 

Intersection Type, defaults to: {IntersectionType.CONTINUE}
(possbile types: 
{IntersectionType.STOP}, {IntersectionType.STOP_LIGHT}, {IntersectionType.YIELD}, {IntersectionType.CONTINUE})

Stop Light Name, defaults to: {Prop.STOP_LIGHT_SINGLE}
(possbile names: {Prop.STOP_SIGN}, {Prop.STOP_LIGHT_SINGLE}, {Prop.STOP_LIGHT_DUAL})

Stop Light Positions, defaults to: {(0, 0, 0)}
Traffic Blocked, Ped Blocked, Road Divided, and Alley, all default to: {NO}
(possbile values: {YES}, {NO})

# Stop Lights will only show if the Intersection Type is {IntersectionType.STOP_LIGHT}
"""

#! Do not delete this Street
cruise_start = {
    "street_name": "cruise_start",
    "vertices": [
        (0, 0, 0),              # Keep this
        cruise_start_position]}     

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

# Street example with multiple lanes and all optional settings
street_example = {
    "street_name": "example",
    "lanes": {
        "lane_1": [
            (-40.0, 1.0, -20.0),
            (-30.0, 1.0, -30.0),
            (-30.0, 1.0, -50.0),
        ],
        "lane_2": [  # Add more lanes if desired
            (-40.0, 1.0, -20.0),
            (-40.0, 1.0, -30.0),
            (-40.0, 1.0, -50.0),
        ],
    },
    "intersection_types": [IntersectionType.STOP_LIGHT, IntersectionType.STOP_LIGHT],
    "stop_light_names": [Prop.STOP_LIGHT_DUAL, Prop.STOP_LIGHT_DUAL],
    "stop_light_positions": [
         (10.0, 0.0, -20.0),        # Offset 1
         (10.01, 0.0, -20.0),       # Direction 1
         (-10.0, 0.0, -20.0),       # Offset 2
         (-10.0, 0.0, -20.1)],      # Direction 2
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
#! ======================= SET PROPS ======================= !#


trailer_set = {"offset": (60, 0.0, 70), 
               "end": (60, 0.0, -50), 
               "name": Prop.TRAILER, 
               "separator": "x"} # Use the {}-axis dimension of the object as the spacing between each prop

bridge_orange_buildling = {          
          "offset": (35, 12.0, -70),
          "face": (35 * HUGE, 12.0, -70),
          "name": Prop.BRIDGE_SLIM}

# Prop for CIRCUIT 0 
china_gate = {"offset": (0, 0.0, -20), 
              "face": (1 * HUGE, 0.0, -20), 
              "name": Prop.CHINATOWN_GATE,
              "race_mode": RaceMode.CIRCUIT,
              "race_num": 0}

# Put your non-randomized props here
prop_list = [trailer_set, bridge_orange_buildling, china_gate] 

# Put your randomized props here (you will add them to the list "random_parameters")
random_trees = {
        "offset_y": 0.0,
        "name": [Prop.TREE_SLIM] * 20}

random_sailboats = {
        "offset_y": 0.0,
        "name": [Prop.SAILBOAT] * 19}

random_cars = {
        "offset_y": 0.0,
        "separator": 10.0,
        "name": [PlayerCar.VW_BEETLE, PlayerCar.CITY_BUS, PlayerCar.CADILLAC, PlayerCar.CRUISER, PlayerCar.FORD_F350, 
                 PlayerCar.FASTBACK, PlayerCar.MUSTANG99, PlayerCar.ROADSTER, PlayerCar.PANOZ_GTR_1, PlayerCar.SEMI]}


# Configure your random props here
random_props = [
    {"seed": 123, "num_props": 1, "props_dict": random_trees, "x_range": (65, 135), "z_range": (-65, 65)},
    {"seed": 99, "num_props": 1, "props_dict": random_sailboats, "x_range": (55, 135), "z_range": (-145, -205)},
    {"seed": 1, "num_props": 2, "props_dict": random_cars, "x_range": (52, 138), "z_range": (-136, -68)}]

# APPEND PROPS
app_panoz_gtr = {
    'offset': (5, 2, 5),
    'end': (999, 2, 999),
    'name': PlayerCar.PANOZ_GTR_1}

props_to_append = [app_panoz_gtr]

###################################################################################################################   
################################################################################################################### 
#! ======================= SET PROP PROPERTIES ======================= !#


# The Size does affect how the prop moves after impact. CG stands for Center of Gravity. 
bangerdata_properties = {
    PlayerCar.VW_BEETLE: {"ImpulseLimit2": HUGE, "AudioId": AudioProp.GLASS},
    PlayerCar.CITY_BUS:  {"ImpulseLimit2": 50, "Mass": 50, "AudioId": AudioProp.POLE, "Size": "18 6 5", "CG": "0 0 0"}}

###################################################################################################################   
###################################################################################################################   
#! ======================= SET LIGHTING ======================= !#


lighting_configs = [
    {   # Actual lighting config for Evening and Cloudy
        "time_of_day": TimeOfDay.EVENING,
        "weather": Weather.CLOUDY,
        "sun_heading": 3.14,
        "sun_pitch": 0.65,
        "sun_color": (1.0, 0.6, 0.3),
        "fill_1_heading": -2.5,
        "fill_1_pitch": 0.45,
        "fill_1_color": (0.8, 0.9, 1.0),
        "fill_2_heading": 0.0,
        "fill_2_pitch": 0.45,
        "fill_2_color": (0.75, 0.8, 1.0),
        "ambient_color": (0.1, 0.1, 0.2),
        "fog_end": 600.0,
        "fog_color": (230.0, 100.0, 35.0),
        "shadow_alpha": 180.0,
        "shadow_color": (15.0, 20.0, 30.0)
    },
    {
        # Custom lighting config for Night and Clear
        "time_of_day": TimeOfDay.NIGHT,
        "weather": Weather.CLEAR,
        "sun_pitch": 10.0,
        "sun_color": (40.0, 0.0, 40.0),
        "fill_1_pitch": 10.0,
        "fill_1_color": (40.0, 0.0, 40.0),
        "fill_2_pitch": 10.0,
        "fill_2_color": (40.0, 0.0, 40.0),
    },
]
###################################################################################################################   
################################################################################################################### 
#! ======================= SET PHYSICS ======================= !#


# Available indices: 94, 95, 96, 97, 98
custom_physics = {
    97: {"friction": 20.0, "elasticity": 0.01, "drag": 0.0},  # Sticky
    98: {"friction": 0.1, "elasticity": 0.01, "drag": 0.0}}   # Slippery

###################################################################################################################   
################################################################################################################### 
#! ======================= TEXTURE MODIFICATIONS ======================= !#


texture_modifications = [
    {
        "name": Texture.ROAD_3_LANE,
        "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
    },
    {
        "name": Texture.ROAD_2_LANE,
        "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
    },
    {
        "name": Texture.ROAD_1_LANE,
        "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
    }
]

###################################################################################################################   
################################################################################################################### 
#! ======================= SET DLP ======================= !#


s_res = 4
t_res = 1
r_opts = 636
dlp_flags = 1289  # 1513
material_index = 0
texture_index = 0
physics_index = 0

dlp_patch_name = ""
dlp_group_name = "BOUND\x00" 

# DLP Vertices
dlp_normals = [
    DLPVertex(0, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE),
    DLPVertex(1, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE),
    DLPVertex(2, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE),
    DLPVertex(3, Default.VECTOR_3, Default.VECTOR_2, Color.WHITE)
    ]

# Geometry Vertices
dlp_vertices = [ 
      Vector3(-50.0, 0.0, 80.0),
      Vector3(-140.0, 0.0, 50.0),
      Vector3(-100.0, 0.0, 10.0),
      Vector3(-50.0, 0.0, 30.0)
      ]

# DLP Groups
dlp_groups = [DLPGroup(dlp_group_name, 0, 2, [], [0, 1])]

# DLP Patches                  
dlp_patches = [
    DLPPatch(s_res, t_res, dlp_flags, r_opts, material_index, texture_index, physics_index, 
             [dlp_normals[0], dlp_normals[1], dlp_normals[2], dlp_normals[3]], dlp_patch_name),
    DLPPatch(s_res, t_res, dlp_flags, r_opts, material_index, texture_index, physics_index, 
             [dlp_normals[3], dlp_normals[2], dlp_normals[1], dlp_normals[0]], dlp_patch_name)
    ] 

###################################################################################################################   
################################################################################################################### 
#! ======================= BLENDER AI PATHS ======================= !#


def extract_and_format_road_data(input_folder: Path, output_file: Path) -> None: 
    for file in input_folder.iterdir():
        if file.is_file() and file.suffix == '.road':
            
            with open(file, 'r') as f:
                all_lines = f.readlines()
            
                total_vertex = int(all_lines[6][17:])
                num_vertexs = int(all_lines[1][15:])

                relevant_lines = [line.lstrip() for line in all_lines[8:8+total_vertex+1]]
                blocks = ["".join(relevant_lines[i:i+num_vertexs]) for i in range(0, total_vertex, num_vertexs)]
                
                vertex_string = "\n".join(blocks).replace(" ", ",")

                with open(output_file, mode = "a") as out_f:
                    out_f.write(f"{vertex_string}\n")


def process_generated_road_file(input_file: Path) -> list:
    polyline_block = []
    all_polyline_blocks = []

    with open(input_file, 'r') as f:
        for line in f:
            if line.strip() == '':
                # Empty line denotes end of polyline block, add current polyline to the list and start a new one
                all_polyline_blocks.append(polyline_block)
                polyline_block = []
            else:
                # Add the current line to the current polyline block
                polyline_block.append(tuple(map(float, line.strip().split(','))))

    if polyline_block:
        all_polyline_blocks.append(polyline_block)

    return all_polyline_blocks


def create_road_path(curve_object: bpy.types.Object, vertices) -> None:
    curve_data = curve_object.data
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 1
    curve_data.bevel_depth = 0.70 

    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(vertices) - 1) 
    
    for index, vertex in enumerate(vertices):
        x, y, z = transform_coordinate_system(Vector(vertex), game_to_blender = True)
        polyline.points[index].co = (x, y, z, 1) 


def add_road_paths(all_polyline_blocks) -> None:
    for i, polyline_block in enumerate(all_polyline_blocks):
        
        curve_data = bpy.data.curves.new(f"Street_{i}", type = 'CURVE')
        curve_object = bpy.data.objects.new(f"Street_{i}", curve_data)
        bpy.context.collection.objects.link(curve_object)
    
        for j in range(len(polyline_block) - 1):
            create_road_path(curve_object, polyline_block[j:j + 2])

                    
def apply_path_color_scheme() -> None:
    for path in (obj for obj in bpy.context.collection.objects if obj.type == 'CURVE'):
        num_splines = len(path.data.splines)
        
        for idx, spline in enumerate(path.data.splines):
            mat = bpy.data.materials.new(name = f"Material_{path.name}_{idx}")
            
            # Assign a Red Color to the first and last spline, Blue and Green to the rest
            if idx == 0 or idx == num_splines - 1:
                mat.diffuse_color = Color.RED
            else:
                mat.diffuse_color = [Color.BLUE, Color.GREEN][(idx - 1) % 2]

            path.data.materials.append(mat)
            spline.material_index = idx
            
                      
def process_and_visualize_paths(input_folder: Path, output_file: Path, visualize_ai_paths: bool) -> None:
    if not visualize_ai_paths or not is_blender_running():
        return
    
    extract_and_format_road_data(input_folder, output_file)
    time.sleep(0.1)  # Sleep to ensure file operations are completed

    polyline_blocks = process_generated_road_file(output_file)
    time.sleep(0.1)  # Sleep to ensure file operations are completed

    add_road_paths(polyline_blocks)
    apply_path_color_scheme()
            
###################################################################################################################   
#! ======================= CALL FUNCTIONS ======================= !#


# Core
create_folders()
create_map_info(Folder.SHOP_TUNE / f"{MAP_FILENAME}.CINFO", blitz_race_names, circuit_race_names, checkpoint_race_names)

create_races(race_data)
create_cops_and_robbers(Folder.SHOP_RACE_MAP / "COPSWAYPOINTS.CSV", cnr_waypoints)

check_bound_numbers(polys)
create_cells(Folder.SHOP_CITY / f"{MAP_FILENAME}.CELLS", polys, truncate_cells)
Bounds.create(Folder.SHOP / "BND" / f"{MAP_FILENAME}_HITID.BND", vertices, polys, Folder.DEBUG_RESOURCES / "BOUNDS" / f"{MAP_FILENAME}.txt", debug_bounds)
Portals.write_all(Folder.SHOP_CITY / f"{MAP_FILENAME}.PTL", polys, vertices, lower_portals, empty_portals, debug_portals)
aiStreetEditor.create(street_list, set_ai_streets, set_reverse_ai_streets)
FacadeEditor.create(Folder.SHOP_CITY / f"{MAP_FILENAME}.FCD", facade_list, set_facades, debug_facades)
PhysicsEditor.edit(Folder.EDITOR_RESOURCES / "PHYSICS" / "PHYSICS.DB", Folder.SHOP / "MTL" / "PHYSICS.DB", custom_physics, set_physics, debug_physics)

TextureSheet.append_custom_textures(Folder.EDITOR_RESOURCES / "MTL" / "GLOBAL.TSH", Folder.BASE / "Custom Textures", Folder.SHOP / "MTL" / "TEMP_GLOBAL.TSH", set_texture_sheet)
TextureSheet.write_tweaked(Folder.SHOP / "MTL" / "TEMP_GLOBAL.TSH", Folder.SHOP / "MTL" / "GLOBAL.TSH", texture_modifications)
                    
prop_editor = BangerEditor()
for prop in random_props:
    prop_list.extend(prop_editor.place_randomly(**prop))
prop_editor.process_all(prop_list, set_props)

lighting_instances = LightingEditor.read_file(Folder.EDITOR_RESOURCES / "LIGHTING" / "LIGHTING.CSV")
LightingEditor.write_file(lighting_instances, lighting_configs, Folder.SHOP_TUNE / "LIGHTING.CSV")
LightingEditor.debug(lighting_instances, Folder.DEBUG_RESOURCES / "LIGHTING" / "LIGHTING_DATA.txt", debug_lighting)

copy_dev_folder(Folder.BASE / "dev", Folder.MIDTOWNMADNESS / "dev")
edit_and_copy_mmbangerdata(bangerdata_properties, Folder.EDITOR_RESOURCES / "TUNE", Folder.SHOP_TUNE) 
copy_tune_mmcarsim_files(Folder.EDITOR_RESOURCES / "TUNE", Folder.SHOP_TUNE)
copy_custom_textures(Folder.BASE / "Custom Textures", Folder.SHOP / "TEX16O")

create_ext(Folder.SHOP_CITY / f"{MAP_FILENAME}.EXT", hudmap_vertices)
create_animations(Folder.SHOP_CITY / MAP_FILENAME / "ANIM.CSV", Folder.SHOP_CITY / MAP_FILENAME, animations_data, set_animations)   
create_bridges(bridge_list, set_bridges, Folder.SHOP_CITY / f"{MAP_FILENAME}.GIZMO") 
create_bridge_config(bridge_config_list, set_bridges, Folder.SHOP_TUNE)
create_minimap(set_minimap, debug_minimap, debug_minimap_id, minimap_outline_color, line_width = 0.7, background_color = "black")
create_lars_race_maker("Lars_Race_Maker.html", street_list, hudmap_vertices, set_lars_race_maker)


# Misc
BangerEditor().append_to_file(append_input_props_file, props_to_append, append_output_props_file, append_props)
DLP("DLP7", len(dlp_groups), len(dlp_patches), len(dlp_vertices), dlp_groups, dlp_patches, dlp_vertices).write("TEST.DLP", set_dlp) 

# File Debugging
Bangers.debug_file(debug_props_data_file, Folder.DEBUG_RESOURCES / "PROPS" / debug_props_data_file.with_suffix(".txt"), debug_props_file)
Bangers.debug_file_to_csv(debug_props_data_file, Folder.DEBUG_RESOURCES / "PROPS" / debug_props_data_file.with_suffix(".csv"), debug_props_file_to_csv)
Facades.debug_file(debug_facades_data_file, Folder.DEBUG_RESOURCES / "FACADES" / debug_facades_data_file.with_suffix(".txt"), debug_facades_file)
Portals.debug_file(debug_portals_data_file, Folder.DEBUG_RESOURCES / "PORTALS" / debug_portals_data_file.with_suffix(".txt"), debug_portals_file)
Meshes.debug_file(debug_meshes_data_file, Folder.DEBUG_RESOURCES / "MESHES" / debug_meshes_data_file.with_suffix(".txt"), debug_meshes_file)
Meshes.debug_folder(debug_meshes_data_folder, Folder.DEBUG_RESOURCES / "MESHES" / "MESH TEXT FILES", debug_meshes_folder) 
Bounds.debug_file(debug_bounds_data_file, Folder.DEBUG_RESOURCES / "BOUNDS" / debug_bounds_data_file.with_suffix(".txt"), debug_bounds_file)
Bounds.debug_folder(debug_bounds_data_folder, Folder.DEBUG_RESOURCES / "BOUNDS" / "BND TEXT FILES", debug_bounds_folder)
DLP.debug_file(debug_dlp_data_file, Folder.DEBUG_RESOURCES / "DLP" / debug_dlp_data_file.with_suffix(".txt"), debug_dlp_file)
DLP.debug_folder(debug_dlp_data_folder, Folder.DEBUG_RESOURCES / "DLP" / "DLP TEXT FILES", debug_dlp_folder)

debug_ai(debug_ai_data_file, debug_ai_file,
         Folder.USER_RESOURCES / "AI" / "CHICAGO.map",                                  
         str(Path(Folder.USER_RESOURCES) / "AI" / "Intersection{intersection_id}.int"),
         str(Path(Folder.USER_RESOURCES) / "AI" / "Street{paths}.road")
    )

# Finalizing Part
create_ar(Folder.SHOP)
create_commandline(Folder.MIDTOWNMADNESS, no_ui, no_ui_type, no_ai, less_logs, more_logs)

editor_time = time.time() - start_time
save_editor_run_time(editor_time, Folder.EDITOR_RESOURCES / "last_run_time.pkl")
progress_thread.join()

print("\n" + create_bar_divider(colors_two))
print(Fore.LIGHTCYAN_EX  + "   Successfully created " + Fore.LIGHTYELLOW_EX  + f"{MAP_NAME}!" + Fore.MAGENTA + f" (in {editor_time:.4f} s)" + Fore.RESET)
print(create_bar_divider(colors_two))

start_game(Folder.MIDTOWNMADNESS, "Open1560.exe", play_game)


# Blender
setup_blender()

initialize_blender_panels()
initialize_blender_operators()
initialize_blender_waypoint_editor()
set_blender_keybinding()

create_blender_meshes(Folder.EDITOR_RESOURCES / "TEXTURES", load_all_texures)

process_and_visualize_paths(Folder.SHOP / "dev" / "CITY" / MAP_FILENAME, "AI_PATHS.txt", visualize_ai_paths)


# Cleanup
post_editor_cleanup(delete_shop)

###################################################################################################################   
################################################################################################################### 

from .races import RaceMode
from .props import Prop


NO = 0  
YES = 1 

HUGE = 1E10

PROP_CAN_COLLIDE_FLAG = 0x800

EDITOR_RUNTIME_FILE = "editor_run_time.pkl"
    
WAYPOINT_FILLER = ",0,0,0,0,0,\n"
CHECKPOINT_PREFIXES = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]

BRIDGE_ATTRIBUTE_FILLER = f"\t{Prop.CROSSGATE},0,-999.99,0.00,-999.99,-999.99,0.00,-999.99\n" 

# Headers
CNR_HEADER = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"
MM_DATA_HEADER = ["CarType", "TimeofDay", "Weather", "Opponents", "Cops", "Ambient", "Peds", "NumLaps", "TimeLimit", "Difficulty"]
TEXTURESHEET_HEADER = ["name", "neighborhood", "h", "m", "l", "flags", "alternate", "sibling", "xres", "yres", "hexcolor"]
    
LIGHTING_HEADER = [
    "TimeOfDay", "Weather", "Sun Heading", "Sun Pitch", "Sun Red", "Sun Green", "Sun Blue",
    "Fill-1 Heading", "Fill-1 Pitch", "Fill-1 Red", "Fill-1 Green", "Fill-1 Blue",
    "Fill-2 Heading", "Fill-2 Pitch", "Fill-2 Red", "Fill-2 Green", "Fill-2 Blue",
    "Ambient Red", "Ambient Green", "Ambient Blue", 
    "Fog End", "Fog Red", "Fog Green", "Fog Blue", 
    "Shadow Alpha", "Shadow Red", "Shadow Green", "Shadow Blue"
]

# Race constants
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

RACE_TYPE_INITIALS = {
    RaceMode.BLITZ: "B",
    RaceMode.CIRCUIT: "C",
    RaceMode.CHECKPOINT: "R",
}

DEFAULT_MM_DATA_BY_RACE_MODE = {        
    RaceMode.BLITZ:      [1, 2, 3, 4, 5, 6, 7, 8],   # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit
    RaceMode.CIRCUIT:    [1, 2, 3, 4, 5, 6, 7],      # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps
    RaceMode.CHECKPOINT: [1, 2, 3, 4, 5, 6]          # TimeofDay, Weather, Opponents, Cops, Ambient, Peds
}
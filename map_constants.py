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
    
    
class CnR:
    BANK_HIDEOUT = "Bank Hideout"
    GOLD_POSITION = "Gold Position"
    ROBBER_HIDEOUT = "Robber Hideout"


class Threshold:
    BLITZ_WAYPOINT_COUNT = 11
    CHECKPOINT_RACE_COUNT = 12
    BLITZ_AND_CIRCUIT_RACE_COUNT = 15
    MESH_VERTEX_COUNT = 16
    CELL_TYPE_SWITCH = 200
    CELL_CHARACTER_WARNING = 200
    CELL_CHARACTER_LIMIT = 0xFF    
    VERTEX_INDEX_COUNT = 0x8000
    
    
class Magic:
    MESH = "3HSM"
    BOUND = "2DNB"
    PORTAL = 0
    DEVELOPMENT = "DLP7"
    

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

    IND_WALL = "#7b816a"
    BRICKS_MALL = "#e6cab4"
    SHOP_BRICK = "#394441"
    MARKT_BRICK = "#9c9183"
    

class Anim:
    PLANE = "plane"
    ELTRAIN = "eltrain"


#! Player Cars and Traffic Cars can be used as Opponent cars, Cop cars, and Props
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
    BENCH_MALL = "tpbench_mall"
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
    ROAD = "ROAD"
    ICE = "L_RIVET"

    BRICKS_MALL = "OT_MALL_BRICK"
    BRICKS_SAND = "OT_SHOP03_BRICK"
    BRICKS_GREY = "CT_FOOD_BRICK"
    WALL = "T_WALL"
    IND_WALL = "IND_WALL"
    SHOP_BRICK = "CT_SHOP_BRICK"
    MARKT_BRICK = "OT_MARKT_BRICK"

    GLASS = "R_WIN_01"
    STOP_SIGN = "T_STOP"
    BARRICADE = "T_BARRICADE"
    CHECKPOINT = "CHECK04"
    BUS_RED_TOP = "VPBUSRED_TP_BK"
    
    # Custom Textures (see: MM1-Map-Editor \ Custom Textures)
    LAVA = "T_WATER_LAVA"
    BARRICADE_RED_BLACK = "T_RED_BLACK_BARRICADE"
    
    
class FileType:
    EXT = ".EXT"
    _MESH = ".bms"
    MESH = ".BMS"
    PROP = ".BNG"
    CELL = ".CELLS"
    BOUND = ".BND"
    GIZMO = ".GIZMO"
    PORTAL = ".PTL"
    FACADE = ".FCD"
    DATABASE = ".DB"
    CITY_INFO = ".cinfo"
    DEVELOPMENT = ".DLP"
    TEXTURE_SHEET = ".TSH"
    
    PROP_DATA = ".MMBANGERDATA"
    CAR_SIMULATION = ".MMCARSIM"
    BRIDGE_MANAGER = ".MMBRIDGEMGR"
        
    DIRECTDRAW_SURFACE = ".DDS"
    
    MAP = ".map"
    AI_STREET = ".road"
    INTERSECTION = ".int"
        
    CSV = ".CSV"
    TEXT = ".txt"
    HTML = "html"


class Encoding:
    ASCII = "ascii"
    UTF_8 = "utf-8"
    LATIN_1 = "latin-1"


MIDTOWN_MADNESS = "Open1560.exe"
BLENDER = "blender"
NOTEPAD_PLUS_PLUS = "notepad++.exe"
EDITOR_RUNTIME_FILE = "editor_run_time.pkl"
    
NO = 0  
YES = 1 
HUGE = 1E10
PROP_CAN_COLLIDE_FLAG = 0x800
    
    
CHECKPOINT_PREFIXES = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]

MM_DATA_HEADER = ["CarType", "TimeofDay", "Weather", "Opponents", "Cops", "Ambient", "Peds", "NumLaps", "TimeLimit", "Difficulty"]
CNR_HEADER = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"

WAYPOINT_FILLER = ",0,0,0,0,0,\n"

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


BRIDGE_ATTRIBUTE_FILLER = f"\t{Prop.CROSSGATE},0,-999.99,0.00,-999.99,-999.99,0.00,-999.99\n"  
    
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

    
LIGHTING_HEADER = [
    "TimeOfDay", "Weather", "Sun Heading", "Sun Pitch", "Sun Red", "Sun Green", "Sun Blue",
    "Fill-1 Heading", "Fill-1 Pitch", "Fill-1 Red", "Fill-1 Green", "Fill-1 Blue",
    "Fill-2 Heading", "Fill-2 Pitch", "Fill-2 Red", "Fill-2 Green", "Fill-2 Blue",
    "Ambient Red", "Ambient Green", "Ambient Blue", 
    "Fog End", "Fog Red", "Fog Green", "Fog Blue", 
    "Shadow Alpha", "Shadow Red", "Shadow Green", "Shadow Blue"
]

    
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
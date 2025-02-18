class Portal:
    ACTIVE = 0x1
    OPEN_AREA = 0x2         # Reset Clip MinX, MaxX, MinY, MaxY 
    HALF_OPEN_AREA = 0x4    # Reset MinX or MaxX depending on direction
    PLANE = 0x8             # Must be infront (or behind?) portal plane


class Material:
    DEFAULT = 0
    GRASS = 87
    WATER = 91
    STICKY = 97         # Custom
    NO_FRICTION = 98    # Custom


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


class LevelOfDetail:
    UNKNOWN_1 = 0x1    # A
    LOW = 0x2          # L
    MEDIUM = 0x4       # M
    HIGH = 0x8         # H
    DRIFT = 0x20       # A2
    UNKNOWN_2 = 0x40   # L2
    UNKNOWN_3 = 0x80   # M2
    UNKNOWN_4 = 0x100  # H2
    
    
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


class Magic:
    MESH = "3HSM"
    BOUND = "2DNB"
    PORTAL = 0
    DEVELOPMENT = "DLP7"


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
    
    BANGER_DATA = ".MMBANGERDATA"
    CAR_SIMULATION = ".MMCARSIM"
    BRIDGE_MANAGER = ".MMBRIDGEMGR"
        
    DIRECTDRAW_SURFACE = ".DDS"
    
    MAP = ".map"
    AI_STREET = ".road"
    INTERSECTION = ".int"
        
    CSV = ".CSV"
    TEXT = ".txt"
    HTML = "html"


class Anim:
    PLANE = "plane"
    ELTRAIN = "eltrain"
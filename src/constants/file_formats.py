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


class LOD:
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    VERY_LOW = "VL"


class LevelOfDetail:
    UNKNOWN_1 = 0x1    # A
    LOW = 0x2          # L
    MEDIUM = 0x4       # M
    HIGH = 0x8         # H
    DRIFT = 0x20       # A2
    UNKNOWN_2 = 0x40   # L2
    UNKNOWN_3 = 0x80   # M2
    UNKNOWN_4 = 0x100  # H2
    
    
class MeshFlags:
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

agiMeshSet = MeshFlags  # backward-compat alias for WIP scripts

    
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
    """
    TexSheet (.TSH) per-texture flag letters → agiTexProp::Flags (agiworld/texsheet.h,
    consumed in agiworld/getmesh.cpp).

    Which ones actually CHANGE what you see (and why several seem to do nothing):

    Clearly visible:
      t (TRANSPARENT)  – enables alpha blending (uses the texture's alpha channel).
      g (ALPHA_GLOW)   – additive/glow blend (headlights, sirens, glass glints).
      k (CHROMAKEY)    – colour-key transparency (a key colour becomes see-through).
      n (NOT_LIT)      – full-bright, ignores scene lighting (dashboards, glow, signs).
      d (DULL_OR_DAMAGED) – marks the damaged-skin variant (used by the damage swap).

    Subtle / situational (easy to miss):
      w (SNOWABLE)     – only differs in snow weather (snow builds up); also keeps the
                         texture resident + drops mipmaps.
      l (LIGHTMAP)     – only relevant where a lightmap pass applies (world geometry).
      s (SHADOW)       – flags a shadow-blob texture; no effect on normal car skins.
      e (ROAD_FLOOR_CEILING) – just disables mipmaps; only visible on big tiled surfaces.
      m (ALWAYS_MODULATE) – multiply by vertex/material colour; only shows if the mesh
                         actually carries a non-white colour to modulate with.

    Usually NO visible change on a custom car (this is likely what you hit):
      p (ALWAYS_PERSP_CORRECT) – Open1560's GL renderer is always perspective-correct,
                         so this is effectively a no-op now.
      u / v / c / U / V (CLAMP_*) – texture-edge clamp vs wrap. Only matters when UVs
                         tile beyond [0,1]; car-body UVs sit inside [0,1], so clamping
                         looks identical to wrapping → no visible difference.
    """
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


class AxisRef:
    def __init__(self, axis: str, offset: float = 0.0):
        self.axis = axis
        self.offset = offset

    def __add__(self, value):
        if isinstance(value, (int, float)):
            return AxisRef(self.axis, self.offset + value)
        return NotImplemented

    def __radd__(self, value):
        return self.__add__(value)

    def __sub__(self, value):
        if isinstance(value, (int, float)):
            return AxisRef(self.axis, self.offset - value)
        return NotImplemented

    def __repr__(self):
        if self.offset == 0:
            return f"Axis.{self.axis.upper()}"
        sign = "+" if self.offset > 0 else "-"
        return f"Axis.{self.axis.upper()} {sign} {abs(self.offset)}"

    def resolve(self, dimensions) -> float:
        if self.axis in ("x", "y", "z"):
            return getattr(dimensions, self.axis) + self.offset

        values = (dimensions.x, dimensions.y, dimensions.z)

        if self.axis == "longest":
            return max(values) + self.offset
        elif self.axis == "shortest":
            return min(values) + self.offset
        elif self.axis == "middle":
            return sorted(values)[1] + self.offset

        return 10.0 + self.offset


class Axis:
    X = AxisRef("x")
    Y = AxisRef("y")
    Z = AxisRef("z")
    Longest = AxisRef("longest")
    Shortest = AxisRef("shortest")
    Middle = AxisRef("middle")


class FileType:
    EXTREMA = ".EXT"
    MESH = ".BMS"
    MESH_lowercase = ".bms"
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
    
    AI_MAP = ".map"
    AI_STREET = ".road"
    AI_INTERSECTION = ".int"
    AI = ".BAI"

    PLAYER_SAVE   = ".SAV"
    PLAYER_DIR    = ".DIR"
    PLAYER_CONFIG = ".CFG"
    RACE_RECORD   = ".DAT"

    CSV = ".CSV"
    TEXT = ".txt"
    HTML = ".html"


class Anim:
    PLANE = "plane"
    ELTRAIN = "eltrain"
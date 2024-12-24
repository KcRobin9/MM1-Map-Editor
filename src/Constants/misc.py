class Shape:
    LINE = 2
    TRIANGLE = 3
    QUAD = 4


class Encoding:
    ASCII = "ascii"
    UTF_8 = "utf-8"
    LATIN_1 = "latin-1"


class Executable:
    MIDTOWN_MADNESS = "Open1560.exe"
    BLENDER = "Blender"
    NOTEPAD_PLUS_PLUS = "notepad++.exe"

    
class Threshold:
    BLITZ_WAYPOINT_COUNT = 11
    CHECKPOINT_RACE_COUNT = 12
    BLITZ_AND_CIRCUIT_RACE_COUNT = 15
    MESH_VERTEX_COUNT = 16
    CELL_TYPE_SWITCH = 200
    CELL_CHARACTER_WARNING = 200
    CELL_CHARACTER_LIMIT = 0xFF    
    VERTEX_INDEX_COUNT = 0x8000
    
        
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
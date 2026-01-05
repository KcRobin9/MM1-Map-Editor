from pathlib import Path

from src.core.vector.vector_2 import Vector2
from src.core.vector.vector_3 import Vector3

from src.USER.settings.main import MAP_FILENAME
from src.helpers.main import is_process_running


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
    NOTEPAD_REGULAR = "notepad.exe"
    NOTEPAD_PLUS_PLUS = "notepad++.exe"


class Default:
    ROOM = 1
    VECTOR_2 = Vector2(0, 0)
    VECTOR_3 = Vector3(0, 0, 0)
    NORMAL = "0.0 1.0 0.0"
    GAP_2 = 101


class Folder:
    BASE = Path(__file__).parent.parent.parent.resolve()  # folder: MM1-Map-Editor
    
    SHOP = BASE / "SHOP"
    BUILD = BASE / "build"
    ANGEL = BASE / "angel"
    DEBUG = BASE / "debug" 

    BLENDER_EXPORT = BASE / "blender_export"
    BLENDER_EXPORT_POLYGON = BLENDER_EXPORT / "polygons"
    BLENDER_EXPORT_WAYPOINTS = BLENDER_EXPORT / "waypoints"

    SHOP_CITY = SHOP / "CITY"
    SHOP_RACE = SHOP / "RACE"   
    SHOP_TUNE = SHOP / "TUNE"
    SHOP_BOUND = SHOP / "BND" 
    SHOP_MESHES = SHOP / "BMS" 
    SHOP_MATERIAL = SHOP / "MTL"

    SHOP_TEXTURES_BITMAP = SHOP / "BMP16"
    SHOP_TEXTURES_ALPHA = SHOP / "TEX16A" 
    SHOP_TEXTURES_OPAQUE = SHOP / "TEX16O" 
    SHOP_TEXTURES_PALETTE = SHOP / "TEXP" 

    SHOP_CITY_MAP = SHOP_CITY / f"{MAP_FILENAME}" 
    SHOP_RACE_MAP = SHOP_RACE / f"{MAP_FILENAME}" 

    SHOP_MESH_CITY_MAP = SHOP_MESHES / f"{MAP_FILENAME}CITY"
    SHOP_MESH_LANDMARK_MAP = SHOP_MESHES / f"{MAP_FILENAME}LM"

    SHOP_BOUND_CITY_MAP = SHOP_BOUND / f"{MAP_FILENAME}CITY"
    SHOP_BOUND_LANDMARK_MAP = SHOP_BOUND / f"{MAP_FILENAME}LM"
    
    MIDTOWNMADNESS = BASE / "MidtownMadness"

    MIDTOWNMADNESS_DEV_CITY_MAP = MIDTOWNMADNESS / "dev" / "CITY" / MAP_FILENAME

    USER_RESOURCES = BASE / "Resources" / "User"
    EDITOR_RESOURCES = BASE / "Resources" / "EditorResources"

    DEBUG = BASE / "debug" 

    USER_TEXTURES_CUSTOM = BASE / "src" / "User" / "Textures" / "Custom"

    MAIN = [
        BUILD,
        DEBUG,

        SHOP_TEXTURES_BITMAP,
        SHOP_TEXTURES_ALPHA,
        SHOP_TEXTURES_OPAQUE,

        SHOP_TUNE,
        SHOP_MATERIAL,

        SHOP_CITY_MAP,
        SHOP_RACE_MAP,

        SHOP_MESH_CITY_MAP,
        SHOP_MESH_LANDMARK_MAP,

        SHOP_BOUND_CITY_MAP,
        SHOP_BOUND_LANDMARK_MAP,

        MIDTOWNMADNESS_DEV_CITY_MAP,
    ]
    
    BLENDER = [
        BLENDER_EXPORT_POLYGON,
        BLENDER_EXPORT_WAYPOINTS
    ]

    @classmethod
    def create_all(cls) -> None:
        for folder in cls.MAIN:
            folder.mkdir(parents = True, exist_ok = True)

        if is_process_running(Executable.BLENDER):
            for folder in cls.BLENDER:
                folder.mkdir(parents = True, exist_ok = True)
    

class CommandArgs:
    DEFAULT = f"-path ./dev -allrace -allcars -f -heapsize 499 -maxcops 100 -speedycops -mousemode 1 -l {MAP_FILENAME}"
    QUIET = "-quiet"
    LOG_OPEN = "-logopen"
    VERBOSE = "-agiVerbose"
    CONSOLE = "-console"
    CD_MUSIC = "-cdid"
    NO_AI = "-noai"
    NO_UI = "-noui"
    CIRCUIT = "-circuit"
    RACE = "-race"
    BLITZ = "-blitz"


class Threshold:
    BLITZ_WAYPOINT_COUNT = 11

    CHECKPOINT_RACE_COUNT = 12
    BLITZ_RACE_COUNT = 15
    CIRCUIT_RACE_COUNT = 15
    
    CELL_TYPE_SWITCH = 200
    CELL_CHARACTER_LIMIT = 0xFF  # 255  

    MESH_VERTEX_COUNT = 16
    VERTEX_INDEX_COUNT = 0x8000  # 32768


class ControlType:
    KEYBOARD = "keyboard"
    MOUSE = "mouse"


class Color:
    RED = "#ff0000"
    RED_LIGHT = "#ff8080"
    RED_DARK = "#800000"
    
    GREEN = "#00ff00"
    GREEN_LIGHT = "#80ff80"
    GREEN_DARK = "#008000"
    
    BLUE = "#0000ff"
    BLUE_LIGHT = "#8080ff"
    BLUE_DARK = "#000080"  # Dading: #070644
    
    PURPLE = "#800080"
    PURPLE_LIGHT = "#c080c0"
    PURPLE_DARK = "#400040"
    
    YELLOW = "#ffff00"
    YELLOW_LIGHT = "#ffff80"
    YELLOW_DARK = "#808000"
    
    GOLD = "#ffd700"
    GOLD_LIGHT = "#ffeb80"
    GOLD_DARK = "#806b00"
    
    WHITE = "#ffffff"
    WHITE_DARK = "#cccccc"  # Light gray

    ORANGE = "#ffa500"

    WOOD = "#7b5931"
    SNOW = "#cdcecd"
    WATER = "#5d8096"
    ROAD = "#414441"
    GRASS = "#396d18"

    IND_WALL = "#7b816a"
    BRICKS_MALL = "#e6cab4"
    SHOP_BRICK = "#394441"
    MARKT_BRICK = "#9c9183"
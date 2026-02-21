from src.core.vector.vector_2 import Vector2
from src.core.vector.vector_3 import Vector3

from src.USER.settings.main import MAP_FILENAME


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
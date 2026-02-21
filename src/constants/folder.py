from pathlib import Path

from src.constants.misc import Executable
from src.USER.settings.main import MAP_FILENAME
from src.helpers.main import is_process_running


_BASE = Path(__file__).parent.parent.parent.resolve()
_SHOP = _BASE / "SHOP"
_BLENDER_EXPORT = _BASE / "blender_export"
_MIDTOWN_MADNESS = _BASE / "MidtownMadness"
_RESOURCES = _BASE / "resources"
_DEBUG = _BASE / "debug"


class Folder:
    BASE = _BASE

    class Shop:
        Root     = _SHOP
        City     = _SHOP / "CITY"
        Race     = _SHOP / "RACE"
        Tune     = _SHOP / "TUNE"
        Bound    = _SHOP / "BND"
        Meshes   = _SHOP / "BMS"
        Material = _SHOP / "MTL"

        class Textures:
            Bitmap   = _SHOP / "BMP16"
            Alpha    = _SHOP / "TEX16A"
            Opaque   = _SHOP / "TEX16O"
            Palette  = _SHOP / "TEXP"

        class Map:
            City          = _SHOP / "CITY" / MAP_FILENAME
            Race          = _SHOP / "RACE" / MAP_FILENAME
            MeshCity      = _SHOP / "BMS"  / f"{MAP_FILENAME}CITY"
            MeshLandmark  = _SHOP / "BMS"  / f"{MAP_FILENAME}LM"
            BoundCity     = _SHOP / "BND"  / f"{MAP_FILENAME}CITY"
            BoundLandmark = _SHOP / "BND"  / f"{MAP_FILENAME}LM"

    class Blender:
        Export    = _BLENDER_EXPORT
        Polygons  = _BLENDER_EXPORT / "polygons"
        Waypoints = _BLENDER_EXPORT / "waypoints"
        Models    = _BASE / "blender_models"

    class MidtownMadness:
        Root       = _MIDTOWN_MADNESS
        DevCityMap = _MIDTOWN_MADNESS / "dev" / "CITY" / MAP_FILENAME

    class Resources:
        UserRoot  = _RESOURCES / "user"
        EditorRoot= _RESOURCES / "editor"

        class User:
            Root  = _RESOURCES / "user"
            AI    = _RESOURCES / "user" / "AI"
            Props = _RESOURCES / "user" / "PROPS"
        
        class Editor:
            Root        = _RESOURCES / "editor"
            AI          = _RESOURCES / "editor" / "AI"
            Bounds      = _RESOURCES / "editor" / "BOUNDS"
            DLP         = _RESOURCES / "editor" / "DLP"
            Facades     = _RESOURCES / "editor" / "FACADES"
            Lighting    = _RESOURCES / "editor" / "LIGHTING"
            Meshes      = _RESOURCES / "editor" / "MESHES"
            MTL         = _RESOURCES / "editor" / "MTL"
            Physics     = _RESOURCES / "editor" / "PHYSICS"
            Portals     = _RESOURCES / "editor" / "PORTALS"
            Props       = _RESOURCES / "editor" / "PROPS"
            Race        = _RESOURCES / "editor" / "RACE"
            Textures    = _RESOURCES / "editor" / "TEXTURES"

            class Tune:
                Root          = _RESOURCES / "editor" / "TUNE"
                CarSimulation = _RESOURCES / "editor" / "TUNE" / "MMCARSIM"
                BangerData    = _RESOURCES / "editor" / "TUNE" / "MMBANGERDATA"

    class Debug:
        Root     = _DEBUG
        AI       = _DEBUG / "AI"
        Bounds   = _DEBUG / "BOUNDS"
        DLP      = _DEBUG / "DLP"
        Facades  = _DEBUG / "FACADES"
        Lighting = _DEBUG / "LIGHTING"
        Meshes   = _DEBUG / "MESHES"
        Portals  = _DEBUG / "PORTALS"
        Props    = _DEBUG / "PROPS"

    Build  = _BASE / "build"
    Angel  = _BASE / "angel"

    class Src:
        class User:
            class Textures:
                Custom = _BASE / "src" / "USER" / "textures" / "custom"

    MAIN = [
        Build,
        Debug.Root,
        Shop.Textures.Bitmap,
        Shop.Textures.Alpha,
        Shop.Textures.Opaque,
        Shop.Tune,
        Shop.Material,
        Shop.Map.City,
        Shop.Map.Race,
        Shop.Map.MeshCity,
        Shop.Map.MeshLandmark,
        Shop.Map.BoundCity,
        Shop.Map.BoundLandmark,
        MidtownMadness.DevCityMap,
    ]

    BLENDER = [
        Blender.Polygons,
        Blender.Waypoints,
    ]

    @classmethod
    def create_all(cls) -> None:
        for folder in cls.MAIN:
            folder.mkdir(parents = True, exist_ok = True)
        if is_process_running(Executable.BLENDER):
            for folder in cls.BLENDER:
                folder.mkdir(parents = True, exist_ok = True)

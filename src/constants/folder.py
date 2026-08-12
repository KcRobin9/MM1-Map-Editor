from pathlib import Path

from src.constants.misc import Executable
from src.USER.settings.main import MAP_FILENAME
from src.helpers.main import is_process_running


_BASE      = Path(__file__).parent.parent.parent.resolve()
_SHOP      = _BASE / "SHOP"
_DEBUG     = _BASE / "debug"
_RESOURCES = _BASE / "resources"
_SRC_USER  = _BASE / "src" / "USER"
_BLENDER_EXPORT = _BASE / "blender_export"
_MIDTOWN_MADNESS = _BASE / "MidtownMadness"
_MM_DEV    = _MIDTOWN_MADNESS / "dev"
_RESOURCES = _BASE / "resources"
_USER      = _RESOURCES / "user"
_EDITOR    = _RESOURCES / "editor"
_TUNE      = _EDITOR / "TUNE"


class TextureFolder:
    """Texture sub-folder names the engine expects, used for both SHOP and custom cities."""
    ALPHA   = "TEX16A"   # alpha / cut-out textures (A4R4G4B4)
    OPAQUE  = "TEX16O"   # opaque textures (RGB565)
    BITMAP  = "BMP16"    # minimap / loading-screen JPEGs
    PALETTE = "TEXP"     # palettised textures


class Folder:
    BASE = _BASE
    EDITOR_SCRIPT = _BASE / "MAP_EDITOR_ALPHA_v1.py"

    class Shop:
        Root     = _SHOP
        City     = _SHOP / "CITY"
        Race     = _SHOP / "RACE"
        Tune     = _SHOP / "TUNE"
        Bound    = _SHOP / "BND"
        Meshes   = _SHOP / "BMS"
        Material = _SHOP / "MTL"
        DLP      = _SHOP / "DLP"

        class Textures:
            Bitmap  = _SHOP / TextureFolder.BITMAP
            Alpha   = _SHOP / TextureFolder.ALPHA
            Opaque  = _SHOP / TextureFolder.OPAQUE
            Palette = _SHOP / TextureFolder.PALETTE

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
        DevCityMap = _MM_DEV / "CITY" / MAP_FILENAME
        DevPlayers = _MM_DEV / "players"

    class Resources:
        # city_files/ is split by game: MM1/<CITY> for the editor's own cities, MM2/<CITY> for
        # cities converted from Midtown Madness 2.
        CityFiles    = _RESOURCES / "city_files"
        CityFilesMM1 = CityFiles / "MM1"
        CityFilesMM2 = CityFiles / "MM2"

        class User:
            Root     = _USER
            AI       = _USER / "AI"
            Props    = _USER / "PROPS"
            Facades  = _USER / "FACADES"
            Portals  = _USER / "PORTALS"
            Lighting = _USER / "LIGHTING"
            Meshes   = _USER / "MESHES"
            Bounds   = _USER / "BOUNDS"
            DLP      = _USER / "DLP"
            Physics  = _USER / "PHYSICS"

        class Editor:
            Root          = _EDITOR
            Custom        = _EDITOR / "custom"   # per-city custom-prop assets: custom/<CITY>/{MESHES,BND,TUNE,TEXTURES}
            AI            = _EDITOR / "AI"
            BMS           = _EDITOR / "BMS"
            Bound         = _EDITOR / "BND"
            Bounds        = _EDITOR / "BOUNDS"
            DLP           = _EDITOR / "DLP"
            Facades       = _EDITOR / "FACADES"
            Lighting      = _EDITOR / "LIGHTING"
            Meshes        = _EDITOR / "MESHES"
            MeshesCars    = _EDITOR / "MESHES" / "CARS"
            MeshesFacades = _EDITOR / "MESHES" / "FACADES"
            MeshesProps   = _EDITOR / "MESHES" / "PROPS"
            MeshesMisc    = _EDITOR / "MESHES" / "MISC"
            MTL           = _EDITOR / "MTL"
            Physics       = _EDITOR / "PHYSICS"
            Portals       = _EDITOR / "PORTALS"
            Props         = _EDITOR / "PROPS"
            Race          = _EDITOR / "RACE"
            Textures      = _EDITOR / "TEXTURES"
            Rex           = _EDITOR / "REX"
            PedAnim       = _EDITOR / "ANIM"

            class Tune:
                Root          = _TUNE
                CarSimulation = _TUNE / "MMCARSIM"
                BangerData    = _TUNE / "MMBANGERDATA"

    class Debug:
        Root     = _DEBUG
        Input    = _DEBUG / "input"
        Output   = _DEBUG / "output"
        AI       = _DEBUG / "AI"
        Bounds   = _DEBUG / "BOUNDS"
        DLP      = _DEBUG / "DLP"
        Facades  = _DEBUG / "FACADES"
        Lighting = _DEBUG / "LIGHTING"
        Meshes   = _DEBUG / "MESHES"
        Portals  = _DEBUG / "PORTALS"
        Props    = _DEBUG / "PROPS"

    Build = _BASE / "build"
    Angel = _BASE / "angel"

    class Src:
        class User:
            Root          = _SRC_USER
            Props         = _SRC_USER / "props" / "props.py"
            Facades       = _SRC_USER / "facades.py"
            PlayerProfile = _SRC_USER / "player_profile.py"
            Maps          = _SRC_USER / "maps"
            Mm2Edits      = _SRC_USER / "mm2_edits"

            class Textures:
                Custom = _SRC_USER / "textures" / "custom"

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

    BLENDER = [Blender.Polygons, Blender.Waypoints]

    @classmethod
    def create_all(cls) -> None:
        for folder in cls.MAIN:
            folder.mkdir(parents=True, exist_ok=True)
        if is_process_running(Executable.BLENDER):
            for folder in cls.BLENDER:
                folder.mkdir(parents=True, exist_ok=True)
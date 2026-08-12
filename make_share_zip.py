"""
Bundle a shareable Open1560 city package --- the MINIMUM set a friend needs, so the
"textures didn't load / texsheet crash" mistake can't happen again.

What goes in (and why):
  * !!!!!<CITY>.ar      Geometry, textures (DDS), props and AI --- self-contained per city
  * dev/MTL/GLOBAL.TSH  The LOOSE texture sheet that REGISTERS every custom texture name. It lives
                        OUTSIDE the .ar; without it Open1560 fatals with "Trying to load texture
                        not in texsheet". Must be a UNION sheet, which EXTRA_TEXTURE_DIRS produces
  * README_INSTALL.txt  Where to drop the files
  * Open1560.exe + SDL3.dll + commandline.txt, only with --exe (skip if they run your build already)

Usage:
  python make_share_zip.py                     # every built MM2 city found on disk
  python make_share_zip.py MM2SF MM2London     # just these
  python make_share_zip.py --exe               # also bundle the exe / dll / commandline
  python make_share_zip.py --blender           # BLENDER DATA PACK instead: the git-ignored data a
                                               # friend's repo download lacks (resources/city_files/
                                               # <city>, src/USER/textures/custom*, MM2_PROPS store)
                                               # so the Map Loader panel can load MM2 cities visually.
"""
import sys
import time
import zipfile
from pathlib import Path
from typing import List

from src.constants.city import City
from src.constants.folder import Folder
from src.constants.file_formats import FileType, CITY_AR_PREFIX
from src.constants.custom_props import get_custom_city
from src.ui.console import ok, item

# The loose sheet lives OUTSIDE the .ar, under the game's dev tree, and must ship alongside it.
LOOSE_TEXTURE_SHEET = Path("dev") / "MTL" / f"GLOBAL{FileType.TEXTURE_SHEET}"
OPTIONAL_GAME_FILES = ("Open1560.exe", "SDL3.dll", f"commandline{FileType.TEXT}")

# Packs land beside the repo rather than inside it, so a build never sweeps them into a commit.
OUTPUT_FOLDER = Folder.BASE.parent

BYTES_PER_MB = 1e6
BYTES_PER_KB = 1e3

EXE_FLAG = "--exe"
BLENDER_FLAG = "--blender"
CITY_ARCHIVE_GLOB = f"{CITY_AR_PREFIX}MM2*{FileType.ANGEL_RESOURCE}"

README_BLENDER = """MM1 MAP EDITOR --- BLENDER DATA PACK (for MM2 cities)
The editor repo ships code only; this pack adds the git-ignored DATA it needs.

1. Extract this zip INTO your MM1-Map-Editor folder (the paths line up; merge/overwrite).
2. Set up Blender + VS Code by following setup/SETUP.md in the repo.
3. In src/USER/settings/fast.py set:  CONNECT_BLENDER_ONLY = True
4. Run MAP_EDITOR_ALPHA_v1.py from VS Code (SETUP.md covers this). Blender opens with an empty
   scene and every panel ready.
5. In the 3D view press N -> "Map Loader" tab -> Select Folder -> pick a city under
   resources/city_files -> Load City. It loads fully textured; toggles load meshes/props separately.
"""

# Git-ignored data the Map Loader needs. Taken from the Folder/City constants so a folder rename
# cannot leave this pack quietly shipping nothing.
BLENDER_DATA_DIRS = (
    Folder.Src.User.Textures.Custom.parent,          # custom* DDS (all cities, union)
    get_custom_city(City.Mm2Props.folder).root,      # prop meshes / tunes / textures
)


README = """OPEN1560 MM2-CITY PACK --- INSTALL
1. Copy the !!!!!*.ar file(s) into your MidtownMadness folder (next to Open1560.exe).
2. Copy dev\\MTL\\GLOBAL.TSH into MidtownMadness\\dev\\MTL\\  (create the folders if needed).
   THIS FILE IS REQUIRED --- without it the game crashes with "texture not in texsheet".
3. (If included) Open1560.exe + SDL3.dll + commandline.txt go next to the .ar files.
4. Start Open1560 -> the cities appear in the race locale menu.
"""


def find_built_cities() -> List[str]:
    """Every MM2 city with a packed .ar in MidtownMadness/, newest build order irrelevant."""
    packed = Folder.MidtownMadness.Root.glob(CITY_ARCHIVE_GLOB)

    return sorted(path.stem[len(CITY_AR_PREFIX):] for path in packed)


def bundle(cities: List[str], with_exe: bool) -> Path:
    texture_sheet = Folder.MidtownMadness.Root / LOOSE_TEXTURE_SHEET
    if not texture_sheet.is_file():
        raise SystemExit(f"{LOOSE_TEXTURE_SHEET} missing --- run a build first, it writes the loose sheet")

    output = OUTPUT_FOLDER / f"MM2_share_{'_'.join(cities)}_{time.strftime('%Y%m%d')}.zip"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for city in cities:
            city_archive = (Folder.MidtownMadness.Root /
                            f"{CITY_AR_PREFIX}{city}{FileType.ANGEL_RESOURCE}")
            if not city_archive.is_file():
                raise SystemExit(f"{city_archive.name} not found --- build {city} first")
            archive.write(city_archive, city_archive.name)
            item(f"{city_archive.name}  ({city_archive.stat().st_size / BYTES_PER_MB:.0f} MB)")

        archive.write(texture_sheet, LOOSE_TEXTURE_SHEET.as_posix())
        item(f"{LOOSE_TEXTURE_SHEET.as_posix()}  ({texture_sheet.stat().st_size / BYTES_PER_KB:.0f} KB)"
             f"  <- the piece everyone forgets")

        archive.writestr(f"README_INSTALL{FileType.TEXT}", README)

        if with_exe:
            for name in OPTIONAL_GAME_FILES:
                game_file = Folder.MidtownMadness.Root / name
                if game_file.is_file():
                    archive.write(game_file, name)
                    item(name)

    return output


def bundle_blender_pack(cities: List[str]) -> Path:
    base = Folder.BASE
    output = OUTPUT_FOLDER / f"MM2_blender_pack_{'_'.join(cities)}_{time.strftime('%Y%m%d')}.zip"

    def add_tree(root: Path) -> int:
        """Add every file under `root`, keeping its path relative to the repo. Returns the count."""
        added = 0
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(base).as_posix())
                added += 1

        return added

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for city in cities:
            city_dir = Folder.Resources.CityFiles / city
            if not city_dir.is_dir():
                raise SystemExit(f"{city_dir.relative_to(base).as_posix()} missing --- run a normal "
                                 f"build first (the build exports it)")
            item(f"{city_dir.relative_to(base).as_posix()}  ({add_tree(city_dir)} files)")

        for data_dir in BLENDER_DATA_DIRS:
            if data_dir.is_dir():
                item(f"{data_dir.relative_to(base).as_posix()}  ({add_tree(data_dir)} files)")

        archive.writestr(f"README_BLENDER{FileType.TEXT}", README_BLENDER)

    return output


def main() -> None:
    arguments = sys.argv[1:]
    with_exe = EXE_FLAG in arguments
    blender_pack = BLENDER_FLAG in arguments
    cities = [argument for argument in arguments if not argument.startswith("--")]

    if not cities:
        cities = find_built_cities()
    if not cities:
        raise SystemExit(f"no {CITY_ARCHIVE_GLOB} found --- build a city first")

    if blender_pack:
        output = bundle_blender_pack(cities)
        ok(f"Packed Blender data for {len(cities)} city(ies) -> {output}  "
           f"({output.stat().st_size / BYTES_PER_MB:.0f} MB)")
        return

    output = bundle(cities, with_exe)
    ok(f"Packed {len(cities)} city package(s) -> {output}  ({output.stat().st_size / BYTES_PER_MB:.0f} MB)")


if __name__ == "__main__":
    main()

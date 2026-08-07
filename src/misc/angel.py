import os
import subprocess
import shutil
from pathlib import Path

from src.constants.folder import Folder
from src.constants.constants import REQUIRED_ANGEL_FILES
from src.USER.settings.main import MAP_FILENAME
from src.ui.console import ok, item, red


def copy_angel_resources(shop_folder: Path) -> None:
    for file in Folder.Angel.iterdir():
        if file.name.upper() in REQUIRED_ANGEL_FILES:
            shutil.copy(file, shop_folder / file.name)
            ok(f"Copied {file.name} to SHOP")


_CITY_DATA_EXTS = {'.bng', '.cells', '.ext', '.ptl'}


def _build_shiplist(shop_folder: Path, shiplist_path: Path) -> int:
    """Write every file under the SHOP as a `.\\relative\\path` line (mkar input)."""
    _own_city = MAP_FILENAME.lower()
    lines = []
    for root, _, files in os.walk(shop_folder):
        for f in files:
            if f.lower() in ("run.bat", "ship.bat", "shiplist"):
                continue  # packing helpers, not city data
            rel = os.path.relpath(os.path.join(root, f), shop_folder).replace("/", "\\")
            # Exclude other cities' top-level city data files (BNG/CELLS/EXT/PTL).
            # Without this filter each AR would pack stale copies of other cities'
            # files left in SHOP from previous builds, and because ARs are searched
            # alphabetically the first AR that contains city/MM2SF.bng wins — which
            # may be London (3rd alpha) serving a pre-traffic-lights 5449-banger BNG
            # instead of the freshly built 6263-banger one in the SF AR (5th alpha).
            parts = rel.lower().split('\\')
            if len(parts) == 2 and parts[0] == 'city':
                stem, ext = os.path.splitext(parts[1])
                if ext in _CITY_DATA_EXTS and stem != _own_city:
                    continue
            lines.append(".\\" + rel)
    shiplist_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def run_angel_process(shop_folder: Path) -> bool:
    """
    Pack the SHOP into MidtownMadness/!!!!!{MAP}.ar with mkar. Returns True on success.

    Rewritten to (a) build the shiplist in Python instead of the bundled run.bat — which
    hardcodes a non-existent `\\vck\\shop` path and silently packed an EMPTY archive — and
    (b) run mkar BLOCKING (subprocess.run) so the archive is fully written before the build
    continues to cleanup / delete_shop (the old Popen raced that and produced a ~1 KB AR).
    """
    mm = Path(Folder.MidtownMadness.Root)
    ar_tag = f"!!!!!{MAP_FILENAME}"
    shiplist = mm / f"shiplist.{ar_tag}"
    ar_out = mm / f"{ar_tag}.ar"
    mkar = Path(Folder.Angel) / "mkar.exe"

    count = _build_shiplist(Path(shop_folder), shiplist)
    if count == 0:
        item(red("SHOP is empty — no AR written"))
        return False
    if not mkar.exists():
        item(red(f"mkar.exe not found at {mkar} — no AR written"))
        return False

    result = subprocess.run(
        [str(mkar), str(ar_out), str(shiplist)],
        cwd=str(shop_folder), capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        item(red(f"mkar failed (exit {result.returncode}): "
                 f"{(result.stderr or result.stdout or '').strip()[:400]}"))
        return False

    size_kb = ar_out.stat().st_size / 1024 if ar_out.exists() else 0
    ok(f"Packed {count} file(s) -> {ar_out.name} ({size_kb:.0f} KB)")
    return True


def _sync_city_data_to_dev(shop_folder: Path) -> None:
    """Copy this city's BNG/CELLS/EXT/PTL from SHOP to dev/CITY/ as HFS overrides.

    Required because older city ARs (e.g. !!!!!MM2London.ar) that sort earlier
    alphabetically may contain a stale copy of city/MM2SF.* from a previous build.
    The HFS (-path ./dev) is searched first, so a fresh copy here always wins.
    """
    dev_city = Path(Folder.MidtownMadness.Root) / "dev" / "CITY"
    if not dev_city.exists():
        return
    shop_city = Path(shop_folder) / "city"
    copied = []
    for ext in ("BNG", "CELLS", "EXT", "PTL"):
        src = shop_city / f"{MAP_FILENAME}.{ext}"
        if src.exists():
            shutil.copy2(src, dev_city / f"{MAP_FILENAME}.{ext}")
            copied.append(ext)
    if copied:
        ok(f"Synced city data to dev/CITY/: {MAP_FILENAME}.{{{','.join(copied)}}}")


def create_angel_resource_file(shop_folder: Path) -> None:
    copy_angel_resources(shop_folder)
    if not run_angel_process(shop_folder):
        return                      # packing failed — run_angel_process already said why
    _sync_city_data_to_dev(shop_folder)
    ok(f"Created {MAP_FILENAME}.ar")

import subprocess
import shutil
from pathlib import Path

from src.constants.folder import Folder
from src.constants.constants import REQUIRED_ANGEL_FILES
from src.USER.settings.main import MAP_FILENAME
from src.ui.console import ok


def copy_angel_resources(shop_folder: Path) -> None:
    for file in Folder.Angel.iterdir():
        if file.name.upper() in REQUIRED_ANGEL_FILES:
            shutil.copy(file, shop_folder / file.name)
            ok(f"Copied {file.name} to SHOP")

def run_angel_process(shop_folder: Path) -> None:
    subprocess.Popen(f"cmd.exe /c run !!!!!{MAP_FILENAME}", cwd=shop_folder, creationflags=subprocess.CREATE_NO_WINDOW)

def create_angel_resource_file(shop_folder: Path) -> None:
    copy_angel_resources(shop_folder)
    run_angel_process(shop_folder)
    ok(f"Created {MAP_FILENAME}.ar")

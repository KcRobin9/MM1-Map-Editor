import subprocess
import shutil
from pathlib import Path

from src.constants.misc import Folder
from src.USER.settings.main import MAP_FILENAME
from src.constants.constants import REQUIRED_ANGEL_FILES


def copy_angel_resources(shop_folder: Path) -> None:
    for file in Folder.ANGEL.iterdir():
        if file.name.upper() in REQUIRED_ANGEL_FILES:
            shutil.copy(file, shop_folder / file.name)
            print(f"Copied {file.name} to SHOP folder.")


def run_angel_process(shop_folder: Path) -> None:
    subprocess.Popen(f"cmd.exe /c run !!!!!{MAP_FILENAME}", cwd=shop_folder, creationflags=subprocess.CREATE_NO_WINDOW)


def create_angel_resource_file(shop_folder: Path) -> None:
    copy_angel_resources(shop_folder)
    run_angel_process(shop_folder)
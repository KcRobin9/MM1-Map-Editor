import shutil
from typing import List
from pathlib import Path

from src.USER.settings.main import MAP_NAME, MAP_FILENAME


def create_map_info(output_file: Path, blitz_race_names: List[str], circuit_race_names: List[str], checkpoint_race_names: List[str]) -> None:
    with open (output_file, "w") as f:
        
        f.write(f"""
LocalizedName={MAP_NAME}
MapName={MAP_FILENAME}
RaceDir={MAP_FILENAME}
BlitzCount={len(blitz_race_names)}
CircuitCount={len(circuit_race_names)}
CheckpointCount={len(circuit_race_names)}
BlitzNames={'|'.join(blitz_race_names)}
CircuitNames={'|'.join(circuit_race_names)}
CheckpointNames={'|'.join(checkpoint_race_names)}
""")


def copy_files_to_folder (input_folder: Path, output_folder: Path, pattern: str = "*") -> None:
    for file in input_folder.glob(pattern):
        if file.is_file():
            shutil.copy(file, output_folder / file.name)


def copy_custom_textures_to_shop(input_folder: Path, output_folder: Path) -> None:
    copy_files_to_folder (input_folder, output_folder)


def copy_carsim_files_to_shop(input_folder: Path, output_folder: Path, file_type: str) -> None:
    copy_files_to_folder(input_folder, output_folder, f"*{file_type}")


def ensure_empty_mm_dev_folder(input_folder: Path) -> None:
    if input_folder.is_dir():
        for file in input_folder.iterdir():
            if file.is_file():
                file.unlink()
    else:
        input_folder.mkdir(parents=True, exist_ok=True)
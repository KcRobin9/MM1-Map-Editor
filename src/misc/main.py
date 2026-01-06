import os
import time 
import shutil
import subprocess
from pathlib import Path

from src.constants.misc import Folder, Executable, CommandArgs, ControlType
from src.constants.modes import RaceMode
from src.constants.constants import NOTEPAD_PLUS_PATHS

from src.helpers.main import is_process_running


def post_editor_cleanup(build_folder: Path, shop_folder: Path, delete_shop: bool) -> None:
    os.chdir(Folder.BASE)
    time.sleep(1)  # Make sure folders are no longer in use (i.e. an .ar file is still being created)
    
    try:  # Always delete the build folder
        shutil.rmtree(build_folder)
        print(f"Successfully deleted the BUILD folder")
    except Exception as e:
        print(f"\nFailed to delete the BUILD directory. Reason: {e}\n")
    
    if delete_shop:  # Only delete shop folder if "delete_shop" is True
        try:
            shutil.rmtree(shop_folder)
            print(f"Successfully deleted the SHOP folder")
        except Exception as e:
            print(f"\nFailed to delete the SHOP directory. Reason: {e}\n")


def create_commandline(output_file: Path, no_ui: bool, no_ui_type: str, no_ai: bool, set_music: bool, less_logs: bool, more_logs: bool) -> None:

    cmd_line = CommandArgs.DEFAULT

    if less_logs and more_logs:    
        log_error_message = f"""\n
        ***ERROR***
        You can't have both 'quiet' and 'more logs' enabled. Please choose one."
        """
        raise ValueError(log_error_message)
   
    if less_logs:
        cmd_line += f" {CommandArgs.QUIET}"
       
    if more_logs:
        cmd_line += f" {CommandArgs.LOG_OPEN} {CommandArgs.VERBOSE} {CommandArgs.CONSOLE}"
       
    if set_music:
        cmd_line += f" {CommandArgs.CD_MUSIC}"
   
    if no_ai:
        cmd_line += f" {CommandArgs.NO_AI}"
    
    if no_ui:
        if not no_ui_type or no_ui_type.lower() == "cruise":
            cmd_line += f" -noui {ControlType.KEYBOARD}"
        else:
            race_type, race_index = no_ui_type.split()
            if race_type not in ["circuit", "race", "blitz"]:
                type_error_message = f"""\n
                ***ERROR***
                Invalid Race Type provided. Available types are {RaceMode.BLITZ}, {RaceMode.CHECKPOINT}, and {RaceMode.CIRCUIT}.
                """
                raise ValueError(type_error_message)
                                            
            if not 0 <= int(race_index) <= 14:
                index_error_message = """\n
                ***ERROR***
                Invalid Race Index provided. It should be between 0 and 14.
                """
                raise ValueError(index_error_message)
            
            cmd_line += f" -noui -{race_type} {race_index} -{ControlType.KEYBOARD}"
        
    with open(output_file, "w") as f:
        f.write(cmd_line)

      
def start_game(mm1_folder: str, executable: str, play_game: bool) -> None:    
    if not play_game or is_process_running(Executable.BLENDER) or is_process_running(executable):
        return
    
    subprocess.run(mm1_folder / executable, cwd = mm1_folder)
    print(f"Successfully started {executable}")


def open_with_notepad_plus(input_file: Path) -> None:
    notepad_plus_exe = shutil.which(Executable.NOTEPAD_PLUS_PLUS)  
    
    if notepad_plus_exe:
        subprocess.Popen([notepad_plus_exe, input_file])
        print("Opening file with Notepad++ from PATH.")
        return

    for path in NOTEPAD_PLUS_PATHS:
        subprocess.Popen([path, input_file])
        print(f"Opening file with Notepad++ from hardcoded path: {path}")
        return

    try:
        subprocess.Popen([Executable.NOTEPAD, input_file])
        print("Notepad++ not found, opening file with Classic Notepad.")
    except FileNotFoundError:
        print("Neither Notepad++ nor Classic Notepad found. Unable to open file.")
        raise
import time
import pickle
import logging
import threading
from pathlib import Path
from colorama import Fore, Style, init

from src.Constants.progress_bar import BAR_DIVIDER, PROGRESS_BAR_WIDTH, DEFAULT_RUN_TIME, PROGRESS_UPDATE_INTERVAL, DISABLED_UPDATE_INTERVAL


init(autoreset = True)  # Initialize colorama


class ProgressBar:
    def __init__(self, map_name: str, disable_progress: bool = False):
        self.map_name = map_name
        self.disable_progress = disable_progress
        self.colors = [Style.BRIGHT + color for color in (Fore.RED, Fore.YELLOW, Fore.GREEN)]
        
    def _get_color(self, progress: float) -> str:
        if progress < 33:
            return self.colors[0]
        elif progress < 66:
            return self.colors[1]
        return self.colors[2]
    
    def create_divider(self) -> str:
        return "\n" + "".join(self.colors[i % len(self.colors)] + char for i, char in enumerate(BAR_DIVIDER)) + "\n"
    
    def update(self, progress: float) -> None:
        progress = max(0, min(100, progress))  # Clamp between 0-100
        color = self._get_color(progress)
        
        filled = "#" * (int(progress) // (100 // PROGRESS_BAR_WIDTH))
        empty = "." * (PROGRESS_BAR_WIDTH - len(filled))
        
        progress_line = (f"{color}   Creating... {self.map_name} [{filled}{empty}] {int(progress)}%{Style.RESET_ALL}")
        
        if not self.disable_progress:
            print("\033[H\033[J", end="")
        
        print(f"{self.create_divider()}\n{progress_line}\n{self.create_divider()}\n", end="")


class RunTimeManager:
    def __init__(self, file_path: Path):
        self.file_path = file_path
    
    def load(self) -> float:
        if not self.file_path.exists():
            return DEFAULT_RUN_TIME
            
        try:
            with self.file_path.open('rb') as f:
                return pickle.load(f)
        except (EOFError, pickle.PickleError, OSError) as e:
            logging.warning(f"Error loading run time: {e}")
            return DEFAULT_RUN_TIME
    
    def save(self, run_time: float) -> None:
        try:
            with self.file_path.open('wb') as f:
                pickle.dump(run_time, f)
        except OSError as e:
            logging.error(f"Failed to save run time: {e}")


def track_progress(duration: float, map_name: str, disable_progress: bool = False) -> None:
    progress_bar = ProgressBar(map_name, disable_progress)
    start_time = time.monotonic()
    
    while True:
        elapsed = time.monotonic() - start_time
        progress = (elapsed / duration) * 100
        
        progress_bar.update(progress)
        
        if progress >= 100:
            break
            
        if disable_progress:
            time.sleep(DISABLED_UPDATE_INTERVAL)
        else:
            time.sleep(PROGRESS_UPDATE_INTERVAL)


def start_progress_tracking(map_name: str, runtime_file: Path, disable_progress: bool = False) -> tuple[threading.Thread, float]:
    runtime_manager = RunTimeManager(runtime_file)
    duration = runtime_manager.load()
    
    thread = threading.Thread(target=track_progress, args=(duration, map_name, disable_progress), daemon=True)
    
    thread.start()
    start_time = time.monotonic()
    
    return thread, start_time
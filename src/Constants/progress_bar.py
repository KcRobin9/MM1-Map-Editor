from pathlib import Path
from colorama import Fore
from typing import Final, List


BAR_DIVIDER: str = "=" * 60
PROGRESS_BAR_WIDTH: Final[int] = 20
DEFAULT_RUN_TIME: Final[float] = 2.0
PROGRESS_UPDATE_INTERVAL: Final[float] = 0.025
DISABLED_UPDATE_INTERVAL: Final[float] = 5.0

EDITOR_RUNTIME_FILE = Path("editor_runtime.pkl")

COLORS_ONE: Final[List[str]] = [
    Fore.RED, Fore.LIGHTRED_EX, Fore.YELLOW, Fore.LIGHTYELLOW_EX, 
    Fore.GREEN, Fore.LIGHTGREEN_EX, Fore.CYAN, Fore.LIGHTCYAN_EX, 
    Fore.BLUE, Fore.LIGHTBLUE_EX, Fore.MAGENTA, Fore.LIGHTMAGENTA_EX
]

COLORS_TWO: Final[List[str]] = [
    Fore.LIGHTGREEN_EX, Fore.GREEN, Fore.CYAN, Fore.LIGHTCYAN_EX,
    Fore.BLUE, Fore.LIGHTBLUE_EX
]

COLOR_DIVIDER = "\n" + "".join(COLORS_TWO[i % len(COLORS_TWO)] + char for i, char in enumerate(BAR_DIVIDER)) + "\n"
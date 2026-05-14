import datetime


NO  = 0
YES = 1

ON  = 1
OFF = 0

HUGE = 1E10

PROP_CAN_COLLIDE_FLAG = 0x800

REQUIRED_ANGEL_FILES = ["RUN.BAT", "SHIP.BAT"]

CURRENT_TIME_FORMATTED = datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
    
#TODO: find a better location for this
NOTEPAD_PLUS_PATHS = [
    rf"{drive}:\{folder}\Notepad++\notepad++.exe"
    for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for folder in ["Program Files", "Program Files (x86)"]
]
import datetime


NO  = 0
YES = 1

ON  = 1
OFF = 0

HUGE = 1E10

PROP_CAN_COLLIDE_FLAG = 0x800

REQUIRED_ANGEL_FILES = ["RUN.BAT", "SHIP.BAT"]

TIME_FORMAT = "%Y_%d_%m_%H%M_%S"


# Read at the moment of the call, never at import. A module-level stamp is fixed for the whole
# Blender session, so exporting or backing up twice writes the same filename and the second run
# silently overwrites the first.
def current_time_formatted() -> str:
    return datetime.datetime.now().strftime(TIME_FORMAT)
    
#TODO: find a better location for this
NOTEPAD_PLUS_PATHS = [
    rf"{drive}:\{folder}\Notepad++\notepad++.exe"
    for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for folder in ["Program Files", "Program Files (x86)"]
]
import datetime


NO = 0  
YES = 1 

HUGE = 1E10

PROP_CAN_COLLIDE_FLAG = 0x800

REQUIRED_ANGEL_FILES = ["RUN.BAT", "SHIP.BAT"]

CURRENT_TIME_FORMATTED = datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
    
#TODO: find a better location for this
NOTEPAD_PLUS_PATHS = [
    r"C:\Program Files\Notepad++\notepad++.exe", 
    r"C:\Program Files (x86)\Notepad++\notepad++.exe"
    ]
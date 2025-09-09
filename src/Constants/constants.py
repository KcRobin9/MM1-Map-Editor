import datetime


NO = 0  
YES = 1 

HUGE = 1E10

PROP_CAN_COLLIDE_FLAG = 0x800

CURRENT_TIME_FORMATTED = datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
    
TEXTURESHEET_HEADER = ["name", "neighborhood", "h", "m", "l", "flags", "alternate", "sibling", "xres", "yres", "hexcolor"]
    
LIGHTING_HEADER = [
    "TimeOfDay", "Weather", "Sun Heading", "Sun Pitch", "Sun Red", "Sun Green", "Sun Blue",
    "Fill-1 Heading", "Fill-1 Pitch", "Fill-1 Red", "Fill-1 Green", "Fill-1 Blue",
    "Fill-2 Heading", "Fill-2 Pitch", "Fill-2 Red", "Fill-2 Green", "Fill-2 Blue",
    "Ambient Red", "Ambient Green", "Ambient Blue", 
    "Fog End", "Fog Red", "Fog Green", "Fog Blue", 
    "Shadow Alpha", "Shadow Red", "Shadow Green", "Shadow Blue"
]

#TODO: find a better location for this
NOTEPAD_PLUS_PATHS = [
    r"C:\Program Files\Notepad++\notepad++.exe", 
    r"C:\Program Files (x86)\Notepad++\notepad++.exe"
    ]
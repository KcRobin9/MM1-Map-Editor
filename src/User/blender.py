from src.Constants.misc import Folder


# Load textures
load_all_texures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# Input waypoint file
waypoint_file = Folder.EDITOR_RESOURCES / "RACE" / "RACE2WAYPOINTS.CSV"  

# Waypoints from the Editor ("race_data")
waypoint_number_input = "0", 
waypoint_type_input = "RACE"
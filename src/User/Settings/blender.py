from src.constants.misc import Folder


# Textures
load_all_texures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# AI streets
visualize_ai_paths = False      # Change to "True" if you want to visualize the AI streets in the Blender 

# Waypoints
input_waypoint_file = Folder.EDITOR_RESOURCES / "RACE" / "RACE2WAYPOINTS.CSV"  

# Waypoints from the Editor ("race_data")
waypoint_number_input = "0", 
waypoint_type_input = "RACE"

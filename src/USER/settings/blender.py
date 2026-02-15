from src.constants.misc import Folder

load_target_model = True               # Set True to load an external model instead of the test city
target_blend_file = Folder.BLENDER_MODELS / "RACECITY_2ND.blend"  # Only used when load_target_model = True

# Textures
load_all_textures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# AI streets
visualize_ai_paths = False      # Change to "True" if you want to visualize the AI streets in the Blender 

# Waypoints
input_waypoint_file = Folder.RESOURCES_EDITOR / "RACE" / "RACE2WAYPOINTS.CSV"  

# Waypoints from the Editor ("race_data")
waypoint_number_input = "0", 
waypoint_type_input = "RACE"

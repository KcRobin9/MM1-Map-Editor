from pathlib import Path
from src.constants.folder import Folder

load_target_model = False               # Set True to load an external model instead of the test city
target_blend_file = Folder.Blender.Models / "RACECITY_2ND.blend"  # Only used when load_target_model = True

# Textures
load_all_textures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# AI streets
visualize_ai_paths = False      # Change to "True" if you want to visualize the AI streets in the Blender

# Props
visualize_props = True          # Set True to place props in the Blender scene
prop_bms_folder = Folder.Resources.Editor.BMS   # Root folder containing per-prop BMS subfolders

# Car prop detail options (VP* / VA* vehicles)
prop_car_wheels  = True         # Set True to load and place individual wheel meshes (WHL0–3_H.BMS)
prop_car_lights  = False         # Set True to also load headlight / tail-light / rear-light meshes

# Bulk city BMS import
# Set to a list of folders, each containing *_H.BMS files directly (not in subfolders).
# Example: bulk_bms_folders = [Path("TEST_BMS_CITY/CHICAGOCITY"), Path("TEST_BMS_CITY/CHICAGOLM")]
# Set to [] or None to disable.
# bulk_bms_folders = [Path("TEST_BMS_CITY/all")]  # single folder; use a list for multiple
bulk_bms_folders = []  # No bulk import by default; set to a list of folders to enable

# Waypoints
input_waypoint_file = Folder.Resources.Editor.Race / "RACE2WAYPOINTS.CSV"

# Cops & Robbers Waypoints
input_cnr_waypoint_file = Folder.Resources.Editor.Race / "COPSWAYPOINTS.CSV"

# Waypoints from the Editor ("race_data")
waypoint_number_input = "0"
waypoint_type_input = "RACE"

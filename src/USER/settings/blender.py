from pathlib import Path
from src.constants.folder import Folder

load_target_model = False               # Set True to load an external model instead of the test city
target_blend_file = Folder.Blender.Models / "RACECITY_2ND.blend"  # Only used when load_target_model = True

# Textures
load_all_textures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# Props & Facades
visualize_props    = True       # Set True to place props in the Blender scene
visualize_facades  = True       # Set True to place facades in the Blender scene
prop_bms_folder = Folder.Resources.Editor.Meshes   # Root folder; subfolders CARS/PROPS/MISC are searched automatically

# Car prop detail options (VP* / VA* vehicles)
prop_car_wheels  = True         # Set True to load and place individual wheel meshes (WHL0–3_H.BMS)
prop_car_lights  = False         # Set True to also load headlight / tail-light / rear-light meshes

# Bridges (.GIZMO)
open_bridges        = True              # Visual only — tilt each drawbridge half up around its outer hinge so the two halves form a V at the middle
open_bridges_angle  = 0.471239 * 100    # Tilt angle in degrees (0 = flat / closed, 90 = fully vertical)S
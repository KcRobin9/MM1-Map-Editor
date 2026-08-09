from pathlib import Path
from src.constants.folder import Folder

load_target_model = False               # Set True to load an external model instead of the test city
target_blend_file = Folder.Blender.Models / "RACECITY_2ND.blend"  # Only used when load_target_model = True

# Textures
load_all_textures = False        # Change to "True" if you want to load all textures (materials) (slower loading time)
                                # Change to "False" if you want to load only the textures that are used in your Map (faster loading time)

# Props, Facades & Bridges
visualize_props    = True       # Set True to place props in the Blender scene
visualize_facades  = True       # Set True to place facades in the Blender scene
visualize_bridges  = True       # Set True to place bridges in the Blender scene (reads USER/bridges.py)
prop_bms_folder = Folder.Resources.Editor.Meshes   # Root folder; subfolders CARS/PROPS/MISC are searched automatically

# Car prop detail options (VP* / VA* vehicles)
prop_car_wheels  = True         # Set True to load and place individual wheel meshes (WHL0–3_H.BMS)
prop_car_lights  = False         # Set True to also load headlight / tail-light / rear-light meshes

# Bridges
open_bridges        = True              # Visual only — tilt each drawbridge half up around its outer hinge so the two halves form a V at the middle
open_bridges_angle  = 0.26 * 100    # default value. Value for multiplayer is: : 0.471239 * 100

# MM2 City Import (only used when MM2_CITY is set)
MM2_BLENDER_VIZ = "cell"        # "cell" = one object per landmark cell (fast), "poly" = one per polygon
                                # (full detail, slow --- SF is ~129k objects), "none" = skip the preview
MM2_PROPS_MERGED = True         # Set True to bake each prop TYPE into one object (~6.3k props -> ~37 objects)
                                # Set False for per-instance editing at the cost of a heavier scene
MM2_EXPORT_CITY_FOLDER = True   # Set True to also copy the baked city into resources/city_files/<NAME>/
                                # so the Map Loader panel can reload it after delete_shop wipes SHOP
MM2_SAVE_RELOAD_AFTER_BUILD = True  # Set True to save + reopen the .blend after a build (rebuilds every GPU
                                # batch from scratch; works around the Blender 4.3 NVIDIA draw crash)

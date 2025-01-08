from src.Constants.textures import Texture


# Map Name
MAP_NAME = "My First City"                      # Can be multiple words --- name of the Map in the Race Locale Menu
MAP_FILENAME = "First_City"                     # One word (no spaces)  --- name of the .AR file and the folder in the SHOP folder
   
# Play Game
play_game = True                # Change to "True" to start the game after the Map is created (defaults to False when Blender is running)
delete_shop_and_build = True    # Change to "True" to delete the raw city files after the .AR file has been created

# Map Attributes
set_bridges = True              #* Set "Bridges" to "False" when creating your own map to avoid crashes. Bridges should be implemented last
set_props = True                # Change to "True" if you want PROPS
set_bridges = True              # Change to "True" if you want BRIDGES
set_facades = True              # Change to "True" if you want FACADES
set_physics = True              # Change to "True" if you want PHYSICS (custom)
set_animations = True           # Change to "True" if you want ANIMATIONS (plane and eltrain)
set_texture_sheet = True        # Change to "True" if you want a TEXTURE SHEET (this will enable Custom Textures and modified existing Textures)
set_music = True                # TODO: Update Open1560 (Change to "True" if you want MUSIC during gameplay)

# Minimap
set_minimap = False             # Initially set to "False" to save performance. Change to "True" if you want a MINIMAP (defaults to "False" when Blender is running)                              
minimap_outline_color = None    # Change the outline of the minimap shapes to any color (e.g. "Red"), if you don't want any color, set to "None"

# AI
set_ai_streets = True           # Change to "True" if you want AI streets
set_reverse_ai_streets = False  # Change to "True" if you want to add reverse AI streets
set_lars_race_maker = False     # Change to "True" if you want to create "Lars Race Maker" 
visualize_ai_paths = False      # Change to "True" if you want to visualize the AI streets in the Blender 

# Car Start Position in Cruise (if no polygon has the option "base = True")
cruise_start_position = (40.0, 30.0, -40.0)

# Texture Randomization
randomize_textures = False      # Change to "True" if you want to randomize all textures in your Map
random_textures = [Texture.WATER, Texture.GRASS, Texture.WOOD, Texture.ROAD_3_LANE, Texture.BRICKS_GREY, Texture.CHECKPOINT]

# Other
round_vector_values = True
disable_progress_bar = False    # Change to "True" if you want to disable the progress bar (this will display Errors and Warnings again)
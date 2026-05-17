from src.constants.textures import Texture
from src.constants.file_formats import Axis


# Map Name
MAP_NAME = "My First City"                      # Can be multiple words --- name of the Map in the Race Locale Menu
MAP_FILENAME = "FirstCity"                     # One word (no spaces)  --- name of the .AR file and the folder in the SHOP folder
   
# Play Game + Delete Shop
play_game = True                # Set True to start the game after the Map is created (defaults to False when Blender is running)
delete_shop = True              # Set True to delete the raw city files after the .AR file has been created

# Map Attributes
set_bridges = True              #! Set True to include BRIDGES — implement last, can cause crashes if added too early
set_props = True                # Set True to include PROPS
set_facades = True              # Set True to include FACADES
set_physics = True              # Set True to apply custom PHYSICS
set_animations = True           # Set True to include ANIMATIONS (plane and eltrain)
set_lighting = True             # Set True to apply custom LIGHTING overrides

# Player Data
set_player_data = True          # Set True to write player .sav + .cfg + players.dir into MidtownMadness/dev/players/

# Races & AI
set_races = True                # Set True to create all race files (player/opponent waypoints, AIMAP, CINFO entries)
set_cops_and_robbers = True     # Set True to create the cops-and-robbers waypoints file
set_ai_streets = True           # Set True to include AI streets
set_reverse_ai_streets = False  # Set True to include reverse AI streets
set_lars_race_maker = False     # Set True to generate Lars Race Maker

# Minimap
set_minimap = False             # Set True to generate a MINIMAP (slow; disabled automatically when Blender is running)
minimap_outline_color = None    # Set to a color name (e.g. "Red") to outline minimap shapes; None for no outline

# Misc
set_texture_sheet = True        # Set True to build a TEXTURE SHEET (enables custom and modified textures)
set_music = True                # TODO: Update Open1560 — Set True to enable MUSIC during gameplay

# Car Start Position in Cruise (if no polygon has the option "base = True")
set_cruise_start = False        # Set True to generate cruise_start.road and add its entry in the .map file
cruise_start_position = (0.0, 10.0, 0.0)

# Texture Randomization
randomize_textures = False      # Set True to randomize all textures in your Map
random_textures = [Texture.WATER, Texture.GRASS, Texture.WOOD, Texture.ROAD_3_LANE, Texture.BRICKS_GREY, Texture.CHECKPOINT]

# Other
disable_progress_bar = True     # Set True to show raw console output (disables the progress bar)

default_separator = Axis.Longest
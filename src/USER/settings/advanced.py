from src.constants.city import City

# Command line arguments
no_ui = False                   # Change to "True" if you want skip the game's menu and go straight into Cruise mode
no_ui_type = "cruise"           # Other race types are currently not supported by the game in custom maps
no_ai = False                   # Change to "True" if you want to disable the AI and AI paths

less_logs = False               # Change to "True" if you want to hide most logs. This may prevent frame rate drops if the game is printing tons of errors or warnings
more_logs = False               # Change to "True" if you want additional logs and open a logging console when running the game

# Portals
lower_portals = False           # Change to "True" if you want to lower the portals. This may be useful when you're "truncating" the cells file, and have cells below y = 0. This however may lead to issues with the AI
empty_portals = False           # Change to "True" if you want to create an empty portals file. This may be useful if you're testing a city with tens of thousands of polygons, which the portals file cannot handle. Nevertheless, we can still test the city by creating an empty portals file (this will compromise game visiblity)

# DLP
set_dlp = False                 # Change to "True" if you want to create a DLP file 

# Other
fix_faulty_quads = False        # Change to "True" if you want to fix faulty quads (e.g. self-intersecting quads)
deduplicate_bound_vertices = True  # Change to "False" to disable vertex sharing in BND output (useful for debugging per-polygon index ranges)
set_hitid_grid = True           # Change to "False" to build HITID without the spatial grid (game tests all polygons — slow but useful for debugging)

# City inheritance — set inherit_city to a City constant to enable.
# Each flag below controls whether that specific file is copied from the original.
# inherit_city = City.RaceCity2nd  # set to None to disable
# inherit_city = City.Chicago
inherit_city = None

inherit_hitid   = False    # copy original HITID.BND        instead of generating
inherit_cells   = False    # copy original .CELLS           instead of generating
inherit_portals = False    # copy original .PTL             instead of generating
inherit_bounds  = False    # copy original per-cell BND files instead of generating
inherit_bms     = False    # copy original BMS mesh files   instead of generating

# Granular city file inheritance (each is one specific file type)
inherit_ai       = False   # .BAI — AI vehicle / pedestrian paths
inherit_props    = False   # .BNG — props & bangers (buildings, bridges, objects)
inherit_facades  = False   # .FCD — building facade geometry
inherit_gizmo    = False   # .GIZMO — bridges placement data
inherit_extrema  = False   # .EXT — city extrema (height bounds per cell)

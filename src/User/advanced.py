no_ui = False                   # Change to "True" if you want skip the game's menu and go straight into Cruise mode
no_ui_type = "cruise"           # Other race types are currently not supported by the game in custom maps
no_ai = False                   # Change to "True" if you want to disable the AI and AI paths

less_logs = False               # Change to "True" if you want to hide most logs. This may prevent frame rate drops if the game is printing tons of errors or warnings
more_logs = False               # Change to "True" if you want additional logs and open a logging console when running the game

lower_portals = False           # Change to "True" if you want to lower the portals. This may be useful when you're "truncating" the cells file, and have cells below y = 0. This however may lead to issues with the AI
empty_portals = False           # Change to "True" if you want to create an empty portals file. This may be useful if you're testing a city with tens of thousands of polygons, which the portals file cannot handle. Nevertheless, we can still test the city by creating an empty portals file (this will compromise game visiblity)
truncate_cells = False			# Change to "True" if you want to truncate the characters in the cells file. This may be useful for testing large cities. A maximum of 254 characters is allowed per row in the cells file (~80 polygons). To avoid crashing the game, truncate any charachters past 254 (may compromise game visibility - lowering portals may mitigate this issue)

fix_faulty_quads = False        # Change to "True" if you want to fix faulty quads (e.g. self-intersecting quads)

set_dlp = False                 # Change to "True" if you want to create a DLP file 

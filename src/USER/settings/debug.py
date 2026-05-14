# Editor Debugging
debug_props = False             # Change to "True" if you want a PROPS Debug text file
debug_meshes = False            # Change to "True" if you want MESH Debug text files
debug_bounds = False            # Change to "True" if you want a BOUNDS Debug text file
debug_facades = False           # Change to "True" if you want a FACADES Debug text file
debug_physics = False           # Change to "True" if you want a PHYSICS Debug text file
debug_portals = False           # Change to "True" if you want a PORTALS Debug text file
debug_lighting = False          # Change to "True" if you want a LIGHTING Debug text file
debug_minimap = False           # Change to "True" if you want a HUD Debug JPG file (defaults to "True" when "set_lars_race_maker" is set to "True")
debug_minimap_id = False        # Change to "True" if you want to display the Bound IDs in the HUD Debug JPG file

# File Debugging
# Drop any supported file(s) into:  debug/input/
# Output is written to:             debug/output/run_YYYYMMDD_HHMMSS/
# Supported types: .BNG .BMS .BND .FCD .PTL .DLP .DB .CSV (Lighting) .BAI (AI) ...
# ... .SAV (player save) .DIR (player directory) .CFG (player config) .DAT (race records)
auto_debug = False              # Change to "True" to debug all files found in debug/input/
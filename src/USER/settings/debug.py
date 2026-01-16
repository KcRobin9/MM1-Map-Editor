from src.constants.misc import Folder


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

# File Debugging | The Output Files are written to: "Resources / Debug / ..."
debug_props_file = False
debug_props_file_to_csv = False

debug_facades_file = False
debug_portals_file = False
debug_ai_file = False

debug_meshes_file = False
debug_meshes_folder = False

debug_bounds_file = False
debug_bounds_folder = False

debug_dlp_file = False
debug_dlp_folder = False

# File Input Locations
debug_props_data_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO.BNG"          # Change the input Prop file here
debug_facades_data_file = Folder.RESOURCES_EDITOR / "FACADES" / "CHICAGO.FCD"      # Change the input Facade file here
debug_portals_data_file = Folder.RESOURCES_EDITOR / "PORTALS" / "CHICAGO.PTL"      # Change the input Portal file here
debug_ai_data_file = Folder.RESOURCES_EDITOR / "AI" / "CHICAGO.BAI"                # Change the input AI file here

debug_meshes_data_file = Folder.RESOURCES_EDITOR / "MESHES" / "CULL01_H.BMS"       # Change the input Mesh file here
debug_meshes_data_folder = Folder.RESOURCES_EDITOR / "MESHES" / "MESH FILES"       # Change the input Mesh folder here

debug_bounds_data_file = Folder.RESOURCES_EDITOR / "BOUNDS" / "CHICAGO_HITID.BND"  # Change the input Bound file here
debug_bounds_data_folder = Folder.RESOURCES_EDITOR / "BOUNDS" / "BND FILES"        # Change the input Bound folder here

debug_dlp_data_file = Folder.RESOURCES_EDITOR / "DLP" / "VPFER_L.DLP"              # Change the input DLP file here
debug_dlp_data_folder = Folder.RESOURCES_EDITOR / "DLP" / "DLP FILES"              # Change the input DLP folder here
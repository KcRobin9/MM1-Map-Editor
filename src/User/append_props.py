from src.Constants.misc import Folder


# Append Props
append_props = False            # Change to "True" if you want to append props
append_input_props_file = Folder.EDITOR_RESOURCES / "PROPS" / "CHICAGO.BNG"  
append_output_props_file = Folder.USER_RESOURCES / "PROPS" / "APP_CHICAGO.BNG"  

# Ideally this section should be moved into "main.py" in this folder, but this leads to a circular import error
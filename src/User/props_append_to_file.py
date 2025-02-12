from src.Constants.misc import Folder

from src.Constants.props import Prop
from src.Constants.constants import HUGE
from src.Constants.races import RaceMode
from src.Constants.vehicles import PlayerCar


# Append Props
append_props = False            # Change to "True" if you want to append props
append_input_props_file = Folder.EDITOR_RESOURCES / "PROPS" / "CHICAGO.BNG"  
append_output_props_file = Folder.USER_RESOURCES / "PROPS" / "APP_CHICAGO.BNG"  

# Put the Props that should be Appended to an existing BNG file here
app_panoz_gtr = {
    'offset': (5, 2, 5),
    'end': (999, 2, 999),
    'name': PlayerCar.PANOZ_GTR_1
}

props_to_append = [app_panoz_gtr]

# Ideally this section should be moved into "main.py" in this folder, but this leads to a circular import error
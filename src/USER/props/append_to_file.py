from src.constants.misc import Folder
from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.constants import HUGE
from src.constants.modes import NetworkMode, RaceMode


# Append Props
append_props = False            # Change to "True" if you want to append props
append_input_props_file = Folder.EDITOR_RESOURCES / "PROPS" / "CHICAGO.BNG"  
append_output_props_file = Folder.USER_RESOURCES / "PROPS" / "APP_CHICAGO.BNG"  

# Put the Props that should be Appended to an existing BNG file here
app_trailer = {
    'offset': (5, 2, 5),
    'end': (999, 2, 999),
    'name': Prop.TRAILER
}

props_to_append = [app_trailer]
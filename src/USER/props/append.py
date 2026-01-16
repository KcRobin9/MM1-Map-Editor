from src.constants.misc import Folder
from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.constants import HUGE
from src.constants.file_formats import Axis
from src.constants.modes import NetworkMode, RaceMode


# Append Props
append_props = False            # Change to "True" if you want to append props
append_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO_INPUT.BNG"  
append_output_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO_APPENDED.BNG"  

# Put the Props that should be Appended to an existing BNG file here
trailer_set = {
    "offset": (5, 2, 5),
    "end": (999, 2, 999),
    "name": Prop.TRAILER
}

gigas_barricade = {
    "offset": (154.5, 0.1, 918),
    "end": (139, 0.2, 929),
    "name": Prop.BARRICADE,
    "separator": Axis.X
}

props_to_append = [trailer_set, gigas_barricade]
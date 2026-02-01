from src.constants.misc import Folder
from src.constants.props import Prop


# Configuration
subtract_props = False           # Change to "True" if you want to subtract props
subtract_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO_INPUT.BNG"
subtract_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_SUB.BNG"

subtract_tolerance = 0.25
subtract_require_confirmation = True


# Exact match rules
frosty_trailer = {
    "name": Prop.TRAILER,
    "id": 5591,
}

parked_car = {
    "name": Prop.TRAILER,
    "offset": (150.5, 0, -220.3),
}

barricade_line = {
    "name": Prop.BARRICADE,
    "offset": (322, 0, 387),
    "end": (322, 0, 317),
    "separator": 4,
}

props_to_subtract = [frosty_trailer, parked_car, barricade_line]


# Range rules
barricades_by_id = {
    "name": Prop.BARRICADE,
    "ids": [120, 121, 130],
}

props_in_area = {
    "offset_min": (300, 0, 300),
    "offset_max": (350, 10, 400),
}

trailers_range = {
    "name": Prop.TRAILER,
    "id_min": 5500,
    "id_max": 5600,
}

ranges_to_subtract = [barricades_by_id, props_in_area, trailers_range]
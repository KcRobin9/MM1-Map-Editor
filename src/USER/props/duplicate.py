from src.constants.misc import Folder
from src.constants.props import Prop


# Configuration
duplicate_props = False         # Change to "True" if you want to duplicate props
duplicate_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO_INPUT.BNG"
duplicate_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_DUPLICATED.BNG"

duplicate_tolerance = 0.25


# Duplicate rules - each rule has a filter (to match props) and transforms (to position the copies)
# Filter keys: id, ids, id_min, id_max, name, offset, face, offset_min, offset_max, face_min, face_max, end, separator
# Transform keys: translate, set_offset, set_offset_x/y/z, add_offset_x/y/z, set_face, set_name, etc.

# Example: Duplicate a trailer and move the copy
duplicate_trailer = {
    "name": Prop.TRAILER,
    "id": 5591,
    "translate": (50, 0, 0),
}

# Example: Duplicate all trees in an area and mirror them
mirror_trees = {
    "name": Prop.TREE_SLIM,
    "offset_min": (0, 0, 0),
    "offset_max": (100, 50, 100),
    "mirror_x": True,
    "mirror_x_pivot": 50.0,
}

# Example: Duplicate props and change their type
duplicate_and_change = {
    "name": Prop.BARRICADE,
    "id_min": 100,
    "id_max": 150,
    "translate": (0, 0, 100),
    "set_name": Prop.CONE,
}

# Example: Duplicate a line of props
duplicate_line = {
    "name": Prop.BARRICADE,
    "offset": (100, 0, 100),
    "end": (100, 0, 200),
    "separator": 10,
    "translate": (50, 0, 0),
}

# Put the duplicate rules here
props_to_duplicate = [
    # duplicate_trailer,
    # mirror_trees,
    # duplicate_and_change,
    # duplicate_line,
]

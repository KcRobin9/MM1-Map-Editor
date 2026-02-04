
from src.constants.misc import Folder
from src.constants.props import Prop


# Configuration
edit_props = False              # Change to "True" if you want to edit props
edit_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO_INPUT.BNG"
edit_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_EDITED.BNG"

edit_tolerance = 0.25
edit_require_confirmation = True


# ==============================================================================
# Edit Rules
# ==============================================================================
# Each rule has two parts:
#   1. FILTER - which props to match (you can use any combination)
#   2. TRANSFORM - what changes to apply
#
# FILTERS (use any combination):
#   name            - Match by prop type:        "name": Prop.TRAILER
#   id              - Match single prop index:   "id": 5591
#   ids             - Match multiple indices:    "ids": [100, 101, 102]
#   id_min, id_max  - Match index range:         "id_min": 100, "id_max": 200
#   offset          - Match by position:         "offset": (150.5, 0, -220.3)
#   offset_min, offset_max - Match in area:      "offset_min": (0,0,0), "offset_max": (100,50,100)
#   end, separator  - Match line of props:       "offset": (0,0,0), "end": (100,0,0), "separator": 10
#
# TRANSFORMS:
#   translate          - Move by delta:          "translate": (10, 0, 5)
#   set_offset         - Set absolute position:  "set_offset": (150, 0, 150)
#   set_offset_x/y/z   - Set single axis:        "set_offset_y": 0.0
#   add_offset_x/y/z   - Add to single axis:     "add_offset_y": 2.0
#   set_face           - Set facing direction:   "set_face": (1.0, 0.0, 0.0)
#   set_name           - Change prop type:       "set_name": Prop.TREE_WIDE
#   mirror_x           - Mirror across X axis:   "mirror_x": True, "mirror_x_pivot": 50.0
#   mirror_z           - Mirror across Z axis:   "mirror_z": True, "mirror_z_pivot": 0.0
# ==============================================================================


# Example: Move a specific trailer by ID
move_trailer_by_id = {
    "name": Prop.TRAILER,
    "id": 5591,
    "translate": (10, 0, 5),
}

# Example: Move ALL trailers (no id filter)
move_all_trailers = {
    "name": Prop.TRAILER,
    "translate": (10, 0, 5),
}

# Example: Raise all props in an area by 2 units
raise_props_in_area = {
    "offset_min": (100, 0, 100),
    "offset_max": (200, 50, 200),
    "add_offset_y": 2.0,
}

# Example: Set all trees to ground level
flatten_trees = {
    "name": Prop.TREE_SLIM,
    "set_offset_y": 0.0,
}

# Example: Rotate face of barricade at specific location
rotate_barricade = {
    "name": Prop.BARRICADE,
    "offset": (322, 0, 387),
    "set_face": (1.0, 0.0, 0.0),
}

# Example: Mirror props across X axis
mirror_props = {
    "name": Prop.TREE_SLIM,
    "id_min": 100,
    "id_max": 150,
    "mirror_x": True,
    "mirror_x_pivot": 0.0,
}

# Example: Edit a line of props (using end/separator)
edit_prop_line = {
    "name": Prop.BARRICADE,
    "offset": (154.5, 0.1, 918),
    "end": (139, 0.2, 929),
    "separator": 4,
    "set_offset_y": 0.5,
}


# Put the edit rules here (uncomment the ones you want to use)
props_to_edit = [
    # move_trailer_by_id,
    # move_all_trailers,
    # raise_props_in_area,
    # flatten_trees,
    # rotate_barricade,
    # mirror_props,
    # edit_prop_line,
]
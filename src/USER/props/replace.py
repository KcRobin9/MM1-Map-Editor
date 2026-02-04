from src.constants.misc import Folder
from src.constants.props import Prop


# Configuration
replace_props = False           # Change to "True" if you want to replace props
replace_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO_INPUT.BNG"
replace_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_REPLACED.BNG"

replace_tolerance = 0.25
replace_require_confirmation = True


# ==============================================================================
# Replace Rules
# ==============================================================================
# Each rule has:
#   1. FILTER - which props to match (use any combination, or just one)
#   2. replace_with - the new prop type
#
# FILTERS (use any combination - they work independently!):
#   name            - Match by prop type:        "name": Prop.TRAILER
#   id              - Match single prop index:   "id": 5591
#   ids             - Match multiple indices:    "ids": [100, 101, 102]
#   id_min, id_max  - Match index range:         "id_min": 100, "id_max": 200
#   offset          - Match by position:         "offset": (150.5, 0, -220.3)
#   offset_min, offset_max - Match in area:      "offset_min": (0,0,0), "offset_max": (100,50,100)
# ==============================================================================


# Example: Replace ALL slim trees with wide trees (just "name" filter)
replace_all_slim_trees = {
    "name": Prop.TREE_SLIM,
    "replace_with": Prop.TREE_WIDE,
}

# Example: Replace a specific prop by ID only (just "id" filter)
replace_by_id_only = {
    "id": 5591,
    "replace_with": Prop.SAILBOAT,
}

# Example: Replace all props in a specific area (just area filter)
replace_props_in_area = {
    "offset_min": (100, 0, 100),
    "offset_max": (200, 50, 200),
    "replace_with": Prop.CONE,
}

# Example: Replace barricades in a specific ID range (combined filters)
replace_by_id_range = {
    "name": Prop.BARRICADE,
    "id_min": 100,
    "id_max": 150,
    "replace_with": Prop.BENCH,
}

# Example: Replace a specific trailer at a specific location
replace_trailer_at_position = {
    "name": Prop.TRAILER,
    "offset": (150.5, 0, -220.3),
    "replace_with": Prop.BARRICADE,
}


# Put the replace rules here (uncomment the ones you want to use)
props_to_replace = [
    # replace_all_slim_trees,
    # replace_by_id_only,
    # replace_props_in_area,
    # replace_by_id_range,
    # replace_trailer_at_position,
]
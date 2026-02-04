from src.file_formats.props.props import Bangers
from src.file_formats.props.editor import BangerEditor, edit_and_copy_bangerdata_to_shop
from src.file_formats.props.subtract import subtract_props_from_file
from src.file_formats.props.edit import edit_props_in_file, PropTransform, build_transform
from src.file_formats.props.replace import replace_props_in_file
from src.file_formats.props.matching import matches_exact_filter, matches_range_filter
from src.file_formats.props.expansion import expand_rules
from src.file_formats.props.batch import (
    batch_translate,
    batch_set_name,
    batch_set_height,
    batch_mirror,
    batch_transform,
    create_filter_by_name,
    create_filter_by_id_range,
    create_filter_by_area,
    create_filter_combined,
    duplicate_and_translate,
    find_props_by_proximity,
    align_props_to_grid,
    randomize_face_rotation,
    sort_props_by_distance,
    get_prop_statistics,
    print_statistics
)
from src.file_formats.props.copy import (
    copy_prop,
    copy_and_transform,
    duplicate_props_in_file,
    clone_props_with_offset,
    create_prop_grid,
    create_prop_line,
    create_prop_circle
)

__all__ = [
    # Core
    "Bangers",
    "BangerEditor",
    "edit_and_copy_bangerdata_to_shop",
    
    # Operations
    "subtract_props_from_file",
    "edit_props_in_file",
    "replace_props_in_file",
    "duplicate_props_in_file",
    
    # Transforms
    "PropTransform",
    "build_transform",
    
    # Matching
    "matches_exact_filter",
    "matches_range_filter",
    "expand_rules",
    
    # Batch operations
    "batch_translate",
    "batch_set_name",
    "batch_set_height",
    "batch_mirror",
    "batch_transform",
    
    # Filters
    "create_filter_by_name",
    "create_filter_by_id_range",
    "create_filter_by_area",
    "create_filter_combined",
    
    # Copy/Clone utilities
    "copy_prop",
    "copy_and_transform",
    "clone_props_with_offset",
    "create_prop_grid",
    "create_prop_line",
    "create_prop_circle",
    
    # General utilities
    "duplicate_and_translate",
    "find_props_by_proximity",
    "align_props_to_grid",
    "randomize_face_rotation",
    "sort_props_by_distance",
    "get_prop_statistics",
    "print_statistics",
]

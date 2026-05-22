"""Car Editor package — load / edit / export MM1 car BMS in Blender + pack to AR.

Split from the former single car_editor.py module into focused submodules
(constants, common, paint, wheels, physics, trailer, lights, packing, validate,
import_helpers, operators). The public surface below is re-exported so existing
imports `from ...operators.car_editor import X` keep working unchanged.
"""
from src.integrations.blender.operators.car_editor.constants import (
    _CAR_LIGHT_DEFS, _CAR_LIGHT_TAGS, _CAR_TAG,
)
from src.integrations.blender.operators.car_editor.common import (
    get_car_body, get_car_objects, is_car_obj, update_ce_face_texture, update_ce_face_uv,
)
from src.integrations.blender.operators.car_editor.paint import (
    _find_paint_variants_cached, _variant_color_name,
)
from src.integrations.blender.operators.car_editor.operators import CAR_EDITOR_CLASSES


# Public scene/query helpers (used by the sidebar panel)

# Public constants (used by the panel)

# Operator classes + the registration list (used by inits.py)

__all__ = [
    "is_car_obj", "get_car_objects", "get_car_body",
    "update_ce_face_texture", "update_ce_face_uv",
    "_find_paint_variants_cached", "_variant_color_name",
    "_CAR_TAG", "_CAR_LIGHT_DEFS", "_CAR_LIGHT_TAGS",
    "CAR_EDITOR_CLASSES",
]

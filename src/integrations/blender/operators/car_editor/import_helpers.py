"""Car Editor — import_helpers module (split from the former car_editor.py monolith)."""
import re
import mathutils

from src.integrations.blender.operators.car_editor.common import (
    _get_or_create_collection, get_car_body,
)
from src.integrations.blender.operators.car_editor.constants import _CAR_COLLECTION, _CAR_TAG


# ── Import helpers ────────────────────────────────────────────────────────────

def _tag_as_body(obj, car_name: str) -> None:
    obj[_CAR_TAG]         = "body"
    obj["mm_car_name"]    = car_name
    obj["mm_car_folder"]  = ""
    obj["mm_body_file"]   = "BODY_H.BMS"
    col = _get_or_create_collection(_CAR_COLLECTION)
    if obj.name not in col.objects:
        col.objects.link(obj)


def _tag_as_wheel(obj, idx: int, car_name: str) -> None:
    obj[_CAR_TAG] = f"wheel_{idx}"
    body = get_car_body()
    if body:
        obj.parent = body
        obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    col = _get_or_create_collection(_CAR_COLLECTION)
    if obj.name not in col.objects:
        col.objects.link(obj)


def _derive_car_name(scene) -> str:
    display = (scene.ce_car_display_name or "").strip()
    return ("VP" + display.upper().replace(" ", "")) if display else ""


def _clean_mat_name(name: str) -> str:
    """Strip path/extension noise from an imported material name."""
    # Remove numeric duplicate suffixes (.001, .002 …)
    name = re.sub(r'\.\d{3}$', '', name)
    # Remove trailing _Mat / _Material / _mat suffixes
    name = re.sub(r'(?i)[_\s]?mat(erial)?$', '', name)
    # Keep only ASCII uppercase alphanum + underscore
    name = re.sub(r'[^A-Za-z0-9_]', '_', name).upper()
    name = re.sub(r'_+', '_', name).strip('_')

    # Generic DCC / importer placeholder names that have no game equivalent
    _GENERIC = {
        "MAT", "MAT_BODY", "MAT_BODY_1", "MAT_WHEELS", "MAT_GLASS",
        "MATERIAL", "DEFAULT", "DEFAULTMAT", "LAMBERT", "LAMBERT1",
        "INITIALSHADINGGROUP", "STANDARDSURFACE", "BLINN", "PHONG",
        "DIFFUSE", "UNTITLED", "NONE", "NULL",
    }
    if name in _GENERIC or name.startswith("MAT_") or name.startswith("LAMBERT"):
        return "CARBOTTOM"
    return name or "CARBOTTOM"

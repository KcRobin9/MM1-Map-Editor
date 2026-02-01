from typing import Dict, List, Optional, Set

from src.core.vector.vector_3 import Vector3
from src.core.geometry.bounds import is_within_tolerance, is_within_bounds


def matches_exact_filter(
    prop,
    rule: Dict,
    tolerance: float,
    index: Optional[int] = None
) -> bool:
    if not _matches_id(rule, index):
        return False
    
    if not _matches_name(prop, rule):
        return False
    
    if "offset" in rule:
        target = Vector3(*rule["offset"])
        if not is_within_tolerance(prop.offset, target, tolerance):
            return False
    
    if "face" in rule:
        target = Vector3(*rule["face"])
        if not is_within_tolerance(prop.face, target, tolerance):
            return False
    
    return True


def matches_range_filter(
    prop,
    rule: Dict,
    index: Optional[int] = None
) -> bool:
    if not _matches_id(rule, index):
        return False
    
    if not _matches_id_list(rule, index):
        return False
    
    if not _matches_id_range(rule, index):
        return False
    
    if not _matches_name(prop, rule):
        return False
    
    if "offset_min" in rule and "offset_max" in rule:
        if not is_within_bounds(prop.offset, rule["offset_min"], rule["offset_max"]):
            return False
    
    if "face_min" in rule and "face_max" in rule:
        if not is_within_bounds(prop.face, rule["face_min"], rule["face_max"]):
            return False
    
    return True


def _matches_id(rule: Dict, index: Optional[int]) -> bool:
    if index is None or "id" not in rule:
        return True
    
    try:
        return int(rule["id"]) == int(index)
    except (ValueError, TypeError):
        return True


def _matches_id_list(rule: Dict, index: Optional[int]) -> bool:
    if index is None or "ids" not in rule:
        return True
    
    try:
        ids: Set[int] = {int(x) for x in rule["ids"]}
        return int(index) in ids
    except (ValueError, TypeError):
        return True


def _matches_id_range(rule: Dict, index: Optional[int]) -> bool:
    if index is None:
        return True
    
    if "id_min" not in rule or "id_max" not in rule:
        return True
    
    try:
        lo = int(rule["id_min"])
        hi = int(rule["id_max"])
        return min(lo, hi) <= int(index) <= max(lo, hi)
    except (ValueError, TypeError):
        return True


def _matches_name(prop, rule: Dict) -> bool:
    if "name" not in rule:
        return True
    
    prop_name = prop.name.rstrip("\x00")
    return prop_name == rule["name"]
import math
from typing import Dict, List


def expand_rules(rules: List[Dict]) -> List[Dict]:
    expanded = []
    for rule in rules or []:
        expanded.extend(expand_end_separator(rule))
    return expanded


def expand_end_separator(rule: Dict) -> List[Dict]:
    if "end" not in rule or "separator" not in rule:
        return [rule]

    offset = rule["offset"]
    end = rule["end"]
    separator = float(rule["separator"])
    
    ox, oy, oz = offset
    ex, ey, ez = end
    
    dx, dy, dz = ex - ox, ey - oy, ez - oz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    
    if length <= 0.0 or separator <= 0.0:
        return [_build_rule(offset, rule)]
    
    nx, ny, nz = dx / length, dy / length, dz / length
    num_props = int(length / separator)
    
    expanded = []
    for i in range(num_props):
        distance = i * separator
        position = (
            ox + nx * distance,
            oy + ny * distance,
            oz + nz * distance
        )
        expanded.append(_build_rule(position, rule))
    
    return expanded


def _build_rule(offset: tuple, source: Dict) -> Dict:
    rule = {"offset": offset}
    
    if "name" in source:
        rule["name"] = source["name"]
    
    if "face" in source:
        rule["face"] = source["face"]
    
    return rule
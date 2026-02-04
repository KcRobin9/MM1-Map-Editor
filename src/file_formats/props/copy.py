from pathlib import Path
from typing import List, Dict, Tuple, Set, Callable, Optional

from src.core.vector.vector_3 import Vector3
from src.file_formats.props.props import Bangers
from src.file_formats.props.matching import matches_exact_filter, matches_range_filter
from src.file_formats.props.expansion import expand_rules
from src.file_formats.props.edit import build_transform
from src.ui.console import yellow, green, cyan


def copy_prop(prop: Bangers) -> Bangers:
    return Bangers(
        prop.room,
        prop.flags,
        Vector3(prop.offset.x, prop.offset.y, prop.offset.z),
        Vector3(prop.face.x, prop.face.y, prop.face.z),
        prop.name
    )


def copy_and_transform(prop: Bangers, transform: Callable[[Bangers], Bangers]) -> Bangers:
    new_prop = copy_prop(prop)
    return transform(new_prop)


def duplicate_props_in_file(
    input_file: Path,
    output_file: Path,
    duplicate_rules: List[Dict],
    tolerance: float = 0.25
) -> None:
    with open(input_file, "rb") as f:
        props = Bangers.read_all(f)
    
    if not props:
        print(yellow("Duplicate: Input file has 0 props."))
        return
    
    new_props = []
    for rule in duplicate_rules:
        filter_rule = _extract_filter(rule)
        expanded = expand_rules([filter_rule]) if "end" in filter_rule else [filter_rule]
        transform = build_transform(rule)
        
        for index, prop in enumerate(props):
            for exp_filter in expanded:
                if _matches_filter(prop, exp_filter, tolerance, index):
                    duplicated = copy_and_transform(prop, transform)
                    new_props.append(duplicated)
                    break
    
    props.extend(new_props)
    Bangers.write_all(output_file, props, debug_props=False)
    
    print(f"{green(f'Duplicate: Created {len(new_props)} new prop(s)')}")
    print(f"Duplicate: Total prop count: {len(props)}")
    print(cyan(f"---output file: {output_file.name}"))


def clone_props_with_offset(
    props: List[Bangers],
    offset: Tuple[float, float, float],
    count: int = 1,
    filter_func: Optional[Callable[[Bangers, int], bool]] = None
) -> List[Bangers]:
    clones = []
    delta = Vector3(*offset)
    
    for i, prop in enumerate(props):
        if filter_func and not filter_func(prop, i):
            continue
        
        for n in range(1, count + 1):
            clone = copy_prop(prop)
            clone.offset = clone.offset + (delta * n)
            clones.append(clone)
    
    return clones


# Maybe delete
#
# def create_prop_grid(
#     template: Bangers,
#     start: Tuple[float, float, float],
#     spacing: Tuple[float, float, float],
#     count: Tuple[int, int, int]
# ) -> List[Bangers]:
#     """Creates a 3D grid of props.
#     Example: create_prop_grid(tree, (0,0,0), (10,0,10), (5,1,5)) creates 25 trees in a 5x5 grid
#     """
#     props = []
#     sx, sy, sz = start
#     dx, dy, dz = spacing
#     cx, cy, cz = count
#     
#     for ix in range(cx):
#         for iy in range(cy):
#             for iz in range(cz):
#                 prop = copy_prop(template)
#                 prop.offset = Vector3(
#                     sx + ix * dx,
#                     sy + iy * dy,
#                     sz + iz * dz
#                 )
#                 props.append(prop)
#     
#     return props


# Maybe keep
# def create_prop_circle(
#     template: Bangers,
#     center: Tuple[float, float, float],
#     radius: float,
#     count: int,
#     face_center: bool = True
# ) -> List[Bangers]:
#     """Creates props arranged in a circle.
#     Example: create_prop_circle(tree, (50,0,50), 30, 12) creates 12 trees in a circle
#     """
#     import math
#     
#     props = []
#     cx, cy, cz = center
#     
#     for i in range(count):
#         angle = 2 * math.pi * i / count
#         prop = copy_prop(template)
#         prop.offset = Vector3(
#             cx + radius * math.cos(angle),
#             cy,
#             cz + radius * math.sin(angle)
#         )
#         
#         if face_center:
#             prop.face = Vector3(cx, cy, cz)
#         
#         props.append(prop)
#     
#     return props


def _extract_filter(rule: Dict) -> Dict:
    filter_keys = {
        "id", "ids", "id_min", "id_max",
        "name", "offset", "face", "end", "separator",
        "offset_min", "offset_max", "face_min", "face_max"
    }
    return {k: v for k, v in rule.items() if k in filter_keys}


def _matches_filter(prop: Bangers, rule: Dict, tolerance: float, index: int) -> bool:
    has_exact = any(k in rule for k in ["id", "offset", "face"])
    has_range = any(k in rule for k in ["ids", "id_min", "id_max", "offset_min", "offset_max"])
    
    if has_exact and matches_exact_filter(prop, rule, tolerance, index):
        return True
    
    if has_range and matches_range_filter(prop, rule, index):
        return True
    
    if "name" in rule and not has_exact and not has_range:
        return prop.name.rstrip("\x00") == rule["name"]
    
    return False
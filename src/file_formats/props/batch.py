from pathlib import Path
from typing import List, Dict, Callable, Optional

from src.core.vector.vector_3 import Vector3
from src.file_formats.props.props import Bangers
from src.file_formats.props.edit import PropTransform
from src.ui.console import green, cyan, yellow


def batch_translate(
    props: List[Bangers],
    filter_func: Callable[[Bangers, int], bool],
    delta: tuple
) -> int:
    count = 0
    for i, prop in enumerate(props):
        if filter_func(prop, i):
            PropTransform.translate(prop, delta)
            count += 1
    return count


def batch_set_name(
    props: List[Bangers],
    filter_func: Callable[[Bangers, int], bool],
    new_name: str
) -> int:
    count = 0
    for i, prop in enumerate(props):
        if filter_func(prop, i):
            PropTransform.set_name(prop, new_name)
            count += 1
    return count


def batch_set_height(
    props: List[Bangers],
    filter_func: Callable[[Bangers, int], bool],
    height: float
) -> int:
    count = 0
    for i, prop in enumerate(props):
        if filter_func(prop, i):
            PropTransform.set_offset_y(prop, height)
            count += 1
    return count


def batch_mirror(
    props: List[Bangers],
    filter_func: Callable[[Bangers, int], bool],
    axis: str,
    pivot: float = 0.0
) -> int:
    count = 0
    mirror_func = PropTransform.mirror_x if axis.lower() == 'x' else PropTransform.mirror_z
    for i, prop in enumerate(props):
        if filter_func(prop, i):
            mirror_func(prop, pivot)
            count += 1
    return count


def batch_transform(
    props: List[Bangers],
    filter_func: Callable[[Bangers, int], bool],
    transform_func: Callable[[Bangers], Bangers]
) -> int:
    count = 0
    for i, prop in enumerate(props):
        if filter_func(prop, i):
            transform_func(prop)
            count += 1
    return count


def create_filter_by_name(name: str) -> Callable[[Bangers, int], bool]:
    def filter_func(prop: Bangers, index: int) -> bool:
        return prop.name.rstrip('\x00') == name
    return filter_func


def create_filter_by_id_range(min_id: int, max_id: int) -> Callable[[Bangers, int], bool]:
    def filter_func(prop: Bangers, index: int) -> bool:
        return min_id <= index <= max_id
    return filter_func


def create_filter_by_area(
    min_bounds: tuple,
    max_bounds: tuple
) -> Callable[[Bangers, int], bool]:
    from src.core.geometry.bounds import is_within_bounds
    
    def filter_func(prop: Bangers, index: int) -> bool:
        return is_within_bounds(prop.offset, min_bounds, max_bounds)
    return filter_func


def create_filter_combined(*filters: Callable[[Bangers, int], bool]) -> Callable[[Bangers, int], bool]:
    def combined(prop: Bangers, index: int) -> bool:
        return all(f(prop, index) for f in filters)
    return combined


def duplicate_and_translate(
    props: List[Bangers],
    filter_func: Callable[[Bangers, int], bool],
    delta: tuple
) -> List[Bangers]:
    duplicates = []
    for i, prop in enumerate(props):
        if filter_func(prop, i):
            new_prop = Bangers(
                prop.room,
                prop.flags,
                Vector3(
                    prop.offset.x + delta[0],
                    prop.offset.y + delta[1],
                    prop.offset.z + delta[2]
                ),
                Vector3(prop.face.x, prop.face.y, prop.face.z),
                prop.name
            )
            duplicates.append(new_prop)
    return duplicates


def find_props_by_proximity(
    props: List[Bangers],
    center: tuple,
    radius: float
) -> List[tuple]:
    center_vec = Vector3(*center)
    matches = []
    for i, prop in enumerate(props):
        dist = prop.offset.Dist(center_vec)
        if dist <= radius:
            matches.append((i, prop, dist))
    return sorted(matches, key=lambda x: x[2])


def sort_props_by_distance(props: List[Bangers], origin: tuple = (0, 0, 0)) -> List[Bangers]:
    origin_vec = Vector3(*origin)
    return sorted(props, key=lambda p: p.offset.Dist(origin_vec))


def get_prop_statistics(props: List[Bangers]) -> Dict:
    if not props:
        return {"count": 0}
    
    names = {}
    x_vals, y_vals, z_vals = [], [], []
    
    for prop in props:
        name = prop.name.rstrip('\x00')
        names[name] = names.get(name, 0) + 1
        x_vals.append(prop.offset.x)
        y_vals.append(prop.offset.y)
        z_vals.append(prop.offset.z)
    
    return {
        "count": len(props),
        "unique_names": len(names),
        "name_counts": names,
        "bounds": {
            "min": (min(x_vals), min(y_vals), min(z_vals)),
            "max": (max(x_vals), max(y_vals), max(z_vals))
        },
        "center": (
            sum(x_vals) / len(x_vals),
            sum(y_vals) / len(y_vals),
            sum(z_vals) / len(z_vals)
        )
    }


def print_statistics(props: List[Bangers]) -> None:
    stats = get_prop_statistics(props)
    
    print(f"\n{cyan('Prop Statistics:')}")
    print(f"  Total count: {stats['count']}")
    print(f"  Unique types: {stats['unique_names']}")
    
    if stats['count'] > 0:
        bounds = stats['bounds']
        center = stats['center']
        print(f"  Bounds min: ({bounds['min'][0]:.2f}, {bounds['min'][1]:.2f}, {bounds['min'][2]:.2f})")
        print(f"  Bounds max: ({bounds['max'][0]:.2f}, {bounds['max'][1]:.2f}, {bounds['max'][2]:.2f})")
        print(f"  Center: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
        
        print(f"\n  {cyan('Type breakdown:')}")
        for name, count in sorted(stats['name_counts'].items(), key=lambda x: -x[1]):
            print(f"    {name}: {count}")
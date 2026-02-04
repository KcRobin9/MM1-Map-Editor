from typing import Tuple

from src.core.vector.vector_3 import Vector3


def is_within_tolerance(actual: Vector3, target: Vector3, tolerance: float) -> bool:
    return (
        abs(actual.x - target.x) <= tolerance and
        abs(actual.y - target.y) <= tolerance and
        abs(actual.z - target.z) <= tolerance
    )


def is_within_bounds(
    point: Vector3,
    min_bounds: Tuple[float, float, float],
    max_bounds: Tuple[float, float, float]
) -> bool:
    min_x, min_y, min_z = min_bounds
    max_x, max_y, max_z = max_bounds
    
    lo_x, hi_x = min(min_x, max_x), max(min_x, max_x)
    lo_y, hi_y = min(min_y, max_y), max(min_y, max_y)
    lo_z, hi_z = min(min_z, max_z), max(min_z, max_z)
    
    return (
        lo_x <= point.x <= hi_x and
        lo_y <= point.y <= hi_y and
        lo_z <= point.z <= hi_z
    )


def get_bounds_center(
    min_bounds: Tuple[float, float, float],
    max_bounds: Tuple[float, float, float]
) -> Vector3:
    return Vector3(
        (min_bounds[0] + max_bounds[0]) / 2,
        (min_bounds[1] + max_bounds[1]) / 2,
        (min_bounds[2] + max_bounds[2]) / 2
    )


def get_bounds_size(
    min_bounds: Tuple[float, float, float],
    max_bounds: Tuple[float, float, float]
) -> Vector3:
    return Vector3(
        abs(max_bounds[0] - min_bounds[0]),
        abs(max_bounds[1] - min_bounds[1]),
        abs(max_bounds[2] - min_bounds[2])
    )

from typing import Tuple

from src.core.vector.vector_3 import Vector3


def is_within_tolerance(a: Vector3, b: Vector3, tolerance: float) -> bool:
    return (
        abs(a.x - b.x) <= tolerance and
        abs(a.y - b.y) <= tolerance and
        abs(a.z - b.z) <= tolerance
    )


def is_within_bounds(
    point: Vector3,
    bounds_min: Tuple[float, float, float],
    bounds_max: Tuple[float, float, float]
) -> bool:
    x1, y1, z1 = bounds_min
    x2, y2, z2 = bounds_max
    
    lo_x, hi_x = min(x1, x2), max(x1, x2)
    lo_y, hi_y = min(y1, y2), max(y1, y2)
    lo_z, hi_z = min(z1, z2), max(z1, z2)
    
    return (
        lo_x <= point.x <= hi_x and
        lo_y <= point.y <= hi_y and
        lo_z <= point.z <= hi_z
    )
import struct
import psutil
from typing import Tuple


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def calc_size(fmt: str) -> int:
    return struct.calcsize(fmt)


def calculate_extrema(vertices, coord_indexes = (0, 2)) -> Tuple[float, float, float, float]:
    min_values = [min(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    max_values = [max(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    return min_values + max_values


def is_process_running(process_name: str) -> bool:
    for proc in psutil.process_iter(["name"]):
        if process_name.lower() in proc.info["name"].lower():
            return True
    return False
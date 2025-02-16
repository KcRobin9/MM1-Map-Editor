from typing import Tuple


def calculate_extrema(vertices, coord_indexes = (0, 2)) -> Tuple[float, float, float, float]:
    min_values = [min(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    max_values = [max(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    return min_values + max_values
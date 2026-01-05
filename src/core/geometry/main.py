from typing import List, Tuple, Sequence

from src.core.vector.vector_3 import Vector3


def calculate_center_tuples(vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    return (sum((Vector3.from_tuple(vertex) for vertex in vertices), Vector3(0, 0, 0)) / len(vertices)).to_tuple()


def sort_coordinates(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    max_x_coord = max(vertex_coordinates, key = lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key = lambda coord: coord[0])
    
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]


def calc_center_coords(points: Sequence[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    if not points:
        raise ValueError("Empty sequence of points")
    xs, ys, zs = zip(*points)
    n = len(points)
    return sum(xs) / n, sum(ys) / n, sum(zs) / n


def calc_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def calculate_extrema(vertices, coord_indexes = (0, 2)) -> Tuple[float, float, float, float]:
    min_values = [min(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    max_values = [max(point[index] for polygon in vertices for point in polygon) for index in coord_indexes]
    return min_values + max_values


def transform_coordinate_system(vertex: Vector3, blender_to_game: bool = False, game_to_blender: bool = False) -> Tuple[float, float, float]:
    if blender_to_game and game_to_blender:
        raise ValueError("\nBoth transformation modes cannot be 'True' at the same time.\n")
 
    elif blender_to_game:
        x, y, z = vertex.x, vertex.z, -vertex.y
        
    elif game_to_blender:
        x, y, z = vertex.x, -vertex.z, vertex.y
        
    else:
        raise ValueError("\nOne of the transformation modes must be 'True'.\n")
    
    return x, y, z
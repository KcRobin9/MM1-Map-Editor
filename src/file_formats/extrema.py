from pathlib import Path
from typing import List

from src.Vector.vector_3 import Vector3
from src.Geometry.utils import calculate_extrema


def create_extrema(output_file: Path, polygons: List[Vector3]) -> None:
    min_x, min_z, max_x, max_z = calculate_extrema(polygons)

    with open(output_file, "w") as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")
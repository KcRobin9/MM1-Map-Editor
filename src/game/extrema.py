from typing import List
from pathlib import Path

from core.geometry.main import calculate_extrema

from src.core.vector.vector_3 import Vector3



def create_extrema(output_file: Path, polygons: List[Vector3]) -> None:
    min_x, min_z, max_x, max_z = calculate_extrema(polygons)

    with open(output_file, "w") as f:
        f.write(f"{min_x} {min_z} {max_x} {max_z}")

    print(f"Successfully created extrema file")
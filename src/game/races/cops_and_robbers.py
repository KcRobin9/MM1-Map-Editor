from pathlib import Path
from typing import List, Tuple

from src.game.races.constants import CNR_HEADER
from src.game.waypoints.constants import WAYPOINT_FILLER


def create_cops_and_robbers(output_file: Path, cnr_waypoints: List[Tuple[float, float, float]]) -> None:
    with open(output_file, "w") as f:
        f.write(CNR_HEADER)
        
        for i in range(0, len(cnr_waypoints), 3):
            f.write(", ".join(map(str, cnr_waypoints[i])) + WAYPOINT_FILLER)
            f.write(", ".join(map(str, cnr_waypoints[i + 1])) + WAYPOINT_FILLER)
            f.write(", ".join(map(str, cnr_waypoints[i + 2])) + WAYPOINT_FILLER)
import csv
from pathlib import Path
from typing import List, Optional

from src.game.waypoints.constants import Width, Rotation


def determine_ordinal(n) -> str:
    if 10 <= n % 100 <= 13:
        return f"{n}th"
    return {1: f"{n}st", 2: f"{n}nd", 3: f"{n}rd"}.get(n % 10, f"{n}th")


def write_waypoint_header(f, race_type: str, race_index: int, opp_num: Optional[int] = None) -> None:
    if opp_num is not None:
        header = f"This is your Opponent file for opponent number {opp_num}, in {race_type} race {race_index}\n"
    else:
        header = f"# This is your {determine_ordinal(race_index)} {race_type} race Waypoint file\n"
    f.write(header)


def write_waypoint_coordinates(writer: csv.writer, waypoint: List[float], opp_num: Optional[int] = None) -> None:
    if opp_num is not None:
        row = [*waypoint[:3], Width.MEDIUM, Rotation.AUTO, 0, 0]
    else:
        row = [*waypoint, 0, 0]
    writer.writerow(row)


def write_waypoints(output_file: Path, waypoints: List[List[float]], race_type: str, race_index: int, opp_num: Optional[int] = None) -> None:
    with open(output_file, "w", newline = '') as f:
        write_waypoint_header(f, race_type, race_index, opp_num)

        writer = csv.writer(f, delimiter = ',', lineterminator = ',\n')
        for waypoint in waypoints:
            write_waypoint_coordinates(writer, waypoint, opp_num)
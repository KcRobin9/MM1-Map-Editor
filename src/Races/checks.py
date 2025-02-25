from dataclasses import dataclass

from src.Constants.races import RaceMode
from src.Constants.misc import Threshold


@dataclass
class RaceInfo:
    threshold: int
    name: str


RACE_TYPE_LIMIT = {
    RaceMode.CHECKPOINT: RaceInfo(Threshold.CHECKPOINT_RACE_COUNT, 'Checkpoint'),
    RaceMode.BLITZ: RaceInfo(Threshold.BLITZ_RACE_COUNT, 'Blitz'),
    RaceMode.CIRCUIT: RaceInfo(Threshold.CIRCUIT_RACE_COUNT, 'Circuit')
}


def check_race_count(race_type: str, config) -> None:
    if race_type in RACE_TYPE_LIMIT:
        race_info = RACE_TYPE_LIMIT[race_type]
        if len(config) > race_info.threshold:
            error_message = f"""
            ***ERROR***
            Number of {race_info.name} races cannot be more than {race_info.threshold}
            """
            raise ValueError(error_message)
        

def check_waypoint_count(race_type: str, waypoints) -> None:
    if race_type == RaceMode.BLITZ:
        if len(waypoints) > Threshold.BLITZ_WAYPOINT_COUNT:
            blitz_waypoint_count_error = f"""
            ***ERROR***
            Number of waypoints for Blitz race cannot be more than {Threshold.BLITZ_WAYPOINT_COUNT}
            """
            raise ValueError(blitz_waypoint_count_error)
from typing import List, Dict, TextIO, Union, Optional

from src.game.races.constants import RACE_TYPE_TO_EXTENSION


def write_section(f: TextIO, title: str, data: str) -> None:
    f.write(f"\n{title}\n{data}\n")


def format_police_data(police_data: List[str], num_of_police: int) -> str:
    return "\n".join([str(num_of_police)] + police_data)


def format_opponent_data(opp_cars: Dict[str, List[List[float]]], race_type: str, race_index: int) -> str:
    return "\n".join(
        [f"{opp_car} OPP{opp_index}{race_type}{race_index}{RACE_TYPE_TO_EXTENSION[race_type]}{race_index}" 
        for opp_index, opp_car in enumerate(opp_cars)]
        )


def format_exceptions(exceptions: Optional[List[List[Union[int, float]]]] = None, exceptions_count: Optional[int] = None) -> str:
    if exceptions is None:
        exceptions = []
        
    if exceptions_count is None:
        exceptions_count = len(exceptions)
        
    formatted_exceptions = "\n".join(" ".join(map(str, exception)) for exception in exceptions)
    
    return f"{exceptions_count}\n{formatted_exceptions}"
from typing import Optional, List, Union, Dict

from src.constants.constants import MM_DATA_HEADER, DEFAULT_MM_DATA_BY_RACE_MODE
from src.constants.races import RaceMode


def write_mm_data_header(output_file: str) -> None:
    header = ["Description"] + MM_DATA_HEADER * 2
    with open(output_file, "w") as f:
        f.write(",".join(header) + "\n")


def determine_mm_data_description(race_type: str, prefix: str, race_index: Optional[int] = None) -> str:
    if race_type == RaceMode.CHECKPOINT:
        return prefix
    else:
        return f"{prefix}{race_index}"
    
    
def fill_mm_data_values(race_type: str, custom_mm_data: List[Union[int, float]]) -> List[Union[int, float]]:
    default_values = [1] * 11
    replace_indices = DEFAULT_MM_DATA_BY_RACE_MODE.get(race_type, [])
    
    for index, custom_value in zip(replace_indices, custom_mm_data):
        default_values[index] = custom_value
        
    return default_values[:10]


def generate_mm_data_string(prefix: str, ama_filled_values: List[Union[int, float]], pro_filled_values: List[Union[int, float]]) -> str:
    ama_data = ",".join(map(str, ama_filled_values))
    pro_data = ",".join(map(str, pro_filled_values))
    return f"{prefix},{ama_data},{pro_data}\n"


def write_mm_data(output_file: str, configs: Dict[str, Dict], race_type: str, prefix: str) -> None:
    with open(output_file, "a") as f:
        for race_index, config in configs.items():
            mm_data_description = determine_mm_data_description(race_type, prefix, race_index)
                       
            ama_filled_values = fill_mm_data_values(race_type, config["mm_data"]["ama"])
            pro_filled_values = fill_mm_data_values(race_type, config["mm_data"]["pro"])
                        
            mm_data = generate_mm_data_string(mm_data_description, ama_filled_values, pro_filled_values)

            f.write(mm_data)
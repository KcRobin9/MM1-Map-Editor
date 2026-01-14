import math
from pathlib import Path
from typing import List, Tuple, Dict, Union

from src.game.bridges.constants import BRIDGE_ATTRIBUTE_FILLER, BRIDGE_ORIENTATION_ERROR
from src.game.bridges.configs import BRIDGE_CONFIG_DEFAULT, BRIDGE_CONFIG_TEMPLATE, ORIENTATION_MAPPINGS

from src.constants.modes import NetworkMode, RaceMode
from src.constants.file_formats import FileType


def create_bridges(all_bridges, set_bridges: bool, output_file: Path):
    if not set_bridges:
        return
        
    # if output_file.exists():
    #     os.remove(output_file)
    
    def calculate_facing(offset: Tuple[float, float, float], orientation: Union[str, float]) -> List[float]:
        if isinstance(orientation, (float, int)):
            angle_radians = math.radians(orientation)
            
            return [
                offset[0] + 10 * math.cos(angle_radians),
                offset[1],
                offset[2] + 10 * math.sin(angle_radians)
            ]

        if orientation in ORIENTATION_MAPPINGS:
            return [offset[i] + ORIENTATION_MAPPINGS[orientation][i] for i in range(3)]
         
        raise ValueError(BRIDGE_ORIENTATION_ERROR)
        
    def generate_attribute_lines(bridge_attributes) -> str:
        lines = ""
        
        # For example, Crossgates
        for attr in bridge_attributes:
            attr_offset, attr_orientation, attr_id, attr_type = attr
            attr_facing = calculate_facing(attr_offset, attr_orientation)
            
            line = f"\t{attr_type},{attr_id},{','.join(map(str, attr_offset))},{','.join(map(str, attr_facing))}\n"
            lines += line
            
        return lines

    bridge_data = []
    bridge_type_counts = {}

    for bridge in all_bridges:
        offset, orientation, id, drawbridge, bridge_attributes = bridge

        face = calculate_facing(offset, orientation)
        drawbridge_values = f"{drawbridge},0,{','.join(map(str, offset))},{','.join(map(str, face))}"
        attributes = generate_attribute_lines(bridge_attributes)

        num_fillers = 5 - len(bridge_attributes)        
        fillers = BRIDGE_ATTRIBUTE_FILLER * num_fillers

        # Do not change
        template = (
            f"DrawBridge{id}\n"
            f"\t{drawbridge_values}\n"
            f"{attributes}"
            f"{fillers}"
            f"DrawBridge{id}\n"  
            )
        
        bridge_data.append(template)
        
        # Count bridge types
        bridge_type_counts[drawbridge] = bridge_type_counts.get(drawbridge, 0) + 1

    with open(output_file, "a") as f:
        f.writelines(bridge_data)

    # Build the bridge breakdown string
    if bridge_type_counts:
        breakdown = " , ".join([f"{count}x {bridge_type}" for bridge_type, count in sorted(bridge_type_counts.items())])
        print(f"Successfully created bridge file with {len(all_bridges)} bridge(s) ({breakdown})")
    else:
        print(f"Successfully created bridge file with {len(all_bridges)} bridge(s)")


def create_bridge_config(configs: List[Dict[str, Union[float, int, str]]], set_bridges: bool, output_folder: Path) -> None:
    if not set_bridges:
        return
    
    for config in configs:
        final_config = merge_bridge_configs (BRIDGE_CONFIG_DEFAULT, config)
        config_str = generate_bridge_config_string(final_config)
        filenames = determine_bridge_filenames(final_config)
        write_bridge_config_to_files(filenames, config_str, output_folder)


def merge_bridge_configs(default_config: Dict[str, Union[float, int, str]], custom_config: Dict[str, Union[float, int, str]]) -> Dict[str, Union[float, int, str]]:
    return {**default_config, **custom_config}


def generate_bridge_config_string(config: Dict[str, Union[float, int, str]]) -> str:
    return BRIDGE_CONFIG_TEMPLATE.format(**config)


def determine_bridge_filenames(config: Dict[str, Union[float, int, str]]) -> List[str]:
    filenames = []
    race_type = config["RaceType"]

    if race_type in [RaceMode.ROAM, RaceMode.COPS_AND_ROBBERS]:
        base_name = race_type
        filenames += get_bridge_mode_filenames(base_name, config["Mode"])
    elif race_type in [RaceMode.CHECKPOINT, RaceMode.CIRCUIT, RaceMode.BLITZ]:
        filenames += get_bridge_race_type_filenames(race_type, config["RaceNum"], config["Mode"])
    else:
        raise ValueError(f"\nInvalid RaceType. Must be one of {RaceMode.ROAM}, {RaceMode.BLITZ}, {RaceMode.CHECKPOINT}, {RaceMode.CIRCUIT}, or {RaceMode.COPS_AND_ROBBERS}.\n")

    return filenames


def get_bridge_mode_filenames(base_name: str, mode: str) -> List[str]:
    filenames = []
    if mode in [NetworkMode.SINGLE, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{base_name}{FileType.BRIDGE_MANAGER}")
    if mode in [NetworkMode.MULTI, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{base_name}M{FileType.BRIDGE_MANAGER}")
    return filenames


def get_bridge_race_type_filenames(race_type: str, race_num: str, mode: str) -> List[str]:
    filenames = []
    if mode in [NetworkMode.SINGLE, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{race_type}{race_num}{FileType.BRIDGE_MANAGER}")
    if mode in [NetworkMode.MULTI, NetworkMode.SINGLE_AND_MULTI]:
        filenames.append(f"{race_type}{race_num}M{FileType.BRIDGE_MANAGER}")
    return filenames


def write_bridge_config_to_files(filenames: List[str], config_str: str, output_folder: Path) -> None:
    for filename in filenames:
        file_path = output_folder / filename
        file_path.write_text(config_str)
import random
import shutil
from pathlib import Path
from typing import Dict, Union, List

from src.core.vector.vector_3 import Vector3

from src.game.races.constants import RaceModeNum, RaceMode, RACE_TYPE_INITIALS

from src.constants.constants import PROP_CAN_COLLIDE_FLAG, HUGE
from src.constants.misc import Folder, Encoding, Default
from src.constants.file_formats import FileType, Axis

from src.file_formats.props.props import Bangers
from src.io.binary import write_pack

from src.USER.settings.main import MAP_FILENAME
from src.USER.settings.debug import debug_props 


class BangerEditor:
    def __init__(self) -> None:  
        self.map_filename = Path(MAP_FILENAME)                      
        self.props = [] 
        
    def process_all(self, user_set_props: list, set_props: bool):
        if not set_props:
            return
        
        per_race_props = {}

        for prop in user_set_props:
            race_keys = []
            
            if 'race' in prop:
                race_value = prop['race']
                
                # Handle list of races
                if isinstance(race_value, list):
                    for race in race_value:
                        race_keys.extend(self._expand_race_key(race))
                else:
                    race_keys = self._expand_race_key(race_value)

            elif 'race_mode' in prop:  # Old method support
                race_mode = prop.get('race_mode', RaceMode.ROAM)
                race_num = prop.get('race_num', '')
                if race_mode in [RaceMode.CIRCUIT, RaceMode.CHECKPOINT, RaceMode.BLITZ] and race_num != '':
                    race_keys = [f"{race_mode}_{race_num}"]
                else:
                    race_keys = [race_mode]
            else:
                race_keys = [RaceMode.ROAM]  # No race specified - default to ROAM (goes to base map file)
            
            # Add prop to each specified race
            for race_key in race_keys:
                per_race_props.setdefault(race_key, []).append(prop)

        total_props = 0
        prop_counts = {}
        
        for race_key, race_props in per_race_props.items():                
            self.props.clear()
            self.add_multiple(race_props)
            current_filename = self._filename_with_suffix(race_key)
            Bangers.write_all(Folder.SHOP_CITY / current_filename, self.props, debug_props)
            total_props += len(self.props)
            
            # Count props by name
            for prop in self.props:
                prop_name = prop.name.rstrip('\x00')
                prop_counts[prop_name] = prop_counts.get(prop_name, 0) + 1
        
        # Build the prop breakdown string
        if prop_counts:
            breakdown = ", ".join([f"{count}x {name}" for name, count in sorted(prop_counts.items())])
            print(f"Successfully created props file with {total_props} prop(s)\n{breakdown}, ")
        else:
            print(f"Successfully created props file with {total_props} prop(s)")


    def _expand_race_key(self, race_value):
        if race_value == RaceModeNum.CIRCUIT_ALL or race_value == RaceMode.CIRCUIT:
            return [
                getattr(RaceModeNum, attr) 
                for attr in dir(RaceModeNum) 
                if attr.startswith("CIRCUIT_") and attr != "CIRCUIT_ALL" and not attr.startswith('_')
            ]
        elif race_value == RaceModeNum.CHECKPOINT_ALL or race_value == RaceMode.CHECKPOINT:
            return [
                getattr(RaceModeNum, attr) 
                for attr in dir(RaceModeNum) 
                if attr.startswith("CHECKPOINT_") and attr != "CHECKPOINT_ALL" and not attr.startswith('_')
            ]
        elif race_value == RaceModeNum.BLITZ_ALL or race_value == RaceMode.BLITZ:
            return [
                getattr(RaceModeNum, attr) 
                for attr in dir(RaceModeNum) 
                if attr.startswith("BLITZ_") and attr != "BLITZ_ALL" and not attr.startswith('_')
            ]
        else:
            return [race_value]

    def add_multiple(self, user_set_props):    
        for prop in user_set_props:
            offset = Vector3(*prop['offset']) 
            end = Vector3(*prop['end']) if 'end' in prop else None
            face = Vector3(*prop.get('face', (HUGE, HUGE, HUGE)))
            name = prop['name']
            
            if end is not None:
                diagonal = end - offset
                diagonal_length = diagonal.Mag()
                normalized_diagonal = diagonal.Normalize()
                
                if face == Vector3(HUGE, HUGE, HUGE):
                    face = normalized_diagonal * HUGE
                
                separator = prop.get('separator', 10.0)
            
                if isinstance(separator, str) and separator.lower() in (Axis.X, Axis.Y, Axis.Z):
                    prop_dims = self.load_dimensions(Folder.EDITOR_RESOURCES / "PROPS" / "prop_dimensions.txt").get(name, Vector3(1, 1, 1))
                    separator = getattr(prop_dims, separator.lower())
                elif not isinstance(separator, (int, float)):
                    separator = 10.0
                                            
                num_props = int(diagonal_length / separator)
                
                for i in range(0, num_props):
                    dynamic_offset = offset + normalized_diagonal * (i * separator)
                    self.props.append(
                        Bangers(
                            Default.ROOM, 
                            PROP_CAN_COLLIDE_FLAG, 
                            dynamic_offset, 
                            face, 
                            name + "\x00"
                            )
                        )
            else:
                self.props.append(
                    Bangers(
                        Default.ROOM, 
                        PROP_CAN_COLLIDE_FLAG, 
                        offset, 
                        face, 
                        name + "\x00"
                        )
                    )

    def append_to_file(self, input_props_f: Path, props_to_append: list, appended_props_f: Path, append_props: bool):
        if not append_props:
            return
            
        with open(input_props_f, "rb") as f:
            original_props = Bangers.read_all(f)

        self.props = original_props
        original_count = len(self.props)
        
        with open(input_props_f, "rb") as f:
            f.seek(0, 2)  # Move to the end of the file
            append_offset = f.tell()
        
        self.add_multiple(props_to_append)
        
        with open(appended_props_f, "r+b") as f:
            f.seek(0)  # Update the prop count
            Bangers.write_n(f, self.props)
            
            # Append new props at the correct offset
            f.seek(append_offset)
            for i, prop in enumerate(self.props[original_count:], start=original_count):
                write_pack(f, '<2H', Default.ROOM, PROP_CAN_COLLIDE_FLAG)  
                prop.offset.write(f, '<')
                prop.face.write(f, '<')
                f.write(prop.name.encode(Encoding.UTF_8))
        
        if debug_props:
            Bangers.debug(Folder.DEBUG / "PROPS" / f"{appended_props_f.name}{FileType.TEXT}", self.props)

    def place_randomly(self, seed: int, num_props: int, props_dict: dict, x_range: tuple, z_range: tuple):
        assert len(x_range) == 2 and len(z_range) == 2, "x_range and z_range must each contain exactly two values."

        random.seed(seed)
        names = props_dict.get("name", [])
        names = names if isinstance(names, list) else [names]
        
        random_props = []
        
        for name in names:
            for _ in range(num_props):
                x = random.uniform(*x_range)
                z = random.uniform(*z_range)
                y = props_dict.get("offset_y", 0.0)
                
                new_prop = {
                    "name": name,
                    "offset": (x, y, z)
                } 

                if "face" not in props_dict:
                    new_prop["face"] = (
                        random.uniform(-HUGE, HUGE),
                        random.uniform(-HUGE, HUGE), 
                        random.uniform(-HUGE, HUGE)
                    )
                else:
                    new_prop["face"] = props_dict["face"]

                new_prop.update({k: v for k, v in props_dict.items() if k not in new_prop})
                random_props.append(new_prop)
                
        return random_props

    def _filename_with_suffix(self, race_key):        
        if race_key == RaceMode.ROAM:
            return self.map_filename.with_suffix(FileType.PROP)  # basename gets no suffix, i.e.: First_City.BNG
        
        if "_" in race_key:  # Numbered races like "CIRCUIT_0"
            parts = race_key.rsplit("_", 1)  
            if len(parts) == 2 and parts[1].isdigit():
                race_mode = parts[0]
                race_num = parts[1]
            else:
                race_mode = race_key
                race_num = "0"
        else:
            race_mode = race_key
            race_num = "0"
        
        short_race_mode = RACE_TYPE_INITIALS.get(race_mode, race_mode)
        
        return self.map_filename.parent / f"{self.map_filename.stem}_{short_race_mode}{race_num}{FileType.PROP}"
                                                                            
    @staticmethod  
    def load_dimensions(input_file: Path) -> dict:
        extracted_prop_dim = {}
        
        with open(input_file, "r") as f:
            for line in f:
                prop_name, value_x, value_y, value_z = line.split()
                extracted_prop_dim[prop_name] = Vector3(float(value_x), float(value_y), float(value_z))
        return extracted_prop_dim





def read_banger_file(file_path: Path) -> List[str]:
    with open(file_path, "r") as f:
        return f.readlines()


def write_banger_file(file_path: Path, lines: List[str]) -> None:
    with open(file_path, "w") as f:
        f.writelines(lines)


def update_banger_properties(lines: List[str], properties: Dict[str, Union[int, str]]) -> List[str]:
    updated_lines = lines.copy()
    for i, line in enumerate(updated_lines):
        for key, new_value in properties.items():
            if line.strip().startswith(key):
                updated_lines[i] = f'\t{key} {new_value}\n'
    return updated_lines


def edit_and_copy_bangerdata_to_shop(prop_properties: Dict[str, Dict[str, Union[int, str]]], input_folder: Path, output_folder: Path, file_type: str) -> None:
    for file in input_folder.glob(f"*{file_type}"):  # First copy unmodified files directly
        if file.stem not in prop_properties:
            shutil.copy(file, output_folder)
   
    for prop_key, properties in prop_properties.items():  # Then process and write modified files
        banger_file = input_folder / f"{prop_key}{file_type}"
       
        if banger_file.exists():
            lines = read_banger_file(banger_file)
            updated_lines = update_banger_properties(lines, properties)
            write_banger_file(output_folder / banger_file.name, updated_lines)
import math
from pathlib import Path

from src.constants.misc import Folder, Default
from src.constants.file_formats import FileType

from src.file_formats.facades.facades import Facades
from src.USER.settings.main import MAP_FILENAME


class FacadeEditor:    
    @classmethod
    def create(cls, output_file: str, user_set_facades, set_facades: bool, debug_facades: bool):
        if not set_facades:
            return
        
        facades = cls.process(user_set_facades)
        Facades.write_all(output_file, facades)
        
        # Count facades by name
        facade_counts = {}
        for facade in facades:
            facade_counts[facade.name] = facade_counts.get(facade.name, 0) + 1
        
        # Build the facade breakdown string
        if facade_counts:
            breakdown = ", ".join([f"{count}x {name}" for name, count in sorted(facade_counts.items())])
            print(f"Successfully created facades file with {len(facades)} facade(s)\n---facades: {breakdown}")
        else:
            print(f"Successfully created facades file with {len(facades)} facade(s)")

        Facades.debug(facades, debug_facades, Folder.DEBUG / "FACADES" / f"{MAP_FILENAME}{FileType.TEXT}")

    @staticmethod
    def read_scales(input_file: Path):
        with open(input_file, 'r') as f:
            return {name: float(scale) for name, scale in (line.strip().split(": ") for line in f)}

    @classmethod
    def process(cls, user_set_facades):
        axis_dict = {'x': 0, 'y': 1, 'z': 2}
        scales = cls.read_scales(Folder.RESOURCES_EDITOR / "FACADES" / "FCD scales.txt")

        facades = []
        for params in user_set_facades:
            axis = axis_dict[params['axis']]
            start_coord = params['offset'][axis]
            end_coord = params['end'][axis]

            direction = 1 if start_coord < end_coord else -1

            num_facades = math.ceil(abs(end_coord - start_coord) / params['separator'])

            for i in range(num_facades):
                current_start, current_end = cls.calculate_start_end(params, axis, direction, start_coord, i)
                sides = params.get('sides', (0.0, 0.0, 0.0))
                scale = scales.get(params['name'], params.get('scale', 1.0))
                facades.append(Facades(Default.ROOM, params['flags'], current_start, current_end, sides, scale, params['name']))

        return facades
    
    @staticmethod
    def calculate_start_end(params, axis, direction, start_coord, i):
        shift = direction * params['separator'] * i
        current_start = list(params['offset'])
        current_end = list(params['end'])

        current_start[axis] = start_coord + shift
        end_coord = params['end'][axis]
        
        if direction == 1:
            current_end[axis] = min(start_coord + shift + params['separator'], end_coord)
        else:
            current_end[axis] = max(start_coord + shift - params['separator'], end_coord)

        return tuple(current_start), tuple(current_end)
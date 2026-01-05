import textwrap
from typing import BinaryIO

from src.file_formats.ai.street import aiStreet
from src.file_formats.ai.intersection import aiIntersection
from src.file_formats.ai.helpers import read_array_list

from src.io.binary import read_unpack

from src.constants.misc import Folder

from src.USER.Settings.main import MAP_FILENAME


class aiMap:
    def __init__(self):
        self.paths = []
        self.intersections = []
        self.ambient_roads = []
        self.ped_roads = []

    def load(self, f: BinaryIO) -> None:
        num_isects, num_paths = read_unpack(f, '<2H')

        print(f"{num_paths} roads, {num_isects} isects")

        for _ in range(num_paths):
            self.paths.append(aiStreet.read(f))

        for _ in range(num_isects):
            self.intersections.append(aiIntersection.read(f))

        num_cells, = read_unpack(f, '<I')

        for _ in range(num_cells):
            self.ambient_roads.append(read_array_list(f))

        for _ in range(num_cells):
            self.ped_roads.append(read_array_list(f))

    def read(f: BinaryIO) -> 'aiMap':
        result = aiMap()
        result.load(f)
        return result
    
    
class BaiMap:
    def __init__(self, street_names):
        self.street_names = street_names
        self.write_map()
             
    def write_map(self):           
        with open(Folder.MIDTOWNMADNESS_DEV_CITY_MAP / f"{MAP_FILENAME}.map", 'w') as f:
            f.write(self.map_template())
    
    def map_template(self):
        num_streets = len(self.street_names)
        map_streets = '\n\t\t'.join([f'"{street}"' for street in self.street_names])
        
        map_data = f"""
mmMapData :0 {{
    NumStreets {num_streets}
    Street [
        {map_streets}
    ]
}}
        """
        return textwrap.dedent(map_data).strip()
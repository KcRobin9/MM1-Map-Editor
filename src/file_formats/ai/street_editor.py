import textwrap

from src.constants.file_formats import FileType
from src.constants.props import Prop
from src.constants.constants import NO
from src.constants.misc import Folder, Default

from src.game.races.constants_2 import IntersectionType
from src.file_formats.ai.map import BaiMap

from src.USER.settings.main import MAP_FILENAME


class aiStreetEditor:
    def __init__(self, data, set_reverse_ai_streets: bool):
        self.map_filename = MAP_FILENAME
        self.street_name = data["street_name"]
        self.set_reverse_ai_streets = set_reverse_ai_streets
        self.process_lanes(data)
        self.set_properties(data)
                    
    def process_lanes(self, data):
        if "lanes" in data:
            self.original_lanes = data["lanes"]
        elif "vertices" in data:
            self.original_lanes = {"lane_1": data["vertices"]}
        else:
            raise ValueError("Street data must have either 'lanes' or 'vertices'")

        # Add reverse lanes if set by the user
        self.lanes = self.original_lanes.copy()
        if self.set_reverse_ai_streets:
            for key, values in self.original_lanes.items():
                self.lanes[key].extend(values[::-1])
                        
    def set_properties(self, data):
        default_values = {
            "intersection_types": [IntersectionType.CONTINUE, IntersectionType.CONTINUE],
            "stop_light_positions": [(0.0, 0.0, 0.0)] * 4,
            "stop_light_names": [Prop.STOP_LIGHT_SINGLE, Prop.STOP_LIGHT_SINGLE],
            "traffic_blocked": [NO, NO],
            "ped_blocked": [NO, NO],
            "road_divided": NO,
            "alley": NO,
        }

        for key, default in default_values.items():
            setattr(self, key, data.get(key, default))
            
    @classmethod
    def create(cls, dataset, set_ai_streets: bool, set_reverse_ai_streets: bool):
        if not set_ai_streets:
            return None
        street_names = []
        
        for data in dataset:
            editor = cls(data, set_reverse_ai_streets)
            editor.write()
            street_names.append(editor.street_name)
    
        # Build the street names list
        street_names_str = ", ".join(street_names)
        print(f"Successfully created {len(street_names)} AI street file(s)\n---streets names: {street_names_str}")
        return BaiMap(street_names)

    def write(self):    
        with open(Folder.MIDTOWNMADNESS_DEV_CITY_MAP / f"{self.street_name}{FileType.AI_STREET}", 'w') as f:
            f.write(self.set_template())

    def set_template(self):
        lane_one = list(self.lanes.keys())[0]  # Assuming all lanes have the same number of vertices
        num_vertices_per_lane = len(self.original_lanes[lane_one])
        num_total_vertices = num_vertices_per_lane * len(self.lanes) * (2 if self.set_reverse_ai_streets else 1)
        
        vertices = '\n\t\t'.join('\n\t\t'.join(
            f'{vertex[0]} {vertex[1]} {vertex[2]}' for vertex in vertices) for vertices in self.lanes.values())
        
        normals = '\n\t\t'.join(
            Default.NORMAL for _ in range(num_vertices_per_lane))
        
        stop_light_positions = '\n\t'.join(
            f"""StopLightPos[{i}] {pos[0]} {pos[1]} {pos[2]}"""
            for i, pos in enumerate(self.stop_light_positions))

        street_template = f"""
mmRoadSect :0 {{
    NumVertexs {num_vertices_per_lane}
    NumLanes[0] {len(self.lanes)}
    NumLanes[1] {len(self.lanes) if self.set_reverse_ai_streets else 0}
    NumSidewalks[0] 0
    NumSidewalks[1] 0
    TotalVertexs {num_total_vertices}
    Vertexs [
        {vertices}
    ]
    Normals [
        {normals}
    ]
    IntersectionType[0] {self.intersection_types[0]}
    IntersectionType[1] {self.intersection_types[1]}
    {stop_light_positions}
    Blocked[0] {self.traffic_blocked[0]}
    Blocked[1] {self.traffic_blocked[1]}
    PedBlocked[0] {self.ped_blocked[0]}
    PedBlocked[1] {self.ped_blocked[1]}
    StopLightName [
        "{self.stop_light_names[0]}"
        "{self.stop_light_names[1]}"
    ]
    Divided {self.road_divided}
    Alley {self.alley}
}}
        """
        return textwrap.dedent(street_template).strip()
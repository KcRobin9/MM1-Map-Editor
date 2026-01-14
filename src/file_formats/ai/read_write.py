import math
from pathlib import Path
from typing import List, Any

from src.file_formats.ai.map import aiMap
from src.file_formats.ai.helpers import MiniParser

from src.core.vector.vector_3 import Vector3

from src.game.races.constants_2 import IntersectionType

from src.constants.props import Prop

#! ############ Code by 0x1F9F1 (Modified) // end ############ !#     

def read_ai(input_file: Path):
    ai_map = aiMap()

    with open(input_file, "rb") as f:
        ai_map.load(f)

        here = f.tell()
        f.seek(0, 2)
        assert here == f.tell()

    streets = []
    
    for i, path in enumerate(ai_map.paths):
        assert i == path.id  # ID matches path index      
        assert path.id != path.oncoming_path  # A path should not be its own oncoming
        assert ai_map.paths[path.oncoming_path].oncoming_path == path.id  # A path should be properly linked with its oncoming
        assert path.num_sidewalks in [0, 1]  # No more than 1 sidewalk per road-side

        assert path.intersection_type in [
            IntersectionType.STOP, 
            IntersectionType.STOP_LIGHT, 
            IntersectionType.YIELD, 
            IntersectionType.CONTINUE
            ]  
        
        # TODO: adjust or remove this (i.e. get the actual object name)
        if path.intersection_type == IntersectionType.STOP:
            assert path.stop_light_name == Prop.STOP_SIGN  
        else:
            assert path.stop_light_name in [Prop.STOP_LIGHT_SINGLE, Prop.STOP_LIGHT_DUAL]   

        sink_isect = path.lane_vertices[0]
        source_isect = path.lane_vertices[path.num_vertexes - 1]

        for lane in range(1, path.num_lanes):
            here = lane * path.num_vertexes
            assert path.lane_vertices[here] == sink_isect
            assert path.lane_vertices[here + path.num_vertexes - 1] == source_isect

        if path.num_sidewalks == 0:  # Only custom paths should have no sidewalks
            assert all(v == Vector3(0, 1, 0) for v in path.normals)  # If there are no sidewalks, all normals are straight up

        isect_id = path.intersection_ids[0]
        isect = ai_map.intersections[isect_id]

        has_sink = False
        for isect_path in isect.paths:
            if isect_path != path.id:
                isect_path = ai_map.paths[isect_path]
                if isect_path.intersection_ids[0] != isect_id and isect_path.oncoming_path != path.id:
                    has_sink = True
                    break
                
        if not has_sink:
            print(f"No eligible roads identified to turn onto from road: {path.id}.")

        if path.id < path.oncoming_path:
            streets.append((f"Street{len(streets)}", (path, ai_map.paths[path.oncoming_path])))

    assert len(streets) * 2 == len(ai_map.paths)
    
    return ai_map, streets


def write_ai_map_txt(streets, output_map_file: Path) -> None:
    with open(output_map_file, "w") as f:  
        
        parser = MiniParser(f)

        parser.begin_class("mmMapData")

        parser.field("NumStreets", len(streets))
        parser.field("Street", ["Street" + str(paths[0].id) for _, paths in streets])

        parser.end_class() 
        
        
def write_ai_intersections_txt(ai_map, file_path_pattern: Path) -> None:
    for intersection in ai_map.intersections:        
        
        output_files = Path(file_path_pattern.format(intersection_id = intersection.id))
        
        with open(output_files, 'w') as f: 
                    
            parser = MiniParser(f)
    
            parser.begin_class("mmIntersection")

            parser.field("ID", intersection.id)
            parser.field("Position", intersection.position)

            parser.field("NumSinks", len(intersection.sinks))
            parser.field("Sinks", intersection.sinks)

            parser.field("NumSources", len(intersection.sources))
            parser.field("Sources", intersection.sources)

            parser.field("Paths", intersection.paths)
            parser.field("Directions", intersection.directions)

            parser.end_class()

 
def validate_and_prepare_ai_paths(streets) -> List[Any]:
    prepared_data = []

    for _, paths in streets:
        assert paths[0].num_vertexes == paths[1].num_vertexes
        assert paths[0].num_sidewalks == paths[1].num_sidewalks
        assert paths[0].divided == paths[1].divided
        assert paths[0].alley == paths[1].alley
        assert paths[0].normals == list(reversed(paths[1].normals))
        assert paths[0].normals[0] == Vector3(0, 1, 0)
        assert paths[0].normals[-1] == Vector3(0, 1, 0)

        if paths[0].num_sidewalks != 0:
            for n in range(1, len(paths[0].normals) - 1):
                target = paths[0].normals[n]

                a = paths[0].lane_vertices[n]
                b = paths[0].boundaries[paths[0].num_vertexes + n - 1]
                c = paths[0].boundaries[paths[0].num_vertexes + n]

                normal = calc_normal(a, b, c)
                angle = math.degrees(target.Angle(normal))

                if angle > 0.01:
                    print(f"Road {paths[0].id} has suspicious normal {n}: Expected {target}, Calculated {normal} ({angle:.2f} degrees error)")

            for road in range(2):
                path = paths[road]

                assert path.boundaries[path.num_vertexes:] == list(reversed(paths[road ^ 1].l_boundaries))

                for i in range(path.num_vertexes):
                    a = path.lane_vertices[i + (path.num_lanes * path.num_vertexes)]
                    b = (path.boundaries[i] + path.boundaries[i + path.num_vertexes]) * 0.5
                    assert a.Dist2(b) < 0.00001
        
        prepared_data.append(paths)
    
    return prepared_data


def write_ai_paths(prepared_data: List[Any], file_path_pattern: Path) -> None:
    for paths in prepared_data:
        output_road_files = Path(file_path_pattern.format(paths = paths[0].id))
                
        with open(output_road_files, "w") as f:
            parser = MiniParser(f)
    
            parser.begin_class("mmRoadSect")

            parser.field("NumVertexs", paths[0].num_vertexes)

            parser.field("NumLanes[0]", paths[0].num_lanes)
            parser.field("NumLanes[1]", paths[1].num_lanes)

            parser.field("NumSidewalks[0]", paths[0].num_sidewalks * 2)
            parser.field("NumSidewalks[1]", paths[1].num_sidewalks * 2)

            all_vertexs = []

            for road in range(2):
                path = paths[road]
                split = path.num_lanes * path.num_vertexes
                all_vertexs += path.lane_vertices[0:split]

            if path.num_sidewalks:
                for road in range(2):
                    path = paths[road]
                    all_vertexs += path.boundaries

            expected_count = paths[0].num_vertexes * (paths[0].num_lanes + paths[1].num_lanes + (paths[0].num_sidewalks + paths[1].num_sidewalks) * 2)

            assert len(all_vertexs) == expected_count

            parser.field("TotalVertexs", len(all_vertexs))
            parser.field("Vertexs", all_vertexs)
            parser.field("Normals", paths[0].normals)

            # Yes, these are "supposed" to be backwards
            parser.field("IntersectionType[0]", paths[1].intersection_type)
            parser.field("IntersectionType[1]", paths[0].intersection_type)
            parser.field("StopLightPos[0]", paths[1].stop_light_pos[0])
            parser.field("StopLightPos[1]", paths[1].stop_light_pos[1])
            parser.field("StopLightPos[2]", paths[0].stop_light_pos[0])
            parser.field("StopLightPos[3]", paths[0].stop_light_pos[1])
            
            parser.field("StopLightIndex", paths[0].stop_light_index)
        
            parser.field("Blocked[0]", paths[0].blocked)
            parser.field("Blocked[1]", paths[1].blocked)

            parser.field("PedBlocked[0]", paths[0].ped_blocked)
            parser.field("PedBlocked[1]", paths[1].ped_blocked)

            # Yes, these are "supposed" to be backwards
            parser.field("StopLightName", [paths[1].stop_light_name, paths[0].stop_light_name])

            parser.field("Divided", paths[0].divided)       
            parser.field("Alley", paths[0].alley)
            parser.field("IsFlat", paths[0].is_flat)
            parser.field("HasBridge", paths[0].has_bridge)
            parser.field("SpeedLimit", paths[0].speed_limit)
            
            parser.field("ID", paths[0].id)
            parser.field("OncomingPath", paths[0].oncoming_path)
            parser.field("PathIndex", paths[0].path_index)
            parser.field("EdgeIndex", paths[0].edge_index)
            parser.field("IntersectionIds", paths[0].intersection_ids)
                        
            parser.field("VertXDirs", paths[0].vert_x_dirs)
            parser.field("VertZDirs", paths[0].vert_z_dirs)
            parser.field("SubSectionDirs", paths[0].sub_section_dirs)
            
            parser.field("CenterOffsets", paths[0].center_offsets)
            parser.field("SubSectionOffsets", paths[0].sub_section_offsets)
                    
            parser.field("RoadLength", paths[0].road_length)
            parser.field("LaneWidths", paths[0].lane_widths)
            parser.field("LaneLengths", paths[0].lane_lengths)
            
            parser.end_class()

       
def debug_ai(input_file: Path, debug_file: bool, output_map_file: Path, output_int_files: Path, output_road_files: Path) -> None:
    if not debug_file:
        return
        
    ai_map, streets = read_ai(input_file)
    
    write_ai_map_txt(streets, output_map_file)
    
    paths = validate_and_prepare_ai_paths(streets)
    write_ai_paths(paths, output_road_files)
    
    write_ai_intersections_txt(ai_map, output_int_files)
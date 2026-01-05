import bpy
import time

from pathlib import Path
from mathutils import Vector
from helpers.main import is_process_running

from src.constants.file_formats import FileType
from src.constants.misc import Color, Executable
from src.core.geometry.main import transform_coordinate_system


def extract_and_format_road_data(input_folder: Path, output_file: Path) -> None: 
    for file in input_folder.iterdir():
        if file.is_file() and file.suffix == FileType.AI_STREET:
            
            with open(file, 'r') as f:
                all_lines = f.readlines()
            
                total_vertex = int(all_lines[6][17:])
                num_vertexs = int(all_lines[1][15:])

                relevant_lines = [line.lstrip() for line in all_lines[8:8+total_vertex+1]]
                blocks = ["".join(relevant_lines[i:i+num_vertexs]) for i in range(0, total_vertex, num_vertexs)]
                
                vertex_string = "\n".join(blocks).replace(" ", ",")

                with open(output_file, mode = "a") as out_f:
                    out_f.write(f"{vertex_string}\n")


def process_generated_road_file(input_file: Path) -> list:
    polyline_block = []
    all_polyline_blocks = []

    with open(input_file, 'r') as f:
        for line in f:
            if line.strip() == '':
                # Empty line denotes end of polyline block, add current polyline to the list and start a new one
                all_polyline_blocks.append(polyline_block)
                polyline_block = []
            else:
                # Add the current line to the current polyline block
                polyline_block.append(tuple(map(float, line.strip().split(','))))

    if polyline_block:
        all_polyline_blocks.append(polyline_block)

    return all_polyline_blocks


def create_road_path(curve_object: bpy.types.Object, vertices) -> None:
    curve_data = curve_object.data
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 1
    curve_data.bevel_depth = 0.70 

    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(vertices) - 1) 
    
    for index, vertex in enumerate(vertices):
        x, y, z = transform_coordinate_system(Vector(vertex), game_to_blender = True)
        polyline.points[index].co = (x, y, z, 1) 


def add_road_paths(all_polyline_blocks) -> None:
    for i, polyline_block in enumerate(all_polyline_blocks):
        
        curve_data = bpy.data.curves.new(f"Street_{i}", type = 'CURVE')
        curve_object = bpy.data.objects.new(f"Street_{i}", curve_data)
        bpy.context.collection.objects.link(curve_object)
    
        for j in range(len(polyline_block) - 1):
            create_road_path(curve_object, polyline_block[j:j + 2])

                    
def apply_path_color_scheme() -> None:
    for path in (obj for obj in bpy.context.collection.objects if obj.type == 'CURVE'):
        num_splines = len(path.data.splines)
        
        for idx, spline in enumerate(path.data.splines):
            mat = bpy.data.materials.new(name = f"Material_{path.name}_{idx}")
            
            # Assign a Red Color to the first and last spline, Blue and Green to the rest
            if idx == 0 or idx == num_splines - 1:
                mat.diffuse_color = Color.RED
            else:
                mat.diffuse_color = [Color.BLUE, Color.GREEN][(idx - 1) % 2]

            path.data.materials.append(mat)
            spline.material_index = idx
            
                      
def process_and_visualize_paths(input_folder: Path, output_file: Path, visualize_ai_paths: bool) -> None:
    if not visualize_ai_paths or not is_process_running(Executable.BLENDER):
        return
    
    extract_and_format_road_data(input_folder, output_file)
    time.sleep(0.1)  # Sleep to ensure file operations are completed

    polyline_blocks = process_generated_road_file(output_file)
    time.sleep(0.1)  # Sleep to ensure file operations are completed

    add_road_paths(polyline_blocks)
    apply_path_color_scheme()
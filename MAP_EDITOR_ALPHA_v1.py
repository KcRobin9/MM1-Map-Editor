
#! =====================================================================
#! ================= Midtown Madness 1 Map Editor Alpha ================
#? 
#? This Map Editor allows users to create new maps for Midtown Madness 1
#                                           Copyright (C) May 2023 Robin
#? 
#? This program is free software: you can redistribute it and/or modify
#? it under the terms of the GNU General Public License as published by
#? the Free Software Foundation, either version 3 of the License, or
#? (at your option) any later version.
#? 
#? This program is distributed in the hope that it will be useful, but
#? WITHOUT ANY WARRANTY; without even the implied warranty of
#? MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
#? General Public License for more details.
#? 
#? For more information about GNU see <http://www.gnu.org/licenses/>.
#! =====================================================================
#! =====================================================================

#* Core Python path setup
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

#* Standard library imports
import re
import math
import time
import shutil
import random
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Set, Any, Tuple, Optional, BinaryIO

#* Third-party imports
import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore

#* Map Editor imports
# Core imports
from src.core.vector.vector_2 import Vector2
from src.core.vector.vector_3 import Vector3
from src.core.vector.vector_4 import Vector4

from src.core.geometry.main import calc_center_coords, calc_distance, calculate_center_tuples, calculate_extrema, sort_coordinates
from src.core.geometry.planes import ensure_ccw_order, ensure_quad_ccw_order, compute_plane_edgenormals, compute_edges

# Debug imports
from src.debug.main import Debug

# File format imports
from src.file_formats.ai.read_write import debug_ai
from src.file_formats.ai.street_editor import aiStreetEditor 

from src.file_formats.props.props import Bangers
from src.file_formats.props.editor import BangerEditor, edit_and_copy_bangerdata_to_shop
from src.file_formats.props.subtract import subtract_props_from_file

from src.file_formats.facades.facades import Facades
from src.file_formats.facades.editor import FacadeEditor

from src.file_formats.physics import PhysicsEditor

from src.file_formats.development import DLP

# Game imports
from src.game.races.main import create_races
from src.game.races.cops_and_robbers import create_cops_and_robbers

from src.game.bridges.main import create_bridges, create_bridge_config

from src.game.waypoints.constants import Rotation, Width

from src.game.animations import create_animations
from src.game.extrema import create_extrema
from src.game.lighting import LightingEditor
from src.game.texture_sheet import TextureSheet
from src.game.setup import create_map_info, copy_custom_textures_to_shop, copy_carsim_files_to_shop, ensure_empty_mm_dev_folder

# Helper imports
from src.helpers.main import calc_size, is_process_running

# Integration imports
from src.integrations.blender.setup import setup_blender
from src.integrations.blender.inits import initialize_blender_operators, initialize_blender_panels, initialize_blender_waypoint_editor
from src.integrations.blender.keybindings import set_blender_keybinding
from src.integrations.blender.modeling.ai_paths import process_and_visualize_paths
from src.integrations.blender.modeling.meshes import create_blender_meshes

# IO imports
from src.io.binary import read_unpack, write_pack, read_binary_name, write_binary_name

# Misc imports
from src.misc.main import create_commandline, start_game, post_editor_cleanup
from src.misc.angel import create_angel_resource_file

# Progress bar imports
from src.ui.progress_bar.main import RunTimeManager, start_progress_tracking
from src.ui.progress_bar.constants import EDITOR_RUNTIME_FILE, COLOR_DIVIDER

# Constants imports
from src.constants.constants import * 
from src.constants.file_formats import Portal, Material, Room, LevelOfDetail, agiMeshSet, PlaneEdgesWinding, Magic, FileType
from src.constants.textures import Texture
from src.constants.misc import Shape, Encoding, Executable, Default, Folder, Threshold, Color

# USER imports
from src.USER.settings.main import (
    MAP_NAME, MAP_FILENAME,
    play_game, delete_shop,
    set_bridges, set_props, set_facades, set_physics, set_animations, set_texture_sheet, set_music,
    set_minimap, minimap_outline_color,
    set_ai_streets, set_reverse_ai_streets,
    set_lars_race_maker, 
    cruise_start_position,
    randomize_textures, random_textures,
    round_vector_values, disable_progress_bar
)

from src.USER.settings.advanced import (
    no_ui, no_ui_type, no_ai, 
    less_logs, more_logs, 
    lower_portals, empty_portals, 
    set_dlp, fix_faulty_quads
) 

from src.USER.settings.debug import (
    debug_props, debug_meshes, debug_bounds, debug_facades, debug_physics, debug_portals, debug_lighting, debug_minimap, debug_minimap_id,
    debug_props_file, debug_props_file_to_csv, debug_facades_file, debug_portals_file, debug_ai_file,
    debug_meshes_file, debug_meshes_folder, debug_bounds_file, debug_bounds_folder, debug_dlp_file, debug_dlp_folder,
    debug_props_data_file, debug_facades_data_file, debug_portals_data_file, debug_ai_data_file,
    debug_meshes_data_file, debug_meshes_data_folder, debug_bounds_data_file, debug_bounds_data_folder, debug_dlp_data_file, debug_dlp_data_folder,
)

from src.USER.settings.blender import load_all_texures, visualize_ai_paths

from src.USER.facades import facade_list
from src.USER.ai_streets import street_list
from src.USER.physics import custom_physics
from src.USER.lighting import lighting_configs
from src.USER.animations import animations_data
from src.USER.bridges import bridge_list, bridge_config_list

from src.USER.races.cops_and_robbers import cops_and_robbers_waypoints
from src.USER.races.races import blitz_race_names, checkpoint_race_names, circuit_race_names, race_data

from src.USER.props.properties import prop_properties

from src.USER.props.props import prop_list, random_props  # 'Set' props could be a better name? I.e. create from scratch
from src.USER.props.edit import edit_props, props_to_edit, edit_tolerance, edit_require_confirmation, edit_input_props_file, edit_output_props_file
from src.USER.props.replace import replace_props, props_to_replace, replace_tolerance, replace_require_confirmation, replace_input_props_file, replace_output_props_file
from src.USER.props.duplicate import duplicate_props, props_to_duplicate, duplicate_tolerance, duplicate_input_props_file, duplicate_output_props_file
from src.USER.props.append import append_props, props_to_append, append_input_props_file, append_output_props_file

from src.USER.props.subtract import (
    subtract_props,
    props_to_subtract,
    ranges_to_subtract,
    subtract_tolerance,
    subtract_require_confirmation,
    subtract_input_props_file,
    subtract_output_props_file
)

from src.USER.textures.properties import texture_modifications

from src.USER.misc.dlp import dlp_groups, dlp_patches, dlp_vertices

################################################################################################################               
################################################################################################################
#! ======================= VARIABLE DECLARATIONS & PROGRESS BAR ======================= !#

vertices = [] 
texture_names = []
texcoords_data = {}

polygons_data = []

hudmap_vertices = []
hudmap_properties = {}

progress_thread, start_time = start_progress_tracking(MAP_NAME, EDITOR_RUNTIME_FILE, disable_progress_bar)

################################################################################################################               
################################################################################################################     
#! ======================= POLYGON CLASS ======================= !#

#TODO: refactor and move later
class Polygon:
    def __init__(self, cell_id: int, material_index: int, flags: int, vertex_index: List[int],
                 plane_edges: List[Vector3], plane_normal: Vector3, plane_distance: float, 
                 cell_type: int = Room.DEFAULT, always_visible: bool = False) -> None:
        
        self.cell_id = cell_id
        self.material_index = material_index
        self.flags = flags
        self.vertex_index = vertex_index
        self.plane_edges = plane_edges
        self.plane_normal = plane_normal
        
        if isinstance(plane_distance, list) and len(plane_distance) == 1:
            plane_distance = plane_distance[0]
        elif isinstance(plane_distance, np.float64):
            plane_distance = float(plane_distance)
            
        self.plane_distance = plane_distance
        
        self.cell_type = cell_type
        self.always_visible = always_visible
        
    @property
    def is_quad(self) -> bool:
        return bool(self.flags & Shape.QUAD)

    @property
    def num_verts(self) -> int:
        return Shape.QUAD if self.is_quad else Shape.TRIANGLE
          
    @classmethod
    def read(cls, f: BinaryIO) -> 'Polygon':
        cell_id, material_index, = read_unpack(f, '<HB')
        flags = read_unpack(f, '<B')
        vertex_index = read_unpack(f, '<4H') 
        plane_edges = Vector3.readn(f, Shape.QUAD, '<')
        plane_normal = Vector3.read(f, '<')
        plane_distance = read_unpack(f, '<f')
        return cls(cell_id, material_index, flags, vertex_index, plane_edges, plane_normal, plane_distance)
            
    def write(self, f: BinaryIO) -> None:            
        if len(self.vertex_index) == Shape.TRIANGLE:  # Each polygon requires four vertex indices
            self.vertex_index += (0,)
        
        write_pack(f, '<HB', self.cell_id, self.material_index)
        write_pack(f, '<B', self.flags)
        write_pack(f, '<4H', *self.vertex_index)

        for edge in self.plane_edges:
            edge.write(f, '<')
            
        self.plane_normal.write(f, '<')
        write_pack(f, '<f', self.plane_distance)
    
    def __repr__(self, bnd_instance) -> str:
        vertices_coordinates = [bnd_instance.vertices[idx] for idx in self.vertex_index]
        # plane_d = ', '.join(f'{d:.2f}' for d in self.plane_d)
        return f"""
POLYGON
    Cell ID: {self.cell_id}
    Material Index: {self.material_index}
    Flags: {self.flags}
    Vertex Indices: {self.vertex_index}
    Vertices Coordinates: {vertices_coordinates}
    Plane Edges: {self.plane_edges}
    Plane Normal: {self.plane_normal}
    Plane Distance: {self.plane_distance}
    """
    
################################################################################################################               
################################################################################################################     

Default.POLYGON = Polygon(0, 0, 0, [0, 0, 0, 0], [Default.VECTOR_3 for _ in range(4)], Default.VECTOR_3, [0.0], 0)
polys = [Default.POLYGON]
        
################################################################################################################               

#TODO: move this somewhere else
class Debug:
    _created_folders = set()

    @staticmethod
    def _ensure_output_folder_exists(output_file: Path) -> None:
        output_folder = output_file.parent

        if output_folder in Debug._created_folders:
            return

        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        Debug._created_folders.add(output_folder)

    @staticmethod
    def internal(instance: Any, debug_flag: bool, output_file: Path) -> None:
        if not debug_flag:
            return

        Debug._ensure_output_folder_exists(output_file)
        
        with open(output_file, 'w') as out_f:
            out_f.write(str(instance))
        
        print(f"Debugged instance data to {output_file.name}")

    @staticmethod
    def internal_list(instance_list: List[Any], debug_flag: bool, output_file: Path) -> None:
        if not debug_flag:
            return
        
        Debug._ensure_output_folder_exists(output_file)

        with open(output_file, 'w') as out_f:
            for instance in instance_list:
                out_f.write(repr(instance)) 

        print(f"Debugged list data to {output_file.name}")

################################################################################################################          
#! ======================= BOUNDS CLASS ======================= !#

#TODO: refactor and move later
class Bounds:
    def __init__(self, magic: str, offset: Vector3, x_dim: int, y_dim: int, z_dim: int, 
                 center: Vector3, radius: float, radius_sqr: float, bb_min: Vector3, bb_max: Vector3, 
                 num_verts: int, num_polys: int, num_hot_verts_1: int, num_hot_verts_2: int, num_edges: int, 
                 x_scale: float, z_scale: float, num_indices: int, height_scale: float, cache_size: int, 
                 vertices: List[Vector3], polys: List[Polygon],
                 hot_verts: List[Vector3], edge_verts_1: List[int], edge_verts_2: List[int], 
                 edge_plane_normal: List[Vector3], edge_plane_distance: List[float],
                 row_offsets: Optional[List[int]], bucket_offsets: Optional[List[int]], 
                 row_buckets: Optional[List[int]], fixed_heights: Optional[List[int]]) -> None:
        
        self.magic = magic
        self.offset = offset    
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.z_dim = z_dim
        self.center = center    
        self.radius = radius
        self.radius_sqr = radius_sqr
        self.bb_min = bb_min         
        self.bb_max = bb_max        
        self.num_verts = num_verts
        self.num_polys = num_polys
        self.num_hot_verts_1 = num_hot_verts_1
        self.num_hot_verts_2 = num_hot_verts_2
        self.num_edges = num_edges
        self.x_scale = x_scale
        self.z_scale = z_scale
        self.num_indices = num_indices
        self.height_scale = height_scale
        self.cache_size = cache_size
        
        self.vertices = vertices              
        self.polys = polys   
        
        self.hot_verts = hot_verts
        self.edge_verts_1 = edge_verts_1
        self.edge_verts_2 = edge_verts_2
        self.edge_plane_normal = edge_plane_normal
        self.edge_plane_distance = edge_plane_distance
        self.row_offsets = row_offsets
        self.bucket_offsets = bucket_offsets
        self.row_buckets = row_buckets
        self.fixed_heights = fixed_heights
                  
    @classmethod
    def read(cls, f: BinaryIO) -> 'Bounds':  
        magic = read_binary_name(f, len(Magic.BOUND))
        offset = Vector3.read(f, '<')
        x_dim, y_dim, z_dim = read_unpack(f, '<3l')
        center = Vector3.read(f, '<')
        radius, radius_sqr = read_unpack(f, '<2f')
        bb_min = Vector3.read(f, '<')
        bb_max = Vector3.read(f, '<')
        num_verts, num_polys = read_unpack(f, '<2l')
        num_hot_verts_1, num_hot_verts_2, num_edges = read_unpack(f, '<3l')
        x_scale, z_scale = read_unpack(f, '<2f')
        num_indices, height_scale, cache_size = read_unpack(f, '<lfl')
        
        vertices = Vector3.readn(f, num_verts, '<')
        polys = [Polygon.read(f) for _ in range(num_polys + 1)] 

        hot_verts = Vector3.readn(f, num_hot_verts_2, '<')
        edge_verts_1 = read_unpack(f, f'<{num_edges}I')
        edge_verts_2 = read_unpack(f, f'<{num_edges}I')
        edge_plane_normal = Vector3.readn(f, num_edges, '<')
        edge_plane_distance = read_unpack(f, f'<{num_edges}f')

        row_offsets = None
        bucket_offsets = None
        row_buckets = None
        fixed_heights = None

        if x_dim and y_dim and z_dim:
            row_offsets = read_unpack(f, f'<{z_dim}I')
            bucket_offsets = read_unpack(f, f'<{x_dim * z_dim}H')
            row_buckets = read_unpack(f, f'<{num_indices}H')
            fixed_heights = read_unpack(f, f'<{x_dim * z_dim}B')

        return cls(
            magic, offset, x_dim, y_dim, z_dim, center, radius, radius_sqr, bb_min, bb_max, 
            num_verts, num_polys, num_hot_verts_1, num_hot_verts_2, num_edges, 
            x_scale, z_scale, num_indices, height_scale, cache_size, vertices, polys,
            hot_verts, edge_verts_1, edge_verts_2, edge_plane_normal, edge_plane_distance,
            row_offsets, bucket_offsets, row_buckets, fixed_heights
            )
    
    @classmethod
    def initialize(cls, vertices: List[Vector3], polys: List[Polygon]) -> 'Bounds':
        magic = Magic.BOUND
        offset = Default.VECTOR_3
        x_dim, y_dim, z_dim = 0, 0, 0
        center = Vector3.center(vertices)
        radius = Vector3.calculate_radius(vertices, center)
        radius_sqr = Vector3.calculate_radius_squared(vertices, center)
        bb_min = Vector3.min(vertices)
        bb_max = Vector3.max(vertices)
        num_hot_verts_1, num_hot_verts_2, num_edges = 0, 0, 0
        x_scale, z_scale = 0.0, 0.0
        num_indices, height_scale, cache_size = 0, 0.0, 0
        
        hot_verts = [Default.VECTOR_3]
        edge_verts_1, edge_verts_2 = [0], [1] 
        edge_plane_normal = [Default.VECTOR_3]
        edge_plane_distance = [0.0]  
        row_offsets, bucket_offsets, row_buckets, fixed_heights = [0], [0], [0], [0]  

        return cls(
            magic, offset, x_dim, y_dim, z_dim, 
            center, radius, radius_sqr, bb_min, bb_max, 
            len(vertices), len(polys) - 1, 
            num_hot_verts_1, num_hot_verts_2, num_edges, 
            x_scale, z_scale, num_indices, height_scale, cache_size, 
            vertices, polys, 
            hot_verts, edge_verts_1, edge_verts_2, 
            edge_plane_normal, edge_plane_distance,
            row_offsets, bucket_offsets, row_buckets, fixed_heights
            )
            
    def write(self, f: BinaryIO) -> None:
        write_binary_name(f, self.magic)
        self.offset.write(f, '<')         
        write_pack(f, '<3l', self.x_dim, self.y_dim, self.z_dim)
        self.center.write(f, '<') 
        write_pack(f, '<2f', self.radius, self.radius_sqr)
        self.bb_min.write(f, '<')
        self.bb_max.write(f, '<')
        write_pack(f, '<2l', self.num_verts, self.num_polys)
        write_pack(f, '<3l', self.num_hot_verts_1, self.num_hot_verts_2, self.num_edges)
        write_pack(f, '<2f', self.x_scale, self.z_scale)
        write_pack(f, '<lfl', self.num_indices, self.height_scale, self.cache_size)
 
        for vertex in self.vertices:       
            vertex.write(f, '<')   
        
        for poly in self.polys:           
            poly.write(f)
                    
    @staticmethod
    def create(output_file: Path, vertices: List[Vector3], polys: List[Polygon], debug_file: Path, debug_bounds: bool) -> None:
        bnd = Bounds.initialize(vertices, polys)
                
        with open (output_file, "wb") as f:
            bnd.write(f)

        bnd.debug(debug_bounds, debug_file)
            
    def debug(self, debug_bounds, output_file: Path) -> None:
        Debug.internal(self, debug_bounds, output_file)
                            
    @staticmethod
    def debug_file(input_file: Path, output_file: Path, debug_bounds_file: bool) -> None:
        if not debug_bounds_file:
            return
        
        if not input_file.exists():
            raise FileNotFoundError(f"The file {input_file} does not exist.")
        
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)
        
        with open(input_file, "rb") as in_f:
            bnd = Bounds.read(in_f)

        with open(output_file, "w") as out_f:
            out_f.write(repr(bnd))
            
    @staticmethod
    def debug_folder(input_folder: Path, output_folder: Path, debug_bounds_folder: bool) -> None:
        if not debug_bounds_folder:
            return

        if not input_folder.exists():
            raise FileNotFoundError(f"The folder {input_folder} does not exist.")

        bnd_files = list(input_folder.glob(f"*{FileType.BOUND}"))
        
        if not bnd_files:
            raise FileNotFoundError(f"No {FileType.BOUND} files found in {input_folder}.")

        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        for file in bnd_files:
            output_file = output_folder / file.with_suffix({FileType.TEXT}).name
            Bounds.debug_file(file, output_file, debug_bounds_folder)
            print(f"Processed {file.name} to {output_file.name}")
                    
    def __repr__(self) -> str:
        polygon_polys = '\n'.join([poly.__repr__(self) for poly in self.polys])
        return f"""
BOUND
    Magic: {self.magic}
    Offset: {self.offset}
    X Dim: {self.x_dim}
    Y Dim: {self.y_dim}
    Z Dim: {self.z_dim}
    Center: {self.center}
    Radius: {self.radius:.2f}
    Radius Sqr: {self.radius_sqr:.2f}
    BB Min: {self.bb_min}
    BB Max: {self.bb_max}
    Num Verts: {self.num_verts}
    Num Polys: {self.num_polys}
    Num Hot Verts 1: {self.num_hot_verts_1}
    Num Hot Verts 2: {self.num_hot_verts_2}
    Num Edges: {self.num_edges}
    X Scale: {self.x_scale:.5f}
    Z Scale: {self.z_scale:.5f}
    Num Indices: {self.num_indices}
    Height Scale: {self.height_scale:.5f}
    Cache Size: {self.cache_size}\n
    Vertices:
    {self.vertices}\n
    ======= Polys =======
    {polygon_polys}\n
    ======= Split =======\n
    Hot Verts: {self.hot_verts}
    Edge Verts 1: {self.edge_verts_1}
    Edge Verts 2: {self.edge_verts_2}
    Edge Plane Normal: {self.edge_plane_normal}
    Edge Plane Distance: {', '.join(f'{d:.2f}' for d in self.edge_plane_distance)}\n  
    ======= Split =======\n
    Row Offsets: {self.row_offsets}\n
    ======= Split =======\n
    Bucket Offsets: {self.bucket_offsets}\n
    ======= Split =======\n
    Row Buckets: {self.row_buckets}\n
    ======= Split =======\n
    Fixed Heights: {self.fixed_heights}\n
    """
    
################################################################################################################               
################################################################################################################  
#! ======================= MESHES CLASS ======================= !#

#TODO: refactor and move later
class Meshes:
    def __init__(self, magic: str, vertex_count: int, adjunct_count: int, surface_count: int, indices_count: int,
                 radius: float, radius_sqr: float, bounding_box_radius: float,
                 texture_count: int, flags: int, cache_size: int,
                 texture_names: List[str], vertices: List[Vector3],
                 normals: List[int], tex_coords: List[float], enclosed_shape: List[int],
                 surface_sides: List[int], indices_sides: List[List[int]]) -> None:

        self.magic = magic
        self.vertex_count = vertex_count
        self.adjunct_count = adjunct_count
        self.surface_count = surface_count
        self.indices_count = indices_count
        self.radius = radius
        self.radius_sqr = radius_sqr
        self.bounding_box_radius = bounding_box_radius
        self.texture_count = texture_count
        self.flags = flags
        self.cache_size = cache_size
        self.texture_names = texture_names
        self.vertices = vertices
        self.normals = normals
        self.tex_coords = tex_coords  
        self.enclosed_shape = enclosed_shape  
        self.surface_sides = surface_sides
        self.indices_sides = indices_sides
        
    @classmethod
    def read(cls, input_file: Path) -> 'Meshes':
        with open(input_file, "rb") as f:
            magic = read_binary_name(f, len(Magic.MESH), padding = 12)
            vertex_count, adjunct_count, surface_count, indices_count = read_unpack(f, '<4I')
            radius, radius_sqr, bounding_box_radius = read_unpack(f, '<3f')
            texture_count, flags = read_unpack(f, '<2B')
            
            f.read(2)  # Padding
            cache_size, = read_unpack(f, '<I')
                                      
            texture_names = [read_binary_name(f, 32, Encoding.ASCII, 16) for _ in range(texture_count)]
            
            if vertex_count < Threshold.MESH_VERTEX_COUNT:
                vertices = Vector3.readn(f, vertex_count, '<')
            else:
                vertices = Vector3.readn(f, vertex_count + 8, '<')
                                        
            normals = list(read_unpack(f, f"{adjunct_count}B"))
            tex_coords = list(read_unpack(f, f"{adjunct_count * 2}f"))
            enclosed_shape = list(read_unpack(f, f"{adjunct_count}H"))
            surface_sides = list(read_unpack(f, f"{surface_count}B"))
            
            indices_per_surface = indices_count // surface_count
            indices_sides = [list(read_unpack(f, f"<{indices_per_surface}H")) for _ in range(surface_count)]
            
        return cls(
            magic, vertex_count, adjunct_count, surface_count, indices_count, 
            radius, radius_sqr, bounding_box_radius, 
            texture_count, flags, cache_size, texture_names, vertices, 
            normals, tex_coords, enclosed_shape, surface_sides, indices_sides
            )
                    
    def write(self, output_file: Path) -> None: 
        self.calculate_cache_size()
               
        with open(output_file, "wb") as f:
            write_binary_name(f, self.magic, 16) 
            write_pack(f, '<4I', self.vertex_count, self.adjunct_count, self.surface_count, self.indices_count)
            write_pack(f, '<3f', self.radius, self.radius_sqr, self.bounding_box_radius)
            write_pack(f, '<2B', self.texture_count, self.flags)
            
            f.write(b'\0' * 2)  # Padding
            write_pack(f, '<I', self.cache_size)
            
            for texture_name in self.texture_names:
                write_binary_name(f, texture_name, length = 32, padding = 16) 
                            
            for vertex in self.vertices:
                vertex.write(f, '<')

            if self.vertex_count >= Threshold.MESH_VERTEX_COUNT:
                for _ in range(8):
                    Default.VECTOR_3.write(f, '<')
                                                                        
            write_pack(f, f"{self.adjunct_count}B", *self.normals)
                        
            # Ensure Tex Coords is not larger than (Adjunct Count * 2)
            if len(self.tex_coords) > self.adjunct_count * 2:
                self.tex_coords = self.tex_coords[:self.adjunct_count * 2] 
                
            write_pack(f, f"{self.adjunct_count * 2}f", *self.tex_coords)
            write_pack(f, f"{self.adjunct_count}H", *self.enclosed_shape)
            write_pack(f, f"{self.surface_count}B", *self.surface_sides)

            # Each polygon requires four vertex indices (add the value 0 as the 4th index in case of a triangle)
            for indices_side in self.indices_sides:
                while len(indices_side) == Shape.TRIANGLE:
                    indices_side.append(0)
                write_pack(f, f"{len(indices_side)}H", *indices_side)

    @staticmethod       
    def align_size(value: int) -> int:
        return (value + 7) & ~7
    
    def calculate_cache_size(self) -> None:
        self.cache_size = 0
        
        self.cache_size += self.align_size(self.vertex_count * Vector3.binary_size())

        if self.vertex_count >= Threshold.MESH_VERTEX_COUNT:
            self.cache_size += self.align_size(8 * Vector3.binary_size())

        if self.flags & agiMeshSet.NORMALS:
            self.cache_size += self.align_size(self.adjunct_count * calc_size('B'))

        if self.flags & agiMeshSet.TEXCOORDS:
            self.cache_size += self.align_size(self.adjunct_count * Vector2.binary_size())

        if self.flags & agiMeshSet.COLORS:
            self.cache_size += self.align_size(self.adjunct_count * calc_size('I'))

        self.cache_size += self.align_size(self.adjunct_count * calc_size('H'))

        if self.flags & agiMeshSet.PLANES:
            self.cache_size += self.align_size(self.surface_count * Vector4.binary_size())

        self.cache_size += self.align_size(self.indices_count * calc_size('H'))
        self.cache_size += self.align_size(self.surface_count * calc_size('B'))
  
    #! Debugging crashes ("line 778, in with_suffixif suffix and not suffix.startswith('.') or suffix == '.':")           
    def debug(self, output_file: Path, output_folder: Path, debug_meshes: bool) -> None:
        if not debug_meshes:
            return
            
        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        with open(output_folder / output_file, "w") as f:
            f.write(str(self))

    #TODO:
    # def debug(self, output_file: Path, output_folder: Path, debug_meshes: bool) -> None:
    #     Debug.internal(self, debug_meshes, output_folder / output_file)
                
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_meshes_file: bool) -> None:
        if not debug_meshes_file:
            return
        
        if not input_file.exists():
            raise FileNotFoundError(f"The file {input_file} does not exist.")
            
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(output_file, "w") as out_f:
            out_f.write(str(cls.read(input_file)))
                
    @classmethod
    def debug_folder(cls, input_folder: Path, output_folder: Path, debug_meshes_folder: bool) -> None:
        if not debug_meshes_folder:
            return
        
        if not input_folder.exists():
            raise FileNotFoundError(f"The folder {input_folder} does not exist.")

        mesh_files = list(input_folder.glob(f"*{FileType.MESH}"))
        
        if not mesh_files:
            raise FileNotFoundError(f"No {FileType.MESH} files found in {input_folder}.")
            
        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        for file in mesh_files:
            output_file = output_folder / file.with_suffix({FileType.TEXT}).name
            cls.debug_file(file, output_file, debug_meshes_folder)
                                
    def __repr__(self) -> str:
        return f"""
MESH
    Magic: {self.magic}
    Vertex Count: {self.vertex_count}
    Adjunct Count: {self.adjunct_count}
    Surface Count: {self.surface_count}
    Indices Count: {self.indices_count}
    Radius: {self.radius:.2f}
    Radius Sqr: {self.radius_sqr:.2f}
    BoundingBox Radius: {self.bounding_box_radius:.2f}
    Texture Count: {self.texture_count}
    Flags: {self.flags}
    Cache Size: {self.cache_size}\n
    Texture Names: {self.texture_names}\n
    Vertices: {self.vertices}\n
    Normals: {self.normals}\n
    Tex Coords: {', '.join(f'{coord:.2f}' for coord in self.tex_coords)}\n
    Enclosed Shape: {self.enclosed_shape}\n
    Surface Sides: {self.surface_sides}\n
    Indices Sides: {self.indices_sides}\n
    """
                         
################################################################################################################               
################################################################################################################          
#! ======================= CREATE MESH ======================= !#

#TODO: refactor and move later
def compute_uv(bound_number: int, tile_x: int = 1, tile_y: int = 1, angle_degrees: float = 0.0) -> List[float]:
    
    center_x, center_y = 0.5, 0.5

    coords = [
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1)
    ]

    def rotate_point(x: float, y: float, angle: float) -> Tuple[float, float]:
        rad = math.radians(angle)
        rotated_x = x * math.cos(rad) - y * math.sin(rad)
        rotated_y = x * math.sin(rad) + y * math.cos(rad)
        return rotated_x, rotated_y
    
    def adjust_and_rotate_coords(coords: List[Tuple[float, float]], angle: float) -> List[float]:
        adjusted_coords = []
        for x, y in coords:
            x, y = rotate_point(x - center_x, y - center_y, angle)
            adjusted_coords.extend([(x + center_x) * tile_x, (y + center_y) * tile_y])
        return adjusted_coords
    
    if "entries" not in texcoords_data:
        texcoords_data["entries"] = {}
        
    texcoords_data["entries"][bound_number] = {"tile_x": tile_x, "tile_y": tile_y, "angle_degrees": angle_degrees}

    return adjust_and_rotate_coords(coords, angle_degrees)
        

def determine_mesh_folder_and_filename(cell_id: int, texture_name: List[str]) -> Tuple[Path, str]:
    if cell_id < Threshold.CELL_TYPE_SWITCH:
        target_folder = Folder.SHOP_MESH_LANDMARK_MAP
    else:
        target_folder = Folder.SHOP_MESH_CITY_MAP
                        
    if any(name.startswith(Texture.WATER) for name in texture_name):
        mesh_filename = f"CULL{cell_id:02d}_A2{FileType.MESH_lowercase}"
    else:
        mesh_filename = f"CULL{cell_id:02d}_H{FileType.MESH_lowercase}"

    return target_folder, mesh_filename

           
def save_mesh(
    texture_name: str, texture_indices: List[int] = [1], 
    vertices: List[Vector3] = vertices, polys: List[Polygon] = polys, 
    normals: List[int] = None, tex_coords: List[float] = None, 
    randomize_textures: bool = randomize_textures, random_textures: List[str] = random_textures, 
    debug_meshes: bool = debug_meshes) -> None:
            
    poly = polys[-1]  # Get the last polygon added
    
    cell_id = poly.cell_id
    target_folder, mesh_filename = determine_mesh_folder_and_filename(cell_id, texture_name)
    
    if randomize_textures:
        texture_name = [random.choice(random_textures)] 
        
    texture_names.append(texture_name[0])
    
    mesh = initialize_mesh(vertices, [poly], texture_indices, texture_name, normals, tex_coords)
    mesh.write(target_folder / mesh_filename)
    
    #TODO: see "Debug.internal()"
    if debug_meshes:
        mesh.debug(Path(mesh_filename).with_suffix({FileType.TEXT}), Folder.DEBUG / "MESHES" / MAP_FILENAME, debug_meshes)


def initialize_mesh(
    vertices: List[Vector3], polys: List[Polygon], texture_indices: List[int], 
    texture_name: List[str], normals: List[int] = None, tex_coords: List[float] = None) -> Meshes:
    
    magic = Magic.MESH    
    flags = agiMeshSet.TEXCOORDS_AND_NORMALS
    cache_size = 0
       
    shapes = [[vertices[i] for i in poly.vertex_index] for poly in polys] 
    coordinates = [coord for shape in shapes for coord in shape]
        
    radius = Vector3.calculate_radius(coordinates, Default.VECTOR_3)  # Use Local Offset for the Center (this is not the case for the Bound files)
    radiussq = Vector3.calculate_radius_squared(coordinates, Default.VECTOR_3)
    bounding_box_radius = Vector3.calculate_bounding_box_radius(coordinates)  
    
    vertex_count = len(coordinates)
    adjunct_count = len(coordinates)
    surface_count = len(texture_indices)   
    texture_count = len(texture_name)
    
    # Each polygon requires four indices 
    if len(coordinates) in [Shape.QUAD, Shape.TRIANGLE]: 
        indices_count = surface_count * 4

    enclosed_shape = list(range(adjunct_count))
    normals = normals or [2] * adjunct_count  # 2 is the default value
    tex_coords = tex_coords or [1.0 for _ in range(adjunct_count * 2)]  # tile x and y once if no tex coords are provided
    indices_sides = [list(range(i, i + len(shape))) for i, shape in enumerate(shapes, start = 0)]
  
    return Meshes(
        magic, vertex_count, adjunct_count, surface_count, indices_count, 
        radius, radiussq, bounding_box_radius, 
        texture_count, flags, cache_size,
        texture_name, coordinates, normals, tex_coords, 
        enclosed_shape, texture_indices, indices_sides
        )

################################################################################################################               
################################################################################################################  
#! ======================= CREATE POLYGON ======================= !#

def check_bound_numbers(polys: List[Polygon]) -> None:
    found_bound_number_one = False
    bound_numbers = []
    
    for poly in polys[1:]:  # Skip the filler Polygon with Bound Number 0
        bound_number = poly.cell_id
        
        if bound_number <= 0 or bound_number == Threshold.CELL_TYPE_SWITCH or bound_number >= Threshold.VERTEX_INDEX_COUNT:
            error_message = f"""
            ***ERROR***
            - Polygon with "bound_number = {bound_number}" is not allowed. 
            - Bound Number must be between 1 and 199.
            - Bound Number must be between 201 and 32766.
            """
            raise ValueError(error_message)
        
        if bound_number == 1:
            found_bound_number_one = True
        
        bound_numbers.append(bound_number)
    
    if not found_bound_number_one:
        error_message = f"""
        ***ERROR***
        - There must be at least one Polygon with "bound_number = 1" (this was not found).
        """
        raise ValueError(error_message)

    bound_counter = Counter(bound_numbers)
    duplicate_bound_numbers = {num: count for num, count in bound_counter.items() if count > 1}
    
    if duplicate_bound_numbers:
        duplicate_details = []

        for bound_num, count in duplicate_bound_numbers.items():
            duplicate_details.append(f"\tbound_number = {bound_num} is used {count} times")
        
        error_message = f"""\n
        ***ERROR***
        - Duplicate bound numbers found. Each "bound_number" must be unique.
        - The following bound number(s) are used multiple times:
{chr(10).join(duplicate_details)}
        """
        raise ValueError(error_message)

    
def check_shape_type(vertex_coordinates: Optional[List[Vector3]]) -> None:
    if vertex_coordinates is None:
        error_message = """
        ***ERROR***
        Vertex Coordinates cannot be None.
        A valid list of vertex coordinates must be provided for polygon creation.
        """
        raise ValueError(error_message)

    if len(vertex_coordinates) not in (Shape.TRIANGLE, Shape.QUAD):
        error_message = """
        ***ERROR***
        Unsupported number of vertices.
        You must either set 3 or 4 vertex coordinates per polygon.
        """
        raise ValueError(error_message)


def process_winding(vertex_coordinates: List[Vector3], fix_faulty_quads: bool) -> List[Vector3]:
    if len(vertex_coordinates) == Shape.TRIANGLE:
        return ensure_ccw_order(vertex_coordinates)
    
    elif len(vertex_coordinates) == Shape.QUAD and fix_faulty_quads:
        return ensure_quad_ccw_order(vertex_coordinates)
    
    return vertex_coordinates  


def process_flags(vertex_coordinates: List[Vector3], flags: Optional[int] = None) -> int:
    if flags is not None:
        return flags
   
    if len(vertex_coordinates) == Shape.QUAD:
        return PlaneEdgesWinding.QUAD_Z_AXIS
   
    elif len(vertex_coordinates) == Shape.TRIANGLE:
        return PlaneEdgesWinding.TRIANGLE_Z_AXIS
    

def update_cruise_start_position(vertex_coordinates: List[Vector3]) -> None:
    global cruise_start_position
    x, y, z = calculate_center_tuples(vertex_coordinates)
    cruise_start_position = (x, y + 15, z)
    
    
def create_polygon(
    bound_number: int, vertex_coordinates: List[Vector3], 
    material_index: int = Material.DEFAULT, cell_type: int = Room.DEFAULT, flags: int = None, 
    plane_edges: List[Vector3] = None, wall_side: str = None, sort_vertices: bool = False,
    hud_color: str = Color.ROAD, minimap_outline_color: str = minimap_outline_color, 
    always_visible: bool = True, fix_faulty_quads: bool = fix_faulty_quads, base: bool = False) -> None:

    # Vertex indices
    base_vertex_index = len(vertices)
    
    check_shape_type(vertex_coordinates)
    
    # Store the Polygon Data for Blender (before any manipulation) 
    # TODO: should store data AFTER manipulation (but this needs more investigation in terms of making Game and Blender 1:1)
    polygon_info = {
        "bound_number": bound_number,
        "material_index": material_index,
        "vertex_coordinates": vertex_coordinates,
        "always_visible": always_visible,
        "sort_vertices": sort_vertices,
        "cell_type": cell_type,
        "hud_color": hud_color
    }
    
    polygons_data.append(polygon_info)
    
    # Winding & Flags
    vertex_coordinates = process_winding(vertex_coordinates, fix_faulty_quads)
    flags = process_flags(vertex_coordinates, flags)
     
    # Sorting        
    if sort_vertices: 
        vertex_coordinates = sort_coordinates(vertex_coordinates)
        
    # Base polygon               
    if base:
        update_cruise_start_position(vertex_coordinates)
          
    # Plane Edges    
    if plane_edges is None:
        plane_edges = compute_edges(vertex_coordinates) 
        
    # TODO: Refactor
    # Plane Normals
    if wall_side is None:
        plane_normal, plane_distance = compute_plane_edgenormals(*vertex_coordinates[:3])
    else:
        # Wall with varying X and Y coordinates
        if (max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates) > 0.1 and
            max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
            abs(max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates)) <= 0.15):

            if wall_side == "outside":
                corners = [0, 0, -1, max(coord[2] for coord in vertex_coordinates)]
            elif wall_side == "inside":
                corners = [0, 0, 1, -max(coord[2] for coord in vertex_coordinates)]
            
            plane_normal, plane_distance = corners[:3], corners[3]
            
        # Wall with varying Z and Y coordinates                               
        elif (abs(max(coord[0] for coord in vertex_coordinates) - min(coord[0] for coord in vertex_coordinates)) <= 0.15 and
              max(coord[1] for coord in vertex_coordinates) - min(coord[1] for coord in vertex_coordinates) > 0.1 and
              max(coord[2] for coord in vertex_coordinates) - min(coord[2] for coord in vertex_coordinates) > 0.1):

            if wall_side == "outside":
                corners = [-1, 0, 0, min(coord[0] for coord in vertex_coordinates)]
            elif wall_side == "inside":
                corners = [1, 0, 0, -min(coord[0] for coord in vertex_coordinates)]
                
            plane_normal, plane_distance = corners[:3], corners[3]

    if isinstance(plane_normal, np.ndarray):
        plane_normal = Vector3(*plane_normal.tolist())
        
    elif isinstance(plane_normal, list):
        plane_normal = Vector3(*plane_normal)
        
    # Finalize Polygon
    new_vertices = [Vector3(*coord) for coord in vertex_coordinates]
    vertices.extend(new_vertices)
    
    vertex_indices = [base_vertex_index + i for i in range(len(new_vertices))]
            
    poly = Polygon(
        bound_number, 
        material_index, 
        flags, 
        vertex_indices, 
        plane_edges, 
        plane_normal, 
        plane_distance, 
        cell_type, 
        always_visible
        )
    
    polys.append(poly)
        
    # Save HUD data
    hud_fill = hud_color is not None
    hudmap_vertices.append(vertex_coordinates)
    hudmap_properties[len(hudmap_vertices) - 1] = (hud_fill, hud_color, minimap_outline_color, str(bound_number))
    
################################################################################################################               
################################################################################################################  

Folder.create_all() 

################################################################################################################               
################################################################################################################  

#! =======================CREATING YOUR MAP======================= !#

def user_notes():
    """ 
    Find some Polygons and Textures examples below this text
    You can already run the script and create the Test Map yourself
    
    If you're setting a Quad, make sure the vertices are in the correct order (both clockwise and counterclockwise are OK)
    If you're unsure, set "sort_vertices = True" in the "create_polygon()" function
    
    The Material Index (an optional variable) defaults to 0 (default road friction). You can use the Material class constants    
    Note: you can also set custom Material / Physics Properties (search for: "custom_physics" in this script)
    
    Texture (UV) mapping examples:
    "tex_coords = compute_uv(bound_number = 1, tile_x = 5, tile_y = 2, angle_degrees = 0)"
    "tex_coords = compute_uv(bound_number = 2, tile_x = 4, tile_y = 8, angle_degrees = 90)"
        
    The variable "normals" (an optional variable) in the function "save_mesh()" makes the texture edges darker / lighter 
    If you're setting a Quad, you can for example do: "normals = [40, 2, 50, 1]"
    Where 2 is the default value. It is recommended to try different values to get an idea of the result in-game
        
    To properly set up the AI paths, adhere to the following for "bound_number = x":
    Open Areas: 1 - 199
    Roads: 201 - 859
    Intersections: 860 +
    
    IMPORTANT:
    The "bound_number" can not be equal to 0, 200, be negative, or be greater than 32767
    In addition, there must always exist one polygon with "bound_number = 1"
    
    If you wish to modify or add a Cell, Material, Texture or HUD constant and you are importing / exporting to Blender,
    then you must also modify the respective IMPORTS and EXPORTS. For Cells, this would be "CELL_IMPORT" and "CELL_EXPORT"
    """

#! ==============================TEST_CITY============================== #*
#! ==============================MAIN AREA============================== #*

# Colored Checkpoints
create_polygon(
    bound_number = 99,
    vertex_coordinates = [
        (-25.0, 0.0, 85.0),
        (25.0, 0.0, 85.0),
        (25.0, 0.0, 70.0),
        (-25.0, 0.0, 70.0)])

save_mesh(
    texture_name = [Texture.CHECKPOINT],
    tex_coords = compute_uv(bound_number = 99, tile_x = 5, tile_y = 1, angle_degrees = 0))

# Road with Buildings
create_polygon(
    bound_number = 201,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
        (50.0, 0.0, 70.0),
        (50.0, 0.0, -70.0),
        (-50.0, 0.0, -70.0)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE], normals = [40, 2, 50, 1],
    tex_coords = compute_uv(bound_number = 201, tile_x = 10, tile_y = 10, angle_degrees = 45))

# Grass Area 
create_polygon(
	bound_number = 861,
	material_index = Material.GRASS,
	vertex_coordinates = [
        (-50.0, 0.0, -70.0),
		(10.0, 0.0, -70.0),
        (10.0, 0.0, -130.0),
		(-50.0, 0.0, -130.0)],
        hud_color = Color.GRASS)

save_mesh(
    texture_name = [Texture.GRASS_BASEBALL], 
    tex_coords = compute_uv(bound_number = 861, tile_x = 7, tile_y = 7, angle_degrees = 90))

# Brown Grass Area
create_polygon(
	bound_number = 202,
	material_index = Material.GRASS,
	vertex_coordinates = [
		(10.0, 0.0, -70.0),
        (50.0, 0.0, -70.0),
		(50.0, 0.0, -130.0),
        (10.0, 0.0, -130.0)],
        hud_color = Color.GRASS)

save_mesh(
    texture_name = [Texture.GRASS_WINTER], 
    tex_coords = compute_uv(bound_number = 202, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Snow Area
create_polygon(
	bound_number = 1,
    cell_type = Room.NO_SKIDS,
    material_index = Material.NO_FRICTION,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)],
         hud_color = Color.SNOW)

save_mesh(
    texture_name = [Texture.SNOW], 
    tex_coords = compute_uv(bound_number = 1, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Barricade (Car) Area
create_polygon(
	bound_number = 862,
    cell_type = Room.TUNNEL,
	vertex_coordinates = [
		(50.0, 0.0, -70.0),
		(140.0, 0.0, -70.0),
		(140.0, 0.0, -140.0),
		(50.0, 0.0, -140.0)],
        hud_color = Color.RED_DARK)

save_mesh(
    texture_name = [Texture.BARRICADE_RED_BLACK], 
    tex_coords = compute_uv(bound_number = 862, tile_x = 50, tile_y = 50, angle_degrees = 0))

# Wood (Tree) Area
create_polygon(
	bound_number = 203,
	vertex_coordinates = [
		(50.0, 0.0, 70.0),
		(140.0, 0.0, 70.0),
		(140.0, 0.0, -70.0),
		(50.0, 0.0, -70.0)],
        hud_color = Color.WOOD)

save_mesh(
    texture_name = [Texture.WOOD], 
    tex_coords = compute_uv(bound_number = 203, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Water (Sailboat) Area
create_polygon(
	bound_number = 2,
    cell_type = Room.DRIFT,
	material_index = Material.WATER,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)],
        hud_color = Color.WATER)

save_mesh(
    texture_name = [Texture.WATER_WINTER], 
    tex_coords = compute_uv(bound_number = 2, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Diagonal Grass Road 
create_polygon(
    bound_number = 863,
	hud_color = Material.GRASS,
    vertex_coordinates = [
        (-50.0, 0.0, 110.0),
		(-50.0, 0.0, 140.0),
		(140.0, 0.0, 70.0),
		(93.01, 0.0, 70.0)])

save_mesh(
    texture_name = [Texture.GRASS_BASEBALL],
    tex_coords = compute_uv(bound_number = 863, tile_x = 10.0, tile_y = 10.0, angle_degrees = 90.0))

# Triangle Brick I 
create_polygon(
    bound_number = 204,
    cell_type = Room.NO_SKIDS,
    vertex_coordinates = [
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0),
        (-50.0, 0.0, 0.0)],
        hud_color = Color.YELLOW_LIGHT)

save_mesh(
    texture_name = [Texture.BRICKS_MALL],
    tex_coords = compute_uv(bound_number = 204, tile_x = 10, tile_y = 10, angle_degrees = 90))

# Triangle Brick II
create_polygon(
    bound_number = 205,
    cell_type = Room.NO_SKIDS,
    vertex_coordinates = [
        (-50.0, 0.0, 140.0),
        (-130.0, 15.0, 70.0),
        (-50.0, 0.0, 70.0)],
        hud_color = Color.YELLOW_LIGHT)

save_mesh(
    texture_name = [Texture.BRICKS_MALL],
    tex_coords = compute_uv(bound_number = 205, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Huge Orange Hill 
create_polygon(
	bound_number = 3,
    cell_type = Room.DRIFT,
	vertex_coordinates = [
		(-50.0, 0.0, -210.0),
		(50.0, 0.0, -210.0),
		(50.0, 300.0, -1000.0),
		(-50.0, 300.0, -1000.0)],
        hud_color = Color.ORANGE)

save_mesh(
    texture_name = [Texture.LAVA], 
    tex_coords = compute_uv(bound_number = 3, tile_x = 10, tile_y = 100, angle_degrees = 90))


#! ============================== ORANGE BUILDING ============================== #*
# South Wall
create_polygon(
    bound_number = 4,
    always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -50.0),
        (10.0, 0.0, -50.0),
        (10.0, 30.0, -50.11),
        (-10.0, 30.0, -50.11)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 4, tile_x = 1, tile_y = 1, angle_degrees = 0))

# North Wall
create_polygon(
    bound_number = 5,
    always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -70.00),
        (-10.0, 30.0, -70.0),
        (10.0, 30.0, -70.0),
        (10.0, 0.0, -70.00)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 5, tile_x = 1, tile_y = 1, angle_degrees = 0))

# West Wall
create_polygon(
    bound_number = 6,
    always_visible = False,
    vertex_coordinates = [
        (-9.99, 30.0, -50.0),
        (-9.99, 30.0, -70.0),
        (-10.0, 0.0, -70.0),
        (-10.0, 0.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 6, tile_x = 1, tile_y = 1, angle_degrees = 0))

# East Wall
create_polygon(
    bound_number = 7,
    always_visible = False,
    vertex_coordinates = [
        (10.0, 0.0, -70.0),
        (9.9, 30.0, -70.0),
        (9.9, 30.0, -50.0),
        (10.0, 0.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],  # Not applicable since we are overlaying a Facade on the sides of the building
    tex_coords = compute_uv(bound_number = 7, tile_x = 1, tile_y = 1, angle_degrees = 0))

# Rooftop
create_polygon(
    bound_number = 900,
    cell_type = Room.NO_SKIDS,
    material_index = Material.NO_FRICTION,
    vertex_coordinates = [
        (10.0, 30.0, -70.0),
        (-10.0, 30.0, -70.0),
        (-10.0, 30.0, -50.0),
        (10.0, 30.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 900, tile_x = 1, tile_y = 1, angle_degrees = 0))


#! ============================== BRIDGES ============================== #*
# Bridge I East
create_polygon(
	bound_number = 250,
	vertex_coordinates = [
		(-82.6, 0.0, -80.0),
		(-50.0, 0.0, -80.0),
		(-50.0, 0.0, -120.0),
		(-82.6, 0.0, -120.0)])
save_mesh(
    texture_name = [Texture.INTERSECTION], 
    tex_coords = compute_uv(bound_number = 250, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Road split
create_polygon(
	bound_number = 925,
	vertex_coordinates = [
		(-90.0, 14.75, -80.0),
		(-79.0, 14.75, -80.0),
		(-79.0, 14.75, -120.0),
		(-90.0, 14.75, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION], 
    tex_coords = compute_uv(bound_number = 925, tile_x = 5, tile_y = 5, angle_degrees = 90))

# Bridge II West
create_polygon(
	bound_number = 251,
	vertex_coordinates = [
		(-119.01, 0.0, -80.0),
		(-90.0, 0.0, -80.0),
		(-90.0, 0.0, -120.0),
		(-119.01, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.GRASS], 
    tex_coords = compute_uv(bound_number = 251, tile_x = 5, tile_y = 5, angle_degrees = 0))

# Road West of Bridge
create_polygon(
	bound_number = 252,
	vertex_coordinates = [
        (-160.0, 0.0, -80.0),
		(-119.1, 0.0, -80.0),
        (-119.1, 0.0, -120.0),
		(-160.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE], 
    tex_coords = compute_uv(bound_number = 252, tile_x = 5, tile_y = 3, angle_degrees = 0))

# Intersection West of Bridge
create_polygon(
	bound_number = 950,
	vertex_coordinates = [
        (-200.0, 0.0, -80.0),
		(-160.0, 0.0, -80.0),
        (-160.0, 0.0, -120.0),
		(-200.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION], 
    tex_coords = compute_uv(bound_number = 950, tile_x = 5, tile_y = 5, angle_degrees = 90))


#! ============================== ELEVATED AREA ============================== #*
# Road connected to Bridge Prop
create_polygon(
	bound_number = 501,
    base = False,
	vertex_coordinates = [
		(20.0, 30.0, 0.0),
        (50.0, 30.0, 0.0),
        (50.0, 12.0, -69.9),
        (20.0, 12.0, -69.9)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE], 
    tex_coords = compute_uv(bound_number = 501, tile_x = 3, tile_y = 2, angle_degrees = 90))

# Bricks Intersection
create_polygon(
	bound_number = 1100,
	vertex_coordinates = [
		(20.0, 30.0, 40.0),
        (50.0, 30.0, 40.0),
        (50.0, 30.0, 0.0),
        (20.0, 30.0, 0.0)])

save_mesh(
    texture_name = [Texture.BRICKS_GREY], 
    tex_coords = compute_uv(bound_number = 1100, tile_x = 10, tile_y = 10, angle_degrees = 0))

# Red Bus Color
create_polygon(
	bound_number = 502,
	vertex_coordinates = [
		(-10.0, 30.0, 40.0),
        (20.0, 30.0, 40.0),
        (20.0, 30.0, 0.0),
        (-10.0, 30.0, 0.0)])

save_mesh(
    texture_name = [Texture.BUS_RED_TOP], 
    tex_coords = compute_uv(bound_number = 502, tile_x = 4, tile_y = 3, angle_degrees = 0))

create_polygon(
	bound_number = 503,
	vertex_coordinates = [
		(-10.0, 30.0, 0.0),
        (10.0, 30.0, 0.0),
        (10.0, 30.0, -50.0),
        (-10.0, 30.0, -50.0)])

save_mesh(
    texture_name = [Texture.GLASS], 
    tex_coords = compute_uv(bound_number = 503, tile_x = 5, tile_y = 12, angle_degrees = 0))


#! ============================== SPEEDBUMPS ============================== #*
# Speed Bump South
create_polygon(
	bound_number = 206,
	vertex_coordinates = [ 
     (50.00,0.00,-130.00), 
     (50.00,3.00,-135.00), 
     (-50.00,3.00,-135.00), 
     (-50.00,0.00,-130.00)],
    hud_color = Color.RED_LIGHT)

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 206, tile_x = 15, tile_y = 1, angle_degrees = 90))

# Speed Bump North
create_polygon(
	bound_number = 207,
	vertex_coordinates = [
		(-50.0, 3.0, -135.0),
		(50.0, 3.0, -135.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)],
         hud_color = Color.RED_LIGHT)

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 207, tile_x = 1, tile_y = 10, angle_degrees = 0))

# Triangle Side I
create_polygon(
	bound_number = 208,
	vertex_coordinates = [
		(-50.0, 0.0, -140.0),
		(-50.01, 0.0, -130.0),
		(-50.0, 3.0, -135.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 208, tile_x = 30, tile_y = 30, angle_degrees = 90))

# Triangle Side II
create_polygon(
	bound_number = 209,
	vertex_coordinates = [
		(50.0, 0.0, -140.0),
		(50.01, 0.0, -130.0),
		(50.0, 3.0, -135.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN], 
    tex_coords = compute_uv(bound_number = 209, tile_x = 30, tile_y = 30, angle_degrees = 90))


#! ============================== CURVED FREEWAY ============================== #* 
create_polygon(
	bound_number = 2220,
	vertex_coordinates = [
		(-160.0, -0.00, -120.0),
		(-200.0, -0.00, -120.0),
		(-160.0, -3.0, -160.0)])

save_mesh(texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2220, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2221,
	vertex_coordinates = [
		(-200.0, -0.00, -120.0),
        (-160.0, -3.0, -160.0),
		(-200.0, -3.0, -160.0)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2221, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2222,
	vertex_coordinates = [
		(-160.0, -3.0, -160.0),
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2222, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2223,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-200.0, -3.0, -160.0),
		(-191.82, -6.00, -223.82)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2223, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2224,
	vertex_coordinates = [
		(-156.59, -6.00, -204.88),
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2224, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2225,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-191.82, -6.00, -223.82),
		(-165.59, -9.00, -260.54)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2225, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2226,
	vertex_coordinates = [
		(-140.06, -9.00, -229.75),
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2226, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2227,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-165.59, -9.00, -260.54),
		(-127.21, -12.00, -286.30)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2227, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

create_polygon(
	bound_number = 2228,
	vertex_coordinates = [
		(-117.58, -12.00, -247.47),
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2228, tile_x = 3.0, tile_y = 3.0, angle_degrees = 0))

create_polygon(
	bound_number = 2229,
	vertex_coordinates = [
		(-90.0, -15.00, -254.51),
		(-127.21, -12.00, -286.30),
		(-90.0, -15.00, -294.48)])

save_mesh(
	texture_name = [Texture.FREEWAY],
	tex_coords = compute_uv(bound_number = 2229, tile_x = 3.0, tile_y = 3.0, angle_degrees = 90))

# Intersection
create_polygon(
	bound_number = 924,
	vertex_coordinates = [
        (-90.0, -15.00, -254.51),
        (-79.0, -15.00, -254.51),
        (-79.0, -15.00, -294.48),
        (-90.0, -15.00, -294.48)])

save_mesh(
	texture_name = [Texture.INTERSECTION],
	tex_coords = compute_uv(bound_number = 924, tile_x = 5.0, tile_y = 5.0, angle_degrees = 0))

# Hill
create_polygon(
	bound_number = 923,
	vertex_coordinates = [
		(-79.0, -15.00, -254.51),
		(-90.0, -15.00, -254.51),
        (-90.0, 14.75, -120.0),
		(-79.0, 14.75, -120.0)],
	hud_color = Color.YELLOW_LIGHT)

save_mesh(
	texture_name = [Texture.ZEBRA_CROSSING],
	tex_coords = compute_uv(bound_number = 923, tile_x = 5.0, tile_y = 5.0, angle_degrees = 0))

################################################################################################################               
################################################################################################################             
#! ======================= CELLS ======================= !#

#TODO: refactor and move later
@dataclass
class CellCenter:
    x: float
    y: float
    z: float
    cell_id: int


def get_cell_type(cell_id: int, polys: List[Polygon]) -> int:  
    for poly in polys:
        if poly.cell_id == cell_id:
            return poly.cell_type
    return Room.DEFAULT


def write_cell_row(cell_id: int, cell_type: int, always_visible_data: str, mesh_a2_files: Set[int]) -> str:       
    model = LevelOfDetail.DRIFT if cell_id in mesh_a2_files else LevelOfDetail.HIGH
    return f"{cell_id},{model},{cell_type}{always_visible_data}\n"


def get_cell_ids(landmark_folder: Path, city_folder: Path) -> Tuple[List[int], Set[int]]:
    meshes_regular = []
    meshes_water_drift = set()

    files = [file for folder in [landmark_folder, city_folder] for file in folder.iterdir()]
    
    for file in files:
        cell_id = int(re.findall(r'\d+', file.name)[0])

        if file.name.endswith(f"_A2{FileType.MESH_lowercase}"):
            meshes_water_drift.add(cell_id)

        if file.name.endswith(FileType.MESH_lowercase):
            meshes_regular.append(cell_id)
            
    return meshes_regular, meshes_water_drift


def calculate_cell_centers(polys: List[Polygon]) -> Dict[int, CellCenter]:
    # print("\nCalculating cell centers...")
    centers = {}
    valid_cell_count = 0
    
    for poly in polys:
        if poly.cell_id > 0:  # Only count non-zero cells
            valid_cell_count += 1
            vertex_positions = [(vertices[i].x, vertices[i].y, vertices[i].z) for i in poly.vertex_index]
            center_x, center_y, center_z = calc_center_coords(vertex_positions)
            
            centers[poly.cell_id] = CellCenter(center_x, center_y, center_z, poly.cell_id)
            # print(f"Cell {poly.cell_id} center: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")
    
    # print(f"Total valid cells (excluding 0): {valid_cell_count}")
    return centers


def calculate_distance(center1: CellCenter, center2: CellCenter) -> float:
    p1 = (center1.x, center1.y, center1.z)
    p2 = (center2.x, center2.y, center2.z)
    return calc_distance(p1, p2)


def get_cell_count_limit(cell_id: int, model: int, cell_type: int) -> int:
    base_line = f"{cell_id},{model},{cell_type},0\n"
    base_length = len(base_line)
    
    # Each additional cell will need: a comma + the number. Assume worst case of 4 digits per cell ID
    chars_per_cell = 4  # comma + 4 digits
    
    remaining_chars = Threshold.CELL_CHARACTER_LIMIT - base_length - 5  # Using actual limit since we handle length proactively
    max_cells = remaining_chars // chars_per_cell
    return max_cells


def get_nearest_cells(cell_id: int, centers: Dict[int, CellCenter], max_cells: int) -> List[int]:
    # (f"\nFinding nearest cells for cell {cell_id}...")
    
    if cell_id not in centers:
        return []
        
    source_center = centers[cell_id]
    
    # Calculate distances to all other cells (excluding 0 and self)
    distances = []
    for target_center in centers.values():
        target_id = target_center.cell_id
        if target_id == cell_id or target_id == 0:  # Skip self and cell 0
            continue
            
        distance = calculate_distance(source_center, target_center)
        distances.append((distance, target_id))
    
    # Sort by distance and take up to max_cells
    distances.sort()  
    nearest = [cell_id for _, cell_id in distances[:max_cells]]
    
    # print(f"Found {len(nearest)} nearest cells")

    # if nearest:
    #     print(f"Distance order: {nearest[:10]}...")
    
    return nearest


def get_cell_visibility_by_distance(cell_id: int, polys: List[Polygon], cell_type: int) -> List[int]:
    centers = calculate_cell_centers(polys)
    max_cells = get_cell_count_limit(cell_id, LevelOfDetail.HIGH, cell_type)
    return get_nearest_cells(cell_id, centers, max_cells)


def create_cells(output_file: Path, polys: List[Polygon]) -> None:
    mesh_files, mesh_a2_files = get_cell_ids(Folder.SHOP_MESH_LANDMARK_MAP, Folder.SHOP_MESH_CITY_MAP)

    with open(output_file, "w") as f:    
        f.write(f"{len(mesh_files)}\n")
        f.write(str(max(mesh_files) + 1000) + "\n")

        for cell_id in sorted(mesh_files):
            cell_type = get_cell_type(cell_id, polys)
            
            # Get visible cells based on distance
            visible_cell_ids = get_cell_visibility_by_distance(cell_id, polys, cell_type)
            visible_count = len(visible_cell_ids)
            
            # Create the visibility data string
            always_visible_data = f",{visible_count}"
            if visible_count > 0:
                always_visible_data += f",{','.join(map(str, visible_cell_ids))}"
            
            # Write the cell row
            model = LevelOfDetail.DRIFT if cell_id in mesh_a2_files else LevelOfDetail.HIGH
            row = write_cell_row(cell_id, cell_type, always_visible_data, mesh_a2_files)
            f.write(row)

    sorted_cells = sorted(mesh_files)
    min_cell = min(sorted_cells) if sorted_cells else 0
    max_cell = max(sorted_cells) if sorted_cells else 0
    cell_ids_str = ", ".join(map(str, sorted_cells))
    
    # Count cell types
    cell_type_counts = {}
    for poly in polys[1:]:  # Skip default
        if poly.cell_id in sorted_cells:
            cell_type = poly.cell_type
            cell_type_counts[cell_type] = cell_type_counts.get(cell_type, 0) + 1

    # Map cell types to readable names
    cell_type_names = {
        Room.DEFAULT: "default",
        Room.TUNNEL: "tunnel", 
        Room.DRIFT: "drift",
        Room.NO_SKIDS: "no_skids"
    }

    type_breakdown = "x, ".join([f"{cell_type_names.get(t, f'type_{t}')}: {count}" 
                               for t, count in sorted(cell_type_counts.items())])
    
    print(f"Successfully created cells file (count: {len(mesh_files)}, min: {min_cell}, max: {max_cell})")
    print(f"---cell IDs: {cell_ids_str}")
    print(f"---cell types: {type_breakdown}")
    
################################################################################################################               
################################################################################################################
#! ======================= MINIMAP ======================= !#

#TODO: refactor and move later
def create_minimap(set_minimap: bool, debug_minimap: bool, debug_minimap_id: bool, 
                  minimap_outline_color: str, line_width: float, background_color: str) -> None:
    
    if not set_minimap or is_process_running(Executable.BLENDER):
        return
    
    global hudmap_vertices
    global hudmap_properties

    min_x, min_z, max_x, max_z = calculate_extrema(hudmap_vertices)

    width = int(max_x - min_x)
    height = int(max_z - min_z) 
    
    def draw_polygon(ax, polygon, minimap_outline_color: str, 
                    label = None, add_label = False, hud_fill = False, hud_color = None) -> None:

        xs, ys = zip(*[(point[0], point[2]) for point in polygon])
        xs, ys = xs + (xs[0],), ys + (ys[0],)  # The commas after [0] should not be removed

        if minimap_outline_color:
            ax.plot(xs, ys, minimap_outline_color, line_width)

        if hud_fill:
            ax.fill(xs, ys, hud_color)

        if add_label: 
            center = calculate_center_tuples(polygon)
            ax.text(center[0], center[2], label, color = "white", ha = "center", va = "center", fontsize = 4.0)   
            
    # Regular Export (320 and 640 versions)
    _, ax = plt.subplots()
    ax.set_facecolor(background_color)

    for i, polygon in enumerate(hudmap_vertices):
        hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))

        draw_polygon(ax, polygon, minimap_outline_color, add_label = False, hud_fill = hud_fill, hud_color = hud_color)

    ax.set_aspect("equal", "box")
    ax.axis("off")

    # Save JPG 640 and 320 Pictures                    
    plt.savefig(Folder.SHOP_TEXTURES_BITMAP / f"{MAP_FILENAME}640.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color)
    plt.savefig(Folder.SHOP_TEXTURES_BITMAP / f"{MAP_FILENAME}320.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color) 

    print(f"Successfully created minimap with {len(hudmap_vertices)} polygon(s)")

    if debug_minimap or set_lars_race_maker:
        _, ax_debug = plt.subplots(figsize = (width, height), dpi = 1)
        ax_debug.set_facecolor("black")

        for i, polygon in enumerate(hudmap_vertices):
            hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))

            draw_polygon(ax_debug, polygon, minimap_outline_color, 
                        label = bound_label if debug_minimap_id else None, 
                        add_label = True, hud_fill = hud_fill, hud_color = hud_color)

        ax_debug.axis("off")
        ax_debug.set_xlim([min_x, max_x])
        ax_debug.set_ylim([max_z, min_z])  # Flip the image vertically
        ax_debug.set_position([0, 0, 1, 1]) 
        plt.savefig(Folder.BASE / f"{MAP_FILENAME}_HUD_debug.jpg", dpi = 1, bbox_inches = None, pad_inches = 0, facecolor = "purple")

        print(f"Successfully created debug minimap with {len(hudmap_vertices)} polygon(s)")
        print(f"Minimap dimensions: Width = {width}, Height = {height}")
                            
################################################################################################################               
################################################################################################################
#! ======================= PORTAL GENERATION ======================= !#

#! ############ Code by 0x1F9F1 (Modified) // start ############ !#   

#TODO: refactor and move later              
MIN_Y = -20
MAX_Y = 50
COLINEAR_FUDGE = 0.00001
MERGE_COLINEAR = True
RADIUS_FUDGE = 1
TANGENT_ANGLE_FUDGE = 0.999
TANGENT_DIST_FUDGE = 0.1
CORNER_FUDGE = 0.1
LENGTH_FUDGE = 1
STRICT_EDGES = False

if MERGE_COLINEAR:
    assert not STRICT_EDGES
    
        
class Edge:
    def __init__(self, v1, v2):
        A = Vector2(v1.y - v2.y, v2.x - v1.x)
        assert A == (v1 - v2).Cross()

        c = A.Dot(v1)
        d = A.Mag2()

        if d > 0.00001:
            line = Vector3(A.x, A.y, -c) * (d ** -0.5)
        else:
            line = Vector3(0, 0, HUGE)

        self.v1 = v1
        self.v2 = v2

        self.line = line

        self.v1p = self.line_pos(self.v1, 0)
        self.v2p = self.line_pos(self.v2, 0)

        assert self.v1p < self.v2p

        self.length = d ** 0.5

        assert abs(self.length - self.v1.Dist(self.v2)) < 0.0001
        delta = self.v1p + self.length - self.v2p
        assert abs(delta) < 0.0001, delta

    # Distance tangential to the line
    def tangent_dist(self, point):
        return (point.x * self.line.x) + (point.y * self.line.y) + self.line.z

    # Distance along the line
    def line_pos(self, point, dist):
        x = point.x + self.line.x * dist
        y = point.y + self.line.y * dist
        return (x * self.line.y) - (y * self.line.x)

    def pos_to_point(self, pos):
        return Vector2(
             (self.line.y * pos) - (self.line.x * self.line.z),
            -(self.line.x * pos) - (self.line.y * self.line.z))
    
    
class Cell:
    def __init__(self, id):
        self.id = id
        self.edges = []

    def add_edge(self, v1, v2):
        # Discard the Y (height) coordinate
        v1 = Vector2(v1.x, v1.z)
        v2 = Vector2(v2.x, v2.z)

        if v1.Dist2(v2) < 0.00001:
            return

        self.edges.append(Edge(v1, v2))

    def merge_colinear(self):
        i = 0

        while i < len(self.edges):
            edge1 = self.edges[i]

            j = i + 1

            while j < len(self.edges):
                edge2 = self.edges[j]
                j += 1

                angle = (edge1.line.x * edge2.line.x) + (edge1.line.y * edge2.line.y)

                if abs(angle) < 0.999:
                    continue

                v1p = edge1.tangent_dist(edge2.v1)
                if abs(v1p) > COLINEAR_FUDGE:
                    continue

                v2p = edge1.tangent_dist(edge2.v2)
                if abs(v2p) > COLINEAR_FUDGE:
                    continue

                v1p = edge1.line_pos(edge2.v1, v1p)
                v2p = edge1.line_pos(edge2.v2, v2p)

                v1p, v2p = min(v1p, v2p), max(v1p, v2p)

                if (v2p < edge1.v1p + CORNER_FUDGE) or (v1p > edge1.v2p - CORNER_FUDGE):
                    continue

                edge1.v1p = min(edge1.v1p, v1p)
                edge1.v2p = max(edge1.v2p, v2p)

                edge1.v1 = edge1.pos_to_point(edge1.v1p)
                edge1.v2 = edge1.pos_to_point(edge1.v2p)

                del self.edges[j - 1]
                j = i + 1

            i += 1

    def process(self):
        if MERGE_COLINEAR:
            self.merge_colinear()

        bb_min = Vector2( HUGE,  HUGE)
        bb_max = Vector2(-HUGE, -HUGE)

        for edge in self.edges:
            for vert in (edge.v1,edge.v2):
                bb_min.x = min(bb_min.x, vert.x)
                bb_min.y = min(bb_min.y, vert.y)

                bb_max.x = max(bb_max.x, vert.x)
                bb_max.y = max(bb_max.y, vert.y)

        self.bb_min = bb_min
        self.bb_max = bb_max
        self.center = (self.bb_min + self.bb_max) * 0.5
        self.radius = (self.bb_min.Dist(self.bb_max) * 0.5)

    def check_radius(self, other, fudge):
        return self.center.Dist2(other.center) < (self.radius + other.radius + fudge) ** 2
    

def prepare_portals(polys: List[Polygon], vertices: List[Vector3]):
    cells = {}

    for poly in polys:
        if poly.cell_id in cells: 
            cell = cells[poly.cell_id]
        else:
            cell = Cell(poly.cell_id)
            cells[poly.cell_id] = cell

        for i in range(poly.num_verts):
            j = (i + 1) % poly.num_verts
            cell.add_edge(vertices[poly.vertex_index[i]], vertices[poly.vertex_index[j]]) 

    for cell in cells.values():
        cell.process()

    portals = set()

    cell_vs_cell = 0
    edge_vs_edge = 0

    for cell1 in cells.values():
        for cell2 in cells.values():
            if cell1.id >= cell2.id:
                continue

            if not cell1.check_radius(cell2, RADIUS_FUDGE):
                continue

            cell_vs_cell += 1

            for edge1 in cell1.edges:
                for edge2 in cell2.edges:
                    edge_vs_edge += 1

                    v1p = edge1.tangent_dist(edge2.v1)
                    if abs(v1p) > TANGENT_DIST_FUDGE:
                        continue

                    v2p = edge1.tangent_dist(edge2.v2)
                    if abs(v2p) > TANGENT_DIST_FUDGE:
                        continue

                    v1p = edge1.line_pos(edge2.v1, v1p)
                    v2p = edge1.line_pos(edge2.v2, v2p)

                    v1p, v2p = min(v1p, v2p), max(v1p, v2p)

                    # Check whether any parts of the two edges are touching
                    if (v2p < edge1.v1p + CORNER_FUDGE) or (v1p > edge1.v2p - CORNER_FUDGE):
                        continue

                    if STRICT_EDGES:
                        # Check whether these two edges match
                        if (abs((v1p - edge1.v1p)) > CORNER_FUDGE) or (abs(v2p - edge1.v2p) > CORNER_FUDGE):
                            continue
                    else:
                        if (v2p - v1p) < LENGTH_FUDGE:
                            continue
                        pass

                    v1p = max(edge1.v1p, v1p)
                    v2p = min(edge1.v2p, v2p)

                    assert v1p < v2p

                    # TODO: Preserve y-height
                    p1 = edge1.pos_to_point(v1p)
                    p2 = edge1.pos_to_point(v2p)

                    portals.add((cell1.id, cell2.id, p1, p2))
                    
    return cells, portals

#! ############ Code by 0x1F9F1 (Modified) // end ############ !# 

class Portals:
    def __init__(self, flags: int, edge_count: int, gap_2: int, cell_1: int, cell_2: int, height: float, 
                 _min: Vector3, _max: Vector3, vertex_c: Vector3 = None) -> None:
        
        self.flags = flags
        self.edge_count = edge_count
        self.gap_2 = gap_2
        self.cell_1 = cell_1
        self.cell_2 = cell_2
        self.height = height
        self._min = _min 
        self._max = _max
        self.vertex_c = vertex_c
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        magic = read_binary_name(f, calc_size('<I'))
        count, = read_unpack(f, '<I')
        return count
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'Portals':
        flags, edge_count, = read_unpack(f, '<2B')
        gap_2, = read_unpack(f, '<H')
        cell_1, cell_2, = read_unpack(f, '<2H')  
        height, = read_unpack(f, '<f')   
        _min = Vector3.read(f, '<')
        _max = Vector3.read(f, '<')
        
        vertex_c = None
        if edge_count == Shape.TRIANGLE:
            vertex_c = Vector3.read(f, '<')

        return cls(flags, edge_count, gap_2, cell_1, cell_2, height, _min, _max, vertex_c)
        
    @classmethod
    def read_all(cls, f: BinaryIO) -> 'List[Portals]':
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, portals: 'List[Portals]') -> None:
        write_pack(f, '<I', Magic.PORTAL) 
        write_pack(f, '<I', len(portals))
                
    @classmethod
    def write_all(cls, output_file: Path,
                  polys: List[Polygon], vertices: List[Vector3], 
                  lower_portals: bool, empty_portals: bool, debug_portals: bool) -> None:    
            
        with open(output_file, "wb") as f:
            if empty_portals:
                pass
            
            else:
                _, portal_tuples = prepare_portals(polys, vertices)
                
                portals = []
                
                cls.write_n(f, portal_tuples)

                for cell_1, cell_2, v1, v2 in portal_tuples:
                    flags = Portal.ACTIVE
                    edge_count = Shape.LINE
                    gap_2 = Default.GAP_2
                    height = MAX_Y - MIN_Y
                    _min = Vector3(v1.x, -50 if lower_portals else 0, v1.y)
                    _max = Vector3(v2.x, -50 if lower_portals else 0, v2.y)

                    portal = Portals(flags, edge_count, gap_2, cell_1, cell_2, height, _min, _max)
                    portals.append(portal)
                    
                    write_pack(f, '<2B', flags, edge_count)
                    write_pack(f, '<H', gap_2)
                    write_pack(f, '<2H', cell_2, cell_1)
                    write_pack(f, '<f', height)
                    _min.write(f, '<')
                    _max.write(f, '<')
                    
                print(f"Successfully created {len(portal_tuples)} portal(s)")
                cls.debug(portals, debug_portals, Folder.DEBUG / "PORTALS" / f"{MAP_FILENAME}_PTL.txt")            

    @classmethod
    def debug(cls, portals: 'List[Portals]', debug_portals: bool, output_file: Path) -> None:
        Debug.internal_list(portals, debug_portals, output_file)
                            
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_portals_file: bool) -> None:
        if not debug_portals_file:
            return
        
        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, "rb") as in_f:
            portals = cls.read_all(in_f)

        if not portals:
            print(f"No portals found in {input_file.name}")
            return

        with open(output_file, "w") as out_f:
            for portal in portals:
                out_f.write(repr(portal))

        print(f"Processed {input_file.name} to {output_file.name}")
            
    def __repr__(self):
            return f"""
PORTAL
    Flags: {self.flags}
    EdgeCount: {self.edge_count}
    Gap 2: {self.gap_2}
    Cell 1: {self.cell_1}
    Cell 2: {self.cell_2}
    Height: {self.height:.2f}
    Min: {self._min}
    Max: {self._max}
    {'Vertex C ' + str(self.vertex_c) if self.vertex_c is not None else ''}
    """
 
################################################################################################################               
###############################################################################################################
#! ======================= LARS RACE MAKER ======================= !#


#TODO: refactor and move later
def get_first_and_last_street_vertices(street_list):
    processed_vertices = []
    
    for street in street_list:
        vertices = street["vertices"]
        if vertices: 
            for vertex in (vertices[0], vertices[-1]):
                processed = [vertex[0], vertex[1], vertex[2], Rotation.AUTO, Width.LARGE, 0.0, 0.0, 0.0, 0.0]
                processed_vertices.append(processed)  


    vertices_set = set(tuple(v) for v in processed_vertices)
    unique_processed_vertices = [list(v) for v in vertices_set]
    
    return unique_processed_vertices


#! ############ Code by Lars (Modified) // start ############ !# 

def create_lars_race_maker(output_file: Path, street_list, hudmap_vertices: List[Vector3], set_lars_race_maker: bool) -> None:  
    if not set_lars_race_maker:
        return

    min_x, max_x, min_z, max_z = calculate_extrema(hudmap_vertices)
    
    canvas_width = int(max_x - min_x)
    canvas_height = int(max_z - min_z)

    vertices_processed = get_first_and_last_street_vertices(street_list)
    vertices_string = ",\n".join([str(coord) for coord in vertices_processed])

    template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: #2b2b2b;
        }}
        #myCanvas {{
            background-color: #2b2b2b;
        }}
        #out {{
            color: white;
        }}
    </style>
</head>
<body>
    <img id = "scream" width = "{canvas_width}" height = "{canvas_height}" src = "{MAP_FILENAME}_HUD_debug.jpg" alt = "The Scream" style = "display:none;">
    <canvas id = "myCanvas" width = "{canvas_width}" height = "{canvas_height}" style = "background-color: #2b2b2b;">
        Your browser does not support the HTML5 canvas tag.
    </canvas>
    <div id="out"></div>

    <script>
    var MIN_X = {min_x};
    var MAX_X = {max_x};
    var MIN_Z = {min_z};
    var MAX_Z = {max_z};
    var coords = [{vertices_string}];

    function mapRange(value, in_min, in_max, out_min, out_max) {{
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
    }}

    window.onload = function() {{
        var canvas = document.getElementById("myCanvas");
        var ctx = canvas.getContext("2d");
        var img = document.getElementById("scream");
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        for (var i = 0; i < coords.length; i++) {{
            ctx.lineWidth = "10";
            ctx.strokeStyle = "blue";
            ctx.beginPath();
            let mappedX = mapRange(coords[i][0], MIN_X, MAX_X, 0, canvas.width);
            let mappedZ = mapRange(coords[i][2], MIN_Z, MAX_Z, 0, canvas.height);
            ctx.arc(mappedX, mappedZ, 5, 0, 2 * Math.PI);
            ctx.fill();
        }}
    }};

    let last = null;
    function getCursorPosition(canvas, event) {{
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        console.log("x: " + x + " y: " + y);
        let closest = [-1, 10000000000];
        for (var i = 0; i < coords.length; i++) {{
            let mappedX = mapRange(coords[i][0], MIN_X, MAX_X, 0, canvas.width);
            let mappedZ = mapRange(coords[i][2], MIN_Z, MAX_Z, 0, canvas.height);

            let dist = (x - mappedX)**2 + (y - mappedZ)**2;
            if (closest[1] > dist) {{
                closest = [i, dist];
            }}
        }}
        if (closest[1] < 500) {{
            document.getElementById("out").innerHTML += coords[closest[0]].join(',');
            document.getElementById("out").innerHTML += '<br/>';
            if (last) {{
                var canvas = document.getElementById("myCanvas");
                var ctx = canvas.getContext("2d");
                ctx.lineWidth = "5";
                ctx.strokeStyle = "blue";
                ctx.beginPath();
                ctx.moveTo(last[0], last[1]);
                ctx.lineTo(x, y);
                ctx.stroke();
            }}
            last = [x,y];
        }}
    }}

    const canvas = document.getElementById('myCanvas');
    canvas.addEventListener('mousedown', function(e) {{
        getCursorPosition(canvas, e);
    }});
    </script>
</body>
</html>
    """

    with open(output_file, "w") as f:
        f.write(template)

#! ################# Code by Lars (Modified) // end ################# !# 

###################################################################################################################
###################################################################################################################  

#! Do not delete or change this Street
cruise_start = {
    "street_name": "cruise_start",
    "vertices": [
    (0, 0, 0), 
    cruise_start_position
    ]
}     

street_list = street_list + [cruise_start]

###################################################################################################################
#! ======================= CALL FUNCTIONS ======================= !#

# Setup
copy_custom_textures_to_shop(Folder.USER_TEXTURES_CUSTOM, Folder.SHOP_TEXTURES_OPAQUE)
copy_carsim_files_to_shop(Folder.RESOURCES_EDITOR / "TUNE" / "MMCARSIM", Folder.SHOP_TUNE, FileType.CAR_SIMULATION)
ensure_empty_mm_dev_folder(Folder.MIDTOWNMADNESS_DEV_CITY_MAP) 
create_commandline(Folder.MIDTOWNMADNESS / f"commandline{FileType.TEXT}", no_ui, no_ui_type, no_ai, set_music, less_logs, more_logs)
create_map_info(Folder.SHOP_TUNE / f"{MAP_FILENAME}{FileType.CITY_INFO}", blitz_race_names, circuit_race_names, checkpoint_race_names)

edit_and_copy_bangerdata_to_shop(prop_properties, Folder.RESOURCES_EDITOR / "TUNE" / "MMBANGERDATA", Folder.SHOP_TUNE, FileType.BANGER_DATA)

# Races
create_races(race_data)
create_cops_and_robbers(Folder.SHOP_RACE_MAP / f"COPSWAYPOINTS{FileType.CSV}", cops_and_robbers_waypoints)

# Map
check_bound_numbers(polys)

total_polys = len(polys) - 1  # Exclude default polygon at index 0
quads = sum(1 for poly in polys[1:] if poly.is_quad)
triangles = total_polys - quads
print(f"Successfully created {total_polys} polygon(s) (triangles: {triangles}x, quads: {quads}x, vertices: {len(vertices)}x)")

# Texture usage statistics
texture_counter = Counter(texture_names)
unique_textures = len(texture_counter)
all_textures_str = ", ".join([f"{tex}: {count}x" for tex, count in texture_counter.items()])
print(f"Succesfully utilized: {unique_textures} unique texture(s)\n---textures: ({all_textures_str})")

create_cells(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.CELL}", polys)
Bounds.create(Folder.SHOP_BOUND / f"{MAP_FILENAME}_HITID{FileType.BOUND}", vertices, polys, Folder.DEBUG / "BOUNDS" / f"{MAP_FILENAME}{FileType.TEXT}", debug_bounds)
Portals.write_all(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.PORTAL}", polys, vertices, lower_portals, empty_portals, debug_portals)
aiStreetEditor.create(street_list, set_ai_streets, set_reverse_ai_streets)
FacadeEditor.create(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.FACADE}", facade_list, set_facades, debug_facades)
PhysicsEditor.edit(Folder.RESOURCES_EDITOR / "PHYSICS" / f"PHYSICS{FileType.DATABASE}", Folder.SHOP_MATERIAL / f"PHYSICS{FileType.DATABASE}", custom_physics, set_physics, debug_physics)

TextureSheet.append_custom_textures(Folder.RESOURCES_EDITOR / "MTL" / "GLOBAL.TSH", Folder.USER_TEXTURES_CUSTOM, Folder.SHOP / "MTL" / "TEMP_GLOBAL.TSH", set_texture_sheet)
TextureSheet.write_tweaked(Folder.SHOP_MATERIAL / "TEMP_GLOBAL.TSH", Folder.SHOP_MATERIAL / "GLOBAL.TSH", texture_modifications, set_texture_sheet)
                    
prop_editor = BangerEditor()
for prop in random_props:
    prop_list.extend(prop_editor.place_randomly(**prop))
prop_editor.process_all(prop_list, set_props)

lighting_instances = LightingEditor.read_file(Folder.RESOURCES_EDITOR / "LIGHTING" / "LIGHTING.CSV")
LightingEditor.write_file(lighting_instances, lighting_configs, Folder.SHOP_TUNE / "LIGHTING.CSV")
LightingEditor.debug(lighting_instances, Folder.DEBUG / "LIGHTING" / "LIGHTING_DATA.txt", debug_lighting)

create_extrema(f"{Folder.SHOP_CITY_MAP}{FileType.EXTREMA}", hudmap_vertices)
create_animations(Folder.SHOP_CITY_MAP, animations_data, set_animations)   
create_bridges(bridge_list, set_bridges, f"{Folder.SHOP_CITY_MAP}{FileType.GIZMO}") 
create_bridge_config(bridge_config_list, set_bridges, Folder.SHOP_TUNE)
create_minimap(set_minimap, debug_minimap, debug_minimap_id, minimap_outline_color, line_width = 0.7, background_color = "black")
create_lars_race_maker(f"Lars_Race_Maker{FileType.HTML}", street_list, hudmap_vertices, set_lars_race_maker)

# Misc
DLP(Magic.DEVELOPMENT, len(dlp_groups), len(dlp_patches), len(dlp_vertices), dlp_groups, dlp_patches, dlp_vertices).write(f"TEST{FileType.DEVELOPMENT}", set_dlp) 

editor = BangerEditor()

# File / Folder Debugging
DLP.debug_file(debug_dlp_data_file, Folder.DEBUG / "DLP" / debug_dlp_data_file.with_suffix(FileType.TEXT), debug_dlp_file)
Bounds.debug_file(debug_bounds_data_file, Folder.DEBUG / "BOUNDS" / debug_bounds_data_file.with_suffix(FileType.TEXT), debug_bounds_file)
Bangers.debug_file(debug_props_data_file, Folder.DEBUG / "PROPS" / debug_props_data_file.with_suffix(FileType.TEXT), debug_props_file)
Facades.debug_file(debug_facades_data_file, Folder.DEBUG / "FACADES" / debug_facades_data_file.with_suffix(FileType.TEXT), debug_facades_file)
Portals.debug_file(debug_portals_data_file, Folder.DEBUG / "PORTALS" / debug_portals_data_file.with_suffix(FileType.TEXT), debug_portals_file)
Meshes.debug_file(debug_meshes_data_file, Folder.DEBUG / "MESHES" / debug_meshes_data_file.with_suffix(FileType.TEXT), debug_meshes_file)
DLP.debug_file(debug_dlp_data_file, Folder.DEBUG / "DLP" / debug_dlp_data_file.with_suffix(FileType.TEXT), debug_dlp_file)

Bangers.debug_file_to_csv(debug_props_data_file, Folder.DEBUG / "PROPS" / debug_props_data_file.with_suffix(FileType.CSV), debug_props_file_to_csv)
Meshes.debug_folder(debug_meshes_data_folder, Folder.DEBUG / "MESHES" / "MESH TEXT FILES", debug_meshes_folder) 
Bounds.debug_folder(debug_bounds_data_folder, Folder.DEBUG / "BOUNDS" / "BND TEXT FILES", debug_bounds_folder)
DLP.debug_folder(debug_dlp_data_folder, Folder.DEBUG / "DLP" / "DLP TEXT FILES", debug_dlp_folder)

debug_ai(
    debug_ai_data_file, debug_ai_file,
    Folder.RESOURCES_USER / "AI" / "CHICAGO.map",                                  
    str(Path(Folder.RESOURCES_USER) / "AI" / "Intersection{intersection_id}.int"),
    str(Path(Folder.RESOURCES_USER) / "AI" / "Street{paths}.road")
    )

# Finalizing Part
create_angel_resource_file(Folder.SHOP)

end_time = time.monotonic()
editor_time = end_time - start_time

# Save the runtime
runtime_manager = RunTimeManager(Folder.RESOURCES_EDITOR / EDITOR_RUNTIME_FILE)
runtime_manager.save(editor_time)
progress_thread.join()  # Wait for progress bar to complete

print(COLOR_DIVIDER)
print(Fore.LIGHTCYAN_EX + "   Successfully created " + Fore.LIGHTYELLOW_EX + f"{MAP_NAME}!" + Fore.MAGENTA + f" (in {editor_time:.4f} s)" + Fore.RESET)
print(COLOR_DIVIDER)

post_editor_cleanup(Folder.BUILD, Folder.SHOP, delete_shop)

if subtract_props:
    shutil.copy(subtract_input_props_file, subtract_output_props_file) 
    subtract_props_from_file(
        input_file=subtract_input_props_file,
        output_file=subtract_output_props_file,
        exact_rules=props_to_subtract,
        range_rules=ranges_to_subtract,
        tolerance=subtract_tolerance,
        require_confirmation=subtract_require_confirmation
    )

if append_props:
    shutil.copy(append_input_props_file, append_output_props_file)
    editor.append_to_file(
        append_output_props_file,
        props_to_append,
        append_output_props_file,
        append_props
    )

if edit_props:
    shutil.copy(edit_input_props_file, edit_output_props_file)
    from src.file_formats.props.edit import edit_props_in_file
    edit_props_in_file(
        input_file=edit_input_props_file,
        output_file=edit_output_props_file,
        edit_rules=props_to_edit,
        tolerance=edit_tolerance,
        require_confirmation=edit_require_confirmation
    )

if replace_props:
    shutil.copy(replace_input_props_file, replace_output_props_file)
    from src.file_formats.props.replace import replace_props_in_file
    replace_props_in_file(
        input_file=replace_input_props_file,
        output_file=replace_output_props_file,
        replace_rules=props_to_replace,
        tolerance=replace_tolerance,
        require_confirmation=replace_require_confirmation
    )

if duplicate_props:
    shutil.copy(duplicate_input_props_file, duplicate_output_props_file)
    from src.file_formats.props.copy import duplicate_props_in_file
    duplicate_props_in_file(
        input_file=duplicate_input_props_file,
        output_file=duplicate_output_props_file,
        duplicate_rules=props_to_duplicate,
        tolerance=duplicate_tolerance
    )

start_game(Folder.MIDTOWNMADNESS, Executable.MIDTOWN_MADNESS, play_game)

# Blender
setup_blender()

initialize_blender_panels()
initialize_blender_operators()
initialize_blender_waypoint_editor()
set_blender_keybinding()

create_blender_meshes(Folder.RESOURCES_EDITOR / "TEXTURES", load_all_texures)

process_and_visualize_paths(Folder.SHOP / "dev" / "CITY" / MAP_FILENAME, f"AI_PATHS{FileType.TEXT}", visualize_ai_paths)

###################################################################################################################   
################################################################################################################### 
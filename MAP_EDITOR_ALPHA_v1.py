
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


# Core Python path setup
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
# Standard library imports
import re
import csv
import math
import time
import psutil
import shutil
import random
import datetime
import textwrap
import subprocess
from itertools import cycle
from dataclasses import dataclass
from typing import List, Dict, Set, Any, Union, Tuple, Optional, BinaryIO, Sequence

# Third-party imports
import bpy
import pyautogui
import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore

# Map Editor Components
from src.Vector.vector_2 import Vector2
from src.Vector.vector_3 import Vector3
from src.Vector.vector_4 import Vector4

from src.IO.binary_parsing import read_unpack, write_pack, read_binary_name, write_binary_name, calc_size

from src.Debug.main import Debug

from src.Constants.configs import BRIDGE_CONFIG_DEFAULT, ORIENTATION_MAPPINGS, TEXTURESHEET_MAPPING
from src.Constants.textures import Texture, TEXTURE_EXPORT
from src.Constants.props import Prop
from src.Constants.misc import Shape, Encoding, Executable, Default, Folder, Threshold, Color, CommandArgs
from src.Constants.file_types import Portal, Material, Room, LevelOfDetail, agiMeshSet, PlaneEdgesWinding, Magic, FileType
from src.Constants.races import IntersectionType, RaceMode, NetworkMode, CnR, Rotation, Width
from src.Constants.progress_bar import EDITOR_RUNTIME_FILE, COLOR_DIVIDER
from src.Constants.constants import *

from src.Races.main import create_races
from src.Races.cops_and_robbers import create_cops_and_robbers

from src.Geometry.utils import calculate_extrema

from src.ProgressBar.main import RunTimeManager, start_progress_tracking

from src.Blender.setup import delete_existing_meshes, enable_developer_extras, enable_vertex_snapping, adjust_3D_view_settings
from src.Blender.handlers import initialize_depsgraph_update_handler
from src.Blender.Operators.process_extrude import OBJECT_OT_ProcessPostExtrude
from src.Blender.Operators.rename_polygons import OBJECT_OT_RenameChildren, OBJECT_OT_RenameSequential

from src.FileFormats.dlp import DLP
from src.FileFormats.ext import create_ext
from src.FileFormats.animations import create_animations

# Map Settings
from src.User.Settings.main import *
from src.User.Settings.advanced import *
from src.User.Settings.debug import *
from src.User.Settings.blender import load_all_texures, visualize_ai_paths, input_waypoint_file, waypoint_number_input, waypoint_type_input

from src.User.Props.props import random_props, prop_list
from src.User.Props.properties import prop_properties
from src.User.Props.append_to_file import append_props, props_to_append, append_input_props_file, append_output_props_file

from src.User.Races.races import race_data, blitz_race_names, circuit_race_names, checkpoint_race_names
from src.User.Races.cops_and_robbers import cops_and_robbers_waypoints

from src.User.Textures.properties import texture_modifications

from src.User.Misc.dlp import dlp_groups, dlp_patches, dlp_vertices

from src.User.ai_streets import street_list
from src.User.animations import animations_data
from src.User.bridges import bridge_list, bridge_config_list
from src.User.physics import custom_physics
from src.User.facades import facade_list
from src.User.lighting import lighting_configs

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
#! ======================= COMMON HELPER FUNCTIONS ======================= !#


def calculate_center_tuples(vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    return (sum((Vector3.from_tuple(vertex) for vertex in vertices), Vector3(0, 0, 0)) / len(vertices)).to_tuple()


def sort_coordinates(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    max_x_coord = max(vertex_coordinates, key = lambda coord: coord[0])
    min_x_coord = min(vertex_coordinates, key = lambda coord: coord[0])
    
    max_z_for_max_x = max([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_max_x = min([coord for coord in vertex_coordinates if coord[0] == max_x_coord[0]], key = lambda coord: coord[2])
    max_z_for_min_x = max([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])
    min_z_for_min_x = min([coord for coord in vertex_coordinates if coord[0] == min_x_coord[0]], key = lambda coord: coord[2])

    return [max_z_for_max_x, min_z_for_max_x, min_z_for_min_x, max_z_for_min_x]


def calc_center_coords(points: Sequence[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    if not points:
        raise ValueError("Empty sequence of points")
    xs, ys, zs = zip(*points)
    n = len(points)
    return sum(xs) / n, sum(ys) / n, sum(zs) / n


def calc_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    return (dx * dx + dy * dy + dz * dz) ** 0.5

################################################################################################################ 

def transform_coordinate_system(vertex: Vector3, blender_to_game: bool = False, game_to_blender: bool = False) -> Tuple[float, float, float]:
    if blender_to_game and game_to_blender:
        raise ValueError("\nBoth transformation modes cannot be 'True' at the same time.\n")
 
    elif blender_to_game:
        x, y, z = vertex.x, vertex.z, -vertex.y
        
    elif game_to_blender:
        x, y, z = vertex.x, -vertex.z, vertex.y
        
    else:
        raise ValueError("\nOne of the transformation modes must be 'True'.\n")
    
    return x, y, z


def open_with_notepad_plus(input_file: Path) -> None:
    notepad_plus_exe = shutil.which(Executable.NOTEPAD_PLUS_PLUS)  
    
    if notepad_plus_exe:
        subprocess.Popen([notepad_plus_exe, input_file])
        print("Opening file with Notepad++ from PATH.")
        return

    for path in NOTEPAD_PLUS_PATHS:
        subprocess.Popen([path, input_file])
        print(f"Opening file with Notepad++ from hardcoded path: {path}")
        return

    try:
        subprocess.Popen([Executable.NOTEPAD, input_file])
        print("Notepad++ not found, opening file with Classic Notepad.")
    except FileNotFoundError:
        print("Neither Notepad++ nor Classic Notepad found. Unable to open file.")
        raise

################################################################################################################ 
################################################################################################################               
#! ======================= CREATE MESH ======================= !#


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
        target_folder = Folder.SHOP_MESH_LANDMARK
    else:
        target_folder = Folder.SHOP_MESH_CITY
                
    target_folder.mkdir(parents = True, exist_ok = True)
        
    if any(name.startswith(Texture.WATER) for name in texture_name):
        mesh_filename = f"CULL{cell_id:02d}_A2{FileType._MESH}"
    else:
        mesh_filename = f"CULL{cell_id:02d}_H{FileType._MESH}"

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
        mesh.debug(Path(mesh_filename).with_suffix({FileType.TEXT}), Folder.DEBUG_RESOURCES / "MESHES" / MAP_FILENAME, debug_meshes)


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
#! ======================= ADVANCED VECTOR CALCULATIONS ======================= !#


def ensure_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    vertex_1, vertex_2, vertex_3 = vertex_coordinates
    
    normal = compute_normal(vertex_1, vertex_2, vertex_3)
    reference_up = np.array([0, 1, 0])
    
    dot_product = np.dot(normal, reference_up)
    
    if dot_product < 0: # Clockwise --> swap the order of the vertices
        return [vertex_1, vertex_3, vertex_2]
    else:               # Counterclockwise --> no changes needed
        return [vertex_1, vertex_2, vertex_3]
    
    
def compute_normal(vertex_1: Vector3, vertex_2: Vector3, vertex_3: Vector3) -> np.ndarray:
    v1 = np.array(vertex_2) - np.array(vertex_1)
    v2 = np.array(vertex_3) - np.array(vertex_1)
    normal = np.cross(v1, v2)
    return normal / np.linalg.norm(normal)


def ensure_quad_ccw_order(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    normal = compute_normal(*vertex_coordinates[:3])
    
    # Use Gram-Schmidt process to get two orthogonal vectors on the plane
    basis_1 = np.array(vertex_coordinates[1]) - np.array(vertex_coordinates[0])
    basis_1 -= np.dot(basis_1, normal) * normal
    basis_1 /= np.linalg.norm(basis_1)
    basis_2 = np.cross(normal, basis_1)

    # Project vertices onto the plane defined by the normal
    projections = [
        (np.dot(vertex, basis_1), np.dot(vertex, basis_2))
        for vertex in vertex_coordinates
        ]

    # Compute the centroid of the projected points
    centroid = np.mean(projections, axis = 0)
    
    # Compute angles of vertices relative to centroid
    delta = np.array(projections) - centroid
    angles = np.arctan2(delta[:, 1], delta[:, 0])
    
    # Sort vertices based on these angles
    sorted_indices = np.argsort(angles)
    
    return [vertex_coordinates[i] for i in sorted_indices]


def compute_plane_edgenormals(vertex_1: Vector3, vertex_2: Vector3, vertex_3: Vector3):     
    plane_normal = compute_normal(vertex_1, vertex_2, vertex_3)
    
    plane_distance = -np.dot(plane_normal, vertex_1)

    plane_normal = np.round(plane_normal, 3)
    plane_distance = round(plane_distance, 3)

    return plane_normal, plane_distance


def compute_edges(vertex_coordinates: List[Vector3]) -> List[Vector3]:
    vertices = [np.array([vertex[0], 0, vertex[2]]) for vertex in vertex_coordinates]
    plane_normal, _ = compute_plane_edgenormals(*vertices[:3]) 

    num_verts = len(vertices)  
        
    plane_edges = []

    abs_plane_x = abs(plane_normal[0])
    abs_plane_y = abs(plane_normal[1])
    abs_plane_z = abs(plane_normal[2])

    negate = 1.0

    # TODO: Refactor
    if abs_plane_x < abs_plane_y or abs_plane_x < abs_plane_z:
        if abs_plane_y < abs_plane_x or abs_plane_y < abs_plane_z:
            if plane_normal[2] < 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[1] * negate, D[0] * negate, -np.dot([-D[1], D[0]], [A[0], A[1]])]))
        else:
            if plane_normal[1] > 0.0:
                negate = -1.0
            for i in range(num_verts):
                A = vertices[i]
                B = vertices[(i+1) % num_verts]
                D = B - A
                plane_edges.append(np.array([-D[2] * negate, D[0] * negate, -np.dot([-D[2], D[0]], [A[0], A[2]])]))
    else:
        if plane_normal[0] < 0.0:
            negate = -1.0
        for i in range(num_verts):
            A = vertices[i]
            B = vertices[(i+1) % num_verts]
            D = B - A
            plane_edges.append(np.array([-D[2] * negate, D[1] * negate, -np.dot([-D[2], D[1]], [A[1], A[2]])]))

    # Normalize edges
    for i in range(len(plane_edges)):
        norm_val = np.linalg.norm(plane_edges[i][:2])  # Only first two components
        plane_edges[i][:2] /= norm_val
        plane_edges[i][2] /= norm_val
        
    edges = [Vector3(edge[0], edge[1], edge[2]) for edge in plane_edges]
    
    # All shapes must always have 4 vectors
    if len(vertices) == Shape.TRIANGLE:
        edges.append(Default.VECTOR_3)
    
    return edges

################################################################################################################               
################################################################################################################ 
#! ======================= CREATE POLYGON ======================= !#


def check_bound_numbers(polys: List[Polygon]) -> None:
    found_one = False
    
    for poly in polys[1:]:  # Skip the filler Polygon with Bound Number 0 
        if poly.cell_id <= 0 or poly.cell_id == Threshold.CELL_TYPE_SWITCH or poly.cell_id >= Threshold.VERTEX_INDEX_COUNT:
            error_message = f"""
            ***ERROR***
            - Polygon with "bound_number =  {poly.cell_id}" is not valid. 
            - Bound Number must be between 1 and 199, and 201 and 32766.
            """
            raise ValueError(error_message)
        
        if poly.cell_id == 1:
            found_one = True

    if not found_one:
        error_message = f"""
        ***ERROR***
        - There must be at least one Polygon with Bound Number 1 (this was not found).
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
#! ======================= SETUP PREPARATION ======================= !#


def create_folders() -> None:
    FOLDER_STRUCTURE = [
        Folder.BASE / "build", 
        Folder.SHOP / "BMP16", 
        Folder.SHOP / "TEX16O", 
        Folder.SHOP / "TUNE", 
        Folder.SHOP / "MTL",
        Folder.SHOP / "CITY" / MAP_FILENAME,
        Folder.SHOP / "RACE" / MAP_FILENAME,
        Folder.SHOP / "BMS" / f"{MAP_FILENAME}CITY",
        Folder.SHOP / "BMS" / f"{MAP_FILENAME}LM",
        Folder.SHOP / "BND" / f"{MAP_FILENAME}CITY",
        Folder.SHOP / "BND" / f"{MAP_FILENAME}LM",
        Folder.MIDTOWNMADNESS / "dev" / "CITY" / MAP_FILENAME,
        ]
    
    for path in FOLDER_STRUCTURE:
        path.mkdir(parents = True, exist_ok = True)

        
def create_map_info(output_file: Path, blitz_race_names: List[str], circuit_race_names: List[str], checkpoint_race_names: List[str]) -> None:
    with open (output_file, "w") as f:
        
        # Removed 'lower()' for 'RaceDir'
        f.write(f"""
LocalizedName={MAP_NAME}
MapName={MAP_FILENAME}
RaceDir={MAP_FILENAME}
BlitzCount={len(blitz_race_names)}
CircuitCount={len(circuit_race_names)}
CheckpointCount={len(circuit_race_names)}
BlitzNames={'|'.join(blitz_race_names)}
CircuitNames={'|'.join(circuit_race_names)}
CheckpointNames={'|'.join(checkpoint_race_names)}
""")


def copy_files_to_folder (input_folder: Path, output_folder: Path, pattern: str = "*") -> None:
    for file in input_folder.glob(pattern):
        if file.is_file():
            shutil.copy(file, output_folder / file.name)


def copy_custom_textures_to_shop(input_folder: Path, output_folder: Path) -> None:
    copy_files_to_folder (input_folder, output_folder)


def copy_carsim_files_to_shop(input_folder: Path, output_folder: Path, file_type: str) -> None:
    copy_files_to_folder(input_folder, output_folder, f"*{file_type}")


def ensure_empty_mm_dev_folder(input_folder: Path) -> None:
    if input_folder.is_dir():
        for file in input_folder.iterdir():
            if file.is_file():
                file.unlink()
    else:
        input_folder.mkdir(parents=True, exist_ok=True)

################################################################################################################               
################################################################################################################             
#! ======================= CELLS ======================= !#


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

        if file.name.endswith(f"_A2{FileType._MESH}"):
            meshes_water_drift.add(cell_id)

        if file.name.endswith(FileType._MESH):
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
    if nearest:
        print(f"Distance order: {nearest[:10]}...")
    
    return nearest


def get_cell_visibility_by_distance(cell_id: int, polys: List[Polygon], cell_type: int) -> List[int]:
    centers = calculate_cell_centers(polys)
    max_cells = get_cell_count_limit(cell_id, LevelOfDetail.HIGH, cell_type)
    return get_nearest_cells(cell_id, centers, max_cells)


def create_cells(output_file: Path, polys: List[Polygon]) -> None:
    mesh_files, mesh_a2_files = get_cell_ids(Folder.SHOP_MESH_LANDMARK, Folder.SHOP_MESH_CITY)

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

################################################################################################################               
################################################################################################################
#! ======================= MINIMAP ======================= !#


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
            ax.text(center[0], center[2], label, color = "white", 
                    ha = "center", va = "center", fontsize = 4.0)   
            
    # Regular Export (320 and 640 versions)
    _, ax = plt.subplots()
    ax.set_facecolor(background_color)

    for i, polygon in enumerate(hudmap_vertices):
        hud_fill, hud_color, _, bound_label = hudmap_properties.get(i, (False, None, None, None))

        draw_polygon(ax, polygon, minimap_outline_color, 
                     add_label = False, hud_fill = hud_fill, hud_color = hud_color)

    ax.set_aspect("equal", "box")
    ax.axis("off")

    # Save JPG 640 and 320 Pictures                    
    plt.savefig(Folder.SHOP / "BMP16" / f"{MAP_FILENAME}640.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color)
    plt.savefig(Folder.SHOP / "BMP16" / f"{MAP_FILENAME}320.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color) 

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
                            
################################################################################################################               
################################################################################################################
#! ======================= BRIDGES ======================= !#  
                               
def create_bridges(all_bridges, set_bridges: bool, output_file: Path):
    if not set_bridges:
        return
        
    if output_file.exists():
        os.remove(output_file)
    
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
         
        orientation_error = f"""
        ***ERROR***
        Invalid Bridge Orientation.
        Please choose from one of the following: NORTH, SOUTH, EAST, WEST,
        NORTH_EAST, NORTH_WEST, SOUTH_EAST, SOUTH_WEST or set the orientation
        using a numeric value between 0 and 360 degrees.
        """
        raise ValueError(orientation_error)
        
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

    for bridge in all_bridges:
        offset, orientation, id, drawbridge, bridge_attributes = bridge

        face = calculate_facing(offset, orientation)
        drawbridge_values = f"{drawbridge},0,{','.join(map(str, offset))},{','.join(map(str, face))}"
        attributes = generate_attribute_lines(bridge_attributes)

        num_fillers = 5 - len(bridge_attributes)        
        fillers = BRIDGE_ATTRIBUTE_FILLER * num_fillers

        template = (  # Do not change
            f"DrawBridge{id}\n"
            f"\t{drawbridge_values}\n"
            f"{attributes}"
            f"{fillers}"
            f"DrawBridge{id}\n"  
            )
        
        bridge_data.append(template)

    with open(output_file, "a") as f:
        f.writelines(bridge_data)


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
    template = """
    mmBridgeMgr :076850a0 {{
        BridgeDelta {BridgeDelta}
        BridgeOffGoal {BridgeOffGoal}
        BridgeOnGoal {BridgeOnGoal}
        GateDelta {GateDelta}
        GateOffGoal {GateOffGoal}
        GateOnGoal {GateOnGoal}
        BridgeOnDelay {BridgeOnDelay}
        GateOffDelay {GateOffDelay}
        BridgeOffDelay {BridgeOffDelay}
        GateOnDelay {GateOnDelay}
    }}
    """
    return template.format(**config)


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

################################################################################################################               
################################################################################################################
#! ======================= PORTAL GENERATION ======================= !#

#! ############ Code by 0x1F9F1 (Modified) // start ############ !#   

                 
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

################################################################################################################               
################################################################################################################
#! ======================= PORTALS II ======================= !#


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
                    
                cls.debug(portals, debug_portals, Folder.DEBUG_RESOURCES / "PORTALS" / f"{MAP_FILENAME}_PTL.txt")            

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
################################################################################################################            
#! ======================= BANGERS CLASS ======================= !#

                                                  
class Bangers:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.name = name
                
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '<I')[0]
            
    @classmethod
    def read(cls, f: BinaryIO) -> 'Bangers':
        room, flags = read_unpack(f, '<2H')
        offset = Vector3.read(f, '<')
        face = Vector3.read(f, '<')  
        name = read_binary_name(f)
        return cls(room, flags, offset, face, name)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> 'List[Bangers]':
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, bangers: List['Bangers']) -> None:
        write_pack(f, '<I', len(bangers))
    
    @classmethod
    def write_all(cls, output_file: Path, bangers: List['Bangers'], debug_props: bool) -> None:
        with open(output_file, mode = "wb") as f:
            
            cls.write_n(f, bangers)
        
            for banger in bangers:
                write_pack(f, '<2H', Default.ROOM, PROP_CAN_COLLIDE_FLAG)  
                banger.offset.write(f, '<')
                banger.face.write(f, '<')
                f.write(banger.name.encode(Encoding.UTF_8))
                    
            cls.debug(bangers, debug_props, Folder.DEBUG_RESOURCES / "PROPS" / f"{output_file}{FileType.TEXT}")
    
    #! Works, but the Debug file should not land in "...\MM1-Map-Editor\SHOP\CITY"
    @classmethod
    def debug(cls, bangers: List['Bangers'], debug_props: bool, output_file: Path,) -> None:
        Debug.internal_list(bangers, debug_props, output_file)
                    
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_props_file: bool) -> None:
        if not debug_props_file:
            return

        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, 'rb') as in_f:
            bangers = cls.read_all(in_f)

        with open(output_file, 'w') as out_f:
            for banger in bangers:
                out_f.write(repr(banger))
        print(f"Processed {input_file.name} to {output_file.name}")
        
    @classmethod
    def debug_file_to_csv(cls, input_file: Path, output_file: Path, debug_props_file_to_csv: bool) -> None:
        if not debug_props_file_to_csv:
            return
        
        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, 'rb') as in_f:
            bangers = cls.read_all(in_f)

        with open(output_file, 'w') as out_f:
            out_f.write(f"{len(bangers)}\n")  # Count
            
            for banger in bangers:
                formatted_line = f"{banger.room},{banger.flags}," \
                                 f"{banger.offset.x:.2f},{banger.offset.y:.2f},{banger.offset.z:.2f}," \
                                 f"{banger.face.x:.2f},{banger.face.y:.2f},{banger.face.z:.2f}," \
                                 f"{banger.name}\n"
                                 
                out_f.write(formatted_line)
        print(f"Processed {input_file.name} to {output_file.name} in CSV format")
                                    
    def __repr__(self):
        return f"""
BANGER
    Room: {self.room}
    Flags: {self.flags}
    Start: {self.offset}
    Face: {self.face}
    Name: {self.name}
    """
    
################################################################################################################               
###############################################################################################################
#! ======================= BANGERS EDITOR ======================= !#


class BangerEditor:
    def __init__(self) -> None:  
        self.map_filename = Path(MAP_FILENAME)                      
        self.props = [] 
        
    def process_all(self, user_set_props: list, set_props: bool):
        if not set_props:
            return
        
        per_race_props = {}

        for prop in user_set_props:
            race_mode = prop.get('race_mode', 'DEFAULT')
            race_num = prop.get('race_num', '')
            race_key = f"{race_mode}_{race_num}" if race_mode != 'DEFAULT' else 'DEFAULT'
            per_race_props.setdefault(race_key, []).append(prop)

        for race_key, race_props in per_race_props.items():                
            self.props.clear()
            self.add_multiple(race_props)
            current_filename = self._filename_with_suffix(race_key)
            Bangers.write_all(Folder.SHOP_CITY / current_filename, self.props, debug_props) 
            
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
            
                if isinstance(separator, str) and separator.lower() in ["x", "y", "z"]:
                    prop_dims = self.load_dimensions(Folder.EDITOR_RESOURCES / "PROPS" / "Prop Dimensions.txt").get(name, Vector3(1, 1, 1))
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
            Bangers.debug(Folder.DEBUG_RESOURCES / "PROPS" / f"{appended_props_f.name}{FileType.TEXT}", self.props)

                        
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
        if race_key == "DEFAULT":
            return self.map_filename.with_suffix(FileType.PROP)
            
        race_mode, race_num = race_key.split("_")
        short_race_mode = {RaceMode.CIRCUIT: "C", RaceMode.CHECKPOINT: "R", RaceMode.BLITZ: "B"}.get(race_mode, race_mode)
        race_num = race_num or "0"        
        return self.map_filename.parent / f"{self.map_filename.stem}_{short_race_mode}{race_num}{FileType.PROP}"
                                                                            
    @staticmethod  
    def load_dimensions(input_file: Path) -> dict:
        extracted_prop_dim = {}
        
        with open(input_file, "r") as f:
            for line in f:
                prop_name, value_x, value_y, value_z = line.split()
                extracted_prop_dim[prop_name] = Vector3(float(value_x), float(value_y), float(value_z))
        return extracted_prop_dim

################################################################################################################               
################################################################################################################
#! ======================= MMBANGERDATA EDITOR ======================= !#

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

################################################################################################################               
################################################################################################################

#! ======================= FACADES CLASS ======================= !#


class Facades:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, sides: Vector3, scale: float, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.sides = sides
        self.scale = scale
        self.name = name
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '<I')[0]

    @classmethod
    def read(cls, f: BinaryIO) -> 'Facades':
        room, flags = read_unpack(f, '<2H')
        offset = Vector3.read(f, '<')
        face = Vector3.read(f, '<')
        sides = Vector3.read(f, '<')
        scale, = read_unpack(f, '<f')
        name = read_binary_name(f)
        return cls(room, flags, offset, face, sides, scale, name)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['Facades']:
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, facades: List['Facades']) -> None:
        return write_pack(f, '<I', len(facades))
        
    def write(self, f: BinaryIO) -> None: 
        write_pack(f, '<2H', Default.ROOM, self.flags)  # Hardcode the Room value such that all Facades are visible in the game    
        write_pack(f, '<3f', *self.offset)  
        write_pack(f, '<3f', *self.face)
        write_pack(f, '<3f', *self.sides)
        write_pack(f, '<f', self.scale)
        write_binary_name(f, self.name, terminate = True) 
        
    @classmethod
    def write_all(cls, output_file: Path, facades: List['Facades']) -> None:
        with open(output_file, mode = "wb") as f:
            
            cls.write_n(f, facades)
            
            for facade in facades:
                facade.write(f)

    @staticmethod
    def debug(facades: List['Facades'], debug_facades: bool, output_file: Path) -> None:
        Debug.internal_list(facades, debug_facades, output_file)
                                           
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_facade_file: bool) -> None:
        if not debug_facade_file:
            return

        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, "rb") as in_f:
            facades = cls.read_all(in_f)

        with open(output_file, "w") as out_f:
            for facade in facades:
                out_f.write(repr(facade))
        print(f"Processed {input_file.name} to {output_file.name}")
        
    def __repr__(self):
        return f"""
FACADE
    Room: {self.room}
    Flags: {self.flags}
    Offset: {self.offset}
    Face: {self.face}
    Sides: {self.sides}
    Scale: {self.scale:.2f}
    Name: {self.name}
    """
    
################################################################################################################               
################################################################################################################
#! ======================= FACADE EDITOR ======================= !#


class FacadeEditor:    
    @classmethod
    def create(cls, output_file: str, user_set_facades, set_facades: bool, debug_facades: bool):
        if not set_facades:
            return
        
        facades = cls.process(user_set_facades)
        Facades.write_all(output_file, facades)

        Facades.debug(facades, debug_facades, Folder.DEBUG_RESOURCES / "FACADES" / f"{MAP_FILENAME}{FileType.TEXT}")

    @staticmethod
    def read_scales(input_file: Path):
        with open(input_file, 'r') as f:
            return {name: float(scale) for name, scale in (line.strip().split(": ") for line in f)}

    @classmethod
    def process(cls, user_set_facades):
        axis_dict = {'x': 0, 'y': 1, 'z': 2}
        scales = cls.read_scales(Folder.EDITOR_RESOURCES / "FACADES" / "FCD scales.txt")

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
    
################################################################################################################               
################################################################################################################
#! ======================= PHYSICS ======================= !#


class PhysicsEditor:
    def __init__(self, name: str, friction: float, elasticity: float, drag: float, 
                 bump_height: float, bump_width: float, bump_depth: float, sink_depth: float, 
                 type: int, sound: int, velocity: Vector2, ptx_color: Vector3) -> None:
        
        self.name = name
        self.friction = friction
        self.elasticity = elasticity
        self.drag = drag
        self.bump_height = bump_height
        self.bump_width = bump_width
        self.bump_depth = bump_depth
        self.sink_depth = sink_depth
        self.type = type
        self.sound = sound
        self.velocity = velocity
        self.ptx_color = ptx_color 
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '>I')[0]

    @staticmethod
    def read(f: BinaryIO) -> 'PhysicsEditor':
        name = read_binary_name(f, 32, Encoding.LATIN_1)
        friction, elasticity, drag = read_unpack(f, '>3f')
        bump_height, bump_width, bump_depth, sink_depth = read_unpack(f, '>4f')
        type, sound = read_unpack(f, '>2I')
        velocity = Vector2.read(f, '>')
        ptx_color = Vector3.read(f, '>')
        return PhysicsEditor(name, friction, elasticity, drag, bump_height, bump_width, bump_depth, sink_depth, type, sound, velocity, ptx_color)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['PhysicsEditor']:
        return [cls.read(f) for _ in range(cls.readn(f))]

    def write(self, f: BinaryIO) -> None:        
        write_binary_name(f, self.name, length = 32, encoding = Encoding.LATIN_1, terminate = True)
        write_pack(f, '>3f', self.friction, self.elasticity, self.drag)
        write_pack(f, '>4f', self.bump_height, self.bump_width, self.bump_depth, self.sink_depth)
        write_pack(f, '>2I', self.type, self.sound)
        self.velocity.write(f, '>')
        self.ptx_color.write(f, '>')

    @staticmethod
    def write_all(output_file: Path, custom_params: List['PhysicsEditor']) -> None:
        with open(output_file, "wb") as f:
            write_pack(f, '>I', len(custom_params))
            
            for param in custom_params:                
                param.write(f)
                
    @classmethod    
    def edit(cls, input_file: Path, output_file: Path, user_set_properties: dict, set_physics: bool, debug_physics: bool) -> None:
        if not set_physics:
            return
        
        with open(input_file, "rb") as f:
            original_data = cls.read_all(f)   
             
        for phys_index, properties in user_set_properties.items():
            physics_obj = original_data[phys_index - 1]
            
            for attr, value in properties.items():
                setattr(physics_obj, attr, value)
                    
        cls.write_all(output_file, original_data)
        
        if debug_physics:
            os.makedirs(Folder.DEBUG_RESOURCES / "PHYSICS", exist_ok = True)
            cls.debug(Folder.DEBUG_RESOURCES / "PHYSICS" / "PHYSICS_DB.txt", original_data)
                        
    @classmethod
    def debug(cls, debug_filename: Path, physics_params: List['PhysicsEditor']) -> None: 
        with open(debug_filename, 'w') as debug_f:
            for idx, physics_param in enumerate(physics_params):
                debug_f.write(physics_param.__repr__(idx))
                debug_f.write("\n")

    def __repr__(self, idx = None) -> str:
        header = f"PHYSICS (# {idx + 1})" if idx is not None else "PHYSICS"
        name = self.name.rstrip('\x00' + 'Í')
        
        return f"""
{header}
    Name: '{name}',
    Friction: {self.friction:.2f},
    Elasticity: {self.elasticity:.2f},
    Drag: {self.drag:.2f},
    Bump height: {self.bump_height:.2f},
    Bump width: {self.bump_width:.2f},
    Bump depth: {self.bump_depth:.2f},
    Sink Depth: {self.sink_depth:.2f},
    Type: {self.type},
    Sound: {self.sound},
    Velocity: {self.velocity},
    Ptx color: {self.ptx_color}
    """

################################################################################################################               
################################################################################################################
#! ======================= LIGHTING ======================= !#


class LightingEditor:
    def __init__(self, time_of_day: int, weather: int, 
                 sun_heading: float, sun_pitch: float, sun_color: Tuple[float, float, float], 
                 fill_1_heading: float, fill_1_pitch: float, fill_1_color: Tuple[float, float, float], 
                 fill_2_heading: float, fill_2_pitch: float, fill_2_color: Tuple[float, float, float], 
                 ambient_color: Tuple[float, float, float],  
                 fog_end: float, fog_color: Tuple[float, float, float], 
                 shadow_alpha: float, shadow_color: Tuple[float, float, float]) -> None:
        
        self.time_of_day = time_of_day
        self.weather = weather
        self.sun_heading = sun_heading
        self.sun_pitch = sun_pitch
        self.sun_color = sun_color
        self.fill_1_heading = fill_1_heading
        self.fill_1_pitch = fill_1_pitch
        self.fill_1_color = fill_1_color
        self.fill_2_heading = fill_2_heading
        self.fill_2_pitch = fill_2_pitch
        self.fill_2_color = fill_2_color
        self.ambient_color = ambient_color
        self.fog_end = fog_end
        self.fog_color = fog_color
        self.shadow_alpha = shadow_alpha
        self.shadow_color = shadow_color
        
    @classmethod
    def read_rows(cls, row: list[Union[int, float, str]]) -> 'LightingEditor':
        return cls(
            time_of_day = int(row[0]),
            weather = int(row[1]),
            sun_heading = float(row[2]),
            sun_pitch = float(row[3]),
            sun_color = (float(row[4]), float(row[5]), float(row[6])),
            fill_1_heading = float(row[7]),
            fill_1_pitch = float(row[8]),
            fill_1_color = (float(row[9]), float(row[10]), float(row[11])),
            fill_2_heading = float(row[12]),
            fill_2_pitch = float(row[13]),
            fill_2_color = (float(row[14]), float(row[15]), float(row[16])),
            ambient_color = (float(row[17]), float(row[18]), float(row[19])),
            fog_end = float(row[20]),
            fog_color = (float(row[21]), float(row[22]), float(row[23])),
            shadow_alpha = float(row[24]),
            shadow_color = (float(row[25]), float(row[26]), float(row[27]))
        )
    
    @classmethod
    def read_file(cls, filename: Path):
        instances = []
        
        with open(filename, newline = "") as f:
            reader = csv.reader(f)
            next(reader)  
            
            for data in reader:
                instance = cls.read_rows(data)
                instances.append(instance)
                
        return instances
        
    def apply_changes(self, changes):
        for attribute, new_value in changes.items():
            if hasattr(self, attribute):
                current_value = getattr(self, attribute)
                
                if isinstance(current_value, tuple) and isinstance(new_value, tuple):
                    # Update only the specified components for tuple attributes
                    updated_value = tuple(new_value[i] if i < len(new_value) else current_value[i] for i in range(len(current_value)))
                    setattr(self, attribute, updated_value)
                else:
                    setattr(self, attribute, new_value)
            
    @staticmethod
    def process_changes(instances, config_list):
        for config in config_list:
            for instance in instances:
                if instance.time_of_day == config["time_of_day"] and instance.weather == config["weather"]:
                    instance.apply_changes(config)
        return instances
                
    def write_rows(self):
        def format_value(value):
            return int(value) if isinstance(value, float) and value.is_integer() else value

        return [
            format_value(self.time_of_day),
            format_value(self.weather),
            format_value(self.sun_heading),
            format_value(self.sun_pitch),
            *map(format_value, self.sun_color),
            format_value(self.fill_1_heading),
            format_value(self.fill_1_pitch),
            *map(format_value, self.fill_1_color),
            format_value(self.fill_2_heading),
            format_value(self.fill_2_pitch),
            *map(format_value, self.fill_2_color),
            *map(format_value, self.ambient_color),
            format_value(self.fog_end),
            *map(format_value, self.fog_color),
            format_value(self.shadow_alpha),
            *map(format_value, self.shadow_color)
        ]
        
    @classmethod
    def write_file(cls, instances, lighting_configs, filename: Path):
        cls.process_changes(instances, lighting_configs)
        
        with open(filename, mode = "w", newline = "") as f:
            writer = csv.writer(f)        
            writer.writerow(LIGHTING_HEADER)
            
            for instance in instances:
                writer.writerow(instance.write_rows())
                
    @classmethod
    def debug(cls, instances, debug_file: str, debug_lighting: bool) -> None:
        if not debug_lighting:
            return

        with open(debug_file, "w") as debug_f:
            for instance in instances:
                debug_f.write(instance.__repr__())
                debug_f.write("\n")
                
    def __repr__(self):
        return f"""
LIGHTING
    Time of Day: {self.time_of_day}
    Weather: {self.weather}
    Sun Heading: {self.sun_heading:.2f}
    Sun Pitch: {self.sun_pitch:.2f}
    Sun Color: {self.sun_color}
    Fill 1 Heading: {self.fill_1_heading:.2f}
    Fill 1 Pitch: {self.fill_1_pitch:.2f}
    Fill 1 Color: {self.fill_1_color}
    Fill 2 Heading: {self.fill_2_heading:.2f}
    Fill 2 Pitch: {self.fill_2_pitch:.2f}
    Fill 2 Color: {self.fill_2_color}
    Ambient Color: {self.ambient_color}
    Fog End: {self.fog_end:.2f}
    Fog Color: {self.fog_color}
    Shadow Alpha: {self.shadow_alpha:.2f}
    Shadow Color: {self.shadow_color}
    """

###################################################################################################################
###################################################################################################################
#! ======================= TEXTURESHEET ======================= !#


class TextureSheet:
    def __init__(self, name: str = "", neighborhood: int = 0, 
                 lod_high: int = 0, lod_medium: int = 0, lod_low: int = 1, 
                 flags: str = "", alternate: str = "", sibling: str = "", 
                 x_res: int = 64, y_res: int = 64, hex_color: str = "000000") -> None:
        
        self.name = name
        self.neighborhood = neighborhood
        self.lod_high = lod_high
        self.lod_medium = lod_medium
        self.lod_low = lod_low
        self.flags = flags
        self.alternate = alternate
        self.sibling = sibling
        self.x_res = x_res
        self.y_res = y_res
        self.hex_color = hex_color
        
    @staticmethod
    def read_sheet(input_file: Path) -> Dict[str, List[str]]:
        with open(input_file, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            return {row[0]: row for row in reader}

    @staticmethod
    def get_custom_texture_filenames(input_textures: Path) -> List[str]:
         return [f.stem for f in input_textures.glob(f"*{FileType.DIRECTDRAW_SURFACE}")]
     
    @staticmethod
    def parse_flags(flags: List[str]) -> str:
        flag_str = "".join(flags)
        print(f"Parsing flags {flags} to {flag_str}")  
        return flag_str

    @classmethod
    def append_custom_textures(cls, input_file: Path, input_textures: Path, output_file: Path, set_texture_sheet: bool) -> None:
        if not set_texture_sheet:
            return
              
        with open(input_file, "r") as in_f:
            texturesheet_lines = in_f.readlines()
                    
        existing_texture_names = set(line.split(',')[0].strip() for line in texturesheet_lines)
        custom_texture_names = TextureSheet.get_custom_texture_filenames(input_textures)
        
        with open(output_file, "w") as out_f: 
            out_f.writelines(texturesheet_lines)  # Write the existing texturesheet lines first
                    
            for custom_tex in custom_texture_names:
                if custom_tex not in existing_texture_names:
                    out_f.write(f"{custom_tex},0,0,0,1,,{custom_tex},,64,64,000000\n")  # TODO: Add support for custom flags
                    
    @staticmethod
    def write(textures: Dict[str, List[str]], output_file: Path):
        with open(output_file, "w", newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(TEXTURESHEET_HEADER)
            
            for row in textures.values():
                writer.writerow(row)

    @classmethod
    def write_tweaked(cls, input_file: Path, output_file: Path, texture_changes: List[dict], set_texture_sheet: bool):
        if not set_texture_sheet:
            return
        
        textures = cls.read_sheet(input_file)

        for changes in texture_changes:
            target = changes.get("name")
            
            if not target or target not in textures:
                print(f"Texture '{target}' not found or not specified.")
                continue

            texture = textures[target]
            
            for key, value in changes.items():
                if key == "name":
                    continue 
                
                if key == "flags":
                    value = cls.parse_flags(value)  
                    
                if key in TEXTURESHEET_MAPPING:
                    texture[TEXTURESHEET_MAPPING[key]] = str(value)

        cls.write(textures, output_file)
                    
###################################################################################################################
###################################################################################################################
#! ======================= AI ======================= !#


#! ############ Code by 0x1F9F1 (Modified) // start ############ !#   

class aiStreet:                  
    def load(self, f: BinaryIO) -> None:
        self.id, = read_unpack(f, '<H')
        self.num_vertexes, = read_unpack(f, '<H')
        self.num_lanes, = read_unpack(f, '<H')
        self.num_sidewalks, = read_unpack(f, '<H')
        self.stop_light_index, = read_unpack(f, '<H')
        self.intersection_type, = read_unpack(f, '<H')
        self.blocked, = read_unpack(f, '<H')
        self.ped_blocked, = read_unpack(f, '<H')
        self.divided, = read_unpack(f, '<H')
        self.is_flat, = read_unpack(f, '<H')
        self.has_bridge, = read_unpack(f, '<H')
        self.alley, = read_unpack(f, '<H')
        self.road_length, = read_unpack(f, '<f')
        self.speed_limit, = read_unpack(f, '<f')
        self.stop_light_name = read_binary_name(f, 32)
        self.oncoming_path, = read_unpack(f, '<I')
        self.edge_index, = read_unpack(f, '<I')
        self.path_index, = read_unpack(f, '<I')
        self.sub_section_offsets = read_unpack(f, f'<{self.num_vertexes * (self.num_lanes + self.num_sidewalks)}f')
        self.center_offsets = read_unpack(f, f'<{self.num_vertexes}f')
        self.intersection_ids = read_unpack(f, '<2I')
        self.lane_vertices = Vector3.readn(f, self.num_vertexes * (self.num_lanes + self.num_sidewalks))

        # Center / Dividing line between the two sides of the road
        self.center_vertices = Vector3.readn(f, self.num_vertexes, '<')
        self.vert_x_dirs = Vector3.readn(f, self.num_vertexes, '<')
        self.normals = Vector3.readn(f, self.num_vertexes, '<')
        self.vert_z_dirs = Vector3.readn(f, self.num_vertexes, '<')
        self.sub_section_dirs = Vector3.readn(f, self.num_vertexes, '<')

        # Outer Edges, Inner Edges (Curb)
        self.boundaries = Vector3.readn(f, self.num_vertexes * 2, '<')

        # Inner Edges on the opposite side of the road
        self.l_boundaries = Vector3.readn(f, self.num_vertexes, '<')
        self.stop_light_pos = Vector3.readn(f, 2, '<')
        self.lane_widths = read_unpack(f, '<5f')
        self.lane_lengths = read_unpack(f, '<10f')

    def read(f: BinaryIO) -> 'aiStreet':
        result = aiStreet()
        result.load(f)
        return result


class aiIntersection:
    def load(self, f: BinaryIO) -> None:
        self.id, = read_unpack(f, '<H')
        self.position = Vector3.read(f, '<')

        num_sinks, = read_unpack(f, '<H')
        self.sinks = read_unpack(f, f'<{num_sinks}I')

        num_sources, = read_unpack(f, '<H')
        self.sources = read_unpack(f, f'<{num_sources}I')

        self.paths = read_unpack(f, f'<{num_sinks + num_sources}I')
        self.directions = read_unpack(f, f'<{num_sinks + num_sources}f')

    @staticmethod
    def read(f: BinaryIO) -> 'aiIntersection':
        result = aiIntersection()
        result.load(f)
        return result


def read_array_list(f) -> List[int]:
    num_items, = read_unpack(f, '<I')
    return read_unpack(f, f'<{num_items}I')


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


class MiniParser:
    def __init__(self, file):
        self.file = file
        self.indent = 0
        self.newline = False

    def print(self, data):
        if self.newline:
            self.file.write(' ' * (self.indent * 4))
            self.newline = False

        self.file.write(data)
        if data.endswith('\n'):
            self.newline = True

    def begin_class(self, name):
        self.print(f'{name} :0 {{\n')
        self.indent += 1

    def value(self, value):
        if isinstance(value, list):
            self.print('[\n')
            self.indent += 1
            for val in value:
                self.value(val)
                self.print('\n')
            self.indent -= 1
            self.print(']')
            
        elif isinstance(value, str):            
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            self.print(f'"{escaped_value}"')
            
        elif isinstance(value, int):
            self.print(str(value))
            
        elif isinstance(value, float):
            self.print(f"{value:.2f}")
                    
        elif isinstance(value, tuple):
            formatted_values = ', '.join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in value)
            self.print(f'({formatted_values})')
                                
        elif isinstance(value, Vector3):
            self.print(f'{value.x:.2f} {value.y:.2f} {value.z:.2f}')
            
        else:
            raise Exception(f'Invalid Value Type {type(value)}')

    def field(self, name, value):
        self.print(f'{name} ')
        self.value(value)
        self.print('\n')

    def end_class(self):
        self.indent -= 1
        self.print('}\n')


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
        
#! ############ Code by 0x1F9F1 (Modified) // end ############ !#         

###################################################################################################################
###################################################################################################################
#! ======================= BAI MAP ======================= !#

       
class BaiMap:
    def __init__(self, street_names):
        self.street_names = street_names
        self.write_map()
             
    def write_map(self):           
        with open(Folder.MIDTOWNMADNESS / "dev" / "CITY" / MAP_FILENAME / f"{MAP_FILENAME}.map", 'w') as f:
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
       
###################################################################################################################
###################################################################################################################
#! ======================= AI STREET EDITOR ======================= !#


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

        return BaiMap(street_names)

    def write(self):    
        with open(Folder.MIDTOWNMADNESS / "dev" / "CITY" / MAP_FILENAME / f"{self.street_name}{FileType.AI_STREET}", 'w') as f:
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
    
################################################################################################################               
################################################################################################################    
#! ======================= LARS RACE MAKER ======================= !#


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
#! ======================= FINALIZING FUNCTIONS ======================= !#


def create_angel_resource_file(shop_folder: Path) -> None:
    for file in Path("angel").iterdir():
        if file.name in ["CMD.EXE", "RUN.BAT", "SHIP.BAT"]:
            shutil.copy(file, shop_folder / file.name)
            
    subprocess.Popen(f"cmd.exe /c run !!!!!{MAP_FILENAME}", cwd = shop_folder, creationflags = subprocess.CREATE_NO_WINDOW)


def post_editor_cleanup(build_folder: Path, shop_folder: Path, delete_shop: bool) -> None:
    os.chdir(Folder.BASE)
    time.sleep(1)  # Make sure folders are no longer in use (i.e. an .ar file is still being created)
    
    # Always delete the build folder
    try:  
        shutil.rmtree(build_folder)
    except Exception as e:
        print(f"Failed to delete the BUILD directory. Reason: {e}")
    
    # Only delete shop folder if "delete_shop" is True
    if delete_shop:
        try:
            shutil.rmtree(shop_folder)
        except Exception as e:
            print(f"Failed to delete the SHOP directory. Reason: {e}")


def create_commandline(
    output_file: Path, no_ui: bool, no_ui_type: str,
    no_ai: bool, set_music: bool, less_logs: bool, more_logs: bool) -> None:

    cmd_line = CommandArgs.DEFAULT

    if less_logs and more_logs:    
        log_error_message = f"""\n
        ***ERROR***
        You can't have both 'quiet' and 'more logs' enabled. Please choose one."
        """
        raise ValueError(log_error_message)
   
    if less_logs:
        cmd_line += f" {CommandArgs.QUIET}"
       
    if more_logs:
        cmd_line += f" {CommandArgs.LOG_OPEN} {CommandArgs.VERBOSE} {CommandArgs.CONSOLE}"
       
    if set_music:
        cmd_line += f" {CommandArgs.CD_MUSIC}"
   
    if no_ai:
        cmd_line += f" {CommandArgs.NO_AI}"
    
    if no_ui:
        if not no_ui_type or no_ui_type.lower() == "cruise":
            cmd_line += f" -noui {ControlType.KEYBOARD}"
        else:
            race_type, race_index = no_ui_type.split()
            if race_type not in ["circuit", "race", "blitz"]:
                type_error_message = f"""\n
                ***ERROR***
                Invalid Race Type provided. Available types are {RaceMode.BLITZ}, {RaceMode.CHECKPOINT}, and {RaceMode.CIRCUIT}.
                """
                raise ValueError(type_error_message)
                                            
            if not 0 <= int(race_index) <= 14:
                index_error_message = """\n
                ***ERROR***
                Invalid Race Index provided. It should be between 0 and 14.
                """
                raise ValueError(index_error_message)
            
            cmd_line += f" -noui -{race_type} {race_index} -{ControlType.KEYBOARD}"
        
    with open(output_file, "w") as f:
        f.write(cmd_line)
		

def is_process_running(process_name: str) -> bool:
    for proc in psutil.process_iter(["name"]):
        if process_name.lower() in proc.info["name"].lower():
            return True
    return False
      

def start_game(mm1_folder: str, executable: str, play_game: bool) -> None:    
    if not play_game or is_process_running(Executable.BLENDER) or is_process_running(executable):
        return
    
    subprocess.run(mm1_folder / executable, cwd = mm1_folder)

###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER SETUP ======================= !#

# TODO: move this to src/Blender/...
def setup_blender() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    delete_existing_meshes()
    enable_developer_extras()
    enable_vertex_snapping()
    adjust_3D_view_settings()
    initialize_depsgraph_update_handler()
    
###################################################################################################################
###################################################################################################################
#! ======================= BLENDER CREATE MODEL ======================= !#                   
                    
                        
def load_textures(input_folder: Path, load_all_textures: bool) -> None:
    for texture in input_folder.glob(f"*{FileType.DIRECTDRAW_SURFACE}"):
        texture_str = str(texture)
        
        if texture_str not in bpy.data.images:
            texture_image = bpy.data.images.load(texture_str)
        else:
            texture_image = bpy.data.images[texture_str]

        if load_all_textures:
            material_name = texture.stem
            
            if material_name not in bpy.data.materials:
                create_material_from_texture(material_name, texture_image)


def create_material_from_texture(material_name, texture_image):
    mat = bpy.data.materials.new(name = material_name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type = "ShaderNodeBsdfPrincipled")
    texture_node = nodes.new(type = "ShaderNodeTexImage")
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type = "ShaderNodeOutputMaterial")
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])     
    
    
def apply_texture_to_object(obj, texture_path):
    # Extract the filename (without extension) from the texture_path
    material_name = os.path.splitext(os.path.basename(texture_path))[0]
    
    # Check if the material with this name already exists
    if material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
    else:
        mat = bpy.data.materials.new(name = material_name)

    obj.data.materials.append(mat)
    obj.active_material = mat

    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type = "ShaderNodeBsdfPrincipled")
    texture_node = nodes.new(type = "ShaderNodeTexImage")
    
    texture_image = bpy.data.images.load(str(texture_path))  # Converting to String is necessary    
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type = "ShaderNodeOutputMaterial")
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])

    unwrap_uv_to_aspect_ratio(obj, texture_image)
    
       
def create_mesh_from_polygon_data(polygon_data, texture_folder = None):
    name = f"P{polygon_data['bound_number']}"
    bound_number = polygon_data["bound_number"]
    script_vertices = polygon_data["vertex_coordinates"]

    transformed_vertices = [transform_coordinate_system(Vector3.from_tuple(vertex), game_to_blender = True) for vertex in script_vertices]
    
    edges = []
    faces = [range(len(transformed_vertices))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    
    obj["cell_type"] = str(polygon_data["cell_type"])
    obj["material_index"] = str(polygon_data["material_index"])
    
    set_hud_checkbox(polygon_data["hud_color"], obj)
    
    for vertex in transformed_vertices:
        vertex_item = obj.vertex_coords.add()
        vertex_item.x, vertex_item.y, vertex_item.z = vertex
    
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(transformed_vertices, edges, faces)
    mesh.update()
    
    custom_properties = ["sort_vertices", "cell_type", "hud_color", "material_index", "always_visible"]
    
    for custom_prop in custom_properties:
        if custom_prop in polygon_data:
            obj[custom_prop] = polygon_data[custom_prop]
    
    if not obj.data.uv_layers:
        obj.data.uv_layers.new()

    # Retrieve the original UVs after creating the object and before tiling
    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in obj.data.uv_layers.active.data]
    obj["original_uvs"] = original_uvs
    
    bpy.types.Object.tile_x = bpy.props.FloatProperty(name = "Tile X", default = 2.0, update = update_uv_tiling)
    bpy.types.Object.tile_y = bpy.props.FloatProperty(name = "Tile Y", default = 2.0, update = update_uv_tiling)
    bpy.types.Object.rotate = bpy.props.FloatProperty(name = "Rotate", default = 0.0, update = update_uv_tiling)
    
    if bound_number in texcoords_data.get("entries", {}):
        obj.tile_x = texcoords_data["entries"][bound_number].get("tile_x", 1)
        obj.tile_y = texcoords_data["entries"][bound_number].get("tile_y", 1)
        obj.rotate = texcoords_data["entries"][bound_number].get("angle_degrees", 5)
    else:
        obj.tile_x = 2
        obj.tile_y = 2
        obj.rotate = 0.1
        
    if texture_folder:
        apply_texture_to_object(obj, texture_folder)    
        tile_uvs(obj, obj.tile_x, obj.tile_y)
        rotate_uvs(obj, obj.rotate)  
        
        obj.data.update()
            
    return obj


def create_blender_meshes(texture_folder: Path, load_all_textures: bool) -> None:
    if not is_process_running(Executable.BLENDER):
        return

    load_textures(texture_folder, load_all_textures)

    textures = [texture_folder / f"{texture_name}{FileType.DIRECTDRAW_SURFACE}" for texture_name in texture_names]

    for poly, texture in zip(polygons_data, textures):
        create_mesh_from_polygon_data(poly, texture)
    
###################################################################################################################
###################################################################################################################
#! ======================= BLENDER UV MAPPING ======================= !#


def unwrap_uv_to_aspect_ratio(obj, image):
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    
    bpy.ops.uv.unwrap(method = 'ANGLE_BASED', margin = 0.001)
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj.data.uv_layers.active.active = True

    # Normalize the UVs to ensure they use the entire texture
    bbox = [obj.data.uv_layers.active.data[i].uv for i in range(len(obj.data.uv_layers.active.data))]
    uvs_min = [min(co[0] for co in bbox), min(co[1] for co in bbox)]
    uvs_max = [max(co[0] for co in bbox), max(co[1] for co in bbox)]
    
    for uv_loop in obj.data.uv_layers.active.data:
        uv_loop.uv[0] = (uv_loop.uv[0] - uvs_min[0]) / (uvs_max[0] - uvs_min[0])
        uv_loop.uv[1] = (uv_loop.uv[1] - uvs_min[1]) / (uvs_max[1] - uvs_min[1])
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    
def tile_uvs(obj, tile_x = 1, tile_y = 1):
    bpy.ops.object.mode_set(mode = 'OBJECT')

    # Get the active UV layer of the object
    uv_layer = obj.data.uv_layers.active.data

    # Restore original UVs
    original_uvs = obj["original_uvs"]
    for i, uv_data in enumerate(uv_layer):
        uv_data.uv[0] = original_uvs[i][0]
        uv_data.uv[1] = original_uvs[i][1]

    # Loop over each UV coordinate and scale it
    for uv_data in uv_layer:
        uv_data.uv[0] *= tile_x
        uv_data.uv[1] *= tile_y


def rotate_uvs(obj, angle_degrees):    
    bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Get the active UV layer of the object
    uv_layer = obj.data.uv_layers.active.data
    
    angle_rad = math.radians(angle_degrees)

    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)

    # Rotate each UV coordinate around the UV center (0.5, 0.5)
    for uv_data in uv_layer:
        u, v = uv_data.uv
        u -= 0.5
        v -= 0.5
        rotated_u = u * cos_angle - v * sin_angle
        rotated_v = u * sin_angle + v * cos_angle
        uv_data.uv = (rotated_u + 0.5, rotated_v + 0.5)

     
def update_uv_tiling(self, context: bpy.types.Context) -> None:
    bpy.ops.object.select_all(action = 'DESELECT')
    self.select_set(True)
    bpy.context.view_layer.objects.active = self

    tile_uvs(self, self.tile_x, self.tile_y)
    rotate_uvs(self, self.rotate)

    
# UV MAPPING OPERATOR
class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            
            # Check if the object has the necessary custom properties
            if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "angle_degrees"]):
                
                tile_uvs(obj, obj["tile_x"], obj["tile_y"])
                rotate_uvs(obj, obj["angle_degrees"])

        return {"FINISHED"}
                        
###################################################################################################################
###################################################################################################################

#! ======================= BLENDER PANELS ======================= !#


CELL_IMPORT = [
    (str(Room.DEFAULT), "Default", "", "", Room.DEFAULT),
    (str(Room.TUNNEL), "Tunnel", "", "", Room.TUNNEL),
    (str(Room.INDOORS), "Indoors", "", "", Room.INDOORS),
    (str(Room.DRIFT), "Drift", "", "", Room.DRIFT),
    (str(Room.NO_SKIDS), "No Skids", "", "", Room.NO_SKIDS)
    ]

CELL_EXPORT = {
    str(Room.TUNNEL): "Room.TUNNEL",
    str(Room.INDOORS): "Room.INDOORS",
    str(Room.DRIFT): "Room.DRIFT",
    str(Room.NO_SKIDS): "Room.NO_SKIDS"
}


bpy.types.Object.cell_type = bpy.props.EnumProperty(
    items = CELL_IMPORT,
    name = "Cell Type",
    description = "Select the type of cell"
)


class OBJECT_PT_CellTypePanel(bpy.types.Panel):
    bl_label = "Cell Type"
    bl_idname = "OBJECT_PT_cell_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "cell_type", text = "Cell Type")
        else:
            layout.label(text = "No active object")
            
###################################################################################################################?

MATERIAL_IMPORT = [
    (str(Material.DEFAULT), "Road", "", "", Material.DEFAULT),
    (str(Material.GRASS), "Grass", "", "", Material.GRASS),
    (str(Material.WATER), "Water", "", "", Material.WATER),
    (str(Material.STICKY), "Sticky", "", "", Material.STICKY),
    (str(Material.NO_FRICTION), "No Friction", "", "", Material.NO_FRICTION)
]

MATERIAL_EXPORT = {
    str(Material.GRASS): "Material.GRASS",
    str(Material.WATER): "Material.WATER",
    str(Material.STICKY): "Material.STICKY",
    str(Material.NO_FRICTION): "Material.NO_FRICTION"
}


bpy.types.Object.material_index = bpy.props.EnumProperty(
    items = MATERIAL_IMPORT,
    name = "Material Type",
    description = "Select the type of material"
)


class OBJECT_PT_MaterialTypePanel(bpy.types.Panel):
    bl_label = "Material Type"
    bl_idname = "OBJECT_PT_material_index"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context) -> None:
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "material_index", text = "Material")
        else:
            layout.label(text = "No active object")

###################################################################################################################?

HUD_IMPORT = [
    (Color.ROAD, "Road", "", "", 1),
    (Color.GRASS, "Grass", "", "", 2),
    (Color.WATER, "Water", "", "", 3),
    (Color.SNOW, "Snow", "", "", 4),
    (Color.WOOD, "Wood", "", "", 5),
    (Color.ORANGE, "Orange", "", "", 6),
    (Color.RED_LIGHT, "Light Red", "", "", 7),
    (Color.RED_DARK, "Dark Red", "", "", 8),
    (Color.YELLOW_LIGHT, "Light Yellow", "", "", 9)
]

HUD_EXPORT = {
    # '#414441': "Color.ROAD",
    '#7b5931': "Color.WOOD",
    '#cdcecd': "Color.SNOW",
    '#5d8096': "Color.WATER",
    '#396d18': "Color.GRASS",
    '#af0000': "Color.RED_DARK",
    '#ffa500': "Color.ORANGE",
    '#ff7f7f': "Color.RED_LIGHT",
    '#ffffe0': "Color.YELLOW_LIGHT"
}


def set_hud_checkbox(color, obj):
    for i, (color_value, _, _, _, _) in enumerate(HUD_IMPORT):
        if color_value == color:
            obj.hud_colors[i] = True
            break


bpy.types.Object.hud_colors = bpy.props.BoolVectorProperty(
    name = "HUD Colors",
    description = "Select the color of the HUD",
    size = 9, 
    default = (False, False, False, False, False, False, False, False, False)
)


class OBJECT_PT_HUDColorPanel(bpy.types.Panel):
    bl_label = "HUD Type"
    bl_idname = "OBJECT_PT_hud_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            row = layout.row(align = True)
            col = row.column(align = True)
            half_length = len(HUD_IMPORT) // 2 + len(HUD_IMPORT) % 2
            
            for i, (_, name, _, _, _) in enumerate(HUD_IMPORT):
                if i == half_length:
                    col = row.column(align = True)
                
                col.prop(obj, "hud_colors", index = i, text = name, toggle = True)
        else:
            layout.label(text = "No active object")

###################################################################################################################?

bpy.types.Object.always_visible = bpy.props.BoolProperty(
    name = "Always Visible",
    description = "If true, the polygon is always visible",
    default = False
)


bpy.types.Object.sort_vertices = bpy.props.BoolProperty(
    name = "Sort Vertices",
    description = "If true, sort the vertices",
    default = False
)


class OBJECT_PT_PolygonMiscOptionsPanel(bpy.types.Panel):
    bl_label = "Polygon Options"
    bl_idname = "OBJECT_PT_polygon_options"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "always_visible", text = "Always Visible")
            layout.prop(obj, "sort_vertices", text = "Sort Vertices")
        else:
            layout.label(text = "No active object")
            
###################################################################################################################?
            
def update_vertex_coordinates(self, context):
    obj = self.id_data
    if obj and hasattr(obj.data, "vertices"):
        for index, coord in enumerate(obj.vertex_coords):
            if len(obj.data.vertices) > index:
                obj.data.vertices[index].co = (coord.x, coord.y, coord.z)
        obj.data.update()


class VertexGroup(bpy.types.PropertyGroup):
    x: bpy.props.FloatProperty(name = "X", update = update_vertex_coordinates)
    y: bpy.props.FloatProperty(name = "Y", update = update_vertex_coordinates)
    z: bpy.props.FloatProperty(name = "Z", update = update_vertex_coordinates)
    

class OBJECT_PT_VertexCoordinates(bpy.types.Panel):
    bl_label = "Vertices"
    bl_idname = "OBJECT_PT_vertex_coordinates"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        
        if obj:
            for vertex in obj.vertex_coords:
                col = layout.column(align = True)
                col.prop(vertex, "x")
                col.prop(vertex, "y")
                col.prop(vertex, "z")
        else:
            layout.label(text = "No active object")
            
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER POLYGON EXPORT ======================= !#


def format_decimal(value: Union[int, float]) -> str:
    if value == int(value): 
        return f"{value:.1f}"
    else: 
        return f"{value:.2f}"

    
def validate_and_extract_bound_number(name: str) -> int:
    if name.startswith("P"):
        return int(name[1:])
    elif name.startswith("Shape_"):
        return int(name.split("_")[1])
    else:
        raise ValueError(f"Unrecognized Polygon Name Format: {name}")
    
    
def extract_polygon_data(obj: bpy.types.Object) -> Dict[str, Union[int, str, bool, list]]:
    bound_number = validate_and_extract_bound_number(obj.name)
    
    extracted_polygon_data = {
        "bound_number": bound_number,
        "material_index": obj["material_index"],
        "cell_type": obj["cell_type"],
        "always_visible": obj["always_visible"], 
        "sort_vertices": obj["sort_vertices"],
        "vertex_coordinates": obj.data.vertices,
        "hud_color": obj["hud_color"],
        "rotate": obj["rotate"]
        }
    
    return extracted_polygon_data


def extract_polygon_texture(obj) -> str:
    if obj.material_slots:
        mat = obj.material_slots[0].material
        
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    return os.path.splitext(node.image.name)[0].replace(".DDS", "").replace(".dds", "")
                
    return Texture.CHECKPOINT  # Default value


def format_texture_name(texture_name: str) -> str:
    texture_constant = TEXTURE_EXPORT.get(texture_name, texture_name)
    return next((f'Texture.{name}' for name, value in vars(Texture).items() if value == texture_constant), f'"{texture_name}"')


def format_vertices(vertices: List[bpy.types.MeshVertex]) -> str:
    formatted_vertices = []
    
    for vertex in vertices:
        transformed_vertex = transform_coordinate_system(vertex.co, blender_to_game = True)
        formatted_vertex = f"({', '.join(format_decimal(comp) for comp in transformed_vertex)})"
        formatted_vertices.append(formatted_vertex)
        
    return ",\n\t\t".join(formatted_vertices)


def gather_optional_variables(poly_data: Dict[str, Union[int, str, bool, list]], obj: bpy.types.Object) -> str:
    optional_vars = []
    
    cell_type = CELL_EXPORT.get(str(poly_data["cell_type"]), None)
    material_index = MATERIAL_EXPORT.get(str(poly_data["material_index"]), None)
    hud_color = HUD_EXPORT.get(next((HUD_IMPORT[index][0] for index, checked in enumerate(obj.hud_colors) if checked), None), None)
        
    if cell_type:
        optional_vars.append(f"cell_type = {cell_type}")
    
    if material_index:
        optional_vars.append(f"material_index = {material_index}")
    
    if hud_color:
        optional_vars.append(f"hud_color = {hud_color}")

    if poly_data["sort_vertices"]:
        optional_vars.append("sort_vertices = True")
        
    if not poly_data["always_visible"]:
        optional_vars.append("always_visible = False")
        
    return ",\n\t".join(optional_vars) + ("," if optional_vars else "")


def export_formatted_polygons(obj: bpy.types.Object) -> str:
    poly_data = extract_polygon_data(obj)
    texture_name = extract_polygon_texture(obj).upper()
    formatted_texture = format_texture_name(texture_name)
    formatted_vertices = format_vertices(poly_data["vertex_coordinates"])
    optional_variables_str = gather_optional_variables(poly_data, obj)

    tile_x = obj.get("tile_x", 1)
    tile_y = obj.get("tile_y", 1)
    rotation = poly_data.get("rotate", 999.0)
    
    if optional_variables_str:
        optional_variables_str = f"\n\t{optional_variables_str}"
    
    template = f"""
create_polygon(
    bound_number = {poly_data['bound_number']},{optional_variables_str}
    vertex_coordinates = [
        {formatted_vertices}])

save_mesh(
    texture_name = [{formatted_texture}],
    tex_coords = compute_uv(bound_number = {poly_data['bound_number']}, tile_x = {tile_x:.2f}, tile_y = {tile_y:.2f}, angle_degrees = {rotation:.2f}))
"""

    return template


class OBJECT_OT_ExportPolygons(bpy.types.Operator):
    bl_idname = "object.export_polygons"
    bl_label = "Export Blender Polygons"
    
    select_all: bpy.props.BoolProperty(default = True)

    def execute(self, context: bpy.types.Context) -> Set[set]:            
        output_folder = Folder.BASE / "Polygon Export"
        output_folder.mkdir(exist_ok = True)
                
        current_time = datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
        export_file = output_folder / f"Polygons_{current_time}{FileType.TEXT}"
                            
        # Select Mesh Objects based on the "select_all" property
        if self.select_all:
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        else:
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
            
        if not mesh_objects:
            self.report({"WARNING"}, "No mesh objects found for export.")
            return {"CANCELLED"}
        
        # Set the first mesh object as the active object and apply transformations (to get Global coordinates)
        context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    
        try:
            with open(export_file, "w") as f:
                for obj in mesh_objects:
                    export_script = export_formatted_polygons(obj) 
                    f.write(export_script + "\n\n")
                    
            # Open the file with Notepad++ and simulate copy to clipboard
            open_with_notepad_plus(export_file)                                
            time.sleep(1.0)  # Give Notepad++ time to load the file
            pyautogui.hotkey("ctrl", "a")
            pyautogui.hotkey("ctrl", "c")
            
            self.report({"INFO"}, f"Saved data to {export_file}")
            bpy.ops.object.select_all(action = "DESELECT")
            
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export polygons: {str(e)}")
            return {"CANCELLED"}
        
        return {"FINISHED"}
    
###################################################################################################################   
###################################################################################################################    
#! ======================= BLENDER MISC OPERATORS ======================= !#


CUSTOM_PROPERTIES_CONFIG_DEFAULT = {
    "cell_type": Room.DEFAULT,
    "material_index": Material.DEFAULT,
    "hud_color": Color.ROAD,
    "sort_vertices": NO,
    "always_visible": YES,
    "tile_x": 2.0,
    "tile_y": 2.0,
    "rotate": 0.01
}


class OBJECT_OT_AssignCustomProperties(bpy.types.Operator):
    bl_idname = "object.assign_custom_properties"
    bl_label = "Assign Custom Properties to Polygons"
    bl_description = "Assign Custom Properties to polygons that do not have them yet"
    bl_options = {"REGISTER", "UNDO"}

    def assign_defaults(self, obj: bpy.types.Object, property_name: str, default_value: any) -> None:
        if property_name not in obj:
            obj[property_name] = default_value

    def execute(self, context: bpy.types.Context) -> set:
        for obj in context.scene.objects:
            if obj.type == "MESH":
                for prop_name, default_value in CUSTOM_PROPERTIES_CONFIG_DEFAULT.items():
                    self.assign_defaults(obj, prop_name, default_value)

                uv_layer = obj.data.uv_layers.active
                
                if uv_layer is None:
                    uv_layer = obj.data.uv_layers.new(name = "UVMap")
                    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in uv_layer.data]
                    obj["original_uvs"] = original_uvs

        self.report({"INFO"}, "Assigned Custom Properties")
        return {"FINISHED"}
      
###################################################################################################################   
################################################################################################################### 
#! ======================= BLENDER WAYPOINT OBJECTS / FUNCTIONS ======================= !#


POLE_HEIGHT = 3.0
POLE_DIAMETER = 0.2
FLAG_HEIGHT = 0.8
FLAG_HEIGHT_OFFSET = 2.2


#! Duplicate (see src/Blender/waypoints)
def get_all_waypoints() -> List[bpy.types.Object]:
    return [obj for obj in bpy.data.objects if obj.name.startswith("WP_")]


def update_waypoint_colors() -> None:
    waypoints = get_all_waypoints()

    if not waypoints:
        return

    waypoints[0].data.materials[0].diffuse_color = Color.WHITE      # First Waypoint
    waypoints[-1].data.materials[0].diffuse_color = Color.GREEN     # Last Waypoint

    for waypoint in waypoints[1:-1]:
        waypoint.data.materials[0].diffuse_color = Color.BLUE       # Intermediate Waypoints
        

def create_waypoint_material(name: str, color: Tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def create_waypoint_pole(height: float, diameter: float, location: Tuple[float, float, float],
                         color: Tuple[float, float, float, float]) -> bpy.types.Object:
    
    bpy.ops.mesh.primitive_cylinder_add(radius = diameter / 2, depth = height, location = location)
    pole = bpy.context.object
    pole_material = create_waypoint_material("PoleMaterial", color) 
    pole.data.materials.append(pole_material)
    return pole


def create_waypoint_flag(width: float, height: float, cursor_z: float, flag_height_offset: float, 
                         location: Tuple[float, float, float], 
                         color: Tuple[float, float, float, float]) -> bpy.types.Object:
    
    bpy.ops.mesh.primitive_plane_add(size = 1, location = location)
    flag = bpy.context.object
    flag.scale.x = width 
    flag.scale.y = height 
    flag.rotation_euler.x = math.pi / 2  # Rotate 90 degrees around x-axis
    flag.location.z = cursor_z + flag_height_offset + height / 2 
    
    flag_material = create_waypoint_material("FlagMaterial", color)
    flag.data.materials.append(flag_material)
    
    return flag


def create_gold_bar(location: Tuple[float, float, float], scale: float = 1.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size = 1, location = location)
    gold = bpy.context.object
    gold.scale *= scale  
    
    gold_material = create_waypoint_material("GoldMaterial", Color.YELLOW)  
    gold.data.materials.append(gold_material)
    gold.name = "Gold_Default"
    
    return gold

  
def create_waypoint(x: Optional[float] = None, y: Optional[float] = None, z: Optional[float] = None, 
                    rotation: float = Rotation.NORTH, width: float = Width.DEFAULT, name: Optional[str] = None, 
                    flag_color: Tuple[float, float, float, float] = Color.BLUE) -> bpy.types.Object:                
    
    if x is None or y is None or z is None:  # If (x, y, z) is NOT provided, use the current cursor position
        cursor_location = bpy.context.scene.cursor.location.copy()
    else:
        cursor_location = Vector((x, y, z))  # If (x, y, z) ARE provided, create a new location vector
  
    pole_one_location = (cursor_location.x - width / 2, cursor_location.y, cursor_location.z + POLE_HEIGHT / 2)
    pole_two_location = (cursor_location.x + width / 2, cursor_location.y, cursor_location.z + POLE_HEIGHT / 2)
    
    pole_one = create_waypoint_pole(POLE_HEIGHT, POLE_DIAMETER, pole_one_location, Color.WHITE) 
    pole_two = create_waypoint_pole(POLE_HEIGHT, POLE_DIAMETER, pole_two_location, Color.WHITE) 

    flag = create_waypoint_flag(width, FLAG_HEIGHT, cursor_location.z, FLAG_HEIGHT_OFFSET, cursor_location, flag_color)

    # Select and join the pole and flag objects
    bpy.ops.object.select_all(action = "DESELECT")
    pole_one.select_set(True)
    pole_two.select_set(True)
    flag.select_set(True)
    bpy.context.view_layer.objects.active = flag
    bpy.ops.object.join()

    waypoint = bpy.context.object    
    waypoint.rotation_euler.z = math.radians(rotation)
    waypoint.name = name if name else "WP_Default"
    
    # Set the origin to the midpoint of the poles
    midpoint = ((pole_one_location[0] + pole_two_location[0]) / 2, 
                (pole_one_location[1] + pole_two_location[1]) / 2, 
                cursor_location.z)
    
    bpy.context.scene.cursor.location = midpoint
    bpy.ops.object.origin_set(type = "ORIGIN_CURSOR")

    # Reset the cursor location if coordinates were not provided
    if x is None or y is None or z is None:
        bpy.context.scene.cursor.location = cursor_location
        
    update_waypoint_colors() 

    return waypoint

##############################################################################################################################################?
    
def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def calculate_waypoint_rotation(x1: float, z1: float, x2: float, z2: float) -> float:
    dx = x2 - x1
    dz = z2 - z1
    rotation_rad = math.atan2(dx, dz) 
    return math.degrees(rotation_rad)


def get_waypoint_name(race_type: str, race_number: int, wp_idx: int) -> str:    
    return f"WP_{RACE_TYPE_INITIALS[race_type]}{race_number}_{wp_idx}"


def load_waypoints_from_race_data(race_data: dict, race_type_input: str, race_number_input: int) -> None:
    race_key = f"{race_type_input}_{race_number_input}"  
    
    if race_key in race_data:
        waypoints = race_data[race_key]["waypoints"]
        
        for index, waypoint_data in enumerate(waypoints):
            x, y, z, rotation, scale = waypoint_data
            x, y, z = transform_coordinate_system(Vector((x, y, z)), game_to_blender = True)
            waypoint_name = get_waypoint_name(race_type_input, race_number_input, index)
            create_waypoint(x, y, z, rotation, scale, waypoint_name)
            
        update_waypoint_colors()
    else:
        print("Race data not found for the specified race type and number.")
        

def load_waypoints_from_csv(waypoint_file: Path) -> None:
    file_info = str(waypoint_file).replace(FileType.CSV, "").replace("WAYPOINTS", "")
    
    race_type = "".join(filter(str.isalpha, file_info))
    race_number = "".join(filter(str.isdigit, file_info))
    
    waypoints_data = []

    with open(waypoint_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if len(row) < 5:
                continue  
            
            waypoints_data.append([float(value) for value in row[:5]])

    for wp_idx, waypoint in enumerate(waypoints_data):
        x, y, z, rotation, width = waypoint
        x, y, z = transform_coordinate_system(Vector((x, y, z)), game_to_blender = True)
        waypoint_name = get_waypoint_name(race_type, race_number, wp_idx)
        
        if rotation == Rotation.AUTO and wp_idx < len(waypoints_data) - 1:
            next_waypoint = waypoints_data[wp_idx + 1]
            rotation = calculate_waypoint_rotation(x, z, next_waypoint[0], next_waypoint[2]) 

        if width == Width.AUTO:
            width = Width.DEFAULT

        waypoint = create_waypoint(x, y, z, -rotation, width, waypoint_name)
        
    update_waypoint_colors()
    
    
def load_cops_and_robbers_waypoints(input_file: Path) -> None:    
    waypoint_types = cycle([CnR.BANK_HIDEOUT, CnR.GOLD_POSITION, CnR.ROBBER_HIDEOUT])
    set_count = 1

    with open(input_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header 

        for row in reader:
            if len(row) < 3 or not all(is_float(val) for val in row[:3]):
                raise ValueError("\nCSV file can't be parsed. Each row must have at least 3 floats or integer values.\n")
            
            x, y, z = transform_coordinate_system(Vector(map(float, row[:3])), game_to_blender = True)                           
            waypoint_type = next(waypoint_types)

            if waypoint_type == CnR.BANK_HIDEOUT:
                create_waypoint(x, y, z, name = f"CR_Bank{set_count}", flag_color = Color.PURPLE)
                
            elif waypoint_type == CnR.GOLD_POSITION:
                create_gold_bar((x, y, z), scale = 3.0) 
                bpy.context.object.name = f"CR_Gold{set_count}"
                
            elif waypoint_type == CnR.ROBBER_HIDEOUT:
                create_waypoint(x, y, z, name = f"CR_Robber{set_count}", flag_color = Color.GREEN)  
                
            if waypoint_type == CnR.ROBBER_HIDEOUT:
                set_count += 1  # Increase the set count after completing each set of three
    
    
def export_selected_waypoints(export_all: bool = False, add_brackets: bool = False) -> None:
    if export_all:
        waypoints = get_all_waypoints()
    else:
        waypoints = [wp for wp in get_all_waypoints() if wp.select_get()]
            
    output_folder = Folder.BASE / "Waypoint Export"
    output_folder.mkdir(exist_ok = True)

    current_time = datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
    export_file = output_folder / f"Waypoints_{current_time}{FileType.TEXT}"

    with open(export_file, "w") as f:
        print("")
        f.write("# x, y, z, rotation, scale \n")
        
        for waypoint in waypoints:
            vertex = waypoint.matrix_world.to_translation()
            vertex.x, vertex.y, vertex.z = transform_coordinate_system(vertex, blender_to_game = True)
            
            rotation_euler = waypoint.rotation_euler
            rotation_degrees = math.degrees(rotation_euler.z) % Rotation.FULL_CIRCLE
            
            if rotation_degrees > Rotation.HALF_CIRCLE:
                rotation_degrees -= Rotation.FULL_CIRCLE
                
            wp_line = f"{vertex.x:.2f}, {vertex.y:.2f}, {vertex.z:.2f}, {rotation_degrees:.2f}, {waypoint.scale.x:.2f}"
            
            if add_brackets:
                wp_line = f"\t\t\t[{wp_line}],"

            f.write(wp_line + "\n")
            print(wp_line)
            
    # Open the file with Notepad++ and simulate copy to clipboard
    open_with_notepad_plus(export_file)                                
    time.sleep(1.0)  # Give Notepad++ time to load the file
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "c")
            
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER WAYPOINT OPERATORS ======================= !#


class CREATE_SINGLE_WAYPOINT_OT_operator(bpy.types.Operator):
    bl_idname = "create.single_waypoint"
    bl_label = "Create Single Waypoint"

    def execute(self, context: bpy.types.Context) -> set:
        create_waypoint(name = "WP_")  
        self.report({"INFO"}, "Created Waypoint")
        return {"FINISHED"}


class LOAD_WAYPOINTS_FROM_CSV_OT_operator(bpy.types.Operator):
    bl_idname = "load.waypoints_from_csv"
    bl_label = "Load Waypoints from CSV"

    def execute(self, context: bpy.types.Context) -> set:
        load_waypoints_from_csv(input_waypoint_file)
        self.report({"INFO"}, "Loaded Waypoints from CSV")
        return {"FINISHED"}


class LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator(bpy.types.Operator):
    bl_idname = "load.waypoints_from_race_data"
    bl_label = "Load Waypoints from Race Data"

    def execute(self, context: bpy.types.Context) -> set:
        load_waypoints_from_race_data(race_data, waypoint_type_input, waypoint_number_input)
        self.report({"INFO"}, "Loaded Waypoints from Race Data")
        return {"FINISHED"}
    
    
class LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator(bpy.types.Operator):
    bl_idname = "load.cnr_from_csv"
    bl_label = "Load CnR Waypoints from CSV"

    def execute(self, context: bpy.types.Context) -> set:
        Folder.BASE
        load_cops_and_robbers_waypoints("COPSWAYPOINTS.CSV")
        self.report({"INFO"}, "Loaded Cops & Robber Waypoints from CSV")
        return {"FINISHED"}


class EXPORT_SELECTED_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints"
    bl_label = "Export selected Waypoints"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = False, add_brackets = False)
        self.report({"INFO"}, "Exported Selected Waypoints")
        return {"FINISHED"}
    
    
class EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints_with_brackets"
    bl_label = "Export selected Waypoints with Brackets"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = False, add_brackets = True)
        self.report({"INFO"}, "Exported Selected Waypoints with Brackets")
        return {"FINISHED"}
    
    
class EXPORT_ALL_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints"
    bl_label = "Export All Waypoints"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = True, add_brackets = False)
        self.report({"INFO"}, "Exported All Waypoints")
        return {"FINISHED"}


class EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints_with_brackets"
    bl_label = "Export All Waypoints with Brackets"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = True, add_brackets = True)
        self.report({"INFO"}, "Exported All Waypoints with Brackets")
        return {"FINISHED"}
        
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER INIT ======================= !#
        
                
def initialize_blender_panels() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    bpy.utils.register_class(VertexGroup)
    bpy.types.Object.vertex_coords = bpy.props.CollectionProperty(type = VertexGroup)
    bpy.utils.register_class(OBJECT_PT_CellTypePanel)
    bpy.utils.register_class(OBJECT_PT_MaterialTypePanel)
    bpy.utils.register_class(OBJECT_PT_PolygonMiscOptionsPanel)
    bpy.utils.register_class(OBJECT_PT_HUDColorPanel)
    bpy.utils.register_class(OBJECT_PT_VertexCoordinates)
        
        
def initialize_blender_operators() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    bpy.utils.register_class(OBJECT_OT_UpdateUVMapping)
    bpy.utils.register_class(OBJECT_OT_ExportPolygons)
    bpy.utils.register_class(OBJECT_OT_AssignCustomProperties)
    bpy.utils.register_class(OBJECT_OT_ProcessPostExtrude)
    bpy.utils.register_class(OBJECT_OT_RenameChildren)
    bpy.utils.register_class(OBJECT_OT_RenameSequential)
    

def initialize_blender_waypoint_editor() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    bpy.utils.register_class(CREATE_SINGLE_WAYPOINT_OT_operator)
    bpy.utils.register_class(LOAD_WAYPOINTS_FROM_CSV_OT_operator)
    bpy.utils.register_class(LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator)
    bpy.utils.register_class(LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator)
    bpy.utils.register_class(EXPORT_SELECTED_WAYPOINTS_OT_operator)
    bpy.utils.register_class(EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator)
    bpy.utils.register_class(EXPORT_ALL_WAYPOINTS_OT_operator)
    bpy.utils.register_class(EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator)
    
###################################################################################################################
################################################################################################################### 
#! ======================= BLENDER KEYBINDINGS ======================= !#
      
      
def set_blender_keybinding() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name = "Object Mode", space_type = "EMPTY")

        #? === Workflow Automation === ?#
        # Ctrl + E to export selected polygon(s)
        kmi_export_selected = km.keymap_items.new("object.export_polygons", "E", "PRESS", ctrl = True)
        kmi_export_selected.properties.select_all = False

        # Shift + E to export all polygons
        kmi_export_all = km.keymap_items.new("object.export_polygons", "E", "PRESS", shift = True)
        kmi_export_all.properties.select_all = True

        # Shift + P to assign custom properties to newly created polygon(s)
        km.keymap_items.new("object.assign_custom_properties", "P", "PRESS", shift = True)

        # Shift + X to process an extruded mesh without triangulation
        kmi_custom_extrude_no_triangulate = km.keymap_items.new("object.process_post_extrude", "X", "PRESS", shift = True)
        kmi_custom_extrude_no_triangulate.properties.triangulate = False    
        
        # Ctrl + Shift + X to process an extruded mesh with triangulation
        kmi_custom_extrude_triangulate = km.keymap_items.new("object.process_post_extrude", "X", "PRESS", ctrl = True, shift = True)
        kmi_custom_extrude_triangulate.properties.triangulate = True

        # Ctrl + Shift + Q to rename children objects
        km.keymap_items.new("object.auto_rename_children", "Q", "PRESS", ctrl = True, shift = True)

        # Ctrl + Alt + Q to rename objects sequentially
        km.keymap_items.new("object.rename_sequential", "Q", "PRESS", ctrl = True, alt = True)
        
        #? === Waypoints === ?#
        # Shift + Y to create a single aypoint
        km.keymap_items.new("create.single_waypoint", "Y", "PRESS", shift = True)  
                
        # Shift + C to load waypoints from CSV
        km.keymap_items.new("load.waypoints_from_csv", "C", "PRESS", shift = True) 

        # Shift + R to load waypoints from "race_data" dictionary
        km.keymap_items.new("load.waypoints_from_race_data", "R", "PRESS", shift = True)  
        
        # Shift + W to export selected waypoint(s)
        km.keymap_items.new("export.selected_waypoints", "W", "PRESS", shift = True)
        
        # Ctrl + W to export selected waypoint(s) with brackets
        km.keymap_items.new("export.selected_waypoints_with_brackets", "W", "PRESS", ctrl = True)
        
        # Ctrl + Shift + W to export all waypoints
        km.keymap_items.new("export.all_waypoints", "W", "PRESS", ctrl = True, shift = True)
        
        # Ctrl + Alt + W to export all waypoins with brackets
        km.keymap_items.new("export.all_waypoints_with_brackets", "W", "PRESS", ctrl = True, alt = True)
        
        # Alt + C to load CnR waypoints from CSV
        km.keymap_items.new("load.cnr_from_csv", "O", "PRESS", alt = True)

###################################################################################################################   
################################################################################################################### 
#! ======================= BLENDER AI PATHS ======================= !#


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
create_folders()
copy_custom_textures_to_shop(Folder.USER_CUSTOM_TEXTURES, Folder.SHOP / "TEX16O")
copy_carsim_files_to_shop(Folder.EDITOR_RESOURCES / "TUNE" / "MMCARSIM", Folder.SHOP_TUNE, FileType.CAR_SIMULATION)
ensure_empty_mm_dev_folder(Folder.MIDTOWNMADNESS / "dev" / "CITY" / MAP_FILENAME) 
create_commandline(Folder.MIDTOWNMADNESS / f"commandline{FileType.TEXT}", no_ui, no_ui_type, no_ai, set_music, less_logs, more_logs)
create_map_info(Folder.SHOP_TUNE / f"{MAP_FILENAME}{FileType.CITY_INFO}", blitz_race_names, circuit_race_names, checkpoint_race_names)

edit_and_copy_bangerdata_to_shop(prop_properties, Folder.EDITOR_RESOURCES / "TUNE" / "MMBANGERDATA", Folder.SHOP_TUNE, FileType.BANGER_DATA)

# Races
create_races(race_data)
create_cops_and_robbers(Folder.SHOP_RACE_MAP / f"COPSWAYPOINTS{FileType.CSV}", cops_and_robbers_waypoints)

# Map
check_bound_numbers(polys)

create_cells(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.CELL}", polys)
Bounds.create(Folder.SHOP_BOUND / f"{MAP_FILENAME}_HITID{FileType.BOUND}", vertices, polys, Folder.DEBUG_RESOURCES / "BOUNDS" / f"{MAP_FILENAME}{FileType.TEXT}", debug_bounds)
Portals.write_all(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.PORTAL}", polys, vertices, lower_portals, empty_portals, debug_portals)
aiStreetEditor.create(street_list, set_ai_streets, set_reverse_ai_streets)
FacadeEditor.create(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.FACADE}", facade_list, set_facades, debug_facades)
PhysicsEditor.edit(Folder.EDITOR_RESOURCES / "PHYSICS" / f"PHYSICS{FileType.DATABASE}", Folder.SHOP / "MTL" / f"PHYSICS{FileType.DATABASE}", custom_physics, set_physics, debug_physics)

TextureSheet.append_custom_textures(Folder.EDITOR_RESOURCES / "MTL" / "GLOBAL.TSH", Folder.USER_CUSTOM_TEXTURES, Folder.SHOP / "MTL" / "TEMP_GLOBAL.TSH", set_texture_sheet)
TextureSheet.write_tweaked(Folder.SHOP_MATERIAL / "TEMP_GLOBAL.TSH", Folder.SHOP_MATERIAL / "GLOBAL.TSH", texture_modifications, set_texture_sheet)
                    
prop_editor = BangerEditor()
for prop in random_props:
    prop_list.extend(prop_editor.place_randomly(**prop))
prop_editor.process_all(prop_list, set_props)

lighting_instances = LightingEditor.read_file(Folder.EDITOR_RESOURCES / "LIGHTING" / "LIGHTING.CSV")
LightingEditor.write_file(lighting_instances, lighting_configs, Folder.SHOP_TUNE / "LIGHTING.CSV")
LightingEditor.debug(lighting_instances, Folder.DEBUG_RESOURCES / "LIGHTING" / "LIGHTING_DATA.txt", debug_lighting)

create_ext(Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.EXT}", hudmap_vertices)
create_animations(Folder.SHOP_CITY / MAP_FILENAME, animations_data, set_animations)   
create_bridges(bridge_list, set_bridges, Folder.SHOP_CITY / f"{MAP_FILENAME}{FileType.GIZMO}") 
create_bridge_config(bridge_config_list, set_bridges, Folder.SHOP_TUNE)
create_minimap(set_minimap, debug_minimap, debug_minimap_id, minimap_outline_color, line_width = 0.7, background_color = "black")
create_lars_race_maker(f"Lars_Race_Maker{FileType.HTML}", street_list, hudmap_vertices, set_lars_race_maker)

# Misc
DLP(Magic.DEVELOPMENT, len(dlp_groups), len(dlp_patches), len(dlp_vertices), dlp_groups, dlp_patches, dlp_vertices).write(f"TEST{FileType.DEVELOPMENT}", set_dlp) 

editor = BangerEditor()
shutil.copy(append_input_props_file, append_output_props_file)
editor.append_to_file(append_input_props_file, props_to_append, append_output_props_file, append_props)

# File / Folder Debugging
DLP.debug_file(debug_dlp_data_file, Folder.DEBUG_RESOURCES / "DLP" / debug_dlp_data_file.with_suffix(FileType.TEXT), debug_dlp_file)
Bounds.debug_file(debug_bounds_data_file, Folder.DEBUG_RESOURCES / "BOUNDS" / debug_bounds_data_file.with_suffix(FileType.TEXT), debug_bounds_file)
Bangers.debug_file(debug_props_data_file, Folder.DEBUG_RESOURCES / "PROPS" / debug_props_data_file.with_suffix(FileType.TEXT), debug_props_file)
Facades.debug_file(debug_facades_data_file, Folder.DEBUG_RESOURCES / "FACADES" / debug_facades_data_file.with_suffix(FileType.TEXT), debug_facades_file)
Portals.debug_file(debug_portals_data_file, Folder.DEBUG_RESOURCES / "PORTALS" / debug_portals_data_file.with_suffix(FileType.TEXT), debug_portals_file)
Meshes.debug_file(debug_meshes_data_file, Folder.DEBUG_RESOURCES / "MESHES" / debug_meshes_data_file.with_suffix(FileType.TEXT), debug_meshes_file)
DLP.debug_file(debug_dlp_data_file, Folder.DEBUG_RESOURCES / "DLP" / debug_dlp_data_file.with_suffix(FileType.TEXT), debug_dlp_file)

Bangers.debug_file_to_csv(debug_props_data_file, Folder.DEBUG_RESOURCES / "PROPS" / debug_props_data_file.with_suffix(FileType.CSV), debug_props_file_to_csv)
Meshes.debug_folder(debug_meshes_data_folder, Folder.DEBUG_RESOURCES / "MESHES" / "MESH TEXT FILES", debug_meshes_folder) 
Bounds.debug_folder(debug_bounds_data_folder, Folder.DEBUG_RESOURCES / "BOUNDS" / "BND TEXT FILES", debug_bounds_folder)
DLP.debug_folder(debug_dlp_data_folder, Folder.DEBUG_RESOURCES / "DLP" / "DLP TEXT FILES", debug_dlp_folder)

debug_ai(
    debug_ai_data_file, debug_ai_file,
    Folder.USER_RESOURCES / "AI" / "CHICAGO.map",                                  
    str(Path(Folder.USER_RESOURCES) / "AI" / "Intersection{intersection_id}.int"),
    str(Path(Folder.USER_RESOURCES) / "AI" / "Street{paths}.road")
    )

# Finalizing Part
create_angel_resource_file(Folder.SHOP)

end_time = time.monotonic()
editor_time = end_time - start_time

# Save the runtime
runtime_manager = RunTimeManager(Folder.EDITOR_RESOURCES / EDITOR_RUNTIME_FILE)
runtime_manager.save(editor_time)
progress_thread.join()  # Wait for progress bar to complete

print(COLOR_DIVIDER)
print(Fore.LIGHTCYAN_EX + "   Successfully created " + Fore.LIGHTYELLOW_EX + f"{MAP_NAME}!" + Fore.MAGENTA + f" (in {editor_time:.4f} s)" + Fore.RESET)
print(COLOR_DIVIDER)

start_game(Folder.MIDTOWNMADNESS, Executable.MIDTOWN_MADNESS, play_game)


# Blender
setup_blender()

initialize_blender_panels()
initialize_blender_operators()
initialize_blender_waypoint_editor()
set_blender_keybinding()

create_blender_meshes(Folder.EDITOR_RESOURCES / "TEXTURES", load_all_texures)

process_and_visualize_paths(Folder.SHOP / "dev" / "CITY" / MAP_FILENAME, f"AI_PATHS{FileType.TEXT}", visualize_ai_paths)

# Cleanup
post_editor_cleanup(Folder.BASE / "build", Folder.SHOP, delete_shop)

###################################################################################################################   
################################################################################################################### 
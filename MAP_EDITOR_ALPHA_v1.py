
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
import json
import math
import time
import shutil
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List, Dict, Set, Any, Tuple, Optional, BinaryIO

#* Third-party imports
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
from src.debug.auto import run_auto_debug

# File format imports
from src.file_formats.ai.street_editor import aiStreetEditor 
from src.file_formats.props.editor import BangerEditor, edit_and_copy_bangerdata_to_shop
from src.file_formats.props.custom import copy_custom_prop_assets_to_shop
from src.file_formats.facades.editor import FacadeEditor
from src.file_formats.physics import Physics
from src.file_formats.development import DLP

# Game imports
from src.game.races.main import create_races
from src.game.races.cops_and_robbers import create_cops_and_robbers

from src.game.bridges.main import create_bridges, create_bridge_config

from src.game.waypoints.constants import Rotation, Width

from src.game.animations import create_animations
from src.game.extrema import create_extrema
from src.game.lighting import Lighting
from src.game.texture_sheet import TextureSheet
from src.game.setup import create_map_info, copy_custom_textures_to_shop, copy_carsim_files_to_shop, ensure_empty_mm_dev_folder
from src.game.player_profile import apply_player_profile

# Roadnet (single-graph city compiler) imports
from src.game.mapgen.roadnet import RoadNetwork, RoadNetworkCompiler, grid_city
from src.game.mapgen.roadnet.presets import build_preset
from src.game.mapgen.roadnet.validate import validate_network, summarize as summarize_issues
from src.game.mapgen.roadnet.build_city import emit_roadnet_city, stage_roadnet_ai, write_roam_aimap, curved_grade, audit_collision
from src.game.mapgen.roadnet.race_gen import roadnet_checkpoint_race, roadnet_circuit_race
from src.game.mapgen.roadnet.scenery import generate_props

# MM2 -> MM1 conversion imports
from src.game.mapgen.mm2 import emit_mm2_city, Mm2Options, mm2_props
from src.game.mapgen.mm2.pathset import pathset_props
from src.game.mapgen.mm2.groundsnap import snap_props
from src.game.mapgen.mm2.bai import build_network as build_bai_network
from src.game.mapgen.mm2.bai_direct import stage_bai_direct
from src.game.mapgen.mm2.races import convert_mm2_races

# Helper imports
from src.helpers.main import calc_size, is_process_running

# Integration imports
from src.integrations.blender.setup import setup_blender
from src.integrations.blender.inits import initialize_blender_operators, initialize_blender_panels, initialize_blender_waypoint_editor
from src.integrations.blender.keybindings import set_blender_keybinding
from src.integrations.blender.modeling.props import place_props_in_scene
from src.integrations.blender.operators.facades import place_facades_in_scene
from src.integrations.blender.modeling.bridges import place_bridges_in_scene
from src.integrations.blender.operators.bridges import _bridges_py_to_blocks

# IO imports
from src.io.binary import read_unpack, write_pack, read_binary_name, write_binary_name

# Misc imports
from src.misc.main import create_commandline, start_game, post_editor_cleanup
from src.misc.angel import create_angel_resource_file

# Progress bar / console imports
from src.ui.progress_bar.main import RunTimeManager, start_progress_tracking
from src.ui.progress_bar.constants import COLOR_DIVIDER
from src.ui.console import ok, sep, detail, item, suppress_stdout_matching

# Constants imports
from src.constants.constants import * 
from src.constants.file_formats import Portal, Material, Room, LevelOfDetail, MeshFlags, PlaneEdgesWinding, Magic, FileType, BoundFormat, DdsHeader
from src.constants.textures import Texture
from src.constants.folder import Folder, TextureFolder
from src.constants.city import City
from src.constants.custom_props import get_custom_city
from src.constants.custom_props.mm2_props import Mm2Prop
from src.constants.mm2 import Mm2CellPreview
from src.constants.props import Prop, BangerFlags
from src.constants.misc import Shape, Encoding, Executable, Default, Threshold
from src.constants.color import Color

# USER imports
from src.USER.settings._resolver import (
    MAP_NAME, MAP_FILENAME, MAP_SPEC_FILE,
    EXTRA_TEXTURE_DIRS,
    play_game, delete_shop,
    set_bridges, set_props, set_facades, set_physics, set_animations, set_texture_sheet, set_music,
    set_minimap, minimap_outline_color,
    set_ai_streets, set_reverse_ai_streets,
    set_lars_race_maker, set_cruise_start,
    cruise_start_position,
    randomize_textures, random_textures,
    disable_progress_bar,
    set_player_data,
    set_races, set_cops_and_robbers, set_lighting,
    no_ui, no_ui_type, no_ai,
    less_logs, more_logs,
    lower_portals, empty_portals,
    set_dlp, fix_faulty_quads, deduplicate_bound_vertices, set_hitid_grid,
    inherit_city, inherit_hitid, inherit_cells, inherit_portals, inherit_bounds, inherit_bms,
    inherit_ai, inherit_props, inherit_facades, inherit_gizmo, inherit_extrema,
    debug_props, debug_meshes, debug_bounds, debug_facades, debug_physics, debug_portals, debug_lighting, debug_minimap, debug_minimap_id,
    auto_debug,
    load_target_model, load_all_textures,
    visualize_props, visualize_facades, visualize_bridges,
    MM2_BLENDER_VIZ, MM2_EXPORT_CITY_FOLDER, MM2_PROPS_MERGED, MM2_SAVE_RELOAD_AFTER_BUILD,
    prop_bms_folder, prop_car_wheels, prop_car_lights,  # Tweak
    SKIP_AR_CREATION, CONNECT_BLENDER_ONLY,
)

from src.USER.facades import facade_list
from src.USER.physics import custom_physics
from src.USER.lighting import lighting_configs
from src.USER.animations import animations_data
from src.USER.bridges import bridge_list, bridge_config_list
from src.USER.ai_streets import street_list

from src.USER.races.cops_and_robbers import cops_and_robbers_waypoints
from src.USER.races.races import blitz_race_names, checkpoint_race_names, circuit_race_names, race_data

from src.USER.textures.properties import texture_modifications

from src.USER.misc.dlp import dlp_groups, dlp_patches, dlp_vertices

from src.USER.props.props import prop_list, random_props  # 'Set' props could be a better name? I.e. create from scratch
from src.USER.props.append import append_props, props_to_append, append_input_props_file, append_output_props_file
from src.USER.props.properties import prop_properties

# Blender imports
from src.integrations.blender.inits import (
    unregister_all,
    initialize_blender_panels, initialize_blender_operators, initialize_blender_waypoint_editor
)

################################################################################################################               
################################################################################################################
#! ======================= VARIABLE DECLARATIONS & PROGRESS BAR ======================= !#

vertices = [] 
texture_names = []
texcoords_data = {}

polygons_data = []

hudmap_vertices = []
hudmap_properties = {}

progress_thread, start_time = start_progress_tracking(MAP_NAME, Folder.Resources.Editor.Root / "editor_runtime.pkl", disable_progress_bar)

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
    def read(cls, f: BinaryIO, vertex_index_format: str = BoundFormat.VERTEX_INDEX) -> 'Polygon':
        cell_id, material_index, = read_unpack(f, '<HB')
        flags, = read_unpack(f, '<B')
        vertex_index = read_unpack(f, vertex_index_format)
        plane_edges = Vector3.readn(f, Shape.QUAD)
        plane_normal = Vector3.read(f)
        plane_distance = read_unpack(f, '<f')
        return cls(cell_id, material_index, flags, vertex_index, plane_edges, plane_normal, plane_distance)

    def write(self, f: BinaryIO, vertex_index_format: str = BoundFormat.VERTEX_INDEX) -> None:
        if len(self.vertex_index) == Shape.TRIANGLE:  # Each polygon requires four vertex indices
            self.vertex_index += (0,)

        write_pack(f, '<HB', self.cell_id, self.material_index)
        write_pack(f, '<B', self.flags)
        write_pack(f, vertex_index_format, *self.vertex_index)

        for edge in self.plane_edges:
            edge.write(f)
            
        self.plane_normal.write(f)
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

# Accumulates per-polygon mesh data keyed by cell_id; flushed to BMS files at export time
_mesh_segments: Dict[int, list] = {}

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
#! ======================= SPATIAL GRID (MakeTable) ======================= !#

# ── MaxY helpers (mmPolygon::MaxY, CornersHeight, CheckCellXSide, CheckCellZSide, CheckCorner) ──

def _poly_check_corner(poly: Polygon, x: float, z: float,
                       plane_x: List[float], plane_z: List[float], plane_d: List[float]) -> float:
    if poly.plane_normal.y == 0.0:
        return -999999.0

    for i in range(len(plane_x)):
        if x * plane_x[i] + z * plane_z[i] + plane_d[i] < 0.0:
            return -999999.0

    return -(poly.plane_normal.x * x + poly.plane_normal.z * z + poly.plane_distance) / poly.plane_normal.y


def _poly_corners_height(poly: Polygon, vertices: List[Vector3],
                         x1: float, z1: float, x2: float, z2: float) -> float:
    n = poly.num_verts
    sign = 1.0 if poly.plane_normal.y <= 0.0 else -1.0
    plane_x, plane_z, plane_d = [], [], []

    for i in range(n):
        v1 = vertices[poly.vertex_index[i]]
        v2 = vertices[poly.vertex_index[(i + 1) % n]]
        px = -(v2.z - v1.z) * sign
        pz = (v2.x - v1.x) * sign
        pd = -(px * v1.x + pz * v1.z)
        length = math.sqrt(px * px + pz * pz)
        if length < 1e-9:
            return -999999.0
        plane_x.append(px / length)
        plane_z.append(pz / length)
        plane_d.append(pd / length)

    max_y = -999999.0
    for cx, cz in ((x1, z1), (x1, z2), (x2, z1), (x2, z2)):
        y = _poly_check_corner(poly, cx, cz, plane_x, plane_z, plane_d)
        if y > max_y:
            max_y = y
    return max_y


def _poly_check_x_side(poly: Polygon, vertices: List[Vector3],
                       plane_x: float, z_min: float, z_max: float) -> float:
    max_y = -999999.0
    n = poly.num_verts

    for i in range(n):
        v1 = vertices[poly.vertex_index[i]]
        v2 = vertices[poly.vertex_index[(i + 1) % n]]
        if (v1.x < plane_x < v2.x) or (v1.x > plane_x > v2.x):
            factor = (plane_x - v1.x) / (v2.x - v1.x)
            z_int = (v2.z - v1.z) * factor + v1.z
            if z_min <= z_int <= z_max:
                y = (v2.y - v1.y) * factor + v1.y
                if y > max_y:
                    max_y = y
    return max_y


def _poly_check_z_side(poly: Polygon, vertices: List[Vector3],
                       plane_z: float, x_min: float, x_max: float) -> float:
    max_y = -999999.0
    n = poly.num_verts

    for i in range(n):
        v1 = vertices[poly.vertex_index[i]]
        v2 = vertices[poly.vertex_index[(i + 1) % n]]
        if (v1.z < plane_z < v2.z) or (v1.z > plane_z > v2.z):
            factor = (plane_z - v1.z) / (v2.z - v1.z)
            x_int = (v2.x - v1.x) * factor + v1.x
            if x_min <= x_int <= x_max:
                y = (v2.y - v1.y) * factor + v1.y
                if y > max_y:
                    max_y = y
    return max_y


def _poly_max_y(poly: Polygon, vertices: List[Vector3],
                x_min: float, z_min: float, x_max: float, z_max: float) -> float:
    max_y = -999999.0

    for i in range(poly.num_verts):
        v = vertices[poly.vertex_index[i]]
        if x_min <= v.x <= x_max and z_min <= v.z <= z_max:
            if v.y > max_y:
                max_y = v.y

    max_y = max(max_y, _poly_corners_height(poly, vertices, x_min, z_min, x_max, z_max))
    max_y = max(max_y, _poly_check_x_side(poly, vertices, x_min, z_min, z_max))
    max_y = max(max_y, _poly_check_x_side(poly, vertices, x_max, z_min, z_max))
    max_y = max(max_y, _poly_check_z_side(poly, vertices, z_min, x_min, x_max))
    max_y = max(max_y, _poly_check_z_side(poly, vertices, z_max, x_min, x_max))
    return max_y


# ── Scanline rasterizer (mmPolygon::Plot, PlotTriangle, PlotScan) ────────────

def _plot_scan(x1: int, x2: int, z: int,
               table: List[List[int]], x_dim: int, z_dim: int,
               poly_idx: int, max_bucket: int) -> bool:
    x1 = max(0, min(x_dim - 1, int(x1)))
    x2 = max(0, min(x_dim - 1, int(x2)))
    z = max(0, min(z_dim - 1, int(z)))
    overflow = False

    for x in range(x1, x2 + 1):
        cell = x + x_dim * z
        bucket = table[cell]
        if poly_idx in bucket:
            continue
        if len(bucket) >= max_bucket:
            overflow = True
            continue
        bucket.append(poly_idx)
    return overflow


def _plot_triangle(vi0: int, vi1: int, vi2: int,
                   poly: Polygon, vertices: List[Vector3],
                   table: List[List[int]], x_dim: int, z_dim: int,
                   bb_min: Vector3, x_scale: float, z_scale: float,
                   poly_idx: int, max_bucket: int) -> bool:
    def grid_pos(vi):
        v = vertices[poly.vertex_index[vi]]
        return [(v.x - bb_min.x) * x_scale, (v.z - bb_min.z) * z_scale]

    v0 = grid_pos(vi0)
    v1 = grid_pos(vi1)
    v2 = grid_pos(vi2)

    # Sort descending by Z so v0[1] >= v1[1] >= v2[1] — rest of function depends on this
    if v1[1] < v0[1] or v1[1] < v2[1]:
        if v2[1] >= v0[1] and v2[1] >= v1[1]:
            v0, v2 = v2, v0
    else:
        v0, v1 = v1, v0
    if v2[1] >= v1[1]:
        v1, v2 = v2, v1

    slope_01 = (v1[0] - v0[0]) / (v0[1] - v1[1]) if v0[1] != v1[1] else 0.0
    slope_02 = (v2[0] - v0[0]) / (v0[1] - v2[1]) if v0[1] != v2[1] else 0.0
    slope_12 = (v2[0] - v1[0]) / (v1[1] - v2[1]) if v1[1] != v2[1] else 0.0

    overflow = False

    if int(v0[1]) - int(v1[1]) >= 2:
        left_x = v0[0]
        right_x = v0[0]
        left_sl = slope_01
        right_sl = slope_02

        if left_sl > right_sl:
            left_sl, right_sl = right_sl, left_sl

        if left_sl > 0.0:
            left_x -= left_sl
        if right_sl < 0.0:
            right_x -= right_sl

        frac0 = v0[1] - float(int(v0[1]))
        left_x += frac0 * left_sl
        right_x += frac0 * right_sl

        for z in range(int(v0[1]) - 1, int(v1[1]), -1):
            left_x += left_sl
            right_x += right_sl
            overflow |= _plot_scan(int(left_x), int(right_x), z, table, x_dim, z_dim, poly_idx, max_bucket)

    if int(v1[1]) - int(v2[1]) >= 2:
        t_mid = (v1[1] - v0[1]) / (v2[1] - v0[1])
        left_x = v1[0]
        right_x = v0[0] + t_mid * (v2[0] - v0[0])
        left_sl = slope_12
        right_sl = slope_02

        if left_x > right_x:
            left_x, right_x = right_x, left_x
            left_sl, right_sl = right_sl, left_sl

        if left_sl > 0.0:
            left_x -= left_sl
        if right_sl < 0.0:
            right_x -= right_sl

        frac1 = v1[1] - float(int(v1[1]))
        left_x += frac1 * left_sl
        right_x += frac1 * right_sl

        for z in range(int(v1[1]) - 1, int(v2[1]), -1):
            left_x += left_sl
            right_x += right_sl
            overflow |= _plot_scan(int(left_x), int(right_x), z, table, x_dim, z_dim, poly_idx, max_bucket)

    frac0 = v0[1] - float(int(v0[1]))
    frac1 = v1[1] - float(int(v1[1]))
    frac2 = v2[1] - float(int(v2[1]))

    px_v0_v0v1 = slope_01 * frac0 + v0[0]
    px_v0_v0v2 = slope_02 * frac0 + v0[0]
    px_v1_v1v2 = slope_12 * frac1 + v1[0]
    px_v1_back = v1[0] - (1.0 - frac1) * slope_01
    px_v2_v0v2 = v2[0] - (1.0 - frac2) * slope_02
    px_v2_v1v2 = v2[0] - (1.0 - frac2) * slope_12

    if int(v0[1]) == int(v2[1]):
        overflow |= _plot_scan(int(min(v0[0], v1[0], v2[0])),
                               int(max(v0[0], v1[0], v2[0])),
                               int(v0[1]), table, x_dim, z_dim, poly_idx, max_bucket)
    elif int(v0[1]) == int(v1[1]):
        overflow |= _plot_scan(int(min(v0[0], v1[0], px_v0_v0v2, px_v1_v1v2)),
                               int(max(v0[0], v1[0], px_v0_v0v2, px_v1_v1v2)),
                               int(v0[1]), table, x_dim, z_dim, poly_idx, max_bucket)
    elif int(v1[1]) == int(v2[1]):
        overflow |= _plot_scan(int(min(v1[0], v2[0], px_v1_back, px_v2_v0v2)),
                               int(max(v1[0], v2[0], px_v1_back, px_v2_v0v2)),
                               int(v1[1]), table, x_dim, z_dim, poly_idx, max_bucket)

    if int(v0[1]) != int(v1[1]):
        overflow |= _plot_scan(int(min(v0[0], px_v0_v0v1, px_v0_v0v2)),
                               int(max(v0[0], px_v0_v0v1, px_v0_v0v2)),
                               int(v0[1]), table, x_dim, z_dim, poly_idx, max_bucket)

    if int(v1[1]) != int(v0[1]) and int(v1[1]) != int(v2[1]):
        lx = min(v1[0], px_v1_back, px_v1_v1v2)
        rx = max(v1[0], px_v1_back, px_v1_v1v2)

        t_v1 = (v1[1] - v0[1]) / (v2[1] - v0[1])
        long_x = v0[0] + t_v1 * (v2[0] - v0[0])
        long_fwd = slope_02 * frac1 + long_x
        long_bk = long_x - (1.0 - frac1) * slope_02

        lx = min(lx, long_fwd, long_bk)
        rx = max(rx, long_fwd, long_bk)
        overflow |= _plot_scan(int(lx), int(rx), int(v1[1]), table, x_dim, z_dim, poly_idx, max_bucket)

    if int(v2[1]) != int(v1[1]):
        overflow |= _plot_scan(int(min(v2[0], px_v2_v0v2, px_v2_v1v2)),
                               int(max(v2[0], px_v2_v0v2, px_v2_v1v2)),
                               int(v2[1]), table, x_dim, z_dim, poly_idx, max_bucket)

    return overflow


def _plot_polygon(poly: Polygon, vertices: List[Vector3],
                  table: List[List[int]], x_dim: int, z_dim: int,
                  bb_min: Vector3, x_scale: float, z_scale: float,
                  poly_idx: int, max_bucket: int) -> bool:
    if poly.num_verts == 4:
        overflow = _plot_triangle(0, 1, 2, poly, vertices, table, x_dim, z_dim,
                                  bb_min, x_scale, z_scale, poly_idx, max_bucket)
        overflow |= _plot_triangle(0, 2, 3, poly, vertices, table, x_dim, z_dim,
                                   bb_min, x_scale, z_scale, poly_idx, max_bucket)
    else:
        overflow = _plot_triangle(0, 1, 2, poly, vertices, table, x_dim, z_dim,
                                  bb_min, x_scale, z_scale, poly_idx, max_bucket)
    return overflow


# ── Grid array builder (mmBoundTemplate::DoMakeTable second pass) ─────────────

def _build_grid_arrays(table: List[List[int]], x_dim: int, z_dim: int,
                       x_scale: float, z_scale: float,
                       bb_min: Vector3, vertices: List[Vector3], polys: List[Polygon]):
    row_offsets: List[int] = []
    bucket_offsets: List[int] = []
    row_buckets: List[int] = [0]     # index 0 is the empty-cell sentinel (never written)
    heights: List[float] = []

    current_idx = 1
    global_max_y = 0.0

    for z in range(z_dim):
        row_offsets.append(current_idx - 1)

        for x in range(x_dim):
            cell = x + x_dim * z
            bucket = table[cell]
            added = False
            max_y = -999999.0

            bucket_offsets.append(current_idx - row_offsets[z])

            for poly_idx in bucket:
                row_buckets.append(poly_idx)
                current_idx += 1
                added = True

                x_min = x / x_scale + bb_min.x
                z_min = z / z_scale + bb_min.z
                x_max = (x + 1) / x_scale + bb_min.x
                z_max = (z + 1) / z_scale + bb_min.z
                try:
                    y = _poly_max_y(polys[poly_idx], vertices, x_min, z_min, x_max, z_max)
                except (TypeError, ZeroDivisionError):
                    # Robustness guard: a malformed poly must not abort the whole build. The cell's
                    # MaxY is only a culling height hint (not collision), so skipping one poly's
                    # contribution is harmless. (Added during the BOUNDS fix after a non-reproducible
                    # range_iterator vertex crash here.)
                    continue
                if y > max_y:
                    max_y = y

            if added:
                row_buckets[-1] |= BoundFormat.ROW_BUCKETS_TERMINATOR_U32   # terminator bit on the last entry
            else:
                bucket_offsets[-1] = 0       # empty-cell sentinel

            heights.append(max_y)
            if max_y > global_max_y:
                global_max_y = max_y

    if global_max_y < 0.0:
        global_max_y = 0.0

    height_scale = global_max_y / 255.0

    fixed_heights: List[int] = []
    for h in heights:
        if h <= 0.0 or height_scale <= 0.0:
            fixed_heights.append(0)
        else:
            fixed_heights.append(min(255, int(h / height_scale)))

    return row_offsets, bucket_offsets, row_buckets, fixed_heights, height_scale, current_idx


def make_table(vertices: List[Vector3], polys: List[Polygon],
               x_dim: int = 100, z_dim: int = 100,
               max_bucket: int = 256, max_tries: int = 25):
    # BOUNDS/COLLISION FIX (SLIDE / cell=0): a cell bucket that fills past max_bucket DROPS the
    # overflowing polys from the lookup grid (see _plot_scan) -> those polys have no HITID cell ->
    # the car slides on them. The retry loop below grows the grid on overflow, but dense
    # terrain/overpass stacks could still exceed the old cap of 80 at the largest grid and silently
    # lose drivable polys. Raised to 256 (the row_buckets entries are 15-bit poly indices + a
    # terminator bit, so depth has no format limit; the grow loop still keeps most buckets shallow).
    if not vertices or len(polys) <= 1:
        return None

    bb_min = Vector3.min(vertices)
    bb_max = Vector3.max(vertices)

    x_extent = bb_max.x - bb_min.x
    z_extent = bb_max.z - bb_min.z
    if x_extent <= 0.0 or z_extent <= 0.0:
        return None

    for attempt in range(max_tries):
        scale = 1.0 + attempt * 0.5
        cur_xd = max(1, int(x_dim * scale))
        cur_zd = max(1, int(z_dim * scale))
        x_scale = cur_xd / x_extent
        z_scale = cur_zd / z_extent

        table: List[List[int]] = [[] for _ in range(cur_xd * cur_zd)]
        overflow = False

        for poly_idx, poly in enumerate(polys[1:], start=1):  # skip filler at index 0
            if _plot_polygon(poly, vertices, table, cur_xd, cur_zd,
                             bb_min, x_scale, z_scale, poly_idx, max_bucket):
                overflow = True

        if not overflow:
            break

    # HITID gap fill: give every empty cell the first polygon of an 8-connected neighbour, closing
    # the 1-cell seams left by sliver-rejected road transitions and PSDL boundary rounding.
    # ONE pass only, so genuinely empty areas (ocean, building interiors) stay empty.
    gap_filled = 0

    for cell_z in range(cur_zd):
        for cell_x in range(cur_xd):
            cell = cell_x + cur_xd * cell_z
            if table[cell]:
                continue

            neighbours = ((cell_x + dx, cell_z + dz)
                          for dz in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dz)

            for nx, nz in neighbours:
                if not (0 <= nx < cur_xd and 0 <= nz < cur_zd):
                    continue

                neighbour = table[nx + cur_xd * nz]
                if neighbour:
                    table[cell] = [neighbour[0]]
                    gap_filled += 1
                    break

    row_offsets, bucket_offsets, row_buckets, fixed_heights, height_scale, _ = \
        _build_grid_arrays(table, cur_xd, cur_zd, x_scale, z_scale, bb_min, vertices, polys)

    # ── Grid debug ────────────────────────────────────────────────────────────
    total_cells = cur_xd * cur_zd
    bucket_sizes = [len(b) for b in table if b]
    non_empty = len(bucket_sizes)
    max_fill = max(bucket_sizes) if bucket_sizes else 0
    avg_fill = sum(bucket_sizes) / non_empty if non_empty else 0.0
    num_entries = len(row_buckets) - 1
    max_y = height_scale * 255.0

    ok(f"HITID Grid: {cur_xd}×{cur_zd} ({total_cells} cells){sep()}attempt {attempt + 1}/{max_tries}")
    item(f"XScale={x_scale:.3f}  ZScale={z_scale:.3f}  HeightScale={height_scale:.5f}  maxY~{max_y:.2f}")
    item(f"Non-empty: {non_empty}/{total_cells} ({100 * non_empty / total_cells:.1f}%)  "
         f"Entries: {num_entries}  Avg fill: {avg_fill:.1f}  Max fill: {max_fill}/256"
         + (f"  Gap-filled: {gap_filled}" if gap_filled else ""))

    # for poly_idx, poly in enumerate(polys[1:], start=1):
    #     cell_count = sum(1 for b in table if poly_idx in b)
    #     shape = "quad" if poly.num_verts == 4 else "tri"
    #     item(f"  P{poly.cell_id} (idx={poly_idx}, {shape}) → {cell_count} cells")

    fill_dist = Counter(len(b) for b in table if b)
    dist_str = "  ".join(f"{k}pol:{v}cells" for k, v in sorted(fill_dist.items()))
    item(f"Fill dist: {dist_str}")

    top_cells = sorted([(i, table[i]) for i in range(len(table)) if table[i]],
                       key=lambda kv: len(kv[1]), reverse=True)[:5]
    for cell_idx, bucket in top_cells:
        cx = cell_idx % cur_xd
        cz = cell_idx // cur_xd
        poly_ids = ", ".join(f"P{polys[p].cell_id}(idx={p})" for p in bucket)
        item(f"  Top cell ({cx},{cz}): {len(bucket)} polys -> {poly_ids}")

    non_zero_h = [h for h in fixed_heights if h > 0]
    if non_zero_h:
        item(f"MaxY heights (0-255): min={min(non_zero_h)}  max={max(non_zero_h)}  "
             f"non-zero cells: {len(non_zero_h)}/{total_cells}")
    # ─────────────────────────────────────────────────────────────────────────

    return cur_xd, cur_zd, x_scale, z_scale, height_scale, row_offsets, bucket_offsets, row_buckets, fixed_heights


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
        offset = Vector3.read(f)
        x_dim, y_dim, z_dim = read_unpack(f, '<3l')
        center = Vector3.read(f)
        radius, radius_sqr = read_unpack(f, '<2f')
        bb_min = Vector3.read(f)
        bb_max = Vector3.read(f)
        num_verts, num_polys = read_unpack(f, '<2l')
        num_hot_verts_1, num_hot_verts_2, num_edges = read_unpack(f, '<3l')
        x_scale, z_scale = read_unpack(f, '<2f')
        num_indices_raw, height_scale, cache_size = read_unpack(f, '<Ifl')
        has_u32_row_buckets = bool(num_indices_raw & BoundFormat.ROW_BUCKETS_U32_FLAG)
        num_indices = num_indices_raw & ~BoundFormat.ROW_BUCKETS_U32_FLAG

        vertices = Vector3.readn(f, num_verts)
        # BND3 stores i32 VertIndices, the older BND2 i16. Pick from the magic, otherwise every
        # field after VertIndices reads at the wrong offset on an existing city.
        vertex_index_format = (BoundFormat.VERTEX_INDEX_EXTENDED if magic == Magic.BOUND_EXTENDED
                               else BoundFormat.VERTEX_INDEX)
        polys = [Polygon.read(f, vertex_index_format) for _ in range(num_polys + 1)]

        hot_verts = Vector3.readn(f, num_hot_verts_2)
        edge_verts_1 = read_unpack(f, f'<{num_edges}I')
        edge_verts_2 = read_unpack(f, f'<{num_edges}I')
        edge_plane_normal = Vector3.readn(f, num_edges)
        edge_plane_distance = read_unpack(f, f'<{num_edges}f')

        row_offsets = None
        bucket_offsets = None
        row_buckets = None
        fixed_heights = None

        if x_dim and y_dim and z_dim:
            row_offsets = read_unpack(f, f'<{z_dim}I')
            bucket_offsets = read_unpack(f, f'<{x_dim * z_dim}H')
            if has_u32_row_buckets:
                row_buckets = read_unpack(f, f'<{num_indices}I')
            else:
                narrow = read_unpack(f, f'<{num_indices}H')
                # Widen BND2's u16 entries to the in-memory u32 form, moving the terminator bit.
                row_buckets = tuple(
                    (entry & ~BoundFormat.ROW_BUCKETS_TERMINATOR_U16) | BoundFormat.ROW_BUCKETS_TERMINATOR_U32
                    if entry & BoundFormat.ROW_BUCKETS_TERMINATOR_U16 else entry
                    for entry in narrow
                )
            fixed_heights = read_unpack(f, f'<{x_dim * z_dim}B')

        return cls(
            magic, offset, x_dim, y_dim, z_dim, center, radius, radius_sqr, bb_min, bb_max, 
            num_verts, num_polys, num_hot_verts_1, num_hot_verts_2, num_edges, 
            x_scale, z_scale, num_indices, height_scale, cache_size, vertices, polys,
            hot_verts, edge_verts_1, edge_verts_2, edge_plane_normal, edge_plane_distance,
            row_offsets, bucket_offsets, row_buckets, fixed_heights
            )
    
    @classmethod
    def initialize(cls, vertices: List[Vector3], polys: List[Polygon],
                   grid_x_dim: int = 0, grid_z_dim: int = 0) -> 'Bounds':
        # Remap global vertex indices to a local deduplicated vertex table so
        # polygon vertex_index values always fit in uint16 (< 65535).
        # Large cities (Chicago) have 80k+ global vertices; the original HITID
        # for Chicago has only 8049 unique positions — dedup keeps us in range.
        coord_to_local: dict = {}
        local_vertices: List[Vector3] = []
        local_polys: List[Polygon] = []
        for poly in polys:
            new_vi = []
            for g_idx in poly.vertex_index[:poly.num_verts]:
                v = vertices[g_idx]
                key = (v.x, v.y, v.z)
                if key not in coord_to_local:
                    coord_to_local[key] = len(local_vertices)
                    local_vertices.append(v)
                new_vi.append(coord_to_local[key])
            local_polys.append(Polygon(
                poly.cell_id, poly.material_index, poly.flags, new_vi,
                poly.plane_edges, poly.plane_normal, poly.plane_distance,
                poly.cell_type, poly.always_visible,
            ))
        vertices = local_vertices
        polys    = local_polys

        # RETAIL COMPATIBILITY: write BND2 (i16 VertIndices) so the map loads on stock MM1. Only a
        # city that still overflows i16 AFTER the dedup above -- an imported MM2 city like NY or
        # Buenos Aires with INST buildings -- escalates to BND3, which needs Open1560 to load.
        magic = (Magic.BOUND_EXTENDED if len(vertices) > BoundFormat.MAX_VERTICES
                 else Magic.BOUND)
        offset = Default.VECTOR_3
        center = Vector3.center(vertices)
        radius = Vector3.calculate_radius(vertices, center)
        radius_sqr = Vector3.calculate_radius_squared(vertices, center)
        bb_min = Vector3.min(vertices)
        bb_max = Vector3.max(vertices)
        num_hot_verts_1, num_hot_verts_2, num_edges = 0, 0, 0
        cache_size = 0

        hot_verts = []
        edge_verts_1, edge_verts_2 = [], []
        edge_plane_normal = []
        edge_plane_distance = []

        if grid_x_dim > 0 and grid_z_dim > 0:
            grid = make_table(vertices, polys, grid_x_dim, grid_z_dim)
        else:
            grid = None

        if grid is not None:
            x_dim, z_dim, x_scale, z_scale, height_scale, row_offsets, bucket_offsets, row_buckets, fixed_heights = grid
            y_dim       = 1
            num_indices = len(row_buckets)
        else:
            x_dim, y_dim, z_dim = 0, 0, 0
            x_scale, z_scale = 0.0, 0.0
            num_indices, height_scale = 0, 0.0
            row_offsets, bucket_offsets, row_buckets, fixed_heights = [], [], [], []

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
        # A city that overflows i16 vertex indices is written as BND3, which also carries the wider
        # u32 RowBuckets. Everything else stays BND2 so retail MM1 can still load the map.
        is_extended = (self.magic == Magic.BOUND_EXTENDED)
        vertex_index_format = (BoundFormat.VERTEX_INDEX_EXTENDED if is_extended
                               else BoundFormat.VERTEX_INDEX)
        row_bucket_count = self.num_indices | BoundFormat.ROW_BUCKETS_U32_FLAG if is_extended else self.num_indices

        write_binary_name(f, self.magic)
        self.offset.write(f)
        write_pack(f, '<3l', self.x_dim, self.y_dim, self.z_dim)
        self.center.write(f)
        write_pack(f, '<2f', self.radius, self.radius_sqr)
        self.bb_min.write(f)
        self.bb_max.write(f)
        write_pack(f, '<2l', self.num_verts, self.num_polys)
        write_pack(f, '<3l', self.num_hot_verts_1, self.num_hot_verts_2, self.num_edges)
        write_pack(f, '<2f', self.x_scale, self.z_scale)
        write_pack(f, '<Ifl', row_bucket_count, self.height_scale, self.cache_size)

        for vertex in self.vertices:
            vertex.write(f)

        for poly in self.polys:
            poly.write(f, vertex_index_format)

        # Edge section (num_edges=0 for editor-generated bounds → no bytes written)
        for v in self.hot_verts:
            v.write(f)
        if self.num_edges:
            write_pack(f, f'<{self.num_edges}I', *self.edge_verts_1)
            write_pack(f, f'<{self.num_edges}I', *self.edge_verts_2)
            for n in self.edge_plane_normal:
                n.write(f)
            write_pack(f, f'<{self.num_edges}f', *self.edge_plane_distance)

        # Spatial grid (only written when XDim/YDim/ZDim are all non-zero)
        if self.x_dim and self.y_dim and self.z_dim:
            write_pack(f, f'<{self.z_dim}I',               *self.row_offsets)
            write_pack(f, f'<{self.x_dim * self.z_dim}H',  *self.bucket_offsets)

            if is_extended:
                write_pack(f, f'<{self.num_indices}I', *self.row_buckets)
            else:
                # RowBuckets are held in memory in the wide u32 form (bit31 = terminator). BND2
                # stores them as u16 with the terminator at bit15, so narrow them back on the way out.
                narrowed = [((entry & ~BoundFormat.ROW_BUCKETS_TERMINATOR_U32) | BoundFormat.ROW_BUCKETS_TERMINATOR_U16)
                            if entry & BoundFormat.ROW_BUCKETS_TERMINATOR_U32 else entry
                            for entry in self.row_buckets]
                write_pack(f, f'<{self.num_indices}H', *narrowed)

            write_pack(f, f'<{self.x_dim * self.z_dim}B',  *self.fixed_heights)

    @staticmethod
    def create(output_file: Path, vertices: List[Vector3], polys: List[Polygon],
               debug_file: Path, debug_bounds: bool,
               grid_x_dim: int = 0, grid_z_dim: int = 0) -> None:
        bnd = Bounds.initialize(vertices, polys, grid_x_dim, grid_z_dim)

        with open(output_file, "wb") as f:
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
                 normals: List[int], tex_coords: List[float], vert_colors: List[int],
                 planes: List[float], enclosed_shape: List[int],
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
        self.vert_colors = vert_colors
        self.planes = planes
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
                vertices = Vector3.readn(f, vertex_count)
            else:
                vertices = Vector3.readn(f, vertex_count + 8)

            normals = list(read_unpack(f, f"{adjunct_count}B")) if (flags & MeshFlags.NORMALS) else []
            tex_coords = list(read_unpack(f, f"{adjunct_count * 2}f")) if (flags & MeshFlags.TEXCOORDS) else []
            vert_colors = list(read_unpack(f, f"{adjunct_count * 4}B")) if (flags & MeshFlags.COLORS) else []

            enclosed_shape = list(read_unpack(f, f"{adjunct_count}H"))

            # 4 floats (Vector4) per surface — BSP plane equations
            planes = list(read_unpack(f, f"<{surface_count * 4}f")) if (flags & MeshFlags.PLANES) else []

            surface_sides = list(read_unpack(f, f"{surface_count}B"))

            indices_per_surface = indices_count // surface_count
            indices_sides = [list(read_unpack(f, f"<{indices_per_surface}H")) for _ in range(surface_count)]

        return cls(
            magic, vertex_count, adjunct_count, surface_count, indices_count,
            radius, radius_sqr, bounding_box_radius,
            texture_count, flags, cache_size, texture_names, vertices,
            normals, tex_coords, vert_colors, planes, enclosed_shape, surface_sides, indices_sides
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
                vertex.write(f)

            if self.vertex_count >= Threshold.MESH_VERTEX_COUNT:
                xs = [v.x for v in self.vertices]
                ys = [v.y for v in self.vertices]
                zs = [v.z for v in self.vertices]
                mn = (min(xs), min(ys), min(zs))
                mx = (max(xs), max(ys), max(zs))
                for cx in (mn[0], mx[0]):
                    for cy in (mn[1], mx[1]):
                        for cz in (mn[2], mx[2]):
                            write_pack(f, '<3f', cx, cy, cz)

            if self.flags & MeshFlags.NORMALS:
                write_pack(f, f"{self.adjunct_count}B", *self.normals)

            if self.flags & MeshFlags.TEXCOORDS:
                tex_coords = self.tex_coords[:self.adjunct_count * 2]
                write_pack(f, f"{self.adjunct_count * 2}f", *tex_coords)

            if self.flags & MeshFlags.COLORS:
                write_pack(f, f"{self.adjunct_count * 4}B", *self.vert_colors)

            write_pack(f, f"{self.adjunct_count}H", *self.enclosed_shape)

            if self.flags & MeshFlags.PLANES:
                write_pack(f, f"<{self.surface_count * 4}f", *self.planes)

            write_pack(f, f"{self.surface_count}B", *self.surface_sides)

            # Each polygon requires four vertex indices (add 0 as the 4th index for triangles)
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

        if self.flags & MeshFlags.NORMALS:
            self.cache_size += self.align_size(self.adjunct_count * calc_size('B'))

        if self.flags & MeshFlags.TEXCOORDS:
            self.cache_size += self.align_size(self.adjunct_count * Vector2.binary_size())

        if self.flags & MeshFlags.COLORS:
            self.cache_size += self.align_size(self.adjunct_count * calc_size('I'))

        self.cache_size += self.align_size(self.adjunct_count * calc_size('H'))

        if self.flags & MeshFlags.PLANES:
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

    # Keep the '\n's after 'Cache Size'  
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
    UVs: {', '.join(f'{coord:.2f}' for coord in self.tex_coords)}\n
    Vertex Colors: {self.vert_colors}\n
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

    # Key by (bound_number, sub) so each polygon in a multi-poly cell keeps its own UV settings.
    # sub = how many segments already accumulated for this cell → matches Blender's .001/.002 suffix order.
    sub = len(_mesh_segments.get(bound_number, []))
    texcoords_data["entries"][(bound_number, sub)] = {"tile_x": tile_x, "tile_y": tile_y, "angle_degrees": angle_degrees}

    return adjust_and_rotate_coords(coords, angle_degrees)
        

def determine_mesh_folder_and_filename(cell_id: int, texture_name: List[str]) -> Tuple[Path, str]:
    if cell_id < Threshold.CELL_TYPE_SWITCH:
        target_folder = Folder.Shop.Map.MeshLandmark
    else:
        target_folder = Folder.Shop.Map.MeshCity
                        
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
    n_verts = poly.num_verts

    if randomize_textures:
        texture_name = [random.choice(random_textures)]

    texture_names.append(texture_name[0])

    raw_uvs = list(tex_coords) if tex_coords is not None else [1.0] * (n_verts * 2)

    seg = {
        'poly':          poly,
        'texture_name':  texture_name[0],
        'texture_index': texture_indices[0] if texture_indices else 1,
        'normals':       list(normals)     if normals is not None else [2] * n_verts,
        'tex_coords':    raw_uvs[:n_verts * 2],  # compute_uv() always yields 4 pairs; triangles need only 3
    }

    if cell_id not in _mesh_segments:
        _mesh_segments[cell_id] = []
    _mesh_segments[cell_id].append(seg)


def initialize_mesh(
    vertices: List[Vector3], polys: List[Polygon], texture_indices: List[int],
    texture_name: List[str], normals: List[int] = None, tex_coords: List[float] = None) -> Meshes:

    shapes = [[vertices[i] for i in poly.vertex_index[:poly.num_verts]] for poly in polys]
    coordinates = [coord for shape in shapes for coord in shape]

    radius = Vector3.calculate_radius(coordinates, Default.VECTOR_3)
    radiussq = Vector3.calculate_radius_squared(coordinates, Default.VECTOR_3)
    bounding_box_radius = Vector3.calculate_bounding_box_radius(coordinates)

    vertex_count = len(coordinates)
    adjunct_count = len(coordinates)
    surface_count = len(texture_indices)
    texture_count = len(texture_name)
    indices_count = surface_count * 4  # always 4 indices per polygon (tris get a 0-padded 4th)

    cache_size = 0

    enclosed_shape = list(range(adjunct_count))
    normals    = normals    or [2]   * adjunct_count
    tex_coords = tex_coords or [1.0] * (adjunct_count * 2)

    # Build per-surface vertex index lists using cumulative offsets
    offset = 0
    indices_sides = []
    for shape in shapes:
        indices_sides.append(list(range(offset, offset + len(shape))))
        offset += len(shape)

    return Meshes(
        Magic.MESH, vertex_count, adjunct_count, surface_count, indices_count,
        radius, radiussq, bounding_box_radius,
        texture_count, MeshFlags.TEXCOORDS_AND_NORMALS, cache_size,
        texture_name, coordinates, normals, tex_coords, [], [],
        enclosed_shape, texture_indices, indices_sides
        )




def write_one_mesh(cell_id, segments, vertices, target_folder, mesh_filename, debug_meshes):
    texture_slot: Dict[str, int] = {}
    for segment in segments:
        name = segment['texture_name']
        if name not in texture_slot:
            texture_slot[name] = len(texture_slot) + 1  # 1-based texture index

    all_texture_names   = list(texture_slot.keys())
    texture_indices     = [texture_slot[segment['texture_name']] for segment in segments]
    all_polys           = [segment['poly'] for segment in segments]
    combined_normals    = [v for segment in segments for v in segment['normals']]
    combined_tex_coords = [v for segment in segments for v in segment['tex_coords']]

    mesh = initialize_mesh(vertices, all_polys, texture_indices, all_texture_names,
                           combined_normals, combined_tex_coords)
    mesh.write(target_folder / mesh_filename)

    if debug_meshes:
        mesh.debug(Path(mesh_filename).with_suffix(FileType.TEXT), Folder.Debug.Meshes / MAP_FILENAME, debug_meshes)


def flush_meshes(vertices: List[Vector3] = vertices, debug_meshes: bool = debug_meshes) -> None:
    # AUTO-SPLIT over-dense cells (2026-07): a landmark cell whose HIGH mesh exceeds the engine's
    # 16384-verts/mesh render buffer is split into CULL<id>_H + CULL<id>_H2. The engine renders H2 as a
    # real secondary opaque mesh (Meshes[6], pass-3, DrawLit+Z; cull flag LevelOfDetail.UNKNOWN_4=0x100),
    # so this ~doubles a cell's capacity to 2×16384 without portals — unblocks dense INST cities (NY/BA)
    # under the 199-landmark-cell limit. No-op for SF/London (all cells < 16384). Water (_A2) cells are
    # never split. get_cell_ids/write_cell_row set the H2 cull flag for split cells.
    for cell_id, segments in _mesh_segments.items():
        cell_textures = [segment['texture_name'] for segment in segments]
        target_folder, base_fname = determine_mesh_folder_and_filename(cell_id, cell_textures)
        is_water = base_fname.endswith(f"_A2{FileType.MESH_lowercase}")
        total_verts = sum(segment['poly'].num_verts for segment in segments)

        if is_water or total_verts <= Threshold.MESH_VERTEX_BUFFER:
            write_one_mesh(cell_id, segments, vertices, target_folder, base_fname, debug_meshes)
            continue

        # Pack the primary group (H) up to the vert limit; the remainder goes to H2.
        primary_segments, primary_verts = [], 0
        for segment in segments:
            segment_verts = segment['poly'].num_verts
            if primary_segments and primary_verts + segment_verts > Threshold.MESH_VERTEX_BUFFER:
                break
            primary_segments.append(segment)
            primary_verts += segment_verts

        secondary_segments = segments[len(primary_segments):]
        secondary_verts = sum(segment['poly'].num_verts for segment in secondary_segments)
        secondary_filename = f"CULL{cell_id:02d}_H2{FileType.MESH_lowercase}"

        write_one_mesh(cell_id, primary_segments, vertices, target_folder, base_fname, debug_meshes)
        write_one_mesh(cell_id, secondary_segments, vertices, target_folder, secondary_filename, debug_meshes)
        item(f"cell {cell_id}: {total_verts} verts > {Threshold.MESH_VERTEX_BUFFER} --- "
             f"split into H({primary_verts}) + H2({secondary_verts})")

        if secondary_verts > Threshold.MESH_VERTEX_BUFFER:
            item(f"WARNING: cell {cell_id} H2 = {secondary_verts} verts still > "
                 f"{Threshold.MESH_VERTEX_BUFFER} (no H3 slot) --- lower max_tris_per_cell so each "
                 f"cell fits in 2x{Threshold.MESH_VERTEX_BUFFER} verts.")


def write_per_cell_bounds(vertices: List[Vector3], polys: List[Polygon]) -> None:
    # Build per-cell polygon sets.  Every polygon is written to its own cell (primary)
    # AND to any other cell whose tight XZ bounding box it overlaps.  This ensures that
    # when GetStartCell returns a stale neighbouring cell (the common case while
    # transitioning between road blocks) the wheel-physics BND for that cell still has
    # the ground polygon → no fall-through.  Non-drivable polys (facades, INST) only
    # expand collision geometry, which is harmless: near-vertical normals cause FullSegment
    # to fail for downward probes anyway.
    cells: Dict[int, List[Polygon]] = defaultdict(list)

    # Step 1: compute tight XZ bbox for every cell from its primary polygons.
    cell_bbox: Dict[int, List[float]] = {}   # cell_id -> [min_x, max_x, min_z, max_z]

    for poly in polys[1:]:
        cell_id = poly.cell_id
        xs = [vertices[vi].x for vi in poly.vertex_index[:poly.num_verts]]
        zs = [vertices[vi].z for vi in poly.vertex_index[:poly.num_verts]]

        if cell_id in cell_bbox:
            bbox = cell_bbox[cell_id]
            if xs[0] < bbox[0] or len(xs) > 1:
                bbox[0] = min(bbox[0], min(xs))
            bbox[1] = max(bbox[1], max(xs))
            if zs[0] < bbox[2] or len(zs) > 1:
                bbox[2] = min(bbox[2], min(zs))
            bbox[3] = max(bbox[3], max(zs))
        else:
            cell_bbox[cell_id] = [min(xs), max(xs), min(zs), max(zs)]

    cell_ids = list(cell_bbox.keys())
    cell_boxes = [cell_bbox[cell_id] for cell_id in cell_ids]   # parallel to cell_ids

    # Step 2: assign each polygon to all cells it overlaps (O(N_polys × N_cells);
    # N_cells ≈ 394 for BA/NY so this is fast even for 600 k polys).
    multi_added = 0

    for poly in polys[1:]:
        xs = [vertices[vi].x for vi in poly.vertex_index[:poly.num_verts]]
        zs = [vertices[vi].z for vi in poly.vertex_index[:poly.num_verts]]
        poly_min_x, poly_max_x = min(xs), max(xs)
        poly_min_z, poly_max_z = min(zs), max(zs)

        primary_cell = poly.cell_id
        cells[primary_cell].append(poly)   # always include in its primary cell

        for cell_id, (min_x, max_x, min_z, max_z) in zip(cell_ids, cell_boxes):
            if cell_id == primary_cell:
                continue
            if (poly_max_x >= min_x and poly_min_x <= max_x
                    and poly_max_z >= min_z and poly_min_z <= max_z):
                cells[cell_id].append(poly)
                multi_added += 1

    if multi_added:
        item(f"Per-cell BNDs: {multi_added} extra polygon placements from XZ bbox overlap "
             f"(avg {multi_added / max(1, len(cell_ids)):.1f} extras/cell)")

    total_raw = 0
    total_local = 0
    cells_with_sharing = 0
    best_saved = 0
    best_cell = -1

    for cell_id, cell_polys in cells.items():
        g_to_local: Dict[int, int] = {}
        local_vertices: List[Vector3] = []
        raw_count = sum(poly.num_verts for poly in cell_polys)

        if deduplicate_bound_vertices:
            coord_to_local: Dict[tuple, int] = {}
            for poly in cell_polys:
                for g_idx in poly.vertex_index[:poly.num_verts]:
                    key = (vertices[g_idx].x, vertices[g_idx].y, vertices[g_idx].z)
                    if key not in coord_to_local:
                        coord_to_local[key] = len(local_vertices)
                        local_vertices.append(vertices[g_idx])
                    g_to_local[g_idx] = coord_to_local[key]
        else:
            for poly in cell_polys:
                for g_idx in poly.vertex_index[:poly.num_verts]:
                    if g_idx not in g_to_local:
                        g_to_local[g_idx] = len(g_to_local)
                        local_vertices.append(vertices[g_idx])

        local_polys: List[Polygon] = [Default.POLYGON]
        for poly in cell_polys:
            local_polys.append(Polygon(
                cell_id        = poly.cell_id,
                material_index = poly.material_index,
                flags          = poly.flags,
                vertex_index   = [g_to_local[i] for i in poly.vertex_index[:poly.num_verts]],
                plane_edges    = poly.plane_edges,
                plane_normal   = poly.plane_normal,
                plane_distance = poly.plane_distance,
                cell_type      = poly.cell_type,
                always_visible = poly.always_visible,
            ))

        if cell_id < Threshold.CELL_TYPE_SWITCH:
            output_folder = Folder.Shop.Map.BoundLandmark
        else:
            output_folder = Folder.Shop.Map.BoundCity

        output_file = output_folder / f"BOUND{cell_id:02d}{FileType.BOUND}"
        Bounds.create(output_file, local_vertices, local_polys, None, False)

        saved = raw_count - len(local_vertices)
        total_raw += raw_count
        total_local += len(local_vertices)
        if saved > 0:
            cells_with_sharing += 1
        if saved > best_saved:
            best_saved = saved
            best_cell = cell_id

    # ── BND deduplication debug ───────────────────────────────────────────────
    mode = "ON" if deduplicate_bound_vertices else "OFF"
    ok(f"Per-cell BNDs: {len(cells)} cells written  (vertex dedup {mode})")
    total_saved = total_raw - total_local
    pct = 100 * total_saved / total_raw if total_raw else 0.0
    item(f"Raw vertex-refs: {total_raw}  ->  Local verts: {total_local}  ({total_saved} saved, {pct:.1f}%)")
    if deduplicate_bound_vertices and best_cell >= 0:
        item(f"Cells with sharing: {cells_with_sharing}/{len(cells)}  "
             f"(most saved: {best_saved} verts in BOUND{best_cell:02d})")
    # ─────────────────────────────────────────────────────────────────────────

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
    always_visible: bool = True, fix_faulty_quads: bool = fix_faulty_quads, base: bool = False,
    flip: bool = False, fix_winding: bool = True) -> None:

    base_vertex_index = len(vertices)
    check_shape_type(vertex_coordinates)
    if fix_winding:
        vertex_coordinates = process_winding(vertex_coordinates, fix_faulty_quads)
    flags = process_flags(vertex_coordinates, flags)

    if sort_vertices:
        vertex_coordinates = sort_coordinates(vertex_coordinates)

    if flip:
        vertex_coordinates = list(reversed(vertex_coordinates))

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
              
    if base:
        update_cruise_start_position(vertex_coordinates)
          
    if plane_edges is None:
        plane_edges, axis_flag = compute_edges(vertex_coordinates)
        flags = (flags & 0xFC) | axis_flag  # Sync projection axis bits with actual geometry
        
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

    if isinstance(plane_normal, list):
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

# Wipe SHOP before building too, not just after, so leftovers from a previous (or crashed) build
# cannot be packed into the .AR — that is what bloated MM2SF.ar from 36 MB to 67 MB with London's
# files. Folder.create_all() below recreates the empty skeleton.
if delete_shop and Folder.Shop.Root.is_dir():
    shutil.rmtree(Folder.Shop.Root, ignore_errors=True)
    ok("Cleaned the SHOP folder before building (no stale / cross-city leftovers)")

Folder.create_all()

# ROADNET (opt-in, export-safe): defined here BEFORE the polygon region so the editor's
# "Export Polygons" (which rewrites that region) cannot wipe this definition. See
# src/game/mapgen/roadnet. ROADNET_CITY drives the geometry block (end of polygon region);
# the AI is staged then consumed during the build, around the dev-folder clear.
try:
    from src.USER.settings.main import ROADNET_CITY
except Exception:
    ROADNET_CITY = None
try:
    from src.USER.settings.main import MM2_CITY
except Exception:
    MM2_CITY = None
try:
    from src.USER.settings.main import ROADNET_BOOT_RACE
except Exception:
    ROADNET_BOOT_RACE = False
from src.game.mapgen.roadnet.build_city import consume_staged_ai as roadnet_consume_ai

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
# Last exported: 2026-05-30 14:57:45

create_polygon(
    bound_number = 1,
    vertex_coordinates = [
        (-42.23, 30.0, 40.0),
		(-12.23, 30.0, 40.0),
		(-12.23, 30.0, -0.0),
		(-42.23, 30.0, -0.0)])

save_mesh(
    texture_name = [Texture.CHECKPOINT],
    tex_coords = compute_uv(bound_number = 1, tile_x = 4.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 99,
    vertex_coordinates = [
        (-25.0, 0.0, 85.0),
		(25.0, 0.0, 85.0),
		(25.0, 0.0, 70.0),
		(-25.0, 0.0, 70.0)])

save_mesh(
    texture_name = [Texture.CHECKPOINT],
    tex_coords = compute_uv(bound_number = 99, tile_x = 5.00, tile_y = 1.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 999,
    vertex_coordinates = [
        (-50.0, 0.0, 70.0),
		(50.0, 0.0, 70.0),
		(50.0, 0.0, -70.0),
		(-50.0, 0.0, -70.0)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE],
    tex_coords = compute_uv(bound_number = 999, tile_x = 10.00, tile_y = 10.00, angle_degrees = 45.00))


create_polygon(
    bound_number = 861,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-50.0, 0.0, -70.0),
		(10.0, 0.0, -70.0),
		(10.0, 0.0, -130.0),
		(-50.0, 0.0, -130.0)])

save_mesh(
    texture_name = [Texture.GRASS_BASEBALL],
    tex_coords = compute_uv(bound_number = 861, tile_x = 7.00, tile_y = 7.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 202,
	material_index = Material.GRASS,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (10.0, 0.0, -70.0),
		(50.0, 0.0, -70.0),
		(50.0, 0.0, -130.0),
		(10.0, 0.0, -130.0)])

save_mesh(
    texture_name = [Texture.GRASS_WINTER],
    tex_coords = compute_uv(bound_number = 202, tile_x = 5.00, tile_y = 5.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 1,
	cell_type = Room.NO_SKIDS,
	material_index = Material.NO_FRICTION,
	hud_color = Color.SNOW,
    vertex_coordinates = [
        (-50.0, 0.0, -140.0),
		(50.0, 0.0, -140.0),
		(50.0, 0.0, -210.0),
		(-50.0, 0.0, -210.0)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 1, tile_x = 10.00, tile_y = 10.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 862,
	cell_type = Room.TUNNEL,
	hud_color = Color.RED_DARK,
    vertex_coordinates = [
        (50.0, 0.0, -70.0),
		(140.0, 0.0, -70.0),
		(140.0, 0.0, -140.0),
		(50.0, 0.0, -140.0)])

save_mesh(
    texture_name = [Texture.BARRICADE_RED_BLACK],
    tex_coords = compute_uv(bound_number = 862, tile_x = 50.00, tile_y = 50.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 203,
	hud_color = Color.WOOD,
    vertex_coordinates = [
        (50.0, 0.0, 70.0),
		(140.0, 0.0, 70.0),
		(140.0, 0.0, -70.0),
		(50.0, 0.0, -70.0)])

save_mesh(
    texture_name = [Texture.WOOD],
    tex_coords = compute_uv(bound_number = 203, tile_x = 10.00, tile_y = 10.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 2,
	cell_type = Room.DRIFT,
	material_index = Material.WATER,
	hud_color = Color.WATER,
    vertex_coordinates = [
        (50.0, 0.0, -140.0),
		(140.0, 0.0, -140.0),
		(140.0, 0.0, -210.0),
		(50.0, 0.0, -210.0)])

save_mesh(
    texture_name = [Texture.WATER_WINTER],
    tex_coords = compute_uv(bound_number = 2, tile_x = 10.00, tile_y = 10.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 863,
	hud_color = Color.GRASS,
    vertex_coordinates = [
        (-50.0, 0.0, 110.0),
		(-50.0, 0.0, 140.0),
		(140.0, 0.0, 139.71),
		(139.94, 0.0, 110.11)])

save_mesh(
    texture_name = [Texture.GRASS_BASEBALL],
    tex_coords = compute_uv(bound_number = 863, tile_x = 10.00, tile_y = 10.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 999,
	cell_type = Room.NO_SKIDS,
	hud_color = Color.YELLOW_LIGHT,
    vertex_coordinates = [
        (-130.0, 15.0, 70.0),
		(-50.0, 0.0, 70.0),
		(-50.0, 0.0, -0.0)])

save_mesh(
    texture_name = [Texture.BRICKS_MALL],
    tex_coords = compute_uv(bound_number = 999, tile_x = 10.00, tile_y = 10.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 999,
	cell_type = Room.NO_SKIDS,
	hud_color = Color.YELLOW_LIGHT,
    vertex_coordinates = [
        (-50.0, 0.0, 140.0),
		(-50.0, 0.0, 70.0),
		(-130.0, 15.0, 70.0)])

save_mesh(
    texture_name = [Texture.BRICKS_MALL],
    tex_coords = compute_uv(bound_number = 999, tile_x = 10.00, tile_y = 10.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 3,
	cell_type = Room.DRIFT,
	hud_color = Color.ORANGE,
    vertex_coordinates = [
        (-50.0, 0.0, -210.0),
		(50.0, 0.0, -210.0),
		(50.0, 300.0, -1000.0),
		(-50.0, 300.0, -1000.0)])

save_mesh(
    texture_name = [Texture.LAVA],
    tex_coords = compute_uv(bound_number = 3, tile_x = 10.00, tile_y = 100.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 4,
	always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -50.0),
		(10.0, 0.0, -50.0),
		(10.0, 30.0, -50.11),
		(-10.0, 30.0, -50.11)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 4, tile_x = 1.00, tile_y = 1.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 5,
	always_visible = False,
    vertex_coordinates = [
        (-10.0, 0.0, -70.0),
		(-10.0, 30.0, -70.0),
		(10.0, 30.0, -70.0),
		(10.0, 0.0, -70.0)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 5, tile_x = 1.00, tile_y = 1.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 6,
	always_visible = False,
    vertex_coordinates = [
        (-9.99, 30.0, -50.0),
		(-9.99, 30.0, -70.0),
		(-10.0, 0.0, -70.0),
		(-10.0, 0.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 6, tile_x = 1.00, tile_y = 1.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 7,
	always_visible = False,
    vertex_coordinates = [
        (10.0, 0.0, -70.0),
		(9.90, 30.0, -70.0),
		(9.90, 30.0, -50.0),
		(10.0, 0.0, -50.0)])

save_mesh(
    texture_name = [Texture.SNOW],
    tex_coords = compute_uv(bound_number = 7, tile_x = 1.00, tile_y = 1.00, angle_degrees = 0.00))


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
    tex_coords = compute_uv(bound_number = 900, tile_x = 1.00, tile_y = 1.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 250,
    vertex_coordinates = [
        (-82.60, 0.0, -80.0),
		(-50.0, 0.0, -80.0),
		(-50.0, 0.0, -120.0),
		(-82.60, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION],
    tex_coords = compute_uv(bound_number = 250, tile_x = 5.00, tile_y = 5.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 925,
    vertex_coordinates = [
        (-90.0, 14.75, -80.0),
		(-79.0, 14.75, -80.0),
		(-79.0, 14.75, -120.0),
		(-90.0, 14.75, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION],
    tex_coords = compute_uv(bound_number = 925, tile_x = 5.00, tile_y = 5.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 251,
    vertex_coordinates = [
        (-119.01, 0.0, -80.0),
		(-90.0, 0.0, -80.0),
		(-90.0, 0.0, -120.0),
		(-119.01, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.GRASS],
    tex_coords = compute_uv(bound_number = 251, tile_x = 5.00, tile_y = 5.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 252,
    vertex_coordinates = [
        (-160.0, 0.0, -80.0),
		(-119.10, 0.0, -80.0),
		(-119.10, 0.0, -120.0),
		(-160.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE],
    tex_coords = compute_uv(bound_number = 252, tile_x = 5.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 950,
    vertex_coordinates = [
        (-200.0, 0.0, -80.0),
		(-160.0, 0.0, -80.0),
		(-160.0, 0.0, -120.0),
		(-200.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.INTERSECTION],
    tex_coords = compute_uv(bound_number = 950, tile_x = 5.00, tile_y = 5.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 501,
    vertex_coordinates = [
        (20.0, 30.0, -0.0),
		(50.0, 30.0, -0.0),
		(50.0, 12.0, -69.90),
		(20.0, 12.0, -69.90)])

save_mesh(
    texture_name = [Texture.ROAD_3_LANE],
    tex_coords = compute_uv(bound_number = 501, tile_x = 3.00, tile_y = 2.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 1100,
    vertex_coordinates = [
        (20.0, 30.0, 40.0),
		(50.0, 30.0, 40.0),
		(50.0, 30.0, -0.0),
		(20.0, 30.0, -0.0)])

save_mesh(
    texture_name = [Texture.BRICKS_GREY],
    tex_coords = compute_uv(bound_number = 1100, tile_x = 10.00, tile_y = 10.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 502,
    vertex_coordinates = [
        (-10.0, 30.0, 40.0),
		(20.0, 30.0, 40.0),
		(20.0, 30.0, -0.0),
		(-10.0, 30.0, -0.0)])

save_mesh(
    texture_name = [Texture.BUS_RED_TOP],
    tex_coords = compute_uv(bound_number = 502, tile_x = 4.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 599,
    flip=True,      # use this wall to test texture/collision side flipping
    vertex_coordinates = [
        (-10.0, 30.0, 10.0),
		(-10.0, 30.0, 40.0),
		(-10.0, 0.0, 40.0),
		(-10.0, 0.0, 10.0)])

save_mesh(
    texture_name = ["13_WIN"],
    tex_coords = compute_uv(bound_number = 599, tile_x = 10.00, tile_y = 10.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 503,
    vertex_coordinates = [
        (-10.0, 30.0, -0.0),
		(10.0, 30.0, -0.0),
		(10.0, 30.0, -50.0),
		(-10.0, 30.0, -50.0)])

save_mesh(
    texture_name = [Texture.GLASS],
    tex_coords = compute_uv(bound_number = 503, tile_x = 5.00, tile_y = 12.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 206,
	hud_color = Color.RED_LIGHT,
    vertex_coordinates = [
        (50.0, 0.0, -130.0),
		(50.0, 3.0, -135.0),
		(-50.0, 3.0, -135.0),
		(-50.0, 0.0, -130.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN],
    tex_coords = compute_uv(bound_number = 206, tile_x = 15.00, tile_y = 1.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 207,
	hud_color = Color.RED_LIGHT,
    vertex_coordinates = [
        (-50.0, 3.0, -135.0),
		(50.0, 3.0, -135.0),
		(50.0, 0.0, -140.0),
		(-50.0, 0.0, -140.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN],
    tex_coords = compute_uv(bound_number = 207, tile_x = 1.00, tile_y = 10.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 208,
    vertex_coordinates = [
        (-50.0, 0.0, -140.0),
		(-50.01, 0.0, -130.0),
		(-50.0, 3.0, -135.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN],
    tex_coords = compute_uv(bound_number = 208, tile_x = 30.00, tile_y = 30.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 209,
    vertex_coordinates = [
        (50.0, 0.0, -140.0),
		(50.0, 3.0, -135.0),
		(50.01, 0.0, -130.0)])

save_mesh(
    texture_name = [Texture.STOP_SIGN],
    tex_coords = compute_uv(bound_number = 209, tile_x = 30.00, tile_y = 30.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 2220,
    vertex_coordinates = [
        (-160.0, 0.0, -120.0),
		(-160.0, -3.0, -160.0),
		(-200.0, 0.0, -120.0)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2220, tile_x = 3.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 2221,
    vertex_coordinates = [
        (-200.0, 0.0, -120.0),
		(-160.0, -3.0, -160.0),
		(-200.0, -3.0, -160.0)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2221, tile_x = 3.00, tile_y = 4.00, angle_degrees = -45.00))


create_polygon(
    bound_number = 2222,
    vertex_coordinates = [
        (-160.0, -3.0, -160.0),
		(-156.59, -6.0, -204.88),
		(-200.0, -3.0, -160.0)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2222, tile_x = 3.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 2223,
    vertex_coordinates = [
        (-156.59, -6.0, -204.88),
		(-191.82, -6.0, -223.82),
		(-200.0, -3.0, -160.0)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2223, tile_x = 3.00, tile_y = 3.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 2224,
    vertex_coordinates = [
        (-156.59, -6.0, -204.88),
		(-140.06, -9.0, -229.75),
		(-191.82, -6.0, -223.82)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2224, tile_x = 3.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 2225,
    vertex_coordinates = [
        (-140.06, -9.0, -229.75),
		(-165.59, -9.0, -260.54),
		(-191.82, -6.0, -223.82)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2225, tile_x = 3.00, tile_y = 3.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 2226,
    vertex_coordinates = [
        (-140.06, -9.0, -229.75),
		(-117.58, -12.0, -247.47),
		(-165.59, -9.0, -260.54)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2226, tile_x = 3.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 2227,
    vertex_coordinates = [
        (-117.58, -12.0, -247.47),
		(-127.21, -12.0, -286.30),
		(-165.59, -9.0, -260.54)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2227, tile_x = 3.00, tile_y = 3.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 2228,
    vertex_coordinates = [
        (-117.58, -12.0, -247.47),
		(-90.0, -15.0, -254.51),
		(-127.21, -12.0, -286.30)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2228, tile_x = 3.00, tile_y = 3.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 2229,
    vertex_coordinates = [
        (-90.0, -15.0, -254.51),
		(-90.0, -15.0, -294.48),
		(-127.21, -12.0, -286.30)])

save_mesh(
    texture_name = [Texture.FREEWAY],
    tex_coords = compute_uv(bound_number = 2229, tile_x = 3.00, tile_y = 3.00, angle_degrees = 90.00))


create_polygon(
    bound_number = 924,
    vertex_coordinates = [
        (-90.0, -15.0, -254.51),
		(-79.0, -15.0, -254.51),
		(-79.0, -15.0, -294.48),
		(-90.0, -15.0, -294.48)])

save_mesh(
    texture_name = [Texture.INTERSECTION],
    tex_coords = compute_uv(bound_number = 924, tile_x = 5.00, tile_y = 5.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 923,
	hud_color = Color.YELLOW_LIGHT,
    vertex_coordinates = [
        (-79.0, -15.0, -254.51),
		(-90.0, -15.0, -254.51),
		(-90.0, 14.75, -120.0),
		(-79.0, 14.75, -120.0)])

save_mesh(
    texture_name = [Texture.ZEBRA_CROSSING],
    tex_coords = compute_uv(bound_number = 923, tile_x = 5.00, tile_y = 5.00, angle_degrees = 0.00))


create_polygon(
    bound_number = 211,
    vertex_coordinates = [
        (-55.0, 0.0, 343.36),
		(240.35, 0.0, 344.25),
		(247.98, 0.0, 135.52),
		(-50, 0.0, 140.40)])

save_mesh(
    texture_name = [Texture.BRICKS_GREY],
    tex_coords = compute_uv(bound_number = 211, tile_x = 50.00, tile_y = 50.00, angle_degrees = 0.00))

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


def write_cell_row(cell_id: int, cell_type: int, always_visible_data: str, mesh_a2_files: Set[int],
                   h2_cells: Set[int] = frozenset()) -> str:
    # `model` is the engine's cull-flags bitmask (LevelOfDetail.* == CULL_FLAG_* in cellrend.cpp).
    model = LevelOfDetail.DRIFT if cell_id in mesh_a2_files else LevelOfDetail.HIGH
    if cell_id in h2_cells:
        model |= LevelOfDetail.UNKNOWN_4     # 0x100 == CULL_FLAG_H2: also load the split _H2 mesh
    return f"{cell_id},{model},{cell_type}{always_visible_data}\n"


def get_cell_ids(landmark_folder: Path, city_folder: Path) -> Tuple[List[int], Set[int], Set[int]]:
    meshes_regular = []
    seen_regular: Set[int] = set()          # dedup: a cell may now have both _H and _H2 files
    meshes_water_drift = set()
    h2_cells: Set[int] = set()              # cells whose HIGH mesh was split into a secondary _H2

    files = [file for folder in [landmark_folder, city_folder] for file in folder.iterdir()]

    bms_path = FileType.MESH_lowercase          # ".bms"
    for file in files:
        cell_id = int(re.findall(r'\d+', file.name)[0])
        low = file.name.lower()

        if low.endswith(f"_a2{bms_path}"):
            meshes_water_drift.add(cell_id)
        if low.endswith(f"_h2{bms_path}"):
            h2_cells.add(cell_id)

        if low.endswith(bms_path) and cell_id not in seen_regular:
            seen_regular.add(cell_id)
            meshes_regular.append(cell_id)

    return meshes_regular, meshes_water_drift, h2_cells


def calculate_cell_centers(polys: List[Polygon]) -> Dict[int, CellCenter]:
    # Accumulate ALL vertex positions across ALL polygons per cell, then average.
    # Overwriting per-polygon (old behaviour) gave wrong centers for cells with
    # many surfaces (city round-trip), because the last polygon could be a small
    # edge piece far from the actual cell centroid.
    all_positions: Dict[int, List[Tuple[float, float, float]]] = {}

    for poly in polys:
        if poly.cell_id > 0:
            bucket = all_positions.setdefault(poly.cell_id, [])
            for i in poly.vertex_index[:poly.num_verts]:
                bucket.append((vertices[i].x, vertices[i].y, vertices[i].z))

    centers = {}
    for cell_id, positions in all_positions.items():
        center_x, center_y, center_z = calc_center_coords(positions)
        centers[cell_id] = CellCenter(center_x, center_y, center_z, cell_id)

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


def _inherit_city_files(city, hitid: bool, cells: bool, portals: bool, bounds: bool, bms: bool,
                        ai: bool, props: bool, facades: bool, gizmo: bool, extrema: bool) -> None:
    import shutil
    src    = city.path
    prefix = city.prefix

    ok(f"Inheriting city files from {city.name}")

    single_copies = [
        (hitid,   src / f"{prefix}_HITID{FileType.BOUND}", Folder.Shop.Bound / f"{MAP_FILENAME}_HITID{FileType.BOUND}"),
        (cells,   src / f"{prefix}{FileType.CELL}",        Folder.Shop.City  / f"{MAP_FILENAME}{FileType.CELL}"),
        (portals, src / f"{prefix}{FileType.PORTAL}",      Folder.Shop.City  / f"{MAP_FILENAME}{FileType.PORTAL}"),
        (ai,      src / f"{prefix}{FileType.AI}",          Folder.Shop.City  / f"{MAP_FILENAME}{FileType.AI}"),
        (props,   src / f"{prefix}{FileType.PROP}",        Folder.Shop.City  / f"{MAP_FILENAME}{FileType.PROP}"),
        (facades, src / f"{prefix}{FileType.FACADE}",      Folder.Shop.City  / f"{MAP_FILENAME}{FileType.FACADE}"),
        (gizmo,   src / f"{prefix}{FileType.GIZMO}",       Folder.Shop.City  / f"{MAP_FILENAME}{FileType.GIZMO}"),
        (extrema, src / f"{prefix}{FileType.EXTREMA}",     Folder.Shop.City  / f"{MAP_FILENAME}{FileType.EXTREMA}"),
    ]
    for enabled, src_file, dst_file in single_copies:
        if not enabled:
            item(f"[OFF]  {src_file.name}")
            continue
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            item(f"{src_file.name} → {dst_file.name}")
        else:
            item(f"[SKIP] {src_file.name} not found")

    # Per-cell BND files — original has extra collision geometry (walls, kerbs)
    # beyond what's in the BMS surfaces, so polygon counts differ. Inheriting
    # keeps bounding spheres correct for frustum culling.
    for bound_src_dir, bound_dst_dir, label in [
        (src / "BOUNDS" / f"{prefix}CITY", Folder.Shop.Map.BoundCity,     "CITY bounds"),
        (src / "BOUNDS" / f"{prefix}LM",   Folder.Shop.Map.BoundLandmark, "LM bounds"),
    ]:
        if not bound_src_dir.is_dir():
            continue
        if bounds:
            copied = sum(
                1 for f in bound_src_dir.iterdir()
                if (shutil.copy2(f, bound_dst_dir / f.name), True)[1]
            )
            item(f"{label}: {copied} file(s) → {bound_dst_dir.name}")
        else:
            item(f"[OFF]  {label}")

    # BMS mesh files — overwrite generated files with originals for isolation testing.
    for bms_src_dir, bms_dst_dir, label in [
        (src / "MESHES" / f"{prefix}CITY", Folder.Shop.Map.MeshCity,     "CITY meshes"),
        (src / "MESHES" / f"{prefix}LM",   Folder.Shop.Map.MeshLandmark, "LM meshes"),
    ]:
        if not bms_src_dir.is_dir():
            continue
        if bms:
            copied = sum(
                1 for f in bms_src_dir.iterdir()
                if f.suffix.upper() == FileType.MESH.upper()
                and (shutil.copy2(f, bms_dst_dir / f.name), True)[1]
            )
            item(f"{label}: {copied} file(s) → {bms_dst_dir.name}")
        else:
            # Gap-fill only: copy files that weren't generated (e.g. CULL60_H2.BMS)
            copied = 0
            for f in bms_src_dir.iterdir():
                dst = bms_dst_dir / f.name
                if not dst.exists():
                    shutil.copy2(f, dst)
                    copied += 1
            if copied:
                item(f"{label}: {copied} gap-fill file(s) → {bms_dst_dir.name}")


def create_cells(output_file: Path, polys: List[Polygon]) -> None:
    mesh_files, mesh_a2_files, h2_cells = get_cell_ids(Folder.Shop.Map.MeshLandmark, Folder.Shop.Map.MeshCity)

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
            row = write_cell_row(cell_id, cell_type, always_visible_data, mesh_a2_files, h2_cells)
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

    type_breakdown = ", ".join(f"{cell_type_names.get(t, f'type_{t}')}: {count}x"
                              for t, count in sorted(cell_type_counts.items()))

    ok(f"Created cells file{sep()}{len(mesh_files)} cells, range: {min_cell}–{max_cell}")
    item(cell_ids_str)
    detail("Types", type_breakdown)
    
################################################################################################################               
################################################################################################################
#! ======================= MINIMAP ======================= !#

#TODO: refactor and move later
def create_minimap(set_minimap: bool, debug_minimap: bool, debug_minimap_id: bool, minimap_outline_color: str, line_width: float, background_color: str) -> None:
    # No Blender auto-skip: the headless roadnet build needs the minimap too. Still gated by
    # set_minimap, so interactive authoring is unaffected.
    if not set_minimap:
        return

    global hudmap_vertices
    global hudmap_properties

    min_x, min_z, max_x, max_z = calculate_extrema(hudmap_vertices)

    width = int(max_x - min_x)
    height = int(max_z - min_z) 
    
    def draw_polygon(ax, polygon, minimap_outline_color: str, label = None, add_label = False, hud_fill = False, hud_color = None) -> None:
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
    plt.savefig(Folder.Shop.Textures.Bitmap / f"{MAP_FILENAME}640.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color)
    plt.savefig(Folder.Shop.Textures.Bitmap / f"{MAP_FILENAME}320.JPG", dpi = 1000, bbox_inches = "tight", pad_inches = 0.02, facecolor = background_color) 

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
        # Defensive: guard against degenerate geometry (malformed vertices or edges).
        # 'float' with no .z has been observed for large MM2 cities — skip this edge pair.
        if not hasattr(point, 'x') or not hasattr(point, 'y') or not hasattr(self.line, 'z'):
            return float('inf')
        return (point.x * self.line.x) + (point.y * self.line.y) + self.line.z

    # Distance along the line
    def line_pos(self, point, dist):
        x = point.x + self.line.x * dist
        y = point.y + self.line.y * dist
        return (x * self.line.y) - (y * self.line.x)

    def pos_to_point(self, pos):
        if not hasattr(self.line, 'z'):
            return Vector2(0.0, 0.0)
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

            # Landmark/ground cells (bound < CELL_TYPE_SWITCH, e.g. the grass base = 1) are
            # ALWAYS visible and don't need portals. Skipping them is correct for any map and
            # critical when the ground is subdivided into many tiles: otherwise that one cell
            # gains hundreds of edges and the portal graph explodes, making the runtime cull
            # spin (city hangs on the first frame at ~100% CPU).
            if cell1.id < Threshold.CELL_TYPE_SWITCH or cell2.id < Threshold.CELL_TYPE_SWITCH:
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
        _min = Vector3.read(f)
        _max = Vector3.read(f)
        
        vertex_c = None
        if edge_count == Shape.TRIANGLE:
            vertex_c = Vector3.read(f)

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
                # Write a valid zero-portal header so the game reads magic+count cleanly.
                write_pack(f, '<I', Magic.PORTAL)
                write_pack(f, '<I', 0)

            else:
                _, portal_tuples = prepare_portals(polys, vertices)

                portals = []

                cls.write_n(f, portal_tuples)

                for cell_1, cell_2, v1, v2 in portal_tuples:
                    # OPEN_AREA (0x2): resets all clipping planes at each portal crossing.
                    # ACTIVE (0x1) is implicit — the engine treats all portals as active
                    # regardless of that bit. Reference: hitid_to_ptl.py by 0x1F9F1.
                    flags = Portal.OPEN_AREA
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
                    _min.write(f)
                    _max.write(f)

                ok(f"Created {len(portal_tuples)} portal(s)")
                cls.debug(portals, debug_portals, Folder.Debug.Portals / f"{MAP_FILENAME}_PTL.txt")            

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
        def v(vec): return f"{vec.x:.2f}, {vec.y:.2f}, {vec.z:.2f}"
        vertex_c_line = f"    Vertex C\t{v(self.vertex_c)}" if self.vertex_c is not None else ""
        return f"""
PORTAL
    Flags:\t\t{self.flags}
    EdgeCount:\t{self.edge_count}
    Gap 2:\t\t{self.gap_2}
    Cell 1:\t\t{self.cell_1}
    Cell 2:\t\t{self.cell_2}
    Height:\t\t{self.height:.2f}
    Min:\t\t{v(self._min)}
    Max:\t\t{v(self._max)}
{vertex_c_line}"""
 
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

if set_cruise_start:
    street_list = street_list + [cruise_start]

###################################################################################################################
#! ======================= CALL FUNCTIONS ======================= !#

_fixed_prop_list = []  # populated inside the AR block; also read by the Blender section
mm2_prop_net = None   # MM2 BAI road network -> procedural scenery props (lights/hydrants/etc.)
# Per-city converted-DDS dir (e.g. custom_london): both the DDS file-copy AND the texsheet append must
# use it so city-unique textures reach the build. Read from the MM2_CITY opts up-front.
mm2_custom_dir = None
if MM2_CITY:
    mc_opts = MM2_CITY[1] if (isinstance(MM2_CITY, (tuple, list)) and len(MM2_CITY) > 1) else {}
    mm2_custom_dir = (mc_opts.get("custom_dds_dir") if isinstance(mc_opts, dict) else None) or None


def load_mm2_cell_overrides() -> Optional[dict]:
    """Cells edited in Blender and exported by 'Export MM2 Cell Edits', or None if there are none."""
    overrides_file = (Folder.Src.User.Mm2Edits /
                      f"{MAP_FILENAME}{Mm2CellPreview.OVERRIDES_SUFFIX}{FileType.JSON}")
    if not overrides_file.is_file():
        return None

    try:
        cells = json.load(open(overrides_file)).get("cells") or None
    except Exception as error:
        item(f"WARNING: {overrides_file.name} unreadable ({error}) — ignored")
        return None

    if cells:
        ok(f"MM2: loaded {len(cells)} Blender cell override(s){sep()}"
           f"delete {overrides_file.name} to build pristine again")

    return cells

# Debug-only: force roadnet AI on even for a curves+height map, to reproduce the remaining
# ambient-collision crash against a debug build. See stage_roadnet_ai_if_safe.
FORCE_ROADNET_AI = False


def clear_geometry_buffers() -> None:
    """Drop every in-memory city buffer so a generator can replace the whole map from scratch."""
    for buffer in (vertices, texture_names, texcoords_data, polygons_data,
                   hudmap_vertices, hudmap_properties, _mesh_segments, polys):
        buffer.clear()
    polys.append(Default.POLYGON)


def resolve_roadnet_network(roadnet_city):
    """Turn the ROADNET_CITY setting into a RoadNetwork.

    Accepts a RoadNetwork, a callable returning one, a preset name, the literal "blender" (compile
    the roads authored in the Blender Road Builder), or a (cols, rows) pair for a grid city.
    """
    if isinstance(roadnet_city, RoadNetwork):
        return roadnet_city

    if callable(roadnet_city):
        return roadnet_city()

    if isinstance(roadnet_city, str):
        if roadnet_city.lower() == "blender":
            # Phase 2: compile the roads authored in the Blender Road Builder (RS_* spines).
            from src.integrations.blender.road_to_roadnet import blender_roads_network
            return blender_roads_network()
        return build_preset(roadnet_city)

    if isinstance(roadnet_city, (tuple, list)) and len(roadnet_city) == 2:
        return grid_city(int(roadnet_city[0]), int(roadnet_city[1]))

    raise ValueError("ROADNET_CITY must be a preset name, (cols,rows), a RoadNetwork, or a "
                     f"callable; got {type(roadnet_city)}")


def validate_roadnet_network(roadnet_network) -> None:
    """Surface structural ERRORs + AI-safe-envelope WARNINGs BEFORE building, so a bad graph fails
    with a clear, actionable message instead of crashing mid-compile."""
    issues = validate_network(roadnet_network)
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    warnings = [issue for issue in issues if issue.severity == "WARN"]
    network_name = getattr(roadnet_network, "name", "?")

    if issues:
        ok(f"roadnet: network '{network_name}' check - {summarize_issues(issues)}")
        for issue in warnings:
            ok(f"   WARN  {issue.message}")
        for issue in errors:
            ok(f"   ERROR {issue.message}")

    if errors:
        raise ValueError(f"roadnet network '{network_name}' has {len(errors)} structural error(s) "
                         f"(listed above) - fix the graph or choose another ROADNET_CITY")


def stage_roadnet_ai_if_safe(roadnet_network, roadnet_compiled, polygon_count: int) -> None:
    """Stage the AI map + ROAM.AIMAP, unless the graph is one the engine's AI cannot survive.

    AI on a curves+HEIGHT map still corrupts memory in the ambient/collision AI: the engine's
    spatial AI assumes a flat city, so the rails reset fine but DetectAmbientCollision jumps a
    garbage pointer. The opponent crash IS fixed (Open1560 forces 0 race opponents in roam mode).
    Until the ambient layer is fixed too, a curves+height map runs with NO AI --- the player still
    drives, crash-free. Flat / straight-terraced / flat-curved maps keep full traffic. A road has to
    be BOTH curved AND graded to trip this, so zoned slopes+curves keep full AI.
    """
    if FORCE_ROADNET_AI or not curved_grade(roadnet_network):
        stage_roadnet_ai(roadnet_compiled)
        write_roam_aimap(roadnet_compiled, Folder.Shop.Map.Race, density = 1.0, num_cops = 2)

    ok(f"roadnet: replaced city with {polygon_count} polygons + staged AI + ROAM.AIMAP "
       f"({len(roadnet_network.nodes)} nodes / {len(roadnet_compiled.sections)} roads)")


def audit_roadnet_collision(roadnet_compiled) -> None:
    """Warn about quads the car would fall through. Never fatal --- the map is still playable."""
    try:
        non_planar, down_facing, _ = audit_collision(roadnet_compiled)
    except Exception:
        return

    if non_planar or down_facing:
        ok(f"roadnet: COLLISION WARNING - {non_planar} non-planar + {down_facing} down-facing "
           f"quads would FALL THROUGH")


def generate_roadnet_races(roadnet_network, roadnet_compiled) -> None:
    """Build the graph's races: RACE_0 is a checkpoint race near the change (0 opponents/cops/
    ambient, so it works on hilly maps too); CIRCUIT_0 is a real loop with OPPONENTS that navigate
    the intersections, and is only generated on non-curve+height maps because opponents crash on
    those. Boot `-race 0` for the checkpoints, `-circuit 0` to race the opponents."""
    try:
        Folder.Shop.Map.Race.mkdir(parents = True, exist_ok = True)
        race_data = roadnet_checkpoint_race(roadnet_compiled)
        feature_spawns = getattr(roadnet_compiled.network, "feature_spawns", None) or []
        checkpoint_names = [name for (_, _, name) in feature_spawns]

        if not curved_grade(roadnet_network) and not checkpoint_names:
            try:
                race_data.update(roadnet_circuit_race(roadnet_compiled, num_opponents = 5))
                ok(f"roadnet: circuit race + "
                   f"{race_data['CIRCUIT_0']['aimap']['num_of_opponents']} opponents")
            except Exception as error:
                ok(f"roadnet: circuit race skipped ({error})")

        create_races(race_data)

        if checkpoint_names:
            create_map_info(Folder.Shop.Tune / f"{MAP_FILENAME}{FileType.CITY_INFO}",
                            blitz_race_names, circuit_race_names, checkpoint_names)
            ok(f"roadnet: showcase {len(checkpoint_names)} checkpoint races -> "
               f"{', '.join(checkpoint_names)}")

        # The engine reads the base "<race>.aimap" on default difficulty -> copy each _P variant.
        for aimap_p in Folder.Shop.Map.Race.glob("*.AIMAP_P"):
            shutil.copy(aimap_p, aimap_p.with_suffix(".AIMAP"))
    except Exception as error:
        ok(f"roadnet: races skipped ({error})")



def import_mm2_races(mm2_races_dir: str) -> None:
    """Import a city's MM2 races (blitz / checkpoint / circuit) so they are selectable in MM1 with
    the same spawn and checkpoints as MM2.

    Writes the MM1 race files into the build's RACE folder and re-registers the CINFO under the real
    MM2 race names, which live in the city's own .cinfo at <mm2core>/tune/<city>.cinfo --- a sibling
    of the race folder itself.
    """
    races_dir = Path(mm2_races_dir)
    Folder.Shop.Map.Race.mkdir(parents = True, exist_ok = True)

    city_cinfo = races_dir.parent.parent / "tune" / f"{races_dir.name}{FileType.CITY_INFO}"
    blitz_names, checkpoint_names, circuit_names, _ = convert_mm2_races(
        str(races_dir), str(Folder.Shop.Map.Race),
        cinfo_path = str(city_cinfo) if city_cinfo.exists() else "", log = item)

    create_map_info(Folder.Shop.Tune / f"{MAP_FILENAME}{FileType.CITY_INFO}",
                    blitz_names, circuit_names, checkpoint_names)
    ok(f"mm2: imported MM2 races -> {len(blitz_names)} blitz, {len(checkpoint_names)} checkpoint, "
       f"{len(circuit_names)} circuit (real MM2 names from cinfo)")


def collect_mm2_pathset_props(pathset_path):
    """Hand-placed scenery from <city>/props.pathset: trees, palms, lamps, benches and signs at
    their real MM2 world coords + facing (1:1 frame, no mirror).

    MM2's own .pkg prop meshes do not load in MM1, so each MM2 model maps to the nearest MM1
    placeholder --- locations and angles first, better meshes later.
    """
    props, skipped = pathset_props(str(pathset_path))
    ok(f"mm2: {len(props)} prop(s) from props.pathset "
       f"(skipped {sum(skipped.values())} with no MM1 placeholder)")

    return props


def collect_mm2_density_props(rules_dir, raw_psdl_path):
    """Per-road street furniture at MM2's REAL density: a 1:1 reproduction of MM2's own procedural
    placement (propdefs.csv / proprules.csv + the .psdl propRule/paths), walked exactly like MM2
    walks each road's two sidewalks."""
    # .psdl fallback, used only when raw_psdl.json was not patched with the rule bytes:
    # <city_dir>/../<cityname>.psdl, e.g. .../city/sf/ -> .../city/sf.psdl
    psdl_path = rules_dir.parent / (rules_dir.name + FileType.MM2_GEOMETRY)
    props = list(mm2_props.generate(str(raw_psdl_path), str(rules_dir),
                                    psdl_path = str(psdl_path), log = item))
    ok(f"mm2: + {len(props)} per-road furniture (1:1 MM2 propdefs/proprules)")

    return props


def collect_mm2_traffic_lights(bai_path, json_path):
    """Traffic lights, 1:1 from the BAI's STORED per-road-end (position, facing) verts.

    The PSDL-intersection synthesis over-placed badly (~814 vs SF's real 283), so it is only the
    fallback for a city with no .bai configured.
    """
    if bai_path and Path(bai_path).exists():
        props = list(mm2_props.bai_traffic_lights(bai_path, log = item))
        if props:
            ok(f"mm2: + {len(props)} traffic lights (1:1 from BAI stored data)")
    else:
        props = list(mm2_props.intersection_traffic_lights(json_path, log = item))
        if props:
            ok(f"mm2: + {len(props)} intersection traffic lights (synthesised, no BAI)")

    return props


def collect_mm2_legacy_props(mm2_prop_net):
    """LEGACY shortcut: approximate furniture from the road graph (lamps / benches / bins).

    Its trees are dropped because the pathset carries the real ones, and the props it does keep are
    remapped onto the real converted MM2 meshes.
    """
    remap = {Prop.LIGHT_SIDEWALK: (Mm2Prop.LAMP, BangerFlags.BREAKABLE_GLOW),
             Prop.BENCH: (Mm2Prop.BENCH, BangerFlags.BREAKABLE)}
    dropped = {Prop.TREE_SLIM, Prop.TREE_WIDE}

    props = []
    for prop in generate_props(mm2_prop_net, hydrants = False):
        if prop["name"] in dropped:
            continue

        remapped = remap.get(prop["name"])
        if remapped:
            prop["name"], prop["flags"] = remapped
        props.append(prop)

    return props


def collect_mm2_props(json_path, options, pathset_path, bai_path, mm2_prop_net, legacy_props):
    """Assemble the full MM2 prop list: hand-placed pathset scenery, then per-road furniture and
    traffic lights, falling back to procedural road-graph scenery when a city has neither."""
    pathset = Path(pathset_path) if pathset_path else None
    has_pathset = bool(pathset and pathset.exists())

    prop_list = collect_mm2_pathset_props(pathset) if has_pathset else []

    # The density rules run INDEPENDENTLY of the hand-placed pathset: NY ships propdefs/proprules
    # but no city props.pathset, so the rules dir falls back to the facades.csv folder.
    facades_csv = options.get("facades_csv")
    rules_dir = (pathset.parent if has_pathset else
                 Path(facades_csv).parent if facades_csv else None)
    raw_psdl_path = Path(json_path.replace("expanded_psdl.json", "raw_psdl.json"))

    use_density_rules = (not legacy_props and rules_dir
                         and (rules_dir / "propdefs.csv").exists() and raw_psdl_path.exists())

    if use_density_rules:
        prop_list += collect_mm2_density_props(rules_dir, raw_psdl_path)
        prop_list += collect_mm2_traffic_lights(bai_path, json_path)
    elif has_pathset:
        legacy = collect_mm2_legacy_props(mm2_prop_net)
        prop_list += legacy
        ok(f"mm2: + {len(legacy)} per-road furniture (LEGACY approximate density)")
    elif not prop_list:
        prop_list = generate_props(mm2_prop_net)
        ok(f"mm2: generated {len(prop_list)} scenery prop(s) along the MM2 road graph")

    return prop_list


#* ----------------------------------------------------------------------------------------------------------------

if not SKIP_AR_CREATION:
    # Setup
    copy_custom_textures_to_shop(Path(mm2_custom_dir) if mm2_custom_dir else Folder.Src.User.Textures.Custom,
                                 Folder.Shop.Textures.Opaque)
    copy_carsim_files_to_shop(Folder.Resources.Editor.Tune.CarSimulation, Folder.Shop.Tune, FileType.CAR_SIMULATION)
    ensure_empty_mm_dev_folder(Folder.MidtownMadness.DevCityMap)
    # Wipe the per-cell SHOP output: the packer walks the WHOLE SHOP, so orphaned BND/BMS from an
    # earlier layout would ship in the .AR. This build rewrites only the cells it needs, so every
    # other cell must be gone. Single-file outputs (.CELLS/.PTL/HITID) are overwritten anyway.
    for stale_dir in (Folder.Shop.Map.BoundCity, Folder.Shop.Map.MeshCity,
                      Folder.Shop.Map.BoundLandmark, Folder.Shop.Map.MeshLandmark):
        if stale_dir.is_dir():
            shutil.rmtree(stale_dir, ignore_errors=True)
        stale_dir.mkdir(parents = True, exist_ok = True)
    ok("Wiped stale per-cell BND/BMS from SHOP (clean build, no leftovers)")
    create_commandline(Folder.MidtownMadness.Root / f"commandline{FileType.TEXT}", no_ui, no_ui_type, no_ai, set_music, less_logs, more_logs)
    create_map_info(Folder.Shop.Tune / f"{MAP_FILENAME}{FileType.CITY_INFO}", blitz_race_names, circuit_race_names, checkpoint_race_names)
    edit_and_copy_bangerdata_to_shop(prop_properties, Folder.Resources.Editor.Tune.BangerData, Folder.Shop.Tune, FileType.BANGER_DATA)

    # Player data
    if set_player_data:
        apply_player_profile()

    # Races
    if set_races:
        create_races(race_data)
    if set_cops_and_robbers:
        create_cops_and_robbers(Folder.Shop.Map.Race / f"COPSWAYPOINTS{FileType.CSV}", cops_and_robbers_waypoints)

    # ROADNET (opt-in): replace ALL hand-authored / exported polygons with geometry built
    # from one road-network graph, and stage its AI. Runs HERE — after the polygon region
    # and outside it — so the editor's "Export Polygons" can never wipe it (the previous
    # in-region block kept getting overwritten). Geometry + AI come from the same vertices.
    roadnet_compiled = None   # set when ROADNET_CITY is active; used later to auto-generate scenery
    if ROADNET_CITY:
        roadnet_network = resolve_roadnet_network(ROADNET_CITY)
        validate_roadnet_network(roadnet_network)

        clear_geometry_buffers()

        roadnet_compiled = RoadNetworkCompiler().compile(roadnet_network)
        polygon_count = emit_roadnet_city(roadnet_compiled, create_polygon, save_mesh, compute_uv)

        stage_roadnet_ai_if_safe(roadnet_network, roadnet_compiled, polygon_count)
        audit_roadnet_collision(roadnet_compiled)
        generate_roadnet_races(roadnet_network, roadnet_compiled)

    # MM2 -> MM1 (opt-in): replace ALL polygons with tessellated MM2 PSDL geometry
    # (wilkovatch/psdl-import 'expanded_psdl.json'). Phase-1 = player-only drivable shell:
    # real geometry + collision, MM1 placeholder textures, every cell always-visible (no portals).
    # MM2_CITY = "path/to/expanded_psdl.json"  OR  ("path", {"mirror_x": False, "grid_cells": 14, ...})
    if MM2_CITY:
        clear_geometry_buffers()

        if isinstance(MM2_CITY, (tuple, list)):
            mm2_json, mm2_options = MM2_CITY[0], (MM2_CITY[1] if len(MM2_CITY) > 1 else {})
        else:
            mm2_json, mm2_options = MM2_CITY, {}
        mm2_min_ai = bool(mm2_options.pop("min_ai", False))
        mm2_bai_path = mm2_options.pop("bai_path", None)   # Phase-2: real BAI AI source (not a Mm2Options field)
        # DIRECT-AI toggle (opt-in): write the BAI's REAL 3D lane/sidewalk geometry straight into
        # .road (preserves hills/one-way/curves+grades), bypassing the lossy roadnet rebuild.
        # DEFAULT OFF -> the hybrid roadnet path below stays the shipped default.
        mm2_bai_direct = bool(mm2_options.pop("bai_direct", False))
        mm2_races_dir = mm2_options.pop("mm2_races", None)   # MM2 race folder (not an Mm2Options field)
        mm2_pathset_path = mm2_options.pop("props_pathset", None)  # MM2 props.pathset (not a Mm2Options field)
        # 1:1 PROCEDURAL FURNITURE (default): reproduce MM2's propdefs/proprules placement exactly
        # (src/game/mapgen/mm2/mm2_props). Set "legacy_props": True in the MM2_CITY opts to fall back
        # to the old approximate roadnet.scenery.generate_props furniture (hydrants/grass-trees/etc.).
        mm2_legacy_props = bool(mm2_options.pop("legacy_props", False))
        mm2_custom_dir = mm2_options.get("custom_dds_dir") or None  # per-city DDS dir for the texsheet append
        mm2_stats = emit_mm2_city(create_polygon, save_mesh, compute_uv, mm2_json,
                                  Mm2Options(**mm2_options), overrides = load_mm2_cell_overrides())
        ok(f"mm2: imported {mm2_stats['polygons']} polygons into {mm2_stats['cells']} cells "
           f"(always-visible, no portals)")
        # BOUNDS/COLLISION FIX (FALL-THROUGH): report drivable sliver tris dropped (their rounded
        # edge half-planes would degenerate -> point-in-poly rejects -> car falls through).
        rej_s = mm2_stats.get("rejected_slivers", 0)
        if rej_s:
            ok(f"mm2: rejected {rej_s} sliver DRIVABLE poly(s) (fall-through guard)")
        # Per-poly MM2 obj_type aligned to `polys` (filler at index 0, then one entry per emitted
        # poly in creation order). Consumed by the prop ground-snap to skip building roofs/podiums
        # (BUG A: traffic-lights were riding up onto buildings). Captured HERE, right after emit, so
        # the 1:1 alignment with polys[1:] is guaranteed before any later geometry could touch polys.
        mm2_poly_types = [None] * len(polys)
        ot_list = mm2_stats.get("obj_types") or []
        for _i, _t in enumerate(ot_list):
            if 1 + _i < len(mm2_poly_types):
                mm2_poly_types[1 + _i] = _t
        item(", ".join(f"{t}: {c}x" for t, c in mm2_stats['textures'].items()))

        if mm2_races_dir:
            import_mm2_races(mm2_races_dir)

        # DIAGNOSTIC scaffold: a tiny roadnet AI grid so the city has an AI map (HasAIMap=true),
        # a ROAM.AIMAP and a checkpoint race + cinfo - matching what a normal/roadnet city has.
        # Tests whether the player-car-audio boot crash is caused by a city with no AI/race data.
        # The AI rails are a small grid near origin (geometry stays MM2); density 0 = no traffic.
        if mm2_min_ai:
            # A MINIMAL 2-node road segment placed so node 0 sits EXACTLY on the MM2 spawn road
            # point (same pipeline coord frame as the MM2 geometry). spawn_near snaps to that node,
            # so the player spawns on a real MM2 surface -> GetStartCell's down-ray hits a poly.
            mm2_spawn = mm2_options.get("spawn_xz", (0.0, 0.0))
            _sx, _sz = float(mm2_spawn[0]), float(mm2_spawn[1])
            mm2_bai = mm2_bai_path
            if mm2_bai and mm2_bai_direct:
                # DIRECT-AI PATH (opt-in via "bai_direct": True): write the BAI's real 3D geometry
                # straight into .road -> rails follow SF's hills, one-way roads stay one-way, curved
                # + graded roads are kept, and NO mid-road spurious intersections (the engine
                # regenerates intersections from pinched road endpoints). No compiled roadnet, so
                # cops aren't seeded and procedural props fall back off (pathset props still work).
                direct_stats = stage_bai_direct(mm2_bai, MAP_FILENAME)
                # PROPS: still compile the roadnet graph (cheap) purely to feed mm2_prop_net, so the
                # pathset/furniture prop list + its texsheet sync (copy_custom_prop_assets) run EXACTLY
                # like the default path. (Setting this None drops the custom-prop textures from
                # GLOBAL.TSH -> FATAL "texture not in texsheet" on the first banger, e.g. mm2hotdog.)
                # The roadnet AI itself is NOT staged here -- the DIRECT .road above wins.
                mm2_network, _ = build_bai_network(mm2_bai)
                mm2_network.spawn_near = (_sx, _sz)
                mm2_prop_net = RoadNetworkCompiler().compile(mm2_network)

                # No compiled roadnet drives the AI here, so ROAM gets ambient traffic and no cops.
                write_roam_aimap(None, Folder.Shop.Map.Race, density = 1.0, num_cops = 0)
                ok(f"mm2: staged DIRECT BAI AI ({direct_stats['written']} roads, "
                   f"{direct_stats['one_way']} one-way, {direct_stats['skipped_loop']} loops "
                   f"skipped) + AMBIENT traffic [real 3D rails]")
            elif mm2_bai:
                # Phase-2 EXPERIMENTAL (DEFAULT): the REAL SF road graph from the MM2 .bai (379 roads /
                # 214 intersections), so traffic drives actual SF streets instead of the 2-node stub.
                # CAVEAT: roadnet AI is FLAT while SF is hilly -> cars sit at the wrong height on
                # slopes (per-vertex-Y rails are a known hard problem). Spawn area is ~sea level.
                mm2_network, bai_stats = build_bai_network(mm2_bai)
                mm2_network.spawn_near = (_sx, _sz)
                mm2_compiled = RoadNetworkCompiler().compile(mm2_network)
                mm2_prop_net = mm2_compiled   # reuse the BAI road graph for procedural scenery props
                stage_roadnet_ai(mm2_compiled)
                # ambient traffic ONLY: cops crash on Reset (aiVehiclePolice::Reset ->
                # DeterminePerpMapComponent) on this network; ambient cars drive fine. num_cops=0.
                # TEMP: detailed INST buildings finer-partition the cells -> ambient cars near them hit
                # cellAtPos=-999 and fall (cascade crash). Until that buildings<->AI-cell interaction is
                # fixed, drop ambient density to 0 when buildings are baked in (player + races still work).
                mm2_ambient = 1.0   # full ambient traffic (re-testing the buildings<->AI-cell interaction)
                write_roam_aimap(mm2_compiled, Folder.Shop.Map.Race, density=mm2_ambient, num_cops=0)
                ok(f"mm2: staged REAL BAI AI ({bai_stats['edges']} roads / {len(mm2_network.nodes)} "
                   f"intersections) + AMBIENT traffic (no cops) [terrain-following AI]")
            else:
                mm2_network = RoadNetwork(name="MM2Stub")
                mm2_network.add_node((_sx, _sz), node_id=0)
                mm2_network.add_node((_sx + 40.0, _sz), node_id=1)
                mm2_network.add_edge(0, 1, lanes_fwd=1, lanes_rev=1)
                mm2_network.spawn_near = (_sx, _sz)
                mm2_compiled = RoadNetworkCompiler().compile(mm2_network)
                stage_roadnet_ai(mm2_compiled)
                write_roam_aimap(mm2_compiled, Folder.Shop.Map.Race, density=0.0, num_cops=0)
                # NB: deliberately NO checkpoint race here - it would hijack the cruise spawn to the
                # grid origin (empty space). We keep only the AI map + ROAM so HasAIMap=true; the
                # car spawns at our base=True MM2 road poly.
                ok("mm2: staged minimal AI map + ROAM (HasAIMap diagnostic, no race spawn)")

    # Map
    # check_bound_numbers(polys)

    total_polys = len(polys) - 1  # Exclude default polygon at index 0
    quads = sum(1 for poly in polys[1:] if poly.is_quad)
    triangles = total_polys - quads
    ok(f"Created {total_polys} polygon(s){sep()}triangles: {triangles}x, quads: {quads}x, vertices: {len(vertices)}x")

    # Texture usage statistics
    texture_counter = Counter(texture_names)
    unique_textures = len(texture_counter)
    all_textures_str = ", ".join(f"{tex}: {count}x" for tex, count in texture_counter.items())
    ok(f"Utilized {unique_textures} unique texture(s)")
    item(all_textures_str)

    flush_meshes()

    if not (inherit_city and inherit_cells):
        create_cells(Folder.Shop.City / f"{MAP_FILENAME}{FileType.CELL}", polys)

    # Ground-plane polygon filter — used for both HITID and portal generation.
    # For MM2 cities: use a DRIVABLE allowlist rather than a |ny| threshold. mm2_poly_types
    # is captured right after emit_mm2_city (before INST buildings are added), so INST polys
    # have no entry in poly_id_to_type and are excluded by the allowlist — avoiding bucket
    # overflow from INST building roofs (horizontal |ny|≈1, huge vertex/polygon counts).
    # For non-MM2 builds (roadnet/manual): fall back to the normal |ny|>=0.3 height filter.
    _DRIVABLE_OBJ = frozenset((
        "road", "divided_road", "walkway", "road_triangle_fan",
        "triangle_fan", "sidewalk_strip", "crosswalk",
    ))
    # Steep-but-drivable rescue band: ramps, banked roads and hill crests sit below the |ny|>=0.3
    # ground filter yet still have a real XZ footprint the car drives across. Anything flatter than
    # this is a near-vertical curb riser or road-edge wall --- no footprint, not drivable, and
    # including it would only bloat the grid and worsen bucket overflow.
    STEEP_DRIVABLE_MIN_NY = 0.05
    UNCOVERED_REPORT_LIMIT = 15
    poly_types = globals().get("mm2_poly_types")
    # Build id→type map so we can filter O(1) per poly (list is indexed 1:1 with polys).
    poly_id_to_type = (
        {id(polys[i]): poly_types[i] for i in range(min(len(polys), len(poly_types)))}
        if poly_types else {}
    )
    if poly_types:
        # MM2 build: only DRIVABLE-typed PSDL polys. INST polys (absent from poly_id_to_type)
        # are visual-only geometry and must not appear in the HITID ground/collision mesh.
        _ground_polys = [p for p in polys if poly_id_to_type.get(id(p)) in _DRIVABLE_OBJ]
    else:
        _ground_polys = [p for p in polys if abs(p.plane_normal.y) >= 0.3]

    # BOUNDS/COLLISION FIX (SLIDE / cell=0 / no car control): the HITID cell-lookup grid is what
    # the engine uses to resolve which RoomId/poly is under the car. The plain |ny|>=0.3 filter
    # EXCLUDES steep-but-drivable surfaces — ramps, banked roads, hill crests — so on those the
    # per-cell BND collision plane exists but the HITID grid returns cell 0 -> the car gets no
    # surface RoomId -> it slides with no control. FIX: force every DRIVABLE MM2 obj_type
    # (road/divided/walkway/crosswalk/sidewalk/triangle_fan) into the HITID grid regardless of ny,
    # while leaving the (ny>=0.3) set untouched for portal generation. mm2_poly_types is indexed
    # 1:1 with `polys` (index 0 = filler); absent (None) for non-MM2 builds -> falls back to the
    # plain ground set, so this is a no-op for roadnet/manual cities.
    if poly_types:
        ground_set = set(id(p) for p in _ground_polys)
        hitid_polys = list(_ground_polys)
        added_count = 0

        for poly_index, poly in enumerate(polys):
            if id(poly) in ground_set:
                continue

            obj_type = poly_types[poly_index] if poly_index < len(poly_types) else None
            if obj_type in _DRIVABLE_OBJ and abs(poly.plane_normal.y) >= STEEP_DRIVABLE_MIN_NY:
                hitid_polys.append(poly)
                added_count += 1

        if added_count:
            ok(f"HITID: forced {added_count} steep/banked DRIVABLE poly(s) into the cell grid "
               f"(0.05<=|ny|<0.3, would have slid) -> {len(hitid_polys)} total ground polys")
    else:
        hitid_polys = _ground_polys

    if not (inherit_city and inherit_hitid):
        # 300x300 grid keeps HITID.BND around 6.5 MB (u32 row_buckets are 4 bytes each,
        # adding ~0.5 MB over the old u16 build). mkar.exe fails silently above ~8 MB
        # because its internal size field is 23-bit; tested: 11 MB (793x778 + u32) → exit 1.
        hitid_xd = 300 if set_hitid_grid else 0
        hitid_zd = 300 if set_hitid_grid else 0

        overflow_note = "15-bit safe" if len(hitid_polys) <= 32767 else "WOULD OVERFLOW 15-bit -> u32 fix active"
        ok(f"HITID: {len(hitid_polys)} poly(s) -> grid {hitid_xd}x{hitid_zd} ({overflow_note})")

        Bounds.create(
            Folder.Shop.Bound / f"{MAP_FILENAME}_HITID{FileType.BOUND}",
            vertices, hitid_polys,
            Folder.Debug.Bounds / f"{MAP_FILENAME}{FileType.TEXT}",
            debug_bounds,
            grid_x_dim=hitid_xd,
            grid_z_dim=hitid_zd,
        )

    # Build-time coverage check: any HITID poly with cell_id=0 has RoomId=0 in the BND file.
    # The engine returns RoomId=0 from the grid lookup -> no surface physics -> car drifts.
    # These are the "bound but no cell" polygons that show up in-game as loss-of-control zones.
    uncovered_hitid = [p for p in hitid_polys if p.cell_id == 0]

    if uncovered_hitid:
        ok(f"HITID COVERAGE: {len(hitid_polys) - len(uncovered_hitid)}/{len(hitid_polys)} poly(s) have a cell")
        item(f"UNCOVERED (cell_id=0, DRIFT RISK): {len(uncovered_hitid)} poly(s) -> fix their cell assignment")

        for poly in uncovered_hitid[:UNCOVERED_REPORT_LIMIT]:
            centroid_x = sum(vertices[vi].x for vi in poly.vertex_index[:poly.num_verts]) / max(1, poly.num_verts)
            centroid_z = sum(vertices[vi].z for vi in poly.vertex_index[:poly.num_verts]) / max(1, poly.num_verts)
            item(f"  mat={poly.material_index}  centroid=({centroid_x:.1f}, {centroid_z:.1f})")

        if len(uncovered_hitid) > UNCOVERED_REPORT_LIMIT:
            item(f"  ... and {len(uncovered_hitid) - UNCOVERED_REPORT_LIMIT} more")
    else:
        ok(f"HITID coverage: all {len(hitid_polys)} HITID poly(s) have a cell (zero drift-from-cell=0 risk)")

    if not (inherit_city and inherit_bounds):
        write_per_cell_bounds(vertices, polys)

    if not (inherit_city and inherit_portals):
        Portals.write_all(
            Folder.Shop.City / f"{MAP_FILENAME}{FileType.PORTAL}",
            _ground_polys, vertices,
            lower_portals, empty_portals,
            debug_portals
        )

    if inherit_city:
        _inherit_city_files(inherit_city, inherit_hitid, inherit_cells, inherit_portals, inherit_bounds, inherit_bms,
                            inherit_ai, inherit_props, inherit_facades, inherit_gizmo, inherit_extrema)

    aiStreetEditor.create(
        street_list,
        set_ai_streets, set_reverse_ai_streets
    )

    # ROADNET AI: if a road-network was built (Blender "Road Net" button or the ROADNET_CITY
    # block staged it), move its .road/.map into the dev folder NOW — after the normal AI pass
    # and after the dev-folder clear — so roadnet AI wins and survives. No-op if nothing staged.
    roadnet_ai_n = roadnet_consume_ai(Folder.MidtownMadness.DevCityMap, MAP_FILENAME)
    if roadnet_ai_n:
        ok(f"roadnet AI: {roadnet_ai_n} file(s) -> {Folder.MidtownMadness.DevCityMap.name}")

    mm2_facade_list, facades_on = facade_list, set_facades
    if roadnet_compiled is not None:
        # Auto-generate building fronts around the block perimeters from the road graph.
        from src.game.mapgen.roadnet.scenery import generate_facades as gen_fac
        mm2_facade_list = gen_fac(roadnet_compiled)
        facades_on = True
        ok(f"roadnet: generated {len(mm2_facade_list)} facade(s)")
    FacadeEditor.create(
        Folder.Shop.City / f"{MAP_FILENAME}{FileType.FACADE}",
        mm2_facade_list,
        facades_on,
        debug_facades
    )

    Physics.edit(
        Folder.Resources.Editor.Physics / f"PHYSICS{FileType.DATABASE}",
        Folder.Shop.Material / f"PHYSICS{FileType.DATABASE}",
        custom_physics,
        set_physics,
        debug_physics
    )

    # MM2 cities keep their converted DDS in a per-city folder (custom_dds_dir); append THAT so
    # city-unique textures (e.g. London's CF_MARBLE01_WIN_5_F) reach the sheet, not just src/.../custom.
    # Plus EXTRA_TEXTURE_DIRS -> a UNION loose sheet so several cities run from one shared install.
    if mm2_custom_dir:
        tex_custom_dir = Path(mm2_custom_dir)
    else:
        tex_custom_dir = Folder.Src.User.Textures.Custom
    try:
        from src.USER.settings.main import EXTRA_TEXTURE_DIRS as extra_tex_dirs
    except Exception:
        extra_tex_dirs = []
    tex_dirs = [tex_custom_dir] + [Path(d) for d in (extra_tex_dirs or []) if Path(d).is_dir()]
    TextureSheet.append_custom_textures(
        Folder.Resources.Editor.MTL / f"GLOBAL{FileType.TEXTURE_SHEET}",
        tex_dirs if len(tex_dirs) > 1 else tex_custom_dir,
        Folder.Shop.Material / f"TEMP_GLOBAL{FileType.TEXTURE_SHEET}",
        set_texture_sheet
    )

    TextureSheet.write_tweaked(
        Folder.Shop.Material / f"TEMP_GLOBAL{FileType.TEXTURE_SHEET}",
        Folder.Shop.Material / f"GLOBAL{FileType.TEXTURE_SHEET}",
        texture_modifications,
        set_texture_sheet
    )

    # Custom-texture fix: the engine loads mtl/global.tsh ONCE at startup (InitTexSheet), and the
    # FileSystem returns the first provider that has it - a LOOSE file under the dev path (-path ./dev)
    # is searched before core.ar, whereas the city .ar mounts too late to override. So the appended
    # sheet (base + custom) must also be dropped loose in dev/MTL or referenced custom textures fail
    # with "Trying to load texture not in texsheet". (The DDS themselves load fine from the city .ar.)
    if set_texture_sheet:
        import shutil as _sh
        dev_mtl = Folder.MidtownMadness.DevCityMap.parent.parent / "MTL"
        dev_mtl.mkdir(parents=True, exist_ok=True)
        _sh.copy(str(Folder.Shop.Material / f"GLOBAL{FileType.TEXTURE_SHEET}"),
                 str(dev_mtl / f"GLOBAL{FileType.TEXTURE_SHEET}"))
        ok(f"texsheet: copied GLOBAL.TSH -> {dev_mtl} (loose startup override for custom textures)")

    prop_editor = BangerEditor()
    props_on = set_props
    rn_random = random_props

    if roadnet_compiled is not None:
        # Auto-generate scenery (street-lights / trees / hydrants) from the road graph and use it in
        # place of the hand-authored prop_list; force props on for the generated city. The template's
        # random props (cars / sailboats) are skipped so the generated city stays clean.
        prop_list = generate_props(roadnet_compiled)
        props_on = True
        rn_random = []
        ok(f"roadnet: generated {len(prop_list)} scenery prop(s)")

    elif mm2_prop_net is not None:
        prop_list = collect_mm2_props(mm2_json, mm2_options, mm2_pathset_path, mm2_bai_path,
                                      mm2_prop_net, mm2_legacy_props)
        props_on = True
        rn_random = []

        # GROUND-SNAP (measured fix): the MM2 city geometry is authored 1:1 into the MM1 frame and
        # the pathset props sit at their real MM2 Y (delta ~0), but the per-road DENSITY FURNITURE
        # (lamps/benches/bins/meters/poles/traffic-lights) is placed at a fixed CURB_HEIGHT plus a
        # COARSE nearest-BAI-road-point terrain() estimate. On hilly SF that left ~50% of the ~3,600
        # furniture props half-buried or sunk (min -112 m, per the built BNG). Snapping every prop's
        # Y to the ACTUAL authored ground triangle under it makes the delta ~0 by construction.
        # Hanging props (banners / exit gantries / Ghirardelli) keep their raw elevated Y.
        #
        # mm2_poly_types (captured right after emit) lets the snap rest props on real GROUND
        # (road/sidewalk/grass) and never on a building roof or podium.
        snap_props(prop_list, vertices, polys,
                   obj_types = globals().get("mm2_poly_types"), log = item)
    _fixed_prop_list = list(prop_list)  # snapshot before random props are expanded into prop_list
    for prop in rn_random:
        prop_list.extend(prop_editor.place_randomly(prop))
    prop_editor.process_all(prop_list, props_on)

    # Pack mesh/bound/tune/textures for any custom-city props the map uses
    copy_custom_prop_assets_to_shop(_fixed_prop_list, random_props, props_on)

    # copy_custom_prop_assets_to_shop just APPENDED the custom PROP textures (palm fronds, hotdog cart,
    # etc.) to SHOP/MTL/GLOBAL.TSH -- but the LOOSE dev/MTL/GLOBAL.TSH (the sheet the engine actually
    # loads at startup) was copied earlier, BEFORE the prop list existed. Without re-syncing it the game
    # FATALs with "Trying to load texture not in texsheet" on the first custom-prop banger. Re-copy now.
    if set_texture_sheet and props_on:
        import shutil as sh2
        dev_mtl2 = Folder.MidtownMadness.DevCityMap.parent.parent / "MTL"
        dev_mtl2.mkdir(parents=True, exist_ok=True)
        sh2.copy(str(Folder.Shop.Material / f"GLOBAL{FileType.TEXTURE_SHEET}"),
                  str(dev_mtl2 / f"GLOBAL{FileType.TEXTURE_SHEET}"))
        ok("texsheet: re-synced loose dev/MTL/GLOBAL.TSH with custom prop textures")
        # Multi-city coexistence: register EVERY MM2_PROPS texture (both SF + London props) in the loose
        # sheet, so the OTHER city's props resolve too (their DDS load from that city's own .ar). Without
        # this, building one city drops the other city's prop textures from the shared loose sheet, and
        # the other city's bangers FATAL with "not in texsheet". The DDS only need to be in each city's
        # own .ar (packed per-build for that city's used props); the sheet is shared.
        mm2tex_root = get_custom_city(City.Mm2Props.folder).texture_root
        loose_tsh = dev_mtl2 / f"GLOBAL{FileType.TEXTURE_SHEET}"

        if mm2tex_root.is_dir() and loose_tsh.exists():
            declared_names = {line.split(",")[0] for line in open(loose_tsh)}
            added_count = 0

            with open(loose_tsh, "a") as sheet_file:
                for sub_name in (TextureFolder.OPAQUE, TextureFolder.ALPHA):
                    texture_dir = mm2tex_root / sub_name
                    if not texture_dir.is_dir():
                        continue

                    poly_flags = "t" if sub_name == TextureFolder.ALPHA else ""
                    for texture_file in texture_dir.glob(f"*{FileType.DIRECTDRAW_SURFACE}"):
                        name = texture_file.stem
                        if name in declared_names:
                            continue

                        # DDS header: height and width are the two u32 at byte offset 12.
                        with open(texture_file, "rb") as dds_file:
                            dds_file.seek(DdsHeader.DIMENSIONS_OFFSET)
                            height, width = read_unpack(dds_file, "<II")

                        sheet_file.write(f"{name},0,0,0,1,{poly_flags},{name},,"
                                         f"{width or DdsHeader.FALLBACK_SIZE},{height or DdsHeader.FALLBACK_SIZE},000000\n")
                        declared_names.add(name); added_count += 1

            ok(f"texsheet: +{added_count} extra MM2_PROPS textures registered (multi-city coexistence)")

    if set_lighting:
        lighting_instances = Lighting.read_all(Folder.Resources.Editor.Lighting / "LIGHTING.CSV")  # Read original
        Lighting.write_all(lighting_instances, lighting_configs, Folder.Shop.Tune / "LIGHTING.CSV")  # Tweak and write new file
        Lighting.debug(lighting_instances, Folder.Resources.User.Lighting / "LIGHTING_self.txt", debug_lighting)

    create_extrema(f"{Folder.Shop.Map.City}{FileType.EXTREMA}", hudmap_vertices)
    create_animations(Folder.Shop.Map.City, animations_data, set_animations)
    create_bridges(bridge_list, set_bridges, f"{Folder.Shop.Map.City}{FileType.GIZMO}")
    create_bridge_config(bridge_config_list, set_bridges, Folder.Shop.Tune)
    create_minimap(set_minimap, debug_minimap, debug_minimap_id, minimap_outline_color, line_width = 0.7, background_color = "black")

    create_lars_race_maker(
        f"Lars_Race_Maker{FileType.HTML}",
        street_list,
        hudmap_vertices,
        set_lars_race_maker
    )

    # Misc
    DLP(
        Magic.DEVELOPMENT,
        len(dlp_groups), len(dlp_patches), len(dlp_vertices),
        dlp_groups, dlp_patches, dlp_vertices
    ).write(f"TEST{FileType.DEVELOPMENT}", set_dlp)

    editor = BangerEditor()

    # Auto-debug: drop files into debug/input/ to debug them; output lands in debug/output/run_YYYYMMDD_HHMMSS/
    run_auto_debug(Bounds, Meshes, Portals, auto_debug)

    # Finalizing Part
    create_angel_resource_file(Folder.Shop.Root)

    end_time = time.monotonic()
    editor_time = end_time - start_time

    # Save the runtime
    runtime_manager = RunTimeManager(Folder.Resources.Editor.Root / "editor_runtime.pkl")
    runtime_manager.save(editor_time)
    progress_thread.join()  # Wait for progress bar to complete

    print(COLOR_DIVIDER)
    print(Fore.LIGHTCYAN_EX + "   Successfully created " + Fore.LIGHTYELLOW_EX + f"{MAP_NAME}!" + Fore.MAGENTA + f" (in {editor_time:.4f} s)" + Fore.RESET)
    print(COLOR_DIVIDER)

def export_mm2_city_folder() -> None:
    """Copy the baked city into resources/city_files/<NAME>/ so the Map Loader panel can reload it.

    Runs BEFORE post_editor_cleanup wipes SHOP; otherwise the geometry only survives inside the .ar.
    """
    destination = Folder.Resources.CityFiles / MAP_FILENAME
    if destination.exists():
        shutil.rmtree(destination, ignore_errors = True)
    destination.mkdir(parents = True, exist_ok = True)

    for source, target in (
        (Folder.Shop.Map.MeshCity,      destination / "MESHES" / f"{MAP_FILENAME}CITY"),
        (Folder.Shop.Map.MeshLandmark,  destination / "MESHES" / f"{MAP_FILENAME}LM"),
        (Folder.Shop.Map.BoundCity,     destination / "BOUNDS" / f"{MAP_FILENAME}CITY"),
        (Folder.Shop.Map.BoundLandmark, destination / "BOUNDS" / f"{MAP_FILENAME}LM"),
    ):
        if source.is_dir() and any(source.iterdir()):
            shutil.copytree(source, target, dirs_exist_ok = True)

    # Loose per-city metadata: <NAME>.FCD / .BNG / .CELLS / .EXT / .PTL
    for city_file in Folder.Shop.City.glob(f"{MAP_FILENAME}.*"):
        if city_file.is_file():
            shutil.copy(city_file, destination / city_file.name)

    hitid = Folder.Shop.Bound / f"{MAP_FILENAME}_HITID{FileType.BOUND}"
    if hitid.is_file():
        shutil.copy(hitid, destination / hitid.name)

    # MM2 AI is roadnet .road/.map rather than a single .BAI, so ship it under AI/ for reference.
    if Folder.MidtownMadness.DevCityMap.is_dir():
        shutil.copytree(Folder.MidtownMadness.DevCityMap, destination / "AI", dirs_exist_ok = True)

    write_mm2_source_manifest(destination)

    # MM2 cities are all always-visible LANDMARK cells, so count both dirs for an honest total.
    mesh_count = sum(1 for sub in (f"{MAP_FILENAME}CITY", f"{MAP_FILENAME}LM")
                     for f in (destination / "MESHES" / sub).glob("*")
                     if f.suffix.lower() == ".bms")
    ok(f"Exported city folder -> resources/city_files/{MAP_FILENAME}/{sep()}"
       f"{mesh_count} BMS meshes{sep()}load via the 'Map Loader' N-panel")


def write_mm2_source_manifest(destination: Path) -> None:
    """Record which real MM2 sources this conversion came from, so the pairing stays discoverable."""
    options = MM2_CITY[1] if isinstance(MM2_CITY, (tuple, list)) and len(MM2_CITY) > 1 else {}
    manifest = {
        "note": "MM1 conversion of an MM2 city. Ground truth loads from these MM2 sources "
                "(Map Loader N-panel -> 'Load MM2 Ground Truth (PSDL)').",
        "expanded_psdl":  MM2_CITY[0] if isinstance(MM2_CITY, (tuple, list)) else str(MM2_CITY),
        "props_pathset":  options.get("props_pathset"),
        "bai":            options.get("bai_path"),
        "inst_buildings": options.get("inst_buildings"),
        "geometry_dir":   options.get("inst_geometry_dir"),
        "custom_dds_dir": options.get("custom_dds_dir"),
    }
    (destination / f"MM2_SOURCE{FileType.JSON}").write_text(json.dumps(manifest, indent = 2))


if MM2_CITY and MM2_EXPORT_CITY_FOLDER:
    try:
        export_mm2_city_folder()
    except Exception as error:
        item(f"WARNING: city-folder export failed ({error}) — the .ar is unaffected")

    post_editor_cleanup(Folder.Build, Folder.Shop.Root, delete_shop)

    if append_props:
        shutil.copy(append_input_props_file, append_output_props_file)
        editor.append_to_file(
            append_output_props_file,
            props_to_append,
            append_output_props_file,
            append_props
        )

    # ROADNET_BOOT_RACE: "circuit" -> boot the lap race WITH OPPONENTS; True/"race" -> checkpoint
    # race at the change; False -> normal Cruise auto-boot near the change (with traffic).
    _bm = str(ROADNET_BOOT_RACE).lower() if ROADNET_CITY else "false"
    if _bm == "circuit":
        boot_args = ["-cruisenow", "-circuit", "0"]
    elif _bm in ("true", "race", "1"):
        boot_args = ["-cruisenow", "-race", "0"]
    else:
        boot_args = None
    start_game(Folder.MidtownMadness.Root, Executable.MIDTOWN_MADNESS, play_game, boot_args)

#* ----------------------------------------------------------------------------------------------------------------

# Blender
unregister_all()  # Clean slate before re-registering

setup_blender(load_target_model)

initialize_blender_panels()
initialize_blender_operators()
initialize_blender_waypoint_editor()

set_blender_keybinding()

###################################################################################################################   
###################################################################################################################

import bpy
import bmesh

from src.core.geometry.main import transform_coordinate_system

from src.integrations.blender.modeling.meshes import _apply_materials_to_mesh
from src.integrations.blender.modeling.uv_mapping import update_uv_tiling, set_texture_folder
from src.integrations.blender.panels.hud import set_hud_color


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
    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    texture_node = nodes.new(type="ShaderNodeTexImage")
    texture_node.image = texture_image

    links = mat.node_tree.links
    link = links.new
    link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])

    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])


def apply_texture_to_object(obj, texture_path):
    material_name = Path(texture_path).stem

    if material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
    else:
        mat = bpy.data.materials.new(name=material_name)

    obj.data.materials.append(mat)
    obj.active_material = mat
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    diffuse_shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    links = mat.node_tree.links
    link = links.new
    link(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])

    # MM2 cities keep their DDS in src/USER/textures/custom* (not resources/editor/TEXTURES), so a
    # texture may be absent here. Only wire an image node when the file actually loads -- a missing or
    # unreadable DDS leaves an untextured (base-colour) material instead of hard-crashing the whole
    # Blender visualisation (bpy.data.images.load raises RuntimeError on a bad path). See the search
    # path built in create_blender_meshes.
    if texture_path and Path(texture_path).is_file():
        try:
            texture_image = bpy.data.images.load(str(texture_path))
            texture_node = nodes.new(type="ShaderNodeTexImage")
            texture_node.image = texture_image
            link(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])
        except Exception as _e:
            print(f"WARNING: Blender could not load texture '{texture_path}': {_e}")


def apply_computed_uvs(objects):
    for obj in objects:
        if obj.type != 'MESH':
            continue

        uv_layer = obj.data.uv_layers.active
        if not uv_layer:
            continue

        bound_number = int(obj.name.lstrip("P").split(".")[0])
        name_parts = obj.name.split(".")
        sub = int(name_parts[1]) if len(name_parts) > 1 else 0
        entry = texcoords_data.get("entries", {}).get((bound_number, sub), {})

        tile_x = entry.get("tile_x", 1.0)
        tile_y = entry.get("tile_y", 1.0)
        angle_degrees = entry.get("angle_degrees", 0.0)

        base_coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        center_x, center_y = 0.5, 0.5
        rad = math.radians(angle_degrees)

        computed_uvs = []
        for x, y in base_coords:
            x -= center_x
            y -= center_y
            rx = x * math.cos(rad) - y * math.sin(rad)
            ry = x * math.sin(rad) + y * math.cos(rad)
            computed_uvs.append(((rx + center_x) * tile_x, (ry + center_y) * tile_y))

        for i, uv_data in enumerate(uv_layer.data):
            u, v = computed_uvs[i % len(computed_uvs)]
            uv_data.uv = (u, 1.0 - v)

        obj.data.update()


def create_mesh_from_polygon_data(polygon_data, texture_folder=None):
    name = f"P{polygon_data['bound_number']}"
    bound_number = polygon_data["bound_number"]
    script_vertices = polygon_data["vertex_coordinates"]

    transformed_vertices = [transform_coordinate_system(Vector3.from_tuple(vertex), game_to_blender=True) for vertex in script_vertices]

    edges = []
    faces = [range(len(transformed_vertices))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    obj["cell_type"] = str(polygon_data["cell_type"])
    obj["material_index"] = str(polygon_data["material_index"])

    set_hud_color(polygon_data["hud_color"], obj)

    for vertex in transformed_vertices:
        vertex_item = obj.vertex_coords.add()
        vertex_item.x, vertex_item.y, vertex_item.z = vertex

    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(transformed_vertices, edges, faces)
    mesh.update()

    custom_properties = ["sort_vertices", "cell_type", "material_index", "always_visible"]

    for custom_prop in custom_properties:
        if custom_prop in polygon_data:
            obj[custom_prop] = polygon_data[custom_prop]

    if not obj.data.uv_layers:
        obj.data.uv_layers.new()

    bpy.types.Object.tile_x = bpy.props.FloatProperty(name="Tile X", default=2.0, update=update_uv_tiling)
    bpy.types.Object.tile_y = bpy.props.FloatProperty(name="Tile Y", default=2.0, update=update_uv_tiling)
    bpy.types.Object.angle_degrees = bpy.props.FloatProperty(name="Angle Degrees", default=0.0, update=update_uv_tiling)

    name_parts = obj.name.split(".")
    sub = int(name_parts[1]) if len(name_parts) > 1 else 0
    if (bound_number, sub) in texcoords_data.get("entries", {}):
        obj.tile_x = texcoords_data["entries"][(bound_number, sub)].get("tile_x", 1.0)
        obj.tile_y = texcoords_data["entries"][(bound_number, sub)].get("tile_y", 1.0)
        obj.angle_degrees = texcoords_data["entries"][(bound_number, sub)].get("angle_degrees", 0.0)
    else:
        obj.tile_x = 2.0
        obj.tile_y = 2.0
        obj.angle_degrees = 0.0

    if texture_folder:
        apply_texture_to_object(obj, texture_folder)

    return obj


def blender_texture_search_dirs(primary) -> list:
    """Ordered texture-folder search path for the Blender preview. Stock editor TEXTURES first, then
    the active MM2 city's per-city DDS dir (custom_dds_dir), every EXTRA_TEXTURE_DIRS, and the
    MM2_PROPS prop textures. An imported MM2 city keeps its DDS in src/USER/textures/custom* (NOT in
    resources/editor/TEXTURES), so without this the preview crashes on the first MM2 texture (S_GRASS).
    Order = precedence; the first existing <dir>/<name>.DDS wins."""
    dirs = [Path(primary)]

    # mm2_custom_dir is only bound when an MM2 city is being built in this run.
    try:
        if mm2_custom_dir:
            dirs.append(Path(mm2_custom_dir))
    except NameError:
        pass

    dirs += [Path(extra_dir) for extra_dir in (EXTRA_TEXTURE_DIRS or [])]
    mm2_props_tex = get_custom_city(City.Mm2Props.folder).texture_root
    dirs += [mm2_props_tex / TextureFolder.OPAQUE, mm2_props_tex / TextureFolder.ALPHA]

    # CRITICAL: make every dir ABSOLUTE (relative to the repo root). The custom/EXTRA dirs are relative
    # strings ("src/USER/textures/custom"); Path.exists() resolves them against the process CWD, but
    # bpy.data.images.load() resolves a relative path against Blender's blend-file dir -> exists() can
    # pass while the load fails ("No such file": S_OCEAN-0007.DDS). Absolute paths make both agree.
    seen, search_dirs = set(), []
    for directory in dirs:
        directory = directory if directory.is_absolute() else (Folder.BASE / directory)
        key = str(directory).lower()
        if key not in seen:
            seen.add(key)
            search_dirs.append(directory)

    return search_dirs


def resolve_texture_file(texture_name: str, search_dirs: list):
    """First existing <dir>/<texture_name>.DDS across search_dirs, else None."""
    filename = f"{texture_name}{FileType.DIRECTDRAW_SURFACE}"

    for directory in search_dirs:
        candidate = directory / filename
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue        # an unreadable / disconnected dir must not abort the whole search

    return None


def _show_blender_error(message: str, title: str = "MM1 Map Editor — Error") -> None:
    """Display a popup message box in Blender's UI."""
    lines = [ln.strip() for ln in message.strip().splitlines() if ln.strip()]
    def draw(self, _context):
        for line in lines:
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")


def group_polygons_by_cell() -> dict:
    """Group poly indices by cell -> {bound_number: [(poly_index, sub)]}.

    `sub` is the per-cell occurrence index, so the UV lookup keys (bound_number, sub) match what the
    per-poly path uses (Blender's P{n} / P{n}.001 dedup order).
    """
    cell_members = {}
    sub_counter = {}

    for poly_index, poly in enumerate(polygons_data):
        bound_number = poly["bound_number"]
        sub = sub_counter.get(bound_number, 0)
        sub_counter[bound_number] = sub + 1
        cell_members.setdefault(bound_number, []).append((poly_index, sub))

    return cell_members


def reset_mm2_cell_collection():
    """Return the "MM2 Cells" collection, emptied. Clearing it stops re-runs from accumulating
    duplicates (Cell1, Cell1.001, ...) and frees the meshes those objects held."""
    collection = (bpy.data.collections.get(Mm2CellPreview.COLLECTION)
                  or bpy.data.collections.new(Mm2CellPreview.COLLECTION))
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)

    for stale_object in list(collection.objects):
        stale_mesh = stale_object.data
        bpy.data.objects.remove(stale_object, do_unlink=True)
        if stale_mesh and stale_mesh.users == 0:
            bpy.data.meshes.remove(stale_mesh)

    return collection


def create_blender_meshes_merged_by_cell(texture_folder) -> None:
    """MM2 VIZ PATH B — one MERGED Blender object per landmark cell instead of one per polygon.

    A full MM2 city is ~129k polygons across ~86 landmark cells (SF); one-object-per-poly is
    unusable in Blender. This groups the in-memory `polygons_data` by `bound_number` (= cell id) and
    builds a single bmesh per cell with one material slot per distinct texture, so SF loads as ~86
    editable, textured objects in seconds. UVs use the same tile/angle scheme as the per-poly path
    (texcoords_data), and textures resolve across the MM2 custom dirs (see blender_texture_search_dirs).
    """
    if not is_process_running(Executable.BLENDER):
        return

    search_dirs = blender_texture_search_dirs(texture_folder)
    cell_members = group_polygons_by_cell()
    collection = reset_mm2_cell_collection()

    # Per-face obj_type (road/facade/roof/...) is embedded as an int attribute + a legend custom prop
    # so the "Export MM2 Cell Edits" operator can re-emit edited cells faithfully (drivable/HITID
    # classification depends on it). mm2_poly_types is parallel to polys (filler at 0).
    poly_types = globals().get("mm2_poly_types") or []
    type_legend = sorted({t for t in poly_types if t})
    type_index = {t: k for k, t in enumerate(type_legend)}
    cells_built = 0

    for bound_number, members in sorted(cell_members.items()):
        # Distinct textures in this cell -> material slot index.
        cell_textures, texture_slot = [], {}
        for poly_index, _ in members:
            texture = texture_names[poly_index] if poly_index < len(texture_names) else ""
            if texture not in texture_slot:
                texture_slot[texture] = len(cell_textures)
                cell_textures.append(texture)

        segments = _mesh_segments.get(bound_number, [])   # per-poly segments for THIS cell, emit order
        mesh = bpy.data.meshes.new(f"{Mm2CellPreview.OBJECT_PREFIX}{bound_number}")
        builder = bmesh.new()
        uv_layer = builder.loops.layers.uv.new()
        type_layer = (builder.faces.layers.int.new(Mm2CellPreview.OBJECT_TYPE)
                      if type_legend else None)

        for poly_index, sub in members:
            vertices = [transform_coordinate_system(Vector3.from_tuple(v), game_to_blender=True)
                        for v in polygons_data[poly_index]["vertex_coordinates"]]
            try:
                face = builder.faces.new([builder.verts.new(v) for v in vertices])
            except ValueError:
                continue  # degenerate/duplicate

            texture = texture_names[poly_index] if poly_index < len(texture_names) else ""
            face.material_index = texture_slot.get(texture, 0)
            if type_layer is not None and (poly_index + 1) < len(poly_types) and poly_types[poly_index + 1]:
                face[type_layer] = type_index.get(poly_types[poly_index + 1], 0)

            # Real MM2 UVs are per-vertex, stored by save_mesh in _mesh_segments[cell][sub]['tex_coords']
            # (the SAME data that feeds the .bms -> what the game and "load city" use). The tile/angle
            # texcoords_data is a placeholder (tile=1, angle=0) for MM2 and must NOT be used here. They
            # align to vertex_coordinates order because _wind_up_facing reorders verts+uvs together and
            # MM2 polys emit with fix_winding=False. V is flipped for Blender's bottom-left origin,
            # same as the .bms importer (_to_blender_uv).
            tex_coords = segments[sub]["tex_coords"] if sub < len(segments) else None
            for corner, loop in enumerate(face.loops):
                if tex_coords and (2 * corner + 1) < len(tex_coords):
                    loop[uv_layer].uv = (tex_coords[2 * corner], 1.0 - tex_coords[2 * corner + 1])
                else:
                    loop[uv_layer].uv = (0.0, 0.0)

        for _ in cell_textures:
            mesh.materials.append(None)

        # GPU-crash hardening: a failed faces.new (degenerate/duplicate) leaves orphan loose verts;
        # malformed procedural meshes are a known trigger for the NVIDIA draw-manager use-after-free
        # (GPU_batch_draw_parameter_get). Drop loose verts and validate before the mesh is ever drawn.
        loose_vertices = [v for v in builder.verts if not v.link_faces]
        if loose_vertices:
            bmesh.ops.delete(builder, geom=loose_vertices, context="VERTS")

        builder.normal_update(); builder.to_mesh(mesh); builder.free()
        mesh.validate(verbose=False)
        mesh.update()

        cell_object = bpy.data.objects.new(f"{Mm2CellPreview.OBJECT_PREFIX}{bound_number}", mesh)
        cell_object[Mm2CellPreview.CELL_ID] = bound_number
        if type_legend:
            cell_object[Mm2CellPreview.OBJECT_TYPE_LEGEND] = json.dumps(type_legend)
        collection.objects.link(cell_object)

        try:
            _apply_materials_to_mesh(mesh, cell_textures, search_dirs)
        except Exception as error:
            print(f"WARNING: materials for Cell{bound_number} failed ({error}) --- left untextured")
        cells_built += 1

    print(f"OK MM2 viz (merge-per-cell): {cells_built} cell object(s) from {len(polygons_data)} polygons")


def create_blender_meshes(texture_folder: Path, load_all_textures: bool, load_target_model: bool) -> None:
    if not is_process_running(Executable.BLENDER):
        return

    if load_target_model:
        return

    # ── Validate polygons before building meshes ──────────────────────────────
    has_p1  = any(p["bound_number"] == 1 for p in polygons_data)
    has_p200 = any(p["bound_number"] == 200 for p in polygons_data)

    if not has_p1:
        _show_blender_error(
            "No polygon with bound_number = 1 found.\n"
            "Every map must contain at least one polygon with bound_number = 1.\n"
            "Add it to your polygon list in MAP_EDITOR_ALPHA_v1.py and re-run."
        )
        return

    if has_p200:
        _show_blender_error(
            "A polygon with bound_number = 200 was found.\n"
            "bound_number 200 is reserved and cannot be used.\n"
            "Change it to a different value and re-run."
        )
        return

    set_texture_folder(texture_folder)

    load_textures(texture_folder, load_all_textures)

    # Resolve each poly's texture across the stock + MM2 custom dirs so an imported MM2 city renders
    # (its DDS live in src/USER/textures/custom*, not resources/editor/TEXTURES). Unresolved -> None
    # (untextured mesh) instead of a hard crash on the first missing DDS.
    texture_search_dirs = blender_texture_search_dirs(texture_folder)
    missing_names = set()
    created_objects = []
    for poly, texture_name in zip(polygons_data, texture_names):
        texture_path = resolve_texture_file(texture_name, texture_search_dirs)
        if texture_path is None:
            missing_names.add(texture_name)
        obj = create_mesh_from_polygon_data(poly, texture_path)
        created_objects.append(obj)
    if missing_names:
        _ex = ", ".join(sorted(missing_names)[:15])
        print(f"WARNING: {len(missing_names)} texture(s) not found in any search dir -> untextured in "
              f"Blender preview: {_ex}{' ...' if len(missing_names) > 15 else ''}")

    # Set texture_name on each object after all materials are loaded
    for obj, texture_name in zip(created_objects, texture_names):
        try:
            obj.texture_name = texture_name
        except TypeError:
            pass

    apply_computed_uvs(created_objects)

###################################################################################################################   
###################################################################################################################

# BLENDER-ONLY MM2 preview: the .AR block (with its MM2 emit) is skipped in Blender-only modes, so
# polygons_data would still hold the hand-authored grid. Emit the MM2 geometry + props for the scene.
def emit_mm2_blender_preview() -> list:
    """Emit MM2 geometry into the scene buffers and return its props. Geometry only: no .AR/AI/SHOP."""
    json_path, options = (MM2_CITY[0], dict(MM2_CITY[1])) if isinstance(MM2_CITY, (tuple, list)) else (MM2_CITY, {})

    clear_geometry_buffers()

    emit_options = dict(options)
    for key in ("min_ai", "bai_path", "bai_direct", "mm2_races", "props_pathset", "legacy_props"):
        emit_options.pop(key, None)                 # not Mm2Options fields
    stats = emit_mm2_city(create_polygon, save_mesh, compute_uv, json_path,
                          Mm2Options(**emit_options), overrides = load_mm2_cell_overrides())
    ok(f"MM2 preview: {stats['polygons']} polygons in {stats['cells']} cells")

    # obj_type per poly (parallel to polys, filler at 0) — the cell viz embeds it per face so
    # 'Export MM2 Cell Edits' can round-trip edits back into the emit.
    globals()["mm2_poly_types"] = [None] + list(stats.get("obj_types") or [])

    return mm2_preview_props(json_path, options)


def mm2_preview_props(json_path: str, options: dict) -> list:
    """The same 1:1 furniture the .AR gets: pathset placements, density rules, traffic lights."""
    pathset = Path(options["props_pathset"]) if options.get("props_pathset") else None
    has_pathset = bool(pathset and pathset.exists())

    # Rule files sit beside the pathset, or beside facades.csv for cities without one (NY).
    facades_csv = options.get("facades_csv")
    rules_dir = (pathset.parent if has_pathset else
                 Path(facades_csv).parent if facades_csv else None)

    props = []
    if has_pathset:
        props, _ = pathset_props(str(pathset))

    raw_json = Path(str(json_path).replace("expanded_psdl.json", "raw_psdl.json"))
    if rules_dir and (rules_dir / "propdefs.csv").exists() and raw_json.exists():
        psdl_path = rules_dir.parent / (rules_dir.name + FileType.MM2_GEOMETRY)
        props += list(mm2_props.generate(str(raw_json), str(rules_dir), psdl_path = str(psdl_path)))

        bai_path = options.get("bai_path")
        if bai_path and Path(bai_path).exists():
            props += list(mm2_props.bai_traffic_lights(bai_path))      # the BAI's own stored lights
        else:
            props += list(mm2_props.intersection_traffic_lights(json_path))

    if not props:
        item("MM2 preview: no pathset or propdefs for this city — no props")
        return []

    snap_props(props, vertices, polys, obj_types = None)
    ok(f"MM2 preview: {len(props)} prop(s)")

    return props


if MM2_CITY and SKIP_AR_CREATION and is_process_running(Executable.BLENDER) and not load_target_model         and MM2_BLENDER_VIZ != "none" and not CONNECT_BLENDER_ONLY:
    try:
        _fixed_prop_list = emit_mm2_blender_preview()
    except Exception as error:
        item(f"WARNING: MM2 preview failed ({error})")

# MM2 city preview: pick the viz path (poly = one obj/poly, cell = merged per landmark cell, none =
# skip). Only branches for an active MM2 city; a normal hand-authored/roadnet map keeps the per-poly
# path. See MM2_BLENDER_VIZ in src/USER/settings/blender.py.
if CONNECT_BLENDER_ONLY and is_process_running(Executable.BLENDER):
    print("CONNECT_BLENDER_ONLY: empty scene — panels/operators ready (Map Loader / MM2 Ground "
          "Truth / Car Editor). Load content on demand; flip the flag in settings/fast.py to build.")
elif MM2_CITY and is_process_running(Executable.BLENDER) and not load_target_model:
    if MM2_BLENDER_VIZ == "cell":
        create_blender_meshes_merged_by_cell(Folder.Resources.Editor.Textures)
    elif MM2_BLENDER_VIZ == "none":
        print("MM2 viz: skipped (MM2_BLENDER_VIZ='none')")
    else:
        create_blender_meshes(Folder.Resources.Editor.Textures, load_all_textures, load_target_model)
else:
    create_blender_meshes(Folder.Resources.Editor.Textures, load_all_textures, load_target_model)

if visualize_props and is_process_running(Executable.BLENDER):
    with suppress_stdout_matching("Unable to find a suitable DXT compression"):
        place_props_in_scene(
            _fixed_prop_list, random_props, prop_bms_folder,
            texture_folder=Folder.Resources.Editor.Textures,
            car_wheels=prop_car_wheels,
            car_lights=prop_car_lights,
            merge_instances=MM2_PROPS_MERGED,
        )

if visualize_facades and is_process_running(Executable.BLENDER):
    with suppress_stdout_matching("Unable to find a suitable DXT compression"):
        place_facades_in_scene(
            facade_list,
            texture_folder=Folder.Resources.Editor.Textures,
        )

if visualize_bridges and is_process_running(Executable.BLENDER):
    blocks = _bridges_py_to_blocks(bridge_list)
    if blocks:
        place_bridges_in_scene(blocks, Path(prop_bms_folder),
                               texture_folder=Folder.Resources.Editor.Textures)

# Rebuild the "Current" texture list now that polygons, props, and bulk meshes
# are all loaded — so every material in the scene is reflected.
if is_process_running(Executable.BLENDER):
    from src.integrations.blender.modeling.uv_mapping import refresh_current_textures
    refresh_current_textures()

# END-OF-BUILD SCENE HYGIENE (GPU crash fix): the build creates/removes thousands of datablocks in
# one operator; Blender's draw manager can then reference freed GPU batches on the next workbench
# redraw (EXCEPTION_ACCESS_VIOLATION in GPU_batch_draw_parameter_get). Purge orphaned datablocks and
# rebuild the depsgraph ONCE, cleanly, before the first heavy draw, and tag every 3D view so the
# redraw starts from fresh caches.
if is_process_running(Executable.BLENDER):
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
        bpy.context.view_layer.update()
        for win in bpy.context.window_manager.windows:
            for cell_area in win.screen.areas:
                if cell_area.type == "VIEW_3D":
                    cell_area.tag_redraw()
        print("OK Blender scene hygiene: orphans purged, depsgraph rebuilt, views tagged")
    except Exception as _he:
        print(f"WARNING: scene-hygiene pass failed ({_he}) — harmless, continuing")

# NUCLEAR GPU-crash workaround (MM2_SAVE_RELOAD_AFTER_BUILD), v3. The Blender 4.3.0 NVIDIA
# use-after-free (GPU_batch_draw_parameter_get in workbench::OpaquePass) fires on the FIRST viewport
# redraw after the build script's operator returns — BEFORE any timer can run (Blender's main loop
# draws in the same iteration; timers only get the next one). So a deferred save+reload alone cannot
# help. v3 sequence:
#   1. SYNC: save the built scene to a .blend NOW (file carries the normal SOLID shading).
#   2. SYNC: flip every 3D viewport to WIREFRAME — wireframe shading does not enter
#      workbench::OpaquePass, so the unavoidable first draws bypass the crashing code path entirely.
#   3. DEFERRED (0.1s timer): wm.open_mainfile(the saved file) — a clean load rebuilds every GPU
#      batch from scratch and restores the file's SOLID shading. Session state (panels, VS Code
#      connection) survives an open_mainfile.
if MM2_SAVE_RELOAD_AFTER_BUILD and MM2_CITY and is_process_running(Executable.BLENDER) \
        and not load_target_model and MM2_BLENDER_VIZ != "none" and not CONNECT_BLENDER_ONLY:
    srl_path = str(Folder.Blender.Models / f"{MAP_FILENAME}session_path.blend")
    Folder.Blender.Models.mkdir(parents=True, exist_ok=True)
    try:
        bpy.ops.wm.save_as_mainfile(filepath=srl_path, check_existing=False, compress=False)
        for win in bpy.context.window_manager.windows:
            for cell_area in win.screen.areas:
                if cell_area.type == "VIEW_3D":
                    for view_space in cell_area.spaces:
                        if view_space.type == "VIEW_3D":
                            view_space.shading.type = "WIREFRAME"   # dodge OpaquePass until the reload
        print(f"OK saved session + viewports to WIREFRAME (crash dodge) — reloading {srl_path} ...")

        def mm2_reload():
            try:
                bpy.ops.wm.open_mainfile(filepath=srl_path)
                print("OK reload complete — GPU caches rebuilt from clean load, shading restored")
            except Exception as _se:
                print(f"WARNING: reload failed ({_se}) — set a 3D view back to Solid manually")
            return None                 # one-shot timer

        bpy.app.timers.register(mm2_reload, first_interval=0.1)
    except Exception as _se:
        print(f"WARNING: save+wireframe stage failed ({_se}) — scene left as built")

###################################################################################################################
################################################################################################################### 
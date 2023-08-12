import os
import time
import shutil
import psutil
import struct
import fnmatch
import textwrap
import numpy as np
import subprocess
from pathlib import Path
from typing import List


############################ SETUP ############################

#? While this script can be used, it is still a work in progress.

#! Change this
mm1_directory =  "C:\\Users\\robin\\Desktop\\MM1_DLP\\"

# Don't change this
mm1_exe = Path(mm1_directory) / "Open1560.exe"
dev_caddie_bnd_output = Path(mm1_directory) / "dev" / "BND" / "vpcaddie_bnd.bnd"

dev_caddie_bnd_output_text = "DEV_CADDIE_BND_OUTPUT.TXT"
xore_compiler = "XORE_COMPILER.bat"

INDENT = '\t'

###############################################################

# Simplify Struct Usage
def read_unpack(file, fmt):
    return struct.unpack(fmt, file.read(struct.calcsize(fmt)))

def write_pack(file, fmt, *args):
    file.write(struct.pack(fmt, *args))
    

# VECTOR CLASS
class Vector2:
    def __init__(self, u, v):
        self.u = u
        self.v = v

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
    @classmethod
    def from_file(cls, file):
        x, y, z = read_unpack(file, '<3f')
        return cls(x, y, z)
    
    def __repr__(self, round_values=True):
        if round_values:
            return '{{{:.2f},{:.2f},{:.2f}}}'.format(round(self.x, 3), round(self.y, 3), round(self.z, 3))
        else:
            return '{{{:f},{:f},{:f}}}'.format(self.x, self.y, self.z)


# DLP CLASS
class DLPVertex: 
    def __init__(self, id, position, uv, color):
        self.id = id
        self.position = position
        self.uv = uv
        self.color = color

class DLPPatch:
    def __init__(self, s_res, t_res, flags, r_opts, mtl_idx, tex_idx, phys_idx, vertices, name):
        self.s_res = s_res
        self.t_res = t_res
        self.flags = flags
        self.r_opts = r_opts
        self.mtl_idx = mtl_idx
        self.tex_idx = tex_idx
        self.phys_idx = phys_idx
        self.vertices = vertices
        self.name = name

class DLPGroup:
    def __init__(self, name, num_vertices, num_patches, vertex_indices, patch_indices):
        self.name = name
        self.num_vertices = num_vertices
        self.num_patches = num_patches
        self.vertex_indices = vertex_indices
        self.patch_indices = patch_indices

class DLP:
    def __init__(self, magic, num_groups, num_patches, num_vertices, groups, patches, vertices):
        self.magic = magic
        self.num_groups = num_groups
        self.num_patches = num_patches
        self.num_vertices = num_vertices
        self.groups = groups
        self.patches = patches
        self.vertices = vertices

    def dlp_save(self, new_file_path):
        with open(new_file_path, 'wb') as file:
            
            write_pack(file, '>4s', self.magic.encode())
            write_pack(file, '>III', self.num_groups, self.num_patches, self.num_vertices)

            # Write Groups
            for group in self.groups:
                write_pack(file, '>B', len(group.name))
                write_pack(file, f'>{len(group.name)}s', group.name.encode())
                write_pack(file, '>II', group.num_vertices, group.num_patches)
                write_pack(file, f'>{group.num_vertices}H', *group.vertex_indices)
                write_pack(file, f'>{group.num_patches}H', *group.patch_indices)

            # Write Patches
            for patch in self.patches:
                write_pack(file, '>7H', patch.s_res, patch.t_res, patch.flags, patch.r_opts, patch.mtl_idx, patch.tex_idx, patch.phys_idx)
                for vertex in patch.vertices:
                    write_pack(file, '>HfffI', vertex.id, vertex.position.x, vertex.position.y, vertex.position.z, vertex.color)
                    write_pack(file, '>ff', vertex.uv.u, vertex.uv.v)

                write_pack(file, '>I', len(patch.name))
                write_pack(file, f'>{len(patch.name)}s', patch.name.encode())

            # Write Vertices
            for vertex in self.vertices:
                write_pack(file, '>fff', vertex.x, vertex.y, vertex.z)
                # file.write(b'\x00' * 12) # 12 bytes of filler, seems correct for _BND.DLP files
 
                        
# POLYGON CLASS
class Polygon:
    def __init__(self, cell_id: int, mtl_index: int, flags: int, vert_indices: List[int],
                 plane_edges: List[Vector3], plane_n: Vector3, plane_d: float, cell_type: int = 0) -> None:
        self.cell_id = cell_id
        self.mtl_index = mtl_index
        self.flags = flags
        self.vert_indices = vert_indices
        self.plane_edges = plane_edges
        self.plane_n = plane_n
        
        if isinstance(plane_d, list) and len(plane_d) == 1:
            plane_d = plane_d[0]
        elif isinstance(plane_d, np.float64):
            plane_d = float(plane_d)
            
        self.plane_d = plane_d
        self.cell_type = cell_type

    @property
    def is_quad(self) -> bool:
        return bool(self.flags & 4)

    @property
    def num_verts(self) -> int:
        return 4 if self.is_quad else 3

    @classmethod
    def from_file(cls, file):
        cell_id, mtl_index, flags, *vert_indices = read_unpack(file, '<HBB4H')
        plane_edges = [Vector3.from_file(file) for _ in range(4)]
        plane_n = Vector3.from_file(file)
        plane_d, = read_unpack(file, '<f')
        return cls(cell_id, mtl_index, flags, vert_indices, plane_edges, plane_n, plane_d)
    
        
    def format_data(self):
        vertices_coordinates = []
        
        for index in self.vert_indices:
            vertices_coordinates.append(bnd.vertices[index])
            
            vertices_index = ', '.join([f"{vertex}" for vertex in self.vert_indices])
            
            vertices_str = ',\n'.join([f"{INDENT*1}({vertex})" for vertex in vertices_coordinates])
            
            plane_edges_str = ',\n'.join([f"{INDENT}({vec})" for vec in self.plane_edges])
            
            plane_d_str = '{:.2f}'.format(round(self.plane_d, 2)) 
                        
            polygon_str = textwrap.dedent(f"""  
order = \n{vertices_index},
    vertex_coordinates = [
{vertices_str}],
plane_edges = [
{plane_edges_str}],
plane_normal = ("custom", {self.plane_n}, {plane_d_str})\n
""")
        return polygon_str.strip()
    
# create_polygon( 
#     bound_number = 0,
#     material_index = 0,

    def __repr__(self, round_values=True):
        vertices_coordinates = [BND.vertices[index] for index in self.vert_indices]
        plane_d_str = f'{round(self.plane_d, 2):.2f}' if round_values else f'{self.plane_d:f}'

        return f'''
Polygon
Cell ID: {self.cell_id}
Material Index: {self.mtl_index}
Flags: {self.flags}
Vertices Indices: {self.vert_indices}
Vertices Coordinates: {vertices_coordinates}
Plane Edges: {self.plane_edges}
Plane N: {self.plane_n}
Plane D: [{plane_d_str}]
        '''
    
# BND CLASS    
class BND:
    def __init__(self, magic: str, offset: Vector3, x_dim: int, y_dim: int, z_dim: int, 
                 center: Vector3, radius: float, radius_sqr: float, bb_min: Vector3, bb_max: Vector3, 
                 num_verts: int, num_polys: int, num_hot_verts1: int, num_hot_verts2: int, num_edges: int, 
                 x_scale: float, z_scale: float, num_indices: int, height_scale: float, cache_size: int, 
                 vertices: List[Vector3], polys: List[Polygon]):
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
        self.num_hot_verts1 = num_hot_verts1
        self.num_hot_verts2 = num_hot_verts2
        self.num_edges = num_edges
        self.x_scale = x_scale
        self.z_scale = z_scale
        self.num_indices = num_indices
        self.height_scale = height_scale
        self.cache_size = cache_size
        
        self.vertices = vertices              
        self.polys = polys                       

    @classmethod
    def from_file(cls, file):
        magic = read_unpack(f, '<4s')[0]
        offset = Vector3.from_file(f)
        x_dim, y_dim, z_dim = read_unpack(f, '<3l')
        center = Vector3.from_file(f)
        radius, radius_sqr = read_unpack(f, '<2f')
        bb_min = Vector3.from_file(f)
        bb_max = Vector3.from_file(f)
        num_verts, num_polys, num_hot_verts1, num_hot_verts2, num_edges = read_unpack(f, '<5l')
        x_scale, z_scale, num_indices, height_scale, cache_size = read_unpack(f, '<2f3l')
        vertices = [Vector3.from_file(f) for _ in range(num_verts)]
        polys = [Polygon.from_file(f) for _ in range(num_polys + 1)] 

        return cls(magic, offset, x_dim, y_dim, z_dim, center, radius, radius_sqr, bb_min, bb_max, 
                   num_verts, num_polys, num_hot_verts1, num_hot_verts2, num_edges, 
                   x_scale, z_scale, num_indices, height_scale, cache_size, vertices, polys)
                
    # Write BND TEXT data
    def write_editor_data(self, file_name):
        with open(file_name, 'w') as f:
            for i, poly in enumerate(self.polys, 0):
                if poly.vert_indices == [0, 1, 2, 3]:  
                    f.write(f'# Iteration # {i}\n')
                    f.write(poly.format_data())
                    f.write('\n\n')
                
    def __repr__(self) -> str:
        return f'''
BND
Vertices: {self.vertices}
Polys: {self.polys}
    '''

###############################################################################################################

# other flags: 1513, 1289 (num: 4), 257 (num: ...)

# DLP GROUP fillers
num_vertices_zero = 0
num_vertex_indices_zero = []

# DLP PATCH fillers
flags = 1289
r_opts = 636

mtl_idx = 0
tex_idx = 0
phys_idx = 0
color = 4294967295

name_patch = "" # should be empty

# DLP VERTEX fillers
xyz_filler = Vector3(0.0, 0.0, 0.0)     
uv_filler = Vector2(0.0, 0.0)             

# DYNAMIC values
grp_bound = "BOUND\x00"                 # looks okay --- space between names: 8 bytes (2x 4 bytes)
      
#########################################################################################################

#! Implementation
# Seems to not matter (i.e. 0.0 {fillers} values are fine)
vertices = [
    DLPVertex(0, xyz_filler, uv_filler, color),
    DLPVertex(1, xyz_filler, uv_filler, color),
    DLPVertex(2, xyz_filler, uv_filler, color),
    DLPVertex(3, xyz_filler, uv_filler, color)]

geometry_vertices = [ 
      Vector3(-50.0,0.0,80.0),
      Vector3(-140.0,0.0,50.0),
      Vector3(-100.0,0.0,10.0),
      Vector3(-50.0,0.0,30.0)]

# Group no. 1
group1 = DLPGroup(
    grp_bound, num_vertices_zero, 2, 
    num_vertex_indices_zero,
    [0, 1]) 

# Patches                  
patches = [
    DLPPatch(4, 1, 1513, r_opts, mtl_idx, tex_idx, phys_idx, [vertices[0], vertices[1], vertices[2], vertices[3]], name_patch),
    DLPPatch(4, 1, 1513, r_opts, mtl_idx, tex_idx, phys_idx, [vertices[3], vertices[2], vertices[1], vertices[0]], name_patch)]

# DLP object
dlp_object = DLP(
    "DLP7", 
    1, # num_groups
    2, # num_patches
    4, # num_vertices
    [group1], patches, geometry_vertices)

#################################################################################3

def file_handler(mm1_directory, remove_targets, add_target):
    shiplist_file = os.path.join(mm1_directory, "shiplist.core")

    # Remove the target line from shiplist.core
    with open(shiplist_file, 'r') as f:
        lines = f.readlines()
        
    with open(shiplist_file, 'w') as f:
        for line in lines:
            if not any(remove_target in line for remove_target in remove_targets):
                f.write(line)
                
    # Remove target files from subdirectories
    for remove_target in remove_targets:
        for root, _, files in os.walk(mm1_directory):
            for item in fnmatch.filter(files, "*{}*".format(remove_target)):
                os.remove(os.path.join(root, item))
                
    # Create the dev folder and its sub-folders
    dev_folder = os.path.join(mm1_directory, "dev")
    os.makedirs(dev_folder, exist_ok=True)                       # Creates dev folder if it doesn't exist
    os.makedirs(os.path.join(dev_folder, "BMS"), exist_ok=True)  # Creates BMS folder inside dev
    os.makedirs(os.path.join(dev_folder, "BND"), exist_ok=True)  # Creates BND folder inside dev
    
    shutil.copy(add_target, os.path.join(mm1_directory, "DLP"))

    # Add the add_target to shiplist.core if it doesn't already exist
    with open(shiplist_file, 'a+') as f: 
        f.seek(0)  
        lines = f.read()
        if add_target not in lines:
            f.write(".\\DLP\\" + add_target + "\n")
            
            
def is_midtown_running(process_name):
    for proc in psutil.process_iter(['name']):
        if process_name.lower() in proc.info['name'].lower():
            return True
    return False

# Wait script execution until Midtown Madness is closed
game_process_names = ['Open1560.exe', 'Midtown.exe']
while any(is_midtown_running(proc_name) for proc_name in game_process_names):
    time.sleep(1)

print("\nExited Midtown Madness, printing data...\n")
    
#######################################################################################################

rt_1 = "VPCADDIE_BND.BND" 
rt_2 = "VPCADDIE.DLP"
rt_3 = "VPCADDIE_BND.DLP"
remove_targets = [rt_1, rt_2, rt_3] # need to keep all

created_dlp = "vpcaddie_bnd.dlp"

# Save DLP
dlp_object.dlp_save(created_dlp)

file_handler(mm1_directory, remove_targets, created_dlp)
print("\nSaved DLP file, Compiling .ar and Starting Game...\n")

# Run stuff
subprocess.call([os.path.join(mm1_directory, xore_compiler) ])

# Wait script execution until Midtown Madness is closed
game_process_names = ['Open1560.exe', 'Midtown.exe']
while any(is_midtown_running(proc_name) for proc_name in game_process_names):
    time.sleep(1)

print("\nExited Midtown Madness, printing data...\n")

# Open & Write & Print
with open(dev_caddie_bnd_output, 'rb') as f:
    bnd = BND.from_file(f)
    bnd.write_editor_data(dev_caddie_bnd_output_text)
    
with open(dev_caddie_bnd_output_text) as file:
    file_contents = file.read()
    print(file_contents)
    

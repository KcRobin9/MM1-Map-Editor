import os
import re
import time
import shutil
import psutil
import struct
import fnmatch
import textwrap
import subprocess


###### SETUP ######
mm1_directory = "C:\\Users\\robin\\Desktop\\store_v1_MM1\\"
mm1_exe = "C:\\Users\\robin\\Desktop\\store_v1_MM1\\Open1560.exe\\"

# assumes you have a "compiler.bat" or equivalent to compile the .ar and boot the game
xore_compiler = "XORE_COMPILER.bat"
###################


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
        x, y, z = struct.unpack('<3f', file.read(12))
        return cls(x, y, z)
    
    def __repr__(self, round_values=True):
        if round_values:
            return '{{{:.2f},{:.2f},{:.2f}}}'.format(round(self.x, 3), round(self.y, 3), round(self.z, 3))
        else:
            return '{{{:f},{:f},{:f}}}'.format(self.x, self.y, self.z)

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
            
            file.write(self.magic.encode())
            file.write(struct.pack('>I', self.num_groups))
            file.write(struct.pack('>I', self.num_patches))
            file.write(struct.pack('>I', self.num_vertices))

            # Write Groups
            for group in self.groups:
                file.write(struct.pack('>B', len(group.name)))
                file.write(struct.pack(f'>{len(group.name)}s', group.name.encode()))
                file.write(struct.pack('>I', group.num_vertices))
                file.write(struct.pack('>I', group.num_patches))
                file.write(struct.pack(f'>{group.num_vertices}H', *group.vertex_indices))
                file.write(struct.pack(f'>{group.num_patches}H', *group.patch_indices))

            # Write Patches
            for patch in self.patches:
                file.write(struct.pack('>7H', patch.s_res, patch.t_res, patch.flags, patch.r_opts, patch.mtl_idx, patch.tex_idx, patch.phys_idx))
                for vertex in patch.vertices:
                    file.write(struct.pack('>H', vertex.id))
                    file.write(struct.pack('>fff', vertex.position.x, vertex.position.y, vertex.position.z))
                    file.write(struct.pack('>ff', vertex.uv.u, vertex.uv.v))
                    file.write(struct.pack('>I', vertex.color))

                file.write(struct.pack('>I', len(patch.name)))
                file.write(struct.pack(f'>{len(patch.name)}s', patch.name.encode()))

            # Write Vertices
            for vertex in self.vertices:
                file.write(struct.pack('>fff', vertex.x, vertex.y, vertex.z))
                # file.write(b'\x00' * 12) # 12 bytes of filler, seems correct for _BND.DLP files
 
INDENT = '\t'           
                
# POLYGON CLASS [BND]
class Polygon:
    def __init__(self, word0, mtl_index, flags, vert_indices, some_vecs, corners):
        self.word0 = word0
        self.mtl_index = mtl_index  
        self.flags = flags          
        self.vert_indices = vert_indices
        self.some_vecs = some_vecs
        self.corners = corners

    @classmethod
    def from_file(cls, file):
        word0, mtl_index, flags, *vert_indices = struct.unpack('<HBB4H', file.read(12))
        some_vecs = [Vector3.from_file(file) for _ in range(4)]
        corners = list(struct.unpack('<4f', file.read(16)))
        
        return cls(word0, mtl_index, flags, vert_indices, some_vecs, corners)
    
    def as_function_call(self):
        vertices_coordinates = []
        for index in self.vert_indices:
            vertices_coordinates.append(bnd.vertices[index])

        vertices_str = ',\n'.join([f"{INDENT*1}{vertex}" for vertex in vertices_coordinates])
        some_vecs_str = ',\n'.join([f"{INDENT*1}{vec}" for vec in self.some_vecs])
        corners_str = ','.join(['{:.2f}'.format(round(corner, 2)) for corner in self.corners])  # Round the corners

        polygon_str = textwrap.dedent(
f"""
create_and_append_polygon(
bound_number = 0,
material_index = 0,
vertex_coordinates=[
{vertices_str}],
some_vecs = [
{some_vecs_str}],
corners = [{corners_str}], sort_vertices=False)\n
""")
        return polygon_str.strip()
    
    
    def __repr__(self, round_values=True):
        vertices_coordinates = []
        for index in self.vert_indices:
            vertices_coordinates.append(bnd.vertices[index])

        if round_values:
            corners_str = '[{}]'.format(', '.join(['{:.2f}'.format(round(corner, 2)) for corner in self.corners]))
        else:
            corners_str = '[{}]'.format(', '.join(['{:f}'.format(corner) for corner in self.corners]))

        return '\n Polygon \n Bound number: {}\n Material Index: {}\n Flags: {}\n Vertices Indices: {}\n Vertices Coordinates: {}\n Directional Coordinates: {}\n Corners: {}\n'.format(self.word0, self.mtl_index, self.flags, self.vert_indices, vertices_coordinates, self.some_vecs, corners_str)
    

# BND CLASS    
class BND:
    def __init__(self, magic, offset, width, row_count, height, center, radius, radius_sqr, min_, max_, num_verts, num_polys, num_hot_verts, num_vertices_unk, edge_count, scaled_dist_x, z_dist, num_indexs, height_scale, unk12, vertices, polys):
        self.magic = magic
        self.offset = offset    
        self.width = width
        self.row_count = row_count
        self.height = height
        self.center = center    
        self.radius = radius
        self.radius_sqr = radius_sqr
        self.min = min_         
        self.max = max_        
        self.num_verts = num_verts
        self.num_polys = num_polys
        self.num_hot_verts = num_hot_verts
        self.num_vertices_unk = num_vertices_unk
        self.edge_count = edge_count
        self.scaled_dist_x = scaled_dist_x
        self.z_dist = z_dist
        self.num_indexs = num_indexs
        self.height_scale = height_scale
        self.unk12 = unk12
        self.vertices = vertices              
        self.polys = polys                      

    @classmethod
    def from_file(cls, file):
        magic = struct.unpack('<4s', file.read(4))[0]
        offset = Vector3.from_file(file)
        width, row_count, height = struct.unpack('<3l', file.read(12)) 
        center = Vector3.from_file(file)
        radius, radius_sqr = struct.unpack('<2f', file.read(8))
        min_ = Vector3.from_file(file)
        max_ = Vector3.from_file(file)
        num_verts, num_polys, num_hot_verts, num_vertices_unk, edge_count = struct.unpack('<5l', file.read(20))
        scaled_dist_x, z_dist, num_indexs, height_scale, unk12 = struct.unpack('<fflfl', file.read(20))
        vertices = [Vector3.from_file(file) for _ in range(num_verts)]
        polys = [Polygon.from_file(file) for _ in range(num_polys + 1)] 

        return cls(magic, offset, width, row_count, height, center, radius, radius_sqr, min_, max_, num_verts, num_polys, num_hot_verts, num_vertices_unk, edge_count, scaled_dist_x, z_dist, num_indexs, height_scale, unk12, vertices, polys)
                
    # Write BND TEXT data
    def write_to_file(self, file_name):
        with open(file_name, 'w') as f:
            for i, poly in enumerate(self.polys, 1):  # Start counting from 1
                f.write(f'# Iteration # {i}\n')
                f.write(poly.as_function_call())
                f.write('\n\n')
                
    def __repr__(self):
        return 'BND\n Magic: {}\n Offset: {}\n Width: {}\n Row_count: {}\n Height: {}\n Center: {}\n Radius: {}\n Radius_sqr: {}\n min: {}\n max: {}\n Num Verts: {}\n Num Polys: {}\n Num Hot Verts: {}\n Num Vertices Unk: {}\n Edge count: {}\n Scaled Dist. X: {}\n Z Dist.: {}\n Num Indexs: {}\n Height Scale: {}\n Unk12: {}\n Vertices: {}\n\n Polys: {}\n\n'.format(
            self.magic, self.offset, self.width, self.row_count, self.height, self.center, self.radius, self.radius_sqr, self.min, self.max, self.num_verts, self.num_polys, self.num_hot_verts, self.num_vertices_unk, self.edge_count, self.scaled_dist_x, self.z_dist, self.num_indexs, self.height_scale, self.unk12, self.vertices, self.polys)

###############################################################################################################

# other flags: 1513, 1289 (num: 4), 257 (num: ...)

# DLP MAIN filler values
dlp7_magic = "DLP7"

# DLP GROUP filler values
num_vertices_zero = 0
num_vertex_indices_zero = []

# DLP PATCH filler values
flags = 1289
r_opts = 636

mtl_idx = 0
tex_idx = 0
phys_idx = 0
color = 4294967295

name_patch = "" # should be empty

# DLP VERTEX filler values
position_xyz_filler = Vector3(0.0, 0.0, 0.0)    # does not matter  
uv_filler = Vector2(0.0, 0.0)                   # does not matter    

# DYNAMIC values
grp_bound = "BOUND\x00"                 # looks okay --- space between names: 8 bytes (2x 4 bytes)
      
#########################################################################################################

# SEEMS TO NOT MATTER (i.e. 0.0 {filles} values are fine)
vertices = [
    DLPVertex(0, position_xyz_filler, uv_filler, color),
    DLPVertex(1, position_xyz_filler, uv_filler, color),
    DLPVertex(2, position_xyz_filler, uv_filler, color),
    DLPVertex(3, position_xyz_filler, uv_filler, color)]


v = [ 
    Vector3(-40, 15.0, 80),
    Vector3(-50, 15.0, 80),
    Vector3(-50, 25.0, 50),
    Vector3(-40, 25.0, 50)]

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
    dlp7_magic, 
    1, # num_groups
    2, # num_patches
    4, # num_vertices
    [group1], patches, v)

#################################################################################3

def file_handler(mm1_directory, remove_targets, add_target):
    shiplist_file = os.path.join(mm1_directory, "shiplist.core")

    # OBJECTIVE 1:
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
                
    # OBJECTIVE 2:
    # Create the dev folder and its sub-folders
    dev_folder = os.path.join(mm1_directory, "dev")
    os.makedirs(dev_folder, exist_ok=True)  # Creates dev folder if it doesn't exist
    os.makedirs(os.path.join(dev_folder, "BMS"), exist_ok=True)  # Creates BMS folder inside dev
    os.makedirs(os.path.join(dev_folder, "BND"), exist_ok=True)  # Creates BND folder inside dev
    
    # OBJECTIVE 3:
    # Copy the add_target file to the DLP directory
    shutil.copy(add_target, os.path.join(mm1_directory, "DLP"))

    # OBJECTIVE 4:
    # Add the add_target to shiplist.core if it doesn't already exist
    with open(shiplist_file, 'a+') as f:  # Open in append and read mode
        f.seek(0)  # Go to start of file
        lines = f.read()
        if add_target not in lines:
            f.write(".\\DLP\\" + add_target + "\n")
    
#######################################################################################################

desired_coordinates_order = [str(coord).replace(" ", "") for coord in map(str, v[0:4])]

def get_matching_iteration_from_file(file_name, desired_coordinates_order):
    # Convert desired_coordinates_order to list of string for exact match comparison
    desired_coordinates = [str(coord).replace(" ", "") for coord in desired_coordinates_order]
    
    with open(file_name, 'r') as file:
        content = file.read()

    iterations = re.findall('# Iteration # (\d+)', content)
    vertices = re.findall('vertex_coordinates=\[(.*?)\]', content, re.DOTALL)

    for iteration, vertex in zip(iterations, vertices):
        # Extract all coordinates and remove extra spaces
        coordinates = re.findall('\{([^}]+)\}', vertex)
        coordinates = [coord.replace(" ", "") for coord in coordinates[:4]]  # Only consider the first four

        print("Checking with Coordinates:", coordinates, type(coordinates))

        # Check if the list of coordinates matches the desired list
        if coordinates == desired_coordinates:
            return iteration, vertex
    
    return None, None


dev_caddie_bnd_output = "C:\\Users\\robin\\Desktop\\store_v1_MM1\\dev\\BND\\vpcaddie_bnd.bnd"
dev_caddie_bnd_output_text = "DEV_CADDIE_BND_OUTPUT.TXT"

bat_file = os.path.join(mm1_directory, xore_compiler)  

rt_1 = "VPCADDIE_BND.BND" 
rt_2 = "VPCADDIE.DLP"
rt_3 = "VPCADDIE_BND.DLP"
remove_targets = [rt_1, rt_2, rt_3] # need to keep all

created_dlp = "vpcaddie_bnd.dlp"

# Save DLP
dlp_object.dlp_save(created_dlp)
file_handler(mm1_directory, remove_targets, created_dlp)
print("\nSaved DLP file, compiling .ar and starting game...\n")

subprocess.call([bat_file])

# Function to check if a process is running
def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if process_name.lower() in proc.info['name'].lower():
            return True
    return False

# Wait script execution until Midtown Madness is closed
game_process_names = ['Open1560.exe', 'Midtown.exe']
while any(is_process_running(proc_name) for proc_name in game_process_names):
    time.sleep(1)

print("\neExited Midtown Madness, printing data...\n")
    
with open(dev_caddie_bnd_output, 'rb') as f:
    bnd = BND.from_file(f)
    bnd.write_to_file(dev_caddie_bnd_output_text)
    
with open(dev_caddie_bnd_output_text) as file:
    file_contents = file.read()
    print(file_contents)
    
iteration, vertex_coordinates = get_matching_iteration_from_file(dev_caddie_bnd_output_text, desired_coordinates_order)
if iteration is not None:
    print(f"Matching iteration found: #{iteration}\nCoordinates:\n{vertex_coordinates}")
else:
    print("No matching iteration found.")
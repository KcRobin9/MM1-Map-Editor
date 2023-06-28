import os
import re
import bpy
import subprocess

# Note: This script is designed to be run from Blender's Scripting Editor 

######## FILES ########
model_vertices_import_file = "Model_Vertices_IMPORT.txt"
model_vertices_export_file = "Model_Vertices_EXPORT.txt"

bai_paths_import_file = "CHICAGO.road" # any
bai_paths_export_file = "Bai_Paths_EXPORT.txt"

######### BOOLEANS #########
# Import
import_and_model_vertices = False 
import_and_model_bai_paths = False

# Export
export_model_vertices = False  
open_model_file_after_export = False

export_bai_paths = False
open_bai_paths_file_after_export = False

# Add Custom Properties to Shapes in Collection (recommended)
set_texture_property = False  

decimals = 2 # numer of decimals in the Export File 
tab = '\t'


# Create Polylines
def create_polyline(curve_object, coordinates):
    curve_data = curve_object.data
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 1
    curve_data.bevel_depth = 0.70  # Line thickness

    # Create the Polyline
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(coordinates) - 1) # One point is added by default
    for i, coord in enumerate(coordinates):
        x, y, z = coord
        polyline.points[i].co = (x, y, z, 1) # the 4th element is for homogeneous coordinates (usually equals 1)

# Function to add Custom Properties with default values
def set_default_texture_property():
    for obj in bpy.context.collection.objects:
        
        # Set Texture Name
        if 'texture_name' not in obj.keys():
            obj["texture_name"] = "RINTER" # default value
        
        # Set TexCoords Mode
        if 'TexCoords_mode' not in obj.keys():
            obj["TexCoords_mode"] = "repeating_vertical" # default value
            
        # Set TexCoords Values (x,y)
        if 'TexCoords_values (x,y)' not in obj.keys():
            obj["TexCoords_values (x,y)"] = (10.0, 10.0) # default value

if set_texture_property:
    set_default_texture_property()
        
# Extract Vertices Coordinates (Map) from Input File
def extract_coords(coord_str):
    coords = re.findall(r"{(.*?)}", coord_str)
    coords = [tuple(map(float, c.split(','))) for c in coords]
    
    # swap y and z coordinates and change sign of y
    coords = [(x,-z,y) for x, y, z in coords]
    return coords

# Create Meshes from Coordinates
def create_mesh(coords, name):
    edges = []
    faces = [(range(len(coords)))]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bpy.context.collection.objects.link(obj)

    if import_and_model_vertices:
        mesh.from_pydata(coords, edges, faces)
        mesh.update()

    return obj 

# Export Mesh Coordinates
def export_mesh(filename):
    with open(filename, "w") as f:
        for index, obj in enumerate(bpy.context.collection.objects, start=1):
            if obj.type == 'MESH':
                
                # reverse transformations for y and z, and convert to global coordinates
                coords = [(obj.matrix_world @ x.co).xyz for x in obj.data.vertices]
                coords = [(x.x,x.z,-x.y) for x in coords]
                # for (Blender) planes, resort vertices order
                if len(coords) == 4:
                    coords[2], coords[3] = coords[3], coords[2]

                # extract the material_index and texture_name from the object
                split_name = obj.name.split('_')
                if len(split_name) > 1 and split_name[-1].isdigit():
                    material_index = int(split_name[-1])
                    obj_name = '_'.join(split_name[:-1]) # exclude material_index in the Name
                else:
                    material_index = 0  
                    obj_name = obj.name

                texture_name = obj.get('texture_name', 'RINTER')              
                tex_mode = obj.get('TexCoords_mode', 'repeating_vertical')    
                tex_values = obj.get('TexCoords_values (x,y)', (10.0, 10.0))   

                # Write data
                f.write(f"# {obj_name}\n") # use obj_name instead of obj.name
                f.write(f"create_and_append_polygon(\n")
                f.write(f"{tab}bound_number = {index},\n")  
                f.write(f"{tab}material_index = {material_index},\n")
                f.write(f"{tab}vertex_coordinates=[\n")
                
                for i, coord in enumerate(coords):
                    coordz = tuple(round(val, decimals) for val in coord)
                    if i != len(coords) - 1:
                        f.write(f"{tab}{tab}({coordz[0]:.{decimals}f}, {coordz[1]:.{decimals}f}, {coordz[2]:.{decimals}f}),\n")
                    else:
                        f.write(f"{tab}{tab}({coordz[0]:.{decimals}f}, {coordz[1]:.{decimals}f}, {coordz[2]:.{decimals}f})])\n\n")

                f.write(f"generate_and_save_bms_file(\n")
                f.write(f"{tab}string_names = [\"{texture_name}\"],\n") 
                f.write(
                    f"{tab}TexCoords=generate_tex_coords(mode=\"{tex_mode}\", repeat_x={tex_values[0]}, repeat_y={tex_values[1]}))\n\n")
                
# Export BAI Paths
def export_bai_paths_func(filename):
    with open(filename, "a") as f:  # Append mode
        for obj in bpy.context.collection.objects:
            if obj.type == 'CURVE':
                f.write(f"# {obj.name}\n")
                f.write(f"{tab}Polyline Coordinates:\n")
                
                # Loop through each spline in the curve
                for spline in obj.data.splines:
                    for point in spline.points:
                        coords = point.co
                        f.write(f"{tab}{tab}({coords[0]:.{decimals}f}, {coords[1]:.{decimals}f}, {coords[2]:.{decimals}f})\n")
                f.write("\n")  # extra line for visual separation between polylines

# Polyline Coloring
def apply_color_scheme():
    colors = [(0, 0, 1, 1), (0, 1, 0, 1)]  # Blue, Green
    red_color = (1, 0, 0, 1)  # Red

    curve_objects = [obj for obj in bpy.context.collection.objects if obj.type == 'CURVE']

    for curve_object in curve_objects:
        splines = curve_object.data.splines
        for i in range(len(splines)):
            mat = bpy.data.materials.new(name=f"Material_{curve_object.name}_{i}")

            if i == 0 or i == len(splines) - 1:  # Check if it is the first or the last segment
                mat.diffuse_color = red_color
            else:
                mat.diffuse_color = colors[(i-1) % len(colors)]  # Alternate between Blue and Green for the rest

            curve_object.data.materials.append(mat)
            splines[i].material_index = i
            
apply_color_scheme()

# Create Polylines from Coordinates
def add_predefined_polylines(polyline_coords_list):
    for i, polyline_coords in enumerate(polyline_coords_list):
        # Create the Curve Datablock
        curve_data = bpy.data.curves.new(f"MyPolyline_{i}", type='CURVE')
        curve_object = bpy.data.objects.new(f"MyPolyline_{i}", curve_data)
        bpy.context.collection.objects.link(curve_object)
    
        for j in range(len(polyline_coords)-1):
            create_polyline(curve_object, [polyline_coords[j], polyline_coords[j+1]])
    
    apply_color_scheme()

def parse_polylines_from_file(filepath):
    polyline_coords_list = []
    polyline_coords = []

    with open(filepath, 'r') as file:
        for line in file:
            if line.strip() == '':
                # Empty line denotes end of polyline, add current polyline to the list and start a new one
                polyline_coords_list.append(polyline_coords)
                polyline_coords = []
            else:
                # Parse coordinates and add to the current polyline
                x, y, z = map(float, line.strip().split(','))
                polyline_coords.append((x, y, z))

    # Add the last polyline if it's not empty
    if polyline_coords:
        polyline_coords_list.append(polyline_coords)

    return polyline_coords_list

# Adding a Polyline with Predefined Values
if import_and_model_bai_paths:
    # polyline_coords_list = parse_polylines_from_file(bai_paths_import_file) # CHICAGO BAI
    
    # MANUAL PAHTS
    polyline_coords_road = [(0, 0, 0), 
                            (0, 40, 0), 
                            (0, 80, 10), 
                            (0, 120, 20), 
                            (0, 160, 30), 
                            (0, 200, 30), 
                            (0, 240, 30), 
                            (0, 280, 30)]
    
    polyline_coords_shortcut = [(30, 40, 0), (60, 40, 0), (90, 40, 0)] 
    polyline_coords_list = [polyline_coords_road, polyline_coords_shortcut]  # add more if you want

    add_predefined_polylines(polyline_coords_list)
    
# Import and Model Vertices in Blender
if import_and_model_vertices:
    with open(model_vertices_import_file, "r") as file:
        lines = file.readlines()

    for index, line in enumerate(lines):
        coords = extract_coords(line)
        create_mesh(coords, f"Shape_{index}")
                
# Export Model Vertices (in Collection)
if export_model_vertices:
    export_mesh(model_vertices_export_file)
    
# Open Model Vertices Text File after Export
if open_model_file_after_export:
    if os.name == 'nt':  # for windows
        os.startfile(model_vertices_export_file)
    elif os.name == 'posix':  # for mac/linux
        subprocess.call(('open', model_vertices_export_file))
    
# Export the BAI Paths
if export_bai_paths:
    export_bai_paths_func(bai_paths_export_file)
      
# Open BAI Paths Text File after Export
if open_bai_paths_file_after_export:
    if os.name == 'nt':  # for windows
        os.startfile(bai_paths_export_file)
    elif os.name == 'posix':  # for mac/linux
        subprocess.call(('open', export_filename))
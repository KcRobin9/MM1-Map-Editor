import os
from pathlib import Path
import bpy
from constants.file_formats import FileType
from constants.misc import Executable
from core.geometry.main import transform_coordinate_system
from core.vector.vector_3 import Vector3
from helpers.main import is_process_running
from integrations.blender.uv_mapping import tile_uvs, rotate_uvs, unwrap_uv_to_aspect_ratio, update_uv_tiling


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
    
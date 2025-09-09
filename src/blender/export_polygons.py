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
    
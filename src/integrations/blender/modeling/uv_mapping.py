import bpy
import math

from src.constants.textures import Texture

from pathlib import Path
from src.constants.file_formats import FileType


_texture_folder = None


def set_texture_folder(folder) -> None:
    global _texture_folder
    _texture_folder = folder


def _build_texture_items():
    items = []
    for attr_name, dds_name in vars(Texture).items():
        if attr_name.startswith('_') or not isinstance(dds_name, str):
            continue
        display_name = attr_name.replace('_', ' ').title()
        items.append((dds_name, display_name, dds_name))
    items.sort(key=lambda x: x[1])
    return items


TEXTURE_ENUM_ITEMS = _build_texture_items()


def update_texture_name(self, context) -> None:
    if not _texture_folder or not self.texture_name:
        return

    def apply_texture(obj) -> None:
        texture_path = Path(str(_texture_folder)) / f"{obj.texture_name}{FileType.DIRECTDRAW_SURFACE}"
        if not texture_path.exists():
            return

        obj.data.materials.clear()

        material_name = obj.texture_name
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
        texture_node = nodes.new(type="ShaderNodeTexImage")
        texture_image = bpy.data.images.load(str(texture_path), check_existing=True)
        texture_node.image = texture_image

        links = mat.node_tree.links
        links.new(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        links.new(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])

    # Always apply to self first (the active object whose dropdown was changed)
    apply_texture(self)

    # Then apply the same texture to other selected meshes
    selected_meshes = [
        obj for obj in context.selected_objects
        if obj.type == 'MESH' and obj != self
    ]
    for obj in selected_meshes:
        # Directly apply self's chosen texture to each other selected object
        texture_path = Path(str(_texture_folder)) / f"{self.texture_name}{FileType.DIRECTDRAW_SURFACE}"
        if texture_path.exists():
            obj.data.materials.clear()
            material_name = self.texture_name

            if material_name in bpy.data.materials:
                mat = bpy.data.materials[material_name]
            else:
                mat = bpy.data.materials.new(name=material_name)

            obj.data.materials.append(mat)
            obj.active_material = mat
            mat.use_nodes = True
            nodes = obj.data.materials[0].node_tree.nodes

            for node in nodes:
                nodes.remove(node)

            diffuse_shader = nodes.new(type="ShaderNodeBsdfPrincipled")
            texture_node = nodes.new(type="ShaderNodeTexImage")
            texture_image = bpy.data.images.load(str(texture_path), check_existing=True)
            texture_node.image = texture_image
            links = obj.data.materials[0].node_tree.links
            links.new(texture_node.outputs["Color"], diffuse_shader.inputs["Base Color"])
            output_node = nodes.new(type="ShaderNodeOutputMaterial")
            links.new(diffuse_shader.outputs["BSDF"], output_node.inputs["Surface"])


def update_uv_tiling(self, context) -> None:
    obj = self
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return

    tile_x = obj.tile_x
    tile_y = obj.tile_y
    angle_degrees = obj.angle_degrees

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


class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's tile and rotation properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            if obj.type != 'MESH':
                continue
            update_uv_tiling(obj, context)
        return {"FINISHED"}
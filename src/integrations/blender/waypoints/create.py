import bpy
import math
from typing import Optional, Tuple
from mathutils import Vector

from src.constants.color import Color
from src.constants.folder import Folder
from src.game.waypoints.constants import Rotation, Width
from src.integrations.blender.waypoints.helpers import update_waypoint_colors
from src.integrations.blender.waypoints.constants import (
    POLE_HEIGHT, POLE_DIAMETER, FLAG_HEIGHT, FLAG_HEIGHT_OFFSET,
    FLAG_TEXTURE, IMG_PREFIX, MAT_PREFIX, FLAG_BANDS, FlagUV
)


_WP_COLLECTION = "Waypoints"


def _get_or_create_wp_collection() -> bpy.types.Collection:
    col = bpy.data.collections.get(_WP_COLLECTION)
    if col is None:
        col = bpy.data.collections.new(_WP_COLLECTION)
        bpy.context.scene.collection.children.link(col)
    return col


def _move_to_wp_collection(obj: bpy.types.Object) -> None:
    target = _get_or_create_wp_collection()
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    target.objects.link(obj)


def create_waypoint_material(name: str, color: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = Color.to_rgba(color)
    return mat


def _load_source_texture() -> Optional[bpy.types.Image]:
    tex_path = Folder.Resources.Editor.Textures / FLAG_TEXTURE
    if not tex_path.is_file():
        return None

    existing = bpy.data.images.get(FLAG_TEXTURE)
    if existing:
        return existing

    img      = bpy.data.images.load(str(tex_path))
    img.name = FLAG_TEXTURE
    return img


def _get_or_create_cropped_image(flag_type: str) -> Optional[bpy.types.Image]:
    img_name = IMG_PREFIX + flag_type
    existing = bpy.data.images.get(img_name)
    if existing:
        return existing

    src = _load_source_texture()
    if src is None:
        return None

    src.pixels  # force load
    src_w        = src.size[0]
    src_h        = src.size[1]
    channels     = src.channels
    y_min, y_max = FLAG_BANDS[flag_type]
    scale        = src_h / 1024.0
    py_min       = round(y_min * scale)
    py_max       = round(y_max * scale)
    crop_h       = py_max - py_min

    src_pixels = list(src.pixels)

    cropped = bpy.data.images.new(img_name, width=src_w, height=crop_h, alpha=True)
    cropped.colorspace_settings.name = src.colorspace_settings.name

    dst_pixels = [0.0] * (src_w * crop_h * channels)

    for row in range(crop_h):
        src_row   = py_min + row
        dst_row   = (crop_h - 1) - row   # DDS is top-to-bottom; Blender pixels are bottom-to-top
        src_start = src_row * src_w * channels
        dst_start = dst_row * src_w * channels
        dst_pixels[dst_start: dst_start + src_w * channels] = \
            src_pixels[src_start: src_start + src_w * channels]

    cropped.pixels = dst_pixels
    cropped.pack()
    return cropped


def purge_flag_materials() -> None:
    for flag_type in (FlagUV.CHECKPOINT, FlagUV.FINISH, FlagUV.BANK, FlagUV.HIDEOUT):
        mat = bpy.data.materials.get(MAT_PREFIX + flag_type)

        if mat:
            bpy.data.materials.remove(mat)
        img = bpy.data.images.get(IMG_PREFIX + flag_type)
        if img:
            bpy.data.images.remove(img)


def _get_or_create_flag_material(flag_type: str) -> bpy.types.Material:
    mat_name = MAT_PREFIX + flag_type
    existing = bpy.data.materials.get(mat_name)

    if existing:
        return existing

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes       = True
    mat["wp_textured"]  = True
    mat["wp_flag_type"] = flag_type

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output   = nodes.new("ShaderNodeOutputMaterial")
    bsdf     = nodes.new("ShaderNodeBsdfPrincipled")
    tex_node = nodes.new("ShaderNodeTexImage")
    uv_node  = nodes.new("ShaderNodeTexCoord")

    img = _get_or_create_cropped_image(flag_type)

    if img:
        tex_node.image     = img
        tex_node.extension = "CLIP"

    bsdf.inputs["Roughness"].default_value          = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0

    links.new(uv_node.outputs["UV"],     tex_node.inputs["Vector"])
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"],      output.inputs["Surface"])

    output.location   = (400, 0)
    bsdf.location     = (200, 0)
    tex_node.location = (-100, 0)
    uv_node.location  = (-400, 0)

    return mat


def _apply_flag_uvs(flag: bpy.types.Object, flip_u: bool = False) -> None:
    mesh     = flag.data
    uv_layer = mesh.uv_layers.active or mesh.uv_layers.new()

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v  = mesh.vertices[mesh.loops[loop_idx].vertex_index]
            u  = (1.0 if v.co.x > 0 else 0.0) if flip_u else (0.0 if v.co.x > 0 else 1.0)
            vv = 1.0 if v.co.y > 0 else 0.0
            uv_layer.data[loop_idx].uv = (u, vv)


def create_waypoint_pole(height: float, diameter: float,
                         location: Tuple[float, float, float],
                         color: Tuple[float, float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(radius=diameter / 2, depth=height, location=location)
    pole = bpy.context.object
    pole.data.materials.append(create_waypoint_material("PoleMaterial", color))
    return pole


def create_waypoint_flag(width: float, height: float, cursor_z: float, flag_height_offset: float,
                         location: Tuple[float, float, float], flag_type: str) -> bpy.types.Object:
    mat = _get_or_create_flag_material(flag_type)
    z   = cursor_z + flag_height_offset + height / 2

    bpy.ops.mesh.primitive_plane_add(size=1, location=location)
    front                  = bpy.context.object
    front.scale.x          = width
    front.scale.y          = height
    front.rotation_euler.x = math.pi / 2
    front.location.z       = z
    front.data.materials.append(mat)
    _apply_flag_uvs(front, flip_u=False)

    bpy.ops.mesh.primitive_plane_add(size=1, location=location)
    back                  = bpy.context.object
    back.scale.x          = width
    back.scale.y          = height
    back.rotation_euler.x = math.pi / 2
    back.location.z       = z
    back.data.materials.append(mat)
    _apply_flag_uvs(back, flip_u=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    front.select_set(True)
    back.select_set(True)
    bpy.context.view_layer.objects.active = front
    bpy.ops.object.join()

    return bpy.context.object


def create_gold_bar(location: Tuple[float, float, float], scale: float = 1.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    gold = bpy.context.object
    gold.scale *= scale

    gold.data.materials.append(create_waypoint_material("GoldMaterial", Color.YELLOW))
    gold.name = "Gold_Default"
    _move_to_wp_collection(gold)
    return gold


def create_waypoint(x: Optional[float] = None, y: Optional[float] = None, z: Optional[float] = None,
                    rotation: float = Rotation.NORTH, width: float = Width.DEFAULT,
                    name: Optional[str] = None, flag_type: str = FlagUV.CHECKPOINT) -> bpy.types.Object:

    cursor_location = bpy.context.scene.cursor.location.copy() if (x is None or y is None or z is None) \
                      else Vector((x, y, z))

    pole_one_location = (cursor_location.x - width / 2, cursor_location.y, cursor_location.z + POLE_HEIGHT / 2)
    pole_two_location = (cursor_location.x + width / 2, cursor_location.y, cursor_location.z + POLE_HEIGHT / 2)

    pole_one = create_waypoint_pole(POLE_HEIGHT, POLE_DIAMETER, pole_one_location, Color.WHITE)
    pole_two = create_waypoint_pole(POLE_HEIGHT, POLE_DIAMETER, pole_two_location, Color.WHITE)
    flag     = create_waypoint_flag(width, FLAG_HEIGHT, cursor_location.z, FLAG_HEIGHT_OFFSET,
                                    cursor_location, flag_type)

    bpy.ops.object.select_all(action="DESELECT")
    pole_one.select_set(True)
    pole_two.select_set(True)
    flag.select_set(True)
    bpy.context.view_layer.objects.active = flag
    bpy.ops.object.join()

    waypoint                  = bpy.context.object
    waypoint.rotation_euler.z = math.radians(rotation)
    waypoint.name             = name if name else "WP_Default"

    midpoint = (
        (pole_one_location[0] + pole_two_location[0]) / 2,
        (pole_one_location[1] + pole_two_location[1]) / 2,
        cursor_location.z,
    )
    bpy.context.scene.cursor.location = midpoint
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

    if x is None or y is None or z is None:
        bpy.context.scene.cursor.location = cursor_location

    waypoint["wp_flag_type"] = flag_type

    update_waypoint_colors()
    _move_to_wp_collection(waypoint)
    return waypoint
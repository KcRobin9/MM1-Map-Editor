import bpy

from src.constants.color import Color
from src.constants.file_formats import Material, Room
from src.constants.constants import YES, NO


def get_used_bound_numbers(scene) -> set:
    used = set()
    for obj in scene.objects:
        if obj.type == "MESH" and obj.name.startswith("P"):
            try:
                num = int(obj.name[1:].split(".")[0])
                used.add(num)
            except ValueError:
                pass
    return used


def next_available_bound_number(used: set, start: int = 201) -> int:
    n = start
    while n in used or n == 0 or n == 200:
        n += 1
    return n


def has_invalid_polygon_names(scene) -> list:
    """Returns list of objects with invalid names (contain a dot suffix)."""
    invalid = []
    for obj in scene.objects:
        if obj.type == "MESH" and obj.name.startswith("P") and "." in obj.name:
            invalid.append(obj.name)
    return invalid


def assign_map_editor_properties(obj, source=None) -> None:
    if source:
        obj["cell_type"]       = source.get("cell_type", Room.DEFAULT)
        obj["material_index"]  = source.get("material_index", Material.DEFAULT)
        obj["hud_color"]       = source.get("hud_color", Color.ROAD)
        obj["sort_vertices"]   = source.get("sort_vertices", NO)
        obj["always_visible"]  = source.get("always_visible", YES)
        obj.tile_x             = source.tile_x
        obj.tile_y             = source.tile_y
        obj.angle_degrees      = source.angle_degrees
    else:
        obj["cell_type"]      = Room.DEFAULT
        obj["material_index"] = Material.DEFAULT
        obj["hud_color"]      = Color.ROAD
        obj["sort_vertices"]  = NO
        obj["always_visible"] = YES
        obj.tile_x            = 1.0
        obj.tile_y            = 1.0
        obj.angle_degrees     = 0.0

    if obj.data.uv_layers.active is None:
        obj.data.uv_layers.new(name="UVMap")
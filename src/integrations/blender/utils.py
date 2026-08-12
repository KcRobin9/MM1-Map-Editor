import bpy

from src.constants.color import Color
from src.constants.file_formats import Material, Room
from src.constants.constants import YES, NO


# The bound number in a polygon name, or None when the name is not one.
# Blender's deduplicated form counts, so P201 and P201.001 both give 201.
def polygon_bound_number(name: str):
    if not name.startswith("P"):
        return None

    try:
        return int(name[1:].split(".")[0])
    except ValueError:
        return None


# Takes any object sequence rather than the scene, so callers can pass a selection instead.
def get_polygon_objects(objects, sort: bool = False) -> list:
    # A polygon is P followed by a digit, which leaves out reference objects such as PA_Start
    polygons = [
        obj for obj in objects
        if obj.type == "MESH" and polygon_bound_number(obj.name) is not None
    ]

    if not sort:
        return polygons

    return sorted(polygons, key=lambda obj: (polygon_bound_number(obj.name), obj.name))


def get_used_bound_numbers(scene) -> set:
    used = set()
    for obj in scene.objects:
        number = polygon_bound_number(obj.name) if obj.type == "MESH" else None
        if number is not None:
            used.add(number)
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
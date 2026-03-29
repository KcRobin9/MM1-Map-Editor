import bpy
from typing import NamedTuple, List
from pathlib import Path

from src.constants.file_formats import Material, Room
from src.constants.color import Color
from src.integrations.blender.utils import get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties

from src.constants.textures import Texture


class PolySpec(NamedTuple):
    width:          float
    length:         float
    offset_x:       float
    offset_y:       float
    texture:        str
    material_index: int   = Material.DEFAULT
    cell_type:      int   = Room.DEFAULT
    hud_color:      str   = Color.ROAD
    tile_x:         float = 2.0
    tile_y:         float = 2.0
    angle_degrees:  float = 0.0


PRESETS: dict[str, List[PolySpec]] = {

    "ROAD_SIDEWALK": [
        PolySpec(width=20.0, length=20.0, offset_x=0.0,   offset_y=0.0, texture=Texture.ROAD_2_LANE, tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-12.5, offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=12.5,  offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
    ],
    "BOULEVARD_SIDEWALK": [
        PolySpec(width=30.0, length=20.0, offset_x=0.0,   offset_y=0.0, texture=Texture.ROAD_3_LANE, tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-17.5, offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=17.5,  offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
    ],
    "ALLEY": [
        PolySpec(width=8.0, length=20.0, offset_x=0.0, offset_y=0.0, texture=Texture.ROAD_1_LANE, tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
    ],
    "INTERSECTION_T": [
        PolySpec(width=20.0, length=20.0, offset_x=0.0,  offset_y=0.0,   texture=Texture.ROAD_2_LANE,  tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
        PolySpec(width=20.0, length=20.0, offset_x=0.0,  offset_y=-20.0, texture=Texture.INTERSECTION, tile_x=2.0, tile_y=2.0, angle_degrees=0.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-12.5, offset_y=0.0,  texture=Texture.SIDEWALK,     tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=12.5,  offset_y=0.0,  texture=Texture.SIDEWALK,     tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
    ],
    "INTERSECTION_4WAY": [
        PolySpec(width=20.0, length=20.0, offset_x=0.0,  offset_y=0.0,  texture=Texture.INTERSECTION, tile_x=2.0, tile_y=2.0, angle_degrees=0.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-12.5, offset_y=0.0, texture=Texture.SIDEWALK,     tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=12.5,  offset_y=0.0, texture=Texture.SIDEWALK,     tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
        PolySpec(width=20.0, length=5.0, offset_x=0.0,  offset_y=-12.5, texture=Texture.SIDEWALK,     tile_x=1.0, tile_y=4.0, angle_degrees=0.0),
        PolySpec(width=20.0, length=5.0, offset_x=0.0,  offset_y=12.5,  texture=Texture.SIDEWALK,     tile_x=1.0, tile_y=4.0, angle_degrees=0.0),
        # Corner pieces
        PolySpec(width=5.0,  length=5.0, offset_x=-12.5, offset_y=-12.5, texture=Texture.SIDEWALK,   tile_x=2.0, tile_y=2.0, angle_degrees=0.0),
        PolySpec(width=5.0,  length=5.0, offset_x=12.5,  offset_y=-12.5, texture=Texture.SIDEWALK,   tile_x=2.0, tile_y=2.0, angle_degrees=0.0),
        PolySpec(width=5.0,  length=5.0, offset_x=-12.5, offset_y=12.5,  texture=Texture.SIDEWALK,   tile_x=2.0, tile_y=2.0, angle_degrees=0.0),
        PolySpec(width=5.0,  length=5.0, offset_x=12.5,  offset_y=12.5,  texture=Texture.SIDEWALK,   tile_x=2.0, tile_y=2.0, angle_degrees=0.0),
    ],
    "ROAD_ZEBRA_CROSSING": [
        PolySpec(width=20.0, length=8.0,  offset_x=0.0, offset_y=-14.0, texture=Texture.ROAD_2_LANE,     tile_x=2.0, tile_y=1.0, angle_degrees=90.0),
        PolySpec(width=20.0, length=4.0,  offset_x=0.0, offset_y=0.0,   texture=Texture.ZEBRA_CROSSING,  tile_x=2.0, tile_y=1.0, angle_degrees=0.0),
        PolySpec(width=20.0, length=8.0,  offset_x=0.0, offset_y=14.0,  texture=Texture.ROAD_2_LANE,     tile_x=2.0, tile_y=1.0, angle_degrees=90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-12.5, offset_y=0.0, texture=Texture.SIDEWALK,        tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=12.5,  offset_y=0.0, texture=Texture.SIDEWALK,        tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
    ],
    "FREEWAY": [
        PolySpec(width=40.0, length=20.0, offset_x=0.0, offset_y=0.0, texture=Texture.FREEWAY, tile_x=2.0, tile_y=4.0, angle_degrees=90.0),
    ],
    "GRASS_PATCH": [
        PolySpec(width=20.0, length=20.0, offset_x=0.0, offset_y=0.0, texture=Texture.GRASS, material_index=Material.GRASS, hud_color=Color.GRASS, tile_x=4.0, tile_y=4.0, angle_degrees=0.0),
    ],
    "WATER_SURFACE": [
        PolySpec(width=40.0, length=40.0, offset_x=0.0, offset_y=0.0, texture=Texture.WATER, material_index=Material.WATER, hud_color=Color.WATER, tile_x=4.0, tile_y=4.0, angle_degrees=0.0),
    ],
    "SNOW_ROAD": [
        PolySpec(width=20.0, length=20.0, offset_x=0.0,   offset_y=0.0, texture=Texture.ROAD_2_LANE,    tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-12.5, offset_y=0.0, texture=Texture.SNOW,           tile_x=4.0, tile_y=2.0, angle_degrees=0.0),
        PolySpec(width=5.0,  length=20.0, offset_x=12.5,  offset_y=0.0, texture=Texture.SNOW,           tile_x=4.0, tile_y=2.0, angle_degrees=0.0),
    ],

}

PRESET_ITEMS = [
    ("ROAD_SIDEWALK",      "Road + Sidewalk",           "2-lane road with sidewalks on both sides"),
    ("BOULEVARD_SIDEWALK", "Boulevard + Sidewalk",      "Wide 3-lane road with sidewalks"),
    ("ALLEY",              "Alley",                     "Narrow 1-lane road, no sidewalks"),
    ("INTERSECTION_T",     "T-Intersection",            "T-shaped road junction"),
    ("INTERSECTION_4WAY",  "4-Way Intersection",        "Full crossroads with corner sidewalk pieces"),
    ("ROAD_ZEBRA_CROSSING","Road + Zebra Crossing",     "Road split by a pedestrian crossing"),
    ("FREEWAY",            "Freeway",                   "Wide freeway section, no sidewalks"),
    ("GRASS_PATCH",        "Grass Patch",               "Open grassy area"),
    ("WATER_SURFACE",      "Water Surface",             "Large flat water polygon"),
    ("SNOW_ROAD",          "Snow Road",                 "Road with snow banks on the sides"),
]


def _apply_material(obj: bpy.types.Object, texture: str, texture_folder) -> None:
    if not texture_folder:
        return

    texture_path = Path(str(texture_folder)) / f"{texture}.DDS"
    if not texture_path.exists():
        return

    mat = bpy.data.materials.get(texture) or bpy.data.materials.new(name=texture)

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.active_material = mat
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    bsdf     = nodes.new("ShaderNodeBsdfPrincipled")
    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = bpy.data.images.load(str(texture_path), check_existing=True)
    output   = nodes.new("ShaderNodeOutputMaterial")

    links = mat.node_tree.links
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"],      output.inputs["Surface"])


def _create_rect_object(name: str, width: float, length: float) -> bpy.types.Object:
    hw, hl = width / 2, length / 2
    verts = [(-hw, -hl, 0.0), (hw, -hl, 0.0), (hw, hl, 0.0), (-hw, hl, 0.0)]
    faces = [(0, 1, 2, 3)]

    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    bpy.context.collection.objects.link(obj)

    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")

    return obj


class OBJECT_OT_SpawnPreset(bpy.types.Operator):
    bl_idname      = "object.spawn_polygon_preset"
    bl_label       = "Spawn Preset"
    bl_description = "Spawn a group of connected polygons at the 3D cursor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        from src.integrations.blender.modeling.uv_mapping import _texture_folder

        preset_key = context.scene.polygon_preset
        specs      = PRESETS.get(preset_key)

        if not specs:
            self.report({"ERROR"}, f"Unknown preset: {preset_key}")
            return {"CANCELLED"}

        cursor  = context.scene.cursor.location
        used    = get_used_bound_numbers(context.scene)
        created = []

        for spec in specs:
            num = next_available_bound_number(used)
            used.add(num)

            obj = _create_rect_object(f"P{num}", spec.width, spec.length)
            obj.location = (cursor.x + spec.offset_x, cursor.y + spec.offset_y, cursor.z)

            assign_map_editor_properties(obj)
            obj["cell_type"]      = str(spec.cell_type)
            obj["material_index"] = str(spec.material_index)

            obj.tile_x            = spec.tile_x
            obj.tile_y            = spec.tile_y
            obj.angle_degrees     = spec.angle_degrees

            _apply_material(obj, spec.texture, _texture_folder)
            created.append(obj)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in created:
            obj.select_set(True)
        if created:
            context.view_layer.objects.active = created[0]

        self.report({"INFO"}, f"Spawned {len(created)} polygon(s) from '{preset_key}'")
        return {"FINISHED"}
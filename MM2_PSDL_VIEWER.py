"""
PURE MM2 -> Blender ground-truth viewer.

Renders the ORIGINAL MM2 data with ZERO MM1-pipeline placement code, in the same Blender
coordinates as the MM1 Map-Editor preview --- so you can run TWO Blender instances (one MM1 preview,
one this) and compare the same spot pixel-by-pixel:

  * "PSDL Rooms"    --- the wilkovatch-tessellated PSDL geometry, one object PER MM2 ROOM (not our
                        quadtree cells), raw expander UVs, real textures.
  * "MM2 Props GT"  --- every props.pathset instance with the REAL MM2 .pkg mesh, placed by MM2's own
                        facing math (mesh local +X -> p1-p0). Models without a .pkg get an ARROW empty
                        pointing the stored facing. Object names = MM2 model names.
  * "BAI Roads GT"  --- lane splines (cyan), sidewalk edges (green), centreline (white) from the .bai.
  * "BAI TrafficLights GT" --- the BAI's STORED traffic-light origin verts (arrow empties), the
                        ground truth to judge our synthesised intersection lights against.

No stored ground truth exists for DENSITY furniture (MM2 places it at runtime) --- compare that
against real MM2 screenshots instead.

USE: open a second Blender manually -> Scripting tab -> open this file -> Run Script.
     City = ACTIVE_CITY from the editor settings (or set env MM2_VIEWER_CITY=SF|NY|BA|LONDON).
HEADLESS CHECK: python MM2_PSDL_VIEWER.py --gather-only   (counts only, no bpy)
"""
import os
import sys
import site
import math
import json
import struct
from pathlib import Path

# Blender's interpreter carries neither the repo root nor the user site-packages on sys.path, and
# this file lives AT the repo root, so both are added before any `src.*` import can resolve. This is
# the one place Folder.BASE cannot be used --- importing it is exactly what needs the path first.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

_USER_SITE = site.getusersitepackages()
if _USER_SITE and Path(_USER_SITE).is_dir() and _USER_SITE not in sys.path:
    sys.path.append(_USER_SITE)

# Optional dependency: gather() is deliberately headless-safe so --gather-only runs without Blender.
try:
    import bpy
    import bmesh
except ImportError:
    bpy = bmesh = None

from src.core.vector.vector_3 import Vector3
from src.core.geometry.main import transform_coordinate_system
from src.game.mapgen.mm2.bai import parse_bai_full
from src.game.mapgen.mm2.pkg import parse_pkg
from src.game.mapgen.mm2 import pathset
from src.game.mapgen.mm2.mm2_props import VEHICLE_RULE_SIGNALIZED
from src.game.mapgen.mm2.mm2_city import load_expanded, load_textures
from src.constants.folder import Folder
from src.constants.file_formats import FileType, LOD

CITY = os.environ.get("MM2_VIEWER_CITY", "").upper() or None

MESH_LODS = (LOD.HIGH, LOD.MEDIUM, LOD.LOW, LOD.VERY_LOW)   # some pkgs ship no H LOD
NO_TEXTURE = "notexture"

VERTS_PER_TRIANGLE = 3
MIN_SPLINE_POINTS = 2
ORIGIN_EPSILON = 1e-6       # a traffic-light origin at 0,0,0 is an unset record
FACING_EPSILON = 1e-9       # below this the stored facing has no direction


class Collection:
    """Names of the collections this viewer owns. Toggling their visibility is how you A/B."""
    ROOMS = "PSDL Rooms"
    PROPS = "MM2 Props GT"
    ROADS = "BAI Roads GT"
    TRAFFIC_LIGHTS = "BAI TrafficLights GT"


class LineColor:
    """Blender viewport object colours, so the BAI spline kinds are told apart at a glance."""
    CENTRE = (1.0, 1.0, 1.0, 1.0)
    LANE = (0.0, 0.8, 1.0, 1.0)
    SIDEWALK = (0.1, 1.0, 0.2, 1.0)


LINE_COLORS = {"centre": LineColor.CENTRE, "lane": LineColor.LANE, "swalk": LineColor.SIDEWALK}


# ── data gathering (headless-safe: no bpy) ────────────────────────────────────────────────────────

def city_config(city: str = None) -> tuple:
    """The (json_path, options) MM2_CITY entry for `city`, or for the active city when omitted.

    Per-city configs live in the gitignored src/USER/settings/local.py, so viewing a city OTHER
    than the active one needs that file's CITY_CFGS.
    """
    from src.USER.settings import main as settings

    if city:
        configs = getattr(settings, "CITY_CFGS", None)
        if not configs:
            raise SystemExit(f"MM2_VIEWER_CITY={city} needs CITY_CFGS in src/USER/settings/local.py")
        if city.upper() not in configs:
            raise SystemExit(f"unknown city {city!r}; CITY_CFGS has {sorted(configs)}")

        return city.upper(), configs[city.upper()]["MM2_CITY"]

    if not settings.MM2_CITY:
        raise SystemExit("no MM2_CITY set --- configure it in src/USER/settings/local.py")

    return getattr(settings, "ACTIVE_CITY", "ACTIVE"), settings.MM2_CITY


def _stock_geometry_dirs() -> list:
    """Every configured city's MM2 geometry dir --- stock props (sp_*_f) live in the base game's."""
    from src.USER.settings import main as settings

    configs = getattr(settings, "CITY_CFGS", None) or {}

    return [config.get("MM2_CITY", (None, {}))[1].get("inst_geometry_dir")
            for config in configs.values()]


def _gather_rooms(json_path: str) -> list:
    """PSDL rooms as [{id, objects}], where each object is a list of {tex, otype, tris} groups.

    One group per material, because a room object can span several textures and Blender wants one
    material slot each. Triangles carry their own UVs so nothing has to be recomputed at build time.
    """
    data = load_expanded(json_path)
    raw_path = json_path.replace("expanded_psdl.json", "raw_psdl.json")
    texture_pool = load_textures(raw_path) if Path(raw_path).exists() else []

    rooms = []
    for room in data["rooms"]:
        objects = []

        for room_object in room.get("objects") or []:
            if not room_object:
                continue

            vertices = room_object["vertices"]
            uvs = room_object.get("uvs") or []
            materials = room_object.get("materials") or []
            groups = []

            for group_index, indices in enumerate(room_object.get("triangles") or []):
                material_index = materials[group_index] if group_index < len(materials) else None
                texture = (texture_pool[material_index]
                           if isinstance(material_index, int) and material_index < len(texture_pool)
                           else "")

                triangles = []
                for start in range(0, len(indices) - 2, VERTS_PER_TRIANGLE):
                    corners = indices[start:start + VERTS_PER_TRIANGLE]
                    try:
                        triangles.append(tuple(
                            (tuple(vertices[i]), tuple(uvs[i]) if i < len(uvs) else (0.0, 0.0))
                            for i in corners))
                    except IndexError:
                        continue        # a truncated index run just loses that triangle

                if triangles:
                    groups.append({"tex": (texture or "").upper(),
                                   "otype": room_object.get("name", ""), "tris": triangles})

            if groups:
                objects.append(groups)

        if objects:
            rooms.append({"id": room["id"], "objects": objects})

    return rooms


def _gather_prop_meshes(props: list, options: dict) -> dict:
    """model -> {sections, shader_tex} from its real .pkg, or None when no mesh could be read.

    Player-made cities reuse STOCK MM2 props (sp_*_f / _l) whose .pkg lives in the base game's
    geometry dir rather than the city's own, so the city dir is searched first and then every other
    configured city's.
    """
    geometry_dirs = [directory for directory
                     in [options.get("inst_geometry_dir")] + _stock_geometry_dirs()
                     if directory and Path(directory).is_dir()]
    geometry_dirs = list(dict.fromkeys(geometry_dirs))      # de-duplicate, keep search order

    if not (props and geometry_dirs):
        return {}

    meshes = {}
    for model in sorted({prop["model"] for prop in props}):
        pkg_path = next((Path(directory) / (model + FileType.MM2_MESH)
                         for directory in geometry_dirs
                         if (Path(directory) / (model + FileType.MM2_MESH)).is_file()), None)
        if not pkg_path:
            meshes[model] = None
            continue

        try:
            mesh = None
            for lod in MESH_LODS:
                mesh = parse_pkg(str(pkg_path), lod)
                if mesh.get("sections"):
                    break

            meshes[model] = {"sections": (mesh or {}).get("sections") or [],
                             "shader_tex": (mesh or {}).get("shader_tex") or []}
        except (OSError, ValueError, IndexError, KeyError, struct.error):
            meshes[model] = None        # an unreadable pkg falls back to an arrow empty

    return meshes


def _gather_bai(options: dict) -> dict:
    """BAI ground truth: {roads: [{id, lines}], tl: [{road, tag, pos, fac}]}.

    `lines` are (kind, points) so the build can colour each spline kind differently. Traffic lights
    come only from SIGNALIZED road ends; the two stored verts are (position, facing target), which
    is the engine's own aiTrafficLightInstance::Init convention.
    """
    bai = {"roads": [], "tl": []}
    bai_path = options.get("bai_path")
    if not (bai_path and Path(bai_path).exists()):
        return bai

    roads, _ = parse_bai_full(bai_path)
    for road in roads:
        lines = [("centre", list(road.origin))]
        for side in (road.right, road.left):
            for lane in side.lanes:
                lines.append(("lane", list(lane)))
            lines.append(("swalk", list(side.sidewalk_inner)))
            lines.append(("swalk", list(side.sidewalk_outer)))
        bai["roads"].append({"id": road.id, "lines": lines})

        for tag, rule, verts in (("start", road.vrule_start, road.tl_start),
                                 ("end", road.vrule_end, road.tl_end)):
            if rule != VEHICLE_RULE_SIGNALIZED or not verts or len(verts) < 2:
                continue

            position, facing = tuple(verts[0]), tuple(verts[1])
            if any(abs(axis) > ORIGIN_EPSILON for axis in position):
                bai["tl"].append({"road": road.id, "tag": tag,
                                  "pos": position, "fac": facing})

    return bai


def _texture_dirs(options: dict) -> list:
    """This city's own DDS first, then every shared texture folder the build registers."""
    from src.USER.settings.main import EXTRA_TEXTURE_DIRS

    configured = [options.get("custom_dds_dir") or ""] + list(EXTRA_TEXTURE_DIRS or [])
    dirs = [str(Folder.BASE / directory) for directory in configured if directory]
    dirs.append(str(Folder.Resources.Editor.Textures))

    return dirs


def gather(city: str = None) -> dict:
    """Read every MM2 ground-truth source for one city. No Blender involved."""
    city, mm2_city = city_config(city)
    json_path, options = mm2_city[0], mm2_city[1]

    props = []
    pathset_path = options.get("props_pathset")
    if pathset_path and Path(pathset_path).exists():
        # Raw expansion: positions + MM2 facing angle, with NO model mapping applied.
        props = pathset.expand_paths(pathset.parse_pathset(pathset_path))

    return {"city":     city,
            "rooms":    _gather_rooms(json_path),
            "props":    props,
            "meshes":   _gather_prop_meshes(props, options),
            "bai":      _gather_bai(options),
            "tex_dirs": _texture_dirs(options)}


# ── Blender scene build ───────────────────────────────────────────────────────────────────────────

def _free_orphan_data(datablock) -> None:
    """Free an object's data once nothing references it.

    Each datablock type lives in its OWN bpy.data collection, and this viewer makes both meshes
    (rooms, props) and curves (BAI splines) --- handing a Curve to bpy.data.meshes.remove raises.
    """
    if not datablock or getattr(datablock, "users", 1) != 0:
        return

    if isinstance(datablock, bpy.types.Mesh):
        bpy.data.meshes.remove(datablock)
    elif isinstance(datablock, bpy.types.Curve):
        bpy.data.curves.remove(datablock)


def _reset_collection(name: str):
    """The named collection, linked to the scene and emptied so a re-run does not accumulate."""
    collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)

    for stale_object in list(collection.objects):
        datablock = stale_object.data
        bpy.data.objects.remove(stale_object, do_unlink = True)
        _free_orphan_data(datablock)

    return collection


def _material(texture: str, texture_dirs: list, cache: dict):
    """A Principled material showing `texture`, from the first search dir that has the DDS."""
    if texture in cache:
        return cache[texture]

    material = bpy.data.materials.get(f"GT_{texture}") or bpy.data.materials.new(f"GT_{texture}")
    material.use_nodes = True
    nodes = material.node_tree
    nodes.nodes.clear()

    output = nodes.nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.nodes.new("ShaderNodeBsdfPrincipled")
    nodes.links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    for directory in texture_dirs:
        texture_file = Path(directory) / f"{texture}{FileType.DIRECTDRAW_SURFACE}"
        if texture_file.is_file():
            image_node = nodes.nodes.new("ShaderNodeTexImage")
            image_node.image = bpy.data.images.load(str(texture_file), check_existing = True)
            nodes.links.new(image_node.outputs["Color"], shader.inputs["Base Color"])
            break

    cache[texture] = material

    return material


def _mesh_from_groups(name: str, textured_groups, texture_dirs: list, cache: dict):
    """Build one Blender mesh from (texture, triangles) groups, one material slot per texture.

    Triangles arrive in GAME space carrying their own UVs; both are converted here, so the room and
    prop builders share the whole vertex/UV/material path.
    """
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    uv_layer = builder.loops.layers.uv.new()

    slots, slot_of = [], {}
    for texture, triangles in textured_groups:
        if texture not in slot_of:
            slot_of[texture] = len(slots)
            slots.append(texture)
        slot = slot_of[texture]

        for triangle in triangles:
            try:
                face = builder.faces.new(
                    builder.verts.new(transform_coordinate_system(Vector3.from_tuple(point),
                                                                  game_to_blender=True))
                    for point, _ in triangle)
            except ValueError:
                continue        # degenerate or duplicate face

            face.material_index = slot
            for loop, (_, uv) in zip(face.loops, triangle):
                loop[uv_layer].uv = (uv[0], 1.0 - uv[1])    # blender V -> game V

    # A rejected face leaves orphan verts behind; drop them before the mesh is ever drawn.
    loose_vertices = [vertex for vertex in builder.verts if not vertex.link_faces]
    if loose_vertices:
        bmesh.ops.delete(builder, geom = loose_vertices, context = "VERTS")

    for _ in slots:
        mesh.materials.append(None)

    builder.to_mesh(mesh)
    builder.free()
    mesh.validate(verbose = False)

    for index, texture in enumerate(slots):
        mesh.materials[index] = _material(texture, texture_dirs, cache)

    return mesh


def _build_rooms(rooms: list, texture_dirs: list, cache: dict) -> None:
    """One Blender object per MM2 ROOM --- deliberately not our quadtree cells."""
    collection = _reset_collection(Collection.ROOMS)

    for room in rooms:
        groups = [(group["tex"], group["tris"])
                  for room_object in room["objects"] for group in room_object]
        mesh = _mesh_from_groups(f"Room{room['id']}", groups, texture_dirs, cache)
        collection.objects.link(bpy.data.objects.new(f"Room{room['id']}", mesh))


def _build_prop_meshes(meshes: dict, texture_dirs: list, cache: dict) -> dict:
    """model -> a reusable Blender mesh (or None), so every instance shares one datablock."""
    base_meshes = {}

    for model, mesh_data in meshes.items():
        if not mesh_data or not mesh_data["sections"]:
            base_meshes[model] = None
            continue

        shader_textures = mesh_data["shader_tex"]
        groups = []
        for shader_offset, triangles in mesh_data["sections"]:
            texture = (shader_textures[shader_offset]
                       if 0 <= shader_offset < len(shader_textures) else "")
            groups.append(((texture or NO_TEXTURE).upper(), triangles))

        base_meshes[model] = _mesh_from_groups(f"GTPROP_{model}", groups, texture_dirs, cache)

    return base_meshes


def _build_prop_instances(props: list, base_meshes: dict) -> None:
    """Place every pathset instance at MM2's own facing.

    The mesh's local +X is aligned to the stored facing angle, and game R_y(theta) is Blender
    R_z(-theta) under the (x, -z, y) transform. A model with no .pkg becomes an arrow empty so the
    stored facing is still visible.
    """
    collection = _reset_collection(Collection.PROPS)

    for index, prop in enumerate(props):
        mesh = base_meshes.get(prop["model"])
        prop_object = bpy.data.objects.new(f"{prop['model']}.{index}", mesh)

        if mesh is None:
            prop_object.empty_display_type = "SINGLE_ARROW"
            prop_object.empty_display_size = 2.0

        prop_object.location = transform_coordinate_system(
            Vector3(prop["x"], prop["y"], prop["z"]), game_to_blender=True)
        prop_object.rotation_euler = (0.0, 0.0, -math.radians(prop.get("angle") or 0.0))
        collection.objects.link(prop_object)


def _build_bai(bai: dict) -> None:
    """BAI splines as coloured curves, plus an arrow empty per stored traffic-light origin."""
    road_collection = _reset_collection(Collection.ROADS)

    for road in bai["roads"]:
        for kind, points in road["lines"]:
            if len(points) < MIN_SPLINE_POINTS:
                continue

            curve = bpy.data.curves.new(f"R{road['id']}_{kind}", "CURVE")
            curve.dimensions = "3D"
            spline = curve.splines.new("POLY")
            spline.points.add(len(points) - 1)

            for index, point in enumerate(points):
                x, y, z = transform_coordinate_system(Vector3.from_tuple(point),
                                                      game_to_blender=True)
                spline.points[index].co = (x, y, z, 1.0)

            curve_object = bpy.data.objects.new(f"R{road['id']}_{kind}", curve)
            curve_object.color = LINE_COLORS[kind]
            road_collection.objects.link(curve_object)

    light_collection = _reset_collection(Collection.TRAFFIC_LIGHTS)

    for light in bai["tl"]:
        light_object = bpy.data.objects.new(f"TL_r{light['road']}_{light['tag']}", None)
        light_object.empty_display_type = "SINGLE_ARROW"    # the arrow shows the STORED facing
        light_object.empty_display_size = 3.0
        light_object.location = transform_coordinate_system(
            Vector3.from_tuple(light["pos"]), game_to_blender=True)

        delta_x = light["fac"][0] - light["pos"][0]
        delta_z = light["fac"][2] - light["pos"][2]
        if abs(delta_x) > FACING_EPSILON or abs(delta_z) > FACING_EPSILON:
            light_object.rotation_euler = (0.0, 0.0, -math.atan2(delta_z, delta_x))

        light_collection.objects.link(light_object)


def build(data: dict, do_rooms: bool = True, do_props: bool = True, do_bai: bool = True) -> None:
    """Build the ground-truth collections in the current Blender scene."""
    if bpy is None:
        raise RuntimeError("build() needs Blender --- run this inside Blender, or use --gather-only")

    texture_dirs = data["tex_dirs"]
    material_cache = {}

    if do_rooms:
        _build_rooms(data["rooms"], texture_dirs, material_cache)

    if do_props:
        base_meshes = _build_prop_meshes(data["meshes"], texture_dirs, material_cache)
        _build_prop_instances(data["props"], base_meshes)

    if do_bai:
        _build_bai(data["bai"])

    real_meshes = sum(1 for mesh in data["meshes"].values() if mesh)
    print(f"OK MM2 GT viewer [{data['city']}]: {len(data['rooms'])} rooms, "
          f"{len(data['props'])} GT props ({real_meshes} real pkg meshes), "
          f"{len(data['bai']['roads'])} BAI roads, {len(data['bai']['tl'])} stored traffic lights")


if __name__ == "__main__":
    data = gather(CITY)

    if "--gather-only" in sys.argv:
        real_meshes = sum(1 for mesh in data["meshes"].values() if mesh)
        print(f"[gather-only] {data['city']}: rooms={len(data['rooms'])} props={len(data['props'])} "
              f"pkg_meshes={real_meshes}/{len(data['meshes'])} "
              f"bai_roads={len(data['bai']['roads'])} tl={len(data['bai']['tl'])}")
    else:
        build(data)

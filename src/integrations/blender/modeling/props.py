import bpy
import json
import math
import mathutils
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.vector.vector_3 import Vector3
from src.core.geometry.main import transform_coordinate_system
from src.constants.constants import HUGE
from src.constants.folder import Folder

from src.integrations.blender.modeling.meshes import (
    read_bms,
    build_blender_mesh,
    _apply_materials_to_mesh,
)


# Anything above this threshold in all three components is the "undefined" sentinel
_HUGE_SENTINEL = HUGE * 0.5


# ── Prop metadata serialization ───────────────────────────────────────────────

def _serialize_prop_config(config: dict) -> str:
    """Serialize a prop config dict to a JSON string for storage on Blender objects.

    Handles AxisRef objects (separator values) which are not JSON-serializable.
    All other values (tuples of numbers, strings, lists) are serializable as-is.
    """
    serializable: dict = {}
    for k, v in config.items():
        if hasattr(v, "axis") and hasattr(v, "resolve"):  # AxisRef
            serializable[k] = {"__type__": "axis", "axis": v.axis, "offset": float(v.offset)}
        elif isinstance(v, tuple):
            # tuples → lists for JSON; works for (x,y,z) offsets and nested area tuples
            def _tuple_to_list(t: Any) -> Any:
                if isinstance(t, tuple):
                    return [_tuple_to_list(i) for i in t]
                return t
            serializable[k] = _tuple_to_list(v)
        elif isinstance(v, list):
            def _list_clean(lst: Any) -> Any:
                if isinstance(lst, (list, tuple)):
                    return [_list_clean(i) for i in lst]
                return lst
            serializable[k] = _list_clean(v)
        else:
            serializable[k] = v
    return json.dumps(serializable)


# ── Coordinate helpers ────────────────────────────────────────────────────────

def _to_blender_location(game_offset: tuple) -> Tuple[float, float, float]:
    return transform_coordinate_system(Vector3(*game_offset), game_to_blender=True)


def _to_blender_rotation_z(angle: Optional[float], face: Optional[tuple]) -> float:
    """
    Convert a game angle (degrees) or face vector to a Blender Z-axis rotation
    (radians).

    Game angle convention:
        0° → pointing +X (East).
        The face vector (cos θ, 0, sin θ) in game space maps to Blender
        direction (-cos θ, sin θ, 0).  Starting from the mesh's default
        -X orientation, rotating by -θ aligns it with that direction.

    The undefined sentinel (HUGE, HUGE, HUGE) is identified by its non-zero
    Y component — all real direction vectors have fy = 0.
    """
    if angle is not None:
        return -math.radians(angle)

    if face is not None:
        fx, fy, fz = face
        # The undefined sentinel is exactly (HUGE, HUGE, HUGE) — all three
        # components large and positive.  Random face vectors can have large Y,
        # so checking fy alone is unreliable; require all three.
        if fx > _HUGE_SENTINEL and fy > _HUGE_SENTINEL and fz > _HUGE_SENTINEL:
            return 0.0
        return math.atan2(-fz, fx)

    return 0.0


# ── Prop instance expansion ───────────────────────────────────────────────────

def _load_dimensions_cache() -> Dict[str, Vector3]:
    """Load the pre-computed prop dimensions used to resolve Axis-based separators."""
    dim_file = Folder.Resources.Editor.Props / "prop_dimensions.txt"
    if not dim_file.exists():
        return {}

    cache: Dict[str, Vector3] = {}
    with open(dim_file, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 4:
                prop_name, x, y, z = parts
                cache[prop_name] = Vector3(float(x), float(y), float(z))
    return cache


def _resolve_separator(sep, prop_name: str, dims_cache: Dict[str, Vector3]) -> float:
    """Resolve an Axis-based or numeric separator to a float distance."""
    if isinstance(sep, (int, float)):
        return float(sep)
    if hasattr(sep, "resolve"):
        return sep.resolve(dims_cache.get(prop_name, Vector3(1, 1, 1)))
    return 10.0


def expand_prop_instances(
    prop_list: list,
    random_props: list,
    dims_cache: Optional[Dict[str, Vector3]] = None,
) -> List[dict]:
    """
    Expand prop_list and random_props into a flat list of single-placement dicts.

    Mirrors BangerEditor.add_multiple() and BangerEditor.place_randomly() exactly
    so that Blender placement matches what the binary prop file contains.

    Each returned dict has:
        name           : str
        offset         : tuple (game coords)
        face           : tuple | None
        angle          : float | None
        mm_group_id    : str  (e.g. "fixed_0", "random_1")
        mm_group_type  : str  ("fixed" | "random")
        mm_config_json : str  (JSON-serialized original config dict)
    """
    if dims_cache is None:
        dims_cache = _load_dimensions_cache()

    instances: List[dict] = []

    # ── Fixed props ──────────────────────────────────────────────────────────
    for prop_idx, prop in enumerate(prop_list):
        name   = prop["name"]
        offset = Vector3(*prop["offset"])
        end    = Vector3(*prop["end"]) if "end" in prop else None
        angle  = prop.get("angle", None)
        face   = prop.get("face", None)

        group_id     = f"fixed_{prop_idx}"
        config_json  = _serialize_prop_config(prop)

        if face is None and angle is not None:
            rad = math.radians(angle)
            face = (HUGE * math.cos(rad), 0.0, HUGE * math.sin(rad))
        elif face is None:
            face = (HUGE, HUGE, HUGE)

        if end is not None:
            diagonal  = end - offset
            direction = diagonal.Normalize()
            sep       = _resolve_separator(prop.get("separator", 10.0), name, dims_cache)
            count     = int(diagonal.Mag() / sep)

            # When the user gave no explicit angle or face, align props along
            # the line of travel.  Without this, face stays as the (HUGE,HUGE,HUGE)
            # sentinel and _to_blender_rotation_z returns 0 (no rotation).
            if prop.get("face") is None and angle is None:
                face = (direction.x * HUGE, direction.y * HUGE, direction.z * HUGE)

            for i in range(count):
                pos = offset + direction * (i * sep)
                instances.append({
                    "name": name, "offset": pos.to_tuple(), "face": face, "angle": angle,
                    "mm_group_id": group_id, "mm_group_type": "fixed", "mm_config_json": config_json,
                })
        else:
            instances.append({
                "name": name, "offset": offset.to_tuple(), "face": face, "angle": angle,
                "mm_group_id": group_id, "mm_group_type": "fixed", "mm_config_json": config_json,
            })

    # ── Random props ─────────────────────────────────────────────────────────
    for rand_idx, config in enumerate(random_props):
        names = config.get("name", [])
        if isinstance(names, str):
            names = [names]
        count = config.get("count", None)
        if count is not None and len(names) == 1:
            names = names * count

        num_props = config.get("num_props", 1)
        seed = config["seed"]
        (x_min, y_min, z_min), (x_max, y_max, z_max) = config["area"]

        cfg_angle = config.get("angle", None)
        cfg_face  = config.get("face", None)

        group_id    = f"random_{rand_idx}"
        config_json = _serialize_prop_config(config)

        random.seed(seed)
        for name in names:
            for _ in range(num_props):
                x = random.uniform(x_min, x_max)
                z = random.uniform(z_min, z_max)
                y = y_min if y_min == y_max else random.uniform(y_min, y_max)

                if cfg_face is not None:
                    face = cfg_face
                elif cfg_angle is not None:
                    rad = math.radians(cfg_angle)
                    face = (HUGE * math.cos(rad), 0.0, HUGE * math.sin(rad))
                else:
                    face = (
                        random.uniform(-HUGE, HUGE),
                        random.uniform(-HUGE, HUGE),
                        random.uniform(-HUGE, HUGE),
                    )

                instances.append({
                    "name": name,
                    "offset": (x, y, z),
                    "face": face,
                    "angle": cfg_angle,
                    "mm_group_id": group_id,
                    "mm_group_type": "random",
                    "mm_config_json": config_json,
                })

    return instances


# ── BMS file resolver ─────────────────────────────────────────────────────────

def _resolve_bms_file(prop_name: str, bms_root: Path) -> Optional[Path]:
    """
    Locate the primary BMS file for a prop inside the BMS subfolder tree.

    Folder layout:   bms_root / <PROP_NAME_UPPER> / <filename>.BMS

    File selection rules:
        • All vehicles (vp* / va*) → BODY_H.BMS, fallback BODY_M.BMS, then H.BMS.
          BODY_H contains only the car body, giving clean per-panel textures.
          H.BMS is the combined full-LOD mesh (body + all four wheels); its wheel
          texture dominates visually, so it is used only as a last resort.
        • All other props → H.BMS

    Returns None when the folder does not exist or no matching BMS file is found.
    """
    prop_folder = bms_root / prop_name.upper()
    if not prop_folder.is_dir():
        return None

    if prop_name.lower().startswith(("va", "vp")):
        # Vehicle — prefer body-only mesh for clean texture visualization
        for filename in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS"):
            candidate = prop_folder / filename
            if candidate.exists():
                return candidate
        return None

    # Regular props
    h_bms = prop_folder / "H.BMS"
    return h_bms if h_bms.exists() else None


# ── Scene placement ───────────────────────────────────────────────────────────

def _bms_to_bl_offset(mesh: bpy.types.Mesh) -> Tuple[float, float, float]:
    """Convert a mesh's stored game-space mesh_offset to Blender-space XYZ."""
    ox, oy, oz = mesh.get("mesh_offset", [0.0, 0.0, 0.0])
    return (-ox, oz, oy)


def _load_bms_mesh(
    bms_file: Path,
    name: str,
    texture_folder: Optional[Path],
) -> Optional[bpy.types.Mesh]:
    """Read one BMS file, build the Blender mesh, and apply materials. Returns None on error."""
    try:
        bms_data = read_bms(bms_file)
        mesh = build_blender_mesh(name, bms_data)
        if texture_folder and bms_data["texture_names"]:
            _apply_materials_to_mesh(mesh, bms_data["texture_names"], texture_folder)
        return mesh
    except Exception as exc:
        print(f"  Could not load {bms_file.name}: {exc}")
        return None


def _load_vehicle_parts(
    prop_name: str,
    prop_folder: Path,
    texture_folder: Optional[Path],
    load_wheels: bool,
    load_lights: bool,
) -> dict:
    """
    Load every requested BMS component for a vehicle prop.

    Returns a dict:
        body   : bpy.types.Mesh | None
        wheels : List[bpy.types.Mesh]   (each carries mesh_offset for placement)
        extras : List[bpy.types.Mesh]   (fenders, etc.)
        lights : List[bpy.types.Mesh]
    """
    parts: dict = {"body": None, "wheels": [], "extras": [], "lights": []}

    # ── Body ─────────────────────────────────────────────────────────────────
    for candidate in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS"):
        f = prop_folder / candidate
        if f.exists():
            parts["body"] = _load_bms_mesh(f, prop_name, texture_folder)
            break

    # ── Wheels (WHL0_H .. WHL9_H) ────────────────────────────────────────────
    if load_wheels:
        for i in range(10):
            f = prop_folder / f"WHL{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms_mesh(f, f"{prop_name}.WHL{i}", texture_folder)
            if mesh is not None:
                parts["wheels"].append(mesh)

    # ── Fenders and other named sub-parts (FNDR0_H, FNDR1_H, ...) ────────────
    # Some vehicles (e.g. VPPANOZ/Roadster) have detachable fender meshes that
    # are separate from BODY_H.BMS and must be loaded alongside the body.
    for i in range(10):
        f = prop_folder / f"FNDR{i}_H.BMS"
        if not f.exists():
            break
        mesh = _load_bms_mesh(f, f"{prop_name}.FNDR{i}", texture_folder)
        if mesh is not None:
            parts["extras"].append(mesh)

    # ── Lights ───────────────────────────────────────────────────────────────
    if load_lights:
        for candidate in ("HLIGHT_H.BMS", "HLIGHT.BMS", "TLIGHT.BMS", "RLIGHT.BMS"):
            f = prop_folder / candidate
            if f.exists():
                mesh = _load_bms_mesh(f, f"{prop_name}.{f.stem}", texture_folder)
                if mesh is not None:
                    parts["lights"].append(mesh)

    return parts


def _place_vehicle_instance(
    prop_name: str,
    parts: dict,
    game_loc: Tuple[float, float, float],
    z_rot: float,
    collection: "bpy.types.Collection",
) -> "Optional[bpy.types.Object]":
    """Place a full vehicle (body + optional wheels / lights) in the scene.

    Returns the body object so callers can tag it with metadata, or None if
    the body mesh is missing.

    Wheels, fenders, and other sub-parts are parented to the body with their
    BMS mesh_offset as the LOCAL position.  matrix_parent_inverse is reset to
    identity after each parent assignment so child.location is pure local space.
    """
    body_mesh = parts["body"]
    if body_mesh is None:
        return None

    # Body — placed at world position
    body_obj = bpy.data.objects.new(prop_name, body_mesh)
    collection.objects.link(body_obj)
    bl_body_off = _bms_to_bl_offset(body_mesh)
    body_obj.location = (
        game_loc[0] + bl_body_off[0],
        game_loc[1] + bl_body_off[1],
        game_loc[2] + bl_body_off[2],
    )
    body_obj.rotation_euler = (0.0, 0.0, z_rot)

    def _add_child(mesh: bpy.types.Mesh) -> None:
        child = bpy.data.objects.new(mesh.name, mesh)
        collection.objects.link(child)
        child.parent = body_obj
        # Reset the parent-inverse matrix so child.location is pure local space
        # (relative to the body origin), not compensated to keep world position.
        child.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        child.location = _bms_to_bl_offset(mesh)

    for whl_mesh in parts["wheels"]:
        _add_child(whl_mesh)
    for extra_mesh in parts["extras"]:
        _add_child(extra_mesh)
    for light_mesh in parts["lights"]:
        _add_child(light_mesh)

    return body_obj


_PROPS_COLLECTION = "Props"


def _get_or_create_collection(name: str) -> "bpy.types.Collection":
    """Return the named collection, creating it and linking to the scene if needed."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _clear_collection(col: "bpy.types.Collection") -> None:
    """Remove all objects (and their mesh data) from a collection."""
    for obj in list(col.objects):
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def place_props_in_scene(
    prop_list: list,
    random_props: list,
    bms_folder: Path,
    texture_folder: Optional[Path] = None,
    car_wheels: bool = True,
    car_lights: bool = False,
) -> None:
    """
    Build prop meshes from BMS files and place instances directly in the scene.

    All objects are placed into the "MM1_Props" collection which is cleared
    at the start of every run, preventing duplicates on re-runs.

    For regular props (TP*) a single H.BMS mesh is placed per instance.
    For vehicle props (VP* / VA*) the body mesh is placed together with
    optional wheels and lights — all parented to the body object.

    Args:
        prop_list      : Fixed prop list from USER/props/props.py.
        random_props   : Random prop configs from USER/props/props.py.
        bms_folder     : Root folder containing per-prop BMS subfolders.
        texture_folder : Folder containing .DDS textures (optional).
        car_wheels     : Load WHL0–N_H.BMS and parent to body.
        car_lights     : Load HLIGHT/TLIGHT/RLIGHT meshes and parent to body.
    """
    # Clear previous run's objects so re-running never doubles up props
    props_col = _get_or_create_collection(_PROPS_COLLECTION)
    _clear_collection(props_col)

    dims_cache = _load_dimensions_cache()
    instances = expand_prop_instances(prop_list, random_props, dims_cache)

    if not instances:
        return

    unique_names = list(dict.fromkeys(inst["name"] for inst in instances))

    # mesh_cache : prop_name → Mesh (regular props)
    # veh_cache  : prop_name → parts dict (vehicle props)
    mesh_cache: Dict[str, Optional[bpy.types.Mesh]] = {}
    veh_cache:  Dict[str, Optional[dict]]            = {}

    print("Building prop meshes...")
    for prop_name in unique_names:
        prop_folder = bms_folder / prop_name.upper()
        is_vehicle  = prop_name.lower().startswith(("va", "vp"))

        if is_vehicle:
            if not prop_folder.is_dir():
                print(f"  No BMS folder for '{prop_name}', skipping")
                veh_cache[prop_name] = None
                continue
            parts = _load_vehicle_parts(
                prop_name, prop_folder, texture_folder,
                load_wheels=car_wheels,
                load_lights=car_lights,
            )
            if parts["body"] is None:
                print(f"  No body BMS for '{prop_name}', skipping")
                veh_cache[prop_name] = None
            else:
                whl_count   = len(parts["wheels"])
                extra_count = len(parts["extras"])
                extra_str   = f" + {extra_count} extras" if extra_count else ""
                print(f"  {prop_name}: body + {whl_count} wheels{extra_str}")
                veh_cache[prop_name] = parts
        else:
            bms_file = _resolve_bms_file(prop_name, bms_folder)
            if bms_file is None:
                print(f"  No BMS found for '{prop_name}', skipping")
                mesh_cache[prop_name] = None
                continue
            bms_data = read_bms(bms_file)
            mesh = build_blender_mesh(prop_name, bms_data)
            if texture_folder and bms_data["texture_names"]:
                _apply_materials_to_mesh(mesh, bms_data["texture_names"], texture_folder)
            mesh_cache[prop_name] = mesh
            print(f"  {prop_name}: {bms_data['num_surfaces']} faces, "
                  f"{len(bms_data['texture_names'])} textures")

    # ── Place every instance ──────────────────────────────────────────────────
    placed = 0
    skipped = 0

    for inst in instances:
        prop_name  = inst["name"]
        game_loc   = _to_blender_location(inst["offset"])
        z_rot      = _to_blender_rotation_z(inst.get("angle"), inst.get("face"))
        is_vehicle = prop_name.lower().startswith(("va", "vp"))

        # Metadata for the Prop Editor panel
        group_id    = inst.get("mm_group_id", "")
        group_type  = inst.get("mm_group_type", "fixed")
        config_json = inst.get("mm_config_json", "{}")

        if is_vehicle:
            parts = veh_cache.get(prop_name)
            if parts is None:
                skipped += 1
                continue
            body_obj = _place_vehicle_instance(prop_name, parts, game_loc, z_rot, props_col)
            if body_obj is not None:
                body_obj["mm_prop_group_id"]    = group_id
                body_obj["mm_prop_type"]         = group_type
                body_obj["mm_prop_config_json"]  = config_json
            placed += 1
        else:
            mesh = mesh_cache.get(prop_name)
            if mesh is None:
                skipped += 1
                continue
            obj = bpy.data.objects.new(prop_name, mesh)
            props_col.objects.link(obj)
            bl_off = _bms_to_bl_offset(mesh)
            obj.location = (
                game_loc[0] + bl_off[0],
                game_loc[1] + bl_off[1],
                game_loc[2] + bl_off[2],
            )
            obj.rotation_euler = (0.0, 0.0, z_rot)
            # Tag with Prop Editor metadata
            obj["mm_prop_group_id"]   = group_id
            obj["mm_prop_type"]       = group_type
            obj["mm_prop_config_json"] = config_json
            placed += 1

    print(f"Props placed in scene: {placed} (skipped: {skipped})")


_TRAFFIC_LIGHTS_COLLECTION = "Traffic Lights"

# Persistent mesh cache — built once per Blender session, reused on every refresh
_tl_mesh_cache: Dict[str, Optional[bpy.types.Mesh]] = {}


def _get_tl_mesh(
    prop_name: str,
    bms_folder: Path,
    texture_folder: Optional[Path],
) -> Optional[bpy.types.Mesh]:
    """Return a cached BMS mesh for a traffic-light prop, loading it on first use."""
    if prop_name not in _tl_mesh_cache:
        bms_file = _resolve_bms_file(prop_name, bms_folder)
        if bms_file is None:
            print(f"  Traffic light: no BMS for '{prop_name}', skipping")
            _tl_mesh_cache[prop_name] = None
        else:
            _tl_mesh_cache[prop_name] = _load_bms_mesh(bms_file, prop_name, texture_folder)
    return _tl_mesh_cache[prop_name]


def _place_tl_object(
    tl_key: str,
    prop_name: str,
    light: dict,
    bms_folder: Path,
    texture_folder: Optional[Path],
    col: "bpy.types.Collection",
) -> bool:
    mesh = _get_tl_mesh(prop_name, bms_folder, texture_folder)
    if mesh is None:
        return False
    bl_loc = _to_blender_location(light["offset"])
    z_rot  = _to_blender_rotation_z(None, light["face"])
    bl_off = _bms_to_bl_offset(mesh)
    obj = bpy.data.objects.new(f"TL_{tl_key}", mesh)
    col.objects.link(obj)
    obj.location = (bl_loc[0] + bl_off[0], bl_loc[1] + bl_off[1], bl_loc[2] + bl_off[2])
    obj.rotation_euler = (0.0, 0.0, z_rot)
    return True


def place_traffic_lights_in_scene(
    lights: List[dict],
    bms_folder: Path,
    texture_folder: Optional[Path] = None,
) -> int:
    """
    Spawn all traffic light props into the "Traffic Lights" collection.

    Each entry in `lights` must have:
        name   : str   — prop name (e.g. Prop.TRAFFIC_LIGHT_SINGLE)
        offset : tuple — game-space (x, y, z) position
        face   : tuple — game-space direction vector (dx, dy, dz); may be (0,0,0)
        tl_key : str   — unique key used to name the object as TL_{tl_key}

    The collection is cleared on every call to avoid duplicates on re-load.
    Returns the number of objects placed.
    """
    col = _get_or_create_collection(_TRAFFIC_LIGHTS_COLLECTION)
    _clear_collection(col)

    placed = 0
    for light in lights:
        prop_name = light["name"]
        tl_key    = light.get("tl_key", prop_name)
        if _place_tl_object(tl_key, prop_name, light, bms_folder, texture_folder, col):
            placed += 1
    return placed


def refresh_one_street_traffic_lights(
    street_name: str,
    lights: List[dict],
    bms_folder: Path,
    texture_folder: Optional[Path] = None,
) -> None:
    """
    Remove and re-place traffic light objects for a single street.

    Objects are identified by the naming prefix `TL_{street_name}_`.
    Only those objects are touched; the rest of the "Traffic Lights"
    collection is left unchanged.
    """
    col    = _get_or_create_collection(_TRAFFIC_LIGHTS_COLLECTION)
    prefix = f"TL_{street_name}_"
    for obj in list(col.objects):
        if obj.name.startswith(prefix):
            bpy.data.objects.remove(obj, do_unlink=True)

    for light in lights:
        prop_name = light["name"]
        tl_key    = light.get("tl_key", prop_name)
        _place_tl_object(tl_key, prop_name, light, bms_folder, texture_folder, col)


_BULK_BMS_COLLECTION = "City BMS"


def place_bulk_bms_in_scene(
    bms_folders: List[Path],
    texture_folder: Optional[Path] = None,
) -> None:
    """
    Bulk-import every *_H.BMS file found directly inside each folder in
    bms_folders and place the resulting meshes into the "MM1_City" collection.

    City BMS files (e.g. CULL1000_H.BMS) store their world position via the
    mesh_offset field in the BMS header, so each mesh is placed at that offset
    with no additional transform.  Non-H BMS variants (_M, _L, _VL) are skipped.

    The collection is cleared at the start of every run to prevent duplicates.

    Args:
        bms_folders    : List of flat folders, each containing *_H.BMS files.
        texture_folder : Folder containing .DDS textures (optional).
    """
    city_col = _get_or_create_collection(_BULK_BMS_COLLECTION)
    _clear_collection(city_col)

    total_loaded = 0
    total_skipped = 0

    for folder in bms_folders:
        folder = Path(folder)
        if not folder.is_dir():
            print(f"  Bulk BMS folder not found, skipping: {folder}")
            continue

        h_files = sorted(folder.glob("*_H.BMS"))
        print(f"  Bulk loading {len(h_files)} H.BMS files from {folder.name}...")

        for bms_file in h_files:
            name = bms_file.stem  # e.g. "CULL1000_H"
            try:
                bms_data = read_bms(bms_file)
                mesh = build_blender_mesh(name, bms_data)
                if texture_folder and bms_data["texture_names"]:
                    _apply_materials_to_mesh(mesh, bms_data["texture_names"], texture_folder)

                obj = bpy.data.objects.new(name, mesh)
                city_col.objects.link(obj)

                # City blocks encode their world position in mesh_offset
                obj.location = _bms_to_bl_offset(mesh)

                total_loaded += 1
            except Exception as exc:
                print(f"    Could not load {bms_file.name}: {exc}")
                total_skipped += 1

    print(f"Bulk BMS: {total_loaded} meshes placed, {total_skipped} skipped")

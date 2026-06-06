"""Dash Editor — assembly, scene sync, preview and config round-trip helpers."""
import bpy
import math
import mathutils
from pathlib import Path
from typing import List, Optional

from src.constants.folder import Folder
from src.integrations.blender.modeling import tune_blocks as tb
from src.integrations.blender.modeling.meshes import _to_blender_pos
from src.integrations.blender.modeling.bms_writer import _from_blender_pos
from src.integrations.blender.operators.car_editor.common import _tex_folder, _bms_to_bl_offset

from src.integrations.blender.operators.dash_editor.meshio import load_part_mesh
from src.integrations.blender.operators.dash_editor.camera import build_pov_camera
from src.integrations.blender.operators.dash_editor.constants import (
    DASH_PARTS, DASH_PLACEMENT_FIELD, NEEDLE_ROT_FIELD, NEEDLE_ROT_PROP,
    SCALAR_FIELD_PROP, NEEDLE_TAGS, DEFAULT_TEMPLATE_CAR, _DASH_TAG, _ROOT_TAG, _DASH_COLLECTION,
)

_DEV_TUNE  = Folder.BASE / "development" / "core" / "TUNE"
_PART_FILE = dict(DASH_PARTS)


# ── Scene queries ─────────────────────────────────────────────────────────────

def is_dash_obj(obj) -> bool:
    return obj is not None and obj.get(_DASH_TAG) is not None


def get_dash_objects() -> List[bpy.types.Object]:
    return [o for o in bpy.data.objects if is_dash_obj(o)]


def get_dash_root() -> Optional[bpy.types.Object]:
    for o in get_dash_objects():
        if o.get(_DASH_TAG) == _ROOT_TAG:
            return o
    return None


def get_dash_part(tag: str) -> Optional[bpy.types.Object]:
    for o in get_dash_objects():
        if o.get(_DASH_TAG) == tag:
            return o
    return None


def clear_dash() -> None:
    for obj in get_dash_objects():
        bpy.data.objects.remove(obj, do_unlink=True)


def _get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


# ── Source resolution ─────────────────────────────────────────────────────────

def list_dash_cars() -> List[str]:
    """Car names that have a ``{CAR}_DASH/DASH.BMS`` under the editor mesh folders."""
    names = set()
    for base in (Folder.Resources.Editor.MeshesCars, Folder.Resources.Editor.Meshes / "CAR_DASH"):
        if base.is_dir():
            for d in base.iterdir():
                if d.is_dir() and d.name.upper().endswith("_DASH") and (d / "DASH.BMS").is_file():
                    names.add(d.name[:-5])  # strip "_DASH"
    return sorted(names)


def resolve_dash_dir(car: str) -> Optional[Path]:
    for cand in (
        Folder.Resources.Editor.MeshesCars / f"{car}_DASH",
        Folder.Resources.Editor.Meshes / "CAR_DASH" / f"{car}_DASH",
        Folder.Shop.Meshes / f"{car}_DASH",
        Folder.Resources.Editor.MeshesCars / f"{DEFAULT_TEMPLATE_CAR}_DASH",
    ):
        if cand.is_dir() and (cand / "DASH.BMS").is_file():
            return cand
    return None


def _resolve_tune(filename: str, template_filename: str) -> Optional[Path]:
    for cand in (Folder.Shop.Tune / filename, _DEV_TUNE / filename, _DEV_TUNE / template_filename):
        if cand.is_file():
            return cand
    return None


def resolve_mmdashview(car: str) -> Optional[Path]:
    return _resolve_tune(f"{car}.MMDASHVIEW", f"{DEFAULT_TEMPLATE_CAR}.MMDASHVIEW")


def resolve_povcamcs(car: str) -> Optional[Path]:
    return _resolve_tune(f"{car}_DASH.POVCAMCS", f"{DEFAULT_TEMPLATE_CAR}_DASH.POVCAMCS")


# ── Load / assemble ───────────────────────────────────────────────────────────

def _vec(block: dict, key: str, default=(0.0, 0.0, 0.0)) -> tuple:
    v = block.get(key)
    return tuple(v) if v and len(v) >= 3 else tuple(default)


def _scalar(block: dict, key: str, default: float = 0.0) -> float:
    v = block.get(key)
    return float(v[0]) if v else default


def load_dash(scene, car: str) -> tuple:
    """Build the full dash assembly for `car`. Returns (root_obj, message)."""
    dash_dir = resolve_dash_dir(car)
    if dash_dir is None:
        return None, f"No dash meshes found for {car}"

    mmview_path = resolve_mmdashview(car)
    mmview_text = tb.read_file(mmview_path) if mmview_path else ""
    block = tb.parse_block(mmview_text) if mmview_text else {}

    pov_path = resolve_povcamcs(car)
    pov_text = tb.read_file(pov_path) if pov_path else ""
    pov_block = tb.parse_block(pov_text) if pov_text else {}

    clear_dash()
    col = _get_or_create_collection(_DASH_COLLECTION)
    tex_folder = _tex_folder(scene)

    # ── DashLCS root empty ────────────────────────────────────────────────────
    root = bpy.data.objects.new(f"{car}_DASH", None)
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 0.3
    col.objects.link(root)
    root.location = _to_blender_pos(_vec(block, "DashPos"))
    root[_DASH_TAG] = _ROOT_TAG
    root["mm_car_name"]   = car
    root["mm_car_folder"] = str(dash_dir)
    root["mmview_text"]   = mmview_text
    root["pov_text"]      = pov_text

    # ── Parts ─────────────────────────────────────────────────────────────────
    loaded = 0
    for tag, filename in DASH_PARTS:
        bms_file = dash_dir / filename
        if not bms_file.is_file():
            continue
        mesh = load_part_mesh(bms_file, f"{car}_{tag}", tex_folder)
        if mesh is None:
            continue

        obj = bpy.data.objects.new(f"{car}_{tag}", mesh)
        col.objects.link(obj)
        obj.parent = root
        obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        obj[_DASH_TAG] = tag

        field = DASH_PLACEMENT_FIELD.get(tag)
        if field is not None:
            obj.location = _to_blender_pos(_vec(block, field))
        else:
            obj.location = _bms_to_bl_offset(mesh)   # dash + gear: geometry carries position

        if tag in NEEDLE_ROT_FIELD:
            min_field, _ = NEEDLE_ROT_FIELD[tag]
            obj.rotation_euler = (0.0, _scalar(block, min_field), 0.0)

        loaded += 1

    # ── Scene props from the config ───────────────────────────────────────────
    scene.de_updating = True
    for field, prop in SCALAR_FIELD_PROP.items():
        if field in block:
            setattr(scene, prop, _scalar(block, field))
    for tag, (min_field, max_field) in NEEDLE_ROT_FIELD.items():
        min_prop, max_prop = NEEDLE_ROT_PROP[tag]
        setattr(scene, min_prop, _scalar(block, min_field))
        setattr(scene, max_prop, _scalar(block, max_field))
    if "m_Offset" in pov_block:
        scene.de_cam_offset = _vec(pov_block, "m_Offset", (0.0, 1.2, 0.3))
    if "m_cameraFOV" in pov_block:
        scene.de_cam_fov = _scalar(pov_block, "m_cameraFOV", 60.0)
    if "m_Pitch" in pov_block:
        scene.de_cam_pitch = _scalar(pov_block, "m_Pitch", 0.0)
    if "m_cameraNear" in pov_block:
        scene.de_cam_near = _scalar(pov_block, "m_cameraNear", 0.1)
    if "m_cameraFar" in pov_block:
        scene.de_cam_far = _scalar(pov_block, "m_cameraFar", 1600.0)
    scene.de_preview = 0.0
    scene.de_updating = False

    # ── POV camera ────────────────────────────────────────────────────────────
    # Flush transforms so root.matrix_world is current before the camera frames it.
    bpy.context.view_layer.update()
    if pov_block:
        build_pov_camera(root, pov_block, col)

    apply_preview(scene)
    return root, f"Loaded {car} dash: {loaded} parts from {dash_dir.name}"


# ── Gauge preview ─────────────────────────────────────────────────────────────

def apply_preview(scene) -> None:
    """Rotate the needles (and spin the wheel) to visualise the gauge sweep.

    frac 0 → each needle sits at its RotMin (rest); frac 1 → RotMax (full scale).
    The wheel turns a quarter-turn each way scaled by WheelFact so steering reads.
    """
    frac = scene.de_preview
    for tag in NEEDLE_TAGS:
        obj = get_dash_part(tag)
        if obj is None:
            continue
        min_prop, max_prop = NEEDLE_ROT_PROP[tag]
        rot_min = getattr(scene, min_prop)
        rot_max = getattr(scene, max_prop)
        obj.rotation_euler = (0.0, rot_min + (rot_max - rot_min) * frac, 0.0)

    wheel = get_dash_part("wheel")
    if wheel is not None:
        steer = (frac * 2.0 - 1.0)   # map 0..1 → -1..1
        wheel.rotation_euler = (0.0, -steer * scene.de_wheel_fact * (math.pi / 2.0), 0.0)


def update_de_preview(self, context) -> None:
    if getattr(self, "de_updating", False):
        return
    apply_preview(self)


def update_de_gauge(self, context) -> None:
    """Re-apply the preview when any gauge rotation / wheel-fact prop changes."""
    if getattr(self, "de_updating", False):
        return
    apply_preview(self)


# ── Config write-back (export) ────────────────────────────────────────────────

def build_mmdashview_text(scene, root) -> str:
    """Patch the loaded MMDASHVIEW text with the current scene/object state."""
    text = root.get("mmview_text", "")
    if not text:
        return text

    text = tb.set_values(text, "DashPos", _from_blender_pos(root.location))

    for tag, field in DASH_PLACEMENT_FIELD.items():
        obj = get_dash_part(tag)
        if obj is not None:
            text = tb.set_values(text, field, _from_blender_pos(obj.location))

    for tag, (min_field, max_field) in NEEDLE_ROT_FIELD.items():
        min_prop, max_prop = NEEDLE_ROT_PROP[tag]
        text = tb.set_values(text, min_field, [getattr(scene, min_prop)])
        text = tb.set_values(text, max_field, [getattr(scene, max_prop)])

    for field, prop in SCALAR_FIELD_PROP.items():
        text = tb.set_values(text, field, [getattr(scene, prop)])

    return text


def build_povcamcs_text(scene, root) -> str:
    """Patch the loaded POVCAMCS text with the current camera scene props."""
    text = root.get("pov_text", "")
    if not text:
        return text

    text = tb.set_values(text, "m_Offset", list(scene.de_cam_offset))
    text = tb.set_values(text, "m_cameraFOV", [scene.de_cam_fov])
    text = tb.set_values(text, "m_Pitch", [scene.de_cam_pitch])
    text = tb.set_values(text, "m_cameraNear", [scene.de_cam_near])
    text = tb.set_values(text, "m_cameraFar", [scene.de_cam_far])
    return text


# ── Part swap + texture reskin ────────────────────────────────────────────────

def _part_tex_names(obj) -> List[str]:
    return [m.name for m in obj.data.materials if m is not None]


def _find_dds(folder: Path, name: str) -> Optional[Path]:
    for ext in (".dds", ".DDS"):
        cand = folder / f"{name}{ext}"
        if cand.is_file():
            return cand
    return None


def get_tex_overrides(root) -> dict:
    return dict(root.get("tex_overrides", {})) if root else {}


def _merge_tex_overrides(root, mapping: dict) -> None:
    current = dict(root.get("tex_overrides", {}))
    current.update(mapping)
    root["tex_overrides"] = current


def _set_material_image(mat, image_path: str) -> None:
    if mat is None or not mat.use_nodes:
        return
    img = bpy.data.images.load(image_path, check_existing=True)
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            node.image = img
            return


def swap_part(scene, obj, source_car: str) -> tuple:
    """Replace a dash part's mesh with the same part from `source_car`.

    The swapped-in mesh keeps the current car's texture NAMES (remapped by slot, so
    the car's own TSH still resolves them), and the source car's textures are recorded
    as overrides so they pack into the AR under those names — the part keeps its look.
    """
    tag = obj.get(_DASH_TAG)
    if tag not in _PART_FILE:
        return False, "Not a swappable dash part."

    src_dir = resolve_dash_dir(source_car)
    if src_dir is None:
        return False, f"No dash meshes for {source_car}."

    bms_file = src_dir / _PART_FILE[tag]
    if not bms_file.is_file():
        return False, f"{source_car} has no {_PART_FILE[tag]}."

    local_names = _part_tex_names(obj)
    tex_folder  = _tex_folder(scene)
    new_mesh    = load_part_mesh(bms_file, f"{obj.name}_swap", tex_folder)
    if new_mesh is None:
        return False, "Failed to load the swap mesh."

    foreign_names = list(new_mesh.get("texture_names", []))
    old_mesh = obj.data
    obj.data = new_mesh

    remap, overrides = {}, {}
    for i, fname in enumerate(foreign_names):
        if i < len(local_names):
            remap[fname.upper()] = local_names[i]
            dds = _find_dds(tex_folder, fname)
            if dds is not None:
                overrides[local_names[i]] = str(dds)
    obj["tex_remap"] = remap

    root = get_dash_root()
    if root is not None and overrides:
        _merge_tex_overrides(root, overrides)

    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

    return True, f"Swapped {tag} from {source_car}."


def reskin_part(scene, obj, image_path: str) -> tuple:
    """Point the active texture slot of `obj` at a custom DDS (packed on export)."""
    mats = obj.data.materials
    if not mats or all(m is None for m in mats):
        return False, "Part has no texture slot to reskin."

    idx = min(obj.active_material_index, len(mats) - 1)
    mat = mats[idx]
    if mat is None:
        return False, "Active material slot is empty."

    root = get_dash_root()
    if root is not None:
        _merge_tex_overrides(root, {mat.name: image_path})

    _set_material_image(mat, image_path)
    return True, f"Reskinned texture '{mat.name}'."


# ── Dash texture catalogue (the reskin dropdown) ──────────────────────────────

_GEAR_TEX     = {"G_1", "G_2", "G_3", "G_4", "G_5", "G_6", "G_7", "G_8", "G_N", "G_R", "G_P", "G_D"}
_TEX_PATTERNS = ("DASH", "NEEDLE", "STRWHEEL")
_TEX_PART_LABEL = {
    "DASHL": "Dash Left", "DASHM": "Dash Middle", "DASHR": "Dash Right", "DASHWHL": "Dash Wheel",
    "STRWHEEL": "Steering Wheel", "SNEEDLE": "Needle", "NEEDLE": "Needle", "DASNEEDLE": "Needle",
}


def list_dash_textures() -> List[str]:
    """Every dash-related .DDS stem in the editor texture pool (all cars)."""
    names = set()
    base = Folder.Resources.Editor.Textures
    if base.is_dir():
        for f in base.iterdir():
            if f.suffix.lower() != ".dds":
                continue
            up = f.stem.upper()
            if up in _GEAR_TEX or any(p in up for p in _TEX_PATTERNS):
                names.add(f.stem)
    return sorted(names)


def dash_texture_label(stem: str) -> str:
    """Friendly label for the reskin dropdown, e.g. 'VPMUSTANG99 · Dash Middle'."""
    if stem.upper() in _GEAR_TEX:
        return f"Gear: {stem.split('_')[-1]}"
    if "_" in stem:
        prefix, part = stem.rsplit("_", 1)
        return f"{prefix} · {_TEX_PART_LABEL.get(part.upper(), part)}"
    return stem


def apply_texture_name(scene, obj, tex_name: str) -> tuple:
    """Resolve a catalogue texture name to its DDS and reskin the active slot with it."""
    dds = _find_dds(_tex_folder(scene), tex_name)
    if dds is None:
        return False, f"Texture '{tex_name}' not found in the texture folder."
    return reskin_part(scene, obj, str(dds))


def update_de_reskin_texture(self, context) -> None:
    """Apply the chosen catalogue texture to the active dash part's active slot."""
    if getattr(self, "de_updating", False):
        return

    obj = context.active_object
    if obj is None or obj.get(_DASH_TAG) in (None, _ROOT_TAG, "pov_camera"):
        return

    name = self.de_reskin_texture
    if name:
        apply_texture_name(self, obj, name)

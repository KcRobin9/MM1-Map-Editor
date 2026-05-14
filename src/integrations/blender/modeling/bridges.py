"""
Place drawbridge / crossgate props into the Blender scene from parsed GIZMO
data. Each GizmoBlock becomes a "bridge group" holding 1-6 entry objects in
the "Bridges" collection. Every entry is rendered using the same BMS-loading
pipeline as regular props (props.py) so the visual stays consistent.

The Z-rotation comes from `(face - offset)` interpreted as a game-space
direction vector — the GIZMO format stores the face as a world point, not a
HUGE-scaled sentinel like the BNG format does, so we subtract here.
"""
import bpy
import json
import math
import mathutils
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from src.file_formats.gizmo.gizmo import GizmoBlock, GizmoEntry

from src.integrations.blender.modeling.props import (
    _to_blender_location,
    _to_blender_rotation_z,
    _bms_to_bl_offset,
    _resolve_bms_file,
)
from src.integrations.blender.modeling.meshes import (
    read_bms,
    build_blender_mesh,
    _apply_materials_to_mesh,
)
from src.ui.console import ok, sep, item, suppress_stdout_matching


_BRIDGES_COLLECTION = "Bridges"

# Custom-property tags applied to every bridge-entry object in the scene.
TAG_GROUP_ID    = "mm_bridge_group_id"     # e.g. "bridge_3"
TAG_ENTRY_IDX   = "mm_bridge_entry_index"  # int — position within the block
TAG_ROLE        = "mm_bridge_role"         # "drawbridge" | "attribute"
TAG_NAME        = "mm_bridge_name"         # raw prop game-id (e.g. tpdrawbridge06)
TAG_CONFIG_JSON = "mm_bridge_config_json"  # serialized entry dict


# ── Collection helpers ────────────────────────────────────────────────────────

def _get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _clear_collection(col: bpy.types.Collection) -> None:
    for obj in list(col.objects):
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def get_bridges_collection() -> Optional[bpy.types.Collection]:
    return bpy.data.collections.get(_BRIDGES_COLLECTION)


def get_bridge_objects() -> List[bpy.types.Object]:
    col = get_bridges_collection()
    return list(col.objects) if col else []


def is_bridge_obj(obj) -> bool:
    return obj is not None and TAG_GROUP_ID in obj


# ── Mesh cache (one BMS per prop type, reused across entries) ─────────────────

_MESH_CACHE: Dict[str, Optional[bpy.types.Mesh]] = {}


def _bridge_mesh(prop_name: str, bms_folder: Path,
                 texture_folder: Optional[Path]) -> Optional[bpy.types.Mesh]:
    key = prop_name.lower()
    if key in _MESH_CACHE:
        cached = _MESH_CACHE[key]
        if cached is not None and cached.name in bpy.data.meshes:
            return cached
    bms_file = _resolve_bms_file(prop_name, bms_folder)
    if bms_file is None:
        _MESH_CACHE[key] = None
        return None
    try:
        bms_data = read_bms(bms_file)
        mesh = build_blender_mesh(prop_name, bms_data)
        if texture_folder and bms_data.get("texture_names"):
            with suppress_stdout_matching("Unable to find a suitable DXT compression"):
                _apply_materials_to_mesh(mesh, bms_data["texture_names"], texture_folder)
    except Exception as exc:
        item(f"Could not load BMS for '{prop_name}': {exc}")
        _MESH_CACHE[key] = None
        return None
    _MESH_CACHE[key] = mesh
    return mesh


# ── Orientation ───────────────────────────────────────────────────────────────

def face_direction(offset: Tuple[float, float, float],
                   face:   Tuple[float, float, float]) -> Tuple[float, float, float]:
    """GIZMO face is a world point, not a direction — subtract offset to get one."""
    return (face[0] - offset[0], face[1] - offset[1], face[2] - offset[2])


def direction_to_z_rot(offset: Tuple[float, float, float],
                       face:   Tuple[float, float, float]) -> float:
    return _to_blender_rotation_z(None, face_direction(offset, face))


# ── Code-friendly conversions ─────────────────────────────────────────────────

def direction_to_angle_deg(offset: Tuple[float, float, float],
                           face:   Tuple[float, float, float]) -> float:
    """Convert (offset, face) → user-facing rotation in degrees (0=East, +Z = +90).

    Matches the convention in `src.game.bridges.main.calculate_facing`:
        face = offset + 10*(cos θ, 0, sin θ)
    so θ = atan2(dz, dx).
    """
    dx = face[0] - offset[0]
    dz = face[2] - offset[2]
    if abs(dx) < 1e-9 and abs(dz) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(dz, dx))


def angle_deg_to_face(offset: Tuple[float, float, float],
                      angle_deg: float,
                      distance: float = 10.0) -> Tuple[float, float, float]:
    """Inverse of `direction_to_angle_deg` — build a face world-point from an angle."""
    rad = math.radians(angle_deg)
    return (
        offset[0] + distance * math.cos(rad),
        offset[1],
        offset[2] + distance * math.sin(rad),
    )


# ── Placement ─────────────────────────────────────────────────────────────────

def _entry_to_config_dict(entry: GizmoEntry) -> dict:
    return {
        "name":   entry.name,
        "flags":  entry.flags,
        "offset": list(entry.offset),
        "face":   list(entry.face),
    }


def _apply_pivot_rotation(obj: bpy.types.Object,
                          hinge_blender: Tuple[float, float, float],
                          axis_blender: Tuple[float, float, float],
                          angle_rad: float) -> None:
    """Rotate `obj` about `hinge_blender` around `axis_blender` by `angle_rad`.

    Decomposes explicitly into a new location + new rotation_euler so we never
    read `obj.matrix_world` (which is stale immediately after assigning
    `obj.location` until the depsgraph updates).
    """
    axis = mathutils.Vector(axis_blender)
    if axis.length < 1e-9:
        return
    axis.normalize()
    hinge = mathutils.Vector(hinge_blender)

    R3 = mathutils.Matrix.Rotation(angle_rad, 3, axis)
    R_quat = mathutils.Quaternion(axis, angle_rad)

    # New location: rotate (current_loc - hinge) around hinge
    old_loc = mathutils.Vector(obj.location)
    obj.location = hinge + R3 @ (old_loc - hinge)

    # New rotation: compose R onto the existing Z rotation
    old_quat = obj.rotation_euler.to_quaternion()
    new_quat = R_quat @ old_quat
    obj.rotation_euler = new_quat.to_euler('XYZ')


def _open_bridges_settings() -> Tuple[bool, float]:
    """Read `open_bridges` + `open_bridges_angle` from USER/settings/blender.py.
    Tolerates missing attributes so older settings files still work."""
    try:
        from src.USER.settings.blender import open_bridges as _enabled
    except ImportError:
        _enabled = False
    try:
        from src.USER.settings.blender import open_bridges_angle as _angle
    except ImportError:
        _angle = 60.0
    return bool(_enabled), float(_angle)


def _place_one_entry(
    bridge_id: int,
    entry_idx: int,
    entry: GizmoEntry,
    bms_folder: Path,
    texture_folder: Optional[Path],
    col: bpy.types.Collection,
    open_angle_rad: float = 0.0,
) -> Optional[bpy.types.Object]:
    mesh = _bridge_mesh(entry.name, bms_folder, texture_folder)
    if mesh is None:
        return None

    z_rot = direction_to_z_rot(entry.offset, entry.face)
    game_loc = _to_blender_location(entry.offset)
    bl_off = _bms_to_bl_offset(mesh, z_rot)

    role = "drawbridge" if entry.is_drawbridge() else "attribute"
    obj_name = f"bridge_{bridge_id}_{entry_idx:02d}_{entry.name}"
    obj = bpy.data.objects.new(obj_name, mesh)
    col.objects.link(obj)
    obj.location = (
        game_loc[0] + bl_off[0],
        game_loc[1] + bl_off[1],
        game_loc[2] + bl_off[2],
    )
    obj.rotation_euler = (0.0, 0.0, z_rot)

    # ── Visual "raised drawbridge" effect ─────────────────────────────────────
    # Tilt each drawbridge half up around its outer hinge (the GIZMO offset
    # point). The face vector — converted to Blender coords — is the hinge
    # axis (perpendicular to the bridge's long axis), so a positive angle
    # lifts the inner end for both halves of any oriented pair.
    if role == "drawbridge" and abs(open_angle_rad) > 1e-6:
        fd_game = (entry.face[0] - entry.offset[0],
                   entry.face[1] - entry.offset[1],
                   entry.face[2] - entry.offset[2])
        # Game (x, y, z) → Blender (x, -z, y) — direction-wise
        axis_blender = (fd_game[0], -fd_game[2], fd_game[1])
        _apply_pivot_rotation(obj, game_loc, axis_blender, open_angle_rad)

    obj[TAG_GROUP_ID]    = f"bridge_{bridge_id}"
    obj[TAG_ENTRY_IDX]   = entry_idx
    obj[TAG_ROLE]        = role
    obj[TAG_NAME]        = entry.name
    obj[TAG_CONFIG_JSON] = json.dumps(_entry_to_config_dict(entry))
    return obj


def place_bridges_in_scene(
    blocks: Iterable[GizmoBlock],
    bms_folder: Path,
    texture_folder: Optional[Path] = None,
) -> int:
    """Clear the Bridges collection and place every GizmoBlock entry in the scene.

    Returns the number of objects placed.
    """
    col = _get_or_create_collection(_BRIDGES_COLLECTION)
    _clear_collection(col)
    _MESH_CACHE.clear()

    open_enabled, open_angle_deg = _open_bridges_settings()
    open_angle_rad = math.radians(open_angle_deg) if open_enabled else 0.0

    placed = 0
    skipped: List[str] = []
    blocks = list(blocks)
    label = "raised" if open_enabled else "flat"
    ok(f"Placing bridges in scene{sep()}{len(blocks)} bridge group(s) ({label})")
    for blk in blocks:
        for idx, entry in enumerate(blk.entries):
            obj = _place_one_entry(blk.bridge_id, idx, entry,
                                   bms_folder, texture_folder, col,
                                   open_angle_rad=open_angle_rad)
            if obj is None:
                skipped.append(entry.name)
            else:
                placed += 1

    if skipped:
        unique = sorted(set(skipped))
        item(f"Skipped (no BMS): {', '.join(unique)}")
    ok(f"Bridges placed{sep()}{placed}x object(s)")
    return placed


# ── Reading scene back to blocks ──────────────────────────────────────────────

def _config_from_obj(obj: bpy.types.Object) -> Optional[dict]:
    try:
        return json.loads(obj.get(TAG_CONFIG_JSON, "{}"))
    except Exception:
        return None


def collect_blocks_from_scene() -> List[GizmoBlock]:
    """Walk the Bridges collection and rebuild the GizmoBlock list."""
    objs = get_bridge_objects()
    if not objs:
        return []

    by_gid: Dict[str, List[Tuple[int, dict]]] = {}
    for obj in objs:
        gid = obj.get(TAG_GROUP_ID)
        cfg = _config_from_obj(obj)
        if not gid or cfg is None:
            continue
        entry_idx = int(obj.get(TAG_ENTRY_IDX, 0))
        by_gid.setdefault(gid, []).append((entry_idx, cfg))

    blocks: List[GizmoBlock] = []
    for gid in sorted(by_gid.keys(), key=lambda g: int(g.split("_")[-1]) if g.split("_")[-1].isdigit() else 0):
        bridge_id = int(gid.split("_")[-1])
        entries_sorted = [cfg for _, cfg in sorted(by_gid[gid], key=lambda t: t[0])]
        entries = [
            GizmoEntry(
                name=cfg["name"],
                flags=int(cfg.get("flags", 0)),
                offset=tuple(cfg["offset"]),
                face=tuple(cfg["face"]),
            )
            for cfg in entries_sorted
        ]
        blocks.append(GizmoBlock(bridge_id=bridge_id, entries=entries))
    return blocks


# ── Unique group access ───────────────────────────────────────────────────────

def get_unique_groups() -> Dict[str, List[bpy.types.Object]]:
    """Return {group_id: [objs]} sorted by bridge id."""
    out: Dict[str, List[bpy.types.Object]] = {}
    for obj in get_bridge_objects():
        gid = obj.get(TAG_GROUP_ID)
        if not gid:
            continue
        out.setdefault(gid, []).append(obj)
    # Sort objects in each group by entry index
    for gid in out:
        out[gid].sort(key=lambda o: int(o.get(TAG_ENTRY_IDX, 0)))
    return out

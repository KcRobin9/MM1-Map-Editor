"""
Bridge Editor operators — load/save GIZMO files, edit drawbridge groups,
and translate between the scene representation and the Python `bridges.py`
format used by `src.game.bridges.main.create_bridges`.
"""
import bpy
import importlib
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.constants.folder import Folder
from src.file_formats.gizmo.gizmo import GizmoBlock, GizmoEntry, read_gizmo, write_gizmo
from src.game.waypoints.constants import Rotation
from src.integrations.blender.modeling.bridges import (
    TAG_GROUP_ID, TAG_ENTRY_IDX, TAG_ROLE, TAG_NAME, TAG_CONFIG_JSON,
    angle_deg_to_face, direction_to_angle_deg,
    collect_blocks_from_scene,
    get_bridge_objects, get_unique_groups,
    is_bridge_obj,
    place_bridges_in_scene,
)


# ── Prop name dropdown ────────────────────────────────────────────────────────

def _build_bridge_name_items() -> List[Tuple[str, str, str]]:
    """Bridge-relevant prop entries from `Prop` — drawbridges + crossgates + bases."""
    from src.constants.props import Prop
    bridge_attrs = (
        "BRIDGE_SLIM", "BRIDGE_WIDE", "BRIDGE_BUILDING",
        "CROSSGATE", "CROSSGATE_SHORT", "CROSSGATE_BASE",
    )
    items: List[Tuple[str, str, str]] = []
    for attr in bridge_attrs:
        val = getattr(Prop, attr, None)
        if not isinstance(val, str):
            continue
        friendly = attr.replace("_", " ").title()
        items.append((val, friendly, f"Prop.{attr}"))
    return items


BRIDGE_NAME_ITEMS: List[Tuple[str, str, str]] = _build_bridge_name_items()

_GAME_TO_FRIENDLY: Dict[str, str] = {i[0]: i[1] for i in BRIDGE_NAME_ITEMS}
_GAME_TO_CONST:    Dict[str, str] = {i[0]: i[2] for i in BRIDGE_NAME_ITEMS}


def bridge_name_to_friendly(name: str) -> str:
    return _GAME_TO_FRIENDLY.get(name, name)


def bridge_name_to_const(name: str) -> str:
    return _GAME_TO_CONST.get(name, f'"{name}"')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _config_of(obj) -> dict:
    try:
        return json.loads(obj.get(TAG_CONFIG_JSON, "{}"))
    except Exception:
        return {}


def _bridge_id_from_group(group_id: str) -> int:
    tail = group_id.split("_")[-1]
    return int(tail) if tail.isdigit() else 0


def _next_free_bridge_id() -> int:
    used = {_bridge_id_from_group(o.get(TAG_GROUP_ID, "")) for o in get_bridge_objects()}
    used.discard(0)
    bid = 1
    while bid in used:
        bid += 1
    return bid


# Default config-cache so re-place after edits is one call.

def _re_place_from_scene() -> None:
    from src.USER.settings.blender import prop_bms_folder
    blocks = collect_blocks_from_scene()
    place_bridges_in_scene(blocks, Path(prop_bms_folder),
                           texture_folder=Folder.Resources.Editor.Textures)


# ── Auto-apply (form update callback) ─────────────────────────────────────────

_APPLYING = False
_TIMER_PENDING = False


def _do_re_place(scene_name: str) -> None:
    global _TIMER_PENDING
    _TIMER_PENDING = False
    scene = bpy.data.scenes.get(scene_name)
    if scene is None:
        return

    prev_group_id = scene.be_active_group_id

    try:
        _re_place_from_scene()
    except Exception as exc:
        import traceback
        print(f"[Bridge Editor] Re-place error: {exc}")
        print(traceback.format_exc())
        return

    # Re-select the group that was being edited so the user stays in context.
    if not prev_group_id:
        return
    group_objs = [o for o in get_bridge_objects() if o.get(TAG_GROUP_ID) == prev_group_id]
    if not group_objs:
        return
    for o in bpy.data.objects:
        try:
            if o.select_get():
                o.select_set(False)
        except Exception:
            pass
    target = group_objs[0]
    for o in group_objs:
        try:
            o.select_set(True)
        except Exception:
            pass
    try:
        bpy.context.view_layer.objects.active = target
    except Exception:
        pass


def _apply_changes_to_scene(scene) -> None:
    """Write the active entry's form values back to its tagged object's JSON."""
    global _APPLYING, _TIMER_PENDING
    if _APPLYING:
        return

    obj_name = scene.be_active_obj_name
    if not obj_name:
        return
    obj = bpy.data.objects.get(obj_name)
    if obj is None or not is_bridge_obj(obj):
        return

    _APPLYING = True
    try:
        offset = (round(scene.be_offset_x, 3),
                  round(scene.be_offset_y, 3),
                  round(scene.be_offset_z, 3))
        angle  = float(scene.be_angle)
        face   = angle_deg_to_face(offset, angle, distance=10.0)

        cfg = _config_of(obj)
        cfg["name"]   = scene.be_prop_name or cfg.get("name", "tpdrawbridge06")
        cfg["offset"] = list(offset)
        cfg["face"]   = list(face)
        obj[TAG_CONFIG_JSON] = json.dumps(cfg)
        obj[TAG_NAME]        = cfg["name"]
    except Exception as exc:
        print(f"[Bridge Editor] Apply error: {exc}")
    finally:
        _APPLYING = False

    if not _TIMER_PENDING:
        _TIMER_PENDING = True
        scene_name = scene.name
        bpy.app.timers.register(lambda: _do_re_place(scene_name), first_interval=0.05)


def _update_bridge_form(self, context):
    _apply_changes_to_scene(context.scene)


def load_form_from_obj(scene, obj) -> bool:
    """Populate the edit form from a bridge entry object's stored config."""
    global _APPLYING
    if not is_bridge_obj(obj):
        return False
    cfg = _config_of(obj)
    if not cfg:
        return False

    _APPLYING = True
    try:
        scene.be_active_obj_name = obj.name
        scene.be_active_group_id = obj.get(TAG_GROUP_ID, "")
        scene.be_active_role     = obj.get(TAG_ROLE, "attribute")
        name = cfg.get("name", "")
        if name in _GAME_TO_FRIENDLY:
            scene.be_prop_name = name
        offset = cfg.get("offset", [0.0, 0.0, 0.0])
        scene.be_offset_x = float(offset[0])
        scene.be_offset_y = float(offset[1])
        scene.be_offset_z = float(offset[2])
        face = cfg.get("face", [offset[0] + 10, offset[1], offset[2]])
        scene.be_angle = direction_to_angle_deg(tuple(offset), tuple(face))
    finally:
        _APPLYING = False
    return True


# ── Code generation (matches USER/bridges.py style) ───────────────────────────

_COMPASS_ATTRS = ("NORTH", "NORTH_EAST", "EAST", "SOUTH_EAST", "SOUTH", "SOUTH_WEST", "WEST", "NORTH_WEST")
_ROTATION_NAMES: Dict[float, str] = {getattr(Rotation, a): a for a in _COMPASS_ATTRS}


def _rotation_label(angle: float) -> str:
    for val, name in _ROTATION_NAMES.items():
        if abs(angle - val) < 0.5:
            return f"Rotation.{name}"
    return f"{angle:.2f}"


def _fmt_xyz(t) -> str:
    x, y, z = float(t[0]), float(t[1]), float(t[2])
    return f"({x:.2f}, {y:.2f}, {z:.2f})"


def _block_to_python(block: GizmoBlock) -> List[str]:
    """Emit Python tuples matching USER/bridges.py bridge_list structure.

    One drawbridge → one tuple. Crossgates are assigned to the nearest
    drawbridge entry (so blocks with 2 drawbridges produce 2 tuples that
    share the same bridge id).
    """
    drawbridges = block.drawbridges()
    crossgates  = block.crossgates()
    if not drawbridges:
        return []

    # Partition crossgates by nearest drawbridge in 2D (XZ) space.
    buckets: Dict[int, List[GizmoEntry]] = {i: [] for i in range(len(drawbridges))}
    for cg in crossgates:
        best_idx = 0
        best_d2  = float("inf")
        for i, db in enumerate(drawbridges):
            dx = cg.offset[0] - db.offset[0]
            dz = cg.offset[2] - db.offset[2]
            d2 = dx*dx + dz*dz
            if d2 < best_d2:
                best_d2 = d2
                best_idx = i
        buckets[best_idx].append(cg)

    lines: List[str] = []
    for i, db in enumerate(drawbridges):
        db_angle = direction_to_angle_deg(db.offset, db.face)
        cgs = buckets[i]
        cg_lines = []
        for cg in cgs:
            cg_angle = direction_to_angle_deg(cg.offset, cg.face)
            cg_lines.append(
                f"        ({_fmt_xyz(cg.offset)}, {_rotation_label(cg_angle)}, "
                f"{block.bridge_id}, {bridge_name_to_const(cg.name)}),"
            )
        if cg_lines:
            lines.append(
                f"    ({_fmt_xyz(db.offset)}, {_rotation_label(db_angle)}, "
                f"{block.bridge_id}, {bridge_name_to_const(db.name)}, ["
            )
            lines.extend(cg_lines)
            lines.append("    ]),")
        else:
            lines.append(
                f"    ({_fmt_xyz(db.offset)}, {_rotation_label(db_angle)}, "
                f"{block.bridge_id}, {bridge_name_to_const(db.name)}, []),"
            )
    return lines


def generate_python_code(blocks: List[GizmoBlock]) -> str:
    out = [
        "# Generated by Bridge Editor",
        "from src.constants.props import Prop",
        "from src.game.waypoints.constants import Rotation",
        "",
        "bridge_list = [",
    ]
    for blk in blocks:
        out.extend(_block_to_python(blk))
    out.append("]")
    return "\n".join(out)


# ── Operators ─────────────────────────────────────────────────────────────────

class BRIDGES_OT_LoadExternal(bpy.types.Operator):
    """Load drawbridges from an external .GIZMO file"""
    bl_idname = "bridges.load_external"
    bl_label  = "Load External GIZMO"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.gizmo;*.GIZMO", options={"HIDDEN"})

    def invoke(self, context, event):
        self.filepath = str(Folder.BASE) + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        from src.USER.settings.blender import prop_bms_folder
        path = Path(self.filepath)
        if not path.exists():
            self.report({"ERROR"}, f"File not found: {path}")
            return {"CANCELLED"}

        blocks = read_gizmo(path)
        n = place_bridges_in_scene(blocks, Path(prop_bms_folder),
                                   texture_folder=Folder.Resources.Editor.Textures)
        self.report({"INFO"}, f"Loaded {len(blocks)} bridge(s) ({n} entries) from {path.name}")
        return {"FINISHED"}


class BRIDGES_OT_Clear(bpy.types.Operator):
    """Remove all bridge entries from the scene"""
    bl_idname = "bridges.clear"
    bl_label  = "Clear Bridges"

    def execute(self, context):
        col = bpy.data.collections.get("Bridges")
        if not col:
            self.report({"INFO"}, "No bridges to clear")
            return {"FINISHED"}
        n = len(col.objects)
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        self.report({"INFO"}, f"Cleared {n} bridge object(s)")
        return {"FINISHED"}


class BRIDGES_OT_ReloadFromPy(bpy.types.Operator):
    """Reload bridges from USER/bridges.py and re-place"""
    bl_idname = "bridges.reload_from_py"
    bl_label  = "Reload from bridges.py"

    def execute(self, context):
        from src.USER.settings.blender import prop_bms_folder
        try:
            import src.USER.bridges as _mod
            importlib.reload(_mod)
        except Exception as exc:
            self.report({"ERROR"}, f"Could not load USER/bridges.py: {exc}")
            return {"CANCELLED"}

        blocks = _bridges_py_to_blocks(getattr(_mod, "bridge_list", []))
        n = place_bridges_in_scene(blocks, Path(prop_bms_folder),
                                   texture_folder=Folder.Resources.Editor.Textures)
        self.report({"INFO"}, f"Reloaded {len(blocks)} bridge(s) ({n} entries) from bridges.py")
        return {"FINISHED"}


def _bridges_py_to_blocks(user_bridge_list) -> List[GizmoBlock]:
    """Convert USER/bridges.py `bridge_list` tuples → GizmoBlock list."""
    blocks_by_id: Dict[int, GizmoBlock] = {}

    for tup in user_bridge_list:
        try:
            offset, rotation, bid, drawbridge_type, attributes = tup
        except (ValueError, TypeError):
            continue
        bid = int(bid)
        block = blocks_by_id.setdefault(bid, GizmoBlock(bridge_id=bid))

        db_face = angle_deg_to_face(tuple(offset), float(rotation), distance=10.0)
        block.entries.append(GizmoEntry(
            name=str(drawbridge_type), flags=0,
            offset=tuple(offset), face=db_face,
        ))
        for atup in attributes:
            try:
                a_offset, a_rot, _aid, a_type = atup
            except (ValueError, TypeError):
                continue
            cg_face = angle_deg_to_face(tuple(a_offset), float(a_rot), distance=10.0)
            block.entries.append(GizmoEntry(
                name=str(a_type), flags=0,
                offset=tuple(a_offset), face=cg_face,
            ))

    return [blocks_by_id[k] for k in sorted(blocks_by_id.keys())]


class BRIDGES_OT_SaveGizmo(bpy.types.Operator):
    """Write all scene bridge groups to a .GIZMO file"""
    bl_idname = "bridges.save_gizmo"
    bl_label  = "Save GIZMO"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.gizmo;*.GIZMO", options={"HIDDEN"})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "bridges.gizmo"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        blocks = collect_blocks_from_scene()
        if not blocks:
            self.report({"WARNING"}, "No bridges in scene")
            return {"CANCELLED"}
        path = Path(self.filepath)
        write_gizmo(path, blocks, pad_to_six=True)
        n_entries = sum(len(b.entries) for b in blocks)
        self.report({"INFO"}, f"Saved {len(blocks)} bridge(s) ({n_entries} entries) to {path.name}")
        return {"FINISHED"}


class BRIDGES_OT_ExportCode(bpy.types.Operator):
    """Generate Python (USER/bridges.py-style) code for all scene bridges"""
    bl_idname = "bridges.export_code"
    bl_label  = "Export as Code"

    def execute(self, context):
        blocks = collect_blocks_from_scene()
        if not blocks:
            self.report({"WARNING"}, "No bridges in scene")
            return {"CANCELLED"}
        code = generate_python_code(blocks)
        print("\n" + "=" * 70)
        print("# ── BRIDGE EDITOR EXPORT ─────────────────────────────────────────")
        print(code)
        print("=" * 70 + "\n")
        try:
            context.window_manager.clipboard = code
            self.report({"INFO"}, "Exported — copied to clipboard")
        except Exception:
            self.report({"INFO"}, "Exported — see console")
        return {"FINISHED"}


class BRIDGES_OT_SelectGroup(bpy.types.Operator):
    """Select all objects in the active bridge group"""
    bl_idname = "bridges.select_group"
    bl_label  = "Select Group"

    def execute(self, context):
        obj = context.active_object
        if not is_bridge_obj(obj):
            self.report({"WARNING"}, "Active object is not a bridge")
            return {"CANCELLED"}
        gid = obj.get(TAG_GROUP_ID)
        bpy.ops.object.select_all(action="DESELECT")
        n = 0
        for o in get_bridge_objects():
            if o.get(TAG_GROUP_ID) == gid:
                o.select_set(True)
                n += 1
        context.view_layer.objects.active = obj
        self.report({"INFO"}, f"Selected {n} object(s) in {gid}")
        return {"FINISHED"}


class BRIDGES_OT_DeleteGroup(bpy.types.Operator):
    """Remove every object in the active bridge group"""
    bl_idname = "bridges.delete_group"
    bl_label  = "Delete Group"

    def execute(self, context):
        obj = context.active_object
        if not is_bridge_obj(obj):
            self.report({"WARNING"}, "Active object is not a bridge")
            return {"CANCELLED"}
        gid = obj.get(TAG_GROUP_ID)
        to_remove = [o for o in get_bridge_objects() if o.get(TAG_GROUP_ID) == gid]
        for o in to_remove:
            bpy.data.objects.remove(o, do_unlink=True)
        self.report({"INFO"}, f"Deleted {len(to_remove)} object(s) from {gid}")
        return {"FINISHED"}


class BRIDGES_OT_LoadIntoForm(bpy.types.Operator):
    """Populate the Edit form from the active bridge entry"""
    bl_idname = "bridges.load_into_form"
    bl_label  = "Edit"

    def execute(self, context):
        obj = context.active_object
        if not is_bridge_obj(obj):
            self.report({"WARNING"}, "Active object is not a bridge")
            return {"CANCELLED"}
        if not load_form_from_obj(context.scene, obj):
            self.report({"ERROR"}, "Could not parse bridge config")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Editing {obj.name}")
        return {"FINISHED"}


class BRIDGES_OT_CreateBridge(bpy.types.Operator):
    """Create a new bridge group (2 drawbridge halves + 4 crossgates) at the form offset"""
    bl_idname = "bridges.create_bridge"
    bl_label  = "Create Bridge"

    def execute(self, context):
        from src.USER.settings.blender import prop_bms_folder
        scene = context.scene

        bid = _next_free_bridge_id()
        ox, oy, oz = scene.bc_offset_x, scene.bc_offset_y, scene.bc_offset_z
        angle      = float(scene.bc_angle)
        drawbridge = scene.bc_drawbridge_name
        crossgate  = scene.bc_crossgate_name
        span       = float(scene.bc_span)        # distance between the 2 drawbridge halves
        gate_off   = float(scene.bc_gate_offset) # offset of crossgate from drawbridge centre (perp.)

        rad = math.radians(angle)
        # fwd  = face/hinge axis direction (the angle the user types)
        # perp = road direction (perpendicular to fwd — halves sit on either side)
        fwd  = (math.cos(rad), 0.0, math.sin(rad))
        perp = (-math.sin(rad), 0.0, math.cos(rad))

        def _add(off, name, ang):
            face = angle_deg_to_face(off, ang, distance=10.0)
            return GizmoEntry(name=name, flags=0, offset=off, face=face)

        # Halves separated along road direction (perp). Each half faces along the
        # hinge axis (fwd / fwd+180) so the open-bridges pivot rotates them upward.
        half_a_off = (ox + perp[0] * span/2, oy, oz + perp[2] * span/2)
        half_b_off = (ox - perp[0] * span/2, oy, oz - perp[2] * span/2)
        a_angle = angle
        b_angle = angle + 180

        entries = [_add(half_a_off, drawbridge, a_angle),
                   _add(half_b_off, drawbridge, b_angle)]

        # 2 crossgates per half — offset along ±fwd (hinge axis), facing outward.
        for half_off in (half_a_off, half_b_off):
            gate1 = (half_off[0] + fwd[0] * gate_off, half_off[1] + 0.15, half_off[2] + fwd[2] * gate_off)
            gate2 = (half_off[0] - fwd[0] * gate_off, half_off[1] + 0.15, half_off[2] - fwd[2] * gate_off)
            entries.append(_add(gate1, crossgate, angle))
            entries.append(_add(gate2, crossgate, angle + 180))

        block = GizmoBlock(bridge_id=bid, entries=entries)
        all_blocks = collect_blocks_from_scene() + [block]
        place_bridges_in_scene(all_blocks, Path(prop_bms_folder),
                               texture_folder=Folder.Resources.Editor.Textures)
        self.report({"INFO"}, f"Created bridge_{bid} with {len(entries)} entries")
        return {"FINISHED"}


BRIDGE_EDITOR_CLASSES = [
    BRIDGES_OT_LoadExternal,
    BRIDGES_OT_Clear,
    BRIDGES_OT_ReloadFromPy,
    BRIDGES_OT_SaveGizmo,
    BRIDGES_OT_ExportCode,
    BRIDGES_OT_SelectGroup,
    BRIDGES_OT_DeleteGroup,
    BRIDGES_OT_LoadIntoForm,
    BRIDGES_OT_CreateBridge,
]

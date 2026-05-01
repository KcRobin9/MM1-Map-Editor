import bpy
import json
import importlib
import math
from pathlib import Path
from typing import Dict, List, Tuple

from src.constants.folder import Folder


_FACADES_COLLECTION = "Facades"
_FACADE_TAG         = "mm_facade_group_id"
_FACADE_CFG_TAG     = "mm_facade_config_json"


# ── Facade name ↔ label tables (built once at import) ────────────────────────

def _build_facade_name_items() -> List[Tuple[str, str, str]]:
    items = []
    from src.constants.facades import Facade
    for attr, val in sorted(vars(Facade).items()):
        if attr.startswith("_") or not isinstance(val, str):
            continue
        friendly = attr.replace("_", " ").title()
        const    = f"Facade.{attr}"
        items.append((val, friendly, const))
    return items


FACADE_NAME_ITEMS: List[Tuple[str, str, str]] = _build_facade_name_items()

_GAME_TO_FRIENDLY: Dict[str, str] = {item[0]: item[1] for item in FACADE_NAME_ITEMS}
_GAME_TO_CONST:    Dict[str, str] = {item[0]: item[2] for item in FACADE_NAME_ITEMS}


def facade_name_to_friendly(name: str) -> str:
    return _GAME_TO_FRIENDLY.get(name, name)


def facade_name_to_const(name: str) -> str:
    return _GAME_TO_CONST.get(name, f'"{name}"')


# ── Flags enum items (built once at import) ────────────────────────────────────
# Only named combinations (multi-char names / named presets), not raw primitive bits.
# Identifier = str(int_value) so Blender EnumProperty can store it as string.

def _build_flags_items() -> List[Tuple[str, str, str]]:
    from src.constants.facades import FcdFlags
    seen: Dict[int, str] = {}
    for attr, val in vars(FcdFlags).items():
        if attr.startswith("_") or not isinstance(val, int):
            continue
        # Prefer longer / more-descriptive names when multiple attrs share a value
        if val not in seen or len(attr) > len(seen[val]):
            seen[val] = attr
    return sorted(
        [(str(val), name, f"0x{val:03X}  ({val})") for val, name in seen.items()],
        key=lambda x: int(x[0]),
    )


FACADE_FLAGS_ITEMS: List[Tuple[str, str, str]] = _build_flags_items()

# Fast reverse: int value → attr name
_FLAGS_INT_TO_NAME: Dict[int, str] = {int(i[0]): i[1] for i in FACADE_FLAGS_ITEMS}


def flags_to_const(flags_val: int) -> str:
    name = _FLAGS_INT_TO_NAME.get(flags_val)
    return f"FcdFlags.{name}" if name else str(flags_val)


# ── Collection / object helpers ───────────────────────────────────────────────

def _get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _clear_collection(col: bpy.types.Collection) -> None:
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def get_facade_objects() -> List[bpy.types.Object]:
    if _FACADES_COLLECTION not in bpy.data.collections:
        return []
    return list(bpy.data.collections[_FACADES_COLLECTION].objects)


def is_facade_obj(obj) -> bool:
    if obj is None:
        return False
    if _FACADE_TAG in obj:
        return True
    # Also accept child mesh objects whose parent is a tagged facade empty
    return obj.parent is not None and _FACADE_TAG in obj.parent


def get_unique_groups() -> Dict[str, dict]:
    """Return {group_id: config_dict} for every unique facade group in the scene."""
    groups: Dict[str, dict] = {}
    for obj in get_facade_objects():
        gid = obj.get(_FACADE_TAG)
        if gid and gid not in groups:
            try:
                cfg = json.loads(obj.get(_FACADE_CFG_TAG, "{}"))
                groups[gid] = cfg
            except Exception:
                pass
    return groups


# ── Panel-count computation (mirrors FacadeEditor.process logic) ──────────────

def _panel_positions(cfg: dict) -> List[Tuple[tuple, tuple]]:
    """Return list of (game_start, game_end) for every panel in a facade group."""
    axis_map = {'x': 0, 'y': 1, 'z': 2}
    axis     = axis_map.get(cfg.get('axis', 'x'), 0)
    offset   = list(cfg.get('offset', [0.0, 0.0, 0.0]))
    end      = list(cfg.get('end',    [0.0, 0.0, 0.0]))
    sep      = float(cfg.get('separator', 10.0))
    if sep <= 0:
        sep = 10.0

    start_c = offset[axis]
    end_c   = end[axis]
    length  = abs(end_c - start_c)
    n       = max(1, math.ceil(length / sep))
    direction = 1 if start_c <= end_c else -1

    panels = []
    for i in range(n):
        shift = direction * sep * i
        cur_s = list(offset)
        cur_e = list(end)
        cur_s[axis] = start_c + shift
        if direction == 1:
            cur_e[axis] = min(start_c + shift + sep, end_c)
        else:
            cur_e[axis] = max(start_c + shift - sep, end_c)
        panels.append((tuple(cur_s), tuple(cur_e)))
    return panels


# ── BMS loading helper ────────────────────────────────────────────────────────

_MESHES_FACADES = Folder.Resources.Editor.MeshesFacades

_BMS_VARIANTS = ("FACADE_H.BMS", "BLDG_H.BMS", "H.BMS", "FACADE_M.BMS", "M.BMS", "FACADE_L.BMS")

# Side-part filenames to try in order
_LEFT_VARIANTS  = ("LEFT.BMS",)
_RIGHT_VARIANTS = ("RIGHT.BMS",)
_TOP_VARIANTS   = ("TOP_H.BMS", "TOP.BMS")
_BACK_VARIANTS  = ("BACK.BMS",)


def _find_facade_bms(name: str) -> Path | None:
    folder = _MESHES_FACADES / name.upper()
    if not folder.is_dir():
        return None
    for variant in _BMS_VARIANTS:
        p = folder / variant
        if p.exists():
            return p
    return None


def _find_bms_variant(folder: Path, variants) -> Path | None:
    for v in variants:
        p = folder / v
        if p.exists():
            return p
    return None


def _load_bms_part(bms_file: Path, name: str, tex_folder) -> "bpy.types.Mesh | None":
    from src.integrations.blender.modeling.meshes import read_bms, build_blender_mesh, _apply_materials_to_mesh
    try:
        bms_data = read_bms(bms_file)
        mesh = build_blender_mesh(name, bms_data)
        if tex_folder and bms_data.get("texture_names"):
            _apply_materials_to_mesh(mesh, bms_data["texture_names"], tex_folder)
        mesh["bms_source_file"] = str(bms_file)
        ox, oy, oz = bms_data.get("mesh_offset", [0.0, 0.0, 0.0])
        mesh["_bl_offset"] = (-ox, oz, oy)
        return mesh
    except Exception as exc:
        print(f"[Facade Editor] BMS load failed ({bms_file.name}): {exc}")
        return None


def _add_child_obj(mesh, name: str, tag: str, parent_obj, col):
    import mathutils
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.parent = parent_obj
    obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    obj.location = mesh.get("_bl_offset", (0.0, 0.0, 0.0))
    obj[_FACADE_TAG] = tag
    return obj


def _game_to_blender(gx: float, gy: float, gz: float) -> Tuple[float, float, float]:
    """Game (x, height, z) → Blender (x, -z, height) — matches transform_coordinate_system(game_to_blender)."""
    return (gx, -gz, gy)


def _facade_matrix_to_blender(
    start: Tuple[float, float, float],
    end:   Tuple[float, float, float],
    scale: float,
) -> "mathutils.Matrix":
    """
    Port of MatrixFromPoints() from the game binary, converted to a Blender matrix_world.

    The game builds a 3×4 transform where:
      m0 = normalised(end-start) * (dist/scale)  — forward axis, scaled to fit panel gap
      m1 = world_up = (0,1,0)                    — up axis
      m2 = cross(m1, m0_normalised)              — right axis (unit length)
      m3 = start, with Y clamped to min(start.y, end.y)

    scale = nominal mesh width (from "FCD scales.txt" or fcd.scale).
    The length_factor = dist/scale stretches or squishes the mesh along its forward axis
    so it exactly spans the gap between start and end.

    Game → Blender: (gx, gy, gz) → (gx, -gz, gy).
    BMS meshes face -X in Blender, so game-forward maps onto Blender -X.
    """
    import mathutils

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]

    dist = (dx * dx + dy * dy + dz * dz) ** 0.5
    if dist == 0.0 or scale == 0.0:
        # Degenerate: no direction — return identity at start
        loc = mathutils.Vector((start[0], -start[2], start[1]))
        mat = mathutils.Matrix.Identity(4)
        mat.translation = loc
        return mat

    inv = 1.0 / dist
    length_factor = dist / scale

    # Normalised forward in game space
    nx, ny, nz = dx * inv, dy * inv, dz * inv

    # right = cross(world_up=(0,1,0), forward_normalised)
    # = (1*nz - 0*ny,  0*nx - 0*nz,  0*ny - 1*nx) = (nz, 0, -nx)
    rx, ry, rz = nz, 0.0, -nx

    # Game-space column vectors (matching C++ m0 scaled, m1=up, m2=right):
    #   forward_g = (nx, ny, nz) * length_factor   — the stretched axis
    #   up_g      = (0, 1, 0)
    #   right_g   = (rx, ry, rz)

    # Convert each to Blender space: (gx,gy,gz) → (gx, -gz, gy)
    def g2b(gx, gy, gz):
        return (gx, -gz, gy)

    fwd_b = g2b(nx * length_factor, ny * length_factor, nz * length_factor)
    up_b  = g2b(0.0, 1.0, 0.0)   # → (0, 0, 1)
    rgt_b = g2b(rx, ry, rz)

    # BMS meshes have their geometry along local -X, so we need:
    #   local +X maps to  -fwd_b  (into the facade face, which the game drives forward)
    #   local +Y maps to  -rgt_b  (game right becomes Blender -Y because of axis flip)
    #   local +Z maps to   up_b   (= Blender Z)
    # Build matrix column by column (Blender Matrix rows = rows of the matrix):
    col_x = (-fwd_b[0], -fwd_b[1], -fwd_b[2])
    col_y = (-rgt_b[0], -rgt_b[1], -rgt_b[2])
    col_z = ( up_b[0],   up_b[1],   up_b[2])

    mat3 = mathutils.Matrix((
        (col_x[0], col_y[0], col_z[0]),
        (col_x[1], col_y[1], col_z[1]),
        (col_x[2], col_y[2], col_z[2]),
    ))

    # Position: game clamps to min Y (height), matching C++ `if m3.y > end.y: m3.y = end.y`
    px, py, pz = start[0], start[1], start[2]
    if start[1] > end[1]:
        py = end[1]
    loc = mathutils.Vector(g2b(px, py, pz))

    mat4 = mat3.to_4x4()
    mat4.translation = loc
    return mat4


# ── Scene placement ───────────────────────────────────────────────────────────

def place_facades_in_scene(facade_cfgs: list, texture_folder=None) -> None:
    """
    Place facade groups in the Blender scene.

    Each panel becomes a parent Empty at the panel's world position/rotation,
    with child mesh objects for FACADE_H (main), LEFT, RIGHT, TOP parts as
    available on disk and gated by the sides values.
    """
    if texture_folder is None:
        texture_folder = Folder.Resources.Editor.Textures

    col = _get_or_create_collection(_FACADES_COLLECTION)
    _clear_collection(col)

    placed       = 0
    missing      = 0
    missing_names: set = set()

    for grp_idx, cfg in enumerate(facade_cfgs):
        gid    = f"facade_{grp_idx}"
        name   = cfg.get('name', 'unknown')
        panels = _panel_positions(cfg)
        sides  = cfg.get('sides', [0.0, 0.0, 0.0])
        sides_l, sides_r, sides_d = (float(v) for v in sides)
        flags  = int(cfg.get('flags', 0))
        face_vec  = cfg.get('face_vec')   # present for FCD records; None for editor groups
        fcd_scale = float(cfg.get('scale', 1.0))

        mesh_folder = (_MESHES_FACADES / name.upper()) if (_MESHES_FACADES / name.upper()).is_dir() else None

        # Gate side/top/back parts by FcdFlags bits — mirrors C++ mmFacadeInstance::Draw.
        # INST_INIT_FLAG_FCD_LEFT=0x8, RIGHT=0x10, TOP=0x20, BACK=0x400
        has_left  = bool(flags & 0x008)
        has_right = bool(flags & 0x010)
        has_roof  = bool(flags & 0x020)
        has_back  = bool(flags & 0x400)

        for pnl_idx, (game_start, game_end) in enumerate(panels):
            panel_name = f"{name}_{grp_idx}_{pnl_idx}"

            # ── Parent empty ──────────────────────────────────────────────
            parent_obj = bpy.data.objects.new(panel_name, None)
            parent_obj.empty_display_type  = "ARROWS"
            parent_obj.empty_display_size  = 1.0
            col.objects.link(parent_obj)

            if face_vec is not None:
                # FCD record: offset is panel start, face_vec is panel end.
                g_start = tuple(cfg['offset'])
                g_end   = tuple(face_vec)
            else:
                g_start = game_start
                g_end   = game_end

            mat = _facade_matrix_to_blender(g_start, g_end, fcd_scale)
            parent_obj.matrix_world = mat

            parent_obj[_FACADE_TAG]       = gid
            parent_obj[_FACADE_CFG_TAG]   = json.dumps(cfg)
            parent_obj["mm_facade_name"]  = name
            parent_obj["mm_facade_panel"] = pnl_idx

            if mesh_folder is None:
                if name not in missing_names:
                    print(f"  [Facade Editor] No BMS folder for '{name}'")
                    missing_names.add(name)
                missing += 1
                continue

            placed += 1

            # ── Main facade mesh (FACADE_H / H) ───────────────────────────
            main_bms = _find_bms_variant(mesh_folder, _BMS_VARIANTS)
            if main_bms:
                mesh = _load_bms_part(main_bms, f"{panel_name}_H", texture_folder)
                if mesh:
                    _add_child_obj(mesh, f"{panel_name}_H", "FACADE_H", parent_obj, col)

            # ── Left side (gated by FcdFlags.LEFT/LEFT_B + non-zero sides) ─
            if has_left:
                left_bms = _find_bms_variant(mesh_folder, _LEFT_VARIANTS)
                if left_bms:
                    mesh = _load_bms_part(left_bms, f"{panel_name}_LEFT", texture_folder)
                    if mesh:
                        _add_child_obj(mesh, f"{panel_name}_LEFT", "LEFT", parent_obj, col)

            # ── Right side (gated by FcdFlags.RIGHT/RIGHT_B + non-zero sides)
            if has_right:
                right_bms = _find_bms_variant(mesh_folder, _RIGHT_VARIANTS)
                if right_bms:
                    mesh = _load_bms_part(right_bms, f"{panel_name}_RIGHT", texture_folder)
                    if mesh:
                        _add_child_obj(mesh, f"{panel_name}_RIGHT", "RIGHT", parent_obj, col)

            # ── Top (gated by FcdFlags.ROOF) ──────────────────────────────
            if has_roof:
                top_bms = _find_bms_variant(mesh_folder, _TOP_VARIANTS)
                if top_bms:
                    mesh = _load_bms_part(top_bms, f"{panel_name}_TOP", texture_folder)
                    if mesh:
                        _add_child_obj(mesh, f"{panel_name}_TOP", "TOP", parent_obj, col)

            # ── Back (gated by FcdFlags.BACK = 0x400) ─────────────────────
            if has_back:
                back_bms = _find_bms_variant(mesh_folder, _BACK_VARIANTS)
                if back_bms:
                    mesh = _load_bms_part(back_bms, f"{panel_name}_BACK", texture_folder)
                    if mesh:
                        _add_child_obj(mesh, f"{panel_name}_BACK", "BACK", parent_obj, col)

    print(f"Facades placed in scene: {placed} (missing BMS: {missing})")


# ── Code generation ───────────────────────────────────────────────────────────

def _fmt_vec(vals) -> str:
    return f"({', '.join(f'{float(v):.2f}' for v in vals)})"


def generate_python_code(groups: Dict[str, dict]) -> str:
    lines = [
        "# Generated by Facade Editor",
        "from src.constants.facades import Facade, FcdFlags",
        "",
    ]

    var_names = []
    for gid, cfg in sorted(groups.items(), key=lambda x: x[0]):
        var = f"facade_{gid.replace('facade_', '')}"
        var_names.append(var)
        lines.append(f"{var} = {{")
        lines.append(f'    "name":      {facade_name_to_const(cfg.get("name", ""))},')
        lines.append(f'    "flags":     {flags_to_const(int(cfg.get("flags", 1)))},')
        lines.append(f'    "offset":    {_fmt_vec(cfg.get("offset", [0, 0, 0]))},')
        lines.append(f'    "end":       {_fmt_vec(cfg.get("end",    [0, 0, 0]))},')
        lines.append(f'    "axis":      "{cfg.get("axis", "x")}",')
        lines.append(f'    "separator": {float(cfg.get("separator", 10.0)):.2f},')
        sides = cfg.get("sides", [0.0, 0.0, 0.0])
        if any(float(s) != 0.0 for s in sides):
            lines.append(f'    "sides":     {_fmt_vec(sides)},')
        if not cfg.get("scale_auto", True):
            lines.append(f'    "scale":     {float(cfg.get("scale", 1.0)):.2f},')
        lines.append("}")
        lines.append("")

    lines.append(f"facade_list = [{', '.join(var_names)}]")
    return "\n".join(lines)


# ── Update callbacks (form → scene → deferred re-place) ──────────────────────

_APPLYING      = False
_TIMER_PENDING = False


def _do_place(scene_name: str) -> None:
    global _APPLYING, _TIMER_PENDING
    _TIMER_PENDING = False

    import bpy as _bpy
    scene = _bpy.data.scenes.get(scene_name)
    if scene is None:
        return
    groups = get_unique_groups()
    if not groups:
        return
    try:
        place_facades_in_scene(list(groups.values()))
    except Exception as exc:
        import traceback
        print(f"[Facade Editor] Auto-place error: {exc}")
        print(traceback.format_exc())


def _apply_facade_changes(scene) -> None:
    global _APPLYING, _TIMER_PENDING
    if _APPLYING:
        return
    group_id = getattr(scene, "fe_active_group_id", "")
    if not group_id:
        return
    groups = get_unique_groups()
    if group_id not in groups:
        return

    _APPLYING = True
    try:
        cfg = groups[group_id]
        cfg["name"]       = scene.fe_facade_name
        cfg["flags"]      = int(scene.fe_flags)
        cfg["offset"]     = [round(scene.fe_offset_x, 2), round(scene.fe_offset_y, 2), round(scene.fe_offset_z, 2)]
        cfg["end"]        = [round(scene.fe_end_x,    2), round(scene.fe_end_y,    2), round(scene.fe_end_z,    2)]
        cfg["axis"]       = scene.fe_axis
        cfg["separator"]  = round(scene.fe_separator, 3)
        cfg["sides"]      = [round(scene.fe_sides_x, 2), round(scene.fe_sides_y, 2), round(scene.fe_sides_z, 2)]
        cfg["scale_auto"] = scene.fe_scale_auto
        cfg["scale"]      = round(scene.fe_scale, 3)

        new_json = json.dumps(cfg)
        for obj in get_facade_objects():
            if obj.get(_FACADE_TAG) == group_id:
                obj[_FACADE_CFG_TAG] = new_json
    except Exception as exc:
        print(f"[Facade Editor] Config update error: {exc}")
    finally:
        _APPLYING = False

    if not _TIMER_PENDING:
        _TIMER_PENDING = True
        scene_name = scene.name
        import bpy as _bpy
        _bpy.app.timers.register(lambda: _do_place(scene_name), first_interval=0.05)


def _update_facade_form(self, context):
    _apply_facade_changes(context.scene)


def load_form_from_obj(scene, obj) -> bool:
    """Populate the Edit form from a tagged facade object. Returns True on success."""
    global _APPLYING
    if not is_facade_obj(obj):
        return False
    try:
        cfg = json.loads(obj.get(_FACADE_CFG_TAG, "{}"))
    except Exception:
        return False

    _APPLYING = True
    try:
        scene.fe_active_group_id = obj.get(_FACADE_TAG, "")

        name = cfg.get("name", "")
        if name in _GAME_TO_CONST:
            scene.fe_facade_name = name

        flags_val = int(cfg.get("flags", 1))
        flags_str = str(flags_val)
        if flags_str in {item[0] for item in FACADE_FLAGS_ITEMS}:
            scene.fe_flags = flags_str

        offset = cfg.get("offset", [0.0, 0.0, 0.0])
        scene.fe_offset_x = float(offset[0])
        scene.fe_offset_y = float(offset[1])
        scene.fe_offset_z = float(offset[2])

        end = cfg.get("end", [0.0, 0.0, 0.0])
        scene.fe_end_x = float(end[0])
        scene.fe_end_y = float(end[1])
        scene.fe_end_z = float(end[2])

        scene.fe_axis      = cfg.get("axis", "x")
        scene.fe_separator = float(cfg.get("separator", 10.0))

        sides = cfg.get("sides", [0.0, 0.0, 0.0])
        scene.fe_sides_x = float(sides[0])
        scene.fe_sides_y = float(sides[1])
        scene.fe_sides_z = float(sides[2])

        scene.fe_scale_auto = bool(cfg.get("scale_auto", True))
        scene.fe_scale      = float(cfg.get("scale", 1.0))
    finally:
        _APPLYING = False
    return True


# ── Operators ─────────────────────────────────────────────────────────────────

class FACADES_OT_Reload(bpy.types.Operator):
    """Reload facades from USER/facades.py and re-place in the scene"""
    bl_idname = "facades.reload"
    bl_label  = "Reload from facades.py"

    def execute(self, context):
        import src.USER.facades as _mod
        importlib.reload(_mod)
        place_facades_in_scene(_mod.facade_list)
        self.report({"INFO"}, f"Loaded {len(_mod.facade_list)} facade group(s)")
        return {"FINISHED"}


class FACADES_OT_Clear(bpy.types.Operator):
    """Remove all facades from the scene without reloading"""
    bl_idname = "facades.clear"
    bl_label  = "Clear Facades"

    def execute(self, context):
        col = _get_or_create_collection(_FACADES_COLLECTION)
        _clear_collection(col)
        self.report({"INFO"}, "Facades cleared")
        return {"FINISHED"}


class FACADES_OT_SelectGroup(bpy.types.Operator):
    """Select all objects belonging to the same facade group as the active object"""
    bl_idname = "facades.select_group"
    bl_label  = "Select Group"

    def execute(self, context):
        obj = context.active_object
        if not is_facade_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged facade")
            return {"CANCELLED"}
        gid = obj.get(_FACADE_TAG)
        bpy.ops.object.select_all(action="DESELECT")
        for o in get_facade_objects():
            if o.get(_FACADE_TAG) == gid:
                o.select_set(True)
        context.view_layer.objects.active = obj
        count = sum(1 for o in get_facade_objects() if o.get(_FACADE_TAG) == gid)
        self.report({"INFO"}, f"Selected {count} object(s) in group '{gid}'")
        return {"FINISHED"}


class FACADES_OT_LoadIntoForm(bpy.types.Operator):
    """Populate the edit form from the active facade object's stored config"""
    bl_idname = "facades.load_into_form"
    bl_label  = "Edit"

    def execute(self, context):
        obj = context.active_object
        if not is_facade_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged facade")
            return {"CANCELLED"}
        if not load_form_from_obj(context.scene, obj):
            self.report({"ERROR"}, "Could not parse facade config")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Editing '{context.scene.fe_active_group_id}'")
        return {"FINISHED"}


class FACADES_OT_ExportCode(bpy.types.Operator):
    """Print Python code for all facade groups to console and clipboard"""
    bl_idname = "facades.export_code"
    bl_label  = "Export All as Code"

    def execute(self, context):
        groups = get_unique_groups()
        if not groups:
            self.report({"WARNING"}, "No facade groups in scene — reload facades first")
            return {"CANCELLED"}
        code = generate_python_code(groups)
        print("\n" + "=" * 70)
        print("# ── FACADE EDITOR EXPORT ───────────────────────────────────────────")
        print(code)
        print("=" * 70 + "\n")
        try:
            context.window_manager.clipboard = code
            self.report({"INFO"}, "Exported — copied to clipboard")
        except Exception:
            self.report({"INFO"}, "Exported — see console")
        return {"FINISHED"}


class FACADES_OT_ExportGroupCode(bpy.types.Operator):
    """Export Python code for only the currently active facade group"""
    bl_idname = "facades.export_group_code"
    bl_label  = "Copy Group as Code"

    def execute(self, context):
        group_id = context.scene.fe_active_group_id
        if not group_id:
            self.report({"WARNING"}, "No active group — click 'Edit' on a facade first")
            return {"CANCELLED"}
        groups = get_unique_groups()
        if group_id not in groups:
            self.report({"ERROR"}, f"Group '{group_id}' not found")
            return {"CANCELLED"}
        code = generate_python_code({group_id: groups[group_id]})
        print("\n" + "─" * 50)
        print(code)
        print("─" * 50 + "\n")
        try:
            context.window_manager.clipboard = code
            self.report({"INFO"}, "Copied to clipboard")
        except Exception:
            self.report({"INFO"}, "See console")
        return {"FINISHED"}


class FACADES_OT_CreateGroup(bpy.types.Operator):
    """Create a new facade group from the Create Facade form and place it in the scene"""
    bl_idname = "facades.create_group"
    bl_label  = "Create Facade"

    def execute(self, context):
        scene = context.scene
        cfg = {
            "name":       scene.fc_facade_name,
            "flags":      int(scene.fc_flags),
            "offset":     [round(scene.fc_offset_x, 2), round(scene.fc_offset_y, 2), round(scene.fc_offset_z, 2)],
            "end":        [round(scene.fc_end_x,    2), round(scene.fc_end_y,    2), round(scene.fc_end_z,    2)],
            "axis":       scene.fc_axis,
            "separator":  round(scene.fc_separator, 3),
            "sides":      [round(scene.fc_sides_x, 2), round(scene.fc_sides_y, 2), round(scene.fc_sides_z, 2)],
            "scale_auto": scene.fc_scale_auto,
            "scale":      round(scene.fc_scale, 3),
        }
        groups   = get_unique_groups()
        all_cfgs = list(groups.values()) + [cfg]
        try:
            place_facades_in_scene(all_cfgs)
            friendly = facade_name_to_friendly(scene.fc_facade_name)
            self.report({"INFO"}, f"Created facade group '{friendly}'")
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Failed to create facade: {exc}")
            return {"CANCELLED"}
        return {"FINISHED"}


class FACADES_OT_DeleteGroup(bpy.types.Operator):
    """Remove all scene objects belonging to the active facade group"""
    bl_idname = "facades.delete_group"
    bl_label  = "Delete Group"

    def execute(self, context):
        obj = context.active_object
        if not is_facade_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged facade")
            return {"CANCELLED"}
        gid       = obj.get(_FACADE_TAG)
        parents   = [o for o in get_facade_objects() if o.get(_FACADE_TAG) == gid]
        to_remove = list(parents)
        for p in parents:
            to_remove.extend(list(p.children))
        for o in to_remove:
            bpy.data.objects.remove(o, do_unlink=True)
        self.report({"INFO"}, f"Deleted {len(to_remove)} object(s) in group '{gid}'")
        return {"FINISHED"}


class FACADES_OT_LoadExternal(bpy.types.Operator):
    """Load and visualise facades from an existing binary .FCD file"""
    bl_idname = "facades.load_external"
    bl_label  = "Load External FCD"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.fcd;*.FCD", options={"HIDDEN"})

    def invoke(self, context, event):
        self.filepath = str(Folder.BASE) + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        from src.file_formats.facades.facades import Facades
        path = Path(self.filepath)
        if not path.exists():
            self.report({"ERROR"}, f"File not found: {path}")
            return {"CANCELLED"}

        with open(path, "rb") as f:
            raw_facades = Facades.read_all(f)

        # Each binary record is already one fully-expanded panel.
        # face = the end world-position of the panel (set by FacadeEditor.process as current_end).
        # We store it in "face_vec" so place_facades_in_scene can derive the
        # panel's facing direction (offset→face) without re-tiling via _panel_positions.
        cfg_list = []
        for fcd in raw_facades:
            name = fcd.name.rstrip("\x00")
            cfg_list.append({
                "name":       name,
                "flags":      fcd.flags,
                "offset":     [fcd.offset.x, fcd.offset.y, fcd.offset.z],
                "end":        [fcd.offset.x, fcd.offset.y, fcd.offset.z],  # start==end → _panel_positions gives n=1
                "face_vec":   [fcd.face.x,   fcd.face.y,   fcd.face.z],   # end world-pos for rotation
                "axis":       "x",
                "separator":  1.0,
                "sides":      [fcd.sides.x, fcd.sides.y, fcd.sides.z],
                "scale_auto": False,
                "scale":      fcd.scale,
            })

        place_facades_in_scene(cfg_list)
        self.report({"INFO"}, f"Loaded {len(cfg_list)} facade records from {path.name}")
        return {"FINISHED"}


class FACADES_OT_SaveFCD(bpy.types.Operator):
    """Write all facade groups to a binary .FCD file"""
    bl_idname = "facades.save_fcd"
    bl_label  = "Save FCD File"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.fcd;*.FCD", options={"HIDDEN"})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "CHICAGO.FCD"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        from src.file_formats.facades.editor import FacadeEditor
        from src.file_formats.facades.facades import Facades

        groups = get_unique_groups()
        if not groups:
            self.report({"WARNING"}, "No facade groups in scene — load or create facades first")
            return {"CANCELLED"}

        try:
            instances = FacadeEditor.process(list(groups.values()))
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to process facades: {exc}")
            return {"CANCELLED"}

        path = Path(self.filepath)
        Facades.write_all(path, instances)
        self.report({"INFO"}, f"Saved {len(instances)} facade instances to {path.name}")
        return {"FINISHED"}


FACADE_EDITOR_CLASSES = [
    FACADES_OT_Reload,
    FACADES_OT_Clear,
    FACADES_OT_SelectGroup,
    FACADES_OT_LoadIntoForm,
    FACADES_OT_ExportCode,
    FACADES_OT_ExportGroupCode,
    FACADES_OT_CreateGroup,
    FACADES_OT_DeleteGroup,
    FACADES_OT_LoadExternal,
    FACADES_OT_SaveFCD,
]

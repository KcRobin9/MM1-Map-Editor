import bpy
import json
import importlib
import math
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from src.constants.folder import Folder
from src.ui.console import ok, sep, item, suppress_stdout_matching


_FACADES_COLLECTION = "Facades"
_FACADE_TAG         = "mm_facade_group_id"     # group UUID — set ONLY on parent empties
_FACADE_CFG_TAG     = "mm_facade_config_json"  # serialized cfg — set ONLY on parent empties
_FACADE_PART_TAG    = "mm_facade_part"         # part label (FACADE_H/LEFT/RIGHT/TOP/BACK/GRND) — set ONLY on child meshes


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

def _build_flags_items() -> List[Tuple[str, str, str]]:
    from src.constants.facades import FcdFlags
    seen: Dict[int, str] = {}
    for attr, val in vars(FcdFlags).items():
        if attr.startswith("_") or not isinstance(val, int):
            continue
        if val not in seen or len(attr) > len(seen[val]):
            seen[val] = attr
    return sorted(
        [(str(val), name, f"0x{val:03X}  ({val})") for val, name in seen.items()],
        key=lambda x: int(x[0]),
    )


FACADE_FLAGS_ITEMS: List[Tuple[str, str, str]] = _build_flags_items()

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


def _is_group_id(val) -> bool:
    """Real group IDs start with 'facade_'. Filters out legacy scenes where
    children mistakenly stored part names like 'FACADE_H' under the same key."""
    return isinstance(val, str) and val.startswith("facade_")


def is_facade_obj(obj) -> bool:
    """True if obj is a tagged parent empty OR a child of one."""
    if obj is None:
        return False
    if _is_group_id(obj.get(_FACADE_TAG)):
        return True
    return obj.parent is not None and _is_group_id(obj.parent.get(_FACADE_TAG))


def _to_tagged_parent(obj):
    """Walk up to the tagged parent empty, or return obj if it is one. None if neither."""
    if obj is None:
        return None
    if _is_group_id(obj.get(_FACADE_TAG)):
        return obj
    if obj.parent is not None and _is_group_id(obj.parent.get(_FACADE_TAG)):
        return obj.parent
    return None


def get_unique_groups() -> Dict[str, dict]:
    """
    Return {group_id: config_dict} for every facade group in the scene.
    Group IDs are stable across rebuilds (live in cfg["_gid"]).
    """
    groups: Dict[str, dict] = {}
    for obj in get_facade_objects():
        gid = obj.get(_FACADE_TAG)
        if not _is_group_id(gid) or gid in groups:
            continue
        try:
            cfg = json.loads(obj.get(_FACADE_CFG_TAG, "{}"))
        except Exception:
            continue
        if cfg:
            groups[gid] = cfg
    return groups


def _ensure_gid(cfg: dict) -> str:
    """Return cfg['_gid'], minting a fresh UUID-based one if missing."""
    gid = cfg.get("_gid")
    if not gid:
        gid = f"facade_{uuid.uuid4().hex[:10]}"
        cfg["_gid"] = gid
    return gid


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


def _detect_dominant_axis(p0, p1) -> str:
    """Pick the axis along which |p1-p0| is largest. Defaults to 'x' on ties."""
    dx, dy, dz = abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), abs(p1[2] - p0[2])
    if dx >= dz and dx >= dy:
        return 'x'
    if dz >= dy:
        return 'z'
    return 'y'


# ── BMS loading helper ────────────────────────────────────────────────────────

_MESHES_FACADES = Folder.Resources.Editor.MeshesFacades

_BMS_VARIANTS = ("FACADE_H.BMS", "BLDG_H.BMS", "H.BMS", "FACADE_M.BMS", "M.BMS", "FACADE_L.BMS")
_LEFT_VARIANTS  = ("LEFT.BMS",)
_RIGHT_VARIANTS = ("RIGHT.BMS",)
_TOP_VARIANTS   = ("TOP_H.BMS", "TOP.BMS")
_BACK_VARIANTS  = ("BACK.BMS",)
_GRND_VARIANTS  = ("GRND_H.BMS", "GRND.BMS")

# FcdFlags.DT_BLDG / INST_INIT_FLAG_BUILDING — selects mmBuildingInstance render path
_DT_BLDG_FLAG = 0x004


def is_dt_cfg(cfg: dict) -> bool:
    return bool(int(cfg.get("flags", 0)) & _DT_BLDG_FLAG)


# FCD scales table — loaded once and cached
_FCD_SCALES_CACHE: Optional[Dict[str, float]] = None


def _load_fcd_scales() -> Dict[str, float]:
    """Load (and cache) the canonical scale table at FCD scales.txt."""
    global _FCD_SCALES_CACHE
    if _FCD_SCALES_CACHE is not None:
        return _FCD_SCALES_CACHE
    scales: Dict[str, float] = {}
    path = Folder.Resources.Editor.Facades / "FCD scales.txt"
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if ": " in line:
                    name, val = line.split(": ", 1)
                    try:
                        scales[name] = float(val)
                    except ValueError:
                        pass
    except FileNotFoundError:
        print(f"[Facade Editor] FCD scales file not found at {path}")
    _FCD_SCALES_CACHE = scales
    return scales


def _resolve_scale(cfg: dict) -> float:
    """
    If scale_auto (default True), look up canonical scale from FCD scales.txt;
    otherwise use the explicit cfg['scale']. Falls back to 1.0 on miss.
    """
    scale_auto = cfg.get("scale_auto", True)
    if scale_auto:
        scales = _load_fcd_scales()
        return float(scales.get(cfg.get("name", ""), float(cfg.get("scale", 1.0))))
    return float(cfg.get("scale", 1.0))


def _find_bms_variant(folder: Path, variants) -> Optional[Path]:
    for v in variants:
        p = folder / v
        if p.exists():
            return p
    return None


# ── Mesh cache: key = (absolute BMS path, shear) → cached Blender Mesh ────────
#
# A sheared variant is needed because Blender's matrix_world setter decomposes
# the assigned matrix into loc/rot/scale and drops any non-orthogonal part (see
# BKE_object_apply_mat4 → mat4_to_loc_rot_size). The game's facade matrix is
# *deliberately* sheared (m0 carries the Y tilt while m1 stays (0,1,0)), so to
# reproduce a tilted SHEAR-flag facade we bake that Y tilt into the mesh and
# leave the object's matrix orthonormal.

_BMS_MESH_CACHE: Dict[Tuple[str, int], "bpy.types.Mesh"] = {}

# Round shear to this many decimal places so panels with near-identical tilt
# share a single sheared mesh datablock.
_SHEAR_CACHE_PRECISION = 4


def _shear_y_key(shear_y: float) -> int:
    return int(round(shear_y * (10 ** _SHEAR_CACHE_PRECISION)))


def _apply_shear_to_mesh(mesh: "bpy.types.Mesh", shear_y: float) -> None:
    """
    Reproduce the m0.y shear directly on mesh vertices.
        game:    new_vy = old_vy + (dy/scale) * vx       (the matrix's shear)
        blender: new_vz = old_vz - shear_y    * vx       (after the X-flip in
                                                          _to_blender_pos)
    """
    if shear_y == 0.0:
        return
    for v in mesh.vertices:
        v.co.z -= shear_y * v.co.x
    mesh.update()


def _bms_cached_mesh(bms_file: Path, label: str, tex_folder, shear_y: float = 0.0) -> Optional["bpy.types.Mesh"]:
    """Return a Blender Mesh for `bms_file`, optionally with a baked Y shear."""
    key = (str(bms_file.resolve()).lower(), _shear_y_key(shear_y))
    cached = _BMS_MESH_CACHE.get(key)
    if cached is not None and cached.users >= 0 and cached.name in bpy.data.meshes:
        return cached

    from src.integrations.blender.modeling.meshes import (
        read_bms, build_blender_mesh, _apply_materials_to_mesh,
    )
    try:
        bms_data = read_bms(bms_file)
        label_suffix = f"_sh{key[1]:+d}" if shear_y != 0.0 else ""
        mesh = build_blender_mesh(f"{label}{label_suffix}", bms_data)
        if tex_folder and bms_data.get("texture_names"):
            with suppress_stdout_matching("Unable to find a suitable DXT compression"):
                _apply_materials_to_mesh(mesh, bms_data["texture_names"], tex_folder)
        mesh["bms_source_file"] = str(bms_file)
        ox, oy, oz = bms_data.get("mesh_offset", [0.0, 0.0, 0.0])
        mesh["_bl_offset"] = (-ox, oz, oy)
        _apply_shear_to_mesh(mesh, shear_y)
    except Exception as exc:
        item(f"BMS load failed ({bms_file.name}): {exc}")
        return None

    _BMS_MESH_CACHE[key] = mesh
    return mesh


def _invalidate_mesh_cache() -> None:
    stale = [k for k, m in _BMS_MESH_CACHE.items() if m.name not in bpy.data.meshes]
    for k in stale:
        del _BMS_MESH_CACHE[k]


def _add_child_obj(mesh, name: str, part: str, parent_obj, col):
    import mathutils
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.parent = parent_obj
    obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    obj.location = mesh.get("_bl_offset", (0.0, 0.0, 0.0))
    # Children get the part tag only — group-id / cfg-json keys live on the parent.
    obj[_FACADE_PART_TAG] = part
    return obj


def _facade_matrix_to_blender(
    start: Tuple[float, float, float],
    end:   Tuple[float, float, float],
    scale: float,
) -> Tuple["mathutils.Matrix", float]:
    """
    Port of MatrixFromPoints() from the game binary, split so Blender can
    actually render the result.

    Game matrix (per IDA disasm of `?MatrixFromPoints@@…`):
        m0 = (end-start).normalised() * (|end-start|/scale)    forward
        m1 = (0, 1, 0)                                          up
        m2 = m1 × m0_normalised   (in XZ plane, unit length)    right
        m3 = start                (NO Y clamping — verified in asm)

    Shear note. When start.y ≠ end.y the matrix is *sheared*: m0 carries a Y
    component but m1 stays (0,1,0), so m0·m1 ≠ 0. The game's renderer applies
    the Matrix34 directly to vertices, so the shear works. Blender, however,
    decomposes any matrix assigned to ``obj.matrix_world`` into loc + rot +
    scale (BKE_object_apply_mat4 → mat4_to_loc_rot_size) and *drops* the shear
    — which is the bug that flattens every tilted facade.

    The workaround: return an orthonormal matrix (m0 projected to the XZ
    plane, no Y) plus a separate ``shear_y`` factor that the caller bakes into
    the mesh vertices. End result matches the game.

    Returns:
        (mat4, shear_y) where applying the shear to each mesh vertex via
        ``new_vz_blender = old_vz_blender - shear_y * old_vx_blender`` and
        then transforming by ``mat4`` reproduces the game's full Matrix34.
    """
    import mathutils

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]

    dist_xz = (dx * dx + dz * dz) ** 0.5
    if scale == 0.0 or dist_xz < 1e-7:
        # Degenerate (zero-length wall or purely vertical drop). Place the
        # parent at start and skip the shear — the caller will see a stack
        # of meshes at the panel origin.
        loc = mathutils.Vector((start[0], -start[2], start[1]))
        mat = mathutils.Matrix.Identity(4)
        mat.translation = loc
        return mat, 0.0

    length_factor_xz = dist_xz / scale
    nx_xz = dx / dist_xz
    nz_xz = dz / dist_xz

    def g2b(gx, gy, gz):
        return (gx, -gz, gy)

    # Forward, up, right — all built with m0.y = 0 so the matrix is orthonormal.
    fwd_b = g2b(nx_xz * length_factor_xz, 0.0, nz_xz * length_factor_xz)
    up_b  = g2b(0.0, 1.0, 0.0)
    rgt_b = g2b(nz_xz, 0.0, -nx_xz)

    col_x = (-fwd_b[0], -fwd_b[1], -fwd_b[2])
    col_y = (-rgt_b[0], -rgt_b[1], -rgt_b[2])
    col_z = ( up_b[0],   up_b[1],   up_b[2])

    mat3 = mathutils.Matrix((
        (col_x[0], col_y[0], col_z[0]),
        (col_x[1], col_y[1], col_z[1]),
        (col_x[2], col_y[2], col_z[2]),
    ))

    loc = mathutils.Vector(g2b(start[0], start[1], start[2]))

    mat4 = mat3.to_4x4()
    mat4.translation = loc

    # Tilt that the matrix's m0.y *would* have applied, expressed in Blender
    # mesh-space. Derivation:
    #     game:    Δvy = (dy/scale) * vx
    #     mesh import (_to_blender_pos): vx_b = -vx_g, vz_b = vy_g
    #     →        Δvz_b = -(dy/scale) * vx_b
    shear_y = dy / scale
    return mat4, shear_y


def _dt_matrix_to_blender(
    start: Tuple[float, float, float],
    end:   Tuple[float, float, float],
    sides: Tuple[float, float, float],
) -> "mathutils.Matrix":
    """
    Port of mmBuildingInstance::Init() from the game binary.

    Used for DT## downtown-core buildings (flag 0x004 / INST_INIT_FLAG_BUILDING).
    Three explicit world points:
        m0 = (end   - start)   forward axis (length = |face - offset|)
        m1 = (0, 1, 0)         up axis (unit)
        m2 = (sides - start)   depth axis — sides is a 3D point, NOT (L,R,D)
        m3 = start             origin
    """
    import mathutils

    fx_g = end[0]   - start[0]
    fy_g = end[1]   - start[1]
    fz_g = end[2]   - start[2]
    sx_g = sides[0] - start[0]
    sy_g = sides[1] - start[1]
    sz_g = sides[2] - start[2]

    def g2b(gx, gy, gz):
        return (gx, -gz, gy)

    fwd_b = g2b(fx_g, fy_g, fz_g)
    up_b  = g2b(0.0, 1.0, 0.0)
    dep_b = g2b(sx_g, sy_g, sz_g)

    col_x = (-fwd_b[0], -fwd_b[1], -fwd_b[2])
    col_y = ( dep_b[0],  dep_b[1],  dep_b[2])
    col_z = ( up_b[0],   up_b[1],   up_b[2])

    mat3 = mathutils.Matrix((
        (col_x[0], col_y[0], col_z[0]),
        (col_x[1], col_y[1], col_z[1]),
        (col_x[2], col_y[2], col_z[2]),
    ))

    loc = mathutils.Vector(g2b(start[0], start[1], start[2]))
    mat4 = mat3.to_4x4()
    mat4.translation = loc
    return mat4


# ── Scene placement ───────────────────────────────────────────────────────────

class PlaceReport:
    """Aggregate counts so the caller can show a single toast."""
    __slots__ = ("placed", "missing_folder", "missing_main", "missing_names")

    def __init__(self):
        self.placed: int = 0
        self.missing_folder: int = 0
        self.missing_main: int = 0
        self.missing_names: set = set()

    def summary(self) -> str:
        msg = f"{self.placed} panel(s) placed"
        if self.missing_folder:
            msg += f", {self.missing_folder} missing BMS folder"
        if self.missing_main:
            msg += f", {self.missing_main} missing main mesh"
        if self.missing_names:
            preview = sorted(self.missing_names)[:5]
            extra = f" +{len(self.missing_names)-5} more" if len(self.missing_names) > 5 else ""
            msg += f"  ({', '.join(preview)}{extra})"
        return msg


def place_facades_in_scene(
    facade_cfgs: list,
    texture_folder=None,
) -> PlaceReport:
    """
    Place facade groups in the Blender scene. Each panel becomes a parent Empty
    at the panel's world position/rotation, with child mesh objects for each
    BMS part actually present on disk and gated by FcdFlags.

    Group IDs in cfg["_gid"] are preserved across calls; missing ones get minted.
    """
    if texture_folder is None:
        texture_folder = Folder.Resources.Editor.Textures

    col = _get_or_create_collection(_FACADES_COLLECTION)
    _clear_collection(col)
    _invalidate_mesh_cache()

    rep = PlaceReport()

    for cfg in facade_cfgs:
        gid    = _ensure_gid(cfg)
        name   = cfg.get('name', 'unknown')
        flags  = int(cfg.get('flags', 0))
        sides  = cfg.get('sides', [0.0, 0.0, 0.0])
        is_dt  = bool(flags & _DT_BLDG_FLAG)

        fcd_scale = _resolve_scale(cfg)
        panels    = _panel_positions(cfg)

        mesh_folder = (_MESHES_FACADES / name.upper()) if (_MESHES_FACADES / name.upper()).is_dir() else None

        # Mirror C++ side-flag gating; DT only renders FACADE + GRND.
        if is_dt:
            has_left = has_right = has_roof = has_back = False
        else:
            has_left  = bool(flags & 0x008)
            has_right = bool(flags & 0x010)
            has_roof  = bool(flags & 0x020)
            has_back  = bool(flags & 0x400)

        cfg_json = json.dumps(cfg)

        for pnl_idx, (game_start, game_end) in enumerate(panels):
            panel_name = f"{name}_{gid[-8:]}_{pnl_idx}"

            parent_obj = bpy.data.objects.new(panel_name, None)
            parent_obj.empty_display_type = "ARROWS"
            parent_obj.empty_display_size = 1.0
            col.objects.link(parent_obj)

            if is_dt:
                mat = _dt_matrix_to_blender(game_start, game_end,
                                            tuple(float(s) for s in sides))
                # DT buildings render via mmBuildingInstance which stores a
                # full Matrix34 — no equivalent of mmYInstance's shear, so we
                # keep the current behaviour and don't bake anything.
                shear_y = 0.0
            else:
                mat, shear_y = _facade_matrix_to_blender(
                    game_start, game_end, fcd_scale
                )
            parent_obj.matrix_world = mat

            parent_obj[_FACADE_TAG]       = gid
            parent_obj[_FACADE_CFG_TAG]   = cfg_json
            parent_obj["mm_facade_name"]  = name
            parent_obj["mm_facade_panel"] = pnl_idx

            if mesh_folder is None:
                rep.missing_folder += 1
                rep.missing_names.add(name)
                continue

            main_bms = _find_bms_variant(mesh_folder, _BMS_VARIANTS)
            if main_bms:
                m = _bms_cached_mesh(main_bms, f"{name}_H", texture_folder, shear_y)
                if m:
                    _add_child_obj(m, f"{panel_name}_H", "FACADE_H", parent_obj, col)
                    rep.placed += 1
            else:
                rep.missing_main += 1
                rep.missing_names.add(name)

            grnd_bms = _find_bms_variant(mesh_folder, _GRND_VARIANTS)
            if grnd_bms:
                m = _bms_cached_mesh(grnd_bms, f"{name}_GRND", texture_folder, shear_y)
                if m:
                    _add_child_obj(m, f"{panel_name}_GRND", "GRND", parent_obj, col)

            if has_left:
                left_bms = _find_bms_variant(mesh_folder, _LEFT_VARIANTS)
                if left_bms:
                    m = _bms_cached_mesh(left_bms, f"{name}_LEFT", texture_folder, shear_y)
                    if m:
                        _add_child_obj(m, f"{panel_name}_LEFT", "LEFT", parent_obj, col)

            if has_right:
                right_bms = _find_bms_variant(mesh_folder, _RIGHT_VARIANTS)
                if right_bms:
                    m = _bms_cached_mesh(right_bms, f"{name}_RIGHT", texture_folder, shear_y)
                    if m:
                        _add_child_obj(m, f"{panel_name}_RIGHT", "RIGHT", parent_obj, col)

            if has_roof:
                top_bms = _find_bms_variant(mesh_folder, _TOP_VARIANTS)
                if top_bms:
                    m = _bms_cached_mesh(top_bms, f"{name}_TOP", texture_folder, shear_y)
                    if m:
                        _add_child_obj(m, f"{panel_name}_TOP", "TOP", parent_obj, col)

            if has_back:
                back_bms = _find_bms_variant(mesh_folder, _BACK_VARIANTS)
                if back_bms:
                    m = _bms_cached_mesh(back_bms, f"{name}_BACK", texture_folder, shear_y)
                    if m:
                        _add_child_obj(m, f"{panel_name}_BACK", "BACK", parent_obj, col)

    unique_names = list(dict.fromkeys(cfg.get("name", "") for cfg in facade_cfgs))
    total_panels = sum(len(_panel_positions(cfg)) for cfg in facade_cfgs)
    name_list    = ", ".join(unique_names)
    ok(f"Facades placed in scene{sep()}{total_panels} panel(s)  ·  {len(unique_names)} unique")
    if unique_names:
        item(name_list)
    if rep.missing_names:
        item(f"Missing BMS: {', '.join(sorted(rep.missing_names))}")
    return rep


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
    for i, (gid, cfg) in enumerate(sorted(groups.items(), key=lambda x: x[0])):
        var = f"facade_{i}"
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
        cfg["_gid"]       = group_id
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


def _resolve_active_group_id(context) -> str:
    """Tag of active object's tagged parent, else scene's stored id as fallback."""
    obj = context.active_object
    parent = _to_tagged_parent(obj)
    if parent is not None:
        return parent.get(_FACADE_TAG, "")
    return getattr(context.scene, "fe_active_group_id", "")


# ── Operators ─────────────────────────────────────────────────────────────────

class FACADES_OT_Reload(bpy.types.Operator):
    """Reload facades from USER/facades.py and re-place in the scene"""
    bl_idname = "facades.reload"
    bl_label  = "Reload from facades.py"

    def execute(self, context):
        import src.USER.facades as _mod
        importlib.reload(_mod)
        cfgs = [dict(c) for c in _mod.facade_list]
        for c in cfgs:
            c.pop("_gid", None)
        rep = place_facades_in_scene(cfgs)
        self.report({"INFO"}, f"USER reload: {rep.summary()}")
        return {"FINISHED"}


class FACADES_OT_Clear(bpy.types.Operator):
    """Remove all facades from the scene without reloading"""
    bl_idname = "facades.clear"
    bl_label  = "Clear Facades"

    def execute(self, context):
        col = _get_or_create_collection(_FACADES_COLLECTION)
        _clear_collection(col)
        _invalidate_mesh_cache()
        context.scene.fe_active_group_id = ""
        self.report({"INFO"}, "Facades cleared")
        return {"FINISHED"}


class FACADES_OT_SelectGroup(bpy.types.Operator):
    """Select all objects belonging to the same facade group as the active object"""
    bl_idname = "facades.select_group"
    bl_label  = "Select Group"

    def execute(self, context):
        gid = _resolve_active_group_id(context)
        if not gid:
            self.report({"WARNING"}, "Active object is not a tagged facade")
            return {"CANCELLED"}
        bpy.ops.object.select_all(action="DESELECT")
        first = None
        count = 0
        for o in get_facade_objects():
            if o.get(_FACADE_TAG) == gid:
                o.select_set(True)
                first = first or o
                count += 1
        if first:
            context.view_layer.objects.active = first
        self.report({"INFO"}, f"Selected {count} object(s) in group '{gid}'")
        return {"FINISHED"}


class FACADES_OT_LoadIntoForm(bpy.types.Operator):
    """Populate the edit form from the active facade object's stored config"""
    bl_idname = "facades.load_into_form"
    bl_label  = "Edit"

    def execute(self, context):
        tagged = _to_tagged_parent(context.active_object)
        if tagged is None:
            self.report({"WARNING"}, "Active object is not a tagged facade")
            return {"CANCELLED"}
        if not load_form_from_obj(context.scene, tagged):
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
            self.report({"INFO"}, f"Exported {len(groups)} group(s) — copied to clipboard")
        except Exception:
            self.report({"INFO"}, f"Exported {len(groups)} group(s) — see console")
        return {"FINISHED"}


class FACADES_OT_ExportGroupCode(bpy.types.Operator):
    """Export Python code for only the currently active facade group"""
    bl_idname = "facades.export_group_code"
    bl_label  = "Copy Group as Code"

    def execute(self, context):
        group_id = _resolve_active_group_id(context)
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
        new_gid = _ensure_gid(cfg)
        groups = get_unique_groups()
        all_cfgs = list(groups.values()) + [cfg]
        try:
            place_facades_in_scene(all_cfgs)
            scene.fe_active_group_id = new_gid
            friendly = facade_name_to_friendly(scene.fc_facade_name)
            self.report({"INFO"}, f"Created facade group '{friendly}'")
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Failed to create facade: {exc}")
            return {"CANCELLED"}
        return {"FINISHED"}


class FACADES_OT_DuplicateGroup(bpy.types.Operator):
    """Duplicate the active facade group, offsetting its position along its axis"""
    bl_idname = "facades.duplicate_group"
    bl_label  = "Duplicate Group"

    def execute(self, context):
        gid = _resolve_active_group_id(context)
        if not gid:
            self.report({"WARNING"}, "No active group — click 'Edit' on a facade first")
            return {"CANCELLED"}
        groups = get_unique_groups()
        if gid not in groups:
            self.report({"ERROR"}, f"Group '{gid}' not found")
            return {"CANCELLED"}

        src_cfg = groups[gid]
        new_cfg = json.loads(json.dumps(src_cfg))   # deep copy
        new_cfg.pop("_gid", None)
        new_gid = _ensure_gid(new_cfg)

        # Offset both endpoints along the cfg's axis (or +X if DT) so the copy
        # is visible. Distance = 1.5× the wall length, min 10.
        axis_idx = {"x": 0, "y": 1, "z": 2}.get(new_cfg.get("axis", "x"), 0)
        off = list(new_cfg.get("offset", [0.0, 0.0, 0.0]))
        end = list(new_cfg.get("end",    [0.0, 0.0, 0.0]))
        span = abs(end[axis_idx] - off[axis_idx]) if not is_dt_cfg(new_cfg) else 0.0
        bump = max(span * 1.5, 10.0)
        off[axis_idx] += bump
        end[axis_idx] += bump
        new_cfg["offset"] = off
        new_cfg["end"]    = end

        all_cfgs = list(groups.values()) + [new_cfg]
        try:
            place_facades_in_scene(all_cfgs)
            context.scene.fe_active_group_id = new_gid
            self.report({"INFO"}, f"Duplicated → '{new_gid}' (offset by {bump:.1f})")
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Failed to duplicate: {exc}")
            return {"CANCELLED"}
        return {"FINISHED"}


class FACADES_OT_DeleteGroup(bpy.types.Operator):
    """Remove all scene objects belonging to the active facade group"""
    bl_idname = "facades.delete_group"
    bl_label  = "Delete Group"

    def execute(self, context):
        gid = _resolve_active_group_id(context)
        if not gid:
            self.report({"WARNING"}, "No active group selected")
            return {"CANCELLED"}
        parents   = [o for o in get_facade_objects() if o.get(_FACADE_TAG) == gid]
        to_remove = list(parents)
        for p in parents:
            to_remove.extend(list(p.children))
        for o in to_remove:
            bpy.data.objects.remove(o, do_unlink=True)
        if context.scene.fe_active_group_id == gid:
            context.scene.fe_active_group_id = ""
        self.report({"INFO"}, f"Deleted {len(to_remove)} object(s) in group '{gid}'")
        return {"FINISHED"}


class FACADES_OT_BakeFromCursor(bpy.types.Operator):
    """Set the form's Offset (or End) to the 3D cursor's game-space position"""
    bl_idname = "facades.bake_from_cursor"
    bl_label  = "Use Cursor as Offset"

    target: bpy.props.EnumProperty(
        items=[("offset", "Offset", ""), ("end", "End", "")],
        default="offset",
    )
    form: bpy.props.EnumProperty(
        items=[("create", "Create", ""), ("edit", "Edit", "")],
        default="create",
    )

    def execute(self, context):
        # Blender (bx, by, bz) → game (-bx, bz, by)  (inverse of g2b)
        bx, by, bz = context.scene.cursor.location
        gx, gy, gz = -bx, bz, by
        prefix = "fc_" if self.form == "create" else "fe_"
        target = self.target
        setattr(context.scene, f"{prefix}{target}_x", round(gx, 2))
        setattr(context.scene, f"{prefix}{target}_y", round(gy, 2))
        setattr(context.scene, f"{prefix}{target}_z", round(gz, 2))
        self.report({"INFO"}, f"{self.form}.{target} ← cursor ({gx:.2f}, {gy:.2f}, {gz:.2f})")
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

        # Each binary record is one fully-expanded panel. Map directly into the
        # standard offset/end form so live-editing the panel's start or end
        # updates the rendered position. Separator=length+ε keeps n_panels=1.
        cfg_list = []
        for fcd in raw_facades:
            name = fcd.name.rstrip("\x00")
            offset = (fcd.offset.x, fcd.offset.y, fcd.offset.z)
            end    = (fcd.face.x,   fcd.face.y,   fcd.face.z)
            axis   = _detect_dominant_axis(offset, end)
            length = max(abs(end[0]-offset[0]), abs(end[1]-offset[1]), abs(end[2]-offset[2]))
            cfg_list.append({
                "name":       name,
                "flags":      fcd.flags,
                "offset":     [offset[0], offset[1], offset[2]],
                "end":        [end[0],    end[1],    end[2]],
                "axis":       axis,
                "separator":  max(length, 0.01) + 1e-3,
                "sides":      [fcd.sides.x, fcd.sides.y, fcd.sides.z],
                "scale_auto": False,
                "scale":      fcd.scale,
            })

        rep = place_facades_in_scene(cfg_list)
        self.report({"INFO"}, f"Loaded {len(cfg_list)} records from {path.name} — {rep.summary()}")
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
    FACADES_OT_DuplicateGroup,
    FACADES_OT_DeleteGroup,
    FACADES_OT_BakeFromCursor,
    FACADES_OT_LoadExternal,
    FACADES_OT_SaveFCD,
]

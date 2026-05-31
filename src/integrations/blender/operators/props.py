import bpy
import json
import math
import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.constants.folder import Folder
from src.constants.props import BangerFlags
from src.constants.file_formats import AxisRef
from src.constants.constants import HUGE, CURRENT_TIME_FORMATTED
from src.constants.props_orientation import PROP_ORIENTATION_OFFSET
from src.integrations.blender.modeling.props import place_props_in_scene, _find_prop_folder

_PROPS_COLLECTION = "Props"

# ── Prop name ↔ friendly label tables (built once at import) ──────────────────

def _build_prop_name_items() -> List[Tuple[str, str, str]]:
    """
    Return [(game_id, "Friendly Label", "Prop.CONST_NAME"), ...]
    sorted by friendly label, with PlayerCar entries appended.
    """
    items = []

    from src.constants.props import Prop
    for attr, val in sorted(vars(Prop).items()):
        if attr.startswith("_") or not isinstance(val, str):
            continue
        friendly = attr.replace("_", " ").title()    # BRIDGE_SLIM → "Bridge Slim"
        const    = f"Prop.{attr}"
        items.append((val, friendly, const))

    try:
        from src.constants.vehicles import PlayerCar
        for attr, val in sorted(vars(PlayerCar).items()):
            if attr.startswith("_") or not isinstance(val, str):
                continue
            friendly = "Car: " + attr.replace("_", " ").title()
            const    = f"PlayerCar.{attr}"
            items.append((val, friendly, const))
    except ImportError:
        pass

    return items


PROP_NAME_ITEMS: List[Tuple[str, str, str]] = _build_prop_name_items()

# Variants used by the Replace tool's dropdowns
PROP_NAME_ITEMS_FROM = [("__ALL__", "ALL", "Replace every prop type in the scene")] + PROP_NAME_ITEMS
PROP_NAME_ITEMS_TO   = PROP_NAME_ITEMS + [("__RANDOM__", "RANDOM", "Assign a random prop type to each matched group")]


# ── Custom-city props (community maps) ────────────────────────────────────────

def _build_custom_prop_items() -> Dict[str, List[Tuple[str, str, str]]]:
    """city folder → [(game_id, 'PREFIX: Friendly', 'Catalogue.ATTR'), ...]."""
    from src.constants.custom_props import CUSTOM_CITIES

    by_city: Dict[str, List[Tuple[str, str, str]]] = {}
    for folder, city in CUSTOM_CITIES.items():
        cat = city.catalogue
        items = []
        for attr, val in sorted(vars(cat).items()):
            if attr.startswith("_") or not isinstance(val, str):
                continue
            friendly = f"{city.definition.prefix}: " + attr.replace("_", " ").title()
            items.append((val, friendly, f"{cat.__name__}.{attr}"))
        by_city[folder] = items
    return by_city


CUSTOM_PROP_ITEMS: Dict[str, List[Tuple[str, str, str]]] = _build_custom_prop_items()


def _build_custom_city_items() -> List[Tuple[str, str, str]]:
    """Dropdown selector: NONE + each custom city by its friendly name."""
    from src.constants.custom_props import CUSTOM_CITIES

    items = [("NONE", "Chicago / Stock", "Show the stock props (Chicago and shared base-game props)")]
    for folder, city in CUSTOM_CITIES.items():
        if not city.prop_ids:   # texture-only cities (e.g. Paulville) have no props to list
            continue
        items.append((folder, city.definition.name, f"Show custom props from {city.definition.name}"))
    return items


CUSTOM_CITY_ITEMS: List[Tuple[str, str, str]] = _build_custom_city_items()

# Cache the per-city merged item lists so Blender keeps the string refs alive.
_PROP_ENUM_CACHE: Dict[str, List[Tuple[str, str, str]]] = {}


def prop_name_enum_items(self, context):
    """Dynamic dropdown items: stock props when no city is selected, otherwise
    ONLY the chosen custom city's props (keeps the menu small)."""
    folder = getattr(context.scene, "pe_custom_city", "NONE") if context else "NONE"
    if folder not in _PROP_ENUM_CACHE:
        _PROP_ENUM_CACHE[folder] = PROP_NAME_ITEMS if folder == "NONE" else CUSTOM_PROP_ITEMS.get(folder, [])
    return _PROP_ENUM_CACHE[folder]


# Fast reverse lookup: game_id → const string (e.g. "tpdrawbridge04" → "Prop.BRIDGE_SLIM")
_GAME_TO_CONST: Dict[str, str] = {item[0]: item[2] for item in PROP_NAME_ITEMS}
# game_id → friendly label  (includes custom props for nice panel labels)
_GAME_TO_FRIENDLY: Dict[str, str] = {item[0]: item[1] for item in PROP_NAME_ITEMS}
for _items in CUSTOM_PROP_ITEMS.values():
    for _id, _friendly, _const in _items:
        _GAME_TO_FRIENDLY[_id] = _friendly
        _GAME_TO_CONST[_id]    = _const


def prop_name_to_const(name: str) -> str:
    """'tpdrawbridge04'  →  'Prop.BRIDGE_SLIM'  (fallback: quoted string)"""
    return _GAME_TO_CONST.get(name, f'"{name}"')


def prop_name_to_friendly(name: str) -> str:
    """'tpdrawbridge04'  →  'Bridge Slim'  (fallback: raw name)"""
    return _GAME_TO_FRIENDLY.get(name, name)


# ── Banger flag enum items + helpers (built once at import) ────────────────────

_BANGER_FLAG_PRESETS: List[Tuple[str, int, str]] = [
    ("BREAKABLE",       BangerFlags.BREAKABLE,       "Standard street prop — breaks when hit, not drivable"),
    ("BREAKABLE_GLOW",  BangerFlags.BREAKABLE_GLOW,  "Breakable + glow mesh (street lights)"),
    ("DRIVABLE_SOLID",  BangerFlags.DRIVABLE_SOLID,  "Drivable solid surface (terrain) — will NOT break"),
    ("STATIC_BUILDING", BangerFlags.STATIC_BUILDING, "Static building/wall — solid, not a banger"),
]

# Blender EnumProperty items: (id=str(int_value), label, description)
BANGER_FLAG_ITEMS: List[Tuple[str, str, str]] = [
    (str(val), name.replace("_", " ").title(), f"{desc}   (0x{val:X})")
    for name, val, desc in _BANGER_FLAG_PRESETS
]

_FLAG_INT_TO_CONST: Dict[int, str] = {val: name for name, val, _ in _BANGER_FLAG_PRESETS}


def banger_flags_to_const(flags_val: int) -> str:
    """Normalized flag int → 'BangerFlags.NAME' for code export (fallback: int)."""
    name = _FLAG_INT_TO_CONST.get(BangerFlags.normalize(flags_val))
    return f"BangerFlags.{name}" if name else str(flags_val)


# ── Label / display helpers ───────────────────────────────────────────────────

_ROTATION_LABELS = {
    0.01:   "NORTH",
    45.0:   "NORTH_EAST",
    90.0:   "EAST",
    135.0:  "SOUTH_EAST",
    179.99: "SOUTH",
    -135.0: "SOUTH_WEST",
    -90.0:  "WEST",
    -45.0:  "NORTH_WEST",
}


def rotation_label(angle: float) -> str:
    return _ROTATION_LABELS.get(float(angle), f"{angle:.2f}°")


def separator_label(sep: Any) -> str:
    if isinstance(sep, dict) and sep.get("__type__") == "axis":
        axis = sep["axis"].capitalize()
        off  = sep.get("offset", 0.0)
        if off:
            sign = "+" if off > 0 else "-"
            return f"Axis.{axis} {sign} {abs(off)}"
        return f"Axis.{axis}"
    try:
        return f"{float(sep):.2f}"
    except (TypeError, ValueError):
        return str(sep)


# ── Serialization helpers ─────────────────────────────────────────────────────

def _serialize_config(config: dict) -> str:
    serializable = {}
    for k, v in config.items():
        if hasattr(v, "axis") and hasattr(v, "resolve"):   # AxisRef
            serializable[k] = {"__type__": "axis", "axis": v.axis, "offset": float(v.offset)}
        elif isinstance(v, (tuple, list)) and k in ("offset", "end"):
            serializable[k] = list(v)
        elif isinstance(v, (tuple, list)) and k == "area":
            serializable[k] = [list(p) for p in v]
        elif isinstance(v, (tuple, list)):
            serializable[k] = list(v)
        else:
            serializable[k] = v
    return json.dumps(serializable)


def _deserialize_separator(sep_val: Any) -> Any:
    if isinstance(sep_val, dict) and sep_val.get("__type__") == "axis":
        return AxisRef(sep_val["axis"], sep_val.get("offset", 0.0))
    return sep_val


def _deserialize_config(cfg: dict) -> dict:
    result = {}
    for k, v in cfg.items():
        if k == "separator":
            result[k] = _deserialize_separator(v)
        elif k in ("offset", "end") and isinstance(v, list):
            result[k] = tuple(float(x) for x in v)
        elif k == "area" and isinstance(v, list):
            result[k] = [tuple(float(x) for x in p) for p in v]
        elif k == "name" and isinstance(v, list):
            result[k] = list(v)
        else:
            result[k] = v
    return result


# ── Scene / collection access ─────────────────────────────────────────────────

def get_prop_objects() -> List[bpy.types.Object]:
    if _PROPS_COLLECTION not in bpy.data.collections:
        return []
    return list(bpy.data.collections[_PROPS_COLLECTION].objects)


def is_prop_obj(obj) -> bool:
    return obj is not None and "mm_prop_group_id" in obj


def get_unique_groups() -> Dict[str, Tuple[str, dict]]:
    groups: Dict[str, Tuple[str, dict]] = {}
    for obj in get_prop_objects():
        gid = obj.get("mm_prop_group_id")
        if gid and gid not in groups:
            try:
                cfg   = json.loads(obj.get("mm_prop_config_json", "{}"))
                ptype = obj.get("mm_prop_type", "fixed")
                if ptype != "random" and "area" in cfg:
                    ptype = "random"
                groups[gid] = (ptype, cfg)
            except Exception:
                pass
    return groups


def _sorted_fixed(groups: Dict) -> List[Tuple[str, dict]]:
    def _key(k):
        parts = k.split("_")
        return int(parts[-1]) if parts[-1].isdigit() else 0
    return sorted(
        [(k, cfg) for k, (t, cfg) in groups.items() if t == "fixed"],
        key=lambda x: _key(x[0]),
    )


def _sorted_random(groups: Dict) -> List[Tuple[str, dict]]:
    def _key(k):
        parts = k.split("_")
        return int(parts[-1]) if parts[-1].isdigit() else 0
    return sorted(
        [(k, cfg) for k, (t, cfg) in groups.items() if t == "random"],
        key=lambda x: _key(x[0]),
    )


def _rebuild_lists(groups: Dict) -> Tuple[list, list]:
    prop_list    = [_deserialize_config(cfg) for _, cfg in _sorted_fixed(groups)]
    random_props = [_deserialize_config(cfg) for _, cfg in _sorted_random(groups)]
    return prop_list, random_props


# ── Coordinate helpers ────────────────────────────────────────────────────────

def blender_to_game(bl_x: float, bl_y: float, bl_z: float) -> Tuple[float, float, float]:
    """Blender (x, y, z) → game (x, height, z).  Inverse of game(x,y,z)→blender(x,-z,y)"""
    return (bl_x, bl_z, -bl_y)


# ── Code generation ───────────────────────────────────────────────────────────

def _fmt_offset(vals) -> str:
    x, y, z = [float(v) for v in vals]
    return f"({x:.2f}, {y:.2f}, {z:.2f})"


def _fmt_separator(sep: Any) -> str:
    if isinstance(sep, dict) and sep.get("__type__") == "axis":
        axis = sep["axis"].capitalize()
        off  = sep.get("offset", 0.0)
        if off:
            sign = "+" if off > 0 else "-"
            return f"Axis.{axis} {sign} {abs(off):.2f}"
        return f"Axis.{axis}"
    try:
        return f"{float(sep):.2f}"
    except (TypeError, ValueError):
        return str(sep)


def _emit_fixed_config(lines: list, cfg: dict) -> None:
    offset = cfg.get("offset", [0, 0, 0])
    lines.append(f'    "offset": {_fmt_offset(offset)},')

    if "end" in cfg:
        lines.append(f'    "end": {_fmt_offset(cfg["end"])},')

    name = cfg.get("name", "")
    if isinstance(name, list):
        name_str = ", ".join(prop_name_to_const(n) for n in name)
        lines.append(f'    "name": [{name_str}],')
    else:
        lines.append(f'    "name": {prop_name_to_const(name)},')

    if "angle" in cfg and cfg["angle"] is not None:
        angle = cfg["angle"]
        label = rotation_label(float(angle))
        if label in _ROTATION_LABELS.values():
            lines.append(f'    "angle": Rotation.{label},')
        else:
            lines.append(f'    "angle": {float(angle):.2f},')

    if "separator" in cfg:
        lines.append(f'    "separator": {_fmt_separator(cfg["separator"])},')

    _emit_flags(lines, cfg)

    if cfg.get("race"):
        race_strs = ", ".join(f"RaceModeNum.{r}" for r in cfg["race"])
        lines.append(f'    "race": [{race_strs}],')


def _emit_flags(lines: list, cfg: dict) -> None:
    """Emit a "flags" entry only when it differs from the default (keeps output clean)."""
    flags = cfg.get("flags")
    if flags is None or int(flags) == BangerFlags.DEFAULT:
        return
    lines.append(f'    "flags": {banger_flags_to_const(int(flags))},')


def _emit_random_config(lines: list, cfg: dict) -> None:
    name = cfg.get("name", "")
    if isinstance(name, list):
        if len(name) > 5:
            chunks = [name[i:i+5] for i in range(0, len(name), 5)]
            lines.append('    "name": [')
            for chunk in chunks:
                lines.append(f'        {", ".join(prop_name_to_const(n) for n in chunk)},')
            lines.append('    ],')
        else:
            name_str = ", ".join(prop_name_to_const(n) for n in name)
            lines.append(f'    "name": [{name_str}],')
    else:
        lines.append(f'    "name": {prop_name_to_const(name)},')

    if "seed" in cfg:
        lines.append(f'    "seed": {cfg["seed"]},')
    if "count" in cfg:
        lines.append(f'    "count": {cfg["count"]},')
    if "num_props" in cfg:
        lines.append(f'    "num_props": {cfg["num_props"]},')

    if "area" in cfg:
        area = cfg["area"]
        p1, p2 = area[0], area[1]
        lines.append(f'    "area": ({_fmt_offset(p1)}, {_fmt_offset(p2)}),')

    if "separator" in cfg:
        lines.append(f'    "separator": {_fmt_separator(cfg["separator"])},')

    _emit_flags(lines, cfg)

    if cfg.get("race"):
        race_strs = ", ".join(f"RaceModeNum.{r}" for r in cfg["race"])
        lines.append(f'    "race": [{race_strs}],')


def generate_python_code(groups: Dict) -> str:
    lines = [
        "# Generated by Prop Editor",
        "from src.constants.props import Prop, BangerFlags",
        "from src.constants.vehicles import PlayerCar",
        "from src.constants.file_formats import Axis",
        "from src.game.waypoints.constants import Rotation",
        "from src.game.races.constants import RaceModeNum",
        "",
    ]

    prop_var_names   = []
    random_var_names = []

    for gid, cfg in _sorted_fixed(groups):
        var = f"prop_{gid.replace('fixed_', '')}"
        prop_var_names.append(var)
        lines.append(f"{var} = {{")
        _emit_fixed_config(lines, cfg)
        lines.append("}")
        lines.append("")

    # Always emit prop_list (even empty) so the file stays a drop-in replacement
    # for USER/props/props.py, which the pipeline imports by name.
    lines.append(f"prop_list = [{', '.join(prop_var_names)}]")
    lines.append("")

    for gid, cfg in _sorted_random(groups):
        var = f"random_{gid.replace('random_', '')}"
        random_var_names.append(var)
        lines.append(f"{var} = {{")
        _emit_random_config(lines, cfg)
        lines.append("}")
        lines.append("")

    lines.append(f"random_props = [{', '.join(random_var_names)}]")

    code = "\n".join(lines)

    # Inject custom-prop catalogue imports when their constants are referenced
    from src.constants.custom_props import CUSTOM_CITIES
    extra = [f"from {c.catalogue.__module__} import {c.catalogue.__name__}"
             for c in CUSTOM_CITIES.values() if f"{c.catalogue.__name__}." in code]
    if extra:
        anchor = "from src.constants.props import Prop, BangerFlags\n"
        code = code.replace(anchor, anchor + "\n".join(extra) + "\n", 1)

    return code


def _code_from_lists(prop_list: list, random_props: list) -> str:
    """Generate Prop Editor code from raw prop_list / random_props (not scene groups)."""
    groups: Dict[str, Tuple[str, dict]] = {}
    for i, cfg in enumerate(prop_list):
        groups[f"fixed_{i}"] = ("fixed", cfg)
    for i, cfg in enumerate(random_props):
        groups[f"random_{i}"] = ("random", cfg)
    return generate_python_code(groups)


# ── Row consolidation (collapse evenly-spaced runs into offset+end+separator) ──

def _consolidate_rows(prop_list: list, min_run: int = 4, max_gap: float = 45.0,
                      perp_tol: float = 0.6, y_tol: float = 0.05) -> list:
    """
    Collapse collinear, evenly-spaced runs of identical props into a single
    {offset, end, separator} row config. Effectively lossless: feeding the row
    back through BangerEditor.add_multiple reproduces the original point
    positions to within ~0.01 units (measured 0.008 max on Chicago).

    Props are matched only when they share name, angle (0.1° bucket) and flags,
    sit at the same height (within y_tol — rows are emitted flat, so members must
    be coplanar to stay lossless), and are evenly spaced along a line within
    tolerance. Anything that doesn't form a run of >= min_run stays an individual
    prop. Configs that already carry an "end" (existing rows) pass through
    untouched.
    """
    passthrough, singles = [], []
    for cfg in prop_list:
        (passthrough if ("end" in cfg or "offset" not in cfg) else singles).append(cfg)

    buckets: Dict[tuple, list] = {}
    for cfg in singles:
        key = (cfg.get("name"),
               round(float(cfg.get("angle", 0.0)), 1),
               int(cfg.get("flags", BangerFlags.DEFAULT)))
        buckets.setdefault(key, []).append(cfg)

    result = list(passthrough)

    for (name, angle, flags), items in buckets.items():
        coords = [(float(c["offset"][0]), float(c["offset"][1]), float(c["offset"][2])) for c in items]
        n = len(items)
        used = [False] * n

        # Spatial hash on the XZ plane for O(1) neighbour lookups.
        cell = 1.0
        grid: Dict[tuple, list] = {}
        for idx, (x, _y, z) in enumerate(coords):
            grid.setdefault((int(x // cell), int(z // cell)), []).append(idx)

        def _near(tx: float, tz: float, ty: float, run: set) -> int:
            cx, cz = int(tx // cell), int(tz // cell)
            best, best_d = -1, perp_tol
            for ox in (-1, 0, 1):
                for oz in (-1, 0, 1):
                    for m in grid.get((cx + ox, cz + oz), ()):
                        if used[m] or m in run or abs(coords[m][1] - ty) > y_tol:
                            continue
                        d = math.hypot(coords[m][0] - tx, coords[m][2] - tz)
                        if d <= best_d:
                            best, best_d = m, d
            return best

        order = sorted(range(n), key=lambda k: (coords[k][0], coords[k][2]))

        for i in order:
            if used[i]:
                continue
            xi, yi, zi = coords[i]

            # Candidate seeds: nearby unused points (cap the search for speed).
            neighbours = []
            ci, cj = int(xi // cell), int(zi // cell)
            span = int(max_gap // cell) + 1
            for ox in range(-span, span + 1):
                for oz in range(-span, span + 1):
                    for m in grid.get((ci + ox, cj + oz), ()):
                        if m == i or used[m]:
                            continue
                        sep = math.hypot(coords[m][0] - xi, coords[m][2] - zi)
                        if 0.5 < sep <= max_gap:
                            neighbours.append((sep, m))
            neighbours.sort(key=lambda t: t[0])

            best_run, best_dir, best_sep = None, None, None
            for sep, j in neighbours[:16]:
                ux, uz = (coords[j][0] - xi) / sep, (coords[j][2] - zi) / sep
                run = [i]
                k = 1
                while True:
                    found = _near(xi + ux * sep * k, zi + uz * sep * k, yi, set(run))
                    if found == -1:
                        break
                    run.append(found)
                    k += 1
                if best_run is None or len(run) > len(best_run):
                    best_run, best_dir, best_sep = run, (ux, uz), sep

            if best_run is not None and len(best_run) >= min_run:
                for m in best_run:
                    used[m] = True
                count = len(best_run)
                ux, uz = best_dir
                # diag = (count + 0.5) * sep keeps int(diag/sep) == count exactly.
                ex = xi + ux * best_sep * (count + 0.5)
                ez = zi + uz * best_sep * (count + 0.5)
                result.append({
                    "name": name,
                    "offset": (round(xi, 2), round(yi, 2), round(zi, 2)),
                    "end": (round(ex, 2), round(yi, 2), round(ez, 2)),
                    "separator": round(best_sep, 3),
                    "angle": angle,
                    "flags": flags,
                })
            else:
                used[i] = True
                result.append({
                    "name": name,
                    "offset": (round(xi, 2), round(yi, 2), round(zi, 2)),
                    "angle": angle,
                    "flags": flags,
                })

    return result


# ── Auto-apply logic (called by form update callbacks) ────────────────────────

_APPLYING  = False   # re-entry guard
_TIMER_PENDING = False   # prevents stacking deferred re-place calls


def _do_place(scene_name: str) -> None:
    """Deferred placement — called via bpy.app.timers so object creation is safe."""
    global _APPLYING, _TIMER_PENDING
    _TIMER_PENDING = False

    import bpy as _bpy
    from pathlib import Path

    scene = _bpy.data.scenes.get(scene_name)
    if scene is None:
        print("[Prop Editor] _do_place: scene not found")
        return

    group_id = getattr(scene, "pe_active_group_id", "")
    groups = get_unique_groups()

    print(f"[Prop Editor] _do_place: group_id='{group_id}'  groups={list(groups.keys())}")

    if not groups:
        print("[Prop Editor] _do_place: no groups found — skipping re-place to preserve scene")
        return

    try:
        from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights

        # ── Pre-flight BMS check ──────────────────────────────────────────────
        # Collect every unique prop name that would be placed.
        prop_list_raw, random_props_raw = _rebuild_lists(groups)
        missing_bms: list = []

        for prop_cfg in prop_list_raw:
            name = prop_cfg.get("name", "")
            if not name:
                continue
            is_vehicle  = name.lower().startswith(("va", "vp"))
            found_folder = _find_prop_folder(name, Path(prop_bms_folder))
            if is_vehicle:
                found = found_folder is not None and any(
                    (found_folder / f).exists()
                    for f in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS")
                )
            else:
                found = found_folder is not None and (found_folder / "H.BMS").exists()

            if not found:
                missing_bms.append(name)
                print(f"[Prop Editor] WARNING: No BMS found for '{name}' "
                      f"(searched under {Path(prop_bms_folder)})")

        if missing_bms:
            print(f"[Prop Editor] Aborting re-place — missing BMS for: {missing_bms}")
            print(f"[Prop Editor] Existing scene objects are preserved.")
            return

        # ── All BMS present — safe to clear and rebuild ───────────────────────
        print(f"[Prop Editor] Placing {len(prop_list_raw)} fixed + {len(random_props_raw)} random group(s)...")
        place_props_in_scene(
            prop_list_raw, random_props_raw,
            prop_bms_folder,
            texture_folder=Folder.Resources.Editor.Textures,
            car_wheels=prop_car_wheels,
            car_lights=prop_car_lights,
        )
        print("[Prop Editor] Re-place complete.")

    except Exception as exc:
        import traceback
        print(f"[Prop Editor] Auto-place error: {exc}")
        print(traceback.format_exc())


def _apply_prop_changes(scene) -> None:
    """
    Update the in-memory config (and JSON on existing objects) immediately,
    then schedule a deferred call to place_props_in_scene via a timer so that
    object creation/deletion happens outside Blender's depsgraph evaluation.
    """
    global _APPLYING, _TIMER_PENDING
    if _APPLYING:
        return
    group_id = getattr(scene, "pe_active_group_id", "")
    if not group_id:
        return

    groups = get_unique_groups()
    if group_id not in groups:
        return

    _APPLYING = True
    try:
        ptype, cfg = groups[group_id]

        if ptype == "fixed":
            cfg["offset"] = (
                round(scene.pe_offset_x, 2),
                round(scene.pe_offset_y, 2),
                round(scene.pe_offset_z, 2),
            )
            if scene.pe_has_end:
                cfg["end"] = (
                    round(scene.pe_end_x, 2),
                    round(scene.pe_end_y, 2),
                    round(scene.pe_end_z, 2),
                )
            elif "end" in cfg:
                del cfg["end"]

            cfg["angle"] = round(scene.pe_angle, 2)

            new_name = scene.pe_prop_name
            if new_name:
                cfg["name"] = new_name

        elif ptype == "random":
            cfg["area"] = [
                (round(scene.pe_area_x1, 2), round(scene.pe_area_y1, 2), round(scene.pe_area_z1, 2)),
                (round(scene.pe_area_x2, 2), round(scene.pe_area_y2, 2), round(scene.pe_area_z2, 2)),
            ]
            cfg["seed"] = scene.pe_seed
            if "count" in cfg:
                cfg["count"] = scene.pe_rand_count
            elif "num_props" in cfg:
                cfg["num_props"] = scene.pe_rand_count

            new_name = scene.pe_prop_name
            if new_name and isinstance(cfg.get("name"), str):
                cfg["name"] = new_name

        cfg["flags"] = int(scene.pe_flags)

        groups[group_id] = (ptype, cfg)

        # Patch the JSON on existing objects so the config is up-to-date
        # even before the deferred re-place runs.
        new_json = _serialize_config(cfg)
        for obj in get_prop_objects():
            if obj.get("mm_prop_group_id") == group_id:
                obj["mm_prop_config_json"] = new_json

    except Exception as exc:
        print(f"[Prop Editor] Config update error: {exc}")
    finally:
        _APPLYING = False

    # Schedule a single deferred placement (collapse rapid repeated changes).
    if not _TIMER_PENDING:
        _TIMER_PENDING = True
        scene_name = scene.name

        import bpy as _bpy
        _bpy.app.timers.register(lambda: _do_place(scene_name), first_interval=0.05)


def _update_prop_form(self, context):
    """Update callback — any form scene property triggers this."""
    _apply_prop_changes(context.scene)


# ── Operators ─────────────────────────────────────────────────────────────────

class PROPS_OT_ReloadProps(bpy.types.Operator):
    """Reload props from USER/props/props.py and re-place in the scene"""
    bl_idname = "props.reload"
    bl_label  = "Reload from props.py"

    def execute(self, context):
        import src.USER.props.props as _mod
        importlib.reload(_mod)

        from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights

        place_props_in_scene(
            _mod.prop_list,
            _mod.random_props,
            prop_bms_folder,
            texture_folder=Folder.Resources.Editor.Textures,
            car_wheels=prop_car_wheels,
            car_lights=prop_car_lights,
        )

        self.report({"INFO"}, f"Loaded {len(_mod.prop_list)} fixed + {len(_mod.random_props)} random prop groups")
        return {"FINISHED"}


class PROPS_OT_ClearProps(bpy.types.Operator):
    """Remove all props from the scene without reloading"""
    bl_idname = "props.clear"
    bl_label  = "Clear Props"

    def execute(self, context):
        from src.integrations.blender.modeling.props import _get_or_create_collection, _clear_collection, _PROPS_COLLECTION
        col = _get_or_create_collection(_PROPS_COLLECTION)
        _clear_collection(col)
        self.report({"INFO"}, "Props cleared")
        return {"FINISHED"}


class PROPS_OT_SelectGroup(bpy.types.Operator):
    """Select all objects belonging to the same prop group as the active object"""
    bl_idname = "props.select_group"
    bl_label  = "Select Group"

    def execute(self, context):
        obj = context.active_object
        if not is_prop_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged prop")
            return {"CANCELLED"}

        gid = obj.get("mm_prop_group_id")
        bpy.ops.object.select_all(action="DESELECT")
        for o in get_prop_objects():
            if o.get("mm_prop_group_id") == gid:
                o.select_set(True)
        context.view_layer.objects.active = obj

        count = sum(1 for o in get_prop_objects() if o.get("mm_prop_group_id") == gid)
        self.report({"INFO"}, f"Selected {count} object(s) in group '{gid}'")
        return {"FINISHED"}


def load_form_from_obj(scene, obj) -> bool:
    """
    Populate the Edit Prop Group form from a prop object's stored config.
    Returns True on success.  Safe to call from draw() — guarded by _APPLYING.
    """
    global _APPLYING
    if not is_prop_obj(obj):
        return False
    try:
        cfg   = json.loads(obj.get("mm_prop_config_json", "{}"))
        ptype = obj.get("mm_prop_type", "fixed")
        # Infer type from config keys when the tag is missing or wrong
        if ptype != "random" and "area" in cfg:
            ptype = "random"
    except Exception:
        return False

    _APPLYING = True
    try:
        scene.pe_active_group_id   = obj.get("mm_prop_group_id", "")
        scene.pe_active_group_type = ptype

        raw_name = cfg.get("name", "")
        if isinstance(raw_name, str) and raw_name in _GAME_TO_CONST:
            scene.pe_prop_name = raw_name

        scene.pe_flags = str(BangerFlags.normalize(int(cfg.get("flags", BangerFlags.DEFAULT))))

        if ptype == "fixed":
            offset = cfg.get("offset", [0.0, 0.0, 0.0])
            scene.pe_offset_x = float(offset[0])
            scene.pe_offset_y = float(offset[1])
            scene.pe_offset_z = float(offset[2])

            if "end" in cfg:
                scene.pe_has_end = True
                end = cfg["end"]
                scene.pe_end_x = float(end[0])
                scene.pe_end_y = float(end[1])
                scene.pe_end_z = float(end[2])
            else:
                scene.pe_has_end = False
                scene.pe_end_x = scene.pe_offset_x
                scene.pe_end_y = scene.pe_offset_y
                scene.pe_end_z = scene.pe_offset_z

            scene.pe_angle = float(cfg.get("angle", 0.0))

        elif ptype == "random":
            area = cfg.get("area", [[0, 0, 0], [0, 0, 0]])
            scene.pe_area_x1 = float(area[0][0])
            scene.pe_area_y1 = float(area[0][1])
            scene.pe_area_z1 = float(area[0][2])
            scene.pe_area_x2 = float(area[1][0])
            scene.pe_area_y2 = float(area[1][1])
            scene.pe_area_z2 = float(area[1][2])
            scene.pe_seed       = int(cfg.get("seed", 0))
            scene.pe_rand_count = int(cfg.get("count", cfg.get("num_props", 1)))
    finally:
        _APPLYING = False

    return True


class PROPS_OT_LoadIntoForm(bpy.types.Operator):
    """Populate the edit form from the active prop's stored config"""
    bl_idname = "props.load_into_form"
    bl_label  = "Edit"

    def execute(self, context):
        obj = context.active_object
        if not is_prop_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged prop")
            return {"CANCELLED"}

        if not load_form_from_obj(context.scene, obj):
            self.report({"ERROR"}, "Could not parse prop config")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Editing '{context.scene.pe_active_group_id}'")
        return {"FINISHED"}


class PROPS_OT_ExportCode(bpy.types.Operator):
    """Print Python code for all prop groups to console + clipboard"""
    bl_idname = "props.export_code"
    bl_label  = "Export All Groups"

    def execute(self, context):
        groups = get_unique_groups()
        if not groups:
            self.report({"WARNING"}, "No tagged prop groups found — reload props first")
            return {"CANCELLED"}

        code = generate_python_code(groups)
        print("\n" + "=" * 70)
        print("# ── PROP EDITOR EXPORT ──────────────────────────────────────────────")
        print(code)
        print("=" * 70 + "\n")

        try:
            context.window_manager.clipboard = code
            self.report({"INFO"}, "Exported — copied to clipboard")
        except Exception:
            self.report({"INFO"}, "Exported — see console")

        return {"FINISHED"}


class PROPS_OT_ExportGroupCode(bpy.types.Operator):
    """Export Python code for only the currently active prop group"""
    bl_idname = "props.export_group_code"
    bl_label  = "Copy Group as Code"

    def execute(self, context):
        scene    = context.scene
        group_id = scene.pe_active_group_id

        if not group_id:
            self.report({"WARNING"}, "No active group — click 'Edit' on a prop first")
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


def _write_props_py(filepath: str, code: str) -> Path:
    path = Path(filepath)
    if path.suffix.lower() != ".py":
        path = path.with_suffix(".py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return path


def _replace_user_props_file(code: str) -> Tuple[Path, Optional[Path]]:
    """
    Back up the current src/USER/props/props.py to props_backup_{timestamp}.py
    (same folder), then overwrite it with the exported code. Returns
    (target_path, backup_path | None).
    """
    target = Folder.Src.User.Props
    backup = None
    if target.exists():
        backup = target.with_name(f"props_backup_{CURRENT_TIME_FORMATTED}.py")
        backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code, encoding="utf-8")
    return target, backup


class PROPS_OT_ExportFaithfulFile(bpy.types.Operator):
    """Write every prop individually to a .py file — exact rebuild, verbose"""
    bl_idname = "props.export_faithful_file"
    bl_label  = "Export Faithful (.py)"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.py", options={"HIDDEN"})

    def invoke(self, context, event):
        if getattr(context.scene, "pr_replace_user_props", False):
            return self.execute(context)
        if not self.filepath:
            self.filepath = str(Folder.BASE / "props_faithful.py")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        groups = get_unique_groups()
        if not groups:
            self.report({"WARNING"}, "No prop groups in scene — load or create props first")
            return {"CANCELLED"}

        code = generate_python_code(groups)
        n_fixed  = sum(1 for _, (t, _c) in groups.items() if t == "fixed")
        n_random = sum(1 for _, (t, _c) in groups.items() if t == "random")

        if getattr(context.scene, "pr_replace_user_props", False):
            target, backup = _replace_user_props_file(code)
            note = f" (backup: {backup.name})" if backup else ""
            self.report({"INFO"}, f"Replaced {target.name}: {n_fixed} fixed + {n_random} random{note}")
        else:
            path = _write_props_py(self.filepath, code)
            self.report({"INFO"}, f"Wrote {n_fixed} fixed + {n_random} random groups to {path.name}")
        return {"FINISHED"}


class PROPS_OT_ExportConsolidatedFile(bpy.types.Operator):
    """Collapse evenly-spaced runs into rows, then write to a .py file — compact, lossless"""
    bl_idname = "props.export_consolidated_file"
    bl_label  = "Export Consolidated (.py)"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.py", options={"HIDDEN"})

    def invoke(self, context, event):
        if getattr(context.scene, "pr_replace_user_props", False):
            return self.execute(context)
        if not self.filepath:
            self.filepath = str(Folder.BASE / "props_consolidated.py")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        groups = get_unique_groups()
        if not groups:
            self.report({"WARNING"}, "No prop groups in scene — load or create props first")
            return {"CANCELLED"}

        prop_list, random_props = _rebuild_lists(groups)
        before = len(prop_list)
        consolidated = _consolidate_rows(prop_list)
        after = len(consolidated)
        rows = sum(1 for c in consolidated if "end" in c)

        code = _code_from_lists(consolidated, random_props)

        if getattr(context.scene, "pr_replace_user_props", False):
            target, backup = _replace_user_props_file(code)
            note = f" (backup: {backup.name})" if backup else ""
            self.report({"INFO"}, f"Replaced {target.name}: {before} props → {after} entries ({rows} rows){note}")
        else:
            path = _write_props_py(self.filepath, code)
            self.report({"INFO"}, f"{before} props → {after} entries ({rows} rows) → {path.name}")
        return {"FINISHED"}


class PROPS_OT_CreatePropGroup(bpy.types.Operator):
    """Create a new prop group from the Create Prop form and place it in the scene"""
    bl_idname = "props.create_prop_group"
    bl_label  = "Create Prop"

    def execute(self, context):
        scene = context.scene
        ptype = scene.pc_prop_type

        flags = int(scene.pc_flags)

        if ptype == "fixed":
            cfg: dict = {
                "name":   scene.pc_prop_name,
                "offset": (round(scene.pc_offset_x, 2), round(scene.pc_offset_y, 2), round(scene.pc_offset_z, 2)),
                "angle":  round(scene.pc_angle, 2),
                "flags":  flags,
            }
            if scene.pc_has_end:
                cfg["end"] = (round(scene.pc_end_x, 2), round(scene.pc_end_y, 2), round(scene.pc_end_z, 2))
        else:
            cfg = {
                "name":  scene.pc_prop_name,
                "seed":  scene.pc_seed,
                "count": scene.pc_rand_count,
                "area":  [
                    (round(scene.pc_area_x1, 2), round(scene.pc_area_y1, 2), round(scene.pc_area_z1, 2)),
                    (round(scene.pc_area_x2, 2), round(scene.pc_area_y2, 2), round(scene.pc_area_z2, 2)),
                ],
                "flags": flags,
            }

        groups = get_unique_groups()
        prop_list_raw, random_props_raw = _rebuild_lists(groups)

        if ptype == "fixed":
            prop_list_raw.append(cfg)
        else:
            random_props_raw.append(cfg)

        try:
            from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights
            place_props_in_scene(
                prop_list_raw, random_props_raw,
                prop_bms_folder,
                texture_folder=Folder.Resources.Editor.Textures,
                car_wheels=prop_car_wheels,
                car_lights=prop_car_lights,
            )
            friendly = prop_name_to_friendly(scene.pc_prop_name)
            self.report({"INFO"}, f"Created {ptype} prop '{friendly}'")
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Failed to create prop: {exc}")
            return {"CANCELLED"}

        return {"FINISHED"}


def _face_to_angle(
    fx: float, fy: float, fz: float,
    prop_name: str,
    ox: float = 0.0, oz: float = 0.0,
) -> float:
    """Convert a BNG face value back to a user-facing angle in degrees.

    Handles two storage formats:
    - Our format:   face = direction × HUGE  (|fx| or |fz| very large)
    - Original game format: face is a world-space point; direction = face - offset

    In both cases we compute direction = face - offset, then extract the XZ angle.
    For our HUGE-scaled format the offset terms are negligible so the result is
    identical to treating face as the direction directly.
    """
    # Undefined-face sentinel written by our code: face == (HUGE, HUGE, HUGE)
    if fx > HUGE * 0.5 and fy > HUGE * 0.5 and fz > HUGE * 0.5:
        return 0.01  # default to NORTH

    # direction = face - offset  (works for both game and our format)
    dx = fx - ox
    dz = fz - oz
    effective_deg = math.degrees(math.atan2(dz, dx))
    user_angle    = effective_deg - PROP_ORIENTATION_OFFSET.get(prop_name, 0)
    return round(user_angle, 2)


class PROPS_OT_LoadExternal(bpy.types.Operator):
    """Load props from an external .BNG file and place them in the scene"""
    bl_idname = "props.load_external"
    bl_label  = "Load External BNG"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.bng;*.BNG", options={"HIDDEN"})

    def invoke(self, context, event):
        self.filepath = str(Folder.BASE) + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        from src.file_formats.props.props import Bangers
        from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights

        path = Path(self.filepath)
        if not path.exists():
            self.report({"ERROR"}, f"File not found: {path}")
            return {"CANCELLED"}

        with open(path, "rb") as f:
            bangers = Bangers.read_all(f)

        # Convert each banger's face vector back to a user-facing angle so the
        # existing expand_prop_instances pipeline (orientation offset, face
        # computation, Blender rotation) handles everything correctly — and the
        # props appear with user-friendly angles in the inspector/export.
        prop_list = []
        for b in bangers:
            name  = b.name.rstrip("\x00")
            angle = _face_to_angle(b.face.x, b.face.y, b.face.z, name,
                                   ox=b.offset.x, oz=b.offset.z)
            prop_list.append({
                "name":   name,
                "offset": (b.offset.x, b.offset.y, b.offset.z),
                "angle":  angle,
                "flags":  BangerFlags.normalize(b.flags),
            })

        place_props_in_scene(
            prop_list,
            [],
            prop_bms_folder,
            texture_folder=Folder.Resources.Editor.Textures,
            car_wheels=prop_car_wheels,
            car_lights=prop_car_lights,
        )

        self.report({"INFO"}, f"Loaded {len(prop_list)} props from {path.name}")
        return {"FINISHED"}


class PROPS_OT_ReplacePropType(bpy.types.Operator):
    """Replace scene props by type. From=ALL matches everything; To=RANDOM picks a random type per group."""
    bl_idname = "props.replace_prop_type"
    bl_label  = "Replace Prop Type"

    def execute(self, context):
        import random as _random

        scene     = context.scene
        from_name = scene.pr_from_name  # game id or "__ALL__"
        to_name   = scene.pr_to_name    # game id or "__RANDOM__"

        all_game_ids = [item[0] for item in PROP_NAME_ITEMS]  # excludes sentinels

        if from_name != "__ALL__" and to_name != "__RANDOM__" and from_name == to_name:
            self.report({"WARNING"}, "From and To are the same — nothing to do")
            return {"CANCELLED"}

        groups = get_unique_groups()
        matched_groups = 0

        for gid, (ptype, cfg) in groups.items():
            name_val = cfg.get("name")

            # Decide whether this group matches the From filter
            if from_name == "__ALL__":
                matches = True
            elif isinstance(name_val, str):
                matches = (name_val == from_name)
            elif isinstance(name_val, list):
                matches = any(n == from_name for n in name_val)
            else:
                matches = False

            if not matches:
                continue

            # Decide the replacement name
            if to_name == "__RANDOM__":
                replacement = _random.choice(all_game_ids)
            else:
                replacement = to_name

            # Apply — preserve list structure for random groups
            if isinstance(name_val, list):
                if from_name == "__ALL__":
                    if to_name == "__RANDOM__":
                        cfg["name"] = [_random.choice(all_game_ids) for _ in name_val]
                    else:
                        cfg["name"] = [replacement] * len(name_val)
                else:
                    if to_name == "__RANDOM__":
                        cfg["name"] = [_random.choice(all_game_ids) if n == from_name else n for n in name_val]
                    else:
                        cfg["name"] = [replacement if n == from_name else n for n in name_val]
            else:
                cfg["name"] = replacement

            matched_groups += 1
            new_json = _serialize_config(cfg)
            for obj in get_prop_objects():
                if obj.get("mm_prop_group_id") == gid:
                    obj["mm_prop_config_json"] = new_json

        if not matched_groups:
            label = "ALL" if from_name == "__ALL__" else prop_name_to_friendly(from_name)
            self.report({"WARNING"}, f"No props matching '{label}' found in scene")
            return {"CANCELLED"}

        # Re-place so new BMS meshes are loaded
        try:
            from src.USER.settings.blender import prop_bms_folder, prop_car_wheels, prop_car_lights
            updated_groups = get_unique_groups()
            prop_list, random_props = _rebuild_lists(updated_groups)
            place_props_in_scene(
                prop_list, random_props,
                prop_bms_folder,
                texture_folder=Folder.Resources.Editor.Textures,
                car_wheels=prop_car_wheels,
                car_lights=prop_car_lights,
            )
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            self.report({"ERROR"}, f"Replace succeeded but re-place failed: {exc}")
            return {"CANCELLED"}

        from_label = "ALL" if from_name == "__ALL__" else prop_name_to_friendly(from_name)
        to_label   = "RANDOM" if to_name == "__RANDOM__" else prop_name_to_friendly(to_name)
        self.report({"INFO"}, f"Replaced '{from_label}' → '{to_label}' in {matched_groups} group(s)")
        return {"FINISHED"}


class PROPS_OT_DeleteGroup(bpy.types.Operator):
    """Remove all scene objects belonging to the active prop group"""
    bl_idname = "props.delete_group"
    bl_label  = "Delete Group"

    def execute(self, context):
        obj = context.active_object
        if not is_prop_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged prop")
            return {"CANCELLED"}

        gid = obj.get("mm_prop_group_id")
        to_remove = [o for o in get_prop_objects() if o.get("mm_prop_group_id") == gid]
        for o in to_remove:
            bpy.data.objects.remove(o, do_unlink=True)

        self.report({"INFO"}, f"Deleted {len(to_remove)} object(s) in group '{gid}'")
        return {"FINISHED"}


class PROPS_OT_SaveBNG(bpy.types.Operator):
    """Write all scene prop groups to a binary .BNG file"""
    bl_idname = "props.save_bng"
    bl_label  = "Save BNG"

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.bng;*.BNG", options={"HIDDEN"})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "props.bng"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        from src.file_formats.props.props import Bangers
        from src.integrations.blender.modeling.props import expand_prop_instances
        from src.core.vector.vector_3 import Vector3

        groups = get_unique_groups()
        if not groups:
            self.report({"WARNING"}, "No prop groups in scene — load or create props first")
            return {"CANCELLED"}

        prop_list, random_props = _rebuild_lists(groups)
        instances = expand_prop_instances(prop_list, random_props)

        bangers = []
        for inst in instances:
            ox, oy, oz = inst["offset"]
            face = inst.get("face") or (HUGE, HUGE, HUGE)
            fx, fy, fz = face
            flags = inst.get("flags", BangerFlags.DEFAULT)
            name = inst["name"]
            if not name.endswith("\x00"):
                name += "\x00"
            bangers.append(Bangers(
                0, flags,
                Vector3(ox, oy, oz),
                Vector3(fx, fy, fz),
                name,
            ))

        path = Path(self.filepath)
        Bangers.write_all(path, bangers, debug_props=False)

        self.report({"INFO"}, f"Saved {len(bangers)} props to {path.name}")
        return {"FINISHED"}


PROP_EDITOR_CLASSES = [
    PROPS_OT_ReloadProps,
    PROPS_OT_ClearProps,
    PROPS_OT_SelectGroup,
    PROPS_OT_LoadIntoForm,
    PROPS_OT_ExportCode,
    PROPS_OT_ExportGroupCode,
    PROPS_OT_ExportFaithfulFile,
    PROPS_OT_ExportConsolidatedFile,
    PROPS_OT_CreatePropGroup,
    PROPS_OT_LoadExternal,
    PROPS_OT_ReplacePropType,
    PROPS_OT_DeleteGroup,
    PROPS_OT_SaveBNG,
]

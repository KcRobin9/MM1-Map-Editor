import bpy
import json
import importlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.integrations.blender.modeling.props import place_props_in_scene
from src.constants.file_formats import AxisRef
from src.constants.folder import Folder

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

# Fast reverse lookup: game_id → const string (e.g. "tpdrawbridge04" → "Prop.BRIDGE_SLIM")
_GAME_TO_CONST: Dict[str, str] = {item[0]: item[2] for item in PROP_NAME_ITEMS}
# game_id → friendly label
_GAME_TO_FRIENDLY: Dict[str, str] = {item[0]: item[1] for item in PROP_NAME_ITEMS}


def prop_name_to_const(name: str) -> str:
    """'tpdrawbridge04'  →  'Prop.BRIDGE_SLIM'  (fallback: quoted string)"""
    return _GAME_TO_CONST.get(name, f'"{name}"')


def prop_name_to_friendly(name: str) -> str:
    """'tpdrawbridge04'  →  'Bridge Slim'  (fallback: raw name)"""
    return _GAME_TO_FRIENDLY.get(name, name)


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

    if cfg.get("race"):
        race_strs = ", ".join(f"RaceModeNum.{r}" for r in cfg["race"])
        lines.append(f'    "race": [{race_strs}],')


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

    if cfg.get("race"):
        race_strs = ", ".join(f"RaceModeNum.{r}" for r in cfg["race"])
        lines.append(f'    "race": [{race_strs}],')


def generate_python_code(groups: Dict) -> str:
    lines = [
        "# Generated by Prop Editor",
        "from src.constants.props import Prop",
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

    if prop_var_names:
        lines.append(f"prop_list = [{', '.join(prop_var_names)}]")
        lines.append("")

    for gid, cfg in _sorted_random(groups):
        var = f"random_{gid.replace('random_', '')}"
        random_var_names.append(var)
        lines.append(f"{var} = {{")
        _emit_random_config(lines, cfg)
        lines.append("}")
        lines.append("")

    if random_var_names:
        lines.append(f"random_props = [{', '.join(random_var_names)}]")

    return "\n".join(lines)


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
            is_vehicle = name.lower().startswith(("va", "vp"))
            if is_vehicle:
                veh_folder = Path(prop_bms_folder) / name.upper()
                found = any(
                    (veh_folder / f).exists()
                    for f in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS")
                )
            else:
                prop_folder = Path(prop_bms_folder) / name.upper()
                found = (prop_folder / "H.BMS").exists()

            if not found:
                missing_bms.append(name)
                print(f"[Prop Editor] WARNING: No BMS found for '{name}' "
                      f"(expected {Path(prop_bms_folder) / name.upper()})")

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


class PROPS_OT_LoadIntoForm(bpy.types.Operator):
    """Populate the edit form from the active prop's stored config"""
    bl_idname = "props.load_into_form"
    bl_label  = "Edit"

    def execute(self, context):
        obj = context.active_object
        if not is_prop_obj(obj):
            self.report({"WARNING"}, "Active object is not a tagged prop")
            return {"CANCELLED"}

        try:
            cfg   = json.loads(obj.get("mm_prop_config_json", "{}"))
            ptype = obj.get("mm_prop_type", "fixed")
        except Exception:
            self.report({"ERROR"}, "Could not parse prop config")
            return {"CANCELLED"}

        scene = context.scene

        # Guard against triggering _apply_prop_changes while we load
        global _APPLYING
        _APPLYING = True
        try:
            scene.pe_active_group_id   = obj.get("mm_prop_group_id", "")
            scene.pe_active_group_type = ptype

            # Prop name (single-name entries only for the dropdown)
            raw_name = cfg.get("name", "")
            if isinstance(raw_name, str) and raw_name in _GAME_TO_CONST:
                scene.pe_prop_name = raw_name

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

        self.report({"INFO"}, f"Editing '{scene.pe_active_group_id}'")
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


class PROPS_OT_CreatePropGroup(bpy.types.Operator):
    """Create a new prop group from the Create Prop form and place it in the scene"""
    bl_idname = "props.create_prop_group"
    bl_label  = "Create Prop"

    def execute(self, context):
        scene = context.scene
        ptype = scene.pc_prop_type

        if ptype == "fixed":
            cfg: dict = {
                "name":   scene.pc_prop_name,
                "offset": (round(scene.pc_offset_x, 2), round(scene.pc_offset_y, 2), round(scene.pc_offset_z, 2)),
                "angle":  round(scene.pc_angle, 2),
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


PROP_EDITOR_CLASSES = [
    PROPS_OT_ReloadProps,
    PROPS_OT_SelectGroup,
    PROPS_OT_LoadIntoForm,
    PROPS_OT_ExportCode,
    PROPS_OT_ExportGroupCode,
    PROPS_OT_CreatePropGroup,
]

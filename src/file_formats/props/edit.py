
from pathlib import Path
from typing import List, Dict, Tuple, Set, Callable

from src.core.vector.vector_3 import Vector3
from src.file_formats.props.props import Bangers
from src.file_formats.props.matching import matches_exact_filter, matches_range_filter
from src.file_formats.props.expansion import expand_rules
from src.ui.console import yellow, green, red, cyan
from src.ui.prompts.edit import prompt_edit_selection


class PropTransform:
    @staticmethod
    def translate(prop: Bangers, delta: Tuple[float, float, float]) -> Bangers:
        prop.offset = prop.offset + Vector3(*delta)
        return prop
    
    @staticmethod
    def set_offset(prop: Bangers, offset: Tuple[float, float, float]) -> Bangers:
        prop.offset = Vector3(*offset)
        return prop
    
    @staticmethod
    def set_offset_x(prop: Bangers, x: float) -> Bangers:
        prop.offset.x = x
        return prop
    
    @staticmethod
    def set_offset_y(prop: Bangers, y: float) -> Bangers:
        prop.offset.y = y
        return prop
    
    @staticmethod
    def set_offset_z(prop: Bangers, z: float) -> Bangers:
        prop.offset.z = z
        return prop
    
    @staticmethod
    def add_offset(prop: Bangers, axis: str, value: float) -> Bangers:
        current = getattr(prop.offset, axis.lower())
        setattr(prop.offset, axis.lower(), current + value)
        return prop
    
    @staticmethod
    def set_face(prop: Bangers, face: Tuple[float, float, float]) -> Bangers:
        prop.face = Vector3(*face)
        return prop
    
    @staticmethod
    def set_face_x(prop: Bangers, x: float) -> Bangers:
        prop.face.x = x
        return prop
    
    @staticmethod
    def set_face_y(prop: Bangers, y: float) -> Bangers:
        prop.face.y = y
        return prop
    
    @staticmethod
    def set_face_z(prop: Bangers, z: float) -> Bangers:
        prop.face.z = z
        return prop
    
    @staticmethod
    def rotate_face(prop: Bangers, delta: Tuple[float, float, float]) -> Bangers:
        prop.face = prop.face + Vector3(*delta)
        return prop
    
    @staticmethod
    def set_name(prop: Bangers, name: str) -> Bangers:
        prop.name = name if name.endswith('\x00') else name + '\x00'
        return prop
        
    # @staticmethod
    # def scale_offset(prop: Bangers, scale: float) -> Bangers:
    #     prop.offset = prop.offset * scale
    #     return prop
    
    @staticmethod
    def mirror_x(prop: Bangers, pivot: float = 0.0) -> Bangers:
        prop.offset.x = 2 * pivot - prop.offset.x
        prop.face.x = -prop.face.x
        return prop
    
    @staticmethod
    def mirror_z(prop: Bangers, pivot: float = 0.0) -> Bangers:
        prop.offset.z = 2 * pivot - prop.offset.z
        prop.face.z = -prop.face.z
        return prop
    
    @staticmethod
    def swap_xz(prop: Bangers) -> Bangers:
        prop.offset.x, prop.offset.z = prop.offset.z, prop.offset.x
        prop.face.x, prop.face.z = prop.face.z, prop.face.x
        return prop


def build_transform(edit_rule: Dict) -> Callable[[Bangers], Bangers]:
    transforms = []
    
    if "translate" in edit_rule:
        delta = edit_rule["translate"]
        transforms.append(lambda p, d=delta: PropTransform.translate(p, d))
    
    if "set_offset" in edit_rule:
        offset = edit_rule["set_offset"]
        transforms.append(lambda p, o=offset: PropTransform.set_offset(p, o))
    
    if "set_offset_x" in edit_rule:
        x = edit_rule["set_offset_x"]
        transforms.append(lambda p, v=x: PropTransform.set_offset_x(p, v))
    
    if "set_offset_y" in edit_rule:
        y = edit_rule["set_offset_y"]
        transforms.append(lambda p, v=y: PropTransform.set_offset_y(p, v))
    
    if "set_offset_z" in edit_rule:
        z = edit_rule["set_offset_z"]
        transforms.append(lambda p, v=z: PropTransform.set_offset_z(p, v))
    
    if "add_offset_x" in edit_rule:
        v = edit_rule["add_offset_x"]
        transforms.append(lambda p, val=v: PropTransform.add_offset(p, 'x', val))
    
    if "add_offset_y" in edit_rule:
        v = edit_rule["add_offset_y"]
        transforms.append(lambda p, val=v: PropTransform.add_offset(p, 'y', val))
    
    if "add_offset_z" in edit_rule:
        v = edit_rule["add_offset_z"]
        transforms.append(lambda p, val=v: PropTransform.add_offset(p, 'z', val))
    
    if "set_face" in edit_rule:
        face = edit_rule["set_face"]
        transforms.append(lambda p, f=face: PropTransform.set_face(p, f))
    
    if "set_face_x" in edit_rule:
        x = edit_rule["set_face_x"]
        transforms.append(lambda p, v=x: PropTransform.set_face_x(p, v))
    
    if "set_face_y" in edit_rule:
        y = edit_rule["set_face_y"]
        transforms.append(lambda p, v=y: PropTransform.set_face_y(p, v))
    
    if "set_face_z" in edit_rule:
        z = edit_rule["set_face_z"]
        transforms.append(lambda p, v=z: PropTransform.set_face_z(p, v))
    
    if "rotate_face" in edit_rule:
        delta = edit_rule["rotate_face"]
        transforms.append(lambda p, d=delta: PropTransform.rotate_face(p, d))
    
    if "set_name" in edit_rule:
        name = edit_rule["set_name"]
        transforms.append(lambda p, n=name: PropTransform.set_name(p, n))
        
    # if "scale_offset" in edit_rule:
    #     scale = edit_rule["scale_offset"]
    #     transforms.append(lambda p, s=scale: PropTransform.scale_offset(p, s))
    
    if "mirror_x" in edit_rule:
        pivot = edit_rule.get("mirror_x_pivot", 0.0)
        transforms.append(lambda p, pv=pivot: PropTransform.mirror_x(p, pv))
    
    if "mirror_z" in edit_rule:
        pivot = edit_rule.get("mirror_z_pivot", 0.0)
        transforms.append(lambda p, pv=pivot: PropTransform.mirror_z(p, pv))
    
    if "swap_xz" in edit_rule and edit_rule["swap_xz"]:
        transforms.append(PropTransform.swap_xz)
    
    def combined_transform(prop: Bangers) -> Bangers:
        for transform in transforms:
            prop = transform(prop)
        return prop
    
    return combined_transform


def edit_props_in_file(
    input_file: Path,
    output_file: Path,
    edit_rules: List[Dict],
    tolerance: float = 0.25,
    require_confirmation: bool = True
) -> None:
    with open(input_file, "rb") as f:
        props = Bangers.read_all(f)
    
    if not props:
        print(yellow("Edit: Input file has 0 props. Nothing to edit."))
        return
    
    candidates = _find_editable_props(props, edit_rules, tolerance)
    
    print(f"\nEdit: Loaded {len(props)} prop(s) from {input_file.name}")
    print(f"Edit: Matches found: {len(candidates)}\n")
    
    if not candidates:
        print(red("Edit: No matches. Nothing was edited."))
        return
    
    _print_edit_candidates(candidates)
    
    indices_to_edit = _get_indices_to_edit(candidates, require_confirmation)
    
    if not indices_to_edit:
        print(red("Edit: Cancelled. Nothing was edited."))
        return
    
    edit_count = 0
    for index, prop, rule, transform in candidates:
        if index in indices_to_edit:
            props[index] = transform(prop)
            edit_count += 1
    
    Bangers.write_all(output_file, props, debug_props=False)
    
    print(f"\n{green(f'Edit: Modified {edit_count} prop(s)')}")
    print(cyan(f"---output file: {output_file.name}"))


def _find_editable_props(
    props: List[Bangers],
    edit_rules: List[Dict],
    tolerance: float
) -> List[Tuple[int, Bangers, Dict, Callable]]:
    candidates = []
    seen_indices: Set[int] = set()
    
    for rule in edit_rules:
        filter_rule = _extract_filter(rule)
        expanded_filters = expand_rules([filter_rule]) if "end" in filter_rule else [filter_rule]
        transform = build_transform(rule)
        
        for index, prop in enumerate(props):
            if index in seen_indices:
                continue
            
            for expanded_filter in expanded_filters:
                if _matches_filter(prop, expanded_filter, tolerance, index):
                    candidates.append((index, prop, rule, transform))
                    seen_indices.add(index)
                    break
    
    return candidates


def _extract_filter(rule: Dict) -> Dict:
    filter_keys = {
        "id", "ids", "id_min", "id_max",
        "name", "offset", "face", "end", "separator",
        "offset_min", "offset_max", "face_min", "face_max"
    }
    return {k: v for k, v in rule.items() if k in filter_keys}


def _matches_filter(prop: Bangers, rule: Dict, tolerance: float, index: int) -> bool:
    has_exact = any(k in rule for k in ["id", "offset", "face"])
    has_range = any(k in rule for k in ["ids", "id_min", "id_max", "offset_min", "offset_max", "face_min", "face_max"])
    
    if has_exact and matches_exact_filter(prop, rule, tolerance, index):
        return True
    
    if has_range and matches_range_filter(prop, rule, index):
        return True
    
    if "name" in rule and not has_exact and not has_range:
        prop_name = prop.name.rstrip("\x00")
        return prop_name == rule["name"]
    
    return False


def _print_edit_candidates(candidates: List[Tuple[int, Bangers, Dict, Callable]], max_display: int = 200) -> None:
    for index, prop, rule, _ in candidates[:max_display]:
        name = prop.name.rstrip("\x00")
        o = prop.offset
        edit_ops = _describe_edits(rule)
        print(yellow(
            f"[{index}] {name} | "
            f"offset=({o.x:.3f}, {o.y:.3f}, {o.z:.3f}) | "
            f"edits: {edit_ops}"
        ))
    
    if len(candidates) > max_display:
        print(f"... plus {len(candidates) - max_display} more matches (not shown).")


def _describe_edits(rule: Dict) -> str:
    edit_keys = [
        "translate", "set_offset", "set_offset_x", "set_offset_y", "set_offset_z",
        "add_offset_x", "add_offset_y", "add_offset_z",
        "set_face", "set_face_x", "set_face_y", "set_face_z", "rotate_face",
        "set_name", "mirror_x", "mirror_z", "swap_xz"
        # Commented out: "scale_offset"
    ]
    ops = [f"{k}={rule[k]}" for k in edit_keys if k in rule]
    return ", ".join(ops) if ops else "none"


def _get_indices_to_edit(
    candidates: List[Tuple[int, Bangers, Dict, Callable]],
    require_confirmation: bool
) -> Set[int]:
    all_indices = {i for i, _, _, _ in candidates}
    
    if not require_confirmation:
        return all_indices
    
    selected = prompt_edit_selection(candidates)
    
    if not selected:
        return set()
    
    return all_indices & selected
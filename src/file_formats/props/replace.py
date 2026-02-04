from pathlib import Path
from typing import List, Dict, Tuple, Set

from src.file_formats.props.props import Bangers
from src.file_formats.props.matching import matches_exact_filter, matches_range_filter
from src.file_formats.props.expansion import expand_rules
from src.ui.console import yellow, green, red, cyan
from src.ui.prompts.replace import prompt_replace_selection


def replace_props_in_file(
    input_file: Path,
    output_file: Path,
    replace_rules: List[Dict],
    tolerance: float = 0.25,
    require_confirmation: bool = True
) -> None:
    expanded_rules = []
    for rule in replace_rules:
        filter_part = _extract_filter(rule)
        expanded = expand_rules([filter_part]) if "end" in filter_part else [filter_part]
        for exp in expanded:
            expanded_rules.append({**exp, "replace_with": rule["replace_with"]})
    
    with open(input_file, "rb") as f:
        props = Bangers.read_all(f)
    
    if not props:
        print(yellow("Replace: Input file has 0 props. Nothing to replace."))
        return
    
    candidates = _find_replaceable_props(props, expanded_rules, tolerance)
    
    print(f"\nReplace: Loaded {len(props)} prop(s) from {input_file.name}")
    print(f"Replace: Matches found: {len(candidates)}\n")
    
    if not candidates:
        print(red("Replace: No matches. Nothing was replaced."))
        return
    
    _print_candidates(candidates)
    
    indices_to_replace = _get_indices_to_replace(candidates, require_confirmation)
    
    if not indices_to_replace:
        print(red("Replace: Cancelled. Nothing was replaced."))
        return
    
    replace_count = 0
    for index, prop, new_name in candidates:
        if index in indices_to_replace:
            props[index].name = new_name if new_name.endswith('\x00') else new_name + '\x00'
            replace_count += 1
    
    Bangers.write_all(output_file, props, debug_props=False)
    
    print(f"\n{green(f'Replace: Replaced {replace_count} prop(s)')}")
    print(cyan(f"---output file: {output_file.name}"))


def _extract_filter(rule: Dict) -> Dict:
    filter_keys = {
        "id", "ids", "id_min", "id_max",
        "name", "offset", "face", "end", "separator",
        "offset_min", "offset_max", "face_min", "face_max"
    }
    return {k: v for k, v in rule.items() if k in filter_keys}


def _find_replaceable_props(
    props: List[Bangers],
    rules: List[Dict],
    tolerance: float
) -> List[Tuple[int, Bangers, str]]:
    candidates = []
    seen_indices: Set[int] = set()
    
    for rule in rules:
        new_name = rule["replace_with"]
        filter_rule = {k: v for k, v in rule.items() if k != "replace_with"}
        
        for index, prop in enumerate(props):
            if index in seen_indices:
                continue
            
            if _matches_filter(prop, filter_rule, tolerance, index):
                candidates.append((index, prop, new_name))
                seen_indices.add(index)
    
    return candidates


def _matches_filter(prop: Bangers, rule: Dict, tolerance: float, index: int) -> bool:
    has_exact = any(k in rule for k in ["id", "offset", "face"])
    has_range = any(k in rule for k in ["ids", "id_min", "id_max", "offset_min", "offset_max"])
    
    if has_exact and matches_exact_filter(prop, rule, tolerance, index):
        return True
    
    if has_range and matches_range_filter(prop, rule, index):
        return True
    
    if "name" in rule and not has_exact and not has_range:
        return prop.name.rstrip("\x00") == rule["name"]
    
    return False


def _print_candidates(candidates: List[Tuple[int, Bangers, str]], max_display: int = 200) -> None:
    for index, prop, new_name in candidates[:max_display]:
        old_name = prop.name.rstrip("\x00")
        o = prop.offset
        print(yellow(
            f"[{index}] {old_name} -> {new_name} | "
            f"offset=({o.x:.3f}, {o.y:.3f}, {o.z:.3f})"
        ))
    
    if len(candidates) > max_display:
        print(f"... plus {len(candidates) - max_display} more matches (not shown).")


def _get_indices_to_replace(
    candidates: List[Tuple[int, Bangers, str]],
    require_confirmation: bool
) -> Set[int]:
    all_indices = {i for i, _, _ in candidates}
    
    if not require_confirmation:
        return all_indices
    
    selected = prompt_replace_selection(candidates)
    
    if not selected:
        return set()
    
    return all_indices & selected

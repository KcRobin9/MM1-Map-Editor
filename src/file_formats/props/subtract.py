from pathlib import Path
from typing import List, Dict, Tuple, Set

from src.core.vector.vector_3 import Vector3
from src.file_formats.props.props import Bangers
from src.file_formats.props.matching import matches_exact_filter, matches_range_filter
from src.file_formats.props.expansion import expand_rules
from src.ui.console import yellow, green, red, cyan
from src.ui.prompts.subtract import prompt_subtract_selection


def subtract_props_from_file(
    input_file: Path,
    output_file: Path,
    exact_rules: List[Dict],
    range_rules: List[Dict],
    tolerance: float = 0.25,
    require_confirmation: bool = True
) -> None:
    expanded_exact = expand_rules(exact_rules)
    
    with open(input_file, "rb") as f:
        props = Bangers.read_all(f)
    
    if not props:
        print(yellow("Subtract: Input file has 0 props. Nothing to remove."))
        return
    
    candidates = _find_matching_props(props, expanded_exact, range_rules, tolerance)
    
    print(f"\nSubtract: Loaded {len(props)} prop(s) from {input_file.name}")
    print(f"Subtract: Matches found: {len(candidates)}\n")
    
    if not candidates:
        print(red("Subtract: No matches. Nothing was removed."))
        return
    
    _print_candidates(candidates)
    
    indices_to_remove = _get_indices_to_remove(candidates, require_confirmation)
    
    if not indices_to_remove:
        print(red("Subtract: Cancelled. Nothing was removed."))
        return
    
    remaining_props = [p for i, p in enumerate(props) if i not in indices_to_remove]
    
    Bangers.write_all(output_file, remaining_props, debug_props=False)
    
    print(f"\n{green(f'Subtract: Removed {len(indices_to_remove)} prop(s)')}")
    print(f"Subtract: New prop count: {len(remaining_props)}")
    print(cyan(f"---output file: {output_file.name}"))


def _find_matching_props(
    props: List[Bangers],
    exact_rules: List[Dict],
    range_rules: List[Dict],
    tolerance: float
) -> List[Tuple[int, Bangers, str]]:
    candidates = []
    seen_indices: Set[int] = set()
    
    for index, prop in enumerate(props):
        if index in seen_indices:
            continue
        
        for rule in exact_rules:
            if matches_exact_filter(prop, rule, tolerance, index):
                candidates.append((index, prop, f"exact: {rule}"))
                seen_indices.add(index)
                break
        
        if index in seen_indices:
            continue
        
        for rule in range_rules or []:
            if matches_range_filter(prop, rule, index):
                candidates.append((index, prop, f"range: {rule}"))
                seen_indices.add(index)
                break
    
    return candidates


def _print_candidates(candidates: List[Tuple[int, Bangers, str]], max_display: int = 200) -> None:
    for index, prop, reason in candidates[:max_display]:
        name = prop.name.rstrip("\x00")
        o = prop.offset
        f = prop.face
        print(yellow(
            f"[{index}] {name} | "
            f"offset=({o.x:.3f}, {o.y:.3f}, {o.z:.3f}) | "
            f"face=({f.x:.3f}, {f.y:.3f}, {f.z:.3f}) | "
            f"{reason}"
        ))
    
    if len(candidates) > max_display:
        print(f"... plus {len(candidates) - max_display} more matches (not shown).")


def _get_indices_to_remove(
    candidates: List[Tuple[int, Bangers, str]],
    require_confirmation: bool
) -> Set[int]:
    all_indices = {i for i, _, _ in candidates}
    
    if not require_confirmation:
        return all_indices
    
    selected = prompt_subtract_selection(candidates)
    
    if not selected:
        return set()
    
    return all_indices & selected
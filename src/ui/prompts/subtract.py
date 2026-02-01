import re
from typing import List, Tuple, Set, Optional

from src.ui.console import yellow, green, red


def prompt_subtract_selection(candidates: List[Tuple[int, object, str]]) -> Optional[Set[int]]:
    """
    Interactive prompt for selecting which props to subtract.
    
    Args:
        candidates: List of (index, prop, reason) tuples
        
    Returns:
        Set of selected indices, or None if cancelled
    """
    all_indices = {i for i, _, _ in candidates}
    selected: Set[int] = set()

    while True:
        user_input = _get_user_input()
        command = user_input.lower()

        if command in ("none", ""):
            return None
        if command == "all":
            return set(all_indices)
        if command == "clear":
            selected.clear()
            print(yellow("Selection cleared."))
            continue
        if command == "done":
            return set(selected) if selected else None

        selected = _process_tokens(user_input, candidates, all_indices, selected)
        _print_selection_summary(selected, candidates, all_indices)


def _get_user_input() -> str:
    prompt = """
================================================================
Subtract Selection
================================================================

Commands:
  all   - Select all matches
  none  - Cancel operation
  done  - Confirm current selection
  clear - Clear current selection

Selection Syntax:
  1234       - Select by ID
  100-120    - Select ID range
  tp_trailer - Select by name
  tp_*       - Select by name prefix (wildcard)
  !1234      - Remove from selection (prefix with !)

> """
    return input(prompt).strip()


def _process_tokens(
    user_input: str,
    candidates: List[Tuple[int, object, str]],
    all_indices: Set[int],
    selected: Set[int]
) -> Set[int]:
    for raw in user_input.split(","):
        token = raw.strip()
        if not token:
            continue

        negate = token.startswith("!")
        if negate:
            token = token[1:].strip()
            if not token:
                continue

        ids = _parse_token(token, candidates, all_indices)

        if negate:
            selected -= ids
        else:
            selected |= ids

    return selected


def _parse_token(
    token: str,
    candidates: List[Tuple[int, object, str]],
    all_indices: Set[int]
) -> Set[int]:
    range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", token)
    
    if range_match:
        a, b = int(range_match.group(1)), int(range_match.group(2))
        lo, hi = min(a, b), max(a, b)
        return set(range(lo, hi + 1)) & all_indices
    
    if token.isdigit():
        v = int(token)
        return {v} if v in all_indices else set()
    
    return _ids_for_name(token.lower(), candidates)


def _ids_for_name(name_pattern: str, candidates: List[Tuple[int, object, str]]) -> Set[int]:
    def get_name(prop) -> str:
        return prop.name.rstrip("\x00").lower()
    
    if name_pattern.endswith("*"):
        prefix = name_pattern[:-1]
        return {i for i, p, _ in candidates if get_name(p).startswith(prefix)}
    
    return {i for i, p, _ in candidates if get_name(p) == name_pattern}


def _print_selection_summary(
    selected: Set[int],
    candidates: List[Tuple[int, object, str]],
    all_indices: Set[int]
) -> None:
    if not selected:
        print(yellow(f"Selected 0 of {len(all_indices)}. Type 'done' to confirm or 'none' to cancel."))
        return

    counts = {}
    for i, p, _ in candidates:
        if i in selected:
            name = p.name.rstrip("\x00")
            counts[name] = counts.get(name, 0) + 1

    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    top_str = ", ".join([f"{name}={count}" for name, count in top])
    
    print(yellow(f"Selected {len(selected)} of {len(all_indices)}. By name: {top_str}"))
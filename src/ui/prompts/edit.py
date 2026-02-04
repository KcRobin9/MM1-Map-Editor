from typing import List, Tuple, Set, Optional, Callable

from src.file_formats.props.props import Bangers
from src.ui.console import yellow, green, cyan


def prompt_edit_selection(candidates: List[Tuple[int, Bangers, dict, Callable]]) -> Optional[Set[int]]:
    print(f"\n{cyan('Options:')}")
    print("  [a] Edit ALL matched props")
    print("  [s] Select specific props by index (comma-separated)")
    print("  [p] Preview changes for a specific prop")
    print("  [c] Cancel operation")
    
    while True:
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'a':
            return {i for i, _, _, _ in candidates}
        
        elif choice == 's':
            indices_input = input("Enter indices to edit (comma-separated): ").strip()
            try:
                selected = _parse_indices(indices_input)
                valid = {i for i, _, _, _ in candidates}
                filtered = selected & valid
                
                if not filtered:
                    print(yellow("No valid indices selected."))
                    continue
                
                invalid = selected - valid
                if invalid:
                    print(yellow(f"Ignored invalid indices: {sorted(invalid)}"))
                
                print(green(f"Selected {len(filtered)} prop(s) for editing."))
                return filtered
                
            except ValueError:
                print(yellow("Invalid input. Use comma-separated numbers."))
                continue
        
        elif choice == 'p':
            index_input = input("Enter index to preview: ").strip()
            try:
                idx = int(index_input)
                _preview_edit(candidates, idx)
            except ValueError:
                print(yellow("Invalid index."))
            continue
        
        elif choice == 'c':
            return None
        
        else:
            print(yellow("Invalid choice. Enter 'a', 's', 'p', or 'c'."))


def _parse_indices(input_str: str) -> Set[int]:
    parts = input_str.replace(" ", "").split(",")
    indices = set()
    
    for part in parts:
        if not part:
            continue
        
        if "-" in part and not part.startswith("-"):
            start, end = part.split("-", 1)
            indices.update(range(int(start), int(end) + 1))
        else:
            indices.add(int(part))
    
    return indices


def _preview_edit(candidates: List[Tuple[int, Bangers, dict, Callable]], target_idx: int) -> None:
    for index, prop, rule, transform in candidates:
        if index != target_idx:
            continue
        
        from copy import deepcopy
        from src.core.vector.vector_3 import Vector3
        
        original_offset = Vector3(prop.offset.x, prop.offset.y, prop.offset.z)
        original_face = Vector3(prop.face.x, prop.face.y, prop.face.z)
        original_name = prop.name
        original_room = prop.room
        original_flags = prop.flags
        
        modified = transform(prop)
        
        print(f"\n{cyan(f'Preview for index [{index}]:')}")
        print(f"  Name:   {original_name.rstrip(chr(0))} -> {modified.name.rstrip(chr(0))}")
        print(f"  Offset: ({original_offset.x:.3f}, {original_offset.y:.3f}, {original_offset.z:.3f}) -> "
              f"({modified.offset.x:.3f}, {modified.offset.y:.3f}, {modified.offset.z:.3f})")
        print(f"  Face:   ({original_face.x:.3f}, {original_face.y:.3f}, {original_face.z:.3f}) -> "
              f"({modified.face.x:.3f}, {modified.face.y:.3f}, {modified.face.z:.3f})")
        print(f"  Room:   {original_room} -> {modified.room}")
        print(f"  Flags:  {original_flags} -> {modified.flags}")
        
        prop.offset = original_offset
        prop.face = original_face
        prop.name = original_name
        prop.room = original_room
        prop.flags = original_flags
        
        return
    
    print(yellow(f"Index [{target_idx}] not found in candidates."))

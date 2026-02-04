from typing import List, Tuple, Set, Optional

from src.file_formats.props.props import Bangers
from src.ui.console import yellow, green, cyan


def prompt_replace_selection(candidates: List[Tuple[int, Bangers, str]]) -> Optional[Set[int]]:
    print(f"\n{cyan('Options:')}")
    print("  [a] Replace ALL matched props")
    print("  [s] Select specific props by index (comma-separated)")
    print("  [c] Cancel operation")
    
    while True:
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'a':
            return {i for i, _, _ in candidates}
        
        elif choice == 's':
            indices_input = input("Enter indices to replace (comma-separated): ").strip()
            try:
                selected = _parse_indices(indices_input)
                valid = {i for i, _, _ in candidates}
                filtered = selected & valid
                
                if not filtered:
                    print(yellow("No valid indices selected."))
                    continue
                
                invalid = selected - valid
                if invalid:
                    print(yellow(f"Ignored invalid indices: {sorted(invalid)}"))
                
                print(green(f"Selected {len(filtered)} prop(s) for replacement."))
                return filtered
                
            except ValueError:
                print(yellow("Invalid input. Use comma-separated numbers."))
                continue
        
        elif choice == 'c':
            return None
        
        else:
            print(yellow("Invalid choice. Enter 'a', 's', or 'c'."))


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

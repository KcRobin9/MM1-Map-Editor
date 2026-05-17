import os
import re

# --- CONFIGURATION ---
DRY_RUN = False          # Always test with True first!
TARGET_EXT = ".BMS"
RECURSIVE = True         # Search subdirectories as well as the script's directory
SEARCH_PATH = None       # None = use script's directory; set a path to hardcode, e.g.:
                         # SEARCH_PATH = r"C:\Users\robin\Desktop\MeshDump"

# Split into two distinct priority groups to ensure one of each survives
TERRAIN_LODS = ["H", "M", "L", "VL"]       # Becomes Pass 1 (Terrain)
BUILDING_LODS = ["H2", "M2", "L2", "VL2"]  # Becomes Pass 4 (Buildings)
SPECIALS = ["A", "A2"]              # Always rendered, always kept


def cleanup_directory(directory):
    files = [f for f in os.listdir(directory) if f.upper().endswith(TARGET_EXT)]

    if not files:
        return

    # Structure: { base_name: { 'TERRAIN': {variant: file}, 'BUILDING': {variant: file}, 'SPECIAL': [files] } }
    groups = {}

    pattern = re.compile(r"^(.*)_(VL2|VL|H2|H|M2|M|L2|L|A2|A)$", re.IGNORECASE)

    for f in files:
        name_part = os.path.splitext(f)[0]
        match = pattern.match(name_part)

        if match:
            base, variant = match.groups()
            variant = variant.upper()
            if base not in groups:
                groups[base] = {'TERRAIN': {}, 'BUILDING': {}, 'SPECIAL': []}

            if variant in TERRAIN_LODS:
                groups[base]['TERRAIN'][variant] = f
            elif variant in BUILDING_LODS:
                groups[base]['BUILDING'][variant] = f
            elif variant in SPECIALS:
                groups[base]['SPECIAL'].append(f)
        else:
            base = name_part
            if base not in groups:
                groups[base] = {'TERRAIN': {}, 'BUILDING': {}, 'SPECIAL': []}
            groups[base]['TERRAIN']['H_BASE'] = f

    printed_header = False

    for base, data in groups.items():
        to_keep = set()
        to_delete = []

        for spec_file in data['SPECIAL']:
            to_keep.add(spec_file)

        t_vars = data['TERRAIN']
        t_winner = None
        for p in ["H_BASE", "H", "M", "L", "VL"]:
            if p in t_vars:
                t_winner = p
                break

        for var, f in t_vars.items():
            if var == t_winner:
                to_keep.add(f)
            else:
                to_delete.append(f)

        b_vars = data['BUILDING']
        b_winner = None
        for p in BUILDING_LODS:
            if p in b_vars:
                b_winner = p
                break

        for var, f in b_vars.items():
            if var == b_winner:
                to_keep.add(f)
            else:
                to_delete.append(f)

        if to_keep or to_delete:
            if not printed_header:
                print(f"\n  [{directory}]")
                printed_header = True
            print(f"  [{base}]")
            for k in sorted(to_keep):
                print(f"    [KEEPING] -> {k}")
            for d in sorted(to_delete):
                if DRY_RUN:
                    print(f"    [WILL DELETE] -> {d}")
                else:
                    try:
                        os.remove(os.path.join(directory, d))
                        print(f"    [DELETED] -> {d}")
                    except Exception as e:
                        print(f"    [ERROR] {d}: {e}")


def main():
    root = SEARCH_PATH if SEARCH_PATH else os.path.dirname(os.path.abspath(__file__))

    print(f"\n--- {'DRY RUN' if DRY_RUN else 'LIVE MODE'} | Root: {root} | Recursive: {RECURSIVE} ---")

    if RECURSIVE:
        for dirpath, dirnames, _ in os.walk(root):
            dirnames.sort()
            cleanup_directory(dirpath)
    else:
        cleanup_directory(root)


if __name__ == "__main__":
    main()

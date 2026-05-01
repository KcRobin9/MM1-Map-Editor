import os
import re

# --- CONFIGURATION ---
DRY_RUN = False  # Always test with True first!
TARGET_EXT = ".BMS"

# Split into two distinct priority groups to ensure one of each survives
TERRAIN_LODS = ["H", "M", "L"]      # Becomes Pass 1 (Terrain)
BUILDING_LODS = ["H2", "M2", "L2"]  # Becomes Pass 4 (Buildings)
SPECIALS = ["A", "A2"]             # Always rendered, always kept

def cleanup_cull_variants():
    cwd = os.getcwd()
    files = [f for f in os.listdir(cwd) if f.upper().endswith(TARGET_EXT)]
    
    if not files:
        print("No matching files found.")
        return

    # Structure: { base_name: { 'TERRAIN': {variant: file}, 'BUILDING': {variant: file}, 'SPECIAL': [files] } }
    groups = {}

    # Regex captures the base name and the suffix
    pattern = re.compile(r"^(.*)_(H2|H|M2|M|L2|L|A2|A)$", re.IGNORECASE)

    for f in files:
        name_part = os.path.splitext(f)[0]
        match = pattern.match(name_part)
        
        # Handle standard variants
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
        
        # Handle the "No Suffix" H case (e.g., CULL01.BMS)
        else:
            # We assume a file with no suffix is a High Terrain file
            base = name_part
            if base not in groups:
                groups[base] = {'TERRAIN': {}, 'BUILDING': {}, 'SPECIAL': []}
            groups[base]['TERRAIN']['H_BASE'] = f

    print(f"\n--- {'DRY RUN' if DRY_RUN else 'LIVE MODE'} ---")

    for base, data in groups.items():
        to_keep = set()
        to_delete = []

        # 1. Always keep Specials
        for spec_file in data['SPECIAL']:
            to_keep.add(spec_file)

        # 2. Process Terrain Bucket (H_BASE > H > M > L)
        t_vars = data['TERRAIN']
        t_winner = None
        for p in ["H_BASE", "H", "M", "L"]:
            if p in t_vars:
                t_winner = p
                break
        
        for var, f in t_vars.items():
            if var == t_winner:
                to_keep.add(f)
            else:
                to_delete.append(f)

        # 3. Process Building Bucket (H2 > M2 > L2)
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

        # Output Results
        if to_keep or to_delete:
            print(f"[{base}]")
            for k in sorted(to_keep):
                print(f"  [KEEPING] -> {k}")
            for d in sorted(to_delete):
                if DRY_RUN:
                    print(f"  [WILL DELETE] -> {d}")
                else:
                    try:
                        os.remove(os.path.join(cwd, d))
                        print(f"  [DELETED] -> {d}")
                    except Exception as e:
                        print(f"  [ERROR] {d}: {e}")

if __name__ == "__main__":
    cleanup_cull_variants()
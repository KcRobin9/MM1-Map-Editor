import os
import re

# --- CONFIGURATION ---
DRY_RUN = False  # Set to False to actually delete files
TARGET_EXT = ".BMS"
# Priority order: lower index = higher priority. 
# A2 is excluded from this list because it is "Always Keep".
PRIORITY_MAP = ["H2", "H", "M2", "M", "L2", "L", "A"]

def cleanup_cull_variants():
    cwd = os.getcwd()
    files = [f for f in os.listdir(cwd) if f.upper().endswith(TARGET_EXT)]
    
    if not files:
        print("No matching files found in current directory.")
        return

    # Dictionary structure: { base_name: { variant_suffix: full_filename } }
    # Example: { "CULL210_xxxx": { "H": "CULL210_xxxx_H.BMS", "M": "CULL210_xxxx_M.BMS" } }
    groups = {}

    # Regex to capture the base name and the variant suffix
    # Looks for an underscore followed by the variant name before the extension
    pattern = re.compile(r"^(.*)_(H2|H|M2|M|L2|L|A2|A)$", re.IGNORECASE)

    for f in files:
        name_part = os.path.splitext(f)[0]
        match = pattern.match(name_part)
        
        if match:
            base, variant = match.groups()
            variant = variant.upper()
            if base not in groups:
                groups[base] = {}
            groups[base][variant] = f
        else:
            print(f"Skipping {f}: Does not match recognized variant pattern.")

    print(f"\n--- {'DRY RUN: No files will be deleted' if DRY_RUN else 'LIVE MODE: Deleting files'} ---")

    for base, variants in groups.items():
        # 1. Handle the "Special" A2 - We never delete this.
        if "A2" in variants:
            print(f"[{base}] Found A2: Preserving as special exception.")
            variants.pop("A2")

        # 2. Identify the highest remaining variant
        highest_found = None
        for p in PRIORITY_MAP:
            if p in variants:
                highest_found = p
                break
        
        if highest_found:
            print(f"[{base}] Highest variant is _{highest_found}. Preserving.")
            
            # 3. Mark others for deletion
            for v, filename in variants.items():
                if v != highest_found:
                    if DRY_RUN:
                        print(f"  [WILL DELETE] -> {filename}")
                    else:
                        try:
                            os.remove(os.path.join(cwd, filename))
                            print(f"  [DELETED] -> {filename}")
                        except Exception as e:
                            print(f"  [ERROR] Could not delete {filename}: {e}")
        else:
            if not variants: # Case where only A2 existed
                continue
            print(f"[{base}] No standard variants to compare.")

if __name__ == "__main__":
    cleanup_cull_variants()
    if DRY_RUN:
        print("\nReview the output above. If it looks correct, set DRY_RUN = False in the script.")
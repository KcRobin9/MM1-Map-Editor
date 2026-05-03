"""
Compare vertices in CAR_EXPORT/BODY_H.BMS against all known originals.
Prints which car it matches, then lists modified vertices.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.integrations.blender.modeling.meshes import read_bms


def read_points(path: Path):
    bms = read_bms(path)
    return bms["points"], bms["flags"], len(bms["points"])


export_path = Path("CAR_EXPORT/BODY_H.BMS")
exp_points, exp_flags, exp_n = read_points(export_path)

originals = {
    "VPPANOZ":     Path("CAR_FILES_TEST/VPPANOZ/BODY_H.BMS"),
    "VPFORD":      Path("CAR_FILES_TEST/VPFORD/BODY_H.BMS"),
    "VPMUSTANG99": Path("CAR_FILES_TEST/VPMUSTANG99/BODY_H.BMS"),
}

best_match = -1
best_name  = None
best_orig  = None
for name, path in originals.items():
    try:
        orig_points, _, orig_n = read_points(path)
    except Exception as e:
        print(f"Could not read {name}: {e}")
        continue
    if orig_n != exp_n:
        print(f"{name}: vertex count mismatch ({orig_n} vs {exp_n}), skipping")
        continue
    matches = sum(1 for a, b in zip(orig_points, exp_points)
                  if all(abs(a[i] - b[i]) < 1e-4 for i in range(3)))
    print(f"{name}: {matches}/{exp_n} vertices match")
    if matches > best_match:
        best_match = matches
        best_name  = name
        best_orig  = orig_points

print(f"\nBest match: {best_name}")
print(f"Exported flags: 0x{exp_flags:02X}")

print("\n=== Modified vertices (index, original -> exported) ===")
changed = []
for i, (orig, exp) in enumerate(zip(best_orig, exp_points)):
    if any(abs(orig[j] - exp[j]) > 1e-4 for j in range(3)):
        changed.append((i, orig, exp))

if not changed:
    print("No differences found -- vertex edits were NOT captured (still in Edit Mode during export?)")
else:
    for idx, orig, exp in changed:
        dx = exp[0] - orig[0]; dy = exp[1] - orig[1]; dz = exp[2] - orig[2]
        print(f"  [{idx:3d}]  orig=({orig[0]:+.4f}, {orig[1]:+.4f}, {orig[2]:+.4f})"
              f"  ->  exp=({exp[0]:+.4f}, {exp[1]:+.4f}, {exp[2]:+.4f})"
              f"  D=({dx:+.4f}, {dy:+.4f}, {dz:+.4f})")
    print(f"\nTotal: {len(changed)} vertex/vertices modified")

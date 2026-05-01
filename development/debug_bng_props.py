"""
Debug: compare expected prop positions (from props.py + add_multiple logic)
against the actual positions stored in FirstCity.BNG.

Run from the repo root:
    python debug_bng_props.py

Output:
  - Per-prop delta between expected and actual game positions
  - A CSV of every prop in the BNG
  - Blender placement analysis (mesh_offset rotation issue)
"""

import math
import sys
from pathlib import Path

# ── Bootstrap path so project imports work ───────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from src.file_formats.props.props import Bangers
from src.constants.constants import PROP_CAN_COLLIDE_FLAG, HUGE
from src.constants.props_orientation import PROP_ORIENTATION_OFFSET
from src.core.vector.vector_3 import Vector3
from src.USER.settings.main import default_separator

# Import prop list but we'll re-simulate add_multiple() here
from src.USER.props.props import prop_list

BNG_PATH = Path("SHOP/CITY/FirstCity.BNG")
CSV_OUT   = Path("debug_bng_dump.csv")


# ── Replicate BangerEditor.add_multiple() ────────────────────────────────────

def simulate_add_multiple(user_set_props):
    """Returns list of (name, Vector3_offset, Vector3_face) matching game binary output."""
    results = []

    for prop in user_set_props:
        offset = Vector3(*prop['offset'])
        end    = Vector3(*prop['end']) if 'end' in prop else None
        name   = prop['name']

        if 'face' in prop:
            face = Vector3(*prop['face'])
        elif 'angle' in prop:
            effective  = prop['angle'] + PROP_ORIENTATION_OFFSET.get(name, 0)
            angle_rad  = math.radians(effective)
            face       = Vector3(HUGE * math.cos(angle_rad), 0.0, HUGE * math.sin(angle_rad))
        else:
            face = Vector3(HUGE, HUGE, HUGE)

        if end is not None:
            diagonal        = end - offset
            diagonal_length = diagonal.Mag()
            normalized      = diagonal.Normalize()

            if face == Vector3(HUGE, HUGE, HUGE):
                face = normalized * HUGE

            separator = prop.get('separator', default_separator)
            num_props = int(diagonal_length / separator)

            for i in range(num_props):
                pos = offset + normalized * (i * separator)
                results.append((name, pos, face))
        else:
            results.append((name, offset, face))

    return results


# ── Game-to-Blender coordinate helpers ───────────────────────────────────────

def game_to_blender(x, y, z):
    """Standard game → blender coordinate transform."""
    return (x, -z, y)


def rotate_offset_by_face(ox, oy, oz, face: Vector3):
    """
    Rotate a LOCAL mesh_offset by the prop's facing direction.
    The game stores the prop's local +X axis as the face vector.
    We construct a 2-D rotation matrix in the XZ plane (Y is up, unchanged).
    """
    # Normalise the face vector in XZ plane
    fx, fz = face.x, face.z
    length = math.sqrt(fx * fx + fz * fz)
    if length < 1e-6:
        return ox, oy, oz
    fx /= length
    fz /= length

    # face = local +X direction
    # local +Z direction = rotate face 90° CCW: (-fz, fx)
    # rotated_x = ox * fx  + oz * (-fz)
    # rotated_z = ox * fz  + oz * fx
    rx = ox * fx  + oz * (-fz)
    rz = ox * fz  + oz * fx
    return rx, oy, rz


# ── Blender placement simulation ─────────────────────────────────────────────
# mesh_offset values for common props (game-space, from BMS files)
# If you don't have them, set to (0,0,0) and note that in output.
# These are approximate — the exact values come from the BMS header.
# Update this dict by reading actual BMS files or from prop_dimensions analysis.
MESH_OFFSETS_GAME = {
    # prop_name: (ox, oy, oz)  — game space
    # Fill in from BMS header reads; 0,0,0 means "not measured yet"
}


def blender_pos_current(game_x, game_y, game_z, mesh_off):
    """Current Blender placement: game_to_blender(pos) + (-ox, oz, oy) (BUGGY for rotated props)."""
    ox, oy, oz = mesh_off
    bx, by, bz = game_to_blender(game_x, game_y, game_z)
    return (bx + (-ox), by + oz, bz + oy)


def blender_pos_corrected(game_x, game_y, game_z, mesh_off, face: Vector3):
    """Corrected Blender placement: rotate mesh_offset by prop orientation first."""
    ox, oy, oz = mesh_off
    rx, ry, rz = rotate_offset_by_face(ox, oy, oz, face)
    bx, by, bz = game_to_blender(game_x, game_y, game_z)
    # Correct coordinate transform for offset too: game_to_blender of rotated offset
    bo_x, bo_y, bo_z = game_to_blender(rx, ry, rz)
    return (bx + bo_x, by + bo_y, bz + bo_z)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BNG_PATH.exists():
        print(f"ERROR: {BNG_PATH} not found. Run from repo root.")
        return

    # 1. Read actual BNG
    print(f"Reading {BNG_PATH} ...")
    with open(BNG_PATH, "rb") as f:
        actual = Bangers.read_all(f)
    print(f"  {len(actual)} props in BNG\n")

    # 2. Write CSV dump of every prop
    with open(CSV_OUT, "w") as f:
        f.write("idx,name,off_x,off_y,off_z,face_x,face_y,face_z\n")
        for i, b in enumerate(actual):
            n = b.name.rstrip('\x00')
            f.write(f"{i},{n},{b.offset.x:.4f},{b.offset.y:.4f},{b.offset.z:.4f},"
                    f"{b.face.x:.4f},{b.face.y:.4f},{b.face.z:.4f}\n")
    print(f"BNG dump written to {CSV_OUT}\n")

    # 3. Simulate expected positions
    print("Simulating expected positions from props.py ...")
    expected = simulate_add_multiple(prop_list)
    print(f"  {len(expected)} expected props\n")

    # 4. Compare — match by name + closest position
    print("=== Position Comparison (expected vs actual BNG) ===")
    print(f"{'#':>4}  {'Name':<25}  {'Expected XYZ':>36}  {'Actual XYZ':>36}  {'Delta':>12}")
    print("-" * 120)

    used_actual = set()
    total_delta = 0.0
    mismatches  = 0

    for i, (name, exp_pos, face) in enumerate(expected):
        clean_name = name.rstrip('\x00')

        # Find closest unused actual prop with the same name
        best_dist = float('inf')
        best_j    = -1
        for j, b in enumerate(actual):
            if j in used_actual:
                continue
            if b.name.rstrip('\x00') != clean_name:
                continue
            d = math.sqrt(
                (b.offset.x - exp_pos.x)**2 +
                (b.offset.y - exp_pos.y)**2 +
                (b.offset.z - exp_pos.z)**2
            )
            if d < best_dist:
                best_dist = d
                best_j    = j

        if best_j == -1:
            print(f"{i:>4}  {clean_name:<25}  {exp_pos.x:>10.3f},{exp_pos.y:>10.3f},{exp_pos.z:>10.3f}  {'NOT FOUND IN BNG':>36}")
            mismatches += 1
            continue

        used_actual.add(best_j)
        act = actual[best_j]
        total_delta += best_dist

        flag = "  OK" if best_dist < 0.05 else f"  *** DELTA={best_dist:.3f}"
        if best_dist >= 0.05:
            mismatches += 1

        print(
            f"{i:>4}  {clean_name:<25}  "
            f"{exp_pos.x:>10.3f},{exp_pos.y:>10.3f},{exp_pos.z:>10.3f}  "
            f"{act.offset.x:>10.3f},{act.offset.y:>10.3f},{act.offset.z:>10.3f}  "
            f"d={best_dist:>7.3f}{flag}"
        )

    print(f"\nTotal: {len(expected)} props, {mismatches} mismatches, avg delta={total_delta/max(len(expected),1):.4f}")

    # 5. Show props in BNG that were NOT matched
    unmatched = [b for j, b in enumerate(actual) if j not in used_actual]
    if unmatched:
        print(f"\n=== {len(unmatched)} props in BNG with no matching expected prop ===")
        for b in unmatched:
            print(f"  {b.name.rstrip(chr(0)):<25}  offset=({b.offset.x:.3f},{b.offset.y:.3f},{b.offset.z:.3f})")

    # 6. Mesh_offset rotation analysis
    print("\n=== Mesh Offset Rotation Analysis ===")
    print("For props where MESH_OFFSETS_GAME is populated, show current vs corrected Blender pos.\n")
    for name_raw, mesh_off in MESH_OFFSETS_GAME.items():
        # Find one instance of this prop in expected
        for ename, epos, eface in expected:
            if ename.rstrip('\x00') == name_raw:
                cur = blender_pos_current(epos.x, epos.y, epos.z, mesh_off)
                cor = blender_pos_corrected(epos.x, epos.y, epos.z, mesh_off, eface)
                diff = math.sqrt(sum((a-b)**2 for a,b in zip(cur, cor)))
                print(f"  {name_raw:<25}  face=({eface.x:.1f},{eface.y:.1f},{eface.z:.1f})")
                print(f"    current Blender : ({cur[0]:.3f},{cur[1]:.3f},{cur[2]:.3f})")
                print(f"    corrected Blender: ({cor[0]:.3f},{cor[1]:.3f},{cor[2]:.3f})")
                print(f"    position shift   : {diff:.3f} units")
                break

    print("\nDone. Check delta values:")
    print("  delta~0   -> Blender pos matches game (no fix needed for that row)")
    print("  delta~N   -> mesh_offset rotation mismatch — prop face direction matters")
    print("  large non-mesh delta -> add_multiple() logic bug")


if __name__ == "__main__":
    main()

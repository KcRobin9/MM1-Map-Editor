"""
Standalone BMS debug dumper — no Blender required.
Usage:  python debug_bms.py <path_to_bms_file>
        python debug_bms.py resources/editor/BMS/VPBUS/BODY_H.BMS
"""

import sys
from collections import Counter
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.constants.file_formats import MeshFlags
from src.integrations.blender.modeling.meshes import read_bms


def debug_bms(bms_file: Path) -> None:
    bms = read_bms(bms_file)

    points          = bms["points"]
    mesh_offset     = bms["mesh_offset"]
    radius          = bms["radius"]
    num_adjuncts    = bms["num_adjuncts"]
    num_surfaces    = bms["num_surfaces"]
    normal_indices  = bms["normal_indices"]
    tex_coords      = bms["tex_coords"]
    vert_colors     = bms["vert_colors"]
    vertex_indices  = bms["vertex_indices"]
    texture_indices = bms["texture_indices"]
    surface_indices = bms["surface_indices"]
    texture_names   = bms["texture_names"]
    flags           = bms["flags"]
    num_points      = len(points)
    num_indices     = num_surfaces * 4

    print(f"mesh_offset    = {mesh_offset}")
    print(f"num_points     = {num_points}")
    print(f"num_adjuncts   = {num_adjuncts}")
    print(f"num_surfaces   = {num_surfaces}")
    print(f"num_indices    = {num_indices}  (num_surfaces * 4)")
    print(f"radius         = {radius}")
    print(f"num_textures   = {len(texture_names)}")
    print(f"flags          = 0b{flags:08b}  ({flags})")
    print(f"  TEXCOORDS  = {bool(flags & MeshFlags.TEXCOORDS)}")
    print(f"  NORMALS    = {bool(flags & MeshFlags.NORMALS)}")
    print(f"  COLORS     = {bool(flags & MeshFlags.COLORS)}")
    print(f"  PLANES     = {bool(flags & MeshFlags.PLANES)}")

    print(f"\n--- Texture names ---")
    for i, name in enumerate(texture_names):
        print(f"  [{i}] '{name}'")

    print(f"\n--- Vertex positions: {num_points} points ---")
    for i, p in enumerate(points):
        if i < 8 or i >= num_points - 4:
            print(f"  [{i:4d}] {p}")
        elif i == 8:
            print(f"  ... ({num_points - 12} more) ...")

    print(f"\n--- Per-adjunct data ---")
    if normal_indices:
        print(f"  normals[0..7]    = {normal_indices[:8]}")
    else:
        print(f"  normals          = (not present)")

    if tex_coords:
        print(f"  tex_coords[0..7] = {tex_coords[:8]}")
    else:
        print(f"  tex_coords       = (not present)")

    if vert_colors:
        print(f"  vert_colors[0..7] = {vert_colors[:8]}")
    else:
        print(f"  vert_colors      = (not present)")

    print(f"\n--- Adjunct → point mapping ---")
    print(f"  vertex_indices[0..15] = {vertex_indices[:16]}")
    out_of_range = [v for v in vertex_indices if v >= num_points]
    if out_of_range:
        print(f"  WARNING: {len(out_of_range)} indices out of range [0, {num_points - 1}]: {out_of_range[:10]}")
    else:
        print(f"  All indices in range [0, {num_points - 1}]  OK")

    print(f"\n--- Surface texture indices ---")
    dist = Counter(texture_indices)
    print(f"  distribution: {dict(sorted(dist.items()))}")
    print(f"  first 32: {texture_indices[:32]}")
    bad = [v for v in texture_indices if v > len(texture_names)]
    if bad:
        print(f"  WARNING: {len(bad)} indices exceed num_textures ({len(texture_names)}): {bad[:10]}")
    else:
        print(f"  All in range [0, {len(texture_names)}]  OK")

    print(f"\n--- Surface adjunct indices ---")
    print(f"  first 16 (4 per face): {surface_indices[:16]}")
    tris  = sum(1 for i in range(0, len(surface_indices), 4) if surface_indices[i + 3] == 0)
    quads = num_surfaces - tris
    print(f"  tris={tris}  quads={quads}")
    bad_adj = [v for v in surface_indices if v >= num_adjuncts]
    if bad_adj:
        print(f"  WARNING: {len(bad_adj)} adjunct indices out of range [0, {num_adjuncts - 1}]: {bad_adj[:10]}")
    else:
        print(f"  All adjunct refs in range  OK")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_bms.py <path_to_bms>")
        print("Example: python debug_bms.py resources/editor/BMS/VPBUS/BODY_H.BMS")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"=== BMS Debug Dump: {path} ===\n")
    debug_bms(path)

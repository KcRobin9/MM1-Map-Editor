"""
Standalone BMS debug dumper — no Blender required.
Usage:  python debug_bms.py <path_to_bms_file>
        python debug_bms.py resources/editor/BMS/VPBUS/BODY_H.BMS
"""

import struct
import sys
from pathlib import Path


def read_bms_debug(bms_file: Path) -> dict:
    with open(bms_file, "rb") as f:
        raw = f.read()

    f_pos = [0]  # mutable cursor

    def read(n):
        data = raw[f_pos[0]: f_pos[0] + n]
        f_pos[0] += n
        return data

    def skip(n, label=""):
        if label:
            print(f"  [skip {n} bytes @ 0x{f_pos[0]:04X}  — {label}]")
        f_pos[0] += n

    magic = struct.unpack("<L", read(4))[0]
    print(f"magic          = 0x{magic:08X}  (expected 0x4D534833 = 'HSM3'{'  OK' if magic == 0x4D534833 else '  MISMATCH!'})")

    mesh_offset = struct.unpack("<fff", read(12))
    print(f"mesh_offset    = {mesh_offset}")

    num_points, num_adjuncts, num_surfaces, num_indices = struct.unpack("<LLLL", read(16))
    print(f"num_points     = {num_points}")
    print(f"num_adjuncts   = {num_adjuncts}")
    print(f"num_surfaces   = {num_surfaces}")
    print(f"num_indices    = {num_indices}  (should be num_surfaces * 4 = {num_surfaces * 4})")

    radius = struct.unpack("<fff", read(12))
    print(f"radius         = {radius}")

    num_textures = struct.unpack("<B", read(1))[0]
    flags        = struct.unpack("<B", read(1))[0]
    print(f"num_textures   = {num_textures}")
    print(f"flags          = 0b{flags:08b}  ({flags})")
    print(f"  bit 0 (TEXCOORDS) = {bool(flags & 1)}")
    print(f"  bit 1 (NORMALS)   = {bool(flags & 2)}")
    print(f"  bit 2 (COLORS)    = {bool(flags & 4)}")
    print(f"  bit 4 (PLANES)    = {bool(flags & 16)}")

    pad_cache = read(6)
    print(f"padding+cache  = {pad_cache.hex()}  (2-byte pad + 4-byte cache_size)")

    print(f"\n--- Texture names (pos 0x{f_pos[0]:04X}) ---")
    texture_names = []
    for i in range(num_textures):
        raw_name = bytearray(read(32))
        null_pos  = raw_name.find(b"\x00")
        name = raw_name[:null_pos].decode("ascii", errors="replace") if null_pos != -1 else raw_name.decode("ascii", errors="replace")
        padding = read(16)
        texture_names.append(name)
        print(f"  [{i}] '{name}'  (pad={padding.hex()})")

    print(f"\n--- Vertex positions: {num_points} points (pos 0x{f_pos[0]:04X}) ---")
    points = []
    for i in range(num_points):
        p = struct.unpack("<fff", read(12))
        points.append(p)
        if i < 8 or i >= num_points - 4:
            print(f"  [{i:4d}] {p}")
        elif i == 8:
            print(f"  ... ({num_points - 12} more) ...")

    # Bounding-box sentinel vertices
    sentinel_count = 0
    if num_points >= 16:
        sentinel_count = 8
        print(f"\n  [skipping {sentinel_count} sentinel bbox verts @ 0x{f_pos[0]:04X}]")
        f_pos[0] += 12 * sentinel_count

    print(f"\n--- Per-adjunct data (pos 0x{f_pos[0]:04X}) ---")

    normal_indices = []
    if flags & 2:
        normal_indices = list(struct.unpack(f"{num_adjuncts}B", read(num_adjuncts)))
        print(f"  normals[0..7]  = {normal_indices[:8]}")
    else:
        print(f"  normals        = (not present)")

    tex_coords = []
    if flags & 1:
        for _ in range(num_adjuncts):
            uv = struct.unpack("<ff", read(8))
            tex_coords.append(uv)
        print(f"  tex_coords[0..7] = {tex_coords[:8]}")
    else:
        print(f"  tex_coords     = (not present)")

    if flags & 4:
        print(f"  [skipping COLORS: {4 * num_adjuncts} bytes @ 0x{f_pos[0]:04X}]")
        f_pos[0] += 4 * num_adjuncts

    print(f"\n--- Adjunct->point mapping (pos 0x{f_pos[0]:04X}) ---")
    vertex_indices = list(struct.unpack(f"{num_adjuncts}H", read(num_adjuncts * 2)))
    print(f"  vertex_indices[0..15] = {vertex_indices[:16]}")
    out_of_range = [v for v in vertex_indices if v >= num_points]
    if out_of_range:
        print(f"  WARNING: {len(out_of_range)} indices out of range [0, {num_points-1}]: {out_of_range[:10]}")
    else:
        print(f"  All indices in range [0, {num_points - 1}]  OK")

    if flags & 16:
        print(f"\n  [skipping PLANES: {16 * num_surfaces} bytes @ 0x{f_pos[0]:04X}]")
        f_pos[0] += 16 * num_surfaces

    print(f"\n--- Surface texture indices (pos 0x{f_pos[0]:04X}) ---")
    texture_indices = list(struct.unpack(f"<{num_surfaces}B", read(num_surfaces)))
    from collections import Counter
    dist = Counter(texture_indices)
    print(f"  distribution: {dict(sorted(dist.items()))}")
    print(f"  first 32: {texture_indices[:32]}")
    bad = [v for v in texture_indices if v > num_textures]
    if bad:
        print(f"  WARNING: {len(bad)} indices exceed num_textures ({num_textures}): {bad[:10]}")
    else:
        print(f"  All in range [0, {num_textures}]  OK")

    print(f"\n--- Surface adjunct indices (pos 0x{f_pos[0]:04X}) ---")
    surface_indices = list(struct.unpack(f"{num_indices}H", read(num_indices * 2)))
    print(f"  first 16 (4 per face): {surface_indices[:16]}")
    tris  = sum(1 for i in range(0, len(surface_indices), 4) if surface_indices[i+3] == 0)
    quads = num_surfaces - tris
    print(f"  tris={tris}  quads={quads}")
    bad_adj = [v for v in surface_indices if v >= num_adjuncts]
    if bad_adj:
        print(f"  WARNING: {len(bad_adj)} adjunct indices out of range [0, {num_adjuncts-1}]: {bad_adj[:10]}")
    else:
        print(f"  All adjunct refs in range  OK")

    remaining = len(raw) - f_pos[0]
    print(f"\n--- End of parse @ 0x{f_pos[0]:04X}, remaining bytes = {remaining} ---")
    if remaining > 0:
        print(f"  Trailing bytes (hex): {raw[f_pos[0]:f_pos[0]+64].hex()}")

    return {
        "points": points,
        "mesh_offset": mesh_offset,
        "num_adjuncts": num_adjuncts,
        "num_surfaces": num_surfaces,
        "tex_coords": tex_coords,
        "normal_indices": normal_indices,
        "vertex_indices": vertex_indices,
        "texture_indices": texture_indices,
        "surface_indices": surface_indices,
        "texture_names": texture_names,
        "flags": flags,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_bms.py <path_to_bms>")
        print("Example files to try:")
        print("  python debug_bms.py BODY_H.BMS")
        print("  python debug_bms.py resources/editor/BMS/VPBUS/BODY_H.BMS")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"=== BMS Debug Dump: {path} ===\n")
    read_bms_debug(path)

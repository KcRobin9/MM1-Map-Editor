"""
BMS round-trip / header verification — runnable WITHOUT Blender.

Reads an original BMS, re-serialises it with the production writer (write_bms),
then re-reads the output and compares both the raw header bytes and every parsed
field. Its main job is to guarantee the writer keeps texture names at file offset
52 (0x34) and round-trips counts/flags/indices exactly — the alignment that, when
broken, makes exported cars crash the game while original cars still load.

Usage:
    python development/bms_roundtrip_check.py [path/to/original.BMS]

Defaults to resources/editor/MESHES/CARS/VPPANOZ/BODY_H.BMS.
Exit code 0 = all checks pass, 1 = a mismatch was found.
"""
import sys
import struct
from pathlib import Path

# Repo root = parent of development/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.integrations.blender.modeling.meshes import read_bms          # noqa: E402
from src.integrations.blender.modeling.bms_writer import write_bms     # noqa: E402
from src.constants.file_formats import MeshFlags                       # noqa: E402

# File offset where the first texture name must begin. Derived from the header:
# magic(4) + mesh_offset(12) + 4 counts(16) + radius×3(12)
#          + TextureCount(1) + Flags(1) + padding(2) + cache_size(4) = 52.
TEXNAME_OFFSET = 52

_FLAG_NAMES = [
    (MeshFlags.TEXCOORDS, "UV"),
    (MeshFlags.NORMALS,   "NORMAL"),
    (MeshFlags.COLORS,    "CPV"),
    (MeshFlags.OFFSET,    "OFFSET"),
    (MeshFlags.PLANES,    "PLANES"),
]


def _flag_str(flags: int) -> str:
    on = [name for bit, name in _FLAG_NAMES if flags & bit]
    return f"0x{flags:02X} (" + "|".join(on) + ")" if on else f"0x{flags:02X}"


def dump_header(path: Path, label: str) -> dict:
    """Print the raw header fields of a BMS file and return them as a dict."""
    raw = path.read_bytes()
    # Field offsets: magic@0(4) mesh_offset@4(12) counts@16(16) radius@32(12)
    #                TextureCount@44(1) Flags@45(1) padding@46(2) cache_size@48(4)
    #                first texture name @52
    magic = raw[0:4]
    mesh_offset = struct.unpack_from("<3f", raw, 4)
    vc, ac, sc, ic = struct.unpack_from("<4I", raw, 16)
    radius = struct.unpack_from("<3f", raw, 32)
    tex_count = raw[44]
    flags = raw[45]
    padding = struct.unpack_from("<H", raw, 46)[0]
    cache_size = struct.unpack_from("<I", raw, 48)[0]
    first_name = raw[TEXNAME_OFFSET:TEXNAME_OFFSET + 32].split(b"\0")[0].decode("ascii", "replace")

    print(f"  [{label}] {path.name}  ({len(raw)} bytes)")
    print(f"    magic            : {magic!r}")
    print(f"    mesh_offset      : ({mesh_offset[0]:.4f}, {mesh_offset[1]:.4f}, {mesh_offset[2]:.4f})")
    print(f"    vert/adj/surf/idx: {vc} / {ac} / {sc} / {ic}")
    print(f"    radius (r,r²,bb) : ({radius[0]:.4f}, {radius[1]:.4f}, {radius[2]:.4f})")
    print(f"    TextureCount     : {tex_count}")
    print(f"    Flags            : {_flag_str(flags)}")
    print(f"    padding          : {padding}")
    print(f"    cache_size       : 0x{cache_size:X} ({cache_size})")
    print(f"    name@offset {TEXNAME_OFFSET}   : {first_name!r}")
    return {
        "magic": magic, "mesh_offset": mesh_offset, "counts": (vc, ac, sc, ic),
        "tex_count": tex_count, "flags": flags, "padding": padding,
        "first_name": first_name, "size": len(raw),
    }


def check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    else:
        src = ROOT / "resources/editor/MESHES/CARS/VPPANOZ/BODY_H.BMS"

    if not src.is_file():
        print(f"ERROR: source BMS not found: {src}")
        return 1

    print("=" * 72)
    print(f"BMS round-trip check: {src}")
    print("=" * 72)

    # ── 1. Parse original ─────────────────────────────────────────────────────
    print("\n[1] Original header")
    h0 = dump_header(src, "orig")

    d0 = read_bms(src)

    # Our writer never emits BSP plane data, so a faithful round-trip of an
    # original file with PLANES must drop that flag (mirrors mesh_to_bms_data).
    d0_flags_in = d0["flags"]
    d0["flags"] = d0_flags_in & ~MeshFlags.PLANES

    # ── 2. Re-serialise with the production writer ────────────────────────────
    out = ROOT / "temp" / "bms_roundtrip" / src.name
    out.parent.mkdir(parents=True, exist_ok=True)
    write_bms(d0, out)

    print("\n[2] Re-serialised header")
    h1 = dump_header(out, "out ")

    # ── 3. Header-level assertions (the alignment that matters) ───────────────
    print("\n[3] Header checks")
    all_ok = True
    all_ok &= check("magic preserved", h1["magic"] == h0["magic"])
    all_ok &= check("vert/adj/surf/idx counts preserved",
                    h1["counts"] == h0["counts"],
                    f"{h1['counts']} vs {h0['counts']}")
    all_ok &= check("TextureCount preserved",
                    h1["tex_count"] == h0["tex_count"],
                    f"{h1['tex_count']} vs {h0['tex_count']}")
    all_ok &= check("first texture name starts at offset 52 (no shift)",
                    h1["first_name"] == h0["first_name"],
                    f"{h1['first_name']!r} vs {h0['first_name']!r}")
    all_ok &= check("padding is zero", h1["padding"] == 0, str(h1["padding"]))
    all_ok &= check("flags low byte preserved (minus PLANES)",
                    h1["flags"] == (h0["flags"] & ~MeshFlags.PLANES),
                    f"{_flag_str(h1['flags'])} vs orig {_flag_str(h0['flags'])}")

    # ── 4. Re-read output and compare every parsed field ──────────────────────
    print("\n[4] Re-parse + field comparison")
    d1 = read_bms(out)

    def cmp_field(name, transform=lambda x: x):
        a, b = transform(d0.get(name)), transform(d1.get(name))
        return check(f"{name} round-trips", a == b,
                     "" if a == b else f"len {len(d0.get(name) or [])} vs {len(d1.get(name) or [])}")

    all_ok &= cmp_field("texture_names")
    all_ok &= cmp_field("num_adjuncts")
    all_ok &= cmp_field("num_surfaces")
    all_ok &= cmp_field("vertex_indices")
    all_ok &= cmp_field("texture_indices")
    all_ok &= cmp_field("surface_indices")
    all_ok &= cmp_field("normal_indices")
    # Vertex positions: compare with tolerance (float repack is exact, but be safe).
    pts_ok = len(d0["points"]) == len(d1["points"]) and all(
        all(abs(a - b) < 1e-5 for a, b in zip(p0, p1))
        for p0, p1 in zip(d0["points"], d1["points"])
    )
    all_ok &= check("vertex positions round-trip", pts_ok)

    print("\n" + "=" * 72)
    print("RESULT:", "ALL CHECKS PASSED" if all_ok else "FAILURES DETECTED")
    print("=" * 72)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

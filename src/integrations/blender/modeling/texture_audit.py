"""
Texture / TSH audit (Blender-free).

The most common in-game failure mode for custom content is "the object loads but is
invisible or black". It happens when a BMS mesh references a texture name that is
either (a) not declared in any texture sheet (TSH) the game loads, or (b) has no DDS
on disk, or (c) is an alpha texture sitting in the opaque folder (TEX16O) so its
cut-out renders as a black box.

This module walks the built BMS, collects every referenced texture name, and checks
each against the TSH declarations + the DDS search folders. It is pure Python (uses
the bpy-free read_bms) so it can run in the build pipeline or behind a Blender op.

The engine resolves a texture by FILENAME along the search path tex16a -> tex16o, and
finds the per-name TSH row to decide render flags, so a name needs BOTH a DDS file and
a TSH row. Base-game textures (declared in GLOBAL.TSH) live in core.ar and are assumed
present even without a local DDS.
"""
import struct
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from src.integrations.blender.modeling.meshes import read_bms


def dds_has_alpha(path: Path) -> Optional[bool]:
    """True if the DDS carries per-pixel alpha (DDPF_ALPHA* or DXT3/DXT5). None on error."""
    try:
        with open(path, "rb") as f:
            head = f.read(128)
    except OSError:
        return None

    if len(head) < 88 or head[:4] != b"DDS ":
        return None

    pf_flags = struct.unpack_from("<I", head, 80)[0]   # DDS_PIXELFORMAT.dwFlags
    fourcc = head[84:88]

    if pf_flags & (0x1 | 0x2):                          # DDPF_ALPHAPIXELS | DDPF_ALPHA
        return True
    if fourcc in (b"DXT3", b"DXT5"):
        return True
    return False


def collect_referenced_textures(bms_root: Path) -> Dict[str, List[str]]:
    """Map UPPER texture name to the list of BMS filenames that reference it (recursive)."""
    refs: Dict[str, List[str]] = {}
    root = Path(bms_root)
    if not root.is_dir():
        return refs

    for bms in sorted(root.rglob("*.BMS")):
        try:
            data = read_bms(bms)
        except Exception:
            continue
        for tex in data.get("texture_names", []):
            refs.setdefault(tex.upper().strip(), []).append(bms.name)

    return refs


def parse_tsh_names(tsh_path: Path) -> Set[str]:
    """UPPER texture names declared in a TSH CSV (skips the header row)."""
    names: Set[str] = set()
    path = Path(tsh_path)
    if not path.is_file():
        return names

    for i, line in enumerate(path.read_text(encoding="ascii", errors="replace").splitlines()):
        if i == 0 or not line.strip():
            continue
        names.add(line.split(",")[0].strip().upper())

    return names


def locate_dds(name: str, folders: List[Tuple[str, Path]]) -> Optional[Tuple[str, Path]]:
    """First (label, path) whose folder contains {name}.dds, searched in order."""
    for label, folder in folders:
        for ext in (".DDS", ".dds"):
            candidate = Path(folder) / f"{name}{ext}"
            if candidate.is_file():
                return (label, candidate)
    return None


def audit_textures(bms_root: Path, map_tsh_paths: List[Path], global_tsh_path: Path,
                   tex_folders: List[Tuple[str, Path]], packed_labels: Optional[Set[str]] = None) -> dict:
    """Audit every texture referenced by the BMS under bms_root.

    tex_folders: (label, Path) in search order, e.g. [("TEX16A", ...), ("TEX16O", ...),
    ("resources", ...)].
    packed_labels: labels that are part of the BUILD output (e.g. {"TEX16A","TEX16O"}).
    The "undeclared in TSH" warning only fires for a texture whose DDS resolves from a
    packed folder, because stock textures resolved from resources are declared in
    per-car/city TSHs inside core.ar (not on disk), so flagging them would be noise.
    Pass None to treat every folder as packed.

    Returns a report dict with lists:
      missing     - referenced, no DDS found AND not a base-game (GLOBAL.TSH) texture
      undeclared  - packed DDS present but no TSH row (likely invisible in-game)
      alpha_split - alpha texture found only in an opaque (..16O) folder (may render black)
      ok          - count that passed
    """
    refs = collect_referenced_textures(bms_root)

    global_declared = parse_tsh_names(global_tsh_path)
    map_declared: Set[str] = set()
    for tsh in map_tsh_paths:
        map_declared |= parse_tsh_names(tsh)
    declared = global_declared | map_declared

    missing, undeclared, alpha_split = [], [], []
    ok = 0

    for name, users in sorted(refs.items()):
        loc = locate_dds(name, tex_folders)

        if loc is None:
            if name in global_declared:        # base-game textures live in core.ar
                ok += 1
            else:
                missing.append((name, users))
            continue

        label, path = loc
        is_packed = packed_labels is None or label in packed_labels
        flagged = False

        if is_packed and name not in declared:
            undeclared.append((name, label, users))
            flagged = True
        if dds_has_alpha(path) is True and label.upper().endswith("16O"):
            alpha_split.append((name, label))
            flagged = True

        if not flagged:
            ok += 1

    return {
        "referenced":  len(refs),
        "ok":          ok,
        "missing":     missing,
        "undeclared":  undeclared,
        "alpha_split": alpha_split,
    }


def format_report(report: dict) -> str:
    """Human-readable multi-line report (ASCII only, safe for the Windows console)."""
    lines = [
        f"Texture audit: {report['referenced']} referenced, {report['ok']} OK, "
        f"{len(report['missing'])} missing, {len(report['undeclared'])} undeclared, "
        f"{len(report['alpha_split'])} alpha-in-opaque.",
    ]

    if report["missing"]:
        lines.append("\n[MISSING DDS - will be invisible/untextured]")
        for name, users in report["missing"]:
            lines.append(f"  {name}   <- {', '.join(sorted(set(users))[:4])}")

    if report["undeclared"]:
        lines.append("\n[NOT IN ANY TSH - likely invisible in-game]")
        for name, label, users in report["undeclared"]:
            lines.append(f"  {name}  (DDS in {label})   <- {', '.join(sorted(set(users))[:4])}")

    if report["alpha_split"]:
        lines.append("\n[ALPHA TEXTURE IN OPAQUE FOLDER - may render as a black box]")
        for name, label in report["alpha_split"]:
            lines.append(f"  {name}  (in {label}; move to TEX16A)")

    if not (report["missing"] or report["undeclared"] or report["alpha_split"]):
        lines.append("\nAll referenced textures resolve.")

    return "\n".join(lines)

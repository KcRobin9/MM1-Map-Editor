"""Car Editor — paint module (split from the former car_editor.py monolith)."""
import os
from pathlib import Path
from collections import Counter

from src.integrations.blender.modeling.meshes import _build_material

from src.integrations.blender.operators.car_editor.constants import _GENERIC_TEXTURES


# Per-session cache: keyed by (car_name, tex_folder_str) → list[str]
_paint_variant_cache: dict = {}


def _car_paint_texture_names(body_mesh) -> list:
    """Non-generic, car-specific textures that belong to a paint scheme."""
    return [
        t for t in (body_mesh.get("texture_names") or [])
        if t not in _GENERIC_TEXTURES and "_" in t
    ]


def _detect_paint_prefix(body_mesh) -> str:
    """
    Return the colour-variant prefix for this car's body textures.
    E.g. 'VPPANOZGREEN', 'VPF350BLUE'.  Returns '' when detection fails.

    Uses the most-common prefix among non-generic, non-DMG textures so that
    shared base textures like VPF350_BD (prefix 'VPF350') don't pollute the
    result when the majority of textures use e.g. 'VPF350BLUE'.
    """
    specific = [t for t in _car_paint_texture_names(body_mesh)
                if not t.upper().endswith("_DMG")]
    if not specific:
        return ""
    counts = Counter(t.split("_")[0] for t in specific)
    prefix, freq = counts.most_common(1)[0]
    # Require the most-common prefix to cover at least half the specific textures.
    return prefix if freq * 2 >= len(specific) else ""


def _find_paint_variants(body_mesh, tex_folder: Path, current_prefix: str) -> list:
    """
    Return a sorted list of all paint-variant prefixes available in tex_folder
    for this car, e.g. ['VPBULLET', 'VPBULLETBLUE', 'VPBULLETRED', 'VPBULLETWHITE'].
    Returns [] when only one variant exists or detection fails.

    Works by trying progressively shorter base prefixes (from the full
    current_prefix down to 4 chars) and returning the set of variants that
    yields the most complete matches.  This handles both:
      - Strategy A: current_prefix IS the base (e.g. VPBULLET has siblings
        VPBULLETBLUE, VPBULLETRED …).
      - Strategy B: current_prefix contains a colour suffix (e.g. VPPANOZGREEN
        → base VPPANOZ has siblings VPPANOZBLUE, VPPANOZMAGENTA, VPPANOZRED).
    """
    if not current_prefix:
        return []

    cp = current_prefix.upper()

    # Only use textures whose prefix matches current_prefix to derive required
    # suffixes.  This excludes shared base textures like VPF350_BD (prefix
    # "VPF350") when the variant prefix is "VPF350BLUE".
    variant_specific = [
        t for t in _car_paint_texture_names(body_mesh)
        if not t.upper().endswith("_DMG") and t.upper().split("_")[0] == cp
    ]
    if not variant_specific:
        return []

    suffixes = frozenset("_" + "_".join(t.split("_")[1:]) for t in variant_specific)

    try:
        existing = {p.stem.upper() for p in tex_folder.iterdir()
                    if p.suffix.upper() == ".DDS"}
    except OSError:
        return []

    # Try every base length from len(cp) down to 4.
    # Keep the result with the most valid variants found at any length.
    best: list = []
    for length in range(len(cp), 3, -1):
        base = cp[:length]
        cand_prefixes = {
            s.split("_")[0]
            for s in existing
            if "_" in s and s.split("_")[0].startswith(base)
        }
        valid = sorted(
            p for p in cand_prefixes
            if all((p + s) in existing for s in suffixes)
        )
        if len(valid) > len(best):
            best = valid

    return best if len(best) > 1 else []


def _find_paint_variants_cached(car_name: str, body_mesh,
                                tex_folder: Path, current_prefix: str) -> list:
    key = (car_name, str(tex_folder))
    if key not in _paint_variant_cache:
        _paint_variant_cache[key] = _find_paint_variants(body_mesh, tex_folder, current_prefix)
    return _paint_variant_cache[key]


def _variant_color_name(variant: str, all_variants: list) -> str:
    """
    Derive a human-readable colour label, e.g. 'VPBULLETBLUE' → 'Blue'.
    Uses the longest common prefix of all variants as the base car name.
    """
    base = os.path.commonprefix(all_variants)
    color = variant[len(base):]
    return color.title() if color else "Default"


def _build_paint_chain(body_mesh, tex_folder: Path) -> list:
    """
    Ordered paint-variant prefixes for the body, current/default first, e.g.
    ['VPBULLET', 'VPBULLETBLUE', 'VPBULLETRED', 'VPBULLETWHITE']. Returns [] when
    the body has no detectable colour variants. Used to wire the TSH sibling chain
    so the variants are selectable as paint jobs in the game's car menu.
    """
    prefix = _detect_paint_prefix(body_mesh)
    if not prefix:
        return []
    variants = _find_paint_variants(body_mesh, tex_folder, prefix)
    if len(variants) < 2:
        return []
    cur = prefix.upper()
    return [cur] + [v.upper() for v in variants if v.upper() != cur]


def _apply_paint_variant(car_objects: list, new_prefix: str,
                         current_prefix: str, tex_folder: Path) -> int:
    """
    For every material whose name starts with current_prefix, replace it with the
    equivalent material using new_prefix.  Handles both normal and _DMG slots.
    Returns the number of material slots successfully swapped.
    """
    seen   = set()
    count  = 0
    cp_up  = current_prefix.upper()

    for obj in car_objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        if id(mesh) in seen:
            continue
        seen.add(id(mesh))

        for i, mat in enumerate(mesh.materials):
            if mat is None or not mat.name.upper().startswith(cp_up):
                continue
            suffix   = mat.name[len(current_prefix):]   # e.g. '_FT' or '_FT_DMG'
            new_name = new_prefix + suffix
            dds      = tex_folder / f"{new_name}.DDS"
            if not dds.exists():
                dds = tex_folder / f"{new_name}.dds"
            if not dds.exists():
                continue
            mesh.materials[i] = _build_material(new_name, tex_folder)
            count += 1

    return count

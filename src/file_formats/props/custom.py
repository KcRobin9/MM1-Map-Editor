"""
Copy custom-city prop assets into the SHOP folder so a map that uses props from a
community city (e.g. Box Design Raceway) actually works in-game.

Stock props live in the base game's core.ar and are never repacked. Custom props
are NOT in the base game, so every custom prop placed in the map needs its mesh,
collision bound, banger tune and textures packed into the map's own .ar.
"""
import shutil
from pathlib import Path
from typing import Iterable, List, Set

from src.constants.folder import Folder
from src.constants.custom_props import get_custom_city, custom_city_of_prop
from src.integrations.blender.modeling.meshes import read_bms
from src.ui.console import ok, sep, item


def _used_custom_props(prop_list: list, random_props: list) -> Set[str]:
    """Collect the lowercased ids of every custom prop referenced by the map."""
    names: Set[str] = set()

    def _add(value) -> None:
        if isinstance(value, (list, tuple)):
            for v in value:
                _add(v)
        elif isinstance(value, str):
            names.add(value.lower())

    for cfg in list(prop_list) + list(random_props):
        _add(cfg.get("name", ""))

    return {n for n in names if custom_city_of_prop(n)}


def _copy_prop_textures(texture_root: Path, mesh_dir: Path) -> int:
    """Copy the DDS textures referenced by a prop's high-LOD mesh into SHOP,
    preserving the TEX16A (alpha) / TEX16O (opaque) split. Standard textures that
    the base game already provides are not in texture_root and are skipped."""
    high = mesh_dir / "H.BMS"
    if not high.exists():
        return 0

    try:
        tex_names = read_bms(high).get("texture_names", [])
    except Exception as exc:
        item(f"Could not read textures from {high.name}: {exc}")
        return 0

    copied = 0
    for tex in tex_names:
        for sub, shop in (("TEX16A", Folder.Shop.Textures.Alpha),
                          ("TEX16O", Folder.Shop.Textures.Opaque)):
            # Base texture + its optional normal map (engine loads "<name>_N" by suffix).
            for candidate in (f"{tex}.DDS", f"{tex}_N.DDS"):
                src = texture_root / sub / candidate
                if src.exists():
                    shop.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, shop / candidate)
                    copied += 1

    return copied


def copy_custom_prop_assets_to_shop(prop_list: list, random_props: list, set_props: bool) -> None:
    """
    For every custom-city prop placed in the map, copy its mesh (all LODs),
    collision bound, banger tune and textures into the matching SHOP folders.
    """
    if not set_props:
        return

    used = _used_custom_props(prop_list, random_props)
    if not used:
        return

    copied_props: List[str] = []
    missing: List[str] = []
    tex_total = 0

    for prop_id in sorted(used):
        city = get_custom_city(custom_city_of_prop(prop_id))
        name = prop_id.upper()

        mesh_src = city.mesh_root / name
        if not mesh_src.is_dir():
            missing.append(name)
            continue

        # ── Mesh (H/M/L/VL) ───────────────────────────────────────────────────
        mesh_dst = Folder.Shop.Meshes / name
        mesh_dst.mkdir(parents=True, exist_ok=True)
        for bms in mesh_src.glob("*.BMS"):
            shutil.copy(bms, mesh_dst / bms.name)

        # ── Collision bound (optional — flat billboards/logos have none) ──────
        bnd = city.bnd_root / f"{name}_BND.BND"
        if bnd.exists():
            Folder.Shop.Bound.mkdir(parents=True, exist_ok=True)
            shutil.copy(bnd, Folder.Shop.Bound / bnd.name)

        # ── Banger tune (mass / breakability) ─────────────────────────────────
        tune = city.tune_root / f"{name}.MMBANGERDATA"
        if tune.exists():
            Folder.Shop.Tune.mkdir(parents=True, exist_ok=True)
            shutil.copy(tune, Folder.Shop.Tune / tune.name)

        # ── Textures ──────────────────────────────────────────────────────────
        tex_total += _copy_prop_textures(city.texture_root, mesh_src)

        copied_props.append(name)

    ok(f"Copied custom prop assets{sep()}{len(copied_props)} prop(s), {tex_total} texture(s)")
    if copied_props:
        item(", ".join(copied_props))
    for name in missing:
        item(f"No mesh found for custom prop '{name}'")

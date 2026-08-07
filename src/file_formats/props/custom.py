"""
Copy custom-city prop assets into the SHOP folder so a map that uses props from a
community city (e.g. Box Design Raceway) actually works in-game.

Stock props live in the base game's core.ar and are never repacked. Custom props
are NOT in the base game, so every custom prop placed in the map needs its mesh,
collision bound, banger tune and textures packed into the map's own .ar.
"""
import struct
import shutil
from pathlib import Path
from typing import Iterable, List, Set

from src.constants.folder import Folder
from src.constants.file_formats import FileType
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


def _copy_prop_textures(texture_root: Path, mesh_dir: Path) -> Set[str]:
    """Copy the DDS textures referenced by a prop's high-LOD mesh into SHOP,
    preserving the TEX16A (alpha) / TEX16O (opaque) split. Standard textures that
    the base game already provides are not in texture_root and are skipped.

    Returns the set of custom texture names (the BMS-referenced names found in the
    store) so they can be registered in the texture sheet."""
    high = mesh_dir / "H.BMS"
    if not high.exists():
        return set()

    try:
        tex_names = read_bms(high).get("texture_names", [])
    except Exception as exc:
        item(f"Could not read textures from {high.name}: {exc}")
        return set()

    registered: Set[str] = set()
    for tex in tex_names:
        for sub, shop in (("TEX16A", Folder.Shop.Textures.Alpha),
                          ("TEX16O", Folder.Shop.Textures.Opaque)):
            # Base texture + its optional normal map (engine loads "<name>_N" by suffix).
            for candidate in (f"{tex}.DDS", f"{tex}_N.DDS"):
                src = texture_root / sub / candidate
                if src.exists():
                    shop.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, shop / candidate)
                    if candidate == f"{tex}.DDS":
                        registered.add(tex)

    return registered


def _dds_dimensions(path: Path) -> tuple:
    """(width, height) from a DDS header; falls back to 64x64 on any problem."""
    try:
        with open(path, "rb") as f:
            head = f.read(20)
        if head[:4] != b"DDS ":
            return (64, 64)
        height, width = struct.unpack_from("<II", head, 12)  # dwHeight, dwWidth
        return (width or 64, height or 64)
    except Exception:
        return (64, 64)


def _register_textures_in_tsh(tex_names: Set[str]) -> int:
    """Append rows for custom prop textures to the map's texture sheet so the game
    can resolve them by name. The TSH is written earlier in the pipeline, so we
    append after the fact. No-op when the TSH doesn't exist (set_texture_sheet off)."""
    if not tex_names:
        return 0

    tsh = Folder.Shop.Material / f"GLOBAL{FileType.TEXTURE_SHEET}"
    if not tsh.exists():
        item("No texture sheet in SHOP — custom prop textures not registered "
             "(set_texture_sheet must be True for custom prop textures to render)")
        return 0

    existing = {line.split(",")[0].strip() for line in tsh.read_text().splitlines()}

    added = 0
    with open(tsh, "a") as f:
        for tex in sorted(tex_names):
            if tex in existing:
                continue
            is_alpha = (Folder.Shop.Textures.Alpha / f"{tex}.DDS").exists()
            if is_alpha:
                w, h = _dds_dimensions(Folder.Shop.Textures.Alpha / f"{tex}.DDS")
            else:
                w, h = _dds_dimensions(Folder.Shop.Textures.Opaque / f"{tex}.DDS")
            # Alpha cutout textures need the 't' (Transparent) flag so the engine enables
            # alpha blending; without it they render as solid black rectangles.
            flags = "t" if is_alpha else ""
            # name,neighborhood,h,m,l,flags,alternate,sibling,xres,yres,hexcolor
            f.write(f"{tex},0,0,0,1,{flags},{tex},,{w},{h},000000\n")
            added += 1

    return added


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
    custom_textures: Set[str] = set()

    for prop_id in sorted(used):
        city = get_custom_city(custom_city_of_prop(prop_id))
        name = prop_id.upper()

        mesh_src = city.mesh_root / name
        if not mesh_src.is_dir():
            missing.append(name)
            continue

        # ── Mesh (H/M/L/VL) ───────────────────────────────────────────────────
        # The BNG references the banger by its LOWERCASE id and the game's AR lookup
        # is case-sensitive (core.ar stores banger geometry lowercase, e.g.
        # bms/tp_tree10m/). The source folder on disk is uppercase, so copy it into a
        # LOWERCASE SHOP folder to match the reference — otherwise the prop loads but
        # is invisible (geometry path never resolves).
        mesh_dst = Folder.Shop.Meshes / prop_id
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
        custom_textures |= _copy_prop_textures(city.texture_root, mesh_src)

        copied_props.append(name)

    # Register the custom textures in the map's texture sheet so the game resolves
    # them by name (copying the DDS alone is not enough).
    registered = _register_textures_in_tsh(custom_textures)

    ok(f"Copied custom prop assets{sep()}{len(copied_props)} prop(s), "
       f"{len(custom_textures)} texture(s), {registered} registered in TSH")
    if copied_props:
        item(", ".join(copied_props))
    for name in missing:
        item(f"No mesh found for custom prop '{name}'")

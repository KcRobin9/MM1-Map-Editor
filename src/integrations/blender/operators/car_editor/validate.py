"""Car Editor — validate module (split from the former car_editor.py monolith)."""
from src.constants.folder import Folder
from src.constants.file_formats import FileType

from src.integrations.blender.operators.car_editor.common import (
    _base_car_name, _get_trailer_parts, _has_custom_trailer, _is_original_car, _tex_folder,
    get_car_body, get_car_objects,
)
from src.integrations.blender.operators.car_editor.lights import (
    _get_siren_housing_objs, _get_siren_light_objs,
)
from src.integrations.blender.operators.car_editor.constants import _CAR_TAG, _GENERIC_TEXTURES


def _validate_car(context) -> tuple:
    """
    Pre-flight checks for the loaded car. Returns (errors, warnings) — errors
    block packing (would crash / not appear in-game), warnings are advisory.
    """
    errors:   list = []
    warnings: list = []

    car_objects = get_car_objects()
    if not car_objects:
        return (["No car loaded — use Load Car or New From Template."], [])

    body = get_car_body()
    if body is None:
        errors.append("No body part — tag a mesh as the body.")
    elif not body.data.polygons:
        errors.append("Body mesh has no faces.")

    nfaces = sum(len(o.data.polygons) for o in car_objects if o.type == "MESH")
    if nfaces > 12000:
        warnings.append(f"High poly count ({nfaces} faces) — MM1 may slow or fail to load.")

    # ── Wheels ────────────────────────────────────────────────────────────────
    wheels = [o for o in car_objects if o.get(_CAR_TAG, "").startswith("wheel_")]
    idxs = sorted(int(o.get(_CAR_TAG).split("_")[1]) for o in wheels
                  if o.get(_CAR_TAG, "").split("_")[1].isdigit())
    if not wheels:
        warnings.append("No wheels tagged — the car will have none in-game.")
    else:
        if len(wheels) not in (4, 6):
            warnings.append(f"{len(wheels)} wheels — MM1 expects 4 or 6 (others may misbehave).")
        if idxs != list(range(len(idxs))):
            warnings.append(f"Wheel indices have gaps {idxs} — use Renumber (fill gaps).")

    # ── Materials / textures ──────────────────────────────────────────────────
    tex_folder = _tex_folder(context.scene)
    empty_slots = 0
    missing: set = set()
    for o in car_objects:
        if o.type != "MESH":
            continue
        if not o.data.materials:
            empty_slots += 1
            continue
        for mat in o.data.materials:
            if mat is None:
                empty_slots += 1
                continue
            name = mat.name.upper()
            if name in _GENERIC_TEXTURES or name == "CARBOTTOM" or name.startswith("FXLT"):
                continue
            if not (tex_folder / f"{name}.DDS").exists() and not (tex_folder / f"{name}.dds").exists():
                missing.add(mat.name)
    if empty_slots:
        warnings.append(f"{empty_slots} empty material slot(s) — those faces export as CARBOTTOM.")
    if missing:
        shown = ", ".join(sorted(missing)[:6]) + ("…" if len(missing) > 6 else "")
        warnings.append(f"{len(missing)} texture(s) missing from editor TEXTURES: {shown} "
                        "(must exist in the game or the car renders untextured).")

    # ── Texture-count soft ceiling ────────────────────────────────────────────
    used_tex = {mat.name.upper() for o in car_objects if o.type == "MESH"
                for mat in o.data.materials if mat}
    if len(used_tex) > 64:
        warnings.append(f"{len(used_tex)} distinct textures — large TSH; consider consolidating "
                        "to keep load time and memory sane.")

    # ── Trailer integrity (custom trailer in the scene) ───────────────────────
    if _has_custom_trailer():
        t_parts  = _get_trailer_parts()
        if not any(o.get(_CAR_TAG) == "trailer_body" for o in t_parts):
            warnings.append("Custom trailer has no trailer_body — it won't render in-game.")
        if not any(o.get(_CAR_TAG, "").startswith("trailer_wheel_") for o in t_parts):
            warnings.append("Custom trailer has no wheels — it may drag on the ground in-game.")

    # ── Siren bar consistency ─────────────────────────────────────────────────
    siren_lenses  = _get_siren_light_objs()
    siren_housing = _get_siren_housing_objs()
    siren_enabled = bool(siren_lenses or siren_housing or getattr(context.scene, "ce_add_siren", False))
    if (siren_lenses or siren_housing) and not (siren_lenses and siren_housing):
        warnings.append("Siren bar incomplete — reload it via 'Load Siren Lights' so both the "
                        "housing and the red/blue flash lenses are present.")

    # ── Custom-car SHOP support files ─────────────────────────────────────────
    car_name = _base_car_name(body.get("mm_car_name", "")) if body is not None else ""
    if car_name and not _is_original_car(car_name):
        # .INFO is the discovery file — without it the car never appears in the menu.
        if not (Folder.Shop.Tune / f"{car_name}.INFO").exists():
            errors.append(f"Custom car '{car_name}' has no .INFO — run 'Init Support Files' or "
                          "'Save Loaded Car as Custom' first (else it won't appear in the menu).")

        # DLP/BND/TSH/audio are regenerated on every pack, so only flag a PARTIAL
        # SHOP state: the body is already staged but a critical sibling is missing
        # (the failure mode behind the earlier ferris-wheel / no-light bugs).
        if (Folder.Shop.Meshes / car_name / "BODY_H.BMS").exists():
            staged = {
                "DLP (wheel spin pivots)": Folder.Shop.DLP / f"{car_name}{FileType.DEVELOPMENT}",
                "BND (collision)":         Folder.Shop.Bound / f"{car_name}_BND.BND",
                "TSH (texture sheet)":     Folder.Shop.Material / f"{car_name}{FileType.TEXTURE_SHEET}",
            }
            for label, path in staged.items():
                if not path.exists():
                    warnings.append(f"SHOP is missing the {label} for '{car_name}' — re-pack to regenerate.")
            if siren_enabled and not (Folder.Shop.Tune / f"{car_name}.MMPLAYERCARAUDIO").exists():
                warnings.append("Siren is enabled but no MMPLAYERCARAUDIO is staged — re-pack "
                                "(the siren audio is generated during packing).")

    return errors, warnings

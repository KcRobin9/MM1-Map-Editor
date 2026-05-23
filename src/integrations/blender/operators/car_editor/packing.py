"""Car Editor — packing module (split from the former car_editor.py monolith)."""
import os
import re
import shutil
import subprocess

from src.constants.folder import Folder
from src.constants.car_assets import LightColor
from src.constants.file_formats import FileType
from src.integrations.blender.modeling.meshes import read_bms
from src.integrations.blender.modeling.bms_writer import write_bms
from src.integrations.blender.modeling.car_bnd import generate_car_bnd
from src.integrations.blender.modeling.car_dlp import generate_car_dlp, generate_trailer_dlp

from src.integrations.blender.operators.car_editor.paint import (
    _build_paint_chain, _variant_color_name,
)
from src.integrations.blender.operators.car_editor.common import (
    _copy_files_to_shop, _is_original_car, get_car_body,
)

# Filename prefix for editor-generated car ARs. Ten '!' (the lowest printable ASCII)
# sorts the AR earliest so it wins the override, and uniquely tags our cars so
# "Clean AR" can remove only them (never the base game's !1560.ar / 1560.ar / etc.).
CAR_AR_PREFIX = "!" * 10


def _pack_car_ar(car_name: str, minimal: bool = False) -> bool:
    """
    Pack the car's files from SHOP into !!!!!{car_name}.ar in MidtownMadness/.

    Collects from the standard SHOP subdirs:
      SHOP/BMS/{NAME}/*            → BMS/{NAME}/* in AR
      SHOP/TUNE/{NAME}*            → TUNE/*        in AR
      SHOP/MTL/{NAME}.TSH          → MTL/*         in AR
      SHOP/BND/{NAME}_BND.BND     → BND/*         in AR

    When ``minimal`` is True only BMS/{NAME}/ is packed (editing an existing
    game car): the original TSH, dashboard, textures and collision remain in
    effect, so we override geometry only — no TUNE/MTL/BND/TEX16A/_DASH.

    A temp staging tree is assembled so mkar receives correct relative paths.
    The !!!!!-prefix ensures the file loads last, overriding any prior copy.
    """

    mm1_folder   = Folder.MidtownMadness.Root
    mkar_exe     = Folder.Angel / "mkar.exe"

    if not mkar_exe.exists():
        print(f"[Car Editor] mkar.exe not found at {mkar_exe}")
        return False

    car_bms_dir = Folder.Shop.Meshes / car_name
    if not car_bms_dir.is_dir():
        print(f"[Car Editor] No BMS folder: {car_bms_dir}")
        return False

    bms_files = sorted(f for f in car_bms_dir.iterdir() if f.is_file())
    if not bms_files:
        print(f"[Car Editor] No BMS files in {car_bms_dir}")
        return False

    ar_name = f"{CAR_AR_PREFIX}{car_name}.ar"
    ar_out  = mm1_folder / ar_name
    tmp_dir = Folder.BASE / f"_car_pack_tmp_{car_name}"

    try:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True)

        # BMS meshes → BMS/{NAME}/
        bms_dst = tmp_dir / "BMS" / car_name
        bms_dst.mkdir(parents=True)
        for f in bms_files:
            shutil.copy2(f, bms_dst / f.name)

        # mmDamage::InitDamage hardcodes Meshes[2] = _M body; NULL crashes damage.c:14
        body_h = bms_dst / "BODY_H.BMS"
        body_m = bms_dst / "BODY_M.BMS"
        if body_h.exists() and not body_m.exists():
            shutil.copy2(body_h, body_m)

        # Physics override (existing-car retune): if the user enabled Override
        # Physics, a patched {NAME}.MMCARSIM was staged in SHOP/TUNE — include it
        # even in minimal mode so the new handling reaches the game. Geometry-only
        # edits never create this file, so normal minimal packs are unaffected.
        if minimal:
            carsim = Folder.Shop.Tune / f"{car_name}.MMCARSIM"
            if carsim.exists():
                tune_dst = tmp_dir / "TUNE"
                tune_dst.mkdir(exist_ok=True)
                shutil.copy2(carsim, tune_dst / carsim.name)

        # Vehicle Showcase image (BMP16/{NAME}_SHOW.JPG) — the picker's "Vehicle
        # Showcase" photo. Packed in both modes (a tweaked stock car can override
        # its stock photo too); only present when the user generated one.
        show_jpg = Folder.Shop.Textures.Bitmap / f"{car_name.upper()}_SHOW.JPG"
        if show_jpg.exists():
            bmp_dst = tmp_dir / "BMP16"
            bmp_dst.mkdir(exist_ok=True)
            shutil.copy2(show_jpg, bmp_dst / show_jpg.name)

        # Everything below (dash, tune, TSH, collision, textures) is only packed
        # for brand-new cars.  For an existing game car we override geometry only
        # and let the base AR supply the rest — see _is_original_car.
        if not minimal:
            # Dashboard sub-folder BMS/{NAME}_DASH/ — the game loads this separately
            # from the main BMS folder; if not overridden the original AR's dash meshes
            # remain active and reference textures not declared in our TSH.
            dash_shop = Folder.Shop.Meshes / f"{car_name}_DASH"
            if dash_shop.is_dir():
                dash_dst = tmp_dir / "BMS" / f"{car_name}_DASH"
                dash_dst.mkdir(parents=True)
                for f in sorted(dash_shop.iterdir()):
                    if f.is_file():
                        shutil.copy2(f, dash_dst / f.name)

            # Trailer sub-car BMS/{NAME}_TRAILER/ — the game loads the trailer as
            # a separate vehicle named "{NAME}_trailer" (mmTrailer::Init).
            trailer_shop = Folder.Shop.Meshes / f"{car_name}_TRAILER"
            if trailer_shop.is_dir():
                trailer_dst = tmp_dir / "BMS" / f"{car_name}_TRAILER"
                trailer_dst.mkdir(parents=True)
                for f in sorted(trailer_shop.iterdir()):
                    if f.is_file():
                        shutil.copy2(f, trailer_dst / f.name)

            # TUNE files whose name starts with car_name → TUNE/
            tune_src = Folder.Shop.Tune
            if tune_src.is_dir():
                tune_dst = tmp_dir / "TUNE"
                tune_dst.mkdir()
                for f in sorted(tune_src.iterdir()):
                    if f.is_file() and f.name.upper().startswith(car_name.upper()):
                        shutil.copy2(f, tune_dst / f.name)

            # TSH texture sheet → MTL/
            tsh_src = Folder.Shop.Material / f"{car_name}{FileType.TEXTURE_SHEET}"
            if tsh_src.exists():
                mtl_dst = tmp_dir / "MTL"
                mtl_dst.mkdir()
                shutil.copy2(tsh_src, mtl_dst / tsh_src.name)

            # Collision → BND/ (car + optional trailer)
            bnd_dst = tmp_dir / "BND"
            for bnd_name in (f"{car_name}_BND.BND", f"{car_name}_TRAILER_BND.BND"):
                bnd_src = Folder.Shop.Bound / bnd_name
                if bnd_src.exists():
                    bnd_dst.mkdir(exist_ok=True)
                    shutil.copy2(bnd_src, bnd_dst / bnd_src.name)

            # Car DLP → DLP/{NAME}.DLP — the engine reads each wheel's spin pivot
            # (mmWheel::Center) from this file's WHLn_H group centroid. Without it
            # the wheels orbit the car origin ("ferris wheel"). The trailer DLP
            # ({NAME}_TRAILER.DLP) supplies the trailer's TWHL/TRAILER centroids.
            dlp_dst = tmp_dir / "DLP"
            for dlp_name in (f"{car_name}{FileType.DEVELOPMENT}",
                             f"{car_name}_TRAILER{FileType.DEVELOPMENT}"):
                dlp_src = Folder.Shop.DLP / dlp_name
                if dlp_src.exists():
                    dlp_dst.mkdir(exist_ok=True)
                    shutil.copy2(dlp_src, dlp_dst / dlp_src.name)

            # Wheel texture (and any other TEX16A assets) → TEX16A/
            tex16a_shop = Folder.Shop.Textures.Alpha
            if tex16a_shop.is_dir():
                tex_files = [f for f in tex16a_shop.iterdir()
                             if f.is_file() and f.suffix.upper() == ".DDS"]
                if tex_files:
                    tex_dst = tmp_dir / "TEX16A"
                    tex_dst.mkdir()
                    for f in tex_files:
                        shutil.copy2(f, tex_dst / f.name)

        pack_files = sorted(f for f in tmp_dir.rglob("*") if f.is_file())
        if not pack_files:
            print(f"[Car Editor] Nothing staged to pack for {car_name}")
            return False

        lines = [f"./{f.relative_to(tmp_dir).as_posix()}" for f in pack_files]
        shiplist_path = tmp_dir / f"shiplist.{car_name}"
        shiplist_path.write_bytes(("\n".join(lines) + "\n").encode("ascii"))

        # mkar auto-detects the LONGEST common path prefix across all shiplist
        # entries and strips it from the stored names.  When every file lives
        # under one subtree (e.g. a minimal pack with only BMS/{NAME}/*), that
        # common prefix is the whole directory, so entries get flattened to bare
        # filenames and the game can't find BMS/{NAME}/BODY_H.BMS.  Force the
        # prefix length to 2 so only the leading "./" is stripped and the real
        # BMS/.., TUNE/.., MTL/.. paths are preserved.
        print(f"[Car Editor] Packing {len(pack_files)} files → {ar_name} …")
        result = subprocess.run(
            [str(mkar_exe), str(ar_out), str(shiplist_path), "2"],
            cwd=str(tmp_dir),
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.stdout:
            print(f"[Car Editor] mkar: {result.stdout.strip()}")
        if result.stderr:
            print(f"[Car Editor] mkar: {result.stderr.strip()}")

        if result.returncode != 0:
            print(f"[Car Editor] mkar failed (exit {result.returncode})")
            return False

        print(f"[Car Editor] Created {ar_out}")
        return True

    finally:
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except OSError as e:
                print(f"[Car Editor] Warning: cleanup failed: {e}")


def _ensure_wheels_in_shop(car_name: str) -> int:
    """
    If no WHL*_H.BMS files exist in SHOP/BMS/{car_name}/, copy them from
    the VPMUSTANG99 reference in resources/editor/MESHES/CARS/VPMUSTANG99/.
    Returns the number of wheel files copied.
    """
    bms_dst = Folder.Shop.Meshes / car_name
    if list(bms_dst.glob("WHL*_H.BMS")):
        return 0  # already have wheels

    src_dir = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99"
    copied  = _copy_files_to_shop(src_dir, bms_dst, [f"WHL{i}_H.BMS" for i in range(10)])

    if copied:
        print(f"[Car Editor] No wheels tagged — copied {copied} VPMUSTANG99 wheels to SHOP/BMS/{car_name}/")
    return copied


def _ensure_lights_in_shop(car_name: str) -> int:
    """
    Refresh the stock light meshes (head/tail/brake/reverse/signals) in
    SHOP/BMS/{car_name}/ from the VPMUSTANG99 reference — a verbatim copy that
    preserves the original light-slot geometry. Edited/recoloured lights (when
    loaded in the scene) are written AFTER this by _export_car_lights, so they
    still take precedence; this just guarantees a known-good baseline.
    Returns the number of files copied.
    """
    src_dir = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99"
    return _copy_files_to_shop(
        src_dir, Folder.Shop.Meshes / car_name,
        ["HLIGHT_H.BMS", "TLIGHT.BMS", "BLIGHT.BMS", "RLIGHT.BMS", "SLIGHT0.BMS", "SLIGHT1.BMS"],
    )


def _ensure_dash_in_shop(car_name: str) -> int:
    """
    If SHOP/BMS/{car_name}_DASH/ doesn't exist or is empty, copy the dashboard
    BMS files from resources/editor/MESHES/CARS/VPMUSTANG99_DASH/.
    Returns the number of files copied.
    """
    dash_dst = Folder.Shop.Meshes / f"{car_name}_DASH"
    if dash_dst.is_dir() and any(dash_dst.iterdir()):
        return 0  # already populated

    src_dir = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99_DASH"
    if not src_dir.is_dir():
        return 0

    copied = _copy_files_to_shop(src_dir, dash_dst, [f.name for f in sorted(src_dir.glob("*.BMS"))])
    if copied:
        print(f"[Car Editor] Copied {copied} dash BMS files → SHOP/BMS/{car_name}_DASH/")
    return copied


def _ensure_trailer_in_shop(car_name: str) -> int:
    """
    Stage the stock VPSEMI trailer as this car's {NAME}_TRAILER sub-car in SHOP:
      BMS/{NAME}_TRAILER/      (TRAILER + TWHL0-3 + SHADOW + TLIGHT)
      DLP/{NAME}_TRAILER.DLP   (TRAILER_H + TWHL0-3_H centroids)
      BND/{NAME}_TRAILER_BND.BND

    The engine loads this as a separate vehicle "{NAME}_trailer" and hitches it
    on when the car's .INFO has the trailer flag (0x2). Returns BMS files staged.
    """
    SOURCE = "VPSEMI_TRAILER"
    editor = Folder.Resources.Editor

    bms_src = editor.MeshesCars / SOURCE
    bms_dst = Folder.Shop.Meshes / f"{car_name}_TRAILER"
    bms_dst.mkdir(parents=True, exist_ok=True)
    n = 0
    if bms_src.is_dir():
        for f in sorted(bms_src.glob("*.BMS")):
            shutil.copy2(f, bms_dst / f.name)
            n += 1

    dlp_src = editor.DLP / f"{SOURCE}{FileType.DEVELOPMENT}"
    if dlp_src.exists():
        Folder.Shop.DLP.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dlp_src, Folder.Shop.DLP / f"{car_name}_TRAILER{FileType.DEVELOPMENT}")

    bnd_src = editor.Bound / f"{SOURCE}_BND.BND"
    if bnd_src.exists():
        Folder.Shop.Bound.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bnd_src, Folder.Shop.Bound / f"{car_name}_TRAILER_BND.BND")

    if n:
        print(f"[Car Editor] Staged stock trailer → SHOP/BMS/{car_name}_TRAILER ({n} BMS files)")
    return n


def _generate_car_dlp_in_shop(car_name: str) -> bool:
    """
    Generate SHOP/DLP/{car}.DLP from the car's exported BMS by retargeting a
    template DLP's BODY_H/WHLn_H groups to the actual part bounds, so each wheel's
    spin pivot (DLP centroid) matches its real hub position.

    The template is chosen by wheel count: 5-6 wheels use VPSEMI (which has the
    WHL4_H/WHL5_H groups a 6-wheeler queries); otherwise VPMUSTANG99.
    Falls back to a verbatim template copy if generation fails.
    """

    bms_dir  = Folder.Shop.Meshes / car_name
    six_wheel = (bms_dir / "WHL4_H.BMS").exists()
    template_name = "VPSEMI" if six_wheel else "VPMUSTANG99"
    template = Folder.Resources.Editor.DLP / f"{template_name}{FileType.DEVELOPMENT}"
    dlp_dir  = Folder.Shop.DLP
    dlp_dir.mkdir(parents=True, exist_ok=True)
    out      = dlp_dir / f"{car_name}{FileType.DEVELOPMENT}"

    if not template.exists():
        print(f"[Car Editor] Template DLP missing: {template}")
        return False

    try:
        applied = generate_car_dlp(template, bms_dir, out)
        groups  = ", ".join(name for name, _ in applied)
        print(f"[Car Editor] Generated DLP ({template_name} base) → SHOP/DLP/{out.name} (retargeted: {groups})")
        return True
    except Exception as exc:
        print(f"[Car Editor] DLP generation failed ({exc}); copying {template_name} DLP verbatim")
        shutil.copy2(template, out)
        return False


def _generate_trailer_dlp_in_shop(car_name: str) -> bool:
    """
    Generate SHOP/DLP/{car}_TRAILER.DLP from the edited trailer BMS by retargeting
    the VPSEMI_TRAILER template's TRAILER_H + TWHLn_H groups to the actual part
    bounds, so the trailer body/wheel centroids match what the user edited.
    """

    bms_dir  = Folder.Shop.Meshes / f"{car_name}_TRAILER"
    template = Folder.Resources.Editor.DLP / f"VPSEMI_TRAILER{FileType.DEVELOPMENT}"
    out      = Folder.Shop.DLP / f"{car_name}_TRAILER{FileType.DEVELOPMENT}"

    if not template.exists():
        print(f"[Car Editor] Trailer template DLP missing: {template}")
        return False

    try:
        applied = generate_trailer_dlp(template, bms_dir, out)
        groups  = ", ".join(name for name, _ in applied)
        print(f"[Car Editor] Generated trailer DLP → SHOP/DLP/{out.name} (retargeted: {groups})")
        return True
    except Exception as exc:
        print(f"[Car Editor] Trailer DLP generation failed ({exc}); keeping stock trailer DLP")
        return False


def _generate_car_bnd_in_shop(car_name: str) -> bool:
    """
    Generate SHOP/BND/{car}_BND.BND sized to the car's actual body, so it collides
    at its real dimensions instead of as a copied VPMUSTANG99 box.

    Builds an 8-vertex box collision hull from the exported BODY_H.BMS car-space
    AABB (same format/edges/hot-verts as stock car bounds). Falls back to copying
    VPMUSTANG99_BND.BND if generation fails.
    """

    bms_dir = Folder.Shop.Meshes / car_name
    bnd_dir = Folder.Shop.Bound
    bnd_dir.mkdir(parents=True, exist_ok=True)
    out     = bnd_dir / f"{car_name}_BND.BND"

    if not (bms_dir / "BODY_H.BMS").exists():
        print(f"[Car Editor] BODY_H.BMS missing for {car_name}; skipping BND generation")
        return False

    try:
        info = generate_car_bnd(bms_dir, out)
        print(f"[Car Editor] Generated BND → SHOP/BND/{out.name} "
              f"(box r={info['radius']:.2f}, {info['edges']} edges)")
        return True
    except Exception as exc:
        print(f"[Car Editor] BND generation failed ({exc}); copying VPMUSTANG99 collision")
        src = Folder.Resources.Editor.Bound / "VPMUSTANG99_BND.BND"
        if src.exists():
            shutil.copy2(src, out)
        return False


def _generate_shadow_in_shop(car_name: str) -> bool:
    """
    Generate SHOP/BMS/{car}/SHADOW_H.BMS sized to the car's footprint so the ground
    shadow matches the real body instead of a copied VPMUSTANG99 one.

    Takes the stock VPMUSTANG99 shadow as a template (a flat VPFSHDW quad pair at
    ground level) and rescales its X (width) / Z (length) to the exported body's
    car-space AABB, keeping the UVs and surface structure intact.
    """
    bms_dir  = Folder.Shop.Meshes / car_name
    body_bms = bms_dir / "BODY_H.BMS"
    template = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99" / "SHADOW_H.BMS"
    if not body_bms.exists() or not template.exists():
        return False

    try:
        body = read_bms(body_bms)
        bpts = body["points"]
        xs = [p[0] for p in bpts]
        zs = [p[2] for p in bpts]
        body_x_half  = (max(xs) - min(xs)) / 2.0
        body_x_mid   = (max(xs) + min(xs)) / 2.0
        body_z_half  = (max(zs) - min(zs)) / 2.0
        body_z_mid   = (max(zs) + min(zs)) / 2.0

        shadow = read_bms(template)
        spts = shadow["points"]
        sx_half = max(abs(p[0]) for p in spts) or 1.0
        szs     = [p[2] for p in spts]
        sz_half = (max(szs) - min(szs)) / 2.0 or 1.0
        sz_mid  = (max(szs) + min(szs)) / 2.0

        xk = body_x_half / sx_half
        zk = body_z_half / sz_half
        shadow["points"] = [
            (body_x_mid + x * xk, 0.0, body_z_mid + (z - sz_mid) * zk)
            for (x, _y, z) in spts
        ]

        write_bms(shadow, bms_dir / "SHADOW_H.BMS")
        print(f"[Car Editor] Generated shadow → SHOP/BMS/{car_name}/SHADOW_H.BMS "
              f"(±{body_x_half:.2f} × {body_z_half * 2:.2f})")
        return True
    except Exception as exc:
        print(f"[Car Editor] Shadow generation failed ({exc}); keeping copied shadow")
        return False


def _generate_trailer_bnd_in_shop(car_name: str) -> bool:
    """
    Generate SHOP/BND/{car}_TRAILER_BND.BND sized to the edited trailer body.

    The trailer collision box uses the trailer's local AABB with no positional
    offset (the trailer instance frame handles placement). Falls back to keeping
    the stock VPSEMI_TRAILER collision staged by _ensure_trailer_in_shop.
    """

    bms_dir = Folder.Shop.Meshes / f"{car_name}_TRAILER"
    out     = Folder.Shop.Bound / f"{car_name}_TRAILER_BND.BND"

    if not (bms_dir / "TRAILER_H.BMS").exists():
        print(f"[Car Editor] TRAILER_H.BMS missing for {car_name}; keeping stock trailer BND")
        return False

    try:
        info = generate_car_bnd(bms_dir, out, body_name="TRAILER_H")
        print(f"[Car Editor] Generated trailer BND → SHOP/BND/{out.name} "
              f"(box r={info['radius']:.2f})")
        return True
    except Exception as exc:
        print(f"[Car Editor] Trailer BND generation failed ({exc}); keeping stock trailer BND")
        return False


def _patch_info_fields(car_name: str, fields: dict) -> None:
    """Replace (or append) ``key=value`` lines in SHOP/TUNE/{car}.INFO. Keys not
    present in the file are appended; everything else is preserved in place."""
    info = Folder.Shop.Tune / f"{car_name}.INFO"
    if not info.exists():
        return

    remaining = {k: v for k, v in fields.items()}
    out = []
    for ln in info.read_text(encoding="ascii").splitlines():
        key = ln.split("=", 1)[0] if "=" in ln else None
        if key in remaining:
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(ln)
    for key, value in remaining.items():
        out.append(f"{key}={value}")

    info.write_text("\n".join(out) + "\n", encoding="ascii")


def _read_info_fields(car_name: str) -> dict:
    """Parse SHOP/TUNE/{car}.INFO into a {key: value} dict (empty if no file)."""
    info = Folder.Shop.Tune / f"{car_name}.INFO"
    out = {}
    if info.exists():
        for ln in info.read_text(encoding="ascii").splitlines():
            if "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def _set_info_flags(car_name: str, six_wheel: bool = False, has_trailer: bool = False,
                    has_siren: bool = False) -> None:
    """
    Patch the Flags= line in SHOP/TUNE/{car}.INFO from detected car features.
    VEH_INFO_FLAG bits: 0x1 = 6 wheels, 0x2 = trailer, 0x8 = siren
    (see Open1560 vehinfo.h / mmCar::TranslateFlags).
    """
    flags = (0x1 if six_wheel else 0) | (0x2 if has_trailer else 0) | (0x8 if has_siren else 0)
    _patch_info_fields(car_name, {"Flags": flags})
    print(f"[Car Editor] {car_name}.INFO Flags={flags} "
          f"(6wheel={six_wheel}, trailer={has_trailer}, siren={has_siren})")


def _set_info_colors(car_name: str, colors: list) -> None:
    """Patch the Colors= line in SHOP/TUNE/{car}.INFO to the paint colour names."""
    if not colors:
        return
    value = ",".join(colors)
    _patch_info_fields(car_name, {"Colors": value})
    print(f"[Car Editor] {car_name}.INFO Colors={value}")


def _apply_info_stats(car_name: str, scene) -> None:
    """Write the menu/.INFO stat fields from the Car Info panel props. Paint
    variant Colors (if any) are applied AFTER this by _set_info_colors."""
    _patch_info_fields(car_name, {
        "Description": scene.ce_info_description.strip() or car_name,
        "Colors":      scene.ce_info_colors.strip() or "Red",
        "Horsepower":  int(scene.ce_info_horsepower),
        "Top Speed":   int(scene.ce_info_topspeed),
        "Durability":  int(scene.ce_info_durability),
        "Mass":        int(scene.ce_info_mass),
    })
    print(f"[Car Editor] {car_name}.INFO stats updated "
          f"(HP={scene.ce_info_horsepower}, top={scene.ce_info_topspeed})")


def _sync_info_props_from_car(scene, car_name: str) -> None:
    """Populate the Car Info panel props from an existing {car}.INFO (no-op if the
    car has none — stock cars don't carry a .INFO)."""
    d = _read_info_fields(car_name)
    if not d:
        return
    if "Description" in d:
        scene.ce_info_description = d["Description"]
    if "Colors" in d:
        scene.ce_info_colors = d["Colors"]
    for key, prop in (("Horsepower", "ce_info_horsepower"), ("Top Speed", "ce_info_topspeed"),
                      ("Durability", "ce_info_durability"), ("Mass", "ce_info_mass")):
        try:
            setattr(scene, prop, int(float(d[key])))
        except (KeyError, ValueError, TypeError):
            pass


def _audio_profile_path(profile: str):
    """Locate {profile}.MMPLAYERCARAUDIO (engine + horn sounds) — editor resources
    first, then the game's development/core/TUNE."""
    for cand in (
        Folder.Resources.Editor.Tune.CarSimulation.parent / f"{profile}.MMPLAYERCARAUDIO",
        Folder.BASE / "development" / "core" / "TUNE" / f"{profile}.MMPLAYERCARAUDIO",
    ):
        if cand.exists():
            return cand
    return None


def _ensure_car_audio_in_shop(car_name: str, profile: str, siren: bool = False) -> bool:
    """Stage SHOP/TUNE/{car}.MMPLAYERCARAUDIO from the chosen source car's audio
    profile so the custom car uses that car's engine + horn sounds. When ``siren``
    is set, enable the siren flag (m_bFlags 4) so StartSiren has a sound object
    (else it crashes on a null AudSound)."""
    base = _audio_profile_path(profile) or _audio_profile_path("VPMUSTANG99")
    if base is None:
        print(f"[Car Editor] No MMPLAYERCARAUDIO for '{profile}'; audio skipped")
        return False

    text = base.read_text(encoding="ascii", errors="replace")
    if siren:
        text = re.sub(r"(m_bFlags\s+)\d+", r"\g<1>4", text, count=1)

    out = Folder.Shop.Tune / f"{car_name}.MMPLAYERCARAUDIO"
    out.write_text(text, encoding="ascii")
    print(f"[Car Editor] Car audio → {out.name} (profile={profile}, siren={siren})")
    return True


def _build_car_tsh(car_name: str, car_objects, paint_variants: bool = True) -> list:
    """
    Write SHOP/MTL/{car_name}.TSH from ALL textures that will end up in the AR:

    1. Materials on the Blender car objects (what we exported this session).
    2. Any BMS files already sitting in SHOP/BMS/{car_name}/ that we didn't
       export (e.g. stale VL.BMS, light meshes copied by Init) — those files
       reference textures the game will try to look up, so they must be declared.

    When `paint_variants` and the body's textures have colour siblings (e.g. a car
    built on VPBULLET → VPBULLETBLUE/RED/WHITE), every variant is declared and the
    TSH `sibling` column is chained so the game offers them as paint jobs (the
    engine derives the paint-job count from this chain via GetVariationCount).

    Rules:
    - CARBOTTOM is in GLOBAL.TSH — skip it here.
    - Wheel / cop textures (WHL, *TOPLIGHT, VPCOPLIGHTS) load from TEX16A ('t').
    - FXLTGLOW* are global glow ('g'); everything else is a body texture ('d').

    Returns the list of paint colour names (e.g. ['Default','Blue',...]) or [].
    """
    seen  = set()
    names = []

    def _add(n: str) -> None:
        n = n.upper().strip()
        if n and n != "CARBOTTOM" and n not in seen:
            seen.add(n)
            names.append(n)

    # 1. Blender scene materials
    for obj in car_objects:
        if obj.type != "MESH":
            continue
        for mat in obj.data.materials:
            if mat is not None:
                _add(mat.name)

    # 2. BMS files already in SHOP — main folder + _DASH + _TRAILER subfolders
    for scan_dir in (
        Folder.Shop.Meshes / car_name,
        Folder.Shop.Meshes / f"{car_name}_DASH",
        Folder.Shop.Meshes / f"{car_name}_TRAILER",
    ):
        if scan_dir.is_dir():
            for bms_file in scan_dir.glob("*.BMS"):
                try:
                    data = read_bms(bms_file)
                    for tex in data.get("texture_names", []):
                        _add(tex)
                except Exception:
                    pass

    # 3. Paint variants — declare every colour sibling + build the sibling chain.
    #    ONLY for genuinely custom variant textures. If the variants belong to a
    #    STOCK car (e.g. a car built on VPBUG textures), the base game's TSH already
    #    chains them — re-declaring a different chain order conflicts with it and
    #    makes GetVariationCount loop forever (hang at load). Stock-textured cars
    #    already get their paint jobs from core for free, so we skip them.
    sibling_map: dict = {}   # NAME(upper) -> sibling name (or "")
    color_names: list = []
    if paint_variants:
        body_obj   = get_car_body()
        tex_folder = Folder.Resources.Editor.Textures
        chain = _build_paint_chain(body_obj.data, tex_folder) if body_obj else []
        common_base = os.path.commonprefix(chain) if chain else ""
        if len(chain) >= 2 and not _is_original_car(common_base):
            base = chain[0]
            suffixes = sorted({n[len(base):] for n in names
                               if n.startswith(base) and "_" in n})
            for suf in suffixes:
                variant_names = [p + suf for p in chain]
                for i, vn in enumerate(variant_names):
                    _add(vn)
                    sibling_map[vn.upper()] = variant_names[i + 1] if i + 1 < len(variant_names) else ""
            color_names = [_variant_color_name(p, chain) for p in chain]
        elif len(chain) >= 2:
            print(f"[Car Editor] Paint variants for '{common_base}' come from the base "
                  "game TSH — skipping re-chain to avoid a sibling cycle.")

    mtl_dst = Folder.Shop.Material
    mtl_dst.mkdir(parents=True, exist_ok=True)
    tsh_path = mtl_dst / f"{car_name}{FileType.TEXTURE_SHEET}"

    lines = ["name,neighborhood,h,m,l,flags,alternate,sibling,xres,yres,hexcolor"]
    for n in sorted(names):
        # Stock glow textures (FXLTGLOW/RED/AMBER, FXLTCONE) live in GLOBAL.TSH and
        # need the 'g' flag. Our generated colours (blue/green/coloured cone) are
        # packed into TEX16A, so they need 'tg' (packed + additive glow).
        is_global_glow = n.upper() in LightColor.GLOBAL_TEXTURES
        is_custom_glow = n.upper().startswith("FXLT") and not is_global_glow
        if "TOPLIGHT" in n:
            flags = "tg"   # flashing-lens texture: packed (TEX16A) + glow (additive)
        elif "WHL" in n or n == "VPCOPLIGHTS":
            flags = "td"   # packed normal texture (wheel, housing lens)
        elif is_custom_glow:
            flags = "tg"   # generated colour: packed (TEX16A) + glow (additive)
        elif is_global_glow:
            flags = "g"
        else:
            flags = "d"
        sib = sibling_map.get(n, "")
        lines.append(f"{n},car,0,0,1,{flags},,{sib},64,64,000000")

    tsh_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    extra = f", {len(color_names)} paint colours" if color_names else ""
    print(f"[Car Editor] TSH written: {len(names)} texture(s){extra} → {tsh_path.name}")
    return color_names


def _init_new_car_files(car_name: str, display_name: str = "Custom Car") -> list:
    """
    Populate SHOP subdirs with support files for a brand-new car name.

    Writes directly into the standard SHOP layout:
        SHOP/TUNE/  — physics (.MMCARSIM), wheel banger, .INFO
        SHOP/MTL/   — {NAME}.TSH (texture sheet)
        SHOP/BND/   — {NAME}_BND.BND (collision, copied from VPMUSTANG99)
        SHOP/BMS/{NAME}/ — lights, shadow (_H only)
        SHOP/TEX16A/ — wheel texture

    All source files come from resources/editor.
    Returns a list of human-readable result strings.
    """

    SOURCE   = "VPMUSTANG99"
    editor   = Folder.Resources.Editor
    msgs     = []

    # ── TUNE: physics (MMCARSIM) ──────────────────────────────────────────────
    tune_dst = Folder.Shop.Tune
    tune_dst.mkdir(parents=True, exist_ok=True)

    carsim_src = editor.Tune.CarSimulation / f"{SOURCE}.MMCARSIM"
    if carsim_src.exists():
        shutil.copy2(carsim_src, tune_dst / f"{car_name}.MMCARSIM")
        msgs.append(f"TUNE: copied {SOURCE}.MMCARSIM → {car_name}.MMCARSIM")
    else:
        msgs.append(f"TUNE: {SOURCE}.MMCARSIM not found in resources/editor, skipped")

    # ── TUNE: WHL0 banger data ────────────────────────────────────────────────
    # Verbatim copy — NodeName inside stays "vpmustang99_WHL0", only filename changes.
    banger_src = editor.Tune.BangerData / f"{SOURCE}_WHL0.MMBANGERDATA"
    if banger_src.exists():
        shutil.copy2(banger_src, tune_dst / f"{car_name}_WHL0.MMBANGERDATA")
        msgs.append("TUNE: WHL0 banger data copied from VPMUSTANG99 (verbatim)")
    else:
        msgs.append("TUNE: VPMUSTANG99_WHL0.MMBANGERDATA not found in resources/editor, skipped")

    # ── TUNE: .INFO — game discovers custom cars by scanning TUNE/ for *.INFO ─
    info_path = tune_dst / f"{car_name}.INFO"
    info_path.write_text(
        f"BaseName={car_name}\n"
        f"Description={display_name}\n"
        f"Colors=Red\n"
        f"Flags=0\n"
        f"Order=-1\n"
        f"ScoringBias=5.0\n"
        f"UnlockScore=0\n"
        f"UnlockFlags=0\n"
        f"Horsepower=320\n"
        f"Top Speed=200\n"
        f"Durability=500000\n"
        f"Mass=1500\n",
        encoding="ascii",
    )
    msgs.append(f"TUNE: generated .INFO — display name: '{display_name}'")

    # ── MTL: TSH ──────────────────────────────────────────────────────────────
    # CARBOTTOM is in GLOBAL.TSH — must NOT be duplicated here.
    # VPCOP_WHL needs flag 't' so the engine loads it from TEX16A/.
    mtl_dst = Folder.Shop.Material
    mtl_dst.mkdir(parents=True, exist_ok=True)
    tsh = mtl_dst / f"{car_name}{FileType.TEXTURE_SHEET}"
    tsh.write_text(
        "name,neighborhood,h,m,l,flags,alternate,sibling,xres,yres,hexcolor\n"
        "VPCOP_WHL,car,0,0,1,td,,,64,64,000000\n",
        encoding="ascii",
    )
    msgs.append("MTL: generated TSH (VPCOP_WHL wheel texture entry)")

    # ── BND: collision ────────────────────────────────────────────────────────
    bnd_dst = Folder.Shop.Bound
    bnd_dst.mkdir(parents=True, exist_ok=True)
    bnd_src = editor.Bound / f"{SOURCE}_BND.BND"
    if bnd_src.exists():
        shutil.copy2(bnd_src, bnd_dst / f"{car_name}_BND.BND")
        msgs.append("BND: copied VPMUSTANG99 collision")
    else:
        msgs.append("BND: VPMUSTANG99_BND.BND not found in resources/editor/BND, skipped")

    # ── DLP: wheel spin pivots ────────────────────────────────────────────────
    # The engine reads each wheel's Center from the DLP's WHLn_H group centroid.
    dlp_dst = Folder.Shop.DLP
    dlp_dst.mkdir(parents=True, exist_ok=True)
    dlp_src = editor.DLP / f"{SOURCE}{FileType.DEVELOPMENT}"
    if dlp_src.exists():
        shutil.copy2(dlp_src, dlp_dst / f"{car_name}{FileType.DEVELOPMENT}")
        msgs.append("DLP: copied VPMUSTANG99 wheel pivots")
    else:
        msgs.append("DLP: VPMUSTANG99.DLP not found in resources/editor/DLP, skipped")

    # ── BMS: lights + shadow reference files ─────────────────────────────────
    bms_src = editor.MeshesCars / SOURCE
    bms_dst = Folder.Shop.Meshes / car_name
    bms_dst.mkdir(parents=True, exist_ok=True)
    bms_n   = 0
    for fname in [
        "BLIGHT.BMS", "HLIGHT_H.BMS",
        "RLIGHT.BMS", "SHADOW_H.BMS",
        "SLIGHT0.BMS", "SLIGHT1.BMS", "TLIGHT.BMS",
    ]:
        src = bms_src / fname
        if src.exists():
            shutil.copy2(src, bms_dst / fname)
            bms_n += 1
    msgs.append(f"BMS: {bms_n} support files (lights + shadow _H) → SHOP/BMS/{car_name}")

    # ── BMS: dashboard sub-folder ─────────────────────────────────────────────
    # The game loads BMS/{NAME}_DASH/ separately; without overriding it the
    # original car AR's dash meshes stay active and reference car-specific
    # textures that aren't in our TSH, causing a fatal error on launch.
    dash_src = editor.MeshesCars / f"{SOURCE}_DASH"
    dash_dst = Folder.Shop.Meshes / f"{car_name}_DASH"
    if dash_src.is_dir():
        dash_dst.mkdir(parents=True, exist_ok=True)
        dash_n = 0
        for f in sorted(dash_src.iterdir()):
            if f.is_file() and f.suffix.upper() == ".BMS":
                shutil.copy2(f, dash_dst / f.name)
                dash_n += 1
        msgs.append(f"BMS: {dash_n} dashboard files → SHOP/BMS/{car_name}_DASH")
    else:
        msgs.append(f"BMS: {SOURCE}_DASH not found in resources/editor, skipped")

    # ── TEX16A: wheel texture ─────────────────────────────────────────────────
    tex16a_dst = Folder.Shop.Textures.Alpha
    tex16a_dst.mkdir(parents=True, exist_ok=True)
    whl_tex = editor.Textures / "VPCOP_WHL.DDS"
    if whl_tex.exists():
        shutil.copy2(whl_tex, tex16a_dst / "VPCOP_WHL.DDS")
        msgs.append("TEX16A: copied VPCOP_WHL.DDS wheel texture")
    else:
        msgs.append("TEX16A: VPCOP_WHL.DDS not found in resources/editor/TEXTURES, skipped")

    return msgs

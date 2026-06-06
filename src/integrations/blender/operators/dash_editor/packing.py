"""Dash Editor — export to SHOP + pack into a standalone override AR.

The dash is packed into its OWN AR ``!!!!!!!!!!{CAR}_DASH.ar`` (the ten-'!' Car
Editor prefix + ``_DASH``) containing ``BMS/{CAR}_DASH/*`` + ``TUNE/{CAR}.MMDASHVIEW``
+ ``TUNE/{CAR}_DASH.POVCAMCS``. A separate AR is deliberate: it overrides the dash
for any car (stock or custom) without requiring — or clobbering — the main car AR
the Car Editor produces. The ten-'!' prefix makes it load last so it wins.
"""
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from src.constants.folder import Folder
from src.constants.misc import Executable
from src.integrations.blender.operators.car_editor.packing import CAR_AR_PREFIX

from src.integrations.blender.operators.dash_editor.meshio import export_part
from src.integrations.blender.operators.dash_editor.constants import DASH_PARTS
from src.integrations.blender.operators.dash_editor.common import (
    get_dash_root, get_dash_part, get_tex_overrides, build_mmdashview_text, build_povcamcs_text,
)


def export_dash_to_shop(scene) -> Tuple[int, List[str], List[str]]:
    """Write every dash part BMS to SHOP/BMS/{car}_DASH/, the patched config files
    to SHOP/TUNE/, and any swapped/reskinned textures to SHOP/TEX16A/.
    Returns (parts_written, messages, texture_names_written)."""
    root = get_dash_root()
    msgs: List[str] = []
    if root is None:
        return 0, ["No dash loaded."], []

    car = root["mm_car_name"]
    bms_dst = Folder.Shop.Meshes / f"{car}_DASH"
    bms_dst.mkdir(parents=True, exist_ok=True)

    written = 0
    for tag, filename in DASH_PARTS:
        obj = get_dash_part(tag)
        if obj is None:
            continue
        try:
            export_part(obj, bms_dst / filename)
            written += 1
        except Exception as exc:
            msgs.append(f"{filename}: {exc}")
    msgs.append(f"BMS: {written} dash meshes → SHOP/BMS/{car}_DASH")

    Folder.Shop.Tune.mkdir(parents=True, exist_ok=True)

    mmview = build_mmdashview_text(scene, root)
    if mmview:
        (Folder.Shop.Tune / f"{car}.MMDASHVIEW").write_text(mmview, encoding="ascii")
        msgs.append(f"TUNE: {car}.MMDASHVIEW")

    pov = build_povcamcs_text(scene, root)
    if pov:
        (Folder.Shop.Tune / f"{car}_DASH.POVCAMCS").write_text(pov, encoding="ascii")
        msgs.append(f"TUNE: {car}_DASH.POVCAMCS")

    # Swapped / reskinned textures → TEX16A (the engine searches tex16a before
    # tex16o, so a same-named DDS here overrides the stock pixels with no TSH change).
    tex_names: List[str] = []
    overrides = get_tex_overrides(root)
    if overrides:
        tex_dst = Folder.Shop.Textures.Alpha
        tex_dst.mkdir(parents=True, exist_ok=True)
        for name, src in overrides.items():
            src_path = Path(src)
            if src_path.is_file():
                shutil.copy2(src_path, tex_dst / f"{name}.DDS")
                tex_names.append(name)
        if tex_names:
            msgs.append(f"TEX16A: {len(tex_names)} dash textures")

    return written, msgs, tex_names


def pack_dash_ar(car: str, tex_names: List[str] = None) -> bool:
    """Pack the car's dash files from SHOP into !!!!!!!!!!{car}_DASH.ar.

    `tex_names` are swapped/reskinned texture names (no extension) staged in
    SHOP/TEX16A/ that must ride along so the override looks right in-game."""
    mkar_exe = Folder.Angel / "mkar.exe"
    if not mkar_exe.exists():
        print(f"[Dash Editor] mkar.exe not found at {mkar_exe}")
        return False

    bms_src  = Folder.Shop.Meshes / f"{car}_DASH"
    if not bms_src.is_dir() or not any(bms_src.iterdir()):
        print(f"[Dash Editor] No dash BMS in {bms_src}")
        return False

    ar_out  = Folder.MidtownMadness.Root / f"{CAR_AR_PREFIX}{car}_DASH.ar"
    tmp_dir = Folder.BASE / f"_dash_pack_tmp_{car}"

    try:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True)

        # BMS/{car}_DASH/*
        dash_dst = tmp_dir / "BMS" / f"{car}_DASH"
        dash_dst.mkdir(parents=True)
        for f in sorted(bms_src.iterdir()):
            if f.is_file():
                shutil.copy2(f, dash_dst / f.name)

        # TEX16A/{name}.DDS — swapped/reskinned textures
        for name in (tex_names or []):
            src = Folder.Shop.Textures.Alpha / f"{name}.DDS"
            if src.is_file():
                tex_dst = tmp_dir / "TEX16A"
                tex_dst.mkdir(exist_ok=True)
                shutil.copy2(src, tex_dst / src.name)

        # TUNE/{car}.MMDASHVIEW + {car}_DASH.POVCAMCS
        for tune_name in (f"{car}.MMDASHVIEW", f"{car}_DASH.POVCAMCS"):
            src = Folder.Shop.Tune / tune_name
            if src.is_file():
                tune_dst = tmp_dir / "TUNE"
                tune_dst.mkdir(exist_ok=True)
                shutil.copy2(src, tune_dst / tune_name)

        pack_files = sorted(f for f in tmp_dir.rglob("*") if f.is_file())
        lines = [f"./{f.relative_to(tmp_dir).as_posix()}" for f in pack_files]
        shiplist_path = tmp_dir / f"shiplist.{car}_dash"
        shiplist_path.write_bytes(("\n".join(lines) + "\n").encode("ascii"))

        # Force prefix-strip length 2 (only the leading "./") so BMS/.. TUNE/..
        # paths are preserved — same mkar quirk handled in _pack_car_ar.
        print(f"[Dash Editor] Packing {len(pack_files)} files → {ar_out.name} …")
        result = subprocess.run(
            [str(mkar_exe), str(ar_out), str(shiplist_path), "2"],
            cwd=str(tmp_dir),
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.stdout:
            print(f"[Dash Editor] mkar: {result.stdout.strip()}")
        if result.stderr:
            print(f"[Dash Editor] mkar: {result.stderr.strip()}")
        if result.returncode != 0:
            print(f"[Dash Editor] mkar failed (exit {result.returncode})")
            return False

        print(f"[Dash Editor] Created {ar_out}")
        return True

    finally:
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except OSError as e:
                print(f"[Dash Editor] Warning: cleanup failed: {e}")


def launch_game() -> Tuple[bool, str]:
    exe = Folder.MidtownMadness.Root / Executable.MIDTOWN_MADNESS
    if not exe.exists():
        return False, f"Executable not found: {exe}"
    print(f"[Dash Editor] Launching {exe} …")
    subprocess.Popen([str(exe)], cwd=str(Folder.MidtownMadness.Root))
    return True, "game launching"

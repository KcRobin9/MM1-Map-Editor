"""Car Editor — trailer module (split from the former car_editor.py monolith)."""
import shutil

from src.constants.folder import Folder
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data, write_bms

from src.integrations.blender.operators.car_editor.common import (
    _get_trailer_parts, get_car_objects,
)
from src.integrations.blender.operators.car_editor.constants import _CAR_TAG


def _sync_trailer_wheel_texture_props(scene) -> None:
    """Set ce_trailer_wheel_texture_{i} to each loaded trailer wheel's actual texture."""
    for o in get_car_objects():
        tag = o.get(_CAR_TAG, "")
        if not tag.startswith("trailer_wheel_") or o.type != "MESH":
            continue
        try:
            idx = int(tag.split("_")[-1])
        except (ValueError, IndexError):
            continue
        mats = o.data.materials
        if mats and mats[0]:
            try:
                setattr(scene, f"ce_trailer_wheel_texture_{idx}", mats[0].name)
            except (TypeError, ValueError):
                pass  # texture not in the dropdown's item list — leave as-is


def _export_custom_trailer(car_name: str) -> int:
    """
    Export the edited trailer parts (body + TWHL wheels) to SHOP/BMS/{car}_TRAILER/,
    overwriting the stock TRAILER_H / TWHLn meshes. All parts are centered+offset
    (bake_location=True) relative to the trailer root. Returns parts exported.

    SHADOW/TLIGHT/BND come from the stock trailer staged by _ensure_trailer_in_shop.
    Caller must be in OBJECT mode.
    """
    trailer_dir = Folder.Shop.Meshes / f"{car_name}_TRAILER"
    trailer_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    for obj in _get_trailer_parts():
        tag = obj.get(_CAR_TAG, "")
        if tag == "trailer_body":
            out_name = "TRAILER_H.BMS"
        elif tag.startswith("trailer_wheel_"):
            out_name = f"TWHL{tag.split('_')[-1]}_H.BMS"
        else:
            continue
        try:
            write_bms(mesh_to_bms_data(obj, bake_location=True), trailer_dir / out_name)
            n += 1
        except Exception as exc:
            print(f"[Car Editor] Trailer export failed for {out_name}: {exc}")

    # LOD copies so the game's M/L/VL slots match the edited high-detail mesh.
    th = trailer_dir / "TRAILER_H.BMS"
    if th.exists():
        for s in ("TRAILER_M.BMS", "TRAILER_L.BMS", "TRAILER_VL.BMS"):
            shutil.copy2(th, trailer_dir / s)
    for i in range(10):
        wh = trailer_dir / f"TWHL{i}_H.BMS"
        if not wh.exists():
            break
        for s in (f"TWHL{i}_M.BMS", f"TWHL{i}_L.BMS"):
            shutil.copy2(wh, trailer_dir / s)

    if n:
        print(f"[Car Editor] Exported {n} custom trailer part(s) → SHOP/BMS/{car_name}_TRAILER")
    return n

"""Car Editor — physics module (split from the former car_editor.py monolith)."""
import shutil

from src.constants.folder import Folder
from src.integrations.blender.modeling.car_physics import (
    apply_physics_to_file, DEFAULTS, read_physics_from_file,
)


def _physics_params_from_scene(scene) -> dict:
    """Read the 7 exposed handling params off the scene props."""
    return {
        "mass":       float(getattr(scene, "ce_phys_mass", 1500.0)),
        "horsepower": float(getattr(scene, "ce_phys_horsepower", 320.0)),
        "drag":       float(getattr(scene, "ce_phys_drag", 0.12)),
        "downforce":  float(getattr(scene, "ce_phys_downforce", 0.0)),
        "grip":       float(getattr(scene, "ce_phys_grip", 0.9)),
        "drift":      float(getattr(scene, "ce_phys_drift", 7.0)),
        "suspension": float(getattr(scene, "ce_phys_suspension", 75300.0)),
        "cg_x":       float(getattr(scene, "ce_phys_cg_x", 0.0)),
        "cg_height":  float(getattr(scene, "ce_phys_cg_height", -0.06)),
        "cg_z":       float(getattr(scene, "ce_phys_cg_z", 0.0)),
    }


def _base_carsim_path(car_name: str):
    """Locate a base MMCARSIM to patch: SHOP first, then editor resources, then core."""
    candidates = [
        Folder.Shop.Tune / f"{car_name}.MMCARSIM",
        Folder.Resources.Editor.Tune.CarSimulation / f"{car_name}.MMCARSIM",
        Folder.BASE / "development" / "core" / "TUNE" / f"{car_name}.MMCARSIM",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _apply_physics_in_shop(car_name: str, scene) -> bool:
    """
    Patch SHOP/TUNE/{car}.MMCARSIM with the panel's handling values.

    Sources a base MMCARSIM if one isn't already staged (so existing cars can be
    retuned too). Only called when the user enabled the Override Physics toggle.
    """

    tune_dir = Folder.Shop.Tune
    tune_dir.mkdir(parents=True, exist_ok=True)
    out = tune_dir / f"{car_name}.MMCARSIM"

    if not out.exists():
        base = _base_carsim_path(car_name)
        if base is None:
            print(f"[Car Editor] No base MMCARSIM found for {car_name}; physics override skipped")
            return False
        shutil.copy2(base, out)

    try:
        apply_physics_to_file(out, _physics_params_from_scene(scene))
        print(f"[Car Editor] Applied physics override → SHOP/TUNE/{out.name}")
        return True
    except Exception as exc:
        print(f"[Car Editor] Physics override failed ({exc})")
        return False


_PHYS_PROP = {
    "mass": "ce_phys_mass", "horsepower": "ce_phys_horsepower", "drag": "ce_phys_drag",
    "downforce": "ce_phys_downforce", "grip": "ce_phys_grip", "drift": "ce_phys_drift",
    "suspension": "ce_phys_suspension", "cg_x": "ce_phys_cg_x",
    "cg_height": "ce_phys_cg_height", "cg_z": "ce_phys_cg_z",
}


def _sync_physics_props_from_car(scene, car_name: str) -> None:
    """Read a car's MMCARSIM into the Physics panel props and turn override off."""

    base = _base_carsim_path(car_name)
    values = dict(DEFAULTS)
    if base is not None:
        try:
            values.update(read_physics_from_file(base))
        except Exception as exc:
            print(f"[Car Editor] Could not read physics for {car_name}: {exc}")

    for key, prop in _PHYS_PROP.items():
        if key in values:
            try:
                setattr(scene, prop, float(values[key]))
            except Exception:
                pass
    scene.ce_phys_override = False

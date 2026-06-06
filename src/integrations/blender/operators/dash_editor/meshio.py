"""Dash Editor — per-part BMS load / export.

Loading reuses the Car Editor's `_load_bms` (read_bms → build_blender_mesh →
materials). Export is dash-specific: a dash part's placement and needle rotation
live in the .MMDASHVIEW config, NOT in the BMS, so the BMS must capture only the
part's LOCAL geometry — object location/rotation are neutralised before extraction
and the part's original mesh_offset (the wheel hub, zero for the rest) is preserved.
"""
import bpy
import mathutils
from pathlib import Path
from typing import Optional

from src.integrations.blender.operators.car_editor.common import _load_bms
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data, write_bms


def load_part_mesh(bms_file: Path, name: str, tex_folder: Optional[Path]) -> Optional[bpy.types.Mesh]:
    """Load one dash BMS into a Blender mesh data-block (or None on failure)."""
    return _load_bms(bms_file, name, tex_folder)


def export_part(obj: bpy.types.Object, out_path: Path) -> None:
    """Write a dash part object back to a BMS file in its own local frame.

    Object location + rotation are temporarily zeroed so neither the .MMDASHVIEW
    placement nor the needle rest/preview rotation bakes into the vertices; scale
    stays applied (geometry edits round-trip). The part keeps its original
    mesh_offset so the wheel's hub offset + OFFSET flag survive unchanged.
    """
    mesh = obj.data
    orig_offset = tuple(mesh.get("mesh_offset", (0.0, 0.0, 0.0)))

    saved_loc = obj.location.copy()
    saved_rot = obj.rotation_euler.copy()
    try:
        obj.location = mathutils.Vector((0.0, 0.0, 0.0))
        obj.rotation_euler = (0.0, 0.0, 0.0)
        # bake_location=True works off matrix_local (parent_inverse is identity for
        # dash parts), so the parented DASH root's DashPos is not included.
        data = mesh_to_bms_data(obj, bake_location=True)
    finally:
        obj.location = saved_loc
        obj.rotation_euler = saved_rot

    data["mesh_offset"] = orig_offset   # write_bms re-sets the OFFSET flag when nonzero

    # A swapped-in part keeps the source mesh but is remapped to the current car's
    # texture NAMES, so the car's own TSH still resolves them (the source skin is
    # packed under those names separately — see common.swap_part).
    remap = {k.upper(): v for k, v in dict(obj.get("tex_remap", {})).items()}
    if remap:
        data["texture_names"] = [remap.get(n.upper(), n) for n in data["texture_names"]]

    write_bms(data, out_path)

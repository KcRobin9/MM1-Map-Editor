import bpy
from typing import List

from src.integrations.blender.waypoints.constants import FlagUV


def get_all_waypoints() -> List[bpy.types.Object]:
    return [obj for obj in bpy.data.objects if obj.name.startswith("WP_") or obj.name.startswith("CR_")]


def _is_circuit(waypoints: List[bpy.types.Object]) -> bool:
    return any(obj.name.startswith("WP_CIR_") for obj in waypoints)


def _get_flag_mat_slot(obj: bpy.types.Object) -> int:
    for i, mat in enumerate(obj.data.materials):
        if mat and mat.get("wp_textured"):
            return i
    return -1


def _assign_flag_type(obj: bpy.types.Object, flag_type: str) -> None:
    # Deferred import: circular dependency (create → helpers → create)
    from src.integrations.blender.waypoints.create import _get_or_create_flag_material
    slot = _get_flag_mat_slot(obj)
    if slot == -1:
        return
    obj.data.materials[slot] = _get_or_create_flag_material(flag_type)
    obj["wp_flag_type"] = flag_type


def update_waypoint_colors() -> None:
    all_wps  = get_all_waypoints()
    race_wps = [wp for wp in all_wps if wp.name.startswith("WP_")]
    cnr_wps  = [wp for wp in all_wps if wp.name.startswith("CR_")]
    circuit  = _is_circuit(race_wps)

    for i, wp in enumerate(race_wps):
        if _get_flag_mat_slot(wp) == -1:
            continue
        is_finish = (circuit and i == 0) or (not circuit and i == len(race_wps) - 1)
        _assign_flag_type(wp, FlagUV.FINISH if is_finish else FlagUV.CHECKPOINT)

    for wp in cnr_wps:
        if _get_flag_mat_slot(wp) == -1:
            continue
        _assign_flag_type(wp, FlagUV.BANK if "Bank" in wp.name else FlagUV.HIDEOUT)
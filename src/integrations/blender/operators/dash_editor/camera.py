"""Dash Editor — cockpit POV camera.

The dash is only ever seen through the cockpit camera ({CAR}_DASH.POVCAMCS). A real
Blender camera built from that config lets the user frame the dash exactly as the
player would, in Blender, without launching the game.

POVCAMCS fields used: m_Offset (camera position, car-local), m_cameraFOV (degrees),
m_cameraNear / m_cameraFar (clip range), TrackTo (look-at point, car-local). The
camera position + look target are converted with the same BMS convention the dash
meshes use so the camera sits coherently in the assembled scene. Exact in-game
framing is calibrated visually (see the Verification note in the plan).
"""
import math

import bpy
import mathutils

from src.integrations.blender.modeling.meshes import _to_blender_pos
from src.integrations.blender.operators.dash_editor.constants import _POV_CAMERA_NAME, _DASH_TAG


def build_pov_camera(root_obj, pov_values: dict, col: bpy.types.Collection):
    """Create (or refresh) the cockpit camera from parsed POVCAMCS values.

    `pov_values` is the dict from tune_blocks.parse_block of the .POVCAMCS file.
    The camera is placed in world space relative to the dash root and aimed at the
    look target, then tagged so Clear Dash removes it. Returns the camera object.
    """
    offset = pov_values.get("m_Offset", [0.0, 1.2, 0.3])
    track  = pov_values.get("TrackTo",  [0.0, 1.0, 0.0])
    fov    = pov_values.get("m_cameraFOV",  [60.0])[0]
    near   = pov_values.get("m_cameraNear", [0.1])[0]
    far    = pov_values.get("m_cameraFar",  [1600.0])[0]

    cam_data = bpy.data.cameras.get(_POV_CAMERA_NAME) or bpy.data.cameras.new(_POV_CAMERA_NAME)
    cam_data.lens_unit  = "FOV"
    cam_data.angle      = math.radians(max(1.0, min(170.0, fov)))
    cam_data.clip_start = max(1e-3, near)
    cam_data.clip_end   = max(near + 1.0, far)

    cam_obj = bpy.data.objects.get(_POV_CAMERA_NAME)
    if cam_obj is None or cam_obj.type != "CAMERA":
        cam_obj = bpy.data.objects.new(_POV_CAMERA_NAME, cam_data)
    else:
        cam_obj.data = cam_data
    if cam_obj.name not in col.objects:
        col.objects.link(cam_obj)
    cam_obj[_DASH_TAG] = "pov_camera"

    # m_Offset / TrackTo are car-local, in the dash frame → root-relative; convert
    # to world space through the root's matrix so the camera frames the assembly.
    cam_world    = root_obj.matrix_world @ mathutils.Vector(_to_blender_pos(offset))
    target_world = root_obj.matrix_world @ mathutils.Vector(_to_blender_pos(track))

    cam_obj.location = cam_world
    direction = target_world - cam_world
    if direction.length > 1e-6:
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    return cam_obj

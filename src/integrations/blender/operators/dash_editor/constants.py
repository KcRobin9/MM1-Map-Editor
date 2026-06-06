"""Dash Editor — constants.

The MM1 cockpit ("Driver") view is mmDashView: a small 3D assembly drawn in front
of the camera and parked on the car body. It is composed of seven BMS meshes in a
per-car ``{CAR}_DASH/`` folder plus a ``{CAR}.MMDASHVIEW`` placement config and a
``{CAR}_DASH.POVCAMCS`` cockpit-camera config. Engine truth: Open1560
mmgame/dash.cpp / dash.h / gauge.cpp.

Scene-graph hierarchy (mirrors mmDashView's node tree — DashLCS owns everything):

    DASH root (empty)            = DashLCS, placed at DashPos on the car body
      ├─ dash mesh               drawn at DashLCS origin (no own placement field)
      ├─ gear mesh               drawn at DashLCS origin (position baked in verts)
      ├─ roof mesh               RoofLCS    → RoofPos
      ├─ wheel mesh              WheelLCS   → WheelOffset (spins with steering)
      ├─ speed needle            SpeedGuage → SpeedPos,  rest angle SpeedMinRot
      ├─ tach needle             RPMGuage   → RPMPos,    rest angle RPMMinRot
      └─ damage needle           DamageGuage→ DamagePos, rest angle DamageMinRot

All positions live in the same car-local frame as the BMS vertices, so they use the
BMS convention ``_to_blender_pos = (-x, z, y)``. Needles rotate around the game Z
axis, which maps to Blender +Y under that (proper, det +1) transform.
"""

_DASH_COLLECTION = "Dash Editor"
_DASH_TAG        = "mm_dash_part"   # custom prop on every dash object
_ROOT_TAG        = "root"           # _DASH_TAG value on the DashLCS empty

# part tag -> BMS filename inside {CAR}_DASH/
DASH_PARTS = [
    ("dash",          "DASH.BMS"),
    ("roof",          "ROOF.BMS"),
    ("wheel",         "WHEEL.BMS"),
    ("gear",          "GEAR_INDICATOR.BMS"),
    ("speed_needle",  "SPEED_NEEDLE.BMS"),
    ("tach_needle",   "TACH_NEEDLE.BMS"),
    ("damage_needle", "DAMAGE_NEEDLE.BMS"),
]

# part tag -> MMDASHVIEW Vector3 field that places it (relative to DashLCS).
# dash + gear have no field: they draw at the DashLCS origin.
DASH_PLACEMENT_FIELD = {
    "roof":          "RoofPos",
    "wheel":         "WheelOffset",
    "speed_needle":  "SpeedPos",
    "tach_needle":   "RPMPos",
    "damage_needle": "DamagePos",
}

# needle tag -> (MinRot field, MaxRot field) — the needle sweep, radians around Z.
NEEDLE_ROT_FIELD = {
    "speed_needle":  ("SpeedMinRot",  "SpeedMaxRot"),
    "tach_needle":   ("RPMMinRot",    "RPMMaxRot"),
    "damage_needle": ("DamageMinRot", "DamageMaxRot"),
}

# needle tag -> (de_*_rot_min, de_*_rot_max) scene-prop names (panel + preview).
NEEDLE_ROT_PROP = {
    "speed_needle":  ("de_speed_rot_min",  "de_speed_rot_max"),
    "tach_needle":   ("de_rpm_rot_min",    "de_rpm_rot_max"),
    "damage_needle": ("de_damage_rot_min", "de_damage_rot_max"),
}

# MMDASHVIEW scalar field <-> de_* scene prop.
SCALAR_FIELD_PROP = {
    "MaxSpeed":  "de_max_speed",
    "MaxRPM":    "de_max_rpm",
    "MinSpeed":  "de_min_speed",
    "WheelFact": "de_wheel_fact",
}

NEEDLE_TAGS = ("speed_needle", "tach_needle", "damage_needle")

_POV_CAMERA_NAME = "Dash POV Camera"

DEFAULT_TEMPLATE_CAR = "VPMUSTANG99"

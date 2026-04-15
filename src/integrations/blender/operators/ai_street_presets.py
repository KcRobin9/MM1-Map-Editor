import bpy
import math
from typing import NamedTuple, List

from mathutils import Vector
from src.game.races.constants_2 import IntersectionType
from src.integrations.blender.operators.ai_streets import (
    ST_PREFIX,
    _build_curve_object,
    _set_street_defaults,
    apply_street_color,
    _next_street_name,
)


# ── Data model ────────────────────────────────────────────────────────────────

class StreetSpec(NamedTuple):
    vertices:          List            # [(x, y, z), ...] relative to cursor (Blender space)
    intersection_0:    str = str(IntersectionType.CONTINUE)
    intersection_1:    str = str(IntersectionType.CONTINUE)
    road_divided:      str = "NO"
    alley:             str = "NO"
    traffic_blocked_0: str = "NO"
    traffic_blocked_1: str = "NO"


# ── Arc helper ────────────────────────────────────────────────────────────────

def _arc(cx: float, cy: float, radius: float,
         start_deg: float, end_deg: float, n_pts: int, z: float = 0.0) -> List:
    pts = []
    for i in range(n_pts):
        t = i / max(1, n_pts - 1)
        a = math.radians(start_deg + t * (end_deg - start_deg))
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z))
    return pts


# ── Preset builders ───────────────────────────────────────────────────────────
# All coords are in Blender space, relative to cursor.
# L = arm length, W = lane width, R = turn radius, N = curve points.

def _single_straight(L, W, R, N):
    return [StreetSpec([(0, 0, 0), (0, L, 0)])]


def _two_lane_road(L, W, R, N):
    hw = W / 2
    return [
        StreetSpec([(-hw, 0, 0), (-hw, L, 0)]),   # left lane  → forward
        StreetSpec([(hw, L, 0),  (hw, 0, 0)]),     # right lane ← backward
    ]


def _four_lane_road(L, W, R, N):
    specs = []
    for x in (-3*W/2, -W/2):                       # two left lanes → forward
        specs.append(StreetSpec([(x, 0, 0), (x, L, 0)]))
    for x in (W/2, 3*W/2):                         # two right lanes ← backward
        specs.append(StreetSpec([(x, L, 0), (x, 0, 0)]))
    return specs


def _oneway_3lane(L, W, R, N):
    return [
        StreetSpec([(-W,  0, 0), (-W,  L, 0)]),
        StreetSpec([(0,   0, 0), (0,   L, 0)]),
        StreetSpec([(W,   0, 0), (W,   L, 0)]),
    ]


def _highway_divided(L, W, R, N):
    """4-lane divided highway — road_divided flag set on all lanes."""
    specs = []
    for x in (-3*W/2, -W/2):
        specs.append(StreetSpec([(x, 0, 0), (x, L, 0)], road_divided="YES"))
    for x in (W/2, 3*W/2):
        specs.append(StreetSpec([(x, L, 0), (x, 0, 0)], road_divided="YES"))
    return specs


def _alley(L, W, R, N):
    return [StreetSpec([(0, 0, 0), (0, L, 0)], alley="YES")]


def _dead_end(L, W, R, N):
    return [StreetSpec(
        [(0, 0, 0), (0, L, 0)],
        intersection_0=str(IntersectionType.STOP),
        intersection_1=str(IntersectionType.STOP),
    )]


def _t_junction(L, W, R, N):
    """Three arms: North, East, West — meeting at cursor."""
    return [
        StreetSpec([(0,  0, 0), (0,  L, 0)]),    # North
        StreetSpec([(0,  0, 0), (L,  0, 0)]),    # East
        StreetSpec([(-L, 0, 0), (0,  0, 0)]),    # West → center
    ]


def _four_way(L, W, R, N):
    """Four arms N / S / E / W meeting at cursor."""
    return [
        StreetSpec([(0,  0, 0), (0,  L, 0)]),   # North
        StreetSpec([(0, -L, 0), (0,  0, 0)]),   # South → center
        StreetSpec([(0,  0, 0), (L,  0, 0)]),   # East
        StreetSpec([(-L, 0, 0), (0,  0, 0)]),   # West → center
    ]


def _y_junction(L, W, R, N):
    """Three arms at 120° angles (Y shape, north branch pointing up)."""
    specs = []
    for deg in (90, 210, 330):
        a = math.radians(deg)
        specs.append(StreetSpec([(0, 0, 0), (math.cos(a)*L, math.sin(a)*L, 0)]))
    return specs


def _six_way(L, W, R, N):
    """Six arms at 60° (star / asterisk pattern)."""
    specs = []
    for i in range(6):
        a = math.radians(90 + i * 60)
        specs.append(StreetSpec([(0, 0, 0), (math.cos(a)*L, math.sin(a)*L, 0)]))
    return specs


def _diagonal_cross(L, W, R, N):
    """Four arms at 45° diagonals (× shape)."""
    specs = []
    for deg in (45, 135, 225, 315):
        a = math.radians(deg)
        specs.append(StreetSpec([(0, 0, 0), (math.cos(a)*L, math.sin(a)*L, 0)]))
    return specs


def _curve_90_right(L, W, R, N):
    """Single lane curving 90° to the right (north → east)."""
    # Arc centre (R, 0), starts at 180° (west of centre = origin), ends at 90° (north of centre)
    return [StreetSpec(_arc(R, 0, R, 180, 90, N))]


def _curve_90_left(L, W, R, N):
    """Single lane curving 90° to the left (north → west)."""
    # Arc centre (-R, 0), starts at 0°, ends at 90°
    return [StreetSpec(_arc(-R, 0, R, 0, 90, N))]


def _curve_45_right(L, W, R, N):
    """Single lane curving 45° to the right."""
    pts = _arc(R, 0, R, 180, 135, max(3, (N + 1) // 2))
    return [StreetSpec(pts)]


def _two_lane_curve_90(L, W, R, N):
    """Two parallel lanes both making a 90° right curve."""
    left_pts  = _arc(R, 0, R - W/2, 180,  90, N)   # inner (tighter)
    right_pts = _arc(R, 0, R + W/2,  90, 180, N)   # outer, reversed direction
    return [
        StreetSpec(left_pts),
        StreetSpec(right_pts),
    ]


def _s_curve(L, W, R, N):
    """Single lane making an S-shape (right then left curve)."""
    half = max(3, (N + 1) // 2)
    # First arc: right turn.  Centre (R, 0), 180° → 90°.  Ends at (R, R).
    pts1 = _arc(R, 0,    R, 180,  90, half)
    # Second arc: left turn.  Centre (R, 2R), 270° → 360°.  Starts at (R, R).
    pts2 = _arc(R, 2*R,  R, 270, 360, half)[1:]   # skip duplicate join point
    return [StreetSpec(pts1 + list(pts2))]


def _hairpin(L, W, R, N):
    """180° hairpin turn — goes north, curves back south."""
    return [StreetSpec(_arc(R, 0, R, 180, 0, N))]


def _roundabout(L, W, R, N):
    """Circular ring road + 4 entry/exit arms (N/E/S/W)."""
    specs = []

    # Ring: closed circle approximated with 12 vertices
    n_ring = max(8, N + 4)
    ring_pts = [
        (R * math.cos(math.radians(360 * i / n_ring)),
         R * math.sin(math.radians(360 * i / n_ring)),
         0.0)
        for i in range(n_ring + 1)   # +1 closes the loop
    ]
    specs.append(StreetSpec(ring_pts))

    # 4 entry arms
    arm = L * 0.4
    for deg in (90, 0, 270, 180):   # N, E, S, W
        a  = math.radians(deg)
        ex, ey = R * math.cos(a),       R * math.sin(a)
        ox, oy = (R + arm) * math.cos(a), (R + arm) * math.sin(a)
        specs.append(StreetSpec([(ox, oy, 0), (ex, ey, 0)]))

    return specs


def _t_junction_2lane(L, W, R, N):
    """T-junction with 2 lanes per arm (6 streets total)."""
    hw = W / 2
    specs = []
    # North arm (2 lanes)
    specs.append(StreetSpec([(-hw, 0, 0), (-hw, L, 0)]))
    specs.append(StreetSpec([(hw,  L, 0), (hw,  0, 0)]))
    # East arm
    specs.append(StreetSpec([(0,  hw, 0), (L,  hw, 0)]))
    specs.append(StreetSpec([(L, -hw, 0), (0, -hw, 0)]))
    # West arm
    specs.append(StreetSpec([(-L, -hw, 0), (0, -hw, 0)]))
    specs.append(StreetSpec([(0,   hw, 0), (-L, hw, 0)]))
    return specs


def _four_way_2lane(L, W, R, N):
    """4-way junction with 2 lanes per arm (8 streets total)."""
    hw = W / 2
    specs = []
    # N/S axis
    specs.append(StreetSpec([(-hw, -L, 0), (-hw, L, 0)]))
    specs.append(StreetSpec([(hw,   L, 0), (hw, -L, 0)]))
    # E/W axis
    specs.append(StreetSpec([(-L, hw, 0), (L,  hw, 0)]))
    specs.append(StreetSpec([(L, -hw, 0), (-L, -hw, 0)]))
    return specs


# ── Registry ──────────────────────────────────────────────────────────────────

_BUILDERS = {
    "SINGLE":         _single_straight,
    "2_LANE":         _two_lane_road,
    "4_LANE":         _four_lane_road,
    "ONEWAY_3":       _oneway_3lane,
    "HIGHWAY":        _highway_divided,
    "ALLEY":          _alley,
    "DEAD_END":       _dead_end,
    "T_JUNCTION":     _t_junction,
    "T_JUNC_2L":      _t_junction_2lane,
    "4_WAY":          _four_way,
    "4_WAY_2L":       _four_way_2lane,
    "Y_JUNCTION":     _y_junction,
    "6_WAY":          _six_way,
    "DIAGONAL_X":     _diagonal_cross,
    "CURVE_90R":      _curve_90_right,
    "CURVE_90L":      _curve_90_left,
    "CURVE_45R":      _curve_45_right,
    "2LANE_CURVE90":  _two_lane_curve_90,
    "S_CURVE":        _s_curve,
    "HAIRPIN":        _hairpin,
    "ROUNDABOUT":     _roundabout,
}

ST_PRESET_ITEMS = [
    # ── Straight ──────────────────────────────────────────────────────────────
    ("SINGLE",        "Single Street",         "One straight street, 2 vertices"),
    ("2_LANE",        "2-Lane Road",           "Two parallel streets, opposing directions"),
    ("4_LANE",        "4-Lane Road",           "Four parallel streets (2 each direction)"),
    ("ONEWAY_3",      "One-Way 3-Lane",        "Three lanes all in the same direction"),
    ("HIGHWAY",       "Highway (Divided)",     "4 lanes, road_divided flag set on all"),
    ("ALLEY",         "Alley",                 "Single narrow street, alley flag set"),
    ("DEAD_END",      "Dead End / Cul-de-sac", "Street with Stop intersection at both ends"),
    # ── Junctions ─────────────────────────────────────────────────────────────
    ("T_JUNCTION",    "T-Junction",            "3 arms: N, E, W from cursor"),
    ("T_JUNC_2L",     "T-Junction (2-lane)",   "T-junction with 2 lanes per arm (6 streets)"),
    ("4_WAY",         "4-Way Junction",        "4 arms N/S/E/W from cursor"),
    ("4_WAY_2L",      "4-Way Junction (2-lane)","4-way with 2 lanes per arm (8 streets)"),
    ("Y_JUNCTION",    "Y-Junction",            "3 arms at 120° angles"),
    ("6_WAY",         "6-Way Star",            "6 arms at 60° angles"),
    ("DIAGONAL_X",    "Diagonal Cross (×)",    "4 arms at 45° diagonals"),
    # ── Curves ────────────────────────────────────────────────────────────────
    ("CURVE_90R",     "Curve 90° Right",       "Single street curving 90° right (N→E)"),
    ("CURVE_90L",     "Curve 90° Left",        "Single street curving 90° left (N→W)"),
    ("CURVE_45R",     "Curve 45° Right",       "Single street curving 45° right"),
    ("2LANE_CURVE90", "2-Lane Curve 90°",      "Two parallel lanes both turning 90° right"),
    ("S_CURVE",       "S-Curve",               "Street curving right then left"),
    ("HAIRPIN",       "Hairpin (180°)",        "Street that U-turns back on itself"),
    # ── Complex ───────────────────────────────────────────────────────────────
    ("ROUNDABOUT",    "Roundabout",            "Circular ring road with 4 entry/exit arms"),
]


# ── Operator ──────────────────────────────────────────────────────────────────

class OBJECT_OT_SpawnStreetPreset(bpy.types.Operator):
    bl_idname      = "object.spawn_street_preset"
    bl_label       = "Spawn Street Preset"
    bl_description = "Spawn the selected AI street preset at the 3D cursor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        scene   = context.scene
        key     = scene.st_street_preset
        builder = _BUILDERS.get(key)

        if builder is None:
            self.report({"ERROR"}, f"Unknown street preset: {key}")
            return {"CANCELLED"}

        L = scene.st_preset_length
        W = scene.st_preset_lane_width
        R = scene.st_preset_turn_radius
        N = scene.st_preset_curve_points

        specs   = builder(L, W, R, N)
        cursor  = context.scene.cursor.location
        created = []

        for spec in specs:
            name = _next_street_name(scene)
            # Offset each vertex by cursor position
            world_pts = [
                (cursor.x + v[0], cursor.y + v[1], cursor.z + v[2])
                for v in spec.vertices
            ]
            if len(world_pts) < 2:
                continue

            obj = _build_curve_object(f"{ST_PREFIX}{name}", world_pts, context)
            _set_street_defaults(obj)

            # Apply per-spec overrides
            obj.st_intersection_0    = spec.intersection_0
            obj.st_intersection_1    = spec.intersection_1
            obj.st_road_divided      = spec.road_divided
            obj.st_alley             = spec.alley
            obj.st_traffic_blocked_0 = spec.traffic_blocked_0
            obj.st_traffic_blocked_1 = spec.traffic_blocked_1

            apply_street_color(obj)
            created.append(obj)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in created:
            obj.select_set(True)
        if created:
            context.view_layer.objects.active = created[0]

        self.report({"INFO"}, f"Spawned {len(created)} street(s) from preset '{key}'")
        return {"FINISHED"}


STREET_PRESET_CLASSES = [
    OBJECT_OT_SpawnStreetPreset,
]

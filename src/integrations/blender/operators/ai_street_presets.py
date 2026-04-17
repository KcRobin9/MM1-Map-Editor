import bpy
import math
from typing import NamedTuple, List

from src.game.races.constants_2 import IntersectionType
from src.integrations.blender.operators.ai_streets import (
    ST_PREFIX,
    _build_curve_object,
    _get_or_create_ai_streets_collection,
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


class PresetParams(NamedTuple):
    """
    Unified parameter set forwarded to every preset builder.

    length      — total road / arm length
    split       — vertex spacing (0 = use n_curve for curves, 2 verts for straights)
    lanes       — number of parallel lanes
    sep         — centre-to-centre distance between lanes
    radius      — arc radius for curved presets
    n_curve     — vertex count on arcs when split = 0
    lane_width  — arm offset used by fixed-topology junction presets
    """
    length:     float
    split:      float
    lanes:      int
    sep:        float
    radius:     float
    n_curve:    int
    lane_width: float


# ── Low-level geometry helpers ────────────────────────────────────────────────

def _arc(cx: float, cy: float, radius: float,
         start_deg: float, end_deg: float, n_pts: int, z: float = 0.0) -> List:
    pts = []
    for i in range(n_pts):
        t = i / max(1, n_pts - 1)
        a = math.radians(start_deg + t * (end_deg - start_deg))
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z))
    return pts


def _lane_offsets(lanes: int, sep: float) -> List[float]:
    """Return X offsets for `lanes` parallel tracks centred on 0."""
    if lanes <= 1:
        return [0.0]
    return [(-(lanes - 1) / 2.0 + i) * sep for i in range(lanes)]


def _n_linear(length: float, split: float) -> int:
    if split > 0:
        return max(2, math.ceil(length / split) + 1)
    return 2


def _n_arc(radius: float, angle_deg: float, split: float, n_default: int) -> int:
    if split > 0:
        arc_len = abs(math.radians(angle_deg)) * max(0.01, abs(radius))
        return max(2, math.ceil(arc_len / split) + 1)
    return n_default


def _straight_pts(length: float, split: float, x_off: float = 0.0) -> List:
    n = _n_linear(length, split)
    return [(x_off, length * i / max(1, n - 1), 0.0) for i in range(n)]


def _arc_pts(cx: float, cy: float, radius: float,
             start_deg: float, end_deg: float,
             angle_deg: float, split: float, n_default: int) -> List:
    n = _n_arc(radius, angle_deg, split, n_default)
    return _arc(cx, cy, radius, start_deg, end_deg, n)


# ── Preset builders ───────────────────────────────────────────────────────────


# ── Custom / general-purpose ──────────────────────────────────────────────────

def _preset_custom(p: PresetParams):
    """
    Fully parametric: straight when radius=0, 90° right-hand curve when radius>0.
    Respects all lane / split / separator params.
    """
    offsets = _lane_offsets(p.lanes, p.sep)
    if p.radius <= 0:
        return [StreetSpec(_straight_pts(p.length, p.split, off)) for off in offsets]
    return [
        StreetSpec(_arc_pts(p.radius, 0, max(0.1, p.radius + off),
                            180, 90, 90, p.split, p.n_curve))
        for off in offsets
    ]


# ── Straight roads ────────────────────────────────────────────────────────────

def _preset_single_straight(p: PresetParams):
    """Single centre-line road. Useful as a simple AI path anchor."""
    return [StreetSpec(_straight_pts(p.length, p.split))]


def _preset_road_opposing(p: PresetParams):
    """
    N lanes split into two opposing directions (first half forward, second half backward).
    Uses sep for lane spacing.  Works for 2, 4, 6 … lanes.
    """
    offsets = _lane_offsets(p.lanes, p.sep)
    half    = max(1, len(offsets) // 2)
    n       = _n_linear(p.length, p.split)
    ys      = [p.length * i / max(1, n - 1) for i in range(n)]
    specs   = []
    for i, off in enumerate(offsets):
        pts = [(off, y, 0.0) for y in (list(reversed(ys)) if i >= half else ys)]
        specs.append(StreetSpec(pts))
    return specs


def _preset_highway_divided(p: PresetParams):
    """Opposing lanes with road_divided=YES — for highways and dual-carriageways."""
    offsets = _lane_offsets(p.lanes, p.sep)
    half    = max(1, len(offsets) // 2)
    n       = _n_linear(p.length, p.split)
    ys      = [p.length * i / max(1, n - 1) for i in range(n)]
    specs   = []
    for i, off in enumerate(offsets):
        pts = [(off, y, 0.0) for y in (list(reversed(ys)) if i >= half else ys)]
        specs.append(StreetSpec(pts, road_divided="YES"))
    return specs


def _preset_alley(p: PresetParams):
    """Single narrow passage with alley flag."""
    return [StreetSpec(_straight_pts(p.length, p.split), alley="YES")]


def _preset_dead_end(p: PresetParams):
    """Dead end / cul-de-sac — STOP intersections at both ends."""
    return [StreetSpec(
        _straight_pts(p.length, p.split),
        intersection_0=str(IntersectionType.STOP),
        intersection_1=str(IntersectionType.STOP),
    )]


def _preset_oneway(p: PresetParams):
    """N parallel lanes all travelling the same direction (one-way street)."""
    return [StreetSpec(_straight_pts(p.length, p.split, off))
            for off in _lane_offsets(p.lanes, p.sep)]


# ── Junctions (topology-fixed — lanes/split intentionally ignored) ────────────

def _preset_t_junction(p: PresetParams):
    """Simple 3-arm T: forward (N), right (E), left (W)."""
    L = p.length
    return [
        StreetSpec([(0,  0, 0), (0,  L, 0)]),
        StreetSpec([(0,  0, 0), (L,  0, 0)]),
        StreetSpec([(-L, 0, 0), (0,  0, 0)]),
    ]


def _preset_t_junction_2lane(p: PresetParams):
    """T-junction with two opposing lanes per arm (uses lane_width for arm spacing)."""
    L, hw = p.length, p.lane_width / 2
    return [
        StreetSpec([(-hw, 0, 0), (-hw, L, 0)]),
        StreetSpec([(hw,  L, 0), (hw,  0, 0)]),
        StreetSpec([(0,  hw, 0), (L,   hw, 0)]),
        StreetSpec([(L, -hw, 0), (0,  -hw, 0)]),
        StreetSpec([(-L, -hw, 0), (0, -hw, 0)]),
        StreetSpec([(0,   hw, 0), (-L, hw, 0)]),
    ]


def _preset_four_way(p: PresetParams):
    """4-way cross: N, S, E, W arms from cursor."""
    L = p.length
    return [
        StreetSpec([(0,  0, 0), (0,  L, 0)]),
        StreetSpec([(0, -L, 0), (0,  0, 0)]),
        StreetSpec([(0,  0, 0), (L,  0, 0)]),
        StreetSpec([(-L, 0, 0), (0,  0, 0)]),
    ]


def _preset_four_way_2lane(p: PresetParams):
    """4-way with two opposing lanes per arm."""
    L, hw = p.length, p.lane_width / 2
    return [
        StreetSpec([(-hw, -L, 0), (-hw, L, 0)]),
        StreetSpec([(hw,   L, 0), (hw, -L, 0)]),
        StreetSpec([(-L,  hw, 0), (L,   hw, 0)]),
        StreetSpec([(L,  -hw, 0), (-L, -hw, 0)]),
    ]


def _preset_y_junction(p: PresetParams):
    """Y-junction: 3 arms at 120° angles."""
    L = p.length
    return [
        StreetSpec([(0, 0, 0), (math.cos(math.radians(a)) * L,
                                math.sin(math.radians(a)) * L, 0)])
        for a in (90, 210, 330)
    ]


def _preset_six_way(p: PresetParams):
    """6-arm star at 60° intervals."""
    L = p.length
    return [
        StreetSpec([(0, 0, 0), (math.cos(math.radians(90 + i * 60)) * L,
                                math.sin(math.radians(90 + i * 60)) * L, 0)])
        for i in range(6)
    ]


def _preset_diagonal_cross(p: PresetParams):
    """4 arms at 45° diagonals."""
    L = p.length
    return [
        StreetSpec([(0, 0, 0), (math.cos(math.radians(d)) * L,
                                math.sin(math.radians(d)) * L, 0)])
        for d in (45, 135, 225, 315)
    ]


# ── Curves (respect lanes, sep, split, radius, n_curve) ───────────────────────

def _preset_curve_90_right(p: PresetParams):
    """N→E (90° right). Multi-lane: each lane gets its own arc radius."""
    R = max(5.0, p.radius)
    return [
        StreetSpec(_arc_pts(R, 0, max(0.1, R + off), 180, 90, 90, p.split, p.n_curve))
        for off in _lane_offsets(p.lanes, p.sep)
    ]


def _preset_curve_90_left(p: PresetParams):
    """N→W (90° left)."""
    R = max(5.0, p.radius)
    return [
        StreetSpec(_arc_pts(-R, 0, max(0.1, R + off), 0, 90, 90, p.split, p.n_curve))
        for off in _lane_offsets(p.lanes, p.sep)
    ]


def _preset_curve_45_right(p: PresetParams):
    """45° right-hand curve."""
    R = max(5.0, p.radius)
    half = max(3, p.n_curve // 2 + 1)
    return [
        StreetSpec(_arc_pts(R, 0, max(0.1, R + off), 180, 135, 45, p.split, half))
        for off in _lane_offsets(p.lanes, p.sep)
    ]


def _preset_curve_180(p: PresetParams):
    """180° U-turn / hairpin."""
    R = max(5.0, p.radius)
    return [
        StreetSpec(_arc_pts(R, 0, max(0.1, R + off), 180, 0, 180, p.split, p.n_curve))
        for off in _lane_offsets(p.lanes, p.sep)
    ]


def _preset_s_curve(p: PresetParams):
    """Right-then-left S-bend."""
    R    = max(5.0, p.radius)
    half = max(3, p.n_curve // 2 + 1)
    specs = []
    for off in _lane_offsets(p.lanes, p.sep):
        r    = max(0.1, R + off)
        pts1 = _arc_pts(R, 0,    r, 180,  90, 90, p.split, half)
        pts2 = _arc_pts(R, 2*R,  r, 270, 360, 90, p.split, half)[1:]
        specs.append(StreetSpec(pts1 + list(pts2)))
    return specs


def _preset_roundabout(p: PresetParams):
    """Circular ring road with 4 entry/exit arms."""
    R, L   = max(5.0, p.radius), p.length
    n_ring = max(8, p.n_curve + 4)
    ring_pts = [
        (R * math.cos(math.radians(360 * i / n_ring)),
         R * math.sin(math.radians(360 * i / n_ring)), 0.0)
        for i in range(n_ring + 1)
    ]
    specs = [StreetSpec(ring_pts)]
    arm = max(L * 0.4, 10.0)
    for deg in (90, 0, 270, 180):
        a  = math.radians(deg)
        ex, ey = R * math.cos(a),         R * math.sin(a)
        ox, oy = (R + arm) * math.cos(a), (R + arm) * math.sin(a)
        specs.append(StreetSpec([(ox, oy, 0), (ex, ey, 0)]))
    return specs


# ── Preset registry ───────────────────────────────────────────────────────────

_BUILDERS = {
    # ── General
    "CUSTOM":         _preset_custom,
    # ── Straight roads
    "SINGLE":         _preset_single_straight,
    "OPPOSING":       _preset_road_opposing,
    "ONEWAY":         _preset_oneway,
    "HIGHWAY":        _preset_highway_divided,
    "ALLEY":          _preset_alley,
    "DEAD_END":       _preset_dead_end,
    # ── Junctions
    "T_JUNCTION":     _preset_t_junction,
    "T_JUNC_2L":      _preset_t_junction_2lane,
    "FOUR_WAY":       _preset_four_way,
    "FOUR_WAY_2L":    _preset_four_way_2lane,
    "Y_JUNCTION":     _preset_y_junction,
    "SIX_WAY":        _preset_six_way,
    "DIAGONAL_X":     _preset_diagonal_cross,
    # ── Curves
    "CURVE_90R":      _preset_curve_90_right,
    "CURVE_90L":      _preset_curve_90_left,
    "CURVE_45R":      _preset_curve_45_right,
    "CURVE_180":      _preset_curve_180,
    "S_CURVE":        _preset_s_curve,
    # ── Complex
    "ROUNDABOUT":     _preset_roundabout,
}

ST_PRESET_ITEMS = [
    # ── General ───────────────────────────────────────────────────────────────
    ("CUSTOM",      "★ Custom",                    "Straight (radius=0) or curved (radius>0) — all params apply"),
    # ── Straight ──────────────────────────────────────────────────────────────
    ("SINGLE",      "Single Lane",                  "One centre-line AI path"),
    ("OPPOSING",    "Opposing Lanes",               "N lanes split into two opposing directions"),
    ("ONEWAY",      "One-Way (N lanes)",             "N parallel lanes all going the same direction"),
    ("HIGHWAY",     "Highway (Divided)",             "Opposing lanes with road_divided flag"),
    ("ALLEY",       "Alley",                         "Single-lane narrow passage, alley flag set"),
    ("DEAD_END",    "Dead End",                      "Single lane, STOP intersections at both ends"),
    # ── Junctions ─────────────────────────────────────────────────────────────
    ("T_JUNCTION",  "T-Junction",                   "3 arms: N, E, W from cursor"),
    ("T_JUNC_2L",   "T-Junction (2-lane)",           "T with two opposing lanes per arm"),
    ("FOUR_WAY",    "4-Way Junction",               "4 arms: N/S/E/W from cursor"),
    ("FOUR_WAY_2L", "4-Way Junction (2-lane)",       "4-way with two opposing lanes per arm"),
    ("Y_JUNCTION",  "Y-Junction",                   "3 arms at 120°"),
    ("SIX_WAY",     "6-Way Star",                   "6 arms at 60° intervals"),
    ("DIAGONAL_X",  "Diagonal Cross (×)",           "4 arms at 45° diagonals"),
    # ── Curves ────────────────────────────────────────────────────────────────
    ("CURVE_90R",   "Curve 90° Right",              "N→E; lanes, sep, radius, split all apply"),
    ("CURVE_90L",   "Curve 90° Left",               "N→W; lanes, sep, radius, split all apply"),
    ("CURVE_45R",   "Curve 45° Right",              "Shallow right; lanes + split + radius"),
    ("CURVE_180",   "Curve 180° (U-turn)",          "Full hairpin; lanes + split + radius"),
    ("S_CURVE",     "S-Curve",                      "Right-then-left bend; lanes + split + radius"),
    # ── Complex ───────────────────────────────────────────────────────────────
    ("ROUNDABOUT",  "Roundabout",                   "Circular ring + 4 entry/exit arms"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_preset_subcollection(key: str) -> bpy.types.Collection:
    """Create a numbered child collection inside 'AI Streets' for one spawn batch."""
    parent = _get_or_create_ai_streets_collection()
    i = 1
    while True:
        name = f"{key}_{i:03d}"
        if name not in bpy.data.collections:
            break
        i += 1
    col = bpy.data.collections.new(name)
    parent.children.link(col)
    return col


def _apply_converge(specs: list, start: bool, end: bool) -> list:
    """Pin all lane endpoints to the centre lane's start and/or end point."""
    if not specs or (not start and not end):
        return specs
    ci = len(specs) // 2
    cv = list(specs[ci].vertices)
    out = []
    for spec in specs:
        verts = list(spec.vertices)
        if start:
            verts[0]  = cv[0]
        if end:
            verts[-1] = cv[-1]
        out.append(spec._replace(vertices=verts))
    return out


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

        params = PresetParams(
            length     = scene.st_preset_length,
            split      = scene.st_preset_length_split,
            lanes      = scene.st_preset_lanes,
            sep        = scene.st_preset_lane_separator,
            radius     = scene.st_preset_turn_radius,
            n_curve    = scene.st_preset_curve_points,
            lane_width = scene.st_preset_lane_width,
        )

        specs = builder(params)

        # Converge endpoints to centre lane
        specs = _apply_converge(
            specs,
            start = scene.st_preset_converge_start,
            end   = scene.st_preset_converge_end,
        )

        # Sub-collection groups this spawn batch in the Outliner
        sub_col    = _get_or_create_preset_subcollection(key)
        grouped    = scene.st_preset_grouped
        group_name = sub_col.name if grouped else ""

        cursor  = context.scene.cursor.location
        created = []

        for spec in specs:
            if len(spec.vertices) < 2:
                continue
            name = _next_street_name(scene)
            world_pts = [
                (cursor.x + v[0], cursor.y + v[1], cursor.z + v[2])
                for v in spec.vertices
            ]
            obj = _build_curve_object(f"{ST_PREFIX}{name}", world_pts, context,
                                      collection=sub_col)
            _set_street_defaults(obj)

            obj.st_group_name        = group_name
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

        label = f"grouped as '{group_name}'" if grouped else f"{len(created)} street(s)"
        self.report({"INFO"}, f"Spawned {len(created)} street(s) → '{sub_col.name}' ({label})")
        return {"FINISHED"}


STREET_PRESET_CLASSES = [
    OBJECT_OT_SpawnStreetPreset,
]

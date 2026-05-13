import bpy
import math
from typing import NamedTuple, List
from pathlib import Path
from src.constants.file_formats import Material, Room
from src.constants.color import Color
from src.integrations.blender.utils import get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties
from src.integrations.blender.modeling import uv_mapping as _uvm

def _get_texture_folder():
    """Live accessor — `_texture_folder` is reassigned by set_texture_folder()
    after this module imports, so we read it from the module each call."""
    return _uvm._texture_folder

from src.constants.textures import Texture


class PolySpec(NamedTuple):
    width:          float
    length:         float
    offset_x:       float
    offset_y:       float
    texture:        str
    material_index: int   = Material.DEFAULT
    cell_type:      int   = Room.DEFAULT
    hud_color:      str   = Color.ROAD
    tile_x:         float = 2.0
    tile_y:         float = 2.0
    angle_degrees:  float = 0.0   # texture / UV rotation
    rotation_z:     float = 0.0   # actual mesh rotation around Z (degrees)
    z_offset:       float = 0.0   # height offset for hills / multi-level


# ── Layout helpers ─────────────────────────────────────────────────────────────

def _build_intersection(
    h_lanes: int,
    v_lanes: int,
    *,
    lane_width:    float = 6.0,
    sidewalk_w:    float = 5.0,
    zebra_depth:   float = 4.0,
    arm_length:    float = 16.0,
    include_arms:  tuple = ("N", "S", "E", "W"),   # which arms exist (omit = T-junction etc.)
    include_zebra: bool  = True,
    one_way:       bool  = False,
) -> List[PolySpec]:
    """
    Build a generic perpendicular intersection (T, 4-way, or partial).
    All polygons axis-aligned. Sidewalk corners + curb-ramp cut-outs auto-placed.

    Texture conventions:
        ROAD_*_LANE  — striped along its length axis. We rotate vertical roads
                       with angle_degrees=90 so dashes run correctly N-S.
        SIDEWALK     — tile_x=4, tile_y=1 along sidewalk length.
        ZEBRA        — stripes perpendicular to direction of travel.
    """
    H = h_lanes * lane_width    # horizontal road width (Y-extent of horizontal arm)
    V = v_lanes * lane_width    # vertical road width (X-extent of vertical arm)
    hh, vh = H / 2, V / 2
    sw     = sidewalk_w
    zd     = zebra_depth
    al     = arm_length         # length of each road arm from intersection edge

    road_h_tex = {1: Texture.ROAD_1_LANE, 2: Texture.ROAD_2_LANE, 3: Texture.ROAD_3_LANE}.get(h_lanes, Texture.ROAD_3_LANE)
    road_v_tex = {1: Texture.ROAD_1_LANE, 2: Texture.ROAD_2_LANE, 3: Texture.ROAD_3_LANE}.get(v_lanes, Texture.ROAD_3_LANE)

    specs: List[PolySpec] = []

    # ── Intersection core ─────────────────────────────────────────────────
    specs.append(PolySpec(
        width=V, length=H, offset_x=0, offset_y=0,
        texture=Texture.INTERSECTION, tile_x=max(V / 10.0, 2.0), tile_y=max(H / 10.0, 2.0),
        angle_degrees=0.0,
    ))

    has_n = "N" in include_arms
    has_s = "S" in include_arms
    has_e = "E" in include_arms
    has_w = "W" in include_arms

    # ── Horizontal arms (E / W) with zebra in front of intersection ────────
    if has_w:
        # zebra (west of intersection)
        if include_zebra:
            specs.append(PolySpec(
                width=zd, length=H, offset_x=-vh - zd / 2, offset_y=0,
                texture=Texture.ZEBRA_CROSSING, tile_x=1.0, tile_y=max(H / 4.0, 2.0),
                angle_degrees=0.0,
            ))
        # road (further west)
        road_off  = -vh - (zd if include_zebra else 0) - al / 2
        specs.append(PolySpec(
            width=al, length=H, offset_x=road_off, offset_y=0,
            texture=road_h_tex, tile_x=max(al / 10.0, 1.5), tile_y=max(H / 5.0, 2.0),
            angle_degrees=0.0,
        ))
        # outer extents in X for sidewalks
    if has_e:
        if include_zebra:
            specs.append(PolySpec(
                width=zd, length=H, offset_x=vh + zd / 2, offset_y=0,
                texture=Texture.ZEBRA_CROSSING, tile_x=1.0, tile_y=max(H / 4.0, 2.0),
            ))
        road_off = vh + (zd if include_zebra else 0) + al / 2
        specs.append(PolySpec(
            width=al, length=H, offset_x=road_off, offset_y=0,
            texture=road_h_tex, tile_x=max(al / 10.0, 1.5), tile_y=max(H / 5.0, 2.0),
        ))
    if has_n:
        if include_zebra:
            specs.append(PolySpec(
                width=V, length=zd, offset_x=0, offset_y=hh + zd / 2,
                texture=Texture.ZEBRA_CROSSING, tile_x=max(V / 4.0, 2.0), tile_y=1.0,
                angle_degrees=90.0,
            ))
        road_off = hh + (zd if include_zebra else 0) + al / 2
        specs.append(PolySpec(
            width=V, length=al, offset_x=0, offset_y=road_off,
            texture=road_v_tex, tile_x=max(V / 5.0, 2.0), tile_y=max(al / 10.0, 1.5),
            angle_degrees=90.0,
        ))
    if has_s:
        if include_zebra:
            specs.append(PolySpec(
                width=V, length=zd, offset_x=0, offset_y=-hh - zd / 2,
                texture=Texture.ZEBRA_CROSSING, tile_x=max(V / 4.0, 2.0), tile_y=1.0,
                angle_degrees=90.0,
            ))
        road_off = -hh - (zd if include_zebra else 0) - al / 2
        specs.append(PolySpec(
            width=V, length=al, offset_x=0, offset_y=road_off,
            texture=road_v_tex, tile_x=max(V / 5.0, 2.0), tile_y=max(al / 10.0, 1.5),
            angle_degrees=90.0,
        ))

    # ── Sidewalks ─────────────────────────────────────────────────────────
    # Outer X extent: half of horizontal-arm bounding box
    h_outer = vh + (zd if include_zebra else 0) + al   # absolute |x| extent of horizontal roads
    v_outer = hh + (zd if include_zebra else 0) + al

    # Side strips parallel to horizontal arms (above & below each arm)
    for sign_y in (+1, -1):
        if (sign_y > 0 and not (has_e or has_w)) or (sign_y < 0 and not (has_e or has_w)):
            continue
        side_y = sign_y * (hh + sw / 2)
        if has_w:
            specs.append(PolySpec(
                width=h_outer - vh, length=sw,
                offset_x=-(vh + (h_outer - vh) / 2), offset_y=side_y,
                texture=Texture.SIDEWALK, tile_x=max((h_outer - vh) / 5.0, 2.0), tile_y=1.0,
                angle_degrees=0.0,
            ))
        if has_e:
            specs.append(PolySpec(
                width=h_outer - vh, length=sw,
                offset_x=(vh + (h_outer - vh) / 2), offset_y=side_y,
                texture=Texture.SIDEWALK, tile_x=max((h_outer - vh) / 5.0, 2.0), tile_y=1.0,
                angle_degrees=0.0,
            ))

    # Side strips parallel to vertical arms
    for sign_x in (+1, -1):
        if (sign_x > 0 and not (has_n or has_s)):
            continue
        side_x = sign_x * (vh + sw / 2)
        if has_n:
            specs.append(PolySpec(
                width=sw, length=v_outer - hh,
                offset_x=side_x, offset_y=hh + (v_outer - hh) / 2,
                texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max((v_outer - hh) / 5.0, 2.0),
                angle_degrees=90.0,
            ))
        if has_s:
            specs.append(PolySpec(
                width=sw, length=v_outer - hh,
                offset_x=side_x, offset_y=-(hh + (v_outer - hh) / 2),
                texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max((v_outer - hh) / 5.0, 2.0),
                angle_degrees=90.0,
            ))

    # Corner squares: present only when both adjacent arms exist OR the
    # corner is on the closed side of a T-junction (then it bridges across).
    def _corner(sx: int, sy: int):
        cx = sx * (vh + sw / 2)
        cy = sy * (hh + sw / 2)
        specs.append(PolySpec(
            width=sw, length=sw, offset_x=cx, offset_y=cy,
            texture=Texture.SIDEWALK, tile_x=1.0, tile_y=1.0,
        ))

    # Decide which corner pieces to place
    corner_map = {
        (+1, +1): (has_e, has_n),
        (-1, +1): (has_w, has_n),
        (+1, -1): (has_e, has_s),
        (-1, -1): (has_w, has_s),
    }
    for (sx, sy), (a, b) in corner_map.items():
        if a and b:
            _corner(sx, sy)

    # T-junction closed side: a single long sidewalk strip across the closed arm
    if not has_n:
        # Span across top, including over where intersection meets sidewalk
        total_w = 2 * h_outer
        specs.append(PolySpec(
            width=total_w, length=sw, offset_x=0, offset_y=hh + sw / 2,
            texture=Texture.SIDEWALK, tile_x=max(total_w / 5.0, 4.0), tile_y=1.0,
        ))
    if not has_s:
        total_w = 2 * h_outer
        specs.append(PolySpec(
            width=total_w, length=sw, offset_x=0, offset_y=-hh - sw / 2,
            texture=Texture.SIDEWALK, tile_x=max(total_w / 5.0, 4.0), tile_y=1.0,
        ))
    if not has_e:
        total_h = 2 * v_outer
        specs.append(PolySpec(
            width=sw, length=total_h, offset_x=vh + sw / 2, offset_y=0,
            texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max(total_h / 5.0, 4.0),
        ))
    if not has_w:
        total_h = 2 * v_outer
        specs.append(PolySpec(
            width=sw, length=total_h, offset_x=-vh - sw / 2, offset_y=0,
            texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max(total_h / 5.0, 4.0),
        ))

    return specs


def _build_roundabout(
    *,
    outer_radius:  float = 18.0,
    road_width:    float = 7.0,
    sidewalk_w:    float = 4.0,
    arm_length:    float = 16.0,
    segments:      int   = 8,
    arms:          tuple = ("N", "S", "E", "W"),
) -> List[PolySpec]:
    """Roundabout: central grass island ringed by N rotated road segments, plus arms."""
    specs: List[PolySpec] = []
    inner_r = outer_radius - road_width
    seg_angle = 360.0 / segments
    # Tangent chord length at the centre radius of the ring
    centre_r = (outer_radius + inner_r) / 2
    chord = 2 * centre_r * math.tan(math.radians(seg_angle / 2))

    # Ring of road segments
    for i in range(segments):
        a = i * seg_angle
        rad = math.radians(a)
        cx = centre_r * math.cos(rad)
        cy = centre_r * math.sin(rad)
        specs.append(PolySpec(
            width=chord, length=road_width,
            offset_x=cx, offset_y=cy,
            texture=Texture.INTERSECTION,
            tile_x=max(chord / 5.0, 1.5), tile_y=max(road_width / 5.0, 1.0),
            rotation_z=a + 90.0,
        ))

    # Central grass island (square inscribed inside inner circle)
    island_side = inner_r * 1.4
    specs.append(PolySpec(
        width=island_side, length=island_side, offset_x=0, offset_y=0,
        texture=Texture.GRASS, tile_x=2.0, tile_y=2.0,
    ))

    # Approach arms
    arm_map = {"E": 0.0, "N": 90.0, "W": 180.0, "S": 270.0}
    for arm in arms:
        a = arm_map[arm]
        rad = math.radians(a)
        # Road segment from outer ring outward
        ox = (outer_radius + arm_length / 2) * math.cos(rad)
        oy = (outer_radius + arm_length / 2) * math.sin(rad)
        specs.append(PolySpec(
            width=arm_length, length=road_width * 2.0,
            offset_x=ox, offset_y=oy,
            texture=Texture.ROAD_2_LANE,
            tile_x=max(arm_length / 8.0, 1.5), tile_y=2.0,
            rotation_z=a,
        ))
        # Sidewalks flanking each arm
        for side in (+1, -1):
            sx = ox + math.cos(rad + math.pi / 2) * side * (road_width + sidewalk_w / 2)
            sy = oy + math.sin(rad + math.pi / 2) * side * (road_width + sidewalk_w / 2)
            specs.append(PolySpec(
                width=arm_length, length=sidewalk_w,
                offset_x=sx, offset_y=sy,
                texture=Texture.SIDEWALK,
                tile_x=max(arm_length / 5.0, 2.0), tile_y=1.0,
                rotation_z=a,
            ))

    return specs


def _build_driveway(
    *,
    boulevard_lanes: int   = 3,
    lane_width:      float = 6.0,
    access_width:    float = 8.0,
    access_length:   float = 18.0,
    sidewalk_w:      float = 5.0,
    ramp_depth:      float = 4.0,
) -> List[PolySpec]:
    """Image 5 — boulevard with a side-road driveway (curb ramps, no zebra)."""
    H = boulevard_lanes * lane_width
    hh = H / 2
    aw = access_width
    al = access_length
    specs: List[PolySpec] = []

    # Boulevard core (60 wide)
    specs.append(PolySpec(
        width=60.0, length=H, offset_x=0, offset_y=0,
        texture=Texture.ROAD_3_LANE, tile_x=6.0, tile_y=max(H / 5.0, 2.0),
    ))
    # Junction patch (where access meets boulevard) - just asphalt
    specs.append(PolySpec(
        width=aw, length=H, offset_x=0, offset_y=0,
        texture=Texture.INTERSECTION, tile_x=1.0, tile_y=max(H / 4.0, 2.0),
    ))
    # Access road south
    specs.append(PolySpec(
        width=aw, length=al, offset_x=0, offset_y=-hh - al / 2,
        texture=Texture.ROAD_1_LANE, tile_x=2.0, tile_y=max(al / 8.0, 2.0),
        angle_degrees=90.0,
    ))
    # Sidewalks: along boulevard south side, with two diagonal "curb ramps"
    # flanking the access road. Approximated as small dark rectangles.
    # Left long strip
    strip_w = (60.0 - aw) / 2 - ramp_depth
    specs.append(PolySpec(
        width=strip_w, length=sidewalk_w,
        offset_x=-(aw / 2 + ramp_depth + strip_w / 2), offset_y=-hh - sidewalk_w / 2,
        texture=Texture.SIDEWALK, tile_x=max(strip_w / 5.0, 3.0), tile_y=1.0,
    ))
    specs.append(PolySpec(
        width=strip_w, length=sidewalk_w,
        offset_x=(aw / 2 + ramp_depth + strip_w / 2), offset_y=-hh - sidewalk_w / 2,
        texture=Texture.SIDEWALK, tile_x=max(strip_w / 5.0, 3.0), tile_y=1.0,
    ))
    # Diagonal ramps (rotated dark intersection texture)
    for sx in (+1, -1):
        cx = sx * (aw / 2 + ramp_depth / 2)
        specs.append(PolySpec(
            width=ramp_depth * 1.4, length=sidewalk_w * 1.1,
            offset_x=cx, offset_y=-hh - sidewalk_w / 2,
            texture=Texture.INTERSECTION,
            tile_x=1.0, tile_y=1.0,
            rotation_z=-45.0 * sx,
        ))
    # North sidewalk (continuous)
    specs.append(PolySpec(
        width=60.0, length=sidewalk_w, offset_x=0, offset_y=hh + sidewalk_w / 2,
        texture=Texture.SIDEWALK, tile_x=12.0, tile_y=1.0,
    ))
    # Side sidewalks along access road
    for sx in (+1, -1):
        specs.append(PolySpec(
            width=sidewalk_w, length=al,
            offset_x=sx * (aw / 2 + sidewalk_w / 2), offset_y=-hh - al / 2,
            texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max(al / 5.0, 3.0),
        ))

    return specs


def _build_y_intersection(
    *,
    lane_width:  float = 6.0,
    lanes:       int   = 2,
    arm_length:  float = 18.0,
    sidewalk_w:  float = 4.0,
    branch_deg:  float = 60.0,
) -> List[PolySpec]:
    """3-way Y-intersection — three arms meeting at angles ±branch_deg from south."""
    W = lanes * lane_width
    specs: List[PolySpec] = []

    # Central triangular-ish intersection patch (approximated by hexagon-bounding square)
    specs.append(PolySpec(
        width=W * 1.6, length=W * 1.6, offset_x=0, offset_y=0,
        texture=Texture.INTERSECTION, tile_x=3.0, tile_y=3.0,
    ))

    # Three arm angles, measured CCW from +X
    angles = [90.0, 90.0 + (180.0 - branch_deg), 90.0 - (180.0 - branch_deg)]
    for a in angles:
        rad = math.radians(a)
        cx = (arm_length / 2 + W * 0.8) * math.cos(rad)
        cy = (arm_length / 2 + W * 0.8) * math.sin(rad)
        # Road
        specs.append(PolySpec(
            width=arm_length, length=W,
            offset_x=cx, offset_y=cy,
            texture=Texture.ROAD_2_LANE,
            tile_x=max(arm_length / 8.0, 2.0), tile_y=2.0,
            rotation_z=a,
        ))
        # Zebra near the intersection
        zx = (W * 0.85) * math.cos(rad)
        zy = (W * 0.85) * math.sin(rad)
        specs.append(PolySpec(
            width=3.0, length=W,
            offset_x=zx, offset_y=zy,
            texture=Texture.ZEBRA_CROSSING, tile_x=1.0, tile_y=2.0,
            rotation_z=a,
        ))
        # Sidewalks on both sides of arm
        for side in (+1, -1):
            sx = cx + math.cos(rad + math.pi / 2) * side * (W / 2 + sidewalk_w / 2)
            sy = cy + math.sin(rad + math.pi / 2) * side * (W / 2 + sidewalk_w / 2)
            specs.append(PolySpec(
                width=arm_length, length=sidewalk_w,
                offset_x=sx, offset_y=sy,
                texture=Texture.SIDEWALK,
                tile_x=max(arm_length / 5.0, 3.0), tile_y=1.0,
                rotation_z=a,
            ))

    return specs


def _build_hill_segment(
    *,
    lanes:        int   = 2,
    lane_width:   float = 6.0,
    length:       float = 30.0,
    peak_height:  float = 4.0,
    sidewalk_w:   float = 4.0,
    sections:     int   = 5,
) -> List[PolySpec]:
    """A straight road that rises to a crest then falls — sections piecewise on Z."""
    specs: List[PolySpec] = []
    W = lanes * lane_width
    sec_len = length / sections
    for i in range(sections):
        # Trigonometric hill profile (0 → 1 → 0 across sections)
        t  = (i + 0.5) / sections
        z  = peak_height * math.sin(math.pi * t)
        y  = -length / 2 + sec_len * (i + 0.5)
        specs.append(PolySpec(
            width=W, length=sec_len, offset_x=0, offset_y=y,
            texture=Texture.ROAD_2_LANE, tile_x=2.0, tile_y=max(sec_len / 5.0, 1.0),
            angle_degrees=90.0, z_offset=z,
        ))
        # Sidewalks
        for sx in (+1, -1):
            specs.append(PolySpec(
                width=sidewalk_w, length=sec_len,
                offset_x=sx * (W / 2 + sidewalk_w / 2), offset_y=y,
                texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max(sec_len / 5.0, 1.0),
                angle_degrees=90.0, z_offset=z,
            ))
    return specs


def _build_road_zebra(
    *,
    lanes: int = 2, lane_width: float = 6.0,
    arm_length: float = 14.0, zebra_depth: float = 4.0, sidewalk_w: float = 4.0,
) -> List[PolySpec]:
    """A straight road segment broken in the middle by a single zebra crossing."""
    W = lanes * lane_width
    specs: List[PolySpec] = []
    # Two road halves
    for sy in (+1, -1):
        oy = sy * (zebra_depth / 2 + arm_length / 2)
        specs.append(PolySpec(
            width=W, length=arm_length, offset_x=0, offset_y=oy,
            texture=Texture.ROAD_2_LANE, tile_x=2.0, tile_y=max(arm_length / 5.0, 2.0),
            angle_degrees=90.0,
        ))
    # Zebra
    specs.append(PolySpec(
        width=W, length=zebra_depth, offset_x=0, offset_y=0,
        texture=Texture.ZEBRA_CROSSING, tile_x=max(W / 4.0, 2.0), tile_y=1.0,
        angle_degrees=90.0,
    ))
    # Sidewalks along full length
    total_len = arm_length * 2 + zebra_depth
    for sx in (+1, -1):
        specs.append(PolySpec(
            width=sidewalk_w, length=total_len,
            offset_x=sx * (W / 2 + sidewalk_w / 2), offset_y=0,
            texture=Texture.SIDEWALK, tile_x=1.0, tile_y=max(total_len / 5.0, 3.0),
            angle_degrees=90.0,
        ))
    return specs


# ── Preset registry ────────────────────────────────────────────────────────────

PRESETS: dict[str, List[PolySpec]] = {

    "ROAD_SIDEWALK": [
        PolySpec(width=20.0, length=20.0, offset_x=0.0,   offset_y=0.0, texture=Texture.ROAD_2_LANE, tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-12.5, offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=12.5,  offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
    ],
    "BOULEVARD_SIDEWALK": [
        PolySpec(width=30.0, length=20.0, offset_x=0.0,   offset_y=0.0, texture=Texture.ROAD_3_LANE, tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=-17.5, offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=-90.0),
        PolySpec(width=5.0,  length=20.0, offset_x=17.5,  offset_y=0.0, texture=Texture.SIDEWALK,    tile_x=4.0, tile_y=1.0, angle_degrees=90.0),
    ],
    "ALLEY": [
        PolySpec(width=8.0, length=20.0, offset_x=0.0, offset_y=0.0, texture=Texture.ROAD_1_LANE, tile_x=2.0, tile_y=2.0, angle_degrees=90.0),
    ],

    # ── Intersections (T) ─────────────────────────────────────────────────
    "T_INT_SMALL":  _build_intersection(h_lanes=2, v_lanes=2, lane_width=6.0,  sidewalk_w=5.0,
                                        arm_length=14.0, include_arms=("E", "W", "S")),
    "T_INT_BIG":    _build_intersection(h_lanes=3, v_lanes=2, lane_width=6.0,  sidewalk_w=6.0,
                                        arm_length=18.0, include_arms=("E", "W", "S")),

    # ── Intersections (4-way) ─────────────────────────────────────────────
    "INT_4WAY_SMALL": _build_intersection(h_lanes=2, v_lanes=2, lane_width=6.0,  sidewalk_w=5.0,
                                          arm_length=14.0),
    "INT_4WAY_BIG":   _build_intersection(h_lanes=3, v_lanes=3, lane_width=6.0,  sidewalk_w=6.0,
                                          arm_length=18.0),

    # ── No-zebra variants ─────────────────────────────────────────────────
    "INT_4WAY_NOZEBRA": _build_intersection(h_lanes=2, v_lanes=2, lane_width=6.0, sidewalk_w=5.0,
                                            arm_length=14.0, include_zebra=False),

    # ── Y / diagonal junction ─────────────────────────────────────────────
    "Y_INT_3WAY": _build_y_intersection(lanes=2, lane_width=6.0, arm_length=18.0,
                                         sidewalk_w=4.0, branch_deg=60.0),

    # ── Driveway / banked-access ──────────────────────────────────────────
    "DRIVEWAY": _build_driveway(),

    # ── Roundabout ────────────────────────────────────────────────────────
    "ROUNDABOUT": _build_roundabout(outer_radius=18.0, road_width=7.0,
                                    sidewalk_w=4.0, arm_length=16.0, segments=12),

    # ── Hill / sloped road (multi-section) ────────────────────────────────
    "ROAD_HILL": _build_hill_segment(lanes=2, lane_width=6.0, length=40.0,
                                     peak_height=4.0, sidewalk_w=4.0, sections=7),

    # ── Road with single zebra crossing ───────────────────────────────────
    "ROAD_ZEBRA": _build_road_zebra(),
}


PRESET_ITEMS = [
    ("ROAD_SIDEWALK",      "Road + Sidewalk",            "2-lane road with sidewalks on both sides"),
    ("BOULEVARD_SIDEWALK", "Boulevard + Sidewalk",       "Wide 3-lane road with sidewalks"),
    ("ALLEY",              "Alley",                      "Narrow 1-lane road, no sidewalks"),
    ("ROAD_ZEBRA",         "Road + Zebra",               "Straight road with one zebra crossing"),
    ("T_INT_SMALL",        "T-Intersection (small)",     "T-junction, 2x2 lanes + zebras + sidewalks"),
    ("T_INT_BIG",          "T-Intersection (big)",       "T-junction, 6-lane boulevard meets 2-lane"),
    ("INT_4WAY_SMALL",     "4-Way Intersection (small)", "4-way, 2x2 lanes + zebras + sidewalks"),
    ("INT_4WAY_BIG",       "4-Way Intersection (big)",   "4-way, 6-lane boulevard crossroads"),
    ("INT_4WAY_NOZEBRA",   "4-Way (no zebra)",           "Plain crossroads, no pedestrian crossings"),
    ("Y_INT_3WAY",         "Y-Intersection (3-way)",     "Diagonal 3-way junction with angled arms"),
    ("DRIVEWAY",           "Driveway / Side-Access",     "Boulevard with curb-ramp side road"),
    ("ROUNDABOUT",         "Roundabout",                 "Circular roundabout with grass island"),
    ("ROAD_HILL",          "Road Hill",                  "Sloped road that crests and descends"),
]


class OBJECT_OT_SpawnHeart(bpy.types.Operator):
    bl_idname      = "object.spawn_heart"
    bl_label       = "♥ Spawn Heart"
    bl_description = "Spawn a smooth heart shape (24 triangles) at the 3D cursor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        N     = 24    # triangles / perimeter samples
        scale = 1.5   # ~48 units wide — good game scale

        # Parametric heart curve — tip points down
        perimeter = []
        for i in range(N):
            t = 2 * math.pi * i / N
            x =  16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
                  - 2 * math.cos(3 * t) - math.cos(4 * t))
            perimeter.append((x * scale, y * scale, 0.0))

        cx = sum(p[0] for p in perimeter) / N
        cy = sum(p[1] for p in perimeter) / N

        verts = [(cx, cy, 0.0)] + perimeter
        faces = [(0, i + 1, (i + 1) % N + 1) for i in range(N)]

        mesh = bpy.data.meshes.new("Heart")
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        obj = bpy.data.objects.new("Heart", mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = context.scene.cursor.location.copy()

        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name="UVMap")

        assign_map_editor_properties(obj)
        used = get_used_bound_numbers(context.scene)
        num  = next_available_bound_number(used)
        obj.name              = f"P{num}"
        obj["material_index"] = str(Material.GRASS)
        obj["cell_type"]      = str(0)
        obj.tile_x            = 4.0
        obj.tile_y            = 4.0

        _apply_material(obj, Texture.GRASS, _get_texture_folder())

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({"INFO"}, f"Spawned heart ({N} tris) as P{num}")
        return {"FINISHED"}


def _apply_material(obj: bpy.types.Object, texture: str, texture_folder) -> None:
    if not texture_folder:
        return

    texture_path = Path(str(texture_folder)) / f"{texture}.DDS"
    if not texture_path.exists():
        return

    mat = bpy.data.materials.get(texture) or bpy.data.materials.new(name=texture)

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.active_material = mat
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    bsdf     = nodes.new("ShaderNodeBsdfPrincipled")
    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = bpy.data.images.load(str(texture_path), check_existing=True)
    output   = nodes.new("ShaderNodeOutputMaterial")

    links = mat.node_tree.links
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"],      output.inputs["Surface"])


def _create_rect_object(name: str, width: float, length: float) -> bpy.types.Object:
    hw, hl = width / 2, length / 2
    verts = [(-hw, -hl, 0.0), (hw, -hl, 0.0), (hw, hl, 0.0), (-hw, hl, 0.0)]
    faces = [(0, 1, 2, 3)]

    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    bpy.context.collection.objects.link(obj)

    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")

    return obj


class OBJECT_OT_SpawnPreset(bpy.types.Operator):
    bl_idname      = "object.spawn_polygon_preset"
    bl_label       = "Spawn Preset"
    bl_description = "Spawn a group of connected polygons at the 3D cursor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        preset_key = context.scene.polygon_preset
        specs      = PRESETS.get(preset_key)

        if not specs:
            self.report({"ERROR"}, f"Unknown preset: {preset_key}")
            return {"CANCELLED"}

        cursor  = context.scene.cursor.location
        used    = get_used_bound_numbers(context.scene)
        created = []

        for spec in specs:
            num = next_available_bound_number(used)
            used.add(num)

            obj = _create_rect_object(f"P{num}", spec.width, spec.length)
            obj.location = (
                cursor.x + spec.offset_x,
                cursor.y + spec.offset_y,
                cursor.z + spec.z_offset,
            )
            if spec.rotation_z != 0.0:
                obj.rotation_euler = (0.0, 0.0, math.radians(spec.rotation_z))

            assign_map_editor_properties(obj)
            obj["cell_type"]      = str(spec.cell_type)
            obj["material_index"] = str(spec.material_index)

            obj.tile_x            = spec.tile_x
            obj.tile_y            = spec.tile_y
            obj.angle_degrees     = spec.angle_degrees

            _apply_material(obj, spec.texture, _get_texture_folder())
            created.append(obj)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in created:
            obj.select_set(True)
        if created:
            context.view_layer.objects.active = created[0]

        self.report({"INFO"}, f"Spawned {len(created)} polygon(s) from '{preset_key}'")
        return {"FINISHED"}

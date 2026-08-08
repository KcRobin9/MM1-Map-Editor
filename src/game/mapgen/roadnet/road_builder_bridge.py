"""
Phase 2 bridge: Blender Road Builder spines  ->  a roadnet `RoadNetwork`.

The Road Builder is the visual authoring surface (draw a spline, set its cross-section and
AI knobs); roadnet is the compiler. This takes the authored roads, welds their endpoints into
junction Nodes, and emits a `RoadNetwork` whose Edges carry EVERY authored knob (lanes
fwd/rev, sidewalks=peds per side, alley, divided/median, curves, intersection types).

KEPT BLENDER-FREE on purpose: this module takes PLAIN DICTS (one per authored road), never
`bpy` objects, so it is unit-testable standalone. The thin reader that pulls `RS_*` objects
into these dicts lives in the Blender integration (`read_road_spines`), and only it needs bpy.

One road dict (all keys optional except `points`):

    {
      "points":        [(x, z), (x, z), ...],   # spine vertices, MM1 ground coords, start..end
      "lane_count":    2,        # rs_lane_count   (lanes PER DIRECTION)
      "lane_width":    5.0,      # rs_lane_width
      "two_way":       True,     # rd_ai_two_way   (False -> one-way, forward only)
      "sidewalk":      True,     # rs_sidewalk_enabled  (sidewalk == pedestrians)
      "sidewalk_side": "BOTH",   # rs_sidewalk_side: BOTH | LEFT | RIGHT
      "sidewalk_width":2.5,      # rs_sidewalk_width
      "curb":          True,     # rs_curb_enabled
      "curb_width":    0.3,      # rs_curb_width
      "median":        False,    # rs_median_enabled
      "median_width":  1.0,      # rs_median_width
      "alley":         False,    # rd_ai_alley
      "isect_start":   3,        # rd_ai_intersection_start  (3 continue/1 light/0 stop/2 yield)
      "isect_end":     3,        # rd_ai_intersection_end
      "speed_limit":   15.0,
    }
"""
from typing import List, Sequence, Tuple

from src.game.mapgen.roadnet.graph import RoadNetwork, DEFAULT_LANE_WIDTH, DEFAULT_SIDEWALK_WIDTH

# Intersection-type ints, matching Edge.intersection_type / the Blender enum order.
ISECT_CONTINUE, ISECT_STOPLIGHT, ISECT_STOP, ISECT_YIELD = 3, 1, 0, 2


def _sidewalk_sides(road: dict) -> Tuple[bool, bool]:
    """rs_sidewalk_enabled + rs_sidewalk_side -> (sidewalk_fwd, sidewalk_rev).

    fwd carriageway runs a->b (its sidewalk is on the LEFT of travel); rev runs b->a (RIGHT).
    """
    if not road.get("sidewalk", True):
        return False, False
    side = str(road.get("sidewalk_side", "BOTH")).upper()
    if side == "LEFT":
        return True, False
    if side == "RIGHT":
        return False, True
    return True, True


def roads_to_network(roads: Sequence[dict], *, snap: float = 8.0,
                     name: str = "BlenderCity") -> RoadNetwork:
    """
    Weld authored road spines into a `RoadNetwork`: endpoints within `snap` of each other
    become one junction Node; each spine becomes one Edge carrying its authored cross-section
    + AI flags, with its intermediate vertices as the Edge `shape` (curve).
    """
    net = RoadNetwork(name=name)

    # 1) Weld endpoints into nodes. First pass collects (a, b, shape, road) with welded ids;
    #    node centres accumulate so a junction sits at the mean of the points snapped to it.
    centres: List[List[float]] = []   # [sum_x, sum_z, count] per node
    s2 = snap * snap

    def weld(p) -> int:
        px, pz = float(p[0]), float(p[1])
        for i, c in enumerate(centres):
            cx, cz = c[0] / c[2], c[1] / c[2]
            if (cx - px) ** 2 + (cz - pz) ** 2 <= s2:
                c[0] += px; c[1] += pz; c[2] += 1
                return i
        centres.append([px, pz, 1])
        return len(centres) - 1

    specs: List[Tuple[int, int, tuple, dict]] = []
    for road in roads:
        pts = list(road.get("points") or [])
        if len(pts) < 2:
            continue
        a = weld(pts[0])
        b = weld(pts[-1])
        if a == b:
            continue                                   # spine loops back onto its own junction
        shape = tuple((float(x), float(z)) for (x, z) in pts[1:-1])
        specs.append((a, b, shape, road))

    # 2) Add nodes at the welded centroids.
    for i, c in enumerate(centres):
        net.add_node((c[0] / c[2], c[1] / c[2]), node_id=i)

    # 3) Add one Edge per spine, mapping every authored knob.
    seen: set = set()
    for (a, b, shape, road) in specs:
        key = tuple(sorted((a, b)))
        if key in seen:
            continue                                   # roadnet allows one section per node pair
        seen.add(key)

        lc = max(1, int(road.get("lane_count", 1)))
        two_way = bool(road.get("two_way", True))
        sw_fwd, sw_rev = _sidewalk_sides(road)
        median_on = bool(road.get("median", False))

        net.add_edge(
            a, b,
            lanes_fwd=lc,
            lanes_rev=lc if two_way else 1,            # roadnet needs >=1 per side; one-way -> rev=1
            sidewalk_fwd=sw_fwd,
            sidewalk_rev=sw_rev,
            lane_width=float(road.get("lane_width", DEFAULT_LANE_WIDTH)),
            sidewalk_width=float(road.get("sidewalk_width", DEFAULT_SIDEWALK_WIDTH)),
            curb_width=float(road.get("curb_width", 0.3)) if road.get("curb", True) else 0.0,
            median_width=float(road.get("median_width", 0.0)) if median_on else 0.0,
            divided=median_on,
            alley=bool(road.get("alley", False)),
            speed_limit=float(road.get("speed_limit", 15.0)),
            shape=shape,
            intersection_type=(int(road.get("isect_start", ISECT_CONTINUE)),
                               int(road.get("isect_end", ISECT_CONTINUE))),
        )

    return net

"""
MM2 .bai (CAI1) -> roadnet RoadNetwork. Phase-2 AI foundation: extract SF's real road graph (379
roads / 214 intersections) and build a roadnet network that aligns with the imported MM2 geometry,
so roadnet can stage a real SF AI map (replacing the 2-node `min_ai` stub).

Validated offline (tools/bai_parser.py + tools/bai_to_roadnet.py): the network compiles with
RoadNetworkCompiler (375 edges, 0 validate errors) and its node bounds match the geometry's road
bounds. NOT yet the default AI source - roadnet AI is FLAT while SF is hilly, so deployed AI cars
would sit at the wrong height on slopes (needs per-vertex-Y rails, a known hard problem). Kept here
ready to wire + test.

Format: Dummiesman/angel-file-formats Midtown Madness 2/BAI.md. Parsed sequentially (RoadData is
variable-length).
"""
import math
import collections
from typing import List, NamedTuple

from src.io.binary import read_unpack, read_vectors, read_binary_name
from src.constants.file_formats import Magic
from src.game.races.constants_2 import IntersectionType
from src.game.mapgen.roadnet import RoadNetwork

FLOAT_BYTES = 4
VECTOR_BYTES = 12           # 3 x f32
ROAD_DATA_PAD_BYTES = 40    # fixed struct between lanesDistances and the lane splines
ROAD_END_BYTES = 14         # u32 intersection, 3 x u16, u32 --- none of it is needed by parse_bai


class RoadFlag:
    """.bai road flag bits, mirrored into the emitted .road fields of the same name."""
    DIVIDED = 0x1
    ALLEY = 0x2


TERRAIN_GRID = 40.0         # metres per cell in the road-height lookup
TERRAIN_MAX_RINGS = 9

MIN_LANE_WIDTH = 2.5
CURVE_TOLERANCE = 3.0       # metres of deviation before a road counts as curved / graded


class Road(NamedTuple):
    id: int
    flags: int
    rooms: List[int]
    half_width: float
    base_speed: float
    lanes_right: int; lanes_left: int; centerline: List[tuple]
    # CARRIAGEWAY half-width per side (centreline -> outer edge of the last CAR lane, i.e. the
    # kerb / sidewalkInner). EXCLUDES the sidewalk strip, unlike `half_width` which reaches the
    # sidewalk OUTER edge. Used to size AI lane_width so rails stop at the kerb, not on the sidewalk.
    carriage_hw_right: float = 0.0; carriage_hw_left: float = 0.0


class Intersection(NamedTuple):
    id: int
    room: int
    center: tuple
    roads: List[int]


def _read_magic(f) -> None:
    """Read + validate the 4-byte CAI1 magic, leaving the cursor at the first record."""
    magic = read_binary_name(f, len(Magic.MM2_AI))
    if magic != Magic.MM2_AI:
        raise ValueError(f"not a CAI1 bai (magic={magic!r})")


def _read_road_data(f, n_sections):
    """Read one SIDE of a road. Returns (n_lanes, sidewalk_width)."""
    n_lanes, n_trams, n_trains, n_side_lanes = read_unpack(f, "<4H")
    read_unpack(f, "<H")                        # nDividers --- unused
    n_lane_slots = n_lanes + n_side_lanes

    # distance[n_lane_slots] and lanesDistances[n_lane_slots][n_sections] are ARC-LENGTH spline data
    # (cumulative distance along each lane spline, values reach >100 m), NOT lateral lane offsets, so
    # they CANNOT size the carriageway. We measure the sidewalk strip from its two boundary splines.
    # Everything up to the sidewalk splines is skipped outright: this parser only needs the two
    # sidewalk boundaries, so materialising the lane / tram / train splines would be pure waste.
    f.seek(FLOAT_BYTES * n_lane_slots, 1)                          # distance
    f.seek(FLOAT_BYTES * n_lane_slots * n_sections, 1)             # lanesDistances
    f.seek(ROAD_DATA_PAD_BYTES, 1)
    f.seek(VECTOR_BYTES * n_lane_slots * n_sections, 1)            # lane splines
    f.seek(VECTOR_BYTES * n_trams * n_sections, 1)                 # tram splines
    f.seek(VECTOR_BYTES * n_trains * n_sections, 1)                # train splines

    sidewalk_inner = read_vectors(f, n_sections)   # the kerb (carriageway / sidewalk boundary)
    sidewalk_outer = read_vectors(f, n_sections)   # the road's outer edge (== the half_width line)

    # Sidewalk strip width = lateral gap between the two sidewalk splines (XZ), averaged over the
    # sections. half_width reaches sidewalkOuter, so carriageway half-width = half_width - this.
    if sidewalk_inner and sidewalk_outer:
        sidewalk_width = sum(math.hypot(inner[0] - outer[0], inner[2] - outer[2])
                             for inner, outer in zip(sidewalk_inner, sidewalk_outer)) / len(sidewalk_inner)
    else:
        sidewalk_width = 0.0

    return n_lanes, sidewalk_width


def _skip_road_end(f):
    """Skip one road-end record (intersection link + 2 boundary verts); nothing here is needed."""
    f.seek(ROAD_END_BYTES + 2 * VECTOR_BYTES, 1)


def _read_intersections(f, count):
    """Read the intersection table that follows the road table."""
    intersections = []

    for _ in range(count):
        intersection_id, room = read_unpack(f, "<2H")
        center = read_vectors(f, 1)[0]
        n_linked_roads, = read_unpack(f, "<H")
        linked = list(read_unpack(f, f"<{n_linked_roads}I"))
        intersections.append(Intersection(intersection_id, room, center, linked))

    return intersections


def parse_bai(path: str):
    """Parse a CAI1 .bai into (roads, intersections). Geometry only, no AI state."""
    with open(path, "rb") as f:
        _read_magic(f)
        n_intersections, n_roads = read_unpack(f, "<2H")

        roads = []
        for _ in range(n_roads):
            road_id, n_sections, flags, n_rooms = read_unpack(f, "<4H")
            rooms = list(read_unpack(f, f"<{n_rooms}H"))

            half_width, block_size = read_unpack(f, "<2f")
            lanes_right, sidewalk_right = _read_road_data(f, n_sections)
            lanes_left, sidewalk_left = _read_road_data(f, n_sections)

            f.seek(FLOAT_BYTES * n_sections, 1)     # per-section distances along the centreline
            origin = read_vectors(f, n_sections)
            f.seek(VECTOR_BYTES * n_sections * 4, 1)   # centre / left / right / normal --- unused
            _skip_road_end(f)
            _skip_road_end(f)

            # Carriageway half-width per side = full half_width minus that side's sidewalk strip.
            carriageway_right = max(0.0, half_width - sidewalk_right)
            carriageway_left = max(0.0, half_width - sidewalk_left)
            roads.append(Road(road_id, flags, rooms, half_width, block_size, lanes_right, lanes_left,
                              origin, carriageway_right, carriageway_left))

        intersections = _read_intersections(f, n_intersections)

    return roads, intersections


# ───────────────────────────────────────────────────────────────────────────────
# DIRECT-AI parser (opt-in alternative to build_network's lossy roadnet path).
#
# parse_bai_full() reads the same bytes as parse_bai() but keeps what the roadnet path
# discards: per-lane/sidewalk 3D splines with real hill Y, per-side lane counts, and each
# RoadEnd's vehicleRule + intersection id + traffic-light origin.
#
# Byte layout (verified empirically against sf.bai = 379 roads / 214 intersections):
#   RoadData (per side, "right" then "left"):
#     u16 nLanes, nTrams, nTrains, nSidewalks, pad
#     f32 distance[n_lane_slots]            (n_lane_slots = nLanes + nSidewalks)
#     f32 laneDistances[n_lane_slots*ns]
#     40 bytes (fixed struct)
#     Vec3 laneVerts[n_lane_slots*ns]       LANE-MAJOR: cols 0..nLanes-1 = car lanes, rest = sw-lane
#     Vec3 tramVerts[nTrams*ns], trainVerts[nTrains*ns]
#     Vec3 sidewalkInner[ns], sidewalkOuter[ns]
#   RoadEnd (x2, end-of-road then start-of-road):
#     u32 intersectionId, u16 x3, u32 vehicleRule, Vec3 trafficLightOrigin[2]
# ───────────────────────────────────────────────────────────────────────────────

class RoadSide(NamedTuple):
    n_lanes: int                 # car lanes this side (0 => this direction is a one-way wall)
    lanes: List[List[tuple]]     # [n_lanes][ns] real 3D lane splines (hills preserved)
    sidewalk_outer: List[tuple]  # [ns] outer curb edge
    sidewalk_inner: List[tuple]  # [ns] inner curb edge (carriageway boundary)


class RoadFull(NamedTuple):
    id: int; ns: int; flags: int
    right: RoadSide              # -> .road dir0 (NumLanes[0])
    left: RoadSide               # -> .road dir1 (NumLanes[1]); emitter REVERSES its sections
    origin: List[tuple]          # [ns] centreline (fallback)
    start_int: int; end_int: int             # intersection ids at section 0 / section ns-1
    start_center: tuple; end_center: tuple   # their 3D centres (pinch targets)
    vrule_start: int; vrule_end: int         # vehicleRule -> IntersectionType (0..3)
    tl_start: List[tuple]; tl_end: List[tuple]   # traffic-light origins (2 verts each)


def _read_road_data_full(f, n_sections):
    """Like _read_road_data but RETURNS the captured lane + sidewalk splines (RoadSide)."""
    n_lanes, n_trams, n_trains, n_side_lanes = read_unpack(f, "<4H")
    read_unpack(f, "<H")                        # nDividers --- unused
    n_lane_slots = n_lanes + n_side_lanes

    f.seek(FLOAT_BYTES * n_lane_slots, 1)                          # distance
    f.seek(FLOAT_BYTES * n_lane_slots * n_sections, 1)             # lanesDistances
    f.seek(ROAD_DATA_PAD_BYTES, 1)

    lane_vertices = read_vectors(f, n_lane_slots * n_sections)     # the direct path KEEPS these
    f.seek(VECTOR_BYTES * n_trams * n_sections, 1)                 # tram splines
    f.seek(VECTOR_BYTES * n_trains * n_sections, 1)                # train splines
    sidewalk_inner = read_vectors(f, n_sections)
    sidewalk_outer = read_vectors(f, n_sections)

    # Lane-major: the first n_lanes columns of lane_vertices are the real car-lane splines.
    lanes = [lane_vertices[lane * n_sections:(lane + 1) * n_sections] for lane in range(n_lanes)]

    return RoadSide(n_lanes, lanes, sidewalk_outer, sidewalk_inner)


def _read_road_end_full(f):
    """Returns (intersection_id, vehicle_rule, [traffic_light_origin x2])."""
    intersection_id, = read_unpack(f, "<I")
    f.seek(3 * 2, 1)                            # unused u16 triple
    vehicle_rule, = read_unpack(f, "<I")
    traffic_light = read_vectors(f, 2)

    return intersection_id, vehicle_rule, traffic_light


SUPPORTED_INTERSECTION_TYPES = (IntersectionType.STOP, IntersectionType.STOP_LIGHT,
                                IntersectionType.CONTINUE)


def _supported_intersection_rule(rule: int) -> int:
    """Map MM2's vehicleRule onto a rule the MM1 engine actually implements.

    MM2's vehicleRule and MM1's IntersectionType share the same enum, so the value passes straight
    through --- except YIELD, which MM1 does not implement: aiGoalRandomDrive returns 0 and spams
    "Yield - Unsuported..." every frame while the ambient car never proceeds. Remap Yield, and any
    0xCDCDCDCD garbage from an uninitialised road end, to CONTINUE.
    """
    if rule in SUPPORTED_INTERSECTION_TYPES:
        return rule

    return IntersectionType.CONTINUE


def _read_road_records_full(f, n_roads):
    """Read every road record, keeping the lane/sidewalk splines and both road ends."""
    records = []

    for _ in range(n_roads):
        road_id, n_sections, flags, n_rooms = read_unpack(f, "<4H")
        f.seek(2 * n_rooms, 1)                  # rooms --- not needed by the direct path
        f.seek(2 * FLOAT_BYTES, 1)              # half_width, base_speed --- not needed here

        right = _read_road_data_full(f, n_sections)
        left = _read_road_data_full(f, n_sections)

        f.seek(FLOAT_BYTES * n_sections, 1)     # per-section distances along the centreline
        origin = read_vectors(f, n_sections)
        f.seek(VECTOR_BYTES * n_sections * 4, 1)   # centre / left / right / normal --- unused

        road_end_start = _read_road_end_full(f)
        road_end_end = _read_road_end_full(f)
        records.append((road_id, n_sections, flags, right, left, origin,
                        road_end_start, road_end_end))

    return records


def _resolve_road_ends(records, intersections):
    """Attach each road to its start/end intersection and sanitise the two vehicle rules.

    The intersection is chosen as the MEMBER intersection nearest each centreline end, which is
    robust to the RoadEnd field order and to the 0xCDCDCDCD-uninitialised ends on loop roads.
    """
    centers = {intersection.id: intersection.center for intersection in intersections}
    members = collections.defaultdict(list)
    for intersection in intersections:
        for road_id in intersection.roads:
            members[road_id].append(intersection.id)

    roads = []
    for road_id, n_sections, flags, right, left, origin, end_a, end_b in records:
        candidates = members.get(road_id, [])
        if not candidates:
            continue

        def nearest(point):
            return min(candidates, key=lambda i: (centers[i][0] - point[0]) ** 2
                                                 + (centers[i][2] - point[2]) ** 2)

        start_id = nearest(origin[0])
        end_id = nearest(origin[-1])

        # Match each RoadEnd's vehicleRule / traffic-light origin to its intersection by stored id.
        rules = {end_a[0]: end_a[1], end_b[0]: end_b[1]}
        traffic_lights = {end_a[0]: end_a[2], end_b[0]: end_b[2]}
        no_light = [(0.0, 0.0, 0.0)] * 2

        roads.append(RoadFull(
            road_id, n_sections, flags, right, left, origin,
            start_id, end_id, centers[start_id], centers[end_id],
            _supported_intersection_rule(rules.get(start_id, IntersectionType.CONTINUE)),
            _supported_intersection_rule(rules.get(end_id, IntersectionType.CONTINUE)),
            traffic_lights.get(start_id, no_light), traffic_lights.get(end_id, no_light)))

    return roads


def parse_bai_full(path: str):
    """Full direct-AI parse. Returns (roads: List[RoadFull], intersections: List[Intersection])."""
    with open(path, "rb") as f:
        _read_magic(f)
        n_intersections, n_roads = read_unpack(f, "<2H")
        records = _read_road_records_full(f, n_roads)
        intersections = _read_intersections(f, n_intersections)

    return _resolve_road_ends(records, intersections), intersections


def _is_curved(road, tolerance: float = CURVE_TOLERANCE) -> bool:
    """True when the centreline bows away from the straight start->end line by more than tolerance."""
    centerline = road.centerline
    if len(centerline) <= 2:
        return False

    start_x, start_z = centerline[0][0], centerline[0][2]
    end_x, end_z = centerline[-1][0], centerline[-1][2]
    span_x, span_z = end_x - start_x, end_z - start_z
    length = math.hypot(span_x, span_z) or 1.0
    normal_x, normal_z = -span_z / length, span_x / length

    return max(abs((point[0] - start_x) * normal_x + (point[2] - start_z) * normal_z)
               for point in centerline[1:-1]) > tolerance


def _is_graded(road, tolerance: float = CURVE_TOLERANCE) -> bool:
    """True when the centreline climbs or falls by more than tolerance."""
    heights = [point[1] for point in road.centerline]

    return (max(heights) - min(heights)) > tolerance


def _build_terrain_lookup(roads):
    """Return terrain(x, z) -> the nearest BAI road-point Y.

    Deliberately NEAREST-POINT, not a cell average: averaging across a slope floats props and AI
    rails above the road on SF's hills. Points are bucketed into a coarse grid and the lookup walks
    outward ring by ring, stopping one ring past the first that produced a hit.
    """
    cells = collections.defaultdict(list)
    for road in roads:
        for point in road.centerline:
            cells[(int(point[0] // TERRAIN_GRID), int(point[2] // TERRAIN_GRID))].append(
                (point[0], point[2], point[1]))

    def terrain(x, z):
        grid_x, grid_z = int(x // TERRAIN_GRID), int(z // TERRAIN_GRID)
        best_distance = None
        best_y = 0.0
        first_hit_ring = None

        for ring in range(TERRAIN_MAX_RINGS):
            if first_hit_ring is not None and ring > first_hit_ring + 1:
                break

            for dx in range(-ring, ring + 1):
                for dz in range(-ring, ring + 1):
                    if ring and max(abs(dx), abs(dz)) != ring:
                        continue          # the interior of this ring was covered by an earlier pass

                    points = cells.get((grid_x + dx, grid_z + dz))
                    if not points:
                        continue
                    if first_hit_ring is None:
                        first_hit_ring = ring

                    for point_x, point_z, point_y in points:
                        distance = (point_x - x) ** 2 + (point_z - z) ** 2
                        if best_distance is None or distance < best_distance:
                            best_distance = distance
                            best_y = point_y

        return best_y

    return terrain


def _add_road_edge(net, road, node_a, node_b):
    """Add one roadnet edge for a BAI road. Raises if roadnet rejects the geometry."""
    centerline = road.centerline
    shape = ([(float(point[0]), float(point[2])) for point in centerline[1:-1]]
             if len(centerline) > 2 else [])

    # roadnet is BIDIRECTIONAL (add_edge rejects a 0-lane direction), so MM2 one-way roads become
    # 2-way here. The AI U-turns are this limitation, and are separate roadnet work.
    lanes_forward = max(1, road.lanes_right)
    lanes_reverse = max(1, road.lanes_left)

    # Size the AI carriageway to the BAI's CAR-LANE span, NOT the full half_width (which reaches the
    # sidewalk OUTER edge). Using half_width put the outer rail ON the sidewalk, so traffic drove
    # onto the pedestrian kerb. carriage_hw runs centreline -> last car-lane edge (the kerb), so
    # max(fwd, rev) lanes land at the kerb and roadnet adds ITS sidewalk outside that. Fall back to
    # half_width only when the BAI side carried no lane-edge distance.
    carriageway_half_width = max(road.carriage_hw_right, road.carriage_hw_left) or road.half_width
    lane_width = max(MIN_LANE_WIDTH, carriageway_half_width / max(lanes_forward, lanes_reverse))

    net.add_edge(node_a, node_b, lanes_fwd = lanes_forward, lanes_rev = lanes_reverse,
                 lane_width = lane_width, shape = shape,
                 divided = bool(road.flags & RoadFlag.DIVIDED),
                 alley = bool(road.flags & RoadFlag.ALLEY))


def _prune_isolated_nodes(net) -> int:
    """Drop nodes left with no edges (roadnet rejects them). Returns how many went."""
    connected = set()
    for edge in net.edges:
        connected.add(edge.a)
        connected.add(edge.b)

    pruned = 0
    for node_id in list(net.nodes):
        if node_id not in connected:
            del net.nodes[node_id]
            pruned += 1

    return pruned


def build_network(bai_path: str, name: str = "MM2SF_AI",
                  terrain_follow: bool = True, skip_curved_grade: bool = True):
    """Parse a .bai and return (RoadNetwork, stats).

    Edges connect the two intersections that reference each road; one-way/divided roads are made
    2-way (>=1 lane each) and duplicate edges between the same node pair are dropped.

    terrain_follow      set net.terrain from the BAI road heights so AI rails follow SF's hills;
                        flat rails let cars fall through the hilly geometry.
    skip_curved_grade   drop roads that are BOTH curved AND graded. Those NaN-crash the engine's
                        wheel-AI; SF's grid streets are straight-graded and survive, so only the
                        winding roads are excluded.
    """
    roads, intersections = parse_bai(bai_path)

    road_ends = collections.defaultdict(list)
    for intersection in intersections:
        for road_id in intersection.roads:
            road_ends[road_id].append(intersection.id)

    net = RoadNetwork(name = name)
    node_for_intersection = {
        intersection.id: net.add_node((float(intersection.center[0]),
                                       float(intersection.center[2]))).id
        for intersection in intersections
    }

    if terrain_follow:
        net.terrain = _build_terrain_lookup(roads)

    edges = skipped = curved_and_graded = 0
    seen_node_pairs = set()

    for road in roads:
        ends = road_ends.get(road.id, [])
        if len(ends) != 2 or ends[0] == ends[1]:
            skipped += 1
            continue

        if skip_curved_grade and _is_curved(road) and _is_graded(road):
            curved_and_graded += 1
            continue

        node_a, node_b = node_for_intersection[ends[0]], node_for_intersection[ends[1]]
        node_pair = (min(node_a, node_b), max(node_a, node_b))
        if node_pair in seen_node_pairs:
            skipped += 1
            continue

        try:
            _add_road_edge(net, road, node_a, node_b)
        except Exception:
            skipped += 1
            continue

        seen_node_pairs.add(node_pair)
        edges += 1

    pruned = _prune_isolated_nodes(net)

    return net, {"roads": len(roads), "intersections": len(intersections), "edges": edges,
                 "skipped": skipped, "curved_graded_dropped": curved_and_graded,
                 "isolated_pruned": pruned}

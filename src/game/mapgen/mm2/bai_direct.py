"""
DIRECT MM2 BAI -> MM1/Open1560 AI converter (OPT-IN alternative to the lossy roadnet path).

The roadnet path (bai.build_network -> RoadNetworkCompiler -> stage_roadnet_ai) rebuilds a
FLAT, 2-way, straight-edge approximation of the road graph: it drops the BAI's per-vertex Y
(bai.py terrain hack), forces every one-way road to 2-way, and drops curved+graded roads.

This module instead writes the BAI's REAL 3D lane/sidewalk splines straight into .road files:
  * real per-vertex Y  -> rails follow SF's hills instead of flying across levels
  * one-way preserved  -> a side with 0 BAI car lanes => that direction is Blocked (default) or
                          NumLanes=0 (one_way_mode="true", needs a patched engine) -- see _columns
  * curved + graded preserved -> the spline verts ARE the curve/grade, nothing dropped
  * no mid-road spurious intersections -> the engine regenerates intersections purely from
    pinched road ENDPOINTS (we write NO .int files; see "endpoint pinching" below).

Default stays OFF (the hybrid roadnet path is the shipped default) --- enabled via the MM2
opt `bai_direct: True` (see MAP_EDITOR_ALPHA_v1.py + src/USER/settings/main.py).

.road field set + order is exactly what Open1560's text parser accepts
(mmcityinfo/roadsect.cpp) --- emit NOTHING past Alley.
"""
import math
from typing import List
from pathlib import Path

from src.constants.file_formats import FileType
from src.game.mapgen.mm2.bai import parse_bai_full, RoadFull, RoadFlag
from src.game.races.constants_2 import IntersectionType
from src.game.mapgen.roadnet.emit import RoadFileWriter          # reuse the exact .road formatter
from src.game.mapgen.roadnet.build_city import staging_dir, map_file_text
from src.USER.settings.main import MAP_FILENAME

COINCIDENT_EPSILON = 1.0e-3
NUDGE_DISTANCE = 0.01
MAX_LANES = 4              # the engine caps NumLanes at 4 (aiPath.cpp:304)
SIDEWALKS_PER_SIDE = 2     # outer + inner curb spline


def _distance3(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _pinch(column: List[tuple], start: tuple, end: tuple) -> List[tuple]:
    """Overwrite a column's two ENDPOINTS with the intersection centres, so adjacent roads share the
    junction point and the engine's AddIntersection dedupes them into one node. Coincident
    consecutive verts are then nudged apart, because a zero-length segment NaNs the engine's
    normalize()."""
    points = [(float(v[0]), float(v[1]), float(v[2])) for v in column]
    points[0] = (float(start[0]), float(start[1]), float(start[2]))
    points[-1] = (float(end[0]), float(end[1]), float(end[2]))

    for i in range(1, len(points)):
        if _distance3(points[i], points[i - 1]) >= COINCIDENT_EPSILON:
            continue

        # Push the later vert a hair along the road so no segment is zero-length.
        reference = points[i + 1] if i + 1 < len(points) else points[i - 1]
        delta_x = reference[0] - points[i - 1][0]
        delta_z = reference[2] - points[i - 1][2]
        length = math.hypot(delta_x, delta_z) or 1.0
        points[i] = (points[i][0] + delta_x / length * NUDGE_DISTANCE,
                     points[i][1],
                     points[i][2] + delta_z / length * NUDGE_DISTANCE)

    return points


ONE_WAY_MODES = ("blocked", "true", "phantom")


def _resolve_one_way_mode(one_way_mode, true_one_way) -> str:
    """`true_one_way` is the legacy bool alias: True -> "true", False -> "phantom"."""
    if true_one_way is not None:
        return "true" if true_one_way else "phantom"
    if one_way_mode not in ONE_WAY_MODES:
        raise ValueError(f"one_way_mode must be one of {ONE_WAY_MODES}, got {one_way_mode!r}")
    return one_way_mode


def _columns(road: RoadFull, one_way_mode: str = "blocked"):
    """Assemble the .road Vertexs[] columns in engine order
    [dir0 car lanes][dir1 car lanes][dir0 sidewalks][dir1 sidewalks], each pinched.
    Returns (cols, nl0, nl1, sw0, sw1, blocked0, blocked1).
    """
    # SIDE / DIRECTION MAPPING, measured on all 4 BAIs + retail CHICAGO .road files. MM2 stores every
    # lane spline in DRIVING order: the BAI's first block (bai.py calls it `right`) holds the lanes
    # travelling END->START, the second (`left`) holds START->END. Both blocks' sidewalks run
    # START->END. MM1 dir0 travels start->end and dir1 the reverse, and lane 0 is innermost in both
    # formats, so:
    #     dir0 = `left` lanes as stored   + `left` sidewalks as stored
    #     dir1 = `right` lanes as stored  + `right` sidewalks REVERSED
    # Getting this backwards zigzags every lane on a road with 3+ sections and runs dir1 on the
    # oncoming side --- the "sudden U-turns" and "wrong way" ambient behaviour.
    #
    # ONE-WAY HANDLING (`one_way_mode`); a block with 0 car lanes is a one-way road:
    #   "blocked" (default) --- the empty direction gets one phantom lane on the road centreline and
    #       is flagged Blocked[dir]=1. The ambient spawner and ChooseNext*Link skip IsBlocked paths,
    #       so ambients only drive the legal way. Opponents (aiGoalFollowWayPts) ignore IsBlocked,
    #       and MM2's own .opp routes go against the arrow on roughly half their one-way hops
    #       (577 legal vs 556 illegal across SF's 288 .opp files), so their routes stay 1:1.
    #       Works on a stock engine.
    #   "true" --- NumLanes[dir]=0, no phantom. Needs an Open1560 build with the one-way patch: the
    #       unpatched engine reads road end points from column 0, which on a NumLanes[0]=0 road is
    #       the reversed dir-1 lane, giving swapped intersections and a bad rail hand-off. Routes
    #       that go against a one-way are re-routed by opp_routes.
    #   "phantom" --- the legacy output: phantom lane, NOT blocked, every road 2-way.
    start, end = road.start_center, road.end_center

    forward_lanes = road.left.lanes                   # start->end as stored
    backward_lanes = road.right.lanes                 # end->start as stored
    blocked_dir0 = blocked_dir1 = 0

    if one_way_mode != "true":
        if not road.left.n_lanes:
            forward_lanes = [road.origin]
            blocked_dir0 = 1 if one_way_mode == "blocked" else 0
        if not road.right.n_lanes:
            backward_lanes = [list(reversed(road.origin))]
            blocked_dir1 = 1 if one_way_mode == "blocked" else 0

    lanes_dir0 = min(MAX_LANES, len(forward_lanes))
    lanes_dir1 = min(MAX_LANES, len(backward_lanes))

    # A sidewalk pair exists when both curb splines are present (always true for the SF/London BAI).
    # Emitting the pair also keeps the cop-spawn index in bounds --- NumSidewalks=0 reads OOB.
    has_sidewalks_dir0 = bool(road.left.sidewalk_outer and road.left.sidewalk_inner)
    has_sidewalks_dir1 = bool(road.right.sidewalk_outer and road.right.sidewalk_inner)
    sidewalks_dir0 = SIDEWALKS_PER_SIDE if has_sidewalks_dir0 else 0
    sidewalks_dir1 = SIDEWALKS_PER_SIDE if has_sidewalks_dir1 else 0

    columns: List[List[tuple]] = []

    for lane in forward_lanes[:lanes_dir0]:           # dir0 car lanes (start->end)
        columns.append(_pinch(lane, start, end))

    for lane in backward_lanes[:lanes_dir1]:          # dir1 car lanes (end->start, as stored)
        columns.append(_pinch(lane, end, start))

    if sidewalks_dir0:                                # dir0 sidewalks: outer then inner
        columns.append(_pinch(road.left.sidewalk_outer, start, end))
        columns.append(_pinch(road.left.sidewalk_inner, start, end))

    if sidewalks_dir1:                                # dir1 sidewalks, reversed to run end->start
        columns.append(_pinch(list(reversed(road.right.sidewalk_outer)), end, start))
        columns.append(_pinch(list(reversed(road.right.sidewalk_inner)), end, start))

    return columns, lanes_dir0, lanes_dir1, sidewalks_dir0, sidewalks_dir1, blocked_dir0, blocked_dir1


def emit_road_direct(road: RoadFull, one_way_mode: str = "blocked") -> str:
    """One mmRoadSect (.road) carrying the BAI's true 3D geometry."""
    n_vertices = road.ns
    (columns, lanes_dir0, lanes_dir1, sidewalks_dir0, sidewalks_dir1,
     blocked_dir0, blocked_dir1) = _columns(road, one_way_mode)

    vertices: List[tuple] = []
    for column in columns:
        vertices.extend(column)

    total_vertices = n_vertices * (lanes_dir0 + lanes_dir1 + sidewalks_dir0 + sidewalks_dir1)
    if len(vertices) != total_vertices:
        raise ValueError(f"road {road.id}: emitted {len(vertices)} verts, header declares "
                         f"{total_vertices} --- the engine would read past the array")

    end_lights, start_lights = road.tl_end, road.tl_start
    rule_start, rule_end = road.vrule_start, road.vrule_end

    # A phantom (Blocked / legacy) direction carries no MM2 traffic: give it CONTINUE and no light, or
    # the engine would add a traffic-light instance for it (at the BAI's zeroed origin, i.e. the world
    # origin) and hand it a green phase nobody uses. dir1 arrives at the START (IntersectionType[0],
    # StopLightPos[0..1]); dir0 at the END (IntersectionType[1], StopLightPos[2..3]).
    no_light = [(0.0, 0.0, 0.0)] * 2
    if blocked_dir1 or (one_way_mode == "phantom" and not road.right.n_lanes):
        rule_start, start_lights = IntersectionType.CONTINUE, no_light
    if blocked_dir0 or (one_way_mode == "phantom" and not road.left.n_lanes):
        rule_end, end_lights = IntersectionType.CONTINUE, no_light

    writer = RoadFileWriter()
    writer.begin("mmRoadSect")
    writer.f_int("NumVertexs", n_vertices)
    writer.f_int("NumLanes[0]", lanes_dir0)
    writer.f_int("NumLanes[1]", lanes_dir1)
    writer.f_int("NumSidewalks[0]", sidewalks_dir0)
    writer.f_int("NumSidewalks[1]", sidewalks_dir1)
    writer.f_int("TotalVertexs", total_vertices)
    writer.f_vec3_list("Vertexs", vertices)
    writer.f_vec3_list("Normals", [(0.0, 1.0, 0.0)] * n_vertices)  # UP; engine re-derives the frames

    writer.f_int("IntersectionType[0]", rule_start)
    writer.f_int("IntersectionType[1]", rule_end)
    # The engine reads StopLightPos[2..3] for dir0 (which arrives at the END) and [0..1] for dir1
    # (arrives at the START) --- aiPath::AddPathVerts -> GetStopLightPos(isStartIntersection), and
    # retail CHICAGO Street0 has its END light in [2..3]. Swapping them puts every engine-placed
    # traffic light at the far end of its road.
    writer.f_vec3("StopLightPos[0]", start_lights[0]); writer.f_vec3("StopLightPos[1]", start_lights[1])
    writer.f_vec3("StopLightPos[2]", end_lights[0]); writer.f_vec3("StopLightPos[3]", end_lights[1])

    writer.f_int("Blocked[0]", blocked_dir0); writer.f_int("Blocked[1]", blocked_dir1)   # one-way: see _columns
    writer.f_int("PedBlocked[0]", 0); writer.f_int("PedBlocked[1]", 0)
    writer.f_str_list("StopLightName", ["tplttrafc", "tplttrafc"])
    writer.f_int("Divided", 1 if (road.flags & RoadFlag.DIVIDED) else 0)
    writer.f_int("Alley", 1 if (road.flags & RoadFlag.ALLEY) else 0)
    writer.end()
    return writer.text()


def stage_bai_direct(bai_path: str, map_filename: str = None, one_way_mode: str = "blocked",
                     true_one_way: bool = None) -> dict:
    """Parse a .bai and STAGE Street{id}.road + {map}.map into the roadnet staging folder, so
    the build's consume_staged_ai() copies them into DevCityMap after the mid-build wipe
    (exactly where stage_roadnet_ai writes). DROP-IN replacement for the roadnet AI stage."""
    # one_way_mode: "blocked" (default) flags the phantom reverse lane Blocked, so ambients obey the
    # arrow while opponents may still follow MM2's against-the-arrow routes; "true" writes
    # NumLanes[dir]=0 and needs the one-way patch; "phantom" is the legacy 2-way output. See
    # _columns. `true_one_way` is the bool alias: True -> "true", False -> "phantom".
    one_way_mode = _resolve_one_way_mode(one_way_mode, true_one_way)
    if map_filename is None:
        map_filename = MAP_FILENAME

    roads, intersections = parse_bai_full(bai_path)

    # Clear the staging folder so a re-run cannot leave last build's Street*.road behind.
    stage_dir = Path(staging_dir(map_filename))
    if stage_dir.is_dir():
        for stale in stage_dir.iterdir():
            stale.unlink()
    stage_dir.mkdir(parents=True, exist_ok=True)

    street_names: List[str] = []
    written = skipped_loop = skipped_nolane = failed = 0

    for road in roads:
        # Self-loop (both ends dedupe to ONE intersection) => degenerate road, skip (the roadnet
        # path skipped these too); and a road with NO car lanes either side has nothing to drive.
        if road.start_int == road.end_int:
            skipped_loop += 1; continue
        if road.right.n_lanes == 0 and road.left.n_lanes == 0:
            skipped_nolane += 1; continue

        try:
            text = emit_road_direct(road, one_way_mode)
        except Exception:
            failed += 1; continue

        name = f"Street{road.id}"
        (stage_dir / f"{name}{FileType.AI_STREET}").write_text(text)
        street_names.append(name)
        written += 1

    (stage_dir / f"{map_filename}{FileType.AI_MAP}").write_text(map_file_text(map_filename, street_names))

    return {"roads": len(roads), "intersections": len(intersections), "written": written,
            "skipped_loop": skipped_loop, "skipped_nolane": skipped_nolane,
            "failed": failed, "dir": str(stage_dir), "one_way_mode": one_way_mode,
            "one_way": sum(1 for r in roads if r.right.n_lanes == 0 or r.left.n_lanes == 0)}




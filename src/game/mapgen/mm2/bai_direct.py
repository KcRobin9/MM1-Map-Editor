"""
DIRECT MM2 BAI -> MM1/Open1560 AI converter (OPT-IN alternative to the lossy roadnet path).

The roadnet path (bai.build_network -> RoadNetworkCompiler -> stage_roadnet_ai) rebuilds a
FLAT, 2-way, straight-edge approximation of the road graph: it drops the BAI's per-vertex Y
(bai.py terrain hack), forces every one-way road to 2-way, and drops curved+graded roads.

This module instead writes the BAI's REAL 3D lane/sidewalk splines straight into .road files:
  * real per-vertex Y  -> rails follow SF's hills instead of flying across levels
  * one-way preserved  -> a side with 0 BAI car lanes => NumLanes=0 (engine-accepted)
  * curved + graded preserved -> the spline verts ARE the curve/grade, nothing dropped
  * no mid-road spurious intersections -> the engine regenerates intersections purely from
    pinched road ENDPOINTS (we write NO .int files; see "endpoint pinching" below).

Default stays OFF (the hybrid roadnet path is the shipped default) — enabled via the MM2
opt `bai_direct: True` (see MAP_EDITOR_ALPHA_v1.py + src/USER/settings/main.py).

.road field set + order is exactly what Open1560's text parser accepts
(mmcityinfo/roadsect.cpp) — emit NOTHING past Alley.
"""
import math
from typing import List
from pathlib import Path

from src.constants.file_formats import FileType
from src.game.mapgen.mm2.bai import parse_bai_full, RoadFull, RoadSide, RoadFlag
from src.game.mapgen.roadnet.emit import RoadFileWriter          # reuse the exact .road formatter
from src.game.mapgen.roadnet.build_city import staging_dir, map_file_text, write_roam_aimap
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


def _columns(road: RoadFull):
    """Assemble the .road Vertexs[] columns in engine order
    [dir0 car lanes][dir1 car lanes][dir0 sidewalks][dir1 sidewalks], each pinched.

    dir0 = BAI "right" (sections as-is): pinch vert0=start, vertN=end.
    dir1 = BAI "left" with sections REVERSED (the opposing carriageway): after the reversal
           vert0 is the physical END and vertN the START, so pinch is start<->end swapped.
    Returns (cols, nl0, nl1, sw0, sw1).

    ONE-WAY HANDLING: a BAI side with 0 car lanes is a true one-way. BUT the MM1 engine's rail
    graph cannot route into a 0-lane direction -- aiRailSet::CalcRailPosition computes
    NextLane = NumLanes-1 = -1 and indexes LaneVertices[-vc+1] (negative) -> ACCESS_VIOLATION
    when an ambient transitions into it. (This is why the roadnet path force-converts one-ways
    to 2-way.) So we synthesize ONE phantom lane on the empty side from the road CENTRELINE
    (origin) -- a real on-road spline at the correct hill Y -- giving the engine a valid >=1-lane
    direction while still keeping the REAL geometry (hills/curves/grades) the roadnet path drops."""
    start, end = road.start_center, road.end_center

    right_lanes = road.right.lanes if road.right.n_lanes else [road.origin]
    left_lanes = road.left.lanes if road.left.n_lanes else [road.origin]
    lanes_dir0 = min(MAX_LANES, len(right_lanes))
    lanes_dir1 = min(MAX_LANES, len(left_lanes))

    # A sidewalk pair exists when both curb splines are present (always true for the SF/London BAI).
    # Emitting the pair also keeps the cop-spawn index in bounds --- NumSidewalks=0 reads OOB.
    has_sidewalks_dir0 = bool(road.right.sidewalk_outer and road.right.sidewalk_inner)
    has_sidewalks_dir1 = bool(road.left.sidewalk_outer and road.left.sidewalk_inner)
    sidewalks_dir0 = SIDEWALKS_PER_SIDE if has_sidewalks_dir0 else 0
    sidewalks_dir1 = SIDEWALKS_PER_SIDE if has_sidewalks_dir1 else 0

    columns: List[List[tuple]] = []

    for lane in right_lanes[:lanes_dir0]:             # dir0 car lanes
        columns.append(_pinch(lane, start, end))

    for lane in left_lanes[:lanes_dir1]:              # dir1 car lanes, sections reversed
        columns.append(_pinch(list(reversed(lane)), end, start))

    if sidewalks_dir0:                                # dir0 sidewalks: outer then inner
        columns.append(_pinch(road.right.sidewalk_outer, start, end))
        columns.append(_pinch(road.right.sidewalk_inner, start, end))

    if sidewalks_dir1:                                # dir1 sidewalks, reversed to match dir1
        columns.append(_pinch(list(reversed(road.left.sidewalk_outer)), end, start))
        columns.append(_pinch(list(reversed(road.left.sidewalk_inner)), end, start))

    return columns, lanes_dir0, lanes_dir1, sidewalks_dir0, sidewalks_dir1


def emit_road_direct(road: RoadFull) -> str:
    """One mmRoadSect (.road) carrying the BAI's true 3D geometry."""
    n_vertices = road.ns
    columns, lanes_dir0, lanes_dir1, sidewalks_dir0, sidewalks_dir1 = _columns(road)

    vertices: List[tuple] = []
    for column in columns:
        vertices.extend(column)

    total_vertices = n_vertices * (lanes_dir0 + lanes_dir1 + sidewalks_dir0 + sidewalks_dir1)
    if len(vertices) != total_vertices:
        raise ValueError(f"road {road.id}: emitted {len(vertices)} verts, header declares "
                         f"{total_vertices} --- the engine would read past the array")

    end_lights, start_lights = road.tl_end, road.tl_start

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

    writer.f_int("IntersectionType[0]", road.vrule_start)
    writer.f_int("IntersectionType[1]", road.vrule_end)
    writer.f_vec3("StopLightPos[0]", end_lights[0]); writer.f_vec3("StopLightPos[1]", end_lights[1])
    writer.f_vec3("StopLightPos[2]", start_lights[0]); writer.f_vec3("StopLightPos[3]", start_lights[1])

    writer.f_int("Blocked[0]", 0); writer.f_int("Blocked[1]", 0)
    writer.f_int("PedBlocked[0]", 0); writer.f_int("PedBlocked[1]", 0)
    writer.f_str_list("StopLightName", ["tplttrafc", "tplttrafc"])
    writer.f_int("Divided", 1 if (road.flags & RoadFlag.DIVIDED) else 0)
    writer.f_int("Alley", 1 if (road.flags & RoadFlag.ALLEY) else 0)
    writer.end()
    return writer.text()


def stage_bai_direct(bai_path: str, map_filename: str = None) -> dict:
    """Parse a .bai and STAGE Street{id}.road + {map}.map into the roadnet staging folder, so
    the build's consume_staged_ai() copies them into DevCityMap after the mid-build wipe
    (exactly where stage_roadnet_ai writes). DROP-IN replacement for the roadnet AI stage."""
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
            text = emit_road_direct(road)
        except Exception:
            failed += 1; continue

        name = f"Street{road.id}"
        (stage_dir / f"{name}{FileType.AI_STREET}").write_text(text)
        street_names.append(name)
        written += 1

    (stage_dir / f"{map_filename}{FileType.AI_MAP}").write_text(map_file_text(map_filename, street_names))

    return {"roads": len(roads), "intersections": len(intersections), "written": written,
            "skipped_loop": skipped_loop, "skipped_nolane": skipped_nolane,
            "failed": failed, "dir": str(stage_dir),
            "one_way": sum(1 for r in roads if r.right.n_lanes == 0 or r.left.n_lanes == 0)}




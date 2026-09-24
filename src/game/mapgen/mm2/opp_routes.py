"""
Graph-valid MM1 opponent routes from MM2 .opp files, over the DIRECT BAI road network.

Why: MM1's aiGoalFollowWayPts ctor resolves every middle .opp waypoint to an intersection and then
Quitf("ERROR: No road between intersections") unless each consecutive pair is joined by ONE road
(aiGoalFollowWayPts.cpp, DetRdSegBetweenInts). The raw MM2 .opp files are authored against MM2's BAI;
our converted network is the same BAI minus the self-loop / no-lane roads bai_direct skips, with
one-way sides that are REALLY one-way in one_way_mode "true". So a raw route can (a) snap to the
wrong junction, (b) step over a dropped road, or (c) drive a one-way backwards. This module snaps
each waypoint to our nearest intersection, checks the DIRECTED road graph, and repairs every broken
hop with the shortest path over our roads.

The graph is built from the same parse (bai.parse_bai_full) and the same skip rules as
bai_direct.stage_bai_direct, so "connected here" == "DetRdSegBetweenInts finds a path in-game":
  * dir0 (NumLanes[0]) = the BAI's `left` block, whose lanes are stored start->end: start_int -> end_int
  * dir1 (NumLanes[1]) = the BAI's `right` block, stored end->start:                 end_int -> start_int
  (see bai_direct._columns for the measurement behind that mapping)
A block with 0 lanes contributes no edge in one_way_mode "true" (the engine
builds no aiPath for it); otherwise bai_direct phantom-lanes it ("blocked"/"phantom") and opponents
may drive it, so both directions are edges.

Waypoint positions emitted for the middle rows are the BAI intersection centres EXACTLY (the same
floats bai_direct pinches the road end points to), so the engine's nearest-intersection resolve
lands on the intended junction with distance 0.
"""
import heapq
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.constants.mm2 import MM2_OPPONENT_CAR, MM2_OPPONENT_CAR_DEFAULT
from src.game.mapgen.mm2.bai import parse_bai_full, RoadFull

SNAP_WARN_DISTANCE = 25.0      # a middle waypoint further than this from any junction is not one of ours
MIN_ROUTE_ROWS = 3             # spawn + at least one junction + finish
SNAP_EXACT_DISTANCE = 1e-3     # an emitted middle row should sit ON its junction
OPPONENT_SECTION = "[Opponent]"


def mm1_model(mm2_model: str) -> str:
    return MM2_OPPONENT_CAR.get(mm2_model.lower(), MM2_OPPONENT_CAR_DEFAULT)


class RoadGraph:
    """Directed intersection graph of the roads bai_direct actually writes."""

    def __init__(self, roads: List[RoadFull], intersections, one_way_mode: str = "blocked"):
        # Only "true" leaves a 0-lane block without an aiPath; "blocked"/"phantom" still emit one,
        # so opponents can legally drive both ways there and the edge stays in the graph.
        drops_empty_side = one_way_mode == "true"
        self.centers: Dict[int, Tuple[float, float, float]] = {}
        # adjacency[a][b] = (road_id, length)
        self.adjacency: Dict[int, Dict[int, Tuple[int, float]]] = {}
        self.roads_written = 0
        self.one_way_edges = 0

        for road in roads:
            if road.start_int == road.end_int:
                continue                                  # self-loop: bai_direct skips it
            if road.right.n_lanes == 0 and road.left.n_lanes == 0:
                continue                                  # nothing to drive: skipped too
            self.roads_written += 1

            length = _polyline_length(road.origin)
            forward = road.left.n_lanes > 0 or not drops_empty_side   # left block = start->end
            backward = road.right.n_lanes > 0 or not drops_empty_side  # right block = end->start
            if forward:
                self._add_edge(road.start_int, road.end_int, road.id, length)
            if backward:
                self._add_edge(road.end_int, road.start_int, road.id, length)
            if forward != backward:
                self.one_way_edges += 1

            self.centers[road.start_int] = road.start_center
            self.centers[road.end_int] = road.end_center

        # Junctions that touch no written road do not exist in-game.
        self._ids = list(self.centers)

    def _add_edge(self, a: int, b: int, road_id: int, length: float) -> None:
        self.adjacency.setdefault(a, {})
        self.adjacency.setdefault(b, {})
        existing = self.adjacency[a].get(b)
        if existing is None or length < existing[1]:
            self.adjacency[a][b] = (road_id, length)

    def nearest(self, x: float, z: float) -> Tuple[int, float]:
        """(intersection id, XZ distance) of the junction closest to (x, z)."""
        best_id, best_d2 = -1, float("inf")
        for node in self._ids:
            center = self.centers[node]
            d2 = (center[0] - x) ** 2 + (center[2] - z) ** 2
            if d2 < best_d2:
                best_id, best_d2 = node, d2
        return best_id, math.sqrt(best_d2)

    def connected(self, a: int, b: int) -> bool:
        return b in self.adjacency.get(a, {})

    def shortest_path(self, a: int, b: int) -> Optional[List[int]]:
        """Dijkstra over road length, a -> b inclusive; None when b is unreachable from a."""
        if a == b:
            return [a]

        dist = {a: 0.0}
        prev: Dict[int, int] = {}
        heap = [(0.0, a)]

        while heap:
            d, node = heapq.heappop(heap)
            if node == b:
                break
            if d > dist.get(node, float("inf")):
                continue
            for nxt, (_, length) in self.adjacency.get(node, {}).items():
                nd = d + length
                if nd < dist.get(nxt, float("inf")):
                    dist[nxt] = nd
                    prev[nxt] = node
                    heapq.heappush(heap, (nd, nxt))
        if b not in dist:
            return None

        path = [b]
        while path[-1] != a:
            path.append(prev[path[-1]])
        return list(reversed(path))


def _polyline_length(points) -> float:
    total = 0.0
    for i in range(1, len(points)):
        total += math.dist(points[i][:3], points[i - 1][:3])
    return total


def load_graph(bai_path: str, one_way_mode: str = "blocked") -> RoadGraph:
    roads, intersections = parse_bai_full(bai_path)
    return RoadGraph(roads, intersections, one_way_mode)


def read_opp_rows(path: Path) -> List[List[float]]:
    """MM2 .opp -> [[x, y, z], ...] (header dropped). Row 0 = spawn, last = finish, rest = junctions."""
    rows = []
    for line in path.read_text(encoding = "latin-1").splitlines()[1:]:
        columns = line.split(",")
        if len(columns) < 3:
            continue
        try:
            rows.append([float(columns[0]), float(columns[1]), float(columns[2])])
        except ValueError:
            continue
    return rows


def convert_route(rows: List[List[float]], graph: RoadGraph, log = None, label: str = "") -> Optional[dict]:
    """Snap + validate + repair one route. Returns None when it cannot be made graph-valid.

    Result: {"rows": [[x,y,z],...], "ids": [junction ids], "snapped": n, "repaired": n,
             "inserted": n, "far_snaps": n}
    """
    if len(rows) < MIN_ROUTE_ROWS:
        if log:
            log(f"opp {label}: only {len(rows)} rows, skipped")
        return None

    spawn, finish = rows[0], rows[-1]

    ids: List[int] = []
    far_snaps = 0
    for x, y, z in rows[1:-1]:
        node, distance = graph.nearest(x, z)
        if node < 0:
            return None
        if distance > SNAP_WARN_DISTANCE:
            # No junction of OURS near this MM2 waypoint (a junction on a road bai_direct skipped, or
            # a mid-road point): snapping it would bend the route to a junction MM2 never visited.
            # Drop it; the hop repair below bridges its neighbours with the shortest road path.
            far_snaps += 1
            continue
        if not ids or ids[-1] != node:              # collapse consecutive duplicates
            ids.append(node)

    if not ids:
        if log:
            log(f"opp {label}: no waypoint lands near one of our junctions, opponent dropped")
        return None

    # Repair: every hop must be ONE road in the directed graph.
    repaired = inserted = 0
    route: List[int] = [ids[0]]
    for nxt in ids[1:]:
        cur = route[-1]
        if graph.connected(cur, nxt):
            route.append(nxt)
            continue
        path = graph.shortest_path(cur, nxt)
        if path is None:
            if log:
                log(f"opp {label}: junction {cur} -> {nxt} unreachable, opponent dropped")
            return None
        repaired += 1
        inserted += len(path) - 2
        route.extend(path[1:])

    # The engine's Init() needs a road between junction 1 and junction 2 (Rail->NextLink).
    if len(route) < 2:
        # A single-junction route: extend one hop so the opponent has a NextLink to start on.
        outgoing = graph.adjacency.get(route[0], {})
        if not outgoing:
            if log:
                log(f"opp {label}: lone junction {route[0]} has no exit, opponent dropped")
            return None
        # Prefer the exit that points towards the finish.
        route.append(min(outgoing, key = lambda n: math.dist(graph.centers[n][::2], (finish[0], finish[2]))))

    out_rows = [spawn] + [list(graph.centers[node]) for node in route] + [finish]
    return {"rows": out_rows, "ids": route, "snapped": len(ids), "repaired": repaired,
            "inserted": inserted, "far_snaps": far_snaps}


def verify_route(rows: List[List[float]], graph: RoadGraph) -> List[str]:
    """Headless re-check of an EMITTED route the way the engine will read it: every middle row must
    resolve (nearest junction, distance 0) and every consecutive junction pair must be one road."""
    problems = []
    ids = []

    # Every middle row must land exactly on a junction the engine can resolve
    for index, (x, _y, z) in enumerate(rows[1:-1], start = 1):
        node, distance = graph.nearest(x, z)
        if distance > SNAP_EXACT_DISTANCE:
            problems.append(f"row {index} is {distance:.2f} m off junction {node}")
        ids.append(node)

    # ...and every consecutive pair must be joined by a single road
    for index in range(1, len(ids)):
        if not graph.connected(ids[index - 1], ids[index]):
            problems.append(f"no road {ids[index - 1]} -> {ids[index]} (rows {index}, {index + 1})")

    if len(ids) < 2:
        problems.append("fewer than 2 junctions")

    return problems


def parse_aimap_opponents(aimap_path: Path) -> List[Tuple[str, str, float]]:
    """[(mm2 model, .opp file name, max throttle)] from a MM2 aimap's [Opponent] section."""
    lines = aimap_path.read_text(encoding = "latin-1").splitlines()
    out = []
    index = 0

    while index < len(lines):
        if lines[index].strip() != OPPONENT_SECTION:
            index += 1
            continue

        # The section header is followed by a count, then that many entry lines
        index += 1
        count_line = lines[index].strip() if index < len(lines) else "0"
        count = int(count_line) if count_line.lstrip("-").isdigit() else 0
        index += 1

        read = 0
        while read < count and index < len(lines):
            line = lines[index].strip()
            index += 1
            if not line or line.startswith("#"):
                continue
            columns = line.split()
            if len(columns) < 2:
                continue
            throttle = 1.0
            if len(columns) >= 3:
                try:
                    throttle = float(columns[2])
                except ValueError:
                    pass
            out.append((columns[0], columns[1], throttle))
            read += 1
        break
    return out

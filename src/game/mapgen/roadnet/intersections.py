"""
Intersection solver — the capability the old tool was missing entirely.

Mirrors Open1560 `aiIntersection::CreateRoadMap` exactly:
  * sink-path heading uses vertex index 1; source-path heading uses VertexCount-2
  * heading = atan2(dx, dz) of (centre - 0.5*VertXDir - intersection_pos)
  * Paths/Directions are the sink+source merge sorted ascending by heading
  * each source path's EdgeIndex and each sink path's PathIndex = its slot in that ring

It also back-fills `path_index` / `edge_index` onto the PathData objects so the .road
files carry the routing data the runtime walks to choose exits.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List

from src.game.mapgen.roadnet.roadsect import PathData


@dataclass
class IntersectionRecord:
    id: int
    position: tuple                       # (x, y, z)
    sinks: List[int] = field(default_factory=list)
    sources: List[int] = field(default_factory=list)
    paths: List[int] = field(default_factory=list)
    directions: List[float] = field(default_factory=list)


def _heading(path: PathData, vert_idx: int, pos_xz) -> float:
    center = path.center_verts[vert_idx]
    xdir = path.vert_x_dirs[vert_idx]
    dx = center[0] - xdir[0] * 0.5 - pos_xz[0]
    dz = center[2] - xdir[2] * 0.5 - pos_xz[1]
    return math.atan2(dx, dz)


def solve_intersections(node_positions: Dict[int, tuple],
                        paths: List[PathData]) -> List[IntersectionRecord]:
    """
    Build one IntersectionRecord per node and stamp path_index/edge_index back onto the
    paths. `node_positions` maps node id -> (x, z). `paths` is every PathData (fwd+rev).
    """
    by_sink: Dict[int, List[PathData]] = {nid: [] for nid in node_positions}
    by_source: Dict[int, List[PathData]] = {nid: [] for nid in node_positions}
    for p in paths:
        by_sink.setdefault(p.sink_node, []).append(p)
        by_source.setdefault(p.source_node, []).append(p)

    records: List[IntersectionRecord] = []

    for nid in sorted(node_positions):
        pos = node_positions[nid]
        sink_paths = by_sink.get(nid, [])
        source_paths = by_source.get(nid, [])

        path_ids: List[int] = []
        directions: List[float] = []

        # sink paths first (heading at vertex index 1)
        for p in sink_paths:
            path_ids.append(p.id)
            directions.append(_heading(p, 1, pos))
        # then source paths (heading at VertexCount - 2)
        for p in source_paths:
            path_ids.append(p.id)
            directions.append(_heading(p, p.num_vertexs - 2, pos))

        total = len(path_ids)

        # Exact replica of the runtime's swap-sort (ascending by direction).
        for i in range(1, total):
            for j in range(i, total):
                if directions[j] < directions[i - 1]:
                    directions[i - 1], directions[j] = directions[j], directions[i - 1]
                    path_ids[i - 1], path_ids[j] = path_ids[j], path_ids[i - 1]

        slot_of = {pid: idx for idx, pid in enumerate(path_ids)}

        # EdgeIndex on source paths, PathIndex on sink paths.
        for p in source_paths:
            p.edge_index = slot_of[p.id]
        for p in sink_paths:
            p.path_index = slot_of[p.id]

        records.append(IntersectionRecord(
            id=nid,
            position=(pos[0], 0.0, pos[1]),
            sinks=[p.id for p in sink_paths],
            sources=[p.id for p in source_paths],
            paths=path_ids,
            directions=directions,
        ))

    return records

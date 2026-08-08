"""
Cross-section sweep + faithful derivation of a road section's two paths.

This is where the single vertex set is produced. One `Edge` becomes a `RoadSection`
holding two `PathData` (forward + reverse carriageway). The derived AI fields
(CenterVerts / RoadLength / LaneWidths / LaneLengths) are computed EXACTLY as the
Open1560 runtime computes them in `aiPath::CalcCenterVerts`, so the emitted record is
self-consistent with how the game will re-derive it at load.

Vertex layout per the runtime / read_write.write_ai_paths:
  * Each carriageway's LaneVertices = [lane_0 .. lane_{L-1}, sidewalk_centre] columns,
    each column `num_vertexs` long.
  * Boundaries = [outer_strip, inner_strip], each `num_vertexs` long (the curb edges).
  * The .road Vertexs[] block = fwd lane columns + rev lane columns
                              + fwd boundaries + rev boundaries.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from src.game.mapgen.roadnet.geometry import (
    Vec2, Vec3, add2, mul2, sample_polyline, tangents,
    lateral_dir, back_dir, to_vec3, v3_sub, v3_dist, v3_dot_xz,
)
from src.game.mapgen.roadnet.graph import Edge

UP: Vec3 = (0.0, 1.0, 0.0)
ZERO3: Vec3 = (0.0, 0.0, 0.0)


@dataclass
class PathData:
    """One carriageway (one AI path) of a road section."""
    id: int
    oncoming_id: int
    sink_node: int            # intersection id this path terminates at
    source_node: int          # intersection id this path originates at

    num_vertexs: int = 0
    num_lanes: int = 1
    num_sidewalks: int = 1    # 0 or 1 (printed ×2 in the .road)

    lane_cols: List[List[Vec3]] = field(default_factory=list)      # [num_lanes][nv]
    sidewalk_centre: Optional[List[Vec3]] = None                   # [nv] or None
    boundaries: List[Vec3] = field(default_factory=list)           # [outer(nv) + inner(nv)]

    vert_x_dirs: List[Vec3] = field(default_factory=list)          # [nv]
    vert_z_dirs: List[Vec3] = field(default_factory=list)          # [nv]
    normals: List[Vec3] = field(default_factory=list)              # [nv]

    center_verts: List[Vec3] = field(default_factory=list)         # [nv]  (derived)
    center_offsets: List[float] = field(default_factory=list)      # [nv]  (derived)
    road_length: float = 10.0                                      # (derived)
    lane_widths: List[float] = field(default_factory=list)         # (derived)
    lane_lengths: List[float] = field(default_factory=list)        # (derived)
    sub_section_dirs: List[Vec3] = field(default_factory=list)
    sub_section_offsets: List[float] = field(default_factory=list)

    # connectivity — filled by the intersection solver
    path_index: int = 0
    edge_index: int = 0
    intersection_ids: tuple = (0, 0)   # (source_isect, sink_isect)

    # passthrough flags
    intersection_type: int = 3
    speed_limit: float = 15.0
    divided: int = 0
    alley: int = 0
    is_flat: int = 1
    has_bridge: int = 0
    blocked: int = 0
    ped_blocked: int = 0
    stop_light_name: str = "tplttrafc"
    stop_light_pos: tuple = ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))

    def lane_vertices(self) -> List[Vec3]:
        """Flattened LaneVertices = lane columns then the sidewalk-centre column."""
        out: List[Vec3] = []
        for col in self.lane_cols:
            out.extend(col)
        if self.sidewalk_centre is not None:
            out.extend(self.sidewalk_centre)
        return out


@dataclass
class RoadSection:
    edge_index: int
    edge: Edge
    fwd: PathData
    rev: PathData
    # The shared road centreline samples + per-vertex forward tangent. The mesh zone
    # strips (carriageway / sidewalks) are derived from THESE — the same inputs the AI
    # cross-section used — so mesh and AI cannot drift.
    samples: List[Vec2] = field(default_factory=list)
    forward: List[Vec2] = field(default_factory=list)
    pinch: List[float] = field(default_factory=list)


# ── carriageway construction ─────────────────────────────────────────────────

def _build_carriageway(samples: List[Vec2], num_lanes: int, has_sidewalk: bool,
                       lane_width: float, sidewalk_width: float, base_offset: float = 0.0):
    """
    Sweep one carriageway's columns + frames from the shared road centreline samples.

    Lanes sit on the +lateral (right-of-travel) side at centres base_offset + (j+0.5)*lw.
    `base_offset` is the divided-boulevard median half-width (0 for undivided), pushing the
    whole carriageway away from the centreline so the median gap sits between the two sides.
    Returns (lane_cols, sidewalk_centre|None, boundaries, x_dirs, z_dirs).
    """
    nv = len(samples)
    fwd = tangents(samples)

    x_dirs: List[Vec3] = []
    z_dirs: List[Vec3] = []
    for i in range(nv):
        xd2 = lateral_dir(fwd[i])
        zd2 = back_dir(fwd[i])
        # Index 0 frame is zeroed to match the reference (.road VertXDirs[0] == 0 0 0).
        if i == 0:
            x_dirs.append(ZERO3)
            z_dirs.append(ZERO3)
        else:
            x_dirs.append((xd2[0], 0.0, xd2[1]))
            z_dirs.append((zd2[0], 0.0, zd2[1]))

    # Endpoint pinch: every column converges to the node centre at vertex 0 and N-1 so
    # adjacent sections share the junction point and the runtime's lane-start-alignment
    # invariant holds (all lanes share their first/last vertex). Interior is full width.
    def _scale(i: int) -> float:
        return 0.0 if (i == 0 or i == nv - 1) else 1.0

    def offset_col(lateral: float) -> List[Vec3]:
        col: List[Vec3] = []
        for i in range(nv):
            xd2 = lateral_dir(fwd[i])               # use true frame (not the zeroed idx 0)
            p = add2(samples[i], mul2(xd2, lateral * _scale(i)))
            col.append(to_vec3(p, 0.0))
        return col

    lane_cols = [offset_col(base_offset + (j + 0.5) * lane_width) for j in range(num_lanes)]

    sidewalk_centre = None
    boundaries: List[Vec3] = []
    if has_sidewalk:
        edge_lat = base_offset + num_lanes * lane_width
        outer = offset_col(edge_lat + sidewalk_width)
        inner = offset_col(edge_lat)
        sidewalk_centre = offset_col(edge_lat + sidewalk_width * 0.5)
        boundaries = outer + inner          # [outer(nv), inner(nv)]

    return lane_cols, sidewalk_centre, boundaries, x_dirs, z_dirs


def _calc_center_verts(path: PathData, oncoming_lane0: List[Vec3]) -> None:
    """
    Mirror aiPath::CalcCenterVerts: derive CenterVerts/CenterOffsets/RoadLength/
    LaneWidths/LaneLengths into `path`. `oncoming_lane0` is the oncoming path's lane-0
    column (used to place the road centreline halfway between carriageways).
    """
    nv = path.num_vertexs
    lane0 = path.lane_cols[0]
    cv: List[Vec3] = [ZERO3] * nv
    cv[0] = lane0[0]
    cv[nv - 1] = lane0[nv - 1]

    rev_idx = nv - 2
    for i in range(1, nv - 1):
        v = oncoming_lane0[rev_idx]
        cv[i] = (
            lane0[i][0] + (v[0] - lane0[i][0]) * 0.5,
            lane0[i][1] + (v[1] - lane0[i][1]) * 0.5,
            lane0[i][2] + (v[2] - lane0[i][2]) * 0.5,
        )
        rev_idx -= 1
    path.center_verts = cv

    # CenterOffsets — cumulative arc length along the centreline.
    offs = [0.0] * nv
    d = 0.0
    for i in range(1, nv):
        d += v3_dist(cv[i], cv[i - 1])
        offs[i] = d
    path.center_offsets = offs

    xdir2 = (path.vert_x_dirs[2][0], path.vert_x_dirs[2][2])

    # RoadLength
    if path.num_sidewalks:
        diff = v3_sub(path.boundaries[1], cv[2])        # Boundaries[1] = outer strip vtx 1
        path.road_length = abs(v3_dot_xz(diff, xdir2))
    else:
        path.road_length = 10.0

    # LaneWidths[i] for i in 0..(num_sidewalks + num_lanes - 1)
    total_elems = path.num_sidewalks + path.num_lanes
    lane_vertices = path.lane_vertices()
    lw_list = [0.0] * 5                                  # .road always prints 5 slots
    for i in range(total_elems):
        diff = v3_sub(lane_vertices[nv * i + 1], cv[2])
        if i < 5:
            lw_list[i] = abs(v3_dot_xz(diff, xdir2))
    path.lane_widths = lw_list

    # LaneLengths[] — the lateral clamp bands (10 slots printed).
    ll = [0.0] * 10
    rl = path.road_length
    lw = path.lane_widths
    offset = (lw[1] - lw[0]) * -0.5
    ll[0] = -rl
    ll[1] = lw[0] - offset
    for i in range(1, path.num_lanes):
        dd = lw[i] - lw[i - 1]
        ll[2 * i] = lw[i - 1] - dd * -0.5
        ll[2 * i + 1] = lw[i] - dd * -0.5
    if 2 * path.num_lanes < 10:
        ll[2 * path.num_lanes] = rl
    path.lane_lengths = ll


def _calc_subsections(path: PathData) -> None:
    """
    Approximate SubSectionDirs/SubSectionOffsets. These feed minor runtime bookkeeping
    (not the cornering math, which is driven by VertXDirs + Vertexs). SubSectionOffsets
    is the cumulative length along lane-0 then along the sidewalk centre (2*nv values
    in the reference); SubSectionDirs is the per-vertex forward with ends zeroed.
    NOTE: best-effort v1 — exact retail values come from the original art.
    """
    nv = path.num_vertexs
    lane0 = path.lane_cols[0]
    # dirs: forward between consecutive lane-0 verts, ends zeroed (matches Street0 shape)
    dirs: List[Vec3] = [ZERO3]
    for i in range(1, nv - 1):
        d = v3_sub(lane0[i + 1], lane0[i])
        n = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5
        dirs.append((d[0] / n, d[1] / n, d[2] / n) if n > 1e-9 else ZERO3)
    dirs.append(ZERO3)
    path.sub_section_dirs = dirs

    def cum(col: List[Vec3]) -> List[float]:
        out = [0.0]
        d = 0.0
        for i in range(1, len(col)):
            d += v3_dist(col[i], col[i - 1])
            out.append(d)
        return out

    second = path.sidewalk_centre if path.sidewalk_centre is not None else lane0
    path.sub_section_offsets = cum(lane0) + cum(second)


# ── public ────────────────────────────────────────────────────────────────────

def build_road_section(edge: Edge, edge_index: int,
                       a_pos: Vec2, b_pos: Vec2,
                       fwd_id: int, rev_id: int) -> RoadSection:
    """
    Build both carriageways for `edge`. Returns a RoadSection with fully derived AI
    fields. Connectivity indices (path_index/edge_index/intersection_ids) are filled
    later by the intersection solver.

    Convention (verified vs Street0.road): the forward path's vertices run a->b, it
    SINKS at `a` and SOURCES at `b`; the reverse path runs b->a, sinks at `b`,
    sources at `a`. IntersectionIds = (source_isect, sink_isect).
    """
    nv = edge.num_verts
    pts: List[Vec2] = [a_pos, *[(float(p[0]), float(p[1])) for p in edge.shape], b_pos]
    fwd_samples = sample_polyline(pts, nv)
    rev_samples = list(reversed(fwd_samples))

    _median = edge.median_half()
    fwd_cols, fwd_sw, fwd_bnd, fwd_xd, fwd_zd = _build_carriageway(
        fwd_samples, edge.lanes_fwd, edge.sidewalk_fwd, edge.lane_width, edge.sidewalk_width, _median)
    rev_cols, rev_sw, rev_bnd, rev_xd, rev_zd = _build_carriageway(
        rev_samples, edge.lanes_rev, edge.sidewalk_rev, edge.lane_width, edge.sidewalk_width, _median)

    def mk(pid, onc, sink, source, cols, sw, bnd, xd, zd, lanes, has_sw, itype) -> PathData:
        p = PathData(id=pid, oncoming_id=onc, sink_node=sink, source_node=source)
        p.num_vertexs = nv
        p.num_lanes = lanes
        p.num_sidewalks = 1 if has_sw else 0
        p.lane_cols = cols
        p.sidewalk_centre = sw
        p.boundaries = bnd
        p.vert_x_dirs = xd
        p.vert_z_dirs = zd
        p.normals = [UP] * nv
        p.intersection_type = itype
        p.speed_limit = float(edge.speed_limit)
        p.divided = 1 if edge.is_divided() else 0
        p.alley = 1 if edge.alley else 0
        p.is_flat = 1 if edge.is_flat else 0
        p.has_bridge = 1 if edge.has_bridge else 0
        return p

    fwd = mk(fwd_id, rev_id, edge.a, edge.b, fwd_cols, fwd_sw, fwd_bnd, fwd_xd, fwd_zd,
             edge.lanes_fwd, edge.sidewalk_fwd, edge.intersection_type[0])
    rev = mk(rev_id, fwd_id, edge.b, edge.a, rev_cols, rev_sw, rev_bnd, rev_xd, rev_zd,
             edge.lanes_rev, edge.sidewalk_rev, edge.intersection_type[1])

    # Derived fields use the OTHER carriageway's lane-0 column as the oncoming reference.
    _calc_center_verts(fwd, rev.lane_cols[0])
    _calc_center_verts(rev, fwd.lane_cols[0])
    _calc_subsections(fwd)
    _calc_subsections(rev)

    # IntersectionIds = (source_isect, sink_isect)
    fwd.intersection_ids = (fwd.source_node, fwd.sink_node)
    rev.intersection_ids = (rev.source_node, rev.sink_node)

    forward = tangents(fwd_samples)
    pinch = [0.0 if (i == 0 or i == nv - 1) else 1.0 for i in range(nv)]
    return RoadSection(edge_index=edge_index, edge=edge, fwd=fwd, rev=rev,
                       samples=fwd_samples, forward=forward, pinch=pinch)

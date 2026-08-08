"""
Invariant checker for compiled road sections + intersections.

Mirrors the validation `src/file_formats/ai/read_write.py` performs on a loaded BAI, so
a network compiled here passes the Map Editor's own round-trip checks. Returns a list of
`Issue(severity, message)`; `severity` is "ERROR" (would break the game / format) or
"WARN" (suspicious but loadable).
"""
import math
from dataclasses import dataclass
from typing import List

from src.game.mapgen.roadnet.roadsect import RoadSection
from src.game.mapgen.roadnet.intersections import IntersectionRecord

EPS = 1e-3


@dataclass
class Issue:
    severity: str
    message: str

    def __str__(self):
        return f"[{self.severity}] {self.message}"


def _close(a, b, eps=EPS) -> bool:
    return all(abs(a[k] - b[k]) <= eps for k in range(3))


def validate_sections(sections: List[RoadSection]) -> List[Issue]:
    issues: List[Issue] = []
    for s in sections:
        for tag, p, other in (("fwd", s.fwd, s.rev), ("rev", s.rev, s.fwd)):
            nv = p.num_vertexs

            # TotalVertexs invariant
            expected = nv * (s.fwd.num_lanes + s.rev.num_lanes +
                             (s.fwd.num_sidewalks + s.rev.num_sidewalks) * 2)
            total = sum(len(c) for c in (s.fwd.lane_cols + s.rev.lane_cols)) \
                + (len(s.fwd.boundaries) + len(s.rev.boundaries) if s.fwd.num_sidewalks else 0)
            if total != expected:
                issues.append(Issue("ERROR",
                    f"Street{s.fwd.id} {tag}: Vertexs {total} != invariant {expected}"))

            # lane-start / lane-end alignment (all lanes share first/last vertex)
            if p.lane_cols:
                first = p.lane_cols[0][0]
                last = p.lane_cols[0][nv - 1]
                for li, col in enumerate(p.lane_cols[1:], start=1):
                    if not _close(col[0], first):
                        issues.append(Issue("ERROR",
                            f"Street{s.fwd.id} {tag} lane {li}: start vertex != lane 0"))
                    if not _close(col[nv - 1], last):
                        issues.append(Issue("ERROR",
                            f"Street{s.fwd.id} {tag} lane {li}: end vertex != lane 0"))

            # normals: ends up; flat road => all up
            if p.normals:
                if not _close(p.normals[0], (0, 1, 0)):
                    issues.append(Issue("WARN", f"Street{s.fwd.id} {tag}: first normal not up"))
                if not _close(p.normals[-1], (0, 1, 0)):
                    issues.append(Issue("WARN", f"Street{s.fwd.id} {tag}: last normal not up"))
            if p.num_sidewalks == 0:
                if any(not _close(n, (0, 1, 0)) for n in p.normals):
                    issues.append(Issue("WARN",
                        f"Street{s.fwd.id} {tag}: no sidewalks but non-up normal(s)"))

            # sidewalk midpoint: centre column == midpoint(outer, inner)
            if p.num_sidewalks and p.sidewalk_centre is not None:
                for i in range(nv):
                    outer = p.boundaries[i]
                    inner = p.boundaries[nv + i]
                    mid = ((outer[0] + inner[0]) * 0.5,
                           (outer[1] + inner[1]) * 0.5,
                           (outer[2] + inner[2]) * 0.5)
                    if not _close(p.sidewalk_centre[i], mid, 1e-2):
                        issues.append(Issue("WARN",
                            f"Street{s.fwd.id} {tag} v{i}: sidewalk midpoint mismatch"))
                        break

        # oncoming symmetry
        if s.fwd.oncoming_id != s.rev.id or s.rev.oncoming_id != s.fwd.id:
            issues.append(Issue("ERROR", f"Street{s.fwd.id}: oncoming link not symmetric"))
        if s.fwd.num_vertexs != s.rev.num_vertexs:
            issues.append(Issue("ERROR", f"Street{s.fwd.id}: num_vertexs mismatch fwd/rev"))
        if s.fwd.num_sidewalks != s.rev.num_sidewalks:
            issues.append(Issue("WARN", f"Street{s.fwd.id}: num_sidewalks mismatch fwd/rev"))
        if s.fwd.divided != s.rev.divided or s.fwd.alley != s.rev.alley:
            issues.append(Issue("WARN", f"Street{s.fwd.id}: divided/alley mismatch fwd/rev"))

    return issues


def validate_intersections(records: List[IntersectionRecord],
                           num_nodes: int) -> List[Issue]:
    issues: List[Issue] = []
    for rec in records:
        # directions ascending
        for i in range(1, len(rec.directions)):
            if rec.directions[i] < rec.directions[i - 1] - 1e-6:
                issues.append(Issue("ERROR",
                    f"Intersection{rec.id}: Directions not ascending at {i}"))
                break
        # Paths is sinks+sources as a set
        if sorted(rec.paths) != sorted(list(rec.sinks) + list(rec.sources)):
            issues.append(Issue("ERROR",
                f"Intersection{rec.id}: Paths != Sinks+Sources"))
        # a usable junction has somewhere to go
        if rec.sinks and not rec.sources:
            issues.append(Issue("WARN",
                f"Intersection{rec.id}: has sinks but no sources (dead-end traffic)"))
    return issues


def summarize(issues: List[Issue]) -> str:
    errors = sum(1 for i in issues if i.severity == "ERROR")
    warns = sum(1 for i in issues if i.severity == "WARN")
    return f"{errors} error(s), {warns} warning(s)"


def validate_network(net) -> List[Issue]:
    """
    Pre-compile sanity check on a RoadNetwork GRAPH (presets / Blender / programmatic), so problems
    are reported BEFORE the build instead of crashing mid-way. ERRORs are structural (would break the
    build); WARNs flag AI-safe-envelope geometry that builds fine but can crash the engine's AI on a
    procedural map (curve+grade, 3-lane, divided, alley, perpendicular curve+curve, very steep grade).
    Returns Issue(severity, message); pair with summarize().
    """
    issues: List[Issue] = []

    # structural (ERRORs): reuse the graph's own topology checks
    for problem in net.validate_topology():
        issues.append(Issue("ERROR", problem))

    # geometry sanity per edge
    for i, e in enumerate(net.edges):
        if e.a not in net.nodes or e.b not in net.nodes:
            continue  # dangling already reported by validate_topology
        ax, az = net.nodes[e.a].pos
        bx, bz = net.nodes[e.b].pos
        if not all(math.isfinite(v) for v in (ax, az, bx, bz)):
            issues.append(Issue("ERROR", f"edge {i} ({e.a}->{e.b}): non-finite node position"))
            continue
        if (bx - ax) ** 2 + (bz - az) ** 2 < 1e-6:
            issues.append(Issue("ERROR",
                f"edge {i}: coincident endpoints (zero-length road) at ({ax:.1f},{az:.1f}) - "
                f"nodes {e.a} and {e.b} are on top of each other"))
        if getattr(e, "lane_width", 1.0) <= 0.0:
            issues.append(Issue("WARN", f"edge {i}: lane_width <= 0 ({getattr(e, 'lane_width', None)})"))

    # AI-safe envelope (WARNs) - geometry the engine's AI is known to handle badly
    n_three = sum(1 for e in net.edges if e.lanes_fwd >= 3 or e.lanes_rev >= 3)
    if n_three:
        issues.append(Issue("WARN", f"{n_three} edge(s) with 3+ lanes - a known AI freeze risk; prefer <=2 lanes (use wider lane_width for a wide road)"))
    n_div = sum(1 for e in net.edges if getattr(e, "divided", False))
    if n_div:
        issues.append(Issue("WARN", f"{n_div} divided edge(s) - grass medians can trap AI cars"))
    n_alley = sum(1 for e in net.edges if getattr(e, "alley", False))
    if n_alley:
        issues.append(Issue("WARN", f"{n_alley} alley edge(s) - no-sidewalk roads can crash the AI"))

    terrain = getattr(net, "terrain", None)
    if terrain is not None:
        # curve+grade: a curved road that also climbs (crashes the wheel AI)
        for i, e in enumerate(net.edges):
            shape = getattr(e, "shape", None)
            if not shape:
                continue
            pts = [net.nodes[e.a].pos] + list(shape) + [net.nodes[e.b].pos]
            ys = [terrain(p[0], p[1]) for p in pts]
            if max(ys) - min(ys) > 0.5:
                issues.append(Issue("WARN", f"edge {i}: curve+grade (a curved road on a slope) - crashes the AI wheel sim; confine curves to flat zones"))
                break
        # very steep grade
        for e in net.edges:
            ax, az = net.nodes[e.a].pos
            bx, bz = net.nodes[e.b].pos
            seg = ((bx - ax) ** 2 + (bz - az) ** 2) ** 0.5 or 1.0
            if abs(terrain(bx, bz) - terrain(ax, az)) / seg > 0.18:
                issues.append(Issue("WARN", "terrain exceeds ~18% grade somewhere - very steep; keep slopes a SINGLE smooth ramp (the engine handles ~15%, kinks/steeper can crash the AI rails)"))
                break

    # perpendicular curve+curve: a node where a curved horizontal AND a curved vertical road meet
    cc_nodes = 0
    for nid in net.nodes:
        has_h = has_v = False
        for e in net.edges:
            if (e.a == nid or e.b == nid) and getattr(e, "shape", None):
                ax, az = net.nodes[e.a].pos
                bx, bz = net.nodes[e.b].pos
                if abs(bx - ax) >= abs(bz - az):
                    has_h = True
                else:
                    has_v = True
        if has_h and has_v:
            cc_nodes += 1
    if cc_nodes:
        issues.append(Issue("WARN", f"{cc_nodes} node(s) where a curved horizontal + curved vertical road cross (perpendicular curve+curve) - sharp such junctions can crash the AI"))

    return issues

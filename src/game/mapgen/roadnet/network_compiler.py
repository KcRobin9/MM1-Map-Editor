"""
RoadNetworkCompiler — the orchestrator. graph -> all coherent products.

    net = grid_city(3, 3)
    compiled = RoadNetworkCompiler().compile(net)
    compiled.write_ai("out/AI")        # streets/*.road, intersections/*.int, CHICAGO.map
    quads = compiled.road_mesh_quads() # drivable mesh from the SAME vertices as the AI

Everything is derived from one graph, so the mesh, the AI cross-section, the intersection
routing and the cell ids stay in step.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List

from src.game.mapgen.roadnet.graph import RoadNetwork
from src.game.mapgen.roadnet.roadsect import RoadSection, PathData, build_road_section
from src.game.mapgen.roadnet.intersections import IntersectionRecord, solve_intersections
from src.game.mapgen.roadnet.emit import emit_road, emit_intersection, emit_map
from src.game.mapgen.roadnet.validate import (
    Issue, validate_sections, validate_intersections, summarize,
)

# Cell-id scheme mirroring Angel's Type-1 (road interior) / Type-2 (intersection) split.
CELL_ROAD_BASE = 100
CELL_ISECT_BASE = 1000


@dataclass
class MeshQuad:
    verts: List                       # 4 game-space (x, y, z) corners, CCW
    cell: int
    kind: str                         # "road" | "intersection"
    section: int = -1
    node: int = -1


@dataclass
class CompiledNetwork:
    network: RoadNetwork
    sections: List[RoadSection]
    intersections: List[IntersectionRecord]
    paths: List[PathData] = field(default_factory=list)

    # ── AI text emission ────────────────────────────────────────────────────────

    def write_ai(self, out_dir: str) -> Dict[str, int]:
        """Write streets/*.road, intersections/*.int and CHICAGO.map under out_dir."""
        streets_dir = os.path.join(out_dir, "streets")
        isect_dir = os.path.join(out_dir, "intersections")
        os.makedirs(streets_dir, exist_ok=True)
        os.makedirs(isect_dir, exist_ok=True)

        for s in self.sections:
            with open(os.path.join(streets_dir, f"Street{s.fwd.id}.road"), "w") as f:
                f.write(emit_road(s))

        for rec in self.intersections:
            with open(os.path.join(isect_dir, f"Intersection{rec.id}.int"), "w") as f:
                f.write(emit_intersection(rec))

        street_ids = [s.fwd.id for s in self.sections]
        with open(os.path.join(out_dir, "CHICAGO.map"), "w") as f:
            f.write(emit_map(street_ids))

        return {"streets": len(self.sections), "intersections": len(self.intersections)}

    # ── drivable mesh from the SAME vertices ────────────────────────────────────

    def road_mesh_quads(self) -> List[MeshQuad]:
        """
        One drivable surface quad per centreline segment, spanning the full footprint
        (reverse-carriageway outer edge to forward-carriageway outer edge). Because these
        corners are the very vertices the AI uses, the mesh and AI share geometry exactly.
        """
        quads: List[MeshQuad] = []
        for si, s in enumerate(self.sections):
            cell = CELL_ROAD_BASE + si
            fwd, rev = s.fwd, s.rev
            nv = fwd.num_vertexs

            # Right edge = forward carriageway outer boundary (or outermost lane edge).
            right = fwd.boundaries[0:nv] if fwd.num_sidewalks else fwd.lane_cols[-1]
            # Left edge = reverse carriageway outer boundary, reversed to align indices.
            left_src = rev.boundaries[0:nv] if rev.num_sidewalks else rev.lane_cols[-1]
            left = list(reversed(left_src))

            for i in range(nv - 1):
                quads.append(MeshQuad(
                    verts=[left[i], right[i], right[i + 1], left[i + 1]],
                    cell=cell, kind="road", section=si))
        return quads

    def intersection_quads(self) -> List[MeshQuad]:
        """A square patch per junction sized to its widest incident road."""
        quads: List[MeshQuad] = []
        for rec in self.intersections:
            half = self._node_patch_half(rec.id)
            cx, _, cz = rec.position
            quads.append(MeshQuad(
                verts=[(cx - half, 0.0, cz - half), (cx + half, 0.0, cz - half),
                       (cx + half, 0.0, cz + half), (cx - half, 0.0, cz + half)],
                cell=CELL_ISECT_BASE + rec.id, kind="intersection", node=rec.id))
        return quads

    def _node_patch_half(self, node_id: int) -> float:
        widest = 10.0
        for e in self.network.edges:
            if node_id in (e.a, e.b):
                w = e.total_lanes() * e.lane_width
                if e.sidewalk_fwd:
                    w += e.sidewalk_width
                if e.sidewalk_rev:
                    w += e.sidewalk_width
                widest = max(widest, w)
        return widest / 2.0

    def cell_assignments(self) -> Dict[int, str]:
        """cell id -> 'road:N' / 'intersection:N' (Type-1 / Type-2 markers)."""
        cells: Dict[int, str] = {}
        for si in range(len(self.sections)):
            cells[CELL_ROAD_BASE + si] = f"road:{si}"
        for rec in self.intersections:
            cells[CELL_ISECT_BASE + rec.id] = f"intersection:{rec.id}"
        return cells

    # ── validation ──────────────────────────────────────────────────────────────

    def validate(self) -> List[Issue]:
        issues = validate_sections(self.sections)
        issues += validate_intersections(self.intersections, len(self.network.nodes))
        return issues

    def report(self) -> str:
        issues = self.validate()
        lines = [
            f"Network '{self.network.name}': {len(self.network.nodes)} nodes, "
            f"{len(self.sections)} sections, {len(self.paths)} paths, "
            f"{len(self.intersections)} intersections",
            f"Validation: {summarize(issues)}",
        ]
        for issue in issues[:40]:
            lines.append(f"  {issue}")
        if len(issues) > 40:
            lines.append(f"  ... and {len(issues) - 40} more")
        return "\n".join(lines)


class RoadNetworkCompiler:
    """graph -> CompiledNetwork. Stateless; call compile()."""

    def compile(self, network: RoadNetwork) -> CompiledNetwork:
        problems = network.validate_topology()
        if problems:
            raise ValueError("road network has topology problems:\n  " +
                             "\n  ".join(problems))

        node_positions = {nid: n.pos for nid, n in network.nodes.items()}

        sections: List[RoadSection] = []
        paths: List[PathData] = []
        for ei, e in enumerate(network.edges):
            fwd_id = 2 * ei
            rev_id = 2 * ei + 1
            sec = build_road_section(
                e, ei, network.nodes[e.a].pos, network.nodes[e.b].pos, fwd_id, rev_id)
            sections.append(sec)
            paths.append(sec.fwd)
            paths.append(sec.rev)

        intersections = solve_intersections(node_positions, paths)

        # back-fill solver results that affect the .road (path/edge index) are already on
        # the PathData; nothing else to wire.
        return CompiledNetwork(
            network=network, sections=sections, intersections=intersections, paths=paths)

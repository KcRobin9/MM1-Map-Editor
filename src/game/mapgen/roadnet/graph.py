"""
The road-network graph — the ONLY thing the user edits.

  Node = an intersection (a position on the ground plane).
  Edge = a bidirectional road section between two nodes, with a cross-section
         (lanes per direction, sidewalks, width, flags).

Everything downstream (geometry, AI, intersections, cells) is derived from this graph
so the products cannot drift. This mirrors the single source of truth Angel's City tool
held.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from src.game.mapgen.roadnet.geometry import Vec2

# MM1 / Chicago defaults (metres). Verified against Street0.road:
#   lane centre at 2.50 = 0.5*lane_width, sidewalk centre at 7.50, RoadLength 10.00.
DEFAULT_LANE_WIDTH = 5.0
DEFAULT_SIDEWALK_WIDTH = 5.0
DEFAULT_SPEED_LIMIT = 15.0
DEFAULT_NUM_VERTS = 6          # centreline samples per section (Street0 uses 6)


@dataclass
class Node:
    """An intersection / junction."""
    id: int
    pos: Vec2                  # (x, z) on the ground plane
    name: str = ""

    def __post_init__(self):
        self.pos = (float(self.pos[0]), float(self.pos[1]))


@dataclass
class Edge:
    """
    A bidirectional road section connecting node `a` -> node `b`.

    The forward carriageway runs a->b; the reverse carriageway runs b->a. Lane counts
    are PER DIRECTION (NumLanes[0]/NumLanes[1]) — this is the asymmetry the old
    road_builder lacked.
    """
    a: int                     # node id (forward-start; the forward path SINKS here)
    b: int                     # node id (forward-end;   the forward path SOURCES here)

    lanes_fwd: int = 1         # NumLanes[0]
    lanes_rev: int = 1         # NumLanes[1]
    sidewalk_fwd: bool = True  # NumSidewalks[0] -> 2 boundary strips when True
    sidewalk_rev: bool = True  # NumSidewalks[1]

    lane_width: float = DEFAULT_LANE_WIDTH
    sidewalk_width: float = DEFAULT_SIDEWALK_WIDTH
    speed_limit: float = DEFAULT_SPEED_LIMIT
    num_verts: int = DEFAULT_NUM_VERTS

    # Raised kerb: the sidewalk sits CURB_HEIGHT above the road, bridged by a short steep curb
    # face this wide (a "mini wall"). 0 = flush kerb. Only applies where there is a sidewalk.
    curb_width: float = 0.3

    # Divided boulevard: a median strip of this width separates the two carriageways. 0 =
    # undivided. When > 0 the carriageways are pushed apart by median_width/2 each (both the
    # mesh AND the AI lane vertices) and `divided` is implied true.
    median_width: float = 0.0

    divided: bool = False
    alley: bool = False
    is_flat: bool = True       # v1 emits flat roads (y=0, normals up) — see network_compiler
    has_bridge: bool = False

    # BRIDGE: a deck that ARCHES up to this peak height (m) over its span (0 at the shore ends),
    # crossing water/a gap. >0 turns the section into a bridge: the road Y arches, and the ground
    # (water) UNDER it is kept instead of being cut out, so the water shows beneath the deck.
    deck_height: float = 0.0
    # BRIDGE slope SHAPE (see _deck_lift): "arch" (symmetric hump, default), "early" (steep-up/gentle-
    # down), "late" (gentle-up/steep-down), "double" (two humps within one piece). All return to 0 at
    # both ends so the deck meets the flat road with no step. Lets one deck piece have richer slopes.
    deck_profile: str = "arch"

    # BANKING (racetrack camber): tilt the deck laterally INTO the turn by this many DEGREES. Signed by
    # the turn direction automatically; tapered by the arch so it eases to flat at the node ends. Needs
    # deck_height>0 (the lift keeps the low inner edge above ground). 0 = flat (no camber).
    bank_deg: float = 0.0

    # ROOFED TUNNEL: >0 wraps the road in vertical walls (floor -> this height) + a down-facing
    # ceiling, so you drive through a covered section. Pair with sidewalk_fwd/rev=False.
    tunnel_height: float = 0.0

    # Optional intermediate shape points (x,z) between a and b for curved sections.
    # If empty, the section is straight. Endpoints are taken from the nodes.
    shape: Sequence[Vec2] = field(default_factory=tuple)

    # Per-end intersection control. Index 0 = the `a`/sink end, 1 = the `b`/source end.
    # Values are IntersectionType ints (3 = CONTINUE, 1 = STOP_LIGHT, 0 = STOP, 2 = YIELD).
    intersection_type: Tuple[int, int] = (3, 3)

    def median_half(self) -> float:
        return self.median_width / 2.0

    def is_divided(self) -> bool:
        return self.divided or self.median_width > 0.0

    def total_lanes(self) -> int:
        return self.lanes_fwd + self.lanes_rev

    def num_sidewalks_fwd(self) -> int:
        """The .road NumSidewalks[0] value (boundary-strip count): 2 if present else 0."""
        return 2 if self.sidewalk_fwd else 0

    def num_sidewalks_rev(self) -> int:
        return 2 if self.sidewalk_rev else 0


@dataclass
class RoadNetwork:
    """A whole city's road graph."""
    name: str = "GeneratedCity"
    nodes: Dict[int, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    # ── building ──────────────────────────────────────────────────────────────

    def add_node(self, pos: Vec2, node_id: Optional[int] = None, name: str = "") -> Node:
        if node_id is None:
            node_id = (max(self.nodes) + 1) if self.nodes else 0
        if node_id in self.nodes:
            raise ValueError(f"duplicate node id {node_id}")
        n = Node(id=node_id, pos=pos, name=name)
        self.nodes[node_id] = n
        return n

    def add_edge(self, a: int, b: int, **kwargs) -> Edge:
        if a not in self.nodes or b not in self.nodes:
            raise ValueError(f"edge {a}->{b} references unknown node")
        if a == b:
            raise ValueError("edge cannot connect a node to itself")
        e = Edge(a=a, b=b, **kwargs)
        self.edges.append(e)
        return e

    # ── queries ────────────────────────────────────────────────────────────────

    def degree(self, node_id: int) -> int:
        return sum(1 for e in self.edges if e.a == node_id or e.b == node_id)

    def incident_edges(self, node_id: int) -> List[Tuple[int, Edge]]:
        """Return (edge_index, edge) for every edge touching the node."""
        return [(i, e) for i, e in enumerate(self.edges) if e.a == node_id or e.b == node_id]

    def validate_topology(self) -> List[str]:
        """Cheap structural checks; returns a list of human-readable problems."""
        problems: List[str] = []
        for i, e in enumerate(self.edges):
            if e.a not in self.nodes or e.b not in self.nodes:
                problems.append(f"edge {i}: dangling node reference {e.a}->{e.b}")
            if e.lanes_fwd < 1 or e.lanes_rev < 1:
                problems.append(f"edge {i}: each direction needs >=1 lane "
                                f"(got {e.lanes_fwd}/{e.lanes_rev})")
            if e.num_verts < 2:
                problems.append(f"edge {i}: num_verts must be >= 2")
        seen = set()
        for i, e in enumerate(self.edges):
            key = tuple(sorted((e.a, e.b)))
            if key in seen:
                problems.append(f"edge {i}: duplicate section between {e.a} and {e.b}")
            seen.add(key)
        for nid in self.nodes:
            if self.degree(nid) == 0:
                problems.append(f"node {nid}: isolated (no roads)")
        return problems


# ── convenience builders ────────────────────────────────────────────────────

def grid_city(cols: int, rows: int, spacing: float = 120.0,
              lanes_fwd: int = 1, lanes_rev: int = 1,
              name: str = "GridCity") -> RoadNetwork:
    """
    Build a simple cols×rows grid network — a good smoke-test city.

    Nodes are laid out on a regular lattice; every horizontal & vertical neighbour pair
    gets a bidirectional road section.
    """
    net = RoadNetwork(name=name)
    ids: Dict[Tuple[int, int], int] = {}
    nid = 0
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2.0) * spacing
            z = (r - (rows - 1) / 2.0) * spacing
            net.add_node((x, z), node_id=nid)
            ids[(c, r)] = nid
            nid += 1
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                net.add_edge(ids[(c, r)], ids[(c + 1, r)],
                             lanes_fwd=lanes_fwd, lanes_rev=lanes_rev)
            if r + 1 < rows:
                net.add_edge(ids[(c, r)], ids[(c, r + 1)],
                             lanes_fwd=lanes_fwd, lanes_rev=lanes_rev)
    return net

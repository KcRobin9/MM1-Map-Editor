"""
roadnet — single-source-of-truth road-network compiler for MM1.

    ONE road-network graph  ->  MANY coherent emitters (all sharing vertices)

It is the Map-Editor analogue of Angel Studios' unreleased City tool: a graph of
intersections (nodes) and bidirectional road sections (edges) is swept ONCE into a
shared vertex set, and every downstream product is derived from those same vertices:

    graph ──┬─ sweep bidirectional cross-section along each edge  -> shared Vertexs[]
            ├─ mmRoadSect (.road)   lanes/dir + sidewalks + VertXDirs/VertZDirs                
            ├─ mmIntersection (.int) Sinks/Sources/Paths/Directions + indices                  
            ├─ CHICAGO.map (.map)   the street list
            ├─ drivable road mesh   (same centreline + width as the AI)                         
            └─ per-section cell ids  (one cell per section + per intersection)                       

Because mesh and AI come from the SAME vertices they stay in step, which is the root
cause of the per-junction swerve / 3-lane frozen-RoadDist / orbit bug class.

The core (graph/geometry/roadsect/intersections/emit/validate/network_compiler) is
PURE PYTHON with no Blender or heavy `src.*` dependency, so it runs and self-tests
standalone:

    python -m src.game.mapgen.roadnet.demo

Faithfulness anchors (Open1560):
  * aiPath::CalcCenterVerts  -> RoadLength / LaneWidths / LaneLengths / CenterVerts
  * aiIntersection::CreateRoadMap -> Sinks/Sources sort, EdgeIndex/PathIndex
  * read_write.write_ai_paths -> exact mmRoadSect field order & Vertexs[] layout
"""

from src.game.mapgen.roadnet.graph import Node, Edge, RoadNetwork, grid_city
from src.game.mapgen.roadnet.network_compiler import RoadNetworkCompiler, CompiledNetwork

__all__ = [
    "Node",
    "Edge",
    "RoadNetwork",
    "grid_city",
    "RoadNetworkCompiler",
    "CompiledNetwork",
]

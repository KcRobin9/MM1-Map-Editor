"""MM2 -> MM1 city converter (PSDL geometry rip).

Reads the tessellated geometry produced by `wilkovatch/psdl-import`
(`output/expanded_psdl.json`) and authors it into the MM1 Map-Editor pipeline
(create_polygon / save_mesh / compute_uv), exactly like roadnet's emit_roadnet_city.

Phase-1 scope: a drivable, PLAYER-ONLY shell - real MM2 geometry + collision, MM1
placeholder textures, every cell always-visible (no portals). AI/traffic = later phase.
"""
from src.game.mapgen.mm2.mm2_city import (
    load_expanded, iter_mm2_polys, emit_mm2_city, Mm2PolySpec, Mm2Options,
)

__all__ = [
    "load_expanded", "iter_mm2_polys", "emit_mm2_city", "Mm2PolySpec", "Mm2Options",
]

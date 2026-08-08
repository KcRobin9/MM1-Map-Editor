"""
Adapter: roadnet -> the existing build pipeline.

Bridges a CompiledNetwork to the structures `MAP_EDITOR_ALPHA_v1.py`/`compile_mapspec`
already consume (`PolygonSpec`) and to the AI folder the pipeline reads. Kept in a
separate module (with lazy imports) so the core roadnet package stays Blender-free and
standalone-testable; importing THIS module is what couples roadnet to the rest of the tool.

Typical use inside the build pipeline:

    from src.game.mapgen.roadnet import RoadNetworkCompiler
    from src.game.mapgen.roadnet.pipeline_adapter import to_polygon_specs, write_ai_to_devmap

    compiled = RoadNetworkCompiler().compile(network)
    polys = to_polygon_specs(compiled)          # feed create_polygon()/save_mesh()
    write_ai_to_devmap(compiled)                # drop .road/.int/.map where the build expects
"""
from typing import List

from src.game.mapgen.roadnet.network_compiler import CompiledNetwork


def to_polygon_specs(compiled: CompiledNetwork) -> List:
    """
    Convert the road + intersection quads into the pipeline's PolygonSpec list. Because
    these quads come from the same vertices as the AI, the resulting mesh and the .road
    cross-section are coherent by construction.
    """
    from src.game.mapgen.compiler import PolygonSpec
    from src.constants.color import Color
    from src.constants.file_formats import Material, Room
    from src.game.mapgen.spec import road_texture, _INTERSECTION_TEX

    polys: List = []

    for q in compiled.road_mesh_quads():
        # bound numbers must avoid 0/200 and stay in range; CELL_ROAD_BASE=100 is safe.
        polys.append(PolygonSpec(
            bound=q.cell,
            verts=[(v[0], v[1], v[2]) for v in q.verts],
            material_index=Material.DEFAULT, cell_type=Room.DEFAULT, hud_color=Color.ROAD,
            texture=road_texture(2), tile_x=2.0, tile_y=2.0, angle=0.0, is_spawn=False,
        ))

    for q in compiled.intersection_quads():
        polys.append(PolygonSpec(
            bound=q.cell,
            verts=[(v[0], v[1], v[2]) for v in q.verts],
            material_index=Material.DEFAULT, cell_type=Room.DEFAULT, hud_color=Color.ROAD,
            texture=_INTERSECTION_TEX, tile_x=2.0, tile_y=2.0, angle=0.0, is_spawn=False,
        ))

    return polys


def write_ai_to_devmap(compiled: CompiledNetwork) -> dict:
    """Write the AI files into the pipeline's dev city-map folder (Folder.MidtownMadness)."""
    from src.constants.folder import Folder
    out_dir = str(Folder.MidtownMadness.DevCityMap)
    return compiled.write_ai(out_dir)

"""
Realise a CompiledMap through the pipeline's polygon API.

The compiler is Blender-free and only produces PolygonSpec data; this thin glue feeds
that data into MAP_EDITOR_ALPHA_v1.py's existing create_polygon()/save_mesh() so the
rest of the build (collision bounds, cells, portals, .AR) happens unchanged. The
pipeline functions are passed in (dependency injection) to avoid importing the big
entry script — call it from there:

    from src.game.mapgen.compiler import compile_mapspec
    from src.game.mapgen.spec import load_spec
    from src.game.mapgen.emit import emit_compiled_map
    emit_compiled_map(compile_mapspec(load_spec("my_map.json")),
                      create_polygon, save_mesh, compute_uv)
"""
from src.game.mapgen.compiler import CompiledMap


def emit_compiled_map(compiled: CompiledMap, create_polygon, save_mesh, compute_uv) -> int:
    """Author every compiled polygon via the pipeline API. Returns the count."""
    for poly in compiled.polygons:
        create_polygon(
            bound_number=poly.bound,
            vertex_coordinates=poly.verts,
            material_index=poly.material_index,
            cell_type=poly.cell_type,
            hud_color=poly.hud_color,
            base=poly.is_spawn,
        )
        if poly.texture:
            save_mesh(
                texture_name=[poly.texture],
                tex_coords=compute_uv(bound_number=poly.bound, tile_x=poly.tile_x,
                                      tile_y=poly.tile_y, angle_degrees=poly.angle),
            )
    return len(compiled.polygons)

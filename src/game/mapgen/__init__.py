"""
mapgen — generate Midtown Madness maps from a high-level MapSpec.

The MapSpec (spec.py) is the shared contract; compile_mapspec (compiler.py) realises it
into pipeline-ready polygons; emit_compiled_map (emit.py) feeds them through the build.
A MapSpec can be hand/AI-authored (JSON) or produced procedurally (generator.py). The
compiler is Blender-free so generation can run headless / on the fly.
"""
from src.game.mapgen.spec import load_spec, save_spec, validate_spec, EXAMPLE_SPEC
from src.game.mapgen.compiler import compile_mapspec, CompiledMap, PolygonSpec
from src.game.mapgen.generator import grid_mapspec
from src.game.mapgen.emit import emit_compiled_map

__all__ = [
    "load_spec", "save_spec", "validate_spec", "EXAMPLE_SPEC",
    "compile_mapspec", "CompiledMap", "PolygonSpec",
    "grid_mapspec", "emit_compiled_map",
]

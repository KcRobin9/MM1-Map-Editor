"""
Assemble MM2 detailed buildings: INST placements x PKG meshes -> world-space triangles (with UVs +
texture) ready to bake into the MM1 city. Ties together inst.py (placements) + pkg.py (meshes).

Transform: a COORDINATE component maps a model vertex v to
    world = origin + v.x * x_axis + v.y * y_axis + v.z * z_axis      (axes are the columns)
A SIMPLE component is a Y-rotation by the stored heading, then a translation to the location.
"""
import math
from typing import Dict, Iterator, Tuple
from pathlib import Path

from src.constants.file_formats import FileType
from .inst import parse_inst
from .pkg import parse_pkg


def _place_by_axes(point, axes, origin):
    """Coordinate component: the INST carries a full 3x3 axis matrix."""
    (xx, xy, xz), (yx, yy, yz), (zx, zy, zz) = axes
    return (origin[0] + point[0] * xx + point[1] * yx + point[2] * zx,
            origin[1] + point[0] * xy + point[1] * yy + point[2] * zy,
            origin[2] + point[0] * xz + point[1] * yz + point[2] * zz)


def _place_by_heading(point, heading_x, heading_z, location):
    """Simple component: rotate about Y so local +X follows the heading, then translate."""
    return (location[0] + point[0] * heading_x - point[2] * heading_z,
            location[1] + point[1],
            location[2] + point[0] * heading_z + point[2] * heading_x)


def iter_buildings(inst_path: str, geometry_dir: str, lod: str = "H",
                   _cache: Dict = None) -> Iterator[Tuple[str, tuple, tuple, tuple]]:
    """Yield (texture, v0, v1, v2) world-space triangles, each vN = (position3, uv2).

    One triangle per building face, across every INST placement whose PKG mesh is on disk.
    Meshes are cached by model name, since a city places the same model many times.
    """
    cache: Dict[str, Dict] = {} if _cache is None else _cache

    for placement in parse_inst(inst_path):
        name = placement["name"]

        if name not in cache:
            pkg_path = Path(geometry_dir) / (name + FileType.MM2_MESH)
            cache[name] = parse_pkg(str(pkg_path), lod) if pkg_path.exists() else None

        mesh = cache[name]
        if not mesh or not mesh["sections"]:
            continue

        if placement.get("simple"):
            heading = math.radians(placement["angle"])
            heading_x, heading_z = math.sin(heading), math.cos(heading)
            location = placement["pos"]
            to_world = lambda point: _place_by_heading(point, heading_x, heading_z, location)
        else:
            axes, origin = placement["axes"], placement["pos"]
            to_world = lambda point: _place_by_axes(point, axes, origin)

        shader_textures = mesh["shader_tex"]
        for shader_offset, triangles in mesh["sections"]:
            texture = shader_textures[shader_offset] if 0 <= shader_offset < len(shader_textures) else ""

            for (p0, uv0), (p1, uv1), (p2, uv2) in triangles:
                yield (texture, (to_world(p0), uv0), (to_world(p1), uv1), (to_world(p2), uv2))


if __name__ == "__main__":
    import sys
    import collections

    inst_path, geometry_dir = sys.argv[1], sys.argv[2]
    cache = {}
    textures = collections.Counter()
    triangle_count = 0
    xs, ys, zs = [], [], []

    for texture, a, b, c in iter_buildings(inst_path, geometry_dir, _cache = cache):
        triangle_count += 1
        textures[texture] += 1
        for position, _uv in (a, b, c):
            xs.append(position[0])
            ys.append(position[1])
            zs.append(position[2])

    placed = sum(1 for mesh in cache.values() if mesh and mesh["sections"])
    missing = sum(1 for mesh in cache.values() if mesh is None)

    print("building triangles:", triangle_count)
    print("models placed:", placed, "/ referenced:", len(cache), "(missing:", missing, ")")
    if xs:
        print("world range x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]"
              % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print("distinct textures:", len(textures))
    print("top textures:", [name for name, _ in textures.most_common(8)])

"""
MapSpec -> game geometry compiler (Blender-free).

Turns a MapSpec (a road-network graph + zones) into a flat list of PolygonSpec — the
exact data the pipeline's create_polygon()/save_mesh() consume. Milestone-1 scope is a
drivable shell: a grass base, road carriageways + sidewalks, an intersection patch at
every node, and a spawn. Collision bounds, cells, portals and the .AR are derived by
the pipeline from these polygons; AI traffic / blocks / facades / props come later.

All math is plain Python on game coords (ground plane = x,z; 1 unit = 1 m).
"""
import math
from typing import Dict, List, NamedTuple, Tuple

from src.constants.color import Color
from src.constants.file_formats import Material, Room
from src.game.mapgen.spec import (
    GROUND_Y, ROAD_Y, SIDEWALK_Y, LANE_WIDTH, SIDEWALK_WIDTH,
    road_texture, ground_texture, _INTERSECTION_TEX, _SIDEWALK_TEX,
)


class PolygonSpec(NamedTuple):
    bound:          int
    verts:          List[Tuple[float, float, float]]   # 4 game-space (x, y, z) corners
    material_index: int
    cell_type:      int
    hud_color:      str
    texture:        str                                 # "" -> untextured
    tile_x:         float
    tile_y:         float
    angle:          float                               # UV rotation (deg)
    is_spawn:       bool


class CompiledMap(NamedTuple):
    polygons: List[PolygonSpec]
    name:     str


# ── 2D helpers on the ground plane (x, z) ─────────────────────────────────────

def _sub(a, b):  return (a[0] - b[0], a[1] - b[1])
def _add(a, b):  return (a[0] + b[0], a[1] + b[1])
def _mul(a, s):  return (a[0] * s, a[1] * s)
def _len(a):     return math.hypot(a[0], a[1])


def _normalize(a):
    n = _len(a)
    return (a[0] / n, a[1] / n) if n > 1e-9 else (1.0, 0.0)


def _right(direction):
    """Right-hand perpendicular in the ground plane."""
    return (-direction[1], direction[0])


def _quad(p0_xz, p1_xz, p2_xz, p3_xz, y):
    """Four (x, z) corners + a height -> 4 game-space (x, y, z) verts."""
    return [(p[0], y, p[1]) for p in (p0_xz, p1_xz, p2_xz, p3_xz)]


def _heading_deg(direction) -> float:
    return math.degrees(math.atan2(direction[1], direction[0]))


# ── Compilation ───────────────────────────────────────────────────────────────

def compile_mapspec(spec: dict) -> CompiledMap:
    polys: List[PolygonSpec] = []
    nodes = {nid: tuple(pos) for nid, pos in spec.get("nodes", {}).items()}
    roads = spec.get("roads", [])

    # Unique, valid bound numbers: the grass base is the mandatory cell #1; everything
    # else counts up from 201 (0/200/negative/>32767 are illegal per create_polygon).
    counter = [201]

    def next_bound() -> int:
        b = counter[0]
        counter[0] += 1
        if counter[0] == 0 or counter[0] == 200:
            counter[0] += 1
        return b

    # Which nodes actually carry roads (only those get an intersection patch).
    degree: Dict[str, int] = {nid: 0 for nid in nodes}
    for road in roads:
        if road.get("from") in degree:
            degree[road["from"]] += 1
        if road.get("to") in degree:
            degree[road["to"]] += 1

    # ── Grass base (the mandatory bound_number == 1 cell) ─────────────────────
    extent = spec.get("extent") or _auto_extent(nodes)
    xmin, zmin, xmax, zmax = extent
    g_tex = ground_texture(spec.get("ground", {}).get("texture", "grass"))
    polys.append(PolygonSpec(
        bound=1,
        verts=_quad((xmin, zmin), (xmax, zmin), (xmax, zmax), (xmin, zmax), GROUND_Y),
        material_index=Material.GRASS, cell_type=Room.DEFAULT, hud_color=Color.GRASS,
        texture=g_tex, tile_x=max(1.0, (xmax - xmin) / 10.0),
        tile_y=max(1.0, (zmax - zmin) / 10.0), angle=0.0, is_spawn=False,
    ))

    # ── Roads (carriageway + two sidewalks per edge) ──────────────────────────
    for road in roads:
        a = nodes.get(road.get("from"))
        b = nodes.get(road.get("to"))
        if a is None or b is None or a == b:
            continue
        lanes = int(road.get("lanes", 2))
        polys.extend(_road_polys(a, b, lanes, next_bound))

    # ── Intersection patches (one square per node that has roads) ─────────────
    spawn_node = spec.get("spawn", {}).get("node")
    for nid, pos in nodes.items():
        if degree.get(nid, 0) == 0:
            continue
        size = _node_patch_size(nid, roads, nodes)
        polys.append(_intersection_poly(pos, size, next_bound(), is_spawn=(nid == spawn_node)))

    # ── Spawn fallback: if no spawn node, mark the grass base as the spawn ─────
    if not any(p.is_spawn for p in polys):
        polys[0] = polys[0]._replace(is_spawn=True)

    return CompiledMap(polygons=polys, name=spec.get("name", "GeneratedMap"))


def _road_polys(a, b, lanes, next_bound) -> List[PolygonSpec]:
    direction = _normalize(_sub(b, a))
    right     = _right(direction)
    half      = lanes * LANE_WIDTH / 2.0
    length    = _len(_sub(b, a))
    angle     = _heading_deg(direction)
    out: List[PolygonSpec] = []

    # Carriageway
    c_in  = _mul(right, half)
    out.append(PolygonSpec(
        bound=next_bound(),
        verts=_quad(_add(a, c_in), _add(b, c_in), _sub(b, c_in), _sub(a, c_in), ROAD_Y),
        material_index=Material.DEFAULT, cell_type=Room.DEFAULT, hud_color=Color.ROAD,
        texture=road_texture(lanes), tile_x=float(lanes),
        tile_y=max(1.0, length / 10.0), angle=angle, is_spawn=False,
    ))

    # Sidewalk on each side (outer edge of the carriageway -> +SIDEWALK_WIDTH)
    for sign in (1.0, -1.0):
        lo = _mul(right, sign * half)
        ro = _mul(right, sign * (half + SIDEWALK_WIDTH))
        out.append(PolygonSpec(
            bound=next_bound(),
            verts=_quad(_add(a, lo), _add(b, lo), _add(b, ro), _add(a, ro), SIDEWALK_Y),
            material_index=Material.DEFAULT, cell_type=Room.DEFAULT, hud_color=Color.ROAD,
            texture=_SIDEWALK_TEX, tile_x=1.0, tile_y=max(1.0, length / 10.0),
            angle=angle, is_spawn=False,
        ))
    return out


def _node_patch_size(nid, roads, nodes) -> float:
    """Patch covers the widest incident road (carriageway + both sidewalks)."""
    widest = LANE_WIDTH * 2
    for road in roads:
        if nid in (road.get("from"), road.get("to")):
            lanes = int(road.get("lanes", 2))
            widest = max(widest, lanes * LANE_WIDTH + 2 * SIDEWALK_WIDTH)
    return widest


def _intersection_poly(center, size, bound, is_spawn) -> PolygonSpec:
    h = size / 2.0
    cx, cz = center
    return PolygonSpec(
        bound=bound,
        verts=_quad((cx - h, cz - h), (cx + h, cz - h), (cx + h, cz + h), (cx - h, cz + h), ROAD_Y),
        material_index=Material.DEFAULT, cell_type=Room.DEFAULT, hud_color=Color.ROAD,
        texture=_INTERSECTION_TEX, tile_x=2.0, tile_y=2.0, angle=0.0, is_spawn=is_spawn,
    )


def _auto_extent(nodes) -> List[float]:
    if not nodes:
        return [-100.0, -100.0, 100.0, 100.0]
    xs = [p[0] for p in nodes.values()]
    zs = [p[1] for p in nodes.values()]
    pad = 60.0
    return [min(xs) - pad, min(zs) - pad, max(xs) + pad, max(zs) + pad]

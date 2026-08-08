"""
MapSpec — the high-level, declarative description of a Midtown Madness map.

This is the shared contract between the "designer" (a human, an AI writing JSON, or
the procedural generator) and the deterministic compiler that realises it into game
geometry. The designer works at the altitude of intent — a road-network graph + zones
+ rules — never raw polygons. The compiler (compiler.py) guarantees the geometry is
drivable (valid widths, snapped junctions; the pipeline then auto-derives collision
bounds, cells, portals and the .AR).

Coordinates are GAME units, ground plane = (x, z), 1 unit = 1 metre. Nodes are [x, z].

Schema (all keys optional unless noted; Milestone-1 fields marked *):
  name*      : str                       output map name
  extent*    : [xmin, zmin, xmax, zmax]  play-area bounding box (the grass base)
  ground     : {"texture": "grass"}      base fill texture key (see _GROUND_TEX)
  nodes*     : {"id": [x, z], ...}        intersections / road endpoints
  roads*     : [ {"from","to","lanes","median"?,"curve"?}, ... ]   edges between nodes
  spawn*     : {"node": "id"}  or  {"pos": [x, z]}                  player start
  blocks     : [ {"nodes":[...], "fill", "facades", "props"} ]     (later milestones)
  water      : [ {"rect":[x0,z0,x1,z1]} ]                          (later milestones)
  races      : [ {"type","route":[node,...]} ]                      (later milestones)

Use load_spec()/validate_spec() to read + sanity-check before compiling.
"""
import json
from pathlib import Path
from typing import List

# ── Scale (grounded: 1 unit = 1 m; see the scale cheat sheet) ──────────────────
LANE_WIDTH     = 5.0    # game units per lane (cars are ~1.8 wide -> ~2.7x)
SIDEWALK_WIDTH = 2.5
GROUND_Y       = 0.0    # grass base plane
ROAD_Y         = 0.05   # roads/intersections lifted slightly above grass (no z-fight)
SIDEWALK_Y     = 0.15   # sidewalk top (curb step)
MIN_TURN_RADIUS = 5.0   # engine floor; prefer 8-15 for comfortable cornering

# Texture keys -> game texture names (see src/constants/textures.py).
_ROAD_TEX_BY_LANES = {1: "R2", 2: "R4", 3: "R6"}
_DEFAULT_ROAD_TEX  = "R4"
_INTERSECTION_TEX  = "RINTER"
_SIDEWALK_TEX      = "SDWLK2"
_GROUND_TEX        = {"grass": "T_GRASS", "water": "T_WATER", "road": "R4"}


def load_spec(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_spec(spec: dict, path) -> None:
    Path(path).write_text(json.dumps(spec, indent=2), encoding="utf-8")


def validate_spec(spec: dict) -> List[str]:
    """Return a list of problems (empty == valid). Designer-friendly messages."""
    problems: List[str] = []

    nodes = spec.get("nodes", {})
    if not nodes:
        problems.append("no 'nodes' defined")
    for nid, pos in nodes.items():
        if not (isinstance(pos, (list, tuple)) and len(pos) == 2):
            problems.append(f"node '{nid}' must be [x, z]")

    roads = spec.get("roads", [])
    if not roads:
        problems.append("no 'roads' defined")
    for i, road in enumerate(roads):
        for end in ("from", "to"):
            if road.get(end) not in nodes:
                problems.append(f"road #{i} '{end}' = {road.get(end)!r} is not a known node")
        if road.get("from") == road.get("to"):
            problems.append(f"road #{i} connects a node to itself")

    spawn = spec.get("spawn", {})
    if "node" in spawn and spawn["node"] not in nodes:
        problems.append(f"spawn node {spawn['node']!r} is not a known node")
    if "node" not in spawn and "pos" not in spawn:
        problems.append("spawn must specify a 'node' or a 'pos'")

    return problems


def road_texture(lanes: int) -> str:
    return _ROAD_TEX_BY_LANES.get(lanes, _DEFAULT_ROAD_TEX)


def ground_texture(key: str) -> str:
    return _GROUND_TEX.get(key, _GROUND_TEX["grass"])


# A tiny reference spec (a single 4-way block) — handy for tests / examples.
EXAMPLE_SPEC: dict = {
    "name": "ExampleBlock",
    "extent": [-160, -160, 160, 260],
    "ground": {"texture": "grass"},
    "nodes": {"A": [-120, 0], "B": [120, 0], "C": [120, 200], "D": [-120, 200]},
    "roads": [
        {"from": "A", "to": "B", "lanes": 2},
        {"from": "B", "to": "C", "lanes": 2},
        {"from": "C", "to": "D", "lanes": 2},
        {"from": "D", "to": "A", "lanes": 2},
    ],
    "spawn": {"node": "A"},
}

"""
Phase 2 reader: live Blender Road Builder spines (`RS_*`)  ->  plain road dicts  ->  RoadNetwork.

This is the ONLY bpy-touching half of the bridge. It reads each authored spine's geometry +
its cross-section + per-road AI flags, hands them to the Blender-free
`roadnet.road_builder_bridge.roads_to_network`, and returns a `RoadNetwork` that the roadnet
compiler turns into a full drivable city (mesh + AI + traffic + cops + peds).

Wire-up: set `ROADNET_CITY = "blender"` in src/USER/settings/main.py, then build as usual ---
the build calls `blender_roads_network()` here instead of a preset.
"""
from typing import List

import bpy

from src.game.races.constants_2 import IntersectionType
from src.game.mapgen.roadnet.road_builder_bridge import roads_to_network
from src.integrations.blender.operators.road_builder import get_spine_vertices, RS_PREFIX

MIN_SPINE_VERTICES = 2      # a road needs at least a start and an end
DEFAULT_SNAP = 8.0          # metres; spine ends closer than this weld into one junction

# Cross-section fallbacks, used when a spine predates the property (getattr default).
DEFAULT_LANE_COUNT = 2
DEFAULT_LANE_WIDTH = 5.0
DEFAULT_SIDEWALK_WIDTH = 2.5
DEFAULT_CURB_WIDTH = 0.3
DEFAULT_MEDIAN_WIDTH = 1.0


def _scene_bool(name: str, default: bool) -> bool:
    """A scene-level boolean default, for spines authored before the per-road flag existed."""
    return bool(getattr(bpy.context.scene, name, default))


def _scene_yesno(name: str, default: bool) -> bool:
    """Same, for the scene properties stored as a "YES" / "NO" enum rather than a bool."""
    value = getattr(bpy.context.scene, name, None)
    if value is None:
        return default

    return str(value).upper() == "YES"


def _scene_intersection(name: str) -> int:
    """A junction dropdown (INTERSECTION_TYPE_ITEMS) -> IntersectionType.

    The enum stores the IntersectionType number itself, as a string ("3" = Continue), so the value
    only needs parsing --- there is no name-to-number table to keep in sync. Anything unparseable
    falls back to CONTINUE, which is the enum's own first entry and so its Blender default.
    """
    try:
        return int(getattr(bpy.context.scene, name))
    except (AttributeError, TypeError, ValueError):
        return IntersectionType.CONTINUE


def read_road_spines() -> List[dict]:
    """Read every `RS_*` spine object into a plain road dict (see road_builder_bridge)."""
    roads: List[dict] = []

    for spine in bpy.data.objects:
        if not spine.name.startswith(RS_PREFIX):
            continue

        vertices = get_spine_vertices(spine)
        if len(vertices) < MIN_SPINE_VERTICES:
            continue

        # Blender world (x, y, z_up) -> MM1 ground (x, z) == (bl_x, -bl_y)  (see blender_to_game).
        points = [(float(vertex.x), float(-vertex.y)) for vertex in vertices]

        roads.append({
            "points": points,

            # Cross-section, authored per spine.
            "lane_count":     getattr(spine, "rs_lane_count", DEFAULT_LANE_COUNT),
            "lane_width":     getattr(spine, "rs_lane_width", DEFAULT_LANE_WIDTH),
            "sidewalk":       getattr(spine, "rs_sidewalk_enabled", True),
            "sidewalk_side":  getattr(spine, "rs_sidewalk_side", "BOTH"),
            "sidewalk_width": getattr(spine, "rs_sidewalk_width", DEFAULT_SIDEWALK_WIDTH),
            "curb":           getattr(spine, "rs_curb_enabled", True),
            "curb_width":     getattr(spine, "rs_curb_width", DEFAULT_CURB_WIDTH),
            "median":         getattr(spine, "rs_median_enabled", False),
            "median_width":   getattr(spine, "rs_median_width", DEFAULT_MEDIAN_WIDTH),

            # AI flags. The per-spine `rs_ai_*` properties are not registered yet, so today every
            # road takes the scene-wide Road Builder setting; once they exist, each spine wins.
            "two_way":     getattr(spine, "rs_ai_two_way", _scene_bool("rd_ai_two_way", True)),
            "alley":       getattr(spine, "rs_ai_alley", _scene_yesno("rd_ai_alley", False)),
            "isect_start": getattr(spine, "rs_ai_isect_start",
                                   _scene_intersection("rd_ai_intersection_start")),
            "isect_end":   getattr(spine, "rs_ai_isect_end",
                                   _scene_intersection("rd_ai_intersection_end")),
        })

    return roads


def blender_roads_network(snap: float = DEFAULT_SNAP):
    """Read the authored spines and build a RoadNetwork (ready for RoadNetworkCompiler)."""
    roads = read_road_spines()
    if not roads:
        raise RuntimeError("ROADNET_CITY='blender' but no RS_* road spines found in the scene")

    return roads_to_network(roads, snap = snap, name = "BlenderCity")

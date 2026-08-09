"""
Ground-snap for MM2->MM1 prop placement.

WHY THIS EXISTS (measured root cause):
The MM2 city geometry is authored 1:1 into the MM1 frame (mm2_city.transform is identity
for SF/London -- scale=1, y_offset=0, mirror_x=False), and the hand-placed `props.pathset`
trees/signs sit at their real MM2 world Y, so they match the ground to within ~0 delta.

BUT the per-road "density furniture" (street-lights/benches/bins/meters/poles/traffic-lights
from roadnet.scenery.generate_props) is placed at a fixed CURB_HEIGHT plus a COARSE terrain()
estimate -- the nearest BAI road-point Y on a 40 m grid. On hilly SF that estimate is wrong by
metres (median ~-1..-2 m, and a long tail down to ~-100 m where no road point is near), so ~50%
of the ~3,600 furniture props end up half-buried or sunk underground. Measured from the built
MM2SF.BNG: mm2lamp x1740 53% buried (min -112 m), tpmail/tppmtr/tptcanc/tptpole 53-58% buried.

FIX: after the prop_list is assembled, snap every prop's Y to the ACTUAL authored city ground
directly under it (the same triangles the player drives on), so the delta is ~0 by construction.
This fixes the furniture AND any steep-terrain pathset outliers with one pass, using the real
emitted geometry rather than an approximation. Overhead props (hanging banners, freeway exit
gantries, the Ghirardelli sign) keep their raw pathset Y -- see OVERHEAD_KEEP_RAW.

Selection rule (REST SURFACE): among the GROUND polys whose XZ footprint contains the prop, pick
the surface the prop should stand ON -- the HIGHEST ground at-or-just-below the prop's current Y
(allowing a small UP_TOL so a prop sitting a hair high still locks to its surface); if the prop is
BELOW every ground poly (buried, e.g. a tree sunk under the grass), snap UP to the LOWEST ground
above it. This rests furniture on the street/sidewalk, lifts buried trees to the grass, and keeps a
bridge/overpass prop on its deck (the highest ground below it) instead of the road underneath.
Falls back to the nearest ground-poly centroid within `radius`; if nothing is near, keeps the raw Y.

GROUND-CLASS FIX (measured): classifying "ground" by plane-normal ALONE (any near-horizontal poly)
grabbed BUILDING ROOFS/PODIUMS -- 189/436 traffic-lights rode up onto buildings, plus 85/1740 lamps
and 53/320 trees. Building tops are horizontal too, so the normal test alone cannot tell them
apart. We therefore also require the poly's MM2 obj_type to be a GROUND type
(road/sidewalk/terrain/intersection-fan), EXCLUDING facade/sliver/roof/INST-building polys. The
obj_type per poly is threaded in from emit_mm2_city (parallel to the editor's `polys`).
"""
import collections
from typing import List, Dict, Optional

# MM2 obj_type tags (set in mm2_city.Mm2PolySpec) that count as drivable/walkable GROUND a prop may
# rest on. Everything else (facade / sliver / roof_triangle_fan / INST "building" / water) is NOT a
# rest surface -- snapping to a building top is exactly the bug we are fixing.
GROUND_OBJ_TYPES = frozenset({
    "road", "divided_road", "walkway",      # carriageway
    "road_triangle_fan",                    # intersection surface
    "triangle_fan",                         # grass / terrain ground fill  <-- trees rest here
    "sidewalk_strip", "crosswalk",          # sidewalk
})

# A prop sitting up to this far ABOVE a ground poly still counts as "resting on" it (curb lips,
# slightly-high terrain estimates). Beyond this, a higher candidate must lie below the prop to win.
REST_ON_TOLERANCE = 0.6

SNAP_EPSILON   = 1e-4   # below this the prop is already on the ground; leave it alone
BADLY_PLACED_Y = 0.5    # reported separately: clearly buried or floating before the snap

# Prop ids (MM1 banger names OR Mm2Prop/Prop enum values) that are intentionally ELEVATED in the
# pathset (overhead banners / exit-sign gantries / the big Ghirardelli sign) -- never snap these to
# the street, or they drop out of the sky. Matched case-insensitively against str(prop_id).
OVERHEAD_KEEP_RAW = {
    "mm2bannerblu", "mm2bannerred", "mm2banneryel",
    "mm2exitcc", "mm2exitemb", "mm2exitgg", "mm2exitmar", "mm2exittb",
    "mm2gdelli",
}

GRID_SIZE = 30.0   # spatial-hash cell size (m)


def _poly_xz_verts(poly, vertices):
    """The poly's own vertices as (x, y, z) tuples, in winding order."""
    return [(vertices[index].x, vertices[index].y, vertices[index].z)
            for index in poly.vertex_index[:poly.num_verts]]


def _point_in_xz(px, pz, verts) -> bool:
    """Even-odd point-in-polygon on the XZ projection (3 or 4 verts).

    Walks each edge (previous -> current) and counts the ones the +X ray from (px, pz) crosses;
    an odd count means the point is inside.
    """
    inside = False
    previous = len(verts) - 1

    for current in range(len(verts)):
        x0, z0 = verts[current][0], verts[current][2]
        x1, z1 = verts[previous][0], verts[previous][2]

        spans_the_ray = (z0 > pz) != (z1 > pz)
        if spans_the_ray and px < (x1 - x0) * (pz - z0) / (z1 - z0 + 1e-12) + x0:
            inside = not inside
        previous = current

    return inside


def _plane_y(px, pz, verts) -> Optional[float]:
    """Y of the poly's plane at (px, pz), fit from its first 3 vertices.

    Returns None for a plane that is edge-on in Y (normal.y ~ 0), where the height at a given XZ
    is undefined and the division below would blow up.
    """
    origin, second, third = verts[0], verts[1], verts[2]
    edge_a = (second[0] - origin[0], second[1] - origin[1], second[2] - origin[2])
    edge_b = (third[0] - origin[0], third[1] - origin[1], third[2] - origin[2])

    normal_y = edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2]
    if abs(normal_y) < 1e-9:
        return None

    normal_x = edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1]
    normal_z = edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0]

    return origin[1] - (normal_x * (px - origin[0]) + normal_z * (pz - origin[2])) / normal_y


def build_ground_index(vertices, polys, min_ny: float = 0.3, obj_types=None):
    """Spatial hash of near-horizontal GROUND polys for fast XZ->Y lookup.
    Returns (grid, polys_xz) where grid maps (gx,gz)->list of poly indices.

    `obj_types`, when given, is a list parallel to `polys` (obj_types[i] = MM2 type of polys[i], or
    None). Only polys whose type is in GROUND_OBJ_TYPES are indexed -- this is what keeps building
    roofs/podiums/facades OUT of the rest-surface search (BUG A/B). If obj_types is None we fall back
    to the old plane-normal-only behaviour (e.g. non-MM2 callers)."""
    grid = collections.defaultdict(list)
    store = []   # (xz_verts, centroid_x, centroid_y, centroid_z)

    for i, poly in enumerate(polys):
        if obj_types is not None:
            obj_type = obj_types[i] if i < len(obj_types) else None
            if obj_type not in GROUND_OBJ_TYPES:    # skip building roofs/facades/water/filler
                continue

        plane_normal = poly.plane_normal
        if plane_normal is None or abs(plane_normal.y) < min_ny:
            continue

        verts = _poly_xz_verts(poly, vertices)
        if len(verts) < 3:
            continue

        centroid_x = sum(v[0] for v in verts) / len(verts)
        centroid_y = sum(v[1] for v in verts) / len(verts)
        centroid_z = sum(v[2] for v in verts) / len(verts)
        poly_index = len(store)
        store.append((verts, centroid_x, centroid_y, centroid_z))

        # Register the poly in EVERY grid cell its XZ bounding box overlaps, so containment
        # lookups never miss a poly that straddles a cell boundary.
        min_gx = int(min(v[0] for v in verts) // GRID_SIZE)
        max_gx = int(max(v[0] for v in verts) // GRID_SIZE)
        min_gz = int(min(v[2] for v in verts) // GRID_SIZE)
        max_gz = int(max(v[2] for v in verts) // GRID_SIZE)
        for grid_x in range(min_gx, max_gx + 1):
            for grid_z in range(min_gz, max_gz + 1):
                grid[(grid_x, grid_z)].append(poly_index)

    return grid, store


def ground_y(grid, store, px, pz, cur_y, radius: float = 22.0):
    """Best REST-surface Y under (px,pz); else the nearest ground centroid within `radius`; else
    None (caller keeps the original Y).

    Rest rule among the GROUND polys whose footprint contains (px,pz):
      * if any sit at-or-just-below the prop (plane_y <= cur_y + REST_ON_TOLERANCE), take the HIGHEST of those
        -- the surface the prop stands on (street/sidewalk/deck), never a road buried under a bridge;
      * else the prop is below all of them (buried, e.g. a tree under the grass) -> take the LOWEST
        ground above it, lifting it onto the nearest real surface.
    This both pulls building-stranded props DOWN to the street (we no longer index building tops) and
    pushes buried props UP to the grass/road. Containment is exact (a poly is registered in every grid
    cell it overlaps). The centroid fallback catches furniture placed just OFF the tessellated ground
    (BAI-graph XZ vs PSDL roads) by snapping to the nearest ground edge instead of a hillside."""
    grid_x, grid_z = int(px // GRID_SIZE), int(pz // GRID_SIZE)
    cell_radius = int(radius // GRID_SIZE) + 1

    best_below = None                       # highest ground at-or-just-below cur_y
    best_above = None                       # lowest ground above cur_y (used only if nothing below)
    nearest_y = None
    nearest_distance = radius * radius
    seen = set()

    for dx in range(-cell_radius, cell_radius + 1):
        for dz in range(-cell_radius, cell_radius + 1):
            for poly_index in grid.get((grid_x + dx, grid_z + dz), ()):
                if poly_index in seen:
                    continue                # a poly spans several cells; only weigh it once
                seen.add(poly_index)

                verts, center_x, center_y, center_z = store[poly_index]
                if _point_in_xz(px, pz, verts):     # prop sits directly over this ground poly
                    y = _plane_y(px, pz, verts)
                    if y is None:
                        continue

                    if y <= cur_y + REST_ON_TOLERANCE:
                        if best_below is None or y > best_below:
                            best_below = y          # keep the HIGHEST surface at/below the prop
                    elif best_above is None or y < best_above:
                        best_above = y              # keep the LOWEST surface above the prop

                else:                               # off-ground: remember the nearest ground edge
                    distance = (center_x - px) ** 2 + (center_z - pz) ** 2
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_y = center_y

    if best_below is not None:
        return best_below
    if best_above is not None:
        return best_above

    return nearest_y   # may be None


def snap_props(prop_list: List[Dict], vertices, polys, *, obj_types=None, log=None) -> dict:
    """Snap each prop's offset Y to the authored GROUND under it (in place). Overhead props keep
    their raw Y. `obj_types` (list parallel to `polys`) restricts snapping to true ground surfaces,
    excluding building roofs/podiums -- pass it for MM2 cities (BUG A/B). Returns a stats dict; if
    `log` is given it's called with a one-line summary."""
    grid, store = build_ground_index(vertices, polys, obj_types = obj_types)

    moved = snapped = kept_overhead = no_ground = 0
    badly_placed = 0                    # props more than BADLY_PLACED_Y off the ground beforehand

    for prop in prop_list:
        offset = prop.get("offset")
        if not offset:
            continue

        if str(prop.get("name", "")).lower() in OVERHEAD_KEEP_RAW:
            kept_overhead += 1
            continue

        x, y, z = offset[0], offset[1], offset[2]
        ground = ground_y(grid, store, x, z, y)
        if ground is None:
            no_ground += 1
            continue

        snapped += 1
        distance_off_ground = abs(y - ground)

        if distance_off_ground > BADLY_PLACED_Y:
            badly_placed += 1
        if distance_off_ground > SNAP_EPSILON:
            moved += 1
            prop["offset"] = (x, ground, z)

    stats = {"total": len(prop_list), "snapped": snapped, "moved": moved,
             "kept_overhead": kept_overhead, "no_ground": no_ground,
             "buried_or_floating_before": badly_placed, "ground_polys": len(store)}
    if log:
        log("ground-snap: %d/%d props snapped to authored ground (%d moved, %d were >0.5m off, "
            "%d overhead kept, %d had no ground under them)" %
            (snapped, stats["total"], moved, badly_placed, kept_overhead, no_ground))

    return stats

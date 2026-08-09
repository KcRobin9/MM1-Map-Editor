"""
MM2 `<city>/props.pathset` (PTH1) -> explicit prop instances for MM1 bangers.

The pathset is MM2's authoritative HAND-PLACED scenery list (trees, palms, lamps, benches,
signs, railings) with real world coords + facing -- unlike sf.inst (buildings only) and the
propdefs/proprules CSVs (procedural, no coords). Format (angel-file-formats Pathset.md):

    Pathset { char[4] = "PTH1"; u32 nPaths; u32 currentPath; Path paths[nPaths]; }
    Path    { char[32] name (0-padded); u32 nPoints; u32 unknown1;
              Point points[nPoints]; u8 type; u8 spacing; char pad[2]; }
    Point   { u32 unknown2; float x; float y; float z; }      # 16 bytes, y = world height

type 0 = Single Points (one prop per point, no facing)
type 1 = Directed Points (points are pairs: p0=pos, p1=facing target -> angle = dir(p1-p0))
type 2 = Line Strip (props every `spacing` m along each segment, facing = segment tangent)
spacing is in 1/4-metre units -> metres = spacing/4.

Coords go straight into MM1 banger offset (world frame matches MM2, no mirror -- verified).
"""
import math
import collections
from typing import List, Dict

from src.constants.mm2 import MM2_PATHSET_PROP
from src.constants.file_formats import Magic
from src.io.binary import read_unpack
from .mm2_props import _build_model_map as shared_model_map

PATH_SINGLE_POINTS   = 0    # one prop per point, no facing
PATH_DIRECTED_POINTS = 1    # points are pairs: position then facing target
PATH_LINE_STRIP      = 2    # props every `spacing` m along each segment, facing the tangent

PATH_HEADER_BYTES = 40      # 32-byte name + u32 nPoints + u32 unknown
PATH_NAME_BYTES   = 32
POINT_BYTES       = 16      # u32 unknown + 3 x f32
MAX_SANE_POINTS   = 200000  # a corrupt count would otherwise run off the end of the file

SPACING_UNITS_PER_METRE = 4.0   # the `spacing` byte is in quarter-metres


def parse_pathset(path: str) -> List[Dict]:
    """Parse a PTH1 pathset. Returns [{name, type, spacing_m, points:[(x,y,z)]}].
    Defensive: stops cleanly if a path's header looks corrupt rather than reading garbage."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)

        magic = f.read(4)
        if magic.decode("latin-1") != Magic.MM2_PROPS:
            raise ValueError("not a PTH1 pathset: %r" % magic)

        n_paths, _ = read_unpack(f, "<2I")
        out: List[Dict] = []

        for _ in range(n_paths):
            if f.tell() + PATH_HEADER_BYTES > size:
                break

            name = f.read(PATH_NAME_BYTES).split(b"\x00")[0].decode("latin-1", "replace").strip()

            n_points, _ = read_unpack(f, "<2I")
            if n_points > MAX_SANE_POINTS or f.tell() + n_points * POINT_BYTES + 4 > size:
                break                               # a corrupt count would run off the file

            points = []
            for _ in range(n_points):
                _, x, y, z = read_unpack(f, "<I3f")
                points.append((x, y, z))

            path_type, spacing = read_unpack(f, "<2B")
            f.seek(2, 1)                            # pad
            out.append({"name": name, "type": path_type,
                        "spacing_m": spacing / SPACING_UNITS_PER_METRE, "points": points})

    return out


def _heading_deg(dx: float, dz: float) -> float:
    # MM1 banger angle: degrees in XZ, 0deg=+X increasing toward +Z (matches BangerEditor).
    return math.degrees(math.atan2(dz, dx))


# Some line-strip props read better at a fixed step than the pathset's own spacing -- e.g. the
# freeway railings become a CONTINUOUS wall when wall segments (~5m wide) are placed every ~4.5m.
STEP_OVERRIDE = {"r4i_rails_f": 4.5}


def expand_paths(paths: List[Dict]) -> List[Dict]:
    """Expand parsed paths into flat prop instances [{model, x, y, z, angle}] (model = raw MM2
    name, still to be mapped to an MM1 placeholder). Mirrors MM2's BangerManager placement."""
    instances: List[Dict] = []

    for path in paths:
        name, path_type, points = path["name"], path["type"], path["points"]
        step = STEP_OVERRIDE.get(name, max(1.0, path["spacing_m"]))
        if not points:
            continue

        if path_type == PATH_SINGLE_POINTS:
            for (x, y, z) in points:
                instances.append({"model": name, "x": x, "y": y, "z": z, "angle": 0.0})

        elif path_type == PATH_DIRECTED_POINTS:
            # Points come in pairs: the first is the position, the second the facing target.
            for i in range(0, len(points) - 1, 2):
                (x, y, z), (target_x, _, target_z) = points[i], points[i + 1]
                instances.append({"model": name, "x": x, "y": y, "z": z,
                                  "angle": _heading_deg(target_x - x, target_z - z)})

        elif path_type == PATH_LINE_STRIP:
            # Place one prop every `step` metres along each segment, facing the segment tangent.
            for (start_x, start_y, start_z), (end_x, end_y, end_z) in zip(points, points[1:]):
                delta_x, delta_y, delta_z = end_x - start_x, end_y - start_y, end_z - start_z
                segment_length = math.hypot(delta_x, delta_z)
                if segment_length < 1e-3:
                    continue

                angle = _heading_deg(delta_x, delta_z)
                step_count = max(1, int(segment_length / step))
                for index in range(step_count):
                    fraction = index / float(step_count)
                    instances.append({"model": name,
                                      "x": start_x + delta_x * fraction,
                                      "y": start_y + delta_y * fraction,
                                      "z": start_z + delta_z * fraction,
                                      "angle": angle})

    return instances


def pathset_props(path: str, only_models=None):
    """Parse + expand + map a city props.pathset to MM1 banger prop_list dicts ready for
    BangerEditor: [{"name": prop_id, "offset": (x,y,z), "angle": deg, "flags": int}].
    `only_models` = optional set of MM2 model names to keep (for a verification slice).
    Returns (prop_list, skipped_counter). Models with no sensible MM1 placeholder
    (railings, freeway pillars, dock cleats, banners, hotdog carts, highway exit signs) are
    skipped -- this is the PLACEHOLDER pass (approach A): nail locations + angles first."""
    prop_map = dict(MM2_PATHSET_PROP)
    # UNION with the shared density-furniture model map (mm2_props._build_model_map) so pathsets from
    # OTHER cities (NY as_sp_*, BA *bsas/_ba variants) resolve without duplicating alias tables.
    # Pathset-specific entries above take precedence (they carry pathset-tuned flags/skips).
    prop_map = {**shared_model_map(), **prop_map}
    # ── DIRECTED-PROP FACING (MM2 -> MM1, log-verified) ───────────────────────────────────────────
    # The hand-placed type-1 BENCH (sp_benchwood_f) stores p1 = the SEAT-facing target (verified: the
    # p1-p0 vectors point ~3 m across the sidewalk toward the road). The banger matrix aligns the mesh
    # -local +X axis to (p1-p0), but the bench seat is on the mesh's -X side (backrest at pkg +X), so
    # without a flip the seat would face the BUILDING. Add 180 deg so the seat faces the target (road),
    # matching the density bench (mm2_props). Long axis (pkg +Z) stays along the road either way.
    SEAT_FLIP_MODELS = {"sp_benchwood_f"}
    out = []
    skipped = collections.Counter()

    for instance in expand_paths(parse_pathset(path)):
        model = instance["model"]
        if only_models is not None and model not in only_models:
            continue

        mapped = prop_map.get(model)
        if not mapped:
            skipped[model] += 1
            continue

        prop_id, flags = mapped
        angle = instance["angle"] + (180.0 if model in SEAT_FLIP_MODELS else 0.0)
        out.append({"name": prop_id, "offset": (instance["x"], instance["y"], instance["z"]),
                    "angle": angle, "flags": flags})

    return out, skipped


if __name__ == "__main__":
    import sys

    paths = parse_pathset(sys.argv[1])
    print("[Pathset] paths parsed: %d" % len(paths))
    print("[Pathset] by type:", dict(collections.Counter(p["type"] for p in paths)))

    models = collections.Counter()
    for path in paths:
        models[path["name"]] += len(path["points"])

    print("[Pathset] distinct models: %d" % len(models))
    for model, count in models.most_common(40):
        print("   %-26s pts=%d" % (model, count))

    print("[Pathset] expanded instances: %d" % len(expand_paths(paths)))

"""
MM2 `<city>/props.pathset` (PTH1) -> explicit prop instances for MM1 bangers.

The pathset is MM2's authoritative HAND-PLACED scenery list (trees, palms, lamps, benches,
signs, railings) with real world coords + facing -- unlike sf.inst (buildings only) and the
propdefs/proprules CSVs (procedural, no coords). Format (angel-file-formats Pathset.md):

    Pathset { char[4] = "PTH1"; u32 nPaths; u32 currentPath; Path paths[nPaths]; }
    Path    { char[32] name (0-padded); u32 nPoints; u32 unknown1;
              Point points[nPoints]; u8 type; u8 spacing; char pad[2]; }
    Point   { u32 unknown2; float x; float y; float z; }      # 16 bytes, y = world height

Placement is 1:1 with MM2's dgPath::Enumerate (midtown2.exe 0x466D40, disassembled):
type 0 = Single Points: identity matrix, m3 = point            -> angle 0 (mesh +X = world +X)
type 1 = Directed Points: pairs (p0, p1); m0 = normalize(p1-p0 with y=0), m2 = up x m0, m3 = p0
                          -> angle = atan2(dz, dx) of (p1-p0)  (mesh +X toward p1, as MM1 banger.cpp)
type 2 = Line Strip: per segment d = p[i+1]-p[i], len = |d| (3-D); n = floor(len/spacing);
                          props at p[i] + k*(d/n) for k = 0..n-1 (NONE when len < spacing); m0 = d/|d|
                          -> angle = atan2(d.z, d.x)
dgPath::Load: spacing = byte * 0.25 m, and a 0 byte means 5.0 m.

Coords go straight into MM1 banger offset (world frame matches MM2, no mirror -- verified).
"""
import math
import collections
from typing import List, Dict

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

SPACING_UNITS_PER_METRE = 4.0   # the `spacing` byte is in quarter-metres (dgPath::Load: byte * 0.25)
DEFAULT_SPACING_M = 5.0         # dgPath::Load substitutes 5.0 m for a zero spacing


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
            spacing_m = spacing / SPACING_UNITS_PER_METRE
            out.append({"name": name, "type": path_type,
                        "spacing_m": spacing_m if spacing_m > 0.0 else DEFAULT_SPACING_M,
                        "points": points})

    return out


def _heading_deg(dx: float, dz: float) -> float:
    # MM1 banger angle: degrees in XZ, 0deg=+X increasing toward +Z (matches BangerEditor).
    return math.degrees(math.atan2(dz, dx))


def expand_paths(paths: List[Dict]) -> List[Dict]:
    """Expand parsed paths into flat prop instances [{model, x, y, z, angle}] (model = raw MM2
    name, still to be mapped to its converted Mm2Prop). 1:1 with dgPath::Enumerate (module doc)."""
    instances: List[Dict] = []

    for path in paths:
        name, path_type, points = path["name"], path["type"], path["points"]
        spacing = path["spacing_m"]
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
            # dgPath::Enumerate: n = floor(len3D / spacing) props per segment at p0 + k*(d/n), the
            # segment END is never placed (the next segment starts there); len < spacing -> none.
            for (start_x, start_y, start_z), (end_x, end_y, end_z) in zip(points, points[1:]):
                delta_x, delta_y, delta_z = end_x - start_x, end_y - start_y, end_z - start_z
                segment_length = math.sqrt(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z)
                if segment_length < spacing or math.hypot(delta_x, delta_z) < 1e-9:
                    continue

                angle = _heading_deg(delta_x, delta_z)
                step_count = int(segment_length / spacing)
                for index in range(step_count):
                    fraction = index / float(step_count)
                    instances.append({"model": name,
                                      "x": start_x + delta_x * fraction,
                                      "y": start_y + delta_y * fraction,
                                      "z": start_z + delta_z * fraction,
                                      "angle": angle})

    return instances


def pathset_props(path: str, only_models=None):
    """Parsed + expanded + mapped props.pathset -> (prop_list, skipped_counter).

    prop_list is BangerEditor-ready: [{"name", "offset": (x,y,z), "angle": deg, "flags"}].
    only_models keeps just those MM2 model names, for a verification slice.
    """
    # The angle is the raw MM2 one, with NO per-model offset: both engines align mesh-local +X to the
    # facing vector (banger.cpp:380 == dgPath::Enumerate) and the mesh IS the MM2 mesh, so whatever
    # MM2 shows, MM1 shows. Skips are the documented no-mesh models only.
    prop_map = shared_model_map()
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
        out.append({"name": prop_id, "offset": (instance["x"], instance["y"], instance["z"]),
                    "angle": instance["angle"], "flags": flags})

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

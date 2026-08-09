"""
1:1 reproduction of Midtown Madness 2's PROCEDURAL street-furniture placement.

MM2 places street furniture (lamps, meters, benches, bins, news boxes, signs, trees, ...) by
walking PROP RULES along every road's two sidewalks. The rules live in three places:

  * `<city>/propdefs.csv`   one row per furniture KIND:
        name,start,distance,maxUse,minLerp,maxLerp,file1..file4
        start    = arc-length (m) of the FIRST instance along the road sidewalk
        distance = spacing (m) between consecutive instances (<=0 -> place nothing)
        maxUse   = max instances per road-side (9999 = unlimited)
        minLerp/maxLerp = lateral lerp fraction across the sidewalk (0=curb, 1=building);
                          rnd(min,max) -- but EVERY MM2 row has min==max, so this is exact.
        file1..4 = .pkg model name(s); one is picked per instance (rnd(0,nMeshes)).
  * `<city>/proprules.csv`  one row per ROAD-SIDE:  rulename,prop1..prop8
        rulename = "n{NN}left" | "n{NN}right"  (NN = the rule-pair number)
        prop1..8 = furniture KIND names placed on that sidewalk (each walked independently).
  * the `.psdl`             links each Road room to a rule-pair number (the `propRule` byte) and
        groups road blocks into whole roads (the `paths`/roadBlocks list). roomFlags bit3 = Road.

ALGORITHM (per road, per side -- faithful to wilkovatch/km2-city-builder RoadGenerator.PlacePropsLane
+ GeometryHelper.GetPointAndDirOnSidewalk + km2cb-mm2-core props/psdl.json placementRules):

  inLine  = the CURB-edge polyline of the sidewalk (road side)
  outLine = the BUILDING-edge polyline (back of the sidewalk)
  midLine[i] = (inLine[i] + outLine[i]) / 2 ;  totalLength = arclength(midLine)
  for each furniture KIND on the side, walk i = 0,1,2,...:
      z = (i==0 ? start : lastZ + distance)
      place WHILE  distance > 0  AND  i < maxUse  AND  z <= totalLength :
          pMid = point at arclength z along midLine
          pIn  = closest point on inLine  to pMid ;  pOut = closest point on outLine to pMid
          pos  = lerp(pIn, pOut, rnd(minLerp,maxLerp))          # lateral across the sidewalk
          dir  = normalize(pIn - pOut)                          # across the road, toward the curb
          fwd  = normalize(cross(down, dir))                    # ALONG the road tangent
          angle = signedAngle(+Z, fwd, +Up)                     # props face along the road
          emit { name: mm1(model), offset:(pos.x, pos.y, pos.z), angle }

Output: editor prop-dicts {name, offset:(x,y,z), angle, flags} -- the SAME shape generate_props
returns (consumed by BangerEditor). Y is the sidewalk Y here; the groundsnap pass refines it.

Coordinate frame: the MM2 city is authored 1:1 into the MM1 frame (mm2_city.transform is identity
for SF/London -- scale 1, no mirror), and the hand-placed props.pathset uses MM1 angle
= atan2(dz,dx) and goes straight in (verified in-game). So we emit the same: world (x,z) pass
through unchanged and angle = degrees(atan2(fwd.z, fwd.x)).
"""
import json
import math
import zlib
import random
import collections
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.io.binary import read_unpack
from src.constants.file_formats import Magic
from src.constants.props import Prop, BangerFlags
from src.constants.custom_props.mm2_props import Mm2Prop
from .bai import parse_bai_full

# BAI road-end vehicleRule: 3 = signalized (place a light), 0/1 = uncontrolled/stop (none).
VEHICLE_RULE_SIGNALIZED = 3

FLOAT_BYTES           = 4
VERTEX_BYTES          = 12    # 3 x f32
VECTOR_BYTES          = 12
CROSSROAD_BYTES       = 8     # 4 x u16
PERIMETER_POINT_BYTES = 4     # 2 x u16


# ── .psdl rule-data parser (roomFlags / propRule / paths only -- no geometry decode) ──────────────
# The geometry (road cross-section vertexRefs) already lives in raw_psdl.json; we only need the three
# tail sections the importer historically dropped. This walks the file exactly like psdl_import.py.

def parse_psdl_rules(psdl_path: str) -> dict:
    """Read the three tail sections psdl-import drops: per-room flags, prop rules, and road paths.

    Geometry is skipped, not decoded -- it already lives in raw_psdl.json. Section order and sizes
    follow angel-file-formats 'PSDL.md'.
    """
    with open(psdl_path, "rb") as f:
        magic = f.read(4)
        if magic.decode("latin-1") != Magic.MM2_GEOMETRY:
            raise ValueError("not a PSDL file: %r" % magic)

        def read_byte() -> int:
            value, = read_unpack(f, "<B")
            return value

        def skip_string() -> None:
            f.seek(read_byte(), 1)          # the length byte counts the terminator

        f.seek(4, 1)                                                # targetSize
        n_vertices, = read_unpack(f, "<I")
        f.seek(n_vertices * VERTEX_BYTES, 1)
        n_floats, = read_unpack(f, "<I")
        f.seek(n_floats * FLOAT_BYTES, 1)

        n_textures, = read_unpack(f, "<I")
        for _ in range(n_textures - 1):
            skip_string()

        n_rooms, = read_unpack(f, "<I")
        f.seek(4, 1)                                                # unknown0
        for _ in range(n_rooms - 1):
            n_perimeter_points, attribute_size = read_unpack(f, "<2I")
            f.seek(n_perimeter_points * PERIMETER_POINT_BYTES, 1)
            f.seek(attribute_size * 2, 1)                           # attributes, kept raw

        room_flags = [read_byte() for _ in range(n_rooms)]
        prop_rules = [read_byte() for _ in range(n_rooms)]
        f.seek(3 * VECTOR_BYTES + FLOAT_BYTES, 1)                   # bbox min/max, centre, radius

        n_paths, = read_unpack(f, "<I")
        paths = []
        for _ in range(n_paths):
            f.seek(4, 1)                                            # unknown4, unknown5

            lanes_forward = read_byte()
            lanes_backward = read_byte()
            f.seek((lanes_forward + lanes_backward) * FLOAT_BYTES, 1)   # per-lane density floats

            f.seek(2, 1)                                            # unknown6
            f.seek(2 * CROSSROAD_BYTES, 1)                          # start / end crossroads

            n_road_blocks = read_byte()
            road_blocks = list(read_unpack(f, f"<{n_road_blocks}H"))

            paths.append({"nFLanes": lanes_forward, "nBLanes": lanes_backward,
                          "roadBlocks": road_blocks})

    return {"roomFlags": room_flags, "propRule": prop_rules, "paths": paths}



def patch_raw_psdl(raw_path: str, psdl_path: str) -> dict:
    """Inject roomFlags/propRule/paths into an existing raw_psdl.json (in place) so the importer's
    single shipped JSON carries the rule bytes. Returns the parsed rule data."""
    rules = parse_psdl_rules(psdl_path)
    with open(raw_path, "r") as f:
        raw = json.load(f)
    raw["roomFlags"] = rules["roomFlags"]
    raw["propRule"] = rules["propRule"]
    raw["paths"] = rules["paths"]
    with open(raw_path, "w") as f:
        json.dump(raw, f)
    return rules


# ── MM2 .pkg model name -> MM1 banger prop id ────────────────────────────────────────────────────
# Reuses the real converted MM2 prop meshes (Mm2Prop) where they exist, else the nearest MM1
# placeholder (Prop). Lights get the GLOW flag. Anything not listed is skipped + logged.

def _build_model_map():
    BRK = BangerFlags.BREAKABLE
    GLOW = BangerFlags.BREAKABLE_GLOW

    return {
        # ── San Francisco ────────────────────────────────────────────────────────────────────
        "sp_lightstreet_f":      (Prop.LIGHT_SIDEWALK, GLOW),
        "sp_lightbanrb_f":       (Mm2Prop.LAMP, GLOW),        # banner street lamp (real MM2 mesh)
        "sp_lightbanrg_f":       (Mm2Prop.LAMP, GLOW),
        "sp_lightbanr_rainbo_f": (Mm2Prop.LAMP, GLOW),
        "sp_lightpark_f":        (Mm2Prop.LIGHT_PARK, GLOW),  # real MM2 park lamp
        "sp_chinalight_f":       (Prop.LIGHT_SIDEWALK, GLOW),
        "sp_mailbox_f":          (Mm2Prop.MAIL, BRK),         # real MM2 mailbox
        "sp_parkmtr_f":          (Prop.PARKING_METER, BRK),
        "sp_hotdogcart_f":       (Mm2Prop.HOTDOG, BRK),       # real MM2 food cart
        "sp_can_gen_f":          (Prop.BIN, BRK),
        "sp_recycle_can_f":      (Prop.BIN, BRK),
        "sp_dumpstr_f":          (Mm2Prop.DUMPSTER, BRK),     # real MM2 dumpster
        "sp_newsblue_f":         (Prop.NEWSPAPER_BOX_BLUE, BRK),
        "sp_newsred_f":          (Prop.NEWSPAPER_BOX_RED, BRK),
        "sp_newsyelw_f":         (Prop.NEWSPAPER_BOX_YELLOW, BRK),
        "sp_benchwood_f":        (Mm2Prop.BENCH, BRK),        # real MM2 bench
        "sp_phonestand_f":       (Prop.PAYPHONE, BRK),
        "sp_traflitsingle_f":    (Prop.TRAFFIC_LIGHT_SINGLE, BRK),
        "sp_traflitdual_f":      (Prop.TRAFFIC_LIGHT_DUAL, BRK),
        "sp_cone_f":             (Prop.CONE, BRK),
        "sp_callbox_f":          (Prop.CALLBOX_EMERGENCY, BRK),
        "sp_telephonepole_f":    (Prop.TELEPHONE_POLE, BRK),
        "sp_chinagate_f":        (Prop.CHINATOWN_GATE, BRK),
        "sp_busstop_f":          (Prop.BUS_STOP, BRK),
        "sp_tree1_s":            (Mm2Prop.TREE, BRK),         # real MM2 tree billboard
        "sp_wrongwayfw":         (Mm2Prop.WRONGWAY, BRK),     # real MM2 wrong-way sign
        "sp_noprk_f":            (Prop.SIGN_DO_NOT_ENTER, BRK),  # no MM1 "no parking" -> sign placeholder
        # ── London ───────────────────────────────────────────────────────────────────────────
        "sp_lightstreet_l":      (Prop.LIGHT_SIDEWALK, GLOW),
        "sp_light_tall_l":       (Prop.LIGHT_HIGHWAY, GLOW),
        "sp_lightthames_l":      (Mm2Prop.LIGHT_THAMES, GLOW),  # real London Thames lamp
        "sp_dumpstr_l":          (Mm2Prop.DUMPSTER_L, BRK),     # real London dumpster
        "sp_can_royal_l":        (Prop.BIN, BRK),
        "sp_mailbox_l":          (Prop.MAILBOX, BRK),
        "sp_newsgroup01_l":      (Prop.NEWSPAPER_BOX_BLUE, BRK),
        "sp_phonebooth_l":       (Prop.PHONE_BOOTH, BRK),       # red phone booth
        # ── New York (as_manhattan, player-made; stock sp_* names + a few as_sp_* customs) ─────
        "sp_crashcan_f":          (Prop.BIN, BRK),
        "sp_speed65_f":           (Mm2Prop.HILLWARN, BRK),      # speed-limit sign -> warn-sign placeholder
        "as_sp_garbage01_m":      (Prop.BIN, BRK),
        "as_sp_garbage02_m":      (Prop.BIN, BRK),
        "as_sp_homelessbox_m":    (Mm2Prop.BOXCARD, BRK),
        "as_sp_sign_noparking_m": (Prop.SIGN_DO_NOT_ENTER, BRK),
        # ── Buenos Aires (bsas, player-made; *_bsas/_ba variants of familiar props) ────────────
        "sp_lightstreet_bsas":     (Mm2Prop.LAMP, GLOW),
        "sp_lightstreet_bsas_hwy": (Prop.LIGHT_HIGHWAY, GLOW),
        "sp_bg_lightstreet_bsas2": (Mm2Prop.LAMP, GLOW),
        "sp_lightpark_bsas":       (Mm2Prop.LIGHT_PARK, GLOW),
        "bsas_farol_4":            (Mm2Prop.LIGHT_PARK, GLOW),  # farol = lantern
        "sp_bigtree1_bsas":        (Mm2Prop.TREE, BRK),
        "sp_tree1_ba":             (Mm2Prop.TREE, BRK),
        "sp_tree5_s":              (Mm2Prop.TREE, BRK),
        "sp_tree6_s":              (Mm2Prop.TREE6, BRK),
        "sp_treejacaranda_ba":     (Mm2Prop.TREE, BRK),
        "sp_palm1_bsas":           (Mm2Prop.PALM, BRK),
        "bsas_dumpster":           (Mm2Prop.DUMPSTER, BRK),
        "sp_light_white_f":        (Prop.LIGHT_SIDEWALK, GLOW),
        # deliberately unmapped (skipped + counted): giz_pcar* parked-car gizmos, cafe furniture /
        # kiosks / billboards / subway entrances (bsas_mesa_*, bsas_kioscodiarios,
        # sp_carapantalla_bsas, sp_subwayen_bsas_s) — no sensible placeholder; needs real converted
        # meshes (build_custom_props) in a later 1:1 pass.
    }


# ── small geometry helpers (mirror km2cb GeometryHelper) ──────────────────────────────────────────

def _path_length(pts) -> float:
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def _point_on_path(pts, z):
    """Point at arc-length z along the polyline (km2cb GetPointOnPath)."""
    cur = 0.0
    for i in range(len(pts) - 1):
        seg = math.dist(pts[i], pts[i + 1])
        if seg > 1e-9 and cur + seg >= z:
            a = (z - cur) / seg
            return tuple(pts[i][k] + (pts[i + 1][k] - pts[i][k]) * a for k in range(3))
        cur += seg
    return pts[-1]


def _finite3(p) -> bool:
    """True iff all 3 components of a point/vector are finite (no NaN / inf)."""
    return (math.isfinite(p[0]) and math.isfinite(p[1]) and math.isfinite(p[2]))


def _walkable(pts) -> bool:
    """True iff the polyline can support an arclength walk: >= 2 FINITE points that are not all
    coincident (i.e. there is at least one non-zero-length segment). Used only to DECIDE whether to
    skip a side -- it does NOT rewrite/reindex the polyline (the curb/building/mid lines are paired
    by row index, so dropping/dedup'ing points would desync it and shift VALID positions)."""
    finite = [p for p in pts if _finite3(p)]
    if len(finite) < 2:
        return False
    return any(math.dist(finite[i], finite[i + 1]) >= 1e-9 for i in range(len(finite) - 1))


def _closest_on_curve(point, curve_points):
    """The point on the polyline nearest `point` (MM2's ClosestPointToCurve)."""
    closest = curve_points[0]
    closest_distance = math.inf

    for start, end in zip(curve_points, curve_points[1:]):
        along = [end[axis] - start[axis] for axis in range(3)]
        length_squared = sum(component * component for component in along)

        if length_squared < 1e-12:                  # degenerate segment: both ends coincide
            candidate = tuple(start)
        else:
            travel = sum((point[axis] - start[axis]) * along[axis] for axis in range(3)) / length_squared
            travel = min(1.0, max(0.0, travel))     # clamp onto the segment
            candidate = tuple(start[axis] + along[axis] * travel for axis in range(3))

        distance = sum((point[axis] - candidate[axis]) ** 2 for axis in range(3))
        if distance < closest_distance:
            closest_distance = distance
            closest = candidate

    return closest


# ── road assembly + the prop walk ─────────────────────────────────────────────────────────────────

def _block_to_room(b: int) -> Tuple[int, bool]:
    """roadBlock value -> (rooms2 geometry id, reversed?). Values >= 0x8000 are signed-negative =
    the block is traversed in REVERSE (its sidewalk left/right swap with travel direction)."""
    if b >= 0x8000:
        return abs(b - 0x10000) - 1, True
    return b - 1, False


def _propidx_for_block(b: int) -> int:
    """roomFlags/propRule index for a roadBlock (= the file room id)."""
    return abs(b - 0x10000) if b >= 0x8000 else b


def _room_road_rows(room) -> List[List[int]]:
    """The road cross-section rows (groups of 4 vertex refs) of a room's road attribute(s).
    Row layout: [building_L, curb_L, curb_R, building_R]."""
    rows = []
    for a in room.get("attributes", []):
        if a.get("type") == "road":
            vr = a.get("vertexRefs", [])
            for i in range(0, len(vr) - 3, 4):
                rows.append(vr[i:i + 4])
    return rows


def _load_propdefs(path: str) -> dict:
    out = {}
    for line in open(path, encoding="latin-1").read().splitlines()[1:]:
        c = [x.strip() for x in line.split(",")]
        if len(c) < 6 or not c[0]:
            continue
        try:
            out[c[0]] = dict(start=float(c[1]), distance=float(c[2]), maxUse=int(c[3]),
                             minLerp=float(c[4]), maxLerp=float(c[5]),
                             files=[x for x in c[6:10] if x])
        except ValueError:
            continue

    return out


def _load_proprules(path: str) -> dict:
    out = {}
    for line in open(path, encoding="latin-1").read().splitlines()[1:]:
        c = [x.strip() for x in line.split(",")]
        if not c or not c[0]:
            continue
        out[c[0]] = [x for x in c[1:9] if x]
    return out


def generate(raw_psdl_path: str, city_dir: str, *, psdl_path: Optional[str] = None,
             log=None, swap_sides: bool = False, max_furniture: int = 0) -> List[Dict]:
    """Reproduce MM2's procedural street furniture for the city in raw_psdl_path.

    raw_psdl_path : psdl-import raw_psdl.json (vertices + per-room road geometry; rule bytes are
                    read from it if present, else parsed from psdl_path).
    city_dir      : the MM2 `mm2core/city/<city>/` folder holding propdefs.csv + proprules.csv.
    psdl_path     : optional `<city>.psdl` (fallback source for roomFlags/propRule/paths).
    swap_sides    : flip which sidewalk is `left` vs `right` (handedness eyeball -- see caveats).
    max_furniture : engine BANGER-COUNT ceiling guard (see the cap near the end). MM1/Open1560
                    ACCESS_VIOLATIONs in agiMonoLighter::LightVertex above ~5.3k TOTAL city bangers;
                    the hand-placed pathset adds ~760, so the procedural furniture is capped here to
                    keep the city under the ceiling. Raise this only if the engine ceiling is raised.
    Returns editor prop-dicts: [{name, offset:(x,y,z), angle, flags}, ...].
    """
    def _log(msg):
        if log:
            log(msg)

    with open(raw_psdl_path, "r") as f:
        raw = json.load(f)
    verts = raw["vertices"]
    rooms = {r["id"]: r for r in raw["rooms"]}

    propRule = raw.get("propRule")
    paths = raw.get("paths")
    if propRule is None or paths is None:
        if not psdl_path or not Path(psdl_path).exists():
            _log("mm2_props: no rule data in raw_psdl.json and no .psdl fallback -> 0 props")
            return []
        rd = parse_psdl_rules(psdl_path)
        propRule, paths = rd["propRule"], rd["paths"]

    propdefs = _load_propdefs(str(Path(city_dir) / "propdefs.csv"))
    proprules = _load_proprules(str(Path(city_dir) / "proprules.csv"))
    model_map = _build_model_map()

    # ── DIRECTED-PROP FACING (MM2 -> MM1, log-verified) ────────────────────────────────────────────
    # Most furniture faces along the road TANGENT (cross(down, dir)); that is correct for symmetric
    # props (poles/meters/cans/trees). But a prop with an ARM or a SEAT must face the ROAD, and each
    # converted mesh's own "forward" axis differs (measured from the .pkg/.bms geometry):
    #   * mm2lamp  (sp_lightstreet_rt_f):   arm + lamp head extend along pkg +Z  (z[-0.01..3.56])
    #   * tplttrafc/dual (MM1 traffic light): arm extends along pkg -X           (x[-6.72..0.12])
    #   * mm2bench (sp_benchwood_f):         backrest at pkg +X -> seat faces pkg -X; long axis pkg +Z
    # The banger matrix aligns the mesh-local +X axis to the placed heading (banger.cpp), and a mesh
    # vertex maps  world = lx*m0 + ly*+Y + lz*m2,  so mesh +Z lands at heading+90 and mesh -X at
    # heading+180. So to point each mesh's real front at the road we set the heading from `dir` (the
    # curb->road direction, heading D) per class. `dir` flips per side automatically, so the arm/seat
    # on BOTH sidewalks reaches the shared carriageway.
    arm_lamp_ids = {Mm2Prop.LAMP}                                         # arm = pkg +Z -> D-90
    traffic_ids = {Prop.TRAFFIC_LIGHT_SINGLE, Prop.TRAFFIC_LIGHT_DUAL}    # arm = pkg -X -> D+180
    bench_ids = {Mm2Prop.BENCH}                                           # seat = pkg -X -> D+180

    def V(i):
        v = verts[i]; return (v[0], v[1], v[2])

    def road_rule(p) -> int:
        """The rule-pair number for a road = the most common VALID propRule among its blocks."""
        vals = []
        for b in p["roadBlocks"]:
            j = _propidx_for_block(b)
            if 0 <= j < len(propRule):
                v = propRule[j]
                if v > 0 and f"n{v:02d}left" in proprules:   # ignore 0 + out-of-range anomalies (e.g. 205)
                    vals.append(v)
        return collections.Counter(vals).most_common(1)[0][0] if vals else 0

    def road_rows(p):
        """Concatenated cross-section rows for the whole road, in travel order. Reversed blocks get
        their rows reversed AND left/right columns swapped so the L/R polylines stay continuous."""
        rows = []
        for b in p["roadBlocks"]:
            road_id, rev = _block_to_room(b)
            room = rooms.get(road_id)
            if room is None:
                continue
            rr = _room_road_rows(room)
            if rev:
                rr = [[r[3], r[2], r[1], r[0]] for r in reversed(rr)]
            rows.extend(rr)
        # drop seam duplicates (adjacent blocks share their boundary cross-section)
        dedup = []

        for r in rows:
            if dedup and dedup[-1] == r:
                continue
            dedup.append(r)

        return dedup

    def walk_side(in_line, out_line, kind_names, out_props, skipped, degenerate):
        # ── DEGENERATE-GEOMETRY GUARD (fixes the agiMonoLighter::LightVertex render crash) ──────────
        # The sidewalk polylines come straight from PSDL vertexRefs; a road with a zero-length lane,
        # a reversed/empty block, or a coincident cross-section row yields coincident (in==out) or
        # NaN points. Without guarding, normalize(in-out) -> NaN facing and lerp(in,out) -> NaN/inf
        # offset; that bad banger then crashes the static-mesh vertex lighter at CreatePipeline. We
        # VALIDATE (don't rewrite) the paired polylines, then per-instance skip any prop with a
        # non-finite offset or a zero-length (degenerate) facing. The three polylines stay paired by
        # row index so EVERY valid prop keeps its exact 1:1 position; only genuinely bad ones drop.
        if not _walkable(in_line) or not _walkable(out_line):   # empty / coincident / all-NaN side
            return

        row_count = min(len(in_line), len(out_line))
        mid_line = [tuple((in_line[i][axis] + out_line[i][axis]) * 0.5 for axis in range(3))
                    for i in range(row_count)]
        if not _walkable(mid_line):              # midline collapses to a point -> nothing placeable
            return

        total_length = _path_length(mid_line)
        if not math.isfinite(total_length) or total_length <= 0.0:   # NaN/inf or zero arclength
            return

        for name in kind_names:
            propdef = propdefs.get(name)
            if not propdef or not propdef["files"]:
                continue

            start, spacing, max_use = propdef["start"], propdef["distance"], propdef["maxUse"]

            # 1:1 SPEC (km2cb-mm2-core elements/props/elements/psdl.json placementRules):
            #   xPos = rnd(minHorizPos, maxHorizPos)   meshIndex = rnd(0, meshNum)
            # i.e. BOTH the curb<->building lerp and the file1-4 pick are RANDOM per prop. MM2 rolls
            # its own runtime RNG (per-instance stream unknowable), so we use a DETERMINISTIC seed per
            # (side, kind, index): statistically identical to MM2, stable across rebuilds. Most SF rows
            # have min==max and 4x the same file -> exact there either way; NY rows genuinely vary.
            lerp_min, lerp_max = propdef["minLerp"], propdef.get("maxLerp", propdef["minLerp"])
            if lerp_max < lerp_min:
                lerp_min, lerp_max = lerp_max, lerp_min
            seed = zlib.crc32(f"{name}:{len(mid_line)}:{round(total_length, 3)}".encode())

            index = 0; last_distance = 0.0
            while True:
                distance = start if index == 0 else last_distance + spacing
                if not (spacing > 0.0 and index < max_use and distance <= total_length):
                    break

                # Advance the walk state first, so a per-instance skip below can just `continue`.
                last_distance = distance; instance_index = index; index += 1

                rng = random.Random(seed + instance_index)
                lerp = lerp_min if (lerp_max - lerp_min) < 1e-9 else rng.uniform(lerp_min, lerp_max)
                mid_point = _point_on_path(mid_line, distance)
                curb_point = _closest_on_curve(mid_point, in_line)
                building_point = _closest_on_curve(mid_point, out_line)
                position = tuple(curb_point[axis] + (building_point[axis] - curb_point[axis]) * lerp
                                 for axis in range(3))
                if not _finite3(position):        # non-finite offset -> would crash the lighter
                    degenerate["nonfinite_pos"] += 1
                    continue

                # Facing basis: across = the curb->road direction (curb - building);
                # forward = cross(down, across) = along the road tangent (default furniture facing).
                across_x, across_z = curb_point[0] - building_point[0], curb_point[2] - building_point[2]
                across_length = math.hypot(across_x, across_z)
                if not math.isfinite(across_length) or across_length < 1e-6:   # zero-width sidewalk
                    degenerate["degenerate_facing"] += 1
                    continue

                across_x, across_z = across_x / across_length, across_z / across_length
                forward_x, forward_z = -across_z, across_x     # cross(Vector3.down, across) in XZ
                if ((forward_x == 0.0 and forward_z == 0.0)
                        or not (math.isfinite(forward_x) and math.isfinite(forward_z))):
                    degenerate["degenerate_facing"] += 1       # atan2(0,0) / NaN -> undefined angle
                    continue

                # 1:1 SPEC: meshIndex = rnd(0, meshNum) -- random pick among file1-4 (same seeded RNG
                # as the lerp above; was a deterministic round-robin before, which skews multi-model
                # rows like NY's blue/red/yellow newsboxes).
                model = propdef["files"][rng.randrange(len(propdef["files"]))]
                mapped = model_map.get(model)
                if not mapped:
                    skipped[model] += 1
                    continue

                # Per-class facing (see the DIRECTED-PROP FACING note above): arm/seat props face the
                # ROAD via the curb->road heading; everything else keeps the road-tangent facing.
                prop_id, flags = mapped
                across_deg = math.degrees(math.atan2(across_z, across_x))
                if prop_id in arm_lamp_ids:
                    angle = across_deg - 90.0    # arm-lamp: arm reaches over the road
                elif prop_id in traffic_ids:
                    angle = across_deg + 180.0   # traffic light: arm over the road
                elif prop_id in bench_ids:
                    angle = across_deg + 180.0   # bench: seat faces road, long axis along it
                else:
                    angle = math.degrees(math.atan2(forward_z, forward_x))   # symmetric/pole: tangent

                if not math.isfinite(angle):
                    degenerate["degenerate_facing"] += 1
                    continue

                out_props.append({"name": prop_id, "offset": position, "angle": angle, "flags": flags})

    out_props: List[Dict] = []
    skipped = collections.Counter()
    degenerate = collections.Counter()                     # degenerate-geometry props dropped (crash guard)
    n_roads = 0
    for p in paths:
        rule = road_rule(p)
        if rule == 0:
            continue
        rows = road_rows(p)
        if len(rows) < 2:
            continue
        n_roads += 1
        rn = f"n{rule:02d}"
        # left  sidewalk: curb=col1, building=col0 ;  right sidewalk: curb=col2, building=col3
        left_in = [V(r[1]) for r in rows]; left_out = [V(r[0]) for r in rows]
        right_in = [V(r[2]) for r in rows]; right_out = [V(r[3]) for r in rows]
        left_rule, right_rule = rn + "left", rn + "right"
        if swap_sides:
            left_rule, right_rule = right_rule, left_rule
        walk_side(left_in, left_out, proprules.get(left_rule, []), out_props, skipped, degenerate)
        walk_side(right_in, right_out, proprules.get(right_rule, []), out_props, skipped, degenerate)

    # ── ENGINE BANGER-COUNT CEILING (render-crash fix, measured) ─────────────────────────────────
    # MM1/Open1560 has a STRUCTURAL ceiling on how many city bangers it can render. Above ~5.3k-5.45k
    # TOTAL instances the first-frame instance-lighting path corrupts memory and ACCESS_VIOLATIONs in
    # agiMonoLighter::LightVertex during CreatePipeline. This is NOT a degenerate prop -- every offset
    # and facing emitted here is finite, and forcing all furniture to ONE proven-good mesh still
    # crashes, so it is count/density-driven, not geometry- or mesh-driven. Proven by bisection:
    # 5259 total bangers boots fully, 5449 crashes (SF furniture 4690 + ~760 hand-placed pathset).
    # The hand-placed pathset/race props add ~760, so we cap the procedural FURNITURE so the city
    # total stays safely under the ceiling. We keep EVERY glow street-light/lamp (they define the
    # streets and carry the rule-density proof, e.g. rule n03's 14 streetlights) and shed only
    # trailing non-glow clutter (cans/phones/news boxes/signs) when over budget -- minimal visual
    # loss, no crash. The proper 1:1 fix is ENGINE-side: raise the instance ceiling (cf. the precedent
    # of growing mmInstanceHeap 0xB9000 -> 0x200000), then raise `max_furniture` to re-enable all props.
    if max_furniture and len(out_props) > max_furniture:
        glow = BangerFlags.BREAKABLE_GLOW
        lights = [p for p in out_props if p["flags"] == glow]
        clutter = [p for p in out_props if p["flags"] != glow]
        budget = max(0, max_furniture - len(lights))
        if len(clutter) > budget:
            dropped = len(clutter) - budget
            out_props = lights + clutter[:budget]
            _log("mm2_props: engine banger-cap -> kept all %d glow lights, dropped %d trailing non-glow "
                 "clutter props to fit the ~5.3k-banger render ceiling (furniture %d -> %d)"
                 % (len(lights), dropped, len(lights) + len(clutter), len(out_props)))
    if skipped:
        _log("mm2_props: %d furniture instances had no MM1 prop mapping (skipped): %s"
             % (sum(skipped.values()), dict(skipped)))
    if degenerate:
        _log("mm2_props: %d furniture instances dropped on DEGENERATE geometry (crash guard): %s"
             % (sum(degenerate.values()), dict(degenerate)))
    _log("mm2_props: %d furniture props on %d roads (1:1 MM2 density)" % (len(out_props), n_roads))
    return out_props


# ── Intersection traffic lights (MM2 engine-placed -> synthetic MM1 props) ──────────────────────────
# MM2's engine places traffic lights at controlled intersections using its city traffic-control system.
# These lights are NOT in any pathset, inst, or proprules file -- the engine derives their positions
# from the PSDL intersection room (road_triangle_fan, type 0x05) perimeters at runtime.
# We replicate this here: for each intersection room, find the outward-facing CORNER of the perimeter
# (the convex extremum toward each approaching street) and place one TRAFFIC_LIGHT_SINGLE there,
# facing the intersection centre (arm over the approaching carriageway).
#
# This gives traffic lights at every controlled intersection in MM2-SF/London -- exactly what the
# MM2 engine renders -- with no pathset or CSV dependency.

def bai_traffic_lights(bai_path: str, *, log=None) -> List[Dict]:
    """1:1 traffic lights from the BAI's STORED data (replaces the PSDL-intersection synthesis).

    Ground truth (MM2Hook src/modules/ai/aiTrafficLight.h + bai RoadEnd record): each road end
    stores vehicleRule + trafficLightOrigin[2], and the engine builds each light via
    aiTrafficLightInstance::Init(name, position, positionFacing) — i.e. the two verts are
    (position, facing target). Rule semantics (observed SF: 3=337x, 1=215x, 0=206x ends):
    rule 3 = signalized -> place a light; 0/1 = uncontrolled/stop -> none.
    Model: dual-arm for multi-lane approaches, single otherwise (refinable). Banger angle = mesh
    local +X toward the facing target (the engine's own convention)."""
    roads, _ = parse_bai_full(bai_path)
    out: List[Dict] = []

    for road in roads:
        # A light at the END faces traffic arriving via dir0 (right side); at the START via dir1.
        road_ends = ((road.vrule_start, road.tl_start, road.left),
                     (road.vrule_end, road.tl_end, road.right))

        for rule, traffic_light, side in road_ends:
            if rule != VEHICLE_RULE_SIGNALIZED or not traffic_light or len(traffic_light) < 2:
                continue

            position, facing_target = traffic_light[0], traffic_light[1]
            if (not (_finite3(position) and _finite3(facing_target))
                    or not any(abs(c) > 1e-6 for c in position)):
                continue                    # unset/degenerate record -> the engine places no light

            delta_x = facing_target[0] - position[0]
            delta_z = facing_target[2] - position[2]
            if math.hypot(delta_x, delta_z) < 1e-6:
                continue                    # position == target -> no defined facing

            angle = math.degrees(math.atan2(delta_z, delta_x))
            name = (Prop.TRAFFIC_LIGHT_DUAL if getattr(side, "n_lanes", 1) >= 2
                    else Prop.TRAFFIC_LIGHT_SINGLE)
            out.append({"name": name, "offset": (position[0], position[1], position[2]),
                        "angle": angle, "flags": BangerFlags.BREAKABLE})

    if log:
        log(f"bai_traffic_lights: {len(out)} lights from stored BAI (rule-3 road ends)")

    return out


def intersection_traffic_lights(expanded_psdl_path: str, *, log=None) -> List[Dict]:
    """Synthesise traffic light props at every PSDL intersection (road_triangle_fan room).

    MM2's engine places traffic lights at controlled intersections via its traffic-control system --
    these are not in any pathset, inst, or proprules CSV. We replicate the visual result here.

    Strategy: for each intersection room, divide the perimeter into 4 quadrants relative to the
    room centroid (NE/NW/SE/SW). In each quadrant, find the perimeter corner CLOSEST to the
    centroid -- that corner is the curb corner where cars approach the intersection, which is where
    MM2 puts a traffic light. This gives exactly 4 lights per intersection (one per approach
    direction) and handles non-square, T-intersections, and dead-end approaches gracefully.

    Returns a list of banger-prop dicts [{name, offset, angle, flags}] ready for BangerEditor.
    """
    try:
        with open(expanded_psdl_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        if log:
            log("intersection_traffic_lights: cannot read %s: %s" % (expanded_psdl_path, e))
        return []

    out = []
    n_intersections = 0
    for room in data.get("rooms", []):
        has_fan = any(o.get("name") == "road_triangle_fan" for o in room.get("objects", []))
        if not has_fan:
            continue
        perim = room.get("perimeter", [])
        if len(perim) < 4:
            continue
        n_intersections += 1
        # Intersection centroid (the reference point for quadrant split)
        cx = sum(p[0] for p in perim) / len(perim)
        cy = sum(p[1] for p in perim) / len(perim)
        cz = sum(p[2] for p in perim) / len(perim)
        # Per quadrant, pick the perimeter corner CLOSEST to the centroid = the curb corner
        # that approaches the junction (the inside corner, not the far convex extent).
        quadrants = {}  # (qx, qz) -> (distance_sq, corner)
        for corner in perim:
            dx, dz = corner[0] - cx, corner[2] - cz
            qx = 1 if dx > 0 else -1
            qz = 1 if dz > 0 else -1
            d2 = dx * dx + dz * dz
            key = (qx, qz)
            if key not in quadrants or d2 < quadrants[key][0]:
                quadrants[key] = (d2, corner)
        # One traffic light per quadrant, arm facing the intersection centre
        for _, corner in quadrants.values():
            px, py, pz = corner[0], corner[1], corner[2]
            dx, dz = cx - px, cz - pz
            dl = math.hypot(dx, dz)
            if dl < 0.5:
                continue
            # MM1 traffic light arm is at mesh -X; banger aligns mesh +X to heading.
            # angle = atan2(dz,dx)+180 -> mesh -X (arm) faces centroid = over the approaching lane.
            angle = math.degrees(math.atan2(dz, dx)) + 180.0
            out.append({
                "name": Prop.TRAFFIC_LIGHT_SINGLE,
                "offset": (px, py, pz),
                "angle": angle,
                "flags": BangerFlags.BREAKABLE,
            })

    if log:
        log("intersection_traffic_lights: %d props at %d intersections (4 per intersection)" %
            (len(out), n_intersections))
    return out


# ── CLI: patch raw_psdl.json with the rule bytes, and/or print a 1:1 verification ────────────────

if __name__ == "__main__":
    import sys
    # usage:
    #   python -m ... patch  <raw_psdl.json> <city.psdl>
    #   python -m ... verify <raw_psdl.json> <city_dir> [city.psdl]
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "patch":
        patch_raw_psdl(sys.argv[2], sys.argv[3])
        print("patched", sys.argv[2])
    else:
        raw_path, city_dir = sys.argv[2], sys.argv[3]
        psdl = sys.argv[4] if len(sys.argv) > 4 else None
        props = generate(raw_path, city_dir, psdl_path=psdl, log=print)
        by = collections.Counter(str(p["name"]) for p in props)
        print("total:", len(props))
        for nm, c in by.most_common():
            print("  %-22s %d" % (nm, c))

"""
Named city presets for the roadnet compiler.

`ROADNET_CITY` in USER settings can be a preset NAME (string) resolved here, e.g.
`ROADNET_CITY = "large"`. Each preset returns a RoadNetwork. They show off scale +
customization: bigger grids, wider avenues, mixed lane counts, non-square blocks.

Add your own: write a zero-arg builder that returns a RoadNetwork and register it in PRESETS.
"""
import math

from src.game.mapgen.roadnet.graph import RoadNetwork, grid_city
from src.game.mapgen.roadnet import terrain as _terrain


def _line_index_maps(net: RoadNetwork):
    """Map each unique node-x / node-z to its column / row index (for picking avenues)."""
    xs = sorted({round(n.pos[0], 3) for n in net.nodes.values()})
    zs = sorted({round(n.pos[1], 3) for n in net.nodes.values()})
    return ({x: i for i, x in enumerate(xs)}, {z: j for j, z in enumerate(zs)})


def _widen_avenues(net: RoadNetwork, every: int = 3, lanes: int = 2) -> RoadNetwork:
    """
    Turn every `every`-th lattice line (column AND row) into a wider avenue with `lanes`
    lanes per direction; the rest stay 1-lane streets. Produces a streets-and-avenues feel.
    """
    col_idx, row_idx = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        vertical = abs(a[0] - b[0]) < 1e-6        # shared x -> runs along a column
        line = col_idx.get(round(a[0], 3)) if vertical else row_idx.get(round(a[1], 3))
        if line is not None and line % every == 0:
            e.lanes_fwd = e.lanes_rev = lanes
    return net


# ── presets ──────────────────────────────────────────────────────────────────

def small() -> RoadNetwork:
    return grid_city(3, 3, spacing=120.0, name="Small")


def medium() -> RoadNetwork:
    return grid_city(5, 5, spacing=120.0, name="Medium")


def large() -> RoadNetwork:
    return grid_city(8, 8, spacing=115.0, name="Large")


def mega() -> RoadNetwork:
    return grid_city(12, 12, spacing=105.0, name="Mega")


def downtown() -> RoadNetwork:
    # Dense, small blocks; every other line is a 2-lane avenue.
    return _widen_avenues(grid_city(7, 7, spacing=85.0, name="Downtown"), every=2, lanes=2)


def avenues() -> RoadNetwork:
    # Wide 3-lane avenues every 3rd line over a roomy grid.
    return _widen_avenues(grid_city(8, 8, spacing=130.0, name="Avenues"), every=3, lanes=3)


def manhattan() -> RoadNetwork:
    # Tall + narrow, long blocks; cross-streets every 3rd line are 2-lane.
    net = grid_city(5, 11, spacing=110.0, name="Manhattan")
    return _widen_avenues(net, every=3, lanes=2)


def boulevard() -> RoadNetwork:
    # Divided boulevards: 2 lanes per direction, a grass median down the centre.
    net = grid_city(5, 5, spacing=170.0, name="Boulevard")
    for e in net.edges:
        e.lanes_fwd = e.lanes_rev = 2
        e.median_width = 8.0
        e.divided = True
    return net


def parkway() -> RoadNetwork:
    # Wide divided avenues (median) every 3rd line over a roomy grid; the rest are streets.
    net = grid_city(7, 7, spacing=150.0, name="Parkway")
    col_idx, row_idx = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        vertical = abs(a[0] - b[0]) < 1e-6
        line = col_idx.get(round(a[0], 3)) if vertical else row_idx.get(round(a[1], 3))
        if line is not None and line % 3 == 0:
            e.lanes_fwd = e.lanes_rev = 2
            e.median_width = 7.0
            e.divided = True
    return net


def highway() -> RoadNetwork:
    # Big, fast grid: 3 lanes each way, divided, NO sidewalks (open highway feel).
    net = grid_city(4, 4, spacing=220.0, name="Highway")
    for e in net.edges:
        e.lanes_fwd = e.lanes_rev = 3
        e.median_width = 6.0
        e.divided = True
        e.sidewalk_fwd = e.sidewalk_rev = False
        e.speed_limit = 80.0
    return net


def _bow_edge(net, e, amp):
    """Replace a straight edge with a gentle arc (shape points), bowing perpendicular by `amp`."""
    x0, z0 = net.nodes[e.a].pos
    x1, z1 = net.nodes[e.b].pos
    horizontal = abs(z1 - z0) < 1e-6
    shp = []
    for k in range(1, 6):
        t = k / 6.0
        px, pz = x0 + t * (x1 - x0), z0 + t * (z1 - z0)
        bow = amp * math.sin(math.pi * t)
        shp.append((px, pz + bow) if horizontal else (px + bow, pz))
    e.shape = tuple(shp)


def _scurve_edge(net, e, amp, cycles=2):
    """Replace a straight edge with a multi-BEND shape: the cl weaves perpendicular by amp*sin(cycles*pi*t).
    cycles=2 -> an S (go left then right WITHIN one piece); 3 -> a wiggle (left-right-left). Returns to the
    straight line at each bend boundary. Denser sampling than _bow_edge so the multi-bend stays smooth."""
    x0, z0 = net.nodes[e.a].pos
    x1, z1 = net.nodes[e.b].pos
    horizontal = abs(z1 - z0) < 1e-6
    shp = []
    for k in range(1, 12):
        t = k / 12.0
        px, pz = x0 + t * (x1 - x0), z0 + t * (z1 - z0)
        bow = amp * math.sin(cycles * math.pi * t)
        shp.append((px, pz + bow) if horizontal else (px + bow, pz))
    e.shape = tuple(shp)


def metropolis() -> RoadNetwork:
    # A grid whose middle avenues sweep as gentle CURVES (2-lane), on a grass carpet. Showcases
    # Phase-1 curved roads + Phase-2 off-grid ground. (Hills are Phase 3 — not yet.)
    net = grid_city(5, 5, spacing=150.0, name="Metropolis")
    col_idx, row_idx = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        horizontal = abs(a[1] - b[1]) < 1e-6
        line = row_idx.get(round(a[1], 3)) if horizontal else col_idx.get(round(a[0], 3))
        if line == 2:                      # the central cross avenues curve + widen
            _bow_edge(net, e, 22.0)
            e.lanes_fwd = e.lanes_rev = 2
    return net


def hills() -> RoadNetwork:
    # STRAIGHT grid over terraced hills (flat levels + smooth ramps). Straight roads keep the AI
    # happy, so this one has full low-density traffic + peds.
    net = grid_city(6, 6, spacing=150.0, name="Hills")
    net.terrain = _terrain.terraced()   # west plateau (+7) + gentle north rise (+4)
    return net


def megacity2() -> RoadNetwork:
    """
    MEGACITY 2 - a full, diverse, AI-DRIVABLE city combining every WORKING lever in one map: an 8x8 grid
    core (its loops auto-generate a CIRCUIT race + a checkpoint trail), CURVED + WIDENED boulevards, a RIVER
    crossed by BRIDGES (gentle deck arch) including ONE curved + BANKED showcase bridge, a gentle corner
    HILL, PARKING LOT / PARK / PLAZA, and mixed lane counts. Everything kept GENTLE so the AI drives it all.
    `-circuit 0` for opponents, `-race 0` for the checkpoint trail.
    """
    net = grid_city(8, 8, spacing=200.0, name="MegaCity2")
    col_idx, row_idx = _line_index_maps(net)
    RIVER = 95.0                               # river band |z| < RIVER, between the two central rows
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        horizontal = abs(a[1] - b[1]) < 1e-6
        line = row_idx.get(round(a[1], 3)) if horizontal else col_idx.get(round(a[0], 3))
        crosses_river = (not horizontal) and min(a[1], b[1]) <= -RIVER and max(a[1], b[1]) >= RIVER
        if crosses_river:                      # BRIDGES over the river (gentle arch, 2-lane)
            e.deck_height = 4.0; e.num_verts = 12; e.lanes_fwd = e.lanes_rev = 2
            if line == 4:                      # ONE curved + BANKED showcase bridge
                _bow_edge(net, e, 26.0); e.bank_deg = 15.0
            else:
                _bow_edge(net, e, 0.0)         # straight, gentle arch (densified)
        elif horizontal and line in (1, 6):    # CURVED + widened outer boulevards (away from the river)
            _bow_edge(net, e, 26.0); e.lanes_fwd = e.lanes_rev = 2
        elif line in (2, 5):                   # wider straight avenues
            e.lanes_fwd = e.lanes_rev = 2

    def _terr(x, z):                           # gentle NW corner HILL (clear of the river)
        dx = min(1.0, max(0.0, (-300.0 - x) / 400.0))
        dz = min(1.0, max(0.0, (z - 300.0) / 400.0))
        return 18.0 * dx * dz                  # up to 18u over ~400u = ~4.5% grade (AI-safe)
    net.terrain = _terr
    net.ground_zones = [
        (-760.0, -RIVER, 760.0, RIVER, "water"),         # the river through the middle
        (320.0, -660.0, 660.0, -340.0, "lot"),           # SE parking lot
        (-660.0, -660.0, -340.0, -340.0, "park"),        # SW park
        (340.0, 340.0, 660.0, 660.0, "plaza"),           # NE civic plaza (concrete)
    ]
    net.spawn_near = (-300.0, -300.0)          # interior node on a wide avenue, on land, well clear of the
    #                                            river (|z|<95); checkpoint trail snakes across the city.
    #                                            (graph coords; the city is scaled x1.15 -> ~(-345,-345))
    return net


def curvyhills() -> RoadNetwork:
    # NEXT-STEP showcase: CURVED roads out at the west edge, which sits up on the +7 plateau, so
    # they sweep AND climb (curve+grade). Curve+grade crashes the engine's AI rails, so this map
    # auto-runs AI-off (player drives; no traffic) — see the terrain+curves gate in the builder.
    net = grid_city(6, 6, spacing=150.0, name="CurvyHills")
    net.terrain = _terrain.terraced()
    col_idx, _ = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        if abs(a[0] - b[0]) < 1e-6 and col_idx.get(round(a[0], 3)) == 0:   # westmost column
            _bow_edge(net, e, 18.0)
    return net


def bumps() -> RoadNetwork:
    # A single central raised plateau you ramp up onto.
    net = grid_city(6, 6, spacing=150.0, name="Bumps")
    net.terrain = _terrain.plateau(amp=6.0)   # one central raised plateau
    return net


def sanfran() -> RoadNetwork:
    # Dramatic elevation — steep grid streets over big hills.
    net = grid_city(6, 6, spacing=150.0, name="SanFran")
    net.terrain = _terrain.terraced([('x', -50.0, -260.0, 13.0), ('z', 40.0, 300.0, 8.0)])  # steep
    return net


def alps() -> RoadNetwork:
    # The showcase: curved central avenues + layered terrain (curve AND grade together).
    net = metropolis()
    net.name = "Alps"
    net.terrain = _terrain.terraced([('x', -40.0, -240.0, 7.0), ('z', 120.0, 340.0, 4.0)])  # curved roads ON terraced hills
    return net


def metrohills() -> RoadNetwork:
    # Flat CURVED avenues + dynamic intersections down the middle, with small height in the
    # CORNERS (straight roads). The curves stay flat -> no curve+grade -> full traffic + peds.
    # Spawn by the curved middle so you see them immediately.
    net = metropolis()
    net.name = "MetroHills"
    net.terrain = _terrain.corners(amp=7.0)
    net.spawn_near = (0.0, 0.0)
    return net



def blenderdemo() -> RoadNetwork:
    """Phase 2 demo: a city built the way the Blender Road Builder feeds it -- authored road dicts
    welded through road_builder_bridge.roads_to_network (varied lanes/peds/alley/divided/curve)."""
    from src.game.mapgen.roadnet.road_builder_bridge import roads_to_network
    g = 140.0
    P = {(c, r): (c * g - g, r * g - g) for c in range(3) for r in range(3)}
    roads = []
    for c in range(3):
        for r in range(3):
            if c + 1 < 3:
                roads.append({"points": [P[(c, r)], P[(c + 1, r)]], "lane_count": 2})
            if r + 1 < 3:
                roads.append({"points": [P[(c, r)], P[(c, r + 1)]], "lane_count": 1})
    roads[1].update(alley=True, two_way=False, sidewalk=False)                 # an alley
    roads[4].update(median=True, median_width=4.0, lane_count=2)               # a divided boulevard
    roads[6]["points"] = [P[(1, 1)], (90.0, 10.0), P[(2, 1)]]                  # a curved road
    return roads_to_network(roads, snap=8.0)


def halfchicago() -> RoadNetwork:
    """
    GO-ALL-OUT showcase: a big, diverse 'half Chicago', deliberately NOT a uniform grid:
      * ROAD HIERARCHY: two wide main avenues (7 m, 2-lane), normal 2-lane secondaries, narrow
        1-lane side streets.
      * CURVED avenues (long-gentle / long-medium / short-sharp) confined to the flat WEST half.
      * an EAST HILL: one long gentle smooth climb (~2% grade) on STRAIGHT roads. No road is ever
        both curved AND graded, and the climb stays gentle/single-ramp -- steeper or kinked grades
        spike the AI wheel sim (mmWheel::ComputeDwtdw crash).
      * AREAS via ground_zones: south-central LAKE (water), sandy SHORE, big SW PARK, NW parking
        LOT (paved). Facade DISTRICTS by x: Chinatown (west) / Downtown (core) / Market (east).
    Inside the AI-safe envelope (no 3-lane / divided / alley / plaza / curve+curve / curve+grade),
    so full traffic + peds + opponents + a circuit race all run crash-free.
    """
    g = 130.0
    cols, rows = 9, 7
    net = RoadNetwork(name="HalfChicago")
    ids = {}
    nid = 0
    x0 = -(cols - 1) / 2.0 * g
    z0 = -(rows - 1) / 2.0 * g
    for r in range(rows):
        for c in range(cols):
            net.add_node((c * g + x0, r * g + z0), node_id=nid)
            ids[(c, r)] = nid
            nid += 1

    # ROAD HIERARCHY (so it doesn't read as a uniform grid): two MAIN avenues are wide, a few
    # secondary avenues are normal 2-lane, and the rest are narrow 1-lane side streets.
    avenue_rows, avenue_cols = {1, 5}, {1, 7}
    for r in range(rows):
        for c in range(cols):
            for dc, dr in ((1, 0), (0, 1)):
                c2, r2 = c + dc, r + dr
                if c2 >= cols or r2 >= rows:
                    continue
                horiz = dr == 0
                if (horiz and r == 3) or (not horiz and c == 4):       # the two MAIN avenues = WIDE
                    lf, lr, lw = 2, 2, 7.0
                elif (horiz and r in avenue_rows) or (not horiz and c in avenue_cols):
                    lf, lr, lw = 2, 2, 5.0                              # secondary avenues = normal
                else:
                    lf, lr, lw = 1, 1, 4.0                              # NARROW side streets
                net.add_edge(ids[(c, r)], ids[(c2, r2)], lanes_fwd=lf, lanes_rev=lr, lane_width=lw)

    # CURVED avenues -- ROWS only (no curve+curve), confined to the flat WEST half so no road is
    # ever both curved AND graded (which crashes the AI). Varied length + sharpness.
    _, row_idx = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        if abs(a[1] - b[1]) > 1e-6:                    # only horizontal (row) edges curve
            continue
        mx = (a[0] + b[0]) * 0.5
        if mx > -20.0:                                 # curves only in the flat west
            continue
        ri = row_idx.get(round(a[1], 3))
        if ri == 1:
            _bow_edge(net, e, 14.0)                    # long, GENTLE
        elif ri == 5:
            _bow_edge(net, e, 22.0)                    # long, MEDIUM
        elif ri == 2 and mx < -260.0:
            _bow_edge(net, e, 26.0)                    # SHORT, SHARP (far west)

    # EAST HILL — DRAMATIC San-Francisco grade (smooth ramp, peak +24, ~15%). Safe in BOTH cruise and
    # races, via three engine fixes for steep AI rails: mmWheel::ComputeDwtdw (clamp load + floor slip
    # divisor), aiRailSet::CalcCopRailPosition (floor 1-sin(half_angle)), aiMap::Init (bound the
    # CopPaths overflow). STRAIGHT roads, single smooth ramp (curves stay west of x=-20 -> no curve+grade).
    net.terrain = _terrain.terraced([('x', 200.0, 440.0, 24.0)])

    # AREAS (x0,z0,x1,z1,kind): block interiors in each region take this texture/look.
    net.ground_zones = [
        (-160.0, 150.0, 140.0, 440.0, "water"),    # south-central lake (kept on the flat side)
        (140.0, 150.0, 260.0, 440.0, "sand"),      # sandy shore at the foot of the east hill
        (-640.0, 150.0, -200.0, 440.0, "park"),    # big SW park
        (-640.0, -440.0, -280.0, -150.0, "lot"),   # NW parking lot (paved)
    ]
    return net



def slopetest() -> RoadNetwork:
    """FEASIBILITY TEST: slopes (straight roads, EAST) + curves (flat, WEST) in SEPARATE zones, so
    no road is both curved and graded (which crashes the AI). If traffic survives, slopes are usable."""
    g = 130.0
    net = grid_city(7, 6, spacing=g, name="SlopeTest")
    net.terrain = _terrain.terraced([('x', 80.0, 460.0, 9.0)])   # flat west of x=80, climbs +9 east
    col_idx, _ = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        if abs(a[0] - b[0]) < 1e-6 and col_idx.get(round(a[0], 3)) in (0, 1):   # flat west columns
            _bow_edge(net, e, 16.0)
    return net



def megacity() -> RoadNetwork:
    """
    BIG showcase: an 11x9 metropolis, the most varied preset. Road hierarchy (wide avenues / normal /
    narrow streets), FOUR curved avenues confined to the flat west, a dramatic-but-safe east hill
    (~11% peak, single smooth ramp), and FIVE ground areas (south lake + sandy shore, big SW park,
    NW parking lot, a north green). Facade districts by x. Inside the AI-safe envelope, so full
    traffic + opponents + a circuit race run clean.
    """
    g = 125.0
    cols, rows = 11, 9
    net = RoadNetwork(name="MegaCity")
    ids, nid = {}, 0
    x0 = -(cols - 1) / 2.0 * g
    z0 = -(rows - 1) / 2.0 * g
    for r in range(rows):
        for c in range(cols):
            net.add_node((c * g + x0, r * g + z0), node_id=nid)
            ids[(c, r)] = nid
            nid += 1

    avenue_rows, avenue_cols = {2, 6}, {2, 8}
    for r in range(rows):
        for c in range(cols):
            for dc, dr in ((1, 0), (0, 1)):
                c2, r2 = c + dc, r + dr
                if c2 >= cols or r2 >= rows:
                    continue
                horiz = dr == 0
                if (horiz and r == 4) or (not horiz and c == 5):
                    lf, lr, lw = 2, 2, 7.0
                elif (horiz and r in avenue_rows) or (not horiz and c in avenue_cols):
                    lf, lr, lw = 2, 2, 5.0
                else:
                    lf, lr, lw = 1, 1, 4.0
                net.add_edge(ids[(c, r)], ids[(c2, r2)], lanes_fwd=lf, lanes_rev=lr, lane_width=lw)

    # FOUR curved avenues -- ROWS only (no perpendicular curve+curve), confined to the flat WEST (x < -30).
    _, row_idx = _line_index_maps(net)
    amp_by_row = {1: 14.0, 3: 22.0, 5: 18.0, 7: 26.0}
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        if abs(a[1] - b[1]) > 1e-6:
            continue
        if (a[0] + b[0]) * 0.5 > -30.0:
            continue
        amp = amp_by_row.get(row_idx.get(round(a[1], 3)))
        if amp:
            _bow_edge(net, e, amp)

    # east hill: smooth single ramp ~11% peak (curves are west of -30, so no curve+grade).
    net.terrain = _terrain.terraced([('x', 200.0, 520.0, 22.0)])
    net.ground_zones = [
        (-150.0, 200.0, 150.0, 510.0, "water"),    # south-central lake
        (150.0, 200.0, 205.0, 510.0, "sand"),      # sandy shore at the hill foot
        (-650.0, 200.0, -250.0, 510.0, "park"),    # big SW park
        (-650.0, -510.0, -320.0, -200.0, "lot"),   # NW parking lot
        (-150.0, -510.0, 200.0, -260.0, "park"),   # a north green
    ]
    return net


def riverside() -> RoadNetwork:
    """
    Waterfront town: a wide WATER band across the south with a sandy marina strip, a riverside park,
    and a parking lot. FLAT (no slope) so curved avenues can sweep freely (no curve+grade). A relaxed,
    pretty cruise map; AI-safe throughout.
    """
    g = 130.0
    cols, rows = 9, 8
    net = RoadNetwork(name="Riverside")
    ids, nid = {}, 0
    x0 = -(cols - 1) / 2.0 * g
    z0 = -(rows - 1) / 2.0 * g
    for r in range(rows):
        for c in range(cols):
            net.add_node((c * g + x0, r * g + z0), node_id=nid)
            ids[(c, r)] = nid
            nid += 1
    for r in range(rows):
        for c in range(cols):
            for dc, dr in ((1, 0), (0, 1)):
                c2, r2 = c + dc, r + dr
                if c2 >= cols or r2 >= rows:
                    continue
                horiz = dr == 0
                if (horiz and r == 3) or (not horiz and c == 4):
                    lf, lr, lw = 2, 2, 6.0
                elif (horiz and r in (1, 5)) or (not horiz and c in (1, 7)):
                    lf, lr, lw = 2, 2, 5.0
                else:
                    lf, lr, lw = 1, 1, 4.0
                net.add_edge(ids[(c, r)], ids[(c2, r2)], lanes_fwd=lf, lanes_rev=lr, lane_width=lw)

    # FLAT map -> curved avenues are safe anywhere; sweep the NORTH rows (ROWS only, no curve+curve).
    _, row_idx = _line_index_maps(net)
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        if abs(a[1] - b[1]) > 1e-6:
            continue
        ri = row_idx.get(round(a[1], 3))
        if ri == 1:
            _bow_edge(net, e, 18.0)
        elif ri == 2:
            _bow_edge(net, e, 12.0)

    net.ground_zones = [
        (-600.0, 250.0, 600.0, 470.0, "water"),    # the river / lakefront across the south
        (-600.0, 150.0, 600.0, 250.0, "sand"),     # beach / marina strip
        (-600.0, -120.0, -180.0, 150.0, "park"),   # riverside park
        (250.0, -470.0, 600.0, -150.0, "lot"),     # parking
    ]
    return net



def islandtown() -> RoadNetwork:
    """
    An ISLAND city: a flat downtown ringed by WATER on every side (waterfront + a marina beach), with
    curved avenues, a park, and a parking lot. No slope, so curves sweep freely. AI-safe throughout.
    """
    g = 130.0
    cols, rows = 9, 8
    net = RoadNetwork(name="IslandTown")
    ids, nid = {}, 0
    x0 = -(cols - 1) / 2.0 * g
    z0 = -(rows - 1) / 2.0 * g
    for r in range(rows):
        for c in range(cols):
            net.add_node((c * g + x0, r * g + z0), node_id=nid)
            ids[(c, r)] = nid
            nid += 1
    for r in range(rows):
        for c in range(cols):
            for dc, dr in ((1, 0), (0, 1)):
                c2, r2 = c + dc, r + dr
                if c2 >= cols or r2 >= rows:
                    continue
                horiz = dr == 0
                if (horiz and r == 3) or (not horiz and c == 4):
                    lf, lr, lw = 2, 2, 6.0
                elif (horiz and r in (1, 5)) or (not horiz and c in (2, 6)):
                    lf, lr, lw = 2, 2, 5.0
                else:
                    lf, lr, lw = 1, 1, 4.0
                net.add_edge(ids[(c, r)], ids[(c2, r2)], lanes_fwd=lf, lanes_rev=lr, lane_width=lw)

    # curved avenues (ROWS only) - flat map so curves are safe anywhere
    _, row_idx = _line_index_maps(net)
    amp_by_row = {1: 16.0, 4: 22.0, 6: 12.0}
    for e in net.edges:
        a, b = net.nodes[e.a].pos, net.nodes[e.b].pos
        if abs(a[1] - b[1]) > 1e-6:
            continue
        amp = amp_by_row.get(row_idx.get(round(a[1], 3)))
        if amp:
            _bow_edge(net, e, amp)

    # WATER ring (the island's edges) + a beach, a park, a lot in the interior
    net.ground_zones = [
        (-720.0, 360.0, 720.0, 520.0, "water"),    # north waterfront
        (-720.0, -520.0, 720.0, -360.0, "water"),  # south waterfront
        (470.0, -360.0, 720.0, 360.0, "water"),    # east waterfront
        (-720.0, -360.0, -470.0, 360.0, "water"),  # west waterfront
        (-460.0, 220.0, -130.0, 360.0, "sand"),    # a marina beach
        (130.0, -360.0, 460.0, -120.0, "park"),    # a park
        (-460.0, -360.0, -130.0, -120.0, "lot"),   # parking
    ]
    return net



def roundabout() -> RoadNetwork:
    """
    FEATURE TEST 1 - a ROUNDABOUT: a circular ring road (8 curved segments following a real circle)
    around a central island, with 4 approach roads tapping in N/E/S/W. FLAT, so the curves are safe;
    the open question is purely how the AI navigates a circular junction + the merges. Spawn is on the
    east approach. Boot `-circuit 0` to race 5 opponents AROUND the ring (the AI test), or `-race 0`
    to drive INTO it from the approach solo.
    """
    net = RoadNetwork(name="Roundabout")
    R = 56.0
    ring = []
    nid = 0
    for k in range(8):
        ang = math.radians(k * 45.0)
        net.add_node((R * math.cos(ang), R * math.sin(ang)), node_id=nid)
        ring.append(nid); nid += 1

    def add_arc(ai, bi, a_deg, b_deg):
        e = net.add_edge(ring[ai], ring[bi], lanes_fwd=1, lanes_rev=1, lane_width=5.0)
        shp = []
        for s in range(1, 6):
            ang = math.radians(a_deg + (s / 6.0) * (b_deg - a_deg))
            shp.append((R * math.cos(ang), R * math.sin(ang)))
        e.shape = tuple(shp)

    for k in range(8):
        add_arc(k, (k + 1) % 8, k * 45.0, (k + 1) * 45.0)

    OUT = 240.0
    for ring_k, (ox, oz) in {0: (OUT, 0.0), 2: (0.0, OUT), 4: (-OUT, 0.0), 6: (0.0, -OUT)}.items():
        net.add_node((ox, oz), node_id=nid)
        net.add_edge(ring[ring_k], nid, lanes_fwd=1, lanes_rev=1, lane_width=5.0)
        nid += 1

    net.spawn_near = (OUT - 20.0, 0.0)   # on the east approach, heading toward the circle
    return net



def bridgetown() -> RoadNetwork:
    """
    FEATURE TEST 2 - a ROAD OVER WATER: a road ARCHES over a river (a water channel) as a BRIDGE
    (`deck_height`>0), with the water kept visible UNDER the deck instead of cut out. A curved shore
    road makes it use the precise ground fill. Spawn on the west approach; `-race 0` drives you over
    the bridge solo (opponents on a bridge need arched AI rails - a follow-up).
    """
    net = RoadNetwork(name="BridgeTown")
    net.add_node((-210.0, 0.0), node_id=0)    # west outer
    net.add_node((-70.0, 0.0), node_id=1)     # west shore (bridge start)
    net.add_node((70.0, 0.0), node_id=2)      # east shore (bridge end)
    net.add_node((210.0, 0.0), node_id=3)     # east outer
    net.add_node((-70.0, 160.0), node_id=4)   # west shore cross
    net.add_node((70.0, 160.0), node_id=5)    # east shore cross
    net.add_edge(0, 1, lane_width=5.0)                              # west approach
    b = net.add_edge(1, 2, lane_width=5.0); b.deck_height = 2.5; b.num_verts = 8   # THE BRIDGE (dense cl -> fine BND)
    _bow_edge(net, b, 0.0)   # straight shape -> densified centreline so the deck ARCH is sampled
    net.add_edge(2, 3, lane_width=5.0)                              # east approach
    e4 = net.add_edge(1, 4, lane_width=5.0); _bow_edge(net, e4, 16.0)   # curved west shore road
    net.add_edge(4, 5, lane_width=5.0)                             # far shore road
    net.add_edge(5, 2, lane_width=5.0)                             # east shore road
    net.ground_zones = [(-45.0, -120.0, 45.0, 120.0, "water")]    # the river (x -45..45)
    net.spawn_near = (-185.0, 0.0)
    return net


def bigbridge() -> RoadNetwork:
    """
    EXPERIMENTAL BIG BRIDGE - a much LONGER (240u span), TALLER + STEEPER (deck_height 8 ~= 3x the gentle
    bridgetown grade, ~6 deg), WIDER (7u lanes) highway arch. Stress-tests the deck/AI/rail/soffit at scale
    and PROBES the bounce/launch/AI-crash limit on a steep grade (gentle is solved; how far does the
    big-facet + clean-SHOP recipe hold?). Keeps the known-good `bridgetown` untouched. AI runs
    (curved_grade=False - straight deck). Drive `-race 0`, or `-circuit 0` for opponents.
    """
    net = RoadNetwork(name="BigBridge")
    net.add_node((-300.0, 0.0), node_id=0)    # west outer - long runway to build speed for the climb
    net.add_node((-120.0, 0.0), node_id=1)    # west shore (bridge start)
    net.add_node((120.0, 0.0), node_id=2)     # east shore (bridge end)
    net.add_node((300.0, 0.0), node_id=3)     # east outer
    net.add_node((-120.0, 260.0), node_id=4)  # shore-road loop (so opponents have a circuit)
    net.add_node((120.0, 260.0), node_id=5)
    LW = 7.0
    net.add_edge(0, 1, lane_width=LW)                                  # long west approach
    b = net.add_edge(1, 2, lane_width=LW); b.deck_height = 8.0; b.num_verts = 14   # THE BIG STEEP DECK
    _bow_edge(net, b, 0.0)                                             # densify the straight cl -> arch samples
    net.add_edge(2, 3, lane_width=LW)                                  # east approach
    e4 = net.add_edge(1, 4, lane_width=LW); _bow_edge(net, e4, 24.0)   # curved shore road (the loop)
    net.add_edge(4, 5, lane_width=LW)
    net.add_edge(5, 2, lane_width=LW)
    net.ground_zones = [(-85.0, -220.0, 85.0, 220.0, "water")]        # a wide river under the span
    net.spawn_near = (-270.0, 0.0)
    return net


def thirdbridge() -> RoadNetwork:
    """
    EXPERIMENTAL CURVED + ARCHED bridge (the big step) - the deck ARCHES up/down AND CURVES left/right at
    once. `_bow_edge(amp>0)` bows the centreline sideways; `deck_height` arches it; the arch is ARC-LENGTH
    based so it rides the curve correctly. SOLO first - curve+grade historically NaN-crashes the AI
    (curved_grade gate auto-disables AI here), so step 2 will flip AI on to test the wheel.cpp clamps.
    Keeps bridgetown + bigbridge untouched.
    """
    net = RoadNetwork(name="ThirdBridge")
    net.add_node((-280.0, 0.0), node_id=0)    # west outer (approach)
    net.add_node((-100.0, 0.0), node_id=1)    # bridge start
    net.add_node((100.0, 0.0), node_id=2)     # bridge end
    net.add_node((280.0, 0.0), node_id=3)     # east outer
    net.add_node((-100.0, 260.0), node_id=4)  # shore-road loop
    net.add_node((100.0, 260.0), node_id=5)
    net.add_edge(0, 1, lane_width=6.0)                                  # west approach
    b = net.add_edge(1, 2, lane_width=6.0); b.deck_height = 4.0; b.num_verts = 18   # CURVED + ARCHED DECK
    _bow_edge(net, b, 35.0)   # the HORIZONTAL curve (deck bows ~35u sideways); deck_height = the arch
    net.add_edge(2, 3, lane_width=6.0)                                  # east approach
    e4 = net.add_edge(1, 4, lane_width=6.0); _bow_edge(net, e4, 20.0)   # curved shore road (loop)
    net.add_edge(4, 5, lane_width=6.0)
    net.add_edge(5, 2, lane_width=6.0)
    net.ground_zones = [(-80.0, -150.0, 80.0, 150.0, "water")]         # river under the curved span
    net.spawn_near = (-250.0, 0.0)
    return net


def epicbridge() -> RoadNetwork:
    """
    EPIC weaving roller-coaster bridge - 3 CONNECTED arched segments that each curve the OPPOSITE way
    (S-weave south->north->south) AND rise to DIFFERENT heights (humps 5/8/4u) across a big lake, with a
    shore road closing the loop for opponents. Combines varied vertical slopes + alternating horizontal
    curves + connected decks. Curve+grade AI is cracked, so opponents ride the whole coaster. The most
    complex deck yet. `-race 0` solo, `-circuit 0` with opponents.
    """
    net = RoadNetwork(name="EpicBridge")
    xs = [-420.0, -260.0, -90.0, 90.0, 260.0, 420.0]      # 6 nodes along the W->E span
    for i, x in enumerate(xs):
        net.add_node((x, 0.0), node_id=i)
    net.add_edge(0, 1, lane_width=6.0)                                 # long west approach
    s1 = net.add_edge(1, 2, lane_width=6.0); s1.deck_height = 5.0; s1.num_verts = 15; _bow_edge(net, s1, 55.0)   # hump1, bow +z
    s2 = net.add_edge(2, 3, lane_width=6.0); s2.deck_height = 8.0; s2.num_verts = 13; _bow_edge(net, s2, -55.0)  # hump2 PEAK, bow -z
    s3 = net.add_edge(3, 4, lane_width=6.0); s3.deck_height = 4.0; s3.num_verts = 14; _bow_edge(net, s3, 45.0)   # hump3, bow +z
    net.add_edge(4, 5, lane_width=6.0)                                 # long east approach
    # shore road closing the loop (so opponents have a circuit back) - lands well clear of the water
    net.add_node((-260.0, 360.0), node_id=6)
    net.add_node((260.0, 360.0), node_id=7)
    e6 = net.add_edge(1, 6, lane_width=6.0); _bow_edge(net, e6, 28.0)
    net.add_edge(6, 7, lane_width=6.0)
    e7 = net.add_edge(7, 4, lane_width=6.0); _bow_edge(net, e7, -28.0)
    net.ground_zones = [(-330.0, -130.0, 330.0, 150.0, "water")]       # big lake under the weaving deck
    net.spawn_near = (-390.0, 0.0)
    return net


def forkbridge() -> RoadNetwork:
    """
    BRANCHING bridge (Y-fork -> diamond) - a flat approach lands on an ISLAND where the road FORKS into
    two DIVERGING arched decks that reconnect at a second island = a drivable DIAMOND loop. The branches
    differ in EVERY way (the "go crazy" ask): branch A (north) is gentle 2-lane (humps 4/6u); branch B
    (south) is taller/steeper 3-lane asymmetric (2 fwd + 1 rev, humps 7/3u), weaving the opposite way.
    Curve+grade AI runs the whole diamond (up one branch, down the other). `-race 0` solo / `-circuit 0`.
    """
    net = RoadNetwork(name="ForkBridge")
    net.add_node((-380.0, 0.0), node_id=0)    # west land approach
    net.add_node((-240.0, 0.0), node_id=1)    # ISLAND FORK (degree 3)
    net.add_node((60.0, 200.0), node_id=2)    # branch A far (NE)
    net.add_node((60.0, -200.0), node_id=3)   # branch B far (SE)
    net.add_node((300.0, 0.0), node_id=4)     # EAST island (the branches reconnect)
    net.add_edge(0, 1, lane_width=6.0)                                  # west approach (flat, on land)
    # Branch A (north loop side): gentle, 2-lane (default 1+1)
    a1 = net.add_edge(1, 2, lane_width=6.0); a1.deck_height = 4.0; a1.num_verts = 15; _bow_edge(net, a1, 55.0)
    a2 = net.add_edge(2, 4, lane_width=6.0); a2.deck_height = 6.0; a2.num_verts = 14; _bow_edge(net, a2, -45.0)
    # Branch B (south loop side): taller/steeper, 3-lane ASYMMETRIC (2 fwd + 1 rev)
    b1 = net.add_edge(1, 3, lane_width=6.0); b1.deck_height = 7.0; b1.num_verts = 14
    b1.lanes_fwd = 2; b1.lanes_rev = 1; _bow_edge(net, b1, -55.0)
    b2 = net.add_edge(3, 4, lane_width=6.0); b2.deck_height = 3.0; b2.num_verts = 15
    b2.lanes_fwd = 2; b2.lanes_rev = 1; _bow_edge(net, b2, 40.0)
    net.ground_zones = [
        (-300.0, -270.0, 380.0, 270.0, "water"),     # the lake the diamond spans
        (-300.0, -55.0, -180.0, 55.0, "sand"),       # west FORK island (node1)
        (240.0, -55.0, 360.0, 55.0, "sand"),         # east island (node4)
    ]
    net.spawn_near = (-360.0, 0.0)
    return net


def wildbridge() -> RoadNetwork:
    """
    WILD per-piece showcase - each deck PIECE flexes its OWN rich internal geometry (the "go crazy per
    deck" ask), so you see them back to back:
      piece 1: S-CURVE (weaves left-then-right within one deck) while arching up-over-down;
      piece 2: DOUBLE hump (up-down-up-down in a single piece) + a curve;
      piece 3: EARLY-skewed slope (steep up, gentle down) + a curve;
      piece 4: LATE-skewed slope (gentle up, steep down) while S-curving.
    Slope profile AND horizontal curve vary per piece. Curve+grade AI runs it all. `-race 0` / `-circuit 0`.
    """
    net = RoadNetwork(name="WildBridge")
    xs = [-480.0, -300.0, -120.0, 60.0, 240.0, 420.0]
    for i, x in enumerate(xs):
        net.add_node((x, 0.0), node_id=i)
    net.add_edge(0, 1, lane_width=6.0)                                  # west approach
    # NOTE: gentled into the AI-safe envelope (the AI's ComputeDwtdw NaN-crashes on a TIGHT S-curve + grade
    # with opponents). Bigger facets (lower num_verts), smaller S-curve amp + deck heights - still clearly
    # S-curves / double / skews, just AI-survivable. Solo can go wilder; opponents need this envelope.
    p1 = net.add_edge(1, 2, lane_width=6.0); p1.deck_height = 5.0; p1.num_verts = 14
    _scurve_edge(net, p1, 26.0, 2)                                      # S-curve + symmetric arch
    p2 = net.add_edge(2, 3, lane_width=6.0); p2.deck_height = 5.0; p2.num_verts = 14
    p2.deck_profile = "double"; _bow_edge(net, p2, 28.0)              # DOUBLE hump + a bend
    p3 = net.add_edge(3, 4, lane_width=6.0); p3.deck_height = 5.0; p3.num_verts = 13
    p3.deck_profile = "early"; _bow_edge(net, p3, -28.0)             # steep-up / gentle-down + a bend
    p4 = net.add_edge(4, 5, lane_width=6.0); p4.deck_height = 5.0; p4.num_verts = 14
    p4.deck_profile = "late"; _scurve_edge(net, p4, 24.0, 2)         # gentle-up / steep-down + S-curve
    # shore road closing the loop for opponents (lands clear of the water)
    net.add_node((-300.0, 360.0), node_id=6)
    net.add_node((240.0, 360.0), node_id=7)
    e6 = net.add_edge(1, 6, lane_width=6.0); _bow_edge(net, e6, 26.0)
    net.add_edge(6, 7, lane_width=6.0)
    e7 = net.add_edge(7, 4, lane_width=6.0); _bow_edge(net, e7, -26.0)
    net.ground_zones = [(-380.0, -135.0, 360.0, 160.0, "water")]       # lake under the wild deck
    net.spawn_near = (-450.0, 0.0)
    return net


def custom_bridge(deck_height=4.0, deck_profile="arch", curve_amp=30.0, scurve_cycles=1,
                  lanes_fwd=1, lanes_rev=1, span=220.0, num_verts=15, water=True,
                  bank_deg=0.0) -> RoadNetwork:
    """A single PARAMETERIZED bridge driven by the Blender tuner sliders: approach -> one arched/curved
    deck (deck_height + deck_profile + a bow OR S-curve via scurve_cycles) -> approach, plus a shore loop
    so opponents can circuit it. NOT in PRESETS (it takes params) - the 'Build Custom Bridge' panel button
    calls it directly. Stays inside the AI-safe envelope by default (gentle curve amounts)."""
    net = RoadNetwork(name="CustomBridge")
    half = max(60.0, span / 2.0)
    loopz = abs(curve_amp) + 200.0
    net.add_node((-half - 150.0, 0.0), node_id=0)   # west approach
    net.add_node((-half, 0.0), node_id=1)           # bridge start
    net.add_node((half, 0.0), node_id=2)            # bridge end
    net.add_node((half + 150.0, 0.0), node_id=3)    # east approach
    net.add_node((-half, loopz), node_id=4)         # shore loop (so opponents have a circuit)
    net.add_node((half, loopz), node_id=5)
    lw = 6.0
    net.add_edge(0, 1, lane_width=lw, lanes_fwd=lanes_fwd, lanes_rev=lanes_rev)
    b = net.add_edge(1, 2, lane_width=lw, lanes_fwd=lanes_fwd, lanes_rev=lanes_rev)
    b.deck_height = float(deck_height); b.num_verts = max(6, int(num_verts)); b.deck_profile = deck_profile
    b.bank_deg = float(bank_deg)
    if int(scurve_cycles) >= 2:
        _scurve_edge(net, b, curve_amp, int(scurve_cycles))
    else:
        _bow_edge(net, b, curve_amp)
    net.add_edge(2, 3, lane_width=lw, lanes_fwd=lanes_fwd, lanes_rev=lanes_rev)
    e4 = net.add_edge(1, 4, lane_width=lw); _bow_edge(net, e4, 24.0)
    net.add_edge(4, 5, lane_width=lw)
    e5 = net.add_edge(5, 2, lane_width=lw); _bow_edge(net, e5, -24.0)
    if water:
        wz = abs(curve_amp) + 70.0
        net.ground_zones = [(-half + 10.0, -wz, half - 10.0, wz, "water")]
    net.spawn_near = (-half - 120.0, 0.0)
    return net


def bankbridge() -> RoadNetwork:
    """
    BANKED CURVE (the first 'roll' geometry) - a big sweeping turn whose deck TILTS/cambers INTO the bend
    like a racetrack or velodrome (Edge.bank_deg=22). The deck arches (deck_height=5) so the banked low
    inner edge stays above the water; the camber tapers to flat at the node ends. AI runs it. `-race 0`
    solo / `-circuit 0` opponents.
    """
    net = RoadNetwork(name="BankBridge")
    net.add_node((-360.0, 0.0), node_id=0)    # west approach
    net.add_node((-180.0, 0.0), node_id=1)    # turn start
    net.add_node((180.0, 0.0), node_id=2)     # turn end
    net.add_node((360.0, 0.0), node_id=3)     # east approach
    net.add_node((-180.0, 300.0), node_id=4)  # shore loop (so opponents have a circuit)
    net.add_node((180.0, 300.0), node_id=5)
    net.add_edge(0, 1, lane_width=6.0)                                  # west approach
    b = net.add_edge(1, 2, lane_width=6.0); b.deck_height = 5.0; b.num_verts = 16; b.bank_deg = 22.0
    _bow_edge(net, b, 80.0)   # a big sweeping bow -> the deck cambers INTO it
    net.add_edge(2, 3, lane_width=6.0)                                  # east approach
    e4 = net.add_edge(1, 4, lane_width=6.0); _bow_edge(net, e4, 26.0)   # shore road (loop)
    net.add_edge(4, 5, lane_width=6.0)
    e5 = net.add_edge(5, 2, lane_width=6.0); _bow_edge(net, e5, -26.0)
    net.ground_zones = [(-200.0, -120.0, 200.0, 200.0, "water")]       # water under the banked sweep
    net.spawn_near = (-330.0, 0.0)
    return net


def jumpbridge() -> RoadNetwork:
    """
    JUMP-BRIDGE (deck gap-jump) - a long RUNWAY to build speed, a RAMP rising to a launch LIP
    (deck_profile='ramp', ends high at deck_height), then a GAP over water you fly across onto a separate
    LANDING bridge. SOLO (the AI won't jump a gap) - the checkpoint trail hops the gap to mark the landing.
    Tune runway length / ramp height / gap width if you over- or under-shoot.
    """
    net = RoadNetwork(name="JumpBridge")
    net.add_node((-520.0, 0.0), node_id=0)    # runway start (spawn)
    net.add_node((-60.0, 0.0), node_id=1)     # ramp start
    net.add_node((40.0, 0.0), node_id=2)      # LAUNCH LIP (dead-end, high)
    net.add_node((160.0, 0.0), node_id=3)     # landing start (across the gap)
    net.add_node((560.0, 0.0), node_id=4)     # landing end
    net.add_edge(0, 1, lane_width=7.0)                                  # long flat runway (build speed)
    r = net.add_edge(1, 2, lane_width=7.0); r.deck_height = 12.0; r.num_verts = 10; r.deck_profile = "ramp"
    _bow_edge(net, r, 0.0)                                              # densify so the ramp is sampled
    land = net.add_edge(3, 4, lane_width=7.0); land.deck_height = 2.0; land.num_verts = 12
    _bow_edge(net, land, 0.0)
    net.ground_zones = [(20.0, -90.0, 150.0, 90.0, "water")]           # the gap is over water (x 40 -> 160)
    net.spawn_near = (-490.0, 0.0)
    return net


def spiralramp() -> RoadNetwork:
    """
    SPIRAL RAMP (the achievable 'helix') - a road that WINDS UP a conical hill: an INWARD spiral (radius
    shrinks as it climbs) on a cone terrain, coiling upward like a mountain road / parking-garage ramp. A
    TRUE constant-radius helix can't be done (it overlaps itself in x/z and the graph stores one height per
    spot); this inward spiral climbs WITHOUT self-overlap. SOLO (curve+grade -> AI off). The trail leads up.
    """
    import math as _m
    net = RoadNetwork(name="SpiralRamp")
    R = 240.0          # rim radius (tight-ish loops for a quick 360)
    H = 80.0           # peak height at the centre (steep descent)
    turns = 2.5        # times around

    def spiral_pt(t):                          # t 0..1: rim -> centre, winding inward
        ang = t * turns * 2.0 * _m.pi
        r = R * (1.0 - 0.7 * t)                # inner radius 0.3R
        return (r * _m.cos(ang), r * _m.sin(ang))

    # ONE continuous road whose SHAPE is the whole spiral - exactly like the bridge deck's curved shape,
    # just extended into a full coil. A SINGLE edge has NO internal intersection nodes, so the engine never
    # clips it into disjointed slabs (the old 95-edge mess); it sweeps one smooth ribbon along the spiral.
    SHP = 60
    net.add_node(spiral_pt(0.0), node_id=0)    # rim end (bottom)
    net.add_node(spiral_pt(1.0), node_id=1)    # centre end (top)
    e = net.add_edge(0, 1, lane_width=7.0)
    e.shape = tuple(spiral_pt(k / SHP) for k in range(1, SHP))   # intermediate spiral points
    e.num_verts = 130                          # enough to follow the coil, but BIG enough facets (~14u) to
    #                                            keep the wheel-contact smooth (fewer seams = less bumpy)

    def _terr(x, z, _R=R, _H=H):               # cone: high centre, 0 rim -> the spiral climbs to H
        r = _m.sqrt(x * x + z * z)
        return _H * max(0.0, 1.0 - r / _R)
    net.terrain = _terr
    # SMOOTH deck-like helix: flat_climb lifts the road UNIFORMLY (a flat ribbon) by the cone's CENTRELINE
    # height, so it climbs WITHOUT tilting sideways. Flat "lot" ground below (no water railings/facades);
    # no_scenery = a bare ramp.
    net.flat_climb = True
    net.ground_zones = [(-(R + 60.0), -(R + 60.0), R + 60.0, R + 60.0, "lot")]
    net.no_scenery = True
    net.race_opponents = 0                     # SOLO: aiVehicleActive::Init NaN-crashes initialising an AI
    #                                            car on this single-edge self-coiling road (engine wall,
    #                                            NOT the rail - rail is now correctly flat). Time-trial only.
    net.spawn_near = spiral_pt(0.9)            # START AT THE TOP (centre) -> race DOWNHILL out to the rim
    return net


def canyon() -> RoadNetwork:
    """
    FEATURE TEST 3 - a CANYON road: the terrain rises into steep CLIFFS on both sides while the road
    winds along the flat canyon FLOOR (|z|<32). Because the road stays on the flat floor it is a flat,
    AI-safe road - the cliffs are pure scenery (dirt walls). Drive `-race 0` through it. (A ROOFED
    tunnel is the harder cousin: it needs an actual bore cut through the terrain + a ceiling.)
    """
    net = RoadNetwork(name="Canyon")
    xs = [-360, -240, -120, 0, 120, 240, 360]
    for i, x in enumerate(xs):
        net.add_node((float(x), 0.0), node_id=i)
    for i in range(len(xs) - 1):
        e = net.add_edge(i, i + 1, lane_width=5.0)
        _bow_edge(net, e, 16.0 if i % 2 == 0 else -16.0)   # gentle S-wind, all within the flat floor

    def canyon_terrain(x, z):
        d = (abs(z) - 32.0) / 45.0          # cliffs rise from |z|=32 to |z|=77
        if d <= 0.0:
            return 0.0
        if d >= 1.0:
            return 30.0
        return 30.0 * (d * d * (3.0 - 2.0 * d))   # smoothstep wall
    net.terrain = canyon_terrain
    net.ground_zones = [(-500.0, 33.0, 500.0, 320.0, "dirt"),
                        (-500.0, -320.0, 500.0, -33.0, "dirt")]   # the cliff walls
    net.spawn_near = (0.0, 0.0)
    return net



def jump() -> RoadNetwork:
    """
    FEATURE TEST 4 - a JUMP: a long straight RUNWAY with a steep RAMP/hump near the far end, then a
    landing run. Floor it EAST (right) and launch off the ramp. (Reuses the bridge deck arch as a
    steep hump, densified so the arch is sampled. Solo player via `-race 0` - opponents would clip the
    un-arched AI rails.)
    """
    net = RoadNetwork(name="Jump")
    xs = [-500, -350, -200, -50, 120, 280, 420, 560]
    for i, x in enumerate(xs):
        net.add_node((float(x), 0.0), node_id=i)
    for i in range(1, len(xs) - 1):
        net.add_edge(i, i + 1, lane_width=6.0)    # rightward chain FIRST -> checkpoint route faces the ramp
    net.add_edge(0, 1, lane_width=6.0)            # left stub last
    ramp = [e for e in net.edges if e.a == 5 and e.b == 6][0]   # the hump (280 -> 420)
    ramp.deck_height = 10.0
    ramp.num_verts = 10                          # dense cl -> fine BND on the launch arch
    _bow_edge(net, ramp, 0.0)                     # densify so the arch is sampled
    net.spawn_near = (-350.0, 0.0)
    return net



def merge_networks(parts):
    """
    Combine several sub-networks into ONE map, each offset into its own region. `parts` is a list of
    (net, (ox, oz), name). Nodes are renumbered, edges/zones/terrains are translated by the region
    offset, and a `feature_spawns` list [(x, z, name), ...] is attached so the build can emit one
    CHECKPOINT race per feature (boot `-race 0/1/2/...` to inspect each without driving between them).
    """
    import dataclasses
    out = RoadNetwork(name="Showcase")
    out.ground_zones = []
    terrains = []          # (terrain_fn, ox, oz, region_bbox)
    spawns = []            # (x, z, name)
    counter = 0
    for net, (ox, oz), name in parts:
        idmap = {}
        for nid, node in net.nodes.items():
            idmap[nid] = counter
            out.add_node((node.pos[0] + ox, node.pos[1] + oz), node_id=counter)
            counter += 1
        for e in net.edges:
            shp = tuple((px + ox, pz + oz) for (px, pz) in e.shape)
            out.edges.append(dataclasses.replace(e, a=idmap[e.a], b=idmap[e.b], shape=shp))
        for (x0, z0, x1, z1, kind) in getattr(net, "ground_zones", []):
            out.ground_zones.append((x0 + ox, z0 + oz, x1 + ox, z1 + oz, kind))
        terr = getattr(net, "terrain", None)
        if terr is not None:
            xs = [n.pos[0] for n in net.nodes.values()]; zs = [n.pos[1] for n in net.nodes.values()]
            bbox = (min(xs) - 500 + ox, min(zs) - 500 + oz, max(xs) + 500 + ox, max(zs) + 500 + oz)
            terrains.append((terr, ox, oz, bbox))
        sn = getattr(net, "spawn_near", None) or (next(iter(net.nodes.values())).pos)
        spawns.append((sn[0] + ox, sn[1] + oz, name))
    if terrains:
        def combined(X, Z):
            for terr, ox, oz, (bx0, bz0, bx1, bz1) in terrains:
                if bx0 <= X <= bx1 and bz0 <= Z <= bz1:
                    return terr(X - ox, Z - oz)
            return 0.0
        out.terrain = combined
    out.feature_spawns = spawns
    out.spawn_near = (spawns[0][0], spawns[0][1])
    return out


def plaza() -> RoadNetwork:
    """
    A pedestrian PLAZA - a concrete town square ringed by a kerb-less loop road so you can drive
    straight onto the open concrete, with props scattered across it.
    """
    net = RoadNetwork(name="Plaza")
    pts = [(-140.0, -140.0), (140.0, -140.0), (140.0, 140.0), (-140.0, 140.0)]
    for i, (x, z) in enumerate(pts):
        net.add_node((x, z), node_id=i)
    for i in range(4):
        net.add_edge(i, (i + 1) % 4, lane_width=5.0, sidewalk_fwd=False, sidewalk_rev=False)
    net.ground_zones = [(-140.0, -140.0, 140.0, 140.0, "plaza")]   # concrete interior
    net.spawn_near = (-140.0, 0.0)
    return net


def industrial() -> RoadNetwork:
    """
    An INDUSTRIAL district - a grid of WIDE haul roads through paved IND_ASPHALT yards, with a concrete
    loading bay and parking pockets. Gritty + sparse: cones/barrels instead of trees, warehouse-style
    building fronts lining the streets. Drive the grid; solo `-race 0`.
    """
    net = RoadNetwork(name="Industrial")
    cols = [0.0, 130.0, 260.0, 390.0]
    rows = [0.0, 130.0, 260.0]
    nid, k = {}, 0
    for r, z in enumerate(rows):
        for c, x in enumerate(cols):
            net.add_node((x, z), node_id=k); nid[(c, r)] = k; k += 1
    for r in range(len(rows)):                                  # horizontal haul roads
        for c in range(len(cols) - 1):
            net.add_edge(nid[(c, r)], nid[(c + 1, r)], lane_width=6.0)
    for c in range(len(cols)):                                  # cross streets
        for r in range(len(rows) - 1):
            net.add_edge(nid[(c, r)], nid[(c, r + 1)], lane_width=6.0)
    # SPECIFIC pockets first (the zone loop takes the FIRST match), then the industrial catch-all.
    net.ground_zones = [
        (285.0, 20.0, 365.0, 110.0, "lot"),               # a truck parking lot (cones/barrels)
        (20.0, 150.0, 110.0, 240.0, "plaza"),             # a concrete loading bay
        (-60.0, -60.0, 450.0, 320.0, "industrial"),       # the paved IND_ASPHALT yards (catch-all)
    ]
    net.spawn_near = (0.0, 0.0)
    return net


def overpass() -> RoadNetwork:
    """
    An OVERPASS - a ground-level road A with a SECOND road B arching UP and OVER it, crossing in x,z at a
    different HEIGHT with NO junction (the roads don't share a node, so the compiler never connects them).
    Drive UNDER the elevated deck on A, or take road B's ramp up and OVER. Reuses the bridge deck_height
    arch (BIG facets per the loop lesson). Solo `-race 0` (B is curved+graded -> AI off on it).
    """
    net = RoadNetwork(name="Overpass")
    # lower road A: straight E-W at ground level
    net.add_node((-240.0, 0.0), node_id=0)
    net.add_node((240.0, 0.0), node_id=1)
    net.add_edge(0, 1, lane_width=6.0)
    # upper road B: N-S, arches up to deck_height 6 (clears road A + the car) and crosses A at (0,0)
    net.add_node((0.0, -240.0), node_id=2)
    net.add_node((0.0, 240.0), node_id=3)
    b = net.add_edge(2, 3, lane_width=5.0)
    b.deck_height = 6.0          # clears a car underneath (incl. the soffit underside); lower = more visible
    b.num_verts = 8             # BIG facets (the SEAVIEW-loop lesson: coarse = no contact sawtooth)
    _bow_edge(net, b, 0.0)      # densify B's straight cl so the arch actually samples
    # An OPEN paved 'lot' all around SUPPRESSES the building facades (so you SEE the two roads crossing,
    # not walled in) while the roads keep their sidewalks -> valid drive cells (no fall-through).
    net.ground_zones = [(-300.0, -300.0, 300.0, 300.0, "lot")]
    net.spawn_near = (-160.0, 0.0)   # on road A, driving EAST toward + under the overpass
    return net


def eltrain() -> RoadNetwork:
    """
    An EL-TRAIN (elevated train line, Chicago-style) - drive the ground road while a raised train line runs
    alongside on trestle supports. v1 = the STATIC structure: DP_LEFT6 trestle supports + R_L_TRAIN cars
    placed at track height via the extra_props hook. (Track mesh + the moving-train ANIMATION are the next
    passes.) Solo `-race 0`.
    """
    from src.constants.props import Prop
    net = RoadNetwork(name="ElTrain")
    net.add_node((-320.0, 0.0), node_id=0)
    net.add_node((320.0, 0.0), node_id=1)
    net.add_edge(0, 1, lane_width=6.0)
    net.ground_zones = [(-360.0, -120.0, 360.0, 120.0, "lot")]   # open paved, no facades to block the view
    props = []
    TRACK_Z = 24.0      # the el-train line runs ~24u to one side of the road
    for x in range(-300, 301, 20):     # trestle support POLES every 20u (the foundation)
        props.append({"name": Prop.ELTRAIN_SUPPORT_WIDE, "offset": (float(x), 0.0, TRACK_Z), "angle": 90})
    # NOTE: the moving TRAIN is an animation set in the Map Editor (deferred, NOT a static prop). The
    # track SPAN between the poles still needs an asset: dp_trainsupport is flagged un-placeable, tfskyway
    # is the facade candidate (flagged "no visibility"). TODO: track span here.
    net.extra_props = props
    net.spawn_near = (-220.0, 0.0)     # on the ground road, the el-train line off to the side
    return net


def marina() -> RoadNetwork:
    """
    A MARINA waterfront - a promenade road with a pier/boardwalk strip + water alongside it (the
    water-facing side gets the T_RAIL railing automatically).
    """
    net = RoadNetwork(name="Marina")
    xs = [-220.0, -110.0, 0.0, 110.0, 220.0]
    for i, x in enumerate(xs):
        net.add_node((x, 0.0), node_id=i)
    for i in range(4):
        net.add_edge(i, i + 1, lane_width=5.0, sidewalk_rev=False)   # no kerb on the water side
    net.ground_zones = [(-300.0, 20.0, 300.0, 220.0, "water"),       # the harbour
                        (-300.0, 7.0, 300.0, 20.0, "pier")]          # boardwalk between road + water
    net.spawn_near = (0.0, 0.0)
    return net


def gapjump() -> RoadNetwork:
    """
    A real GAP JUMP - drive up a terrain ramp to a raised launch deck, fly off the ledge across a gap,
    and land on the landing strip beyond. Terrain-based (like the canyon) so the road follows the ramp
    coherently. Floor it EAST. Solo `-race`.
    """
    net = RoadNetwork(name="GapJump")
    for nid, x in ((0, -200.0), (1, 0.0), (2, 300.0)):       # approach stub + ramp to the ledge
        net.add_node((x, 0.0), node_id=nid)
    net.add_edge(1, 2, lane_width=6.0)                        # ramp FIRST -> route/spawn faces the jump
    net.add_edge(0, 1, lane_width=6.0)
    for nid, x in ((3, 430.0), (4, 630.0)):                  # the landing strip (separate component)
        net.add_node((x, 0.0), node_id=nid)
    net.add_edge(3, 4, lane_width=8.0)

    def gj_terrain(x, z):
        if x < 40.0:
            return 0.0
        if x < 290.0:
            tt = (x - 40.0) / 250.0
            return 14.0 * (tt * tt * (3.0 - 2.0 * tt))       # smooth ramp up to launch height
        if x < 360.0:
            return 14.0                                       # flat launch deck past the road end
        return 0.0                                            # cliff = the gap to clear
    net.terrain = gj_terrain
    net.spawn_near = (0.0, 0.0)
    return net


def lakering() -> RoadNetwork:
    """
    A LAKE + RING ROAD - a circular road looping around a central lake (water zone). Drive the loop
    around the water; the inner shore reads as a waterfront. Spawn on the ring (a degree-2 loop node).
    """
    net = RoadNetwork(name="LakeRing")
    R = 130.0
    N = 12
    for k in range(N):
        ang = math.radians(k * 360.0 / N)
        net.add_node((R * math.cos(ang), R * math.sin(ang)), node_id=k)
    for k in range(N):
        e = net.add_edge(k, (k + 1) % N, lane_width=5.0)
        a_deg, b_deg = k * 360.0 / N, (k + 1) * 360.0 / N
        e.shape = tuple((R * math.cos(math.radians(a_deg + (s / 6.0) * (b_deg - a_deg))),
                         R * math.sin(math.radians(a_deg + (s / 6.0) * (b_deg - a_deg)))) for s in range(1, 6))
    net.ground_zones = [(-92.0, -92.0, 92.0, 92.0, "water")]   # the lake, fully inside the ring
    net.spawn_near = (R, 0.0)
    return net


def tunnel() -> RoadNetwork:
    """
    A ROOFED TUNNEL - drive through a covered section: vertical walls + a down-facing ceiling wrap the
    road. The two middle edges are tunnels; the approaches are open road. Floor it EAST into it.
    """
    net = RoadNetwork(name="Tunnel")
    xs = [-320.0, -150.0, 0.0, 150.0, 320.0]
    for i, x in enumerate(xs):
        net.add_node((x, 0.0), node_id=i)
    net.add_edge(1, 2, lane_width=5.0, sidewalk_fwd=False, sidewalk_rev=False)   # tunnel (route-first)
    net.add_edge(2, 3, lane_width=5.0, sidewalk_fwd=False, sidewalk_rev=False)   # tunnel
    net.add_edge(3, 4, lane_width=5.0)
    net.add_edge(0, 1, lane_width=5.0)
    for ed in net.edges:
        if abs(net.nodes[ed.a].pos[0]) <= 150.0 and abs(net.nodes[ed.b].pos[0]) <= 150.0:
            ed.tunnel_height = 8.0
    net.spawn_near = (-150.0, 0.0)
    return net


def switchback() -> RoadNetwork:
    """
    A SWITCHBACK hill climb - a zigzag road climbing a hillside (terrain rises in +z), reversing
    across the face at each bend. Solo (the curve+grade combo is fine for a player, not the AI).
    """
    net = RoadNetwork(name="Switchback")
    pts = [(-110.0, 0.0), (110.0, 55.0), (-110.0, 110.0), (110.0, 165.0), (-110.0, 220.0), (110.0, 275.0)]
    for i, (x, z) in enumerate(pts):
        net.add_node((x, z), node_id=i)
    for i in range(1, 5):
        net.add_edge(i, i + 1, lane_width=6.0)      # climb edges first -> route/spawn faces UP
    net.add_edge(0, 1, lane_width=6.0)

    def hill(x, z):
        return z * 0.13                              # the hillside rises with z
    net.terrain = hill
    net.spawn_near = (110.0, 55.0)
    return net


def showcase() -> RoadNetwork:
    """
    FEATURE SHOWCASE - every expansion feature in ONE map, each in its own region with its own
    CHECKPOINT race so you can flip between them fast: `-race 0` Jump, `-race 1` Canyon, `-race 2`
    Bridge, `-race 3` Roundabout. Solo player (0 opponents), so the curved/sloped/arched bits are safe.
    """
    return merge_networks([
        (jump(),       (0.0, 0.0),      "Jump"),
        (canyon(),     (0.0, 1800.0),   "Canyon"),
        (bridgetown(), (2200.0, 0.0),   "Bridge"),
        (roundabout(), (2200.0, 1800.0),"Roundabout"),
        (plaza(),      (0.0, 3600.0),   "Plaza"),
        (marina(),     (2200.0, 3600.0),"Marina"),
        (gapjump(),    (0.0, 5400.0),   "GapJump"),
        (lakering(),   (2200.0, 5400.0),"LakeRing"),
        (tunnel(),     (0.0, 7200.0),   "Tunnel"),
        (switchback(), (2200.0, 7200.0),"Switchback"),
    ])


def terrain_from_kind(kind: str, height: float = 18.0, extent: float = 800.0):
    """
    Map a NAMED terrain profile -> a callable h(x,z)->y, for the Blender custom-city builds (the panel
    can't author a Python function, so it picks a name + a height). All profiles are GENTLE (AI-safe) and
    stay >= 0 so roads never dip underground. `extent` ~ half the city's width.
        flat   -> None (no terrain)
        hills  -> gentle rolling hills (0..height)
        corner -> a smooth rise toward one corner (0 at SW, height at NE)
        cone   -> a central peak (height at centre, 0 at the rim) - like a hill town
    """
    import math as _m
    if not kind or kind == "flat":
        return None
    if kind == "hills":
        return lambda x, z: height * 0.5 * (1.0 + _m.sin(x / 260.0) * _m.cos(z / 300.0))
    if kind == "corner":
        return lambda x, z: height * min(1.0, max(0.0, (x + extent) / (2.0 * extent))) \
                                   * min(1.0, max(0.0, (z + extent) / (2.0 * extent)))
    if kind == "cone":
        return lambda x, z: height * max(0.0, 1.0 - _m.hypot(x, z) / extent)
    return None


PRESETS = {
    "small": small,
    "switchback": switchback,
    "tunnel": tunnel,
    "lakering": lakering,
    "gapjump": gapjump,
    "plaza": plaza,
    "industrial": industrial,
    "overpass": overpass,
    "eltrain": eltrain,
    "marina": marina,
    "showcase": showcase,
    "jump": jump,
    "canyon": canyon,
    "bridgetown": bridgetown,
    "bigbridge": bigbridge,
    "thirdbridge": thirdbridge,
    "epicbridge": epicbridge,
    "forkbridge": forkbridge,
    "wildbridge": wildbridge,
    "bankbridge": bankbridge,
    "jumpbridge": jumpbridge,
    "spiralramp": spiralramp,
    "roundabout": roundabout,
    "islandtown": islandtown,
    "megacity": megacity,
    "riverside": riverside,
    "slopetest": slopetest,
    "halfchicago": halfchicago,
    "blenderdemo": blenderdemo,
    "metrohills": metrohills,
    "medium": medium,
    "large": large,
    "mega": mega,
    "downtown": downtown,
    "avenues": avenues,
    "manhattan": manhattan,
    "boulevard": boulevard,
    "parkway": parkway,
    "highway": highway,
    "metropolis": metropolis,
    "megacity2": megacity2,
    "hills": hills,
    "curvyhills": curvyhills,
    "bumps": bumps,
    "sanfran": sanfran,
    "alps": alps,
}


# Global SCALE applied to EVERY preset (Robin: roads felt a touch narrow/short vs car speed). Grows node
# spacing + road/sidewalk widths + deck heights ~15% but KEEPS num_verts + lane counts, so collision facets
# also grow with the span (which reduces the closest-point bounce). Tune this one number to taste.
ROADNET_SCALE = 1.15


def scale_network(net, f):
    """Uniformly scale a whole network by factor f: node positions, road/sidewalk/median/curb widths, deck
    heights, shape points, ground zones, spawn, terrain, props. KEEPS num_verts + lane counts so the facets
    grow with the span (helps the wheel-contact bounce). Mutates and returns net."""
    if not f or f == 1.0:
        return net
    for n in net.nodes.values():
        n.pos = (n.pos[0] * f, n.pos[1] * f)
    for e in net.edges:
        e.lane_width *= f; e.sidewalk_width *= f; e.median_width *= f
        e.deck_height *= f; e.curb_width *= f
        if e.shape:
            e.shape = tuple((px * f, pz * f) for (px, pz) in e.shape)
    if getattr(net, "ground_zones", None):
        net.ground_zones = [(a * f, b * f, c * f, d * f, *rest) for (a, b, c, d, *rest) in net.ground_zones]
    if getattr(net, "spawn_near", None):
        net.spawn_near = (net.spawn_near[0] * f, net.spawn_near[1] * f)
    if getattr(net, "terrain", None):
        _t = net.terrain
        net.terrain = lambda x, z, _t=_t, _f=f: _f * _t(x / _f, z / _f)
    if getattr(net, "extra_props", None):
        for p in net.extra_props:
            ox, oy, oz = p.get("offset", (0.0, 0.0, 0.0))
            p["offset"] = (ox * f, oy * f, oz * f)
    return net


def build_preset(name: str) -> RoadNetwork:
    key = str(name).strip().lower()
    if key not in PRESETS:
        raise ValueError(f"unknown ROADNET_CITY preset {name!r}; options: {sorted(PRESETS)}")
    return scale_network(PRESETS[key](), ROADNET_SCALE)

"""
Scenery generation from a road-network graph (Phase 4).

`generate_props(compiled)` returns a `prop_list` in the editor's dict format
(consumed by `BangerEditor.process_all`): street-lights spaced along every sidewalk,
trees scattered through the grass blocks, and fire hydrants at the intersection corners.

`generate_facades(compiled)` returns a `facade_list` (consumed by `FacadeEditor.create`):
building fronts around the perimeter of each grass block, facing the road.

Everything is derived from the SAME `CompiledNetwork` the geometry + AI come from, so the
scenery lines up with the roads with no hand placement.
"""
import math
from src.game.mapgen.roadnet.build_city import _deck_lift, _bank_slopes
from typing import List, Dict

from src.game.mapgen.roadnet.network_compiler import CompiledNetwork
from src.game.mapgen.roadnet.geometry import normalize2, lateral_dir
from src.game.mapgen.roadnet.build_city import (_road_half_width, _free_intervals,
                                                GRASS_MARGIN, CURB_HEIGHT, FACADE_INSET)


def _heading_deg(fx: float, fz: float) -> float:
    """Angle (degrees) whose face vector (cos,0,sin) points along (fx,fz)."""
    return math.degrees(math.atan2(fz, fx))


def _lattice(compiled: CompiledNetwork):
    nodes = list(compiled.network.nodes.values())
    xs = sorted({round(n.pos[0], 3) for n in nodes})
    zs = sorted({round(n.pos[1], 3) for n in nodes})
    hw = max((_road_half_width(e) for e in compiled.network.edges), default=5.0)
    return xs, zs, hw


def _grass_rects(compiled: CompiledNetwork):
    """The same non-overlapping grass rectangles the ground is tiled from (x0,z0,x1,z1)."""
    xs, zs, hw = _lattice(compiled)
    fx = _free_intervals(xs, xs[0] - GRASS_MARGIN, xs[-1] + GRASS_MARGIN, hw)
    fz = _free_intervals(zs, zs[0] - GRASS_MARGIN, zs[-1] + GRASS_MARGIN, hw)
    return [(x0, z0, x1, z1) for (x0, x1) in fx for (z0, z1) in fz]


def _interior_grass_rects(compiled: CompiledNetwork):
    """Grass rectangles fully enclosed by roads (exclude the outer border tiles)."""
    xs, zs, hw = _lattice(compiled)
    fx = _free_intervals(xs, xs[0] - GRASS_MARGIN, xs[-1] + GRASS_MARGIN, hw)
    fz = _free_intervals(zs, zs[0] - GRASS_MARGIN, zs[-1] + GRASS_MARGIN, hw)
    # The first/last interval in each axis is the border (touches the margin); drop them.
    fx_in = fx[1:-1] if len(fx) > 2 else []
    fz_in = fz[1:-1] if len(fz) > 2 else []
    return [(x0, z0, x1, z1) for (x0, x1) in fx_in for (z0, z1) in fz_in]


def generate_facades(compiled: CompiledNetwork, *, panel: float = 16.0) -> List[Dict]:
    """
    Building fronts swept ALONG each road (both sides), FACING THE STREET — so they follow
    curves dynamically instead of clamping to rectangular blocks.

    For each road section we walk the SAME clipped (and, for curves, densified) centreline the
    mesh uses, offset laterally to the building line (`road_half_width + FACADE_INSET`), and emit
    one facade panel per segment. The FRONT faces 90° CCW of offset->end, so the +side uses
    forward order and the -side reversed order -> both fronts point at the road. Curved roads
    have short segments (1 panel each, following the bend); straight roads are one long segment
    the FCD splitter tiles along its axis.
    """
    from src.constants.facades import Facade, FcdFlags
    from src.game.mapgen.roadnet.build_city import (_section_centerline, _road_half_width,
                                                    GRASS_CARPET_Y, _has_curves, _bound_for_section)

    # Spatial DISTRICTS — different facade families per area so the city reads as distinct
    # neighbourhoods (downtown towers in the core, Chinatown to the west, a shop strip to the east).
    DOWNTOWN = [Facade.BUILDING_DOWNTOWN_1, Facade.BUILDING_DOWNTOWN_2, Facade.BUILDING_DOWNTOWN_3,
                Facade.BUILDING_DOWNTOWN_4, Facade.BUILDING_DOWNTOWN_5, Facade.BUILDING_DOWNTOWN_6]
    CHINATOWN = [Facade.BUILDING_CHINATOWN_1, Facade.BUILDING_CHINATOWN_2, Facade.BUILDING_CHINATOWN_3,
                 Facade.SHOP_CHINATOWN_1, Facade.SHOP_CHINATOWN_2, Facade.SHOP_CHINATOWN_3,
                 Facade.SHOP_CHINATOWN_4, Facade.SHOP_CHINATOWN_5]
    SHOPS = [Facade.SHOP_CHINATOWN_6, Facade.SHOP_CHINATOWN_7, Facade.SHOP_CHINATOWN_8,
             Facade.SHOP_CHINATOWN_9, Facade.SHOP_CHINATOWN_10, Facade.SHOP_CHINATOWN_FOODS,
             Facade.SHOP_CHINATOWN_LIQUOR]

    def _palette_for(cx: float):
        if cx < -120.0:
            return CHINATOWN
        if cx > 120.0:
            return SHOPS
        return DOWNTOWN

    base_y = GRASS_CARPET_Y if _has_curves(compiled) else CURB_HEIGHT

    box = {}
    for nid in compiled.network.nodes:
        inc = [e for e in compiled.network.edges if e.a == nid or e.b == nid]
        box[nid] = max((_road_half_width(e) for e in inc), default=5.0)

    # OPEN areas must stay open: don't put a building wall on the side of a road that faces a
    # park / lot / sand zone. WATER is special: a road that faces water gets a RAIL_WATER railing
    # (a waterfront fence at the sidewalk edge) instead of a building or nothing.
    zones = getattr(compiled.network, "ground_zones", None) or []
    OPEN_KINDS = {"water", "sand", "park", "lot"}

    def _zone_at(px, pz):
        for (zx0, zz0, zx1, zz1, k) in zones:
            if zx0 <= px <= zx1 and zz0 <= pz <= zz1:
                return k
        return None

    facs: List[Dict] = []
    bi = 0
    for si, s in enumerate(compiled.sections):
        e = s.edge
        cl = _section_centerline(s, box.get(e.a, 5.0), box.get(e.b, 5.0))
        if cl is None:
            continue
        room = _bound_for_section(si)            # this road's cell: facades portal-cull WITH the road
        _deck = getattr(e, "deck_height", 0.0)   # bridge: lift railings onto the arched deck
        _tot = cl[-1][2] or 1.0
        arch = [_deck_lift(c[2] / _tot, _deck, getattr(e, "deck_profile", "arch")) for c in cl] if _deck > 0.0 else [0.0] * len(cl)
        bank = _bank_slopes(e, cl, arch, _deck)   # camber: tilt facades with the banked sidewalk edge
        lb = _road_half_width(e) + FACADE_INSET
        # PERF: emit facade/railing panels at a fixed ~8u world spacing, NOT one per centreline point.
        # A dense (num_verts=120) bridge would otherwise spawn ~240 railing facades = 240 draw calls.
        _seg = (cl[-1][2] / (len(cl) - 1)) if len(cl) > 1 else 1.0e9
        _stride = max(1, int(round(8.0 / max(_seg, 0.5))))
        mp, mf, _ = cl[len(cl) // 2]             # section midpoint, for the open-zone probe
        for has_sw, sgn in ((e.sidewalk_fwd, 1.0), (e.sidewalk_rev, -1.0)):
            if not has_sw:
                continue
            px = mp[0] + lateral_dir(mf)[0] * (lb + 12.0) * sgn
            pz = mp[1] + lateral_dir(mf)[1] * (lb + 12.0) * sgn
            behind = _zone_at(px, pz)
            if behind in OPEN_KINDS and behind != "water":
                continue                         # park/lot/sand -> open, no facade
            side_rail = (behind == "water")      # water -> a railing instead of buildings
            # building-line points for this side (offset by the local lateral frame)
            line = [(p[0] + lateral_dir(f)[0] * lb * sgn, p[1] + lateral_dir(f)[1] * lb * sgn)
                    for (p, f, _s) in cl]
            for i in range(0, len(line) - 1, _stride):
                j = min(i + _stride, len(line) - 1)
                o, en = (line[i], line[j]) if sgn > 0 else (line[j], line[i])
                io, ie = (i, j) if sgn > 0 else (j, i)
                dx, dz = en[0] - o[0], en[1] - o[1]
                if abs(dx) < 0.5 and abs(dz) < 0.5:
                    continue
                pk = _zone_at(o[0], o[1])
                if pk in OPEN_KINDS and pk != "water":
                    continue                     # panel over an open (non-water) zone -> drop
                axis = "x" if abs(dx) >= abs(dz) else "z"
                if side_rail or pk == "water":
                    name = Facade.RAIL_WATER     # waterfront railing along the sidewalk edge
                else:
                    pal = _palette_for((o[0] + en[0]) * 0.5)   # district by THIS panel's x
                    name = pal[bi % len(pal)]; bi += 1
                # room = this road's cell (201+): facades/railings portal-cull WITH their street.
                facs.append({"flags": FcdFlags.FRONT, "name": name, "separator": panel, "axis": axis,
                             "room": room,
                             "offset": (o[0], base_y + arch[io] + lb * sgn * bank[io], o[1]),
                             "end": (en[0], base_y + arch[ie] + lb * sgn * bank[ie], en[1])})
    terrain = getattr(compiled.network, "terrain", None)
    if terrain is not None:
        for fc in facs:
            ox, oy, oz = fc["offset"]; ex, ey, ez = fc["end"]
            fc["offset"] = (ox, oy + terrain(ox, oz), oz)
            fc["end"] = (ex, ey + terrain(ex, ez), ez)
    return facs


def _at_arc(cl, t):
    """Interpolate (point2d, forward2d) at arc-length t along a centreline [(p, f, arc), ...]."""
    for i in range(1, len(cl)):
        if cl[i][2] >= t:
            p0, f0, s0 = cl[i - 1]; p1, f1, s1 = cl[i]
            u = (t - s0) / max(s1 - s0, 1e-6)
            return (p0[0] + u * (p1[0] - p0[0]), p0[1] + u * (p1[1] - p0[1])), (f1 if u >= 0.5 else f0)
    return cl[-1][0], cl[-1][1]


def generate_props(compiled: CompiledNetwork, *, light_spacing: float = 32.0,
                   tree_spacing: float = 60.0, hydrants: bool = True) -> List[Dict]:
    if getattr(compiled.network, "no_scenery", False):
        return []                              # bare road (e.g. a ramp): no lamps / trees / hydrants
    from src.constants.props import Prop
    from src.game.mapgen.roadnet.build_city import _section_centerline

    props: List[Dict] = []
    # Sidewalk furniture mix — mostly lamps, with benches / bins / mailboxes / meters / poles
    # interspersed so streets aren't a monotonous row of identical lights.
    FURNITURE = [Prop.LIGHT_SIDEWALK, Prop.LIGHT_SIDEWALK, Prop.BENCH, Prop.LIGHT_SIDEWALK,
                 Prop.BIN, Prop.LIGHT_SIDEWALK, Prop.MAILBOX, Prop.LIGHT_SIDEWALK,
                 Prop.PARKING_METER, Prop.LIGHT_SIDEWALK, Prop.TELEPHONE_POLE]
    fi = 0
    _, _, hw = _lattice(compiled)

    box = {}
    for nid in compiled.network.nodes:
        inc = [e for e in compiled.network.edges if e.a == nid or e.b == nid]
        box[nid] = max((_road_half_width(e) for e in inc), default=5.0)

    # 1) Street-lights spaced along the (curved) sidewalk centre, both sides — they FOLLOW the
    #    road because we walk the same clipped/densified centreline the mesh + facades use.
    for s in compiled.sections:
        e = s.edge
        if not (e.sidewalk_fwd or e.sidewalk_rev):
            continue
        cl = _section_centerline(s, box.get(e.a, 5.0), box.get(e.b, 5.0))
        if cl is None:
            continue
        total = cl[-1][2]
        sw_lat = _road_half_width(e) - e.sidewalk_width * 0.5      # centre of the sidewalk strip
        t = min(light_spacing * 0.5, total * 0.5)
        while t < total:
            p, f = _at_arc(cl, t)
            xd = lateral_dir(f)
            for side, has_sw in ((1.0, e.sidewalk_fwd), (-1.0, e.sidewalk_rev)):
                if not has_sw:
                    continue
                px, pz = p[0] + xd[0] * sw_lat * side, p[1] + xd[1] * sw_lat * side
                ang = _heading_deg(-xd[0] * side, -xd[1] * side)   # face the road
                name = FURNITURE[fi % len(FURNITURE)]; fi += 1
                props.append({"name": name, "offset": (px, CURB_HEIGHT, pz), "angle": ang})
            t += light_spacing

    # 2) Grass-block scenery, AREA-AWARE: dense trees + benches in PARKS, cones/barrels in the
    #    parking LOT, sparse trees on plain grass, nothing on water.
    zones = getattr(compiled.network, "ground_zones", None) or []

    def _zone(x, z):
        for (zx0, zz0, zx1, zz1, k) in zones:
            if zx0 <= x <= zx1 and zz0 <= z <= zz1:
                return k
        return "grass"

    for (x0, z0, x1, z1) in _grass_rects(compiled):
        w, h = x1 - x0, z1 - z0
        if w < 12.0 or h < 12.0:
            continue
        kind = _zone((x0 + x1) * 0.5, (z0 + z1) * 0.5)
        if kind == "water":
            continue                                                   # no scenery on the lake
        spacing = (tree_spacing * 0.75) if kind == "park" else tree_spacing   # parks are denser
        nx = max(1, int(w // spacing))
        nz = max(1, int(h // spacing))
        for i in range(nx):
            for j in range(nz):
                px = x0 + (i + 0.5) * (w / nx)
                pz = z0 + (j + 0.5) * (h / nz)
                if kind in ("lot", "industrial"):
                    name = Prop.CONE if (i + j) % 2 == 0 else Prop.BARREL_BLUE
                elif kind == "park" and (i + j) % 4 == 0:
                    name = Prop.BENCH                                   # benches sprinkled in parks
                else:
                    name = Prop.TREE_WIDE if (i + j) % 2 == 0 else Prop.TREE_SLIM
                props.append({"name": name, "offset": (px, CURB_HEIGHT, pz), "angle": (i * 47 + j * 90) % 360})

    # 3) Fire hydrants on two diagonal grass-block corners of each junction (off the drivable surface).
    if hydrants:
        corner = hw + 1.5
        for rec in compiled.intersections:
            cx, _, cz = rec.position
            for sx, sz in ((1.0, 1.0), (-1.0, -1.0)):
                props.append({"name": Prop.FIRE_HYDRANT,
                              "offset": (cx + sx * corner, CURB_HEIGHT, cz + sz * corner),
                              "angle": _heading_deg(-sx, -sz)})

    # 4) TRAFFIC LIGHTS — placed properly, not at every corner:
    #    * only at REAL junctions (3+ arms) that involve a major road (a 2-lane avenue), so minor
    #      side-street corners and dead-ends get none.
    #    * one per APPROACHING arm, at that road's near-right corner (off the drivable surface),
    #      FACING along the road toward the oncoming traffic it controls (so they read correctly
    #      instead of the old diagonal-facing wonk).
    for rec in compiled.intersections:
        nid = rec.id
        inc = [e for e in compiled.network.edges if e.a == nid or e.b == nid]
        if len(inc) < 3:
            continue
        if not any(max(e.lanes_fwd, e.lanes_rev) >= 2 for e in inc):
            continue
        cx, _, cz = rec.position
        br = box.get(nid, 6.0)
        for e in inc:
            if max(e.lanes_fwd, e.lanes_rev) < 2:
                continue                                # only signal the avenue approaches; minor streets yield
            other = e.b if e.a == nid else e.a
            ox, oz = compiled.network.nodes[other].pos
            dx, dz = ox - cx, oz - cz
            seg = math.hypot(dx, dz) or 1.0
            ux, uz = dx / seg, dz / seg                 # outward unit dir along this arm
            hw_e = _road_half_width(e)
            rx, rz = -uz, ux                            # right side of the inbound (approaching) lane
            px = cx + ux * br + rx * (hw_e + 1.0)       # near-right corner, off the road edge
            pz = cz + uz * br + rz * (hw_e + 1.0)
            props.append({"name": Prop.TRAFFIC_LIGHT_SINGLE,
                          "offset": (px, CURB_HEIGHT, pz),
                          "angle": _heading_deg(ux, uz)})   # face the oncoming traffic along the road

    terrain = getattr(compiled.network, "terrain", None)
    if terrain is not None:
        for pr in props:
            x, y, z = pr["offset"]
            pr["offset"] = (x, y + terrain(x, z), z)
    # CUSTOM per-preset props at ABSOLUTE positions (e.g. el-train supports + cars at fixed heights).
    # Not terrain-offset - the preset places them exactly (incl. elevated y).
    props.extend(getattr(compiled.network, "extra_props", None) or [])
    return props

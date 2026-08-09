"""
roadnet -> full city build integration.

This is the COUPLING layer (like emit.py for MapSpec): it drives the build pipeline's
`create_polygon` / `save_mesh` / `compute_uv` from a CompiledNetwork so a road network
becomes a real, textured, bounded, drivable city — bounds / cells / portals / TSH / .AR
are then produced by the existing pipeline unchanged. It also writes the AI intermediary
(`.road` + `.map`) into the dev city-map folder.

Geometry is emitted as ZONED strips (carriageway / sidewalks / grass base) derived from the
SAME centreline samples + frames + lateral offsets the AI cross-section used — so the mesh
and the AI stay in step.

Usage from MAP_EDITOR_ALPHA_v1.py (mirrors the MAP_SPEC_FILE block at ~1692):

    if ROADNET_CITY:
        from src.game.mapgen.roadnet import grid_city, RoadNetworkCompiler
        from src.game.mapgen.roadnet.build_city import emit_roadnet_city, write_roadnet_ai
        # clear the polygon-state globals in place (see MAP_SPEC_FILE block), then:
        compiled = RoadNetworkCompiler().compile(grid_city(4, 4))
        emit_roadnet_city(compiled, create_polygon, save_mesh, compute_uv)
        write_roadnet_ai(compiled, overwrite=True)      # set set_ai_streets=False!
"""
import math
import os
import shutil
import tempfile
from typing import Iterator, List, NamedTuple

from src.game.mapgen.roadnet.network_compiler import (
    CompiledNetwork, CELL_ROAD_BASE, CELL_ISECT_BASE,
)
from src.game.mapgen.roadnet.roadsect import RoadSection
from src.game.mapgen.roadnet.geometry import lateral_dir
from src.game.mapgen.roadnet.emit import emit_road, emit_map

GROUND_Y = 0.0


class CityQuad(NamedTuple):
    """One textured polygon of the city — consumed by BOTH the build pipeline (export)
    and the Blender preview (objects), so geometry has a single source.

    `uvs` are EXPLICIT per-vertex (u, v) pairs that stay in sync with `verts` through any
    winding flip — this is what fixes the texture rotation/mirroring; nothing recomputes
    them from tile_x/tile_y downstream.
    """
    verts: List          # game-space (x, y, z) corners, oriented UP
    uvs: List            # 4 (u, v) pairs matching verts 1:1
    texture: str         # MM1 texture name (R2/R4/R6/SDWLK2/T_GRASS)
    bound: int           # == cell id
    material_index: int
    cell_type: int
    hud_color: str
    is_spawn: bool
    collision_only: bool = False   # add to the BND (collision) but write NO mesh -> invisible
    wall_side: str = None          # "outside"/"inside" -> clean axis-aligned wall plane (barrier)
    no_flip: bool = False          # keep the AUTHORED down-facing winding (ceilings) - skip _orient + the guard


def _orient(verts, uvs):
    """
    Flip the quad UP if its normal points down, reversing verts AND uvs together so each
    vertex keeps its UV. The correct winding depends on road direction, so the flip is
    genuine; the earlier bug was flipping verts without the UVs (texture mirror/skew).
    """
    if _quad_normal_y(verts) < 0.0:
        return list(reversed(verts)), list(reversed(uvs))
    return list(verts), list(uvs)


def quad_tex_coords(q) -> list:
    """Flat [u0,v0,u1,v1,u2,v2,u3,v3] for save_mesh / the Blender UV layer."""
    return [c for uv in q.uvs for c in uv]


# ── bound-number allocation (cell ids) ───────────────────────────────────────
# bound_number == cell_id. Exactly one polygon must be 1 (the grass base). Roads &
# intersections each get their own cell, counting up from 201 (0/200/<0/>=32767 illegal).

def _bound_for_section(si: int) -> int:
    b = 201 + si
    return b + 1 if b == 200 else b


def _bound_for_intersection(num_sections: int, nid: int) -> int:
    b = 201 + num_sections + nid
    return b + 1 if b == 200 else b


def _road_texture(lanes: int) -> str:
    from src.constants.textures import Texture
    return {1: Texture.ROAD_1_LANE, 2: Texture.ROAD_2_LANE}.get(lanes, Texture.ROAD_3_LANE)


# ── zone geometry (full-width strips, derived from the shared samples) ─────────

def _lateral_point(sample, xd2, lat: float):
    return (sample[0] + xd2[0] * lat, GROUND_Y, sample[1] + xd2[1] * lat)


def _quad_normal_y(verts) -> float:
    """y-component of (v1-v0) x (v2-v0) over the first 3 game-space (x,y,z) verts."""
    ax, az = verts[1][0] - verts[0][0], verts[1][2] - verts[0][2]
    bx, bz = verts[2][0] - verts[0][0], verts[2][2] - verts[0][2]
    return az * bx - ax * bz


CURB_HEIGHT = 0.15   # sidewalks + grass sit this high; a VERTICAL curb wall drops to the road.


def _road_half_width(e) -> float:
    """Total lateral half-footprint: median half + widest carriageway + a sidewalk."""
    hw = e.median_half() + max(e.lanes_fwd, e.lanes_rev) * e.lane_width
    if e.sidewalk_fwd or e.sidewalk_rev:
        hw += e.sidewalk_width
    return hw


def _section_centerline(s: RoadSection, box_a: float, box_b: float):
    """
    The road centreline as a list of (point2d, forward2d, arclen-from-start), CLIPPED by box_a
    at the start and box_b at the end. STRAIGHT edges return 2 points (one quad per strip);
    SHAPED edges return the per-vertex curve samples (one quad per segment, so the strip bends).
    Returns None if the road is too short after clipping.
    """
    from src.game.mapgen.roadnet.geometry import normalize2, dist2, lerp2, sample_polyline, tangents
    e = s.edge
    if not e.shape:                               # straight: keep it to a single segment
        A, B = s.samples[0], s.samples[-1]
        dx, dz = B[0] - A[0], B[1] - A[1]
        L = (dx * dx + dz * dz) ** 0.5
        if L <= box_a + box_b + 1.0:
            return None
        d = normalize2((dx, dz))
        a = (A[0] + d[0] * box_a, A[1] + d[1] * box_a)
        b = (B[0] - d[0] * box_b, B[1] - d[1] * box_b)
        return [(a, d, 0.0), (b, d, L - box_a - box_b)]

    samples, fwd = s.samples, s.forward            # curved: per-vertex samples + tangents
    n = len(samples)

    # Cumulative arc length at each sample, so a distance along the road maps to a vertex pair.
    arc = [0.0]
    for i in range(1, n):
        arc.append(arc[-1] + dist2(samples[i - 1], samples[i]))
    L = arc[-1]

    if L <= box_a + box_b + 1.0:
        return None

    lo, hi = box_a, L - box_b

    def at(t):
        for i in range(1, n):
            if arc[i] >= t:
                st = (t - arc[i - 1]) / max(arc[i] - arc[i - 1], 1e-6)
                return lerp2(samples[i - 1], samples[i], st), (fwd[i] if st >= 0.5 else fwd[i - 1])
        return samples[-1], fwd[-1]

    p0, f0 = at(lo)
    out = [p0]
    for i in range(n):
        if lo + 1e-4 < arc[i] < hi - 1e-4:
            out.append(samples[i])
    p1, f1 = at(hi)
    out.append(p1)
    # Densify to short segments so the swept curve is smooth and per-segment facades stay ~1 panel.
    clen = sum(dist2(out[k - 1], out[k]) for k in range(1, len(out)))
    nseg = max(len(out) - 1, int(clen / 10.0) + 1)
    dense = sample_polyline(out, nseg + 1)
    dfwd = tangents(dense)
    darc = [0.0]
    for i in range(1, len(dense)):
        darc.append(darc[-1] + dist2(dense[i - 1], dense[i]))
    return [(dense[i], dfwd[i], darc[i]) for i in range(len(dense))]



def _deck_lift(frac, deck, profile="arch"):
    """Bridge deck height at arc fraction `frac` (0..1). FILLETED TRAPEZOID: long LINEAR coplanar ramps
    joined to a flat top by SHORT parabolic fillets. Why this exact shape -- MM1's wheel/ground contact
    (faithful to the binary) measures the CLOSEST point on the poly, which only sawtooths across
    NON-coplanar facets. So:
      * a tight curve (sin / smoothstep) makes every facet a new plane -> contact hops -> BOUNCE;
      * a sharp corner makes the slope jump -> a fast car is kicked off it -> LAUNCH / float.
    The fix is BOTH at once: keep the bulk of each ramp a single PLANE (coplanar -> contact smooth ->
    no bounce), and round only the 4 CORNERS over a short, C1-continuous (slope-continuous) fillet so
    there is no kick to launch off. The curved/bouncy region is confined to the brief fillets; the long
    straight ramps and flat top carry no bounce and no launch. Rise spans [0,0.40], flat [0.40,0.60]."""
    # NOTE: the profile barely matters; the FACET SIZE does. Reverse-engineered from SEAVIEW's working
    # vertical LOOP (BOUND03.BND): it drives perfectly even INVERTED on the same closest-point wheel
    # contact because its collision facets are ~19u (median edge). MM1 measures the CLOSEST point on a
    # poly; with BIG facets the wheel's contact patch sits on ONE plane for a long stretch so the closest
    # point only 'hops' at widely-spaced seams (no jitter). With SMALL facets (my old 3.9u) the patch
    # straddles seams and the nearest poly flips every frame -> sawtooth -> bounce. FIX = keep num_verts
    # LOW (~8 over a ~120u span => ~15-20u facets, matching the loop). The hump height is irrelevant to
    # the bounce (the loop rises 52u); only the facet footprint matters. A plain smooth half-sine is fine.
    #
    # PROFILE selects the slope SHAPE. ALL return to 0 at both ends (frac 0 and 1) so the deck meets the
    # flat road at the nodes with NO step. Lets one piece have asymmetric / double slopes (the "go crazy"
    # per-deck ask): arch = symmetric hump; early = steep-up/gentle-down; late = gentle-up/steep-down;
    # double = two humps (up-down-up-down) within a single piece.
    f = max(0.0, min(1.0, frac))
    # GENTLED vs the raw shapes: a SHARP slope reversal (a double-hump dropping to a V at 0, or a very
    # steep skew) spikes the AI wheel load -> mmWheel::ComputeDwtdw NaN -> crash WITH opponents. These stay
    # extreme enough to read as clearly different profiles while remaining AI-safe (solo + opponents).
    if profile == "ramp":     # rises to FULL deck at the END = a launch lip; ONLY for a dead-end jump
        return deck * math.sin(math.pi / 2.0 * f)   # ramp (it ends HIGH - a step - so never connect it)
    if profile == "double":   # two humps with a SHALLOW mid-valley (does NOT drop to 0)
        return deck * (0.5 * math.sin(math.pi * f) + 0.5 * abs(math.sin(2.0 * math.pi * f)))
    if profile == "early":    # peak early-ish: steeper up, gentler down
        return deck * math.sin(math.pi * (f ** 0.72))
    if profile == "late":     # peak late-ish: gentler up, steeper down
        return deck * math.sin(math.pi * (f ** 1.4))
    return deck * math.sin(math.pi * frac)


def _bank_slopes(e, cl, arch, deck):
    """Per-centreline-point bank slope (dy per unit lateral) for racetrack camber: tan(bank_deg) signed by
    the turn direction, tapered by arch/deck so it eases to 0 at the flat node ends. SHARED by the deck
    geometry AND the facades so they tilt together (facades snap to the banked sidewalk edge)."""
    bank_deg = getattr(e, "bank_deg", 0.0)
    if bank_deg == 0.0 or deck <= 0.0 or len(cl) < 3:
        return [0.0] * len(cl)
    turn = 0.0
    for i in range(1, len(cl) - 1):
        ax, az = cl[i][0][0] - cl[i - 1][0][0], cl[i][0][1] - cl[i - 1][0][1]
        bx, bz = cl[i + 1][0][0] - cl[i][0][0], cl[i + 1][0][1] - cl[i][0][1]
        turn += ax * bz - az * bx
    bs = math.tan(math.radians(bank_deg)) * (1.0 if turn >= 0.0 else -1.0)
    return [bs * (a / deck) for a in arch]


# TEMP (Robin 2026-06-26): deck guardrails OFF. On narrow/scaled roads the T_RAIL03 fences have collision,
# so swerving opponents clip them and get stuck. Flip back to True to restore the deck fences.
DECK_GUARDRAILS = False


def _section_zone_quads(s: RoadSection, box_a: float, box_b: float, terrain=None, flat_climb=False):
    """
    Yield (verts4, uvs4, texture, bound) for a section's carriageway + sidewalk strips, swept
    PER SEGMENT along the (possibly curved) clipped centreline — each vertex uses its LOCAL
    lateral frame so curbs/sidewalks bend with the road. U runs along the road (cumulative arc
    length so the texture flows continuously and never resets per segment); V spans the width.
    Clipped to box_a/box_b so it meets but does not overlap the intersection boxes.
    """
    from src.constants.textures import Texture
    from src.game.mapgen.roadnet.geometry import lateral_dir
    e = s.edge
    lw = e.lane_width
    m = e.median_half()
    fwd_road_out = m + e.lanes_fwd * lw
    rev_road_out = -(m + e.lanes_rev * lw)
    fwd_sw_out = fwd_road_out + (e.sidewalk_width if e.sidewalk_fwd else 0.0)
    rev_sw_out = rev_road_out - (e.sidewalk_width if e.sidewalk_rev else 0.0)
    bound = _bound_for_section(s.edge_index)
    road_tex = Texture.ROAD_2_LANE

    cl = _section_centerline(s, box_a, box_b)
    if cl is None:
        return

    # BRIDGE arch: a deck rising to e.deck_height over the span (0 at the shore ends). arch[i] is the
    # per-centreline-point lift applied to every strip of this section; 0 for a normal road.
    deck = getattr(e, "deck_height", 0.0)
    if deck > 0.0:
        total_arc = cl[-1][2] or 1.0
        _prof = getattr(e, "deck_profile", "arch")
        arch = [_deck_lift(sv / total_arc, deck, _prof) for (_pv, _fv, sv) in cl]
    else:
        arch = [0.0] * len(cl)

    # BANKING (racetrack camber): tilt the deck laterally INTO the turn. bank[i] = slope (dy per unit
    # lateral) at centreline point i, signed by the turn direction and TAPERED by the arch fraction so it
    # eases to 0 at the flat node ends (no step) and is fullest at the deck peak. Needs deck_height>0 - the
    # lift keeps the low (inner) edge above ground even where the deck tilts down.
    # FLAT-CLIMB (smooth deck-like helix): lift the road UNIFORMLY per centreline point by the terrain at
    # the CL so the cross-section stays FLAT (a ribbon), instead of draping over the slope (which tilts it).
    # The matching per-vertex terrain lift in iter_city_quads is skipped for these (see flat_climb there).
    if flat_climb and terrain is not None:
        arch = [a + terrain(cl[i][0][0], cl[i][0][1]) for i, a in enumerate(arch)]
    bank = _bank_slopes(e, cl, arch, deck)

    def _lp(p2, xd2, lat, y, bk=0.0):
        return (p2[0] + xd2[0] * lat, y + lat * bk, p2[1] + xd2[1] * lat)

    def strip(hi, lo, tex, repeat_along, y_hi=GROUND_Y, y_lo=GROUND_Y, v_max=1.0):
        rep = max(repeat_along, 1.0)
        for i in range(len(cl) - 1):
            p0, f0, s0 = cl[i]; p1, f1, s1 = cl[i + 1]
            xd0, xd1 = lateral_dir(f0), lateral_dir(f1)
            verts = [_lp(p0, xd0, hi, y_hi + arch[i], bank[i]), _lp(p1, xd1, hi, y_hi + arch[i + 1], bank[i + 1]),
                     _lp(p1, xd1, lo, y_lo + arch[i + 1], bank[i + 1]), _lp(p0, xd0, lo, y_lo + arch[i], bank[i])]
            u0, u1 = round(s0 / rep, 3), round(s1 / rep, 3)
            yield (verts, [(u0, 0.0), (u1, 0.0), (u1, v_max), (u0, v_max)], tex, bound)

    def road_strip(hi, lo):
        # Carriageway: tile the road texture at a CONSISTENT ~10u-square world scale, so a WIDE road
        # tiles the texture across + along instead of stretching one tile over the whole width.
        # Standard/narrow roads (<=10u wide) are unchanged (v_max stays 1.0); only wide roads tile.
        width = abs(hi - lo)
        v_max = max(1.0, width / 10.0)
        yield from strip(hi, lo, road_tex, width / v_max, v_max=v_max)

    def curb_face(lat, road_is_minus):
        for i in range(len(cl) - 1):
            p0, f0, s0 = cl[i]; p1, f1, s1 = cl[i + 1]
            xd0, xd1 = lateral_dir(f0), lateral_dir(f1)
            a0, b0 = _lp(p0, xd0, lat, GROUND_Y + arch[i], bank[i]), _lp(p1, xd1, lat, GROUND_Y + arch[i + 1], bank[i + 1])
            a1, b1 = _lp(p0, xd0, lat, CURB_HEIGHT + arch[i], bank[i]), _lp(p1, xd1, lat, CURB_HEIGHT + arch[i + 1], bank[i + 1])
            verts = [a0, b0, b1, a1] if road_is_minus else [a0, a1, b1, b0]
            u0, u1 = round(s0 / 2.0, 3), round(s1 / 2.0, 3)
            yield (verts, [(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)], Texture.SIDEWALK, bound)

    if m > 0.0:
        yield from road_strip(fwd_road_out, m)
        yield from road_strip(-m, rev_road_out)
        yield from strip(m, -m, Texture.GRASS, max(2.0 * m, 1.0))
    else:
        yield from road_strip(fwd_road_out, rev_road_out)

    if e.sidewalk_fwd:
        yield from curb_face(fwd_road_out, road_is_minus=True)
        yield from strip(fwd_road_out, fwd_sw_out, Texture.SIDEWALK, e.sidewalk_width,
                         y_hi=CURB_HEIGHT, y_lo=CURB_HEIGHT)
    if e.sidewalk_rev:
        yield from curb_face(rev_road_out, road_is_minus=False)
        yield from strip(rev_road_out, rev_sw_out, Texture.SIDEWALK, e.sidewalk_width,
                         y_hi=CURB_HEIGHT, y_lo=CURB_HEIGHT)

    tunnel_h = getattr(e, "tunnel_height", 0.0)
    if tunnel_h > 0.0:
        # ROOFED TUNNEL: a vertical WALL at each road edge (floor -> tunnel_h) + a DOWN-facing CEILING
        # spanning them. The ceiling is yielded with a 5th element True (no_flip) so the winding guard
        # keeps it pointing DOWN (visible from inside); the car drives under it, never collides.
        H = tunnel_h
        for i in range(len(cl) - 1):
            p0, f0, s0 = cl[i]; p1, f1, s1 = cl[i + 1]
            xd0, xd1 = lateral_dir(f0), lateral_dir(f1)
            uL, uR = round(s0 / 4.0, 3), round(s1 / 4.0, 3)
            for lat, rim in ((fwd_road_out, True), (rev_road_out, False)):
                a0 = _lp(p0, xd0, lat, GROUND_Y + arch[i]); b0 = _lp(p1, xd1, lat, GROUND_Y + arch[i + 1])
                a1 = _lp(p0, xd0, lat, H + arch[i]); b1 = _lp(p1, xd1, lat, H + arch[i + 1])
                wv = [a0, b0, b1, a1] if rim else [a0, a1, b1, b0]
                wu = ([(uL, 0.0), (uR, 0.0), (uR, 1.0), (uL, 1.0)] if rim
                      else [(uL, 0.0), (uL, 1.0), (uR, 1.0), (uR, 0.0)])   # UV must follow the winding
                yield (wv, wu, Texture.TUNNEL_WALL, bound)
            cL0 = _lp(p0, xd0, fwd_road_out, H + arch[i]); cR0 = _lp(p0, xd0, rev_road_out, H + arch[i])
            cL1 = _lp(p1, xd1, fwd_road_out, H + arch[i + 1]); cR1 = _lp(p1, xd1, rev_road_out, H + arch[i + 1])
            cv = [cL0, cR0, cR1, cL1]; cu = [(0.0, uL), (1.0, uL), (1.0, uR), (0.0, uR)]
            if (cR0[2] - cL0[2]) * (cR1[0] - cL0[0]) - (cR0[0] - cL0[0]) * (cR1[2] - cL0[2]) > 0.0:
                cv = cv[::-1]; cu = cu[::-1]      # make the ceiling face DOWN (visible from inside)
            yield (cv, cu, Texture.TUNNEL_TOP, bound, True)

    if deck > 0.0:
        # BRIDGE / OVERPASS UNDERSIDE: a DOWN-facing concrete soffit ~1.2u below the deck so the structure
        # reads as a real overpass FROM BELOW (the deck road surface is up-facing = back-face-culled from
        # under, so without this you'd see straight through it). Same no_flip down-facing trick as the
        # tunnel ceiling; emitted only on the clearly-elevated span so the ramp ends don't sink underground.
        SOFFIT = 1.2
        for i in range(len(cl) - 1):
            if arch[i] <= SOFFIT or arch[i + 1] <= SOFFIT:
                continue
            p0, f0, s0 = cl[i]; p1, f1, s1 = cl[i + 1]
            xd0, xd1 = lateral_dir(f0), lateral_dir(f1)
            uL, uR = round(s0 / 4.0, 3), round(s1 / 4.0, 3)
            yb0, yb1 = GROUND_Y + arch[i] - SOFFIT, GROUND_Y + arch[i + 1] - SOFFIT
            sL0 = _lp(p0, xd0, fwd_road_out, yb0); sR0 = _lp(p0, xd0, rev_road_out, yb0)
            sL1 = _lp(p1, xd1, fwd_road_out, yb1); sR1 = _lp(p1, xd1, rev_road_out, yb1)
            sv = [sL0, sR0, sR1, sL1]; su = [(0.0, uL), (1.0, uL), (1.0, uR), (0.0, uR)]
            if (sR0[2] - sL0[2]) * (sR1[0] - sL0[0]) - (sR0[0] - sL0[0]) * (sR1[2] - sL0[2]) > 0.0:
                sv = sv[::-1]; su = su[::-1]      # face DOWN (visible from under the bridge)
            yield (sv, su, Texture.CONCRETE, bound, True)
        # DECK GUARDRAILS: a short T_RAIL fence along BOTH carriageway edges, riding the arch the whole
        # span, DOUBLE-SIDED (both windings) so it reads from the ground road BELOW and from on the deck -
        # the visual cue that there's an elevated road up there. no_flip keeps both faces as authored.
        RAIL_H = 1.1
        rail_lats = []
        if DECK_GUARDRAILS:
            rail_lats = [fwd_road_out, rev_road_out]            # rail between the road and each sidewalk
            if e.sidewalk_fwd: rail_lats.append(fwd_sw_out)     # + the OUTER edge of each sidewalk -> peds boxed in
            if e.sidewalk_rev: rail_lats.append(rev_sw_out)     #   (4 rail lines total when both sidewalks exist)
        for i in range(len(cl) - 1):
            p0, f0, s0 = cl[i]; p1, f1, s1 = cl[i + 1]
            xd0, xd1 = lateral_dir(f0), lateral_dir(f1)
            uL, uR = round(s0 / 4.0, 3), round(s1 / 4.0, 3)
            for lat in rail_lats:
                q0 = _lp(p0, xd0, lat, CURB_HEIGHT + arch[i]); q1 = _lp(p1, xd1, lat, CURB_HEIGHT + arch[i + 1])
                t0 = _lp(p0, xd0, lat, CURB_HEIGHT + arch[i] + RAIL_H); t1 = _lp(p1, xd1, lat, CURB_HEIGHT + arch[i + 1] + RAIL_H)
                rv = [q0, q1, t1, t0]; ru = [(uL, 0.0), (uR, 0.0), (uR, 1.0), (uL, 1.0)]
                yield (rv, ru, Texture.RAIL, bound, True)              # one face
                yield (rv[::-1], ru[::-1], Texture.RAIL, bound, True)  # other face (double-sided)


FLAT_AI_RAILS = False    # lift AI rails onto the terrain so they match the (terraced) cells —
                         # mostly-flat levels + localized ramps, which the AI may tolerate.
GRASS_CARPET_Y = -0.05   # for OFF-GRID (curved) networks the grass is a continuous carpet just
                         # below road level; roads/sidewalks/intersections sit ON TOP, so collision
                         # always picks the road where one exists and grass everywhere else. (Pure
                         # grids keep the non-overlapping lattice fill via _grass_tiles.)
GRASS_TILE = 40.0  # grass is subdivided into ~40u tiles. Small enough that the HITID collision
                   # grid indexes each one (a single 400u quad overflowed it = the fall-through).
                   # Grass is always-visible LM and EXCLUDED from portals (see prepare_portals),
                   # so subdividing it no longer explodes the portal graph / hangs the cull.
GRASS_MARGIN = 30.0  # how far the ground extends beyond the outermost roads.


def _free_intervals(lines, lo, hi, hw):
    """1-D gaps NOT occupied by a road corridor (±hw around each line), within [lo, hi]."""
    out = []
    prev = lo
    for L in lines:
        b = L - hw
        if b > prev + 0.5:
            out.append((prev, b))
        prev = L + hw
    if hi > prev + 0.5:
        out.append((prev, hi))
    return out


def _grass_tiles(compiled: CompiledNetwork):
    """
    NON-OVERLAPPING ground: grass fills every area the roads/intersections do NOT — the blocks
    between roads and the outer border. Raised to CURB_HEIGHT so it is FLUSH with the sidewalks
    (the road sits in a channel between the vertical curbs). Each free rectangle is subdivided
    into ~GRASS_TILE tiles so the HITID indexes them. Yields (verts4, uvs4). Lattice layout.
    """
    nodes = list(compiled.network.nodes.values())
    xs_lines = sorted(set(round(n.pos[0], 3) for n in nodes))
    zs_lines = sorted(set(round(n.pos[1], 3) for n in nodes))
    hw = max((_road_half_width(e) for e in compiled.network.edges), default=5.0)
    fx = _free_intervals(xs_lines, xs_lines[0] - GRASS_MARGIN, xs_lines[-1] + GRASS_MARGIN, hw)
    fz = _free_intervals(zs_lines, zs_lines[0] - GRASS_MARGIN, zs_lines[-1] + GRASS_MARGIN, hw)
    gy = CURB_HEIGHT
    for (x0, x1) in fx:
        for (z0, z1) in fz:
            nx = max(1, int(round((x1 - x0) / GRASS_TILE)))
            nz = max(1, int(round((z1 - z0) / GRASS_TILE)))
            tdx, tdz = (x1 - x0) / nx, (z1 - z0) / nz
            for i in range(nx):
                for j in range(nz):
                    a0, a1 = x0 + i * tdx, x0 + (i + 1) * tdx
                    b0, b1 = z0 + j * tdz, z0 + (j + 1) * tdz
                    verts = [(a0, gy, b0), (a0, gy, b1),
                             (a1, gy, b1), (a1, gy, b0)]
                    uz = max(1.0, round((b1 - b0) / 10.0, 2))
                    ux = max(1.0, round((a1 - a0) / 10.0, 2))
                    uvs = [(0.0, 0.0), (0.0, uz), (ux, uz), (ux, 0.0)]
                    yield verts, uvs


def _network_extent(compiled: CompiledNetwork, pad: float = 80.0):
    xs = [n.pos[0] for n in compiled.network.nodes.values()]
    zs = [n.pos[1] for n in compiled.network.nodes.values()]
    return (min(xs) - pad, min(zs) - pad, max(xs) + pad, max(zs) + pad)


def _has_curves(compiled: CompiledNetwork) -> bool:
    return any(e.shape for e in compiled.network.edges)


def _is_grid_based(compiled: CompiledNetwork) -> bool:
    """True if the nodes sit on a regular lattice (unique-x * unique-z ~= node count), so the
    NON-OVERLAPPING grass lattice fill works even when some edges are drawn as curves."""
    nodes = compiled.network.nodes
    if not nodes:
        return False
    xs = {round(n.pos[0], 1) for n in nodes.values()}
    zs = {round(n.pos[1], 1) for n in nodes.values()}
    return len(xs) * len(zs) <= int(len(nodes) * 1.25) + 1


def curved_grade(net, tol: float = 0.5) -> bool:
    """
    True if any CURVED edge also changes elevation along its length (curve+grade) — the case
    that NaN-crashes the engine's AI rails. Flat curves over flat terrain (or curves on a level
    plateau) return False, so they keep full traffic.
    """
    terrain = getattr(net, "terrain", None)
    if terrain is None:
        return False
    for e in net.edges:
        if not e.shape:
            continue
        pts = [net.nodes[e.a].pos, *e.shape, net.nodes[e.b].pos]
        ys = [terrain(p[0], p[1]) for p in pts]
        if max(ys) - min(ys) > tol:
            return True
    return False


def _intersection_dynamic(compiled: CompiledNetwork, nid, node_pos, h):
    """
    DYNAMIC junction: built from the ACTUAL incident road mouths so it shapes to any approach
    angle (curved/diagonal) with no grass gaps. Per node: gather each road's outward direction
    + carriageway/full half-widths at the clip distance h, sort by angle, then
      (a) FAN the drivable centre (y=0) to each carriageway mouth + across each inner wedge, and
      (b) fill each wedge between consecutive roads with a raised SIDEWALK corner fillet (0.15)
          + a vertical curb on its inner edge.
    Yields (verts, uvs, texture, is_centre).
    """
    import math
    from src.constants.textures import Texture
    cx, cz = node_pos

    boxd = {}
    for n2 in compiled.network.nodes:
        inc = [e for e in compiled.network.edges if e.a == n2 or e.b == n2]
        boxd[n2] = max((_road_half_width(e) for e in inc), default=5.0)

    roads = []
    for s in compiled.sections:
        e = s.edge
        cl = _section_centerline(s, boxd.get(e.a, 5.0), boxd.get(e.b, 5.0))
        if cl is None:
            continue
        if e.a == nid:                       # mouth = the road's CLIPPED end on the curve
            ctr, d = cl[0][0], cl[0][1]
        elif e.b == nid:
            ctr, f = cl[-1][0], cl[-1][1]; d = (-f[0], -f[1])
        else:
            continue
        carr = e.median_half() + max(e.lanes_fwd, e.lanes_rev) * e.lane_width
        roads.append((math.atan2(d[1], d[0]), ctr, d, carr, _road_half_width(e)))
    if not roads:
        return
    roads.sort(key=lambda r: r[0])

    def corner(ctr, d, lat):
        xd = lateral_dir(d)
        return (ctr[0] + xd[0] * lat, ctr[1] + xd[1] * lat)

    CR, CL, SR, SL = [], [], [], []
    for (_a, ctr, d, carr, w) in roads:
        CR.append(corner(ctr, d, carr)); CL.append(corner(ctr, d, -carr))
        SR.append(corner(ctr, d, w));    SL.append(corner(ctr, d, -w))
    n = len(roads)
    nd = (cx, cz)

    def tri(a, b, c, y, tex, centre=False):
        return ([(a[0], y, a[1]), (b[0], y, b[1]), (c[0], y, c[1])],
                [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], tex, centre)

    # (a) drivable fan: each carriageway mouth + the inner wedge across to the next road.
    for i in range(n):
        j = (i + 1) % n
        yield tri(nd, CR[i], CL[i], GROUND_Y, Texture.INTERSECTION, centre=(i == 0))
        yield tri(nd, CL[i], CR[j], GROUND_Y, Texture.INTERSECTION)

    # (b) raised sidewalk corner fillets + inner curb in each wedge (skip roads with no sidewalk).
    for i in range(n):
        j = (i + 1) % n
        if abs(SL[i][0] - CL[i][0]) < 1e-3 and abs(SL[i][1] - CL[i][1]) < 1e-3:
            continue
        quad = [CL[i], SL[i], SR[j], CR[j]]
        yield ([(p[0], CURB_HEIGHT, p[1]) for p in quad],
               [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], Texture.SIDEWALK, False)
        a0 = (CL[i][0], GROUND_Y, CL[i][1]); b0 = (CR[j][0], GROUND_Y, CR[j][1])
        b1 = (CR[j][0], CURB_HEIGHT, CR[j][1]); a1 = (CL[i][0], CURB_HEIGHT, CL[i][1])
        ex, ez = CR[j][0] - CL[i][0], CR[j][1] - CL[i][1]
        mx, mz = (CL[i][0] + CR[j][0]) * 0.5, (CL[i][1] + CR[j][1]) * 0.5
        verts = [a0, b0, b1, a1] if (-ez * (cx - mx) + ex * (cz - mz)) >= 0 else [a0, a1, b1, b0]
        yield (verts, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], Texture.SIDEWALK, False)


def _grass_carpet(compiled: CompiledNetwork):
    """
    OFF-GRID ground: a uniform carpet of ~GRASS_TILE tiles over the whole network AABB at
    GRASS_CARPET_Y (just below road level), so curved/off-lattice roads have continuous ground.
    Roads/sidewalks/intersections are drawn on top; collision picks the road where it exists.
    Yields (verts4, uvs4).
    """
    x0, z0, x1, z1 = _network_extent(compiled, pad=GRASS_MARGIN)
    nx = max(1, int(round((x1 - x0) / GRASS_TILE)))
    nz = max(1, int(round((z1 - z0) / GRASS_TILE)))
    tdx, tdz = (x1 - x0) / nx, (z1 - z0) / nz
    gy = GRASS_CARPET_Y
    for i in range(nx):
        for j in range(nz):
            a0, a1 = x0 + i * tdx, x0 + (i + 1) * tdx
            b0, b1 = z0 + j * tdz, z0 + (j + 1) * tdz
            ux = max(1.0, round((a1 - a0) / 10.0, 2))
            uz = max(1.0, round((b1 - b0) / 10.0, 2))
            yield [(a0, gy, b0), (a0, gy, b1), (a1, gy, b1), (a1, gy, b0)], \
                  [(0.0, 0.0), (0.0, uz), (ux, uz), (ux, 0.0)]


def _grass_dynamic(compiled: CompiledNetwork, tile: float = 15.0):
    """
    DYNAMIC gap-fill grass: lay small tiles over the ground extent, then DROP any tile whose centre
    lands on a road or intersection footprint — computed from the REAL road centrelines (so it hugs
    curves too). Result: non-overlapping grass that follows the actual gaps with no axis-aligned
    slivers at curves. Yields (verts4, uvs4).
    """
    x0, z0, x1, z1 = _network_extent(compiled, pad=GRASS_MARGIN)
    nx = max(1, int(round((x1 - x0) / tile)))
    nz = max(1, int(round((z1 - z0) / tile)))
    tdx, tdz = (x1 - x0) / nx, (z1 - z0) / nz
    gy = GRASS_CARPET_Y

    # Road footprints: (samples, half-width^2, bbox). Intersections: (cx, cz, reach^2).
    roads = []
    for s in compiled.sections:
        if getattr(s.edge, "deck_height", 0.0) > 0.0:
            continue                                   # bridge: keep the water/ground UNDER the deck
        hw = _road_half_width(s.edge)
        xs = [p[0] for p in s.samples]; zs = [p[1] for p in s.samples]
        roads.append((s.samples, hw * hw, (min(xs) - hw, min(zs) - hw, max(xs) + hw, max(zs) + hw)))
    isects = []
    for rec in compiled.intersections:
        inc = [e for e in compiled.network.edges if e.a == rec.id or e.b == rec.id]
        r = max((_road_half_width(e) for e in inc), default=6.0)
        isects.append((rec.position[0], rec.position[2], r * r))

    def on_road(cx, cz):
        for (ix, iz, r2) in isects:
            if (cx - ix) ** 2 + (cz - iz) ** 2 < r2:
                return True
        for (samples, hw2, (bx0, bz0, bx1, bz1)) in roads:
            if cx < bx0 or cx > bx1 or cz < bz0 or cz > bz1:   # bbox reject (most roads, fast)
                continue
            for k in range(len(samples) - 1):
                ax, az = samples[k]; bx, bz = samples[k + 1]
                dx, dz = bx - ax, bz - az
                L2 = dx * dx + dz * dz
                if L2 < 1e-9:
                    continue
                t = ((cx - ax) * dx + (cz - az) * dz) / L2
                t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
                px, pz = ax + t * dx, az + t * dz
                if (cx - px) ** 2 + (cz - pz) ** 2 < hw2:
                    return True
        return False

    for i in range(nx):
        a0, a1 = x0 + i * tdx, x0 + (i + 1) * tdx
        ux = max(1.0, round((a1 - a0) / 10.0, 2))
        for j in range(nz):
            cx, cz = (a0 + a1) * 0.5, z0 + (j + 0.5) * tdz
            if on_road(cx, cz):
                continue
            b0, b1 = z0 + j * tdz, z0 + (j + 1) * tdz
            uz = max(1.0, round((b1 - b0) / 10.0, 2))
            yield [(a0, gy, b0), (a0, gy, b1), (a1, gy, b1), (a1, gy, b0)], \
                  [(0.0, 0.0), (0.0, uz), (ux, uz), (ux, 0.0)]


def _grass_precise(compiled: CompiledNetwork, res: float = 3.0):
    """
    PRECISE ground fill: rasterize the extent at `res`, keep each cell whose centre is OFF the road
    + intersection footprints (so it hugs curves), then GREEDY-MESH adjacent same-zone cells into
    maximal rectangles. Gap/overlap shrinks from the 15u tile-drop's ~half-a-tile to <= `res`, while
    the merge keeps the poly count down (open blocks collapse to a few big rects). Yields (verts4,
    uvs4) like the other ground fills; the caller textures each by its centre zone (rects are
    single-zone by construction).
    """
    x0, z0, x1, z1 = _network_extent(compiled, pad=GRASS_MARGIN)
    W = max(1, int(round((x1 - x0) / res)))
    H = max(1, int(round((z1 - z0) / res)))
    gy = GRASS_CARPET_Y

    # Grass sits at GRASS_CARPET_Y (below road level), so we let it UNDERLAP road edges by ~one cell
    # (shrink the drop footprint by `bias`): the overlap is hidden beneath the road, but it guarantees
    # the grass reaches the road edge with NO visible gap. Only road-middle cells get dropped.
    bias = res
    roads = []
    for s in compiled.sections:
        if getattr(s.edge, "deck_height", 0.0) > 0.0:
            continue                                   # bridge: keep the water/ground UNDER the deck
        hw = _road_half_width(s.edge)
        xs = [p[0] for p in s.samples]; zs = [p[1] for p in s.samples]
        roads.append((s.samples, max(hw - bias, 0.5) ** 2, (min(xs) - hw, min(zs) - hw, max(xs) + hw, max(zs) + hw)))
    isects = []
    for rec in compiled.intersections:
        inc = [e for e in compiled.network.edges if e.a == rec.id or e.b == rec.id]
        r = max((_road_half_width(e) for e in inc), default=6.0)
        isects.append((rec.position[0], rec.position[2], max(r - bias, 0.5) ** 2))

    def on_road(cx, cz):
        for (ix, iz, r2) in isects:
            if (cx - ix) ** 2 + (cz - iz) ** 2 < r2:
                return True
        for (samples, hw2, (bx0, bz0, bx1, bz1)) in roads:
            if cx < bx0 or cx > bx1 or cz < bz0 or cz > bz1:
                continue
            for k in range(len(samples) - 1):
                ax, az = samples[k]; bx, bz = samples[k + 1]
                dx, dz = bx - ax, bz - az
                L2 = dx * dx + dz * dz
                if L2 < 1e-9:
                    continue
                t = ((cx - ax) * dx + (cz - az) * dz) / L2
                t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
                px, pz = ax + t * dx, az + t * dz
                if (cx - px) ** 2 + (cz - pz) ** 2 < hw2:
                    return True
        return False

    zones = getattr(compiled.network, "ground_zones", None) or []

    def zone_of(cx, cz):
        for (zx0, zz0, zx1, zz1, k) in zones:
            if zx0 <= cx <= zx1 and zz0 <= cz <= zz1:
                return k
        return "grass"

    # per-cell zone kind (None on a road) + terrain height. The height keeps a merged tile from
    # spanning the slope: a big FLAT tile next to finer SLOPED tiles leaves a long thin vertical
    # crack (e.g. a flat sand rect against a sloping grass patch). Limiting each merge to a small
    # height band forces fine, terrain-following tiles on slopes (aligned -> no cracks) while flat
    # areas still merge big.
    terrain = getattr(compiled.network, "terrain", None)
    HEIGHT_TOL = 0.4
    cell = [[None] * W for _ in range(H)]
    hgt = [[0.0] * W for _ in range(H)]
    for j in range(H):
        cz = z0 + (j + 0.5) * res
        for i in range(W):
            cx = x0 + (i + 0.5) * res
            if not on_road(cx, cz):
                cell[j][i] = zone_of(cx, cz)
                if terrain is not None:
                    hgt[j][i] = terrain(cx, cz)

    # greedy-mesh same-kind cells into maximal rectangles
    used = [[False] * W for _ in range(H)]
    for j in range(H):
        for i in range(W):
            k = cell[j][i]
            if k is None or used[j][i]:
                continue
            h0 = hgt[j][i]
            w = 1
            while (i + w < W and cell[j][i + w] == k and not used[j][i + w]
                   and abs(hgt[j][i + w] - h0) <= HEIGHT_TOL):
                w += 1
            h = 1
            while j + h < H and all(cell[j + h][i + di] == k and not used[j + h][i + di]
                                    and abs(hgt[j + h][i + di] - h0) <= HEIGHT_TOL for di in range(w)):
                h += 1
            for dj in range(h):
                for di in range(w):
                    used[j + dj][i + di] = True
            a0, b0 = x0 + i * res, z0 + j * res
            a1, b1 = x0 + (i + w) * res, z0 + (j + h) * res
            ux = max(1.0, round((a1 - a0) / 10.0, 2))
            uz = max(1.0, round((b1 - b0) / 10.0, 2))
            yield [(a0, gy, b0), (a0, gy, b1), (a1, gy, b1), (a1, gy, b0)], \
                  [(0.0, 0.0), (0.0, uz), (ux, uz), (ux, 0.0)]


def _incident_dirs(compiled: CompiledNetwork, nid):
    """Cardinal directions (px/nx/pz/nz) that have a road leaving node nid."""
    node = compiled.network.nodes[nid].pos
    dirs = set()
    for e in compiled.network.edges:
        other = (compiled.network.nodes[e.b].pos if e.a == nid else
                 compiled.network.nodes[e.a].pos if e.b == nid else None)
        if other is None:
            continue
        dx, dz = other[0] - node[0], other[1] - node[1]
        dirs.add(('px' if dx > 0 else 'nx') if abs(dx) >= abs(dz) else ('pz' if dz > 0 else 'nz'))
    return dirs


def _carriageway_reach(compiled: CompiledNetwork, nid) -> float:
    """Half-width of the carriageway cross at a node (median half + widest carriageway)."""
    r = 0.0
    for e in compiled.network.edges:
        if e.a == nid or e.b == nid:
            r = max(r, e.median_half() + max(e.lanes_fwd, e.lanes_rev) * e.lane_width)
    return r


def _intersection_pieces(cx, cz, h, cr, dirs):
    """
    Decompose a junction into a 3x3 grid at splits [-h,-cr,cr,h]. The carriageway CROSS
    (centre + the arms that actually have a road) stays road at y=0; the 4 corners + any
    missing-arm side become RAISED sidewalk fillets at y=CURB_HEIGHT; a VERTICAL curb wall
    bridges every road<->sidewalk boundary (so the corners read like wrapped sidewalks you can
    mount, with no gaps). Yields (verts4, uvs4, texture, is_road_centre).
    """
    from src.constants.textures import Texture
    SW, RD = Texture.SIDEWALK, Texture.INTERSECTION

    def gquad(x0, z0, x1, z1, y, tex, centre=False):
        ux = max(1.0, round((x1 - x0) / 10.0, 2))
        uz = max(1.0, round((z1 - z0) / 10.0, 2))
        return ([(x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0)],
                [(0.0, 0.0), (0.0, uz), (ux, uz), (ux, 0.0)], tex, centre)

    if len(dirs) == 4:
        # 4-way junction: carriageway CROSS (centre + 4 arms) at road level; each corner is a
        # RAMP (2 triangles) rising from the centre-side corner (y=0) up to the sidewalk level,
        # with a ramping-curb gap-fill toward each adjacent arm -> you drive UP onto the corner.
        yield gquad(cx - cr, cz - cr, cx + cr, cz + cr, GROUND_Y, RD, True)   # centre
        yield gquad(cx + cr, cz - cr, cx + h,  cz + cr, GROUND_Y, RD)         # +x arm
        yield gquad(cx - h,  cz - cr, cx - cr, cz + cr, GROUND_Y, RD)         # -x arm
        yield gquad(cx - cr, cz + cr, cx + cr, cz + h,  GROUND_Y, RD)         # +z arm
        yield gquad(cx - cr, cz - h,  cx + cr, cz - cr, GROUND_Y, RD)         # -z arm
        T = CURB_HEIGHT
        for sx, sz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            ix, iz = cx + sx * cr, cz + sz * cr        # inner corner (road level)
            ox, oz = cx + sx * h,  cz + sz * h         # outer corner (sidewalk level)
            yield ([(ix, GROUND_Y, iz), (ox, T, iz), (ox, T, oz), (ix, T, oz)],
                   [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], SW, False)   # ramp (2 tris)
            tz = [(ix, GROUND_Y, iz), (ox, GROUND_Y, iz), (ox, T, iz)]            # gap-fill -> x-arm
            if sx == sz:
                tz = [tz[0], tz[2], tz[1]]
            yield (tz, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], SW, False)
            tx = [(ix, GROUND_Y, iz), (ix, GROUND_Y, oz), (ix, T, oz)]            # gap-fill -> z-arm
            if sx != sz:
                tx = [tx[0], tx[2], tx[1]]
            yield (tx, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)], SW, False)
        return

    xs = [-h, -cr, cr, h]
    arm = {(2, 1): 'px', (0, 1): 'nx', (1, 2): 'pz', (1, 0): 'nz'}
    typ = {}
    for i in range(3):
        for j in range(3):
            typ[(i, j)] = ('road' if (i, j) == (1, 1) else
                           ('road' if arm[(i, j)] in dirs else 'walk') if (i, j) in arm else 'walk')

    for (i, j), t in typ.items():
        x0, x1 = cx + xs[i], cx + xs[i + 1]
        z0, z1 = cz + xs[j], cz + xs[j + 1]
        if x1 - x0 < 1e-3 or z1 - z0 < 1e-3:
            continue
        y = GROUND_Y if t == 'road' else CURB_HEIGHT
        tex = Texture.INTERSECTION if t == 'road' else Texture.SIDEWALK
        ux = max(1.0, round((x1 - x0) / 10.0, 2))
        uz = max(1.0, round((z1 - z0) / 10.0, 2))
        verts = [(x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0)]
        uvs = [(0.0, 0.0), (0.0, uz), (ux, uz), (ux, 0.0)]
        yield (verts, uvs, tex, (i, j) == (1, 1))

    def curb_x(x, z0, z1, normal_minus):
        # vertical wall at x, z in [z0,z1], y 0->CURB_HEIGHT; normal -x if normal_minus else +x.
        p = [(x, GROUND_Y, z0), (x, GROUND_Y, z1), (x, CURB_HEIGHT, z1), (x, CURB_HEIGHT, z0)]
        verts = p if normal_minus else [p[0], p[3], p[2], p[1]]
        u = max(1.0, round(abs(z1 - z0) / 2.0, 2))
        return (verts, [(0.0, 0.0), (u, 0.0), (u, 1.0), (0.0, 1.0)], Texture.SIDEWALK, False)

    def curb_z(z, x0, x1, normal_minus):
        # vertical wall at z, x in [x0,x1]; normal -z if normal_minus else +z.
        p = [(x0, GROUND_Y, z), (x0, CURB_HEIGHT, z), (x1, CURB_HEIGHT, z), (x1, GROUND_Y, z)]
        verts = p if normal_minus else [p[0], p[3], p[2], p[1]]
        u = max(1.0, round(abs(x1 - x0) / 2.0, 2))
        return (verts, [(0.0, 0.0), (u, 0.0), (u, 1.0), (0.0, 1.0)], Texture.SIDEWALK, False)

    for i in range(2):
        for j in range(3):
            if typ[(i, j)] != typ[(i + 1, j)]:
                yield curb_x(cx + xs[i + 1], cz + xs[j], cz + xs[j + 1], typ[(i, j)] == 'road')
    for i in range(3):
        for j in range(2):
            if typ[(i, j)] != typ[(i, j + 1)]:
                yield curb_z(cz + xs[j + 1], cx + xs[i], cx + xs[i + 1], typ[(i, j)] == 'road')


EMIT_BUILDING_WALLS = False   # TEMP: facade collision off for testing (code kept). Flip True to
                              # re-enable the invisible BND walls.
WALL_HEIGHT = 14.0   # building collision-wall height (taller than a car; invisible so no cap).
FACADE_INSET = 0.0   # building line AT the sidewalk's outer edge -> facade glued to the sidewalk
                     # (no grass verge gap). _road_half_width already includes the sidewalk width.
WALL_SETBACK = 1.2   # the (invisible) collision wall sits this far BEHIND the facade. Flush with
                     # the facade put the collision plane right on the grass-cell boundary, which
                     # made the car oscillate (jitter); setting it back into the block clears the
                     # boundary -> smooth collision (cost: you drive ~WALL_SETBACK into the front).


def _wall_quad(p0, p1, outw, y0, y1):
    """A vertical wall quad p0->p1 (xz), y0..y1, wound so its normal faces `outw` (outward)."""
    from src.constants.textures import Texture
    ex, ez = p1[0] - p0[0], p1[1] - p0[1]
    a0 = (p0[0], y0, p0[1]); b0 = (p1[0], y0, p1[1])
    b1 = (p1[0], y1, p1[1]); a1 = (p0[0], y1, p0[1])
    # quad [a0,b0,b1,a1] has normal proportional to (-ez, 0, ex); flip if it faces inward.
    verts = [a0, b0, b1, a1] if (-ez * outw[0] + ex * outw[1]) >= 0 else [a0, a1, b1, b0]
    L = (ex * ex + ez * ez) ** 0.5
    u = max(1.0, round(L / 8.0, 2)); vt = max(1.0, round((y1 - y0) / 8.0, 2))
    # "outside" gives the editor's clean wall plane facing -X/-Z; "inside" faces +X/+Z. Pick by
    # the outward direction so the barrier's solid side faces the road.
    side = "outside" if (outw[0] + outw[1]) < 0 else "inside"
    return (verts, [(0.0, 0.0), (u, 0.0), (u, vt), (0.0, vt)], Texture.BRICKS_GREY, side)


def _building_walls(compiled: CompiledNetwork):
    """
    Vertical collision walls around each interior block (the building footprints), so cars
    can't drive through the FCD facades. Same bound as the grass (1) — always-visible LM, no
    portals — so they render + collide where the car actually is (on the block). Yields
    (verts4, uvs4, texture).
    """
    nodes = list(compiled.network.nodes.values())
    xs = sorted({round(n.pos[0], 3) for n in nodes})
    zs = sorted({round(n.pos[1], 3) for n in nodes})
    hw = max((_road_half_width(e) for e in compiled.network.edges), default=5.0)
    fx = _free_intervals(xs, xs[0] - GRASS_MARGIN, xs[-1] + GRASS_MARGIN, hw)
    fz = _free_intervals(zs, zs[0] - GRASS_MARGIN, zs[-1] + GRASS_MARGIN, hw)
    fx_in = fx[1:-1] if len(fx) > 2 else []
    fz_in = fz[1:-1] if len(fz) > 2 else []
    y0, y1 = CURB_HEIGHT, CURB_HEIGHT + WALL_HEIGHT
    for (x0, x1) in fx_in:
        for (z0, z1) in fz_in:
            bx0, bz0 = x0 + FACADE_INSET, z0 + FACADE_INSET
            bx1, bz1 = x1 - FACADE_INSET, z1 - FACADE_INSET
            if bx1 - bx0 < 4.0 or bz1 - bz0 < 4.0:
                continue
            for p0, p1, outw in (((bx0, bz0), (bx1, bz0), (0.0, -1.0)),   # south
                                 ((bx0, bz1), (bx1, bz1), (0.0, 1.0)),    # north
                                 ((bx0, bz0), (bx0, bz1), (-1.0, 0.0)),   # west
                                 ((bx1, bz0), (bx1, bz1), (1.0, 0.0))):   # east
                yield _wall_quad(p0, p1, outw, y0, y1)


# ── the unified geometry generator (single source for export + preview) ───────

def iter_city_quads(compiled: CompiledNetwork) -> Iterator[CityQuad]:
    """
    The city polygons, with the network's terrain height-field (if any) applied to every vertex
    so roads/grass/intersections all follow the hills coherently. `_city_quads_flat` builds the
    flat geometry; this wrapper just displaces Y by `terrain(x, z)`.
    """
    terrain = getattr(compiled.network, "terrain", None)

    def _upness(a, b, c):
        # normalized y-component of triangle (a,b,c)'s normal: +1 up, -1 down, ~0 vertical.
        ax, ay, az = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        bx, by, bz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        ny = az * bx - ax * bz
        nl = ((ay * bz - az * by) ** 2 + ny * ny + (ax * by - ay * bx) ** 2) ** 0.5
        return ny / nl if nl > 1e-9 else 0.0

    def _uptri(tv, tu):
        # a roughly-horizontal triangle facing DOWN renders but falls through -> reverse its winding.
        return (list(tv[::-1]), list(tu[::-1])) if _upness(tv[0], tv[1], tv[2]) < -0.5 else (list(tv), list(tu))

    flat_climb = getattr(compiled.network, "flat_climb", False)
    for q in _city_quads_flat(compiled):
        if terrain is not None and not flat_climb:
            # flat_climb: the road is already lifted (flat, per-CL) inside _section_zone_quads; the rest
            # (water/ground) stays FLAT so the ramp floats over it like a deck.
            q = q._replace(verts=[(x, y + terrain(x, z), z) for (x, y, z) in q.verts])
        if getattr(q, "no_flip", False):
            yield q                      # ceiling / render-only: keep its authored DOWN-facing winding
            continue
        v, uv = q.verts, q.uvs
        # COLLISION GUARDS. MM1 collision is per-poly PLANAR + winding-sensitive, so a quad ships with
        # NO collision (renders fine, car falls through) when it is (a) NON-planar OR (b) wound so a
        # triangle faces DOWN - including non-convex corner fillets a whole-quad flip can't fix. In any
        # of those cases split into 2 triangles and face EACH up; otherwise emit the clean quad as-is.
        if len(v) == 4 and (_nonplanar(v) or _upness(v[0], v[1], v[2]) < -0.5 or _upness(v[0], v[2], v[3]) < -0.5):
            a, b = _uptri([v[0], v[1], v[2]], [uv[0], uv[1], uv[2]]); yield q._replace(verts=a, uvs=b)
            a, b = _uptri([v[0], v[2], v[3]], [uv[0], uv[2], uv[3]]); yield q._replace(verts=a, uvs=b)
        else:
            a, b = _uptri(list(v), list(uv)); yield q._replace(verts=a, uvs=b)


def _nonplanar(v, tol: float = 0.04) -> bool:
    """True if the 4th vertex lies more than `tol` off the plane of the first three."""
    ax, ay, az = v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]
    bx, by, bz = v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]
    nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
    nl = (nx * nx + ny * ny + nz * nz) ** 0.5
    if nl < 1e-9:
        return False
    dx, dy, dz = v[3][0] - v[0][0], v[3][1] - v[0][1], v[3][2] - v[0][2]
    return abs(dx * nx + dy * ny + dz * nz) / nl > tol


def _city_quads_flat(compiled: CompiledNetwork) -> Iterator[CityQuad]:
    """
    Yield every textured, NON-OVERLAPPING polygon of the city: grass blocks (between roads),
    clipped road sections (carriageway + sidewalks), and intersection boxes (one per node).
    Roads stop at the box edge and grass insets from the roads, so no two cells overlap — a
    given (x,z) belongs to exactly one cell, which is what the HITID collision lookup needs.
    Each quad carries explicit, flip-synced UVs. Consumed by both the build export and the
    Blender preview.
    """
    from src.constants.textures import Texture
    from src.constants.file_formats import Material, Room
    from src.constants.color import Color

    # Intersection box half-size per node = the widest incident road's half-width. Roads are
    # clipped by this so they meet the box without overlapping it.
    box = {}
    for nid in compiled.network.nodes:
        incident = [e for e in compiled.network.edges if e.a == nid or e.b == nid]
        box[nid] = max((_road_half_width(e) for e in incident), default=5.0)

    # 1) ground: grid-based cities (even with a few curved edges) get the NON-OVERLAPPING lattice
    #    fill that ONLY fills the gaps between roads; genuinely off-grid networks fall back to the
    #    uniform carpet under everything. Both: small tiles (HITID), bound 1.
    curved = _has_curves(compiled)
    # GROUND ZONES: tag rectangles as water / sand / grass so the ground tile under each picks the
    # right texture (a lake, a beach, parks). network.ground_zones = [(x0,z0,x1,z1,kind), ...].
    _zones = getattr(compiled.network, "ground_zones", None) or []
    _KTEX = {"water": Texture.WATER, "sand": Texture.BRICKS_SAND,
             "grass": Texture.GRASS, "park": Texture.GRASS_BASEBALL,
             "lot": Texture.PARKING_LOT,                 # a real parking-lot texture (was lane-lined R4)
             "plaza": Texture.CONCRETE, "dirt": Texture.DIRT,
             "pier": Texture.PIER, "asphalt": Texture.ASPHALT,
             "industrial": Texture.INDUSTRIAL}
    _KMAT = {"water": Material.WATER}                    # water tiles get the WATER material (others: grass)
    _KHUD = {"water": Color.WATER}                       # minimap colour for the lake/canals
    # curves anywhere -> DYNAMIC footprint-hugging grass (drops tiles on roads, follows curves);
    # pure straight grids -> the clean block-aligned lattice fill.
    ground = _grass_precise(compiled) if curved else _grass_tiles(compiled)
    for verts, uvs in ground:
        v, uv = _orient(verts, uvs)
        cx, cz = (v[0][0] + v[2][0]) * 0.5, (v[0][2] + v[2][2]) * 0.5
        kind = "grass"
        for (x0, z0, x1, z1, k) in _zones:
            if x0 <= cx <= x1 and z0 <= cz <= z1:
                kind = k
                break
        yield CityQuad(verts=v, uvs=uv, texture=_KTEX.get(kind, Texture.GRASS), bound=1,
                       material_index=_KMAT.get(kind, Material.GRASS), cell_type=Room.DEFAULT,
                       hud_color=_KHUD.get(kind, Color.GRASS), is_spawn=False)

    # 1b) building collision walls around the interior blocks (bound 1 = same cell as the grass
    #     the car is on, so it actually collides). collision_only -> BND but NO mesh = invisible,
    #     so only the FCD facade is seen and you still can't drive through. Vertical: _orient noop.
    if EMIT_BUILDING_WALLS:
        for verts, uvs, tex, wside in _building_walls(compiled):
            v, uv = _orient(verts, uvs)
            yield CityQuad(verts=v, uvs=uv, texture=tex, bound=1,
                           material_index=Material.DEFAULT, cell_type=Room.DEFAULT,
                           hud_color=Color.GRASS, is_spawn=False, collision_only=True, wall_side=wside)

    # 2) road sections — CLIPPED to meet the intersection boxes (no road/box overlap).
    _terr = getattr(compiled.network, "terrain", None)
    _flat = getattr(compiled.network, "flat_climb", False)
    for s in compiled.sections:
        ba = box.get(s.edge.a, 5.0)
        bb = box.get(s.edge.b, 5.0)
        for _item in _section_zone_quads(s, ba, bb, _terr, _flat):
            verts, uvs, tex, bound = _item[0], _item[1], _item[2], _item[3]
            _nf = _item[4] if len(_item) > 4 else False
            v, uv = (list(verts), list(uvs)) if _nf else _orient(verts, uvs)   # ceiling keeps DOWN winding
            yield CityQuad(verts=v, uvs=uv, texture=tex, bound=bound,
                           material_index=Material.DEFAULT,
                           cell_type=(Room.TUNNEL if getattr(s.edge, "tunnel_height", 0.0) > 0.0 else Room.DEFAULT),
                           hud_color=Color.ROAD, is_spawn=False, no_flip=_nf)

    # 3) intersections — carriageway cross at road level + raised sidewalk corner fillets
    #    (Chicago-style), with vertical curbs between them. The spawn junction is the one nearest
    #    `network.spawn_near` (so the player starts by whatever was just changed), else the first.
    num_sections = len(compiled.sections)
    _spawn_near = getattr(compiled.network, "spawn_near", None)
    if _spawn_near is not None and compiled.intersections:
        spawn_idx = min(range(len(compiled.intersections)),
                        key=lambda i: (compiled.intersections[i].position[0] - _spawn_near[0]) ** 2
                                    + (compiled.intersections[i].position[2] - _spawn_near[1]) ** 2)
    else:
        spawn_idx = 0
    for idx, rec in enumerate(compiled.intersections):
        h = box.get(rec.id, 5.0)
        cx, _, cz = rec.position
        bound = _bound_for_intersection(num_sections, rec.id)
        cr = _carriageway_reach(compiled, rec.id)
        incident = [e for e in compiled.network.edges if e.a == rec.id or e.b == rec.id]
        dirs = _incident_dirs(compiled, rec.id)
        # The axis-aligned 3x3 decomposition only works for clean cardinal grid junctions. For
        # curved/diagonal/non-grid approaches, build the junction DYNAMICALLY from the actual road
        # mouths so it shapes to the angles with no grass gaps.
        if any(e.shape for e in incident) or len(dirs) != len(incident) or h - cr < 0.5:
            for verts, uvs, tex, is_centre in _intersection_dynamic(compiled, rec.id, (cx, cz), h):
                v, uv = _orient(verts, uvs)
                yield CityQuad(verts=v, uvs=uv, texture=tex, bound=bound,
                               material_index=Material.DEFAULT, cell_type=Room.DEFAULT,
                               hud_color=Color.ROAD, is_spawn=(is_centre and idx == spawn_idx))
            continue
        for verts, uvs, tex, is_centre in _intersection_pieces(cx, cz, h, cr, dirs):
            v, uv = _orient(verts, uvs)
            yield CityQuad(verts=v, uvs=uv, texture=tex, bound=bound,
                           material_index=Material.DEFAULT, cell_type=Room.DEFAULT,
                           hud_color=Color.ROAD, is_spawn=(is_centre and idx == spawn_idx))


# ── the export driver (mirrors emit.emit_compiled_map) ───────────────────────

def emit_roadnet_city(compiled: CompiledNetwork, create_polygon, save_mesh, compute_uv) -> int:
    """
    Author every city polygon via the pipeline API. Returns the polygon count. The
    pipeline then does bounds/cells/portals/TSH/.AR.
    """
    count = 0
    for q in iter_city_quads(compiled):
        create_polygon(bound_number=q.bound, vertex_coordinates=q.verts,
                       material_index=q.material_index, cell_type=q.cell_type,
                       hud_color=q.hud_color, base=q.is_spawn, wall_side=q.wall_side)
        if q.collision_only:
            # BND-only: the create_polygon above gives it collision; writing no mesh keeps it
            # invisible (the FCD facade is the visual). create_polygon already appended a poly,
            # so DON'T call save_mesh (which would also bump the cell's mesh sub-index).
            count += 1
            continue
        # compute_uv is called only for its texcoords bookkeeping side-effect; the actual UVs
        # are our explicit, flip-synced per-vertex coords (texture flows along the road).
        compute_uv(bound_number=q.bound, tile_x=1.0, tile_y=1.0, angle_degrees=0.0)
        save_mesh(texture_name=[q.texture], tex_coords=quad_tex_coords(q))
        count += 1
    return count


# ── AI intermediary writer ────────────────────────────────────────────────────

def write_roadnet_ai(compiled: CompiledNetwork, map_filename: str = None,
                     devmap_dir=None, overwrite: bool = True,
                     write_intersections: bool = False) -> dict:
    """
    Write the AI text files the game compiles into .BAI, into the dev city-map folder
    (flat layout, matching aiStreetEditor/BaiMap): `Street{id}.road` + `{MAP}.map`.

    overwrite=False skips any `.road` that already exists (so hand-tweaked roads survive).
    write_intersections=True also drops `Intersection{id}.int` (the editor normally omits
    these; the game regenerates intersections at load via CreateRoadMap).

    NOTE: when using roadnet AI, set `set_ai_streets = False` in USER settings so the
    build's own aiStreetEditor pass doesn't overwrite these files at build time.
    """
    if map_filename is None:
        from src.USER.settings.main import MAP_FILENAME
        map_filename = MAP_FILENAME
    if devmap_dir is None:
        from src.constants.folder import Folder
        devmap_dir = str(Folder.MidtownMadness.DevCityMap)

    os.makedirs(devmap_dir, exist_ok=True)
    written = 0
    skipped = 0
    street_names = []

    for s in compiled.sections:
        name = f"Street{s.fwd.id}"
        street_names.append(name)
        path = os.path.join(devmap_dir, f"{name}.road")
        if not overwrite and os.path.exists(path):
            skipped += 1
            continue
        with open(path, "w") as f:
            f.write(emit_road(s, None if FLAT_AI_RAILS else getattr(compiled.network, "terrain", None),
                              getattr(compiled.network, "flat_climb", False)))
        written += 1

    # the .map lists the streets the game loads
    with open(os.path.join(devmap_dir, f"{map_filename}.map"), "w") as f:
        f.write(map_file_text(map_filename, street_names))

    isect_written = 0
    if write_intersections:
        from src.game.mapgen.roadnet.emit import emit_intersection
        for rec in compiled.intersections:
            with open(os.path.join(devmap_dir, f"Intersection{rec.id}.int"), "w") as f:
                f.write(emit_intersection(rec))
            isect_written += 1

    return {"roads_written": written, "roads_skipped": skipped,
            "intersections_written": isect_written, "devmap": devmap_dir}


def map_file_text(map_filename: str, street_names: List[str]) -> str:
    streets = "\n        ".join(f'"{n}"' for n in street_names)
    return (f"mmMapData :0 {{\n"
            f"    NumStreets {len(street_names)}\n"
            f"    Street [\n        {streets}\n    ]\n}}\n")


# ── staging (survives the build's dev-folder clear) ──────────────────────────
# The dev city-map folder is wiped mid-build by ensure_empty_mm_dev_folder, so the AI
# can't be written there up-front. Instead it is STAGED to a temp folder (by the Blender
# button or the ROADNET_CITY build block) and CONSUMED into the dev folder during the
# build, after the clear + after the normal AI pass (so roadnet AI wins). Staging is
# cleared on consume, so it never goes stale into an unrelated later build.

def staging_dir(map_filename: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"mm1_roadnet_ai_{map_filename}")


def stage_roadnet_ai(compiled: CompiledNetwork, map_filename: str = None,
                     write_intersections: bool = False) -> dict:
    """Write the roadnet AI (.road + .map [+ .int]) into the temp staging folder."""
    if map_filename is None:
        from src.USER.settings.main import MAP_FILENAME
        map_filename = MAP_FILENAME
    d = staging_dir(map_filename)
    if os.path.isdir(d):
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
    os.makedirs(d, exist_ok=True)

    street_names = []
    for s in compiled.sections:
        name = f"Street{s.fwd.id}"
        street_names.append(name)
        with open(os.path.join(d, f"{name}.road"), "w") as f:
            f.write(emit_road(s, None if FLAT_AI_RAILS else getattr(compiled.network, "terrain", None),
                              getattr(compiled.network, "flat_climb", False)))
    with open(os.path.join(d, f"{map_filename}.map"), "w") as f:
        f.write(map_file_text(map_filename, street_names))
    if write_intersections:
        from src.game.mapgen.roadnet.emit import emit_intersection
        for rec in compiled.intersections:
            with open(os.path.join(d, f"Intersection{rec.id}.int"), "w") as f:
                f.write(emit_intersection(rec))
    return {"staged": len(street_names), "dir": d}


def write_roam_aimap(compiled, race_dir, density: float = 2.0,
                     speed_limit: int = 30, num_cops: int = 4, cop_model: str = "vpcop") -> str:
    """
    Write RACE/<MAP>/ROAM.AIMAP — the cruise AI-event file that turns on AMBIENT TRAFFIC
    (and optionally cops). Without it, aiRaceData->Density is 0 -> finalDensity 0 -> zero
    ambient cars seeded (aiMap.cpp:2715), and Police.Size()==0 -> zero cops (aiMap.cpp:1847).
    Pedestrians don't need this (they use the global PedDensity default), which is why peds
    appear but traffic/cops don't until this file exists.

    Format matches Game_Files/core/RACE/CHICAGO/ROAM.AIMAP. Cops are seeded at intersection
    node positions. 0 opponents (cruise has none -> no aiVehicleOpponent crash).

    `compiled` may be None, which writes the same file with no cops in it.
    """
    import os
    os.makedirs(str(race_dir), exist_ok=True)

    # `compiled` may be None: the direct-BAI path has no compiled network, and with no network
    # there is nowhere to seed cops, so it asks for the cop-free file.
    cops = []
    nodes = list(compiled.network.nodes.values()) if compiled is not None else []
    terrain = getattr(compiled.network, "terrain", None) if compiled is not None else None
    for i in range(min(num_cops, len(nodes))):
        x, z = nodes[i].pos
        # y a touch above the road so the cop drops onto it; FOLLOW THE HILLS (was hardcoded 2.0,
        # which buries a cop on a raised plateau -> bad spawn -> wheel-physics crash). mode 0=patrol.
        y = (terrain(x, z) if terrain else 0.0) + 2.0
        cops.append(f"{cop_model} {x:.1f} {y:.1f} {z:.1f} 0 0")

    text = (
        "# Ambient Traffic Density\n"
        "[Density]\n"
        f"{density}\n\n"
        "# Default Road Speed Limit\n"
        "[Speed Limit]\n"
        f"{speed_limit}\n\n"
        "# Ambient Traffic Exceptions\n"
        "# Rd Id, Density, Speed Limit\n"
        "[Exceptions]\n"
        "0\n\n"
        "# Police Init\n"
        "# Geo File, x, y, z, rotation, mode\n"
        "[Police]\n"
        f"{len(cops)}\n"
        + ("\n".join(cops) + "\n" if cops else "")
        + "\n"
        "# Opponent Init\n"
        "[Opponent]\n"
        "0\n"
    )
    path = os.path.join(str(race_dir), "ROAM.AIMAP")
    with open(path, "w") as f:
        f.write(text)
    return path


def consume_staged_ai(devmap_dir, map_filename: str) -> int:
    """
    Move staged AI into the dev city-map folder (clearing any AI already there), then
    clear staging. Returns the number of files copied (0 if nothing was staged).
    """
    d = staging_dir(map_filename)
    if not os.path.isdir(d):
        return 0
    files = [f for f in os.listdir(d) if f.endswith((".road", ".map", ".int"))]
    if not files:
        return 0
    devmap_dir = str(devmap_dir)
    os.makedirs(devmap_dir, exist_ok=True)
    for f in os.listdir(devmap_dir):
        if f.endswith((".road", ".int", ".map")):
            os.remove(os.path.join(devmap_dir, f))
    for f in files:
        shutil.copy2(os.path.join(d, f), os.path.join(devmap_dir, f))
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    return len(files)


def audit_collision(compiled):
    """
    Count polys that would ship with NO collision (render fine, car falls through): NON-planar
    (4-vert; MM1 collision is per-poly planar) + DOWN-facing horizontal (winding fall-through). The
    iter_city_quads COLLISION GUARDs should keep both at 0; a non-zero result means a guard regressed.
    Returns (non_planar, down_facing, total_quads).
    """
    nonpl = down = total = 0
    for q in iter_city_quads(compiled):
        total += 1
        v = q.verts
        if len(v) == 4 and _nonplanar(v) and not getattr(q, "no_flip", False):
            nonpl += 1   # no_flip = render-only (soffit/ceiling), NOT a drive surface -> not a fall-through
        if len(v) >= 3:
            ax, ay, az = v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]
            bx, by, bz = v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]
            ny = az * bx - ax * bz
            nl = ((ay * bz - az * by) ** 2 + ny * ny + (ax * by - ay * bx) ** 2) ** 0.5
            if nl > 1e-9 and ny / nl < -0.5 and not getattr(q, "collision_only", False) and not getattr(q, "no_flip", False):
                down += 1
    return nonpl, down, total

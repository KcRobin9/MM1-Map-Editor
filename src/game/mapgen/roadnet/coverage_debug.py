"""
Coverage debugger for the roadnet ground/road tiling.

Every rendered surface (road strip, sidewalk, intersection, grass/water/sand/lot tile) is a
horizontal polygon. This rasterizes them all onto a fine (x,z) grid and counts, per cell, how
many ROAD-class (bound>1) and how many GROUND-class (bound==1) polygons cover it:

    GAP      = no road AND no ground  -> a hole between sections (what we want to kill)
    OVERLAP  = ground sits on top of a road (ground should stop at the road edge)
    OK       = exactly one surface

It prints stats + the largest gap clusters (bounding boxes, to target the fix) and writes a PNG
coverage map (red=gap, grey=road, green=ground, yellow=overlap) next to this file.

Run:  python -m src.game.mapgen.roadnet.coverage_debug [preset]
"""
import sys
from collections import deque

from src.game.mapgen.roadnet.presets import build_preset
from src.game.mapgen.roadnet import RoadNetworkCompiler
from src.game.mapgen.roadnet.build_city import iter_city_quads, _network_extent, audit_collision


def _point_in_poly(px, pz, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if ((zi > pz) != (zj > pz)) and (px < (xj - xi) * (pz - zi) / (zj - zi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def analyze(preset="halfchicago", res=2.0, png=True):
    compiled = RoadNetworkCompiler().compile(build_preset(preset))
    quads = list(iter_city_quads(compiled))
    x0, z0, x1, z1 = _network_extent(compiled, pad=10.0)
    W = int((x1 - x0) / res) + 1
    H = int((z1 - z0) / res) + 1
    road = [[0] * W for _ in range(H)]
    ground = [[0] * W for _ in range(H)]

    horiz = 0
    for q in quads:
        # skip only VERTICAL surfaces (building walls); keep ground/road even when steeply sloped.
        # Use the face normal's up-component, not a y-range threshold (which wrongly drops hill tiles).
        v0, v1, v2 = q.verts[0], q.verts[1], q.verts[2]
        ax, ay, az = v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]
        bx, by, bz = v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]
        n_up = az*bx - ax*bz
        n_len = ((ay*bz-az*by)**2 + n_up*n_up + (ax*by-ay*bx)**2) ** 0.5
        if n_len < 1e-9 or abs(n_up)/n_len < 0.5:   # near-vertical -> wall
            continue
        horiz += 1
        poly = [(v[0], v[2]) for v in q.verts]
        minx = min(p[0] for p in poly); maxx = max(p[0] for p in poly)
        minz = min(p[1] for p in poly); maxz = max(p[1] for p in poly)
        i0 = max(0, int((minx - x0) / res)); i1 = min(W - 1, int((maxx - x0) / res) + 1)
        j0 = max(0, int((minz - z0) / res)); j1 = min(H - 1, int((maxz - z0) / res) + 1)
        grid = ground if q.bound == 1 else road
        for j in range(j0, j1 + 1):
            cz = z0 + j * res
            for i in range(i0, i1 + 1):
                cx = x0 + i * res
                if _point_in_poly(cx, cz, poly):
                    grid[j][i] += 1

    # classify the region that SHOULD be covered = the road network's bbox (not the outer pad)
    nx = [n.pos[0] for n in compiled.network.nodes.values()]
    nz = [n.pos[1] for n in compiled.network.nodes.values()]
    rx0, rx1, rz0, rz1 = min(nx) - 40, max(nx) + 40, min(nz) - 40, max(nz) + 40

    gap_cells = []
    n_in = n_gap = n_over = n_ok = 0
    for j in range(H):
        cz = z0 + j * res
        if not (rz0 <= cz <= rz1):
            continue
        for i in range(W):
            cx = x0 + i * res
            if not (rx0 <= cx <= rx1):
                continue
            n_in += 1
            r, g = road[j][i], ground[j][i]
            if r == 0 and g == 0:
                n_gap += 1; gap_cells.append((i, j))
            elif r > 0 and g > 0:
                n_over += 1
            else:
                n_ok += 1

    print(f"[{preset}] {horiz} horizontal quads | sampled {n_in} cells @ {res}u inside the city bbox")
    print(f"  GAP     {n_gap:6d}  ({100*n_gap/max(n_in,1):.2f}%)  area ~{n_gap*res*res:.0f} m^2")
    print(f"  OVERLAP {n_over:6d}  ({100*n_over/max(n_in,1):.2f}%)  (ground on top of road)")
    print(f"  OK      {n_ok:6d}  ({100*n_ok/max(n_in,1):.2f}%)")
    _np, _dn, _tot = audit_collision(compiled)
    _flag = "OK" if (_np == 0 and _dn == 0) else "*** BAD: these fall through ***"
    print(f"  COLLISION non-planar={_np} down-facing={_dn} of {_tot} quads  {_flag}")

    # cluster the gap cells (flood fill) and report the biggest clusters' world bboxes
    gapset = set(gap_cells)
    seen = set()
    clusters = []
    for c in gap_cells:
        if c in seen:
            continue
        comp = []; dq = deque([c]); seen.add(c)
        while dq:
            ci, cj = dq.popleft(); comp.append((ci, cj))
            for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
                nb = (ci+di, cj+dj)
                if nb in gapset and nb not in seen:
                    seen.add(nb); dq.append(nb)
        clusters.append(comp)
    clusters.sort(key=len, reverse=True)
    print(f"  {len(clusters)} gap clusters; biggest:")
    for comp in clusters[:8]:
        xs = [x0 + i * res for i, _ in comp]; zs = [z0 + j * res for _, j in comp]
        print(f"    {len(comp):4d} cells (~{len(comp)*res*res:.0f} m^2)  x[{min(xs):.0f},{max(xs):.0f}] z[{min(zs):.0f},{max(zs):.0f}]")

    if png:
        try:
            from PIL import Image
            img = Image.new("RGB", (W, H), (20, 20, 30))
            px = img.load()
            for j in range(H):
                for i in range(W):
                    r, g = road[j][i], ground[j][i]
                    if r > 0 and g > 0:
                        px[i, H-1-j] = (230, 210, 40)        # overlap = yellow
                    elif r > 0:
                        px[i, H-1-j] = (110, 110, 120)       # road = grey
                    elif g > 0:
                        px[i, H-1-j] = (40, 150, 60)         # ground = green
                    else:
                        cx = x0 + i * res; cz = z0 + j * res
                        if rx0 <= cx <= rx1 and rz0 <= cz <= rz1:
                            px[i, H-1-j] = (235, 40, 40)     # GAP inside city = red
            out = __file__.replace("coverage_debug.py", f"coverage_{preset}.png")
            img.save(out)
            print(f"  wrote {out}")
        except ImportError:
            print("  (PIL not available; skipped PNG)")


if __name__ == "__main__":
    analyze(sys.argv[1] if len(sys.argv) > 1 else "halfchicago")

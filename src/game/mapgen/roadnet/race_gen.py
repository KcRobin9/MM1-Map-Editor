"""
Generate a CHECKPOINT race (RACE_0) from a compiled road network.

The route is a chain of gates starting at the junction nearest `network.spawn_near`, so booting
the game with `-race 0` drops the player straight onto whatever was just changed (no driving the
big grid to find it). The race has 0 opponents / cops / ambient, so it works on hilly + curved
maps too (those crash the moving rail-AI; a player-only checkpoint race does not).

Feed the result to `src.game.races.main.create_races`, then launch Open1560 with `-race 0`.
The city's CINFO already declares one checkpoint (`create_map_info`), so EventId 0 resolves.
"""
from src.game.waypoints.constants import Rotation, Width
from src.constants.time_weather import TimeOfDay, Weather
from src.game.races.constants_2 import MaxOpponents, CopDensity, AmbientDensity, PedDensity


def _one_checkpoint(net, sx, sz, max_gates):
    import math
    from src.game.mapgen.roadnet.build_city import _deck_lift
    terrain = getattr(net, "terrain", None)
    nodes = net.nodes

    edge_of = {}
    for e in net.edges:
        edge_of[(e.a, e.b)] = e
        edge_of[(e.b, e.a)] = e

    adj = {nid: [] for nid in nodes}
    for e in net.edges:
        adj[e.a].append(e.b)
        adj[e.b].append(e.a)

    # ORDERED tour of EVERY node: greedy nearest-unvisited walk; when a connected component runs out
    # (e.g. an overpass's two non-touching roads) HOP to the nearest unvisited node - the player just
    # free-drives that gap to the next part of the feature. So the trail covers the whole thing.
    start = min(nodes, key=lambda nid: (nodes[nid].pos[0] - sx) ** 2 + (nodes[nid].pos[1] - sz) ** 2)
    order, visited, cur = [start], {start}, start

    while len(visited) < len(nodes):
        nxt = [n for n in adj[cur] if n not in visited]
        if nxt:
            cur = nxt[0]
        else:
            px, pz = nodes[cur].pos
            cur = min((n for n in nodes if n not in visited),
                      key=lambda n: (nodes[n].pos[0] - px) ** 2 + (nodes[n].pos[1] - pz) ** 2)
        order.append(cur)
        visited.add(cur)

    # DENSE gates: one at the start, then intermediate gates every ~GATE_STEP along each leg, RIDING the
    # deck arch on elevated edges (deck_height) so the trail leads you UP and OVER bridges/overpasses.
    GATE_STEP = 45.0
    def _gy(x, z):
        return terrain(x, z) if terrain else 0.0

    x0, z0 = nodes[order[0]].pos
    # NUDGE the spawn (first gate) ~25u INTO the road off the start node: a degree-1 dead-end node has a
    # DEGENERATE cell, so spawning exactly on it drops the car through (cellAtPos=-999 -> Reset). Harmless
    # on interior nodes (just moves the spawn a little onto the first leg).
    if len(order) > 1:
        # nudge ALONG the road - toward the first SHAPE point on a curved edge, else the next node - so the
        # spawn lands ON a curved/spiral road (a straight nudge would shove it off-road = same drop).
        _e0 = edge_of.get((order[0], order[1]))
        if _e0 is not None and getattr(_e0, "shape", None):
            _sp = _e0.shape[0] if _e0.a == order[0] else _e0.shape[-1]
            nx0, nz0 = _sp[0], _sp[1]
        else:
            nx0, nz0 = nodes[order[1]].pos
        d = math.hypot(nx0 - x0, nz0 - z0) or 1.0
        x0 += (nx0 - x0) / d * 25.0
        z0 += (nz0 - z0) / d * 25.0

    waypoints = [[round(x0, 2), round(_gy(x0, z0), 2), round(z0, 2), Rotation.AUTO, Width.LARGE]]

    for i in range(1, len(order)):
        a, b = order[i - 1], order[i]
        e = edge_of.get((a, b))
        # gates follow the edge's SHAPE (a curve / spiral) when it has one, NOT the straight node-to-node
        # chord (which cuts ACROSS a curved road and leaves the gates floating off it).
        pa, pb = nodes[a].pos, nodes[b].pos
        if e is not None and getattr(e, "shape", None):
            shp = list(e.shape)
            path = ([pa] + shp + [pb]) if e.a == a else ([pa] + list(reversed(shp)) + [pb])
        else:
            path = [pa, pb]
        dh = getattr(e, "deck_height", 0.0) if e is not None else 0.0
        prof = getattr(e, "deck_profile", "arch") if e is not None else "arch"
        seg = [math.hypot(path[j + 1][0] - path[j][0], path[j + 1][1] - path[j][1]) for j in range(len(path) - 1)]
        total = sum(seg) or 1.0
        steps = max(1, int(total // GATE_STEP))
        for k in range(1, steps + 1):
            target = total * k / steps
            acc = 0.0
            for j in range(len(seg)):
                if acc + seg[j] >= target or j == len(seg) - 1:
                    u = (target - acc) / (seg[j] or 1.0)
                    x = path[j][0] + (path[j + 1][0] - path[j][0]) * u
                    z = path[j][1] + (path[j + 1][1] - path[j][1]) * u
                    y = _deck_lift(target / total, dh, prof) if dh > 0.0 else _gy(x, z)
                    waypoints.append([round(x, 2), round(y, 2), round(z, 2), Rotation.AUTO, Width.LARGE])
                    break
                acc += seg[j]
        if len(waypoints) >= max_gates:
            break
    waypoints = waypoints[:max_gates]
    # OPPONENTS (opt-in via net.race_opponents): rivals racing the SAME gate route - a ROLLING start, each
    # one gate further down the course (on the road, correct height) so the solo time-trial becomes a race.
    n_opp = int(getattr(net, "race_opponents", 0) or 0)
    opponents = []
    if n_opp > 0 and len(waypoints) >= 3:
        from src.constants.vehicles import PlayerCar
        cars = [PlayerCar.MUSTANG_GT, PlayerCar.CADILLAC, PlayerCar.ROADSTER,
                PlayerCar.FASTBACK, PlayerCar.PANOZ_GTR1, PlayerCar.FORD_F350]
        route = [[w[0], w[1], w[2]] for w in waypoints]
        n_opp = max(1, min(n_opp, 8, len(cars), len(route) - 3))
        for i in range(n_opp):
            gi = 2 + i                                   # rolling start: each rival a couple gates down,
            gx, gy, gz = route[gi]                       # spawned ON the centreline (a lateral offset would
            opponents.append({cars[i % len(cars)]: [[gx, gy, gz]] + route[gi + 1:]})   # push off a tight curve)
    max_opp = getattr(MaxOpponents, "_%d" % len(opponents), MaxOpponents._8) if opponents else MaxOpponents._0
    md = [TimeOfDay.NOON, Weather.CLOUDY, max_opp, CopDensity._0, AmbientDensity._0, PedDensity._0]
    return {
        "player_waypoints": waypoints,
        "mm_data": {"ama": list(md), "pro": list(md)},
        "aimap": {"ambient_density": 0.0, "num_of_police": 0, "police": [],
                  "num_of_opponents": len(opponents), "opponents": opponents,
                  "num_of_exceptions": None, "exceptions": []},
    }


def roadnet_checkpoint_race(compiled, max_gates: int = 40) -> dict:
    """One checkpoint race per feature (net.feature_spawns -> RACE_0..N) for a showcase map, else a
    single RACE_0 at spawn_near. 0 opponents/cops/ambient so it works on hilly+curved+arched maps."""
    net = compiled.network
    spawns = getattr(net, "feature_spawns", None)
    if spawns:
        return {f"RACE_{i}": _one_checkpoint(net, sx, sz, max_gates) for i, (sx, sz, _nm) in enumerate(spawns)}
    sx, sz = getattr(net, "spawn_near", None) or (0.0, 0.0)
    return {"RACE_0": _one_checkpoint(net, sx, sz, max_gates)}


# ── circuit race with working opponents ──────────────────────────────────────
# Opponent waypoints are SPARSE intersection nodes; the engine drives the roads between them.
# Hard rules (verified vs aiGoalFollowWayPts.cpp): every waypoint must be an intersection, and
# every consecutive pair (incl. the lap wrap) must be a real road edge. So we drive a LOOP found
# in the graph adjacency.

def _adjacency(net):
    adj = {nid: [] for nid in net.nodes}
    for e in net.edges:
        adj[e.a].append(e.b)
        adj[e.b].append(e.a)
    return adj


def _find_loop(adj, start, min_len=8, max_len=18):
    """DFS for a cycle of nodes start..->start, length in [min_len, max_len]. Returns [] if none."""
    best: list = []

    def dfs(node, path, visited):
        if best:
            return
        for nxt in adj[node]:
            if best:
                return
            if nxt == start and len(path) >= min_len:
                best.extend(path)
                return
            if nxt not in visited and len(path) < max_len:
                visited.add(nxt)
                path.append(nxt)
                dfs(nxt, path, visited)
                if best:
                    return
                path.pop()
                visited.discard(nxt)

    dfs(start, [start], {start})
    return best


def roadnet_circuit_race(compiled, num_opponents: int = 5, laps=None, cars=None) -> dict:
    """
    A CIRCUIT (lap) race over a real loop in the road graph, with `num_opponents` opponents that
    navigate the same loop (sparse intersection waypoints; engine drives the roads between).
    Opponents spawn laterally offset so they don't stack. Boot with `-circuit 0`.
    """
    from src.constants.vehicles import PlayerCar
    from src.game.races.constants_2 import Laps

    net = compiled.network
    terrain = getattr(net, "terrain", None)
    nodes = net.nodes
    adj = _adjacency(net)

    start = max(nodes, key=lambda nid: len(adj[nid]))           # high-degree node = best loop odds
    loop = _find_loop(adj, start, min_len=8, max_len=18) or _find_loop(adj, start, min_len=4, max_len=18)
    if len(loop) < 4:
        raise RuntimeError("roadnet_circuit_race: could not find a loop in the graph")

    # Detect if the first loop leg (where opponents spawn) is a BRIDGE/arched deck (deck_height>0).
    _edge_of = {}
    for _e in net.edges:
        _edge_of[(_e.a, _e.b)] = _e; _edge_of[(_e.b, _e.a)] = _e
    def _leg_deck(i):
        _e = _edge_of.get((loop[i], loop[(i + 1) % len(loop)]))
        return getattr(_e, "deck_height", 0.0) if _e is not None else 0.0

    def P(nid):
        x, z = nodes[nid].pos
        return (round(x, 2), round((terrain(x, z) if terrain else 0.0), 2), round(z, 2))

    # player gates around the loop
    player_wps = [[P(nid)[0], P(nid)[1], P(nid)[2], Rotation.AUTO, Width.LARGE] for nid in loop]

    # Spawn opponents MID-ROAD on the first leg (in the forward-carriageway lanes), NOT at the
    # intersection centre, so they latch onto the rail immediately and accelerate into the race.
    # A staggered starting grid (two abreast, rows back) keeps them from touching.
    x0, sy, z0 = P(loop[0]); x1, _, z1 = P(loop[1])
    dx, dz = (x1 - x0), (z1 - z0)
    L = (dx * dx + dz * dz) ** 0.5 or 1.0
    fwd = (dx / L, dz / L)
    right = (dz / L, -dx / L)                 # right-hand side of travel = the forward lanes
    # If the first leg is a BRIDGE deck, spawn the grid BEHIND loop[0] (~14u off the bridge entrance, on
    # the approach) FACING the bridge, so opponents roll ONTO it rather than starting in the deck rails.
    ahead = -14.0 if _leg_deck(0) > 0.0 else min(22.0, L * 0.4)

    cars = cars or [PlayerCar.MUSTANG_GT, PlayerCar.CADILLAC, PlayerCar.ROADSTER,
                    PlayerCar.FASTBACK, PlayerCar.PANOZ_GTR1, PlayerCar.FORD_F350]
    n = max(1, min(int(num_opponents), 8, len(cars)))
    opponents = []
    for i in range(n):
        lane = 2.5 + (i % 2) * 4.5            # two forward lanes (centres ~2.5 / ~7 off the middle)
        back = (i // 2) * 9.0                 # each pair one grid row further back
        sx = round(x0 + fwd[0] * (ahead - back) + right[0] * lane, 2)
        sz = round(z0 + fwd[1] * (ahead - back) + right[1] * lane, 2)
        # waypoint 0 = the mid-road spawn; the rest stay the loop intersections (so nav is unchanged)
        wps = [[sx, sy, sz]] + [list(P(nid)) for nid in loop[1:]]
        opponents.append({cars[i % len(cars)]: wps})

    laps = laps if laps is not None else Laps._3
    md = [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0,
          PedDensity._0, laps]
    return {
        "CIRCUIT_0": {
            "player_waypoints": player_wps,
            "mm_data": {"ama": list(md), "pro": list(md)},
            "aimap": {
                "ambient_density": 0.0,
                "num_of_police": 0,
                "police": [],
                "num_of_opponents": n,
                "opponents": opponents,
                "num_of_exceptions": None,
                "exceptions": [],
            },
        }
    }

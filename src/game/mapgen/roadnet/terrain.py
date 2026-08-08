"""
Terrain height fields for hilly cities.

A terrain is just a callable `h(x, z) -> y` (the height to ADD to every vertex). Attach one to
a network via `net.terrain = rolling_hills()`; the compiler/build then displaces EVERYTHING at a
given (x,z) by the same amount — roads, grass, sidewalks, intersections, AI rails, props, facades
— so the whole city follows the hills coherently with no vertical overlap. Keep amplitudes gentle
relative to the tile/segment size (~tens of units) so the displaced quads stay near-planar (MM1
collision is per-poly planar).
"""
import math
from typing import Callable, List, Tuple

# (amplitude, wavelength_x, wavelength_z, phase_x, phase_z)
Wave = Tuple[float, float, float, float, float]


def sine_terrain(components: List[Wave]) -> Callable[[float, float], float]:
    def h(x: float, z: float) -> float:
        y = 0.0
        for (a, wx, wz, px, pz) in components:
            y += a * math.sin(x / wx * 2.0 * math.pi + px) * math.cos(z / wz * 2.0 * math.pi + pz)
        return y
    return h


def flat() -> Callable[[float, float], float]:
    return lambda x, z: 0.0


def _smoothstep(e0: float, e1: float, x: float) -> float:
    """0 below e0, 1 above e1, smooth S-curve between (a nice curved ramp)."""
    if e1 == e0:
        return 0.0 if x < e0 else 1.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def terraced(steps=None) -> Callable[[float, float], float]:
    """
    FLAT levels joined by smooth (curved) ramps — the 'road network at y=5' look, not wavy bumps.
    `steps` is a list of (axis, e0, e1, height): the field rises by `height` across the smoothstep
    ramp from `e0` to `e1` along axis 'x' or 'z'. Roads sit flat on each plateau; the ramps
    between are the curved slopes. Default = a steep west rise + a gentle north rise.
    """
    if steps is None:
        steps = [('x', -40.0, -200.0, 7.0),   # steep plateau in the west  (+7 over a 160 ramp)
                 ('z', 110.0, 320.0, 4.0)]     # gentle rise to the north   (+4 over a 210 ramp)

    def h(x, z):
        y = 0.0
        for (axis, e0, e1, hgt) in steps:
            y += hgt * _smoothstep(e0, e1, x if axis == 'x' else z)
        return y
    return h


def corners(amp: float = 6.0, band: float = 70.0, ramp: float = 120.0):
    """
    Height ONLY in the four corners (|x|>band AND |z|>band); FLAT along the central cross
    (|x|<band OR |z|<band). Lets a city keep CURVED roads flat down the middle (no curve+grade,
    so the AI stays happy) while the straight corner roads ramp up — height diffs without the
    curve+grade NaN.
    """
    def h(x, z):
        return amp * _smoothstep(band, band + ramp, abs(x)) * _smoothstep(band, band + ramp, abs(z))
    return h


def plateau(amp: float = 6.0, half: float = 130.0, ramp: float = 90.0):
    """A single central raised plateau (flat top) with smooth ramps on all sides."""
    def h(x, z):
        fx = _smoothstep(-half - ramp, -half, x) - _smoothstep(half, half + ramp, x)
        fz = _smoothstep(-half - ramp, -half, z) - _smoothstep(half, half + ramp, z)
        return amp * fx * fz
    return h


def small_bumps(amp: float = 2.5, wl: float = 45.0):
    """Gentle undulation — speed-bump scale."""
    return sine_terrain([(amp, wl, wl * 1.1, 0.0, 0.0)])


def rolling_hills(amp: float = 11.0, wl: float = 210.0):
    """Big soft hills with a smaller overlay so they aren't a perfect grid of mounds."""
    return sine_terrain([(amp, wl, wl, 0.0, 0.0),
                         (amp * 0.4, wl * 0.45, wl * 0.5, 1.3, 2.1)])


def big_hills(amp: float = 26.0, wl: float = 330.0):
    """Dramatic elevation — a hilly San-Francisco feel."""
    return sine_terrain([(amp, wl, wl * 0.9, 0.4, 0.0),
                         (amp * 0.35, wl * 0.35, wl * 0.4, 2.0, 0.7)])


def mixed() -> Callable[[float, float], float]:
    """Big hills + rolling + small bumps layered — the 'all variants' terrain."""
    return sine_terrain([(24.0, 340.0, 300.0, 0.4, 0.0),
                         (9.0, 150.0, 175.0, 1.3, 2.1),
                         (2.5, 48.0, 52.0, 0.7, 1.1)])

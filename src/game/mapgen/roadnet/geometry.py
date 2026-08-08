"""
Pure-Python vector helpers for the road-network compiler.

Coordinate convention (matches MM1 game space and the .road files):
  * Ground plane is (x, z); +y is up.
  * 1 unit = 1 metre.
  * A "Vec3" is a plain (x, y, z) tuple of floats; ground points are often handled
    as (x, z) 2-tuples and lifted to y=0 when emitted.

Frame convention (verified against Street0.road):
  forward f = unit tangent in the (x,z) plane
  VertXDir  = ( f.z, 0, -f.x )     # lateral, "right" of travel
  VertZDir  = (-f.x, 0, -f.z )     # = -forward (the runtime stores Z pointing backward)
"""
import math
from typing import List, Sequence, Tuple

Vec2 = Tuple[float, float]
Vec3 = Tuple[float, float, float]


# ── 2D (ground-plane) helpers ────────────────────────────────────────────────

def sub2(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] - b[0], a[1] - b[1])


def add2(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] + b[0], a[1] + b[1])


def mul2(a: Vec2, s: float) -> Vec2:
    return (a[0] * s, a[1] * s)


def len2(a: Vec2) -> float:
    return math.hypot(a[0], a[1])


def normalize2(a: Vec2) -> Vec2:
    n = len2(a)
    return (a[0] / n, a[1] / n) if n > 1e-9 else (1.0, 0.0)


def lerp2(a: Vec2, b: Vec2, t: float) -> Vec2:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def dist2(a: Vec2, b: Vec2) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ── Frames ────────────────────────────────────────────────────────────────────

def lateral_dir(forward2: Vec2) -> Vec2:
    """VertXDir in (x,z): the 'right' lateral of travel = ( f.z, -f.x )."""
    return (forward2[1], -forward2[0])


def back_dir(forward2: Vec2) -> Vec2:
    """VertZDir in (x,z): the runtime stores Z pointing backward = -forward."""
    return (-forward2[0], -forward2[1])


# ── 2D <-> game-space Vec3 (y = ground height) ───────────────────────────────

def to_vec3(p2: Vec2, y: float = 0.0) -> Vec3:
    return (p2[0], y, p2[1])


def to_vec3_xz(x: float, z: float, y: float = 0.0) -> Vec3:
    return (x, y, z)


def v3_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v3_dist(a: Vec3, b: Vec3) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def v3_dot_xz(a: Vec3, xdir2: Vec2) -> float:
    """Dot of a Vec3's (x,z) against a 2D direction — the `^` lateral projection."""
    return a[0] * xdir2[0] + a[2] * xdir2[1]


# ── Sampling ────────────────────────────────────────────────────────────────

def sample_polyline(points: Sequence[Vec2], n: int) -> List[Vec2]:
    """Resample a polyline to exactly n points by arc length (n >= 2)."""
    if n < 2:
        raise ValueError("need at least 2 samples")
    if len(points) == 1:
        return [points[0]] * n

    # cumulative lengths
    seg = [0.0]
    for i in range(1, len(points)):
        seg.append(seg[-1] + dist2(points[i - 1], points[i]))
    total = seg[-1]
    if total <= 1e-9:
        return [points[0]] * n

    out: List[Vec2] = []
    for k in range(n):
        target = total * k / (n - 1)
        # find segment containing `target`
        j = 1
        while j < len(seg) - 1 and seg[j] < target:
            j += 1
        seg_len = seg[j] - seg[j - 1]
        t = 0.0 if seg_len <= 1e-9 else (target - seg[j - 1]) / seg_len
        out.append(lerp2(points[j - 1], points[j], t))
    return out


def tangents(samples: Sequence[Vec2]) -> List[Vec2]:
    """Per-sample unit forward direction (central differences, endpoint one-sided)."""
    n = len(samples)
    out: List[Vec2] = []
    for i in range(n):
        if i == 0:
            d = sub2(samples[1], samples[0])
        elif i == n - 1:
            d = sub2(samples[n - 1], samples[n - 2])
        else:
            d = sub2(samples[i + 1], samples[i - 1])
        out.append(normalize2(d))
    return out


def heading_atan2(dx: float, dz: float) -> float:
    """The intersection heading convention used by aiIntersection::CreateRoadMap."""
    return math.atan2(dx, dz)

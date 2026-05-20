"""
Procedural primitive car body + wheel geometry for the Car Editor template system.

All geometry is built directly in **Blender local space**:
  BX = -game_X   (game left  → positive BX)
  BY =  game_Z   (game front → negative BY)
  BZ =  game_Y   (game up    → positive BZ)

Dimensions derived from real MM1 vehicles measured via read_bms().
"""
import math
import bpy
import bmesh


# ── Template catalogue ────────────────────────────────────────────────────────

TEMPLATE_ITEMS = [
    ("SEDAN", "Sedan", "Full-size sedan (VPMUSTANG99 reference — wheels loaded from BMS)"),
]

# Raw template data.  All distances in game-space metres.
#
# Body params:
#   hw        half-width (game X)
#   h         total height (game Y)
#   hl        half-length (game Z, symmetric)
#   gc        ground clearance — Y of the body's lowest point
#   cf_frac   cabin-front Z as fraction of full length (0=front, 1=rear)
#   cr_frac   cabin-rear  Z as fraction of full length (0=front, 1=rear)
#   hood_frac hood/trunk height as fraction of h  (1.0 → flat-top bus/semi)
#
# Wheel tuples: (game_x, game_y, game_z, radius, half_axle_width)
#   game_x negative = left side, game_z negative = front
#
# Trailer-specific keys:
#   body_offset      game-space (x, y, z) offset stored in the BMS header
#   body_filename    BMS filename to write (default "BODY_H.BMS")
#   wheel_prefix     export filename prefix (default "WHL")

_T: dict = {
    "COMPACT": dict(
        hw=0.88, h=1.17, hl=1.78, gc=0.26,
        cf_frac=0.38, cr_frac=0.64, hood_frac=0.48,
        wheels=[
            (-0.65, 0.27, -1.05, 0.27, 0.18),
            ( 0.65, 0.27, -1.05, 0.27, 0.18),
            ( 0.63, 0.27,  1.19, 0.27, 0.18),
            (-0.63, 0.27,  1.19, 0.27, 0.18),
        ],
    ),
    "SEDAN": dict(
        hw=1.02, h=1.44, hl=2.59, gc=0.31,
        cf_frac=0.38, cr_frac=0.62, hood_frac=0.48,
        wheels=[
            (-0.86, 0.31, -1.60, 0.35, 0.22),
            ( 0.86, 0.31, -1.60, 0.35, 0.22),
            ( 0.84, 0.31,  1.52, 0.35, 0.22),
            (-0.84, 0.31,  1.52, 0.35, 0.22),
        ],
    ),
    "SPORTS": dict(
        hw=1.00, h=1.20, hl=2.30, gc=0.28,
        cf_frac=0.42, cr_frac=0.57, hood_frac=0.44,
        wheels=[
            (-0.87, 0.33, -1.48, 0.34, 0.22),
            ( 0.87, 0.33, -1.48, 0.34, 0.22),
            ( 0.86, 0.33,  1.40, 0.34, 0.22),
            (-0.86, 0.33,  1.40, 0.34, 0.22),
        ],
    ),
    "PICKUP": dict(
        hw=1.08, h=1.33, hl=2.64, gc=0.34,
        cf_frac=0.36, cr_frac=0.52, hood_frac=0.52,
        wheels=[
            (-0.82, 0.34, -1.36, 0.37, 0.24),
            ( 0.82, 0.34, -1.36, 0.37, 0.24),
            ( 0.78, 0.34,  1.93, 0.37, 0.24),
            (-0.78, 0.34,  1.93, 0.37, 0.24),
        ],
    ),
    "TRUCK": dict(
        hw=1.23, h=1.53, hl=3.30, gc=0.40,
        cf_frac=0.32, cr_frac=0.67, hood_frac=0.62,
        wheels=[
            (-0.87, 0.43, -1.70, 0.44, 0.28),
            ( 0.87, 0.43, -1.70, 0.44, 0.28),
            ( 0.90, 0.43,  2.74, 0.44, 0.28),
            (-0.90, 0.43,  2.74, 0.44, 0.28),
        ],
    ),
    "BUS": dict(
        hw=1.30, h=3.27, hl=6.93, gc=0.50,
        cf_frac=0.04, cr_frac=0.96, hood_frac=1.00,
        wheels=[
            (-1.05, 0.52, -4.60, 0.53, 0.35),
            ( 1.05, 0.52, -4.60, 0.53, 0.35),
            ( 1.00, 0.52,  3.37, 0.53, 0.35),
            (-1.00, 0.52,  3.37, 0.53, 0.35),
            ( 1.00, 0.52,  4.54, 0.53, 0.35),
            (-1.00, 0.52,  4.54, 0.53, 0.35),
        ],
    ),
    "SEMI": dict(
        hw=1.21, h=3.77, hl=4.17, gc=0.50,
        cf_frac=0.04, cr_frac=0.96, hood_frac=1.00,
        wheels=[
            (-0.98, 0.50, -2.83, 0.53, 0.35),
            ( 0.98, 0.50, -2.83, 0.53, 0.35),
            ( 0.93, 0.50,  2.46, 0.53, 0.35),
            (-0.93, 0.50,  2.46, 0.53, 0.35),
            ( 0.93, 0.50,  3.51, 0.53, 0.35),
            (-0.93, 0.50,  3.51, 0.53, 0.35),
        ],
    ),
    # Trailer uses TRAILER_H.BMS body file + TWHL{n}_H.BMS wheel files.
    # body_offset is the BMS mesh_offset stored in the header (not a world position).
    "TRAILER": dict(
        hw=1.22, h=3.12, hl=6.11, gc=0.31,
        cf_frac=0.02, cr_frac=0.98, hood_frac=1.00,
        body_offset=(0.0, 0.87, 7.56),
        body_filename="TRAILER_H.BMS",
        wheel_prefix="TWHL",
        wheels=[
            (-0.82, 0.50, 10.28, 0.53, 0.35),
            ( 0.83, 0.50, 10.28, 0.53, 0.35),
            ( 0.83, 0.50, 11.60, 0.53, 0.35),
            (-0.82, 0.50, 11.59, 0.53, 0.35),
        ],
    ),
}


# ── UV helper ─────────────────────────────────────────────────────────────────

def _planar_uv(face, uv_layer) -> None:
    """Project face loops to UV using the two axes with most variance."""
    loops = list(face.loops)
    if not loops:
        return
    coords = [l.vert.co for l in loops]
    ranges = [
        max(c[i] for c in coords) - min(c[i] for c in coords)
        for i in range(3)
    ]
    flat_ax = ranges.index(min(ranges))
    u_ax, v_ax = [i for i in range(3) if i != flat_ax]
    u_min = min(c[u_ax] for c in coords)
    v_min = min(c[v_ax] for c in coords)
    u_rng = (max(c[u_ax] for c in coords) - u_min) or 1.0
    v_rng = (max(c[v_ax] for c in coords) - v_min) or 1.0
    for loop in loops:
        co = loop.vert.co
        loop[uv_layer].uv = (
            (co[u_ax] - u_min) / u_rng,
            (co[v_ax] - v_min) / v_rng,
        )


# ── Body mesh ─────────────────────────────────────────────────────────────────

def build_body_mesh(car_name: str, archetype: str) -> bpy.types.Mesh:
    """
    Build a primitive car body mesh (Blender space) from a named archetype.

    Sloped silhouette (hood_frac < 1.0) — 16 verts, 10 faces:
      floor, front, hood-top, windshield, roof, rear-windshield,
      trunk-top, rear, left-side (8-gon), right-side (8-gon).

    Flat-top (hood_frac == 1.0, bus/semi/trailer) — 12 verts, 8 faces:
      floor, front, front-strip, roof, rear-strip, rear,
      left-side (6-gon), right-side (6-gon).

    The mesh origin is the body centre (Blender X=0, Y=0, Z=0).
    Trailers have a non-zero game-space mesh_offset stored in bms_source_file;
    the actual object location in Blender remains at origin.
    """
    t = _T[archetype]

    hw        = t["hw"]
    h         = t["h"]
    hl        = t["hl"]
    gc        = t["gc"]
    cf_frac   = t.get("cf_frac",   0.38)
    cr_frac   = t.get("cr_frac",   0.62)
    hood_frac = t.get("hood_frac", 0.50)
    flat_top  = hood_frac >= 1.0

    # Blender Y = game Z (front/back; front = negative BY)
    y_fr = -hl
    y_cf = -hl + 2.0 * hl * cf_frac
    y_cr = -hl + 2.0 * hl * cr_frac
    y_rr =  hl

    # Blender Z = game Y (height)
    z_gc   = gc
    z_hood = gc + h * min(hood_frac, 1.0)
    z_roof = gc + h

    me = bpy.data.meshes.new(car_name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()

    if flat_top:
        # 12-vert flat-top box (bus / semi / trailer)
        L = [bm.verts.new(( hw, y, z)) for y, z in [
            (y_fr, z_gc),   (y_fr, z_roof),
            (y_cf, z_roof), (y_cr, z_roof),
            (y_rr, z_roof), (y_rr, z_gc),
        ]]
        R = [bm.verts.new((-hw, y, z)) for y, z in [
            (y_fr, z_gc),   (y_fr, z_roof),
            (y_cf, z_roof), (y_cr, z_roof),
            (y_rr, z_roof), (y_rr, z_gc),
        ]]
        sides = [
            bm.faces.new([L[0], L[5], L[4], L[3], L[2], L[1]]),
            bm.faces.new([R[0], R[1], R[2], R[3], R[4], R[5]]),
        ]
        cross = [
            (L[0], R[0], R[5], L[5]),
            (L[0], L[1], R[1], R[0]),
            (L[1], L[2], R[2], R[1]),
            (L[2], L[3], R[3], R[2]),
            (L[3], L[4], R[4], R[3]),
            (L[4], L[5], R[5], R[4]),
        ]
    else:
        # 16-vert sloped silhouette
        L = [bm.verts.new(( hw, y, z)) for y, z in [
            (y_fr, z_gc),   (y_fr, z_hood),
            (y_cf, z_hood), (y_cf, z_roof),
            (y_cr, z_roof), (y_cr, z_hood),
            (y_rr, z_hood), (y_rr, z_gc),
        ]]
        R = [bm.verts.new((-hw, y, z)) for y, z in [
            (y_fr, z_gc),   (y_fr, z_hood),
            (y_cf, z_hood), (y_cf, z_roof),
            (y_cr, z_roof), (y_cr, z_hood),
            (y_rr, z_hood), (y_rr, z_gc),
        ]]
        sides = [
            bm.faces.new([L[0], L[7], L[6], L[5], L[4], L[3], L[2], L[1]]),
            bm.faces.new([R[0], R[1], R[2], R[3], R[4], R[5], R[6], R[7]]),
        ]
        cross = [
            (L[0], R[0], R[7], L[7]),
            (L[0], L[1], R[1], R[0]),
            (L[1], L[2], R[2], R[1]),
            (L[2], L[3], R[3], R[2]),
            (L[3], L[4], R[4], R[3]),
            (L[4], L[5], R[5], R[4]),
            (L[5], L[6], R[6], R[5]),
            (L[6], L[7], R[7], R[6]),
        ]

    for face in sides:
        _planar_uv(face, uv)
        face.material_index = 0

    for verts in cross:
        face = bm.faces.new(verts)
        _planar_uv(face, uv)
        face.material_index = 0

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()

    body_off = list(t.get("body_offset", (0.0, 0.0, 0.0)))
    me["bms_flags"]       = 1
    me["texture_names"]   = ["CARBOTTOM"]
    me["mesh_offset"]     = body_off
    me["bms_source_file"] = ""
    me.materials.append(None)
    return me


# ── Wheel mesh ────────────────────────────────────────────────────────────────

def build_wheel_mesh(wheel_name: str, radius: float, half_width: float,
                     segments: int = 8, mirror: bool = False) -> bpy.types.Mesh:
    """
    Build an 8-segment cylinder wheel mesh (Blender space).

    Axle direction   = Blender X  (game X, side-to-side)
    Disc plane       = Blender Y-Z
    Bottom of wheel  = BZ = -radius (angle = 0)
    """
    N  = segments
    me = bpy.data.meshes.new(wheel_name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()

    L, R = [], []
    for i in range(N):
        angle = 2.0 * math.pi * i / N
        by =  radius * math.sin(angle)
        bz = -radius * math.cos(angle)  # 0 → bottom of wheel
        L.append(bm.verts.new(( half_width, by, bz)))
        R.append(bm.verts.new((-half_width, by, bz)))

    # Outer ring — N quads
    for i in range(N):
        ni   = (i + 1) % N
        face = bm.faces.new([L[i], L[ni], R[ni], R[i]])
        u0, u1 = i / N, (i + 1) / N
        for k, (u, v) in enumerate([(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)]):
            face.loops[k][uv].uv = (u, v)
        face.material_index = 0

    # Left cap (+BX outward)
    left_cap = bm.faces.new(L)
    # Right cap (-BX outward)
    right_cap = bm.faces.new(list(reversed(R)))
    for cap in (left_cap, right_cap):
        for j, loop in enumerate(cap.loops):
            a = 2.0 * math.pi * j / N
            loop[uv].uv = (0.5 + 0.5 * math.sin(a), 0.5 - 0.5 * math.cos(a))
        cap.material_index = 0

    if mirror:
        for v in bm.verts:
            v.co.x = -v.co.x
        for f in bm.faces:
            f.normal_flip()

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()

    me["bms_flags"]       = 1
    me["texture_names"]   = ["VACOMP_WHL"]
    me["bms_source_file"] = ""
    me.materials.append(None)
    return me


# ── Public compat API ─────────────────────────────────────────────────────────

def _make_templates() -> dict:
    out = {}
    for tid, label, _ in TEMPLATE_ITEMS:
        t = _T[tid]
        spec = {
            "label":        label,
            "body":         (t["hw"] * 2, t["h"], t["hl"] * 2, t["gc"],
                             t.get("cf_frac", 0.38), t.get("cr_frac", 0.62)),
            "wheel_radius": t["wheels"][0][3] if t["wheels"] else 0.30,
        }
        if len(t["wheels"]) != 4:
            spec["custom_wheels"] = t["wheels"]
        out[tid] = spec
    return out


TEMPLATES = _make_templates()

_DEFAULT_NAMES = {
    "COMPACT": "VPNEWCOMPACT",
    "SEDAN":   "VPNEWSEDAN",
    "SPORTS":  "VPNEWSPORTS",
    "PICKUP":  "VPNEWPICKUP",
    "TRUCK":   "VPNEWTRUCK",
    "BUS":     "VPNEWBUS",
    "SEMI":    "VPNEWSEMI",
    "TRAILER": "VPNEWTRAILER",
}


def get_template_items():
    return TEMPLATE_ITEMS


def get_template_default_name(template_id: str) -> str:
    return _DEFAULT_NAMES.get(template_id, "VPNEWCAR")


def template_body_offset(template_id: str) -> tuple:
    return tuple(_T[template_id].get("body_offset", (0.0, 0.0, 0.0)))


def template_body_filename(template_id: str) -> str:
    return _T[template_id].get("body_filename", "BODY_H.BMS")


def template_wheel_filename_prefix(template_id: str) -> str:
    return _T[template_id].get("wheel_prefix", "WHL")


def template_wheel_positions(template_id: str) -> list:
    return [(w[0], w[1], w[2]) for w in _T[template_id]["wheels"]]

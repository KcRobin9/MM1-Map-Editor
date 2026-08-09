"""
MM2 PSDL geometry  ->  MM1 Map-Editor polygons.

Input  : `expanded_psdl.json` from wilkovatch/psdl-import, shape:
           {"rooms": [ {"id": int,
                        "perimeter": [[x,y,z], ...],
                        "objects":   [ {"name": str,                 # road / facade / ...
                                        "vertices":  [[x,y,z], ...],  # object-local pool
                                        "triangles": [[i,i,i, ...]],  # indices into vertices
                                        "uvs":       [[u,v], ...],    # parallel to vertices
                                        "materials": [texIdx, ...]    # into raw textures pool
                                       }, ... ] }, ... ]}

Output : a stream of `Mm2PolySpec` (one MM1 polygon = one MM2 triangle), and
         `emit_mm2_city(create_polygon, save_mesh, compute_uv, ...)` which drives the
         pipeline API just like roadnet's `emit_roadnet_city`.

Design notes
------------
* Coordinates: MM2 is (x, y-up, z) on a ground plane of (x, z) - the SAME convention the
  roadnet compiler feeds the pipeline (the BMS writer applies its own (-x,z,y) later). So we
  pass MM2 (x,y,z) through, with an optional `mirror_x` to fix handedness if the city renders
  mirrored, and `scale` (MM2 and MM1 are both ~1 unit = 1 metre, so default 1.0).
* Cells: Phase-1 buckets geometry into a coarse spatial grid of <=199 ALWAYS-VISIBLE landmark
  cells (bound < 200). Landmark cells skip portal generation (no cull spin) and render always -
  heavier but guaranteed to stand up and collide. Real per-room cells + portals come later.
* Textures: mapped by object type -> existing MM1 core.ar tags (no texture conversion needed
  for a first boot). The real MM2 texture name is preserved on the spec for a later DDS pass.
"""
import re
import json
import math
from typing import Callable, Iterator, List, NamedTuple, Optional, Tuple
from pathlib import Path

from src.constants.file_formats import Material, Room, FileType
from src.constants.textures import Texture, MM2_TEXTURE_FALLBACK
from src.constants.color import Color
from src.constants.mm2 import MM2_OBJECT_TYPE, MM2_OBJECT_TYPE_DEFAULT
from src.core.geometry.planes import compute_normal   # WINDING/UV DESYNC FIX (_wind_up_facing)
from .mm2_buildings import iter_buildings



# Temporary flat water plane: quad size and UV scale of the T_WATER fill.
WATER_TILE = 150.0
WATER_UV_SCALE = -0.25


class Mm2Options(NamedTuple):
    mirror_x:    bool  = False   # flip handedness if the city renders mirrored
    scale:       float = 1.0     # MM2->MM1 unit scale (both ~1 m, default identity)
    grid_cells:  int   = 14      # (legacy uniform grid; only used if max_tris_per_cell<=0)
    drop_buildings: bool = False # Phase-1 toggle: skip facade/sliver/roof for a roads-only boot
    y_offset:    float = 0.0     # global vertical nudge
    spawn_xz: Tuple[float, float] = (0.0, 0.0)  # spawn at the road triangle nearest this (x,z)
    # ADAPTIVE CELLS: a quadtree splits the world so no cell exceeds max_tris_per_cell. The MM1
    # render path has a hard 16384-verts/mesh buffer (out[]/fogout[]) + _alloca(AdjunctCount)
    # stack scratch, so a cell mesh must stay well under that. 4000 tris = 12000 verts is safe.
    # All cells stay in the landmark range (<200, always-visible, no portals); must total <=199.
    max_tris_per_cell: int = 4000
    max_cell_depth:    int = 9
    # Real MM2 textures: when on, each triangle-group is textured with its actual MM2 texture name
    # (upper-cased) if a converted DDS for it exists in custom_dds_dir; else the object-type tag.
    use_real_textures: bool = True
    custom_dds_dir:    str  = ""   # folder of converted *.DDS (the editor's src/USER/textures/custom)
    facades_csv:       str  = ""   # MM2 facades.csv -> exact SF wall/roof/sliver texture pools
    inst_buildings:    str  = ""   # MM2 .inst path -> bake detailed INST/PKG buildings into the city
    inst_geometry_dir: str  = ""   # dir of MM2 .pkg building meshes (mm2core/geometry)
    water_level:       Optional[float] = None  # if set, lay a flat MM1 T_WATER plane at this Y to fill
                                               # the void where MM2's (separate) water surface would be


class Mm2PolySpec(NamedTuple):
    bound:          int
    verts:          List[Tuple[float, float, float]]   # 3 game-space (x,y,z) corners (triangle)
    material_index: int
    cell_type:      int
    hud_color:      str
    texture:        str                                 # MM1 tag
    tex_coords:     List[float]                         # [u0,v0,u1,v1,u2,v2]
    mm2_texture:    str                                 # original MM2 name (for later DDS pass)
    obj_type:       str


# ── loading ───────────────────────────────────────────────────────────────────

def load_expanded(json_path: str) -> dict:
    with open(json_path, "r") as f:
        return json.load(f)


def load_textures(raw_json_path: str) -> List[str]:
    """The MM2 texture-name pool from psdl-import's raw_psdl.json (material idx -> name).

    CRITICAL: psdl-import's geometry_expander indexes each object's `materials` into a
    DEDUPLICATED texture list (its `mat_map`, built by `for tex in textures: if tex not in
    mat_map`), NOT this raw global pool. sf.psdl's pool has 457 names but only 325 unique
    (132 duplicates), so every material index past the first dup pointed at the WRONG texture
    when resolved against the raw list -- crosswalks->r4_f (should be rxwalk_f), intersections->
    swalk_stone_l (should be rinter_f), ground fans->road/window textures (should be grass), etc.
    Dedup here (order-preserving) so material indices line up with the json -> exact MM2 textures."""
    with open(raw_json_path, "r") as f:
        raw = json.load(f).get("textures", [])
    seen = set(); out = []
    for t in raw:
        if t not in seen:
            seen.add(t); out.append(t)
    return out


# ── geometry helpers ────────────────────────────────────────────────────────────

def _world_bounds(data: dict) -> Tuple[float, float, float, float]:
    minx = minz = math.inf
    maxx = maxz = -math.inf
    for room in data["rooms"]:
        for obj in room.get("objects", []):
            for v in obj["vertices"]:
                minx = min(minx, v[0]); maxx = max(maxx, v[0])
                minz = min(minz, v[2]); maxz = max(maxz, v[2])
    return minx, minz, maxx, maxz


def _transform(v, opt: Mm2Options):
    x, y, z = v[0] * opt.scale, v[1] * opt.scale + opt.y_offset, v[2] * opt.scale
    if opt.mirror_x:
        x = -x
    return (x, y, z)


def _wind_up_facing(verts, uv):
    """WINDING/UV DESYNC FIX (TEXTURES item): orient a triangle up-facing HERE, reordering its
    verts AND their UV pairs TOGETHER so the texture corners stay glued to their vertex.

    The editor's create_polygon used to do this winding (process_winding -> ensure_ccw_order,
    planes.py:8) AFTER save_mesh had already stored the UVs in original order -> for a down-facing
    tri it swapped verts 1<->2 but NOT the UVs -> UV slots 1<->2 desynced -> textures mirrored/
    rotated (~half-a-tile). We now do the SAME up-facing test the editor did
    (compute_normal(...).Dot(+Y) < 0, i.e. normal.y < 0) but swap the matching UV pair as well,
    then emit with create_polygon(fix_winding=False) so the editor does NOT reorder again.

    For walls/up-facing tris (normal.y >= 0) this returns the input unchanged -- byte-identical to
    before -- so positions, textures, collision planes are untouched; only down-facing UV pairing
    changes. (This also makes the old S_JERSEY_RAIL UV band-aid unnecessary.)"""
    if compute_normal(verts[0], verts[1], verts[2]).y < 0.0:
        # down-facing: swap vert 1<->2 AND uv pair 1<->2 (keep each UV with its own vertex)
        return ([verts[0], verts[2], verts[1]],
                [uv[0], uv[1], uv[4], uv[5], uv[2], uv[3]])
    return verts, uv


# ── adaptive quadtree cells (keep every cell mesh under the engine's verts/mesh limit) ──

class _QNode:
    __slots__ = ("x0", "z0", "x1", "z1", "bound", "kids")

    def __init__(self, x0, z0, x1, z1):
        self.x0 = x0
        self.z0 = z0
        self.x1 = x1
        self.z1 = z1
        self.bound = 0; self.kids = None


def _build_quadtree(centroids, bbox, cap: int, max_depth: int):
    """Split until each leaf holds <= cap centroids. Returns (root, num_cells). Non-empty
    leaves get bound numbers 1..N (landmark range, <200)."""
    root = _QNode(*bbox)
    counter = [0]

    def split(node, pts, depth):
        if len(pts) <= cap or depth >= max_depth:
            if pts:
                counter[0] += 1
                node.bound = counter[0]
            return
        mx = (node.x0 + node.x1) * 0.5
        mz = (node.z0 + node.z1) * 0.5
        node.kids = [_QNode(node.x0, node.z0, mx, mz), _QNode(mx, node.z0, node.x1, mz),
                     _QNode(node.x0, mz, mx, node.z1), _QNode(mx, mz, node.x1, node.z1)]
        q = ([], [], [], [])

        for p in pts:
            q[(0 if p[0] < mx else 1) + (0 if p[1] < mz else 2)].append(p)

        for kid, kpts in zip(node.kids, q):
            split(kid, kpts, depth + 1)

    split(root, centroids, 0)
    return root, counter[0]


def _leaf_bound(root, cx, cz) -> int:
    node = root
    while node.kids is not None:
        mx = (node.x0 + node.x1) * 0.5
        mz = (node.z0 + node.z1) * 0.5
        node = node.kids[(0 if cx < mx else 1) + (0 if cz < mz else 2)]
    return node.bound


# ── the polygon stream ──────────────────────────────────────────────────────────


def _append_building_records(records, extra_tris, opt: Mm2Options, converted,
                             bounds) -> Tuple[float, float, float, float]:
    """Add INST/PKG building triangles (already world-space) as records; return the grown bounds."""
    minx, maxx, minz, maxz = bounds

    for texture_name, triangle in extra_tris:
        corner_a, corner_b, corner_c = triangle
        if opt.mirror_x:
            corner_b, corner_c = corner_c, corner_b

        p0 = _transform(corner_a[0], opt)
        p1 = _transform(corner_b[0], opt)
        p2 = _transform(corner_c[0], opt)
        if _degenerate(p0, p1, p2):
            continue

        upper = (texture_name or "").upper()
        texture = upper if (upper and (converted is None or upper in converted)) else Texture.BRICKS_GREY
        uv = [corner_a[1][0], corner_a[1][1], corner_b[1][0], corner_b[1][1],
              corner_c[1][0], corner_c[1][1]]

        centre_x = (p0[0] + p1[0] + p2[0]) / 3.0
        centre_z = (p0[2] + p1[2] + p2[2]) / 3.0
        minx, maxx = min(minx, centre_x), max(maxx, centre_x)
        minz, maxz = min(minz, centre_z), max(maxz, centre_z)

        records.append(([p0, p1, p2], Material.DEFAULT, Color.IND_WALL, texture, uv,
                        texture, "building", centre_x, centre_z))

    return minx, maxx, minz, maxz

def iter_mm2_polys(data: dict, opt: Mm2Options = Mm2Options(),
                   textures: "List[str]" = None, converted: "set" = None,
                   building_tex: dict = None, extra_tris=None,
                   reject_stats: dict = None) -> Iterator[Mm2PolySpec]:
    """Yield one Mm2PolySpec per MM2 triangle. Cells come from an adaptive quadtree so no cell
    mesh exceeds max_tris_per_cell (keeping it under the engine's per-mesh verts/alloca limit).

    If `textures` (the MM2 name pool) is given, each triangle-GROUP group_index is textured with its real
    MM2 texture `textures[materials[group_index]]` (upper-cased) when a converted DDS exists for it (i.e. the
    name is in `converted`); otherwise it falls back to the object-type placeholder tag."""
    minx, minz, maxx, maxz = _world_bounds(data)
    building_types = ("facade", "sliver", "roof_triangle_fan")

    # Prefer a real MM2 texture over the MM1 placeholder when a poly's own material is empty
    # (MM2 fills these from the active texture-ref, which psdl-import drops) - keeps the city all-MM2.
    def resolve_tex(materials, group_index, default_tex):
        # group group_index uses material group_index (verified: len(triangles)==len(materials) per object)
        if textures and 0 <= group_index < len(materials):
            midx = materials[group_index]
            if 0 <= midx < len(textures):
                nm = (textures[midx] or "").strip()
                up = nm.upper()
                if up and (converted is None or up in converted):
                    return up, nm
        mm2def = MM2_TEXTURE_FALLBACK.get(default_tex)
        if mm2def and (converted is None or mm2def in converted):
            return mm2def, ""
        return default_tex, ""

    # Pass 1: build every triangle's geometry + centroid (drop degenerate / buildings here).
    records = []   # (verts, mat, hud, tex, uv, mm2_tex, object_type, cx, cz)
    for room in data["rooms"]:
        # Compute room centroid (transformed) once per room for facade outward-facing check below.
        perim = room.get("perimeter", [])
        if perim:
            rcx = sum(p[0] for p in perim) / len(perim)
            rcy = sum(p[1] for p in perim) / len(perim)
            rcz = sum(p[2] for p in perim) / len(perim)
            room_centroid = _transform((rcx, rcy, rcz), opt)
        else:
            room_centroid = None
        for obj in room.get("objects", []):
            object_type = obj.get("name", "")
            if opt.drop_buildings and object_type in building_types:
                continue
            default_tex, mat, hud = MM2_OBJECT_TYPE.get(object_type, MM2_OBJECT_TYPE_DEFAULT)
            verts_local = obj["vertices"]
            uvs_local = obj.get("uvs") or []
            materials = obj.get("materials") or []

            # Buildings (facade/sliver/roof): texture from the object's OWN dedup-resolved texRef =
            # the EXACT MM2 wall/roof texture (dedup bug fixed; the full used texture set is converted
            # to DDS). The old per-OBJECT csv-pool hash (facades.csv) was a band-aid for the dedup bug;
            # the real texRef matches MM2 building-for-building. UVs come from psdl-import's real facade
            # uRepeat/vRepeat (_tri_uvs below), with a generated storey-tiled fallback only for the few
            # facade blocks with a misparsed UV field.
            is_building = bool(verts_local) and object_type in building_types
            bld_uv_mode = None
            if is_building:
                fv = verts_local[0]
                bld_ox = float(fv[0]); bld_oz = float(fv[2])
                bld_ymin = min(v[1] for v in verts_local)
                bld_vscale = _FACADE_FLOOR_H
                bld_uv_mode = "roof" if object_type == "roof_triangle_fan" else "wall"

            for group_index, tri_group in enumerate(obj.get("triangles", [])):
                # Real MM2 texture per GROUP, resolved against the DEDUPED pool (see load_textures):
                # exact engine texture for EVERY object -- intersections->rinter_f, crosswalks->rxwalk_f,
                # ground->grass/concrete, roads->real surface, facade/sliver/roof->real MM2 wall/roof.
                # FACADE COLOR FIX: the old "pool[group_index % len(pool)]" override blindly cycled through a
                # sorted alpha set, ignoring the per-face MM2 texture -> all facades got pool[0] (same
                # color) or a wrong rotation. Now: try the REAL per-face texture first (resolve_tex uses
                # the dedup-fixed material index -> exact MM2 wall color per building face). Fall back to
                # the pool ONLY when the real texture is not yet converted (pool adds variety for any
                # un-converted faces instead of falling all the way back to the grey default wall).
                if is_building:
                    gtex, gmm2 = resolve_tex(materials, group_index, default_tex)
                    if gtex == default_tex and building_tex:
                        # real texture not converted -> try pool for variety
                        pool_type = "roof" if object_type == "roof_triangle_fan" else ("sliver" if object_type == "sliver" else "wall")
                        pool = building_tex.get(pool_type)
                        if pool:
                            if isinstance(pool, list) and pool:
                                gtex = pool[group_index % len(pool)]
                                gmm2 = gtex
                            elif isinstance(pool, str):
                                gtex = pool
                                gmm2 = gtex
                    if reject_stats is not None:
                        reject_stats["pool_tex_used"] = reject_stats.get("pool_tex_used", 0) + 1
                else:
                    gtex, gmm2 = resolve_tex(materials, group_index, default_tex)
                if is_building and bld_uv_mode == "wall":
                    bld_vscale = _facade_height(gtex)   # storey height for the garbage-UV fallback
                for k in range(0, len(tri_group) - 2, 3):
                    i0, i1, i2 = tri_group[k], tri_group[k + 1], tri_group[k + 2]
                    try:
                        v0 = verts_local[i0]; v1 = verts_local[i1]; v2 = verts_local[i2]
                    except IndexError:
                        continue
                    p0 = _transform(v0, opt); p1 = _transform(v1, opt); p2 = _transform(v2, opt)
                    if _degenerate(p0, p1, p2):
                        continue
                    # BOUNDS/COLLISION FIX (FALL-THROUGH): drop SLIVER drivable tris. A sliver
                    # (long needle, sub-mm shortest edge or extreme aspect) survives _degenerate yet
                    # its rounded edge half-planes collapse so point-in-poly rejects every probe ->
                    # the car falls through. Slivers are visually ~zero-area so dropping them is safe.
                    # NB: we deliberately do NOT drop near-vertical drivable polys here -- in MM2 the
                    # vertical curb risers / road-edge walls are tagged sidewalk_strip/road and ARE
                    # real visible geometry (~14k in SF). They are correctly kept out of the drivable
                    # HITID grid by the |ny|>=0.3 filter on the editor side; deleting them would gouge
                    # holes in every curb. (See _ground/hitid split in MAP_EDITOR_ALPHA_v1.py.)
                    if object_type in _DRIVABLE_TYPES and _sliver(p0, p1, p2):
                        if reject_stats is not None:
                            reject_stats["sliver"] = reject_stats.get("sliver", 0) + 1
                        continue
                    if opt.mirror_x:           # mirroring flips winding -> swap two verts
                        p1, p2 = p2, p1
                        i1, i2 = i2, i1
                    # FACADE OUTWARD-FACING FIX: PSDL facade/sliver winding is inconsistent — ~70%
                    # of triangles face AWAY from the room interior (away from the drivable street
                    # space), making them invisible to the player. Root cause: psdl-import's "left"/"right"
                    # vertex ordering depends on perimeter traversal direction, which varies per room.
                    # Fix: if the normal points away from the room centroid (= into the building, away
                    # from the street), flip the winding so it faces the open drivable space instead.
                    # The room perimeter encloses the open street space; centroid = street interior.
                    # Correct orientation: normal toward centroid (visible from street).
                    if object_type in ("facade", "sliver") and room_centroid is not None:
                        n = compute_normal(p0, p1, p2)
                        mx = (p0[0]+p1[0]+p2[0])/3; mz = (p0[2]+p1[2]+p2[2])/3
                        my = (p0[1]+p1[1]+p2[1])/3
                        dx = mx-room_centroid[0]; dy = my-room_centroid[1]; dz = mz-room_centroid[2]
                        if n.x*dx + n.y*dy + n.z*dz > 0:  # normal away from centroid = wrong
                            p1, p2 = p2, p1
                            i1, i2 = i2, i1
                    if is_building:
                        # Use psdl-import's REAL MM2 facade/roof UVs (facade block's uRepeat/vRepeat
                        # tiling; roof = planar -0.25*x,z). A few facade blocks have a misparsed field
                        # (V ~65534) -> fall back to the generated storey-tiled UV only for those.
                        uv = _tri_uvs(uvs_local, i0, i1, i2)
                        used_fallback_uv = False
                        if bld_uv_mode == "wall" and max(abs(c) for c in uv) > 1000.0:
                            gu0 = _gen_building_uv(bld_uv_mode, bld_ox, bld_oz, bld_ymin, verts_local[i0], bld_vscale)
                            gu1 = _gen_building_uv(bld_uv_mode, bld_ox, bld_oz, bld_ymin, verts_local[i1], bld_vscale)
                            gu2 = _gen_building_uv(bld_uv_mode, bld_ox, bld_oz, bld_ymin, verts_local[i2], bld_vscale)
                            uv = [gu0[0], gu0[1], gu1[0], gu1[1], gu2[0], gu2[1]]
                            used_fallback_uv = True
                        # V-AXIS CORRECTION for inverted facades: some PSDL cities (SF/London) have
                        # facade sections where semantic "top" Y < "bottom" Y (hillside overhangs,
                        # basement ledges). psdl-import puts V=0 at the semantic top regardless of its
                        # physical Y. In DirectX, V=0 = top of texture, so V=0 at the physically LOWER
                        # vertex renders the texture upside-down. Fix: if the V=0 vertex is physically
                        # below the V=max vertex, mirror V so the higher-Y vertex gets V=0.
                        if object_type == "facade" and bld_uv_mode == "wall" and not used_fallback_uv:
                            _v0, _v1, _v2 = uv[1], uv[3], uv[5]
                            vmin, vmax = min(_v0, _v1, _v2), max(_v0, _v1, _v2)
                            if vmax > vmin + 0.01:
                                vlist = [_v0, _v1, _v2]
                                ylist = [p0[1], p1[1], p2[1]]
                                y_at_vmin = ylist[vlist.index(vmin)]
                                y_at_vmax = ylist[vlist.index(vmax)]
                                if y_at_vmin < y_at_vmax:  # V=0 vertex is physically lower -> flip
                                    uv[1] = vmin + vmax - uv[1]
                                    uv[3] = vmin + vmax - uv[3]
                                    uv[5] = vmin + vmax - uv[5]
                    else:
                        uv = _tri_uvs(uvs_local, i0, i1, i2)
                    # S_JERSEY_RAIL V-FLIP: the DDS was stored bottom-to-top (row 0 = concrete,
                    # row N = yellow paint), but the PSDL places V=0 at the physical TOP of the
                    # barrier where yellow should appear. Flip V so top→V=0→yellow is correct.
                    # (The old band-aid was -u,1-v; the -u was UV-desync noise now gone; only 1-v
                    # is the real texture-origin issue.)
                    if gmm2 and gmm2.upper() == "S_JERSEY_RAIL":
                        uv[1] = 1.0 - uv[1]
                        uv[3] = 1.0 - uv[3]
                        uv[5] = 1.0 - uv[5]
                    cx = (p0[0] + p1[0] + p2[0]) / 3.0
                    cz = (p0[2] + p1[2] + p2[2]) / 3.0
                    records.append(([p0, p1, p2], mat, hud, gtex, uv, gmm2, object_type, cx, cz))

    # Detailed INST/PKG buildings share the cell quadtree with the PSDL geometry, so they are
    # appended as records and the world bounds grow to include them.
    if extra_tris:
        minx, maxx, minz, maxz = _append_building_records(
            records, extra_tris, opt, converted, (minx, maxx, minz, maxz))

    # Temporary flat WATER plane (MM1 core T_WATER) at water_level, filling the void where MM2's
    # separate water surface would be. A coarse grid of quads over the world bounds; cells assigned
    # like everything else. (Proper MM2 water is a separate task.)
    if opt.water_level is not None:
        water_y = float(opt.water_level)
        _, material, hud_color = MM2_OBJECT_TYPE.get("triangle_fan", MM2_OBJECT_TYPE_DEFAULT)

        grid_x = math.floor(minx / WATER_TILE) * WATER_TILE
        while grid_x < maxx:

            grid_z = math.floor(minz / WATER_TILE) * WATER_TILE
            while grid_z < maxz:
                corners = [(grid_x, water_y, grid_z),
                           (grid_x + WATER_TILE, water_y, grid_z),
                           (grid_x + WATER_TILE, water_y, grid_z + WATER_TILE),
                           (grid_x, water_y, grid_z + WATER_TILE)]
                points = [_transform(corner, opt) for corner in corners]
                uvs = [(corner[0] * WATER_UV_SCALE, corner[2] * WATER_UV_SCALE) for corner in corners]

                # UP-facing (+Y) winding, so the collision down-ray hits the surface
                for a, b, c in ((0, 2, 1), (0, 3, 2)):
                    p0, p1, p2 = points[a], points[b], points[c]
                    uv = [uvs[a][0], uvs[a][1], uvs[b][0], uvs[b][1], uvs[c][0], uvs[c][1]]
                    centre_x = (p0[0] + p1[0] + p2[0]) / 3.0
                    centre_z = (p0[2] + p1[2] + p2[2]) / 3.0
                    records.append(([p0, p1, p2], material, hud_color, "T_WATER", uv,
                                    "T_WATER", "water", centre_x, centre_z))

                grid_z += WATER_TILE

            grid_x += WATER_TILE

    # Build the cell assignment: adaptive quadtree (default) or the legacy uniform grid.
    if opt.max_tris_per_cell and opt.max_tris_per_cell > 0:
        root, ncells = _build_quadtree([(r[7], r[8]) for r in records],
                                       (minx, minz, maxx, maxz),
                                       int(opt.max_tris_per_cell), int(opt.max_cell_depth))
        # No hard cell limit: the engine allocates CellArray dynamically and IDs beyond 199 work
        # (verified to 5000). The 1-199 / 200+ split only picks lm vs city BMS, so just log it.
        if ncells > 199:
            print(f"[MM2] NOTE: {ncells} quadtree cells (>199; cells 200+ go into city BMS — geometry still renders)")

        def cell_for(cx, cz):
            return _leaf_bound(root, cx, cz)
    else:
        n = max(1, int(opt.grid_cells))
        span_x = max(maxx - minx, 1e-3); span_z = max(maxz - minz, 1e-3)

        def cell_for(cx, cz):
            gx = min(n - 1, max(0, int((cx - minx) / span_x * n)))
            gz = min(n - 1, max(0, int((cz - minz) / span_z * n)))
            return gx * n + gz + 1

    for verts, mat, hud, tex, uv, mm2_tex, object_type, cx, cz in records:
        # WINDING/UV DESYNC FIX: pre-wind every tri up-facing and reorder its UV pair with it,
        # then emit via create_polygon(fix_winding=False) so the editor won't reorder again.
        verts, uv = _wind_up_facing(verts, uv)
        yield Mm2PolySpec(
            bound=cell_for(cx, cz), verts=verts, material_index=mat,
            cell_type=Room.DEFAULT, hud_color=hud, texture=tex,
            tex_coords=uv, mm2_texture=mm2_tex, obj_type=object_type,
        )


_ROAD_LIKE = ("road", "road_triangle_fan", "walkway", "divided_road")


def _pick_spawn(specs: List[Mm2PolySpec], target_xz: Tuple[float, float]) -> int:
    """Index of the road-like triangle whose centroid is nearest target_xz (-1 if none)."""
    tx, tz = target_xz
    best, best_d = -1, math.inf
    for i, s in enumerate(specs):
        if s.obj_type not in _ROAD_LIKE:
            continue
        cx = (s.verts[0][0] + s.verts[1][0] + s.verts[2][0]) / 3.0
        cz = (s.verts[0][2] + s.verts[1][2] + s.verts[2][2]) / 3.0
        d = (cx - tx) ** 2 + (cz - tz) ** 2
        if d < best_d:
            best_d, best = d, i

    return best


# Building facade UVs: psdl-import's facade V is garbage (up to 65534), so when we override a
# building poly's texture we also generate clean UVs - U along the wall, V by height (each ~floor
# = one texture tile) - so window/facade textures tile by storey instead of smearing.
_FACADE_TILE_W = 6.0    # metres per facade texture column (window bay)
_FACADE_FLOOR_H = 4.0   # metres per facade texture row (storey)
_ROOF_TILE = 8.0        # metres per roof (concrete) tile


def _load_facade_pools(csv_path: str, converted) -> Optional[dict]:
    """Read MM2 facades.csv (neighborhood,name,roof,front,left,right,back,sliver) and return the EXACT
    SF building texture pools {wall, roof, sliver}, filtered to textures we actually converted. Skips
    composite-facade names (e.g. 'MarinaHomeFront01' - those aren't direct textures). Returns None if
    the file is unreadable or yields no usable textures."""
    try:
        lines = open(csv_path, encoding="latin-1").read().splitlines()
    except OSError:
        return None
    wall, roof, sliver = set(), set(), set()

    for ln in lines[1:]:
        c = [x.strip() for x in ln.split(",")]
        if len(c) < 8:
            continue
        for face in c[3:7]:                       # front/left/right/back
            up = face.upper()
            if up and (converted is None or up in converted):
                wall.add(up)
        if c[2] and (converted is None or c[2].upper() in converted):
            roof.add(c[2].upper())
        if c[7] and (converted is None or c[7].upper() in converted):
            sliver.add(c[7].upper())

    if not wall:
        return None

    return {"wall": sorted(wall), "roof": sorted(roof) or None, "sliver": sorted(sliver) or None}


def _facade_height(name: str) -> float:
    """MM2 facade textures encode the building height they cover in the name (..._8_F / _6_F /
    _4_F). Use it as the V tile height so one texture tile spans the right number of storeys."""
    m = re.search(r"_(\d+)_[A-Z]$", name or "")
    return float(m.group(1)) if m else _FACADE_FLOOR_H


def _gen_building_uv(mode, ox, oz, ymin, v, v_scale=_FACADE_FLOOR_H) -> Tuple[float, float]:
    if mode == "roof":
        return (v[0] / _ROOF_TILE, v[2] / _ROOF_TILE)
    # wall: U = horizontal distance from the object's first vertex, V = height above its base
    du = ((v[0] - ox) ** 2 + (v[2] - oz) ** 2) ** 0.5
    return (du / _FACADE_TILE_W, (v[1] - ymin) / v_scale)


def _tri_uvs(uvs_local, i0, i1, i2) -> List[float]:
    def uv(i):
        if 0 <= i < len(uvs_local):
            u, v = uvs_local[i][0], uvs_local[i][1]
            return float(u), float(v)
        return 0.0, 0.0
    u0, v0 = uv(i0); u1, v1 = uv(i1); u2, v2 = uv(i2)
    return [u0, v0, u1, v1, u2, v2]


def _degenerate(p0, p1, p2, eps: float = 1e-5) -> bool:
    ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
    cx = ay * bz - az * by
    cy = az * bx - ax * bz
    cz = ax * by - ay * bx
    return (cx * cx + cy * cy + cz * cz) < eps


# Drivable obj_types: surfaces the car is meant to land/drive on. Their collision plane MUST be a
# clean, up-oriented horizontal-ish plane or the car falls through / loses control. (Excludes
# facade/sliver/roof/building -> those are walls and are allowed to be vertical.)
_DRIVABLE_TYPES = frozenset((
    "road", "divided_road", "walkway", "road_triangle_fan",
    "triangle_fan", "sidewalk_strip", "crosswalk",
))


def _sliver(p0, p1, p2, min_edge: float = 0.02, max_aspect: float = 4000.0) -> bool:
    """BOUNDS/COLLISION FIX (FALL-THROUGH): a triangle that survives _degenerate (area^2 >= 1e-5)
    can still be a SLIVER -- a long, near-zero-width needle. Slivers have a non-trivial area yet
    their rounded edge half-planes (compute_edges) collapse so point-in-poly rejects every probe
    -> no collision hit -> the car falls through. Reject when the shortest edge is sub-mm, or the
    longest-edge / shortest-altitude aspect ratio is extreme (needle)."""
    e0 = ((p1[0]-p0[0])**2 + (p1[1]-p0[1])**2 + (p1[2]-p0[2])**2) ** 0.5
    e1 = ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2) ** 0.5
    e2 = ((p0[0]-p2[0])**2 + (p0[1]-p2[1])**2 + (p0[2]-p2[2])**2) ** 0.5
    shortest = min(e0, e1, e2)
    longest = max(e0, e1, e2)

    if shortest < min_edge:
        return True
    # altitude against the longest edge = 2*area / longest; aspect = longest / altitude
    ax, ay, az = p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]
    bx, by, bz = p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]
    cx = ay*bz - az*by; cy = az*bx - ax*bz; cz = ax*by - ay*bx
    area2 = (cx*cx + cy*cy + cz*cz) ** 0.5            # = 2 * triangle area

    if area2 <= 1e-9:
        return True
    altitude = area2 / longest if longest > 1e-9 else 0.0

    return altitude > 1e-9 and (longest / altitude) > max_aspect


# ── pipeline driver (mirrors emit_roadnet_city) ─────────────────────────────────

def emit_mm2_city(create_polygon: Callable, save_mesh: Callable, compute_uv: Callable,
                  json_path: str, opt: Mm2Options = Mm2Options(),
                  overrides: dict = None) -> dict:
    """
    Author every MM2 triangle into the MM1 pipeline. Returns stats. The pipeline then derives
    bounds / cells / (skipped portals) / TSH / .AR from the authored polygons.

    overrides: Blender cell-edit round-trip (operators/mm2_cells.py). Maps cell id (str/int) ->
    list of {"v": [[x,y,z]x3 game], "uv": [6 floats game], "tex": MM1 texture tag, "ot": obj_type}.
    Every listed cell's polygons are REPLACED by the exported ones before emission.
    """
    data = load_expanded(json_path)

    # Real MM2 textures: load the name pool (raw_psdl.json, sibling of expanded) + the set of
    # converted DDS names present in custom_dds_dir, so the adapter uses real textures where
    # available and the object-type placeholder elsewhere.
    textures = converted = None
    if opt.use_real_textures:
        raw_path = json_path.replace("expanded_psdl.json", "raw_psdl.json")
        if Path(raw_path).exists():
            try:
                textures = load_textures(raw_path)  # DEDUPED to match json material indices
            except Exception:
                textures = None
        custom_dds_dir = Path(opt.custom_dds_dir) if opt.custom_dds_dir else None
        if custom_dds_dir and custom_dds_dir.is_dir():
            converted = {dds.stem.upper()
                         for dds in custom_dds_dir.glob(f"*{FileType.DIRECTDRAW_SURFACE}")}

    # Building facade pool: the real SF wall textures (neighborhood-prefixed WIN/WALL/WOOD/MAT/BRICK,
    # excluding narrow DOOR strips), used to texture facade/sliver polys (see iter_mm2_polys). Roofs
    # get a flat concrete. Falls back to None (object-type placeholder) if none converted.
    building_tex = None
    if converted:
        # broad WALL pool by name pattern (max variety); facades.csv adds its exact entries + the real
        # ROOF/SLIVER pools (roof variety: MM2 uses several roof textures, not one flat concrete).
        wall = set(c for c in converted
                   if re.match(r"(SF|MF|GF|NF|CF|EF|KF|LF|RF|DF|OF|PF|TF|WF|HF|NL)_", c)
                   and any(t in c for t in ("WIN", "WALL", "WOOD", "MAT_", "BRICK", "NONBAY", "STUCCO")))
        roof = next((c for c in ("SF_CONCRETE_5", "S_CONC_RAIL") if c in converted),
                    next((c for c in sorted(converted) if "CONC" in c), Texture.BRICKS_GREY))
        sliver = None
        fac = _load_facade_pools(opt.facades_csv, converted) if opt.facades_csv else None
        if fac:
            wall |= set(fac["wall"])
            roof = fac["roof"] or roof
            sliver = fac["sliver"]
        if wall:
            building_tex = {"wall": sorted(wall), "roof": roof, "sliver": sliver}

    # Detailed INST/PKG buildings (optional): assemble world-space tris from the .inst placements x
    # .pkg meshes and bake them into the city alongside the PSDL geometry.
    extra_tris = None
    if opt.inst_buildings and opt.inst_geometry_dir and Path(opt.inst_buildings).is_file():
            extra_tris = [(tex, (a, b, c))
                      for tex, a, b, c in iter_buildings(opt.inst_buildings, opt.inst_geometry_dir)]

    reject_stats: dict = {}
    specs = list(iter_mm2_polys(data, opt, textures=textures, converted=converted,
                                building_tex=building_tex, extra_tris=extra_tris,
                                reject_stats=reject_stats))

    # BLENDER CELL EDITS (round-trip): replace whole cells with the polys exported from Blender.
    # Applied BEFORE spawn-pick so indices stay consistent. Degenerate edited tris are skipped;
    # winding is normalized the same way as source polys (_wind_up_facing keeps verts+UVs glued).
    if overrides:
        ov_cells = {int(k): v for k, v in overrides.items()}
        n_before = len(specs)
        specs = [s for s in specs if s.bound not in ov_cells]
        n_dropped = n_before - len(specs)
        n_added = n_degen = 0
        for bound, ov_polys in sorted(ov_cells.items()):
            for p in ov_polys:
                verts = [tuple(float(c) for c in corner) for corner in p["v"]]
                if len(verts) != 3 or _degenerate(*verts):
                    n_degen += 1
                    continue
                uv = [float(x) for x in (p.get("uv") or [0.0] * 6)][:6]
                verts, uv = _wind_up_facing(verts, uv)
                object_type = p.get("ot") or "road"
                default_tex, mat, hud = MM2_OBJECT_TYPE.get(object_type, MM2_OBJECT_TYPE_DEFAULT)
                tex = (p.get("tex") or default_tex).upper()
                specs.append(Mm2PolySpec(
                    bound=bound, verts=verts, material_index=mat, cell_type=Room.DEFAULT,
                    hud_color=hud, texture=tex, tex_coords=uv, mm2_texture=tex, obj_type=object_type))
                n_added += 1
        print(f"mm2: BLENDER CELL OVERRIDES applied -> {len(ov_cells)} cell(s): "
              f"{n_dropped} polys replaced by {n_added}"
              + (f" ({n_degen} degenerate skipped)" if n_degen else ""))

    # spawn: mark the road triangle nearest opt.spawn_xz as base=True so the pipeline sets the
    # cruise start from it (same coord transform as the geometry - no manual-coords mismatch).
    spawn_idx = _pick_spawn(specs, opt.spawn_xz)

    n_poly = 0
    cells = set()
    tex_counts = {}
    # obj_type per emitted polygon, in creation order (create_polygon appends exactly one poly per
    # call, so this list lines up 1:1 with the editor's polys[1:] -- index 0 is the filler poly).
    # The ground-snap pass (groundsnap.snap_props) uses it to EXCLUDE building roofs/podiums/facades
    # when picking the surface a prop rests on (else traffic-lights ride up onto buildings). See BUG A.
    obj_types = []
    for idx, spec in enumerate(specs):
        create_polygon(
            bound_number=spec.bound,
            vertex_coordinates=spec.verts,
            material_index=spec.material_index,
            cell_type=spec.cell_type,
            hud_color=spec.hud_color,
            always_visible=True,     # landmark cells: render always, no portals
            fix_winding=False,       # WINDING/UV FIX: already pre-wound up-facing in iter_mm2_polys
                                     # (verts + UVs reordered together) -- do NOT reorder again here
                                     # or the UV pairing desyncs (the original textures-rotated bug).
            base=(idx == spawn_idx),
        )
        compute_uv(bound_number=spec.bound, tile_x=1.0, tile_y=1.0, angle_degrees=0.0)
        save_mesh(texture_name=[spec.texture], tex_coords=spec.tex_coords)
        obj_types.append(spec.obj_type)
        n_poly += 1
        cells.add(spec.bound)
        tex_counts[spec.texture] = tex_counts.get(spec.texture, 0) + 1
    return {"polygons": n_poly, "cells": len(cells), "textures": tex_counts, "obj_types": obj_types,
            "rejected_slivers": reject_stats.get("sliver", 0), "facade_pool_textures": reject_stats.get("pool_tex_used", 0)}


# ── standalone self-test (Blender-free) ─────────────────────────────────────────

if __name__ == "__main__":
    import sys, collections
    path = sys.argv[1] if len(sys.argv) > 1 else "output/expanded_psdl.json"
    opt = Mm2Options()
    data = load_expanded(path)
    minx, minz, maxx, maxz = _world_bounds(data)
    print(f"world: X[{minx:.1f},{maxx:.1f}] Z[{minz:.1f},{maxz:.1f}]  rooms={len(data['rooms'])}")
    by_type = collections.Counter()
    by_tex = collections.Counter()
    cells = set()
    npoly = 0
    ys = []
    for s in iter_mm2_polys(data, opt):
        npoly += 1
        by_type[s.obj_type] += 1
        by_tex[s.texture] += 1
        cells.add(s.bound)
        for v in s.verts:
            ys.append(v[1])
    print(f"polygons(triangles): {npoly}   cells: {len(cells)} (grid {opt.grid_cells}x{opt.grid_cells})")
    print(f"Y range: {min(ys):.2f}..{max(ys):.2f}")
    print("by object type:", dict(by_type))
    print("by MM1 texture:", dict(by_tex))

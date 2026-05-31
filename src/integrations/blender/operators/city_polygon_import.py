"""
City Polygon Import — round-trip editing of existing city BMS files.

Reads CULL{N}_H.BMS and CULL{N}_A.BMS from MESHES/ and creates one Blender
mesh object per BMS surface, named P{N} (Blender auto-deduplicates to
P{N}.001, P{N}.002 … for multi-surface cells).  The export system finds
these objects by their P-prefix names and re-emits one create_polygon() +
save_mesh() call per face, which flush_meshes() reassembles into the correct
CULL{N}_H.bms files.

_H vs _A separation
────────────────────
_H surfaces land in collection "City Polygons" with name P{N}.
_A surfaces land in collection "City Polygons (A)" with name PA{N}.
PA{N} objects are skipped by the standard export operator (which only
selects names starting with "P" followed by a digit), so they serve as
read-only reference until a dedicated _A export path is added.

UV round-trip strategy
─────────────────────
Raw BMS UV values are inverted to (tile_x, tile_y, angle_degrees) via
_invert_compute_uv(), which exactly reverses compute_uv()'s unit-quad
transform.  These are stored as the standard object properties so:
  - the Blender viewport shows correct tiling via update_uv_tiling()
  - the exporter emits compute_uv(…) identically to editor-created polygons
  - no special-casing is needed anywhere in the export pipeline

Normal round-trip
─────────────────
Per-adjunct packed normal indices are stored as obj["bms_normals"] (flat list,
same order as the face corners).  export_formatted_polygons writes them as the
normals= argument of save_mesh() so the game lighting matches the original.
"""

import re
import math
import bpy
import bmesh
from pathlib import Path
from typing import List, Optional, Tuple

from src.constants.folder import Folder
from src.io.binary import read_unpack


def _invert_compute_uv(raw_uvs: List[float]) -> Tuple[float, float, float]:
    """
    Recover (tile_x, tile_y, angle_degrees) from raw BMS UV pairs.

    compute_uv() maps the unit quad V0=(0,0) V1=(1,0) V2=(1,1) V3=(0,1) as:
        u = (rotate_x(x-0.5, y-0.5, θ) + 0.5) * tile_x
        v = (rotate_y(x-0.5, y-0.5, θ) + 0.5) * tile_y

    Step V0→V1 (unit vector (1,0)) maps to (cos θ · tile_x,  sin θ · tile_y).
    Step V0→V3 (unit vector (0,1)) maps to (-sin θ · tile_x,  cos θ · tile_y).
    For triangles V3 is absent; use V2−V1 which equals the V0→V3 step.

    Returns (1.0, 1.0, 0.0) on degenerate input.
    """
    n = len(raw_uvs) // 2
    u = [raw_uvs[i * 2]     for i in range(n)]
    v = [raw_uvs[i * 2 + 1] for i in range(n)]

    du10 = u[1] - u[0]
    dv10 = v[1] - v[0]

    if n >= 4:
        du30 = u[3] - u[0]
        dv30 = v[3] - v[0]
    else:
        du30 = u[2] - u[1]
        dv30 = v[2] - v[1]

    tile_x = math.sqrt(du10 * du10 + du30 * du30)
    tile_y = math.sqrt(dv10 * dv10 + dv30 * dv30)

    if tile_x < 1e-6 or tile_y < 1e-6:
        return 1.0, 1.0, 0.0

    angle_degrees = math.degrees(math.atan2(dv10 / tile_y, du10 / tile_x))
    return tile_x, tile_y, angle_degrees


_COL_H  = "City Polygons"
_COL_LM = "City Polygons (LM)"
_COL_A  = "City Polygons (A)"

# _H matches CULL{N}_H.BMS and CULL{N}_H2.BMS etc. (all H-variants)
_H_PATTERN  = re.compile(r'^CULL(\d+)_H\d*\.BMS$', re.IGNORECASE)
_A_PATTERN  = re.compile(r'^CULL(\d+)_A\.BMS$',    re.IGNORECASE)
# _A2 is the LM ambient LOD — imported as editable P objects for LM cells that have no _H
_A2_PATTERN = re.compile(r'^CULL(\d+)_A2\.BMS$',   re.IGNORECASE)

_LM_THRESHOLD = 200  # cell IDs below this are landmark cells


# ── BND helper ────────────────────────────────────────────────────────────────

def _read_bnd_material_indices(bnd_path: Path) -> List[int]:
    """Return material_index for each non-filler polygon in a BND file."""
    try:
        with open(bnd_path, "rb") as f:
            f.read(4)                               # magic "2DNB"
            f.read(12)                              # offset Vector3
            f.read(12)                              # x_dim, y_dim, z_dim
            f.read(12)                              # center Vector3
            f.read(8)                               # radius, radius_sqr
            f.read(12)                              # bb_min Vector3
            f.read(12)                              # bb_max Vector3
            num_verts, num_polys = read_unpack(f, '<2l')
            f.read(12)                              # num_hv1, num_hv2, num_edges
            f.read(8)                               # x_scale, z_scale
            f.read(12)                              # num_indices, height_scale, cache_size
            f.read(12 * num_verts)                  # vertex table
            result: List[int] = []
            for i in range(num_polys + 1):
                _cell_id, material_index = read_unpack(f, '<HB')
                f.read(73)                          # flags(1) vi(8) edges(48) normal(12) dist(4)
                if i > 0:
                    result.append(material_index)
        return result
    except Exception:
        return []


# ── Collection helpers ────────────────────────────────────────────────────────

def _ensure_collection(name: str) -> bpy.types.Collection:
    """Return the named collection, clearing its objects if it already exists."""
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


# ── BMS → polygon objects ─────────────────────────────────────────────────────

def _import_bms_surfaces(
    bms_file: Path, cell_id: int,
    bnd_material_indices: List[int],
    texture_folder: Path,
    collection: bpy.types.Collection,
    obj_prefix: str = "P",
) -> int:
    """
    Create one Blender mesh object per BMS surface.

    obj_prefix controls the object name: "P" for _H surfaces (exported by
    the standard Export Polygons operator), "PA" for _A surfaces (reference
    only until a dedicated _A export path exists).

    Custom properties set on each object:
      bms_uvs      – flat list [u0,v0, u1,v1, …] of raw BMS UVs (no v-flip),
                     used by _custom_tex_coords_literal for exact round-trip.
      bms_normals  – flat list of packed normal indices, one per face corner,
                     written as  normals=[…]  in save_mesh().
      material_index, cell_type, always_visible, sort_vertices – polygon metadata.

    Returns the number of polygon objects created.
    """
    from src.integrations.blender.modeling.meshes import read_bms, _build_material

    bms             = read_bms(bms_file)
    points          = bms["points"]
    tex_coords      = bms["tex_coords"]
    normal_indices  = bms["normal_indices"]
    vertex_indices  = bms["vertex_indices"]
    surface_indices = bms["surface_indices"]
    texture_indices = bms["texture_indices"]
    texture_names   = bms["texture_names"]
    num_surfaces    = bms["num_surfaces"]
    flags           = bms["flags"]
    has_uvs         = bool(flags & 1)
    has_normals     = bool(flags & 2)

    loaded = 0

    for surf_idx in range(num_surfaces):
        base       = surf_idx * 4
        side_count = 4 if surface_indices[base + 3] > 0 else 3
        adj_list   = surface_indices[base : base + side_count]
        pt_indices = [vertex_indices[adj] for adj in adj_list]

        if len(set(pt_indices)) < side_count:
            continue  # degenerate face — skip

        # ── Resolve texture name ──────────────────────────────────────────────
        tex_slot = texture_indices[surf_idx]
        if tex_slot == 0 or not texture_names:
            tex_name = texture_names[0] if texture_names else "ROAD"
        else:
            tex_name = texture_names[min(tex_slot - 1, len(texture_names) - 1)]

        # ── Build single-face bmesh ───────────────────────────────────────────
        me  = bpy.data.meshes.new(f"{obj_prefix}{cell_id}")
        bm  = bmesh.new()
        bm.from_mesh(me)
        uv_layer = bm.loops.layers.uv.new() if has_uvs else None

        # BMS game space (x, y, z) → Blender (x, -z, y)
        verts = []
        for pt_idx in pt_indices:
            px, py, pz = points[pt_idx]
            verts.append(bm.verts.new((px, -pz, py)))
        bm.verts.ensure_lookup_table()

        try:
            face = bm.faces.new(verts)
        except Exception:
            bm.free()
            bpy.data.meshes.remove(me)
            continue

        raw_uvs: List[float] = []
        raw_normals: List[int] = []
        if uv_layer is not None:
            for xx, loop in enumerate(face.loops):
                adj_idx = adj_list[xx]
                u, v    = tex_coords[adj_idx]
                loop[uv_layer].uv = (u, 1.0 - v)  # v-flip for Blender display
                raw_uvs.extend((u, v))
                if has_normals:
                    raw_normals.append(normal_indices[adj_idx])

        bm.normal_update()
        bm.to_mesh(me)
        bm.free()

        # ── Object ────────────────────────────────────────────────────────────
        obj = bpy.data.objects.new(f"{obj_prefix}{cell_id}", me)
        collection.objects.link(obj)

        # Material — must use ShaderNodeTexImage so extract_polygon_texture works
        mat = _build_material(tex_name, texture_folder)
        me.materials.append(mat)

        # Store raw BMS UV values for exact-round-trip export (game UVs are
        # world-space projected and don't fit the unit-quad pattern compute_uv
        # assumes, so exporting via compute_uv would produce wrong game UVs).
        # Also invert to tile/angle for editing; written via IDProperty bracket
        # syntax so update_uv_tiling() does NOT fire and overwrite the correct
        # Blender UV layer we already set in bmesh above.
        if raw_uvs:
            obj["bms_uvs"] = raw_uvs
            tile_x, tile_y, angle_degrees = _invert_compute_uv(raw_uvs)
            obj["tile_x"]        = tile_x
            obj["tile_y"]        = tile_y
            obj["angle_degrees"] = angle_degrees

        # Packed normal indices — export_formatted_polygons writes normals= arg
        if raw_normals:
            obj["bms_normals"] = raw_normals

        # Polygon metadata — defaults are fine for most city geometry
        mat_idx = bnd_material_indices[surf_idx] if surf_idx < len(bnd_material_indices) else 0
        obj["material_index"] = str(mat_idx)
        obj["cell_type"]      = "0"
        obj["always_visible"] = cell_id < _LM_THRESHOLD  # LM cells are always visible; city cells are portal-controlled
        obj["sort_vertices"]  = False

        loaded += 1

    return loaded


# ── Operators ─────────────────────────────────────────────────────────────────

class CITY_OT_ImportAsPolygons(bpy.types.Operator):
    """Import city CULL_H and CULL_A BMS meshes as editable P{N} polygon objects for round-trip export"""
    bl_idname = "city_loader.import_as_polygons"
    bl_label  = "Import as Polygons"

    def execute(self, context):
        scene  = context.scene
        folder = Path(scene.cl_city_folder)

        if not folder.is_dir():
            self.report({"ERROR"}, f"City folder not found: {folder}")
            return {"CANCELLED"}

        from src.constants.custom_props import custom_city_texture_folders
        meshes_root = folder / "MESHES"
        bounds_root = folder / "BOUNDS"
        base_tex    = (
            Path(scene.cl_texture_folder)
            if scene.cl_texture_folder
            else Folder.Resources.Editor.Textures
        )
        # Custom cities ship their own DDS — search the custom store too
        tex_folder  = [base_tex] + custom_city_texture_folders(folder)

        mesh_dirs = [d for d in meshes_root.iterdir() if d.is_dir()] if meshes_root.is_dir() else []
        if not mesh_dirs:
            self.report({"ERROR"}, f"No MESHES/ subfolders in {folder.name}")
            return {"CANCELLED"}

        col_h  = _ensure_collection(_COL_H)
        col_lm = _ensure_collection(_COL_LM)
        col_a  = _ensure_collection(_COL_A)
        total_h = total_lm = total_a = 0

        # Track which LM cell IDs already have a _H file so we don't
        # double-import the _A2 for those cells.
        lm_h_seen: set = set()

        # Two-pass: first collect _H files so we know which LM cells are covered.
        for mesh_dir in mesh_dirs:
            for bms_file in mesh_dir.glob("*.BMS"):
                m = _H_PATTERN.match(bms_file.name)
                if m:
                    cid = int(m.group(1))
                    if cid < _LM_THRESHOLD:
                        lm_h_seen.add(cid)

        for mesh_dir in mesh_dirs:
            for bms_file in sorted(mesh_dir.glob("*.BMS")):
                m_h  = _H_PATTERN.match(bms_file.name)
                m_a  = _A_PATTERN.match(bms_file.name)
                m_a2 = _A2_PATTERN.match(bms_file.name)

                if m_h:
                    cell_id = int(m_h.group(1))
                    is_lm   = cell_id < _LM_THRESHOLD
                    col        = col_lm if is_lm else col_h
                    obj_prefix = "P"
                    count_key  = "lm" if is_lm else "h"
                elif m_a:
                    cell_id    = int(m_a.group(1))
                    col        = col_a
                    obj_prefix = "PA"
                    count_key  = "a"
                elif m_a2:
                    cell_id = int(m_a2.group(1))
                    if cell_id >= _LM_THRESHOLD or cell_id in lm_h_seen:
                        continue  # city _A2 or LM cell already covered by _H
                    col        = col_lm
                    obj_prefix = "P"
                    count_key  = "lm"
                else:
                    continue

                bnd_path = None
                if bounds_root.is_dir():
                    candidates = list(bounds_root.rglob(f"BOUND{cell_id:02d}.BND"))
                    if candidates:
                        bnd_path = candidates[0]

                bnd_mats = _read_bnd_material_indices(bnd_path) if bnd_path else []

                try:
                    n = _import_bms_surfaces(bms_file, cell_id, bnd_mats, tex_folder, col, obj_prefix)
                    if   count_key == "h":  total_h  += n
                    elif count_key == "lm": total_lm += n
                    else:                   total_a  += n
                except Exception as exc:
                    self.report({"WARNING"}, f"[{bms_file.name}] {exc}")

        msg = f"Imported from {folder.name}: {total_h} city _H, {total_lm} landmark"
        if total_a:
            msg += f", {total_a} _A (reference)"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class CITY_OT_ClearImportedPolygons(bpy.types.Operator):
    """Remove all objects in the 'City Polygons' and 'City Polygons (A)' collections"""
    bl_idname = "city_loader.clear_imported_polygons"
    bl_label  = "Clear Imported Polygons"

    def execute(self, context):
        removed = 0
        for col_name in (_COL_H, _COL_LM, _COL_A):
            col = bpy.data.collections.get(col_name)
            if col:
                for obj in list(col.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed += 1
                bpy.data.collections.remove(col)
        if removed:
            self.report({"INFO"}, f"Removed {removed} polygon object(s)")
        else:
            self.report({"INFO"}, "No imported polygons to clear")
        return {"FINISHED"}


CITY_POLYGON_IMPORT_CLASSES = [
    CITY_OT_ImportAsPolygons,
    CITY_OT_ClearImportedPolygons,
]

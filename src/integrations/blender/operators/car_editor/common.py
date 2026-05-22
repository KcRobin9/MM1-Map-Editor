"""Car Editor — common module (split from the former car_editor.py monolith)."""
import bpy
import math
import bmesh
import shutil
import mathutils
from pathlib import Path
from typing import Optional

from src.constants.folder import Folder
from src.constants.file_formats import MeshFlags
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data
from src.integrations.blender.modeling.meshes import (
    _apply_materials_to_mesh, _to_blender_pos, build_blender_mesh, read_bms,
)

from src.integrations.blender.operators.car_editor.constants import _CAR_TAG, _TIMESTAMP_SUFFIX_RE


def _base_car_name(name: str) -> str:
    """Strip any trailing timestamp suffix so re-exports don't double-stamp the name."""
    return _TIMESTAMP_SUFFIX_RE.sub('', name)


def _tex_folder(scene) -> Path:
    """The editor texture folder for this scene — the user override if set, else
    the default resources/editor/TEXTURES."""
    return Path(scene.ce_texture_folder) if scene.ce_texture_folder else Folder.Resources.Editor.Textures


# ── Face texture update callback ──────────────────────────────────────────────

def _get_or_create_car_mat(mesh, tex_name: str, tex_folder: Path):
    """Return the slot index for tex_name on mesh, creating it if needed."""
    for i, mat in enumerate(mesh.materials):
        if mat and mat.name == tex_name:
            return i

    # Re-use an existing material with this name, or build a fresh textured one.
    if tex_name in bpy.data.materials:
        mat = bpy.data.materials[tex_name]
    else:
        mat = bpy.data.materials.new(name=tex_name)

        tex_path = tex_folder / f"{tex_name}.dds"
        if not tex_path.exists():
            tex_path = tex_folder / f"{tex_name}.DDS"

        if tex_path.exists():
            mat.use_nodes = True

            nodes = mat.node_tree.nodes
            for n in list(nodes):
                nodes.remove(n)

            bsdf     = nodes.new("ShaderNodeBsdfPrincipled")
            tex_node = nodes.new("ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(str(tex_path), check_existing=True)

            links = mat.node_tree.links
            links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

            out = nodes.new("ShaderNodeOutputMaterial")
            links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mesh.materials.append(mat)
    return len(mesh.materials) - 1


def _read_back_face_uv(scene, obj, face) -> None:
    """Read tile_x/tile_y/rotation from face UVs and write them to scene props."""
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        return
    loops = list(face.loops)
    if len(loops) < 3:
        return

    u0, v0 = loops[0][uv_layer].uv
    u1, v1 = loops[1][uv_layer].uv
    u2, v2 = loops[2][uv_layer].uv

    du  = u1 - u0   # cos(a) * tile_x
    du2 = u2 - u1   # -sin(a) * tile_x
    dv  = v1 - v0   # -sin(a) * tile_y
    dv2 = v2 - v1   # -cos(a) * tile_y

    tile_x = math.sqrt(du ** 2 + du2 ** 2)
    tile_y = math.sqrt(dv ** 2 + dv2 ** 2)
    angle  = math.degrees(math.atan2(-du2, du))

    # Suppress update callbacks while writing back
    scene.ce_uv_updating = True
    scene.ce_face_tile_x  = round(tile_x, 4)
    scene.ce_face_tile_y  = round(tile_y, 4)
    scene.ce_face_rotation = round(angle, 2)
    scene.ce_uv_updating = False


def _apply_face_uv(scene, context) -> None:
    """Apply ce_face_tile_x/y/rotation to selected faces on the active car part."""
    obj = context.active_object
    if obj is None or obj.type != "MESH" or obj.mode != "EDIT":
        return
    if not obj.get(_CAR_TAG):
        return
    tile_x = scene.ce_face_tile_x
    tile_y = scene.ce_face_tile_y
    angle  = math.radians(scene.ce_face_rotation)
    cx, cy = 0.5, 0.5

    def _r(bx, by):
        bx -= cx; by -= cy
        rx = bx * math.cos(angle) - by * math.sin(angle)
        ry = bx * math.sin(angle) + by * math.cos(angle)
        return ((rx + cx) * tile_x, 1.0 - (ry + cy) * tile_y)

    quad_uvs = [_r(x, y) for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]]
    tri_uvs  = [_r(x, y) for x, y in [(0, 0), (1, 0), (0.5, 1)]]

    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        return
    for face in bm.faces:
        if not face.select:
            continue
        loops = list(face.loops)
        uvs   = tri_uvs if len(loops) == 3 else quad_uvs
        for i, loop in enumerate(loops):
            loop[uv_layer].uv = uvs[i % len(uvs)]
    bmesh.update_edit_mesh(obj.data)


def update_ce_face_uv(self, context) -> None:
    if self.ce_uv_updating:
        return
    _apply_face_uv(self, context)


def update_ce_face_texture(self, context) -> None:
    """Assign the chosen texture to all selected faces on the active car part."""
    tex_name = self.ce_face_texture
    if not tex_name:
        return
    obj = context.active_object
    if obj is None or obj.type != "MESH" or obj.mode != "EDIT":
        return
    if not obj.get(_CAR_TAG):
        return
    tex_folder = _tex_folder(self)
    slot = _get_or_create_car_mat(obj.data, tex_name, tex_folder)
    bm = bmesh.from_edit_mesh(obj.data)
    changed = 0
    for face in bm.faces:
        if face.select:
            face.material_index = slot
            changed += 1
    bmesh.update_edit_mesh(obj.data)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_original_car(car_name: str) -> bool:
    """
    True when this car ships with the game (its complete originals — dash, TSH,
    textures, lights, collision — are already loaded from the base AR).

    For these cars we build a *minimal override* AR containing only the BMS
    meshes we edited, so the original TSH/dash/textures stay active and nothing
    wrongly defaults to the VPMUSTANG99 template.  resources/editor/MESHES/CARS
    is the editor's source of truth for which cars are original.
    """
    return (Folder.Resources.Editor.MeshesCars / car_name).is_dir()


def _copy_files_to_shop(src_dir: Path, dst_dir: Path, filenames, overwrite: bool = True) -> int:
    """Copy each of ``filenames`` from src_dir into dst_dir (created if needed),
    skipping any that don't exist in the source. With ``overwrite=False`` existing
    destination files are kept. Returns the number copied."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for fname in filenames:
        src = src_dir / fname
        dst = dst_dir / fname
        if not src.exists() or (dst.exists() and not overwrite):
            continue
        shutil.copy2(src, dst)
        copied += 1
    return copied


def _bms_extract_faces_by_texture(bms: dict, keep_names, max_yspan: float = None) -> dict:
    """
    Return a new BMS dict containing only the faces using the named textures.

    max_yspan (optional): drop faces whose vertical extent exceeds it — used to
    strip the thin connector face that links VPCOP's roof bar down to the
    windshield, so only the clean bar remains (and it drops onto the roof neatly).
    """
    keep = {t.upper() for t in keep_names}
    src_tex = bms["texture_names"]
    si, ti, vi = bms["surface_indices"], bms["texture_indices"], bms["vertex_indices"]
    tc, vc, ni = bms.get("tex_coords", []), bms.get("vert_colors", []), bms.get("normal_indices", [])
    pts = bms["points"]

    adj_remap, used_adjuncts, new_surfaces = {}, [], []
    for s in range(bms["num_surfaces"]):
        tex_idx = ti[s]
        tname = src_tex[tex_idx - 1] if 1 <= tex_idx <= len(src_tex) else None
        if not tname or tname.upper() not in keep:
            continue
        base = s * 4
        # 4th slot == 0 marks a triangle; only the first `side` slots are real.
        side = 4 if si[base + 3] > 0 else 3
        real_adj = si[base:base + side]
        if max_yspan is not None:
            ys = [pts[vi[a]][1] for a in real_adj]
            if max(ys) - min(ys) > max_yspan:
                continue
        nq = []
        for a in real_adj:
            if a not in adj_remap:
                adj_remap[a] = len(used_adjuncts)
                used_adjuncts.append(a)
            nq.append(adj_remap[a])
        if side == 3:
            nq.append(0)  # restore triangle marker
        new_surfaces.append((nq, tex_idx, tname))

    new_tex, tex_remap = [], {}
    for _, tex_idx, tname in new_surfaces:
        if tex_idx not in tex_remap:
            new_tex.append(tname)
            tex_remap[tex_idx] = len(new_tex)

    point_remap, new_points = {}, []
    new_vi, new_tc, new_vc, new_ni = [], [], [], []
    for old_a in used_adjuncts:
        p = vi[old_a]
        if p not in point_remap:
            point_remap[p] = len(new_points)
            new_points.append(bms["points"][p])
        new_vi.append(point_remap[p])
        if tc: new_tc.append(tc[old_a])
        if vc: new_vc.append(vc[old_a])
        if ni: new_ni.append(ni[old_a])

    new_si, new_ti = [], []
    for quad, tex_idx, _ in new_surfaces:
        new_si += quad
        new_ti.append(tex_remap[tex_idx])

    return {
        "points": new_points, "mesh_offset": (0.0, 0.0, 0.0), "radius": bms["radius"],
        "num_adjuncts": len(new_vi), "num_surfaces": len(new_surfaces),
        "tex_coords": new_tc, "vert_colors": new_vc, "normal_indices": new_ni,
        "vertex_indices": new_vi, "texture_indices": new_ti,
        "surface_indices": new_si, "texture_names": new_tex,
        "flags": bms["flags"] & ~MeshFlags.PLANES,
    }


def _bms_merge_part_into_body(body: dict, part: dict) -> dict:
    """Append `part` geometry into `body` (part shifted by its mesh_offset)."""
    ox, oy, oz = part["mesh_offset"]
    shifted = [(x + ox, y + oy, z + oz) for (x, y, z) in part["points"]]
    base_np, base_na, bf, pna = len(body["points"]), body["num_adjuncts"], body["flags"], part["num_adjuncts"]

    part_tc = part.get("tex_coords", [])
    part_vc = part.get("vert_colors", [])
    part_ni = part.get("normal_indices", [])
    part_tc = (part_tc if len(part_tc) == pna else [(0.0, 0.0)] * pna) if (bf & MeshFlags.TEXCOORDS) else []
    part_vc = (part_vc if len(part_vc) == pna else [(1.0, 1.0, 1.0, 1.0)] * pna) if (bf & MeshFlags.COLORS) else []
    part_ni = (part_ni if len(part_ni) == pna else [0] * pna) if (bf & MeshFlags.NORMALS) else []

    merged_tex = list(body["texture_names"])
    upper = [t.upper() for t in merged_tex]
    tex_map = {}
    for i, t in enumerate(part["texture_names"]):
        if t.upper() in upper:
            tex_map[i + 1] = upper.index(t.upper()) + 1
        else:
            merged_tex.append(t); upper.append(t.upper())
            tex_map[i + 1] = len(merged_tex)

    # Offset the part's adjunct indices, but keep triangle markers intact: a 4th
    # slot (i%4==3) of 0 means "triangle", not adjunct 0, so it must stay 0.
    part_si = [
        0 if (i % 4 == 3 and s == 0) else s + base_na
        for i, s in enumerate(part["surface_indices"])
    ]

    out = dict(body)
    out["points"] = body["points"] + shifted
    out["texture_names"] = merged_tex
    out["vertex_indices"] = body["vertex_indices"] + [v + base_np for v in part["vertex_indices"]]
    out["tex_coords"] = body.get("tex_coords", []) + part_tc
    out["vert_colors"] = body.get("vert_colors", []) + part_vc
    out["normal_indices"] = body.get("normal_indices", []) + part_ni
    out["texture_indices"] = body["texture_indices"] + [tex_map.get(t, t) for t in part["texture_indices"]]
    out["surface_indices"] = body["surface_indices"] + part_si
    out["num_adjuncts"] = base_na + pna
    out["num_surfaces"] = body["num_surfaces"] + part["num_surfaces"]
    out["flags"] = bf & ~MeshFlags.PLANES
    return out


def _build_menu_mesh_bms(body_obj, car_objects, housing_objs) -> dict:
    """Build the combined H.BMS that the vehicle picker renders.

    Stock cars ship H.BMS as the WHOLE car (body + every wheel + fender) baked
    into one static mesh — the selection menu has no physics sim to place the
    separate wheel meshes, so a body-only H.BMS shows a wheel-less preview.

    Parts are merged with the same body=local / part=baked convention proven by
    the siren-housing merge: wheels/fenders are parented to the body, so their
    baked mesh_offset is body-relative and lands them at the correct hub.  The
    offset is zeroed to match how the game stores H.BMS (offset 0, no OFFSET flag)."""
    data = mesh_to_bms_data(body_obj, bake_location=False)

    for h in housing_objs:
        data = _bms_merge_part_into_body(data, mesh_to_bms_data(h, bake_location=True))

    for obj in car_objects:
        tag = obj.get(_CAR_TAG, "")
        if tag.startswith("wheel_") or tag.startswith("fender_"):
            data = _bms_merge_part_into_body(data, mesh_to_bms_data(obj, bake_location=True))

    data["mesh_offset"] = (0.0, 0.0, 0.0)
    return data


def is_car_obj(obj) -> bool:
    return obj is not None and obj.get(_CAR_TAG) is not None


def get_car_objects():
    return [o for o in bpy.data.objects if is_car_obj(o)]


def get_car_body() -> Optional[bpy.types.Object]:
    for o in get_car_objects():
        if o.get(_CAR_TAG) == "body":
            return o
    return None


# ── Trailer part helpers ──────────────────────────────────────────────────────
# Trailer parts are tagged so they can be edited like car parts but routed to the
# {NAME}_TRAILER sub-car on export. Like wheels, body + TWHL are centered+offset,
# so all trailer parts export via bake_location=True relative to the trailer root.

def _is_trailer_part(tag: str) -> bool:
    return tag in ("trailer_root", "trailer_body") or tag.startswith("trailer_wheel_")


def _get_trailer_root() -> Optional[bpy.types.Object]:
    for o in get_car_objects():
        if o.get(_CAR_TAG) == "trailer_root":
            return o
    return None


def _get_trailer_parts() -> list:
    """Trailer mesh parts (body + wheels), excluding the empty root."""
    return [o for o in get_car_objects()
            if o.get(_CAR_TAG) in ("trailer_body",) or o.get(_CAR_TAG, "").startswith("trailer_wheel_")]


def _has_custom_trailer() -> bool:
    return any(o.get(_CAR_TAG) == "trailer_body" for o in get_car_objects())


def _clear_trailer_objects() -> None:
    """Remove the trailer root + all trailer parts from the scene."""
    for obj in [o for o in get_car_objects() if _is_trailer_part(o.get(_CAR_TAG, ""))]:
        bpy.data.objects.remove(obj, do_unlink=True)


def _bms_to_bl_offset(mesh: bpy.types.Mesh):
    """Convert game-space mesh_offset stored on mesh to Blender location."""
    ox, oy, oz = mesh.get("mesh_offset", [0.0, 0.0, 0.0])
    return (-ox, oz, oy)


def _get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _clear_car_objects() -> None:
    """Remove all objects tagged as car editor parts from the scene."""
    to_remove = get_car_objects()
    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)


def _load_bms(bms_file: Path, name: str, tex_folder: Optional[Path]) -> Optional[bpy.types.Mesh]:
    try:
        bms_data = read_bms(bms_file)
        mesh     = build_blender_mesh(name, bms_data)
        if tex_folder and bms_data["texture_names"]:
            _apply_materials_to_mesh(mesh, bms_data["texture_names"], tex_folder)
        mesh["bms_source_file"] = str(bms_file)
        return mesh
    except Exception as exc:
        print(f"[Car Editor] Could not load {bms_file.name}: {exc}")
        return None


def _add_child_obj(mesh: bpy.types.Mesh, name: str, part_tag: str,
                   parent_obj: bpy.types.Object, col: bpy.types.Collection) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.parent = parent_obj
    obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    obj.location = _bms_to_bl_offset(mesh)
    obj[_CAR_TAG] = part_tag
    return obj


# ── Damage toggle helpers ─────────────────────────────────────────────────────

def _build_damage_remap(mesh) -> dict:
    """Return {normal_slot_idx: dmg_slot_idx} for materials that have a _DMG counterpart."""
    name_to_idx = {mat.name: i for i, mat in enumerate(mesh.materials) if mat}
    return {
        i: name_to_idx[mat.name + "_DMG"]
        for i, mat in enumerate(mesh.materials)
        if mat and not mat.name.endswith("_DMG") and (mat.name + "_DMG") in name_to_idx
    }


# ── Helpers: build a Blender mesh from raw (game-space) verts/faces ──────────

def _build_mesh_from_geometry(
    name: str,
    verts_game,
    quads,
    tris,
    texture_names,
    mesh_offset_game,
    source_filename: str = "",
) -> bpy.types.Mesh:
    """
    Create a Blender Mesh from primitive geometry (game-space verts + face lists).

    Used by the template generator and mirror helper. Sets the same custom
    properties the BMS writer/reader use, so the result round-trips through
    Export → Reload identically to a loaded BMS.
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new()

    for pos in verts_game:
        bm.verts.new(_to_blender_pos(pos))
    bm.verts.ensure_lookup_table()

    _quad_uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    _tri_uvs  = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]

    def _add_face(idx_tuple, base_uvs):
        try:
            face = bm.faces.new([bm.verts[i] for i in idx_tuple])
        except ValueError:
            return  # duplicate face — skip
        face.material_index = 0
        face.smooth = True
        for i, loop in enumerate(face.loops):
            loop[uv_layer].uv = base_uvs[i]

    for q in quads:
        _add_face(q, _quad_uvs)
    for t in tris:
        _add_face(t, _tri_uvs)

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()

    for tname in texture_names:
        mat = bpy.data.materials.get(tname) or bpy.data.materials.new(tname)
        me.materials.append(mat)

    me["bms_flags"]       = MeshFlags.TEXCOORDS
    me["texture_names"]   = list(texture_names)
    me["mesh_offset"]     = list(mesh_offset_game)
    me["bms_source_file"] = source_filename
    return me

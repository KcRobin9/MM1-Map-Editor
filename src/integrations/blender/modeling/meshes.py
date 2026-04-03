import struct
import bmesh
import bpy
from pathlib import Path
from typing import List, Optional

from src.constants.file_formats import FileType


# ── BMS file reader ───────────────────────────────────────────────────────────

def read_bms(bms_file: Path) -> dict:
    """
    Parse a BMS (Binary Mesh Set) file.

    Field order and flag handling mirror the reference Angel Studios Blender
    Addon (import_bms.py by Dummiesman), which is the authoritative source
    for this format.

    Returned keys:
        points          – List[tuple(x,y,z)]  raw vertex positions (game space)
        mesh_offset     – tuple(x,y,z)        local origin offset stored in file
        tex_coords      – List[tuple(u,v)]    per-adjunct UVs (empty if no flag)
        normal_indices  – List[int]           per-adjunct packed normals (empty if no flag)
        vertex_indices  – List[int]           adjunct → point index mapping
        texture_indices – List[int]           surface → texture/material index
        surface_indices – List[int]           flat adjunct-index array (4 per surface)
        texture_names   – List[str]           DDS texture names (no extension)
        num_adjuncts    – int
        num_surfaces    – int
        flags           – int
    """
    with open(bms_file, "rb") as f:
        magic = struct.unpack("<L", f.read(4))[0]
        if magic != 0x4D534833:
            raise ValueError(f"Not a BMS file: {bms_file}")

        mesh_offset = struct.unpack("<fff", f.read(12))

        num_points, num_adjuncts, num_surfaces, num_indices = struct.unpack("<LLLL", f.read(16))

        f.seek(12, 1)  # skip radius (3 × float)

        num_textures = struct.unpack("<B", f.read(1))[0]
        flags        = struct.unpack("<B", f.read(1))[0]

        f.seek(6, 1)   # skip 2-byte padding + 4-byte cache_size

        # ── Texture names (32-byte name + 16-byte padding each) ──────────────
        texture_names: List[str] = []
        for _ in range(num_textures):
            raw = bytearray(f.read(32))
            null_pos = raw.find(b"\x00")
            name = raw[:null_pos].decode("ascii") if null_pos != -1 else raw.decode("ascii")
            texture_names.append(name)
            f.seek(16, 1)

        # ── Vertex positions ──────────────────────────────────────────────────
        points = [struct.unpack("<fff", f.read(12)) for _ in range(num_points)]

        # Large meshes have 8 extra sentinel bounding-box vertices appended
        if num_points >= 16:
            f.seek(12 * 8, 1)

        # ── Per-adjunct data (all conditional on flags) ───────────────────────
        normal_indices: List[int] = []
        if flags & 2:  # NORMALS
            normal_indices = list(struct.unpack(f"{num_adjuncts}B", f.read(num_adjuncts)))

        tex_coords: List[tuple] = []
        if flags & 1:  # TEXCOORDS
            tex_coords = [struct.unpack("<ff", f.read(8)) for _ in range(num_adjuncts)]

        # COLORS — 4 bytes per adjunct (BGRA uint8).  Read instead of skip so
        # build_blender_mesh() can write a vertex-color layer.  This is the
        # only way tire faces on wheels show as black rubber rather than
        # showing the metallic rim texture (the game multiplies tex × vcolor).
        vert_colors: List[tuple] = []
        if flags & 4:
            for _ in range(num_adjuncts):
                b, g, r, a = struct.unpack("4B", f.read(4))
                vert_colors.append((r / 255.0, g / 255.0, b / 255.0, a / 255.0))

        # ── Adjunct → point mapping (always present) ─────────────────────────
        vertex_indices = list(struct.unpack(f"{num_adjuncts}H", f.read(num_adjuncts * 2)))

        # ── Planes (conditional) ─────────────────────────────────────────────
        if flags & 16:  # PLANES — 4 floats per surface, skip
            f.seek(16 * num_surfaces, 1)

        # ── Per-surface texture/material index ────────────────────────────────
        texture_indices = list(struct.unpack(f"<{num_surfaces}B", f.read(num_surfaces)))

        # ── Flat adjunct-index array (4 slots per surface; 4th is 0 for tris) ─
        surface_indices = list(struct.unpack(f"{num_indices}H", f.read(num_indices * 2)))

    return {
        "points":          points,
        "mesh_offset":     mesh_offset,
        "num_adjuncts":    num_adjuncts,
        "num_surfaces":    num_surfaces,
        "tex_coords":      tex_coords,
        "vert_colors":     vert_colors,
        "normal_indices":  normal_indices,
        "vertex_indices":  vertex_indices,
        "texture_indices": texture_indices,
        "surface_indices": surface_indices,
        "texture_names":   texture_names,
        "flags":           flags,
    }


# ── Blender mesh builder ──────────────────────────────────────────────────────

def _vert_key(pos: tuple, normal: Optional[int]) -> str:
    """Deduplication key: same position + same normal = same Blender vertex."""
    return str(pos) if normal is None else f"{pos}|{normal}"


def _to_blender_pos(pos: tuple) -> tuple:
    """
    Convert a game-space (x, y, z) position to Blender space.
    Matches the Angel Studios addon: (-x, z, y).
    """
    return (-pos[0], pos[2], pos[1])


def _to_blender_uv(uv: tuple) -> tuple:
    """Flip V axis: Blender's UV origin is bottom-left, game's is top-left."""
    return (uv[0], 1.0 - uv[1])


def build_blender_mesh(prop_name: str, bms_data: dict) -> bpy.types.Mesh:
    """
    Convert parsed BMS data into a Blender Mesh data-block using bmesh.

    Closely follows import_bms_object() from the Angel Studios Blender Addon
    (Dummiesman).  Key additions over the previous version:

    • face.material_index is set per face from texture_indices[], mapping each
      polygon to the correct material slot (matching the reference formula:
      slot = 0 if texture_index == 0 else texture_index - 1).
    • One material slot placeholder is added to the mesh per texture name so
      that apply_all_prop_materials() can fill them in order later.
    """
    points          = bms_data["points"]
    tex_coords      = bms_data["tex_coords"]
    vert_colors     = bms_data.get("vert_colors", [])
    normal_indices  = bms_data["normal_indices"]
    vertex_indices  = bms_data["vertex_indices"]    # adjunct → point index
    surface_indices = bms_data["surface_indices"]   # flat; 4 slots per surface
    texture_indices = bms_data["texture_indices"]   # surface → texture slot (1-based)
    num_surfaces    = bms_data["num_surfaces"]
    flags           = bms_data["flags"]
    texture_names   = bms_data.get("texture_names", [])

    me = bpy.data.meshes.new(prop_name)
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer    = bm.loops.layers.uv.new()
    color_layer = bm.loops.layers.color.new("Col") if vert_colors else None

    # ── Build deduplicated vertex list ────────────────────────────────────────
    vertex_map: dict = {}
    bm_verts: list   = []

    for adj_idx in range(bms_data["num_adjuncts"]):
        pos    = points[vertex_indices[adj_idx]]
        normal = normal_indices[adj_idx] if (flags & 2) else None
        key    = _vert_key(pos, normal)

        if key not in vertex_map:
            vertex_map[key] = len(bm_verts)
            bm_verts.append(bm.verts.new(_to_blender_pos(pos)))

    bm.verts.ensure_lookup_table()

    # ── Build faces ───────────────────────────────────────────────────────────
    for surf_idx in range(num_surfaces):
        base       = surf_idx * 4
        side_count = 4 if surface_indices[base + 3] > 0 else 3
        adj_list   = surface_indices[base : base + side_count]

        face_verts = []
        for adj_idx in adj_list:
            pos    = points[vertex_indices[adj_idx]]
            normal = normal_indices[adj_idx] if (flags & 2) else None
            key    = _vert_key(pos, normal)
            face_verts.append(bm_verts[vertex_map[key]])

        try:
            face = bm.faces.new(face_verts)

            for xx in range(side_count):
                loop = face.loops[xx]
                adj_idx = adj_list[xx]
                if flags & 1:
                    loop[uv_layer].uv = _to_blender_uv(tex_coords[adj_idx])
                if color_layer is not None:
                    loop[color_layer] = vert_colors[adj_idx]

            tex_idx = texture_indices[surf_idx]
            face.material_index = 0 if tex_idx == 0 else tex_idx - 1

            face.smooth = True
        except Exception:
            pass  # skip degenerate / duplicate-vertex faces

    for _ in texture_names:
        me.materials.append(None)

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()

    # Store metadata so it survives the .blend round-trip and is available
    # to place_props_in_scene when creating per-instance objects.
    me["texture_names"] = texture_names
    me["mesh_offset"]   = list(bms_data.get("mesh_offset", (0.0, 0.0, 0.0)))

    return me


def _build_material(texture_name: str, texture_folder: Path):
    """
    Return a Principled BSDF material for texture_name.

    If a material with this name already exists in bpy.data (e.g. from a
    previous script run), it is rebuilt from scratch so stale/empty materials
    from earlier runs never silently persist.
    """
    texture_path = texture_folder / f"{texture_name}{FileType.DIRECTDRAW_SURFACE}"

    if texture_name in bpy.data.materials:
        mat = bpy.data.materials[texture_name]
        # For FXLT textures the node graph must be emission-based; if an older
        # run stored a Principled version, remove it so it gets rebuilt below.
        if texture_name.upper().startswith("FXLT"):
            has_emission = any(n.type == "EMISSION" for n in mat.node_tree.nodes)
            if not has_emission:
                bpy.data.materials.remove(mat)
                # fall through to create a fresh emission material
            else:
                return mat
        else:
            # Re-use but ensure the image node points at the correct DDS file
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        if texture_path.exists():
                            node.image = bpy.data.images.load(str(texture_path), check_existing=True)
                        break
            return mat

    # Light / FX textures use additive transparent emission in the game.
    # Use a dedicated node setup for them instead of Principled BSDF.
    if texture_name.upper().startswith("FXLT"):
        return _build_emission_material(texture_name, texture_path)

    mat = bpy.data.materials.new(name=texture_name)
    mat.use_nodes            = True
    mat.use_backface_culling = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    output   = nodes.new(type="ShaderNodeOutputMaterial")
    diffuse  = nodes.new(type="ShaderNodeBsdfPrincipled")
    tex_node = nodes.new(type="ShaderNodeTexImage")

    if texture_path.exists():
        tex_node.image = bpy.data.images.load(str(texture_path), check_existing=True)

    links = mat.node_tree.links
    links.new(tex_node.outputs["Color"], diffuse.inputs["Base Color"])
    links.new(diffuse.outputs["BSDF"],   output.inputs["Surface"])

    return mat


def _build_emission_material(texture_name: str, texture_path: Path):
    """
    Transparent additive-style emission material for headlight / FX meshes.

    The texture alpha drives the mix between fully transparent and a soft
    coloured emission.  This avoids the harsh solid-white blob appearance
    that a standard Principled BSDF gives for FXLTGLOW / FXLTCONE textures.
    """
    mat = bpy.data.materials.new(name=texture_name)
    mat.use_nodes     = True
    mat.blend_method  = "BLEND"   # alpha transparency

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    output    = nodes.new(type="ShaderNodeOutputMaterial")
    emit      = nodes.new(type="ShaderNodeEmission")
    transp    = nodes.new(type="ShaderNodeBsdfTransparent")
    mix       = nodes.new(type="ShaderNodeMixShader")
    tex_node  = nodes.new(type="ShaderNodeTexImage")
    gamma     = nodes.new(type="ShaderNodeGamma")      # soften harsh brightness

    emit.inputs["Strength"].default_value = 1.5        # gentle glow strength
    gamma.inputs["Gamma"].default_value   = 2.2        # darken mid-tones

    if texture_path.exists():
        tex_node.image = bpy.data.images.load(str(texture_path), check_existing=True)

    mix.inputs["Fac"].default_value = 0.5   # fixed: 50% transparent, 50% emission

    links = mat.node_tree.links
    links.new(tex_node.outputs["Color"], gamma.inputs["Color"])
    links.new(gamma.outputs["Color"],    emit.inputs["Color"])
    links.new(transp.outputs["BSDF"],    mix.inputs[1])
    links.new(emit.outputs["Emission"],  mix.inputs[2])
    links.new(mix.outputs["Shader"],     output.inputs["Surface"])

    return mat


def _apply_materials_to_mesh(
    mesh: bpy.types.Mesh,
    texture_names: List[str],
    texture_folder: Path,
) -> None:
    """
    Fill the pre-created None material slots in mesh with real materials.

    build_blender_mesh() adds len(texture_names) None slots before calling
    bm.to_mesh() so that face.material_index values are preserved.  This
    function replaces each slot in-place — indices must not change after
    bm.to_mesh().
    """
    while len(mesh.materials) < len(texture_names):
        mesh.materials.append(None)
    for i, name in enumerate(texture_names):
        mesh.materials[i] = _build_material(name, texture_folder)


def apply_all_prop_materials(
    obj: bpy.types.Object,
    texture_names: List[str],
    texture_folder: Path,
) -> None:
    """Kept for call sites outside place_props_in_scene."""
    _apply_materials_to_mesh(obj.data, texture_names, texture_folder)


# Keep the old single-texture name available so call sites that haven't been
# updated yet still work (proxies to slot 0 only).
def apply_prop_material(
    obj: bpy.types.Object,
    texture_name: str,
    texture_folder: Path,
) -> None:
    apply_all_prop_materials(obj, [texture_name], texture_folder)


# ── Asset builder ─────────────────────────────────────────────────────────────

def build_prop_blend(
    prop_name: str,
    bms_folder: Path,
    output_folder: Path,
    texture_folder: Optional[Path] = None,
) -> Optional[bpy.types.Mesh]:
    """
    Read a BMS file, create a Blender mesh, save a standalone .blend asset,
    and return the Mesh data-block.  Returns None when the BMS file is absent.
    """
    bms_file = bms_folder / f"{prop_name}{FileType.MESH}"
    if not bms_file.exists():
        print(f"BMS not found, skipping prop asset: {bms_file}")
        return None

    bms_data = read_bms(bms_file)
    mesh     = build_blender_mesh(prop_name, bms_data)

    temp_obj = bpy.data.objects.new(prop_name, mesh)
    # Apply the mesh's local origin offset stored in the BMS header
    ox, oy, oz = bms_data["mesh_offset"]
    temp_obj.location = _to_blender_pos((ox, oy, oz))

    bpy.context.collection.objects.link(temp_obj)

    if texture_folder and bms_data["texture_names"]:
        apply_all_prop_materials(temp_obj, bms_data["texture_names"], texture_folder)

    output_folder.mkdir(parents=True, exist_ok=True)
    blend_path = output_folder / f"{prop_name}.blend"
    bpy.data.libraries.write(str(blend_path), {temp_obj}, fake_user=False, compress=False)

    bpy.context.collection.objects.unlink(temp_obj)
    bpy.data.objects.remove(temp_obj, do_unlink=False)

    print(f"Saved prop asset: {blend_path.name}")
    return mesh


def build_all_prop_blends(
    prop_names: List[str],
    bms_folder: Path,
    output_folder: Path,
    texture_folder: Optional[Path] = None,
    rebuild: bool = False,
) -> None:
    """Build .blend assets for every unique prop name in the list."""
    for prop_name in prop_names:
        blend_path = output_folder / f"{prop_name}.blend"
        if not rebuild and blend_path.exists():
            continue
        build_prop_blend(prop_name, bms_folder, output_folder, texture_folder)

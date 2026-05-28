"""
Parsers and Blender builders for MM1 pedestrian characters.

File formats handled:
  SKEL  — text, bone hierarchy with parent-relative offsets
  ANIM  — binary LE, XZY Euler rotations per bone per frame
  MOD   — text, skinned mesh with named materials and bone-vertex weights
  VAR   — binary LE, 6 clothing color palette variants (RGBA bytes, 0-255)
  CSV   — text, animation state list for a character (state name, anim file, ...)

Coordinate system:
  Game uses Y-up;  Blender uses Z-up.
  Conversion:  _g2b(x, y, z) = (x, z, y)   (swap Y↔Z, no negation)
  Inverse:     _bl2g(bx, by, bz) = (bx, bz, by)
"""
import io
import bpy
import mathutils

from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from src.io.binary import pack_bytes, read_unpack


# ── Color space helpers ───────────────────────────────────────────────────────
# MOD diffuse values and VAR bytes are sRGB (gamma-encoded, 0-255 or 0.0-1.0).
# Blender's BSDF Base Color input is linear light space.
# Always convert at the boundary so what you see in Blender matches the game.
#
# TODO: Colors still not matching game exactly after sRGB conversion.
# Blender renders correctly, but the game may apply additional gamma/lighting on
# the raw diffuse. Investigate: compare a known stock color (e.g. BUSMAN variant
# 0 jacket #6F90AF) in-game vs Blender to measure the actual offset, and check
# whether the game treats MOD diffuse as sRGB or linear internally.
def _srgb_to_linear(c: float) -> float:
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _bytes_to_linear(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """sRGB byte triplet (0-255) → Blender linear floats."""
    return (_srgb_to_linear(r / 255), _srgb_to_linear(g / 255), _srgb_to_linear(b / 255))


def _linear_to_bytes(r: float, g: float, b: float) -> Tuple[int, int, int]:
    """Blender linear floats → sRGB byte triplet (0-255, clamped)."""
    def _cvt(c: float) -> int:
        return max(0, min(255, int(_linear_to_srgb(c) * 255 + 0.5)))
    return (_cvt(r), _cvt(g), _cvt(b))


# ── Coordinate helpers ────────────────────────────────────────────────────────
def _g2b(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Game Y-up → Blender Z-up: swap Y and Z."""
    return (x, z, y)


def _bl2g(bx: float, by: float, bz: float) -> Tuple[float, float, float]:
    """Blender Z-up → game Y-up: swap Y and Z."""
    return (bx, bz, by)


def _game_euler_xzy_to_blender_quat(ex: float, ey: float, ez: float) -> mathutils.Quaternion:
    """Convert a game XZY Euler (radians) to a Blender quaternion."""
    B      = mathutils.Matrix([[1, 0, 0], [0, 0, 1], [0, 1, 0]])
    R_game = mathutils.Matrix.Rotation(ey, 3, 'Y') @ mathutils.Matrix.Rotation(ez, 3, 'Z') @ mathutils.Matrix.Rotation(ex, 3, 'X')
    return (B @ R_game @ B).to_4x4().to_quaternion()


def _blender_quat_to_game_euler_xzy(quat: mathutils.Quaternion) -> Tuple[float, float, float]:
    """Convert a Blender quaternion to a game XZY Euler (radians)."""
    B     = mathutils.Matrix([[1, 0, 0], [0, 0, 1], [0, 1, 0]])
    euler = (B @ quat.to_matrix() @ B).to_euler('XZY')
    return euler.x, euler.y, euler.z


# ── SKEL parser ───────────────────────────────────────────────────────────────
def parse_skel(path: Path) -> dict:
    """Parse a SKEL text file into a nested bone tree.

    Returns ``{"num_bones": int, "root": bone_node}`` where each bone_node is
    ``{"name": str, "offset": (x, y, z), "children": [...]}``.
    Offsets are parent-relative in game Y-up space.
    """
    tokens = path.read_text().split()
    pos    = 0

    def consume() -> str:
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t

    def expect(val: str) -> None:
        got = consume()
        if got != val:
            raise ValueError(f"SKEL parse error: expected '{val}', got '{got}'")

    def parse_bone() -> dict:
        expect("bone")
        name = consume()
        expect("{")
        expect("offset")
        ox, oy, oz = float(consume()), float(consume()), float(consume())
        children = []

        while pos < len(tokens) and tokens[pos] == "bone":
            children.append(parse_bone())

        expect("}")
        return {"name": name, "offset": (ox, oy, oz), "children": children}

    expect("NumBones")
    num_bones = int(consume())
    root      = parse_bone()
    return {"num_bones": num_bones, "root": root}


# ── ANIM parser / writer ──────────────────────────────────────────────────────
def parse_anim(path: Path) -> dict:
    """Parse a binary ANIM file.

    Returns ``{"frame_count": int, "num_channels": int, "frames": list}``
    where each frame is a list of (x, y, z) tuples — channel 0 is the root
    world position, channels 1..N are per-bone XZY Euler rotations in DFS order.
    """
    buf               = io.BytesIO(path.read_bytes())
    frame_count,      = read_unpack(buf, "<i")
    num_channels,     = read_unpack(buf, "<i")
    num_channels     += 1  # stored as N-1

    frames = []
    for _ in range(frame_count):
        frame = [read_unpack(buf, "<fff") for _ in range(num_channels)]
        frames.append(frame)

    return {"frame_count": frame_count, "num_channels": num_channels, "frames": frames}


def _pack_anim(frame_count: int, num_channels: int, frames: list) -> bytes:
    out = pack_bytes("<ii", frame_count, num_channels - 1)
    for frame in frames:
        for ch in frame:
            out += pack_bytes("<fff", *ch)
    return out


# ── MOD parser ────────────────────────────────────────────────────────────────
def parse_mod(path: Path) -> dict:
    """Parse a MOD text file into mesh data.

    Returns a dict with keys: verts, normals, colors, uvs, materials,
    adjuncts, tris, mtxv, mtxn.  Diffuse/ambient/specular values are raw
    sRGB floats (0.0-1.0) as written in the file — convert to linear before
    passing to Blender shaders.
    """
    verts, normals, colors, uvs         = [], [], [], []
    materials, adjuncts, tris           = [], [], []
    mtxv: List[int]                     = []
    mtxn: List[int]                     = []
    cur_mat: Optional[dict]             = None

    for raw_line in path.read_text().splitlines():
        line  = raw_line.strip()
        if not line or line.startswith("version"):
            continue
        parts = line.split()
        tag   = parts[0]

        if tag == "v":
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif tag == "n":
            normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif tag == "c":
            colors.append((float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])))
        elif tag == "t1":
            uvs.append((float(parts[1]), float(parts[2])))
        elif tag == "mtl":
            cur_mat = {
                "name":     parts[1].rstrip("{").strip(),
                "ambient":  (1.0, 1.0, 1.0),
                "diffuse":  (1.0, 1.0, 1.0),
                "specular": (1.0, 1.0, 1.0),
                "texture1": None,
            }
            materials.append(cur_mat)
        elif tag == "ambient:" and cur_mat:
            cur_mat["ambient"] = (float(parts[1]), float(parts[2]), float(parts[3]))
        elif tag == "diffuse:" and cur_mat:
            cur_mat["diffuse"] = (float(parts[1]), float(parts[2]), float(parts[3]))
        elif tag == "specular:" and cur_mat:
            cur_mat["specular"] = (float(parts[1]), float(parts[2]), float(parts[3]))
        elif tag == "texture1:" and cur_mat:
            cur_mat["texture1"] = None if parts[1] == "none" else parts[1]
        elif tag == "adj":
            adjuncts.append({
                "vi": int(parts[1]), "ni": int(parts[2]), "ci": int(parts[3]),
                "t1i": int(parts[4]), "t2i": int(parts[5]), "mat": int(parts[6]),
            })
        elif tag == "tri":
            tris.append((int(parts[1]), int(parts[2]), int(parts[3])))
        elif tag == "mtxv":
            mtxv = [int(x) for x in parts[1:]]
        elif tag == "mtxn":
            mtxn = [int(x) for x in parts[1:]]

    return {
        "verts": verts, "normals": normals, "colors": colors, "uvs": uvs,
        "materials": materials, "adjuncts": adjuncts, "tris": tris,
        "mtxv": mtxv, "mtxn": mtxn,
    }


# ── Bone hierarchy helpers ────────────────────────────────────────────────────
def dfs_bone_order(skel_data: dict) -> List[dict]:
    """Return a flat DFS list of bone dicts.

    Each entry gains two extra keys:
      ``unique_name`` — deduplicated bone name (e.g. ``spine``, ``spine.001``)
      ``world_pos``   — cumulative world position in game Y-up space
    """
    result:     List[dict] = []
    seen_names: Dict[str, int] = {}

    def _visit(bone: dict, parent_world: Tuple[float, float, float]) -> None:
        ox, oy, oz = bone["offset"]
        px, py, pz = parent_world
        world      = (px + ox, py + oy, pz + oz)

        raw   = bone["name"]
        count = seen_names.get(raw, 0)
        seen_names[raw] = count + 1
        unique = raw if count == 0 else f"{raw}.{count:03d}"

        b               = dict(bone)
        b["unique_name"] = unique
        b["world_pos"]   = world
        result.append(b)

        for child in bone["children"]:
            _visit(child, world)

    _visit(skel_data["root"], (0.0, 0.0, 0.0))
    return result


def build_parent_map(skel_data: dict) -> Dict[int, Optional[int]]:
    """Return ``{dfs_index: parent_dfs_index}``; root maps to ``None``."""
    parent_map: Dict[int, Optional[int]] = {}
    counter = [-1]

    def _visit(bone: dict, parent_idx: Optional[int]) -> None:
        counter[0] += 1
        my_idx = counter[0]
        parent_map[my_idx] = parent_idx
        for child in bone["children"]:
            _visit(child, my_idx)

    _visit(skel_data["root"], None)
    return parent_map


def bone_per_vertex(mtxv: List[int], total_verts: int) -> List[int]:
    """Return the DFS bone index for each vertex via cumulative mtxv counts."""
    result: List[int] = []
    for bone_idx, count in enumerate(mtxv):
        result.extend([bone_idx] * count)
    while len(result) < total_verts:
        result.append(0)
    return result


# ── Collection helper ─────────────────────────────────────────────────────────
def _get_or_create_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


# ── Armature builder ──────────────────────────────────────────────────────────
def build_armature(bone_list: List[dict], parent_map: Dict[int, Optional[int]], char_name: str) -> bpy.types.Object:
    """Create a Blender armature from a flat DFS bone list."""
    arm_data = bpy.data.armatures.new(f"{char_name}_Armature")
    arm_obj  = bpy.data.objects.new(f"{char_name}_Armature", arm_data)
    arm_obj["ske_char_name"] = char_name

    _get_or_create_collection(f"SKE_{char_name}").objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = arm_data.edit_bones
    bone_refs  = []

    for bone in bone_list:
        wx, wy, wz = bone["world_pos"]
        head_bl    = mathutils.Vector(_g2b(wx, wy, wz))
        eb         = edit_bones.new(bone["unique_name"])
        eb.head    = head_bl
        eb.tail    = head_bl + mathutils.Vector((0.0, 0.04, 0.0))
        eb.use_connect = False
        bone_refs.append(eb)

    for i in range(len(bone_list)):
        p = parent_map.get(i)
        if p is not None:
            bone_refs[i].parent = bone_refs[p]

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


# ── Skinned mesh builder ──────────────────────────────────────────────────────
def _load_face_texture(tex_name: str, tex_folder: Path) -> Optional[bpy.types.Image]:
    img_name = f"{tex_name.upper()}.DDS"
    existing = bpy.data.images.get(img_name)

    if existing:
        return existing
    
    dds_path = tex_folder / img_name

    if not dds_path.exists():
        return None
    
    return bpy.data.images.load(str(dds_path))


def build_mesh(mod_data: dict, armature_obj: bpy.types.Object,
               bone_list: List[dict], char_name: str, tex_folder: Optional[Path] = None) -> bpy.types.Object:
    """Create a skinned mesh from parsed MOD data and attach it to the armature."""
    verts_game = mod_data["verts"]
    adjuncts   = mod_data["adjuncts"]
    tris       = mod_data["tris"]
    materials  = mod_data["materials"]
    uvs        = mod_data["uvs"]
    bpv        = bone_per_vertex(mod_data["mtxv"], len(verts_game))

    # MOD vertices are bone-local; add each bone's world position for mesh world coords.
    verts_bl = []
    for vi, v in enumerate(verts_game):
        bi   = bpv[vi]
        bone = bone_list[bi] if bi < len(bone_list) else bone_list[0]
        wx, wy, wz = bone["world_pos"]
        lx, ly, lz = v
        verts_bl.append(mathutils.Vector(_g2b(wx + lx, wy + ly, wz + lz)))

    face_list = [[adjuncts[ai]["vi"] for ai in tri] for tri in tris]

    me = bpy.data.meshes.new(f"{char_name}_Mesh")
    me.from_pydata(verts_bl, [], face_list)
    me.update()

    for m in materials:
        mat = bpy.data.materials.get(m["name"]) or bpy.data.materials.new(m["name"])
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        out_node          = nodes.new("ShaderNodeOutputMaterial")
        out_node.location = (300, 300)
        bsdf              = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location     = (0, 300)
        links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

        r, g, b = m["diffuse"]
        bsdf.inputs["Base Color"].default_value = (
            _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0
        )

        tex_name = m.get("texture1")

        if tex_name and tex_folder:
            img = _load_face_texture(tex_name, tex_folder)
            
            if img:
                tex_node          = nodes.new("ShaderNodeTexImage")
                tex_node.image    = img
                tex_node.location = (-300, 300)
                links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

        me.materials.append(mat)

    for poly, tri in zip(me.polygons, tris):
        poly.material_index = adjuncts[tri[0]]["mat"]

    uv_layer = me.uv_layers.new(name="UVMap")
    for poly, tri in zip(me.polygons, tris):
        for loop_idx, ai in zip(poly.loop_indices, tri):
            t1i = adjuncts[ai]["t1i"]

            if t1i < len(uvs):
                u, v = uvs[t1i]
                uv_layer.data[loop_idx].uv = (u, 1.0 - v)

    mesh_obj                  = bpy.data.objects.new(f"{char_name}_Mesh", me)
    mesh_obj["ske_char_name"] = char_name
    _get_or_create_collection(f"SKE_{char_name}").objects.link(mesh_obj)

    for bone in bone_list:
        mesh_obj.vertex_groups.new(name=bone["unique_name"])

    for vi, bi in enumerate(bpv):
        if bi < len(bone_list):
            vg = mesh_obj.vertex_groups.get(bone_list[bi]["unique_name"])

            if vg:
                vg.add([vi], 1.0, 'REPLACE')

    mesh_obj.parent         = armature_obj
    arm_mod                 = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object          = armature_obj
    return mesh_obj


# ── Animation action builder ──────────────────────────────────────────────────
def apply_anim_action(armature_obj: bpy.types.Object, anim_data: dict,
                      bone_list: List[dict], anim_name: str) -> bpy.types.Action:
    """Build a Blender action from parsed ANIM data and assign it to the armature."""
    action = bpy.data.actions.new(anim_name)
    
    if armature_obj.animation_data is None:
        armature_obj.animation_data_create()

    armature_obj.animation_data.action = action
    action.use_fake_user = True

    # Rotation mode must be set before inserting any F-curve keyframes.
    for pb in armature_obj.pose.bones:
        pb.rotation_mode = 'QUATERNION'

    root_rest_bl = mathutils.Vector(_g2b(*bone_list[0]["world_pos"]))

    def _fc(data_path: str, index: int) -> bpy.types.FCurve:
        fc = action.fcurves.find(data_path, index=index)
        return fc if fc else action.fcurves.new(data_path, index=index)

    def _insert(fc: bpy.types.FCurve, frame_num: int, value: float) -> None:
        kp = fc.keyframe_points.insert(frame_num, value, options={'FAST'})
        kp.interpolation = 'LINEAR'

    # Channel 0: root world position
    root_name = bone_list[0]["unique_name"]
    loc_fcs   = [_fc(f'pose.bones["{root_name}"].location', i) for i in range(3)]

    for f, frame in enumerate(anim_data["frames"]):
        gx, gy, gz = frame[0]
        offset     = mathutils.Vector(_g2b(gx, gy, gz)) - root_rest_bl
        _insert(loc_fcs[0], f + 1, offset.x)
        _insert(loc_fcs[1], f + 1, offset.y)
        _insert(loc_fcs[2], f + 1, offset.z)

    for fc in loc_fcs:
        fc.update()

    # Channels 1..N: per-bone XZY Euler rotations in DFS order
    for bi, bone in enumerate(bone_list):
        rot_path = f'pose.bones["{bone["unique_name"]}"].rotation_quaternion'
        rot_fcs  = [_fc(rot_path, i) for i in range(4)]  # W X Y Z

        for f, frame in enumerate(anim_data["frames"]):
            q = _game_euler_xzy_to_blender_quat(*frame[bi + 1])

            for i, v in enumerate((q.w, q.x, q.y, q.z)):
                _insert(rot_fcs[i], f + 1, v)

        for fc in rot_fcs:
            fc.update()

    return action


# ── Animation export ──────────────────────────────────────────────────────────
def export_anim_from_action(armature_obj: bpy.types.Object, bone_list: List[dict]) -> bytes:
    """Serialize the armature's active action to a binary ANIM byte string."""
    if not armature_obj.animation_data or not armature_obj.animation_data.action:
        raise ValueError("No action on armature")

    action      = armature_obj.animation_data.action
    frame_start = int(action.frame_range[0])
    frame_count = int(action.frame_range[1]) - frame_start + 1
    num_channels = len(bone_list) + 1

    root_rest_bl = mathutils.Vector(_g2b(*bone_list[0]["world_pos"]))

    def _sample(data_path: str, index: int, frame: int) -> float:
        fc = action.fcurves.find(data_path, index=index)
        return fc.evaluate(frame) if fc else 0.0

    frames_out = []

    for f in range(frame_count):
        frame_num  = frame_start + f
        frame_data = []

        root_name = bone_list[0]["unique_name"]
        loc_path  = f'pose.bones["{root_name}"].location'
        pos_bl    = mathutils.Vector((
            _sample(loc_path, 0, frame_num),
            _sample(loc_path, 1, frame_num),
            _sample(loc_path, 2, frame_num),
        )) + root_rest_bl
        frame_data.append(_bl2g(pos_bl.x, pos_bl.y, pos_bl.z))

        for bone in bone_list:
            rot_path = f'pose.bones["{bone["unique_name"]}"].rotation_quaternion'
            q = mathutils.Quaternion((
                _sample(rot_path, 0, frame_num),
                _sample(rot_path, 1, frame_num),
                _sample(rot_path, 2, frame_num),
                _sample(rot_path, 3, frame_num),
            ))

            if q.magnitude < 1e-6:
                q = mathutils.Quaternion()  # identity — bone had no F-curves
            else:
                q.normalize()

            frame_data.append(_blender_quat_to_game_euler_xzy(q))

        frames_out.append(frame_data)

    return _pack_anim(frame_count, num_channels, frames_out)


# ── VAR parser / writer ───────────────────────────────────────────────────────
def parse_var(path: Path) -> dict:
    """Parse a binary VAR file.

    Returns ``{"count": 6, "n_colors": N, "variants": [[(r,g,b), ...], ...]}``.
    Colors are raw sRGB bytes (0-255).  The N colors map 1:1 to the N materials
    in the MOD in definition order (including face texture materials).
    """
    buf      = io.BytesIO(path.read_bytes())
    count,   = read_unpack(buf, "<i")
    n_colors,= read_unpack(buf, "<i")

    variants = []

    for _ in range(count):
        row = []

        for _ in range(n_colors):
            r, g, b, _a = read_unpack(buf, "<BBBB")
            row.append((r, g, b))
        variants.append(row)

    return {"count": count, "n_colors": n_colors, "variants": variants}


def pack_var(var_data: dict) -> bytes:
    """Serialize a var_data dict back to binary VAR bytes."""
    out = pack_bytes("<ii", var_data["count"], var_data["n_colors"])
    for row in var_data["variants"]:
        for r, g, b in row:
            out += pack_bytes("<BBBB", r, g, b, 0xFF)
    return out


def get_all_material_names(mod_data: dict) -> List[str]:
    """Return all material names in MOD definition order (matches VAR color indices)."""
    return [m["name"] for m in mod_data["materials"]]


def apply_var_variant_to_mesh(mod_data: dict, var_data: dict, variant_idx: int) -> None:
    """Apply a VAR variant's colors to the mesh's Blender materials (1:1 with MOD order)."""
    if not (0 <= variant_idx < var_data["count"]):
        return
    
    colors = var_data["variants"][variant_idx]
    for i, mat_name in enumerate(get_all_material_names(mod_data)):
        if i >= len(colors):
            break

        mat = bpy.data.materials.get(mat_name)

        if not mat or not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs["Base Color"].default_value = (*_bytes_to_linear(*colors[i]), 1.0)
                break


def read_var_variant_from_mesh(mod_data: dict, var_data: dict, variant_idx: int) -> None:
    """Read current mesh material colors into a var_data variant slot (1:1 with MOD order)."""
    if not (0 <= variant_idx < var_data["count"]):
        return
    
    row = list(var_data["variants"][variant_idx])

    for i, mat_name in enumerate(get_all_material_names(mod_data)):
        if i >= len(row):
            break

        mat = bpy.data.materials.get(mat_name)

        if not mat or not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                c      = node.inputs["Base Color"].default_value
                row[i] = _linear_to_bytes(c[0], c[1], c[2])
                break
    var_data["variants"][variant_idx] = row


# ── CSV animation list ────────────────────────────────────────────────────────
def _anim_label(states: List[str]) -> str:
    """Build a short human-readable dropdown label from a list of game state names."""
    def _fmt(s: str) -> str:
        return s.replace("_", " ").title()

    # Rank: action states (no underscore, not idle) first, then idles, then transitions.
    IDLE   = {"STAND", "PRONE", "BACKUP"}
    pure   = [s for s in states if "_" not in s and s not in IDLE]
    idles  = [s for s in states if "_" not in s and s in IDLE]
    trans  = [s for s in states if "_" in s]
    ordered = pure + idles + trans

    primary = ordered[0] if ordered else states[0]
    others  = [s for s in ordered if s != primary]

    if not others:
        return _fmt(primary)
    
    if len(others) <= 3:
        return f"{_fmt(primary)}  ({', '.join(_fmt(o) for o in others)})"

    return f"{_fmt(primary)}  (+{len(others)} states)"


def parse_csv_anim_list(path: Path) -> List[Tuple[str, str]]:
    """Parse a character CSV and return ``[(anim_filename, friendly_label), ...]``.

    Each unique ANIM file appears once; the label summarises all game state
    names that reference it (e.g. ``"Walk  (Stand, Stand Walk, Walk Stand)"``).
    """
    file_states: OrderedDict = OrderedDict()

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split(",")
        if len(parts) < 2:
            continue

        state_name = parts[0].strip()
        anim_file  = parts[1].strip().upper()

        if not anim_file or not state_name:
            continue

        file_states.setdefault(anim_file, [])

        if state_name not in file_states[anim_file]:
            file_states[anim_file].append(state_name)

    return [(anim_file, _anim_label(states)) for anim_file, states in file_states.items()]


# ── SKEL writer ───────────────────────────────────────────────────────────────
def export_skel_from_armature(armature_obj: bpy.types.Object, skel_data: dict) -> str:
    """Reconstruct a SKEL text file from the armature's current rest-pose bone positions.

    Reads bone world positions from ``armature.data.bones``, converts Blender Z-up
    → game Y-up, recomputes parent-relative offsets, and preserves the original
    tree structure from ``skel_data``.
    """
    arm        = armature_obj.data
    bone_world: Dict[str, Tuple[float, float, float]] = {}

    for bone in arm.bones:
        head = armature_obj.matrix_world @ bone.head_local
        bone_world[bone.name] = _bl2g(head.x, head.y, head.z)

    # Annotate skel_data tree nodes with unique_names (reverse of dfs_bone_order).
    bone_list = dfs_bone_order(skel_data)
    idx       = [0]

    def _annotate(node: dict) -> dict:
        b = dict(node)
        if idx[0] < len(bone_list):
            b["unique_name"] = bone_list[idx[0]]["unique_name"]
        idx[0] += 1
        b["children"] = [_annotate(c) for c in node.get("children", [])]
        return b

    root = _annotate(skel_data["root"])

    def _write_bone(node: dict, parent_world: Tuple[float, float, float], indent: int) -> str:
        unique = node.get("unique_name", node["name"])
        pos    = bone_world.get(unique, bone_world.get(node["name"], parent_world))
        px, py, pz = parent_world
        ox, oy, oz = pos[0] - px, pos[1] - py, pos[2] - pz
        tab        = "\t" * indent
        lines      = [f"{tab}bone {node['name']} {{",
                      f"{tab}\toffset {ox:.6f} {oy:.6f} {oz:.6f}"]
        for child in node.get("children", []):
            lines.append(_write_bone(child, pos, indent + 1))
        lines.append(f"{tab}}}")
        return "\n".join(lines)

    root_name = root.get("unique_name", root["name"])
    root_pos  = bone_world.get(root_name, (0.0, 0.0, 0.0))
    rx, ry, rz = root_pos

    lines = [
        f"NumBones {skel_data['num_bones']}",
        f"bone {root['name']} {{",
        f"\toffset {rx:.6f} {ry:.6f} {rz:.6f}",
    ]
    for child in root.get("children", []):
        lines.append(_write_bone(child, root_pos, 1))
    lines.append("}")

    return "\n".join(lines) + "\n"


# ── MOD writer ────────────────────────────────────────────────────────────────
def export_mod_colors_from_mesh(mesh_obj: bpy.types.Object, original_mod_text: str) -> str:
    """Patch ``diffuse:`` lines in the original MOD text with current Blender material colors.

    Only materials that exist in both Blender and the MOD are updated;
    everything else (geometry, UVs, texture references) is preserved verbatim.
    """
    if mesh_obj is None:
        return original_mod_text

    mat_colors: Dict[str, Tuple[float, float, float]] = {}

    for mat in mesh_obj.data.materials:
        if mat is None or not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                c = node.inputs["Base Color"].default_value
                # Linear → sRGB: MOD diffuse values are sRGB 0.0-1.0
                mat_colors[mat.name] = (
                    _linear_to_srgb(c[0]),
                    _linear_to_srgb(c[1]),
                    _linear_to_srgb(c[2]),
                )
                break

    cur_mat   = None
    out_lines = []

    for line in original_mod_text.splitlines():
        stripped = line.strip()
        parts    = stripped.split()

        if parts and parts[0] == "mtl":
            cur_mat = parts[1].rstrip("{").strip()
            out_lines.append(line)

        elif parts and parts[0] == "diffuse:" and cur_mat and cur_mat in mat_colors:
            r, g, b = mat_colors[cur_mat]
            out_lines.append(f"\t\tdiffuse: {r:.6f} {g:.6f} {b:.6f}")

        else:
            out_lines.append(line)

    return "\n".join(out_lines) + "\n"


# ── Clear helpers ─────────────────────────────────────────────────────────────
def clear_skeleton_objects(char_name: str) -> None:
    """Remove all Blender objects tagged with the given character name."""
    col_name = f"SKE_{char_name}"
    col      = bpy.data.collections.get(col_name)

    if not col:
        for obj in list(bpy.data.objects):
            if obj.get("ske_char_name") == char_name:
                bpy.data.objects.remove(obj, do_unlink=True)
        return
    
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
        
    bpy.data.collections.remove(col)
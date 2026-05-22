"""Car Editor — lights module (split from the former car_editor.py monolith)."""
import bpy
import shutil
import struct
import mathutils
from pathlib import Path

from src.constants.folder import Folder
from src.constants.car_assets import LightColor
from src.constants.file_formats import FileType, MeshFlags
from src.integrations.blender.modeling.meshes import read_bms
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data, write_bms

from src.integrations.blender.operators.car_editor.common import (
    _add_child_obj, _copy_files_to_shop, _load_bms, get_car_objects,
)
from src.integrations.blender.operators.car_editor.constants import (
    _CAR_LIGHT_DEFS, _CAR_LIGHT_FILE, _CAR_LIGHT_TAGS, _CAR_TAG, _LIGHT_FILE, _SIREN_HOUSING_TAG,
    _SIREN_LIGHT_TAGS,
)


# Glow-colour catalogue (texture names, friendly labels, RGB tints) and the set of
# stock GLOBAL.TSH textures live in src/constants/car_assets.py → LightColor,
# alongside WheelTexture / Vehicle.


def _white_base(tex_name: str) -> str:
    """Strip the colour suffix to get the white source texture name."""
    u = tex_name.upper()
    if u.startswith("FXLTGLOW"):
        return "FXLTGLOW"
    if u.startswith("FXLTCONE"):
        return "FXLTCONE"
    return tex_name


def _colored_tex(tex_name: str, suffix: str) -> str:
    """White base + colour suffix, e.g. (FXLTCONE, 'RED') → 'FXLTCONERED'."""
    return _white_base(tex_name) + suffix


def _tint_dds_a4r4g4b4(src: Path, dst: Path, rgb) -> bool:
    """Tint an uncompressed 16-bit A4R4G4B4 DDS (the format the FX glow textures
    use) to a colour, preserving the header + full mip chain. Each pixel's
    intensity (max RGB nibble) is kept and re-tinted, so a white glow becomes a
    coloured glow with the same alpha falloff."""
    try:
        data = bytearray(src.read_bytes())
    except OSError:
        return False
    if len(data) < 128 or data[:4] != b"DDS ":
        return False
    r_f, g_f, b_f = rgb
    body = data[128:]
    for i in range(0, len(body) - 1, 2):
        v = body[i] | (body[i + 1] << 8)
        a = (v >> 12) & 0xF
        r = (v >> 8) & 0xF
        g = (v >> 4) & 0xF
        b = v & 0xF
        inten = max(r, g, b)
        nr = min(15, round(inten * r_f))
        ng = min(15, round(inten * g_f))
        nb = min(15, round(inten * b_f))
        nv = (a << 12) | (nr << 8) | (ng << 4) | nb
        body[i] = nv & 0xFF
        body[i + 1] = (nv >> 8) & 0xFF
    data[128:] = body
    try:
        dst.write_bytes(data)
        return True
    except OSError:
        return False


def _ensure_glow_texture(tex_name: str, tex_folder: Path) -> None:
    """Make sure tex_name.DDS exists in tex_folder, generating a tinted variant
    from its white base (FXLTGLOW / FXLTCONE) when it's one of our custom colours."""
    path = tex_folder / f"{tex_name}{FileType.DIRECTDRAW_SURFACE}"
    if path.exists():
        return
    base   = _white_base(tex_name)
    suffix = tex_name.upper()[len(base):]
    rgb    = LightColor.SUFFIX_RGB.get(suffix)
    src    = tex_folder / f"{base}{FileType.DIRECTDRAW_SURFACE}"
    if rgb and src.exists():
        _tint_dds_a4r4g4b4(src, path, rgb)


def _is_car_light(tag: str) -> bool:
    return tag in _CAR_LIGHT_FILE


def _get_car_light_objs():
    return [o for o in get_car_objects() if _is_car_light(o.get(_CAR_TAG, ""))]


def _load_car_lights(car_name: str, src_folder, body_obj, col, tex_folder) -> int:
    """Load the car's light effect-meshes (head/tail/brake/reverse/signals) as
    editable parts at their stock positions. Falls back to VPMUSTANG99 per mesh."""
    mustang = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99"
    for o in _get_car_light_objs():
        bpy.data.objects.remove(o, do_unlink=True)
    n = 0
    for tag, fname, _, _ in _CAR_LIGHT_DEFS:
        f = src_folder / fname
        if not f.exists():
            f = mustang / fname
        if not f.exists():
            continue
        mesh = _load_bms(f, f"{car_name}.{tag}", tex_folder)
        if mesh:
            _add_child_obj(mesh, mesh.name, tag, body_obj, col)
            n += 1
    return n


def _write_absolute_vert_bms(obj, out_path: Path, remap_to_global: bool = False) -> None:
    """Write a light / siren mesh as ABSOLUTE car-space verts with no OFFSET flag.

    The engine draws light slots without applying mesh_offset, so we fold the
    object's placement into the vertices and clear the OFFSET flag — baking it as
    centred verts + offset would bury the mesh at the car origin.

    When ``remap_to_global`` is set (stock-car / minimal packs that can't ship a
    TSH) any generated colour texture is remapped to its global GLOBAL.TSH base so
    the engine can still resolve it (the light still works, just white).
    """
    data = mesh_to_bms_data(obj, bake_location=False)
    ox, oy, oz = data["mesh_offset"]
    data["points"]      = [(x + ox, y + oy, z + oz) for (x, y, z) in data["points"]]
    data["mesh_offset"] = (0.0, 0.0, 0.0)
    data["flags"]      &= ~MeshFlags.OFFSET

    if remap_to_global:
        data["texture_names"] = [
            t if t.upper() in LightColor.GLOBAL_TEXTURES else _white_base(t)
            for t in data.get("texture_names", [])
        ]

    write_bms(data, out_path)


def _export_light_objs(car_name: str, objs, minimal: bool = False) -> int:
    """Write any light / siren objects to their BMS slots in SHOP/BMS/{car}/ via
    the unified _LIGHT_FILE registry. In ``minimal`` mode (stock-car edit) generated
    colours are remapped to their global base (no per-car TSH to declare them)."""
    dst = Folder.Shop.Meshes / car_name
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for obj in objs:
        fname = _LIGHT_FILE.get(obj.get(_CAR_TAG, ""))
        if not fname:
            continue
        try:
            _write_absolute_vert_bms(obj, dst / fname, remap_to_global=minimal)
            n += 1
        except Exception as exc:
            print(f"[Car Editor] Light export failed for {fname}: {exc}")
    return n


def _export_car_lights(car_name: str, light_objs, minimal: bool = False) -> int:
    """Write the (possibly edited/moved) car lights to SHOP/BMS/{car}/."""
    return _export_light_objs(car_name, light_objs, minimal)


def _ensure_custom_glow_in_shop(light_objs) -> int:
    """Stage any custom (non-global) FXLT glow textures referenced by the lights
    into SHOP/TEX16A so _pack_car_ar bundles them. Returns the count staged."""
    tex_folder = Folder.Resources.Editor.Textures
    tex16a     = Folder.Shop.Textures.Alpha
    wanted: set = set()
    for obj in light_objs:
        for mat in obj.data.materials:
            if not mat:
                continue
            u = mat.name.upper()
            if u.startswith("FXLT") and u not in LightColor.GLOBAL_TEXTURES:
                wanted.add(mat.name)
    if not wanted:
        return 0
    tex16a.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in wanted:
        _ensure_glow_texture(name, tex_folder)
        src = tex_folder / f"{name}{FileType.DIRECTDRAW_SURFACE}"
        if src.exists():
            shutil.copy2(src, tex16a / src.name)
            n += 1
    return n


def _light_color_value(obj) -> str:
    """The FXLTGLOW* glow texture currently on this light (defaults to FXLTGLOW)."""
    for mat in obj.data.materials:
        if mat and mat.name.upper() in LightColor.TEXTURES:
            return mat.name.upper()
    return "FXLTGLOW"


def _sync_light_props(scene) -> None:
    """Set ce_light_color_{i}/ce_light_beam/siren colours from the loaded objects."""
    by_tag = {o.get(_CAR_TAG, ""): o for o in _get_car_light_objs()}
    try:
        scene.ce_light_syncing = True
        for i, tag in enumerate(_CAR_LIGHT_TAGS):
            obj = by_tag.get(tag)
            if obj is None:
                continue
            try:
                setattr(scene, f"ce_light_color_{i}", _light_color_value(obj))
            except (TypeError, ValueError):
                pass
        head = by_tag.get("light_head")
        if head is not None:
            try:
                scene.ce_light_beam = float(head.get("light_beam", 1.0))
            except (TypeError, ValueError):
                pass
        # Siren lenses (loaded via Load Siren Lights).
        siren = {o.get(_CAR_TAG, ""): o for o in _get_siren_light_objs()}
        for tag, prop in (("light_red", "ce_siren_color_red"),
                          ("light_blue", "ce_siren_color_blue")):
            obj = siren.get(tag)
            if obj is not None:
                try:
                    setattr(scene, prop, _light_color_value(obj))
                except (TypeError, ValueError):
                    pass
    finally:
        scene.ce_light_syncing = False


def _is_siren_light(tag: str) -> bool:
    return tag in _SIREN_LIGHT_TAGS


def _is_siren_part(tag: str) -> bool:
    return tag in _SIREN_LIGHT_TAGS or tag == _SIREN_HOUSING_TAG


def _get_siren_light_objs():
    return [o for o in get_car_objects() if _is_siren_light(o.get(_CAR_TAG, ""))]


def _get_siren_housing_objs():
    return [o for o in get_car_objects() if o.get(_CAR_TAG, "") == _SIREN_HOUSING_TAG]


def _body_roof_anchor(body_obj):
    """
    (top_z, x, y) of the body's high region (the cabin peak) in world space.

    Uses the actual mesh vertices, not the bounding box: for low/wedge cars (e.g.
    Panoz) the highest point is the cockpit, which sits well forward of the bbox
    centre — placing a roof bar at bbox-centre would float it over the lower rear
    deck. We average the X/Y of vertices within the top ~20% of the height so the
    bar lands over the cabin for both boxy and wedge shapes.
    """
    mw = body_obj.matrix_world
    vs = [mw @ v.co for v in body_obj.data.vertices]
    if not vs:
        c = [mw @ mathutils.Vector(b) for b in body_obj.bound_box]
        return (max(p.z for p in c), 0.0, sum(p.y for p in c) / 8.0)
    top_z = max(v.z for v in vs)
    band  = max(0.05, (top_z - min(v.z for v in vs)) * 0.20)
    near  = [v for v in vs if v.z >= top_z - band]
    rx = sum(v.x for v in near) / len(near)
    ry = sum(v.y for v in near) / len(near)
    return (top_z, rx, ry)


def _export_placed_siren_lights(car_name: str, light_objs) -> int:
    """Write the user-placed siren lenses to SHOP/BMS/{car}/REDLIGHT|BLUELIGHT.BMS
    (absolute verts, no OFFSET — see _write_absolute_vert_bms), keeping their
    VPCOP_TOPLIGHT lens + recoloured glow materials."""
    n = _export_light_objs(car_name, light_objs)
    print(f"[Car Editor] Placed siren lights exported ({n}) for {car_name}")
    return n


def _ensure_siren_textures_in_shop() -> int:
    """
    Stage the cop light textures into SHOP/TEX16A so the bar renders in game:
      VPCOPLIGHTS   — the always-visible housing lens (merged into the body)
      VPCOP_TOPLIGHT — the flashing-lens texture on REDLIGHT/BLUELIGHT
    Both are cop-specific (in VPCOP.TSH, not GLOBAL.TSH), so — like the cop wheel
    texture — they must be packed and declared with the 't' (TEX16A) flag.
    """
    n = _copy_files_to_shop(
        Folder.Resources.Editor.Textures, Folder.Shop.Textures.Alpha,
        ["VPCOPLIGHTS.DDS", "VPCOP_TOPLIGHT.DDS"],
    )
    print(f"[Car Editor] Staged {n} cop light texture(s) → SHOP/TEX16A")
    return n


def _bms_roof_ref(bms_path):
    """(top_y, center_z) of a body BMS in car space, or None if unreadable."""
    try:
        d = read_bms(bms_path)
        ox, oy, oz = d["mesh_offset"]
        ys = [p[1] + oy for p in d["points"]]
        zs = [p[2] + oz for p in d["points"]]
        return (max(ys), (min(zs) + max(zs)) * 0.5)
    except Exception:
        return None


def _ensure_siren_lights_in_shop(car_name: str) -> int:
    """
    Stage the police roof-light meshes (REDLIGHT/BLUELIGHT) into SHOP/BMS/{car}/.

    The stock VPCOP lights are modelled at VPCOP's roof height; on a taller/larger
    custom body they'd sit buried. We shift each light's vertices so the pair lands
    on THIS car's roof (top-centre of the body AABB), matching how VPCOP's lights
    straddle its own roofline. The engine draws these (mesh slots 16-17) when the
    siren is toggled; their textures (VPCOP_TOPLIGHT, FXLTGLOWRED) are picked up by
    _build_car_tsh, which scans the BMS folder. Must run BEFORE _build_car_tsh.

    Returns the number of meshes staged.
    """

    src_dir = Folder.Resources.Editor.Meshes / "CARS" / "VPCOP"
    dst_dir = Folder.Shop.Meshes / car_name
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Shift = how far this car's roof moved vs the VPCOP roof the lights were built
    # for. The light meshes already carry the OFFSET flag, so we just bump their
    # 12-byte mesh_offset header field (bytes 4..16) — the engine adds it to every
    # vertex. Byte-patching preserves the mesh exactly (no read/write round-trip).

    ref = _bms_roof_ref(src_dir / "BODY_H.BMS")
    new = _bms_roof_ref(dst_dir / "BODY_H.BMS")
    dy, dz = (new[0] - ref[0], new[1] - ref[1]) if (ref and new) else (0.0, 0.0)

    n = 0
    for mesh in ("REDLIGHT.BMS", "BLUELIGHT.BMS"):
        src = src_dir / mesh
        if not src.exists():
            print(f"[Car Editor] Siren light mesh missing: {src}")
            continue
        raw = bytearray(src.read_bytes())
        if (dy or dz) and len(raw) >= 16:
            ox, oy, oz = struct.unpack_from("<3f", raw, 4)
            struct.pack_into("<3f", raw, 4, ox, oy + dy, oz + dz)
        (dst_dir / mesh).write_bytes(raw)
        n += 1

    print(f"[Car Editor] Police lights staged ({n} mesh(es), roof shift dy={dy:.2f} dz={dz:.2f})")
    return n

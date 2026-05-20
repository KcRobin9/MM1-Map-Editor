"""
Car Editor operators: Load, Export, Reload.

Car objects in the scene are tagged with the custom property ``mm_car_part``
whose value identifies the part type ("body", "wheel_0", "fender_0", …).
The body object also carries ``mm_car_folder`` (source folder path) and
``mm_car_name`` (vehicle name, e.g. "VPFORD").
"""
import bpy
import bmesh
import math
import mathutils
import datetime
import re
from pathlib import Path
from typing import Optional

from src.integrations.blender.modeling.meshes import (
    read_bms, build_blender_mesh, _apply_materials_to_mesh, _build_material,
    _to_blender_pos,
)
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data, write_bms
from src.integrations.blender.modeling import car_templates
from src.constants.folder import Folder
from src.constants.file_formats import FileType, MeshFlags


# ── Paint-variant helpers ─────────────────────────────────────────────────────

# Textures shared across all cars — not part of any paint variant.
_GENERIC_TEXTURES = frozenset({
    "CARBOTTOM", "VAHEADLIGHT", "VASIGNALUNIT", "VASTOPUNIT", "VACOMP_WHL",
})

# Per-session cache: keyed by (car_name, tex_folder_str) → list[str]
_paint_variant_cache: dict = {}


def _car_paint_texture_names(body_mesh) -> list:
    """Non-generic, car-specific textures that belong to a paint scheme."""
    return [
        t for t in (body_mesh.get("texture_names") or [])
        if t not in _GENERIC_TEXTURES and "_" in t
    ]


def _detect_paint_prefix(body_mesh) -> str:
    """
    Return the colour-variant prefix for this car's body textures.
    E.g. 'VPPANOZGREEN', 'VPF350BLUE'.  Returns '' when detection fails.

    Uses the most-common prefix among non-generic, non-DMG textures so that
    shared base textures like VPF350_BD (prefix 'VPF350') don't pollute the
    result when the majority of textures use e.g. 'VPF350BLUE'.
    """
    from collections import Counter
    specific = [t for t in _car_paint_texture_names(body_mesh)
                if not t.upper().endswith("_DMG")]
    if not specific:
        return ""
    counts = Counter(t.split("_")[0] for t in specific)
    prefix, freq = counts.most_common(1)[0]
    # Require the most-common prefix to cover at least half the specific textures.
    return prefix if freq * 2 >= len(specific) else ""


def _find_paint_variants(body_mesh, tex_folder: Path, current_prefix: str) -> list:
    """
    Return a sorted list of all paint-variant prefixes available in tex_folder
    for this car, e.g. ['VPBULLET', 'VPBULLETBLUE', 'VPBULLETRED', 'VPBULLETWHITE'].
    Returns [] when only one variant exists or detection fails.

    Works by trying progressively shorter base prefixes (from the full
    current_prefix down to 4 chars) and returning the set of variants that
    yields the most complete matches.  This handles both:
      - Strategy A: current_prefix IS the base (e.g. VPBULLET has siblings
        VPBULLETBLUE, VPBULLETRED …).
      - Strategy B: current_prefix contains a colour suffix (e.g. VPPANOZGREEN
        → base VPPANOZ has siblings VPPANOZBLUE, VPPANOZMAGENTA, VPPANOZRED).
    """
    if not current_prefix:
        return []

    cp = current_prefix.upper()

    # Only use textures whose prefix matches current_prefix to derive required
    # suffixes.  This excludes shared base textures like VPF350_BD (prefix
    # "VPF350") when the variant prefix is "VPF350BLUE".
    variant_specific = [
        t for t in _car_paint_texture_names(body_mesh)
        if not t.upper().endswith("_DMG") and t.upper().split("_")[0] == cp
    ]
    if not variant_specific:
        return []

    suffixes = frozenset("_" + "_".join(t.split("_")[1:]) for t in variant_specific)

    try:
        existing = {p.stem.upper() for p in tex_folder.iterdir()
                    if p.suffix.upper() == ".DDS"}
    except OSError:
        return []

    # Try every base length from len(cp) down to 4.
    # Keep the result with the most valid variants found at any length.
    best: list = []
    for length in range(len(cp), 3, -1):
        base = cp[:length]
        cand_prefixes = {
            s.split("_")[0]
            for s in existing
            if "_" in s and s.split("_")[0].startswith(base)
        }
        valid = sorted(
            p for p in cand_prefixes
            if all((p + s) in existing for s in suffixes)
        )
        if len(valid) > len(best):
            best = valid

    return best if len(best) > 1 else []


def _find_paint_variants_cached(car_name: str, body_mesh,
                                tex_folder: Path, current_prefix: str) -> list:
    key = (car_name, str(tex_folder))
    if key not in _paint_variant_cache:
        _paint_variant_cache[key] = _find_paint_variants(body_mesh, tex_folder, current_prefix)
    return _paint_variant_cache[key]


def _variant_color_name(variant: str, all_variants: list) -> str:
    """
    Derive a human-readable colour label, e.g. 'VPBULLETBLUE' → 'Blue'.
    Uses the longest common prefix of all variants as the base car name.
    """
    import os
    base = os.path.commonprefix(all_variants)
    color = variant[len(base):]
    return color.title() if color else "Default"


def _detect_wheel_texture(car_objects: list) -> str:
    """Return the material name of the first wheel's first slot, or ''."""
    for obj in car_objects:
        if obj.get(_CAR_TAG, "").startswith("wheel_") and obj.type == "MESH":
            mats = obj.data.materials
            if mats and mats[0]:
                return mats[0].name
    return ""


def _apply_paint_variant(car_objects: list, new_prefix: str,
                         current_prefix: str, tex_folder: Path) -> int:
    """
    For every material whose name starts with current_prefix, replace it with the
    equivalent material using new_prefix.  Handles both normal and _DMG slots.
    Returns the number of material slots successfully swapped.
    """
    seen   = set()
    count  = 0
    cp_up  = current_prefix.upper()

    for obj in car_objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        if id(mesh) in seen:
            continue
        seen.add(id(mesh))

        for i, mat in enumerate(mesh.materials):
            if mat is None or not mat.name.upper().startswith(cp_up):
                continue
            suffix   = mat.name[len(current_prefix):]   # e.g. '_FT' or '_FT_DMG'
            new_name = new_prefix + suffix
            dds      = tex_folder / f"{new_name}.DDS"
            if not dds.exists():
                dds = tex_folder / f"{new_name}.dds"
            if not dds.exists():
                continue
            mesh.materials[i] = _build_material(new_name, tex_folder)
            count += 1

    return count


# Matches a timestamp suffix appended by a previous export, e.g. "_2026_24_04_2045_05"
_TIMESTAMP_SUFFIX_RE = re.compile(r'_\d{4}_\d{2}_\d{2}_\d{4}_\d{2}$')


def _current_time_formatted() -> str:
    return datetime.datetime.now().strftime("%Y_%d_%m_%H%M_%S")


def _base_car_name(name: str) -> str:
    """Strip any trailing timestamp suffix so re-exports don't double-stamp the name."""
    return _TIMESTAMP_SUFFIX_RE.sub('', name)


# ── Constants ─────────────────────────────────────────────────────────────────

_CAR_COLLECTION = "Car Editor"
_CAR_TAG        = "mm_car_part"


# ── Face texture update callback ──────────────────────────────────────────────

def _get_or_create_car_mat(mesh, tex_name: str, tex_folder: Path):
    """Return the slot index for tex_name on mesh, creating it if needed."""
    for i, mat in enumerate(mesh.materials):
        if mat and mat.name == tex_name:
            return i
    # Create a new material
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
    tex_folder = Path(self.ce_texture_folder) if self.ce_texture_folder else Folder.Resources.Editor.Textures
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


def _pack_car_ar(car_name: str, minimal: bool = False) -> bool:
    """
    Pack the car's files from SHOP into !!!!!{car_name}.ar in MidtownMadness/.

    Collects from the standard SHOP subdirs:
      SHOP/BMS/{NAME}/*            → BMS/{NAME}/* in AR
      SHOP/TUNE/{NAME}*            → TUNE/*        in AR
      SHOP/MTL/{NAME}.TSH          → MTL/*         in AR
      SHOP/BND/{NAME}_BND.BND     → BND/*         in AR

    When ``minimal`` is True only BMS/{NAME}/ is packed (editing an existing
    game car): the original TSH, dashboard, textures and collision remain in
    effect, so we override geometry only — no TUNE/MTL/BND/TEX16A/_DASH.

    A temp staging tree is assembled so mkar receives correct relative paths.
    The !!!!!-prefix ensures the file loads last, overriding any prior copy.
    """
    import subprocess
    import shutil

    mm1_folder   = Folder.MidtownMadness.Root
    mkar_exe     = Folder.Angel / "mkar.exe"

    if not mkar_exe.exists():
        print(f"[Car Editor] mkar.exe not found at {mkar_exe}")
        return False

    car_bms_dir = Folder.Shop.Meshes / car_name
    if not car_bms_dir.is_dir():
        print(f"[Car Editor] No BMS folder: {car_bms_dir}")
        return False

    bms_files = sorted(f for f in car_bms_dir.iterdir() if f.is_file())
    if not bms_files:
        print(f"[Car Editor] No BMS files in {car_bms_dir}")
        return False

    ar_name = f"!!!!!{car_name}.ar"
    ar_out  = mm1_folder / ar_name
    tmp_dir = Folder.BASE / f"_car_pack_tmp_{car_name}"

    try:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True)

        # BMS meshes → BMS/{NAME}/
        bms_dst = tmp_dir / "BMS" / car_name
        bms_dst.mkdir(parents=True)
        for f in bms_files:
            shutil.copy2(f, bms_dst / f.name)

        # mmDamage::InitDamage hardcodes Meshes[2] = _M body; NULL crashes damage.c:14
        body_h = bms_dst / "BODY_H.BMS"
        body_m = bms_dst / "BODY_M.BMS"
        if body_h.exists() and not body_m.exists():
            shutil.copy2(body_h, body_m)

        # Everything below (dash, tune, TSH, collision, textures) is only packed
        # for brand-new cars.  For an existing game car we override geometry only
        # and let the base AR supply the rest — see _is_original_car.
        if not minimal:
            # Dashboard sub-folder BMS/{NAME}_DASH/ — the game loads this separately
            # from the main BMS folder; if not overridden the original AR's dash meshes
            # remain active and reference textures not declared in our TSH.
            dash_shop = Folder.Shop.Meshes / f"{car_name}_DASH"
            if dash_shop.is_dir():
                dash_dst = tmp_dir / "BMS" / f"{car_name}_DASH"
                dash_dst.mkdir(parents=True)
                for f in sorted(dash_shop.iterdir()):
                    if f.is_file():
                        shutil.copy2(f, dash_dst / f.name)

            # TUNE files whose name starts with car_name → TUNE/
            tune_src = Folder.Shop.Tune
            if tune_src.is_dir():
                tune_dst = tmp_dir / "TUNE"
                tune_dst.mkdir()
                for f in sorted(tune_src.iterdir()):
                    if f.is_file() and f.name.upper().startswith(car_name.upper()):
                        shutil.copy2(f, tune_dst / f.name)

            # TSH texture sheet → MTL/
            tsh_src = Folder.Shop.Material / f"{car_name}{FileType.TEXTURE_SHEET}"
            if tsh_src.exists():
                mtl_dst = tmp_dir / "MTL"
                mtl_dst.mkdir()
                shutil.copy2(tsh_src, mtl_dst / tsh_src.name)

            # Collision → BND/
            bnd_src = Folder.Shop.Bound / f"{car_name}_BND.BND"
            if bnd_src.exists():
                bnd_dst = tmp_dir / "BND"
                bnd_dst.mkdir()
                shutil.copy2(bnd_src, bnd_dst / bnd_src.name)

            # Car DLP → DLP/{NAME}.DLP — the engine reads each wheel's spin pivot
            # (mmWheel::Center) from this file's WHLn_H group centroid. Without it
            # the wheels orbit the car origin ("ferris wheel").
            dlp_src = Folder.Shop.DLP / f"{car_name}{FileType.DEVELOPMENT}"
            if dlp_src.exists():
                dlp_dst = tmp_dir / "DLP"
                dlp_dst.mkdir()
                shutil.copy2(dlp_src, dlp_dst / dlp_src.name)

            # Wheel texture (and any other TEX16A assets) → TEX16A/
            tex16a_shop = Folder.Shop.Textures.Alpha
            if tex16a_shop.is_dir():
                tex_files = [f for f in tex16a_shop.iterdir()
                             if f.is_file() and f.suffix.upper() == ".DDS"]
                if tex_files:
                    tex_dst = tmp_dir / "TEX16A"
                    tex_dst.mkdir()
                    for f in tex_files:
                        shutil.copy2(f, tex_dst / f.name)

        pack_files = sorted(f for f in tmp_dir.rglob("*") if f.is_file())
        if not pack_files:
            print(f"[Car Editor] Nothing staged to pack for {car_name}")
            return False

        lines = [f"./{f.relative_to(tmp_dir).as_posix()}" for f in pack_files]
        shiplist_path = tmp_dir / f"shiplist.{car_name}"
        shiplist_path.write_bytes(("\n".join(lines) + "\n").encode("ascii"))

        # mkar auto-detects the LONGEST common path prefix across all shiplist
        # entries and strips it from the stored names.  When every file lives
        # under one subtree (e.g. a minimal pack with only BMS/{NAME}/*), that
        # common prefix is the whole directory, so entries get flattened to bare
        # filenames and the game can't find BMS/{NAME}/BODY_H.BMS.  Force the
        # prefix length to 2 so only the leading "./" is stripped and the real
        # BMS/.., TUNE/.., MTL/.. paths are preserved.
        print(f"[Car Editor] Packing {len(pack_files)} files → {ar_name} …")
        result = subprocess.run(
            [str(mkar_exe), str(ar_out), str(shiplist_path), "2"],
            cwd=str(tmp_dir),
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.stdout:
            print(f"[Car Editor] mkar: {result.stdout.strip()}")
        if result.stderr:
            print(f"[Car Editor] mkar: {result.stderr.strip()}")

        if result.returncode != 0:
            print(f"[Car Editor] mkar failed (exit {result.returncode})")
            return False

        print(f"[Car Editor] Created {ar_out}")
        return True

    finally:
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
            except OSError as e:
                print(f"[Car Editor] Warning: cleanup failed: {e}")


def _ensure_wheels_in_shop(car_name: str) -> int:
    """
    If no WHL*_H.BMS files exist in SHOP/BMS/{car_name}/, copy them from
    the VPMUSTANG99 reference in resources/editor/MESHES/CARS/VPMUSTANG99/.
    Returns the number of wheel files copied.
    """
    import shutil
    bms_dst = Folder.Shop.Meshes / car_name
    bms_dst.mkdir(parents=True, exist_ok=True)

    existing = list(bms_dst.glob("WHL*_H.BMS"))
    if existing:
        return 0  # already have wheels

    src_dir = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99"
    copied  = 0
    for i in range(10):
        src = src_dir / f"WHL{i}_H.BMS"
        if not src.exists():
            break
        import shutil as _sh
        _sh.copy2(src, bms_dst / f"WHL{i}_H.BMS")
        copied += 1

    if copied:
        print(f"[Car Editor] No wheels tagged — copied {copied} VPMUSTANG99 wheels to SHOP/BMS/{car_name}/")
    return copied


def _ensure_dash_in_shop(car_name: str) -> int:
    """
    If SHOP/BMS/{car_name}_DASH/ doesn't exist or is empty, copy the dashboard
    BMS files from resources/editor/MESHES/CARS/VPMUSTANG99_DASH/.
    Returns the number of files copied.
    """
    import shutil
    dash_dst = Folder.Shop.Meshes / f"{car_name}_DASH"
    if dash_dst.is_dir() and any(dash_dst.iterdir()):
        return 0  # already populated

    src_dir = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99_DASH"
    if not src_dir.is_dir():
        return 0

    dash_dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    for f in sorted(src_dir.glob("*.BMS")):
        shutil.copy2(f, dash_dst / f.name)
        copied += 1

    if copied:
        print(f"[Car Editor] Copied {copied} dash BMS files → SHOP/BMS/{car_name}_DASH/")
    return copied


def _ensure_dlp_in_shop(car_name: str) -> bool:
    """
    Copy the VPMUSTANG99 template DLP to SHOP/DLP/{car_name}.DLP if not present.

    The game reads each wheel's spin pivot (mmWheel::Center) from the DLP's
    WHLn_H group centroid; without a DLP the pivot defaults to the car origin and
    the wheels orbit it ("ferris wheel"). The mustang DLP's WHL centroids match
    the mustang wheel hub positions, which the SEDAN template reuses.
    Returns True if a file was copied.
    """
    import shutil
    dlp_dst_dir = Folder.Shop.DLP
    dlp_dst_dir.mkdir(parents=True, exist_ok=True)
    dlp_dst = dlp_dst_dir / f"{car_name}{FileType.DEVELOPMENT}"
    if dlp_dst.exists():
        return False

    src = Folder.Resources.Editor.DLP / f"VPMUSTANG99{FileType.DEVELOPMENT}"
    if not src.exists():
        print(f"[Car Editor] Template DLP not found: {src}")
        return False

    shutil.copy2(src, dlp_dst)
    print(f"[Car Editor] Copied template DLP → SHOP/DLP/{car_name}{FileType.DEVELOPMENT}")
    return True


def _build_car_tsh(car_name: str, car_objects) -> None:
    """
    Write SHOP/MTL/{car_name}.TSH from ALL textures that will end up in the AR:

    1. Materials on the Blender car objects (what we exported this session).
    2. Any BMS files already sitting in SHOP/BMS/{car_name}/ that we didn't
       export (e.g. stale VL.BMS, light meshes copied by Init) — those files
       reference textures the game will try to look up, so they must be declared.

    Rules:
    - CARBOTTOM is in GLOBAL.TSH — skip it here.
    - Wheel textures (contain "WHL") need flag 't' (loaded from TEX16A/).
    - Everything else: standard body texture entry.
    """
    seen  = set()
    names = []

    def _add(n: str) -> None:
        n = n.upper().strip()
        if n and n != "CARBOTTOM" and n not in seen:
            seen.add(n)
            names.append(n)

    # 1. Blender scene materials
    for obj in car_objects:
        if obj.type != "MESH":
            continue
        for mat in obj.data.materials:
            if mat is not None:
                _add(mat.name)

    # 2. BMS files already in SHOP — main folder + _DASH subfolder
    for scan_dir in (
        Folder.Shop.Meshes / car_name,
        Folder.Shop.Meshes / f"{car_name}_DASH",
    ):
        if scan_dir.is_dir():
            for bms_file in scan_dir.glob("*.BMS"):
                try:
                    data = read_bms(bms_file)
                    for tex in data.get("texture_names", []):
                        _add(tex)
                except Exception:
                    pass

    mtl_dst = Folder.Shop.Material
    mtl_dst.mkdir(parents=True, exist_ok=True)
    tsh_path = mtl_dst / f"{car_name}{FileType.TEXTURE_SHEET}"

    lines = ["name,neighborhood,h,m,l,flags,alternate,sibling,xres,yres,hexcolor"]
    for n in sorted(names):
        is_wheel_tex = "WHL" in n
        flags = "td" if is_wheel_tex else "d"
        lines.append(f"{n},car,0,0,1,{flags},,,64,64,000000")

    tsh_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"[Car Editor] TSH written: {len(names)} texture(s) → {tsh_path.name}")


def _init_new_car_files(car_name: str, display_name: str = "Custom Car") -> list:
    """
    Populate SHOP subdirs with support files for a brand-new car name.

    Writes directly into the standard SHOP layout:
        SHOP/TUNE/  — physics (.MMCARSIM), wheel banger, .INFO
        SHOP/MTL/   — {NAME}.TSH (texture sheet)
        SHOP/BND/   — {NAME}_BND.BND (collision, copied from VPMUSTANG99)
        SHOP/BMS/{NAME}/ — lights, shadow (_H only)
        SHOP/TEX16A/ — wheel texture

    All source files come from resources/editor.
    Returns a list of human-readable result strings.
    """
    import shutil

    SOURCE   = "VPMUSTANG99"
    editor   = Folder.Resources.Editor
    msgs     = []

    # ── TUNE: physics (MMCARSIM) ──────────────────────────────────────────────
    tune_dst = Folder.Shop.Tune
    tune_dst.mkdir(parents=True, exist_ok=True)

    carsim_src = editor.Tune.CarSimulation / f"{SOURCE}.MMCARSIM"
    if carsim_src.exists():
        shutil.copy2(carsim_src, tune_dst / f"{car_name}.MMCARSIM")
        msgs.append(f"TUNE: copied {SOURCE}.MMCARSIM → {car_name}.MMCARSIM")
    else:
        msgs.append(f"TUNE: {SOURCE}.MMCARSIM not found in resources/editor, skipped")

    # ── TUNE: WHL0 banger data ────────────────────────────────────────────────
    # Verbatim copy — NodeName inside stays "vpmustang99_WHL0", only filename changes.
    banger_src = editor.Tune.BangerData / f"{SOURCE}_WHL0.MMBANGERDATA"
    if banger_src.exists():
        shutil.copy2(banger_src, tune_dst / f"{car_name}_WHL0.MMBANGERDATA")
        msgs.append("TUNE: WHL0 banger data copied from VPMUSTANG99 (verbatim)")
    else:
        msgs.append("TUNE: VPMUSTANG99_WHL0.MMBANGERDATA not found in resources/editor, skipped")

    # ── TUNE: .INFO — game discovers custom cars by scanning TUNE/ for *.INFO ─
    info_path = tune_dst / f"{car_name}.INFO"
    info_path.write_text(
        f"BaseName={car_name}\n"
        f"Description={display_name}\n"
        f"Colors=Red\n"
        f"Flags=0\n"
        f"Order=-1\n"
        f"ScoringBias=5.0\n"
        f"UnlockScore=0\n"
        f"UnlockFlags=0\n"
        f"Horsepower=320\n"
        f"Top Speed=200\n"
        f"Durability=500000\n"
        f"Mass=1500\n",
        encoding="ascii",
    )
    msgs.append(f"TUNE: generated .INFO — display name: '{display_name}'")

    # ── MTL: TSH ──────────────────────────────────────────────────────────────
    # CARBOTTOM is in GLOBAL.TSH — must NOT be duplicated here.
    # VPCOP_WHL needs flag 't' so the engine loads it from TEX16A/.
    mtl_dst = Folder.Shop.Material
    mtl_dst.mkdir(parents=True, exist_ok=True)
    tsh = mtl_dst / f"{car_name}{FileType.TEXTURE_SHEET}"
    tsh.write_text(
        "name,neighborhood,h,m,l,flags,alternate,sibling,xres,yres,hexcolor\n"
        "VPCOP_WHL,car,0,0,1,td,,,64,64,000000\n",
        encoding="ascii",
    )
    msgs.append("MTL: generated TSH (VPCOP_WHL wheel texture entry)")

    # ── BND: collision ────────────────────────────────────────────────────────
    bnd_dst = Folder.Shop.Bound
    bnd_dst.mkdir(parents=True, exist_ok=True)
    bnd_src = editor.Bound / f"{SOURCE}_BND.BND"
    if bnd_src.exists():
        shutil.copy2(bnd_src, bnd_dst / f"{car_name}_BND.BND")
        msgs.append("BND: copied VPMUSTANG99 collision")
    else:
        msgs.append("BND: VPMUSTANG99_BND.BND not found in resources/editor/BND, skipped")

    # ── DLP: wheel spin pivots ────────────────────────────────────────────────
    # The engine reads each wheel's Center from the DLP's WHLn_H group centroid.
    dlp_dst = Folder.Shop.DLP
    dlp_dst.mkdir(parents=True, exist_ok=True)
    dlp_src = editor.DLP / f"{SOURCE}{FileType.DEVELOPMENT}"
    if dlp_src.exists():
        shutil.copy2(dlp_src, dlp_dst / f"{car_name}{FileType.DEVELOPMENT}")
        msgs.append("DLP: copied VPMUSTANG99 wheel pivots")
    else:
        msgs.append("DLP: VPMUSTANG99.DLP not found in resources/editor/DLP, skipped")

    # ── BMS: lights + shadow reference files ─────────────────────────────────
    bms_src = editor.MeshesCars / SOURCE
    bms_dst = Folder.Shop.Meshes / car_name
    bms_dst.mkdir(parents=True, exist_ok=True)
    bms_n   = 0
    for fname in [
        "BLIGHT.BMS", "HLIGHT_H.BMS",
        "RLIGHT.BMS", "SHADOW_H.BMS",
        "SLIGHT0.BMS", "SLIGHT1.BMS", "TLIGHT.BMS",
    ]:
        src = bms_src / fname
        if src.exists():
            shutil.copy2(src, bms_dst / fname)
            bms_n += 1
    msgs.append(f"BMS: {bms_n} support files (lights + shadow _H) → SHOP/BMS/{car_name}")

    # ── BMS: dashboard sub-folder ─────────────────────────────────────────────
    # The game loads BMS/{NAME}_DASH/ separately; without overriding it the
    # original car AR's dash meshes stay active and reference car-specific
    # textures that aren't in our TSH, causing a fatal error on launch.
    dash_src = editor.MeshesCars / f"{SOURCE}_DASH"
    dash_dst = Folder.Shop.Meshes / f"{car_name}_DASH"
    if dash_src.is_dir():
        dash_dst.mkdir(parents=True, exist_ok=True)
        dash_n = 0
        for f in sorted(dash_src.iterdir()):
            if f.is_file() and f.suffix.upper() == ".BMS":
                shutil.copy2(f, dash_dst / f.name)
                dash_n += 1
        msgs.append(f"BMS: {dash_n} dashboard files → SHOP/BMS/{car_name}_DASH")
    else:
        msgs.append(f"BMS: {SOURCE}_DASH not found in resources/editor, skipped")

    # ── TEX16A: wheel texture ─────────────────────────────────────────────────
    tex16a_dst = Folder.Shop.Textures.Alpha
    tex16a_dst.mkdir(parents=True, exist_ok=True)
    whl_tex = editor.Textures / "VPCOP_WHL.DDS"
    if whl_tex.exists():
        shutil.copy2(whl_tex, tex16a_dst / "VPCOP_WHL.DDS")
        msgs.append("TEX16A: copied VPCOP_WHL.DDS wheel texture")
    else:
        msgs.append("TEX16A: VPCOP_WHL.DDS not found in resources/editor/TEXTURES, skipped")

    return msgs


class CAR_OT_InitNewCar(bpy.types.Operator):
    bl_idname  = "car.init_new_car"
    bl_label   = "Init Support Files"
    bl_description = (
        "Write TUNE, MTL, BND and BMS support files for a new car name into "
        "the standard SHOP/ subdirs, sourced from VPMUSTANG99 in core/. "
        "Run once per new car name before exporting BMS."
    )

    def execute(self, context):
        display_name = context.scene.ce_car_display_name.strip()
        car_name     = ("VP" + display_name.upper().replace(" ", "")) if display_name else ""
        if not car_name:
            self.report({"ERROR"}, "Menu Name is empty.")
            return {"CANCELLED"}

        msgs = _init_new_car_files(car_name, display_name)
        errors = [m for m in msgs if m.startswith("ERROR")]
        for m in msgs:
            print(f"[Car Init] {m}")
        if errors:
            self.report({"ERROR"}, errors[0])
        else:
            self.report({"INFO"}, f"Initialised {car_name} — {len(msgs)} files written to SHOP/.")

        return {"FINISHED"}


class CAR_OT_PackAndStartGame(bpy.types.Operator):
    bl_idname  = "car.pack_and_start_game"
    bl_label   = "Create AR + Start Game"
    bl_description = (
        "Export current car BMS to SHOP, pack !!!!!{car_name}.ar, then launch the game. "
        "Always launches — no running-check. One-click full workflow."
    )

    def execute(self, context):
        import subprocess
        from src.constants.misc import Executable

        car_objects = get_car_objects()
        body_obj    = get_car_body()
        if not car_objects or body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj["mm_car_name"])
        minimal  = _is_original_car(car_name)

        # Commit any pending Edit Mode changes
        active_obj = context.view_layer.objects.active
        was_edit   = active_obj is not None and active_obj.mode == "EDIT"
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")

        import shutil as _shutil

        # Export car parts to SHOP/BMS/{NAME}/ so the packer finds them.
        city_dir = Folder.Shop.Meshes / car_name

        # Minimal override (existing game car): wipe the SHOP BMS folder so stale
        # parts from earlier full exports don't leak into the AR, and skip wheels
        # — re-exporting them through the bake path can corrupt geometry, and the
        # original wheels already work in-game.
        if minimal and city_dir.exists():
            _shutil.rmtree(city_dir)
        city_dir.mkdir(parents=True, exist_ok=True)

        errors = []
        for obj in car_objects:
            part_tag = obj.get(_CAR_TAG, "unknown")
            if part_tag.startswith("wheel_"):
                # Wheels are never exported via the bake path (it corrupts the spin
                # pivot). Existing cars keep their originals from the base AR; new
                # cars get VPMUSTANG99's centered wheel BMS + DLP below.
                continue
            src_file = obj.data.get("bms_source_file", "")
            if src_file:
                out_name = Path(src_file).name
            elif part_tag == "body":
                out_name = "BODY_H.BMS"
            elif part_tag.startswith("wheel_"):
                idx = part_tag.split("_")[1]
                out_name = f"WHL{idx}_H.BMS"
            elif part_tag.startswith("fender_"):
                out_name = f"FNDR{part_tag.split('_')[1]}_H.BMS"
            else:
                out_name = f"{part_tag.upper()}.BMS"
            try:
                is_wheel = part_tag.startswith("wheel_")
                bms_data = mesh_to_bms_data(obj, bake_location=is_wheel)
                write_bms(bms_data, city_dir / out_name)
            except Exception as exc:
                errors.append(out_name)
                print(f"[Car Editor] Export failed for {out_name}: {exc}")

        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")

        if errors:
            self.report({"WARNING"}, f"BMS export errors ({len(errors)}): {errors[0]} — AR may be incomplete.")

        # The engine requires two additional body copies regardless of LOD policy:
        #   BODY_M.BMS — mmDamage::InitDamage reads Meshes[2] (medium slot);
        #                NULL there causes an unconditional Abortf (damage.c:14).
        #   H.BMS      — car selection menu renders this mesh; without it the
        #                car is invisible or absent in the vehicle picker.
        # Both are identical to the high-detail export — quality doesn't matter.
        body_h = city_dir / "BODY_H.BMS"
        if body_h.exists():
            for suffix in ("BODY_M.BMS", "BODY_L.BMS", "BODY_VL.BMS", "H.BMS"):
                _shutil.copy2(body_h, city_dir / suffix)

        if not minimal:
            # New car: build a self-contained AR from the VPMUSTANG99 template —
            # centered wheel BMS + matching DLP (so wheels spin on their axle),
            # dashboard, wheel LODs and a generated TSH that declares every
            # texture (the engine fatal-errors on any undeclared texture).
            #
            # STAGE 1 — CONFIRMED WORKING IN-GAME (2026-05-21): wheels spin on
            # their axles instead of orbiting the car centre. Pivot comes from the
            # DLP's WHLn_H centroid; mesh must be origin-centered. Limitation:
            # wheels are locked to VPMUSTANG99 positions. Stage 2 will generate a
            # per-car wheel DLP + export wheels centered for arbitrary placement.
            #
            # Drop any stale baked wheels first so _ensure_wheels_in_shop installs
            # the mustang centered wheels (verts at origin + hub mesh_offset).
            for stale in city_dir.glob("WHL*.BMS"):
                stale.unlink()
            _ensure_wheels_in_shop(car_name)
            _ensure_dash_in_shop(car_name)
            _ensure_dlp_in_shop(car_name)
            for i in range(10):
                whl_h = city_dir / f"WHL{i}_H.BMS"
                if not whl_h.exists():
                    break
                for suffix in (f"WHL{i}_M.BMS", f"WHL{i}_L.BMS", f"WHL{i}_VL.BMS"):
                    _shutil.copy2(whl_h, city_dir / suffix)
            _build_car_tsh(car_name, car_objects)

        if not _pack_car_ar(car_name, minimal=minimal):
            self.report({"ERROR"}, "AR packing failed — check the system console.")
            return {"CANCELLED"}

        exe = Folder.MidtownMadness.Root / Executable.MIDTOWN_MADNESS
        if not exe.exists():
            self.report({"ERROR"}, f"Executable not found: {exe}")
            return {"CANCELLED"}

        n_ok = len(car_objects) - len(errors)
        print(f"[Car Editor] Launching {exe} …")
        subprocess.Popen([str(exe)], cwd=str(Folder.MidtownMadness.Root))
        mode_msg = "minimal override" if minimal else "full"
        self.report({"INFO"}, f"Packed {car_name}.ar ({mode_msg}) — game launching.")
        return {"FINISHED"}


def is_car_obj(obj) -> bool:
    return obj is not None and obj.get(_CAR_TAG) is not None


def get_car_objects():
    return [o for o in bpy.data.objects if is_car_obj(o)]


def get_car_body() -> Optional[bpy.types.Object]:
    for o in get_car_objects():
        if o.get(_CAR_TAG) == "body":
            return o
    return None


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


# ── Operator: Load Car ────────────────────────────────────────────────────────

class CAR_OT_LoadCar(bpy.types.Operator):
    bl_idname   = "car.load_car"
    bl_label    = "Load Car"
    bl_description = (
        "Load a car from a BMS folder (body + wheels + fenders + lights). "
        "Clears any previously loaded car editor objects first."
    )

    # File browser writes the chosen directory here.
    directory: bpy.props.StringProperty(subtype="DIR_PATH", default="")

    def invoke(self, context, event):
        # Open MESHES/CARS so the user picks a car subfolder directly.
        meshes_cars = Folder.Resources.Editor.Meshes / "CARS"
        self.directory = str(meshes_cars) + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        car_folder = Path(self.directory.rstrip("/\\"))
        if not car_folder.is_dir():
            self.report({"ERROR"}, f"Folder not found: {car_folder}")
            return {"CANCELLED"}

        # Texture folder is always the editor TEXTURES folder
        tex_folder = Folder.Resources.Editor.Textures
        context.scene.ce_texture_folder = str(tex_folder)

        _clear_car_objects()
        col      = _get_or_create_collection(_CAR_COLLECTION)
        car_name = car_folder.name

        # ── Body ──────────────────────────────────────────────────────────────
        # TRAILER_H.BMS is tried last so that vehicles like VPSEMI_TRAILER
        # (which have no BODY_H.BMS) load correctly.
        body_mesh = None
        body_file = None
        for candidate in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS", "TRAILER_H.BMS"):
            f = car_folder / candidate
            if f.exists():
                body_mesh = _load_bms(f, car_name, tex_folder)
                body_file = candidate
                break

        if body_mesh is None:
            self.report({"ERROR"},
                        "No body BMS found (BODY_H.BMS / BODY_M.BMS / H.BMS / TRAILER_H.BMS)")
            return {"CANCELLED"}

        body_obj          = bpy.data.objects.new(car_name, body_mesh)
        col.objects.link(body_obj)
        body_obj.location = _bms_to_bl_offset(body_mesh)
        body_obj[_CAR_TAG]        = "body"
        body_obj["mm_car_folder"] = str(car_folder)
        body_obj["mm_car_name"]   = car_name
        body_obj["mm_body_file"]  = body_file or ""

        # ── Wheels (WHL0_H … WHL9_H) ─────────────────────────────────────────
        wheel_count = 0
        for i in range(10):
            f = car_folder / f"WHL{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms(f, f"{car_name}.WHL{i}", tex_folder)
            if mesh:
                _add_child_obj(mesh, mesh.name, f"wheel_{i}", body_obj, col)
                wheel_count += 1

        # ── Fenders (FNDR0_H … FNDR9_H) ──────────────────────────────────────
        fender_count = 0
        for i in range(10):
            f = car_folder / f"FNDR{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms(f, f"{car_name}.FNDR{i}", tex_folder)
            if mesh:
                _add_child_obj(mesh, mesh.name, f"fender_{i}", body_obj, col)
                fender_count += 1

        # ── Lights (optional, off by default) ────────────────────────────────
        light_count = 0
        if context.scene.ce_load_lights:
            _LIGHT_CANDIDATES = (
                "HLIGHT_H.BMS", "HLIGHT_M.BMS", "HLIGHT.BMS",   # headlights
                "TLIGHT_H.BMS", "TLIGHT_M.BMS", "TLIGHT.BMS",   # tail lights
                "RLIGHT_H.BMS", "RLIGHT.BMS",                    # reverse lights
                "BLIGHT_H.BMS", "BLIGHT.BMS",                    # brake lights
                "SLIGHT0.BMS",  "SLIGHT1.BMS",                   # side/signal lights
                "BLUELIGHT.BMS",                                  # police blue light
                "REDLIGHT.BMS",                                   # red light
            )
            found_any = False
            for candidate in _LIGHT_CANDIDATES:
                f = car_folder / candidate
                if not f.exists():
                    continue
                found_any = True
                mesh = _load_bms(f, f"{car_name}.{Path(candidate).stem}", tex_folder)
                if mesh:
                    _add_child_obj(mesh, mesh.name, f"light_{Path(candidate).stem}",
                                   body_obj, col)
                    light_count += 1
            if not found_any:
                print(f"[Car Editor] No light BMS files found in {car_folder} "
                      f"(checked: {', '.join(_LIGHT_CANDIDATES)})")

        # ── Trailer body (TRAILER_H.BMS) ──────────────────────────────────────
        # Skip if TRAILER_H.BMS was already loaded as the main body
        # (e.g. VPSEMI_TRAILER has no BODY_H.BMS — TRAILER_H.BMS IS the car).
        trailer_obj = None
        if body_file != "TRAILER_H.BMS":
            trailer_f = car_folder / "TRAILER_H.BMS"
            if trailer_f.exists():
                mesh = _load_bms(trailer_f, f"{car_name}.TRAILER", tex_folder)
                if mesh:
                    trailer_obj = _add_child_obj(mesh, mesh.name, "trailer", body_obj, col)

        # ── Trailer wheels (TWHL0_H … TWHL9_H) ───────────────────────────────
        # When TRAILER_H.BMS is the main body, TWHL wheels are its primary wheels
        # and get parented directly to body_obj (counted in wheel_count).
        trailer_wheel_parent = trailer_obj if trailer_obj else body_obj
        for i in range(10):
            f = car_folder / f"TWHL{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms(f, f"{car_name}.TWHL{i}", tex_folder)
            if mesh:
                if trailer_obj is None:
                    # TWHL wheels are the only wheels — count them as main wheels
                    _add_child_obj(mesh, mesh.name, f"wheel_{wheel_count}", body_obj, col)
                    wheel_count += 1
                else:
                    _add_child_obj(mesh, mesh.name, f"trailer_wheel_{i}",
                                   trailer_wheel_parent, col)

        # ── Persist folder paths in scene ─────────────────────────────────────
        context.scene.ce_car_folder = str(car_folder)

        # ── Select + frame body ───────────────────────────────────────────────
        bpy.ops.object.select_all(action="DESELECT")
        body_obj.select_set(True)
        context.view_layer.objects.active = body_obj
        try:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        except Exception:
            pass

        # Detect current paint variant and clear the variant cache for the new car
        _paint_variant_cache.clear()
        context.scene.ce_paint_variant  = _detect_paint_prefix(body_mesh)
        context.scene.ce_show_damage    = False  # reset damage toggle on load
        detected_whl_tex = _detect_wheel_texture(get_car_objects())
        if detected_whl_tex:
            context.scene.ce_wheel_texture = detected_whl_tex
            for obj in get_car_objects():
                tag = obj.get(_CAR_TAG, "")
                if tag.startswith("wheel_"):
                    obj["ce_wheel_tex"] = detected_whl_tex
                    try:
                        idx = int(tag.split("_")[1])
                        setattr(context.scene, f"ce_wheel_texture_{idx}", detected_whl_tex)
                    except (ValueError, IndexError, TypeError):
                        pass

        # Some BMS files load with one face already pointing at a _DMG material slot.
        # Toggling damage on then immediately off normalises all faces to clean textures.
        bpy.ops.car.toggle_damage("EXEC_DEFAULT")
        bpy.ops.car.toggle_damage("EXEC_DEFAULT")

        parts_msg = f"body + {wheel_count} wheels"
        if fender_count:
            parts_msg += f" + {fender_count} fenders"
        if light_count:
            parts_msg += f" + {light_count} lights"
        if trailer_obj:
            parts_msg += " + trailer"
        self.report({"INFO"}, f"Loaded {car_name}: {parts_msg}")
        return {"FINISHED"}


# ── Operator: Export Car ──────────────────────────────────────────────────────

class CAR_OT_ExportCar(bpy.types.Operator):
    bl_idname      = "car.export_car"
    bl_label       = "Export Car to BMS"
    bl_description = (
        "Export all loaded car parts back to BMS files. "
        "Output files are written to the Export Folder (scene property)."
    )

    def execute(self, context):
        scene       = context.scene
        car_objects = get_car_objects()
        if not car_objects:
            self.report({"ERROR"}, "No car parts loaded — use Load Car first.")
            return {"CANCELLED"}

        # Validate delete_shop when Add to City is requested
        if scene.ce_add_to_city:
            try:
                from src.USER.settings.main import delete_shop as _delete_shop
            except ImportError:
                _delete_shop = True
            if not _delete_shop:
                self.report(
                    {"ERROR"},
                    "Add to City requires 'delete_shop = True' in src/USER/settings/main.py. "
                    "Set it to True so the game picks up your car from the .AR file instead of raw shop files."
                )
                return {"CANCELLED"}

        body_obj = get_car_body()
        car_name = _base_car_name(body_obj["mm_car_name"] if body_obj else "CAR")

        # Commit any pending Edit Mode changes before reading mesh data.
        active_obj = context.view_layer.objects.active
        was_edit   = active_obj is not None and active_obj.mode == "EDIT"
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")

        # Timestamped export dir — timestamp generated fresh at export time
        export_dir = Folder.Blender.Export / "cars" / f"{car_name}_{_current_time_formatted()}"
        export_dir.mkdir(parents=True, exist_ok=True)
        scene.ce_last_export_dir = str(export_dir)

        # Add to City: SHOP/BMS/<car_name>/ — no timestamp, exact name required by game
        city_dir = None
        if scene.ce_add_to_city:
            city_dir = Folder.Shop.Meshes / car_name
            city_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        errors   = []

        for obj in car_objects:
            part_tag = obj.get(_CAR_TAG, "unknown")
            src_file = obj.data.get("bms_source_file", "")

            if src_file:
                out_name = Path(src_file).name
            elif part_tag == "body":
                out_name = "BODY_H.BMS"
            elif part_tag.startswith("wheel_"):
                idx = part_tag.split("_")[1]
                out_name = f"WHL{idx}_H.BMS"
            elif part_tag.startswith("fender_"):
                idx = part_tag.split("_")[1]
                out_name = f"FNDR{idx}_H.BMS"
            else:
                out_name = f"{part_tag.upper()}.BMS"

            try:
                is_wheel = part_tag.startswith("wheel_")
                bms_data = mesh_to_bms_data(obj, bake_location=is_wheel)
                write_bms(bms_data, export_dir / out_name)
                if city_dir:
                    write_bms(bms_data, city_dir / out_name)
                exported.append(out_name)
                print(f"[Car Editor] Exported: {export_dir / out_name}")
            except Exception as exc:
                errors.append(f"{out_name}: {exc}")
                print(f"[Car Editor] Export failed for {out_name}: {exc}")

        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")

        import shutil as _shutil
        for i in range(10):
            whl_h = export_dir / f"WHL{i}_H.BMS"
            if not whl_h.exists():
                break
            _shutil.copy2(whl_h, export_dir / f"WHL{i}_M.BMS")
            _shutil.copy2(whl_h, export_dir / f"WHL{i}_L.BMS")
            if city_dir:
                _shutil.copy2(whl_h, city_dir / f"WHL{i}_M.BMS")
                _shutil.copy2(whl_h, city_dir / f"WHL{i}_L.BMS")

        if errors:
            self.report({"WARNING"}, f"Exported {len(exported)}, {len(errors)} error(s): {errors[0]}")
        else:
            msg = f"Exported {len(exported)} BMS file(s) to {export_dir}"
            if city_dir:
                msg += f" + SHOP/BMS/{car_name}"
            self.report({"INFO"}, msg)

        if scene.ce_auto_reload and not errors:
            bpy.ops.car.reload_car("EXEC_DEFAULT")

        return {"FINISHED"}


# ── Operator: Reload (verify export) ─────────────────────────────────────────

class CAR_OT_ReloadCar(bpy.types.Operator):
    bl_idname      = "car.reload_car"
    bl_label       = "Reload Exported Car"
    bl_description = (
        "Reload the exported BMS files from the Export Folder for visual verification. "
        "Replaces the current car editor objects."
    )

    def execute(self, context):
        scene      = context.scene
        last_dir   = scene.ce_last_export_dir.strip()
        if not last_dir:
            self.report({"ERROR"}, "No export found yet — export first.")
            return {"CANCELLED"}
        export_dir = Path(last_dir)
        if not export_dir.is_dir():
            self.report({"ERROR"}, f"Export folder not found: {export_dir}")
            return {"CANCELLED"}

        # Verify that at least a body BMS exists before delegating to LoadCar
        # (LoadCar will error-cancel if the body is missing; surface that clearly).
        body_found = any((export_dir / name).exists()
                         for name in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS"))
        if not body_found:
            self.report({"ERROR"},
                        "No body BMS in export folder — body may have failed to export. "
                        "Check the system console for details.")
            return {"CANCELLED"}

        original_folder     = scene.ce_car_folder
        scene.ce_car_folder = str(export_dir)

        try:
            bpy.ops.car.load_car("EXEC_DEFAULT", directory=str(export_dir) + "/")
        except Exception as exc:
            scene.ce_car_folder = original_folder
            self.report({"ERROR"}, f"Reload failed: {exc}")
            return {"CANCELLED"}

        # Restore original source folder reference so the inspector still shows it.
        body_obj = get_car_body()
        if body_obj:
            body_obj["mm_car_folder"] = original_folder

        self.report({"INFO"}, f"Reloaded from {export_dir}")
        return {"FINISHED"}


# ── Operator: Clear Car ───────────────────────────────────────────────────────

class CAR_OT_ClearCar(bpy.types.Operator):
    bl_idname      = "car.clear_car"
    bl_label       = "Clear Car"
    bl_description = "Remove all Car Editor objects from the scene."

    def execute(self, context):
        _clear_car_objects()
        self.report({"INFO"}, "Car editor objects cleared.")
        return {"FINISHED"}


# ── Operator: Assign Texture to Selected Faces ────────────────────────────────

class CAR_OT_AssignTexture(bpy.types.Operator):
    bl_idname      = "car.assign_texture"
    bl_label       = "Assign Texture to Faces"
    bl_description = (
        "Assign the chosen texture slot index to all selected faces "
        "(Edit Mode).  Use the Face Texture Slot spinner in the panel."
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.mode != "EDIT":
            self.report({"WARNING"}, "Enter Edit Mode and select faces first.")
            return {"CANCELLED"}

        slot_idx = context.scene.ce_assign_slot
        if slot_idx >= len(obj.material_slots):
            self.report({"WARNING"}, f"Slot {slot_idx} does not exist on this mesh.")
            return {"CANCELLED"}

        # Assign material slot to selected faces via bmesh
        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        changed = 0
        for face in bm.faces:
            if face.select:
                face.material_index = slot_idx
                changed += 1
        bmesh.update_edit_mesh(obj.data)

        self.report({"INFO"}, f"Assigned slot {slot_idx} to {changed} face(s).")
        return {"FINISHED"}


# ── Operator: Browse Export Folder ────────────────────────────────────────────

class CAR_OT_BrowseExportFolder(bpy.types.Operator):
    bl_idname      = "car.browse_export_folder"
    bl_label       = "Browse Export Folder"
    bl_description = "Set the folder where exported BMS files are written."

    directory: bpy.props.StringProperty(subtype="DIR_PATH", default="")

    def invoke(self, context, event):
        if context.scene.ce_export_folder:
            self.directory = context.scene.ce_export_folder
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        context.scene.ce_export_folder = self.directory.rstrip("/\\")
        return {"FINISHED"}


# ── Operator: Cycle face selection ───────────────────────────────────────────

class CAR_OT_SelectFace(bpy.types.Operator):
    bl_idname      = "car.select_face"
    bl_label       = "Select Face"
    bl_description = "Select the next or previous face on the active car part"
    bl_options     = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        items=[("NEXT", "Next", ""), ("PREV", "Previous", "")],
        default="NEXT",
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        # Ensure Edit Mode + Face select
        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        n = len(bm.faces)
        if n == 0:
            return {"CANCELLED"}

        # Find currently active face index
        current = bm.faces.active.index if bm.faces.active else -1

        if self.direction == "NEXT":
            target = (current + 1) % n
        else:
            target = (current - 1) % n

        # Deselect all, select target
        for f in bm.faces:
            f.select = False
        bm.faces[target].select = True
        bm.faces.active = bm.faces[target]

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        context.scene.ce_active_face_index = target
        _read_back_face_uv(context.scene, obj, bm.faces[target])
        return {"FINISHED"}


# ── Operator: Apply UV tiling/rotation to selected faces ──────────────────────

class CAR_OT_ApplyFaceUV(bpy.types.Operator):
    bl_idname      = "car.apply_face_uv"
    bl_label       = "Apply UV to Selected Faces"
    bl_description = (
        "Apply Tile X/Y and Rotation to the UVs of all selected faces "
        "(Edit Mode). Each face is mapped independently from its corners."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.mode != "EDIT":
            self.report({"WARNING"}, "Enter Edit Mode and select faces first.")
            return {"CANCELLED"}

        scene = context.scene
        tile_x   = scene.ce_face_tile_x
        tile_y   = scene.ce_face_tile_y
        angle    = math.radians(scene.ce_face_rotation)
        cx, cy   = 0.5, 0.5

        def _rotated(bx, by):
            bx -= cx; by -= cy
            rx = bx * math.cos(angle) - by * math.sin(angle)
            ry = bx * math.sin(angle) + by * math.cos(angle)
            return ((rx + cx) * tile_x, 1.0 - (ry + cy) * tile_y)

        quad_uvs = [_rotated(x, y) for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]]
        tri_uvs  = [_rotated(x, y) for x, y in [(0, 0), (1, 0), (0.5, 1)]]

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.new("UVMap")

        changed = 0
        for face in bm.faces:
            if not face.select:
                continue
            loops = list(face.loops)
            uvs   = tri_uvs if len(loops) == 3 else quad_uvs
            for i, loop in enumerate(loops):
                loop[uv_layer].uv = uvs[i % len(uvs)]
            changed += 1

        bmesh.update_edit_mesh(obj.data)
        self.report({"INFO"}, f"Applied UV to {changed} face(s).")
        return {"FINISHED"}


# ── Operator: Add quad or triangle at 3D cursor ───────────────────────────────

class CAR_OT_AddFace(bpy.types.Operator):
    bl_idname      = "car.add_face"
    bl_label       = "Add Face at Cursor"
    bl_description = (
        "Add a quad or triangle at the 3D cursor position, parented to the "
        "active car part (Edit Mode). Assigns the current texture slot."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a car part first.")
            return {"CANCELLED"}

        was_object_mode = (obj.mode != "EDIT")
        if was_object_mode:
            bpy.ops.object.mode_set(mode="EDIT")

        scene  = context.scene
        size   = scene.ce_add_size
        shape  = scene.ce_add_shape
        half   = size * 0.5
        slot   = max(0, min(scene.ce_assign_slot, len(obj.data.materials) - 1))

        # Cursor in local object space
        cursor = context.scene.cursor.location
        local  = obj.matrix_world.inverted() @ cursor
        x, y, z = local.x, local.y, local.z

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.new("UVMap")

        if shape == "TRI":
            verts = [
                bm.verts.new((x - half, y - half, z)),
                bm.verts.new((x + half, y - half, z)),
                bm.verts.new((x,        y + half, z)),
            ]
            base_uvs = [(0, 0), (1, 0), (0.5, 1)]
        else:
            verts = [
                bm.verts.new((x - half, y - half, z)),
                bm.verts.new((x + half, y - half, z)),
                bm.verts.new((x + half, y + half, z)),
                bm.verts.new((x - half, y + half, z)),
            ]
            base_uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

        face = bm.faces.new(verts)
        face.material_index = slot
        for i, loop in enumerate(face.loops):
            u, v = base_uvs[i]
            loop[uv_layer].uv = (u, 1.0 - v)

        bm.verts.index_update()
        bmesh.update_edit_mesh(obj.data)
        self.report({"INFO"}, f"Added {shape} at cursor.")
        return {"FINISHED"}


# ── Operator: Add a texture slot (material) to the active car part ────────────

class CAR_OT_AddTextureSlot(bpy.types.Operator):
    bl_idname      = "car.add_texture_slot"
    bl_label       = "Add Texture Slot"
    bl_description = (
        "Add a new material/texture slot to the active car part. "
        "Enter the texture name (without .dds) in the field above."
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or not is_car_obj(obj):
            self.report({"WARNING"}, "Select a car part first.")
            return {"CANCELLED"}

        tex_name   = context.scene.ce_new_tex_name.strip()
        if not tex_name:
            self.report({"WARNING"}, "Enter a texture name in the field first.")
            return {"CANCELLED"}

        mesh = obj.data
        if any(m and m.name == tex_name for m in mesh.materials):
            self.report({"INFO"}, f"Slot '{tex_name}' already exists.")
            return {"FINISHED"}

        if tex_name in bpy.data.materials:
            mat = bpy.data.materials[tex_name]
        else:
            mat = bpy.data.materials.new(name=tex_name)
            tex_folder_str = context.scene.ce_texture_folder
            if tex_folder_str:
                tex_folder = Path(tex_folder_str)
                tex_path   = tex_folder / f"{tex_name}.dds"
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
        self.report({"INFO"}, f"Added slot [{len(mesh.materials)-1}] '{tex_name}'.")
        return {"FINISHED"}


# ── Operator: Switch paint variant ───────────────────────────────────────────

class CAR_OT_SetPaintVariant(bpy.types.Operator):
    bl_idname      = "car.set_paint_variant"
    bl_label       = "Set Paint Variant"
    bl_description = "Switch to a different car paint job / colour variant"

    variant: bpy.props.StringProperty(default="")

    def execute(self, context):
        scene          = context.scene
        car_objects    = get_car_objects()
        body_obj       = get_car_body()
        if not car_objects or not body_obj:
            self.report({"WARNING"}, "No car loaded.")
            return {"CANCELLED"}

        new_prefix     = self.variant
        current_prefix = scene.ce_paint_variant
        if not new_prefix or new_prefix == current_prefix:
            return {"FINISHED"}

        tex_folder = (Path(scene.ce_texture_folder)
                      if scene.ce_texture_folder else Folder.Resources.Editor.Textures)

        swapped = _apply_paint_variant(car_objects, new_prefix, current_prefix, tex_folder)
        if swapped:
            scene.ce_paint_variant = new_prefix
            self.report({"INFO"}, f"Paint → {new_prefix}  ({swapped} slot(s) swapped).")
        else:
            self.report({"WARNING"}, f"No matching DDS textures found for '{new_prefix}'.")
        return {"FINISHED"}


# ── Damage toggle helpers ─────────────────────────────────────────────────────

def _build_damage_remap(mesh) -> dict:
    """Return {normal_slot_idx: dmg_slot_idx} for materials that have a _DMG counterpart."""
    name_to_idx = {mat.name: i for i, mat in enumerate(mesh.materials) if mat}
    return {
        i: name_to_idx[mat.name + "_DMG"]
        for i, mat in enumerate(mesh.materials)
        if mat and not mat.name.endswith("_DMG") and (mat.name + "_DMG") in name_to_idx
    }


# ── Operator: Toggle Damage View ──────────────────────────────────────────────

class CAR_OT_ToggleDamage(bpy.types.Operator):
    bl_idname      = "car.toggle_damage"
    bl_label       = "Toggle Damage"
    bl_description = (
        "Switch between normal and damaged appearance by remapping face material slots "
        "to their _DMG counterparts (already embedded in the BMS). "
        "Only VP player cars include _DMG texture variants."
    )

    def execute(self, context):
        scene       = context.scene
        car_objects = get_car_objects()
        if not car_objects:
            self.report({"WARNING"}, "No car loaded.")
            return {"CANCELLED"}

        going_to_damage  = not scene.ce_show_damage
        seen_meshes      = set()
        total_faces      = 0
        any_dmg_found    = False

        for obj in car_objects:
            if obj.type != "MESH":
                continue
            mesh = obj.data
            if id(mesh) in seen_meshes:
                continue
            seen_meshes.add(id(mesh))

            fwd = _build_damage_remap(mesh)
            if not fwd:
                continue
            any_dmg_found = True

            remap = fwd if going_to_damage else {v: k for k, v in fwd.items()}

            for poly in mesh.polygons:
                new_idx = remap.get(poly.material_index)
                if new_idx is not None:
                    poly.material_index = new_idx
                    total_faces += 1

            mesh.update()

        if not any_dmg_found:
            self.report({"INFO"}, "No _DMG material slots found — this car has no damage variants.")
            return {"CANCELLED"}

        scene.ce_show_damage = going_to_damage
        label = "damage" if going_to_damage else "normal"
        self.report({"INFO"}, f"Damage view {'ON' if going_to_damage else 'OFF'} — {total_faces} faces remapped.")
        return {"FINISHED"}


# ── Operator: Remove Wheel ────────────────────────────────────────────────────

class CAR_OT_RemoveWheel(bpy.types.Operator):
    bl_idname      = "car.remove_wheel"
    bl_label       = "Remove Selected Wheel"
    bl_description = (
        "Delete the currently active wheel object. "
        "Remaining wheels keep their indices — re-index with 'Renumber Wheels' if needed."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or not is_car_obj(obj):
            self.report({"WARNING"}, "Select a car wheel first.")
            return {"CANCELLED"}

        tag = obj.get(_CAR_TAG, "")
        if not tag.startswith("wheel_"):
            self.report({"WARNING"},
                        f"Active object is '{tag}', not a wheel. Select a wheel part.")
            return {"CANCELLED"}

        name = obj.name
        bpy.data.objects.remove(obj, do_unlink=True)
        self.report({"INFO"}, f"Removed {name}.")
        return {"FINISHED"}


# ── Operator: Renumber Wheels ─────────────────────────────────────────────────

class CAR_OT_RenumberWheels(bpy.types.Operator):
    bl_idname      = "car.renumber_wheels"
    bl_label       = "Renumber Wheels"
    bl_description = (
        "Re-index all wheel_N tags to a continuous 0-based sequence "
        "so WHL0_H … WHLM_H are exported without gaps."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_objs = get_car_objects()
        wheels = sorted(
            [o for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_")],
            key=lambda o: int(o.get(_CAR_TAG, "wheel_0").split("_")[1])
        )
        if not wheels:
            self.report({"WARNING"}, "No wheels found.")
            return {"CANCELLED"}

        body_obj = get_car_body()
        car_name = body_obj.get("mm_car_name", "CAR") if body_obj else "CAR"

        for new_i, whl_obj in enumerate(wheels):
            whl_obj[_CAR_TAG] = f"wheel_{new_i}"
            whl_obj.name      = f"{car_name}.WHL{new_i}"

        self.report({"INFO"}, f"Renumbered {len(wheels)} wheels (0 … {len(wheels)-1}).")
        return {"FINISHED"}


# ── Operator: Open Export Folder in Explorer ──────────────────────────────────

class CAR_OT_OpenExportFolder(bpy.types.Operator):
    bl_idname      = "car.open_export_folder"
    bl_label       = "Open Export Folder"
    bl_description = "Open the last export folder in Windows Explorer"

    def execute(self, context):
        import subprocess
        last_dir = context.scene.ce_last_export_dir.strip()
        if not last_dir:
            self.report({"WARNING"}, "No export folder yet.")
            return {"CANCELLED"}
        from pathlib import Path
        p = Path(last_dir)
        if not p.exists():
            self.report({"WARNING"}, f"Folder not found: {p}")
            return {"CANCELLED"}
        subprocess.Popen(["explorer", str(p)])
        return {"FINISHED"}


# ── Operator: Clear Shop BMS folder ──────────────────────────────────────────

class CAR_OT_ClearShop(bpy.types.Operator):
    bl_idname      = "car.clear_shop"
    bl_label       = "Clear Shop"
    bl_description = (
        "Delete all files in SHOP/BMS/{car_name}/ for the currently loaded car. "
        "Use this before re-exporting to avoid stale LOD or light files being packed."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        import shutil
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}
        car_name = _base_car_name(body_obj.get("mm_car_name", ""))
        shop_dir = Folder.Shop.Meshes / car_name
        if not shop_dir.exists():
            self.report({"INFO"}, f"SHOP/BMS/{car_name}/ does not exist, nothing to clear.")
            return {"FINISHED"}
        n = sum(1 for f in shop_dir.iterdir() if f.is_file())
        shutil.rmtree(shop_dir)
        shop_dir.mkdir()
        self.report({"INFO"}, f"Cleared {n} file(s) from SHOP/BMS/{car_name}/.")
        return {"FINISHED"}


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


def _mirror_wheel_mesh(src_mesh: bpy.types.Mesh, new_name: str) -> bpy.types.Mesh:
    """
    Return a copy of src_mesh mirrored across local X — negates X on every
    vertex and flips face winding so outward normals stay outward.
    Preserves UVs, material slots, and the custom BMS properties.
    """
    new_mesh = src_mesh.copy()
    new_mesh.name = new_name

    bm = bmesh.new()
    bm.from_mesh(new_mesh)
    for v in bm.verts:
        v.co.x = -v.co.x
    for f in bm.faces:
        f.normal_flip()
    bm.normal_update()
    bm.to_mesh(new_mesh)
    bm.free()

    mo = list(new_mesh.get("mesh_offset", [0.0, 0.0, 0.0]))
    mo[0] = -mo[0]
    new_mesh["mesh_offset"] = mo
    new_mesh["bms_source_file"] = ""   # forces export to use part-tag fallback
    return new_mesh


# ── Operator: New Car From Template ──────────────────────────────────────────

class CAR_OT_NewFromTemplate(bpy.types.Operator):
    bl_idname      = "car.new_from_template"
    bl_label       = "New Car From Template"
    bl_description = (
        "Create a fresh primitive car (box body + N wheels) from an archetype "
        "template. Clears any car currently loaded."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene       = context.scene
        template_id = scene.ce_template
        if template_id not in car_templates.TEMPLATES:
            self.report({"ERROR"}, f"Unknown template: {template_id}")
            return {"CANCELLED"}

        # Derive filename from the menu name; fall back to template default.
        display_name = (scene.ce_car_display_name or "").strip()
        if display_name:
            car_name = "VP" + display_name.upper().replace(" ", "")
        else:
            car_name = car_templates.get_template_default_name(template_id)

        _clear_car_objects()
        col = _get_or_create_collection(_CAR_COLLECTION)

        # ── Body ──────────────────────────────────────────────────────────────
        body_file  = car_templates.template_body_filename(template_id)
        tex_folder = Folder.Resources.Editor.Textures
        body_tex   = "CARBOTTOM"

        body_mesh = car_templates.build_body_mesh(car_name, template_id)
        body_mesh["texture_names"]   = [body_tex]
        body_mesh["bms_source_file"] = body_file
        body_mesh.materials[0] = _build_material(body_tex, tex_folder)

        body_obj = bpy.data.objects.new(car_name, body_mesh)
        col.objects.link(body_obj)
        body_obj.location          = _bms_to_bl_offset(body_mesh)
        body_obj[_CAR_TAG]         = "body"
        body_obj["mm_car_folder"]  = ""
        body_obj["mm_car_name"]    = car_name
        body_obj["mm_body_file"]   = body_file

        # ── Wheels — load from VPMUSTANG99 BMS (real geometry + VPCOP_WHL tex) ──
        wheel_positions = car_templates.template_wheel_positions(template_id)
        wheel_prefix    = car_templates.template_wheel_filename_prefix(template_id)
        vpmustang_folder = Folder.Resources.Editor.Meshes / "CARS" / "VPMUSTANG99"

        for i, wpos in enumerate(wheel_positions):
            mesh_name = f"{car_name}.{wheel_prefix}{i}"
            whl_bms   = vpmustang_folder / f"WHL{i}_H.BMS"
            w_mesh    = _load_bms(whl_bms, mesh_name, tex_folder) if whl_bms.exists() else None
            if w_mesh is None:
                wdata      = car_templates._T[template_id]["wheels"][i]
                w_mesh = car_templates.build_wheel_mesh(
                    mesh_name, wdata[3], wdata[4], mirror=(wpos[0] > 0))
                w_mesh.materials[0] = _build_material("VPCOP_WHL", tex_folder)
            w_mesh["mesh_offset"]     = list(wpos)
            w_mesh["bms_source_file"] = f"{wheel_prefix}{i}_H.BMS"
            _add_child_obj(w_mesh, mesh_name, f"wheel_{i}", body_obj, col)

        scene.ce_car_folder = ""

        bpy.ops.object.select_all(action="DESELECT")
        body_obj.select_set(True)
        context.view_layer.objects.active = body_obj
        try:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        except Exception:
            pass

        _paint_variant_cache.clear()
        scene.ce_paint_variant = car_name
        scene.ce_show_damage   = False

        n_wheels = len(wheel_positions)
        self.report({"INFO"},
                    f"Created {car_name}: {car_templates.TEMPLATES[template_id]['label']} "
                    f"(box body + {n_wheels} wheels).")
        return {"FINISHED"}


# ── Operator: Mirror Selected Wheel ──────────────────────────────────────────

class CAR_OT_MirrorWheel(bpy.types.Operator):
    bl_idname      = "car.mirror_wheel"
    bl_label       = "Mirror Selected Wheel"
    bl_description = (
        "Duplicate the active wheel mirrored across the car's X axis "
        "(same axle, opposite side). New wheel is assigned the next free index."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        obj = context.active_object
        if obj is None or not is_car_obj(obj):
            self.report({"WARNING"}, "Select a wheel first.")
            return {"CANCELLED"}
        tag = obj.get(_CAR_TAG, "")
        if not tag.startswith("wheel_"):
            self.report({"WARNING"}, f"Active object is '{tag}', not a wheel.")
            return {"CANCELLED"}

        wheel_indices = [
            int(o.get(_CAR_TAG, "wheel_0").split("_")[1])
            for o in get_car_objects()
            if o.get(_CAR_TAG, "").startswith("wheel_")
        ]
        new_idx  = max(wheel_indices) + 1 if wheel_indices else 0
        car_name = body_obj.get("mm_car_name", "CAR")

        new_mesh = _mirror_wheel_mesh(obj.data, f"{car_name}.WHL{new_idx}")

        col     = _get_or_create_collection(_CAR_COLLECTION)
        new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", new_mesh)
        col.objects.link(new_obj)
        new_obj.parent                = body_obj
        new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        new_obj[_CAR_TAG]             = f"wheel_{new_idx}"

        # Blender X = -game X — flipping Blender X mirrors the wheel in game space too.
        loc = obj.location
        new_obj.location = (-loc.x, loc.y, loc.z)

        bpy.ops.object.select_all(action="DESELECT")
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        self.report({"INFO"}, f"Mirrored {tag} → wheel_{new_idx}.")
        return {"FINISHED"}


# ── Operator: Mirror All Wheels (auto-symmetry) ──────────────────────────────

class CAR_OT_MirrorAllWheels(bpy.types.Operator):
    bl_idname      = "car.mirror_all_wheels"
    bl_label       = "Mirror All Wheels"
    bl_description = (
        "For every existing wheel, create its X-axis mirror unless a wheel "
        "already sits near that mirrored position (tolerance 0.05 m)."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        car_objs = get_car_objects()
        wheels   = [o for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_")]
        if not wheels:
            self.report({"WARNING"}, "No wheels to mirror.")
            return {"CANCELLED"}

        TOL      = 0.05
        car_name = body_obj.get("mm_car_name", "CAR")
        col      = _get_or_create_collection(_CAR_COLLECTION)
        next_idx = max(int(o.get(_CAR_TAG, "wheel_0").split("_")[1]) for o in wheels) + 1

        # Snapshot positions BEFORE we add anything, so newly-added mirrors
        # don't shadow further mirror checks.
        snapshot = [(o, o.location.copy()) for o in wheels]
        created  = 0

        for src_obj, src_loc in snapshot:
            mirror_loc = mathutils.Vector((-src_loc.x, src_loc.y, src_loc.z))
            if any((p - mirror_loc).length < TOL for _, p in snapshot):
                continue  # there's already a wheel at the mirrored spot
            new_mesh = _mirror_wheel_mesh(src_obj.data, f"{car_name}.WHL{next_idx}")
            new_obj  = bpy.data.objects.new(f"{car_name}.WHL{next_idx}", new_mesh)
            col.objects.link(new_obj)
            new_obj.parent                = body_obj
            new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
            new_obj[_CAR_TAG]             = f"wheel_{next_idx}"
            new_obj.location              = mirror_loc
            snapshot.append((new_obj, mirror_loc))
            next_idx += 1
            created  += 1

        if created == 0:
            self.report({"INFO"}, "All wheels already have their mirror partner.")
        else:
            self.report({"INFO"}, f"Mirrored {created} wheel(s).")
        return {"FINISHED"}


# ── Operator: Toggle X Symmetry for Edit Mode ────────────────────────────────

class CAR_OT_ToggleSymmetry(bpy.types.Operator):
    bl_idname      = "car.toggle_symmetry"
    bl_label       = "Toggle X Symmetry"
    bl_description = (
        "Toggle Blender's Edit-Mode X-mirror on every car part. "
        "When ON, vertex/edge/face edits are mirrored across the part's local X axis."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_objs = get_car_objects()
        if not car_objs:
            self.report({"WARNING"}, "No car loaded.")
            return {"CANCELLED"}

        new_val = not context.scene.ce_mirror_x
        for o in car_objs:
            if o.type == "MESH" and o.data is not None:
                o.data.use_mirror_x = new_val
        context.scene.ce_mirror_x = new_val
        self.report({"INFO"}, f"X Symmetry {'ON' if new_val else 'OFF'} for {len(car_objs)} part(s).")
        return {"FINISHED"}


# ── Operator: Apply Wheel Texture ─────────────────────────────────────────────

def _apply_wheel_tex(tex_name: str, wheels: list, tex_folder: Path) -> int:
    """Apply tex_name to all meshes in wheels list. Returns count of meshes changed."""
    seen    = set()
    swapped = 0
    new_mat = _build_material(tex_name, tex_folder)
    for whl in wheels:
        mesh = whl.data
        if id(mesh) in seen:
            continue
        seen.add(id(mesh))
        for i in range(len(mesh.materials)):
            mesh.materials[i] = new_mat
        swapped += 1
    return swapped


class CAR_OT_ApplyWheelTexture(bpy.types.Operator):
    """Apply the scene-level wheel texture to ALL wheels at once."""
    bl_idname      = "car.apply_wheel_texture"
    bl_label       = "Apply to All Wheels"
    bl_description = "Apply the selected texture to every wheel"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene    = context.scene
        tex_name = scene.ce_wheel_texture
        if not tex_name:
            self.report({"WARNING"}, "No wheel texture selected.")
            return {"CANCELLED"}
        wheels = [o for o in get_car_objects() if o.get(_CAR_TAG, "").startswith("wheel_")]
        if not wheels:
            self.report({"WARNING"}, "No wheels loaded.")
            return {"CANCELLED"}
        tex_folder = (Path(scene.ce_texture_folder)
                      if scene.ce_texture_folder else Folder.Resources.Editor.Textures)
        n = _apply_wheel_tex(tex_name, wheels, tex_folder)
        for whl in wheels:
            whl["ce_wheel_tex"] = tex_name
        self.report({"INFO"}, f"Applied {tex_name} to {n} wheel(s).")
        return {"FINISHED"}


class CAR_OT_ApplyWheelTextureSingle(bpy.types.Operator):
    """Apply a texture to one specific wheel by part tag."""
    bl_idname      = "car.apply_wheel_texture_single"
    bl_label       = "Apply Wheel Texture"
    bl_description = "Apply this texture to this wheel"
    bl_options     = {"REGISTER", "UNDO"}

    part_tag : bpy.props.StringProperty()
    tex_name : bpy.props.StringProperty()

    def execute(self, context):
        if not self.tex_name:
            return {"CANCELLED"}
        wheels = [o for o in get_car_objects() if o.get(_CAR_TAG) == self.part_tag]
        if not wheels:
            return {"CANCELLED"}
        scene      = context.scene
        tex_folder = (Path(scene.ce_texture_folder)
                      if scene.ce_texture_folder else Folder.Resources.Editor.Textures)
        _apply_wheel_tex(self.tex_name, wheels, tex_folder)
        # Store choice on the object so the panel can reflect it
        wheels[0]["ce_wheel_tex"] = self.tex_name
        return {"FINISHED"}


# ── Import helpers ────────────────────────────────────────────────────────────

def _tag_as_body(obj, car_name: str) -> None:
    obj[_CAR_TAG]         = "body"
    obj["mm_car_name"]    = car_name
    obj["mm_car_folder"]  = ""
    obj["mm_body_file"]   = "BODY_H.BMS"
    col = _get_or_create_collection(_CAR_COLLECTION)
    if obj.name not in col.objects:
        col.objects.link(obj)


def _tag_as_wheel(obj, idx: int, car_name: str) -> None:
    obj[_CAR_TAG] = f"wheel_{idx}"
    body = get_car_body()
    if body:
        obj.parent = body
        obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    col = _get_or_create_collection(_CAR_COLLECTION)
    if obj.name not in col.objects:
        col.objects.link(obj)


def _derive_car_name(scene) -> str:
    display = (scene.ce_car_display_name or "").strip()
    return ("VP" + display.upper().replace(" ", "")) if display else ""


def _clean_mat_name(name: str) -> str:
    """Strip path/extension noise from an imported material name."""
    import re
    # Remove numeric duplicate suffixes (.001, .002 …)
    name = re.sub(r'\.\d{3}$', '', name)
    # Remove trailing _Mat / _Material / _mat suffixes
    name = re.sub(r'(?i)[_\s]?mat(erial)?$', '', name)
    # Keep only ASCII uppercase alphanum + underscore
    name = re.sub(r'[^A-Za-z0-9_]', '_', name).upper()
    name = re.sub(r'_+', '_', name).strip('_')

    # Generic DCC / importer placeholder names that have no game equivalent
    _GENERIC = {
        "MAT", "MAT_BODY", "MAT_BODY_1", "MAT_WHEELS", "MAT_GLASS",
        "MATERIAL", "DEFAULT", "DEFAULTMAT", "LAMBERT", "LAMBERT1",
        "INITIALSHADINGGROUP", "STANDARDSURFACE", "BLINN", "PHONG",
        "DIFFUSE", "UNTITLED", "NONE", "NULL",
    }
    if name in _GENERIC or name.startswith("MAT_") or name.startswith("LAMBERT"):
        return "CARBOTTOM"
    return name or "CARBOTTOM"


class CAR_OT_ImportTagBody(bpy.types.Operator):
    bl_idname      = "car.import_tag_body"
    bl_label       = "Tag as Body"
    bl_description = "Tag the active mesh as the car body and add it to the Car Editor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj      = context.active_object
        car_name = _derive_car_name(context.scene)
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first.")
            return {"CANCELLED"}
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}
        _tag_as_body(obj, car_name)
        context.scene.ce_paint_variant = car_name
        self.report({"INFO"}, f"Tagged '{obj.name}' as body → {car_name}")
        return {"FINISHED"}


class CAR_OT_ImportTagWheel(bpy.types.Operator):
    bl_idname      = "car.import_tag_wheel"
    bl_label       = "Tag as Wheel"
    bl_description = "Tag the active mesh as the next free wheel"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj      = context.active_object
        car_name = _derive_car_name(context.scene)
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first.")
            return {"CANCELLED"}
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}
        existing = [o for o in get_car_objects() if o.get(_CAR_TAG, "").startswith("wheel_")]
        idx = max((int(o.get(_CAR_TAG).split("_")[1]) for o in existing), default=-1) + 1
        _tag_as_wheel(obj, idx, car_name)
        self.report({"INFO"}, f"Tagged '{obj.name}' as wheel_{idx}")
        return {"FINISHED"}


class CAR_OT_ImportAutoTag(bpy.types.Operator):
    bl_idname      = "car.import_auto_tag"
    bl_label       = "Auto-Tag Scene"
    bl_description = (
        "Heuristic: largest mesh by face count → body; "
        "meshes whose bounding box is roughly as wide as tall → wheels. "
        "Works best when all body/wheel objects are selected."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_name = _derive_car_name(context.scene)
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}

        candidates = [o for o in context.selected_objects if o.type == "MESH"]
        if not candidates:
            self.report({"WARNING"}, "Select the imported mesh objects first.")
            return {"CANCELLED"}

        # Largest by face count → body
        body_obj = max(candidates, key=lambda o: len(o.data.polygons))
        _tag_as_body(body_obj, car_name)
        context.scene.ce_paint_variant = car_name
        tagged_wheels = 0

        for o in candidates:
            if o is body_obj:
                continue
            # Wheel heuristic: bounding box roughly circular in XZ and small
            bb   = o.bound_box  # 8 corners in local space
            xs   = [v[0] for v in bb]
            ys   = [v[1] for v in bb]
            zs   = [v[2] for v in bb]
            w    = max(xs) - min(xs)
            h    = max(ys) - min(ys)
            d    = max(zs) - min(zs)
            size = max(w, h, d)
            # Wheel: roughly square cross-section, smaller than body
            if size < (max(body_obj.dimensions) * 0.5) and abs(w - d) < size * 0.6:
                _tag_as_wheel(o, tagged_wheels, car_name)
                tagged_wheels += 1

        context.scene.ce_paint_variant = car_name
        self.report({"INFO"},
                    f"Auto-tagged: 1 body ({body_obj.name}) + {tagged_wheels} wheel(s) → {car_name}")
        return {"FINISHED"}


class CAR_OT_ImportDecimate(bpy.types.Operator):
    bl_idname      = "car.import_decimate"
    bl_label       = "Decimate Active"
    bl_description = "Apply a Decimate modifier to the active mesh to reduce face count for MM1 compatibility"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh first.")
            return {"CANCELLED"}
        ratio    = context.scene.ce_import_decimate_ratio
        n_before = len(obj.data.polygons)
        mod      = obj.modifiers.new(name="MM1_Decimate", type="DECIMATE")
        mod.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)
        n_after = len(obj.data.polygons)
        self.report({"INFO"}, f"Decimated '{obj.name}': {n_before} → {n_after} faces")
        return {"FINISHED"}


class CAR_OT_ImportCleanMaterials(bpy.types.Operator):
    bl_idname      = "car.import_clean_materials"
    bl_label       = "Clean Material Names"
    bl_description = (
        "Rename all material slots on the active object to game-safe names "
        "(uppercase, ASCII only). Unnamed/noisy slots → CARBOTTOM."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh first.")
            return {"CANCELLED"}
        renamed = 0
        for mat in obj.data.materials:
            if mat is None:
                continue
            clean = _clean_mat_name(mat.name)
            if clean != mat.name:
                mat.name = clean
                renamed += 1
        self.report({"INFO"}, f"Cleaned {renamed} material name(s) on '{obj.name}'.")
        return {"FINISHED"}


class CAR_OT_ImportFlattenMaterials(bpy.types.Operator):
    bl_idname      = "car.import_flatten_materials"
    bl_label       = "Flatten All to CARBOTTOM"
    bl_description = (
        "Replace every material slot on every tagged car object with a single "
        "CARBOTTOM entry. Use this when you just want the car to load without "
        "texture errors — CARBOTTOM is always available in GLOBAL.TSH."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_objs = get_car_objects()
        if not car_objs:
            self.report({"WARNING"}, "No tagged car objects found.")
            return {"CANCELLED"}

        # Get or create a shared CARBOTTOM material
        mat = bpy.data.materials.get("CARBOTTOM")
        if mat is None:
            mat = bpy.data.materials.new("CARBOTTOM")

        changed = 0
        for obj in car_objs:
            if obj.type != "MESH":
                continue
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            # Assign all faces to slot 0
            for poly in obj.data.polygons:
                poly.material_index = 0
            changed += 1

        self.report({"INFO"}, f"Set CARBOTTOM on {changed} car object(s).")
        return {"FINISHED"}


class CAR_OT_ImportApplyTransforms(bpy.types.Operator):
    bl_idname      = "car.import_apply_transforms"
    bl_label       = "Apply Scale & Rotation"
    bl_description = (
        "Apply scale and rotation transforms on all selected objects. "
        "Run this after importing a .dae/.fbx to bake the 100× scale and "
        "Y-up rotation into vertex data so the BMS export is correct."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        targets = [o for o in context.selected_objects if o.type == "MESH"]
        if not targets:
            self.report({"WARNING"}, "Select at least one mesh object first.")
            return {"CANCELLED"}
        # Apply scale+rotation directly via bmesh — no viewport operator needed.
        for obj in targets:
            mat = obj.matrix_basis
            # Strip translation so we only bake scale+rotation into verts
            import mathutils as _mu
            mat_sr = mat.copy()
            mat_sr.translation = _mu.Vector((0, 0, 0))
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.transform(bm, matrix=mat_sr, verts=bm.verts)
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
            # Reset scale+rotation to identity, keep location
            obj.scale    = (1.0, 1.0, 1.0)
            obj.rotation_euler = (0.0, 0.0, 0.0)
        self.report({"INFO"}, f"Applied scale & rotation on {len(targets)} object(s).")
        return {"FINISHED"}


class CAR_OT_SpawnWheelFromTemplate(bpy.types.Operator):
    bl_idname      = "car.spawn_wheel_from_template"
    bl_label       = "Spawn Wheel from Template"
    bl_description = (
        "Load a VPMUSTANG99 reference wheel (WHL0_H.BMS) from resources/editor "
        "and add it as the next free wheel on the current car. "
        "Position it with the 3D cursor or move it after spawning."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car body loaded — tag a body first.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj.get("mm_car_name", "CAR"))

        # Find next free wheel index
        car_objs  = get_car_objects()
        used_idxs = set()
        for o in car_objs:
            tag = o.get(_CAR_TAG, "")
            if tag.startswith("wheel_"):
                try:
                    used_idxs.add(int(tag.split("_")[1]))
                except ValueError:
                    pass
        new_idx = next(i for i in range(20) if i not in used_idxs)

        # Load WHL0_H.BMS from resources/editor as a Blender mesh
        src_dir = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99"
        whl_bms = src_dir / "WHL0_H.BMS"
        if not whl_bms.exists():
            self.report({"ERROR"}, f"Template wheel not found: {whl_bms}")
            return {"CANCELLED"}

        mesh = _load_bms(whl_bms, f"{car_name}.WHL{new_idx}", Folder.Resources.Editor.Textures)
        if mesh is None:
            self.report({"ERROR"}, f"Failed to load template wheel: {whl_bms.name}")
            return {"CANCELLED"}

        mesh["bms_source_file"] = ""  # will export as WHL{new_idx}_H.BMS

        col     = _get_or_create_collection(_CAR_COLLECTION)
        new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", mesh)
        col.objects.link(new_obj)

        new_obj[_CAR_TAG] = f"wheel_{new_idx}"
        new_obj.parent    = body_obj
        # Identity parent-inverse → location is in body-local space.
        # Place wheel at the 3D cursor converted to body-local space.
        new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        cursor_world = context.scene.cursor.location.copy()
        new_obj.location = body_obj.matrix_world.inverted() @ cursor_world

        for o in context.view_layer.objects:
            o.select_set(False)
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        self.report({"INFO"},
                    f"Spawned wheel_{new_idx} from VPMUSTANG99 template. "
                    "Move it to the desired position.")
        return {"FINISHED"}


# ── Operator: Prepare Imported Model (mega-button) ───────────────────────────

class CAR_OT_ImportPrepare(bpy.types.Operator):
    bl_idname      = "car.import_prepare"
    bl_label       = "Prepare Imported Model"
    bl_description = (
        "One-click import prep: auto-tags the selected objects (body + wheels), "
        "flattens all materials to CARBOTTOM, and initialises support files "
        "(TUNE/.INFO/.MMCARSIM/BND). Requires Menu Name to be set."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene    = context.scene
        car_name = _derive_car_name(scene)
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}

        candidates = [o for o in context.selected_objects if o.type == "MESH"]
        if not candidates:
            self.report({"WARNING"}, "Select the imported mesh objects first.")
            return {"CANCELLED"}

        # 1. Auto-tag
        body_obj = max(candidates, key=lambda o: len(o.data.polygons))
        _tag_as_body(body_obj, car_name)
        scene.ce_paint_variant = car_name
        tagged_wheels = 0
        for o in candidates:
            if o is body_obj:
                continue
            bb  = o.bound_box
            xs  = [v[0] for v in bb]; ys = [v[1] for v in bb]; zs = [v[2] for v in bb]
            w   = max(xs) - min(xs);  h  = max(ys) - min(ys);  d  = max(zs) - min(zs)
            sz  = max(w, h, d)
            if sz < (max(body_obj.dimensions) * 0.5) and abs(w - d) < sz * 0.6:
                _tag_as_wheel(o, tagged_wheels, car_name)
                tagged_wheels += 1

        # 2. Flatten all tagged objects to CARBOTTOM
        carbottom = bpy.data.materials.get("CARBOTTOM") or bpy.data.materials.new("CARBOTTOM")
        for obj in get_car_objects():
            if obj.type != "MESH":
                continue
            obj.data.materials.clear()
            obj.data.materials.append(carbottom)
            for poly in obj.data.polygons:
                poly.material_index = 0

        # 3. Init support files
        display = scene.ce_car_display_name.strip() or car_name
        msgs = _init_new_car_files(car_name, display)
        ok   = sum(1 for m in msgs if "skipped" not in m.lower())

        self.report({"INFO"},
                    f"Prepared {car_name}: body + {tagged_wheels} wheel(s) tagged, "
                    f"materials flattened, {ok}/{len(msgs)} support files initialised.")
        return {"FINISHED"}


# ── Operator: Spawn N wheels at bounding-box corners ─────────────────────────

def _body_wheel_positions(body_obj, n: int):
    """
    Return n body-local Blender-space positions for wheel hub placement.

    Blender axis convention for MM1 cars (from _to_blender_pos):
      Blender X  = game -X  (lateral, left = negative Blender X)
      Blender Y  = game  Z  (forward/rear — car faces +Y in Blender)
      Blender Z  = game  Y  (up)

    So front/rear separation is along Blender Y, left/right along Blender X,
    and height (wheel ground level) is along Blender Z.

    n=4 → FL, FR, RL, RR
    n=6 → FL, FM, FR, RL, RM, RR  (trucks / buses)

    Returns positions in body-local space (ready to assign to obj.location
    when the wheel is parented to body with identity parent-inverse).
    """
    import mathutils as _mu

    # Bounding box corners in body-LOCAL space (bound_box is always local)
    corners_local = [_mu.Vector(c) for c in body_obj.bound_box]

    xs = [c.x for c in corners_local]
    ys = [c.y for c in corners_local]   # Blender Y = game forward/rear
    zs = [c.z for c in corners_local]   # Blender Z = game up

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_ground     = min(zs)              # bottom of bbox = wheel centre height

    # Inset slightly from corners so wheels aren't flush with the edge
    inset_x = (x_max - x_min) * 0.05
    inset_y = (y_max - y_min) * 0.08

    # Blender X is negated game X: x_max side = game left, x_min side = game right
    # Blender Y maps to game Z: y_min = game front (game -Z), y_max = game rear (+Z)
    gl = x_max - inset_x   # game left  (Blender +X)
    gr = x_min + inset_x   # game right (Blender -X)
    fy = y_min + inset_y   # front (Blender -Y = game -Z front)
    ry = y_max - inset_y   # rear  (Blender +Y = game +Z rear)

    # Wheel order matches MM1 convention: 0=FL, 1=FR, 2=RR, 3=RL
    if n == 4:
        return [
            _mu.Vector((gl, fy, z_ground)),  # 0 front-left
            _mu.Vector((gr, fy, z_ground)),  # 1 front-right
            _mu.Vector((gr, ry, z_ground)),  # 2 rear-right
            _mu.Vector((gl, ry, z_ground)),  # 3 rear-left
        ]
    elif n == 6:
        mid_y = (fy + ry) * 0.5
        return [
            _mu.Vector((gl, fy,    z_ground)),  # 0 front-left
            _mu.Vector((gr, fy,    z_ground)),  # 1 front-right
            _mu.Vector((gl, mid_y, z_ground)),  # 2 mid-left
            _mu.Vector((gr, mid_y, z_ground)),  # 3 mid-right
            _mu.Vector((gr, ry,    z_ground)),  # 4 rear-right
            _mu.Vector((gl, ry,    z_ground)),  # 5 rear-left
        ]
    else:
        # Generic: evenly spaced along Y axis (forward/rear), alternating left/right
        positions = []
        for i in range(n):
            t  = i / max(n - 1, 1)
            y  = fy + t * (ry - fy)
            bx = gl if (i % 2 == 0) else gr
            positions.append(_mu.Vector((bx, y, z_ground)))
        return positions


class CAR_OT_SpawnWheelsAuto(bpy.types.Operator):
    bl_idname      = "car.spawn_wheels_auto"
    bl_label       = "Spawn Wheels at Corners"
    bl_description = (
        "Spawn N template wheels (from VPMUSTANG99) placed at the body bounding-box "
        "corners so they start at plausible positions. Move them to fine-tune."
    )
    bl_options     = {"REGISTER", "UNDO"}

    wheel_count: bpy.props.IntProperty(
        name="Wheel Count", default=4, min=2, max=10,
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car body — tag a body first.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj.get("mm_car_name", "CAR"))
        src_bms  = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99" / "WHL0_H.BMS"
        if not src_bms.exists():
            self.report({"ERROR"}, f"Template wheel not found: {src_bms}")
            return {"CANCELLED"}

        # Find existing wheel indices to avoid collision
        used_idxs = {
            int(o.get(_CAR_TAG).split("_")[1])
            for o in get_car_objects()
            if o.get(_CAR_TAG, "").startswith("wheel_")
            and o.get(_CAR_TAG).split("_")[1].isdigit()
        }
        free_idxs = [i for i in range(20) if i not in used_idxs]

        positions = _body_wheel_positions(body_obj, self.wheel_count)
        col       = _get_or_create_collection(_CAR_COLLECTION)
        spawned   = 0

        for pos, new_idx in zip(positions, free_idxs):
            mesh = _load_bms(src_bms, f"{car_name}.WHL{new_idx}",
                             Folder.Resources.Editor.Textures)
            if mesh is None:
                continue
            mesh["bms_source_file"] = ""

            new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", mesh)
            col.objects.link(new_obj)
            new_obj[_CAR_TAG]              = f"wheel_{new_idx}"
            new_obj.parent                 = body_obj
            new_obj.matrix_parent_inverse  = mathutils.Matrix.Identity(4)
            # pos is already in body-local Blender space
            new_obj.location = pos
            spawned += 1

        self.report({"INFO"}, f"Spawned {spawned} wheel(s) at bounding-box corners.")
        return {"FINISHED"}


# ── Operator: Debug BMS ──────────────────────────────────────────────────────

class CAR_OT_DebugBMS(bpy.types.Operator):
    bl_idname      = "car.debug_bms"
    bl_label       = "Debug BMS"
    bl_description = (
        "Print debug info for all exported BMS files in SHOP/BMS/{car_name}/. "
        "Shows mesh_offset, point count, textures, bounding box, and radius per file."
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj.get("mm_car_name", ""))
        shop_dir = Folder.Shop.Meshes / car_name

        if not shop_dir.is_dir():
            self.report({"WARNING"}, f"SHOP/BMS/{car_name}/ does not exist — export first.")
            return {"CANCELLED"}

        bms_files = sorted(shop_dir.glob("*.BMS"))
        if not bms_files:
            self.report({"WARNING"}, f"No BMS files in SHOP/BMS/{car_name}/.")
            return {"CANCELLED"}

        print(f"\n{'='*60}")
        print(f"[Debug BMS] Car: {car_name}  ({len(bms_files)} files)")
        print(f"{'='*60}")

        for bms_file in bms_files:
            try:
                data = read_bms(bms_file)
                pts   = data.get("points", [])
                off   = data.get("mesh_offset", (0, 0, 0))
                texs  = data.get("texture_names", [])
                flags = data.get("flags", 0)

                xs = [p[0] for p in pts] or [0]
                ys = [p[1] for p in pts] or [0]
                zs = [p[2] for p in pts] or [0]
                bbox = (
                    f"X[{min(xs):.3f}..{max(xs):.3f}] "
                    f"Y[{min(ys):.3f}..{max(ys):.3f}] "
                    f"Z[{min(zs):.3f}..{max(zs):.3f}]"
                )

                print(f"\n  {bms_file.name}")
                print(f"    mesh_offset : {off[0]:.4f}, {off[1]:.4f}, {off[2]:.4f}")
                print(f"    points      : {len(pts)}")
                print(f"    surfaces    : {data.get('num_surfaces', '?')}")
                print(f"    flags       : 0x{flags:02X}")
                print(f"    textures    : {texs}")
                print(f"    bbox        : {bbox}")
            except Exception as exc:
                print(f"\n  {bms_file.name}  ERROR: {exc}")

        print(f"\n{'='*60}\n")
        self.report({"INFO"}, f"BMS debug printed to system console ({len(bms_files)} files).")
        return {"FINISHED"}


# ── Operator: Select Car Part by tag ─────────────────────────────────────────

class CAR_OT_SelectPart(bpy.types.Operator):
    bl_idname      = "car.select_part"
    bl_label       = "Select Part"
    bl_description = "Select this car part in the viewport"

    part_tag: bpy.props.StringProperty()

    def execute(self, context):
        for obj in get_car_objects():
            if obj.get(_CAR_TAG) == self.part_tag:
                for o in context.view_layer.objects:
                    o.select_set(False)
                obj.select_set(True)
                context.view_layer.objects.active = obj
                return {"FINISHED"}
        return {"CANCELLED"}


# ── Registration list ─────────────────────────────────────────────────────────

CAR_EDITOR_CLASSES = [
    CAR_OT_SelectFace,
    CAR_OT_LoadCar,
    CAR_OT_ExportCar,
    CAR_OT_ReloadCar,
    CAR_OT_ClearCar,
    CAR_OT_AssignTexture,
    CAR_OT_BrowseExportFolder,
    CAR_OT_ApplyFaceUV,
    CAR_OT_AddFace,
    CAR_OT_AddTextureSlot,
    CAR_OT_ToggleDamage,
    CAR_OT_SetPaintVariant,
    CAR_OT_ClearShop,
    CAR_OT_RemoveWheel,
    CAR_OT_RenumberWheels,
    CAR_OT_OpenExportFolder,
    CAR_OT_NewFromTemplate,
    CAR_OT_InitNewCar,
    CAR_OT_PackAndStartGame,
    CAR_OT_MirrorWheel,
    CAR_OT_MirrorAllWheels,
    CAR_OT_ToggleSymmetry,
    CAR_OT_ApplyWheelTexture,
    CAR_OT_ApplyWheelTextureSingle,
    CAR_OT_DebugBMS,
    CAR_OT_SelectPart,
    CAR_OT_ImportTagBody,
    CAR_OT_ImportTagWheel,
    CAR_OT_ImportAutoTag,
    CAR_OT_ImportDecimate,
    CAR_OT_ImportCleanMaterials,
    CAR_OT_ImportApplyTransforms,
    CAR_OT_SpawnWheelFromTemplate,
    CAR_OT_ImportFlattenMaterials,
    CAR_OT_ImportPrepare,
    CAR_OT_SpawnWheelsAuto,
]

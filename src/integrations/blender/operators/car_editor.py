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
)
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data, write_bms
from src.constants.folder import Folder


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

        s.split("_")[0]
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

def _pack_car_ar(car_name: str) -> bool:
    """
    Pack only the BMS files for car_name into !!!!!{car_name}.ar and copy it
    to the MidtownMadness folder.  Returns True on success.

    Uses mkar.exe directly (no run.bat) with a Python-generated shiplist so
    only the car's SHOP/BMS/{car_name}/ files are included — the city .ar
    created by the full map editor run is left untouched.

    The !!!!!-prefix makes the file sort after !!!!!mm1revisited.ar on
    Windows (V > m case-insensitively), so the game loads it last and the
    updated car meshes override any copy in the city archive.
    """
    import subprocess

    shop_folder  = Folder.Shop.Root
    mm1_folder   = Folder.MidtownMadness.Root
    angel_folder = Folder.Angel
    mkar_exe     = angel_folder / "mkar.exe"

    if not mkar_exe.exists():
        print(f"[Car Editor] mkar.exe not found at {mkar_exe}")
        return False

    car_bms_dir = Folder.Shop.Meshes / car_name
    if not car_bms_dir.is_dir():
        print(f"[Car Editor] Car BMS folder not found: {car_bms_dir}")
        return False

    bms_files = sorted(car_bms_dir.iterdir())
    if not bms_files:
        print(f"[Car Editor] No BMS files found in {car_bms_dir}")
        return False

    ar_name = f"!!!!!{car_name}.ar"
    ar_out  = mm1_folder / ar_name

    # Write the shiplist into SHOP so ./BMS/... paths resolve from SHOP,
    # matching how run.bat's `find . -type f` output works.
    ar_rel       = f"../{mm1_folder.name}/{ar_name}"
    shiplist_abs = shop_folder / f"shiplist.{car_name}"

    bms_rel = Folder.Shop.Meshes.relative_to(shop_folder).as_posix()

    # mkar strips the longest common path prefix from all shiplist entries.
    # If all files share ./BMS/VPCADDIE/ mkar strips it and stores flat names.
    # Adding a dummy file in a different directory forces the common prefix to
    # collapse to just "./" so full paths like BMS/VPCADDIE/BODY_H.BMS are kept.
    dummy_abs = shop_folder / f"_car_dummy_{car_name}.tmp"
    dummy_abs.write_bytes(b"")

    lines = [f"./{bms_rel}/{car_name}/{f.name}" for f in bms_files]
    lines.append(f"./{dummy_abs.name}")
    shiplist_abs.write_bytes(("\n".join(lines) + "\n").encode("ascii"))

    print(f"[Car Editor] Packing {len(bms_files)} files → {ar_name} …")
    result = subprocess.run(
        [str(mkar_exe), ar_rel, f"./shiplist.{car_name}"],
        cwd=str(shop_folder),
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.stdout:
        print(f"[Car Editor] mkar stdout: {result.stdout.strip()}")
    if result.stderr:
        print(f"[Car Editor] mkar stderr: {result.stderr.strip()}")

    for tmp in (shiplist_abs, dummy_abs):
        try:
            tmp.unlink()
        except OSError:
            pass

    if result.returncode != 0:
        print(f"[Car Editor] mkar.exe exited with code {result.returncode}")
        return False

    print(f"[Car Editor] Created {ar_out}")
    return True


def _pack_and_launch_game(car_name: str) -> None:
    """
    Pack a car-only .ar (!!!!!{car_name}.ar) then launch the game.
    Skips all city-building — the city .ar from the last map editor run is reused.
    """
    import subprocess
    from src.helpers.main import is_process_running
    from src.constants.misc import Executable

    exe = Folder.MidtownMadness.Root / Executable.MIDTOWN_MADNESS

    if is_process_running(Executable.MIDTOWN_MADNESS):
        print("[Car Editor] Game already running — skipping launch.")
        return

    if not _pack_car_ar(car_name):
        print("[Car Editor] Pack failed — game will not be launched.")
        return

    if not exe.exists():
        print(f"[Car Editor] Executable not found: {exe}")
        return

    print(f"[Car Editor] Launching {Executable.MIDTOWN_MADNESS} …")
    subprocess.Popen([str(exe)], cwd=str(Folder.MidtownMadness.Root))


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
                bms_data = mesh_to_bms_data(obj)
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


        if errors:
            self.report({"WARNING"}, f"Exported {len(exported)}, {len(errors)} error(s): {errors[0]}")
        else:
            msg = f"Exported {len(exported)} BMS file(s) to {export_dir}"
            if city_dir:
                msg += f" + SHOP/BMS/{car_name}"
            self.report({"INFO"}, msg)

        if scene.ce_auto_reload and not errors:
            bpy.ops.car.reload_car("EXEC_DEFAULT")

        if scene.ce_start_game and not errors:
            if not scene.ce_add_to_city:
                self.report({"WARNING"},
                    "Start Game requires 'Add to City' so the BMS is in SHOP before packing.")
            else:
                _pack_and_launch_game(car_name)

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


# ── Operator: Add Wheel ───────────────────────────────────────────────────────

class CAR_OT_AddWheel(bpy.types.Operator):
    bl_idname      = "car.add_wheel"
    bl_label       = "Add Wheel"
    bl_description = (
        "Duplicate an existing wheel mesh and place the new wheel at the 3D cursor. "
        "The new wheel is tagged and parented to the body — it will export as WHL{N}_H.BMS."
    )
    bl_options = {"REGISTER", "UNDO"}

    copy_from: bpy.props.IntProperty(
        name="Copy From Wheel",
        description="Which wheel index to copy the mesh from",
        default=0,
        min=0,
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        # Find all existing wheel_N objects and the highest index
        car_objs  = get_car_objects()
        wheel_map = {}
        for o in car_objs:
            tag = o.get(_CAR_TAG, "")
            if tag.startswith("wheel_"):
                try:
                    idx = int(tag.split("_")[1])
                    wheel_map[idx] = o
                except ValueError:
                    pass

        if not wheel_map:
            self.report({"ERROR"}, "No existing wheels found to copy from.")
            return {"CANCELLED"}

        copy_idx = self.copy_from
        if copy_idx not in wheel_map:
            # Fall back to highest available
            copy_idx = max(wheel_map.keys())

        source_obj = wheel_map[copy_idx]
        new_idx    = max(wheel_map.keys()) + 1

        # Deep-copy the mesh data so the new wheel is independent
        new_mesh = source_obj.data.copy()
        new_mesh["bms_source_file"] = ""  # cleared — will export as WHL{new_idx}_H.BMS
        car_name = body_obj.get("mm_car_name", "CAR")

        col = _get_or_create_collection(_CAR_COLLECTION)
        new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", new_mesh)
        col.objects.link(new_obj)
        new_obj.parent = body_obj
        new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        new_obj[_CAR_TAG] = f"wheel_{new_idx}"

        # Place at 3D cursor in body's local space
        cursor_world = context.scene.cursor.location.copy()
        new_obj.location = body_obj.matrix_world.inverted() @ cursor_world

        # Select the new wheel so the user can see/move it
        bpy.ops.object.select_all(action="DESELECT")
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        self.report({"INFO"},
                    f"Added wheel_{new_idx} (copied from wheel_{copy_idx}). "
                    "Move it to the desired position — location = BMS mesh_offset on export.")
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
    CAR_OT_AddWheel,
    CAR_OT_RemoveWheel,
    CAR_OT_RenumberWheels,
    CAR_OT_OpenExportFolder,
]

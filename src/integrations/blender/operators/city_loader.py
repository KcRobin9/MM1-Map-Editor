"""
City Loader operators — load FCD, BNG, and city meshes from a city folder.

The city folder structure is:
    <city_root>/
        <NAME>.FCD
        <NAME>.BNG
        MESHES/<NAME>CITY/   CULL*.BMS
        MESHES/<NAME>LM/     CULL*.BMS   (optional landmark meshes)

All loading delegates to the existing facade / prop operators and
the shared BMS mesh utilities so no parsing is duplicated.
"""
import bpy
import bmesh
from pathlib import Path
from typing import List

from src.constants.folder import Folder


# ── City mesh loader ──────────────────────────────────────────────────────────

def _build_city_mesh(name: str, bms_data: dict) -> bpy.types.Mesh:
    """
    Like build_blender_mesh but uses (x, -z, y) vertex convention to match
    props/facades rather than the BMS (-x, z, y) convention.
    """
    points          = bms_data["points"]
    tex_coords      = bms_data["tex_coords"]
    vert_colors     = bms_data.get("vert_colors", [])
    normal_indices  = bms_data["normal_indices"]
    vertex_indices  = bms_data["vertex_indices"]
    surface_indices = bms_data["surface_indices"]
    texture_indices = bms_data["texture_indices"]
    num_surfaces    = bms_data["num_surfaces"]
    flags           = bms_data["flags"]
    texture_names   = bms_data.get("texture_names", [])

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.from_mesh(me)

    uv_layer    = bm.loops.layers.uv.new()
    color_layer = bm.loops.layers.color.new("Col") if vert_colors else None
    ni_layer    = bm.loops.layers.int.new("bms_ni") if (flags & 2) else None

    # (x, -z, y) — same convention as props/facades world positions
    for px, py, pz in points:
        bm.verts.new((px, -pz, py))
    bm.verts.ensure_lookup_table()

    for surf_idx in range(num_surfaces):
        base       = surf_idx * 4
        side_count = 4 if surface_indices[base + 3] > 0 else 3
        adj_list   = surface_indices[base : base + side_count]
        pt_indices = [vertex_indices[adj] for adj in adj_list]
        if len(set(pt_indices)) < side_count:
            continue
        try:
            face = bm.faces.new([bm.verts[vi] for vi in pt_indices])
            for xx, loop in enumerate(face.loops):
                adj_idx = adj_list[xx]
                if flags & 1:
                    loop[uv_layer].uv = (tex_coords[adj_idx][0], 1.0 - tex_coords[adj_idx][1])
                if color_layer is not None:
                    loop[color_layer] = vert_colors[adj_idx]
                if ni_layer is not None:
                    loop[ni_layer] = normal_indices[adj_idx]
            face.material_index = 0 if texture_indices[surf_idx] == 0 else texture_indices[surf_idx] - 1
            face.smooth = True
        except Exception:
            pass

    for _ in texture_names:
        me.materials.append(None)

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()

    me["bms_flags"]     = flags
    me["texture_names"] = texture_names
    me["mesh_offset"]   = list(bms_data.get("mesh_offset", (0.0, 0.0, 0.0)))
    return me


def _load_city_meshes(mesh_dirs: List[Path], texture_folder: Path) -> int:
    from src.integrations.blender.modeling.meshes import read_bms
    from src.integrations.blender.modeling.meshes import _apply_materials_to_mesh

    col_name = "City Meshes"
    if col_name not in bpy.data.collections:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    else:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for child in list(col.children):
            for obj in list(child.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(child)

    loaded = 0
    for mesh_dir in mesh_dirs:
        if not mesh_dir.is_dir():
            continue
        sub_name = f"City Meshes — {mesh_dir.name}"
        sub_col = bpy.data.collections.new(sub_name)
        col.children.link(sub_col)

        for bms_file in sorted(mesh_dir.glob("*.BMS")):
            try:
                bms_data = read_bms(bms_file)
                mesh = _build_city_mesh(bms_file.stem, bms_data)
                if bms_data.get("texture_names"):
                    _apply_materials_to_mesh(mesh, bms_data["texture_names"], texture_folder)
                obj = bpy.data.objects.new(bms_file.stem, mesh)
                sub_col.objects.link(obj)
                loaded += 1
            except Exception as exc:
                print(f"[City Loader] BMS load failed ({bms_file.name}): {exc}")
    return loaded


# ── Operators ─────────────────────────────────────────────────────────────────

class CITY_OT_SelectFolder(bpy.types.Operator):
    """Browse to and set the city root folder"""
    bl_idname = "city_loader.select_folder"
    bl_label  = "Select City Folder"

    directory:   bpy.props.StringProperty(subtype="DIR_PATH")
    filter_glob: bpy.props.StringProperty(default="", options={"HIDDEN"})

    def invoke(self, context, event):
        self.directory = str(Folder.BASE / "resources" / "city_files") + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        context.scene.cl_city_folder = self.directory.rstrip("/\\")
        return {"FINISHED"}


class CITY_OT_Load(bpy.types.Operator):
    """Load the selected city: FCD, BNG, and/or meshes based on the checkboxes"""
    bl_idname = "city_loader.load"
    bl_label  = "Load City"

    def execute(self, context):
        scene  = context.scene
        folder = Path(scene.cl_city_folder)

        if not folder.is_dir():
            self.report({"ERROR"}, f"City folder not found: {folder}")
            return {"CANCELLED"}

        fcd_files = list(folder.glob("*.FCD")) + list(folder.glob("*.fcd"))
        bng_files = list(folder.glob("*.BNG")) + list(folder.glob("*.bng"))

        if fcd_files:
            city_name = fcd_files[0].stem.upper()
        elif bng_files:
            city_name = bng_files[0].stem.upper()
        else:
            city_name = folder.name.upper().replace("_", "")

        loaded_parts = []
        errors = []

        # ── FCD ───────────────────────────────────────────────────────────────
        if scene.cl_load_fcd:
            fcd_path = fcd_files[0] if fcd_files else None
            if fcd_path and fcd_path.exists():
                try:
                    bpy.ops.facades.load_external(filepath=str(fcd_path))
                    loaded_parts.append("FCD")
                except Exception as exc:
                    errors.append(f"FCD: {exc}")
            else:
                errors.append(f"FCD: no .FCD file found in {folder.name}")

        # ── BNG ───────────────────────────────────────────────────────────────
        if scene.cl_load_bng:
            bng_path = bng_files[0] if bng_files else None
            if bng_path and bng_path.exists():
                try:
                    bpy.ops.props.load_external(filepath=str(bng_path))
                    loaded_parts.append("BNG")
                except Exception as exc:
                    errors.append(f"BNG: {exc}")
            else:
                errors.append(f"BNG: no .BNG file found in {folder.name}")

        # ── City meshes ───────────────────────────────────────────────────────
        if scene.cl_load_meshes:
            meshes_root = folder / "MESHES"
            mesh_dirs = [d for d in meshes_root.iterdir() if d.is_dir()] if meshes_root.is_dir() else []

            if mesh_dirs:
                tex_folder = Path(scene.cl_texture_folder) if scene.cl_texture_folder else Folder.Resources.Editor.Textures
                n = _load_city_meshes(mesh_dirs, tex_folder)
                loaded_parts.append(f"Meshes ({n} BMS)")
            else:
                errors.append(f"Meshes: no MESHES subfolders found in {folder.name}")

        # ── Report ────────────────────────────────────────────────────────────
        for e in errors:
            self.report({"WARNING"}, e)
        if loaded_parts:
            self.report({"INFO"}, f"[{city_name}] Loaded: " + ", ".join(loaded_parts))
        elif not errors:
            self.report({"WARNING"}, "Nothing selected to load")

        return {"FINISHED"}


class CITY_OT_ClearMeshes(bpy.types.Operator):
    """Remove all loaded city meshes from the scene"""
    bl_idname = "city_loader.clear_meshes"
    bl_label  = "Clear City Meshes"

    def execute(self, context):
        col = bpy.data.collections.get("City Meshes")
        if col:
            removed = 0
            for child in list(col.children):
                removed += len(list(child.objects))
                for obj in list(child.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.collections.remove(child)
            for obj in list(col.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
                removed += 1
            self.report({"INFO"}, f"Removed {removed} city mesh object(s)")
        else:
            self.report({"INFO"}, "No city meshes to clear")
        return {"FINISHED"}


CITY_LOADER_CLASSES = [
    CITY_OT_SelectFolder,
    CITY_OT_Load,
    CITY_OT_ClearMeshes,
]

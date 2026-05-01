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
from pathlib import Path
from typing import List

from src.constants.folder import Folder

_CITY_MESHES_COLLECTION = "City Meshes"


# ── Collection helpers (mirrors facades.py pattern) ──────────────────────────

def _get_or_create_collection(name: str) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _clear_collection(col: bpy.types.Collection) -> None:
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


# ── City mesh loader ──────────────────────────────────────────────────────────

def _load_city_meshes(mesh_dirs: List[Path], texture_folder: Path, col: bpy.types.Collection) -> int:
    """Load all CULL*.BMS files from mesh_dirs into col. Returns count loaded."""
    from src.integrations.blender.modeling.meshes import read_bms, build_blender_mesh, _apply_materials_to_mesh
    import mathutils

    loaded = 0
    for mesh_dir in mesh_dirs:
        if not mesh_dir.is_dir():
            continue
        sub_col_name = f"City Meshes — {mesh_dir.name}"
        if sub_col_name in bpy.data.collections:
            sub_col = bpy.data.collections[sub_col_name]
        else:
            sub_col = bpy.data.collections.new(sub_col_name)
            col.children.link(sub_col)

        for bms_file in sorted(mesh_dir.glob("*.BMS")):
            try:
                bms_data = read_bms(bms_file)
                mesh = build_blender_mesh(bms_file.stem, bms_data)
                if bms_data.get("texture_names"):
                    _apply_materials_to_mesh(mesh, bms_data["texture_names"], texture_folder)
                ox, oy, oz = bms_data.get("mesh_offset", [0.0, 0.0, 0.0])
                obj = bpy.data.objects.new(bms_file.stem, mesh)
                sub_col.objects.link(obj)
                obj.location = (-ox, oz, oy)
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

        # Derive city name from folder name (e.g. RACETRACK_7 → RACETRACK7)
        folder_name = folder.name.upper()
        # Try to find the base name by looking for .FCD or .BNG files
        fcd_files = list(folder.glob("*.FCD")) + list(folder.glob("*.fcd"))
        bng_files = list(folder.glob("*.BNG")) + list(folder.glob("*.bng"))

        city_name = None
        if fcd_files:
            city_name = fcd_files[0].stem.upper()
        elif bng_files:
            city_name = bng_files[0].stem.upper()
        else:
            # Fall back to stripping underscores from folder name
            city_name = folder_name.replace("_", "")

        loaded_parts = []
        errors = []

        # ── FCD ───────────────────────────────────────────────────────────────
        if scene.cl_load_fcd:
            fcd_path = None
            for p in fcd_files:
                fcd_path = p
                break
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
            bng_path = None
            for p in bng_files:
                bng_path = p
                break
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
            # Collect all subdirectories under MESHES (CITY, LM, or any subfolder)
            if meshes_root.is_dir():
                mesh_dirs = [d for d in meshes_root.iterdir() if d.is_dir()]
            else:
                mesh_dirs = []

            if mesh_dirs:
                tex_folder = Path(scene.cl_texture_folder) if scene.cl_texture_folder else Folder.Resources.Editor.Textures
                # Clear existing city meshes before reloading
                if _CITY_MESHES_COLLECTION in bpy.data.collections:
                    parent_col = bpy.data.collections[_CITY_MESHES_COLLECTION]
                    # Remove all sub-collections and their objects
                    for child in list(parent_col.children):
                        for obj in list(child.objects):
                            bpy.data.objects.remove(obj, do_unlink=True)
                        bpy.data.collections.remove(child)
                    _clear_collection(parent_col)

                col = _get_or_create_collection(_CITY_MESHES_COLLECTION)
                n = _load_city_meshes(mesh_dirs, tex_folder, col)
                loaded_parts.append(f"Meshes ({n} BMS)")
            else:
                errors.append(f"Meshes: no MESHES subfolders found in {folder.name}")

        # ── Report ────────────────────────────────────────────────────────────
        msg_parts = []
        if loaded_parts:
            msg_parts.append("Loaded: " + ", ".join(loaded_parts))
        if errors:
            for e in errors:
                self.report({"WARNING"}, e)
        if msg_parts:
            self.report({"INFO"}, f"[{city_name}] " + " | ".join(msg_parts))
        elif not errors:
            self.report({"WARNING"}, "Nothing selected to load")

        return {"FINISHED"}


class CITY_OT_ClearMeshes(bpy.types.Operator):
    """Remove all loaded city meshes from the scene"""
    bl_idname = "city_loader.clear_meshes"
    bl_label  = "Clear City Meshes"

    def execute(self, context):
        removed = 0
        if _CITY_MESHES_COLLECTION in bpy.data.collections:
            parent_col = bpy.data.collections[_CITY_MESHES_COLLECTION]
            for child in list(parent_col.children):
                removed += len(list(child.objects))
                for obj in list(child.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.collections.remove(child)
            removed += len(list(parent_col.objects))
            _clear_collection(parent_col)
        self.report({"INFO"}, f"Removed {removed} city mesh object(s)")
        return {"FINISHED"}


CITY_LOADER_CLASSES = [
    CITY_OT_SelectFolder,
    CITY_OT_Load,
    CITY_OT_ClearMeshes,
]

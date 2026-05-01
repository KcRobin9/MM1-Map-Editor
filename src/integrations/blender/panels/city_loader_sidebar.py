"""
City Loader sidebar panel.  Tab: "City Loader"  (VIEW_3D → N-panel)

Lets you pick a city folder (e.g. resources/city_files/RACETRACK_7) and load
any combination of FCD (facades), BNG (props/bangers) and MESHES in one click.
All heavy lifting is delegated to the existing facade / prop operators.
"""
import bpy
from pathlib import Path

_PANEL_CATEGORY = "City Loader"


class VIEW3D_PT_CityLoader(bpy.types.Panel):
    bl_label       = "City Loader"
    bl_idname      = "VIEW3D_PT_city_loader"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Folder picker ─────────────────────────────────────────────────────
        layout.label(text="City Folder", icon="FILE_FOLDER")
        box = layout.box()
        col = box.column(align=True)

        folder_path = scene.cl_city_folder
        if folder_path:
            folder_name = Path(folder_path).name
            col.label(text=folder_name, icon="SEQUENCE_COLOR_04")
        else:
            row = col.row()
            row.alert = True
            row.label(text="No folder selected", icon="ERROR")

        col.operator("city_loader.select_folder", text="Browse…", icon="FILEBROWSER")

        layout.separator()

        # ── What to load ──────────────────────────────────────────────────────
        layout.label(text="Load Options", icon="SETTINGS")
        box = layout.box()
        col = box.column(align=True)
        col.prop(scene, "cl_load_fcd",    text="Facades  (.FCD)")
        col.prop(scene, "cl_load_bng",    text="Props / Bangers  (.BNG)")
        col.prop(scene, "cl_load_meshes", text="City Meshes  (MESHES/)")

        layout.separator()

        # ── Texture folder override ───────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Texture Folder (meshes)", icon="IMAGE_DATA")
        col.prop(scene, "cl_texture_folder", text="")

        layout.separator()

        # ── Load button ───────────────────────────────────────────────────────
        any_selected = scene.cl_load_fcd or scene.cl_load_bng or scene.cl_load_meshes
        row = layout.row(align=True)
        row.scale_y = 1.6
        row.enabled = bool(folder_path) and any_selected
        row.operator("city_loader.load", text="Load City", icon="IMPORT")

        layout.separator()

        # ── Quick info about discovered files ─────────────────────────────────
        if folder_path:
            p = Path(folder_path)
            if p.is_dir():
                box = layout.box()
                col = box.column(align=True)
                col.label(text="Detected files:", icon="INFO")

                fcd = list(p.glob("*.FCD")) + list(p.glob("*.fcd"))
                bng = list(p.glob("*.BNG")) + list(p.glob("*.bng"))
                meshes_root = p / "MESHES"
                mesh_dirs   = [d for d in meshes_root.iterdir() if d.is_dir()] if meshes_root.is_dir() else []
                bms_count   = sum(len(list(d.glob("*.BMS"))) for d in mesh_dirs)

                _file_row(col, "FCD",    fcd[0].name  if fcd  else None)
                _file_row(col, "BNG",    bng[0].name  if bng  else None)
                _file_row(col, "MESHES", f"{bms_count} BMS across {len(mesh_dirs)} subfolder(s)" if mesh_dirs else None)


class VIEW3D_PT_CityLoaderTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_city_loader_tools"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.label(text="Clear loaded data", icon="TRASH")
        col = layout.column(align=True)
        col.operator("city_loader.clear_meshes", text="Clear City Meshes", icon="MESH_DATA")
        col.operator("facades.clear",            text="Clear Facades",     icon="MOD_BUILD")
        col.operator("props.clear",              text="Clear Props",       icon="PARTICLES")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _file_row(col, label: str, value):
    row = col.row(align=True)
    if value:
        row.label(text=f"  {label}:  {value}", icon="SEQUENCE_COLOR_04")
    else:
        row.alert = True
        row.label(text=f"  {label}:  not found", icon="SEQUENCE_COLOR_01")


# ── Registration ──────────────────────────────────────────────────────────────

CITY_LOADER_PANEL_CLASSES = [
    VIEW3D_PT_CityLoader,
    VIEW3D_PT_CityLoaderTools,
]

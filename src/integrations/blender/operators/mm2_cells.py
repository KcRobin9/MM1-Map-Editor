"""
MM2 Cell edit round-trip: export edited "MM2 Cells" objects back into the build.

The merge-per-cell MM2 preview (create_blender_meshes_merged_by_cell) creates one object per
landmark cell ("Cell<N>" in the "MM2 Cells" collection), carrying per-face texture (material slot),
per-loop game UVs (V-flipped), and per-face obj_type (int attribute indexing the JSON legend on the
object). All of those names live in Mm2CellPreview so both sides cannot drift apart.

"Export MM2 Cell Edits" writes the SELECTED cell objects (or every cell if none is selected) to
    src/USER/mm2_edits/<MAP_FILENAME>cell_overrides.json
On the next build, emit_mm2_city replaces those cells' polygons with the exported ones --- so edits
made in Blender (move/delete/add faces, retexture via material slots) reach the game .ar.

Coordinates: game (x,y,z) <-> Blender (x,-z,y); export applies the inverse (bx,by,bz)->(bx,bz,-by)
after obj.matrix_world (so moving a whole cell object also round-trips). UVs: game v = 1 - blender v.
Quads/ngons created while editing are triangulated on export (calc_loop_triangles).
"""
import sys
import json
from pathlib import Path

import bpy

from src.constants.mm2 import Mm2CellPreview
from src.constants.folder import Folder
from src.constants.file_formats import FileType
from src.USER.settings.main import MAP_FILENAME


def _overrides_path() -> Path:
    """Where this map's exported cell overrides live. The build reads the same path."""
    Folder.Src.User.Mm2Edits.mkdir(parents=True, exist_ok=True)

    return Folder.Src.User.Mm2Edits / f"{MAP_FILENAME}{Mm2CellPreview.OVERRIDES_SUFFIX}{FileType.JSON}"


def _cell_objects(selected_only: bool) -> list:
    """The cell objects to export. With nothing selected, fall back to exporting them all."""
    collection = bpy.data.collections.get(Mm2CellPreview.COLLECTION)
    if not collection:
        return []

    cells = [obj for obj in collection.objects
             if obj.type == "MESH" and Mm2CellPreview.CELL_ID in obj]
    if not selected_only:
        return cells

    return [obj for obj in cells if obj.select_get()] or cells


def _object_type_legend(cell_object) -> list:
    """The object's obj_type legend, or empty if it was never written / is malformed."""
    try:
        return json.loads(cell_object.get(Mm2CellPreview.OBJECT_TYPE_LEGEND, "[]"))
    except (TypeError, ValueError):
        return []       # a hand-edited or truncated legend just means no obj_type survives


def _export_cell(cell_object) -> list:
    """One cell object -> override polys [{v, uv, tex, ot}] in game space."""
    mesh = cell_object.data
    to_world = cell_object.matrix_world
    mesh.calc_loop_triangles()

    uv_layer = mesh.uv_layers.active
    legend = _object_type_legend(cell_object)
    material_names = [material.name if material else "" for material in mesh.materials]

    type_attribute = mesh.attributes.get(Mm2CellPreview.OBJECT_TYPE)
    type_data = type_attribute.data if (type_attribute and type_attribute.domain == "FACE") else None

    polys = []
    for triangle in mesh.loop_triangles:
        vertices, tex_coords = [], []

        for loop_index in triangle.loops:
            loop = mesh.loops[loop_index]
            world = to_world @ mesh.vertices[loop.vertex_index].co
            vertices.append((world.x, world.z, -world.y))            # blender -> game

            if uv_layer:
                u, v = uv_layer.data[loop_index].uv
                tex_coords.extend((float(u), 1.0 - float(v)))        # blender V -> game V
            else:
                tex_coords.extend((0.0, 0.0))

        texture = (material_names[triangle.material_index]
                   if triangle.material_index < len(material_names) else "")

        obj_type = ""
        if type_data is not None and triangle.polygon_index < len(type_data):
            legend_index = type_data[triangle.polygon_index].value
            if 0 <= legend_index < len(legend):
                obj_type = legend[legend_index]

        polys.append({"v": [list(point) for point in vertices], "uv": tex_coords,
                      "tex": texture, "ot": obj_type})

    return polys


class MM2_OT_ExportCellEdits(bpy.types.Operator):
    """Export selected MM2 cell objects (all cells if none selected) as build overrides"""
    bl_idname = "mm2.export_cell_edits"
    bl_label = "Export MM2 Cell Edits"
    bl_options = {"REGISTER"}

    def execute(self, context):
        cell_objects = _cell_objects(selected_only=True)
        if not cell_objects:
            self.report({"ERROR"}, f"No cell objects in collection '{Mm2CellPreview.COLLECTION}'")
            return {"CANCELLED"}

        cells = {}
        for cell_object in sorted(cell_objects, key=lambda o: int(o[Mm2CellPreview.CELL_ID])):
            cells[str(int(cell_object[Mm2CellPreview.CELL_ID]))] = _export_cell(cell_object)

        path = _overrides_path()
        path.write_text(json.dumps({"cells": cells}))

        poly_count = sum(len(polys) for polys in cells.values())
        self.report({"INFO"}, f"Exported {len(cells)} cell(s) / {poly_count} polys -> {path.name}. "
                              f"Next build applies them.")
        return {"FINISHED"}


class MM2_OT_ClearCellEdits(bpy.types.Operator):
    """Delete the exported cell-overrides file (next build uses the pristine MM2 source again)"""
    bl_idname = "mm2.clear_cell_edits"
    bl_label = "Clear MM2 Cell Edits"
    bl_options = {"REGISTER"}

    def execute(self, context):
        path = _overrides_path()
        if path.exists():
            path.unlink()
            self.report({"INFO"}, f"Removed {path.name}")
        else:
            self.report({"INFO"}, "No overrides file to remove")

        return {"FINISHED"}


def _city_items(self, context):
    """City dropdown, active city first. Falls back to SF when no multi-city config is present."""
    try:
        from src.USER.settings.main import CITY_CFGS, ACTIVE_CITY
    except ImportError:
        return [("SF", "SF", "San Francisco")]

    keys = sorted(CITY_CFGS, key=lambda key: (key != ACTIVE_CITY, key))

    return [(key, key, CITY_CFGS[key]["MAP_NAME"]) for key in keys]


class MM2_OT_LoadGroundTruth(bpy.types.Operator):
    """Load the REAL MM2 data (PSDL rooms / pathset props with real .pkg meshes / BAI splines +
    stored traffic lights) into its own collections - zero MM1 placement code, same coordinates.
    Toggle collection visibility to A/B against the MM1-baked city loaded via 'Load City'"""
    bl_idname = "mm2.load_ground_truth"
    bl_label = "Load MM2 Ground Truth (PSDL)"
    bl_options = {"REGISTER"}

    city: bpy.props.EnumProperty(name="City", items=_city_items)
    do_rooms: bpy.props.BoolProperty(name="PSDL Rooms (geometry)", default=True)
    do_props: bpy.props.BoolProperty(name="Pathset Props (real .pkg meshes)", default=True)
    do_bai: bpy.props.BoolProperty(name="BAI Roads + stored Traffic Lights", default=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # The viewer lives at the repo root rather than under src/, so it is imported by name.
        if str(Folder.BASE) not in sys.path:
            sys.path.insert(0, str(Folder.BASE))
        import MM2_PSDL_VIEWER as ground_truth

        try:
            data = ground_truth.gather(self.city)
        except Exception as error:
            self.report({"ERROR"}, f"gather failed: {error}")
            return {"CANCELLED"}

        ground_truth.build(data, do_rooms=self.do_rooms, do_props=self.do_props, do_bai=self.do_bai)
        self.report({"INFO"},
                    f"MM2 GT [{data['city']}]: {len(data['rooms'])} rooms, {len(data['props'])} props, "
                    f"{len(data['bai']['roads'])} BAI roads, {len(data['bai']['tl'])} stored lights")
        return {"FINISHED"}


class VIEW3D_PT_MM2Cells(bpy.types.Panel):
    bl_label = "MM2 Cell Edits"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Map Loader"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Ground truth (real MM2 PSDL/BAI):")
        box.operator("mm2.load_ground_truth", icon="IMPORT")
        box.label(text="A/B vs 'Load City' via collection visibility")

        column = layout.column(align=True)
        column.label(text="Round-trip edited MM2 cells:")
        column.operator("mm2.export_cell_edits", icon="EXPORT")
        column.operator("mm2.clear_cell_edits", icon="TRASH")

        path = _overrides_path()
        column.label(text=f"ACTIVE: {path.name}" if path.exists() else "no overrides exported",
                     icon="CHECKMARK" if path.exists() else "BLANK1")


MM2_CELLS_CLASSES = [
    MM2_OT_LoadGroundTruth,
    MM2_OT_ExportCellEdits,
    MM2_OT_ClearCellEdits,
    VIEW3D_PT_MM2Cells,
]

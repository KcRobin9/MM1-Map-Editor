import bpy

from src.integrations.blender.panels.cells import CELL_IMPORT
from src.integrations.blender.panels.hud import HUD_IMPORT
from src.integrations.blender.panels.materials import MATERIAL_IMPORT


class VIEW3D_PT_MapEditorPanel(bpy.types.Panel):
    bl_label = "Polygon"
    bl_idname = "VIEW3D_PT_map_editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            layout.label(text="Select a polygon", icon='INFO')
            return

        layout.label(text=obj.name, icon='MESH_DATA')


class VIEW3D_PT_MapEditorUV(bpy.types.Panel):
    bl_label = "UV Mapping"
    bl_idname = "VIEW3D_PT_map_editor_uv"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"
    bl_parent_id = "VIEW3D_PT_map_editor"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            return

        layout.prop(obj, "texture_name", text="Texture")
        layout.separator()

        col = layout.column(align=True)
        col.prop(obj, "tile_x", text="Tile X")
        col.prop(obj, "tile_y", text="Tile Y")
        col.prop(obj, "angle_degrees", text="Rotation (°)")
        layout.operator("object.update_uv_mapping", text="Reapply UV", icon='UV')


class VIEW3D_PT_MapEditorCell(bpy.types.Panel):
    bl_label = "Cell & Material"
    bl_idname = "VIEW3D_PT_map_editor_cell"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"
    bl_parent_id = "VIEW3D_PT_map_editor"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            return

        layout.prop(obj, "cell_type", text="Cell Type")
        layout.prop(obj, "material_index", text="Material")


class VIEW3D_PT_MapEditorOptions(bpy.types.Panel):
    bl_label = "Options"
    bl_idname = "VIEW3D_PT_map_editor_options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"
    bl_parent_id = "VIEW3D_PT_map_editor"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            return

        layout.prop(obj, "always_visible", text="Always Visible")
        layout.prop(obj, "sort_vertices", text="Sort Vertices")


class VIEW3D_PT_MapEditorHUD(bpy.types.Panel):
    bl_label = "HUD Color"
    bl_idname = "VIEW3D_PT_map_editor_hud"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"
    bl_parent_id = "VIEW3D_PT_map_editor"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            return

        row = layout.row(align=True)
        col_left = row.column(align=True)
        col_right = row.column(align=True)
        half = len(HUD_IMPORT) // 2 + len(HUD_IMPORT) % 2

        for i, (_, name, _, _, _) in enumerate(HUD_IMPORT):
            col = col_left if i < half else col_right
            col.prop(obj, "hud_colors", index=i, text=name, toggle=True)


class VIEW3D_PT_MapEditorTools(bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "VIEW3D_PT_map_editor_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Export", icon='EXPORT')
        row = layout.row(align=True)
        op = row.operator("object.export_polygons", text="Selected", icon='RESTRICT_SELECT_OFF')
        op.select_all = False
        op = row.operator("object.export_polygons", text="All", icon='WORLD')
        op.select_all = True

        layout.separator()
        layout.label(text="Naming", icon='FONT_DATA')
        row = layout.row(align=True)
        row.operator("object.auto_rename_children", text="Normalize", icon='SORTALPHA')
        row.operator("object.rename_sequential", text="Sequential", icon='LINENUMBERS_ON')
        layout.operator("object.fix_polygon_names", text="Fix Names (.001)", icon='ERROR')  # NEW

        layout.separator()
        layout.label(text="Create", icon='ADD')                                              # NEW
        layout.operator("object.create_polygon", text="New Polygon", icon='MESH_PLANE')     # NEW

        layout.separator()
        layout.label(text="Mesh", icon='MESH_DATA')
        row = layout.row(align=True)
        op = row.operator("object.process_post_extrude", text="Split", icon='MOD_EDGESPLIT')
        op.triangulate = False
        op = row.operator("object.process_post_extrude", text="Split+Tri", icon='MOD_TRIANGULATE')
        op.triangulate = True

        layout.separator()
        layout.operator("object.assign_custom_properties", text="Assign Defaults", icon='PROPERTIES')


SIDEBAR_CLASSES = [
    VIEW3D_PT_MapEditorPanel,
    VIEW3D_PT_MapEditorUV,
    VIEW3D_PT_MapEditorCell,
    VIEW3D_PT_MapEditorOptions,
    VIEW3D_PT_MapEditorHUD,
    VIEW3D_PT_MapEditorTools,
]
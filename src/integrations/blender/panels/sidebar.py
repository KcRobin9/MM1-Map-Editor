import bpy


class VIEW3D_PT_MapEditorPanel(bpy.types.Panel):
    bl_label    = "Polygon"
    bl_idname   = "VIEW3D_PT_map_editor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Map Editor"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj or obj.type != 'MESH':
            layout.label(text="Select a polygon", icon='INFO')
            return

        layout.label(text=obj.name, icon='MESH_DATA')


class VIEW3D_PT_MapEditorUV(bpy.types.Panel):
    bl_label      = "UV Mapping"
    bl_idname     = "VIEW3D_PT_map_editor_uv"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Map Editor"
    bl_parent_id  = "VIEW3D_PT_map_editor"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj or obj.type != 'MESH':
            return

        layout.prop(obj, "texture_name", text="Texture")
        layout.separator()

        col = layout.column(align=True)
        col.prop(obj, "tile_x",         text="Tile X")
        col.prop(obj, "tile_y",         text="Tile Y")
        col.prop(obj, "angle_degrees",  text="Rotation (°)")


class VIEW3D_PT_MapEditorCell(bpy.types.Panel):
    bl_label      = "Cell & Material & HUD Color"
    bl_idname     = "VIEW3D_PT_map_editor_cell"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Map Editor"
    bl_parent_id  = "VIEW3D_PT_map_editor"
    bl_options    = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj or obj.type != 'MESH':
            return

        layout.prop(obj, "cell_type",      text="Cell Type")
        layout.prop(obj, "material_index", text="Material")
        layout.prop(obj, "hud_color",      text="HUD")


class VIEW3D_PT_MapEditorOptions(bpy.types.Panel):
    bl_label      = "Options"
    bl_idname     = "VIEW3D_PT_map_editor_options"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Map Editor"
    bl_parent_id  = "VIEW3D_PT_map_editor"
    bl_options    = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj or obj.type != 'MESH':
            return

        layout.prop(obj, "always_visible", text="Always Visible")
        layout.prop(obj, "sort_vertices",  text="Sort Vertices")



class VIEW3D_PT_MapEditorTools(bpy.types.Panel):
    bl_label      = "Tools"
    bl_idname     = "VIEW3D_PT_map_editor_tools"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Map Editor"

    def draw(self, context):
        layout = self.layout

        # ── 1) Map Status ─────────────────────────────────────────────────────
        scene_meshes = [obj for obj in context.scene.objects if obj.type == "MESH"]
        scene_names  = {obj.name for obj in scene_meshes}
        has_p1   = "P1"  in scene_names
        has_p200 = "P200" in scene_names

        layout.label(text="Map Status", icon='INFO')
        box = layout.box()
        row = box.row()
        if has_p1:
            row.label(text="P1 present", icon='SEQUENCE_COLOR_04')
        else:
            row.alert = True
            row.label(text="P1 missing!", icon='ERROR')
        if has_p200:
            row = box.row()
            row.alert = True
            row.label(text="P200 reserved — rename it!", icon='ERROR')

        # ── 2) Create ─────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Create", icon='ADD')
        col = layout.column(align=True)
        col.prop(context.scene, "polygon_create_shape", text="Shape")
        row = col.row(align=True)
        row.prop(context.scene, "polygon_create_width",  text="W")
        row.prop(context.scene, "polygon_create_length", text="L")
        row = layout.row(align=True)
        row.operator("object.create_polygon",    text="New Polygon", icon='MESH_PLANE')
        row.operator("object.duplicate_polygon", text="Duplicate",   icon='DUPLICATE')

        # ── 3) Presets ────────────────────────────────────────────────────────
        layout.separator()
        layout.prop(context.scene, "polygon_preset", text="Preset")
        layout.operator("object.spawn_polygon_preset", text="Create Preset", icon='IMPORT')

        # ── 4) Mesh ───────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Mesh", icon='MESH_DATA')
        row = layout.row(align=True)
        op  = row.operator("object.process_post_extrude", text="Split",     icon='MOD_EDGESPLIT')
        op.triangulate = False
        op  = row.operator("object.process_post_extrude", text="Split+Tri", icon='MOD_TRIANGULATE')
        op.triangulate = True
        layout.operator("object.assign_custom_properties", text="Assign Defaults", icon='PROPERTIES')

        # ── 5) Naming ─────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Naming", icon='FONT_DATA')
        row = layout.row(align=True)
        row.operator("object.rename_sequential",  text="Sequential",     icon='LINENUMBERS_ON')
        row.operator("object.fix_polygon_names",  text="Fix Poly Names", icon='ERROR')

        # ── 6) Export ─────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Export", icon='EXPORT')
        row = layout.row(align=True)
        op  = row.operator("object.export_polygons", text="Selected", icon='RESTRICT_SELECT_OFF')
        op.select_all = False
        op  = row.operator("object.export_polygons", text="All", icon='WORLD')
        op.select_all = True


SIDEBAR_CLASSES = [
    VIEW3D_PT_MapEditorPanel,
    VIEW3D_PT_MapEditorUV,
    VIEW3D_PT_MapEditorCell,
    VIEW3D_PT_MapEditorOptions,
    VIEW3D_PT_MapEditorTools,
]
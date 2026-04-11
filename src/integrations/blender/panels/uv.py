import bpy


class OBJECT_PT_UVMappingPanel(bpy.types.Panel):
    bl_label = "UV Mapping"
    bl_idname = "OBJECT_PT_uv_mapping"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            layout.label(text="No active mesh object")
            return

        col = layout.column(align=True)
        col.prop(obj, "tile_x", text="Tile X")
        col.prop(obj, "tile_y", text="Tile Y")
        col.prop(obj, "angle_degrees", text="Rotation (°)")
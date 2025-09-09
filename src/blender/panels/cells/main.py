bpy.types.Object.cell_type = bpy.props.EnumProperty(
    items = CELL_IMPORT,
    name = "Cell Type",
    description = "Select the type of cell"
)


class OBJECT_PT_CellTypePanel(bpy.types.Panel):
    bl_label = "Cell Type"
    bl_idname = "OBJECT_PT_cell_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "cell_type", text = "Cell Type")
        else:
            layout.label(text = "No active object")
            
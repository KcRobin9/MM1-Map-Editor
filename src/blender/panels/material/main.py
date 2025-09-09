bpy.types.Object.material_index = bpy.props.EnumProperty(
    items = MATERIAL_IMPORT,
    name = "Material Type",
    description = "Select the type of material"
)


class OBJECT_PT_MaterialTypePanel(bpy.types.Panel):
    bl_label = "Material Type"
    bl_idname = "OBJECT_PT_material_index"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context) -> None:
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "material_index", text = "Material")
        else:
            layout.label(text = "No active object")
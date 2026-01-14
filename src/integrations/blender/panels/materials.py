import bpy

from src.constants.file_formats import Material


MATERIAL_IMPORT = [
    (str(Material.DEFAULT), "Road", "", "", Material.DEFAULT),
    (str(Material.GRASS), "Grass", "", "", Material.GRASS),
    (str(Material.WATER), "Water", "", "", Material.WATER),
    (str(Material.STICKY), "Sticky", "", "", Material.STICKY),
    (str(Material.NO_FRICTION), "No Friction", "", "", Material.NO_FRICTION)
]

MATERIAL_EXPORT = {
    str(Material.GRASS): "Material.GRASS",
    str(Material.WATER): "Material.WATER",
    str(Material.STICKY): "Material.STICKY",
    str(Material.NO_FRICTION): "Material.NO_FRICTION"
}


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
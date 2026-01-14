import bpy

from src.constants.file_formats import Room


CELL_IMPORT = [
    (str(Room.DEFAULT), "Default", "", "", Room.DEFAULT),
    (str(Room.TUNNEL), "Tunnel", "", "", Room.TUNNEL),
    (str(Room.INDOORS), "Indoors", "", "", Room.INDOORS),
    (str(Room.DRIFT), "Drift", "", "", Room.DRIFT),
    (str(Room.NO_SKIDS), "No Skids", "", "", Room.NO_SKIDS)
    ]

CELL_EXPORT = {
    str(Room.TUNNEL): "Room.TUNNEL",
    str(Room.INDOORS): "Room.INDOORS",
    str(Room.DRIFT): "Room.DRIFT",
    str(Room.NO_SKIDS): "Room.NO_SKIDS"
}


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
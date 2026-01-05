import bpy
from src.constants.misc import Color


HUD_IMPORT = [
    (Color.ROAD, "Road", "", "", 1),
    (Color.GRASS, "Grass", "", "", 2),
    (Color.WATER, "Water", "", "", 3),
    (Color.SNOW, "Snow", "", "", 4),
    (Color.WOOD, "Wood", "", "", 5),
    (Color.ORANGE, "Orange", "", "", 6),
    (Color.RED_LIGHT, "Light Red", "", "", 7),
    (Color.RED_DARK, "Dark Red", "", "", 8),
    (Color.YELLOW_LIGHT, "Light Yellow", "", "", 9)
]

HUD_EXPORT = {
    # '#414441': "Color.ROAD",
    '#7b5931': "Color.WOOD",
    '#cdcecd': "Color.SNOW",
    '#5d8096': "Color.WATER",
    '#396d18': "Color.GRASS",
    '#af0000': "Color.RED_DARK",
    '#ffa500': "Color.ORANGE",
    '#ff7f7f': "Color.RED_LIGHT",
    '#ffffe0': "Color.YELLOW_LIGHT"
}


def set_hud_checkbox(color, obj):
    for i, (color_value, _, _, _, _) in enumerate(HUD_IMPORT):
        if color_value == color:
            obj.hud_colors[i] = True
            break


bpy.types.Object.hud_colors = bpy.props.BoolVectorProperty(
    name = "HUD Colors",
    description = "Select the color of the HUD",
    size = 9, 
    default = (False, False, False, False, False, False, False, False, False)
)


class OBJECT_PT_HUDColorPanel(bpy.types.Panel):
    bl_label = "HUD Type"
    bl_idname = "OBJECT_PT_hud_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            row = layout.row(align = True)
            col = row.column(align = True)
            half_length = len(HUD_IMPORT) // 2 + len(HUD_IMPORT) % 2
            
            for i, (_, name, _, _, _) in enumerate(HUD_IMPORT):
                if i == half_length:
                    col = row.column(align = True)
                
                col.prop(obj, "hud_colors", index = i, text = name, toggle = True)
        else:
            layout.label(text = "No active object")
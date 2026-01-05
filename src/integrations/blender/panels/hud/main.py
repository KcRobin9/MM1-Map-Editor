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
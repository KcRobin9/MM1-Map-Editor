bpy.types.Object.always_visible = bpy.props.BoolProperty(
    name = "Always Visible",
    description = "If true, the polygon is always visible",
    default = False
)


bpy.types.Object.sort_vertices = bpy.props.BoolProperty(
    name = "Sort Vertices",
    description = "If true, sort the vertices",
    default = False
)


class OBJECT_PT_PolygonMiscOptionsPanel(bpy.types.Panel):
    bl_label = "Polygon Options"
    bl_idname = "OBJECT_PT_polygon_options"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            layout.prop(obj, "always_visible", text = "Always Visible")
            layout.prop(obj, "sort_vertices", text = "Sort Vertices")
        else:
            layout.label(text = "No active object")
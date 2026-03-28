import bpy


class OBJECT_PT_PolygonMiscOptionsPanel(bpy.types.Panel):
    bl_label = "Polygon Options"
    bl_idname = "OBJECT_PT_polygon_options"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context) -> None:
        layout = self.layout
        obj = context.active_object

        if obj:
            layout.prop(obj, "always_visible", text="Always Visible")
            layout.prop(obj, "sort_vertices", text="Sort Vertices")
        else:
            layout.label(text="No active object")
import bpy


def update_vertex_coordinates(self, context):
    obj = self.id_data
    if obj and hasattr(obj.data, "vertices"):
        for index, coord in enumerate(obj.vertex_coords):
            if len(obj.data.vertices) > index:
                obj.data.vertices[index].co = (coord.x, coord.y, coord.z)
        obj.data.update()


class VertexGroup(bpy.types.PropertyGroup):
    x: bpy.props.FloatProperty(name = "X", update = update_vertex_coordinates)
    y: bpy.props.FloatProperty(name = "Y", update = update_vertex_coordinates)
    z: bpy.props.FloatProperty(name = "Z", update = update_vertex_coordinates)
    

class OBJECT_PT_VertexCoordinates(bpy.types.Panel):
    bl_label = "Vertices"
    bl_idname = "OBJECT_PT_vertex_coordinates"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        
        if obj:
            for vertex in obj.vertex_coords:
                col = layout.column(align = True)
                col.prop(vertex, "x")
                col.prop(vertex, "y")
                col.prop(vertex, "z")
        else:
            layout.label(text = "No active object")
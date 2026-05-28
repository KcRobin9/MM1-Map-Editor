import bpy


def update_vertex_coordinates(self, context):
    obj = self.id_data
    if obj and hasattr(obj.data, "vertices"):
        for index, coord in enumerate(obj.vertex_coords):
            if len(obj.data.vertices) > index:
                obj.data.vertices[index].co = (coord.x, coord.y, coord.z)
        obj.data.update()


class VertexGroup(bpy.types.PropertyGroup):
    x: bpy.props.FloatProperty(name="X", update=update_vertex_coordinates)
    y: bpy.props.FloatProperty(name="Y", update=update_vertex_coordinates)
    z: bpy.props.FloatProperty(name="Z", update=update_vertex_coordinates)


class VIEW3D_PT_MapEditorVertices(bpy.types.Panel):
    bl_label       = "Vertices"
    bl_idname      = "VIEW3D_PT_map_editor_vertices"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Map Editor"
    bl_parent_id   = "VIEW3D_PT_map_editor"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj.vertex_coords:
            layout.label(text="No vertex data", icon="INFO")
            return

        for i, vertex in enumerate(obj.vertex_coords):
            col = layout.column(align=True)
            col.label(text=f"V{i}")
            row = col.row(align=True)
            row.prop(vertex, "x")
            row.prop(vertex, "y")
            row.prop(vertex, "z")
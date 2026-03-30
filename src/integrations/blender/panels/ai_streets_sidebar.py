import bpy
from pyparsing import col
from src.integrations.blender.operators.ai_streets import get_all_streets, is_street, ST_PREFIX


class VIEW3D_PT_StreetEditorPanel(bpy.types.Panel):
    bl_label       = "Street"
    bl_idname      = "VIEW3D_PT_street_editor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Street Editor"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not is_street(obj):
            layout.label(text="Select a street curve", icon='INFO')
            layout.label(text=f"(curves named {ST_PREFIX}...)")
            return

        street_name = obj.name[len(ST_PREFIX):]
        layout.label(text=street_name, icon='CURVE_DATA')

        if obj.data.splines:
            num_verts = len(obj.data.splines[0].points)
            layout.label(text=f"{num_verts} vertices", icon='VERTEXSEL')

        layout.separator()
        layout.label(text="Press Tab to edit vertices", icon='INFO')


class VIEW3D_PT_StreetEditorIntersections(bpy.types.Panel):
    bl_label       = "Intersections"
    bl_idname      = "VIEW3D_PT_street_editor_intersections"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Street Editor"
    bl_parent_id   = "VIEW3D_PT_street_editor"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not is_street(obj):
            return

        col = layout.column(align=True)
        col.label(text="Start:")
        col.prop(obj, "st_intersection_0",    text="Type")
        col.prop(obj, "st_stop_light_name_0", text="Light")

        layout.separator()

        col = layout.column(align=True)
        col.label(text="End:")
        col.prop(obj, "st_intersection_1",    text="Type")
        col.prop(obj, "st_stop_light_name_1", text="Light")

        col.label(text="Stop Light Position:")
        col.prop(obj, "st_sl_pos_0_offset", text="Offset")
        col.prop(obj, "st_sl_pos_0_dir",    text="Direction")


class VIEW3D_PT_StreetEditorProperties(bpy.types.Panel):
    bl_label       = "Road Properties"
    bl_idname      = "VIEW3D_PT_street_editor_properties"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Street Editor"
    bl_parent_id   = "VIEW3D_PT_street_editor"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not is_street(obj):
            return

        col = layout.column(align=True)
        col.label(text="Traffic Blocked:")
        row = col.row(align=True)
        row.prop(obj, "st_traffic_blocked_0", text="Start", toggle=True)
        row.prop(obj, "st_traffic_blocked_1", text="End",   toggle=True)

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Ped Blocked:")
        row = col.row(align=True)
        row.prop(obj, "st_ped_blocked_0", text="Start", toggle=True)
        row.prop(obj, "st_ped_blocked_1", text="End",   toggle=True)

        layout.separator()
        col = layout.column(align=True)
        col.prop(obj, "st_road_divided", text="Road Divided", toggle=True)
        col.prop(obj, "st_alley",        text="Alley",        toggle=True)


class VIEW3D_PT_StreetEditorTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_street_editor_tools"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Street Editor"

    def draw(self, context):
        layout  = self.layout
        streets = get_all_streets()

        layout.label(text=f"Streets in scene: {len(streets)}", icon='CURVE_DATA')

        # Color legend
        box = layout.box()
        box.label(text="Color legend:", icon='COLOR')
        col = box.column(align=True)
        col.label(text="🔵  Continue")
        col.label(text="🟡  Stop Light")
        col.label(text="🟠  Yield")
        col.label(text="🔴  Stop")

        layout.separator()
        layout.label(text="Create", icon='ADD')
        row = layout.row(align=True)
        row.operator("object.create_ai_street",    text="New Street",  icon='CURVE_DATA')
        row.operator("object.duplicate_ai_street", text="Duplicate",   icon='DUPLICATE')

        layout.separator()
        layout.label(text="Load", icon='IMPORT')
        layout.operator("object.load_ai_streets_from_data", text="Load from ai_streets.py", icon='FILE_SCRIPT')

        layout.separator()
        layout.label(text="Export", icon='EXPORT')
        row = layout.row(align=True)
        op = row.operator("object.export_ai_streets", text="Selected", icon='RESTRICT_SELECT_OFF')
        op.export_all = False
        op = row.operator("object.export_ai_streets", text="All",      icon='WORLD')
        op.export_all = True

        layout.separator()
        layout.operator("object.refresh_street_colors", text="Refresh Colors", icon='COLOR')


STREET_EDITOR_CLASSES = [
    VIEW3D_PT_StreetEditorPanel,
    VIEW3D_PT_StreetEditorIntersections,
    VIEW3D_PT_StreetEditorProperties,
    VIEW3D_PT_StreetEditorTools,
]
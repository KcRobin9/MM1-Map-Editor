import bpy
from pyparsing import col
from src.integrations.blender.operators.ai_streets import (
    get_all_streets, get_street_vertices, get_street_vertex_count, is_street, ST_PREFIX,
)


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
            return

        street_name = obj.name[len(ST_PREFIX):]
        layout.label(text=street_name, icon='CURVE_DATA')

        n = get_street_vertex_count(obj)
        layout.label(text=f"{n} vertices  ·  {max(0, n - 1)} segments", icon='VERTEXSEL')

        layout.separator()
        layout.label(text="Shift+RMB to place 3D Cursor", icon='INFO')


class VIEW3D_PT_StreetVertexEditor(bpy.types.Panel):
    bl_label       = "Vertex Editor"
    bl_idname      = "VIEW3D_PT_street_vertex_editor"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Street Editor"
    bl_parent_id   = "VIEW3D_PT_street_editor"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not is_street(obj):
            return

        verts = get_street_vertices(obj)
        n     = len(verts)
        if n == 0:
            layout.label(text="No vertices", icon='ERROR')
            return

        # Clamp active index for display
        idx = max(0, min(context.scene.st_vertex_index, n - 1))
        v   = verts[idx]

        # ── Active vertex info ────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(context.scene, "st_vertex_index", text="Active V")
        row.label(text=f"/ {n - 1}")
        col.label(text=f"({v.x:.2f},  {v.y:.2f},  {v.z:.2f})")

        # ── Extend (append to start / end) ────────────────────────────────────
        layout.separator()
        layout.label(text="Extend Street  (cursor):", icon='CURVE_DATA')
        row = layout.row(align=True)
        op = row.operator("object.append_street_vertex", text="+ Start", icon='TRIA_LEFT')
        op.to_end = False
        op = row.operator("object.append_street_vertex", text="+ End",   icon='TRIA_RIGHT')
        op.to_end = True

        # ── Insert between vertices ───────────────────────────────────────────
        layout.separator()
        layout.label(text=f"Insert after V{idx}  (between V{idx} → V{min(idx + 1, n - 1)}):", icon='ADD')
        row = layout.row(align=True)
        row.operator("object.insert_street_vertex",          text="At Cursor",  icon='CURSOR')
        row.operator("object.insert_street_vertex_midpoint", text="Midpoint",   icon='SNAP_MIDPOINT')

        # ── Edit / delete active ──────────────────────────────────────────────
        layout.separator()
        layout.label(text=f"Edit V{idx}:", icon='VERTEXSEL')
        row = layout.row(align=True)
        row.operator("object.move_street_vertex_to_cursor", text="Move to Cursor", icon='CURSOR')
        row.operator("object.delete_street_vertex",         text="Delete",         icon='X')


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

        layout.separator()
        row = layout.row()
        row.prop(
            context.scene, "st_sl_pos_expanded",
            icon="TRIA_DOWN" if context.scene.st_sl_pos_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False,
        )
        row.label(text="Stop Light Position:")
        if context.scene.st_sl_pos_expanded:
            col2 = layout.column(align=True)
            col2.prop(obj, "st_sl_pos_0_offset", text="Offset")
            col2.prop(obj, "st_sl_pos_0_dir",    text="Direction")


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
        split = col.split(factor=0.55)
        split.label(text="Traffic Blocked (Start):")
        split.prop(obj, "st_traffic_blocked_0", text="")
        split = col.split(factor=0.55)
        split.label(text="Traffic Blocked (End):")
        split.prop(obj, "st_traffic_blocked_1", text="")

        layout.separator()
        col = layout.column(align=True)
        split = col.split(factor=0.55)
        split.label(text="Ped Blocked (Start):")
        split.prop(obj, "st_ped_blocked_0", text="")
        split = col.split(factor=0.55)
        split.label(text="Ped Blocked (End):")
        split.prop(obj, "st_ped_blocked_1", text="")

        layout.separator()
        col = layout.column(align=True)
        split = col.split(factor=0.55)
        split.label(text="Road Divided:")
        split.prop(obj, "st_road_divided", text="")
        split = col.split(factor=0.55)
        split.label(text="Alley:")
        split.prop(obj, "st_alley", text="")


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



STREET_EDITOR_CLASSES = [
    VIEW3D_PT_StreetEditorPanel,
    VIEW3D_PT_StreetVertexEditor,
    VIEW3D_PT_StreetEditorIntersections,
    VIEW3D_PT_StreetEditorProperties,
    VIEW3D_PT_StreetEditorTools,
]
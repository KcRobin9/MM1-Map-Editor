import bpy
from src.integrations.blender.operators.ai_streets import (
    get_all_streets, get_street_vertices, get_street_vertex_count, is_street, ST_PREFIX,
    _get_group_streets,
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
        row = layout.row()
        row.label(text=street_name, icon='CURVE_DATA')

        n = get_street_vertex_count(obj)
        layout.label(text=f"{n} vertices  ·  {max(0, n - 1)} segments", icon='VERTEXSEL')

        gname = getattr(obj, "st_group_name", "")
        if gname:
            lanes = _get_group_streets(obj)
            layout.label(text=f"Group: {gname}  ({len(lanes)} lanes)", icon='LINKED')



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

        idx        = max(0, min(context.scene.st_vertex_index, n - 1))
        v          = verts[idx]
        group_lanes = _get_group_streets(obj)
        is_group    = len(group_lanes) >= 2

        # ── Active vertex ─────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(context.scene, "st_vertex_index", text="Active V")
        row.label(text=f"/ {n - 1}")
        col.label(text=f"({v.x:.2f},  {v.y:.2f},  {v.z:.2f})")
        row2 = col.row(align=True)
        row2.operator("object.cursor_to_street_vertex",  text="Cursor → Vertex", icon='CURSOR')
        row2.operator("object.reverse_street_direction", text="Reverse",          icon='ARROW_LEFTRIGHT')

        # ── Group context (separator + select, only when grouped) ─────────────
        if is_group:
            box2 = layout.box()
            col2 = box2.column(align=True)
            col2.label(text=f"Group: {obj.st_group_name}  ({len(group_lanes)} lanes)", icon='LINKED')
            col2.label(text="● Start = green   ● End = orange", icon='HIDE_OFF')
            col2.prop(context.scene, "st_preset_lane_separator", text="Separator")
            col2.operator("object.select_street_group", text="Select All Lanes", icon='RESTRICT_SELECT_OFF')

        # ── Extend settings (shared by all extend buttons below) ──────────────
        layout.separator()
        layout.label(text="Extend Settings:", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        box = layout.box()
        col = box.column(align=True)
        col.prop(context.scene, "st_extend_length",    text="Length")
        col.prop(context.scene, "st_extend_angle",     text="Angle (°)")
        col.prop(context.scene, "st_extend_elevation", text="Elevation (°)")

        # ── Extend — label and operators adapt to single vs group ─────────────
        layout.separator()
        if is_group:
            layout.label(text=f"Extend Group  ({len(group_lanes)} lanes):", icon='CURVE_DATA')
        else:
            layout.label(text="Extend Street:", icon='CURVE_DATA')

        col = layout.column(align=True)
        col.label(text="By parameters  (L / A / E):")
        row = col.row(align=True)
        if is_group:
            op = row.operator("object.extend_street_group_angle", text="← Start", icon='TRIA_LEFT')
            op.to_end = False; op.angle_offset = context.scene.st_extend_angle
            op = row.operator("object.extend_street_group_angle", text="End →",   icon='TRIA_RIGHT')
            op.to_end = True;  op.angle_offset = context.scene.st_extend_angle
        else:
            op = row.operator("object.extend_street_angle", text="← Start", icon='TRIA_LEFT')
            op.to_end = False; op.angle_offset = context.scene.st_extend_angle
            op = row.operator("object.extend_street_angle", text="End →",   icon='TRIA_RIGHT')
            op.to_end = True;  op.angle_offset = context.scene.st_extend_angle

        col.label(text="At cursor:")
        row = col.row(align=True)
        if is_group:
            op = row.operator("object.append_street_group_vertex", text="← Start", icon='TRIA_LEFT')
            op.to_end = False
            op = row.operator("object.append_street_group_vertex", text="End →",   icon='TRIA_RIGHT')
            op.to_end = True
        else:
            op = row.operator("object.append_street_vertex", text="← Start", icon='TRIA_LEFT')
            op.to_end = False
            op = row.operator("object.append_street_vertex", text="End →",   icon='TRIA_RIGHT')
            op.to_end = True

        # ── Insert — also adapts ──────────────────────────────────────────────
        layout.separator()
        next_idx = min(idx + 1, n - 1)
        layout.label(text=f"Insert after V{idx}  →  V{next_idx}:", icon='ADD')
        row = layout.row(align=True)
        if is_group:
            op = row.operator("object.insert_street_group_vertex", text="At Cursor", icon='CURSOR')
            op.at_cursor = True
            op = row.operator("object.insert_street_group_vertex", text="Midpoint",  icon='SNAP_MIDPOINT')
            op.at_cursor = False
        else:
            row.operator("object.insert_street_vertex",          text="At Cursor", icon='CURSOR')
            row.operator("object.insert_street_vertex_midpoint", text="Midpoint",  icon='SNAP_MIDPOINT')

        # ── Edit active vertex ────────────────────────────────────────────────
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

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Group Name:")
        col.prop(obj, "st_group_name", text="")


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
        layout.prop(context.scene, "st_show_arrows",
                    text="Show Direction Arrows", icon='DRIVER_ROTATIONAL_DIFFERENCE', toggle=True)

        # ── Create ────────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Create", icon='ADD')
        row = layout.row(align=True)
        row.operator("object.create_ai_street",    text="New Street", icon='CURVE_DATA')
        row.operator("object.duplicate_ai_street", text="Duplicate",  icon='DUPLICATE')

        # ── Presets ───────────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Presets", icon='PRESET')
        box = layout.box()
        col = box.column(align=True)
        col.prop(context.scene, "st_street_preset", text="Preset")

        col.separator()
        col.label(text="Geometry:")
        col.prop(context.scene, "st_preset_length",       text="Tot. Length")
        col.prop(context.scene, "st_preset_length_split", text="Split Length")
        col.prop(context.scene, "st_preset_turn_radius",  text="Turn Radius")
        vcount_row = col.row()
        vcount_row.active = (context.scene.st_preset_length_split == 0.0)
        vcount_row.prop(context.scene, "st_preset_curve_points", text="Vertex Count")

        col.separator()
        col.label(text="Lanes:")
        col.prop(context.scene, "st_preset_lanes",          text="Count")
        col.prop(context.scene, "st_preset_lane_separator", text="Separator")

        col.separator()
        col.label(text="Options:")
        col.prop(context.scene, "st_preset_grouped",
                 text="Grouped Street (multi-lane export)", toggle=True)
        multi = context.scene.st_preset_lanes > 1
        r2 = col.row(align=True)
        r2.active = multi
        r2.prop(context.scene, "st_preset_converge_start", text="Converge Start", toggle=True)
        r2.prop(context.scene, "st_preset_converge_end",   text="Converge End",   toggle=True)

        layout.operator("object.spawn_street_preset", text="Spawn Preset", icon='IMPORT')

        # ── Load / Delete ─────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="Load", icon='IMPORT')
        layout.operator("object.load_ai_streets_from_data",
                        text="Load from ai_streets.py", icon='FILE_SCRIPT')
        layout.operator("object.delete_all_streets",
                        text="Delete All Streets",      icon='TRASH')

        # ── Export ────────────────────────────────────────────────────────────
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

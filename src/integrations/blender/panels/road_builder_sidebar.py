import bpy
from src.integrations.blender.operators.road_builder import (
    is_road_spine, get_all_road_spines, get_spine_vertices,
    RS_BAKED_TAG, ROAD_TYPE_ITEMS, _RS_LIFT_KEY, _RS_LIFT_STEP, _RS_LIFT_MIN, _RS_LIFT_MAX,
)


class VIEW3D_PT_RoadBuilderPanel(bpy.types.Panel):
    bl_label       = "Road Builder"
    bl_idname      = "VIEW3D_PT_road_builder"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Road Builder"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object
        spines = get_all_road_spines()

        row = layout.row(align=True)
        row.label(text=f"{len(spines)} spine(s)", icon='CURVE_DATA')
        row.operator("object.create_road_spine", text="New Spine", icon='ADD')

        if obj and is_road_spine(obj):
            layout.separator()
            verts      = get_spine_vertices(obj)
            segs       = max(0, len(verts) - 1)
            baked      = len([o for o in bpy.data.objects if o.get(RS_BAKED_TAG) == obj.name])
            row = layout.row()
            row.label(text=obj.name, icon='CURVE_PATH')
            layout.label(text=f"{len(verts)} vertices · {segs} segment(s) · {baked} polygon(s) baked")


class VIEW3D_PT_RoadBuilderSpine(bpy.types.Panel):
    bl_label       = "Spine Editor"
    bl_idname      = "VIEW3D_PT_road_builder_spine"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Road Builder"
    bl_parent_id   = "VIEW3D_PT_road_builder"

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        obj    = context.active_object

        if not obj or not is_road_spine(obj):
            layout.label(text="Select a road spine", icon='INFO')
            return

        # ── Extend controls ────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Extend", icon='TRACKING_FORWARDS_SINGLE')
        col = box.column(align=True)
        col.prop(scene, "rd_extend_length",    text="Length")
        col.prop(scene, "rd_extend_angle",     text="Turn Angle (°)")
        sub = col.column()
        sub.enabled = not scene.rd_snap_to_terrain
        sub.prop(scene, "rd_extend_elevation", text="Slope (°)")
        col.prop(scene, "rd_snap_to_terrain",  text="Snap to Terrain", icon='SNAP_NORMAL')

        row = box.row(align=True)
        op = row.operator("object.extend_road_spine", text="← Start", icon='COLORSET_03_VEC')
        op.to_end = False
        op = row.operator("object.extend_road_spine", text="End →",   icon='COLORSET_01_VEC')
        op.to_end = True

        row2 = box.row(align=True)
        op = row2.operator("object.remove_road_spine_vertex", text="Undo Start →", icon='BACK')
        op.from_end = False
        op = row2.operator("object.remove_road_spine_vertex", text="← Undo End",   icon='FORWARD')
        op.from_end = True

        # ── Cursor append ──────────────────────────────────────────────────
        box2 = layout.box()
        box2.label(text="Cursor", icon='CURSOR')
        row = box2.row(align=True)
        op = row.operator("object.append_road_spine_vertex", text="← Cursor Start", icon='COLORSET_03_VEC')
        op.to_end = False
        op = row.operator("object.append_road_spine_vertex", text="Cursor End →",   icon='COLORSET_01_VEC')
        op.to_end = True

        # ── Lift ───────────────────────────────────────────────────────────
        lift_z = obj.get(_RS_LIFT_KEY, 0.0)
        box3 = layout.box()
        row  = box3.row(align=True)
        row.label(text=f"Lift: {lift_z:+.0f}", icon='ORIENTATION_GLOBAL')
        up_row = row.row(align=True)
        up_row.enabled = lift_z < _RS_LIFT_MAX
        op = up_row.operator("object.lift_road_spine", text="", icon='TRIA_UP')
        op.delta = _RS_LIFT_STEP
        dn_row = row.row(align=True)
        dn_row.enabled = lift_z > _RS_LIFT_MIN
        op = dn_row.operator("object.lift_road_spine", text="", icon='TRIA_DOWN')
        op.delta = -_RS_LIFT_STEP
        if lift_z != 0.0:
            op = row.operator("object.lift_road_spine", text="", icon='LOOP_BACK')
            op.delta = -lift_z

        # ── Delete ─────────────────────────────────────────────────────────
        layout.separator()
        layout.operator("object.delete_road_spine", text="Delete Spine + Polygons", icon='TRASH')


class VIEW3D_PT_RoadBuilderCrossSection(bpy.types.Panel):
    bl_label       = "Cross-Section"
    bl_idname      = "VIEW3D_PT_road_builder_cross"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Road Builder"
    bl_parent_id   = "VIEW3D_PT_road_builder"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj or not is_road_spine(obj):
            layout.label(text="Select a road spine", icon='INFO')
            return

        # Quick preset row
        row = layout.row(align=True)
        row.prop(context.scene, "rd_road_type", text="")
        row.operator("object.apply_road_type_preset", text="Apply", icon='IMPORT')
        row.operator("object.reset_road_spine",       text="Reset", icon='LOOP_BACK')
        layout.separator()

        # ── Road ──────────────────────────────────────────────────────────
        box = layout.box()
        hdr = box.row(align=True)
        hdr.prop(obj, "rs_road_enabled", text="")
        hdr.label(text="Road", icon='MESH_PLANE')
        sub = box.column(align=True)
        sub.enabled = obj.rs_road_enabled
        sub.prop(obj, "rs_road_texture", text="Texture")
        sub.prop(obj, "rs_lane_count", text="Lanes")
        sub.prop(obj, "rs_lane_width", text="Lane Width")
        sub.prop(obj, "rs_road_tile_x", text="Tile X")
        sub.prop(obj, "rs_road_tile_y", text="Tile Y")
        sub.prop(obj, "rs_road_angle", text="Angle (°)")

        # ── Sidewalk ──────────────────────────────────────────────────────
        box = layout.box()
        hdr = box.row(align=True)
        hdr.prop(obj, "rs_sidewalk_enabled", text="")
        hdr.label(text="Sidewalk", icon='MESH_GRID')
        sub = box.column(align=True)
        sub.enabled = obj.rs_sidewalk_enabled
        sub.prop(obj, "rs_sidewalk_texture", text="Texture")
        sub.prop(obj, "rs_sidewalk_side",    text="Side")
        sub.prop(obj, "rs_sidewalk_width",  text="Width")
        sub.prop(obj, "rs_sidewalk_height", text="Height")
        sub.prop(obj, "rs_sidewalk_tile_x", text="Tile X")
        sub.prop(obj, "rs_sidewalk_tile_y", text="Tile Y")
        sub.prop(obj, "rs_sidewalk_angle", text="Angle (°)")

        # ── Wall (outer barrier) ──────────────────────────────────────────
        box = layout.box()
        hdr = box.row(align=True)
        hdr.prop(obj, "rs_wall_enabled", text="")
        hdr.label(text="Wall / Barrier", icon='MOD_SOLIDIFY')
        sub = box.column(align=True)
        sub.enabled = obj.rs_wall_enabled
        sub.prop(obj, "rs_wall_texture", text="Texture")
        sub.prop(obj, "rs_wall_side",    text="Side")
        sub.prop(obj, "rs_wall_height",  text="Height")
        sub.prop(obj, "rs_wall_tile_x", text="Tile X")
        sub.prop(obj, "rs_wall_tile_y", text="Tile Y")
        sub.prop(obj, "rs_wall_angle",  text="Angle (°)")

        # ── Curb ──────────────────────────────────────────────────────────
        box = layout.box()
        hdr = box.row(align=True)
        hdr.prop(obj, "rs_curb_enabled", text="")
        hdr.label(text="Curb", icon='SNAP_EDGE')
        sub = box.column(align=True)
        sub.enabled = obj.rs_curb_enabled
        sub.prop(obj, "rs_curb_texture", text="Texture")
        sub.prop(obj, "rs_curb_width",  text="Width")
        sub.prop(obj, "rs_curb_height", text="Height")
        sub.prop(obj, "rs_curb_tile_x", text="Tile X")
        sub.prop(obj, "rs_curb_tile_y", text="Tile Y")
        sub.prop(obj, "rs_curb_angle", text="Angle (°)")

        # ── Median ────────────────────────────────────────────────────────
        box = layout.box()
        hdr = box.row(align=True)
        hdr.prop(obj, "rs_median_enabled", text="")
        hdr.label(text="Median Divider", icon='MOD_BEVEL')
        sub = box.column(align=True)
        sub.enabled = obj.rs_median_enabled
        sub.prop(obj, "rs_median_texture", text="Texture")
        sub.prop(obj, "rs_median_width", text="Width")

        # ── Banking ───────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Banking", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        col = box.column(align=True)
        col.prop(obj, "rs_banking_auto",    text="Auto-bank on Curves")
        sub = col.column()
        sub.enabled = obj.rs_banking_auto
        sub.prop(obj, "rs_banking_max_deg", text="Max Degrees")


class VIEW3D_PT_RoadBuilderBake(bpy.types.Panel):
    bl_label       = "Bake"
    bl_idname      = "VIEW3D_PT_road_builder_bake"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Road Builder"
    bl_parent_id   = "VIEW3D_PT_road_builder"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if not obj or not is_road_spine(obj):
            layout.label(text="Select a road spine", icon='INFO')
            return

        verts  = get_spine_vertices(obj)
        segs   = max(0, len(verts) - 1)
        baked  = len([o for o in bpy.data.objects if o.get(RS_BAKED_TAG) == obj.name])

        col = layout.column(align=True)

        if baked > 0:
            col.label(text=f"{baked} polygon(s) currently baked", icon='CHECKMARK')
            col.operator("object.rebake_road_mesh",  text=f"Re-bake ({segs} seg × zones)", icon='FILE_REFRESH')
            col.separator()
            col.operator("object.clear_baked_road",  text="Clear Baked Polygons", icon='X')
        else:
            if segs == 0:
                col.label(text="Spine needs at least 2 vertices", icon='ERROR')
            else:
                col.label(text=f"{segs} segment(s) ready to bake", icon='INFO')
            col.operator("object.bake_road_mesh",    text="Bake Road →  Polygons", icon='MOD_BUILD')


ROAD_BUILDER_PANEL_CLASSES = [
    VIEW3D_PT_RoadBuilderPanel,
    VIEW3D_PT_RoadBuilderSpine,
    VIEW3D_PT_RoadBuilderCrossSection,
    VIEW3D_PT_RoadBuilderBake,
]

"""
Car Editor sidebar panels.  Tab: "Car Editor"  (VIEW_3D → N-panel)

Panels:
  1. Car Inspector   – collapsed by default; shows loaded parts + selected part details
  2. Tools           – Load / Export / Reload
  3. Face Editor     – face navigation, texture picker, UV tiling/rotation
  4. Add Geometry    – add quad/tri, add texture slot
"""
import bpy
from pathlib import Path
from src.integrations.blender.operators.car_editor import (
    is_car_obj, get_car_objects, get_car_body, _CAR_TAG,
    _find_paint_variants_cached, _variant_color_name,
)
from src.constants.folder import Folder

_CATEGORY = "Car Editor"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _part_label(part_tag: str) -> str:
    if part_tag == "body":          return "Body"
    if part_tag.startswith("wheel_"):   return f"Wheel {part_tag.split('_')[1]}"
    if part_tag.startswith("fender_"):  return f"Fender {part_tag.split('_')[1]}"
    if part_tag.startswith("light_"):   return f"Light ({part_tag[6:]})"
    return part_tag.replace("_", " ").title()


def _part_icon(part_tag: str) -> str:
    if part_tag == "body":              return "OUTLINER_OB_MESH"
    if part_tag.startswith("wheel_"):   return "MESH_CIRCLE"
    if part_tag.startswith("fender_"):  return "MOD_SOLIDIFY"
    if part_tag.startswith("light_"):   return "LIGHT"
    return "OBJECT_DATA"


# ── Panel 1: Car Inspector (collapsed by default) ─────────────────────────────

class VIEW3D_PT_CarEditorPanel(bpy.types.Panel):
    bl_label       = "Car Inspector"
    bl_idname      = "VIEW3D_PT_car_editor"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout   = self.layout
        obj      = context.active_object
        car_objs = get_car_objects()
        body_obj = get_car_body()

        if not car_objs:
            layout.label(text="No car loaded - use Tools → Load Car", icon="INFO")
            return

        car_name  = body_obj["mm_car_name"] if body_obj else "Unknown"
        n_wheels  = sum(1 for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_"))
        n_fenders = sum(1 for o in car_objs if o.get(_CAR_TAG, "").startswith("fender_"))

        col = layout.column(align=True)
        col.label(text=f"{car_name}  ·  {len(car_objs)} parts", icon="AUTO")
        summary = f"Wheels: {n_wheels}"
        if n_fenders:
            summary += f"   Fenders: {n_fenders}"
        col.label(text=summary, icon="BLANK1")

        layout.separator(factor=0.5)

        # Selected part details
        if is_car_obj(obj):
            part_tag = obj.get(_CAR_TAG, "?")
            src_file = obj.data.get("bms_source_file", "?")
            n_verts  = len(obj.data.vertices)
            n_faces  = len(obj.data.polygons)
            box = layout.box()
            col = box.column(align=True)
            col.label(text=_part_label(part_tag), icon=_part_icon(part_tag))
            col.label(text=f"{bpy.path.basename(src_file)}  ·  {n_verts}v  {n_faces}f",
                      icon="MESH_DATA")

        layout.separator(factor=0.5)

        # Parts list
        col = layout.column(align=True)
        for o in sorted(car_objs, key=lambda x: x.get(_CAR_TAG, "")):
            tag  = o.get(_CAR_TAG, "?")
            mark = "  ←" if o == obj else ""
            col.label(text=f"{_part_label(tag)}{mark}", icon=_part_icon(tag))


# ── Panel 2: Tools ────────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_car_editor_tools"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Load ──────────────────────────────────────────────────────────────
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("car.load_car",  text="Load Car",  icon="FILE_FOLDER")
        row.operator("car.clear_car", text="Clear",     icon="X")
        sub = col.row()
        sub.enabled = False
        body_slug = get_car_body()
        car_slug  = body_slug["mm_car_name"] if body_slug else "..."
        sub.label(text=f"resources/editor/MESHES/CARS/{car_slug}", icon="FILE_FOLDER")

        layout.separator(factor=0.8)

        # ── Car name + export settings ────────────────────────────────────────
        body_obj = get_car_body()
        car_name = body_obj["mm_car_name"] if body_obj else "..."

        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Car Name:", icon="AUTO")
        row.label(text=car_name)

        col.prop(scene, "ce_add_to_city", text="Add to City  (SHOP/BMS/<name>)")

        sub = col.row()
        sub.enabled = False
        import datetime as _dt
        _ts = _dt.datetime.now().strftime("%Y_%d_%m_%H%M_%S")
        sub.label(text=f"blender_export/cars/{car_name}_{_ts}",
                  icon="FILE_FOLDER")

        layout.separator(factor=0.5)
        col = layout.column(align=True)
        col.prop(scene, "ce_load_lights",   text="Load Lights")
        col.prop(scene, "ce_auto_reload",   text="Auto-Reload After Export")

        layout.separator(factor=0.5)

        # ── Paint Job / Colour Variants ───────────────────────────────────────
        has_car = bool(get_car_objects())
        if has_car and body_obj:
            tf_str     = scene.ce_texture_folder
            tex_folder = Path(tf_str) if tf_str else Folder.Resources.Editor.Textures
            current    = scene.ce_paint_variant
            variants   = _find_paint_variants_cached(
                body_obj["mm_car_name"], body_obj.data, tex_folder, current
            )

            if variants:
                col = layout.column(align=True)
                col.label(text="Paint Job:", icon="COLOR")
                try:
                    cur_idx = variants.index(current)
                except ValueError:
                    cur_idx = 0

                color_label = _variant_color_name(current, variants)
                row = col.row(align=True)
                prev_op         = row.operator("car.set_paint_variant", text="", icon="TRIA_LEFT")
                prev_op.variant = variants[(cur_idx - 1) % len(variants)]
                row.label(text=f"{color_label}  ({cur_idx + 1} / {len(variants)})")
                next_op         = row.operator("car.set_paint_variant", text="", icon="TRIA_RIGHT")
                next_op.variant = variants[(cur_idx + 1) % len(variants)]

        layout.separator(factor=0.5)

        # ── Damage toggle ─────────────────────────────────────────────────────
        has_car = bool(get_car_objects())
        row = layout.row(align=True)
        row.enabled = has_car
        dmg_icon = "FREEZE" if scene.ce_show_damage else "OUTLINER_OB_ARMATURE"
        row.operator(
            "car.toggle_damage",
            text="Damage ON" if scene.ce_show_damage else "Damage OFF",
            icon=dmg_icon,
            depress=scene.ce_show_damage,
        )

        layout.separator(factor=0.8)

        # ── Export / Launch ───────────────────────────────────────────────────
        has_car      = bool(get_car_objects())
        has_last_exp = bool(scene.ce_last_export_dir.strip())

        col = layout.column(align=True)

        # Main export button — label changes when "Start Game" is armed
        row = col.row(align=True)
        row.enabled = has_car
        if scene.ce_start_game:
            row.operator("car.export_car", text="Export BMS + Start Game", icon="PLAY")
        else:
            row.operator("car.export_car", text="Export to BMS", icon="FILE_TICK")

        # Start Game toggle inline with Reload (disabled when Add to City is off)
        row2 = col.row(align=True)
        row2.enabled = has_car and scene.ce_add_to_city
        row2.prop(scene, "ce_start_game", text="", icon="PLAY", toggle=True)
        sub2 = row2.row()
        sub2.enabled = has_last_exp
        sub2.operator("car.reload_car", text="Reload Exported", icon="FILE_REFRESH")

        if has_last_exp:
            from pathlib import Path as _P
            exp_path = _P(scene.ce_last_export_dir)
            sub = col.row()
            sub.enabled = False
            sub.label(text=exp_path.name, icon="TIME")
            # "Open folder" shortcut
            op_row = col.row(align=True)
            op_row.operator("car.open_export_folder", text="Open in Explorer", icon="FILE_FOLDER")


# ── Helpers for face info ─────────────────────────────────────────────────────

def _get_active_face_info(obj):
    """Return (face_index, mat_index, mat_name, n_verts) or None."""
    if obj is None or obj.type != "MESH" or obj.mode != "EDIT":
        return None
    import bmesh as _bm
    bm = _bm.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    face = bm.faces.active
    if face is None:
        for f in bm.faces:
            if f.select:
                face = f
                break
    if face is None:
        return None
    mat_idx  = face.material_index
    mat_name = ""
    mats = obj.data.materials
    if mat_idx < len(mats) and mats[mat_idx]:
        mat_name = mats[mat_idx].name
    return (face.index, mat_idx, mat_name, len(face.verts))


# ── Panel 3: Face Editor ──────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorFaceUV(bpy.types.Panel):
    bl_label       = "Face Editor"
    bl_idname      = "VIEW3D_PT_car_editor_face_uv"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout  = self.layout
        scene   = context.scene
        obj     = context.active_object
        is_car  = is_car_obj(obj)
        in_edit = is_car and obj.mode == "EDIT"

        if not is_car:
            layout.label(text="Select a car part", icon="INFO")
            return

        if not in_edit:
            layout.label(text="Tab into Edit Mode, then select a face.")
            return

        # ── Face navigator ────────────────────────────────────────────────────
        face_info = _get_active_face_info(obj)
        n_faces   = len(obj.data.polygons)

        row = layout.row(align=True)
        row.operator("car.select_face", text="", icon="TRIA_LEFT").direction  = "PREV"
        if face_info:
            shape = "Tri" if face_info[3] == 3 else "Quad"
            row.label(text=f"Face {face_info[0]}  ({shape})  /  {n_faces}")
        else:
            row.label(text=f"No face selected  ({n_faces} faces)")
        row.operator("car.select_face", text="", icon="TRIA_RIGHT").direction = "NEXT"

        layout.separator(factor=0.5)

        # ── Texture ───────────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Texture:", icon="MATERIAL")
        col.prop(scene, "ce_face_texture", text="")

        layout.separator(factor=0.5)

        # ── UV Tiling / Rotation ──────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="UV / Tiling:", icon="UV")
        row = col.row(align=True)
        row.prop(scene, "ce_face_tile_x", text="X")
        row.prop(scene, "ce_face_tile_y", text="Y")
        col.prop(scene, "ce_face_rotation", text="Rotation")


# ── Panel 4: Add Geometry ─────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorGeometry(bpy.types.Panel):
    bl_label       = "Add / Remove Geometry"
    bl_idname      = "VIEW3D_PT_car_editor_geometry"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        obj    = context.active_object
        is_car = is_car_obj(obj)
        in_edit = is_car and obj is not None and obj.mode == "EDIT"

        # ── Add face at cursor ────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Face at Cursor:", icon="MESH_PLANE")
        row = col.row(align=True)
        row.prop(scene, "ce_add_shape", expand=True)
        col.prop(scene, "ce_add_size",     text="Size")
        col.prop(scene, "ce_assign_slot",  text="Texture Slot")
        col.separator(factor=0.5)
        row = col.row()
        row.enabled = is_car
        row.operator("car.add_face", text="Add Face", icon="ADD")

        layout.separator(factor=0.8)

        # ── Delete selected faces ─────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Delete:", icon="TRASH")
        row = col.row()
        row.enabled = in_edit
        row.operator("mesh.delete", text="Delete Selected Faces", icon="TRASH").type = "FACE"

        layout.separator(factor=0.8)

        # ── Add texture slot ──────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Texture Slot:", icon="TEXTURE")
        col.prop(scene, "ce_new_tex_name", text="")
        row = col.row()
        row.enabled = is_car
        row.operator("car.add_texture_slot", text="Add Slot", icon="ADD")


# ── Panel 5: Wheels ───────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorWheels(bpy.types.Panel):
    bl_label       = "Wheels"
    bl_idname      = "VIEW3D_PT_car_editor_wheels"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout   = self.layout
        scene    = context.scene
        car_objs = get_car_objects()
        has_car  = bool(car_objs)

        if not has_car:
            layout.label(text="No car loaded", icon="INFO")
            return

        # Collect wheels sorted by index
        wheels = sorted(
            [o for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_")],
            key=lambda o: int(o.get(_CAR_TAG, "wheel_0").split("_")[1])
        )
        active_obj = context.active_object
        active_tag = active_obj.get(_CAR_TAG, "") if active_obj else ""
        is_wheel   = active_tag.startswith("wheel_")

        # ── Wheel list ────────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text=f"Wheels: {len(wheels)}", icon="MESH_CIRCLE")
        for whl in wheels:
            tag   = whl.get(_CAR_TAG, "")
            idx   = tag.split("_")[1] if "_" in tag else "?"
            loc   = whl.location
            mark  = "  ←" if whl == active_obj else ""
            gx, gy, gz = -loc.x, loc.z, loc.y
            row   = col.row(align=True)
            row.label(
                text=f"WHL{idx}  ({gx:.3f}, {gy:.3f}, {gz:.3f}){mark}",
                icon="MESH_CIRCLE",
            )

        layout.separator(factor=0.8)

        # ── Add wheel ─────────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Wheel at 3D Cursor:", icon="ADD")

        row2 = col.row()
        row2.enabled = has_car
        op = row2.operator("car.add_wheel", text="Add Wheel", icon="ADD")
        op.copy_from = 0

        layout.separator(factor=0.5)
        col.label(text="Move the new wheel to the desired position.", icon="INFO")

        layout.separator(factor=0.8)

        # ── Remove / renumber ─────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Remove / Fix:", icon="TRASH")
        row = col.row(align=True)
        row.enabled = is_wheel
        row.operator("car.remove_wheel",    text="Remove Selected Wheel", icon="TRASH")
        col.operator("car.renumber_wheels", text="Renumber Wheels (fill gaps)", icon="SORTALPHA")


# ── Registration list ─────────────────────────────────────────────────────────

CAR_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_CarEditorPanel,
    VIEW3D_PT_CarEditorTools,
    VIEW3D_PT_CarEditorFaceUV,
    VIEW3D_PT_CarEditorGeometry,
    VIEW3D_PT_CarEditorWheels,
]

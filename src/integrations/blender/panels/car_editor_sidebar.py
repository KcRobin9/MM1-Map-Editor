"""Car Editor sidebar panels.  Tab: "Car Editor"  (VIEW_3D → N-panel)

Panels:
  1. Car    – load/clear, parts list, settings, paint job, export
  2. Edit   – damage/symmetry toggles, face editor, UV tiling, add geometry
  3. Wheels – per-wheel textures, spawn, mirror, remove
  4. Create – new from template + import external (collapsed)
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
    if part_tag == "body":              return "Body"
    if part_tag.startswith("wheel_"):  return f"Wheel {part_tag.split('_')[1]}"
    if part_tag.startswith("fender_"): return f"Fender {part_tag.split('_')[1]}"
    if part_tag.startswith("light_"):  return f"Light ({part_tag[6:]})"
    return part_tag.replace("_", " ").title()


def _part_icon(part_tag: str) -> str:
    if part_tag == "body":              return "OUTLINER_OB_MESH"
    if part_tag.startswith("wheel_"):  return "MESH_CIRCLE"
    if part_tag.startswith("fender_"): return "MOD_SOLIDIFY"
    if part_tag.startswith("light_"):  return "LIGHT"
    return "OBJECT_DATA"


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
    mat_name = ""
    mats = obj.data.materials
    if face.material_index < len(mats) and mats[face.material_index]:
        mat_name = mats[face.material_index].name
    return (face.index, face.material_index, mat_name, len(face.verts))


# ── Panel 1: Car ──────────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorCar(bpy.types.Panel):
    bl_label       = "Car"
    bl_idname      = "VIEW3D_PT_car_editor_car"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout   = self.layout
        scene    = context.scene
        obj      = context.active_object
        car_objs = get_car_objects()
        body_obj = get_car_body()
        has_car  = bool(car_objs)

        # ── Load / Clear ──────────────────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("car.load_car",  text="Load Car", icon="FILE_FOLDER")
        row.operator("car.clear_car", text="Clear",    icon="X")

        trow = layout.row(align=True)
        trow.enabled = has_car
        trow.operator("car.load_trailer", text="Load Trailer", icon="AUTO")

        if has_car:
            layout.separator(factor=0.5)

            # ── Car name + parts list ─────────────────────────────────────────
            car_name = body_obj["mm_car_name"] if body_obj else "Unknown"
            n_wheels = sum(1 for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_"))

            row = layout.row()
            row.label(text=car_name, icon="AUTO")
            row.label(text=f"{len(car_objs)} parts  ·  {n_wheels} wheels")

            col = layout.column(align=True)
            for o in sorted(car_objs, key=lambda x: x.get(_CAR_TAG, "")):
                tag = o.get(_CAR_TAG, "?")
                r   = col.row(align=True)
                op  = r.operator("car.select_part", text=_part_label(tag),
                                 icon=_part_icon(tag), depress=(o == obj))
                op.part_tag = tag

            # ── Selected part details ─────────────────────────────────────────
            if is_car_obj(obj):
                part_tag = obj.get(_CAR_TAG, "?")
                box = layout.box()
                row = box.row()
                row.label(text=_part_label(part_tag), icon=_part_icon(part_tag))
                row.label(text=f"{len(obj.data.vertices)}v  {len(obj.data.polygons)}f")

            layout.separator(factor=0.5)

            # ── Paint Job (contextual) ────────────────────────────────────────
            if body_obj:
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

        # ── Settings ──────────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.prop(scene, "ce_add_to_city",  text="Add to City  (SHOP/BMS/<name>)")
        col.prop(scene, "ce_load_lights",  text="Load Lights")
        col.prop(scene, "ce_auto_reload",  text="Auto-Reload After Export")
        col.prop(scene, "ce_add_trailer",  text="Add Trailer  (stock semi trailer)")

        layout.separator(factor=0.6)

        # ── Export ────────────────────────────────────────────────────────────
        has_last_exp = bool(scene.ce_last_export_dir.strip())

        col = layout.column(align=True)
        row = col.row(align=True)
        row.enabled = has_car
        row.operator("car.export_car",        text="Export BMS",  icon="FILE_TICK")
        row.operator("car.pack_and_start_game", text="AR + Launch", icon="PLAY")

        row2 = col.row(align=True)
        row2.enabled = has_last_exp
        row2.operator("car.reload_car", text="Reload Exported", icon="FILE_REFRESH")

        if has_last_exp:
            exp_path = Path(scene.ce_last_export_dir)
            sub = col.row()
            sub.enabled = False
            sub.label(text=exp_path.name, icon="TIME")
            col.operator("car.open_export_folder", text="Open in Explorer", icon="FILE_FOLDER")

        row3 = col.row(align=True)
        row3.enabled = has_car
        row3.operator("car.clear_shop", text="Clear Shop", icon="TRASH")
        row3.operator("car.debug_bms",  text="Debug BMS",  icon="INFO")


# ── Panel 2: Edit ─────────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorEdit(bpy.types.Panel):
    bl_label       = "Edit"
    bl_idname      = "VIEW3D_PT_car_editor_edit"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY

    def draw(self, context):
        layout  = self.layout
        scene   = context.scene
        obj     = context.active_object
        has_car = bool(get_car_objects())
        is_car  = is_car_obj(obj)
        in_edit = is_car and obj.mode == "EDIT"

        # ── Damage / Symmetry (available any time a car is loaded) ────────────
        row = layout.row(align=True)
        row.enabled = has_car
        row.operator(
            "car.toggle_damage",
            text="Damage ON" if scene.ce_show_damage else "Damage OFF",
            icon="FREEZE" if scene.ce_show_damage else "OUTLINER_OB_ARMATURE",
            depress=scene.ce_show_damage,
        )
        row.operator(
            "car.toggle_symmetry",
            text="Symmetry ON" if scene.ce_mirror_x else "Symmetry OFF",
            icon="MOD_MIRROR" if scene.ce_mirror_x else "ARROW_LEFTRIGHT",
            depress=scene.ce_mirror_x,
        )

        layout.separator(factor=0.6)

        if not is_car:
            layout.label(text="Select a car part to edit faces.", icon="INFO")
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

        # ── UV / Tiling ───────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="UV / Tiling:", icon="UV")
        row = col.row(align=True)
        row.prop(scene, "ce_face_tile_x", text="X")
        row.prop(scene, "ce_face_tile_y", text="Y")
        col.prop(scene, "ce_face_rotation", text="Rotation")

        layout.separator(factor=0.6)

        # ── Add Face ──────────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Face at Cursor:", icon="MESH_PLANE")
        row = col.row(align=True)
        row.prop(scene, "ce_add_shape", expand=True)
        col.prop(scene, "ce_add_size",    text="Size")
        col.prop(scene, "ce_assign_slot", text="Texture Slot")
        col.operator("car.add_face", text="Add Face", icon="ADD")

        layout.separator(factor=0.4)

        # ── Texture Slots ─────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Texture Slot:", icon="TEXTURE")
        col.prop(scene, "ce_new_tex_name", text="")
        col.operator("car.add_texture_slot", text="Add Slot", icon="ADD")


# ── Panel 3: Wheels ───────────────────────────────────────────────────────────

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

        wheels = sorted(
            [o for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_")],
            key=lambda o: int(o.get(_CAR_TAG, "wheel_0").split("_")[1])
        )
        active_obj = context.active_object
        active_tag = active_obj.get(_CAR_TAG, "") if active_obj else ""
        is_wheel   = active_tag.startswith("wheel_")

        # ── Per-wheel list + texture dropdown ─────────────────────────────────
        col = layout.column(align=True)
        col.label(text=f"Wheels: {len(wheels)}", icon="MESH_CIRCLE")
        for whl in wheels:
            tag       = whl.get(_CAR_TAG, "")
            idx       = tag.split("_")[1] if "_" in tag else "?"
            is_active = (whl == active_obj)
            row = col.row(align=True)
            op  = row.operator("car.select_part", text=f"WHL{idx}",
                               icon="MESH_CIRCLE", depress=is_active)
            op.part_tag = tag
            try:
                row.prop(scene, f"ce_wheel_texture_{int(idx)}", text="")
            except (ValueError, TypeError):
                pass

        # ── Trailer wheels (if a trailer is loaded) ───────────────────────────
        trailer_wheels = sorted(
            [o for o in car_objs if o.get(_CAR_TAG, "").startswith("trailer_wheel_")],
            key=lambda o: int(o.get(_CAR_TAG, "trailer_wheel_0").split("_")[-1])
        )
        if trailer_wheels:
            layout.separator(factor=0.6)
            tcol = layout.column(align=True)
            tcol.label(text=f"Trailer Wheels: {len(trailer_wheels)}", icon="AUTO")
            for twhl in trailer_wheels:
                ttag = twhl.get(_CAR_TAG, "")
                tidx = ttag.split("_")[-1]
                trow = tcol.row(align=True)
                op   = trow.operator("car.select_part", text=f"TWHL{tidx}",
                                     icon="AUTO", depress=(twhl == active_obj))
                op.part_tag = ttag
                try:
                    trow.prop(scene, f"ce_trailer_wheel_texture_{int(tidx)}", text="")
                except (ValueError, TypeError):
                    pass

        layout.separator(factor=0.6)

        # ── All-wheels texture ────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="All Wheels:", icon="TEXTURE")
        row = col.row(align=True)
        row.prop(scene, "ce_wheel_texture", text="")
        row.operator("car.apply_wheel_texture", text="", icon="CHECKMARK")

        layout.separator(factor=0.6)

        # ── Spawn wheels ──────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Wheels:", icon="ADD")
        row = col.row(align=True)
        row.prop(scene, "ce_import_wheel_count", text="Count")
        col.operator(
            "car.spawn_wheels_auto", text="Spawn at Corners", icon="PIVOT_BOUNDBOX",
        ).wheel_count = scene.ce_import_wheel_count
        col.operator("car.spawn_wheel_from_template", text="Spawn One at Cursor", icon="CURSOR")

        layout.separator(factor=0.6)

        # ── Mirror ────────────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Mirror Across X:", icon="MOD_MIRROR")
        row = col.row(align=True)
        row.enabled = is_wheel
        row.operator("car.mirror_wheel",      text="Mirror Selected",  icon="ARROW_LEFTRIGHT")
        col.operator("car.mirror_all_wheels", text="Mirror All Wheels", icon="MOD_MIRROR")

        layout.separator(factor=0.6)

        # ── Remove / Renumber ─────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Remove / Fix:", icon="TRASH")
        row = col.row(align=True)
        row.enabled = is_wheel
        row.operator("car.remove_wheel",    text="Remove Selected",    icon="TRASH")
        col.operator("car.renumber_wheels", text="Renumber (fill gaps)", icon="SORTALPHA")


# ── Panel 4: Create ───────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorCreate(bpy.types.Panel):
    bl_label       = "Create"
    bl_idname      = "VIEW3D_PT_car_editor_create"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        from src.integrations.blender.modeling.car_templates import TEMPLATES

        layout   = self.layout
        scene    = context.scene
        obj      = context.active_object
        has_sel  = obj is not None and obj.type == "MESH"
        has_name = bool(scene.ce_car_display_name.strip())
        has_body = get_car_body() is not None

        # ── Menu Name (shared between both creation paths) ────────────────────
        col = layout.column(align=True)
        col.label(text="Menu Name:", icon="TEXT")
        col.prop(scene, "ce_car_display_name", text="")
        display = scene.ce_car_display_name.strip()
        derived = ("VP" + display.upper().replace(" ", "")) if display else "VP???"
        sub = col.row()
        sub.enabled = False
        sub.label(text=f"Filename: {derived}", icon="OUTLINER_OB_FONT")

        layout.separator(factor=0.8)

        # ── From Template ─────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="From Template", icon="MESH_CUBE")

        col = box.column(align=True)
        col.prop(scene, "ce_template", text="")
        spec = TEMPLATES.get(scene.ce_template)
        if spec:
            w, h, l, _, _, _ = spec["body"]
            sub = col.column(align=True)
            sub.enabled = False
            sub.label(text=f"Body  W×H×L  ({w:.2f} × {h:.2f} × {l:.2f})", icon="MESH_CUBE")
            n_w = len(spec["custom_wheels"]) if "custom_wheels" in spec else 4
            sub.label(text=f"Wheels: {n_w}  ·  radius {spec['wheel_radius']:.2f}", icon="MESH_CIRCLE")

        box.separator(factor=0.4)
        col_tmpl = box.column(align=True)
        r = col_tmpl.row()
        r.enabled = has_name
        r.operator("car.new_from_template", text="Create Car in Blender", icon="ADD")
        r2 = col_tmpl.row()
        r2.enabled = has_name
        r2.operator("car.init_new_car", text="Init Support Files", icon="IMPORT")

        layout.separator(factor=0.6)

        # ── Import External ───────────────────────────────────────────────────
        box2 = layout.box()
        box2.label(text="Import External  (.dae / .fbx / …)", icon="IMPORT")
        box2.label(text="Select your meshes in the scene first.", icon="INFO")

        col = box2.column(align=True)
        r = col.row()
        r.enabled = has_name and has_sel
        r.scale_y = 1.3
        r.operator("car.import_prepare", text="Prepare Imported Model", icon="SHADERFX")

        box2.separator(factor=0.4)

        col2 = box2.column(align=True)
        col2.label(text="Add Wheels:", icon="MESH_CIRCLE")
        row = col2.row(align=True)
        row.prop(scene, "ce_import_wheel_count", text="Count")
        r2 = col2.row()
        r2.enabled = has_body
        r2.operator(
            "car.spawn_wheels_auto", text="Spawn at Corners", icon="PIVOT_BOUNDBOX",
        ).wheel_count = scene.ce_import_wheel_count

        layout.separator(factor=0.6)

        # ── Advanced ──────────────────────────────────────────────────────────
        box3 = layout.box()
        box3.label(text="Advanced", icon="TOOL_SETTINGS")

        col = box3.column(align=True)
        col.label(text="Manual Tag:", icon="BOOKMARKS")
        r = col.row(align=True)
        r.enabled = has_sel and has_name
        r.operator("car.import_tag_body",  text="Tag Body",  icon="OUTLINER_OB_MESH")
        r.operator("car.import_tag_wheel", text="Tag Wheel", icon="MESH_CIRCLE")
        r2 = col.row()
        r2.enabled = has_name
        r2.operator("car.import_auto_tag", text="Auto-Tag Scene", icon="SHADERFX")

        box3.separator(factor=0.4)

        col = box3.column(align=True)
        col.label(text="Mesh Prep:", icon="MOD_DECIM")
        col.prop(scene, "ce_import_decimate_ratio", text="Decimate Ratio")
        r = col.row()
        r.enabled = has_sel
        r.operator("car.import_decimate",           text="Decimate Active",       icon="MOD_DECIM")
        r2 = col.row()
        r2.enabled = has_sel
        r2.operator("car.import_clean_materials",   text="Clean Material Names",  icon="MATERIAL")
        box3.operator("car.import_flatten_materials", text="Flatten All → CARBOTTOM", icon="BRUSH_DATA")
        r3 = col.row()
        r3.enabled = has_sel
        r3.operator("car.import_apply_transforms",  text="Apply Scale & Rotation", icon="ORIENTATION_GLOBAL")


# ── Registration list ─────────────────────────────────────────────────────────

CAR_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_CarEditorCar,
    VIEW3D_PT_CarEditorEdit,
    VIEW3D_PT_CarEditorWheels,
    VIEW3D_PT_CarEditorCreate,
]

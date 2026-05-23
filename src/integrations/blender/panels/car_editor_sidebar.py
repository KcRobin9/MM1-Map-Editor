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
    _CAR_LIGHT_DEFS, _CAR_LIGHT_TAGS,
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
        trow.operator("car.load_siren_lights", text="Load Siren Lights", icon="LIGHT")

        if has_car:
            layout.separator(factor=0.5)

            # ── Car name + parts list ─────────────────────────────────────────
            car_name = body_obj["mm_car_name"] if body_obj else "Unknown"
            n_wheels = sum(1 for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_"))

            # Collapsible parts list — the car-name header toggles it.
            hdr = layout.row(align=True)
            hdr.prop(scene, "ce_show_parts", text=car_name, emboss=False,
                     icon="TRIA_DOWN" if scene.ce_show_parts else "TRIA_RIGHT")
            hdr.label(text=f"{len(car_objs)} parts · {n_wheels} wheels")

            if scene.ce_show_parts:
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
        col.prop(scene, "ce_load_lights",  text="Load Lights")
        col.prop(scene, "ce_add_trailer",  text="Add Trailer  (stock semi trailer)")
        col.prop(scene, "ce_add_siren",    text="Police Lights / Siren")
        col.prop(scene, "ce_export_paint_variants", text="Paint Variants  (in-game colour menu)")

        # ── Car Info (.INFO menu stats + engine sound — applied on AR + Launch) ─
        if has_car:
            box = layout.box()
            box.label(text="Car Info  (menu stats)", icon="INFO")
            col = box.column(align=True)
            col.prop(scene, "ce_info_description", text="Name")
            col.prop(scene, "ce_info_colors",      text="Colors")
            row = col.row(align=True)
            row.prop(scene, "ce_info_horsepower", text="HP")
            row.prop(scene, "ce_info_topspeed",   text="Top")
            row = col.row(align=True)
            row.prop(scene, "ce_info_mass",       text="Mass")
            row.prop(scene, "ce_info_durability", text="Durab.")

            box.separator(factor=0.4)
            box.prop(scene, "ce_audio_profile", text="Engine Sound")
            box.separator(factor=0.4)
            box.operator("car.generate_showcase", text="Generate Showcase Image", icon="RENDER_STILL")

        layout.separator(factor=0.6)

        # ── Export ────────────────────────────────────────────────────────────
        has_last_exp = bool(scene.ce_last_export_dir.strip())

        col = layout.column(align=True)
        # Row 1 — export / launch
        r1 = col.row(align=True)
        r1.enabled = has_car
        r1.operator("car.export_car",          text="Export BMS",  icon="FILE_TICK")
        r1.operator("car.pack_and_start_game", text="AR + Launch", icon="PLAY")
        # Row 2 — reload / validate (independent enable states)
        r2 = col.row(align=True)
        c = r2.row(align=True); c.enabled = has_last_exp
        c.operator("car.reload_car", text="Reload", icon="FILE_REFRESH")
        c = r2.row(align=True); c.enabled = has_car
        c.operator("car.validate", text="Validate", icon="CHECKMARK")
        # Row 3 — maintenance (Clear Shop / Clean AR always available; Debug needs a car)
        r3 = col.row(align=True)
        r3.operator("car.clear_shop", text="Clear Shop", icon="TRASH")
        r3.operator("car.clean_ar",   text="Clean AR",   icon="TRASH")
        c = r3.row(align=True); c.enabled = has_car
        c.operator("car.debug_bms",  text="Debug BMS",  icon="INFO")

        if has_last_exp:
            col.operator("car.open_export_folder",
                         text=Path(scene.ce_last_export_dir).name, icon="FILE_FOLDER")


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

        # ── Per-wheel list + texture dropdown + radius ────────────────────────
        col = layout.column(align=True)
        col.label(text=f"Wheels: {len(wheels)}   (texture · radius)", icon="MESH_CIRCLE")
        for whl in wheels:
            tag       = whl.get(_CAR_TAG, "")
            idx       = tag.split("_")[1] if "_" in tag else "?"
            is_active = (whl == active_obj)
            row = col.row(align=True)
            op  = row.operator("car.select_part", text=f"WHL{idx}",
                               icon="NONE", depress=is_active)
            op.part_tag = tag
            try:
                row.prop(scene, f"ce_wheel_texture_{int(idx)}", text="")
                row.prop(scene, f"ce_wheel_radius_{int(idx)}", text="")
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
                                     icon="NONE", depress=(twhl == active_obj))
                op.part_tag = ttag
                try:
                    trow.prop(scene, f"ce_trailer_wheel_texture_{int(tidx)}", text="")
                except (ValueError, TypeError):
                    pass

        layout.separator(factor=0.6)

        # ── All-wheels texture + radius (apply to every wheel at once) ────────
        col = layout.column(align=True)
        col.label(text="All Wheels:", icon="TEXTURE")
        row = col.row(align=True)
        row.prop(scene, "ce_wheel_texture", text="")
        row.operator("car.apply_wheel_texture", text="", icon="CHECKMARK")
        col.prop(scene, "ce_all_wheel_radius", text="Radius")

        layout.separator(factor=0.6)

        # ── Spawn wheels ──────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.label(text="Add Wheels:", icon="ADD")
        col.prop(scene, "ce_wheel_style", text="Style")
        row = col.row(align=True)
        row.prop(scene, "ce_import_wheel_count", text="Count")
        row.prop(scene, "ce_wheel_size", text="Radius")
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


# ── Panel: Lights ─────────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorLights(bpy.types.Panel):
    bl_label       = "Lights"
    bl_idname      = "VIEW3D_PT_car_editor_lights"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout   = self.layout
        scene    = context.scene
        car_objs = get_car_objects()
        has_car  = bool(car_objs)

        # Load button (loads this car's glow meshes, or VPMUSTANG99 as fallback)
        row = layout.row(align=True)
        row.enabled = has_car
        row.operator("car.load_car_lights", text="Load Lights", icon="LIGHT")

        if not has_car:
            layout.label(text="Load a car first", icon="INFO")
            return

        loaded = {o.get(_CAR_TAG, ""): o for o in car_objs}
        active = context.active_object
        light_label = {tag: lbl for tag, _f, _t, lbl in _CAR_LIGHT_DEFS}

        present = [t for t in _CAR_LIGHT_TAGS if t in loaded]
        has_siren = ("light_red" in loaded) or ("light_blue" in loaded)
        if not present and not has_siren:
            layout.separator(factor=0.5)
            info = layout.column(align=True)
            info.enabled = False
            info.label(text="No lights loaded yet.", icon="INFO")
            return

        layout.separator(factor=0.5)

        # ── Per-light: select + glow colour ───────────────────────────────────
        if present:
            col = layout.column(align=True)
            col.label(text="Lights  (select · colour)", icon="LIGHT")
            for i, tag in enumerate(_CAR_LIGHT_TAGS):
                obj = loaded.get(tag)
                if obj is None:
                    continue
                row = col.row(align=True)
                op  = row.operator("car.select_part", text=light_label.get(tag, tag),
                                   icon="NONE", depress=(obj == active))
                op.part_tag = tag
                row.prop(scene, f"ce_light_color_{i}", text="")

        # ── Headlight beam length ─────────────────────────────────────────────
        if "light_head" in loaded:
            layout.separator(factor=0.5)
            bcol = layout.column(align=True)
            bcol.label(text="Headlight Beam:", icon="LIGHT_SPOT")
            bcol.prop(scene, "ce_light_beam", text="Length")

        # ── Siren lenses (if a siren bar is loaded) ───────────────────────────
        siren_red  = loaded.get("light_red")
        siren_blue = loaded.get("light_blue")
        if siren_red or siren_blue:
            layout.separator(factor=0.5)
            scol = layout.column(align=True)
            scol.label(text="Siren  (select · colour)", icon="LIGHT_SUN")
            if siren_red:
                row = scol.row(align=True)
                op  = row.operator("car.select_part", text="Siren Light 1",
                                   icon="NONE", depress=(siren_red == active))
                op.part_tag = "light_red"
                row.prop(scene, "ce_siren_color_red", text="")
            if siren_blue:
                row = scol.row(align=True)
                op  = row.operator("car.select_part", text="Siren Light 2",
                                   icon="NONE", depress=(siren_blue == active))
                op.part_tag = "light_blue"
                row.prop(scene, "ce_siren_color_blue", text="")
        else:
            layout.separator(factor=0.3)
            srow = layout.row(align=True)
            srow.operator("car.load_siren_lights", text="Load Siren Lights", icon="LIGHT_SUN")

        # ── Viewport visibility ───────────────────────────────────────────────
        layout.separator(factor=0.5)
        layout.prop(scene, "ce_hide_light_glows", text="Hide Glows in Viewport",
                    icon="HIDE_ON" if scene.ce_hide_light_glows else "HIDE_OFF")


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

        # ── Car / Menu Name (shared between both creation paths) ──────────────
        display = scene.ce_car_display_name.strip()
        derived = ("VP" + display.upper().replace(" ", "")) if display else ""
        col = layout.column(align=True)
        hdr = col.row(align=True)
        hdr.label(text="Car/Menu Name", icon="TEXT")
        if derived:
            sub = hdr.row()
            sub.enabled = False
            sub.label(text=f"({derived})")
        col.prop(scene, "ce_car_display_name", text="")

        layout.separator(factor=0.5)

        # ── Copy a loaded car into an editable custom car ─────────────────────
        box0 = layout.box()
        box0.label(text="Copy Loaded Car → Custom", icon="DUPLICATE")
        r0 = box0.row()
        r0.enabled = has_body and has_name
        r0.operator("car.make_custom_copy", text="Save Loaded Car as Custom", icon="FILE_TICK")

        layout.separator(factor=0.8)

        # ── From Template ─────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="From Template", icon="MESH_CUBE")

        col = box.column(align=True)
        col.prop(scene, "ce_template", text="")
        col.prop(scene, "ce_wheel_style", text="Wheels")
        col.prop(scene, "ce_template_wheel_count", text="Wheel Count  (0 = template default)")
        r = col.row()
        r.enabled = has_name
        r.operator("car.new_from_template", text="Create Car in Blender", icon="ADD")

        layout.separator(factor=0.6)

        # ── Import External ───────────────────────────────────────────────────
        box2 = layout.box()
        box2.label(text="Import External  (.dae / .fbx / …)", icon="IMPORT")

        col = box2.column(align=True)
        r = col.row()
        r.enabled = has_name and has_sel
        r.scale_y = 1.3
        r.operator("car.import_prepare", text="Prepare Imported Model", icon="SHADERFX")

        box2.separator(factor=0.4)
        hint = box2.row()
        hint.enabled = False
        hint.label(text="Add wheels in the Wheels panel below.", icon="MESH_CIRCLE")

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


# ── Panel 5: Physics ──────────────────────────────────────────────────────────

class VIEW3D_PT_CarEditorPhysics(bpy.types.Panel):
    bl_label       = "Physics"
    bl_idname      = "VIEW3D_PT_car_editor_physics"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout  = self.layout
        scene   = context.scene
        has_car = bool(get_car_objects())

        layout.prop(scene, "ce_phys_override", text="Override Physics")

        col = layout.column(align=True)
        col.enabled = scene.ce_phys_override
        col.label(text="Handling (MMCARSIM)", icon="AUTO")
        col.prop(scene, "ce_phys_mass")
        col.prop(scene, "ce_phys_horsepower")
        col.prop(scene, "ce_phys_drag")
        col.prop(scene, "ce_phys_downforce")
        col.prop(scene, "ce_phys_grip")
        col.prop(scene, "ce_phys_drift")
        col.prop(scene, "ce_phys_suspension")

        cg = layout.column(align=True)
        cg.enabled = scene.ce_phys_override
        cg.label(text="Centre of Gravity (BodyCG)", icon="ORIENTATION_LOCAL")
        cg.prop(scene, "ce_phys_cg_x")
        cg.prop(scene, "ce_phys_cg_height")
        cg.prop(scene, "ce_phys_cg_z")

        sub = layout.column(align=True)
        sub.enabled = scene.ce_phys_override
        sub.operator("car.reset_physics", text="Reset to VPMUSTANG99", icon="LOOP_BACK")

        info = layout.column(align=True)
        info.enabled = False
        if scene.ce_phys_override:
            info.label(text="Applied on AR + Launch", icon="INFO")
        else:
            info.label(text="Off — keeps stock handling", icon="INFO")


# ── Registration list ─────────────────────────────────────────────────────────

CAR_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_CarEditorCar,
    VIEW3D_PT_CarEditorEdit,
    VIEW3D_PT_CarEditorWheels,
    VIEW3D_PT_CarEditorLights,
    VIEW3D_PT_CarEditorCreate,
    VIEW3D_PT_CarEditorPhysics,
]

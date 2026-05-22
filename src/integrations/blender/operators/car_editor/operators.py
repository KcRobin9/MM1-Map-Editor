"""Car Editor — operators module (split from the former car_editor.py monolith)."""
import bpy
import math
import bmesh
import shutil
import mathutils
import subprocess
from pathlib import Path

from src.constants.folder import Folder
from src.constants.misc import Executable
from src.integrations.blender.modeling.meshes import (
    _apply_materials_to_mesh, _build_material, build_blender_mesh, read_bms,
)
from src.constants.constants import CURRENT_TIME_FORMATTED
from src.integrations.blender.modeling import car_templates
from src.integrations.blender.modeling.bms_writer import mesh_to_bms_data, write_bms

from src.integrations.blender.operators.car_editor.paint import (
    _apply_paint_variant, _detect_paint_prefix, _paint_variant_cache,
)
from src.integrations.blender.operators.car_editor.common import (
    _add_child_obj, _base_car_name, _bms_extract_faces_by_texture, _bms_merge_part_into_body,
    _bms_to_bl_offset, _build_damage_remap, _clear_car_objects, _clear_trailer_objects,
    _get_or_create_collection, _has_custom_trailer, _is_original_car,
    _is_trailer_part, _load_bms, _read_back_face_uv, _tex_folder, get_car_body, get_car_objects,
    is_car_obj,
)
from src.integrations.blender.operators.car_editor.lights import (
    _body_roof_anchor, _colored_tex, _ensure_custom_glow_in_shop, _ensure_glow_texture,
    _ensure_siren_lights_in_shop, _ensure_siren_textures_in_shop,
    _export_car_lights, _export_placed_siren_lights, _get_car_light_objs, _get_siren_housing_objs,
    _get_siren_light_objs, _is_car_light, _is_siren_part, _load_car_lights, _sync_light_props,
)
from src.integrations.blender.operators.car_editor.wheels import (
    _apply_wheel_tex, _body_wheel_positions, _detect_wheel_texture, _load_styled_wheel,
    _mirror_wheel_mesh, _scale_wheel_to_radius, _sync_wheel_radius_props, _wheel_current_radius,
)
from src.integrations.blender.operators.car_editor.packing import (
    _build_car_tsh, _ensure_dash_in_shop, _ensure_lights_in_shop, _ensure_trailer_in_shop,
    _ensure_wheels_in_shop, _generate_car_bnd_in_shop, _generate_car_dlp_in_shop,
    _generate_trailer_bnd_in_shop, _generate_trailer_dlp_in_shop, _init_new_car_files,
    _pack_car_ar, _set_info_colors, _set_info_flags, _apply_info_stats, _sync_info_props_from_car,
    _ensure_car_audio_in_shop, _generate_shadow_in_shop,
)
from src.integrations.blender.operators.car_editor.physics import (
    _apply_physics_in_shop, _base_carsim_path, _sync_physics_props_from_car,
)
from src.integrations.blender.operators.car_editor.trailer import (
    _export_custom_trailer, _sync_trailer_wheel_texture_props,
)
from src.integrations.blender.operators.car_editor.constants import (
    _CAR_COLLECTION, _CAR_TAG, _SIREN_HOUSING_TAG, _SIREN_LIGHT_TAGS,
)
from src.integrations.blender.operators.car_editor.import_helpers import (
    _clean_mat_name, _derive_car_name, _tag_as_body, _tag_as_wheel,
)
from src.integrations.blender.operators.car_editor.validate import _validate_car


class CAR_OT_InitNewCar(bpy.types.Operator):
    bl_idname  = "car.init_new_car"
    bl_label   = "Init Support Files"
    bl_description = (
        "Write TUNE, MTL, BND and BMS support files for a new car name into "
        "the standard SHOP/ subdirs, sourced from VPMUSTANG99 in core/. "
        "Run once per new car name before exporting BMS."
    )

    def execute(self, context):
        display_name = context.scene.ce_car_display_name.strip()
        car_name     = ("VP" + display_name.upper().replace(" ", "")) if display_name else ""
        if not car_name:
            self.report({"ERROR"}, "Menu Name is empty.")
            return {"CANCELLED"}

        msgs = _init_new_car_files(car_name, display_name)
        _sync_info_props_from_car(context.scene, car_name)
        errors = [m for m in msgs if m.startswith("ERROR")]
        for m in msgs:
            print(f"[Car Init] {m}")
        if errors:
            self.report({"ERROR"}, errors[0])
        else:
            self.report({"INFO"}, f"Initialised {car_name} — {len(msgs)} files written to SHOP/.")

        return {"FINISHED"}


class CAR_OT_ValidateCar(bpy.types.Operator):
    bl_idname      = "car.validate"
    bl_label       = "Validate Car"
    bl_description = (
        "Pre-flight check (body, wheels, textures, material slots, .INFO) so you "
        "catch problems here instead of via an in-game crash."
    )

    def execute(self, context):
        errors, warnings = _validate_car(context)
        for e in errors:
            print(f"[Validate] ERROR: {e}")
        for w in warnings:
            print(f"[Validate] WARN:  {w}")

        def _draw(menu, _ctx):
            lay = menu.layout
            if not errors and not warnings:
                lay.label(text="All checks passed — ready to pack.", icon="CHECKMARK")
                return
            for e in errors:
                lay.label(text=e, icon="ERROR")
            for w in warnings:
                lay.label(text=w, icon="DOT")

        title = ("Validation: all good"
                 if not errors and not warnings
                 else f"Validation: {len(errors)} error(s), {len(warnings)} warning(s)")
        context.window_manager.popup_menu(_draw, title=title, icon="INFO")
        return {"FINISHED"}


class CAR_OT_PackAndStartGame(bpy.types.Operator):
    bl_idname  = "car.pack_and_start_game"
    bl_label   = "Create AR + Start Game"
    bl_description = (
        "Export current car BMS to SHOP, pack !!!!!{car_name}.ar, then launch the game. "
        "Always launches — no running-check. One-click full workflow."
    )

    def execute(self, context):

        car_objects = get_car_objects()
        body_obj    = get_car_body()
        if not car_objects or body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        # Pre-flight validation: block on errors, log warnings.
        v_errors, v_warnings = _validate_car(context)
        for w in v_warnings:
            print(f"[Validate] WARN:  {w}")
        if v_errors:
            for e in v_errors:
                print(f"[Validate] ERROR: {e}")
            self.report({"ERROR"}, f"Can't pack: {v_errors[0]} (run Validate for the full list).")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj["mm_car_name"])
        minimal  = _is_original_car(car_name)

        # Commit any pending Edit Mode changes
        active_obj = context.view_layer.objects.active
        was_edit   = active_obj is not None and active_obj.mode == "EDIT"
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")


        # Export car parts to SHOP/BMS/{NAME}/ so the packer finds them.
        city_dir = Folder.Shop.Meshes / car_name

        # Minimal override (existing game car): wipe the SHOP BMS folder so stale
        # parts from earlier full exports don't leak into the AR, and skip wheels
        # — re-exporting them through the bake path can corrupt geometry, and the
        # original wheels already work in-game.
        if minimal and city_dir.exists():
            shutil.rmtree(city_dir)
        city_dir.mkdir(parents=True, exist_ok=True)

        errors = []
        housing_objs = _get_siren_housing_objs()
        for obj in car_objects:
            part_tag = obj.get(_CAR_TAG, "unknown")
            if _is_trailer_part(part_tag):
                continue  # trailer parts are exported separately to {NAME}_TRAILER
            if _is_siren_part(part_tag):
                continue  # lenses exported separately; housing merged into body below
            if _is_car_light(part_tag):
                continue  # head/tail/brake/etc exported separately (absolute verts)
            if minimal and part_tag.startswith("wheel_"):
                # Existing game cars keep their original wheels (from the base AR);
                # the original DLP there already provides correct spin pivots.
                continue
            src_file = obj.data.get("bms_source_file", "")
            if src_file:
                out_name = Path(src_file).name
            elif part_tag == "body":
                out_name = "BODY_H.BMS"
            elif part_tag.startswith("wheel_"):
                idx = part_tag.split("_")[1]
                out_name = f"WHL{idx}_H.BMS"
            elif part_tag.startswith("fender_"):
                out_name = f"FNDR{part_tag.split('_')[1]}_H.BMS"
            else:
                out_name = f"{part_tag.upper()}.BMS"
            try:
                is_wheel = part_tag.startswith("wheel_")
                bms_data = mesh_to_bms_data(obj, bake_location=is_wheel)
                # The always-visible siren-bar housing is merged into the body mesh
                # (MM1 has no spare always-on mesh slot, so VPCOP bakes it into its
                # body too). Lenses (REDLIGHT/BLUELIGHT) flash on top separately.
                if part_tag == "body" and housing_objs:
                    for h in housing_objs:
                        bms_data = _bms_merge_part_into_body(
                            bms_data, mesh_to_bms_data(h, bake_location=True))
                write_bms(bms_data, city_dir / out_name)
            except Exception as exc:
                errors.append(out_name)
                print(f"[Car Editor] Export failed for {out_name}: {exc}")

        if errors:
            self.report({"WARNING"}, f"BMS export errors ({len(errors)}): {errors[0]} — AR may be incomplete.")

        # The engine requires two additional body copies regardless of LOD policy:
        #   BODY_M.BMS — mmDamage::InitDamage reads Meshes[2] (medium slot);
        #                NULL there causes an unconditional Abortf (damage.c:14).
        #   H.BMS      — car selection menu renders this mesh; without it the
        #                car is invisible or absent in the vehicle picker.
        # Both are identical to the high-detail export — quality doesn't matter.
        body_h = city_dir / "BODY_H.BMS"
        if body_h.exists():
            for suffix in ("BODY_M.BMS", "BODY_L.BMS", "BODY_VL.BMS", "H.BMS"):
                shutil.copy2(body_h, city_dir / suffix)

        # Lights (head/tail/brake/reverse/signals): for a new car, restore the
        # stock light meshes from VPMUSTANG99 so the slots are always present and
        # correct. Only when the user has explicitly loaded lights in the scene do
        # we overlay their edited/recoloured versions on top (opt-in).
        car_light_objs = _get_car_light_objs()
        if not minimal:
            _ensure_lights_in_shop(car_name)
        if car_light_objs:
            _export_car_lights(car_name, car_light_objs, minimal=minimal)
        if not minimal:
            # Custom colours (blue/green/coloured cone) aren't in GLOBAL.TSH; bundle
            # their generated DDS — for car lights AND recoloured siren lenses — so
            # the TSH 'tg' flag can resolve them in-game.
            staged = _ensure_custom_glow_in_shop(car_light_objs + _get_siren_light_objs())
            if staged:
                print(f"[Car Editor] Staged {staged} custom glow texture(s) → TEX16A")

        if not minimal:
            # New car: build a self-contained AR — wheels were just exported
            # CENTERED (verts at origin + hub mesh_offset + OFFSET flag), so the
            # mesh draws correctly at the pivot. The pivot itself (mmWheel::Center)
            # is read from the car DLP's WHLn_H centroid, which we GENERATE from
            # the exported wheel hubs (Stage 2) so wheels may sit anywhere — not
            # just VPMUSTANG99 positions. Also: dashboard, wheel LODs, and a TSH
            # declaring every texture (the engine fatal-errors on undeclared ones).
            _ensure_wheels_in_shop(car_name)   # fallback for body-only imports
            _ensure_dash_in_shop(car_name)

            # Trailer: an edited (custom) trailer in the scene takes precedence;
            # otherwise the "Add Trailer" toggle attaches the stock semi trailer.
            # Either way stage the stock base (shadow/tail-light/collision), then
            # overwrite body+wheels with the edits and regenerate the trailer DLP.
            custom_trailer = _has_custom_trailer()
            add_trailer    = custom_trailer or bool(getattr(context.scene, "ce_add_trailer", False))
            if add_trailer:
                _ensure_trailer_in_shop(car_name)
            if custom_trailer:
                _export_custom_trailer(car_name)
                _generate_trailer_dlp_in_shop(car_name)
                _generate_trailer_bnd_in_shop(car_name)

            for i in range(10):
                whl_h = city_dir / f"WHL{i}_H.BMS"
                if not whl_h.exists():
                    break
                for suffix in (f"WHL{i}_M.BMS", f"WHL{i}_L.BMS", f"WHL{i}_VL.BMS"):
                    shutil.copy2(whl_h, city_dir / suffix)

            # Police lights must be staged before the TSH so their textures
            # (VPCOP_TOPLIGHT / FXLTGLOWRED) get declared by _build_car_tsh.
            # Editable lights placed via "Load Siren Lights" take precedence; else
            # the toggle auto-places stock lights on the roof.
            light_objs = _get_siren_light_objs()
            add_siren  = (bool(getattr(context.scene, "ce_add_siren", False))
                         or bool(light_objs) or bool(housing_objs))
            if add_siren:
                if light_objs:
                    _export_placed_siren_lights(car_name, light_objs)
                else:
                    _ensure_siren_lights_in_shop(car_name)
                _ensure_siren_textures_in_shop()       # VPCOP_TOPLIGHT + VPCOPLIGHTS

            # Engine + horn sounds: copy the chosen source car's audio profile (and
            # enable the siren flag when a siren is present, else StartSiren crashes).
            _ensure_car_audio_in_shop(car_name, context.scene.ce_audio_profile, siren=add_siren)

            paint_on = bool(getattr(context.scene, "ce_export_paint_variants", True))
            colors = _build_car_tsh(car_name, car_objects, paint_variants=paint_on)
            _apply_info_stats(car_name, context.scene)
            _set_info_flags(car_name,
                            six_wheel=(city_dir / "WHL4_H.BMS").exists(),
                            has_trailer=add_trailer,
                            has_siren=add_siren)
            _set_info_colors(car_name, colors)
            _generate_car_dlp_in_shop(car_name)
            _generate_car_bnd_in_shop(car_name)
            _generate_shadow_in_shop(car_name)   # ground shadow fitted to the body

        # Physics override applies in both modes (new cars and existing-car edits).
        if bool(getattr(context.scene, "ce_phys_override", False)):
            _apply_physics_in_shop(car_name, context.scene)
        elif minimal:
            # Clear any override staged by an earlier pack so a geometry-only edit
            # falls back to the base AR's stock handling.
            stale = Folder.Shop.Tune / f"{car_name}.MMCARSIM"
            if stale.exists():
                stale.unlink()

        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")

        if not _pack_car_ar(car_name, minimal=minimal):
            self.report({"ERROR"}, "AR packing failed — check the system console.")
            return {"CANCELLED"}

        exe = Folder.MidtownMadness.Root / Executable.MIDTOWN_MADNESS
        if not exe.exists():
            self.report({"ERROR"}, f"Executable not found: {exe}")
            return {"CANCELLED"}

        n_ok = len(car_objects) - len(errors)
        print(f"[Car Editor] Launching {exe} …")
        subprocess.Popen([str(exe)], cwd=str(Folder.MidtownMadness.Root))
        mode_msg = "minimal override" if minimal else "full"
        self.report({"INFO"}, f"Packed {car_name}.ar ({mode_msg}) — game launching.")
        return {"FINISHED"}


# ── Operator: Load Car ────────────────────────────────────────────────────────

class CAR_OT_LoadCar(bpy.types.Operator):
    bl_idname   = "car.load_car"
    bl_label    = "Load Car"
    bl_description = (
        "Load a car from a BMS folder (body + wheels + fenders + lights). "
        "Clears any previously loaded car editor objects first."
    )

    # File browser writes the chosen directory here.
    directory: bpy.props.StringProperty(subtype="DIR_PATH", default="")

    def invoke(self, context, event):
        # Open MESHES/CARS so the user picks a car subfolder directly.
        meshes_cars = Folder.Resources.Editor.Meshes / "CARS"
        self.directory = str(meshes_cars) + "/"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        car_folder = Path(self.directory.rstrip("/\\"))
        if not car_folder.is_dir():
            self.report({"ERROR"}, f"Folder not found: {car_folder}")
            return {"CANCELLED"}

        # Texture folder is always the editor TEXTURES folder
        tex_folder = Folder.Resources.Editor.Textures
        context.scene.ce_texture_folder = str(tex_folder)

        _clear_car_objects()
        col      = _get_or_create_collection(_CAR_COLLECTION)
        car_name = car_folder.name

        # ── Body ──────────────────────────────────────────────────────────────
        # TRAILER_H.BMS is tried last so that vehicles like VPSEMI_TRAILER
        # (which have no BODY_H.BMS) load correctly.
        body_mesh = None
        body_file = None
        for candidate in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS", "TRAILER_H.BMS"):
            f = car_folder / candidate
            if f.exists():
                body_mesh = _load_bms(f, car_name, tex_folder)
                body_file = candidate
                break

        if body_mesh is None:
            self.report({"ERROR"},
                        "No body BMS found (BODY_H.BMS / BODY_M.BMS / H.BMS / TRAILER_H.BMS)")
            return {"CANCELLED"}

        body_obj          = bpy.data.objects.new(car_name, body_mesh)
        col.objects.link(body_obj)
        body_obj.location = _bms_to_bl_offset(body_mesh)
        body_obj[_CAR_TAG]        = "body"
        body_obj["mm_car_folder"] = str(car_folder)
        body_obj["mm_car_name"]   = car_name
        body_obj["mm_body_file"]  = body_file or ""

        # ── Wheels (WHL0_H … WHL9_H) ─────────────────────────────────────────
        wheel_count = 0
        for i in range(10):
            f = car_folder / f"WHL{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms(f, f"{car_name}.WHL{i}", tex_folder)
            if mesh:
                _add_child_obj(mesh, mesh.name, f"wheel_{i}", body_obj, col)
                wheel_count += 1

        # ── Fenders (FNDR0_H … FNDR9_H) ──────────────────────────────────────
        fender_count = 0
        for i in range(10):
            f = car_folder / f"FNDR{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms(f, f"{car_name}.FNDR{i}", tex_folder)
            if mesh:
                _add_child_obj(mesh, mesh.name, f"fender_{i}", body_obj, col)
                fender_count += 1

        # ── Lights (optional, off by default) ────────────────────────────────
        # Load the standard glow meshes (head/tail/brake/reverse/signals) as
        # tagged, editable parts so the Lights panel can recolour / move them.
        light_count = 0
        if context.scene.ce_load_lights:
            light_count = _load_car_lights(car_name, car_folder, body_obj, col, tex_folder)
            if not light_count:
                print(f"[Car Editor] No light BMS files found in {car_folder} or VPMUSTANG99")

        # ── Trailer body (TRAILER_H.BMS) ──────────────────────────────────────
        # Skip if TRAILER_H.BMS was already loaded as the main body
        # (e.g. VPSEMI_TRAILER has no BODY_H.BMS — TRAILER_H.BMS IS the car).
        trailer_obj = None
        if body_file != "TRAILER_H.BMS":
            trailer_f = car_folder / "TRAILER_H.BMS"
            if trailer_f.exists():
                mesh = _load_bms(trailer_f, f"{car_name}.TRAILER", tex_folder)
                if mesh:
                    trailer_obj = _add_child_obj(mesh, mesh.name, "trailer", body_obj, col)

        # ── Trailer wheels (TWHL0_H … TWHL9_H) ───────────────────────────────
        # When TRAILER_H.BMS is the main body, TWHL wheels are its primary wheels
        # and get parented directly to body_obj (counted in wheel_count).
        trailer_wheel_parent = trailer_obj if trailer_obj else body_obj
        for i in range(10):
            f = car_folder / f"TWHL{i}_H.BMS"
            if not f.exists():
                break
            mesh = _load_bms(f, f"{car_name}.TWHL{i}", tex_folder)
            if mesh:
                if trailer_obj is None:
                    # TWHL wheels are the only wheels — count them as main wheels
                    _add_child_obj(mesh, mesh.name, f"wheel_{wheel_count}", body_obj, col)
                    wheel_count += 1
                else:
                    _add_child_obj(mesh, mesh.name, f"trailer_wheel_{i}",
                                   trailer_wheel_parent, col)

        # ── Persist folder paths in scene ─────────────────────────────────────
        context.scene.ce_car_folder = str(car_folder)

        # ── Select + frame body ───────────────────────────────────────────────
        bpy.ops.object.select_all(action="DESELECT")
        body_obj.select_set(True)
        context.view_layer.objects.active = body_obj
        try:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        except Exception:
            pass

        # Detect current paint variant and clear the variant cache for the new car
        _paint_variant_cache.clear()
        context.scene.ce_paint_variant  = _detect_paint_prefix(body_mesh)
        context.scene.ce_show_damage    = False  # reset damage toggle on load
        detected_whl_tex = _detect_wheel_texture(get_car_objects())
        if detected_whl_tex:
            context.scene.ce_wheel_texture = detected_whl_tex
            for obj in get_car_objects():
                tag = obj.get(_CAR_TAG, "")
                if tag.startswith("wheel_"):
                    obj["ce_wheel_tex"] = detected_whl_tex
                    try:
                        idx = int(tag.split("_")[1])
                        setattr(context.scene, f"ce_wheel_texture_{idx}", detected_whl_tex)
                    except (ValueError, IndexError, TypeError):
                        pass

        # Sync the Physics panel to this car's real MMCARSIM values (override off),
        # so retuning starts from the truth instead of VPMUSTANG99 defaults.
        _sync_physics_props_from_car(context.scene, _base_car_name(car_name))
        _sync_wheel_radius_props(context.scene)
        _sync_light_props(context.scene)
        _sync_info_props_from_car(context.scene, _base_car_name(car_name))

        # Some BMS files load with one face already pointing at a _DMG material slot.
        # Toggling damage on then immediately off normalises all faces to clean textures.
        bpy.ops.car.toggle_damage("EXEC_DEFAULT")
        bpy.ops.car.toggle_damage("EXEC_DEFAULT")

        parts_msg = f"body + {wheel_count} wheels"
        if fender_count:
            parts_msg += f" + {fender_count} fenders"
        if light_count:
            parts_msg += f" + {light_count} lights"
        if trailer_obj:
            parts_msg += " + trailer"
        self.report({"INFO"}, f"Loaded {car_name}: {parts_msg}")
        return {"FINISHED"}


# ── Operator: Load Trailer ────────────────────────────────────────────────────

class CAR_OT_LoadTrailer(bpy.types.Operator):
    bl_idname      = "car.load_trailer"
    bl_label       = "Load Trailer"
    bl_description = (
        "Load an editable trailer (body + 4 wheels) behind the current car. Uses "
        "the car's own {NAME}_TRAILER if present, otherwise the stock semi trailer "
        "as a starting point. Edit it like the car, then Create AR + Start Game "
        "(the trailer is packed as a {NAME}_TRAILER sub-car)."
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "Load a car first, then load a trailer.")
            return {"CANCELLED"}

        car_name   = _base_car_name(body_obj["mm_car_name"])
        tex_folder = _tex_folder(context.scene)

        # Source: this car's own trailer if present, else the stock semi trailer.
        src = Folder.Resources.Editor.MeshesCars / f"{car_name}_TRAILER"
        if not (src / "TRAILER_H.BMS").exists():
            src = Folder.Resources.Editor.MeshesCars / "VPSEMI_TRAILER"
        if not (src / "TRAILER_H.BMS").exists():
            self.report({"ERROR"}, f"No trailer BMS found at {src}")
            return {"CANCELLED"}

        _clear_trailer_objects()
        col = _get_or_create_collection(_CAR_COLLECTION)

        # Trailer root empty at the car origin, NO rotation/offset — this is the
        # trailer's coordinate frame and it must match the game's so editing is
        # WYSIWYG. The trailer's stock part offsets are game +z, which maps to
        # Blender +Y (= behind the car, since the car's rear is +z), so the parts
        # naturally lay out behind the car. Export uses each part's transform
        # RELATIVE to this root, i.e. trailer-local coordinates.
        root = bpy.data.objects.new(f"{car_name}.TRAILER_ROOT", None)
        col.objects.link(root)
        root.parent = body_obj
        root.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        root.location           = (0.0, 0.0, 0.0)
        root.empty_display_size = 1.0
        root[_CAR_TAG]          = "trailer_root"
        root["mm_trailer_name"] = f"{car_name}_TRAILER"

        # Body + wheels are all centered+offset (like wheels), parented to the root.
        n_parts = 0
        body_mesh = _load_bms(src / "TRAILER_H.BMS", f"{car_name}.TRAILER", tex_folder)
        if body_mesh:
            _add_child_obj(body_mesh, body_mesh.name, "trailer_body", root, col)
            n_parts += 1

        for i in range(10):
            f = src / f"TWHL{i}_H.BMS"
            if not f.exists():
                break
            wm = _load_bms(f, f"{car_name}.TWHL{i}", tex_folder)
            if wm:
                _add_child_obj(wm, wm.name, f"trailer_wheel_{i}", root, col)
                n_parts += 1

        # Sync the "Trailer Wheels" texture dropdowns to the actual loaded textures
        # (otherwise they'd hang on a default like Police/Mustang).
        _sync_trailer_wheel_texture_props(context.scene)

        self.report({"INFO"}, f"Loaded trailer ({n_parts} parts) — edit, then Create AR + Start Game.")
        return {"FINISHED"}


# ── Operator: Load Siren Lights ───────────────────────────────────────────────

class CAR_OT_LoadSirenLights(bpy.types.Operator):
    bl_idname      = "car.load_siren_lights"
    bl_label       = "Load Siren Lights"
    bl_description = (
        "Load editable red/blue police lights onto the car roof. Move them to "
        "position (grab/G); on Create AR + Start Game they pack as REDLIGHT/"
        "BLUELIGHT and the horn key toggles the flashing siren."
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "Load a car first, then load siren lights.")
            return {"CANCELLED"}

        car_name   = _base_car_name(body_obj["mm_car_name"])
        tex_folder = _tex_folder(context.scene)
        src = Folder.Resources.Editor.MeshesCars / "VPCOP"

        # Replace any existing siren parts (housing + lights).
        for o in _get_siren_light_objs() + _get_siren_housing_objs():
            bpy.data.objects.remove(o, do_unlink=True)

        col = _get_or_create_collection(_CAR_COLLECTION)
        context.view_layer.update()

        # Roof anchor from the body MESH (cabin peak + its centre), robust to low
        # wedge cars where the high point sits forward of the bounding-box centre.
        top_z, roof_x, roof_y = _body_roof_anchor(body_obj)

        loaded_objs = []

        # ── Always-visible housing: extract VPCOPLIGHTS faces from VPCOP body ──
        body_bms = src / "BODY_H.BMS"
        if body_bms.exists():
            try:
                housing_bms = _bms_extract_faces_by_texture(
                    read_bms(body_bms), ["VPCOPLIGHTS"], max_yspan=0.4)
                if housing_bms["num_surfaces"]:
                    hmesh = build_blender_mesh(f"{car_name}.{_SIREN_HOUSING_TAG}", housing_bms)
                    _apply_materials_to_mesh(hmesh, housing_bms["texture_names"], tex_folder)
                    loaded_objs.append(
                        _add_child_obj(hmesh, hmesh.name, _SIREN_HOUSING_TAG, body_obj, col))
            except Exception as exc:
                print(f"[Car Editor] Housing extraction failed: {exc}")

        # ── Flashing lenses (REDLIGHT / BLUELIGHT) ────────────────────────────
        for tag, mesh_file in _SIREN_LIGHT_TAGS.items():
            f = src / mesh_file
            if not f.exists():
                print(f"[Car Editor] Siren light mesh missing: {f}")
                continue
            mesh = _load_bms(f, f"{car_name}.{tag}", tex_folder)
            if not mesh:
                continue
            loaded_objs.append(_add_child_obj(mesh, mesh.name, tag, body_obj, col))

        if not loaded_objs:
            self.report({"ERROR"}, "No siren meshes found in VPCOP.")
            return {"CANCELLED"}

        # Place the whole rig as ONE group, anchored on the housing (the bar): its
        # bottom rests on the roof and its centre is over the cabin; the lenses keep
        # their position relative to the bar instead of each drifting independently.
        context.view_layer.update()
        anchor = next((o for o in loaded_objs if o.get(_CAR_TAG) == _SIREN_HOUSING_TAG),
                      loaded_objs[0])
        ac = [anchor.matrix_world @ mathutils.Vector(c) for c in anchor.bound_box]
        dx = roof_x - sum(c.x for c in ac) / 8.0
        dy = roof_y - sum(c.y for c in ac) / 8.0
        dz = top_z - min(c.z for c in ac)
        for o in loaded_objs:
            o.location = (o.location.x + dx, o.location.y + dy, o.location.z + dz)

        loaded = len(loaded_objs)
        context.scene.ce_add_siren = True

        # Stock REDLIGHT/BLUELIGHT both carry a red glow; tint the blue lens blue so
        # the bar reads red+blue by default. The Lights panel can recolour either.
        try:
            bpy.ops.car.set_light_color("EXEC_DEFAULT", part_tag="light_blue",
                                        color="FXLTGLOWBLUE")
        except Exception:
            pass
        _sync_light_props(context.scene)

        # Select all siren parts so a single grab (G) moves the whole bar together.
        bpy.ops.object.select_all(action="DESELECT")
        parts = _get_siren_housing_objs() + _get_siren_light_objs()
        for o in parts:
            o.select_set(True)
        if parts:
            context.view_layer.objects.active = parts[0]

        self.report({"INFO"},
                    "Loaded siren bar (housing + red/blue flash) on the roof — grab (G) to "
                    "position all, then Create AR + Start Game. Recolour in the Lights panel; "
                    "horn toggles the siren.")
        return {"FINISHED"}


# ── Operator: Load Car Lights ─────────────────────────────────────────────────

class CAR_OT_LoadCarLights(bpy.types.Operator):
    bl_idname      = "car.load_car_lights"
    bl_label       = "Load Lights"
    bl_description = (
        "Load the car's head / tail / brake / reverse / signal glow meshes as "
        "editable parts (from this car, or VPMUSTANG99 as a fallback). They render "
        "as additive glows in-game; move, recolour, then Create AR + Start Game."
    )

    def execute(self, context):
        body = get_car_body()
        if body is None:
            self.report({"ERROR"}, "Load a car first, then load lights.")
            return {"CANCELLED"}
        car_name   = _base_car_name(body["mm_car_name"])
        tex_folder = _tex_folder(context.scene)
        src = Path(body.get("mm_car_folder", "")) if body.get("mm_car_folder") else None
        if not (src and src.is_dir()):
            src = Folder.Resources.Editor.MeshesCars / "VPMUSTANG99"

        col = _get_or_create_collection(_CAR_COLLECTION)
        n = _load_car_lights(car_name, src, body, col, tex_folder)
        if not n:
            self.report({"ERROR"}, "No light meshes found for this car or VPMUSTANG99.")
            return {"CANCELLED"}
        _sync_light_props(context.scene)
        self.report({"INFO"},
                    f"Loaded {n} light(s). Edit/recolour in the Lights panel, then "
                    "Create AR + Start Game.")
        return {"FINISHED"}


class CAR_OT_SetLightColor(bpy.types.Operator):
    bl_idname      = "car.set_light_color"
    bl_label       = "Set Light Colour"
    bl_description = "Swap this light's glow colour (white / red / amber)"
    bl_options     = {"REGISTER", "UNDO"}

    part_tag : bpy.props.StringProperty()
    color    : bpy.props.StringProperty(default="FXLTGLOW")

    def execute(self, context):
        objs = [o for o in get_car_objects()
                if o.get(_CAR_TAG) == self.part_tag and o.type == "MESH"]
        if not objs:
            return {"CANCELLED"}
        tex_folder = _tex_folder(context.scene)
        # color is the chosen glow texture (FXLTGLOW / ...RED / ...BLUE / …).
        suffix = self.color.upper().replace("FXLTGLOW", "", 1)
        # Recolour BOTH the glow billboard AND the beam cone so Blender and the
        # game agree. Coloured variants are generated on demand from the white
        # source (so blue/green and coloured cones exist even though the game ships
        # only white/red/amber).
        for obj in objs:
            mesh = obj.data
            for i, mat in enumerate(mesh.materials):
                if not mat:
                    continue
                u = mat.name.upper()
                if u.startswith("FXLTGLOW") or u.startswith("FXLTCONE"):
                    target = _colored_tex(mat.name, suffix)
                    _ensure_glow_texture(target, tex_folder)
                    mesh.materials[i] = _build_material(target, tex_folder)
        return {"FINISHED"}


class CAR_OT_SetBeamLength(bpy.types.Operator):
    bl_idname      = "car.set_beam_length"
    bl_label       = "Set Headlight Beam Length"
    bl_description = "Lengthen / shorten the headlight beam cone"
    bl_options     = {"REGISTER", "UNDO"}

    factor : bpy.props.FloatProperty(default=1.0, min=0.2, max=4.0)

    def execute(self, context):
        objs = [o for o in get_car_objects()
                if o.get(_CAR_TAG) == "light_head" and o.type == "MESH"]
        if not objs:
            return {"CANCELLED"}
        obj   = objs[0]
        cur   = float(obj.get("light_beam", 1.0)) or 1.0
        ratio = self.factor / cur
        if abs(ratio - 1.0) > 1e-3:
            mesh = obj.data
            # Only the beam CONE (FXLTCONE) should stretch; the glow billboard
            # (FXLTGLOW) marks the headlight position and must stay put. Collect the
            # verts used by cone faces and scale just those.
            cone_slots = {i for i, m in enumerate(mesh.materials)
                          if m and m.name.upper().startswith("FXLTCONE")}
            cone_verts = set()
            if cone_slots:
                for poly in mesh.polygons:
                    if poly.material_index in cone_slots:
                        cone_verts.update(poly.vertices)
            bm = bmesh.new(); bm.from_mesh(mesh)
            bm.verts.ensure_lookup_table()
            target = ([bm.verts[i] for i in cone_verts] if cone_verts else list(bm.verts))
            # The beam runs along Blender Y (game fore/aft); the headlight (near)
            # end sits at the largest Y. Anchor there so the cone grows forward only.
            anchor = max(v.co.y for v in target)
            for v in target:
                v.co.y = anchor + (v.co.y - anchor) * ratio
            bm.to_mesh(mesh); bm.free(); mesh.update()
        obj["light_beam"] = self.factor
        return {"FINISHED"}


class CAR_OT_ToggleLightGlows(bpy.types.Operator):
    bl_idname      = "car.toggle_light_glows"
    bl_label       = "Toggle Light Glows"
    bl_description = "Show/hide the light & siren glow meshes in the viewport (they're additive in-game; hide them while editing the body)"

    def execute(self, context):
        hide = bool(context.scene.ce_hide_light_glows)
        for o in get_car_objects():
            tag = o.get(_CAR_TAG, "")
            if _is_car_light(tag) or _is_siren_part(tag):
                o.hide_set(hide)
        return {"FINISHED"}


# ── Operator: Export Car ──────────────────────────────────────────────────────

class CAR_OT_ExportCar(bpy.types.Operator):
    bl_idname      = "car.export_car"
    bl_label       = "Export Car to BMS"
    bl_description = (
        "Export all loaded car parts back to BMS files. "
        "Output files are written to the Export Folder (scene property)."
    )

    def execute(self, context):
        scene       = context.scene
        car_objects = get_car_objects()
        if not car_objects:
            self.report({"ERROR"}, "No car parts loaded — use Load Car first.")
            return {"CANCELLED"}

        # Validate delete_shop when Add to City is requested
        if scene.ce_add_to_city:
            try:
                from src.USER.settings.main import delete_shop as _delete_shop
            except ImportError:
                _delete_shop = True
            if not _delete_shop:
                self.report(
                    {"ERROR"},
                    "Add to City requires 'delete_shop = True' in src/USER/settings/main.py. "
                    "Set it to True so the game picks up your car from the .AR file instead of raw shop files."
                )
                return {"CANCELLED"}

        body_obj = get_car_body()
        car_name = _base_car_name(body_obj["mm_car_name"] if body_obj else "CAR")

        # Commit any pending Edit Mode changes before reading mesh data.
        active_obj = context.view_layer.objects.active
        was_edit   = active_obj is not None and active_obj.mode == "EDIT"
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")

        # Timestamped export dir — timestamp generated fresh at export time
        export_dir = Folder.Blender.Export / "cars" / f"{car_name}_{CURRENT_TIME_FORMATTED}"
        export_dir.mkdir(parents=True, exist_ok=True)
        scene.ce_last_export_dir = str(export_dir)

        # Add to City: SHOP/BMS/<car_name>/ — no timestamp, exact name required by game
        city_dir = None
        if scene.ce_add_to_city:
            city_dir = Folder.Shop.Meshes / car_name
            city_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        errors   = []

        for obj in car_objects:
            part_tag = obj.get(_CAR_TAG, "unknown")
            if _is_trailer_part(part_tag):
                continue  # trailer is packed via Create AR + Start Game
            if _is_siren_part(part_tag):
                continue  # siren parts are handled during Create AR + Start Game
            if _is_car_light(part_tag):
                continue  # car lights are handled during Create AR + Start Game
            src_file = obj.data.get("bms_source_file", "")

            if src_file:
                out_name = Path(src_file).name
            elif part_tag == "body":
                out_name = "BODY_H.BMS"
            elif part_tag.startswith("wheel_"):
                idx = part_tag.split("_")[1]
                out_name = f"WHL{idx}_H.BMS"
            elif part_tag.startswith("fender_"):
                idx = part_tag.split("_")[1]
                out_name = f"FNDR{idx}_H.BMS"
            else:
                out_name = f"{part_tag.upper()}.BMS"

            try:
                is_wheel = part_tag.startswith("wheel_")
                bms_data = mesh_to_bms_data(obj, bake_location=is_wheel)
                write_bms(bms_data, export_dir / out_name)
                if city_dir:
                    write_bms(bms_data, city_dir / out_name)
                exported.append(out_name)
                print(f"[Car Editor] Exported: {export_dir / out_name}")
            except Exception as exc:
                errors.append(f"{out_name}: {exc}")
                print(f"[Car Editor] Export failed for {out_name}: {exc}")

        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")

        for i in range(10):
            whl_h = export_dir / f"WHL{i}_H.BMS"
            if not whl_h.exists():
                break
            shutil.copy2(whl_h, export_dir / f"WHL{i}_M.BMS")
            shutil.copy2(whl_h, export_dir / f"WHL{i}_L.BMS")
            if city_dir:
                shutil.copy2(whl_h, city_dir / f"WHL{i}_M.BMS")
                shutil.copy2(whl_h, city_dir / f"WHL{i}_L.BMS")

        if errors:
            self.report({"WARNING"}, f"Exported {len(exported)}, {len(errors)} error(s): {errors[0]}")
        else:
            msg = f"Exported {len(exported)} BMS file(s) to {export_dir}"
            if city_dir:
                msg += f" + SHOP/BMS/{car_name}"
            self.report({"INFO"}, msg)

        if scene.ce_auto_reload and not errors:
            bpy.ops.car.reload_car("EXEC_DEFAULT")

        return {"FINISHED"}


# ── Operator: Reload (verify export) ─────────────────────────────────────────

class CAR_OT_ReloadCar(bpy.types.Operator):
    bl_idname      = "car.reload_car"
    bl_label       = "Reload Exported Car"
    bl_description = (
        "Reload the exported BMS files from the Export Folder for visual verification. "
        "Replaces the current car editor objects."
    )

    def execute(self, context):
        scene      = context.scene
        last_dir   = scene.ce_last_export_dir.strip()
        if not last_dir:
            self.report({"ERROR"}, "No export found yet — export first.")
            return {"CANCELLED"}
        export_dir = Path(last_dir)
        if not export_dir.is_dir():
            self.report({"ERROR"}, f"Export folder not found: {export_dir}")
            return {"CANCELLED"}

        # Verify that at least a body BMS exists before delegating to LoadCar
        # (LoadCar will error-cancel if the body is missing; surface that clearly).
        body_found = any((export_dir / name).exists()
                         for name in ("BODY_H.BMS", "BODY_M.BMS", "H.BMS"))
        if not body_found:
            self.report({"ERROR"},
                        "No body BMS in export folder — body may have failed to export. "
                        "Check the system console for details.")
            return {"CANCELLED"}

        original_folder     = scene.ce_car_folder
        scene.ce_car_folder = str(export_dir)

        try:
            bpy.ops.car.load_car("EXEC_DEFAULT", directory=str(export_dir) + "/")
        except Exception as exc:
            scene.ce_car_folder = original_folder
            self.report({"ERROR"}, f"Reload failed: {exc}")
            return {"CANCELLED"}

        # Restore original source folder reference so the inspector still shows it.
        body_obj = get_car_body()
        if body_obj:
            body_obj["mm_car_folder"] = original_folder

        self.report({"INFO"}, f"Reloaded from {export_dir}")
        return {"FINISHED"}


# ── Operator: Clear Car ───────────────────────────────────────────────────────

class CAR_OT_ClearCar(bpy.types.Operator):
    bl_idname      = "car.clear_car"
    bl_label       = "Clear Car"
    bl_description = "Remove all Car Editor objects from the scene."

    def execute(self, context):
        _clear_car_objects()
        self.report({"INFO"}, "Car editor objects cleared.")
        return {"FINISHED"}


# ── Operator: Assign Texture to Selected Faces ────────────────────────────────

class CAR_OT_AssignTexture(bpy.types.Operator):
    bl_idname      = "car.assign_texture"
    bl_label       = "Assign Texture to Faces"
    bl_description = (
        "Assign the chosen texture slot index to all selected faces "
        "(Edit Mode).  Use the Face Texture Slot spinner in the panel."
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.mode != "EDIT":
            self.report({"WARNING"}, "Enter Edit Mode and select faces first.")
            return {"CANCELLED"}

        slot_idx = context.scene.ce_assign_slot
        if slot_idx >= len(obj.material_slots):
            self.report({"WARNING"}, f"Slot {slot_idx} does not exist on this mesh.")
            return {"CANCELLED"}

        # Assign material slot to selected faces via bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        changed = 0
        for face in bm.faces:
            if face.select:
                face.material_index = slot_idx
                changed += 1
        bmesh.update_edit_mesh(obj.data)

        self.report({"INFO"}, f"Assigned slot {slot_idx} to {changed} face(s).")
        return {"FINISHED"}


# ── Operator: Browse Export Folder ────────────────────────────────────────────

class CAR_OT_BrowseExportFolder(bpy.types.Operator):
    bl_idname      = "car.browse_export_folder"
    bl_label       = "Browse Export Folder"
    bl_description = "Set the folder where exported BMS files are written."

    directory: bpy.props.StringProperty(subtype="DIR_PATH", default="")

    def invoke(self, context, event):
        if context.scene.ce_export_folder:
            self.directory = context.scene.ce_export_folder
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        context.scene.ce_export_folder = self.directory.rstrip("/\\")
        return {"FINISHED"}


# ── Operator: Cycle face selection ───────────────────────────────────────────

class CAR_OT_SelectFace(bpy.types.Operator):
    bl_idname      = "car.select_face"
    bl_label       = "Select Face"
    bl_description = "Select the next or previous face on the active car part"
    bl_options     = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(
        items=[("NEXT", "Next", ""), ("PREV", "Previous", "")],
        default="NEXT",
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}

        # Ensure Edit Mode + Face select
        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        n = len(bm.faces)
        if n == 0:
            return {"CANCELLED"}

        # Find currently active face index
        current = bm.faces.active.index if bm.faces.active else -1

        if self.direction == "NEXT":
            target = (current + 1) % n
        else:
            target = (current - 1) % n

        # Deselect all, select target
        for f in bm.faces:
            f.select = False
        bm.faces[target].select = True
        bm.faces.active = bm.faces[target]

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
        context.scene.ce_active_face_index = target
        _read_back_face_uv(context.scene, obj, bm.faces[target])
        return {"FINISHED"}


# ── Operator: Apply UV tiling/rotation to selected faces ──────────────────────

class CAR_OT_ApplyFaceUV(bpy.types.Operator):
    bl_idname      = "car.apply_face_uv"
    bl_label       = "Apply UV to Selected Faces"
    bl_description = (
        "Apply Tile X/Y and Rotation to the UVs of all selected faces "
        "(Edit Mode). Each face is mapped independently from its corners."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.mode != "EDIT":
            self.report({"WARNING"}, "Enter Edit Mode and select faces first.")
            return {"CANCELLED"}

        scene = context.scene
        tile_x   = scene.ce_face_tile_x
        tile_y   = scene.ce_face_tile_y
        angle    = math.radians(scene.ce_face_rotation)
        cx, cy   = 0.5, 0.5

        def _rotated(bx, by):
            bx -= cx; by -= cy
            rx = bx * math.cos(angle) - by * math.sin(angle)
            ry = bx * math.sin(angle) + by * math.cos(angle)
            return ((rx + cx) * tile_x, 1.0 - (ry + cy) * tile_y)

        quad_uvs = [_rotated(x, y) for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]]
        tri_uvs  = [_rotated(x, y) for x, y in [(0, 0), (1, 0), (0.5, 1)]]

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.new("UVMap")

        changed = 0
        for face in bm.faces:
            if not face.select:
                continue
            loops = list(face.loops)
            uvs   = tri_uvs if len(loops) == 3 else quad_uvs
            for i, loop in enumerate(loops):
                loop[uv_layer].uv = uvs[i % len(uvs)]
            changed += 1

        bmesh.update_edit_mesh(obj.data)
        self.report({"INFO"}, f"Applied UV to {changed} face(s).")
        return {"FINISHED"}


# ── Operator: Add quad or triangle at 3D cursor ───────────────────────────────

class CAR_OT_AddFace(bpy.types.Operator):
    bl_idname      = "car.add_face"
    bl_label       = "Add Face at Cursor"
    bl_description = (
        "Add a quad or triangle at the 3D cursor position, parented to the "
        "active car part (Edit Mode). Assigns the current texture slot."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a car part first.")
            return {"CANCELLED"}

        was_object_mode = (obj.mode != "EDIT")
        if was_object_mode:
            bpy.ops.object.mode_set(mode="EDIT")

        scene  = context.scene
        size   = scene.ce_add_size
        shape  = scene.ce_add_shape
        half   = size * 0.5
        slot   = max(0, min(scene.ce_assign_slot, len(obj.data.materials) - 1))

        # Cursor in local object space
        cursor = context.scene.cursor.location
        local  = obj.matrix_world.inverted() @ cursor
        x, y, z = local.x, local.y, local.z

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            uv_layer = bm.loops.layers.uv.new("UVMap")

        if shape == "TRI":
            verts = [
                bm.verts.new((x - half, y - half, z)),
                bm.verts.new((x + half, y - half, z)),
                bm.verts.new((x,        y + half, z)),
            ]
            base_uvs = [(0, 0), (1, 0), (0.5, 1)]
        else:
            verts = [
                bm.verts.new((x - half, y - half, z)),
                bm.verts.new((x + half, y - half, z)),
                bm.verts.new((x + half, y + half, z)),
                bm.verts.new((x - half, y + half, z)),
            ]
            base_uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

        face = bm.faces.new(verts)
        face.material_index = slot
        for i, loop in enumerate(face.loops):
            u, v = base_uvs[i]
            loop[uv_layer].uv = (u, 1.0 - v)

        bm.verts.index_update()
        bmesh.update_edit_mesh(obj.data)
        self.report({"INFO"}, f"Added {shape} at cursor.")
        return {"FINISHED"}


# ── Operator: Add a texture slot (material) to the active car part ────────────

class CAR_OT_AddTextureSlot(bpy.types.Operator):
    bl_idname      = "car.add_texture_slot"
    bl_label       = "Add Texture Slot"
    bl_description = (
        "Add a new material/texture slot to the active car part. "
        "Enter the texture name (without .dds) in the field above."
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None or not is_car_obj(obj):
            self.report({"WARNING"}, "Select a car part first.")
            return {"CANCELLED"}

        tex_name   = context.scene.ce_new_tex_name.strip()
        if not tex_name:
            self.report({"WARNING"}, "Enter a texture name in the field first.")
            return {"CANCELLED"}

        mesh = obj.data
        if any(m and m.name == tex_name for m in mesh.materials):
            self.report({"INFO"}, f"Slot '{tex_name}' already exists.")
            return {"FINISHED"}

        if tex_name in bpy.data.materials:
            mat = bpy.data.materials[tex_name]
        else:
            mat = bpy.data.materials.new(name=tex_name)
            tex_folder_str = context.scene.ce_texture_folder
            if tex_folder_str:
                tex_folder = Path(tex_folder_str)
                tex_path   = tex_folder / f"{tex_name}.dds"
                if not tex_path.exists():
                    tex_path = tex_folder / f"{tex_name}.DDS"
                if tex_path.exists():
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    for n in list(nodes):
                        nodes.remove(n)
                    bsdf     = nodes.new("ShaderNodeBsdfPrincipled")
                    tex_node = nodes.new("ShaderNodeTexImage")
                    tex_node.image = bpy.data.images.load(str(tex_path), check_existing=True)
                    links = mat.node_tree.links
                    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
                    out = nodes.new("ShaderNodeOutputMaterial")
                    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

        mesh.materials.append(mat)
        self.report({"INFO"}, f"Added slot [{len(mesh.materials)-1}] '{tex_name}'.")
        return {"FINISHED"}


# ── Operator: Switch paint variant ───────────────────────────────────────────

class CAR_OT_SetPaintVariant(bpy.types.Operator):
    bl_idname      = "car.set_paint_variant"
    bl_label       = "Set Paint Variant"
    bl_description = "Switch to a different car paint job / colour variant"

    variant: bpy.props.StringProperty(default="")

    def execute(self, context):
        scene          = context.scene
        car_objects    = get_car_objects()
        body_obj       = get_car_body()
        if not car_objects or not body_obj:
            self.report({"WARNING"}, "No car loaded.")
            return {"CANCELLED"}

        new_prefix     = self.variant
        current_prefix = scene.ce_paint_variant
        if not new_prefix or new_prefix == current_prefix:
            return {"FINISHED"}

        tex_folder = _tex_folder(scene)

        swapped = _apply_paint_variant(car_objects, new_prefix, current_prefix, tex_folder)
        if swapped:
            scene.ce_paint_variant = new_prefix
            self.report({"INFO"}, f"Paint → {new_prefix}  ({swapped} slot(s) swapped).")
        else:
            self.report({"WARNING"}, f"No matching DDS textures found for '{new_prefix}'.")
        return {"FINISHED"}


# ── Operator: Toggle Damage View ──────────────────────────────────────────────

class CAR_OT_ToggleDamage(bpy.types.Operator):
    bl_idname      = "car.toggle_damage"
    bl_label       = "Toggle Damage"
    bl_description = (
        "Switch between normal and damaged appearance by remapping face material slots "
        "to their _DMG counterparts (already embedded in the BMS). "
        "Only VP player cars include _DMG texture variants."
    )

    def execute(self, context):
        scene       = context.scene
        car_objects = get_car_objects()
        if not car_objects:
            self.report({"WARNING"}, "No car loaded.")
            return {"CANCELLED"}

        going_to_damage  = not scene.ce_show_damage
        seen_meshes      = set()
        total_faces      = 0
        any_dmg_found    = False

        for obj in car_objects:
            if obj.type != "MESH":
                continue
            mesh = obj.data
            if id(mesh) in seen_meshes:
                continue
            seen_meshes.add(id(mesh))

            fwd = _build_damage_remap(mesh)
            if not fwd:
                continue
            any_dmg_found = True

            remap = fwd if going_to_damage else {v: k for k, v in fwd.items()}

            for poly in mesh.polygons:
                new_idx = remap.get(poly.material_index)
                if new_idx is not None:
                    poly.material_index = new_idx
                    total_faces += 1

            mesh.update()

        if not any_dmg_found:
            self.report({"INFO"}, "No _DMG material slots found — this car has no damage variants.")
            return {"CANCELLED"}

        scene.ce_show_damage = going_to_damage
        label = "damage" if going_to_damage else "normal"
        self.report({"INFO"}, f"Damage view {'ON' if going_to_damage else 'OFF'} — {total_faces} faces remapped.")
        return {"FINISHED"}


# ── Operator: Remove Wheel ────────────────────────────────────────────────────

class CAR_OT_RemoveWheel(bpy.types.Operator):
    bl_idname      = "car.remove_wheel"
    bl_label       = "Remove Selected Wheel"
    bl_description = (
        "Delete the currently active wheel object. "
        "Remaining wheels keep their indices — re-index with 'Renumber Wheels' if needed."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or not is_car_obj(obj):
            self.report({"WARNING"}, "Select a car wheel first.")
            return {"CANCELLED"}

        tag = obj.get(_CAR_TAG, "")
        if not tag.startswith("wheel_"):
            self.report({"WARNING"},
                        f"Active object is '{tag}', not a wheel. Select a wheel part.")
            return {"CANCELLED"}

        name = obj.name
        bpy.data.objects.remove(obj, do_unlink=True)
        self.report({"INFO"}, f"Removed {name}.")
        return {"FINISHED"}


# ── Operator: Renumber Wheels ─────────────────────────────────────────────────

class CAR_OT_RenumberWheels(bpy.types.Operator):
    bl_idname      = "car.renumber_wheels"
    bl_label       = "Renumber Wheels"
    bl_description = (
        "Re-index all wheel_N tags to a continuous 0-based sequence "
        "so WHL0_H … WHLM_H are exported without gaps."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_objs = get_car_objects()
        wheels = sorted(
            [o for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_")],
            key=lambda o: int(o.get(_CAR_TAG, "wheel_0").split("_")[1])
        )
        if not wheels:
            self.report({"WARNING"}, "No wheels found.")
            return {"CANCELLED"}

        body_obj = get_car_body()
        car_name = body_obj.get("mm_car_name", "CAR") if body_obj else "CAR"

        for new_i, whl_obj in enumerate(wheels):
            whl_obj[_CAR_TAG] = f"wheel_{new_i}"
            whl_obj.name      = f"{car_name}.WHL{new_i}"

        self.report({"INFO"}, f"Renumbered {len(wheels)} wheels (0 … {len(wheels)-1}).")
        return {"FINISHED"}


# ── Operator: Open Export Folder in Explorer ──────────────────────────────────

class CAR_OT_OpenExportFolder(bpy.types.Operator):
    bl_idname      = "car.open_export_folder"
    bl_label       = "Open Export Folder"
    bl_description = "Open the last export folder in Windows Explorer"

    def execute(self, context):
        last_dir = context.scene.ce_last_export_dir.strip()
        if not last_dir:
            self.report({"WARNING"}, "No export folder yet.")
            return {"CANCELLED"}
        p = Path(last_dir)
        if not p.exists():
            self.report({"WARNING"}, f"Folder not found: {p}")
            return {"CANCELLED"}
        subprocess.Popen(["explorer", str(p)])
        return {"FINISHED"}


# ── Operator: Clear Shop BMS folder ──────────────────────────────────────────

class CAR_OT_ClearShop(bpy.types.Operator):
    bl_idname      = "car.clear_shop"
    bl_label       = "Clear Shop"
    bl_description = (
        "Delete all files in SHOP/BMS/{car_name}/ for the currently loaded car. "
        "Use this before re-exporting to avoid stale LOD or light files being packed."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"INFO"}, "No car loaded — nothing to clear.")
            return {"FINISHED"}
        car_name = _base_car_name(body_obj.get("mm_car_name", ""))
        shop_dir = Folder.Shop.Meshes / car_name
        if not shop_dir.exists():
            self.report({"INFO"}, f"SHOP/BMS/{car_name}/ does not exist, nothing to clear.")
            return {"FINISHED"}
        n = sum(1 for f in shop_dir.iterdir() if f.is_file())
        shutil.rmtree(shop_dir)
        shop_dir.mkdir()
        self.report({"INFO"}, f"Cleared {n} file(s) from SHOP/BMS/{car_name}/.")
        return {"FINISHED"}


# ── Operator: New Car From Template ──────────────────────────────────────────

class CAR_OT_MakeCustomCopy(bpy.types.Operator):
    bl_idname      = "car.make_custom_copy"
    bl_label       = "Save as Custom Car"
    bl_description = (
        "Convert the loaded car into an editable CUSTOM car under the Menu Name. "
        "Custom cars use the full export pipeline, so siren / trailer / paint / "
        "physics all work (stock cars only override geometry). The original car is "
        "left untouched. After this, click Create AR + Start Game."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        body  = get_car_body()
        if body is None:
            self.report({"ERROR"}, "Load a car first.")
            return {"CANCELLED"}

        display = (scene.ce_car_display_name or "").strip()
        if not display:
            self.report({"ERROR"}, "Set a Menu Name first (Create panel).")
            return {"CANCELLED"}

        new_name  = "VP" + display.upper().replace(" ", "")
        orig_name = _base_car_name(body.get("mm_car_name", ""))
        if new_name == orig_name:
            self.report({"ERROR"}, "Menu Name matches the loaded car — pick a different name for the copy.")
            return {"CANCELLED"}
        if _is_original_car(new_name):
            self.report({"ERROR"}, f"{new_name} is a stock car name — choose a different Menu Name.")
            return {"CANCELLED"}

        # Rename the loaded car to the custom name (only the body carries the name).
        body["mm_car_name"]   = new_name
        body["mm_car_folder"] = ""
        body["mm_body_file"]  = "BODY_H.BMS"
        try:
            body.name = new_name
        except Exception:
            pass

        # Build support files for the new name, then override physics with the
        # original car's MMCARSIM so the copy drives like the source.
        msgs = _init_new_car_files(new_name, display)
        _sync_info_props_from_car(scene, new_name)
        base_carsim = _base_carsim_path(orig_name)
        if base_carsim is not None:
            shutil.copy2(base_carsim, Folder.Shop.Tune / f"{new_name}.MMCARSIM")
            msgs.append(f"physics sourced from {orig_name}")

        _paint_variant_cache.clear()
        scene.ce_paint_variant = new_name
        _sync_physics_props_from_car(scene, new_name)
        for m in msgs:
            print(f"[Custom Copy] {m}")

        self.report({"INFO"},
                    f"Saved as custom car '{new_name}' (from {orig_name}). "
                    "Now click Create AR + Start Game — siren/trailer/paint/physics all export.")
        return {"FINISHED"}


class CAR_OT_NewFromTemplate(bpy.types.Operator):
    bl_idname      = "car.new_from_template"
    bl_label       = "New Car From Template"
    bl_description = (
        "Create a fresh primitive car (box body + N wheels) from an archetype "
        "template. Clears any car currently loaded."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene       = context.scene
        template_id = scene.ce_template
        if template_id not in car_templates.TEMPLATES:
            self.report({"ERROR"}, f"Unknown template: {template_id}")
            return {"CANCELLED"}

        # Derive filename from the menu name; fall back to template default.
        display_name = (scene.ce_car_display_name or "").strip()
        if display_name:
            car_name = "VP" + display_name.upper().replace(" ", "")
        else:
            car_name = car_templates.get_template_default_name(template_id)

        _clear_car_objects()
        col = _get_or_create_collection(_CAR_COLLECTION)

        # ── Body ──────────────────────────────────────────────────────────────
        body_file  = car_templates.template_body_filename(template_id)
        tex_folder = Folder.Resources.Editor.Textures
        body_tex   = "CARBOTTOM"

        body_mesh = car_templates.build_body_mesh(car_name, template_id)
        body_mesh["texture_names"]   = [body_tex]
        body_mesh["bms_source_file"] = body_file
        body_mesh.materials[0] = _build_material(body_tex, tex_folder)

        body_obj = bpy.data.objects.new(car_name, body_mesh)
        col.objects.link(body_obj)
        body_obj.location          = _bms_to_bl_offset(body_mesh)
        body_obj[_CAR_TAG]         = "body"
        body_obj["mm_car_folder"]  = ""
        body_obj["mm_car_name"]    = car_name
        body_obj["mm_body_file"]   = body_file

        # ── Wheels — chosen style's geometry, auto-sized to the template radius ──
        wheel_positions = car_templates.template_wheel_positions(template_id)
        wheel_prefix    = car_templates.template_wheel_filename_prefix(template_id)
        style           = getattr(scene, "ce_wheel_style", "") or "VPMUSTANG99"

        for i, wpos in enumerate(wheel_positions):
            mesh_name     = f"{car_name}.{wheel_prefix}{i}"
            wdata         = car_templates._T[template_id]["wheels"][i]
            target_radius = wdata[3]
            w_mesh = _load_styled_wheel(car_name, i, style, tex_folder, target_radius)
            if w_mesh is None:
                w_mesh = car_templates.build_wheel_mesh(
                    mesh_name, wdata[3], wdata[4], mirror=(wpos[0] > 0))
                w_mesh.materials[0] = _build_material("VPCOP_WHL", tex_folder)
            else:
                w_mesh.name = mesh_name
            w_mesh["mesh_offset"]     = list(wpos)
            w_mesh["bms_source_file"] = f"{wheel_prefix}{i}_H.BMS"
            _add_child_obj(w_mesh, mesh_name, f"wheel_{i}", body_obj, col)

        scene.ce_car_folder = ""

        bpy.ops.object.select_all(action="DESELECT")
        body_obj.select_set(True)
        context.view_layer.objects.active = body_obj
        try:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        except Exception:
            pass

        # Auto-create support files (TUNE/.INFO/.MMCARSIM, TSH, BND, …) so the car
        # is packable straight away — no separate "Init Support Files" step.
        for m in _init_new_car_files(car_name, display_name or car_name):
            print(f"[New Car] {m}")
        _sync_info_props_from_car(scene, car_name)

        _paint_variant_cache.clear()
        scene.ce_paint_variant = car_name
        scene.ce_show_damage   = False
        _sync_wheel_radius_props(scene)

        n_wheels = len(wheel_positions)
        self.report({"INFO"},
                    f"Created {car_name}: {car_templates.TEMPLATES[template_id]['label']} "
                    f"(box body + {n_wheels} wheels, support files ready).")
        return {"FINISHED"}


# ── Operator: Mirror Selected Wheel ──────────────────────────────────────────

class CAR_OT_MirrorWheel(bpy.types.Operator):
    bl_idname      = "car.mirror_wheel"
    bl_label       = "Mirror Selected Wheel"
    bl_description = (
        "Duplicate the active wheel mirrored across the car's X axis "
        "(same axle, opposite side). New wheel is assigned the next free index."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        obj = context.active_object
        if obj is None or not is_car_obj(obj):
            self.report({"WARNING"}, "Select a wheel first.")
            return {"CANCELLED"}
        tag = obj.get(_CAR_TAG, "")
        if not tag.startswith("wheel_"):
            self.report({"WARNING"}, f"Active object is '{tag}', not a wheel.")
            return {"CANCELLED"}

        wheel_indices = [
            int(o.get(_CAR_TAG, "wheel_0").split("_")[1])
            for o in get_car_objects()
            if o.get(_CAR_TAG, "").startswith("wheel_")
        ]
        new_idx  = max(wheel_indices) + 1 if wheel_indices else 0
        car_name = body_obj.get("mm_car_name", "CAR")

        new_mesh = _mirror_wheel_mesh(obj.data, f"{car_name}.WHL{new_idx}")

        col     = _get_or_create_collection(_CAR_COLLECTION)
        new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", new_mesh)
        col.objects.link(new_obj)
        new_obj.parent                = body_obj
        new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        new_obj[_CAR_TAG]             = f"wheel_{new_idx}"

        # Blender X = -game X — flipping Blender X mirrors the wheel in game space too.
        loc = obj.location
        new_obj.location = (-loc.x, loc.y, loc.z)

        bpy.ops.object.select_all(action="DESELECT")
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        self.report({"INFO"}, f"Mirrored {tag} → wheel_{new_idx}.")
        return {"FINISHED"}


# ── Operator: Mirror All Wheels (auto-symmetry) ──────────────────────────────

class CAR_OT_MirrorAllWheels(bpy.types.Operator):
    bl_idname      = "car.mirror_all_wheels"
    bl_label       = "Mirror All Wheels"
    bl_description = (
        "For every existing wheel, create its X-axis mirror unless a wheel "
        "already sits near that mirrored position (tolerance 0.05 m)."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        car_objs = get_car_objects()
        wheels   = [o for o in car_objs if o.get(_CAR_TAG, "").startswith("wheel_")]
        if not wheels:
            self.report({"WARNING"}, "No wheels to mirror.")
            return {"CANCELLED"}

        TOL      = 0.05
        car_name = body_obj.get("mm_car_name", "CAR")
        col      = _get_or_create_collection(_CAR_COLLECTION)
        next_idx = max(int(o.get(_CAR_TAG, "wheel_0").split("_")[1]) for o in wheels) + 1

        # Snapshot positions BEFORE we add anything, so newly-added mirrors
        # don't shadow further mirror checks.
        snapshot = [(o, o.location.copy()) for o in wheels]
        created  = 0

        for src_obj, src_loc in snapshot:
            mirror_loc = mathutils.Vector((-src_loc.x, src_loc.y, src_loc.z))
            if any((p - mirror_loc).length < TOL for _, p in snapshot):
                continue  # there's already a wheel at the mirrored spot
            new_mesh = _mirror_wheel_mesh(src_obj.data, f"{car_name}.WHL{next_idx}")
            new_obj  = bpy.data.objects.new(f"{car_name}.WHL{next_idx}", new_mesh)
            col.objects.link(new_obj)
            new_obj.parent                = body_obj
            new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
            new_obj[_CAR_TAG]             = f"wheel_{next_idx}"
            new_obj.location              = mirror_loc
            snapshot.append((new_obj, mirror_loc))
            next_idx += 1
            created  += 1

        if created == 0:
            self.report({"INFO"}, "All wheels already have their mirror partner.")
        else:
            self.report({"INFO"}, f"Mirrored {created} wheel(s).")
        return {"FINISHED"}


# ── Operator: Toggle X Symmetry for Edit Mode ────────────────────────────────

class CAR_OT_ToggleSymmetry(bpy.types.Operator):
    bl_idname      = "car.toggle_symmetry"
    bl_label       = "Toggle X Symmetry"
    bl_description = (
        "Toggle Blender's Edit-Mode X-mirror on every car part. "
        "When ON, vertex/edge/face edits are mirrored across the part's local X axis."
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_objs = get_car_objects()
        if not car_objs:
            self.report({"WARNING"}, "No car loaded.")
            return {"CANCELLED"}

        new_val = not context.scene.ce_mirror_x
        for o in car_objs:
            if o.type == "MESH" and o.data is not None:
                o.data.use_mirror_x = new_val
        context.scene.ce_mirror_x = new_val
        self.report({"INFO"}, f"X Symmetry {'ON' if new_val else 'OFF'} for {len(car_objs)} part(s).")
        return {"FINISHED"}


class CAR_OT_ApplyWheelTexture(bpy.types.Operator):
    """Apply the scene-level wheel texture to ALL wheels at once."""
    bl_idname      = "car.apply_wheel_texture"
    bl_label       = "Apply to All Wheels"
    bl_description = "Apply the selected texture to every wheel"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene    = context.scene
        tex_name = scene.ce_wheel_texture
        if not tex_name:
            self.report({"WARNING"}, "No wheel texture selected.")
            return {"CANCELLED"}
        wheels = [o for o in get_car_objects() if o.get(_CAR_TAG, "").startswith("wheel_")]
        if not wheels:
            self.report({"WARNING"}, "No wheels loaded.")
            return {"CANCELLED"}
        tex_folder = _tex_folder(scene)
        n = _apply_wheel_tex(tex_name, wheels, tex_folder)
        for whl in wheels:
            whl["ce_wheel_tex"] = tex_name
        self.report({"INFO"}, f"Applied {tex_name} to {n} wheel(s).")
        return {"FINISHED"}


class CAR_OT_ApplyWheelTextureSingle(bpy.types.Operator):
    """Apply a texture to one specific wheel by part tag."""
    bl_idname      = "car.apply_wheel_texture_single"
    bl_label       = "Apply Wheel Texture"
    bl_description = "Apply this texture to this wheel"
    bl_options     = {"REGISTER", "UNDO"}

    part_tag : bpy.props.StringProperty()
    tex_name : bpy.props.StringProperty()

    def execute(self, context):
        if not self.tex_name:
            return {"CANCELLED"}
        wheels = [o for o in get_car_objects() if o.get(_CAR_TAG) == self.part_tag]
        if not wheels:
            return {"CANCELLED"}
        scene      = context.scene
        tex_folder = _tex_folder(scene)
        _apply_wheel_tex(self.tex_name, wheels, tex_folder)
        # Store choice on the object so the panel can reflect it
        wheels[0]["ce_wheel_tex"] = self.tex_name
        return {"FINISHED"}


class CAR_OT_SetWheelRadius(bpy.types.Operator):
    """Resize one wheel to a given radius (scaled about its hub)."""
    bl_idname      = "car.set_wheel_radius"
    bl_label       = "Set Wheel Radius"
    bl_description = "Resize this wheel to the given radius"
    bl_options     = {"REGISTER", "UNDO"}

    part_tag : bpy.props.StringProperty()
    radius   : bpy.props.FloatProperty(default=0.35, min=0.02, max=3.0)

    def execute(self, context):
        wheels = [o for o in get_car_objects()
                  if o.get(_CAR_TAG) == self.part_tag and o.type == "MESH"]
        if not wheels:
            return {"CANCELLED"}
        obj   = wheels[0]
        old_r = _wheel_current_radius(obj.data)
        _scale_wheel_to_radius(obj.data, self.radius)
        # Keep the wheel grounded: raise/lower the hub by the radius change so the
        # bottom of the tyre stays put instead of sinking into / floating above road.
        if old_r > 0:
            obj.location.z += (self.radius - old_r)
        return {"FINISHED"}


class CAR_OT_SetAllWheelRadius(bpy.types.Operator):
    """Resize every wheel to one radius (each kept grounded)."""
    bl_idname      = "car.set_all_wheel_radius"
    bl_label       = "Set All Wheel Radii"
    bl_description = "Resize every wheel to this radius at once"
    bl_options     = {"REGISTER", "UNDO"}

    radius : bpy.props.FloatProperty(default=0.35, min=0.02, max=3.0)

    def execute(self, context):
        n = 0
        for o in get_car_objects():
            if not o.get(_CAR_TAG, "").startswith("wheel_") or o.type != "MESH":
                continue
            old_r = _wheel_current_radius(o.data)
            _scale_wheel_to_radius(o.data, self.radius)
            if old_r > 0:
                o.location.z += (self.radius - old_r)
            n += 1
        _sync_wheel_radius_props(context.scene)
        self.report({"INFO"}, f"Set {n} wheel(s) to radius {self.radius:.2f}m.")
        return {"FINISHED"}


class CAR_OT_ImportTagBody(bpy.types.Operator):
    bl_idname      = "car.import_tag_body"
    bl_label       = "Tag as Body"
    bl_description = "Tag the active mesh as the car body and add it to the Car Editor"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj      = context.active_object
        car_name = _derive_car_name(context.scene)
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first.")
            return {"CANCELLED"}
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}
        _tag_as_body(obj, car_name)
        context.scene.ce_paint_variant = car_name
        self.report({"INFO"}, f"Tagged '{obj.name}' as body → {car_name}")
        return {"FINISHED"}


class CAR_OT_ImportTagWheel(bpy.types.Operator):
    bl_idname      = "car.import_tag_wheel"
    bl_label       = "Tag as Wheel"
    bl_description = "Tag the active mesh as the next free wheel"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj      = context.active_object
        car_name = _derive_car_name(context.scene)
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first.")
            return {"CANCELLED"}
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}
        existing = [o for o in get_car_objects() if o.get(_CAR_TAG, "").startswith("wheel_")]
        idx = max((int(o.get(_CAR_TAG).split("_")[1]) for o in existing), default=-1) + 1
        _tag_as_wheel(obj, idx, car_name)
        self.report({"INFO"}, f"Tagged '{obj.name}' as wheel_{idx}")
        return {"FINISHED"}


class CAR_OT_ImportAutoTag(bpy.types.Operator):
    bl_idname      = "car.import_auto_tag"
    bl_label       = "Auto-Tag Scene"
    bl_description = (
        "Heuristic: largest mesh by face count → body; "
        "meshes whose bounding box is roughly as wide as tall → wheels. "
        "Works best when all body/wheel objects are selected."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_name = _derive_car_name(context.scene)
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}

        candidates = [o for o in context.selected_objects if o.type == "MESH"]
        if not candidates:
            self.report({"WARNING"}, "Select the imported mesh objects first.")
            return {"CANCELLED"}

        # Largest by face count → body
        body_obj = max(candidates, key=lambda o: len(o.data.polygons))
        _tag_as_body(body_obj, car_name)
        context.scene.ce_paint_variant = car_name
        tagged_wheels = 0

        for o in candidates:
            if o is body_obj:
                continue
            # Wheel heuristic: bounding box roughly circular in XZ and small
            bb   = o.bound_box  # 8 corners in local space
            xs   = [v[0] for v in bb]
            ys   = [v[1] for v in bb]
            zs   = [v[2] for v in bb]
            w    = max(xs) - min(xs)
            h    = max(ys) - min(ys)
            d    = max(zs) - min(zs)
            size = max(w, h, d)
            # Wheel: roughly square cross-section, smaller than body
            if size < (max(body_obj.dimensions) * 0.5) and abs(w - d) < size * 0.6:
                _tag_as_wheel(o, tagged_wheels, car_name)
                tagged_wheels += 1

        context.scene.ce_paint_variant = car_name
        self.report({"INFO"},
                    f"Auto-tagged: 1 body ({body_obj.name}) + {tagged_wheels} wheel(s) → {car_name}")
        return {"FINISHED"}


class CAR_OT_ImportDecimate(bpy.types.Operator):
    bl_idname      = "car.import_decimate"
    bl_label       = "Decimate Active"
    bl_description = "Apply a Decimate modifier to the active mesh to reduce face count for MM1 compatibility"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh first.")
            return {"CANCELLED"}
        ratio    = context.scene.ce_import_decimate_ratio
        n_before = len(obj.data.polygons)
        mod      = obj.modifiers.new(name="MM1_Decimate", type="DECIMATE")
        mod.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)
        n_after = len(obj.data.polygons)
        self.report({"INFO"}, f"Decimated '{obj.name}': {n_before} → {n_after} faces")
        return {"FINISHED"}


class CAR_OT_ImportCleanMaterials(bpy.types.Operator):
    bl_idname      = "car.import_clean_materials"
    bl_label       = "Clean Material Names"
    bl_description = (
        "Rename all material slots on the active object to game-safe names "
        "(uppercase, ASCII only). Unnamed/noisy slots → CARBOTTOM."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh first.")
            return {"CANCELLED"}
        renamed = 0
        for mat in obj.data.materials:
            if mat is None:
                continue
            clean = _clean_mat_name(mat.name)
            if clean != mat.name:
                mat.name = clean
                renamed += 1
        self.report({"INFO"}, f"Cleaned {renamed} material name(s) on '{obj.name}'.")
        return {"FINISHED"}


class CAR_OT_ImportFlattenMaterials(bpy.types.Operator):
    bl_idname      = "car.import_flatten_materials"
    bl_label       = "Flatten All to CARBOTTOM"
    bl_description = (
        "Replace every material slot on every tagged car object with a single "
        "CARBOTTOM entry. Use this when you just want the car to load without "
        "texture errors — CARBOTTOM is always available in GLOBAL.TSH."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        car_objs = get_car_objects()
        if not car_objs:
            self.report({"WARNING"}, "No tagged car objects found.")
            return {"CANCELLED"}

        # Get or create a shared CARBOTTOM material
        mat = bpy.data.materials.get("CARBOTTOM")
        if mat is None:
            mat = bpy.data.materials.new("CARBOTTOM")

        changed = 0
        for obj in car_objs:
            if obj.type != "MESH":
                continue
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            # Assign all faces to slot 0
            for poly in obj.data.polygons:
                poly.material_index = 0
            changed += 1

        self.report({"INFO"}, f"Set CARBOTTOM on {changed} car object(s).")
        return {"FINISHED"}


class CAR_OT_ImportApplyTransforms(bpy.types.Operator):
    bl_idname      = "car.import_apply_transforms"
    bl_label       = "Apply Scale & Rotation"
    bl_description = (
        "Apply scale and rotation transforms on all selected objects. "
        "Run this after importing a .dae/.fbx to bake the 100× scale and "
        "Y-up rotation into vertex data so the BMS export is correct."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        targets = [o for o in context.selected_objects if o.type == "MESH"]
        if not targets:
            self.report({"WARNING"}, "Select at least one mesh object first.")
            return {"CANCELLED"}
        # Apply scale+rotation directly via bmesh — no viewport operator needed.
        for obj in targets:
            mat = obj.matrix_basis
            # Strip translation so we only bake scale+rotation into verts
            mat_sr = mat.copy()
            mat_sr.translation = mathutils.Vector((0, 0, 0))
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.transform(bm, matrix=mat_sr, verts=bm.verts)
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
            # Reset scale+rotation to identity, keep location
            obj.scale    = (1.0, 1.0, 1.0)
            obj.rotation_euler = (0.0, 0.0, 0.0)
        self.report({"INFO"}, f"Applied scale & rotation on {len(targets)} object(s).")
        return {"FINISHED"}


class CAR_OT_SpawnWheelFromTemplate(bpy.types.Operator):
    bl_idname      = "car.spawn_wheel_from_template"
    bl_label       = "Spawn Wheel from Template"
    bl_description = (
        "Load a VPMUSTANG99 reference wheel (WHL0_H.BMS) from resources/editor "
        "and add it as the next free wheel on the current car. "
        "Position it with the 3D cursor or move it after spawning."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car body loaded — tag a body first.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj.get("mm_car_name", "CAR"))

        # Find next free wheel index
        car_objs  = get_car_objects()
        used_idxs = set()
        for o in car_objs:
            tag = o.get(_CAR_TAG, "")
            if tag.startswith("wheel_"):
                try:
                    used_idxs.add(int(tag.split("_")[1]))
                except ValueError:
                    pass
        new_idx = next(i for i in range(20) if i not in used_idxs)

        # Load the chosen wheel style, sized to the panel's wheel radius.
        style  = getattr(context.scene, "ce_wheel_style", "") or "VPMUSTANG99"
        radius = float(getattr(context.scene, "ce_wheel_size", 0.35))
        mesh = _load_styled_wheel(car_name, new_idx, style,
                                  Folder.Resources.Editor.Textures, radius)
        if mesh is None:
            self.report({"ERROR"}, f"Failed to load wheel style '{style}'")
            return {"CANCELLED"}

        mesh["bms_source_file"] = ""  # will export as WHL{new_idx}_H.BMS

        col     = _get_or_create_collection(_CAR_COLLECTION)
        new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", mesh)
        col.objects.link(new_obj)

        new_obj[_CAR_TAG] = f"wheel_{new_idx}"
        new_obj.parent    = body_obj
        # Identity parent-inverse → location is in body-local space.
        # Place wheel at the 3D cursor converted to body-local space.
        new_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        cursor_world = context.scene.cursor.location.copy()
        new_obj.location = body_obj.matrix_world.inverted() @ cursor_world

        for o in context.view_layer.objects:
            o.select_set(False)
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        _sync_wheel_radius_props(context.scene)
        self.report({"INFO"},
                    f"Spawned wheel_{new_idx} sized to {radius:.2f}m. "
                    "Move it to the desired position.")
        return {"FINISHED"}


# ── Operator: Prepare Imported Model (mega-button) ───────────────────────────

class CAR_OT_ImportPrepare(bpy.types.Operator):
    bl_idname      = "car.import_prepare"
    bl_label       = "Prepare Imported Model"
    bl_description = (
        "One-click import prep: auto-tags the selected objects (body + wheels), "
        "flattens all materials to CARBOTTOM, and initialises support files "
        "(TUNE/.INFO/.MMCARSIM/BND). Requires Menu Name to be set."
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene    = context.scene
        car_name = _derive_car_name(scene)
        if not car_name:
            self.report({"ERROR"}, "Set a Menu Name first.")
            return {"CANCELLED"}

        candidates = [o for o in context.selected_objects if o.type == "MESH"]
        if not candidates:
            self.report({"WARNING"}, "Select the imported mesh objects first.")
            return {"CANCELLED"}

        # 1. Auto-tag
        body_obj = max(candidates, key=lambda o: len(o.data.polygons))
        _tag_as_body(body_obj, car_name)
        scene.ce_paint_variant = car_name
        tagged_wheels = 0
        for o in candidates:
            if o is body_obj:
                continue
            bb  = o.bound_box
            xs  = [v[0] for v in bb]; ys = [v[1] for v in bb]; zs = [v[2] for v in bb]
            w   = max(xs) - min(xs);  h  = max(ys) - min(ys);  d  = max(zs) - min(zs)
            sz  = max(w, h, d)
            if sz < (max(body_obj.dimensions) * 0.5) and abs(w - d) < sz * 0.6:
                _tag_as_wheel(o, tagged_wheels, car_name)
                tagged_wheels += 1

        # 2. Flatten all tagged objects to CARBOTTOM
        carbottom = bpy.data.materials.get("CARBOTTOM") or bpy.data.materials.new("CARBOTTOM")
        for obj in get_car_objects():
            if obj.type != "MESH":
                continue
            obj.data.materials.clear()
            obj.data.materials.append(carbottom)
            for poly in obj.data.polygons:
                poly.material_index = 0

        # 3. Init support files
        display = scene.ce_car_display_name.strip() or car_name
        msgs = _init_new_car_files(car_name, display)
        ok   = sum(1 for m in msgs if "skipped" not in m.lower())

        self.report({"INFO"},
                    f"Prepared {car_name}: body + {tagged_wheels} wheel(s) tagged, "
                    f"materials flattened, {ok}/{len(msgs)} support files initialised.")
        return {"FINISHED"}


class CAR_OT_SpawnWheelsAuto(bpy.types.Operator):
    bl_idname      = "car.spawn_wheels_auto"
    bl_label       = "Spawn Wheels at Corners"
    bl_description = (
        "Spawn N template wheels (from VPMUSTANG99) placed at the body bounding-box "
        "corners so they start at plausible positions. Move them to fine-tune."
    )
    bl_options     = {"REGISTER", "UNDO"}

    wheel_count: bpy.props.IntProperty(
        name="Wheel Count", default=4, min=2, max=10,
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car body — tag a body first.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj.get("mm_car_name", "CAR"))
        style    = getattr(context.scene, "ce_wheel_style", "") or "VPMUSTANG99"
        radius   = float(getattr(context.scene, "ce_wheel_size", 0.35))

        # Find existing wheel indices to avoid collision
        used_idxs = {
            int(o.get(_CAR_TAG).split("_")[1])
            for o in get_car_objects()
            if o.get(_CAR_TAG, "").startswith("wheel_")
            and o.get(_CAR_TAG).split("_")[1].isdigit()
        }
        free_idxs = [i for i in range(20) if i not in used_idxs]

        positions = _body_wheel_positions(body_obj, self.wheel_count)
        col       = _get_or_create_collection(_CAR_COLLECTION)
        spawned   = 0

        for pos, new_idx in zip(positions, free_idxs):
            mesh = _load_styled_wheel(car_name, new_idx, style,
                                      Folder.Resources.Editor.Textures, radius)
            if mesh is None:
                continue
            mesh["bms_source_file"] = ""

            new_obj = bpy.data.objects.new(f"{car_name}.WHL{new_idx}", mesh)
            col.objects.link(new_obj)
            new_obj[_CAR_TAG]              = f"wheel_{new_idx}"
            new_obj.parent                 = body_obj
            new_obj.matrix_parent_inverse  = mathutils.Matrix.Identity(4)
            # pos is already in body-local Blender space
            new_obj.location = pos
            spawned += 1

        _sync_wheel_radius_props(context.scene)
        self.report({"INFO"}, f"Spawned {spawned} wheel(s) at bounding-box corners.")
        return {"FINISHED"}


# ── Operator: Debug BMS ──────────────────────────────────────────────────────

class CAR_OT_DebugBMS(bpy.types.Operator):
    bl_idname      = "car.debug_bms"
    bl_label       = "Debug BMS"
    bl_description = (
        "Print debug info for all exported BMS files in SHOP/BMS/{car_name}/. "
        "Shows mesh_offset, point count, textures, bounding box, and radius per file."
    )

    def execute(self, context):
        body_obj = get_car_body()
        if body_obj is None:
            self.report({"ERROR"}, "No car loaded.")
            return {"CANCELLED"}

        car_name = _base_car_name(body_obj.get("mm_car_name", ""))
        shop_dir = Folder.Shop.Meshes / car_name

        if not shop_dir.is_dir():
            self.report({"WARNING"}, f"SHOP/BMS/{car_name}/ does not exist — export first.")
            return {"CANCELLED"}

        bms_files = sorted(shop_dir.glob("*.BMS"))
        if not bms_files:
            self.report({"WARNING"}, f"No BMS files in SHOP/BMS/{car_name}/.")
            return {"CANCELLED"}

        print(f"\n{'='*60}")
        print(f"[Debug BMS] Car: {car_name}  ({len(bms_files)} files)")
        print(f"{'='*60}")

        for bms_file in bms_files:
            try:
                data = read_bms(bms_file)
                pts   = data.get("points", [])
                off   = data.get("mesh_offset", (0, 0, 0))
                texs  = data.get("texture_names", [])
                flags = data.get("flags", 0)

                xs = [p[0] for p in pts] or [0]
                ys = [p[1] for p in pts] or [0]
                zs = [p[2] for p in pts] or [0]
                bbox = (
                    f"X[{min(xs):.3f}..{max(xs):.3f}] "
                    f"Y[{min(ys):.3f}..{max(ys):.3f}] "
                    f"Z[{min(zs):.3f}..{max(zs):.3f}]"
                )

                print(f"\n  {bms_file.name}")
                print(f"    mesh_offset : {off[0]:.4f}, {off[1]:.4f}, {off[2]:.4f}")
                print(f"    points      : {len(pts)}")
                print(f"    surfaces    : {data.get('num_surfaces', '?')}")
                print(f"    flags       : 0x{flags:02X}")
                print(f"    textures    : {texs}")
                print(f"    bbox        : {bbox}")
            except Exception as exc:
                print(f"\n  {bms_file.name}  ERROR: {exc}")

        print(f"\n{'='*60}\n")
        self.report({"INFO"}, f"BMS debug printed to system console ({len(bms_files)} files).")
        return {"FINISHED"}


# ── Operator: Select Car Part by tag ─────────────────────────────────────────

class CAR_OT_SelectPart(bpy.types.Operator):
    bl_idname      = "car.select_part"
    bl_label       = "Select Part"
    bl_description = "Select this car part in the viewport"

    part_tag: bpy.props.StringProperty()

    def execute(self, context):
        for obj in get_car_objects():
            if obj.get(_CAR_TAG) == self.part_tag:
                for o in context.view_layer.objects:
                    o.select_set(False)
                obj.select_set(True)
                context.view_layer.objects.active = obj
                return {"FINISHED"}
        return {"CANCELLED"}


class CAR_OT_ResetPhysics(bpy.types.Operator):
    bl_idname      = "car.reset_physics"
    bl_label       = "Reset Physics"
    bl_description = "Reset the handling values to the loaded car's stock MMCARSIM (or VPMUSTANG99 if none)"

    def execute(self, context):
        body = get_car_body()
        car_name = _base_car_name(body["mm_car_name"]) if body else "VPMUSTANG99"
        _sync_physics_props_from_car(context.scene, car_name)
        context.scene.ce_phys_override = True  # keep editing enabled after reset
        self.report({"INFO"}, f"Physics reset to {car_name} baseline")
        return {"FINISHED"}


# ── Registration list ─────────────────────────────────────────────────────────

CAR_EDITOR_CLASSES = [
    CAR_OT_SelectFace,
    CAR_OT_ResetPhysics,
    CAR_OT_LoadCar,
    CAR_OT_LoadTrailer,
    CAR_OT_LoadSirenLights,
    CAR_OT_LoadCarLights,
    CAR_OT_SetLightColor,
    CAR_OT_SetBeamLength,
    CAR_OT_ToggleLightGlows,
    CAR_OT_ExportCar,
    CAR_OT_ReloadCar,
    CAR_OT_ClearCar,
    CAR_OT_AssignTexture,
    CAR_OT_BrowseExportFolder,
    CAR_OT_ApplyFaceUV,
    CAR_OT_AddFace,
    CAR_OT_AddTextureSlot,
    CAR_OT_ToggleDamage,
    CAR_OT_SetPaintVariant,
    CAR_OT_ClearShop,
    CAR_OT_RemoveWheel,
    CAR_OT_RenumberWheels,
    CAR_OT_OpenExportFolder,
    CAR_OT_MakeCustomCopy,
    CAR_OT_NewFromTemplate,
    CAR_OT_InitNewCar,
    CAR_OT_ValidateCar,
    CAR_OT_PackAndStartGame,
    CAR_OT_MirrorWheel,
    CAR_OT_MirrorAllWheels,
    CAR_OT_ToggleSymmetry,
    CAR_OT_ApplyWheelTexture,
    CAR_OT_ApplyWheelTextureSingle,
    CAR_OT_SetWheelRadius,
    CAR_OT_SetAllWheelRadius,
    CAR_OT_DebugBMS,
    CAR_OT_SelectPart,
    CAR_OT_ImportTagBody,
    CAR_OT_ImportTagWheel,
    CAR_OT_ImportAutoTag,
    CAR_OT_ImportDecimate,
    CAR_OT_ImportCleanMaterials,
    CAR_OT_ImportApplyTransforms,
    CAR_OT_SpawnWheelFromTemplate,
    CAR_OT_ImportFlattenMaterials,
    CAR_OT_ImportPrepare,
    CAR_OT_SpawnWheelsAuto,
]

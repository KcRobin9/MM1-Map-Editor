import bpy
import math
import shutil
import mathutils
import subprocess

from src.constants.folder import Folder
from src.integrations.blender.modeling.skeleton_mod import (
    _g2b, _game_euler_xzy_to_blender_quat,
    apply_anim_action, apply_var_variant_to_mesh, read_var_variant_from_mesh,
    build_armature, build_mesh, build_parent_map, clear_skeleton_objects,
    dfs_bone_order, export_anim_from_action, export_mod_colors_from_mesh, export_skel_from_armature,
    get_all_material_names, pack_var, parse_anim, parse_csv_anim_list, parse_mod, parse_skel, parse_var,
)

_SKE_TAG = "ske_char_name"

CHAR_ITEMS = [
    ("BUSMAN_INIT",  "Business Man",   ""),
    ("BUSWOM_INIT",  "Business Woman", ""),
    ("CASMAN_INIT",  "Casual Man",     ""),
    ("CASWOM_INIT",  "Casual Woman",   ""),
    ("COP_INIT",     "Cop",            ""),
    ("WINTRMAN_INIT","Winter Man",     ""),
    ("WINTRWOM_INIT","Winter Woman",   ""),
]

_REX = Folder.Resources.Editor.Rex
_PED_ANIM = Folder.Resources.Editor.PedAnim

# In-memory VAR data cache: {char_name: var_data_dict}
# Loaded on demand; mutations here are written out by Export VAR.
_var_cache: dict = {}


def _get_armature(char_name: str):
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and obj.get(_SKE_TAG) == char_name:
            return obj
    return None


def _get_mesh(char_name: str):
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.get(_SKE_TAG) == char_name:
            return obj
    return None


def _load_var(char_name: str):
    """Return cached var_data for char, loading from resources if not yet loaded."""
    if char_name not in _var_cache:
        var_path = _REX / f"{char_name}.VAR"
        if not var_path.exists():
            return None
        _var_cache[char_name] = parse_var(var_path)
    return _var_cache[char_name]


def _shop_rex():
    """Return (and create) the SHOP/REX export directory."""
    d = Folder.Shop.Root / "REX"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_mod(char: str):
    """Parse the MOD for char from the stock resource folder."""
    return parse_mod(_REX / f"{char}.MOD")


def _load_skel(char: str):
    """Parse the SKEL for char. Raises FileNotFoundError if absent."""
    p = _REX / f"{char}.SKEL"
    if not p.exists():
        raise FileNotFoundError(f"SKEL not found: {p}")
    return parse_skel(p)


def _fc_ensure(action, dp, idx):
    fc = action.fcurves.find(dp, index=idx)
    return fc if fc else action.fcurves.new(dp, index=idx)


def _key_linear(fc, frame, val):
    kp = fc.keyframe_points.insert(frame, val, options={'FAST', 'REPLACE'})
    kp.interpolation = 'LINEAR'


def _anim_items(self, context):
    char     = context.scene.ske_char_name
    csv_path = _PED_ANIM / f"{char}.CSV"

    if not csv_path.exists():
        return [("NONE", "No CSV found", "")]

    pairs = parse_csv_anim_list(csv_path)
    if not pairs:
        return [("NONE", "No animations", "")]

    return [(anim.upper(), label, anim.upper()) for anim, label in pairs]


class SKE_OT_LoadSkeleton(bpy.types.Operator):
    bl_idname  = "ske.load_skeleton"
    bl_label   = "Load Skeleton"
    bl_description = "Import the armature for the selected character"

    def execute(self, context):
        char = context.scene.ske_char_name
        try:
            skel = _load_skel(char)
        except FileNotFoundError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        clear_skeleton_objects(char)
        bone_list = dfs_bone_order(skel)
        build_armature(bone_list, build_parent_map(skel), char)

        self.report({"INFO"}, f"Loaded {len(bone_list)} bones for {char}")
        return {"FINISHED"}


class SKE_OT_LoadMesh(bpy.types.Operator):
    bl_idname  = "ske.load_mesh"
    bl_label   = "Load Mesh"
    bl_description = "Import the skinned character mesh (requires skeleton loaded first)"

    def execute(self, context):
        char    = context.scene.ske_char_name
        arm_obj = _get_armature(char)

        if not arm_obj:
            self.report({"ERROR"}, "Load skeleton first")
            return {"CANCELLED"}

        mod_path = _REX / f"{char}.MOD"

        if not mod_path.exists():
            self.report({"ERROR"}, f"MOD not found: {mod_path}")
            return {"CANCELLED"}

        for obj in list(bpy.data.objects):
            if obj.type == 'MESH' and obj.get(_SKE_TAG) == char:
                bpy.data.objects.remove(obj, do_unlink=True)

        bone_list = dfs_bone_order(_load_skel(char))
        build_mesh(parse_mod(mod_path), arm_obj, bone_list, char,
                   tex_folder=Folder.Resources.Editor.Textures)

        self.report({"INFO"}, f"Loaded mesh for {char}")
        return {"FINISHED"}


class SKE_OT_LoadAnimation(bpy.types.Operator):
    bl_idname  = "ske.load_animation"
    bl_label   = "Load Animation"
    bl_description = "Apply animation action to the armature"

    def execute(self, context):
        scene = context.scene
        char = scene.ske_char_name
        anim_name = scene.ske_anim_name

        arm_obj = _get_armature(char)

        if not arm_obj:
            self.report({"ERROR"}, "Load skeleton first")
            return {"CANCELLED"}

        if anim_name == "NONE" or not anim_name:
            self.report({"ERROR"}, "Select an animation")
            return {"CANCELLED"}

        anim_path = _REX / f"{anim_name}.ANIM"
        if not anim_path.exists():
            self.report({"ERROR"}, f"ANIM not found: {anim_path}")
            return {"CANCELLED"}

        bone_list = dfs_bone_order(_load_skel(char))
        anim_data = parse_anim(anim_path)

        apply_anim_action(arm_obj, anim_data, bone_list, anim_name)

        scene.frame_start = 1
        scene.frame_end = anim_data["frame_count"]
        scene.frame_current = 1
        scene.render.fps = 15
        scene.render.fps_base = 1.0

        # Auto-start playback so the animation is immediately visible
        if not bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        self.report({"INFO"}, f"Loaded {anim_name}: {anim_data['frame_count']} frames — playing at 15 fps")
        return {"FINISHED"}


class SKE_OT_ExportAnimation(bpy.types.Operator):
    bl_idname  = "ske.export_animation"
    bl_label   = "Export ANIM"
    bl_description = "Write the active armature action as a binary .ANIM file into SHOP/REX/"

    def execute(self, context):
        scene = context.scene
        char = scene.ske_char_name
        arm_obj = _get_armature(char)

        if not arm_obj:
            self.report({"ERROR"}, "No skeleton loaded")
            return {"CANCELLED"}

        # Auto-create a 1-frame T-pose action if none is loaded
        if not arm_obj.animation_data or not arm_obj.animation_data.action:
            if arm_obj.animation_data is None:
                arm_obj.animation_data_create()

            action = bpy.data.actions.new("TPOSE")
            arm_obj.animation_data.action = action
            action.use_fake_user = True

            for pb in arm_obj.pose.bones:
                pb.rotation_mode = 'QUATERNION'
            self.report({"INFO"}, "No action found — created 1-frame T-pose action")

        bone_list   = dfs_bone_order(_load_skel(char))
        anim_bytes  = export_anim_from_action(arm_obj, bone_list)
        action_name = arm_obj.animation_data.action.name.upper()
        out_path    = _shop_rex() / f"{action_name}.ANIM"
        out_path.write_bytes(anim_bytes)

        self.report({"INFO"}, f"Exported {action_name}.ANIM ({len(anim_bytes)} bytes)")
        return {"FINISHED"}


class SKE_OT_ExportSkel(bpy.types.Operator):
    bl_idname  = "ske.export_skel"
    bl_label   = "Export SKEL"
    bl_description = "Write bone positions from the armature back to SHOP/REX/<CHAR>.SKEL"

    def execute(self, context):
        scene = context.scene
        char = scene.ske_char_name
        arm_obj = _get_armature(char)

        if not arm_obj:
            self.report({"ERROR"}, "No skeleton loaded")
            return {"CANCELLED"}

        skel_path = _REX / f"{char}.SKEL"

        if not skel_path.exists():
            self.report({"ERROR"}, f"Source SKEL not found: {skel_path}")
            return {"CANCELLED"}

        skel_text = export_skel_from_armature(arm_obj, _load_skel(char))
        out_path  = _shop_rex() / f"{char}.SKEL"
        out_path.write_text(skel_text, encoding="ascii")

        self.report({"INFO"}, f"Exported {char}.SKEL")
        return {"FINISHED"}


class SKE_OT_ExportMod(bpy.types.Operator):
    bl_idname  = "ske.export_mod"
    bl_label   = "Export MOD"
    bl_description = "Write material colors from the mesh back to SHOP/REX/<CHAR>.MOD"

    def execute(self, context):
        char     = context.scene.ske_char_name
        mod_path = _REX / f"{char}.MOD"

        if not mod_path.exists():
            self.report({"ERROR"}, f"Source MOD not found: {mod_path}")
            return {"CANCELLED"}

        mesh_obj     = _get_mesh(char)

        patched_text = export_mod_colors_from_mesh(mesh_obj, mod_path.read_text(encoding="ascii", errors="replace"))
        out_path = _shop_rex() / f"{char}.MOD"
        out_path.write_text(patched_text, encoding="ascii")

        self.report({"INFO"}, f"Exported {char}.MOD (colors from Blender materials)")
        return {"FINISHED"}


class SKE_OT_LoadVariant(bpy.types.Operator):
    bl_idname  = "ske.load_variant"
    bl_label   = "Load Variant"
    bl_description = "Apply the selected clothing color variant to the mesh materials"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        variant = scene.ske_var_variant

        if not _get_mesh(char):
            self.report({"ERROR"}, "Load mesh first")
            return {"CANCELLED"}

        var_data = _load_var(char)

        if not var_data:
            self.report({"ERROR"}, f"No VAR file found for {char}")
            return {"CANCELLED"}

        apply_var_variant_to_mesh(_load_mod(char), var_data, variant)
        self.report({"INFO"}, f"Loaded variant {variant} for {char}")
        return {"FINISHED"}


class SKE_OT_SaveVariant(bpy.types.Operator):
    bl_idname  = "ske.save_variant"
    bl_label   = "Save to Variant"
    bl_description = "Store current mesh material colors into the selected variant slot (in memory — use Export VAR to write to disk)"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        variant = scene.ske_var_variant

        if not _get_mesh(char):
            self.report({"ERROR"}, "Load mesh first")
            return {"CANCELLED"}

        var_data = _load_var(char)
        if not var_data:
            self.report({"ERROR"}, f"No VAR file found for {char}")
            return {"CANCELLED"}

        read_var_variant_from_mesh(_load_mod(char), var_data, variant)
        self.report({"INFO"}, f"Saved current colors → variant {variant} (click Export VAR to write)")
        return {"FINISHED"}


class SKE_OT_ExportVar(bpy.types.Operator):
    bl_idname  = "ske.export_var"
    bl_label   = "Export VAR"
    bl_description = "Write the in-memory VAR data (all 6 variants) to SHOP/REX/<CHAR>.VAR"

    def execute(self, context):
        scene = context.scene
        char  = scene.ske_char_name

        var_data = _var_cache.get(char)

        if not var_data:
            self.report({"ERROR"}, "No VAR loaded — change the variant index first")
            return {"CANCELLED"}

        out_path = _shop_rex() / f"{char}.VAR"
        out_path.write_bytes(pack_var(var_data))

        self.report({"INFO"}, f"Exported {char}.VAR ({var_data['count']} variants × {var_data['n_colors']} colors)")
        return {"FINISHED"}


class SKE_OT_OverrideAllVariants(bpy.types.Operator):
    bl_idname  = "ske.override_all_variants"
    bl_label   = "Copy to All Variants"
    bl_description = "Save current mesh colors to every variant slot — quick way to test one outfit in-game"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        variant = scene.ske_var_variant

        if not _get_mesh(char):
            self.report({"ERROR"}, "Load mesh first")
            return {"CANCELLED"}

        var_data = _load_var(char)

        if not var_data:
            self.report({"ERROR"}, f"No VAR file found for {char}")
            return {"CANCELLED"}

        # Read current colors into the selected slot first, then broadcast
        read_var_variant_from_mesh(_load_mod(char), var_data, variant)
        source = list(var_data["variants"][variant])
        for i in range(var_data["count"]):
            var_data["variants"][i] = list(source)

        self.report({"INFO"}, f"Copied variant {variant} → all {var_data['count']} slots (click Export VAR to write)")
        return {"FINISHED"}


class SKE_OT_ClearSkeleton(bpy.types.Operator):
    bl_idname  = "ske.clear_skeleton"
    bl_label   = "Clear"
    bl_description = "Remove all skeleton objects for this character"

    def execute(self, context):
        char = context.scene.ske_char_name
        clear_skeleton_objects(char)
        self.report({"INFO"}, f"Cleared {char}")
        return {"FINISHED"}


class SKE_OT_PackAR(bpy.types.Operator):
    bl_idname  = "ske.pack_ar"
    bl_label   = "Pack AR"
    bl_description = (
        "Pack a complete ped AR: all stock files from resources/editor/REX as base, "
        "with any SHOP/REX edits overriding them. Written to MidtownMadness/ with !!!!! prefix."
    )

    def execute(self, context):
        mkar_exe = Folder.Angel / "mkar.exe"
        if not mkar_exe.exists():
            self.report({"ERROR"}, f"mkar.exe not found: {mkar_exe}")
            return {"CANCELLED"}

        # Build file map: name.upper() → path. Start with all stock files,
        # then let SHOP/REX edits overwrite — so edited files take priority.
        file_map: dict = {}

        exts = {".ANIM", ".SKEL", ".MOD", ".VAR"}

        # 1. Base: every supported file from resources/editor/REX
        for f in sorted(Folder.Resources.Editor.Rex.glob("*")):
            if f.suffix.upper() in exts:
                file_map[f.name.upper()] = f

        # 2. Overrides: anything exported to SHOP/REX
        shop_rex = Folder.Shop.Root / "REX"
        if shop_rex.exists():
            for f in sorted(shop_rex.glob("*")):
                if f.suffix.upper() in exts:
                    file_map[f.name.upper()] = f

        if not file_map:
            self.report({"ERROR"}, "No files to pack — check resources/editor/REX exists")
            return {"CANCELLED"}

        ar_name = context.scene.ske_ar_name.strip() or "!!!!!ped_anims"
        out_ar  = Folder.MidtownMadness.Root / f"{ar_name}.AR"
        tmp_dir = Folder.BASE / "_ped_pack_tmp"
        try:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            rex_dst = tmp_dir / "REX"
            rex_dst.mkdir(parents=True)

            staged = []
            for key in sorted(file_map):
                src = file_map[key]
                shutil.copy2(src, rex_dst / src.name)
                staged.append(src.name)

            shiplist = tmp_dir / "shiplist.peds"
            shiplist.write_bytes(("\n".join(f"./REX/{n}" for n in staged) + "\n").encode("ascii"))

            result = subprocess.run(
                [str(mkar_exe), str(out_ar), str(shiplist), "2"],
                cwd=str(tmp_dir),
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                self.report({"ERROR"}, f"mkar failed: {result.stderr.strip() or result.stdout.strip()}")
                return {"CANCELLED"}

            n_total   = len(staged)
            n_shop    = len([f for f in file_map.values()
                             if str(f).startswith(str(Folder.Shop.Root))])
            self.report({"INFO"}, f"Packed {n_total} files ({n_shop} from SHOP edits) → {out_ar.name}")
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)
        return {"FINISHED"}


class SKE_OT_DebugAnim(bpy.types.Operator):
    bl_idname  = "ske.debug_anim"
    bl_label   = "Debug F-Curves"
    bl_description = "Print animation f-curve stats to the System Console (Window > Toggle System Console)"

    def execute(self, context):
        char = context.scene.ske_char_name
        arm_obj = _get_armature(char)
        if not arm_obj or not arm_obj.animation_data or not arm_obj.animation_data.action:
            self.report({"ERROR"}, "No animation loaded on armature")
            return {"CANCELLED"}

        action = arm_obj.animation_data.action
        fcs = action.fcurves

        print(f"\n=== SKE Debug: {action.name} | {len(fcs)} f-curves | range {action.frame_range[:]} ===")

        identical_count = 0
        for fc in fcs:
            kps = fc.keyframe_points
            if not kps:
                print(f"  EMPTY  {fc.data_path}[{fc.array_index}]")
                continue
            vals = [kp.co[1] for kp in kps]
            mn, mx = min(vals), max(vals)
            identical = abs(mx - mn) < 1e-6
            if identical:
                identical_count += 1
            flag = " <<STATIC" if identical else ""
            print(f"  {len(kps):3d} keys  [{mn:+.4f} .. {mx:+.4f}]  {fc.data_path}[{fc.array_index}]{flag}")

        print(f"\nRotation modes:")

        mode_counts = {}

        for pb in arm_obj.pose.bones:
            mode_counts[pb.rotation_mode] = mode_counts.get(pb.rotation_mode, 0) + 1

        for mode, n in mode_counts.items():
            print(f"  {mode}: {n} bones")

        summary = (f"{len(fcs)} curves — {identical_count} static, "
                   f"{len(fcs) - identical_count} animated. "
                   f"Frame range {int(action.frame_range[0])}–{int(action.frame_range[1])}. "
                   f"See System Console for details.")
        self.report({"INFO"}, summary)

        return {"FINISHED"}


class SKE_OT_NewAnimation(bpy.types.Operator):
    bl_idname  = "ske.new_animation"
    bl_label   = "New Animation"
    bl_description = "Create a blank action with all bones at rest (T-pose) for N frames"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        arm_obj = _get_armature(char)

        if not arm_obj:
            self.report({"ERROR"}, "Load skeleton first")
            return {"CANCELLED"}

        bone_list = dfs_bone_order(_load_skel(char))
        nframes   = scene.ske_new_anim_frames
        name      = scene.ske_new_anim_name.strip().upper() or "NEW_ANIM"

        action = bpy.data.actions.new(name)

        if arm_obj.animation_data is None:
            arm_obj.animation_data_create()
        arm_obj.animation_data.action = action

        action.use_fake_user = True

        for pb in arm_obj.pose.bones:
            pb.rotation_mode = 'QUATERNION'

        root_name = bone_list[0]["unique_name"]
        loc_fcs = [_fc_ensure(action, f'pose.bones["{root_name}"].location', i) for i in range(3)]

        for f in [1, nframes]:
            for fc in loc_fcs:
                _key_linear(fc, f, 0.0)
        for fc in loc_fcs:
            fc.update()

        for bone in bone_list:
            bn  = bone["unique_name"]
            rp  = f'pose.bones["{bn}"].rotation_quaternion'
            rfs = [_fc_ensure(action, rp, i) for i in range(4)]

            for f in [1, nframes]:
                _key_linear(rfs[0], f, 1.0)
                for i in range(1, 4):
                    _key_linear(rfs[i], f, 0.0)
            for fc in rfs:
                fc.update()

        scene.frame_start   = 1
        scene.frame_end     = nframes
        scene.frame_current = 1
        scene.render.fps      = 15
        scene.render.fps_base = 1.0

        self.report({"INFO"}, f"Created '{name}' ({nframes} frames) — Tab into Pose Mode and rotate bones, then Key All")
        return {"FINISHED"}


class SKE_OT_BakePoseKey(bpy.types.Operator):
    bl_idname  = "ske.bake_pose_key"
    bl_label   = "Key All Bones"
    bl_description = "Insert a keyframe for every pose bone at the current frame"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        arm_obj = _get_armature(char)
        if not arm_obj or not arm_obj.animation_data or not arm_obj.animation_data.action:
            self.report({"ERROR"}, "No skeleton / action loaded")
            return {"CANCELLED"}

        frame  = scene.frame_current
        action = arm_obj.animation_data.action
        bpy.context.view_layer.update()

        for pb in arm_obj.pose.bones:
            pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        arm_obj.pose.bones[0].keyframe_insert(data_path="location", frame=frame)

        for fc in action.fcurves:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 0.5:
                    kp.interpolation = 'LINEAR'
            fc.update()

        self.report({"INFO"}, f"Keyed {len(arm_obj.pose.bones)} bones at frame {frame}")
        return {"FINISHED"}


class SKE_OT_FixLoop(bpy.types.Operator):
    bl_idname  = "ske.fix_loop"
    bl_label   = "Fix Loop"
    bl_description = "Copy the first frame's pose to the last frame for a seamless loop"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        arm_obj = _get_armature(char)
        if not arm_obj or not arm_obj.animation_data or not arm_obj.animation_data.action:
            self.report({"ERROR"}, "No animation loaded")
            return {"CANCELLED"}

        action  = arm_obj.animation_data.action
        f_start = int(action.frame_range[0])
        f_end   = int(action.frame_range[1])

        for fc in action.fcurves:
            val = fc.evaluate(f_start)
            kp  = fc.keyframe_points.insert(f_end, val, options={'FAST', 'REPLACE'})
            kp.interpolation = 'LINEAR'
            fc.update()

        self.report({"INFO"}, f"Copied frame {f_start} → {f_end} — animation now loops cleanly")
        return {"FINISHED"}


class SKE_OT_ExportAllActions(bpy.types.Operator):
    bl_idname  = "ske.export_all_actions"
    bl_label   = "Export All Actions"
    bl_description = "Batch-export every Blender action to SHOP/REX/<NAME>.ANIM"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        arm_obj = _get_armature(char)
        if not arm_obj:
            self.report({"ERROR"}, "No skeleton loaded")
            return {"CANCELLED"}

        bone_list = dfs_bone_order(_load_skel(char))
        shop_rex  = _shop_rex()

        if arm_obj.animation_data is None:
            arm_obj.animation_data_create()

        orig_action = arm_obj.animation_data.action
        exported    = 0

        for action in list(bpy.data.actions):
            arm_obj.animation_data.action = action

            try:
                anim_bytes = export_anim_from_action(arm_obj, bone_list)
            except Exception as e:
                self.report({"WARNING"}, f"Skipped {action.name}: {e}")
                continue
            out_path = shop_rex / f"{action.name.upper()}.ANIM"
            out_path.write_bytes(anim_bytes)
            exported += 1

        arm_obj.animation_data.action = orig_action
        self.report({"INFO"}, f"Exported {exported} action(s) to {shop_rex}")
        return {"FINISHED"}


class SKE_OT_GenerateAnim(bpy.types.Operator):
    bl_idname  = "ske.generate_anim"
    bl_label   = "Generate"
    bl_description = "Procedurally generate an animation (Walk/Run/Wave/Idle/Dive/Stumble/Cheer/Scared)"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        arm_obj = _get_armature(char)

        if not arm_obj:
            self.report({"ERROR"}, "Load skeleton first")
            return {"CANCELLED"}

        bone_list = dfs_bone_order(_load_skel(char))
        style     = scene.ske_gen_style
        speed     = scene.ske_walk_speed

        STYLE_FRAMES = {
            "WALK":    30,
            "RUN":     20,
            "WAVE":    30,
            "IDLE":    60,
            "DIVE":    30,
            "STUMBLE": 20,
            "CHEER":   40,
            "SCARED":  24,
        }
        nframes = STYLE_FRAMES[style]
        name    = f"GEN_{style}"

        if name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[name])
        action = bpy.data.actions.new(name)

        if arm_obj.animation_data is None:
            arm_obj.animation_data_create()

        arm_obj.animation_data.action = action
        action.use_fake_user = True

        for pb in arm_obj.pose.bones:
            pb.rotation_mode = 'QUATERNION'

        def _bi(n):
            for i, b in enumerate(bone_list):
                if b["unique_name"] == n or b["name"] == n:
                    return i
            return -1

        BI_SPINE1     = _bi("spine1")
        BI_SPINE2     = _bi("spine2")
        BI_NECK       = _bi("neck")
        BI_HEAD       = _bi("head")
        BI_SHOULDER_R = _bi("shoulder_r")
        BI_ARM_R      = _bi("arm_r")
        BI_LOWARM_R   = _bi("lowarm_r")
        BI_WRIST_R    = _bi("wrist_r")
        BI_SHOULDER_L = _bi("shoulder_l")
        BI_ARM_L      = _bi("arm_l")
        BI_LOWARM_L   = _bi("lowarm_l")
        BI_WRIST_L    = _bi("wrist_l")
        BI_HIP_R      = _bi("hip_r")
        BI_SHIN_R     = _bi("shin_r")
        BI_FOOT_R     = _bi("foot_r")
        BI_HIP_L      = _bi("hip_l")
        BI_SHIN_L     = _bi("shin_l")
        BI_FOOT_L     = _bi("foot_l")

        nb = len(bone_list)

        def _rot(frame, bi_idx, ex, ey, ez):
            if bi_idx < 0:
                return
            
            bn  = bone_list[bi_idx]["unique_name"]
            q   = _game_euler_xzy_to_blender_quat(ex, ey, ez)
            rp  = f'pose.bones["{bn}"].rotation_quaternion'
            rfs = [_fc_ensure(action, rp, i) for i in range(4)]
            _key_linear(rfs[0], frame, q.w)
            _key_linear(rfs[1], frame, q.x)
            _key_linear(rfs[2], frame, q.y)
            _key_linear(rfs[3], frame, q.z)

        def _loc(frame, by, bz=0.0):
            root_name = bone_list[0]["unique_name"]
            lp = f'pose.bones["{root_name}"].location'
            _key_linear(_fc_ensure(action, lp, 0), frame, 0.0)
            _key_linear(_fc_ensure(action, lp, 1), frame, by)
            _key_linear(_fc_ensure(action, lp, 2), frame, bz)

        P = math.pi

        for f in range(nframes):
            frame = f + 1
            prog  = f / nframes
            t     = prog
            si = lambda ph=0, a=1: a * math.sin(2 * P * t + ph)
            co = lambda ph=0, a=1: a * math.cos(2 * P * t + ph)

            # default all bones to T-pose, root to no offset
            for bi_idx in range(nb):
                _rot(frame, bi_idx, 0, 0, 0)
            _loc(frame, 0.0)

            # ── WALK ─────────────────────────────────────────────────────────
            if style == "WALK":
                # character faces -Z game = -Y Blender; forward = decreasing Blender Y
                walk_dist = 1.97 * speed
                _loc(frame, -t * walk_dist, 0.015 * abs(co()))

                arm_ey    = co(0, -0.35)
                hip_ex_r  = co(0,  0.50)
                hip_ex_l  = co(0, -0.50)
                shin_ex_r = 0.25 - si(0, 0.20)
                shin_ex_l = 0.25 + si(0, 0.20)

                _rot(frame, BI_SPINE1,   0.10, 0, 0)
                _rot(frame, BI_ARM_R,    0, arm_ey, 0)
                _rot(frame, BI_LOWARM_R, 0.30, 0, 0)
                _rot(frame, BI_ARM_L,    0, arm_ey, 0)
                _rot(frame, BI_LOWARM_L, 0.30, 0, 0)
                _rot(frame, BI_HIP_R,    hip_ex_r, 0, 0)
                _rot(frame, BI_SHIN_R,   shin_ex_r, 0, 0)
                _rot(frame, BI_HIP_L,    hip_ex_l, 0, 0)
                _rot(frame, BI_SHIN_L,   shin_ex_l, 0, 0)

            # ── RUN ──────────────────────────────────────────────────────────
            elif style == "RUN":
                run_dist = 3.0 * speed
                _loc(frame, -t * run_dist, 0.025 * abs(math.cos(4 * P * t)))

                arm_ey    = co(0, -0.55)
                hip_ex_r  = co(0,  0.70)
                hip_ex_l  = co(0, -0.70)
                shin_ex_r = 0.40 - si(0, 0.30)
                shin_ex_l = 0.40 + si(0, 0.30)
                low_r     = 0.50 - co(0, 0.25)
                low_l     = 0.50 + co(0, 0.25)

                _rot(frame, BI_SPINE1,   0.20, 0, 0)
                _rot(frame, BI_ARM_R,    0, arm_ey, 0)
                _rot(frame, BI_LOWARM_R, low_r, 0, 0)
                _rot(frame, BI_ARM_L,    0, arm_ey, 0)
                _rot(frame, BI_LOWARM_L, low_l, 0, 0)
                _rot(frame, BI_HIP_R,    hip_ex_r, 0, 0)
                _rot(frame, BI_SHIN_R,   shin_ex_r, 0, 0)
                _rot(frame, BI_HIP_L,    hip_ex_l, 0, 0)
                _rot(frame, BI_SHIN_L,   shin_ex_l, 0, 0)

            # ── WAVE ─────────────────────────────────────────────────────────
            elif style == "WAVE":
                _rot(frame, BI_HEAD,       si(0, 0.10), 0, 0)
                _rot(frame, BI_SHOULDER_R, 0, 0,  1.05)
                _rot(frame, BI_ARM_R,      si(0, 0.50), 0, 0)
                _rot(frame, BI_LOWARM_R,   0.40, 0, 0)
                _rot(frame, BI_WRIST_R,    si(P, 0.35), 0, 0)
                _rot(frame, BI_LOWARM_L,   0.20, 0, 0)

            # ── IDLE ─────────────────────────────────────────────────────────
            elif style == "IDLE":
                _rot(frame, BI_SPINE1,   0.05, 0, si(0, 0.02))
                _rot(frame, BI_SPINE2,   0, 0, si(P / 2, 0.015))
                _rot(frame, BI_NECK,     si(0, 0.02), 0, 0)
                _rot(frame, BI_HEAD,     si(P / 4, 0.03), 0, 0)
                _rot(frame, BI_LOWARM_R, 0.25, 0, 0)
                _rot(frame, BI_LOWARM_L, 0.25, 0, 0)

            # ── DIVE ─────────────────────────────────────────────────────────
            elif style == "DIVE":
                ease = prog * prog * (3 - 2 * prog)                       # smoothstep
                arc  = 0.25 * math.sin(prog * P) - ease * 0.75            # up briefly then down to prone
                _loc(frame, -ease * 1.5 * speed, arc)

                _rot(frame, BI_SPINE1,    ease * 0.80, 0, 0)
                _rot(frame, BI_SPINE2,    ease * 0.50, 0, 0)
                _rot(frame, BI_NECK,      ease * 0.25, 0, 0)
                _rot(frame, BI_ARM_R,     0, ease * 0.80, 0)              # both arms reach forward
                _rot(frame, BI_ARM_L,     0, ease * (-0.80), 0)
                _rot(frame, BI_LOWARM_R,  ease * 0.30, 0, 0)
                _rot(frame, BI_LOWARM_L,  ease * 0.30, 0, 0)
                _rot(frame, BI_HIP_R,     ease * (-0.50), 0, 0)           # legs kick back
                _rot(frame, BI_HIP_L,     ease * (-0.50), 0, 0)

            # ── STUMBLE ──────────────────────────────────────────────────────
            elif style == "STUMBLE":
                bell = math.sin(prog * P)                                  # 0 → peak → 0
                sway = math.sin(2 * P * prog) * 0.15
                _loc(frame, -bell * 0.35 * speed)

                _rot(frame, BI_SPINE1,   bell * 0.55, 0, sway)
                _rot(frame, BI_SPINE2,   bell * 0.30, 0, sway * 0.5)
                _rot(frame, BI_NECK,     bell * (-0.20), 0, 0)            # head whips back
                _rot(frame, BI_ARM_R,    bell * (-0.40), 0, bell * 0.60)  # arms flail out
                _rot(frame, BI_ARM_L,    bell * (-0.40), 0, bell * (-0.60))
                _rot(frame, BI_LOWARM_R, bell * 0.50, 0, 0)
                _rot(frame, BI_LOWARM_L, bell * 0.50, 0, 0)
                _rot(frame, BI_HIP_R,    bell * 0.30, 0, 0)
                _rot(frame, BI_SHIN_R,   bell * 0.25, 0, 0)
                _rot(frame, BI_HIP_L,    bell * (-0.25), 0, 0)
                _rot(frame, BI_SHIN_L,   bell * 0.20, 0, 0)

            # ── CHEER ────────────────────────────────────────────────────────
            elif style == "CHEER":
                bounce = 0.02 * abs(math.sin(4 * P * t))
                _loc(frame, 0.0, bounce)

                _rot(frame, BI_SPINE1,    0.05, 0, si(0, 0.02))
                _rot(frame, BI_HEAD,      si(0, 0.08), 0, 0)
                _rot(frame, BI_SHOULDER_R, 0, 0, P / 2 + si(0, 0.10))    # arms raised ~90° and waving
                _rot(frame, BI_SHOULDER_L, 0, 0, -(P / 2 + si(P, 0.10)))
                _rot(frame, BI_ARM_R,      si(0, 0.20), 0, 0)
                _rot(frame, BI_ARM_L,      si(P, 0.20), 0, 0)
                _rot(frame, BI_LOWARM_R,   0.20 + si(0, 0.15), 0, 0)
                _rot(frame, BI_LOWARM_L,   0.20 + si(P, 0.15), 0, 0)
                _rot(frame, BI_WRIST_R,    si(P / 2, 0.25), 0, 0)
                _rot(frame, BI_WRIST_L,    si(P / 2 + P, 0.25), 0, 0)

            # ── SCARED ───────────────────────────────────────────────────────
            elif style == "SCARED":
                scared_dist = 2.5 * speed
                _loc(frame, -t * scared_dist, 0.02 * abs(co()))

                arm_ey    = co(0, -0.50)
                hip_ex_r  = co(0,  0.65)
                hip_ex_l  = co(0, -0.65)
                shin_ex_r = 0.35 - si(0, 0.25)
                shin_ex_l = 0.35 + si(0, 0.25)

                _rot(frame, BI_SPINE1,     0.10, 0, si(0, 0.05))
                _rot(frame, BI_NECK,       si(0, 0.12), 0, 0)
                _rot(frame, BI_HEAD,       si(P / 4, 0.08), 0, 0)
                _rot(frame, BI_SHOULDER_R, 0, 0, 0.60 + si(0, 0.15))     # arms raised out to sides
                _rot(frame, BI_SHOULDER_L, 0, 0, -(0.60 + si(P, 0.15)))
                _rot(frame, BI_ARM_R,      si(0, 0.30), arm_ey, 0)
                _rot(frame, BI_ARM_L,      si(P, 0.30), arm_ey, 0)
                _rot(frame, BI_LOWARM_R,   0.40 + si(0, 0.20), 0, 0)
                _rot(frame, BI_LOWARM_L,   0.40 + si(P, 0.20), 0, 0)
                _rot(frame, BI_HIP_R,      hip_ex_r, 0, 0)
                _rot(frame, BI_SHIN_R,     shin_ex_r, 0, 0)
                _rot(frame, BI_HIP_L,      hip_ex_l, 0, 0)
                _rot(frame, BI_SHIN_L,     shin_ex_l, 0, 0)

        for fc in action.fcurves:
            fc.update()

        scene.frame_start   = 1
        scene.frame_end     = nframes
        scene.frame_current = 1
        scene.render.fps      = 15
        scene.render.fps_base = 1.0

        if not bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        self.report({"INFO"}, f"Generated GEN_{style} ({nframes} frames)")
        return {"FINISHED"}


class SKE_OT_MirrorPose(bpy.types.Operator):
    bl_idname  = "ske.mirror_pose"
    bl_label   = "Mirror Pose L↔R"
    bl_description = "Swap left/right bone rotations (YZ-plane reflection) and insert keyframe"

    def execute(self, context):
        scene   = context.scene
        char    = scene.ske_char_name
        arm_obj = _get_armature(char)
        if not arm_obj:
            self.report({"ERROR"}, "No skeleton loaded")
            return {"CANCELLED"}

        PAIRS = [
            ("hip_r",      "hip_l"),
            ("leg_r",      "leg_l"),
            ("shin_r",     "shin_l"),
            ("foot_r",     "foot_l"),
            ("arm_r",      "arm_l"),
            ("lowarm_r",   "lowarm_l"),
            ("wrist_r",    "wrist_l"),
            ("shoulder_r", "shoulder_l"),
            ("clavicle_r", "clavicle_l"),
        ]

        def _mirror(q):
            # Reflect rotation across YZ plane: Rx unchanged, Ry and Rz negate
            return mathutils.Quaternion((q.w, q.x, -q.y, -q.z))

        bpy.context.view_layer.update()
        frame  = scene.frame_current
        action = arm_obj.animation_data.action if arm_obj.animation_data else None

        # snapshot originals before writing anything
        orig = {}
        for r_name, l_name in PAIRS:
            for nm in (r_name, l_name):
                pb = arm_obj.pose.bones.get(nm)
                if pb:
                    orig[nm] = pb.rotation_quaternion.copy()

        count = 0
        for r_name, l_name in PAIRS:
            pb_r = arm_obj.pose.bones.get(r_name)
            pb_l = arm_obj.pose.bones.get(l_name)
            if not pb_r or not pb_l:
                continue

            new_r = _mirror(orig[l_name])
            new_l = _mirror(orig[r_name])
            pb_r.rotation_quaternion = new_r
            pb_l.rotation_quaternion = new_l

            if action:
                for pb, q in ((pb_r, new_r), (pb_l, new_l)):
                    rp = f'pose.bones["{pb.name}"].rotation_quaternion'
                    for i, v in enumerate((q.w, q.x, q.y, q.z)):
                        fc = action.fcurves.find(rp, index=i) or action.fcurves.new(rp, index=i)
                        kp = fc.keyframe_points.insert(frame, v, options={'FAST', 'REPLACE'})
                        kp.interpolation = 'LINEAR'
                        fc.update()
            count += 1

        self.report({"INFO"}, f"Mirrored {count} bone pairs at frame {frame}")
        return {"FINISHED"}


SKELETON_EDITOR_CLASSES = [
    SKE_OT_LoadSkeleton,
    SKE_OT_LoadMesh,
    SKE_OT_LoadAnimation,
    SKE_OT_ExportAnimation,
    SKE_OT_ExportSkel,
    SKE_OT_ExportMod,
    SKE_OT_LoadVariant,
    SKE_OT_SaveVariant,
    SKE_OT_ExportVar,
    SKE_OT_OverrideAllVariants,
    SKE_OT_ClearSkeleton,
    SKE_OT_PackAR,
    SKE_OT_DebugAnim,
    SKE_OT_NewAnimation,
    SKE_OT_BakePoseKey,
    SKE_OT_FixLoop,
    SKE_OT_ExportAllActions,
    SKE_OT_GenerateAnim,
    SKE_OT_MirrorPose,
]
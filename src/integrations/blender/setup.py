import bpy
from bpy.types import Area, SpaceView3D

from typing import Optional

from src.USER.settings.blender import target_blend_file

from src.helpers.main import is_process_running
from src.constants.misc import Executable
from src.integrations.blender.handlers import initialize_depsgraph_update_handler
from src.ui.console import ok, item


DEFAULT_OBJECTS = {"Camera", "Cube", "Light"}

def setup_blender(load_target_model: bool) -> None:
    if not is_process_running(Executable.BLENDER):
        return

    delete_default_objects()
    enable_developer_extras()          # may save_userpref — keep BEFORE the undo toggle so the
    suppress_undo_during_build()       # temporary use_global_undo=False is never persisted to disk
    enable_vertex_snapping()
    adjust_3D_view_settings()
    initialize_depsgraph_update_handler()

    if load_target_model:
        load_model()

    ok("Blender setup complete")


def suppress_undo_during_build() -> None:
    """CRASH FIX (GPU_batch use-after-free): the VS Code script runner wraps the WHOLE build in one
    operator, so Blender pushes a full-scene undo snapshot of a 129k-poly city + thousands of props
    when it ends — a classic source of EXCEPTION_ACCESS_VIOLATION in the next workbench draw
    (freed GPU batches referenced by the undo/redo depsgraph swap). Disable global undo for the
    duration of the build and restore it ~2s after the script's operator has ended, so manual
    editing afterwards (the MM2 cell-edit workflow) keeps normal Ctrl+Z."""
    prefs = bpy.context.preferences.edit

    def _restore():
        try:
            bpy.context.preferences.edit.use_global_undo = True
        except Exception:
            pass
        return None                  # one-shot timer

    # Registered FIRST and UNCONDITIONALLY: if an earlier build died before reaching this point it
    # left undo off with no pending timer, and an early return here would strand it off for the
    # whole session (silently — Ctrl+Z just stops working). Re-arming a one-shot restore is free.
    bpy.app.timers.register(_restore, first_interval=2.0)

    if prefs.use_global_undo:
        prefs.use_global_undo = False
        item("Undo suppressed for the build (auto-restores right after)")


def delete_default_objects() -> None:
    # Pure data API (no bpy.ops.object.delete): an operator here pushes an undo step and depends on
    # selection/context state; both are crash vectors while a heavy generated scene exists.
    removed = []
    for name in sorted(DEFAULT_OBJECTS):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                # remove the orphaned mesh/camera/light datablock too
                for pool in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
                    try:
                        pool.remove(data)
                        break
                    except Exception:
                        continue
            removed.append(name)

    item(f"Default objects deleted  ({', '.join(removed) if removed else 'none present'})")


def load_model() -> None:
    if target_blend_file is None:
        return

    with bpy.data.libraries.load(str(target_blend_file)) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        bpy.context.collection.objects.link(obj)

    item(f"Loaded external model: {target_blend_file.name}")


def enable_developer_extras() -> None:
    prefs = bpy.context.preferences
    view = prefs.view

    changed = False
    if not view.show_developer_ui:
        view.show_developer_ui = True
        changed = True
    if view.show_splash:
        view.show_splash = False
        changed = True

    if changed:
        bpy.ops.wm.save_userpref()

    item("Developer extras enabled, splash disabled")


def enable_vertex_snapping() -> None:
    bpy.context.tool_settings.use_snap = True
    bpy.context.tool_settings.snap_elements = {"VERTEX"}
    bpy.context.tool_settings.snap_target = "CLOSEST"

    item("Vertex snapping enabled")


def get_3d_space(area: Area) -> Optional[SpaceView3D]:
    return next((space for space in area.spaces if space.type == "VIEW_3D"), None)


def adjust_3D_view_settings() -> None:
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = get_3d_space(area)
            if space:
                space.clip_end = 5000.0

                shading = space.shading
                shading.type = "SOLID"

                shading.light = "FLAT"
                shading.color_type = "TEXTURE"

                item("3D view settings adjusted")
                return
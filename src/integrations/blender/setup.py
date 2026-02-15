import bpy
from bpy.types import Area, SpaceView3D

from typing import Optional

from src.USER.settings.blender import target_blend_file

from src.helpers.main import is_process_running
from src.constants.misc import Executable
from src.integrations.blender.handlers import initialize_depsgraph_update_handler


DEFAULT_OBJECTS = {"Camera", "Cube", "Light"}

def setup_blender(load_target_model: bool) -> None:
    if not is_process_running(Executable.BLENDER):
        return

    delete_default_objects()
    enable_developer_extras()
    enable_vertex_snapping()
    adjust_3D_view_settings()
    initialize_depsgraph_update_handler()
    
    if load_target_model:
        load_model()

    print("Blender setup complete")


def delete_default_objects() -> None:
    for obj in bpy.data.objects:
        obj.select_set(obj.name in DEFAULT_OBJECTS)

    bpy.ops.object.delete()

    print(f"Default objects ({DEFAULT_OBJECTS}) deleted")


def load_model() -> None:
    if target_blend_file is None:
        return

    with bpy.data.libraries.load(str(target_blend_file)) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        bpy.context.collection.objects.link(obj)

    print(f"Loaded external model: {target_blend_file.name}")


def enable_developer_extras() -> None:
    prefs = bpy.context.preferences
    view = prefs.view

    if not view.show_developer_ui:
        view.show_developer_ui = True
        bpy.ops.wm.save_userpref()

        print("Developer Extras enabled")
    else:
        print("Developer Extras already enabled")


def enable_vertex_snapping() -> None:
    bpy.context.tool_settings.use_snap = True
    bpy.context.tool_settings.snap_elements = {"VERTEX"}
    bpy.context.tool_settings.snap_target = "CLOSEST"

    print("Vertex snapping enabled")


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

                print("3D view settings adjusted")
                return
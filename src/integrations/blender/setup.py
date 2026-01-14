import bpy
from bpy.types import Area, SpaceView3D
from typing import Optional

from src.helpers.main import is_process_running 
from src.constants.misc import Executable
from src.integrations.blender.handlers import initialize_depsgraph_update_handler


def setup_blender() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    delete_existing_meshes()
    enable_developer_extras()
    enable_vertex_snapping()
    adjust_3D_view_settings()
    initialize_depsgraph_update_handler()


def delete_existing_meshes() -> None:
    bpy.ops.object.select_all(action = "SELECT")
    bpy.ops.object.delete()


def enable_developer_extras() -> None:
    prefs = bpy.context.preferences
    view = prefs.view
    
    if not view.show_developer_ui:
        view.show_developer_ui = True
        bpy.ops.wm.save_userpref()
        print("Developer Extras enabled!")
    else:
        print("Developer Extras already enabled!")
        
        
def enable_vertex_snapping() -> None:
    bpy.context.tool_settings.use_snap = True
    bpy.context.tool_settings.snap_elements = {"VERTEX"}
    bpy.context.tool_settings.snap_target = "CLOSEST"  


def get_3d_space(area: Area) -> Optional[SpaceView3D]:
    return next((space for space in area.spaces if space.type == "VIEW_3D"), None)
        

def adjust_3D_view_settings() -> None:
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = get_3d_space(area)
            if space:
                space.clip_end = 5000.0  # Clip distance
               
                shading = space.shading
                shading.type = "SOLID"  # Set the shading mode to Solid
               
                # Uniform Lighting
                shading.light = "FLAT"
                shading.color_type = "TEXTURE"
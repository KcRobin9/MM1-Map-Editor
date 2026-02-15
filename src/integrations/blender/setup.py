import bpy
from bpy.types import Area, SpaceView3D
from typing import Optional

from src.helpers.main import is_process_running 
from src.constants.misc import Executable
from src.integrations.blender.handlers import initialize_depsgraph_update_handler


def setup_blender(dont_delete_existing_model) -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    delete_existing_meshes(dont_delete_existing_model)
    enable_developer_extras()
    enable_vertex_snapping()
    adjust_3D_view_settings()
    initialize_depsgraph_update_handler()
    print("Blender setup complete")


def delete_existing_meshes(dont_delete_existing_model) -> None:
    if dont_delete_existing_model:
        print("Existing model not deleted")
        return
    
    bpy.ops.object.select_all(action = "SELECT")
    bpy.ops.object.delete()
    print("Existing model deleted")


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
    print("Vertex Snapping enabled")


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
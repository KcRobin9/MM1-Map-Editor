

import bpy

from constants.misc import Executable
from helpers.main import is_process_running
from integrations.blender.panels.vertex import VertexGroup


def initialize_blender_panels() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    bpy.utils.register_class(VertexGroup)
    bpy.types.Object.vertex_coords = bpy.props.CollectionProperty(type = VertexGroup)
    bpy.utils.register_class(OBJECT_PT_CellTypePanel)
    bpy.utils.register_class(OBJECT_PT_MaterialTypePanel)
    bpy.utils.register_class(OBJECT_PT_PolygonMiscOptionsPanel)
    bpy.utils.register_class(OBJECT_PT_HUDColorPanel)
    bpy.utils.register_class(OBJECT_PT_VertexCoordinates)
        
        
def initialize_blender_operators() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    bpy.utils.register_class(OBJECT_OT_UpdateUVMapping)
    bpy.utils.register_class(OBJECT_OT_ExportPolygons)
    bpy.utils.register_class(OBJECT_OT_AssignCustomProperties)
    bpy.utils.register_class(OBJECT_OT_ProcessPostExtrude)
    bpy.utils.register_class(OBJECT_OT_RenameChildren)
    bpy.utils.register_class(OBJECT_OT_RenameSequential)
    

def initialize_blender_waypoint_editor() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    bpy.utils.register_class(CREATE_SINGLE_WAYPOINT_OT_operator)
    bpy.utils.register_class(LOAD_WAYPOINTS_FROM_CSV_OT_operator)
    bpy.utils.register_class(LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator)
    bpy.utils.register_class(LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator)
    bpy.utils.register_class(EXPORT_SELECTED_WAYPOINTS_OT_operator)
    bpy.utils.register_class(EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator)
    bpy.utils.register_class(EXPORT_ALL_WAYPOINTS_OT_operator)
    bpy.utils.register_class(EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator)
    
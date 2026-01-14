

import bpy

from src.constants.misc import Executable
from src.helpers.main import is_process_running
from src.integrations.blender.modeling.uv_mapping import OBJECT_OT_UpdateUVMapping

from src.integrations.blender.operators.custom_properties import OBJECT_OT_AssignCustomProperties
from src.integrations.blender.operators.export_polygons import OBJECT_OT_ExportPolygons
from src.integrations.blender.operators.process_extrude import OBJECT_OT_ProcessPostExtrude
from src.integrations.blender.operators.rename_polygons import OBJECT_OT_RenameChildren, OBJECT_OT_RenameSequential
from src.integrations.blender.operators.waypoints import CREATE_SINGLE_WAYPOINT_OT_operator, EXPORT_ALL_WAYPOINTS_OT_operator, EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator, EXPORT_SELECTED_WAYPOINTS_OT_operator, EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator, LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator, LOAD_WAYPOINTS_FROM_CSV_OT_operator, LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator

from src.integrations.blender.panels.cells import OBJECT_PT_CellTypePanel
from src.integrations.blender.panels.hud import OBJECT_PT_HUDColorPanel
from src.integrations.blender.panels.materials import OBJECT_PT_MaterialTypePanel
from src.integrations.blender.panels.misc import OBJECT_PT_PolygonMiscOptionsPanel
from src.integrations.blender.panels.vertex import OBJECT_PT_VertexCoordinates, VertexGroup


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
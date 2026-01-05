import bpy

from src.constants.misc import Folder
from src.integrations.blender.waypoints.create import create_waypoint
from src.integrations.blender.waypoints.export import export_selected_waypoints
from src.integrations.blender.waypoints.load import load_cops_and_robbers_waypoints, load_waypoints_from_csv, load_waypoints_from_race_data


class CREATE_SINGLE_WAYPOINT_OT_operator(bpy.types.Operator):
    bl_idname = "create.single_waypoint"
    bl_label = "Create Single Waypoint"

    def execute(self, context: bpy.types.Context) -> set:
        create_waypoint(name = "WP_")  
        self.report({"INFO"}, "Created Waypoint")
        return {"FINISHED"}


class LOAD_WAYPOINTS_FROM_CSV_OT_operator(bpy.types.Operator):
    bl_idname = "load.waypoints_from_csv"
    bl_label = "Load Waypoints from CSV"

    def execute(self, context: bpy.types.Context) -> set:
        load_waypoints_from_csv(input_waypoint_file)
        self.report({"INFO"}, "Loaded Waypoints from CSV")
        return {"FINISHED"}


class LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator(bpy.types.Operator):
    bl_idname = "load.waypoints_from_race_data"
    bl_label = "Load Waypoints from Race Data"

    def execute(self, context: bpy.types.Context) -> set:
        load_waypoints_from_race_data(race_data, waypoint_type_input, waypoint_number_input)
        self.report({"INFO"}, "Loaded Waypoints from Race Data")
        return {"FINISHED"}
    
    
class LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator(bpy.types.Operator):
    bl_idname = "load.cnr_from_csv"
    bl_label = "Load CnR Waypoints from CSV"

    def execute(self, context: bpy.types.Context) -> set:
        Folder.BASE
        load_cops_and_robbers_waypoints("COPSWAYPOINTS.CSV")
        self.report({"INFO"}, "Loaded Cops & Robber Waypoints from CSV")
        return {"FINISHED"}


class EXPORT_SELECTED_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints"
    bl_label = "Export selected Waypoints"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = False, add_brackets = False)
        self.report({"INFO"}, "Exported Selected Waypoints")
        return {"FINISHED"}
    
    
class EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.selected_waypoints_with_brackets"
    bl_label = "Export selected Waypoints with Brackets"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = False, add_brackets = True)
        self.report({"INFO"}, "Exported Selected Waypoints with Brackets")
        return {"FINISHED"}
    
    
class EXPORT_ALL_WAYPOINTS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints"
    bl_label = "Export All Waypoints"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = True, add_brackets = False)
        self.report({"INFO"}, "Exported All Waypoints")
        return {"FINISHED"}


class EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator(bpy.types.Operator):
    bl_idname = "export.all_waypoints_with_brackets"
    bl_label = "Export All Waypoints with Brackets"

    def execute(self, context: bpy.types.Context) -> set:
        export_selected_waypoints(export_all = True, add_brackets = True)
        self.report({"INFO"}, "Exported All Waypoints with Brackets")
        return {"FINISHED"}
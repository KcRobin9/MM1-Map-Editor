# import bpy


# class OBJECT_OT_ProcessPostExtrude(bpy.types.Operator):
#     bl_idname = "object.process_post_extrude"
#     bl_label = "Process Post Extrude"
#     bl_options = {"REGISTER", "UNDO"}
    
#     triangulate: bpy.props.BoolProperty(name = "Triangulate", default = False)

#     @classmethod
#     def poll(cls, context: bpy.types.Context) -> bool:
#         return context.object and context.object.type == "MESH"

#     def execute(self, context: bpy.types.Context) -> set:
#         try:
#             # Store original mode to restore it if operation fails
#             original_mode = context.object.mode
            
#             # Process the mesh
#             bpy.ops.object.mode_set(mode = "EDIT")
#             bpy.ops.mesh.select_all(action = "SELECT")
            
#             if self.triangulate:
#                 bpy.ops.mesh.quads_convert_to_tris()
            
#             bpy.ops.mesh.edge_split()
#             bpy.ops.mesh.separate(type = "LOOSE")
#             bpy.ops.object.mode_set(mode = "OBJECT")
            
#             self.report({"INFO"}, "Processed Post Extrude")
#             return {"FINISHED"}
            
#         except Exception as e:
#             # Restore original mode if possible
#             try:
#                 bpy.ops.object.mode_set(mode = original_mode)
#             except:
#                 pass
                
#             self.report({"ERROR"}, f"Error processing extrude: {str(e)}")
#             return {"CANCELLED"}
        

# # class OBJECT_OT_ProcessPostExtrude(bpy.types.Operator):
# #     bl_idname = "object.process_post_extrude"
# #     bl_label = "Process Post Extrude"
# #     bl_options = {"REGISTER", "UNDO"}
    
# #     triangulate: bpy.props.BoolProperty(name = "Triangulate", default = False)

# #     def execute(self, context: bpy.types.Context) -> set:
# #         if context.object and context.object.type == "MESH":
# #             bpy.ops.object.mode_set(mode = "EDIT")
# #             bpy.ops.mesh.select_all(action = "SELECT")
            
# #             if self.triangulate:
# #                 bpy.ops.mesh.quads_convert_to_tris()
            
# #             bpy.ops.mesh.edge_split()
# #             bpy.ops.mesh.separate(type = "LOOSE")
# #             bpy.ops.object.mode_set(mode = "OBJECT")
# #             self.report({"INFO"}, "Processed Post Extrude")
# #             return {"FINISHED"}
# #         else:
# #             self.report({"WARNING"}, "No mesh object selected")
# #             return {"CANCELLED"}



import bpy

from src.integrations.blender.utils import (
    get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties
)


class OBJECT_OT_ProcessPostExtrude(bpy.types.Operator):
    bl_idname = "object.process_post_extrude"
    bl_label = "Process Post Extrude"
    bl_options = {"REGISTER", "UNDO"}

    triangulate: bpy.props.BoolProperty(name="Triangulate", default=False)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object and context.object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set:
        try:
            source_obj = context.object

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")

            if self.triangulate:
                bpy.ops.mesh.quads_convert_to_tris()

            bpy.ops.mesh.edge_split()
            bpy.ops.mesh.separate(type="LOOSE")
            bpy.ops.object.mode_set(mode="OBJECT")

            # Get used numbers AFTER separating so we don't reuse any
            used = get_used_bound_numbers(context.scene)

            new_objects = [
                obj for obj in context.selected_objects
                if obj.type == "MESH"
            ]

            renamed = []
            for obj in new_objects:
                # Copy properties from source
                assign_map_editor_properties(obj, source=source_obj)

                # Fix name if it has a dot suffix
                if "." in obj.name:
                    old_name = obj.name
                    new_num = next_available_bound_number(used)
                    used.add(new_num)
                    obj.name = f"P{new_num}"
                    renamed.append(f"{old_name} → {obj.name}")

            msg = f"Processed {len(new_objects)} polygon(s)"
            if renamed:
                msg += f". Renamed: {', '.join(renamed)}"
            self.report({"INFO"}, msg)
            return {"FINISHED"}

        except Exception as e:
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except:
                pass
            self.report({"ERROR"}, f"Error: {str(e)}")
            return {"CANCELLED"}
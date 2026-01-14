import bpy


class OBJECT_OT_ProcessPostExtrude(bpy.types.Operator):
    bl_idname = "object.process_post_extrude"
    bl_label = "Process Post Extrude"
    bl_options = {"REGISTER", "UNDO"}
    
    triangulate: bpy.props.BoolProperty(name = "Triangulate", default = False)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object and context.object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set:
        try:
            # Store original mode to restore it if operation fails
            original_mode = context.object.mode
            
            # Process the mesh
            bpy.ops.object.mode_set(mode = "EDIT")
            bpy.ops.mesh.select_all(action = "SELECT")
            
            if self.triangulate:
                bpy.ops.mesh.quads_convert_to_tris()
            
            bpy.ops.mesh.edge_split()
            bpy.ops.mesh.separate(type = "LOOSE")
            bpy.ops.object.mode_set(mode = "OBJECT")
            
            self.report({"INFO"}, "Processed Post Extrude")
            return {"FINISHED"}
            
        except Exception as e:
            # Restore original mode if possible
            try:
                bpy.ops.object.mode_set(mode = original_mode)
            except:
                pass
                
            self.report({"ERROR"}, f"Error processing extrude: {str(e)}")
            return {"CANCELLED"}
        

# class OBJECT_OT_ProcessPostExtrude(bpy.types.Operator):
#     bl_idname = "object.process_post_extrude"
#     bl_label = "Process Post Extrude"
#     bl_options = {"REGISTER", "UNDO"}
    
#     triangulate: bpy.props.BoolProperty(name = "Triangulate", default = False)

#     def execute(self, context: bpy.types.Context) -> set:
#         if context.object and context.object.type == "MESH":
#             bpy.ops.object.mode_set(mode = "EDIT")
#             bpy.ops.mesh.select_all(action = "SELECT")
            
#             if self.triangulate:
#                 bpy.ops.mesh.quads_convert_to_tris()
            
#             bpy.ops.mesh.edge_split()
#             bpy.ops.mesh.separate(type = "LOOSE")
#             bpy.ops.object.mode_set(mode = "OBJECT")
#             self.report({"INFO"}, "Processed Post Extrude")
#             return {"FINISHED"}
#         else:
#             self.report({"WARNING"}, "No mesh object selected")
#             return {"CANCELLED"}
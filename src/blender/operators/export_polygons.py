class OBJECT_OT_ExportPolygons(bpy.types.Operator):
    bl_idname = "object.export_polygons"
    bl_label = "Export Blender Polygons"
    
    select_all: bpy.props.BoolProperty(default = True)

    def execute(self, context: bpy.types.Context) -> Set[set]:                            
        export_file = Folder.BLENDER_EXPORT_POLYGON / f"Polygons_{CURRENT_TIME_FORMATTED}{FileType.TEXT}"
                            
        # Select Mesh Objects based on the "select_all" property
        if self.select_all:
            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        else:
            mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
            
        if not mesh_objects:
            self.report({"WARNING"}, "No mesh objects found for export.")
            return {"CANCELLED"}
        
        # Set the first mesh object as the active object and apply transformations (to get Global coordinates)
        context.view_layer.objects.active = mesh_objects[0]
        bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    
        try:
            with open(export_file, "w") as f:
                for obj in mesh_objects:
                    export_script = export_formatted_polygons(obj) 
                    f.write(export_script + "\n\n")
                    
            # Open the file with Notepad++ and simulate copy to clipboard
            open_with_notepad_plus(export_file)                                
            time.sleep(1.0)  # Give Notepad++ time to load the file
            pyautogui.hotkey(Key.CTRL, Key.A)
            pyautogui.hotkey(Key.CTRL, Key.A)
            
            self.report({"INFO"}, f"Saved data to {export_file}")
            bpy.ops.object.select_all(action = "DESELECT")
            
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export polygons: {str(e)}")
            return {"CANCELLED"}
        
        return {"FINISHED"}
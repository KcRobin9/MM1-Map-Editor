import bpy


def initialize_depsgraph_update_handler() -> None:
    # Remove existing handlers to prevent duplicates
    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)
        
    # Register the handler
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)


def depsgraph_update_handler(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    try:
        updated_waypoints = False
        for update in depsgraph.updates:
            if update.id.__class__ == bpy.types.Object:  # Only check object updates (not materials, etc.)
                obj = update.id
                if obj.name.startswith("WP_"):
                    updated_waypoints = True
                    break
                    
        if depsgraph.id_type_updated('OBJECT'):  # Also check if any objects were added or removed
            updated_waypoints = True
                    
        # Only update colors if waypoints were actually modified
        if updated_waypoints and any(obj.name.startswith("WP_") for obj in bpy.data.objects):
            update_waypoint_colors()
            
    except Exception as e:
        print(f"Error in depsgraph_update_handler: {str(e)}")
import bpy

from src.integrations.blender.waypoints.helpers import update_waypoint_colors
from src.integrations.blender.operators.ai_streets import apply_street_color, ST_PREFIX


def initialize_depsgraph_update_handler() -> None:
    # Remove existing handlers to prevent duplicates
    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)
        
    # Register the handler
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)


def depsgraph_update_handler(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    try:
        updated_waypoints = False
        updated_streets: set = set()

        for update in depsgraph.updates:
            if update.id.__class__ == bpy.types.Object:
                obj = update.id
                if obj.name.startswith("WP_"):
                    updated_waypoints = True
                elif obj.name.startswith(ST_PREFIX) and obj.type == 'CURVE':
                    updated_streets.add(obj.name)
            elif update.id.__class__ == bpy.types.Curve:
                # Spline changes come through as Curve data-block updates
                for obj in bpy.data.objects:
                    if obj.type == 'CURVE' and obj.name.startswith(ST_PREFIX) and obj.data == update.id:
                        updated_streets.add(obj.name)

        if depsgraph.id_type_updated('OBJECT'):
            updated_waypoints = True

        if updated_waypoints and any(obj.name.startswith("WP_") for obj in bpy.data.objects):
            update_waypoint_colors()

        for name in updated_streets:
            obj = bpy.data.objects.get(name)
            if obj:
                apply_street_color(obj)

    except Exception as e:
        print(f"Error in depsgraph_update_handler: {str(e)}")
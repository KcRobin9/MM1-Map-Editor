import bpy

from src.integrations.blender.waypoints.helpers import update_waypoint_colors
from src.integrations.blender.operators.ai_streets import apply_street_color, ST_PREFIX

# Track the last active polygon so we only sync once per selection change.
_last_active_polygon: str = ""


def _sync_texture_category(obj) -> None:
    """Switch the scene's texture_category and obj.texture_name to match the
    active polygon's material.  Safe to call from a depsgraph handler."""
    from pathlib import Path
    from src.integrations.blender.modeling.uv_mapping import (
        category_for_texture, ensure_category_loaded,
    )

    # Read the texture stem from the material node (ground truth).
    tex_stem = None
    if obj.material_slots:
        mat = obj.material_slots[0].material
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image:
                    stem = Path(node.image.name).stem
                    tex_stem = stem.replace(".DDS", "").replace(".dds", "").upper()
                    break

    if not tex_stem:
        return

    scene = bpy.context.scene
    needed_cat = category_for_texture(tex_stem)

    # Load DDS files for the target category before switching (safe here).
    ensure_category_loaded(needed_cat)

    if scene.texture_category != needed_cat:
        scene.texture_category = needed_cat

    # Sync the enum property to match the material.
    if obj.texture_name != tex_stem:
        try:
            obj.texture_name = tex_stem
        except (TypeError, AttributeError):
            pass


def initialize_depsgraph_update_handler() -> None:
    # Remove existing handlers to prevent duplicates
    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)

    # Register the handler
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)


def depsgraph_update_handler(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    global _last_active_polygon
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

        # ── Texture category sync on polygon selection change ──────────────────
        active = bpy.context.active_object
        if (
            active
            and active.type == "MESH"
            and active.name != _last_active_polygon
        ):
            _last_active_polygon = active.name
            # Only sync for polygon objects (P<number> / Shape_<number>).
            n = active.name
            is_polygon = (
                (n.startswith("P") and n[1:].split(".")[0].isdigit())
                or n.startswith("Shape_")
            )
            if is_polygon:
                _sync_texture_category(active)

    except Exception as e:
        print(f"Error in depsgraph_update_handler: {str(e)}")
import bpy
import bmesh
from pathlib import Path

from src.integrations.blender.waypoints.helpers import update_waypoint_colors
from src.integrations.blender.operators.ai_streets import apply_street_color, ST_PREFIX
from src.integrations.blender.modeling.uv_mapping import category_for_texture, ensure_category_loaded

_last_active_polygon: str = ""

_VERTEX_POLL_INTERVAL = 0.05  # seconds — fast enough for smooth live feedback


def _is_polygon_name(name: str) -> bool:
    return (name.startswith("P") and name[1:].split(".")[0].isdigit()) or name.startswith("Shape_")


def _sync_vertex_coords_from_bmesh(obj) -> None:
    bm     = bmesh.from_edit_mesh(obj.data)
    verts  = bm.verts
    coords = obj.vertex_coords

    while len(coords) < len(verts):
        coords.add()

    for i, v in enumerate(verts):
        co = v.co
        coords[i].x = co.x
        coords[i].y = co.y
        coords[i].z = co.z


def _vertex_poll_timer() -> float:
    try:
        ctx = bpy.context
        obj = ctx.active_object
        if obj and obj.type == "MESH" and ctx.mode == "EDIT_MESH" and _is_polygon_name(obj.name):
            _sync_vertex_coords_from_bmesh(obj)
    except Exception:
        pass
    return _VERTEX_POLL_INTERVAL


def _sync_texture_category(obj) -> None:
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

    scene       = bpy.context.scene
    needed_cat  = category_for_texture(tex_stem)

    ensure_category_loaded(needed_cat)

    if scene.texture_category != needed_cat:
        scene.texture_category = needed_cat

    if obj.texture_name != tex_stem:
        try:
            obj.texture_name = tex_stem
        except (TypeError, AttributeError):
            pass


def initialize_depsgraph_update_handler() -> None:
    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)

    if not bpy.app.timers.is_registered(_vertex_poll_timer):
        bpy.app.timers.register(_vertex_poll_timer, persistent=True)


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
                # Spline edits arrive as Curve data-block updates, not Object updates
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

        # ── Vertex coords sync + texture category sync ────────────────────────────
        active = bpy.context.active_object
        if active and active.type == "MESH":
            n          = active.name
            is_polygon = _is_polygon_name(n)

            if is_polygon and depsgraph.id_type_updated('MESH'):
                eval_obj = depsgraph.objects.get(active.name)
                mesh     = eval_obj.data if eval_obj else active.data
                verts    = mesh.vertices
                coords   = active.vertex_coords

                while len(coords) < len(verts):
                    coords.add()

                for i, v in enumerate(verts):
                    co = v.co
                    coords[i].x = co.x
                    coords[i].y = co.y
                    coords[i].z = co.z

            if is_polygon and n != _last_active_polygon:
                _last_active_polygon = n
                _sync_texture_category(active)

    except Exception as e:
        print(f"Error in depsgraph_update_handler: {str(e)}")
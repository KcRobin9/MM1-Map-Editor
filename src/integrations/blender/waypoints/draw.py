"""
Draw waypoint path lines and CnR markers in the 3D viewport.
Registered via draw_handler_add on Blender startup (inits.py).
"""
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

_draw_handler        = None
_draw_handler_street = None


def _draw_waypoint_paths() -> None:
    # Respect the user's toggle
    try:
        if not bpy.context.scene.wp_show_paths:
            return
    except AttributeError:
        pass  # property not yet registered — draw anyway
    # Gather WP_ objects sorted by name (which encodes race + index)
    wps = sorted(
        (o for o in bpy.data.objects if o.name.startswith("WP_")),
        key=lambda o: o.name,
    )
    cnr = [o for o in bpy.data.objects if o.name.startswith("CR_")]

    # ── Race waypoint lines ───────────────────────────────────────────────────
    if len(wps) >= 2:
        # Group by race key (everything before the last '-N' index)
        from collections import defaultdict
        groups: dict = defaultdict(list)
        for obj in wps:
            # Name format: WP_BLZ_0-3  → key = WP_BLZ_0
            parts = obj.name.rsplit("-", 1)
            key   = parts[0] if len(parts) == 2 and parts[1].isdigit() else obj.name
            try:
                idx = int(parts[1]) if len(parts) == 2 else 0
            except ValueError:
                idx = 0
            groups[key].append((idx, obj))

        line_verts = []
        for key, entries in groups.items():
            ordered = [obj for _, obj in sorted(entries, key=lambda t: t[0])]
            for i in range(len(ordered) - 1):
                line_verts.append(ordered[i].matrix_world.to_translation())
                line_verts.append(ordered[i + 1].matrix_world.to_translation())

        if line_verts:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            batch  = batch_for_shader(shader, "LINES", {"pos": line_verts})
            gpu.state.line_width_set(2.0)
            gpu.state.blend_set("ALPHA")
            shader.bind()
            shader.uniform_float("color", (1.0, 0.85, 0.0, 0.85))  # yellow
            batch.draw(shader)
            gpu.state.blend_set("NONE")

    # ── CnR connection lines (Bank→Gold→Robber per set) ───────────────────────
    if cnr:
        from collections import defaultdict
        sets: dict = defaultdict(dict)
        for obj in cnr:
            for role in ("Bank", "Gold", "Robber"):
                if role in obj.name:
                    num_str = obj.name.replace(f"CR_{role}", "")
                    try:
                        sets[int(num_str)][role] = obj
                    except ValueError:
                        pass

        cnr_verts = []
        for s in sets.values():
            ordered = [s.get(r) for r in ("Bank", "Gold", "Robber")]
            present = [o for o in ordered if o is not None]
            for i in range(len(present) - 1):
                cnr_verts.append(present[i].matrix_world.to_translation())
                cnr_verts.append(present[i + 1].matrix_world.to_translation())

        if cnr_verts:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            batch  = batch_for_shader(shader, "LINES", {"pos": cnr_verts})
            gpu.state.line_width_set(1.5)
            gpu.state.blend_set("ALPHA")
            shader.bind()
            shader.uniform_float("color", (0.4, 0.8, 1.0, 0.7))  # light blue
            batch.draw(shader)
            gpu.state.blend_set("NONE")


def _draw_active_street_vertex() -> None:
    """Draw a purple crosshair on the currently active street vertex."""
    try:
        ctx = bpy.context
        obj = ctx.active_object
        if not (obj and obj.type == 'CURVE' and obj.name.startswith('ST_')):
            return
        if not obj.data.splines:
            return

        # Rebuild vertex list inline to avoid circular imports
        verts = []
        for i, sp in enumerate(obj.data.splines):
            if i == 0:
                verts.append(obj.matrix_world @ Vector(sp.points[0].co[:3]))
            verts.append(obj.matrix_world @ Vector(sp.points[1].co[:3]))

        if not verts:
            return

        n   = len(verts)
        idx = max(0, min(ctx.scene.st_vertex_index, n - 1))
        v   = verts[idx]

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.bind()
        gpu.state.blend_set("ALPHA")

        # Filled dot
        batch_pt = batch_for_shader(shader, 'POINTS', {"pos": [(v.x, v.y, v.z)]})
        gpu.state.point_size_set(16.0)
        shader.uniform_float("color", (0.65, 0.0, 1.0, 1.0))   # vivid purple
        batch_pt.draw(shader)

        # Crosshair lines
        S = 3.0
        cross = [
            (v.x - S, v.y,     v.z), (v.x + S, v.y,     v.z),
            (v.x,     v.y - S, v.z), (v.x,     v.y + S, v.z),
        ]
        batch_ln = batch_for_shader(shader, 'LINES', {"pos": cross})
        gpu.state.line_width_set(2.5)
        shader.uniform_float("color", (0.65, 0.0, 1.0, 0.75))
        batch_ln.draw(shader)

        gpu.state.blend_set("NONE")
        gpu.state.point_size_set(1.0)
        gpu.state.line_width_set(1.0)

    except Exception:
        pass


def register_draw_handler() -> None:
    global _draw_handler, _draw_handler_street
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            _draw_waypoint_paths, (), "WINDOW", "POST_VIEW"
        )
    if _draw_handler_street is None:
        _draw_handler_street = bpy.types.SpaceView3D.draw_handler_add(
            _draw_active_street_vertex, (), "WINDOW", "POST_VIEW"
        )


def unregister_draw_handler() -> None:
    global _draw_handler, _draw_handler_street
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        _draw_handler = None
    if _draw_handler_street is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_street, "WINDOW")
        _draw_handler_street = None

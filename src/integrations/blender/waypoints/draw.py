"""
Draw waypoint path lines, CnR markers, street direction arrows, and the
active vertex highlight in the 3D viewport.
Registered via draw_handler_add on Blender startup (inits.py).
"""
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

_draw_handler        = None   # POST_VIEW  — waypoint/CnR lines
_draw_handler_street = None   # POST_VIEW  — street arrows + vertex marker


# ── Waypoint / CnR path lines (POST_VIEW, world-space coordinates) ────────────

def _draw_waypoint_paths() -> None:
    try:
        if not bpy.context.scene.wp_show_paths:
            return
    except AttributeError:
        pass
    wps = sorted(
        (o for o in bpy.data.objects if o.name.startswith("WP_")),
        key=lambda o: o.name,
    )
    cnr = [o for o in bpy.data.objects if o.name.startswith("CR_")]

    # ── Race waypoint lines ───────────────────────────────────────────────────
    if len(wps) >= 2:
        from collections import defaultdict
        groups: dict = defaultdict(list)
        for obj in wps:
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
            shader.uniform_float("color", (1.0, 0.85, 0.0, 0.85))
            batch.draw(shader)
            gpu.state.blend_set("NONE")

    # ── CnR connection lines ──────────────────────────────────────────────────
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
            shader.uniform_float("color", (0.4, 0.8, 1.0, 0.7))
            batch.draw(shader)
            gpu.state.blend_set("NONE")


# ── Street direction arrows + active vertex (POST_VIEW, world-space) ──────────
#
# Both elements use absolute world-unit sizes so they remain constant
# regardless of viewport zoom level.

def _draw_street_overlays() -> None:
    try:
        ctx = bpy.context
        if ctx.region is None or ctx.region_data is None:
            return

        rv3d = ctx.region_data

        # Screen-aligned unit vectors in world space — used for the crosshair
        # so it always faces the camera while staying world-unit sized.
        view_inv  = rv3d.view_matrix.inverted()
        cam_right = Vector(view_inv.col[0][:3]).normalized()
        cam_up    = Vector(view_inv.col[1][:3]).normalized()

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.bind()
        gpu.state.blend_set("ALPHA")

        # ── Direction arrows ──────────────────────────────────────────────────
        try:
            show_arrows = ctx.scene.st_show_arrows
        except AttributeError:
            show_arrows = True

        if show_arrows:
            S    = 2.0                      # chevron arm length (world units)
            Z_UP = Vector((0.0, 0.0, 1.0))
            all_arrow_lines = []

            for obj in bpy.data.objects:
                if obj.type != 'CURVE' or not obj.name.startswith('ST_'):
                    continue
                for sp in obj.data.splines:
                    p0 = obj.matrix_world @ Vector(sp.points[0].co[:3])
                    p1 = obj.matrix_world @ Vector(sp.points[1].co[:3])
                    seg     = p1 - p0
                    seg_len = seg.length
                    if seg_len < 0.01:
                        continue
                    fwd  = seg / seg_len
                    perp = fwd.cross(Z_UP)
                    if perp.length_squared < 0.001:
                        perp = fwd.cross(Vector((0.0, 1.0, 0.0)))
                    perp = perp.normalized()

                    # Chevron tip at 70 % along the segment
                    mid  = p0 + 0.70 * seg
                    tip  = mid + fwd  * S
                    left = mid - fwd  * S + perp * S
                    rig  = mid - fwd  * S - perp * S
                    all_arrow_lines += [tip, left, tip, rig]

            if all_arrow_lines:
                batch = batch_for_shader(shader, 'LINES', {"pos": all_arrow_lines})
                gpu.state.line_width_set(2.0)
                shader.uniform_float("color", (1.0, 1.0, 1.0, 0.7))
                batch.draw(shader)

        # ── Group start/end markers (green = start, orange = end) ───────────
        obj = ctx.active_object
        if obj and obj.type == 'CURVE' and obj.name.startswith('ST_'):
            gname = getattr(obj, "st_group_name", "")
            if gname:
                grp_streets = [
                    o for o in bpy.data.objects
                    if o.type == 'CURVE' and o.name.startswith('ST_')
                    and getattr(o, "st_group_name", "") == gname
                ]
                S = 2.5   # marker arm length (world units)
                start_lines, end_lines = [], []
                start_dots,  end_dots  = [], []
                for st in grp_streets:
                    if not st.data.splines:
                        continue
                    splines = st.data.splines
                    v_start = st.matrix_world @ Vector(splines[0].points[0].co[:3])
                    v_end   = st.matrix_world @ Vector(splines[-1].points[1].co[:3])
                    for v, lines, dots in ((v_start, start_lines, start_dots),
                                           (v_end,   end_lines,   end_dots)):
                        lines += [v - cam_right * S, v + cam_right * S,
                                  v - cam_up    * S, v + cam_up    * S]
                        dots.append(v)

                if start_lines:
                    b = batch_for_shader(shader, 'LINES', {"pos": start_lines})
                    gpu.state.line_width_set(2.5)
                    shader.uniform_float("color", (0.1, 0.9, 0.2, 1.0))   # green = start
                    b.draw(shader)
                    b = batch_for_shader(shader, 'POINTS', {"pos": start_dots})
                    gpu.state.point_size_set(10.0)
                    shader.uniform_float("color", (0.1, 0.9, 0.2, 1.0))
                    b.draw(shader)
                if end_lines:
                    b = batch_for_shader(shader, 'LINES', {"pos": end_lines})
                    gpu.state.line_width_set(2.5)
                    shader.uniform_float("color", (1.0, 0.45, 0.0, 1.0))  # orange = end
                    b.draw(shader)
                    b = batch_for_shader(shader, 'POINTS', {"pos": end_dots})
                    gpu.state.point_size_set(10.0)
                    shader.uniform_float("color", (1.0, 0.45, 0.0, 1.0))
                    b.draw(shader)

        # ── Active vertex marker — shown for every lane in the group ─────────
        obj = ctx.active_object
        if obj and obj.type == 'CURVE' and obj.name.startswith('ST_') and obj.data.splines:

            # Collect streets to mark: whole group or just the active object
            gname = getattr(obj, "st_group_name", "")
            if gname:
                mark_streets = [
                    o for o in bpy.data.objects
                    if o.type == 'CURVE' and o.name.startswith('ST_')
                    and getattr(o, "st_group_name", "") == gname
                ]
            else:
                mark_streets = [obj]

            C   = 2.0   # crosshair arm length (world units)
            idx = ctx.scene.st_vertex_index

            all_cross_lines = []
            all_dots        = []

            for street in mark_streets:
                if not street.data.splines:
                    continue
                verts = []
                for i, sp in enumerate(street.data.splines):
                    if i == 0:
                        verts.append(street.matrix_world @ Vector(sp.points[0].co[:3]))
                    verts.append(street.matrix_world @ Vector(sp.points[1].co[:3]))
                if not verts:
                    continue
                v = verts[max(0, min(idx, len(verts) - 1))]
                all_cross_lines += [
                    v - cam_right * C, v + cam_right * C,
                    v - cam_up    * C, v + cam_up    * C,
                ]
                all_dots.append(v)

            if all_cross_lines:
                batch_c = batch_for_shader(shader, 'LINES', {"pos": all_cross_lines})
                gpu.state.line_width_set(2.5)
                shader.uniform_float("color", (0.65, 0.0, 1.0, 1.0))
                batch_c.draw(shader)

            if all_dots:
                batch_d = batch_for_shader(shader, 'POINTS', {"pos": all_dots})
                gpu.state.point_size_set(8.0)
                shader.uniform_float("color", (0.65, 0.0, 1.0, 1.0))
                batch_d.draw(shader)

        gpu.state.blend_set("NONE")
        gpu.state.line_width_set(1.0)
        gpu.state.point_size_set(1.0)

    except Exception:
        pass


# ── Registration ──────────────────────────────────────────────────────────────

def register_draw_handler() -> None:
    global _draw_handler, _draw_handler_street
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            _draw_waypoint_paths, (), "WINDOW", "POST_VIEW"
        )
    if _draw_handler_street is None:
        _draw_handler_street = bpy.types.SpaceView3D.draw_handler_add(
            _draw_street_overlays, (), "WINDOW", "POST_VIEW"   # world-space sizes
        )


def unregister_draw_handler() -> None:
    global _draw_handler, _draw_handler_street
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, "WINDOW")
        _draw_handler = None
    if _draw_handler_street is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_street, "WINDOW")
        _draw_handler_street = None

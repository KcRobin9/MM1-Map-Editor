"""Car Editor — wheels module (split from the former car_editor.py monolith)."""
import bpy
import math
import bmesh
import mathutils
from pathlib import Path

from src.constants.folder import Folder
from src.integrations.blender.modeling.meshes import _build_material

from src.integrations.blender.operators.car_editor.constants import _CAR_TAG
from src.integrations.blender.operators.car_editor.common import _load_bms, get_car_objects


def _detect_wheel_texture(car_objects: list) -> str:
    """Return the material name of the first wheel's first slot, or ''."""
    for obj in car_objects:
        if obj.get(_CAR_TAG, "").startswith("wheel_") and obj.type == "MESH":
            mats = obj.data.materials
            if mats and mats[0]:
                return mats[0].name
    return ""


def _scale_wheel_to_radius(mesh, target_radius) -> None:
    """Uniformly scale a centred wheel mesh so its disc radius == target_radius.

    The wheel disc lies in the Blender Y-Z plane (axle = X); radius is the max
    distance from the hub (origin) in that plane. Scaling is uniform so width
    grows proportionally with radius. Verts are baked so the export stays clean.
    """
    if not target_radius or target_radius <= 0:
        return
    cur = max((math.hypot(v.co.y, v.co.z) for v in mesh.vertices), default=0.0)
    if cur < 1e-5:
        return
    factor = target_radius / cur
    if abs(factor - 1.0) < 1e-3:
        return
    bm = bmesh.new()
    bm.from_mesh(mesh)
    for v in bm.verts:
        v.co *= factor
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def _wheel_current_radius(mesh) -> float:
    """Disc radius of a centred wheel mesh (max distance from hub in the Y-Z plane)."""
    return max((math.hypot(v.co.y, v.co.z) for v in mesh.vertices), default=0.0)


def _sync_wheel_radius_props(scene) -> None:
    """Set ce_wheel_radius_{i} to each wheel's actual radius (guarded so the update
    callback doesn't fire and re-scale)."""
    try:
        scene.ce_wheel_radius_syncing = True
        first_r = 0.0
        for obj in get_car_objects():
            tag = obj.get(_CAR_TAG, "")
            if not tag.startswith("wheel_") or obj.type != "MESH":
                continue
            try:
                idx = int(tag.split("_")[1])
            except (ValueError, IndexError):
                continue
            r = _wheel_current_radius(obj.data)
            if r > 0:
                first_r = first_r or r
                try:
                    setattr(scene, f"ce_wheel_radius_{idx}", round(r, 3))
                except (TypeError, ValueError):
                    pass
        if first_r > 0:
            try:
                scene.ce_all_wheel_radius = round(first_r, 3)
            except (TypeError, ValueError):
                pass
    finally:
        scene.ce_wheel_radius_syncing = False


def _load_styled_wheel(car_name: str, idx: int, style: str, tex_folder,
                       target_radius=None):
    """
    Load wheel `idx` from the chosen style car's BMS (falls back to its WHL0),
    sized to target_radius. Returns the Blender mesh, or None if unavailable.
    """
    style_dir = Folder.Resources.Editor.MeshesCars / (style or "VPMUSTANG99")
    mesh_name = f"{car_name}.WHL{idx}"
    whl = style_dir / f"WHL{idx}_H.BMS"
    if not whl.is_file():
        whl = style_dir / "WHL0_H.BMS"
    mesh = _load_bms(whl, mesh_name, tex_folder) if whl.is_file() else None
    if mesh is not None and target_radius:
        _scale_wheel_to_radius(mesh, target_radius)
    return mesh


def _mirror_wheel_mesh(src_mesh: bpy.types.Mesh, new_name: str) -> bpy.types.Mesh:
    """
    Return a copy of src_mesh mirrored across local X — negates X on every
    vertex and flips face winding so outward normals stay outward.
    Preserves UVs, material slots, and the custom BMS properties.
    """
    new_mesh = src_mesh.copy()
    new_mesh.name = new_name

    bm = bmesh.new()
    bm.from_mesh(new_mesh)
    for v in bm.verts:
        v.co.x = -v.co.x
    for f in bm.faces:
        f.normal_flip()
    bm.normal_update()
    bm.to_mesh(new_mesh)
    bm.free()

    mo = list(new_mesh.get("mesh_offset", [0.0, 0.0, 0.0]))
    mo[0] = -mo[0]
    new_mesh["mesh_offset"] = mo
    new_mesh["bms_source_file"] = ""   # forces export to use part-tag fallback
    return new_mesh


# ── Operator: Apply Wheel Texture ─────────────────────────────────────────────

def _apply_wheel_tex(tex_name: str, wheels: list, tex_folder: Path) -> int:
    """Apply tex_name to all meshes in wheels list. Returns count of meshes changed."""
    seen    = set()
    swapped = 0
    new_mat = _build_material(tex_name, tex_folder)
    for whl in wheels:
        mesh = whl.data
        if id(mesh) in seen:
            continue
        seen.add(id(mesh))
        for i in range(len(mesh.materials)):
            mesh.materials[i] = new_mat
        swapped += 1
    return swapped


# ── Operator: Spawn N wheels at bounding-box corners ─────────────────────────

def _body_wheel_positions(body_obj, n: int):
    """
    Return n body-local Blender-space positions for wheel hub placement.

    Blender axis convention for MM1 cars (from _to_blender_pos):
      Blender X  = game -X  (lateral, left = negative Blender X)
      Blender Y  = game  Z  (forward/rear — car faces +Y in Blender)
      Blender Z  = game  Y  (up)

    So front/rear separation is along Blender Y, left/right along Blender X,
    and height (wheel ground level) is along Blender Z.

    n=4 → FL, FR, RL, RR
    n=6 → FL, FM, FR, RL, RM, RR  (trucks / buses)

    Returns positions in body-local space (ready to assign to obj.location
    when the wheel is parented to body with identity parent-inverse).
    """

    # Bounding box corners in body-LOCAL space (bound_box is always local)
    corners_local = [mathutils.Vector(c) for c in body_obj.bound_box]

    xs = [c.x for c in corners_local]
    ys = [c.y for c in corners_local]   # Blender Y = game forward/rear
    zs = [c.z for c in corners_local]   # Blender Z = game up

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_ground     = min(zs)              # bottom of bbox = wheel centre height

    # Inset slightly from corners so wheels aren't flush with the edge
    inset_x = (x_max - x_min) * 0.05
    inset_y = (y_max - y_min) * 0.08

    # Blender X is negated game X: x_max side = game left, x_min side = game right
    # Blender Y maps to game Z: y_min = game front (game -Z), y_max = game rear (+Z)
    gl = x_max - inset_x   # game left  (Blender +X)
    gr = x_min + inset_x   # game right (Blender -X)
    fy = y_min + inset_y   # front (Blender -Y = game -Z front)
    ry = y_max - inset_y   # rear  (Blender +Y = game +Z rear)

    # Wheel order matches MM1 convention: 0=FL, 1=FR, 2=RR, 3=RL
    if n == 4:
        return [
            mathutils.Vector((gl, fy, z_ground)),  # 0 front-left
            mathutils.Vector((gr, fy, z_ground)),  # 1 front-right
            mathutils.Vector((gr, ry, z_ground)),  # 2 rear-right
            mathutils.Vector((gl, ry, z_ground)),  # 3 rear-left
        ]
    elif n == 6:
        mid_y = (fy + ry) * 0.5
        return [
            mathutils.Vector((gl, fy,    z_ground)),  # 0 front-left
            mathutils.Vector((gr, fy,    z_ground)),  # 1 front-right
            mathutils.Vector((gl, mid_y, z_ground)),  # 2 mid-left
            mathutils.Vector((gr, mid_y, z_ground)),  # 3 mid-right
            mathutils.Vector((gr, ry,    z_ground)),  # 4 rear-right
            mathutils.Vector((gl, ry,    z_ground)),  # 5 rear-left
        ]
    else:
        # Generic: evenly spaced along Y axis (forward/rear), alternating left/right
        positions = []
        for i in range(n):
            t  = i / max(n - 1, 1)
            y  = fy + t * (ry - fy)
            bx = gl if (i % 2 == 0) else gr
            positions.append(mathutils.Vector((bx, y, z_ground)))
        return positions

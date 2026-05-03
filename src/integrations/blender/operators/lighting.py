"""
Lighting operators — apply MM1 lighting configs to the Blender world.

Source: decompiled mmCullCity::InitTimeOfDayAndWeather

Key facts from the decompiled code:
  - SunHeading defaults 0.0, Fill1Heading -2.5, Fill2Heading 2.5 (radians)
  - Fill1Pitch defaults 0.45, Fill2Pitch 0.5 (radians)
  - SunPitch is hardcoded per TimeOfDay (not from the CSV default):
      Morning=0 → 0.7 rad (~40°)
      Noon=1    → 1.3962635 rad (~80°, nearly overhead)
      Evening=2 → 2.6179938 rad (~150°, low opposite side)
      Night=3   → (uses same 2.6179938 as Evening before switch)
  - All of the above are OVERRIDDEN if a matching row exists in lighting.csv
    (our LIGHTING.txt already has those overrides — they match).
  - SkyColor (camera background) comes from mmEnvSetup struct, not the CSV.
    We approximate it from the fog colour since we don't have the struct data.
  - Night + Evening: ShowLights=1 (dynamic lights visible, additive glow on).
  - Morning: sky tinted 0xC0C0C0 (grey).
  - Noon: agiMeshLighterMin=0.75 (brighter minimum light on meshes).

Viewport: lighting only shows in Material Preview or Rendered mode.
_apply_lighting() switches to Material Preview with use_scene_world=True.
"""
import math
import bpy
from pathlib import Path

from src.constants.folder import Folder


# ── Data ─────────────────────────────────────────────────────────────────────

TIME_ITEMS = [
    ("0", "Morning", ""),
    ("1", "Noon",    ""),
    ("2", "Evening", ""),
    ("3", "Night",   ""),
]

WEATHER_ITEMS = [
    ("0", "Clear",  ""),
    ("1", "Cloudy", ""),
    ("2", "Rain",   ""),
    ("3", "Snow",   ""),
]

_TIME_LABELS    = {0: "Morning", 1: "Noon", 2: "Evening", 3: "Night"}
_WEATHER_LABELS = {0: "Clear", 1: "Cloudy", 2: "Rain", 3: "Snow"}

# Hardcoded SunPitch values from the switch statement in the decompiled code.
# These are the defaults before the CSV override (our CSV matches these).
_SUN_PITCH_DEFAULT = {
    0: 0.7,          # Morning  (~40°, low sun)
    1: 1.3962635,    # Noon     (~80°, nearly overhead)
    2: 2.6179938,    # Evening  (~150°, low on opposite side)
    3: 2.6179938,    # Night    (same as evening — sun below horizon)
}

# Sky background colour per TimeOfDay from mmSky::Color / BGColor
# Morning: 0xFFC0C0C0 (grey), others: default white/unset → we derive from fog
_SKY_TINT = {
    0: (0.75, 0.75, 0.75),  # Morning: grey (0xC0C0C0 / 255)
    1: None,                 # Noon: use fog colour
    2: None,                 # Evening: use fog colour
    3: None,                 # Night: use fog colour
}

# Minimum mesh lighter per TimeOfDay (agiMeshLighterMin)
_MESH_LIGHTER_MIN = {
    0: 0.5,   # Morning
    1: 0.75,  # Noon (brighter)
    2: 0.5,   # Evening
    3: 0.5,   # Night
}

# Whether dynamic/additive glow lights are active (ShowLights)
_SHOW_LIGHTS = {0: False, 1: False, 2: True, 3: True}


class _LightingEntry:
    __slots__ = (
        "time_of_day", "weather",
        "sun_heading", "sun_pitch", "sun_color",
        "fill1_heading", "fill1_pitch", "fill1_color",
        "fill2_heading", "fill2_pitch", "fill2_color",
        "ambient_color",
        "fog_end", "fog_color",
        "shadow_alpha", "shadow_color",
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _parse_lighting_txt(path: Path):
    entries = []
    cur = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if line == "LIGHTING":
                cur = {}
            elif ":" in line:
                key, _, val = line.partition(":")
                cur[key.strip()] = val.strip()
                if "Shadow Color" in cur:
                    def _rgb(s):
                        s = s.strip("()")
                        return tuple(float(x.strip()) for x in s.split(","))

                    entries.append(_LightingEntry(
                        time_of_day   = int(cur["Time of Day"]),
                        weather       = int(cur["Weather"]),
                        sun_heading   = float(cur["Sun Heading"]),
                        sun_pitch     = float(cur["Sun Pitch"]),
                        sun_color     = _rgb(cur["Sun Color"]),
                        fill1_heading = float(cur["Fill 1 Heading"]),
                        fill1_pitch   = float(cur["Fill 1 Pitch"]),
                        fill1_color   = _rgb(cur["Fill 1 Color"]),
                        fill2_heading = float(cur["Fill 2 Heading"]),
                        fill2_pitch   = float(cur["Fill 2 Pitch"]),
                        fill2_color   = _rgb(cur["Fill 2 Color"]),
                        ambient_color = _rgb(cur["Ambient Color"]),
                        fog_end       = float(cur["Fog End"]),
                        fog_color     = _rgb(cur["Fog Color"]),
                        shadow_alpha  = float(cur["Shadow Alpha"]),
                        shadow_color  = _rgb(cur["Shadow Color"]),
                    ))
                    cur = {}
    return entries


_LIGHTING_CACHE: list | None = None

def _get_lighting_table() -> list:
    global _LIGHTING_CACHE
    if _LIGHTING_CACHE is None:
        txt = Folder.BASE / "docs" / "game_formats" / "lighting" / "LIGHTING.txt"
        _LIGHTING_CACHE = _parse_lighting_txt(txt) if txt.exists() else []
    return _LIGHTING_CACHE


def _lookup(time_of_day: int, weather: int) -> "_LightingEntry | None":
    for e in _get_lighting_table():
        if e.time_of_day == time_of_day and e.weather == weather:
            return e
    return None


# ── Viewport ──────────────────────────────────────────────────────────────────

def _set_viewport_material_preview() -> None:
    """Switch every 3D view to Material Preview with world enabled."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                space.shading.type            = "MATERIAL"
                space.shading.use_scene_world = True


# ── Sky mesh ──────────────────────────────────────────────────────────────────

_SKY_OBJ_NAME = "MMSKY"
_SKY_BMS_PATH = Folder.BASE / "resources" / "editor" / "MESHES" / "MISC" / "MMSKY.BMS"


def load_sky_mesh() -> bool:
    """Load MMSKY.BMS as a large background sky dome. Returns True on success."""
    if not _SKY_BMS_PATH.exists():
        print(f"[Lighting] MMSKY.BMS not found at {_SKY_BMS_PATH}")
        return False

    existing = bpy.data.objects.get(_SKY_OBJ_NAME)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    from src.integrations.blender.modeling.meshes import read_bms, _apply_materials_to_mesh
    import bmesh as _bmesh

    bms_data        = read_bms(_SKY_BMS_PATH)
    points          = bms_data["points"]
    tex_coords      = bms_data["tex_coords"]
    vert_colors     = bms_data.get("vert_colors", [])
    vertex_indices  = bms_data["vertex_indices"]
    surface_indices = bms_data["surface_indices"]
    texture_indices = bms_data["texture_indices"]
    num_surfaces    = bms_data["num_surfaces"]
    flags           = bms_data["flags"]
    texture_names   = bms_data.get("texture_names", [])

    me = bpy.data.meshes.new(_SKY_OBJ_NAME)
    bm = _bmesh.new()
    bm.from_mesh(me)

    uv_layer    = bm.loops.layers.uv.new()
    color_layer = bm.loops.layers.color.new("Col") if vert_colors else None

    for px, py, pz in points:
        bm.verts.new((px, -pz, py))
    bm.verts.ensure_lookup_table()

    for surf_idx in range(num_surfaces):
        base       = surf_idx * 4
        side_count = 4 if surface_indices[base + 3] > 0 else 3
        adj_list   = surface_indices[base : base + side_count]
        pt_indices = [vertex_indices[adj] for adj in adj_list]
        if len(set(pt_indices)) < side_count:
            continue
        try:
            face = bm.faces.new([bm.verts[vi] for vi in pt_indices])
            for xx, loop in enumerate(face.loops):
                adj_idx = adj_list[xx]
                if flags & 1:
                    loop[uv_layer].uv = (tex_coords[adj_idx][0], 1.0 - tex_coords[adj_idx][1])
                if color_layer is not None:
                    loop[color_layer] = vert_colors[adj_idx]
            face.material_index = 0 if texture_indices[surf_idx] == 0 else texture_indices[surf_idx] - 1
            face.smooth = True
        except Exception:
            pass

    for _ in texture_names:
        me.materials.append(None)

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()

    if texture_names:
        _apply_materials_to_mesh(me, texture_names, Folder.Resources.Editor.Textures)

    obj = bpy.data.objects.new(_SKY_OBJ_NAME, me)
    obj["mm_sky"] = True
    obj.scale     = (20.0, 20.0, 20.0)
    obj.hide_select = True

    col_name = "Sky"
    if col_name not in bpy.data.collections:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    else:
        col = bpy.data.collections[col_name]
    col.objects.link(obj)

    print(f"[Lighting] Loaded sky mesh: {_SKY_OBJ_NAME}")
    return True


# ── Blender helpers ───────────────────────────────────────────────────────────

def _ensure_light(name: str, light_type: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj and obj.type == "LIGHT" and obj.data.type == light_type:
        return obj
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
    light_data = bpy.data.lights.new(name=name, type=light_type)
    obj = bpy.data.objects.new(name, light_data)
    bpy.context.scene.collection.objects.link(obj)
    obj["mm_lighting"] = True
    return obj


def _set_sun_rotation(obj: bpy.types.Object, heading: float, pitch: float) -> None:
    """
    Orient a SUN lamp.

    Game: heading=0 → North (+Y), clockwise in radians.
          pitch = elevation above horizon in radians.

    SUN lamp shines in local -Z.
    XYZ euler (π/2 - pitch,  0,  -heading):
      X tilt rotates from zenith (π/2) down by pitch.
      Z spin sets the azimuth (negative = clockwise).
    """
    obj.rotation_mode  = "XYZ"
    obj.rotation_euler = (math.pi / 2.0 - pitch, 0.0, -heading)


def _linear(c: float) -> float:
    return c ** 2.2 if c > 0 else 0.0


def _norm255(rgb):
    return tuple(_linear(v / 255.0) for v in rgb)


def _norm1(rgb):
    return tuple(_linear(v) for v in rgb)


def _apply_lighting(entry: "_LightingEntry") -> None:
    tod  = entry.time_of_day
    scene = bpy.context.scene
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # ── World background colour ───────────────────────────────────────────────
    # Game uses SkyColor (from mmEnvSetup, not the CSV) for the camera BGColor.
    # We don't have the struct data, so:
    #   - Morning: 0xC0C0C0 grey (confirmed from decompiled code)
    #   - Others: use fog colour as the sky/horizon tint (closest approximation)
    sky_tint = _SKY_TINT.get(tod)
    if sky_tint is not None:
        bg_r, bg_g, bg_b = [_linear(v) for v in sky_tint]
    else:
        bg_r, bg_g, bg_b = _norm255(entry.fog_color)

    bg_node = nodes.get("Background")
    if bg_node is None:
        nodes.clear()
        out     = nodes.new("ShaderNodeOutputWorld")
        bg_node = nodes.new("ShaderNodeBackground")
        out.location     = (300, 0)
        bg_node.location = (0, 0)
        links.new(bg_node.outputs["Background"], out.inputs["Surface"])

    bg_node.inputs["Color"].default_value    = (bg_r, bg_g, bg_b, 1.0)
    bg_node.inputs["Strength"].default_value = 1.0

    # Store fog colour in a helper node for compositing reference
    world["mm_fog_color"] = list(entry.fog_color)
    fog_node = nodes.get("MM_FogColor")
    if fog_node is None:
        fog_node       = nodes.new("ShaderNodeRGB")
        fog_node.name  = "MM_FogColor"
        fog_node.label = "Fog Color (MM1)"
        fog_node.location = (-300, -200)
    fr, fg, fb = _norm255(entry.fog_color)
    fog_node.outputs[0].default_value = (fr, fg, fb, 1.0)

    # ── Sun energy — scaled by MeshLighterMin and ShowLights context ──────────
    # Noon has the highest minimum (0.75), night/evening enable additive glow.
    mesh_min   = _MESH_LIGHTER_MIN.get(tod, 0.5)
    show_lights = _SHOW_LIGHTS.get(tod, False)

    # Base energies tuned to approximate game feel:
    #   sun is dominant in daytime, ambient carries night scenes.
    sun_energy  = 3.0 * (mesh_min / 0.5)      # scales with lighter minimum
    fill_energy = 1.5 if not show_lights else 0.6  # reduce fills when glow active

    # ── Sun ───────────────────────────────────────────────────────────────────
    sun = _ensure_light("MM_Sun", "SUN")
    _set_sun_rotation(sun, entry.sun_heading, entry.sun_pitch)
    sr, sg, sb = _norm1(entry.sun_color)
    sun.data.color  = (sr, sg, sb)
    sun.data.energy = sun_energy
    sun.data.angle  = math.radians(0.5)

    # ── Fill 1 ────────────────────────────────────────────────────────────────
    f1 = _ensure_light("MM_Fill1", "SUN")
    _set_sun_rotation(f1, entry.fill1_heading, entry.fill1_pitch)
    f1r, f1g, f1b = _norm1(entry.fill1_color)
    f1.data.color  = (f1r, f1g, f1b)
    f1.data.energy = fill_energy
    f1.data.angle  = math.radians(30.0)

    # ── Fill 2 ────────────────────────────────────────────────────────────────
    f2 = _ensure_light("MM_Fill2", "SUN")
    _set_sun_rotation(f2, entry.fill2_heading, entry.fill2_pitch)
    f2r, f2g, f2b = _norm1(entry.fill2_color)
    f2.data.color  = (f2r, f2g, f2b)
    f2.data.energy = fill_energy * 0.67
    f2.data.angle  = math.radians(30.0)

    # ── Ambient — add as extra low-energy sun from above to simulate it ───────
    # (Blender world Background node already carries the sky colour;
    #  ambient_color from the CSV is the mesh ambient fill, approximated here
    #  by boosting world strength slightly.)
    ar, ag, ab = _norm1(entry.ambient_color)
    ambient_lum = (ar + ag + ab) / 3.0
    bg_node.inputs["Strength"].default_value = 0.5 + ambient_lum * 2.0

    # ── Mist ──────────────────────────────────────────────────────────────────
    scene.world.mist_settings.use_mist = True
    scene.world.mist_settings.start    = 5.0
    scene.world.mist_settings.depth    = max(entry.fog_end - 5.0, 1.0)
    scene.world.mist_settings.falloff  = "LINEAR"

    # ── Sky dome tint ─────────────────────────────────────────────────────────
    _tint_sky(entry.fog_color, tod)

    # ── Switch viewport to show the world ────────────────────────────────────
    _set_viewport_material_preview()


def _tint_sky(fog_color_255, tod: int) -> None:
    """Tint the MMSKY vertex colours to match the current sky background."""
    obj = bpy.data.objects.get(_SKY_OBJ_NAME)
    if obj is None or obj.type != "MESH":
        return
    mesh = obj.data
    col_layer = (mesh.vertex_colors.get("Col")
                 or (mesh.vertex_colors[0] if mesh.vertex_colors else None))
    if col_layer is None:
        return
    sky_tint = _SKY_TINT.get(tod)
    if sky_tint is not None:
        r, g, b = sky_tint
    else:
        r, g, b = [min(1.0, v / 255.0) for v in fog_color_255]
    for loop_col in col_layer.data:
        loop_col.color = (r, g, b, 1.0)
    mesh.update()


# ── Update callback ───────────────────────────────────────────────────────────

def _update_lighting(self, context) -> None:
    tod  = int(context.scene.lt_time_of_day)
    wthr = int(context.scene.lt_weather)
    entry = _lookup(tod, wthr)
    if entry:
        _apply_lighting(entry)


# ── Operators ─────────────────────────────────────────────────────────────────

class LIGHTING_OT_Apply(bpy.types.Operator):
    """Apply MM1 lighting for the selected Time and Weather to the Blender world"""
    bl_idname = "lighting.apply"
    bl_label  = "Apply Lighting"

    def execute(self, context):
        tod  = int(context.scene.lt_time_of_day)
        wthr = int(context.scene.lt_weather)
        entry = _lookup(tod, wthr)
        if entry is None:
            self.report({"ERROR"}, "No lighting entry found for this combination")
            return {"CANCELLED"}
        _apply_lighting(entry)
        tl = _TIME_LABELS.get(tod, str(tod))
        wl = _WEATHER_LABELS.get(wthr, str(wthr))
        self.report({"INFO"}, f"MM1 Lighting applied: {tl} / {wl}")
        return {"FINISHED"}


class LIGHTING_OT_Clear(bpy.types.Operator):
    """Remove MM1 lighting objects and restore default solid viewport"""
    bl_idname = "lighting.clear"
    bl_label  = "Clear MM1 Lights"

    def execute(self, context):
        removed = 0
        for name in ("MM_Sun", "MM_Fill1", "MM_Fill2"):
            obj = bpy.data.objects.get(name)
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)
                removed += 1
        if context.scene.world:
            context.scene.world.mist_settings.use_mist = False
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    for space in area.spaces:
                        if space.type == "VIEW_3D":
                            space.shading.type       = "SOLID"
                            space.shading.light      = "FLAT"
                            space.shading.color_type = "TEXTURE"
        self.report({"INFO"}, f"Removed {removed} MM1 light(s)")
        return {"FINISHED"}


class LIGHTING_OT_LoadSky(bpy.types.Operator):
    """Load MMSKY.BMS as the background sky dome"""
    bl_idname = "lighting.load_sky"
    bl_label  = "Load Sky Mesh"

    def execute(self, context):
        if load_sky_mesh():
            self.report({"INFO"}, "Sky mesh loaded")
        else:
            self.report({"WARNING"}, f"MMSKY.BMS not found at {_SKY_BMS_PATH}")
        return {"FINISHED"}


LIGHTING_EDITOR_CLASSES = [
    LIGHTING_OT_Apply,
    LIGHTING_OT_Clear,
    LIGHTING_OT_LoadSky,
]

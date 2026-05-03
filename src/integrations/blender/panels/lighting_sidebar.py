"""
Lighting Editor sidebar panel.  Tab: "Lighting"  (VIEW_3D → N-panel)

Lets you pick Time of Day and Weather and apply the corresponding MM1
lighting preset to the Blender world (sun, fill lights, ambient, fog).
"""
import math
import bpy

from src.integrations.blender.operators.lighting import (
    TIME_ITEMS, WEATHER_ITEMS,
    _lookup, _TIME_LABELS, _WEATHER_LABELS,
)

_PANEL_CATEGORY = "Lighting"

_TIME_ICONS = {
    "0": "LIGHT_SUN",
    "1": "LIGHT_SUN",
    "2": "LIGHT_AREA",
    "3": "LIGHT_HEMI",
}
_WEATHER_ICONS = {
    "0": "SEQUENCE_COLOR_04",  # green = clear
    "1": "SEQUENCE_COLOR_06",  # grey  = cloudy
    "2": "SEQUENCE_COLOR_05",  # blue  = rain
    "3": "SEQUENCE_COLOR_03",  # white = snow
}


def _color_swatch(layout, rgb_01, label: str):
    """Draw a tiny colour preview row."""
    row = layout.row(align=True)
    row.label(text=label)
    # FloatVectorProperty drawn inline as a colour button
    sub = row.row()
    sub.scale_x = 0.5
    # We can't draw a raw tuple as a colour, so just show the hex text
    r, g, b = [min(1.0, max(0.0, v)) for v in rgb_01]
    hex_str  = "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))
    sub.label(text=hex_str)


def _deg(rad: float) -> str:
    return f"{math.degrees(rad):.0f}°"


class VIEW3D_PT_LightingEditor(bpy.types.Panel):
    bl_label       = "Lighting Editor"
    bl_idname      = "VIEW3D_PT_lighting_editor"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Selectors ─────────────────────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Time of Day", icon="TIME")
        col.prop(scene, "lt_time_of_day", expand=True)

        layout.separator(factor=0.5)

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Weather", icon="WORLD")
        col.prop(scene, "lt_weather", expand=True)

        layout.separator()

        # ── Apply button ──────────────────────────────────────────────────────
        row = layout.row(align=True)
        row.scale_y = 1.6
        row.operator("lighting.apply", text="Apply Lighting", icon="LIGHT_SUN")

        layout.separator()

        # ── Live preview of the selected config ───────────────────────────────
        tod  = int(scene.lt_time_of_day)
        wthr = int(scene.lt_weather)
        entry = _lookup(tod, wthr)

        if entry is None:
            layout.label(text="No data for this combination", icon="ERROR")
            return

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Config Preview", icon="INFO")

        # Sun
        col.separator(factor=0.5)
        col.label(text=f"  Sun:  heading {_deg(entry.sun_heading)},  pitch {_deg(entry.sun_pitch)}")
        _color_row(col, entry.sun_color, "  Sun color:", scale_01=True)

        # Fill 1
        col.separator(factor=0.5)
        col.label(text=f"  Fill 1:  heading {_deg(entry.fill1_heading)},  pitch {_deg(entry.fill1_pitch)}")
        _color_row(col, entry.fill1_color, "  Fill 1 color:", scale_01=True)

        # Fill 2
        col.separator(factor=0.5)
        col.label(text=f"  Fill 2:  heading {_deg(entry.fill2_heading)},  pitch {_deg(entry.fill2_pitch)}")
        _color_row(col, entry.fill2_color, "  Fill 2 color:", scale_01=True)

        # Ambient
        col.separator(factor=0.5)
        _color_row(col, entry.ambient_color, "  Ambient:", scale_01=True)

        # Fog
        col.separator(factor=0.5)
        col.label(text=f"  Fog end:  {entry.fog_end:.0f} units")
        _color_row(col, entry.fog_color, "  Fog color:", scale_01=False)

        # Shadow
        col.separator(factor=0.5)
        col.label(text=f"  Shadow α:  {entry.shadow_alpha:.0f}")
        _color_row(col, entry.shadow_color, "  Shadow color:", scale_01=False)


class VIEW3D_PT_LightingEditorTools(bpy.types.Panel):
    bl_label       = "Tools"
    bl_idname      = "VIEW3D_PT_lighting_editor_tools"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = _PANEL_CATEGORY
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("lighting.load_sky",  text="Load Sky Mesh",  icon="WORLD_DATA")
        col.operator("lighting.clear",     text="Clear MM1 Lights", icon="TRASH")

        layout.separator()
        layout.label(text="Active MM1 Lights:", icon="OUTLINER_OB_LIGHT")
        col = layout.column(align=True)
        for name in ("MM_Sun", "MM_Fill1", "MM_Fill2"):
            obj = bpy.data.objects.get(name)
            row = col.row(align=True)
            if obj:
                row.label(text=f"  {name}", icon="LIGHT_SUN")
                row.label(text=f"E={obj.data.energy:.1f}")
            else:
                row.alert = True
                row.label(text=f"  {name}  (not in scene)", icon="SEQUENCE_COLOR_01")

        layout.separator()
        layout.label(text="Mist / Fog:", icon="MOD_SMOKE")
        world = context.scene.world
        if world:
            ms = world.mist_settings
            col = layout.column(align=True)
            col.prop(ms, "use_mist",  text="Enable Mist")
            if ms.use_mist:
                col.prop(ms, "start",  text="Start")
                col.prop(ms, "depth",  text="Depth")
                col.prop(ms, "falloff", text="Falloff")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _color_row(col, rgb, label: str, scale_01: bool):
    """Show a colour as a hex label."""
    if scale_01:
        r, g, b = [min(1.0, max(0.0, v)) for v in rgb]
    else:
        r, g, b = [min(1.0, max(0.0, v / 255.0)) for v in rgb]
    row = col.row(align=True)
    row.label(text=label)
    row.label(text="#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255)))


# ── Registration ──────────────────────────────────────────────────────────────

LIGHTING_EDITOR_PANEL_CLASSES = [
    VIEW3D_PT_LightingEditor,
    VIEW3D_PT_LightingEditorTools,
]

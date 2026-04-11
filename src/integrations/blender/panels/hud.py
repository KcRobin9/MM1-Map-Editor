import bpy
from typing import NamedTuple

from src.constants.color import Color


class HudEntry(NamedTuple):
    color: str
    label: str


HUD_IMPORT: list[HudEntry] = [
    HudEntry(Color.ROAD,         "Road"),
    HudEntry(Color.GRASS,        "Grass"),
    HudEntry(Color.WATER,        "Water"),
    HudEntry(Color.SNOW,         "Snow"),
    HudEntry(Color.WOOD,         "Wood"),
    HudEntry(Color.ORANGE,       "Orange"),
    HudEntry(Color.RED_LIGHT,    "Light Red"),
    HudEntry(Color.RED_DARK,     "Dark Red"),
    HudEntry(Color.YELLOW_LIGHT, "Light Yellow"),
]

# Enum items for the HUD color dropdown (identifier = hex color string)
HUD_COLOR_ITEMS = [
    (entry.color, entry.label, "")
    for entry in HUD_IMPORT
]

HUD_EXPORT: dict[str, str] = {
    # Color.ROAD:         "Color.ROAD",
    Color.WOOD:         "Color.WOOD",
    Color.SNOW:         "Color.SNOW",
    Color.WATER:        "Color.WATER",
    Color.GRASS:        "Color.GRASS",
    Color.RED_DARK:     "Color.RED_DARK",
    Color.ORANGE:       "Color.ORANGE",
    Color.RED_LIGHT:    "Color.RED_LIGHT",
    Color.YELLOW_LIGHT: "Color.YELLOW_LIGHT",
}


def set_hud_color(color, obj: bpy.types.Object) -> None:
    """Set the hud_color enum on obj. Silently ignores None, ints, or unrecognised values."""
    if not isinstance(color, str):
        return
    valid = {item[0] for item in HUD_COLOR_ITEMS}
    if color in valid:
        obj.hud_color = color


# Legacy panel kept only so existing registrations don't break at import time.
# The actual HUD UI lives inside VIEW3D_PT_MapEditorCell in sidebar.py.
class OBJECT_PT_HUDColorPanel(bpy.types.Panel):
    bl_label       = "HUD Type"
    bl_idname      = "OBJECT_PT_hud_type"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "object"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context) -> None:
        layout = self.layout
        obj    = context.active_object
        if not obj:
            layout.label(text="No active object")
            return
        layout.prop(obj, "hud_color", text="HUD")

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


def set_hud_color(color: str, obj: bpy.types.Object) -> None:
    for i, entry in enumerate(HUD_IMPORT):
        if entry.color == color:
            obj.hud_color_index = i
            return


def hud_color_index_update(self, context) -> None:
    new_state = [False] * len(HUD_IMPORT)
    if 0 <= self.hud_color_index < len(HUD_IMPORT):
        new_state[self.hud_color_index] = True
    self.hud_colors = new_state


def hud_colors_update(self, context) -> None:
    current = self.hud_color_index
    true_indices = [i for i in range(len(HUD_IMPORT)) if self.hud_colors[i]]

    if not true_indices:
        new_state = [False] * len(HUD_IMPORT)
        new_state[current] = True
        self.hud_colors = new_state
        return

    newly_selected = next((i for i in true_indices if i != current), None)
    if newly_selected is not None:
        self.hud_color_index = newly_selected


class OBJECT_PT_HUDColorPanel(bpy.types.Panel):
    bl_label = "HUD Type"
    bl_idname = "OBJECT_PT_hud_type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context) -> None:
        layout = self.layout
        obj = context.active_object

        if not obj:
            layout.label(text="No active object")
            return

        half = len(HUD_IMPORT) // 2 + len(HUD_IMPORT) % 2
        row = layout.row(align=True)
        col = row.column(align=True)

        for i, entry in enumerate(HUD_IMPORT):
            if i == half:
                col = row.column(align=True)
            col.prop(obj, "hud_colors", index=i, text=entry.label, toggle=True)
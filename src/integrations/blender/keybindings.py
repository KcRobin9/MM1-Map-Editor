import bpy
from functools import partial
from typing import Any, Dict, Optional

from src.constants.misc import Executable
from src.constants.keyboard import Key, KeyEvent, KeyModifier

from src.helpers.main import is_process_running


def create_keybinding(keymap, operator: str, key: str, modifier: Optional[Dict] = None, properties: Optional[Dict[str, Any]] = None) -> None:
    modifier = modifier or {}
    kmi = keymap.keymap_items.new(operator, key, KeyEvent.PRESS, **modifier)

    if properties:
        for prop_name, prop_value in properties.items():
            setattr(kmi.properties, prop_name, prop_value)


def setup_export_keybindings(bind_func) -> None:
    # Ctrl+Shift+E — export selected polygons
    bind_func("object.export_polygons", Key.E, KeyModifier.CTRL_SHIFT, {"select_all": False})
    # Ctrl+Alt+E  — export all polygons
    bind_func("object.export_polygons", Key.E, KeyModifier.CTRL_ALT,   {"select_all": True})


def set_blender_keybinding() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if not kc:
        return

    km = kc.keymaps.new(name="Object Mode", space_type="EMPTY")

    bind = partial(create_keybinding, km)

    setup_export_keybindings(bind)

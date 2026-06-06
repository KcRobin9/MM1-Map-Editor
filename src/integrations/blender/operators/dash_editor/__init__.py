"""Dash Editor package — load / edit / export the MM1 cockpit dash in Blender.

The cockpit ("Driver") view is mmDashView: seven BMS meshes ({CAR}_DASH/) placed by
a {CAR}.MMDASHVIEW config, viewed through a {CAR}_DASH.POVCAMCS camera. This package
loads them as a live Blender assembly, tunes the gauges/placement/camera, and packs
the result into a standalone override AR. Mirrors the car_editor package layout; the
public surface below is what inits.py and the sidebar import.
"""
from src.integrations.blender.operators.dash_editor.constants import _DASH_TAG
from src.integrations.blender.operators.dash_editor.common import (
    is_dash_obj, get_dash_objects, get_dash_root, get_dash_part, list_dash_cars,
    list_dash_textures, dash_texture_label, update_de_preview, update_de_gauge, update_de_reskin_texture,
)
from src.integrations.blender.operators.dash_editor.operators import DASH_EDITOR_CLASSES


_DASH_CAR_CACHE = []
_DASH_TEX_CACHE = []


def get_dash_car_items(self, context):
    """EnumProperty items: every car that has a {CAR}_DASH/DASH.BMS.

    Cached in a module-global so Blender keeps the item strings alive (returning a
    fresh list each call risks string GC corruption — same pattern as the Car
    Editor's wheel-style enum)."""
    from src.constants.car_assets import Vehicle
    if _DASH_CAR_CACHE:
        return _DASH_CAR_CACHE
    cars = list_dash_cars()
    items = [(c, Vehicle.label(c), f"Edit the {Vehicle.label(c)} dash") for c in cars]
    _DASH_CAR_CACHE[:] = items or [("VPMUSTANG99", "Ford Mustang", "")]
    return _DASH_CAR_CACHE


def get_dash_texture_items(self, context):
    """EnumProperty items: every dash texture from every car (reskin dropdown).
    Cached (see get_dash_car_items for why)."""
    if _DASH_TEX_CACHE:
        return _DASH_TEX_CACHE
    items = [(s, dash_texture_label(s), f"Apply {s}") for s in list_dash_textures()]
    _DASH_TEX_CACHE[:] = items or [("VW_DASHM", "Beetle · Dash Middle", "")]
    return _DASH_TEX_CACHE


__all__ = [
    "is_dash_obj", "get_dash_objects", "get_dash_root", "get_dash_part",
    "list_dash_cars", "get_dash_car_items", "get_dash_texture_items",
    "update_de_preview", "update_de_gauge", "update_de_reskin_texture",
    "_DASH_TAG", "DASH_EDITOR_CLASSES",
]

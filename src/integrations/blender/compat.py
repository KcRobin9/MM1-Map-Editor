"""
Blender cross-version compatibility helpers.

Blender renames/removes Python API enums between releases (e.g. the panel status icons:
SEQUENCE_COLOR_* in <=4.3 became STRIP_COLOR_* in 4.5). Hardcoding either name breaks the other
version. `icon()` resolves the first name the RUNNING Blender actually supports, so panels work on
any version without asking users to upgrade.

Usage:
    from src.integrations.blender.compat import ICON_ON, ICON_OFF, ICON_ALT, icon
    row.label(text="...", icon=ICON_ON)
    row.label(text="...", icon=icon("STRIP_COLOR_09", "SEQUENCE_COLOR_09", default="DOT"))

Also exposes BLENDER_VERSION for explicit `if BLENDER_VERSION >= (5, 0, 0):` shims later.
"""
_AVAILABLE = None


def _available():
    global _AVAILABLE
    if _AVAILABLE is None:
        try:
            import bpy
            _AVAILABLE = {i.identifier for i in
                          bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items}
        except Exception:
            _AVAILABLE = set()          # headless / very old Blender: fall back to defaults
    return _AVAILABLE


def icon(*candidates: str, default: str = "NONE") -> str:
    """First icon name supported by the running Blender, else `default` (always valid: 'NONE')."""
    avail = _available()
    for c in candidates:
        if c in avail:
            return c
    return default if (default in avail or default == "NONE") else "NONE"


try:
    import bpy as _bpy
    BLENDER_VERSION = tuple(_bpy.app.version)
except Exception:
    BLENDER_VERSION = (0, 0, 0)

# Shared status icons used across the editor panels (green dot / red dot / blue dot in 4.x themes).
ICON_ON  = icon("STRIP_COLOR_04", "SEQUENCE_COLOR_04", default="CHECKMARK")   # green: present/ok
ICON_OFF = icon("STRIP_COLOR_01", "SEQUENCE_COLOR_01", default="BLANK1")      # red: missing/off
ICON_ALT = icon("STRIP_COLOR_05", "SEQUENCE_COLOR_05", default="DOT")         # blue: info/special

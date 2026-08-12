"""
Periodic polygon auto-export, so a Blender crash costs minutes instead of a session.

Set `time_auto_save` in src/USER/settings/blender.py to the interval in MINUTES (0 disables it).
Each tick writes a NEW timestamped file to blender_export/autosave/, the same text Export Polygons
produces, so any of them can be pasted straight back into the map editor.
"""
from pathlib import Path

import bpy

from src.constants.constants import current_time_formatted
from src.constants.folder import Folder
from src.constants.file_formats import FileType
from src.integrations.blender.export_polygons import export_formatted_polygons
from src.integrations.blender.utils import get_polygon_objects
from src.USER.settings.blender import time_auto_save, keep_auto_saves

SECONDS_PER_MINUTE = 60
EXPORT_PREFIX = "Polygons_"

# Blender holds an in-progress mesh edit in its own buffer, so a polygon read mid-edit still reports
# the pre-edit vertices. Those ticks are skipped and the next one picks the work up.
EDIT_MODES = {"EDIT_MESH", "EDIT_CURVE", "EDIT_ARMATURE", "EDIT_TEXT", "EDIT_METABALL"}


def _interval_seconds() -> int:
    # Floored at one minute so a stray 0.5 cannot spin the timer
    return max(1, int(time_auto_save)) * SECONDS_PER_MINUTE


def _prune_exports() -> None:
    if not keep_auto_saves:
        return

    # Ordered by modification time, NOT by name: the stamp is %Y_%d_%m, so day sorts ahead of month
    # and 31 January would come out newer than 1 February, deleting the wrong files.
    exports = sorted(Folder.Blender.AutoSave.glob(f"{EXPORT_PREFIX}*{FileType.TEXT}"),
                     key=lambda path: path.stat().st_mtime)

    for stale in exports[:-int(keep_auto_saves)]:
        stale.unlink(missing_ok=True)


# Only reads the scene. The Export Polygons operator applies object transforms and clears the
# selection to reach world space; doing either on a timer would fight the user, so format_vertices
# multiplies by matrix_world instead and nothing here is mutated.
def save_now() -> Path | None:
    if bpy.context.mode in EDIT_MODES:
        return None

    polygons = get_polygon_objects(bpy.context.scene.objects, sort=True)
    if not polygons:
        return None

    # One unexportable object must not cost the other few thousand their backup, so failures are
    # skipped rather than raised. A mesh named like a polygon but missing the editor's custom
    # properties is the usual cause (hand-created, or made before the add-on registered them).
    blocks = []
    skipped = 0
    for obj in polygons:
        try:
            blocks.append(export_formatted_polygons(obj))
        except Exception:
            skipped += 1

    if not blocks:
        return None

    if skipped:
        print(f"[Auto-Save] {skipped} polygon(s) could not be exported and were left out")

    Folder.Blender.AutoSave.mkdir(parents=True, exist_ok=True)
    export_file = Folder.Blender.AutoSave / f"{EXPORT_PREFIX}{current_time_formatted()}{FileType.TEXT}"
    export_file.write_text("\n".join(blocks), encoding="utf-8")

    _prune_exports()
    print(f"[Auto-Save] {len(blocks)} polygons -> {export_file.name}")

    return export_file


# Blender UNREGISTERS a timer whose callback raises, so anything escaping here would silently switch
# auto-save off for the rest of the session --- exactly when it is most needed.
def _auto_save_timer() -> float:
    try:
        save_now()
    except Exception as error:
        print(f"[Auto-Save] tick failed: {error}")

    return _interval_seconds()


def initialize_auto_save() -> None:
    if bpy.app.timers.is_registered(_auto_save_timer):
        bpy.app.timers.unregister(_auto_save_timer)

    if not time_auto_save:
        return

    bpy.app.timers.register(_auto_save_timer, first_interval=_interval_seconds(), persistent=True)
    print(f"[Auto-Save] every {int(time_auto_save)} min -> {Folder.Blender.AutoSave}")


def shutdown_auto_save() -> None:
    if bpy.app.timers.is_registered(_auto_save_timer):
        bpy.app.timers.unregister(_auto_save_timer)

"""
Resolves effective runtime settings by applying FAST mode overrides on top of
the user's saved values.  Import from this module instead of from the
individual settings files — user values are never mutated.
"""

# ── Raw user settings ──────────────────────────────────────────────────────────
from src.USER.settings.main import (
    MAP_NAME, MAP_FILENAME, MAP_SPEC_FILE,
    EXTRA_TEXTURE_DIRS,
    play_game, delete_shop,
    set_bridges, set_props, set_facades, set_physics, set_animations,
    set_texture_sheet, set_music,
    set_minimap, minimap_outline_color,
    set_ai_streets, set_reverse_ai_streets,
    set_lars_race_maker, set_cruise_start,
    cruise_start_position,
    randomize_textures, random_textures,
    disable_progress_bar,
    set_player_data,
    set_races, set_cops_and_robbers, set_lighting,
)

from src.USER.settings.advanced import (
    no_ui, no_ui_type, no_ai,
    less_logs, more_logs,
    lower_portals, empty_portals,
    set_dlp, fix_faulty_quads, deduplicate_bound_vertices, set_hitid_grid,
    inherit_city, inherit_hitid, inherit_cells, inherit_portals, inherit_bounds, inherit_bms,
    inherit_ai, inherit_props, inherit_facades, inherit_gizmo, inherit_extrema,
)

from src.USER.settings.debug import (
    debug_props, debug_meshes, debug_bounds, debug_facades, debug_physics,
    debug_portals, debug_lighting, debug_minimap, debug_minimap_id,
    auto_debug,
)

from src.USER.settings.blender import (
    time_auto_save, keep_auto_saves,
    load_target_model, load_all_textures,
    visualize_props, visualize_facades, visualize_bridges, prop_bms_folder, prop_car_wheels, prop_car_lights,
    MM2_BLENDER_VIZ, MM2_PROPS_MERGED, MM2_EXPORT_CITY_FOLDER, MM2_SAVE_RELOAD_AFTER_BUILD,
)

from src.USER.settings.fast import (FAST_AR_ONLY, BLENDER_ONLY, FAST_BLENDER_ONLY,
                                    FAST_AR_PLUS_BLENDER, CONNECT_BLENDER_ONLY)

# ── Fast mode overrides ────────────────────────────────────────────────────────
_fast_ar = FAST_AR_ONLY or FAST_AR_PLUS_BLENDER
_fast_bl = FAST_BLENDER_ONLY or FAST_AR_PLUS_BLENDER
# BLENDER_ONLY skips AR but keeps props/facades — no setting overrides needed

if _fast_ar:
    set_bridges            = False
    set_props              = False
    set_facades            = False
    set_physics            = False
    set_animations         = False
    set_texture_sheet      = True
    set_music              = True
    set_minimap            = False
    minimap_outline_color  = None
    set_ai_streets         = False
    set_reverse_ai_streets = False
    set_lars_race_maker    = False
    set_cruise_start       = False
    randomize_textures     = False
    disable_progress_bar   = True
    set_player_data        = False
    set_races              = False
    set_cops_and_robbers   = False
    set_lighting           = False
    set_dlp                = False
    # empty_portals is intentionally NOT overridden here — the user may want
    # empty_portals = True during fast builds for city round-trip testing.
    # suppress all debug output
    debug_props      = False
    debug_meshes     = False
    debug_bounds     = False
    debug_facades    = False
    debug_physics    = False
    debug_portals    = False
    debug_lighting   = False
    debug_minimap    = False
    debug_minimap_id = False

if _fast_bl:
    visualize_props    = False
    visualize_facades  = False
    visualize_bridges  = False

# CONNECT_BLENDER_ONLY: panels-only session — no .AR, no scene content at all.
# Force every visualization off.
if CONNECT_BLENDER_ONLY:
    visualize_props    = False
    visualize_facades  = False
    visualize_bridges  = False

# ── Derived runtime flag ───────────────────────────────────────────────────────
# True → skip the entire .AR creation pipeline (Blender-only run)
SKIP_AR_CREATION = BLENDER_ONLY or FAST_BLENDER_ONLY or CONNECT_BLENDER_ONLY

# ── Startup banner ─────────────────────────────────────────────────────────────
_ACTIVE_MODE = (
    "CONNECT_BLENDER_ONLY" if CONNECT_BLENDER_ONLY else
    "FAST_AR_ONLY"         if FAST_AR_ONLY         else
    "BLENDER_ONLY"         if BLENDER_ONLY         else
    "FAST_BLENDER_ONLY"    if FAST_BLENDER_ONLY    else
    "FAST_AR_PLUS_BLENDER" if FAST_AR_PLUS_BLENDER else
    None
)

if _ACTIVE_MODE:
    _DESCRIPTIONS = {
        "CONNECT_BLENDER_ONLY": "Panels only      — no .AR, empty scene, all operators/panels ready",
        "FAST_AR_ONLY":         "Fast .AR build  — props/AI/physics/races skipped",
        "BLENDER_ONLY":         "Blender only     — .AR skipped, props & facades loaded",
        "FAST_BLENDER_ONLY":    "Fast Blender     — .AR skipped, props & facades skipped",
        "FAST_AR_PLUS_BLENDER": "Fast AR + Blender — fast .AR, props & facades skipped",
    }
    print(f"\033[93m[FAST MODE] {_ACTIVE_MODE} — {_DESCRIPTIONS[_ACTIVE_MODE]}\033[0m")

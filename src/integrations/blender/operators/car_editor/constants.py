"""Car Editor — constants module (split from the former car_editor.py monolith)."""
import re


# ── Paint-variant helpers ─────────────────────────────────────────────────────

# Textures shared across all cars — not part of any paint variant.
_GENERIC_TEXTURES = frozenset({
    "CARBOTTOM", "VAHEADLIGHT", "VASIGNALUNIT", "VASTOPUNIT", "VACOMP_WHL",
})


# Matches a timestamp suffix appended by a previous export, e.g. "_2026_24_04_2045_05"
_TIMESTAMP_SUFFIX_RE = re.compile(r'_\d{4}_\d{2}_\d{2}_\d{4}_\d{2}$')


# ── Constants ─────────────────────────────────────────────────────────────────

_CAR_COLLECTION = "Car Editor"
_CAR_TAG        = "mm_car_part"


_SIREN_LIGHT_TAGS = {"light_red": "REDLIGHT.BMS", "light_blue": "BLUELIGHT.BMS"}
_SIREN_HOUSING_TAG = "siren_housing"

# Standard car light effect-meshes. Each renders additively in-game (glow/beam)
# and uses the same absolute-vertex / no-OFFSET format as the siren lenses.
#   (tag, output BMS filename, default glow texture, panel label)
_CAR_LIGHT_DEFS = [
    ("light_head",    "HLIGHT_H.BMS", "FXLTGLOW",      "Headlights"),
    ("light_tail",    "TLIGHT.BMS",   "FXLTGLOWRED",   "Tail Lights"),
    ("light_brake",   "BLIGHT.BMS",   "FXLTGLOWRED",   "Brake Lights"),
    ("light_reverse", "RLIGHT.BMS",   "FXLTGLOW",      "Reverse Lights"),
    ("light_signalL", "SLIGHT0.BMS",  "FXLTGLOWAMBER", "Signal Left"),
    ("light_signalR", "SLIGHT1.BMS",  "FXLTGLOWAMBER", "Signal Right"),
]
_CAR_LIGHT_FILE  = {t: f for t, f, _, _ in _CAR_LIGHT_DEFS}
_CAR_LIGHT_TAGS  = [t for t, _, _, _ in _CAR_LIGHT_DEFS]

# Unified registry: every light/siren part tag → its BMS slot filename. Car lights
# and siren lenses share the same export path (absolute verts, no OFFSET) and the
# same colour pipeline (_light_color_value / set_light_color), so one map drives both.
_LIGHT_FILE = {**_CAR_LIGHT_FILE, **_SIREN_LIGHT_TAGS}

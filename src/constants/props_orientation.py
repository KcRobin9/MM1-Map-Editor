from src.constants.props import Prop

# Per-prop rotation offset (degrees) added on top of the user-facing angle
# before the game face vector is computed, and reflected in the Blender display.
#
# The user always works in "logical" compass degrees (NORTH = thin-end / front
# faces north).  This table corrects for however the original artist oriented
# each BMS model.
#
#   90°  — model long-axis is E-W; rotate so thin end faces north
#  180°  — model front is reversed; flip 180° so front faces north
#  270°  — model is both sideways and reversed; combined 90° + 180° flip

PROP_ORIENTATION_OFFSET: dict = {
    # ── Road barriers ────────────────────────────────────────────────────────
    Prop.BARRICADE:             90,   #  4.0 × 0.5  — long axis E-W

    # ── Street furniture ─────────────────────────────────────────────────────
    Prop.BENCH_MALL:            90,   #  2.5 × 0.68 — long axis E-W

    # ── Newspaper boxes ───────────────────────────────────────────────────────
    Prop.NEWSPAPER_BOX_BLUE:   270,
    Prop.NEWSPAPER_BOX_RED:    270,
    Prop.NEWSPAPER_BOX_YELLOW: 270,
    Prop.NEWSPAPER_BOX_BLUE_2: 270,

    # ── Street furniture (phone) ──────────────────────────────────────────────
    Prop.PAYPHONE:             270,   # wall-mount faces away from expected north

    # ── Vehicles & transport ─────────────────────────────────────────────────
    Prop.TRAILER:              270,   # 16.3 × 4.0 — long axis E-W + reversed
    Prop.SAILBOAT:             270,   # flat billboard, single-sided

    # ── Bridges / crossgates ─────────────────────────────────────────────────
    Prop.CROSSGATE:             90,   # 13.2 × 0.1  — arm extends E-W
    Prop.CROSSGATE_SHORT:       90,   #  9.9 × 0.1
    Prop.CROSSGATE_BASE:        90,   #  0.6 × 1.2

    # ── Walls ────────────────────────────────────────────────────────────────
    Prop.WALL_TALL:             90,   #  8.9 × 0.2
    Prop.WALL_TALL_B:           90,   #  8.0 × 0.2
    Prop.WALL_WIDE:             90,   #  4.7 × 0.4
    Prop.WALL_LOW:              90,   #  5.0 × 0.4

    # ── Gates & structures ───────────────────────────────────────────────────
    Prop.CRANE:                270,   # 51.3 × 3.3  — long axis E-W + reversed
}

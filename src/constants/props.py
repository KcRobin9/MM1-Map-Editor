class Prop:
    """
    Dimensions are noted as  x, y, z.
    Breakable sub-parts (_BREAK*, _BREAKPART*, etc.) are physics debris
    fragments — they exist in the game files but are spawned automatically
    on destruction and are not intended for direct placement. They are
    excluded from this class.

    Props marked  # flat billboard  use a near-zero z depth and face the
    camera; they don't have true 3D geometry.
    """

    # ── Bridges ───────────────────────────────────────────────────────────────
    BRIDGE_SLIM             = "tpdrawbridge04"      # 30.0 × 5.9 × 32.5
    BRIDGE_WIDE             = "tpdrawbridge06"      # 40.0 × 5.9 × 32.5
    BRIDGE_BUILDING         = "tpbridgebuild"       #  6.0 × 14.2 × 6.0

    CROSSGATE               = "tpcrossgate06"       # 13.2 × 0.3 × 0.1  (6-section)
    CROSSGATE_SHORT         = "tpcrossgate04"       #  9.9 × 0.3 × 0.1  (4-section)
    CROSSGATE_BASE          = "tpcrossbase"         #  0.6 × 1.5 × 1.2

    # ── El Train ──────────────────────────────────────────────────────────────
    ELTRAIN                     = "r_l_train"
    ELTRAIN_SUPPORT_SLIM        = "dp_left"             # 11.0 × 10.25 × 1.0
    ELTRAIN_SUPPORT_WIDE        = "dp_left6"            # 16.0 × 10.25 × 1.0
    ELTRAIN_SUPPORT_SPAN        = "dp_trainsupport"     # 23.0 × 13.0  × 1.0  (longer span)
    ELTRAIN_SUPPORT_SPAN_SHORT  = "dp_trainsupport20"   # 22.0 × 13.0  × 1.0

    # ── Traffic lights ────────────────────────────────────────────────────────
    STOP_LIGHT_SINGLE       = "tplttrafc"           #  6.8 × 7.8 × 0.5
    STOP_LIGHT_DUAL         = "tplttrafcdual"       #  9.8 × 7.8 × 0.5
    TRAFFIC_SIGNAL_BOX      = "lightts"             #  4.0 × 6.2 × 0.4  (signal head panel only)

    # ── Traffic signs ─────────────────────────────────────────────────────────
    STOP_SIGN               = "tpsstop"             #  0.8 × 3.2 × 0.1
    WRONG_WAY               = "tpwrongway"          #  1.8 × 2.6 × 0.1
    DO_NOT_ENTER            = "tpswrng"             #  0.8 × 3.2 × 0.1
    SIGN_ONE_WAY_RIGHT      = "tpsone"              #  0.9 × 2.9 × 0.1
    SIGN_ONE_WAY_LEFT       = "tpsoneleft"          #  0.9 × 2.9 × 0.1
    SIGN_LEFT_TURN_ONLY     = "tpleft"              #  0.7 × 2.9 × 0.1
    SIGN_CROSSWALK          = "tpsxwlk"             #  0.5 × 2.3 × 0.3
    SIGN_SPEED              = "tpsspd"              # NOTE: bounding box dims are corrupt/zero in data; prop is likely a speed limit sign
    SIGN_POST               = "tpsst"               #  0.6 × 2.9 × 0.6  (generic post)
    SIGN_ROTATING           = "ipsign_rotate"       #  1.6 × 7.0 × 3.7  (animated rotating sign?)

    SIGN_HIGHWAY_OLDTOWN    = "tpfw_sign_ot"        # 11.0 × 13.0 × 0.9  (Old Town off-ramp)
    SIGN_HIGHWAY_LAKESHORE  = "tpfw_sign_ls"        # 11.0 × 13.0 × 0.9  (Lake Shore Drive off-ramp)
    SIGN_HIGHWAY_DOWNTOWN   = "tpfw_sign_dt"        # 11.0 × 13.0 × 0.9  (Downtown off-ramp)
    SIGN_HIGHWAY_CHINATOWN  = "tpfw_sign_ct"        # 11.0 × 13.0 × 0.9  (Chinatown off-ramp)

    # ── Street lights ─────────────────────────────────────────────────────────
    HIGHWAY_LIGHT           = "tpltst"              #  5.9 × 12.6 × 0.8
    SIDEWALK_LIGHT          = "opstlite"            #  0.4 ×  2.9 × 0.4  (old-style, short)
    SIDEWALK_LIGHT_RED      = "opstlite_red"        #  5.0 × 12.7 × 0.8  (tall colored variants)
    SIDEWALK_LIGHT_GREEN    = "opstlite_green"      #  5.0 × 12.7 × 0.8
    SIDEWALK_LIGHT_BLUE     = "opstlite_blue"       #  5.0 × 12.7 × 0.8

    # ── Road barriers & safety ────────────────────────────────────────────────
    CRASH_CAN               = "tpcrshcan"           #  1.3 × 1.4 × 1.3  (yellow highway end barrier)
    BARRICADE               = "tp_barricade"        #  4.0 × 2.0 × 0.5  (race barricade)
    BARRICADE_SAWHORSE      = "tpsawhrslt"          #  0.8 × 1.5 × 0.8  (orange/white construction sawhorse with amber light)
    CONE                    = "tpcone"              #  0.5 × 0.75 × 0.5
    BARREL_BLUE             = "tpbarrelblue"        #  0.8 × 1.1  × 0.7
    BARREL                  = "tpbarrlm"            #  0.5 × 0.72 × 0.5  (smaller barrel)

    # ── Street furniture ──────────────────────────────────────────────────────
    BENCH                   = "tpbench"             #  0.75 × 1.1 × 2.5   (park bench with backrest)
    BENCH_MALL              = "tpbench_mall"        #  2.5  × 0.6 × 0.68  (wooden bench, no backrest)
    BIN                     = "tptcanc"             #  0.72 × 0.97 × 0.76 (grey trash can)
    BIN_METAL               = "tptcanm"             #  0.73 × 0.97 × 0.76 (metal trash can)
    BIN_PAINTED             = "tptcanp"             #  0.73 × 1.07 × 0.63 (painted trash can)
    DUMPSTER                = "tpdmpstr"            #  1.2  × 1.5  × 2.1  (large blue dumpster)
    MAILBOX                 = "tpmail"              #  0.66 × 1.37 × 0.66
    PARKING_METER           = "tppmtr"              #  0.2  × 1.07 × 0.04
    FIRE_HYDRANT            = "tpfirehy"            #  0.47 × 0.75 × 0.46
    TELEPHONE_POLE          = "tptpole"             #  3.4  × 12.3 × 0.45
    CALLBOX_EMERGENCY       = "tpcallbox"           #  0.48 × 2.53 × 0.42
    BUS_STOP                = "tpsbus"              #  0.46 × 2.75 × 0.10 (bus stop sign post)
    PHONE_BOOTH             = "optbooth"            #  0.85 × 2.0  × 0.85 (enclosed booth)
    PAYPHONE                = "tpphone"             #  0.64 × 2.0  × 0.51 (wall-mounted handset)
    PLANT                   = "tpplanter_mall"      #  0.9  × 1.4  × 0.9  (potted bush)
    SUPPORT_LARGE           = "tpsupport"           #  3.6  × 22.0 × 3.8  (large structural support)

    # ── Newspaper, vending & boxes ────────────────────────────────────────────
    NEWSPAPER_BOX_BLUE      = "tpnews01"            #  0.59 × 1.11 × 0.56
    NEWSPAPER_BOX_RED       = "tpnews02"            #  0.59 × 1.11 × 0.56
    NEWSPAPER_BOX_YELLOW    = "tpnews03"            #  0.59 × 1.11 × 0.56
    NEWSPAPER_BOX_BLUE_2    = "tpnews04"            #  0.59 × 1.11 × 0.56 (alternate blue)
    NEWSPAPER_BOX_MOUNTED   = "tpmnews"             #  0.65 × 1.14 × 0.48 (wall-mounted)
    NEWSSTAND               = "tpbbsw01"            #  1.87 × 1.74 × 1.07
    VENDING_BEVERAGE        = "tpmbevrg"            #  1.0  × 2.0  × 0.75
    BOX_METAL               = "tpmboxs"             #  0.54 × 0.54 × 0.54 (steel box)
    BOX_UTILITY             = "tpuboxs"             #  0.93 × 1.27 × 0.68

    # ── Crates & trash ────────────────────────────────────────────────────────
    BOX_SINGLE              = "tpcboxm"             #  0.8  × 0.8  × 0.79
    BOX_STACK               = "tpcboxbreak"         #  0.96 × 1.21 × 1.87 (three stacked boxes)
    BOX_STACK_ALLEY         = "tpboxalley"          #  4.35 × 2.0  × 1.47 (boxes with wooden plank)
    TRASH_BOXES             = "tptrashalley02"      #  4.15 × 2.0  × 0.95
    TRASH_BOXES_SMALL       = "tptrashalley01"      #  3.56 × 1.1  × 1.35

    # ── Trees ─────────────────────────────────────────────────────────────────
    TREE_SLIM               = "tp_tree10m"          #  7 × 9.88  # flat billboard
    TREE_WIDE               = "tp_tree15m"          # 12 × 15.0  # flat billboard
    TREE_SPARSE             = "tptree_sparce"       #  7 × 9.88  # flat billboard, same mesh as TREE_SLIM

    # ── Vehicles & transport ──────────────────────────────────────────────────
    TRAILER                 = "tp_trailer"          # 16.3 × 4.7 × 4.0  (ramp trailer)
    SAILBOAT                = "tpsailboat"          # 6.0 × 6.0 × 0.1  # flat billboard, single-sided
    PLANE_LARGE             = "vaboeing"            # no collision

    # ── Gates & structures ────────────────────────────────────────────────────
    CHINATOWN_GATE          = "cpgate"              # 28.8 × 14.25 × 4.0
    GATE                    = "tpgate"              # generic gate (only break parts documented)
    CRANE                   = "dp60crane"           # 51.3 × 4.4  × 3.3

    # ── Doors ─────────────────────────────────────────────────────────────────
    DOOR_BREAKABLE          = "ipbreakdoor"         #  3.97 × 5.97 × 0.1  (interactive, breaks on impact)
    MALL_DOOR               = "dpmalldoor"          #  9.86 × 3.5  (animated glass sliding door)
    MALL_DOOR_A             = "dpmalldoora"         #  8.84 × 3.5  (variant A)
    MALL_DOOR_B             = "dpmalldoorb"         #  8.84 × 3.5  (variant B)
    MALL_DOOR_C             = "dpmalldoorc"         #  8.84 × 3.5  (variant C)

    # ── Walls (flat breakable panels) ─────────────────────────────────────────
    WALL_TALL               = "dp31walla"           # 8.9 × 4.3 × 0.2
    WALL_TALL_B             = "dp31wallb"           # 8.0 × 4.3 × 0.2
    WALL_WIDE               = "dp32wall"            # 4.7 × 4.8 × 0.4
    WALL_LOW                = "dp42wall"            # 5.0 × 2.9 × 0.4
    WALL_CONSTRUCTION_A     = "dp60walla"           # 7.2 × 2.4 × 7.3  (construction site wall)
    WALL_CONSTRUCTION_B     = "dp60wallb"           # 7.0 × 2.4 × 7.6
    WALL_CONSTRUCTION_C     = "dp60wallc"           # 4.6 × 3.0 × 4.7


class AudioProp:
    MALLDOOR = 1
    POLE = 3
    SIGN = 4
    MAILBOX = 5
    METER = 6
    TRASHCAN = 7
    BENCH = 8
    TREE = 11
    TRASH_BOXES = 12    # Also used for "bridge crossgate"
    NO_NAME_1 = 13      # Difficult to describe
    BARREL = 15         # Also used for "dumpster"
    PHONEBOOTH = 20
    CONE = 22
    NO_NAME_2 = 24      # Sounds a bit similar to "glass"
    NEWSBOX = 25
    GLASS = 27
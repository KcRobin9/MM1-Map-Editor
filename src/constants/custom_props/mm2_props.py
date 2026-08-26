"""
Custom props converted from the real Midtown Madness 2 `.pkg` prop meshes, so an imported MM2 city
places the actual MM2 model for every prop (pathset scenery, density furniture, BAI traffic lights)
instead of an MM1 placeholder.

Each value is the game prop id --- the lowercase banger name in the .BNG, max 31 chars. The assets
live under `resources/editor/custom/MM2_PROPS/{MESHES,TUNE,TEXTURES}`.

Both engines use the same banger convention (mesh-local +X is the facing vector: banger.cpp:380,
midtown2.exe dgPath::Enumerate 0x466D40), so the MM2 facing carries straight into the MM1 angle and
no per-model rotation fudge is needed.

`MM2_PROP_MODELS` is the single source of truth: model name -> (prop id, banger flags, mass).
"""
from src.constants.props import BangerFlags


class Mm2Prop:
    """Prop ids of the converted MM2 meshes (see module docstring). Ids are stable: never rename."""

    BANNER_BLU             = "mm2bannerblu"           # cp_banrblu_f
    BANNER_RED             = "mm2bannerred"           # cp_banrred_f
    BANNER_YEL             = "mm2banneryel"           # cp_banryel_f
    GDELLI                 = "mm2gdelli"              # np_ghirardelli_f
    EROS                   = "mm2eros"                # op_eros_l
    BARREL_WOOD            = "mm2barrelwood"          # sp_barrelwood_l
    BARRICADE              = "mm2barricade"           # sp_barricadewood_f
    BENCH                  = "mm2bench"               # sp_benchwood_f
    BOLLARD_BLACK          = "mm2bollardblack"        # sp_bollard_black_l
    BOLLARD_STONE          = "mm2bollardstone"        # sp_bollard_stone_l
    CENOTAPH               = "mm2cenotaph"            # sp_cenotaph_gen_l
    EXIT_CC                = "mm2exitcc"              # sp_civcentrexit_f
    CLEAT                  = "mm2cleat"               # sp_cleat_f
    CONE_L                 = "mm2conel"               # sp_cone_l
    CRASHBARREL            = "mm2crashbarrel"         # sp_crashbarrelgroup_f
    DUMPSTER               = "mm2dump"                # sp_dumpstr_f
    DUMPSTER_L             = "mm2dumpl"               # sp_dumpstr_l
    EXIT_EMB               = "mm2exitemb"             # sp_embarcexit_f
    EXIT_GG                = "mm2exitgg"              # sp_ggexit_f
    HILLWARN               = "mm2hillwarn"            # sp_hillwarn_f
    HOTDOG                 = "mm2hotdog"              # sp_hotdogcart_f
    LIGHT_PARK             = "mm2lightpark"           # sp_lightpark_f
    LAMP                   = "mm2lamp"                # sp_lightstreet_rt_f
    LIGHT_THAMES           = "mm2lightthames"         # sp_lightthames_l
    MAIL                   = "mm2mail"                # sp_mailbox_f
    EXIT_MAR               = "mm2exitmar"             # sp_marinexit_f
    NOENTER                = "mm2noenter"             # sp_noenter_f
    OAK                    = "mm2oak"                 # sp_oaktree1_s
    PILASTER               = "mm2pilaster"            # sp_pilaster_l
    BOXBARREL              = "mm2boxbarrel"           # sp_stackboxbarrel_f
    BOXCARD                = "mm2boxcard"             # sp_stackboxcard_f
    BOXES4                 = "mm2boxes4"              # sp_stackboxes_4_l
    STOP                   = "mm2stop"                # sp_stop_f
    EXIT_TB                = "mm2exittb"              # sp_transbayexit_f
    TREE                   = "mm2tree"                # sp_tree1_s
    TREE6                  = "mm2tree6"               # sp_tree6_s
    PALM                   = "mm2palm"                # sp_treepalm4_f
    WRONGWAY               = "mm2wrongway"            # sp_wrongwayfw
    FENCE                  = "mm2fence"               # wp_buck_fence_l
    NY_GARBAGE01_M         = "mm2nygarbage01m"        # as_sp_garbage01_m
    NY_GARBAGE02_M         = "mm2nygarbage02m"        # as_sp_garbage02_m
    NY_HOMELESSBOX_M       = "mm2nyhomelessboxm"      # as_sp_homelessbox_m
    NY_SIGN_NOPARKING_M    = "mm2nysignnoparkingm"    # as_sp_sign_noparking_m
    BSAS_ARCO_FUTBOL       = "mm2bsasarcofutbol"      # bsas_arco_futbol
    BSAS_BAVERDE_A         = "mm2bsasbaverdea"        # bsas_baverde_a
    BSAS_BAVERDE_B         = "mm2bsasbaverdeb"        # bsas_baverde_b
    BSAS_CARTEL_GARAGE     = "mm2bsascartelgarage"    # bsas_cartel_garage
    BSAS_CARTEL_LOCU       = "mm2bsascartellocu"      # bsas_cartel_locu
    BSAS_CONTENEDOR        = "mm2bsascontenedor"      # bsas_contenedor
    BSAS_DUMPSTER          = "mm2bsasdumpster"        # bsas_dumpster
    BSAS_FAROL_4           = "mm2bsasfarol4"          # bsas_farol_4
    BSAS_GLASSWIN_DARK_BIG = "mm2bsasglasswindarkbig" # bsas_glasswin_dark_big
    BSAS_KIOSCODIARIOS     = "mm2bsaskioscodiarios"   # bsas_kioscodiarios
    BSAS_MESA_CAFE1        = "mm2bsasmesacafe1"       # bsas_mesa_cafe1
    BSAS_MESA_CAFE2        = "mm2bsasmesacafe2"       # bsas_mesa_cafe2
    BSAS_PORTON_ESTADIO    = "mm2bsasportonestadio"   # bsas_porton_estadio
    BSAS_TECHITO_YACHTCLUB = "mm2bsastechitoyachtclub"# bsas_techito_yachtclub
    BSAS_TR5_FIX           = "mm2bsastr5fix"          # bsas_tr5_fix
    CP_BANRBLU_20_F        = "mm2cpbanrblu20f"        # cp_banrblu_20_f
    CP_BANRRED_30_F        = "mm2cpbanrred30f"        # cp_banrred_30_f
    CP_BANRYEL_20_F        = "mm2cpbanryel20f"        # cp_banryel_20_f
    AWNING_V_4_L           = "mm2awningv4l"           # sp_awning_v_4_l
    BARRELEXP_L            = "mm2barrelexpl"          # sp_barrelexp_l
    BARRELGRAY_F           = "mm2barrelgrayf"         # sp_barrelgray_f
    BARRIER_RED_L          = "mm2barrierredl"         # sp_barrier_red_l
    BARRIER_WHT_L          = "mm2barrierwhtl"         # sp_barrier_wht_l
    BG_LIGHTSTREET_BSAS    = "mm2bglightstreetbsas"   # sp_bg_lightstreet_bsas
    BG_LIGHTSTREET_BSAS2   = "mm2bglightstreetbsas2"  # sp_bg_lightstreet_bsas2
    BIGTREE1_BSAS          = "mm2bigtree1bsas"        # sp_bigtree1_bsas
    BLKFENCE_BA            = "mm2blkfenceba"          # sp_blkfence_ba
    BOX_CARDBRD_F          = "mm2boxcardbrdf"         # sp_box_cardbrd_f
    BOX_WOOD_L             = "mm2boxwoodl"            # sp_box_wood_l
    BOXFRUIT_L             = "mm2boxfruitl"           # sp_boxfruit_l
    BSAS_9DEJULIOEXIT      = "mm2bsas9dejulioexit"    # sp_bsas_9dejulioexit
    BUSSTOP_F              = "mm2busstopf"            # sp_busstop_f
    CALLBOX_F              = "mm2callboxf"            # sp_callbox_f
    CAN_GEN_F              = "mm2cangenf"             # sp_can_gen_f
    CAN_ROYAL_L            = "mm2canroyall"           # sp_can_royal_l
    CARAPANTALLA_BSAS      = "mm2carapantallabsas"    # sp_carapantalla_bsas
    CHINAGATE_F            = "mm2chinagatef"          # sp_chinagate_f
    CHINALIGHT_F           = "mm2chinalightf"         # sp_chinalight_f
    CRASHCAN_F             = "mm2crashcanf"           # sp_crashcan_f
    FAROL_BOCA             = "mm2farolboca"           # sp_farol_boca
    FWSUPPORT_F            = "mm2fwsupportf"          # sp_fwsupport_f
    GIVEWAY_BSAS           = "mm2givewaybsas"         # sp_giveway_bsas
    GIVEWAY_BSAS2          = "mm2givewaybsas2"        # sp_giveway_bsas2
    LIGHT_TALL_L           = "mm2lighttalll"          # sp_light_tall_l
    LIGHTBANR_RAINBO_F     = "mm2lightbanrrainbof"    # sp_lightbanr_rainbo_f
    LIGHTBANRB_F           = "mm2lightbanrbf"         # sp_lightbanrb_f
    LIGHTBANRG_F           = "mm2lightbanrgf"         # sp_lightbanrg_f
    LIGHTPARK_BSAS         = "mm2lightparkbsas"       # sp_lightpark_bsas
    LIGHTSTREET_BSAS       = "mm2lightstreetbsas"     # sp_lightstreet_bsas
    LIGHTSTREET_BSAS_HWY   = "mm2lightstreetbsashwy"  # sp_lightstreet_bsas_hwy
    LIGHTSTREET_F          = "mm2lightstreetf"        # sp_lightstreet_f
    LIGHTSTREET_L          = "mm2lightstreetl"        # sp_lightstreet_l
    MAILBOX_BSAS           = "mm2mailboxbsas"         # sp_mailbox_bsas
    MAILBOX_L              = "mm2mailboxl"            # sp_mailbox_l
    NEWSBLUE_F             = "mm2newsbluef"           # sp_newsblue_f
    NEWSGROUP01_L          = "mm2newsgroup01l"        # sp_newsgroup01_l
    NEWSRED_F              = "mm2newsredf"            # sp_newsred_f
    NEWSYELW_F             = "mm2newsyelwf"           # sp_newsyelw_f
    NOENTRY_L              = "mm2noentryl"            # sp_noentry_l
    NOPRK_F                = "mm2noprkf"              # sp_noprk_f
    ONEWAYR_BA             = "mm2onewayrba"           # sp_onewayR_ba
    PALM1_BSAS             = "mm2palm1bsas"           # sp_palm1_bsas
    PARKMTR_F              = "mm2parkmtrf"            # sp_parkmtr_f
    PHONEBOOTH_L           = "mm2phoneboothl"         # sp_phonebooth_l
    PHONESTAND_F           = "mm2phonestandf"         # sp_phonestand_f
    RECYCLE_CAN_F          = "mm2recyclecanf"         # sp_recycle_can_f
    SIGN_SANDWICHBD01_L    = "mm2signsandwichbd01l"   # sp_sign_sandwichbd01_l
    SIGN_SANDWICHBD02_L    = "mm2signsandwichbd02l"   # sp_sign_sandwichbd02_l
    SPEED65_F              = "mm2speed65f"            # sp_speed65_f
    STACKBARREL1_L         = "mm2stackbarrel1l"       # sp_stackbarrel1_l
    STACKBARREL_3_L        = "mm2stackbarrel3l"       # sp_stackbarrel_3_l
    STACKBOXES_L           = "mm2stackboxesl"         # sp_stackboxes_l
    STACKBOXFRUIT_3_L      = "mm2stackboxfruit3l"     # sp_stackboxfruit_3_l
    STACKBOXFRUIT_L        = "mm2stackboxfruitl"      # sp_stackboxfruit_l
    STACKBOXS_F            = "mm2stackboxsf"          # sp_stackboxs_f
    SUBWAYEN_BSAS_S        = "mm2subwayenbsass"       # sp_subwayen_bsas_s
    TELEPHONEPOLE_F        = "mm2telephonepolef"      # sp_telephonepole_f
    TRAFLITDUAL_F          = "mm2traflitdualf"        # sp_traflitdual_f
    TRAFLITSINGLE_F        = "mm2traflitsinglef"      # sp_traflitsingle_f
    TREE1_BA               = "mm2tree1ba"             # sp_tree1_ba
    TREE5_S                = "mm2tree5s"              # sp_tree5_s
    TREEJACARANDA_BA       = "mm2treejacarandaba"     # sp_treejacaranda_ba
    TPBENCH_MALL_BA        = "mm2tpbenchmallba"       # tpbench_mall_ba
    TPPLANTER_MALL_BA      = "mm2tpplantermallba"     # tpplanter_mall_ba


_BRK = BangerFlags.BREAKABLE
_GLOW = BangerFlags.BREAKABLE_GLOW       # light models: the engine draws the glow card at night

# MM2 .pkg model name -> (prop id, banger flags, mass). Every model the 4 cities use that has a .pkg.
# Deliberately NOT here: r4i_rails_f (no .pkg exists), giz_pcar0[1-3]_ba
# (parked-car gizmos, MM2 spawns random traffic cars there), sp_cone_f (untextured -> MM1 cone, round so
# rotation is moot), sp_light_white_f (1-triangle glow-only light source, no pole in MM2).
MM2_PROP_MODELS = {
    "cp_banrblu_f":            (Mm2Prop.BANNER_BLU,                _BRK,    5.0),   # SF
    "cp_banrred_f":            (Mm2Prop.BANNER_RED,                _BRK,    5.0),   # SF
    "cp_banryel_f":            (Mm2Prop.BANNER_YEL,                _BRK,    5.0),   # SF
    "np_ghirardelli_f":        (Mm2Prop.GDELLI,                    _BRK,   50.0),   # SF
    "op_eros_l":               (Mm2Prop.EROS,                      _BRK,  200.0),   # LONDON
    "sp_barrelwood_l":         (Mm2Prop.BARREL_WOOD,               _BRK,   20.0),   # LONDON
    "sp_barricadewood_f":      (Mm2Prop.BARRICADE,                 _BRK,   30.0),   # SF
    "sp_benchwood_f":          (Mm2Prop.BENCH,                     _BRK,   20.0),   # BA,LONDON,NY,SF
    "sp_bollard_black_l":      (Mm2Prop.BOLLARD_BLACK,             _BRK,   50.0),   # LONDON
    "sp_bollard_stone_l":      (Mm2Prop.BOLLARD_STONE,             _BRK,   50.0),   # LONDON
    "sp_cenotaph_gen_l":       (Mm2Prop.CENOTAPH,                  _BRK,  500.0),   # LONDON
    "sp_civcentrexit_f":       (Mm2Prop.EXIT_CC,                   _BRK,   40.0),   # SF
    "sp_cleat_f":              (Mm2Prop.CLEAT,                     _BRK,  100.0),   # SF
    "sp_cone_l":               (Mm2Prop.CONE_L,                    _BRK,    5.0),   # BA,LONDON
    "sp_crashbarrelgroup_f":   (Mm2Prop.CRASHBARREL,               _BRK,   20.0),   # BA,SF
    "sp_dumpstr_f":            (Mm2Prop.DUMPSTER,                  _BRK,   60.0),   # SF
    "sp_dumpstr_l":            (Mm2Prop.DUMPSTER_L,                _BRK,   60.0),   # LONDON
    "sp_embarcexit_f":         (Mm2Prop.EXIT_EMB,                  _BRK,   40.0),   # SF
    "sp_ggexit_f":             (Mm2Prop.EXIT_GG,                   _BRK,   40.0),   # SF
    "sp_hillwarn_f":           (Mm2Prop.HILLWARN,                  _BRK,   10.0),   # SF
    "sp_hotdogcart_f":         (Mm2Prop.HOTDOG,                    _BRK,   30.0),   # BA,LONDON,SF
    "sp_lightpark_f":          (Mm2Prop.LIGHT_PARK,                _GLOW,    8.0),  # BA,LONDON,NY,SF
    "sp_lightstreet_rt_f":     (Mm2Prop.LAMP,                      _GLOW,    8.0),  # SF
    "sp_lightthames_l":        (Mm2Prop.LIGHT_THAMES,              _GLOW,    8.0),  # LONDON
    "sp_mailbox_f":            (Mm2Prop.MAIL,                      _BRK,   15.0),   # NY,SF
    "sp_marinexit_f":          (Mm2Prop.EXIT_MAR,                  _BRK,   40.0),   # SF
    "sp_noenter_f":            (Mm2Prop.NOENTER,                   _BRK,   10.0),   # SF
    "sp_oaktree1_s":           (Mm2Prop.OAK,                       _BRK,    8.0),   # LONDON
    "sp_pilaster_l":           (Mm2Prop.PILASTER,                  _BRK,  100.0),   # LONDON
    "sp_stackboxbarrel_f":     (Mm2Prop.BOXBARREL,                 _BRK,   15.0),   # BA,SF
    "sp_stackboxcard_f":       (Mm2Prop.BOXCARD,                   _BRK,   15.0),   # SF
    "sp_stackboxes_4_l":       (Mm2Prop.BOXES4,                    _BRK,   15.0),   # BA,LONDON
    "sp_stop_f":               (Mm2Prop.STOP,                      _BRK,   10.0),   # SF
    "sp_transbayexit_f":       (Mm2Prop.EXIT_TB,                   _BRK,   40.0),   # SF
    "sp_tree1_s":              (Mm2Prop.TREE,                      _BRK,    8.0),   # LONDON,NY,SF
    "sp_tree6_s":              (Mm2Prop.TREE6,                     _BRK,    8.0),   # BA,SF
    "sp_treepalm4_f":          (Mm2Prop.PALM,                      _BRK,    8.0),   # SF
    "sp_wrongwayfw":           (Mm2Prop.WRONGWAY,                  _BRK,   10.0),   # SF
    "wp_buck_fence_l":         (Mm2Prop.FENCE,                     _BRK,   30.0),   # LONDON
    "as_sp_garbage01_m":       (Mm2Prop.NY_GARBAGE01_M,            _BRK,   15.0),   # NY
    "as_sp_garbage02_m":       (Mm2Prop.NY_GARBAGE02_M,            _BRK,   15.0),   # NY
    "as_sp_homelessbox_m":     (Mm2Prop.NY_HOMELESSBOX_M,          _BRK,   15.0),   # NY
    "as_sp_sign_noparking_m":  (Mm2Prop.NY_SIGN_NOPARKING_M,       _BRK,   10.0),   # NY
    "bsas_arco_futbol":        (Mm2Prop.BSAS_ARCO_FUTBOL,          _BRK,   50.0),   # BA
    "bsas_baverde_a":          (Mm2Prop.BSAS_BAVERDE_A,            _BRK,   50.0),   # BA
    "bsas_baverde_b":          (Mm2Prop.BSAS_BAVERDE_B,            _BRK,   50.0),   # BA
    "bsas_cartel_garage":      (Mm2Prop.BSAS_CARTEL_GARAGE,        _BRK,   10.0),   # BA
    "bsas_cartel_locu":        (Mm2Prop.BSAS_CARTEL_LOCU,          _BRK,   10.0),   # BA
    "bsas_contenedor":         (Mm2Prop.BSAS_CONTENEDOR,           _BRK,   60.0),   # BA
    "bsas_dumpster":           (Mm2Prop.BSAS_DUMPSTER,             _BRK,   60.0),   # BA
    "bsas_farol_4":            (Mm2Prop.BSAS_FAROL_4,              _GLOW,    8.0),  # BA
    "bsas_glasswin_dark_big":  (Mm2Prop.BSAS_GLASSWIN_DARK_BIG,    _BRK,   50.0),   # BA
    "bsas_kioscodiarios":      (Mm2Prop.BSAS_KIOSCODIARIOS,        _BRK,  100.0),   # BA
    "bsas_mesa_cafe1":         (Mm2Prop.BSAS_MESA_CAFE1,           _BRK,   20.0),   # BA
    "bsas_mesa_cafe2":         (Mm2Prop.BSAS_MESA_CAFE2,           _BRK,   20.0),   # BA
    "bsas_porton_estadio":     (Mm2Prop.BSAS_PORTON_ESTADIO,       _BRK,  200.0),   # BA
    "bsas_techito_yachtclub":  (Mm2Prop.BSAS_TECHITO_YACHTCLUB,    _BRK,  200.0),   # BA
    "bsas_tr5_fix":            (Mm2Prop.BSAS_TR5_FIX,              _BRK,    8.0),   # BA
    "cp_banrblu_20_f":         (Mm2Prop.CP_BANRBLU_20_F,           _BRK,    5.0),   # SF
    "cp_banrred_30_f":         (Mm2Prop.CP_BANRRED_30_F,           _BRK,    5.0),   # SF
    "cp_banryel_20_f":         (Mm2Prop.CP_BANRYEL_20_F,           _BRK,    5.0),   # SF
    "sp_awning_v_4_l":         (Mm2Prop.AWNING_V_4_L,              _BRK,   20.0),   # BA
    "sp_barrelexp_l":          (Mm2Prop.BARRELEXP_L,               _BRK,   20.0),   # BA
    "sp_barrelgray_f":         (Mm2Prop.BARRELGRAY_F,              _BRK,   20.0),   # BA
    "sp_barrier_red_l":        (Mm2Prop.BARRIER_RED_L,             _BRK,   30.0),   # BA
    "sp_barrier_wht_l":        (Mm2Prop.BARRIER_WHT_L,             _BRK,   30.0),   # BA
    "sp_bg_lightstreet_bsas":  (Mm2Prop.BG_LIGHTSTREET_BSAS,       _GLOW,    8.0),  # BA
    "sp_bg_lightstreet_bsas2": (Mm2Prop.BG_LIGHTSTREET_BSAS2,      _GLOW,    8.0),  # BA
    "sp_bigtree1_bsas":        (Mm2Prop.BIGTREE1_BSAS,             _BRK,    8.0),   # BA
    "sp_blkfence_ba":          (Mm2Prop.BLKFENCE_BA,               _BRK,   30.0),   # BA
    "sp_box_cardbrd_f":        (Mm2Prop.BOX_CARDBRD_F,             _BRK,   15.0),   # BA
    "sp_box_wood_l":           (Mm2Prop.BOX_WOOD_L,                _BRK,   15.0),   # BA
    "sp_boxfruit_l":           (Mm2Prop.BOXFRUIT_L,                _BRK,   15.0),   # BA
    "sp_bsas_9dejulioexit":    (Mm2Prop.BSAS_9DEJULIOEXIT,         _BRK,   40.0),   # BA
    "sp_busstop_f":            (Mm2Prop.BUSSTOP_F,                 _BRK,   10.0),   # SF
    "sp_callbox_f":            (Mm2Prop.CALLBOX_F,                 _BRK,   15.0),   # SF
    "sp_can_gen_f":            (Mm2Prop.CAN_GEN_F,                 _BRK,   15.0),   # LONDON,NY,SF
    "sp_can_royal_l":          (Mm2Prop.CAN_ROYAL_L,               _BRK,   15.0),   # LONDON
    "sp_carapantalla_bsas":    (Mm2Prop.CARAPANTALLA_BSAS,         _BRK,   30.0),   # BA
    "sp_chinagate_f":          (Mm2Prop.CHINAGATE_F,               _BRK,  500.0),   # SF
    "sp_chinalight_f":         (Mm2Prop.CHINALIGHT_F,              _GLOW,    8.0),  # SF
    "sp_crashcan_f":           (Mm2Prop.CRASHCAN_F,                _BRK,   15.0),   # NY
    "sp_farol_boca":           (Mm2Prop.FAROL_BOCA,                _GLOW,    8.0),  # BA
    "sp_fwsupport_f":          (Mm2Prop.FWSUPPORT_F,               _BRK,  500.0),   # SF
    "sp_giveway_bsas":         (Mm2Prop.GIVEWAY_BSAS,              _BRK,   10.0),   # BA
    "sp_giveway_bsas2":        (Mm2Prop.GIVEWAY_BSAS2,             _BRK,   10.0),   # BA
    "sp_light_tall_l":         (Mm2Prop.LIGHT_TALL_L,              _GLOW,    8.0),  # BA,LONDON
    "sp_lightbanr_rainbo_f":   (Mm2Prop.LIGHTBANR_RAINBO_F,        _GLOW,    8.0),  # SF
    "sp_lightbanrb_f":         (Mm2Prop.LIGHTBANRB_F,              _GLOW,    8.0),  # SF
    "sp_lightbanrg_f":         (Mm2Prop.LIGHTBANRG_F,              _GLOW,    8.0),  # SF
    "sp_lightpark_bsas":       (Mm2Prop.LIGHTPARK_BSAS,            _GLOW,    8.0),  # BA
    "sp_lightstreet_bsas":     (Mm2Prop.LIGHTSTREET_BSAS,          _GLOW,    8.0),  # BA
    "sp_lightstreet_bsas_hwy": (Mm2Prop.LIGHTSTREET_BSAS_HWY,      _GLOW,    8.0),  # BA
    "sp_lightstreet_f":        (Mm2Prop.LIGHTSTREET_F,             _GLOW,    8.0),  # BA,NY,SF
    "sp_lightstreet_l":        (Mm2Prop.LIGHTSTREET_L,             _GLOW,    8.0),  # LONDON
    "sp_mailbox_bsas":         (Mm2Prop.MAILBOX_BSAS,              _BRK,   15.0),   # BA
    "sp_mailbox_l":            (Mm2Prop.MAILBOX_L,                 _BRK,   15.0),   # LONDON
    "sp_newsblue_f":           (Mm2Prop.NEWSBLUE_F,                _BRK,   15.0),   # NY,SF
    "sp_newsgroup01_l":        (Mm2Prop.NEWSGROUP01_L,             _BRK,   15.0),   # LONDON
    "sp_newsred_f":            (Mm2Prop.NEWSRED_F,                 _BRK,   15.0),   # NY,SF
    "sp_newsyelw_f":           (Mm2Prop.NEWSYELW_F,                _BRK,   15.0),   # NY,SF
    "sp_noentry_l":            (Mm2Prop.NOENTRY_L,                 _BRK,   10.0),   # BA
    "sp_noprk_f":              (Mm2Prop.NOPRK_F,                   _BRK,   10.0),   # SF
    "sp_onewayR_ba":           (Mm2Prop.ONEWAYR_BA,                _BRK,   10.0),   # BA
    "sp_palm1_bsas":           (Mm2Prop.PALM1_BSAS,                _BRK,    8.0),   # BA
    "sp_parkmtr_f":            (Mm2Prop.PARKMTR_F,                 _BRK,   10.0),   # LONDON,NY,SF
    "sp_phonebooth_l":         (Mm2Prop.PHONEBOOTH_L,              _BRK,   30.0),   # BA,LONDON
    "sp_phonestand_f":         (Mm2Prop.PHONESTAND_F,              _BRK,   30.0),   # NY,SF
    "sp_recycle_can_f":        (Mm2Prop.RECYCLE_CAN_F,             _BRK,   15.0),   # SF
    "sp_sign_sandwichbd01_l":  (Mm2Prop.SIGN_SANDWICHBD01_L,       _BRK,   10.0),   # BA
    "sp_sign_sandwichbd02_l":  (Mm2Prop.SIGN_SANDWICHBD02_L,       _BRK,   10.0),   # BA
    "sp_speed65_f":            (Mm2Prop.SPEED65_F,                 _BRK,   10.0),   # NY
    "sp_stackbarrel1_l":       (Mm2Prop.STACKBARREL1_L,            _BRK,   20.0),   # BA
    "sp_stackbarrel_3_l":      (Mm2Prop.STACKBARREL_3_L,           _BRK,   20.0),   # BA
    "sp_stackboxes_l":         (Mm2Prop.STACKBOXES_L,              _BRK,   15.0),   # BA
    "sp_stackboxfruit_3_l":    (Mm2Prop.STACKBOXFRUIT_3_L,         _BRK,   15.0),   # BA
    "sp_stackboxfruit_l":      (Mm2Prop.STACKBOXFRUIT_L,           _BRK,   15.0),   # BA
    "sp_stackboxs_f":          (Mm2Prop.STACKBOXS_F,               _BRK,   15.0),   # BA
    "sp_subwayen_bsas_s":      (Mm2Prop.SUBWAYEN_BSAS_S,           _BRK,  500.0),   # BA
    "sp_telephonepole_f":      (Mm2Prop.TELEPHONEPOLE_F,           _BRK,   30.0),   # SF
    "sp_traflitdual_f":        (Mm2Prop.TRAFLITDUAL_F,             _BRK,   40.0),   # BA,LONDON,NY,SF
    "sp_traflitsingle_f":      (Mm2Prop.TRAFLITSINGLE_F,           _BRK,   40.0),   # BA,LONDON,NY,SF
    "sp_tree1_ba":             (Mm2Prop.TREE1_BA,                  _BRK,    8.0),   # BA
    "sp_tree5_s":              (Mm2Prop.TREE5_S,                   _BRK,    8.0),   # BA
    "sp_treejacaranda_ba":     (Mm2Prop.TREEJACARANDA_BA,          _BRK,    8.0),   # BA
    "tpbench_mall_ba":         (Mm2Prop.TPBENCH_MALL_BA,           _BRK,   20.0),   # BA
    "tpplanter_mall_ba":       (Mm2Prop.TPPLANTER_MALL_BA,         _BRK,   50.0),   # BA
}


def mm2_model_map() -> dict:
    """model name -> (prop id, banger flags) for the prop placers (mass is a conversion-time detail)."""
    return {model: (prop_id, flags) for model, (prop_id, flags, _mass) in MM2_PROP_MODELS.items()}


def mm2_conversion_jobs() -> list:
    """build_custom_props job tuples (model, PROP_ID_UPPER, mass) for every real-mesh prop."""
    return [(model, prop_id.upper(), mass) for model, (prop_id, _flags, mass) in MM2_PROP_MODELS.items()]

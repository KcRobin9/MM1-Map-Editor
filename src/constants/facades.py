class Facade:
    """
    Chicago facade name constants.

    Naming convention:  <district><sub-type><building-type><number>
      Districts:
        C  = Chinatown
        D  = Downtown
        H  = Hyde Park / Hillside residential area
        I  = Industrial
        O  = Old Town
        R  = Residential (general suburbs)
        T  = The Loop (central business strip)

      Sub-types (second letter, when present):
        F  = Fringe  — side/front-facing building skins
        B  = Back    — alley/rear-facing building skins
        T  = Core    — main road-facing downtown buildings (DT## series)

      Special prefixes:
        CB  = Chinatown Banner
        CP  = Chinatown Pole banner
        DB  = Downtown Back (large background building)
        T_  = Track element

      Suffixes on constant names:
        _UNUSED        — facade exists in the files but is not placed anywhere in Chicago
        _FILE_MISSING  — referenced in the map data but the texture files are absent
        _NO_VISIBILITY — texture file exists but is never visible during normal gameplay
    """

    # ── Banners ──────────────────────────────────────────────────────────────
    BANNER_CHINATOWN_YELLOW           = "cbanr_yel"
    BANNER_CHINATOWN_RED_FILE_MISSING = "cpbanr_red"   # used in-game, texture files missing
    BANNER_CHINATOWN_BLU_FILE_MISSING = "cpbanr_blu"   # used in-game, texture files missing

    # ── Chinatown Fringe (CF) ────────────────────────────────────────────────
    ALLEY_CHINATOWN_1                 = "cfalley01"
    ALLEY_CHINATOWN_2                 = "cfalley02"
    ALLEY_CHINATOWN_3                 = "cfalley03"

    BUILDING_CHINATOWN_1              = "cfbldg01"
    BUILDING_CHINATOWN_2              = "cfbldg02"
    BUILDING_CHINATOWN_3              = "cfbldg03"

    SHOP_CHINATOWN_FOODS              = "cffoods"
    SHOP_CHINATOWN_LIQUOR             = "cfliquor"
    MOTEL_CHINATOWN                   = "cfmotel"
    RESTAURANT_CHINATOWN_1            = "cfrestnt01"
    RESTAURANT_CHINATOWN_2            = "cfrestnt02"
    SHOP_CHINATOWN_1                  = "cfshop01"
    SHOP_CHINATOWN_2                  = "cfshop02"
    SHOP_CHINATOWN_3                  = "cfshop03"
    SHOP_CHINATOWN_4                  = "cfshop04"
    SHOP_CHINATOWN_5                  = "cfshop05"
    SHOP_CHINATOWN_6                  = "cfshop06"
    SHOP_CHINATOWN_7                  = "cfshop07"
    SHOP_CHINATOWN_8                  = "cfshop08"
    SHOP_CHINATOWN_9                  = "cfshop09"
    SHOP_CHINATOWN_10                 = "cfshop10"

    # ── Downtown Back (DB) ───────────────────────────────────────────────────
    MALL_DOWNTOWN_LARGE               = "dbmall"

    # ── Downtown Fringe (DF) ─────────────────────────────────────────────────
    BUILDING_DOWNTOWN_1               = "dfbldg01"
    BUILDING_DOWNTOWN_2               = "dfbldg02"
    BUILDING_DOWNTOWN_3               = "dfbldg03"
    BUILDING_DOWNTOWN_4               = "dfbldg04"
    BUILDING_DOWNTOWN_5               = "dfbldg05"
    BUILDING_DOWNTOWN_6               = "dfbldg06"
    BUILDING_DOWNTOWN_7               = "dfbldg07"
    BUILDING_DOWNTOWN_8               = "dfbldg08"

    HOTEL_DOWNTOWN_1                  = "dfhotel01"
    HOTEL_DOWNTOWN_2                  = "dfhotel02"
    HOTEL_DOWNTOWN_3                  = "dfhotel03"

    MALL_DOWNTOWN_1                   = "dfmall01"
    MALL_DOWNTOWN_2                   = "dfmall02"
    MALL_DOWNTOWN_3                   = "dfmall03"

    SHOP_DOWNTOWN_PRODUCE             = "dfproduce"
    SHOP_DOWNTOWN_SUIT                = "dfsuitstore"

    SKYSCRAPER_DOWNTOWN_1             = "dfskys01"
    SKYSCRAPER_DOWNTOWN_2             = "dfskys02"
    SKYSCRAPER_DOWNTOWN_3             = "dfskys03"
    SKYSCRAPER_DOWNTOWN_4             = "dfskys04"

    # ── Downtown Core (DT) — per-face facade strings ──────────────────────────
    # Each building exposes up to 5 faces: back, front, left, right, roof.
    # Where a face shares the same texture as another, that is noted in a comment.
    # Roofs marked _NO_VISIBILITY are occluded by the camera angle and never seen.

    # dt01
    BUILDING_DOWNTOWN_CORE_1_BACK     = "dt01_back"
    BUILDING_DOWNTOWN_CORE_1_FRONT    = "dt01_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_1_LEFT     = "dt01_left"
    BUILDING_DOWNTOWN_CORE_1_RIGHT    = "dt01_right"  # same texture as _back

    # dt02  (all 5 faces are distinct)
    BUILDING_DOWNTOWN_CORE_2_BACK     = "dt02_back"
    BUILDING_DOWNTOWN_CORE_2_FRONT    = "dt02_front"
    BUILDING_DOWNTOWN_CORE_2_LEFT     = "dt02_left"
    BUILDING_DOWNTOWN_CORE_2_RIGHT    = "dt02_right"
    BUILDING_DOWNTOWN_CORE_2_ROOF     = "dt02_roof"

    # dt03
    BUILDING_DOWNTOWN_CORE_3_BACK     = "dt03_back"
    BUILDING_DOWNTOWN_CORE_3_FRONT    = "dt03_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_3_LEFT     = "dt03_left"   # same texture as _back
    BUILDING_DOWNTOWN_CORE_3_RIGHT    = "dt03_right"  # same texture as _back

    # dt05
    BUILDING_DOWNTOWN_CORE_5_BACK     = "dt05_back"
    BUILDING_DOWNTOWN_CORE_5_FRONT    = "dt05_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_5_LEFT     = "dt05_left"
    BUILDING_DOWNTOWN_CORE_5_RIGHT    = "dt05_right"  # same texture as _left
    BUILDING_DOWNTOWN_CORE_5_ROOF_NO_VISIBILITY = "dt05_roof"

    # dt07
    BUILDING_DOWNTOWN_CORE_7_BACK     = "dt07_back"
    BUILDING_DOWNTOWN_CORE_7_FRONT    = "dt07_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_7_LEFT     = "dt07_left"
    BUILDING_DOWNTOWN_CORE_7_RIGHT    = "dt07_right"  # same texture as _left
    BUILDING_DOWNTOWN_CORE_7_ROOF_NO_VISIBILITY = "dt07_roof"

    # dt08  (weird UV offset on both faces)
    BUILDING_DOWNTOWN_CORE_8_BACK     = "dt08_back"   # weird UV offset
    BUILDING_DOWNTOWN_CORE_8_FRONT    = "dt08_front"  # same texture as _back, weird UV offset
    BUILDING_DOWNTOWN_CORE_8_LEFT     = "dt08_left"   # weird UV offset
    BUILDING_DOWNTOWN_CORE_8_RIGHT    = "dt08_right"  # same texture as _left, weird UV offset

    # dt10
    BUILDING_DOWNTOWN_CORE_10_BACK    = "dt10_back"
    BUILDING_DOWNTOWN_CORE_10_FRONT   = "dt10_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_10_LEFT    = "dt10_left"
    BUILDING_DOWNTOWN_CORE_10_RIGHT   = "dt10_right"  # same texture as _left

    # dt11
    BUILDING_DOWNTOWN_CORE_11_BACK    = "dt11_back"
    BUILDING_DOWNTOWN_CORE_11_FRONT   = "dt11_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_11_LEFT    = "dt11_left"   # same texture as _back
    BUILDING_DOWNTOWN_CORE_11_RIGHT   = "dt11_right"  # same texture as _back

    # dt12
    BUILDING_DOWNTOWN_CORE_12_BACK    = "dt12_back"
    BUILDING_DOWNTOWN_CORE_12_FRONT   = "dt12_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_12_LEFT    = "dt12_left"
    BUILDING_DOWNTOWN_CORE_12_RIGHT   = "dt12_right"  # same texture as _left
    BUILDING_DOWNTOWN_CORE_12_ROOF    = "dt12_roof"

    # dt14
    BUILDING_DOWNTOWN_CORE_14_BACK    = "dt14_back"
    BUILDING_DOWNTOWN_CORE_14_FRONT   = "dt14_front"
    BUILDING_DOWNTOWN_CORE_14_LEFT    = "dt14_left"
    BUILDING_DOWNTOWN_CORE_14_RIGHT   = "dt14_right"

    # dt15
    BUILDING_DOWNTOWN_CORE_15_BACK    = "dt15_back"
    BUILDING_DOWNTOWN_CORE_15_FRONT   = "dt15_front"
    BUILDING_DOWNTOWN_CORE_15_LEFT    = "dt15_left"
    BUILDING_DOWNTOWN_CORE_15_RIGHT   = "dt15_right"
    BUILDING_DOWNTOWN_CORE_15_ROOF    = "dt15_roof"

    # dt18
    BUILDING_DOWNTOWN_CORE_18_BACK    = "dt18_back"
    BUILDING_DOWNTOWN_CORE_18_FRONT   = "dt18_front"
    BUILDING_DOWNTOWN_CORE_18_LEFT    = "dt18_left"
    BUILDING_DOWNTOWN_CORE_18_RIGHT   = "dt18_right"

    # dt19
    BUILDING_DOWNTOWN_CORE_19_BACK    = "dt19_back"
    BUILDING_DOWNTOWN_CORE_19_FRONT   = "dt19_front"
    BUILDING_DOWNTOWN_CORE_19_LEFT    = "dt19_left"
    BUILDING_DOWNTOWN_CORE_19_RIGHT   = "dt19_right"  # same texture as _left

    # dt29
    BUILDING_DOWNTOWN_CORE_29_BACK    = "dt29_back"
    BUILDING_DOWNTOWN_CORE_29_FRONT   = "dt29_front"
    BUILDING_DOWNTOWN_CORE_29_LEFT    = "dt29_left"
    BUILDING_DOWNTOWN_CORE_29_RIGHT   = "dt29_right"

    # dt33a
    BUILDING_DOWNTOWN_CORE_33A_BACK   = "dt33a_back"
    BUILDING_DOWNTOWN_CORE_33A_FRONT  = "dt33a_front"
    BUILDING_DOWNTOWN_CORE_33A_LEFT   = "dt33a_left"
    BUILDING_DOWNTOWN_CORE_33A_RIGHT  = "dt33a_right"
    BUILDING_DOWNTOWN_CORE_33A_ROOF   = "dt33a_roof"

    # dt33d
    BUILDING_DOWNTOWN_CORE_33D_BACK   = "dt33d_back"
    BUILDING_DOWNTOWN_CORE_33D_FRONT  = "dt33d_front"
    BUILDING_DOWNTOWN_CORE_33D_LEFT   = "dt33d_left"
    BUILDING_DOWNTOWN_CORE_33D_RIGHT  = "dt33d_right"  # same texture as _left
    BUILDING_DOWNTOWN_CORE_33D_ROOF   = "dt33d_roof"

    # dt38
    BUILDING_DOWNTOWN_CORE_38_BACK    = "dt38_back"
    BUILDING_DOWNTOWN_CORE_38_FRONT   = "dt38_front"
    BUILDING_DOWNTOWN_CORE_38_LEFT    = "dt38_left"
    BUILDING_DOWNTOWN_CORE_38_RIGHT   = "dt38_right"
    BUILDING_DOWNTOWN_CORE_38_ROOF    = "dt38_roof"

    # dt40
    BUILDING_DOWNTOWN_CORE_40_BACK    = "dt40_back"
    BUILDING_DOWNTOWN_CORE_40_FRONT   = "dt40_front"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_40_LEFT    = "dt40_left"   # same texture as _back
    BUILDING_DOWNTOWN_CORE_40_RIGHT   = "dt40_right"  # same texture as _back
    BUILDING_DOWNTOWN_CORE_40_ROOF_NO_VISIBILITY = "dt40_roof"

    # dt41
    BUILDING_DOWNTOWN_CORE_41_BACK    = "dt41_back"
    BUILDING_DOWNTOWN_CORE_41_FRONT   = "dt41_front"
    BUILDING_DOWNTOWN_CORE_41_LEFT    = "dt41_left"
    BUILDING_DOWNTOWN_CORE_41_RIGHT   = "dt41_right"
    BUILDING_DOWNTOWN_CORE_41_ROOF_NO_VISIBILITY = "dt41_roof"

    # dt54
    BUILDING_DOWNTOWN_CORE_54_BACK    = "dt54_back"
    BUILDING_DOWNTOWN_CORE_54_FRONT   = "dt54_front"
    BUILDING_DOWNTOWN_CORE_54_LEFT    = "dt54_left"
    BUILDING_DOWNTOWN_CORE_54_RIGHT   = "dt54_right"  # same texture as _left
    BUILDING_DOWNTOWN_CORE_54_ROOF    = "dt54_roof"

    # dt56
    BUILDING_DOWNTOWN_CORE_56_BACK    = "dt56_back"
    BUILDING_DOWNTOWN_CORE_56_FRONT   = "dt56_front"
    BUILDING_DOWNTOWN_CORE_56_LEFT    = "dt56_left"
    BUILDING_DOWNTOWN_CORE_56_RIGHT   = "dt56_right"
    BUILDING_DOWNTOWN_CORE_56_ROOF    = "dt56_roof"

    # ── Freeway ───────────────────────────────────────────────────────────────
    WALL_FREEWAY_2                    = "freewaywall02"
    WALL_FREEWAY_4                    = "freewaywall04"  # same texture as _2

    # ── Hyde Park / Hillside Back (HB) ───────────────────────────────────────
    WAREHOUSE_HILLSIDE_BACK_1_UNUSED  = "hbwhse01"
    WAREHOUSE_HILLSIDE_BACK_2         = "hbwhse02"

    # ── Hyde Park / Hillside Fringe (HF) ─────────────────────────────────────
    ALLEY_HILLSIDE_1                  = "hfalley01"
    ALLEY_HILLSIDE_2                  = "hfalley02"

    BUILDING_HILLSIDE_1               = "hfbldg01"
    BUILDING_HILLSIDE_2               = "hfbldg02"
    BUILDING_HILLSIDE_4               = "hfbldg04"

    CONDO_HILLSIDE_1                  = "hfcondo01"
    CONDO_HILLSIDE_2_UNUSED           = "hfcondo02"
    CONDO_HILLSIDE_3_UNUSED           = "hfcondo03"

    SHOP_HILLSIDE_DELI                = "hfdeli"
    INN_HILLSIDE                      = "hfinn"
    SHOP_HILLSIDE_LIQUOR_UNUSED       = "hfliquor"
    OFFICE_HILLSIDE_1                 = "hfoffice01"
    OFFICE_HILLSIDE_2                 = "hfoffice02"
    SHOP_HILLSIDE_PIZZA_UNUSED        = "hfpizza"
    SHOP_HILLSIDE_UNUSED              = "hfshop"
    SHOP_HILLSIDE_1                   = "hfshop01"
    SHOP_HILLSIDE_2                   = "hfshop02"
    SHOP_HILLSIDE_3                   = "hfshop03"
    SHOP_HILLSIDE_4                   = "hfshop04"

    WALL_HILLSIDE_1                   = "hfwall01"

    WAREHOUSE_HILLSIDE_1              = "hfwhse01"
    WAREHOUSE_HILLSIDE_2_UNUSED       = "hfwhse02"
    WAREHOUSE_HILLSIDE_3_UNUSED       = "hfwhse03"
    WAREHOUSE_HILLSIDE_4              = "hfwhse04"

    # ── Industrial Back (IB) ─────────────────────────────────────────────────
    FACTORY_INDUSTRIAL_BACK_1         = "ibfact01"
    FACTORY_INDUSTRIAL_BACK_2         = "ibfact02"
    FACTORY_INDUSTRIAL_BACK_3         = "ibfact03"
    FACTORY_INDUSTRIAL_BACK_4         = "ibfact04"

    # ── Industrial Fringe (IF) ───────────────────────────────────────────────
    BAR_INDUSTRIAL                    = "ifbar"

    BUILDING_INDUSTRIAL_1             = "ifbldg01"
    BUILDING_INDUSTRIAL_2             = "ifbldg02"
    BUILDING_INDUSTRIAL_3             = "ifbldg03"
    BUILDING_INDUSTRIAL_4             = "ifbldg04"
    BUILDING_INDUSTRIAL_5             = "ifbldg05"
    BUILDING_INDUSTRIAL_6             = "ifbldg06"

    DINER_INDUSTRIAL_1                = "ifdiner"
    DINER_INDUSTRIAL_2                = "ifdiner02"

    FACTORY_INDUSTRIAL_1              = "iffact01"
    HOTEL_INDUSTRIAL                  = "ifhotel"
    WALL_INDUSTRIAL_1                 = "ifwall01"

    WAREHOUSE_INDUSTRIAL_1            = "ifwhse01"
    WAREHOUSE_INDUSTRIAL_2            = "ifwhse02"
    WAREHOUSE_INDUSTRIAL_3            = "ifwhse03"

    # ── Old Town Back (OB) ───────────────────────────────────────────────────
    BUILDING_OLDTOWN_BACK_10          = "obbldg10"
    BUILDING_OLDTOWN_BACK_11          = "obbldg11"
    LOT_EMPTY_OLDTOWN_UNUSED          = "obelot"
    THEATER_OLDTOWN                   = "obtheater"

    # ── Old Town Fringe (OF) ─────────────────────────────────────────────────
    APARTMENT_OLDTOWN                 = "ofapt"
    BANK_OLDTOWN_UNUSED               = "ofbank"

    BUILDING_OLDTOWN_1                = "ofbldg01"
    BUILDING_OLDTOWN_2                = "ofbldg02"   # orange brick with many windows
    BUILDING_OLDTOWN_3                = "ofbldg03"

    BROWNSTONE_OLDTOWN_1              = "ofbrstn01"
    BROWNSTONE_OLDTOWN_2              = "ofbrstn02"
    BROWNSTONE_OLDTOWN_3              = "ofbrstn03"
    BROWNSTONE_OLDTOWN_4              = "ofbrstn04"
    BROWNSTONE_OLDTOWN_5              = "ofbrstn05"
    BROWNSTONE_OLDTOWN_6              = "ofbrstn06"
    BROWNSTONE_OLDTOWN_8              = "ofbrstn08"

    HOME_OLDTOWN_1                    = "ofhome01"
    HOME_OLDTOWN_2                    = "ofhome02"
    HOME_OLDTOWN_3                    = "ofhome03"
    HOME_OLDTOWN_5                    = "ofhome05"
    HOME_OLDTOWN_6                    = "ofhome06"
    HOME_OLDTOWN_7                    = "ofhome07"
    HOME_OLDTOWN_10                   = "ofhome10"
    HOME_OLDTOWN_11                   = "ofhome11"

    SHOP_OLDTOWN_1                    = "ofshop01"
    SHOP_OLDTOWN_2                    = "ofshop02"
    SHOP_OLDTOWN_3                    = "ofshop03"
    SHOP_OLDTOWN_4                    = "ofshop04"
    SHOP_OLDTOWN_5                    = "ofshop05"
    SHOP_OLDTOWN_6                    = "ofshop06"
    SHOP_OLDTOWN_7                    = "ofshop07"
    SHOP_OLDTOWN_10_UNUSED            = "ofshop10"

    SHOP_OLDTOWN_SODA                 = "ofsodashop"

    # ── Residential Fringe (RF) ──────────────────────────────────────────────
    BUILDING_RESIDENTIAL_1            = "rfbldg01"
    BUILDING_RESIDENTIAL_2            = "rfbldg02"
    BUILDING_RESIDENTIAL_3            = "rfbldg03"
    BUILDING_RESIDENTIAL_4            = "rfbldg04"
    BUILDING_RESIDENTIAL_5            = "rfbldg05"
    BUILDING_RESIDENTIAL_6            = "rfbldg06"
    BUILDING_RESIDENTIAL_7            = "rfbldg07"
    BUILDING_RESIDENTIAL_8            = "rfbldg08"
    BUILDING_RESIDENTIAL_9            = "rfbldg09"
    BUILDING_RESIDENTIAL_10           = "rfbldg10"
    BUILDING_RESIDENTIAL_11           = "rfbldg11"
    BUILDING_RESIDENTIAL_12           = "rfbldg12"
    BUILDING_RESIDENTIAL_13           = "rfbldg13"
    BUILDING_RESIDENTIAL_14           = "rfbldg14"
    BUILDING_RESIDENTIAL_16           = "rfbldg16"
    BUILDING_RESIDENTIAL_17           = "rfbldg17"
    BUILDING_RESIDENTIAL_18           = "rfbldg18"

    # ── Track / Rail ─────────────────────────────────────────────────────────
    RAIL_WATER                        = "t_rail01"

    # ── The Loop Fringe (TF) ─────────────────────────────────────────────────
    APARTMENT_THELOOP_1               = "tfapt01"
    APARTMENT_THELOOP_3               = "tfapt03"
    APARTMENT_THELOOP_5               = "tfapt05"
    APARTMENT_THELOOP_6               = "tfapt06"
    APARTMENT_THELOOP_7               = "tfapt07"

    BUILDING_THELOOP_1                = "tfbldg01"
    BUILDING_THELOOP_2                = "tfbldg02"
    BUILDING_THELOOP_3                = "tfbldg03"
    BUILDING_THELOOP_4                = "tfbldg04"
    BUILDING_THELOOP_5                = "tfbldg05"
    BUILDING_THELOOP_6                = "tfbldg06"
    BUILDING_THELOOP_7                = "tfbldg07"

    SHOP_THELOOP_CD_STORE             = "tfcdshop"
    CLUB_THELOOP                      = "tfclub"
    SHOP_THELOOP_DEPARTMENT_STORE     = "tfdeptstr01"
    SHOP_THELOOP_DRUGSTORE            = "tfdrug"

    OFFICE_THELOOP_1                  = "tfoff01"
    OFFICE_THELOOP_2                  = "tfoff02"
    OFFICE_THELOOP_3                  = "tfoff03"
    OFFICE_THELOOP_4                  = "tfoff04"

    SUPERMARKET_THELOOP               = "tfsmrkt"
    SUPERMARKET_THELOOP_2             = "tfsmrkt02"

    WALL_THELOOP_1                    = "tfwall01"

    # ── Tunnels ───────────────────────────────────────────────────────────────
    TUNNEL_1                          = "tunnel01"
    TUNNEL_2                          = "tunnel02"
    TUNNEL_3                          = "tunnel03"
    TUNNEL_4                          = "tunnel04"

    # ── Miscellaneous ─────────────────────────────────────────────────────────
    RAMP                              = "ramp01"

    # ── No Visibility ─────────────────────────────────────────────────────────
    # Texture files exist but these facades are never visible during normal gameplay,
    # either due to camera angle (DT roofs) or unknown reasons (bluelight, tfskyway).
    BLUELIGHT_NO_VISIBILITY           = "bluelight"
    SKYWAY_THELOOP_NO_VISIBILITY      = "tfskyway"


class Facade:
    BUILDING_ORANGE_WITH_WINDOWS = "ofbldg02"
    
    WALL_FREEWAY = "freewaywall02"
    RAIL_WATER = "t_rail01"
    
    SHOP_SUIT = "dfsuitstore"
    SHOP_PIZZA = "hfpizza"
    SHOP_SODA = "ofsodashop"
    SHOP_LIQUOR = "cfliquor"
    
    HOME_ONE = "OFHOME01"
    HOME_TWO = "OFHOME02"
    HOME_THREE = "OFHOME03"


# TODO: transform to hex
class FcdFlags:    
    FRONT = 1            
    FRONT_BRIGHT = 3     
    
    FRONT_LEFT = 9  
    FRONT_BACK = 25
    FRONT_RIGHT = 49
    FRONT_ROOFTOP = 33
    
    FRONT_LEFT_ROOF = 105
    FRONT_RIGHT_ROOF = 145
    FRONT_LEFT_RIGHT = 217
    
    FRONT_LEFT_RIGHT_ROOF = 249
    FRONT_BACK_ROOF = 1057
    FRONT_RIGHT_BACK = 1073
    FRONT_LEFT_ROOF_BACK = 1129
    FRONT_RIGHT_ROOF_BACK = 1201
    
    ALL_SIDES = 1273
    
    FRONT_LEFT_ALT = 73  
    FRONT_RIGHT_ROOF_ALT = 177 
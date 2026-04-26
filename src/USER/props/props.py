from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.file_formats import Axis
from src.game.waypoints.constants import Rotation

prop_list = [

    # ── Bridges (30 / 40 / 6 wide; 33 deep) ──────────────────────────────────
    {"name": Prop.BRIDGE_SLIM,              "offset": (  0, 0, 180), "angle": Rotation.NORTH},
    {"name": Prop.BRIDGE_WIDE,              "offset": ( 55, 0, 180), "angle": Rotation.NORTH},
    {"name": Prop.BRIDGE_BUILDING,          "offset": (107, 0, 160), "angle": Rotation.NORTH},

    # ── El Train structures (50 / 11 / 16 wide; 1–3 deep) ────────────────────
    {"name": Prop.ELTRAIN,                  "offset": (140, 0, 160), "angle": Rotation.NORTH},
    {"name": Prop.ELTRAIN_SUPPORT_SLIM,     "offset": (180, 0, 160), "angle": Rotation.NORTH},
    {"name": Prop.ELTRAIN_SUPPORT_WIDE,     "offset": (220, 0, 160), "angle": Rotation.NORTH},

    # ── Chinatown gate (29 wide × 4 deep) ────────────────────────────────────
    {"name": Prop.CHINATOWN_GATE,           "offset": (  0, 0, 205), "angle": Rotation.NORTH},
    # Trailer (4 wide × 16 deep after 270°)
    {"name": Prop.TRAILER,                  "offset": ( 44, 0, 205), "angle": Rotation.NORTH},
    # Construction walls (7–7 wide × 7–8 deep)
    {"name": Prop.WALL_CONSTRUCTION_A,      "offset": ( 60, 0, 205), "angle": Rotation.NORTH},
    {"name": Prop.WALL_CONSTRUCTION_B,      "offset": ( 78, 0, 205), "angle": Rotation.NORTH},
    {"name": Prop.WALL_CONSTRUCTION_C,      "offset": ( 96, 0, 205), "angle": Rotation.NORTH},
    # Plane (no collision mesh; placed last with room to spare)
    {"name": Prop.PLANE_LARGE,              "offset": (120, 0, 300), "angle": Rotation.NORTH},
    {"name": Prop.CRANE,                    "offset": (120, 0, 205), "angle": Rotation.NORTH},

    # ── Crossgates (0.1 wide × 13 deep after 90°; base: 1 × 1) ──────────────
    {"name": Prop.CROSSGATE,                "offset": (  0, 0, 235), "angle": Rotation.NORTH},
    {"name": Prop.CROSSGATE_SHORT,          "offset": ( 12, 0, 235), "angle": Rotation.NORTH},
    {"name": Prop.CROSSGATE_BASE,           "offset": ( 22, 0, 235), "angle": Rotation.NORTH},
    # Flat walls (0.2–0.4 wide × 5–9 deep after 90°)
    {"name": Prop.WALL_TALL,                "offset": ( 33, 0, 235), "angle": Rotation.NORTH},
    {"name": Prop.WALL_TALL_B,              "offset": ( 46, 0, 235), "angle": Rotation.NORTH},
    {"name": Prop.WALL_WIDE,                "offset": ( 57, 0, 235), "angle": Rotation.NORTH},
    {"name": Prop.WALL_LOW,                 "offset": ( 67, 0, 235), "angle": Rotation.NORTH},
    # Mall glass (9 wide)
    {"name": Prop.MALL_GLASS,               "offset": ( 82, 0, 235), "angle": Rotation.NORTH},

    # ── Traffic lights (7 / 10 wide × 0.5 deep) ──────────────────────────────
    {"name": Prop.TRAFFIC_LIGHT_SINGLE,     "offset": (  0, 0, 253), "angle": Rotation.NORTH},
    {"name": Prop.TRAFFIC_LIGHT_DUAL,       "offset": ( 14, 0, 253), "angle": Rotation.NORTH},
    # Highway signs (11 wide × 0.9 deep) — 4 variants
    {"name": Prop.SIGN_HIGHWAY_OLDTOWN,     "offset": ( 34, 0, 253), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_HIGHWAY_LAKESHORE,   "offset": ( 55, 0, 253), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_HIGHWAY_DOWNTOWN,    "offset": ( 76, 0, 253), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_HIGHWAY_CHINATOWN,   "offset": ( 97, 0, 253), "angle": Rotation.NORTH},

    # ── Street lights (5–6 wide × 0.8 deep) ──────────────────────────────────
    {"name": Prop.LIGHT_BLUE_SIDEWALK,      "offset": (  0, 0, 265), "angle": Rotation.NORTH},
    {"name": Prop.LIGHT_GREEN_SIDEWALK,     "offset": ( 10, 0, 265), "angle": Rotation.NORTH},
    {"name": Prop.LIGHT_RED_SIDEWALK,       "offset": ( 20, 0, 265), "angle": Rotation.NORTH},
    {"name": Prop.LIGHT_SIDEWALK,           "offset": ( 30, 0, 265), "angle": Rotation.NORTH},
    {"name": Prop.LIGHT_HIGHWAY,            "offset": ( 37, 0, 265), "angle": Rotation.NORTH},

    # ── Road barriers & safety (0.5–1.3 wide; 1–4 deep) ─────────────────────
    {"name": Prop.CRASH_CAN,                "offset": (  0, 0, 275), "angle": Rotation.NORTH},
    {"name": Prop.BARRICADE,                "offset": (  7, 0, 275), "angle": Rotation.NORTH},
    {"name": Prop.BARRICADE_SAWHORSE,       "offset": ( 14, 0, 275), "angle": Rotation.NORTH},
    {"name": Prop.CONE,                     "offset": ( 20, 0, 275), "angle": Rotation.NORTH},
    {"name": Prop.BARREL_BLUE,              "offset": ( 25, 0, 275), "angle": Rotation.NORTH},

    # ── Street furniture (0.5–3.5 wide; 1–3 deep) ────────────────────────────
    {"name": Prop.BENCH,                    "offset": (  0, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.BENCH_MALL,               "offset": (  7, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.BIN,                      "offset": ( 14, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.DUMPSTER,                 "offset": ( 21, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.MAILBOX,                  "offset": ( 29, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.PARKING_METER,            "offset": ( 35, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.FIRE_HYDRANT,             "offset": ( 41, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.TELEPHONE_POLE,           "offset": ( 48, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.CALLBOX_EMERGENCY,        "offset": ( 57, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.BUS_STOP,                 "offset": ( 63, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.PHONE_BOOTH,              "offset": ( 69, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.PAYPHONE,                 "offset": ( 75, 0, 285), "angle": Rotation.NORTH},
    {"name": Prop.PLANT,                    "offset": ( 81, 0, 285), "angle": Rotation.NORTH},

    # ── Small street signs (0.7–1.8 wide × 0.1 deep) ─────────────────────────
    {"name": Prop.SIGN_STOP,                "offset": (  0, 0, 297), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_WRONG_WAY,           "offset": (  5, 0, 297), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_DO_NOT_ENTER,        "offset": ( 11, 0, 297), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_ONE_WAY_RIGHT,       "offset": ( 17, 0, 297), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_ONE_WAY_LEFT,        "offset": ( 23, 0, 297), "angle": Rotation.NORTH},
    {"name": Prop.SIGN_LEFT_TURN_ONLY,      "offset": ( 29, 0, 297), "angle": Rotation.NORTH},

    # ── Newspaper boxes (≈0.6 wide × 0.6 deep) ───────────────────────────────
    {"name": Prop.NEWSPAPER_BOX_BLUE,       "offset": (  0, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.NEWSPAPER_BOX_RED,        "offset": (  4, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.NEWSPAPER_BOX_YELLOW,     "offset": (  8, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.NEWSPAPER_BOX_BLUE_2,     "offset": ( 12, 0, 307), "angle": Rotation.NORTH},
    # Crates & trash (0.5–4.4 wide × 0.8–2 deep)
    {"name": Prop.BOX_METAL,                "offset": ( 18, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.BOX_SINGLE,               "offset": ( 23, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.BOX_STACK,                "offset": ( 29, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.BOX_STACK_ALLEY,          "offset": ( 37, 0, 307), "angle": Rotation.NORTH},
    {"name": Prop.TRASH_BOXES,              "offset": ( 49, 0, 307), "angle": Rotation.NORTH},

    # ── Trees (7 / 12 wide; billboards) + Sailboat ───────────────────────────
    {"name": Prop.TREE_SLIM,                "offset": (  0, 0, 318), "angle": Rotation.NORTH},
    {"name": Prop.TREE_WIDE,                "offset": ( 17, 0, 318), "angle": Rotation.NORTH},
    {"name": Prop.SAILBOAT,                 "offset": ( 37, 0, 318), "angle": Rotation.NORTH},

]

random_props = []


# ── Original props ────────────────────────────────────────────────────────────
trailer_set = {
    "offset": (60, 0.0, 70),
    "end": (60, 0.0, -50),
    "name": Prop.TRAILER,
    "separator": Axis.Longest
}

bridge_orange_buildling = {
    "offset": (35, 12.0, -70),
    "angle": Rotation.NORTH,
    "name": Prop.BRIDGE_SLIM
}

prop_list += [trailer_set, bridge_orange_buildling]

random_trees = {
    "name": Prop.TREE_SLIM,
    "count": 20,
    "seed": 123,
    "area": ((65, 0, -65), (135, 0, 65)),
}

random_sailboats = {
    "name": Prop.SAILBOAT,
    "count": 19,
    "seed": 99,
    "area": ((55, 0, -205), (135, 0, -145)),
}

random_cars = {
    "name": [
        PlayerCar.VW_BEETLE, PlayerCar.CITY_BUS, PlayerCar.CADILLAC, PlayerCar.POLICE, PlayerCar.FORD_F350,
        PlayerCar.FASTBACK, PlayerCar.MUSTANG_GT, PlayerCar.ROADSTER, PlayerCar.PANOZ_GTR1, PlayerCar.SEMI
    ],
    "seed": 1,
    "num_props": 2,
    "area": ((52, 0, -136), (138, 0, -68)),
    "separator": 10.0,
}

random_props = [random_trees, random_sailboats, random_cars]

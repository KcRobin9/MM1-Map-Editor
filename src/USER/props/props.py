from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.constants import HUGE
from src.constants.file_formats import Axis

from src.game.races.constants import RaceModeNum
from src.game.waypoints.constants import Rotation


# ─── Non-randomized props ────────────────────────────────────────────────────

china_gate = {
    "offset": (0, 0.0, -20),
    "angle": Rotation.SOUTH,          # face: (1 * HUGE, 0.0, -20) → pointing south
    "name": Prop.CHINATOWN_GATE,
    "race": [RaceModeNum.CIRCUIT_0],  # was race_mode: CIRCUIT, race_num: 0
}

trailer_set = {
    "offset": (52, 0.0, 65),
    "end": (52, 0.0, -65),
    "name": Prop.TRAILER,
    "separator": Axis.Longest,
}

bridge_orange_building = {
    "offset": (35, 12.0, -70),
    "angle": Rotation.EAST,           # face: (35 * HUGE, 12.0, -70) → pointing east
    "name": Prop.BRIDGE_SLIM,
}

start_barricades_one = {
    "offset": (-24.0, 0.0, 86.0),
    "end": (24.0, 0.0, 86.0),
    "name": Prop.BARRICADE,
    "separator": Axis.Longest,
}

start_barricades_two = {
    "offset": (-23.75, 0.0, 86.0),
    "end": (-23.75, 0.0, 70.0),
    "name": Prop.BARRICADE,
    "separator": Axis.Longest,
}

start_barricades_three = {
    "offset": (24.0, 0.0, 86.0),
    "end": (24.0, 0.0, 70.0),
    "name": Prop.BARRICADE,
    "separator": Axis.Longest,
}

wrong_way_one = {
    "offset": (0.0, -15.0, -294.5),
    "angle": Rotation.SOUTH,          # face: (0.0, -15.0, 2570.0) → z-positive = south
    "name": Prop.WRONG_WAY,
}

wrong_way_two = {
    "offset": (0.0, -15.0, -276.2),
    "angle": Rotation.SOUTH,          # face: (0.0, -15.0, 2750.0) → z-positive = south
    "name": Prop.WRONG_WAY,
}

prop_list = [
    china_gate,
    trailer_set,
    bridge_orange_building,
    start_barricades_one,
    start_barricades_two,
    start_barricades_three,
    wrong_way_one,
    wrong_way_two,
]


# ─── Randomized props ─────────────────────────────────────────────────────────

random_trees = {
    "name": Prop.TREE_SLIM,
    "count": 20,
    "seed": 123,
    "num_props": 1,
    "area": ((65, 0, -65), (135, 0, 65)),
}

random_sailboats = {
    "name": Prop.SAILBOAT,
    "count": 19,
    "seed": 99,
    "num_props": 1,
    "area": ((55, 0, -205), (135, 0, -145)),
}

random_cars = {
    "name": [
        PlayerCar.VW_BEETLE, PlayerCar.CITY_BUS, PlayerCar.CADILLAC,
        PlayerCar.POLICE, PlayerCar.FORD_F350, PlayerCar.FASTBACK,
        PlayerCar.MUSTANG_GT, PlayerCar.ROADSTER, PlayerCar.PANOZ_GTR1, PlayerCar.SEMI,
    ],
    "seed": 1,
    "num_props": 2,
    "area": ((52, 0, -136), (138, 0, -68)),
    "separator": 10.0,
}

random_trash = {
    "name": [
        Prop.DUMPSTER, Prop.TRASH_BOXES, Prop.CONE,
        Prop.CRASH_CAN, Prop.PLANT, Prop.MAILBOX, Prop.SAWHORSE,  # "tpsawhrslt" → SAWHORSE     geen idee meer wat deze was
    ],
    "seed": 2,
    "num_props": 5,
    "area": ((195, 0, -545), (230, 0, 390)),  # note: z_range was (390, -545), swapped to (min, max)
}

random_props = [random_trees, random_sailboats, random_cars, random_trash]
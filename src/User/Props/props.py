from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.constants import HUGE
from src.constants.file_formats import Axis

from src.game.races.constants import RaceModeNum


trailer_set = {
    "offset": (60, 0.0, 70),
    "end": (60, 0.0, -50),
    "name": Prop.TRAILER,
    "separator": Axis.X,
}

bridge_orange_buildling = {
    "offset": (35, 12.0, -70),
    "face": (35 * HUGE, 12.0, -70),
    "name": Prop.BRIDGE_SLIM
}

# Race specific props
trash_boxes = {
    "offset": (0, 0.0, 0),
    "face": (HUGE, 0.0, 0),
    "name": Prop.TRASH_BOXES,
    "race": [RaceModeNum.CIRCUIT_0, RaceModeNum.CIRCUIT_1]  # Also possible: RaceModeNum.CIRCUIT_ALL
}

# Put the non-randomized props here
prop_list = [trailer_set, bridge_orange_buildling, trash_boxes]


# Put the randomized props here (you will add them to the list "random props")
#TODO: also support RaceMode and RaceModeNum here
random_trees = {
    "offset_y": 0.0,
    "name": [Prop.TREE_SLIM] * 20
}

random_sailboats = {
    "offset_y": 0.0,
    "name": [Prop.SAILBOAT] * 19
}

random_cars = {
    "offset_y": 0.0,
    "separator": 10.0,
    "name": [
        PlayerCar.VW_BEETLE, PlayerCar.CITY_BUS, PlayerCar.CADILLAC, PlayerCar.CRUISER, PlayerCar.FORD_F350,
        PlayerCar.FASTBACK, PlayerCar.MUSTANG99, PlayerCar.ROADSTER, PlayerCar.PANOZ_GTR_1, PlayerCar.SEMI
    ]
}

# Configure the random props here
random_props = [
    {"seed": 123, "num_props": 1, "props_dict": random_trees, "x_range": (65, 135), "z_range": (-65, 65)},
    {"seed": 99, "num_props": 1, "props_dict": random_sailboats, "x_range": (55, 135), "z_range": (-145, -205)},
    {"seed": 1, "num_props": 2, "props_dict": random_cars, "x_range": (52, 138), "z_range": (-136, -68)}
]
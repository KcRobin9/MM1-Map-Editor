from src.Constants.props import Prop
from src.Constants.constants import HUGE
from src.Constants.races import RaceMode
from src.Constants.vehicles import PlayerCar


trailer_set = {
    "offset": (60, 0.0, 70),
    "end": (60, 0.0, -50),
    "name": Prop.TRAILER,
    "separator": "x"  # Use the {}-axis dimension of the object as the spacing between each prop
}

bridge_orange_buildling = {
    "offset": (35, 12.0, -70),
    "face": (35 * HUGE, 12.0, -70),
    "name": Prop.BRIDGE_SLIM
}

china_gate = {
    "offset": (0, 0.0, -20),
    "face": (1 * HUGE, 0.0, -20),
    "name": Prop.CHINATOWN_GATE,
    "race_mode": RaceMode.CIRCUIT,
    "race_num": 0  # Prop for CIRCUIT 0
}

# Put the non-randomized props here
prop_list = [trailer_set, bridge_orange_buildling, china_gate]


# Put the randomized props here (you will add them to the list "random props")
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
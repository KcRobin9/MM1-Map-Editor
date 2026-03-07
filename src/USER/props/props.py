from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.constants import HUGE
from src.constants.file_formats import Axis

from src.game.races.constants import RaceModeNum
from src.game.waypoints.constants import Rotation


car_angle_test = {
    "offset": (40, 0.0, -50),
    "angle": Rotation.NORTH_WEST,       #   -45.0, where North is z-negative
    "name": PlayerCar.CADILLAC,
}

trailer_set = {
    "offset": (60, 0.0, 70),
    "end": (60, 0.0, -50),
    "name": Prop.TRAILER,
    "separator": Axis.Longest  # Trailer dimensions: x=16.34, y=4.69, z=4.00 --> Axis.Longest returns x
}

bridge_orange_buildling = {
    "offset": (35, 12.0, -70),
    "angle": Rotation.NORTH,
    "name": Prop.BRIDGE_SLIM
}

# Race specific props
trash_boxes = {
    "offset": (0, 0.0, 0),
    "angle": Rotation.NORTH, 
    "name": Prop.TRASH_BOXES,
    "race": [RaceModeNum.CIRCUIT_0, RaceModeNum.CIRCUIT_1]  # Also possible: RaceModeNum.CIRCUIT_ALL
}

# Put the non-randomized props here
prop_list = [car_angle_test, trailer_set, bridge_orange_buildling, trash_boxes]


#TODO: also support RaceMode and RaceModeNum here
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
        PlayerCar.VW_BEETLE, PlayerCar.CITY_BUS, PlayerCar.CADILLAC, PlayerCar.POLICE, PlayerCar.FORD_F350,
        PlayerCar.FASTBACK, PlayerCar.MUSTANG_GT, PlayerCar.ROADSTER, PlayerCar.PANOZ_GTR1, PlayerCar.SEMI
    ],
    "seed": 1,
    "num_props": 2,
    "area": ((52, 0, -136), (138, 0, -68)),
    "separator": 10.0,
}

random_props = [random_trees, random_sailboats, random_cars]
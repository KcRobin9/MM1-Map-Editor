from src.constants.facades import Facade, FcdFlags


orange_building_one = {
	"flags": FcdFlags.FRONT,
	"offset": (-10.0, 0.0, -50.0),
	"end": (10, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_OLDTOWN_2,
	"axis": "x"
}

orange_building_two = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (10.0, 0.0, -70.0),
	"end": (-10, 0.0, -70.0),
	"separator": 10.0,
	"name": Facade.BUILDING_OLDTOWN_2,
	"axis": "x"
}

orange_building_three = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -70.0),
	"end": (-10.0, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_OLDTOWN_2,
	"axis": "z"
}

orange_building_four = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (10.0, 0.0, -50.0),
	"end": (10.0, 0.0, -70.0),
	"name": Facade.BUILDING_OLDTOWN_2,
    "axis": "z",
    "separator": 10.0
}

# Pack all Facades for processing
facade_list = [orange_building_one, orange_building_two, orange_building_three, orange_building_four]
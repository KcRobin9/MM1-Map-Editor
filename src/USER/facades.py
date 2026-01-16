from src.constants.facades import Facade, FcdFlags


#* NOTES:
#* Separator: (max_x - min_x) / separator(value) = number of facades
#* Sides: omitted by default, but can be set (relates to lighting, but behavior is not clear)
#* Scale: enlarges or shrinks non-fixed facades

#* All information about Facades (including pictures) can be found in: 
# ... / docs / visual_reference / facades   

# Flags (if applicable, consult the documentation for more info)

    
orange_building_one = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -50.0),
	"end": (10, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "x"
}

orange_building_two = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (10.0, 0.0, -70.0),
	"end": (-10, 0.0, -70.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "x"
}

orange_building_three = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -70.0),
	"end": (-10.0, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "z"
}

orange_building_four = {
	"flags": FcdFlags.FRONT_BRIGHT,
	"offset": (10.0, 0.0, -50.0),
	"end": (10.0, 0.0, -70.0),
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "z",
    "separator": 10.0
}

# Pack all Facades for processing
facade_list = [orange_building_one, orange_building_two, orange_building_three, orange_building_four]
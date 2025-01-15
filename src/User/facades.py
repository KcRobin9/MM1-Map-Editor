from src.Constants.facades import Facade


#* NOTES:
#* Separator: (max_x - min_x) / separator(value) = number of facades
#* Sides: omitted by default, but can be set (relates to lighting, but behavior is not clear)
#* Scale: enlarges or shrinks non-fixed facades

#* All information about Facades (including pictures) can be found in: 
# ... / UserResources / FACADES / ...        
# ... / UserResources / FACADES / FACADE pictures

# Flags (if applicable, consult the documentation for more info)
# TODO: transform to hex
FRONT = 1  # Sometimes 1 is also used for the full model
FRONT_BRIGHT = 3

FRONT_LEFT = 9
FRONT_BACK = 25
FRONT_ROOFTOP = 33
FRONT_LEFT = 41  # Value 73 is also commonly used for this
FRONT_RIGHT = 49

FRONT_LEFT_ROOF = 105 
FRONT_RIGHT_ROOF = 145  # Value 177 is also commonly used for this
FRONT_LEFT_RIGHT = 217
FRONT_LEFT_RIGHT_ROOF = 249

FRONT_BACK_ROOF = 1057
FRONT_RIGHT_BACK = 1073
FRONT_LEFT_ROOF_BACK = 1129
FRONT_RIGHT_ROOF_BACK = 1201
ALL_SIDES = 1273

    
orange_building_one = {
	"flags": FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -50.0),
	"end": (10, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "x"
}

orange_building_two = {
	"flags": FRONT_BRIGHT,
	"offset": (10.0, 0.0, -70.0),
	"end": (-10, 0.0, -70.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "x"
}

orange_building_three = {
	"flags": FRONT_BRIGHT,
	"offset": (-10.0, 0.0, -70.0),
	"end": (-10.0, 0.0, -50.0),
	"separator": 10.0,
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
	"axis": "z"
}

orange_building_four = {
	"flags": FRONT_BRIGHT,
	"offset": (10.0, 0.0, -50.0),
	"end": (10.0, 0.0, -70.0),
	"name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "z",
    "separator": 10.0
}

# Pack all Facades for processing
facade_list = [orange_building_one, orange_building_two, orange_building_three, orange_building_four]
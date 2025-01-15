from src.Constants.props import Prop
from src.Constants.constants import YES, NO
from src.Constants.races import IntersectionType


f"""
The following variables are OPTIONAL:
Intersection Type, defaults to: {IntersectionType.CONTINUE}
(possbile types:
{IntersectionType.STOP}, {IntersectionType.STOP_LIGHT}, {IntersectionType.YIELD}, {IntersectionType.CONTINUE})

Stop Light Name, defaults to: {Prop.STOP_LIGHT_SINGLE}
(possbile names: {Prop.STOP_SIGN}, {Prop.STOP_LIGHT_SINGLE}, {Prop.STOP_LIGHT_DUAL})

Stop Light Positions, defaults to: {(0, 0, 0)}

Traffic Blocked, Ped Blocked, Road Divided, and Alley, all default to: {NO}
(possbile values: {YES}, {NO})

# Stop Lights will only show if the Intersection Type is {IntersectionType.STOP_LIGHT}
"""

main_west = {
    "street_name": "main_west",
    "vertices": [
        (0.0, 0.0, 77.5),  # x, y, z
        (0.0, 0.0, 70.0),
        (0.0, 0.0, 10.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, -10.0),
        (0.0, 0.0, -70.0),
        (0.0, 0.0, -70.0),
        (0.0, 0.0, -100.0)
    ]
}

main_grass_horz = {
    "street_name": "main_grass_horz",
    "vertices": [
        (0.0, 0.0, -100.0),
        (20.0, 0.0, -100.0),
        (25.0, 0.0, -100.0),
        (30.0, 0.0, -100.0),
        (35.0, 0.0, -100.0),
        (40.0, 0.0, -100.0),
        (45.0, 0.0, -100.0),
        (50.0, 0.0, -100.0),
        (95.0, 0.0, -110.0)
    ]
}

main_barricade_wood = {
    "street_name": "barricade_wood",
    "vertices": [
        (95.0, 0.0, -110.0),
        (95.0, 0.0, -70.0),
        (100.0, 0.0, -50.0),
        (105.0, 0.0, -30.0),
        (110.0, 0.0, -10.0),
        (115.0, 0.0, 10.0),
        (120.0, 0.0, 30.0),
        (125.0, 0.0, 50.0),
        (130.0, 0.0, 70.0),
        (40.0, 0.0, 100.0)
    ]
}

double_triangle = {
    "street_name": "double_triangle",
    "vertices": [
        (40.0, 0.0, 100.0),
        (-50.0, 0.0, 135.0),
        (-59.88, 3.04, 125.52),
        (-84.62, 7.67, 103.28),
        (-89.69, 8.62, 62.57),
        (-61.94, 3.42, 32.00),
        (-20, 0.0, 70.0),
        (0.0, 0.0, 77.5)
    ]
}

orange_hill = {
    "street_name": "orange_hill",
    "vertices": [
        (0.0, 245.0, -850.0),
        (0.0, 0.0, -210.0),
        (0.0, 0.0, -155.0),
        (0.0, 0.0, -100.0)
    ]
}

# Street example with multiple lanes and all optional settings
street_example = {
    "street_name": "example",
    "lanes": {
        "lane_1": [
            (-40.0, 1.0, -20.0),
            (-30.0, 1.0, -30.0),
            (-30.0, 1.0, -50.0),
        ],
        "lane_2": [  # Add more lanes if desired
            (-40.0, 1.0, -20.0),
            (-40.0, 1.0, -30.0),
            (-40.0, 1.0, -50.0),
        ],
    },
    "intersection_types": [IntersectionType.STOP_LIGHT, IntersectionType.STOP_LIGHT],
    "stop_light_names": [Prop.STOP_LIGHT_DUAL, Prop.STOP_LIGHT_DUAL],
    "stop_light_positions": [
        (10.0, 0.0, -20.0),        # Offset 1
        (10.01, 0.0, -20.0),       # Direction 1
        (-10.0, 0.0, -20.0),       # Offset 2
        (-10.0, 0.0, -20.1)        # Direction 2
    ],
    "traffic_blocked": [NO, NO],
    "ped_blocked": [NO, NO],
    "road_divided": NO,
    "alley": NO
}

# Pack all AI streets for processing
street_list = [main_west, main_grass_horz, main_barricade_wood, double_triangle, orange_hill]
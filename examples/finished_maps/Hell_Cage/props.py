from src.constants.props import Prop
from src.constants.vehicles import PlayerCar
from src.constants.file_formats import Axis

from src.game.races.constants import RaceModeNum
from src.game.waypoints.constants import Rotation

prop_list = [

    # Line 1
    {
        "offset": (15.00, 0.23, 12.53),
        "end": (116.35, 7.38, 26.93),
        "name": Prop.BARRICADE,
        "separator": 4.0
    },

    # Line 2
    {
        "offset": (13.27, 0.11, 46.08),
        "end": (116.41, 7.39, 60.70),
        "name": Prop.BARRICADE,
        "separator": 4.0
    },

    # Line 3
    {
        "offset": (118.70, 7.45, 27.25),
        "end": (151.65, 7.45, 27.07),
        "name": Prop.BARRICADE,
        "separator": 4.0
    },

    # Line 4
    {
        "offset": (151.77, 7.45, 28.45),
        "end": (152.18, 7.46, 125.59),
        "name": Prop.BARRICADE,
        "separator": 4.0
    },

    {
    "offset": (117.72, 7.45, 62.06),
    "end": (117.45, 7.42, 90.54),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (151.75, 7.46, 125.42),
    "end": (117.89, 7.42, 125.39),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (116.17, 7.69, 125.45),
    "end": (66.40, 20.88, 122.97),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (116.43, 7.62, 91.42),
    "end": (65.64, 21.08, 89.07),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (115.81, 7.34, 27.03),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (117.44, 7.45, 27.14),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (152.12, 7.45, 27.12),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (151.99, 7.46, 125.52),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (117.87, 7.42, 125.74),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (119.43, 7.42, 125.66),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (64.70, 21.17, 88.31),
    "end": (63.56, 21.17, -18.19),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-89.31, 21.17, -18.28),
    "end": (-89.22, 21.17, 88.22),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (63.20, 21.17, -18.42),
    "end": (-54.12, 21.17, -18.21),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (-89.94, 21.17, 88.95),
    "end": (-124.17, 21.17, 89.06),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (65.12, 21.17, 123.41),
    "end": (-159.05, 21.15, 123.00),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (-158.92, 21.15, 122.87),
    "end": (-158.69, 21.15, 89.72),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-158.51, 21.22, 88.51),
    "end": (-158.21, 35.67, -77.91),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (-124.85, 21.20, 88.40),
    "end": (-124.66, 35.67, -77.92),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-158.66, 35.69, -78.94),
    "end": (-157.32, 33.48, -116.89),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-156.86, 33.51, -116.95),
    "end": (-124.33, 34.80, -116.54),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-115.18, 35.43, -116.43),
    "end": (92.39, 59.95, -101.26),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-123.23, 35.76, -79.48),
    "end": (91.38, 60.38, -67.39),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (93.47, 60.00, -100.71),
    "end": (129.31, 60.44, -98.88),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (129.22, 60.44, -97.99),
    "end": (117.05, 58.40, 112.14),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (92.16, 60.44, -66.51),
    "end": (85.75, 58.98, 72.96),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (117.38, 58.40, 112.30),
    "end": (-110.24, 59.34, 101.27),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (85.25, 58.98, 73.81),
    "end": (26.10, 58.58, 71.31),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (25.13, 58.60, 70.03),
    "end": (24.52, 59.55, -8.84),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (23.50, 59.56, -8.88),
    "end": (-112.26, 60.09, -13.20),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (-112.31, 60.08, -12.49),
    "end": (-111.63, 59.34, 102.57),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (147.55, 0.11, -147.91),
    "end": (-50.33, 15.94, -152.11),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (148.22, 0.13, -113.10),
    "end": (-50.89, 16.32, -117.07),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-85.86, 15.44, -116.51),
    "end": (-88.95, 21.15, -19.13),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (-52.84, 16.40, -115.75),
    "end": (-55.74, 21.13, -19.44),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (-51.98, 15.99, -152.32),
    "end": (-85.12, 15.99, -152.38),
    "name": Prop.BARRICADE,
    "separator": 4.0
},

{
    "offset": (-85.00, 15.99, -152.06),
    "end": (-86.00, 15.39, -117.21),
    "name": Prop.BARRICADE,
    "separator": 4.0
},
{
    "offset": (66.83, 20.77, 123.19),
    "angle": 180.0,   # rotate as needed to face the road
    "name": Prop.SIGN_WRONG_WAY
},
{
    "offset": (68.93, 20.22, 123.27),
    "angle": 180.0,   # rotate as needed to face the road
    "name": Prop.SIGN_WRONG_WAY
},
{
    "offset": (63.68, 21.17, -17.63),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},

{
    "offset": (63.47, 21.17, -16.60),  # slight offset to the side
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-89.00, 20.17, -19.50),
    "angle": 0.0,
    "name": Prop.TREE_WIDE
},
{
    "offset": (-89.00, 21.17, 88.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-89.00, 21.17, 86.59),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-53.78, 21.17, -18.45),
    "angle": 0.0,
    "name": Prop.SIGN_HIGHWAY_DOWNTOWN
},
{
    "offset": (64.35, 21.17, 122.62),
    "angle": 90.0,
    "name": Prop.SIGN_HIGHWAY_DOWNTOWN
},
{
    "offset": (-89.47, 21.17, 88.99),
    "angle": 270.0,
    "name": Prop.SIGN_HIGHWAY_CHINATOWN
},
{
    "offset": (65.15, 21.17, 89.00),
    "angle": 0.0,
    "name": Prop.TREE_WIDE
},
{
    "offset": (20.87, 0.64, 46.07),
    "angle": 110.0,
    "name": Prop.SIGN_HIGHWAY_LAKESHORE
},
{
    "offset": (148.67, 0.01, -148.14),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (148.50, 0.11, -112.60),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (12.01, 0.02, 11.91),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (12.12, 0.03, 46.22),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (27.42, 58.31, 89.21),
    "angle": 90.0,
    "name": Prop.CHINATOWN_GATE
},
{
    "offset": (29, 58.31, 76.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 74.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 72.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 102.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 104.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 106.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 108.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 110.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (29, 58.31, 112.00),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (0.79, 19.9016, 35.57),
    "angle": 0.0,
    "name": Prop.SAILBOAT
},

{
    "offset": (-2.17, 19.9016, 68.27),
    "angle": 0.0,
    "name": Prop.SAILBOAT
},

{
    "offset": (-40.32, 19.9016, 76.62),
    "angle": 0.0,
    "name": Prop.SAILBOAT
},
{
    "offset": (0.79, 19.9016, 35.57),
    "angle": 0.0,
    "name": Prop.SAILBOAT
},
{
    "offset": (0.79, 19.9016, 35.57),
    "angle": 180.0,
    "name": Prop.SAILBOAT
},

{
    "offset": (-2.17, 19.9016, 68.27),
    "angle": 0.0,
    "name": Prop.SAILBOAT
},
{
    "offset": (-2.17, 19.9016, 68.27),
    "angle": 180.0,
    "name": Prop.SAILBOAT
},
{
    "offset": (-40.32, 19.9016, 76.62),
    "angle": 0.0,
    "name": Prop.SAILBOAT
},
{
    "offset": (-40.32, 19.9016, 76.62),
    "angle": 180.0,
    "name": Prop.SAILBOAT
},
{
    "offset": (137.30, 0.94, -146.94),
    "angle": 270.0,
    "name": Prop.SIGN_HIGHWAY_LAKESHORE
},
{
    "offset": (145.94, 0.00, -11.99),
    "end": (14.57, 0.00, -11.99),
    "name": Prop.LIGHT_HIGHWAY,
    "angle": 270.0,
    "separator": 36.0
},
{
    "offset": (-14.22, 0.00, -12.70),
    "end": (-145.27, 0.00, -12.70),
    "name": Prop.LIGHT_HIGHWAY,
    "angle": 270.0,
    "separator": 36.0
},
{
    "offset": (-145.27, 0.00, -12.70),
    "angle": 270.0,
    "name": Prop.LIGHT_HIGHWAY
},
{
    "offset": (146.50, 0.00, 12.65),
    "end": (37.68, 0.00, 12.65),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 90.0
},

{
    "offset": (-15.60, 0.00, 12.25),
    "end": (-146.22, 0.01, 12.25),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 90.0
},
# Line 1
{
    "offset": (12.27, 0.00, -95.86),
    "end": (12.27, 0.00, -14.36),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 0.0
},

# Line 2
{
    "offset": (12.27, 0.00, 48.89),
    "end": (12.27, 0.00, 145.86),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 0.0
},

# 🔹 Endpoint lights (extra, as you asked)

{
    "offset": (12.27, 0.00, -14.36),
    "angle": 0.0,
    "name": Prop.LIGHT_HIGHWAY
},
# Line 1
{
    "offset": (-12.12, 0.00, -95.20),
    "end": (-12.12, 0.00, -13.70),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 180.0
},

# Line 2
{
    "offset": (-12.84, 0.00, 48.47),
    "end": (-12.84, 0.00, 146.48),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 180.0
},

# 🔹 Endpoint lights (as you asked)


{
    "offset": (-12.84, 0.00, 146.48),
    "angle": 180.0,
    "name": Prop.LIGHT_HIGHWAY
},
# Line 1
{
    "offset": (148.30, 0.00, 146.74),
    "name": Prop.LIGHT_HIGHWAY,
    "angle": 180.0
},

# Line 2
{
    "offset": (148.30, 0.00, -48.87),
    "end": (148.30, 0.00, -110.63),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 180.0
},

# 🔹 Endpoint lights


{
    "offset": (148.30, 0.00, -110.63),
    "angle": 180.0,
    "name": Prop.LIGHT_HIGHWAY
},
# Line 1 (same X)
{
    "offset": (-147.90, 0.00, -146.61),
    "end": (-147.90, 0.00, -12.77),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 0.0
},

# Line 2 (same X)
{
    "offset": (-147.90, 0.00, 13.11),
    "end": (-147.90, 0.00, 147.20),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 0.0
},

# 🔹 Endpoint lights (same X)

# Line 1 (same Z)
{
    "offset": (-146.71, 0.00, 146.90),
    "end": (-15.47, 0.00, 146.90),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 270.0
},

# Line 2 (same Z)
{
    "offset": (15.90, 0.00, 146.98),
    "end": (144.71, 0.00, 146.98),
    "name": Prop.LIGHT_HIGHWAY,
    "separator": 36.0,
    "angle": 270.0
},
{
    "offset": (-101.22, 0.04, -146.99),
    "angle": 90.0,
    "name": Prop.LIGHT_HIGHWAY
},

{
    "offset": (-132.30, 0.03, -146.99),
    "angle": 90.0,
    "name": Prop.LIGHT_HIGHWAY
},
{
    "offset": (-49.29, 15.87, -150.82),
    "angle": -90.0,
    "name": Prop.BARRICADE_SAWHORSE
},

{
    "offset": (-82.47, 15.72, -113.15),
    "angle": 0.0,
    "name": Prop.BARRICADE_SAWHORSE
},
{
    "offset": (-136.44, 0.00, -118.21),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-64.64, 0.01, -101.76),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-119.52, 0.00, -45.45),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-31.70, 0.01, -66.79),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-89.37, 0.00, -25.26),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (24.34, 0.00, -117.77),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (72.41, 0.00, -66.62),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (28.11, 0.00, -35.07),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (128.93, 0.00, -32.95),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (134.87, 0.00, -97.12),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (140.00, 0.00, 20.76),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (-28.11, 0.00, 108.81),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-26.58, 0.00, 35.05),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-96.43, 0.00, 81.38),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-79.91, 0.00, 25.69),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-134.22, 0.00, 58.20),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (-130.80, 0.00, 130.44),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-130.95, 0.00, 127.80),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-131.31, 0.00, 125.17),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-131.53, 0.00, 122.36),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-131.30, 0.00, 119.64),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-131.28, 0.00, 116.78),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-129.99, 0.00, 113.59),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-120.54, 0.00, 111.36),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-109.51, 0.00, 114.70),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (-128.56, 0.00, 133.43),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-122.61, 0.00, 136.01),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (-111.30, 0.00, 134.67),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (29.39, 0.00, 67.52),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (75.25, 0.00, 75.18),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (69.43, 0.01, 119.29),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (129.68, 0.01, 136.60),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},

{
    "offset": (22.72, 0.00, 135.38),
    "angle": 0.0,
    "name": Prop.TREE_SLIM
},
{
    "offset": (22.43, 21.17, 15.48),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-9.00, 21.16, 14.66),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-43.35, 21.17, 15.96),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-38.24, 21.17, 89.25),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-10.17, 21.17, 89.28),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-55.13, 21.17, 33.79),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (14.53, 21.17, 88.91),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-55.27, 21.17, 56.16),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (30.71, 21.17, 79.23),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (-55.00, 21.17, 81.92),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (30.23, 21.18, 60.89),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (29.75, 21.18, 36.94),
    "angle": 90.0,
    "name": Prop.LIGHT_SIDEWALK
},
{
    "offset": (2.77, 21.17, 88.95),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (30.12, 21.18, 69.07),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (29.70, 21.19, 43.73),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (7.00, 21.16, 16.06),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-27.56, 21.18, 16.00),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-54.82, 21.18, 26.11),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-54.97, 21.18, 49.54),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-54.98, 21.18, 69.47),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-54.87, 21.17, 88.79),
    "angle": 0.0,
    "name": Prop.TREE_WIDE
},
{
    "offset": (30.35, 21.17, 88.87),
    "angle": 0.0,
    "name": Prop.TREE_WIDE
},
{
    "offset": (29.06, 21.17, 16.29),
    "angle": 0.0,
    "name": Prop.TREE_WIDE
},
{
    "offset": (-54.71, 21.17, 16.25),
    "angle": 0.0,
    "name": Prop.TREE_WIDE
},
{
    "offset": (117.34, 7.42, 91.34),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-13.92, 21.19, 88.34),
    "angle": 15.00,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-27.58, 21.19, 88.26),
    "angle": 15.00,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-12.78, 21.19, 16.59),
    "angle": 15.00,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-26.96, 21.20, 16.91),
    "angle": 15.00,
    "name": Prop.CRASH_CAN
},

{
    "offset": (116.33, 7.38, 61.14),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-86.19, 15.32, -118.23),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-123.21, 21.17, 89.42),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (-158.62, 21.15, 89.41),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (92.96, 59.98, -101.09),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (129.42, 60.44, -99.28),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (128.19, 60.43, -99.39),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (92.23, 60.44, -66.94),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (84.02, 58.70, 70.87),
    "angle": 270.0,
    "name": Prop.SIGN_WRONG_WAY
},

{
    "offset": (116.85, 58.42, 110.51),
    "angle": 90.0,
    "name": Prop.SIGN_STOP
},
{
    "offset": (-107.00, 59.00, 98.00),
    "angle": 225.0,
    "name": Prop.SIGN_STOP
},

{
    "offset": (-108.00, 60.09, -8.00),
    "angle": 311.0,
    "name": Prop.SIGN_STOP
},

{
    "offset": (22.00, 59.55, -6.00),
    "angle": 44.0,
    "name": Prop.SIGN_STOP
},
{
    "offset": (-157.86, 35.52, -76.23),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-125.30, 35.69, -79.22),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (-125.49, 35.56, -76.65),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},
{
    "offset": (-157.00, 33.55, -116.11),
    "angle": 0.0,
    "name": Prop.CRASH_CAN
},

{
    "offset": (-119.45, 35.00, -116.06),
    "angle": 291.0,
    "name": Prop.TRAILER
},
{
    "offset": (23.68, 58.62, 74.85),
    "angle": 0.0,
    "name": Prop.PHONE_BOOTH
},
{
    "offset": (52.04, 21.19, 4.00),
    "angle": 270.0,
    "name": Prop.TRAILER
},

{
    "offset": (77.64, 0.00, -64.76),
    "angle": 0.0,
    "name": Prop.TRAILER
},
{
    "offset": (-60, 0.00, 123.57),
    "angle": 180.0,
    "name": Prop.TRAILER
},
{
    "offset": (89.62, 59.69, -97.55),
    "angle": 0.0,
    "name": Prop.CONE
},

{
    "offset": (89.31, 59.69, -95.64),
    "angle": 0.0,
    "name": Prop.CONE
},

# 🔹 Middle one → Sawhorse barricade
{
    "offset": (89.63, 59.75, -93.97),
    "angle": 90.0,
    "name": Prop.BARRICADE_SAWHORSE
},

{
    "offset": (89.45, 59.76, -92.37),
    "angle": 0.0,
    "name": Prop.CONE
},

{
    "offset": (89.44, 59.78, -90.88),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-47.81, 15.86, -140.68),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-47.47, 15.81, -142.46),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-47.55, 15.80, -143.78),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-47.25, 15.77, -145.11),
    "angle": 0.0,
    "name": Prop.CONE
},

{
    "offset": (-79.30, 15.70, -115.15),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-76.42, 15.79, -114.81),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-74.26, 15.87, -114.50),
    "angle": 0.0,
    "name": Prop.CONE
},
{
    "offset": (-78.91, 59.31, 82.79),
    "end": (-79.48, 59.84, 8.87),
    "name": Prop.TRAILER,
    "separator": 4.0,
    "angle": 180.0
},
{
    "offset": (-67.66, 59.81, 3.46),
    "end": (-9.38, 59.62, 3.30),
    "name": Prop.TRAILER,
    "separator": 3.0,
    "angle": 270.0
},
{
    "offset": (-50, 0, -40),
    "angle": -125.0,
    "name": Prop.TRAILER
},
{
    "offset": (28.35, 21.17, 89.40),
    "angle": 0.0,
    "name": Prop.BENCH_MALL
},

{
    "offset": (-52.87, 21.17, 89.40),
    "angle": 0.0,
    "name": Prop.BENCH_MALL
},
# 0 degree benches
{
    "offset": (28.35, 21.17, 89.40),
    "angle": 0.0,
    "name": Prop.BENCH_MALL
},

{
    "offset": (-52.87, 21.17, 89.46),
    "angle": 0.0,
    "name": Prop.BENCH_MALL
},

# 90 degree benches
{
    "offset": (-53.74, 21.17, 15.53),
    "angle": 0.0,
    "name": Prop.BENCH_MALL
},

{
    "offset": (27.01, 21.17, 15.53),
    "angle": 0.0,
    "name": Prop.BENCH_MALL
},
{
    "offset": (-48.85, 16.22, -117.75),
    "angle": 90.0,
    "name": Prop.DUMPSTER
},
]

random_props = []
from src.game.waypoints.constants import Rotation, Width
from src.game.races.constants_2 import MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps, CopStartLane, CopBehavior

from src.constants.vehicles import PlayerCar, TrafficCar
from src.constants.time_weather import TimeOfDay, Weather


# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints (including the start position), the number of waypoints for Circuits and Checkpoints is unlimited
# The max number of laps in Circuit races is 10

# Race Names
blitz_race_names = ["Corner Crashout" , "Mountaineering Endurance"]
circuit_race_names = ["Just a Square", "There and Back" , "De-Loop-De" , "Mini Figure 8" , "The Struggle Is Real" , "The Trailer Circuit" , "After-Job Relaxation"]
checkpoint_race_names = ["Downhill Dash" , "Only Up!" , "Treehall Crash" , "9/11 Time" , "Free Fall"]

# Races
race_data = {
    "BLITZ_0": {
        "player_waypoints": [
    [151.087402, 0.000000, -67.498207, Rotation.WEST, 11.0],
    [-77.104706, 0.000000, -88.311798, Rotation.WEST, 11.0],
    [-158.311081, 0.000000, -0.917385, Rotation.SOUTH, 11.0],
    [149.213303, 0.000000, 157.357483, Rotation.WEST, 11.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 30],
            "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 20],
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 2,
            "police": [
                f"{PlayerCar.POLICE} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.POLICE} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
            ],
            "num_of_opponents": 1,
            "opponents": {
                PlayerCar.CADILLAC: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0],
                ],
            },
            "num_of_exceptions": None,
            "exceptions": [
                [4, 0.0, 45],
                [5, 0.0, 45],
            ],
        },
    },
        "BLITZ_1": {
        "player_waypoints": [
    [74.673958, 6.157734, -131.864471, Rotation.WEST, 11.0],
    [-143.157639, 29.666737, -8.635851, Rotation.SOUTH, 15.0],
    [23.822617, 52.387293, -89.516708, Rotation.WEST, 15.0],
    [-40.191643, 63.982893, -10.465608, Rotation.SOUTH, 30.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.RAIN, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 49],
            "pro": [TimeOfDay.MORNING, Weather.RAIN, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 35],
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 2,
            "police": [
                f"{PlayerCar.POLICE} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.POLICE} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
            ],
            "num_of_opponents": 1,
            "opponents": {
                PlayerCar.CADILLAC: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0],
                ],
            },
            "num_of_exceptions": None,
            "exceptions": [
                [4, 0.0, 45],
                [5, 0.0, 45],
            ],
        },
    },
    "RACE_0": {
        "player_waypoints": [
    [-32.371391, 59.329982, 47.589008, Rotation.SOUTH_EAST, 20.0],
    [104.820694, 59.379291, 12.540339, Rotation.NORTH, 17.0],
    [-141.673187, 28.672099, 2.497837, Rotation.SOUTH, 17.0],
    [134.475800, 7.399643, 74.999001, Rotation.NORTH, 16.0],
    [-147.535294, 0.000000, -0.024386, Rotation.EAST, 13.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Use a list of dicts to allow duplicate car types
            "num_of_opponents": 0,  # Total count of all opponents
            "opponents": [
                {PlayerCar.MUSTANG_GT: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0]
                ]},
                {PlayerCar.MUSTANG_GT: [  # Second Mustang with different waypoints
                    [10.0, 0.0, 35.0],
                    [10.0, 0.0, -130.0]
                ]},
            ],
        },
    },
        "RACE_1": {
        "player_waypoints": [
    [-147.535294, 0.000000, -0.024386, Rotation.EAST, 13.0],
    [134.475800, 7.399643, 74.999001, Rotation.NORTH, 16.0],
    [-141.673187, 28.672099, 2.497837, Rotation.SOUTH, 17.0],
    [104.820694, 59.379291, 12.540339, Rotation.NORTH, 17.0],
    [-32.371391, 59.329982, 47.589008, Rotation.SOUTH_EAST, 20.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Use a list of dicts to allow duplicate car types
            "num_of_opponents": 0,  # Total count of all opponents
            "opponents": [
                {PlayerCar.MUSTANG_GT: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0]
                ]},
                {PlayerCar.MUSTANG_GT: [  # Second Mustang with different waypoints
                    [10.0, 0.0, 35.0],
                    [10.0, 0.0, -130.0]
                ]},
            ],
        },
    },
        "RACE_2": {
        "player_waypoints": [
    [-120.965431, 0.000105, 125.563858, Rotation.EAST, 11.0],
    [160.610092, 0.000021, 79.459946, Rotation.SOUTH, 11.0],
    [16.296705, 0.000098, -108.320663, Rotation.EAST, 11.0],
    [-160.237244, 0.000092, -11.624270, Rotation.SOUTH, 11.0],
    [-137.982834, 0.000163, 114.666679, Rotation.SOUTH_EAST, 11.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.MORNING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Use a list of dicts to allow duplicate car types
            "num_of_opponents": 0,  # Total count of all opponents
            "opponents": [
                {PlayerCar.MUSTANG_GT: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0]
                ]},
                {PlayerCar.MUSTANG_GT: [  # Second Mustang with different waypoints
                    [10.0, 0.0, 35.0],
                    [10.0, 0.0, -130.0]
                ]},
            ],
        },
    },
            "RACE_3": {
        "player_waypoints": [
    [160.609497, 0.000069, -71.941978, Rotation.NORTH, 11.0],
    [1.139673, 12.104420, -132.914383, Rotation.EAST, 17.0],
    [-141.801575, 27.744372, 13.126787, Rotation.SOUTH, 17.0],
    [-104.276909, 38.806781, -160.620239, Rotation.SOUTH, 20.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.EVENING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Use a list of dicts to allow duplicate car types
            "num_of_opponents": 0,  # Total count of all opponents
            "opponents": [
                {PlayerCar.MUSTANG_GT: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0]
                ]},
                {PlayerCar.MUSTANG_GT: [  # Second Mustang with different waypoints
                    [10.0, 0.0, 35.0],
                    [10.0, 0.0, -130.0]
                ]},
            ],
        },
    },
                "RACE_4": {
        "player_waypoints": [
    [-23.956392, 58.217566, 52.700512, Rotation.WEST, 11.0],
    [-91.925468,64.082428, 50.196209, Rotation.WEST, 33.0],    
    [58.045887, 21.170866, 107.586693, Rotation.WEST, 17.0],
    [58.045887, 0.0, 107.586693, Rotation.WEST, 17.0],    
    [-85.527176, 0.000000, -87.492699, Rotation.NORTH_WEST, 18.0],      
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Use a list of dicts to allow duplicate car types
            "num_of_opponents": 0,  # Total count of all opponents
            "opponents": [
                {PlayerCar.MUSTANG_GT: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0]
                ]},
                {PlayerCar.MUSTANG_GT: [  # Second Mustang with different waypoints
                    [10.0, 0.0, 35.0],
                    [10.0, 0.0, -130.0]
                ]},
            ],
        },
    },
    "CIRCUIT_0": {
        "player_waypoints": [
        [3.756357, 0.0, -159.975357, Rotation.WEST, 11.0],
        [-160.524673, 0.0, -133.183899, Rotation.SOUTH, 11.0],
        [-160.401413, 0.0, 131.003799, Rotation.SOUTH, 11.0],
        [53.125317, 0.0, 159.980606, Rotation.EAST, 11.0],
        [160.556046, 0.0, 28.713097, Rotation.NORTH, 11.0],
        [160.628876, 0.0, -140.754776, Rotation.NORTH, 11.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._5],
            "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._5],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
    "CIRCUIT_1": {
        "player_waypoints": [
        [-136.847641, 0.000040, -0.016653, Rotation.EAST, 11.0],
        [64.673523, 3.708784, 36.083004, Rotation.EAST, 17.0],
        [-20.454735, 22.3, 61.111862, Rotation.NORTH, 11.0],
        [63.197556, 7.068204, -132.154327, Rotation.EAST, 17.0],
        [160.568375, 0.000107, 85.216866, Rotation.NORTH, 11.0],
        [-59.500530, 0.000039, 160.049088, Rotation.WEST, 11.0],
        [-160.053833, 0.000000, 54.012020, Rotation.SOUTH, 11.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._4],
            "pro": [TimeOfDay.EVENING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._5],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
        "CIRCUIT_2": {
        "player_waypoints": [
    [9.122496, 21.170104, -1.092455, Rotation.WEST, 16.0],
    [-72.223312, 21.169929, 44.836189, Rotation.SOUTH, 16.0],
    [-21.825138, 21.169885, 106.093903, Rotation.EAST, 16.0],
    [47.055447, 21.169866, 43.291813, Rotation.NORTH, 16.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.EVENING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._10],
            "pro": [TimeOfDay.NIGHT, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._10],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
            "CIRCUIT_3": {
        "player_waypoints": [
    [-55.774361, 21.170104, 107.014801, Rotation.EAST, 16.0],
    [-20.454735, 22.22, 61.111862, Rotation.NORTH, 7.0],
    [-0.040990, 21.170238, -0.512179, Rotation.EAST, 16.0],
    [46.267888, 21.170055, 57.216648, Rotation.NORTH, 16.0],
    [14.610991, 21.170083, 106.305305, Rotation.WEST, 16.0],
    [-20.454735, 22.22, 61.111862, Rotation.NORTH, 7.0],
    [-72.832443, 21.170013, 29.695158, Rotation.SOUTH, 16.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._10],
            "pro": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._10],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
                "CIRCUIT_4": {
        "player_waypoints": [
    [-0.039542, 0.000033, -15.339127, Rotation.SOUTH, 11.0],
    [94.637527, 13.435738, 108.048398, Rotation.WEST, 17.0],
    [52.286758, 21.170026, 29.715700, Rotation.NORTH, 7.0],
    [51.883173, 25.079319, -8.386227, Rotation.NORTH, 1.9],
    [41.414978, 0.000035, -88.579628, Rotation.WEST, 11.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._4],
            "pro": [TimeOfDay.NIGHT, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._5],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
                    "CIRCUIT_5": {
        "player_waypoints": [
    [-50.150471, 59.027327, 86.420578, Rotation.EAST, 11.0],
    [10.786745, 59.110285, 38.871578, Rotation.NORTH, 6.0],
    [-38.836628, 64.004219, -8.539124, Rotation.WEST, 3.0],
    [-91.088661, 63.797909, 39.304817, Rotation.SOUTH, 3.0]
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._4],
            "pro": [TimeOfDay.EVENING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._5],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
                    "CIRCUIT_6": {
        "player_waypoints": [
    [25.625023, 58.063657, 89.298531, Rotation.EAST, 17.0],
    [56.567303, 55.354837, -86.866997, Rotation.WEST, 17.0],
    [-107.437363, 20.38925, 106.210762, Rotation.EAST, 17.0],
    [-19.351797, 21.807803, 49.600502, Rotation.NORTH, 6.0],
    [-107.437363, 20.38925, 106.210762, Rotation.EAST, 17.0],
    [56.567303, 55.354837, -86.866997, Rotation.WEST, 17.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._2],
            "pro": [TimeOfDay.EVENING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.LIMO_WHITE: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.LIMO_BLACK: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
}
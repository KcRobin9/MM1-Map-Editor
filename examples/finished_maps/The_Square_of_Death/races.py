from src.game.waypoints.constants import Rotation, Width
from src.game.races.constants_2 import MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps, CopStartLane, CopBehavior

from src.constants.vehicles import PlayerCar, TrafficCar
from src.constants.time_weather import TimeOfDay, Weather


# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints (including the start position), the number of waypoints for Circuits and Checkpoints is unlimited
# The max number of laps in Circuit races is 10

# Race Names
blitz_race_names = ["No Blitzes"]
circuit_race_names = ["Small Square Loop", "Mini Figure 8 - 2" , "Lil Big 8" , "Inclined Loop" , "I Like Terrains" , "Pondshore Walk "]
checkpoint_race_names = ["Fast asf" , "Depressed Start" , "Drag Race 10"]

# Races
race_data = {
    "BLITZ_0": {
        "player_waypoints": [
    [-82.133263, 1.981088, -54.081749, Rotation.EAST, 8.0],
    [111.355072, -0.000057, 32.113350, Rotation.SOUTH, 8.0],
    [-91.302177, -0.000010, 111.008438, Rotation.WEST, 8.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._3, 20],
            "pro": [TimeOfDay.MORNING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._3, 18],
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
    [101.081993, -0.000020, -110.966087, Rotation.WEST, 8.0],
    [-111.396355, -0.000079, -75.346649, Rotation.SOUTH, 8.0],
    [-39.095039, -0.000093, 72.505249, Rotation.EAST, 8.0],
    [66.593216, -3.829826, 56.448105, Rotation.EAST, 8.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NIGHT, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0,
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
    [60.487961, -3.827961, 40.906162, Rotation.NORTH, 8.0],
    [25.955530, -0.000153, -110.999527, Rotation.WEST, 8.0],    
    [-111.355423, -0.000197, -100.297295, Rotation.SOUTH, 8.0],
    [-55.090458,4.0,-53.707790, Rotation.WEST, 5.0],
    [-111.289421, -0.000106, 91.695908, Rotation.SOUTH, 8.0],
    [74.130402, 3.878384, -49.519573, Rotation.NORTH_EAST, 1.5],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NOON, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0,
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
    [111.397461, -0.098967, 111.619644, Rotation.NORTH_WEST, 12.0],
    [-107.686996, -0.000054, -107.002220, Rotation.NORTH_WEST, 12.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.MORNING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0,
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
        [-25.458344, 0.0, -110.969879, Rotation.WEST, 8.0],
        [-111.096535, 0.0, 36.298763, Rotation.SOUTH, 8.0],
        [-11.815298, 0.0, 110.942574, Rotation.EAST, 8.0],
        [111.454269, 0.0, -18.895742, Rotation.NORTH, 8.0],
    ],
    "mm_data": {
        "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._5],
        "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._5],
    },
    "aimap": {
        "traffic_density": 0,
        "num_of_police": 0,
        "police": [
            f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
        ],
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
    [-40.529598, 0.0, 0.083670, Rotation.EAST, 8.0],
    [0.027165, 0.0, -13.607793, Rotation.NORTH, 8.0],
    [-55.090458,4.0,-53.707790, Rotation.WEST, 5.0],
    [-111.348831, 0.0, -94.378181, Rotation.NORTH, 8.0],
    [-0.044103, 0.0, -85.465385, Rotation.SOUTH, 8.0],
    [-55.090458,4.0,-53.707790, Rotation.WEST, 5.0],
    [-111.109200, 0.0, -16.377771, Rotation.SOUTH, 8.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._4],
            "pro": [TimeOfDay.EVENING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._5],
        },
        "aimap": {
            "traffic_density": 0,
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
    [45.680080, 0.0, 110.954079, Rotation.EAST, 8.0],
    [111.427361, 0.0, 12.992691, Rotation.NORTH, 8.0],
    [-91.111618, 0.0, -0.027222, Rotation.WEST, 8.0],
    [-111.334740, 0.0, -87.251175, Rotation.NORTH, 8.0],
    [-15.258902, 0.0, -110.964996, Rotation.EAST, 8.0],
    [-0.010510, 0.0, 93.984734, Rotation.SOUTH, 8.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.EVENING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._10],
            "pro": [TimeOfDay.NOON, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._10],
        },
        "aimap": {
            "traffic_density": 0,
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
    [94.252129, -1.759290, 58.550003, Rotation.NORTH, 9.0],
    [57.340984, -1.653319, 16.300028, Rotation.WEST, 9.0],
    [18.019890, -1.955878, 43.263016, Rotation.SOUTH, 9.0],
    [56.283001, -2.067514, 92.338760, Rotation.EAST, 9.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._10],
            "pro": [TimeOfDay.NIGHT, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._10],
        },
        "aimap": {
            "traffic_density": 0,
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
    [56.407375, -0.000038, 2.074195, Rotation.NORTH, 11.0],
    [-55.090458,4.0,-53.707790, Rotation.WEST, 5.0],
    [-111.410286, -0.000114, 95.070328, Rotation.SOUTH, 8.0],
    [15.004389, -0.000108, 111.035515, Rotation.EAST, 8.0],
    [60.755424, -3.830196, 57.968204, Rotation.NORTH, 8.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._4],
            "pro": [TimeOfDay.MORNING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._5],
        },
        "aimap": {
            "traffic_density": 0,
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
    [-58.001343, 1.353113, -22.167713, Rotation.EAST, 16.0],
    [-25.036251, 1.475920, -51.006290, Rotation.NORTH, 16.0],
    [-56.675423, 1.424994, -86.368469, Rotation.WEST, 16.0],
    [-86.913673, 1.515365, -59.950821, Rotation.SOUTH, 16.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._7],
            "pro": [TimeOfDay.EVENING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0, Laps._10],
        },
        "aimap": {
            "traffic_density": 0,
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
from src.game.waypoints.constants import Rotation, Width
from src.game.races.constants_2 import MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps, CopStartLane, CopBehavior

from src.constants.vehicles import PlayerCar, TrafficCar
from src.constants.time_weather import TimeOfDay, Weather


# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints (including the start position), the number of waypoints for Circuits and Checkpoints is unlimited
# The max number of laps in Circuit races is 10

# Race Names
blitz_race_names = ["Chaotic Tower"]
circuit_race_names = ["Circuit Race 1", "Circuit Race 2"]
checkpoint_race_names = ["Photo Finish"]

# Races
race_data = {
    "BLITZ_0": {
        "player_waypoints": [
            [0.0, 0.0, 55.0, Rotation.NORTH, 12.0],
            [0.0, 0.0, 15.0, Rotation.NORTH, 12.0],
            [0.0, 0.0, -40.0, Rotation.NORTH, 12.0],
            [0.0, 0.0, -130.0, Rotation.NORTH, 12.0],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 999],
            "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._3, 999],
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 2,
            "police": [
                f"{PlayerCar.CRUISER} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.CRUISER} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
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
            [0.0, 245, -850, Rotation.SOUTH, Width.MEDIUM],
            [0.0, 110, -500, Rotation.SOUTH, Width.MEDIUM],
            [0.0, 110, -497, Rotation.SOUTH, Width.MEDIUM],
            [25.0, 45.0, -325, Rotation.SOUTH, 25.0],
            [35.0, 12.0, -95.0, Rotation.SOUTH, Width.MEDIUM],
            [35.0, 30.0, 0.0, Rotation.SOUTH, Width.MEDIUM],
            [35.0, 30.0, 40.0, Rotation.SOUTH, Width.MEDIUM],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Use a list of dicts to allow duplicate car types
            "num_of_opponents": 2,  # Total count of all opponents
            "opponents": [
                {PlayerCar.MUSTANG99: [
                    [5.0, 0.0, 35.0],
                    [5.0, 0.0, -130.0]
                ]},
                {PlayerCar.MUSTANG99: [  # Second Mustang with different waypoints
                    [10.0, 0.0, 35.0],
                    [10.0, 0.0, -130.0]
                ]},
            ],
        },
    },
    "CIRCUIT_0": {
        "player_waypoints": [
            [0.0, 245, -850, Rotation.SOUTH, Width.MEDIUM],
            [0.0, 110, -500, Rotation.SOUTH, 30.0],
            [25.0, 45.0, -325, Rotation.SOUTH, 25.0],
            [35.0, 12.0, -95.0, Rotation.SOUTH, Width.MEDIUM],
            [35.0, 30.0, 0.0, Rotation.SOUTH, Width.MEDIUM],
            [35.0, 30.0, 40.0, Rotation.SOUTH, Width.MEDIUM],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._2],
            "pro": [TimeOfDay.NIGHT, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # OLD FORMAT: Still supported, but only one of each car type
            "num_of_opponents": 2,
            "opponents": {
                TrafficCar.WHITE_LIMO: [
                    [-10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-10.0, 0.0, -75.0]
                ],
                TrafficCar.BLACK_LIMO: [
                    [10.0, 245, -850],
                    [0.0, 0.0, -100],
                    [10.0, 0.0, -75.0],
                ],
            }
        },
    },
    "CIRCUIT_1": {
        "player_waypoints": [
            [0.0, 110, -500, Rotation.SOUTH, 30.0],
            [25.0, 45.0, -325, Rotation.SOUTH, 25.0],
            [35.0, 12.0, -95.0, Rotation.SOUTH, Width.MEDIUM],
            [35.0, 30.0, 0.0, Rotation.SOUTH, Width.MEDIUM],
            [35.0, 30.0, 40.0, Rotation.SOUTH, Width.MEDIUM],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._2],
            "pro": [TimeOfDay.NIGHT, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            # NEW FORMAT: Multiple of the same car (3 Cadillacs)
            "num_of_opponents": 3,
            "opponents": [
                {PlayerCar.CADILLAC: [
                    [-5.0, 245, -850],
                    [0.0, 0.0, -100],
                    [-5.0, 0.0, -75.0]
                ]},
                {PlayerCar.CADILLAC: [
                    [0.0, 245, -850],
                    [0.0, 0.0, -100],
                    [0.0, 0.0, -75.0]
                ]},
                {PlayerCar.CADILLAC: [
                    [5.0, 245, -850],
                    [0.0, 0.0, -100],
                    [5.0, 0.0, -75.0],
                ]},
            ]
        },
    }
}
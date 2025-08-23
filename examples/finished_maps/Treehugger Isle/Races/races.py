from src.Constants.vehicles import PlayerCar, TrafficCar
from src.Constants.races import Rotation, Width, TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps, CopStartLane, CopBehavior


# Max number of Races is 15 for Blitz, 15 for Circuit, and 12 for Checkpoint
# Blitzes can have a total of 11 waypoints (including the start position), the number of waypoints for Circuits and Checkpoints is unlimited
# The max number of laps in Circuit races is 10

# Race Names
blitz_race_names = ["Straight Jump", "The Ribbon", "Fresh Air"]
circuit_race_names = ["Mini Chicane", "Isle Loop","Circle Around","Snail Loop"]
checkpoint_race_names = ["Among The Trees", "Unsettling Jumps","Left or Right","Isle Driving Test"]

# Races
race_data = {
    "BLITZ_0": {
        "player_waypoints": [
            [1.0, 1.0, -40.0, Rotation.SOUTH, 12.0], 
            [1.0, 1.0, 50.0, Rotation.NORTH, 7.0], 
            [-4.0, 19.0, 197.0, Rotation.NORTH, 2.0],
            [-10.0, 24.0, 235.0, Rotation.NORTH, 10.0],
            [2.0, 15.0, 350.0, Rotation.NORTH, 5.0],
            [1.0, 1.0, 532.0, Rotation.NORTH, 12.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._5, 35],        
            "pro": [TimeOfDay.NOON, Weather.RAIN, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._5, 25], 
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.CRUISER} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
            ],
            "num_of_opponents": 0,
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
            [-111.0, 16.0, 237.0, 90, 10.0], 
            [-80.0, 15.0, 237.0, 90, 10.0], 
            [-31.0, 15.0, 302.0, 146, 7.0],
            [18.0, 15.0, 324.0, Rotation.NORTH, 5.0],
            [7.0, 20.0, 279.0, Rotation.NORTH, 2.0],
            [18.0, 20.0, 234.0, Rotation.SOUTH, 5.0],
            [-14.0, 20.0, 224.0, Rotation.SOUTH, 5.0],
            [2.0, 1.0, 471.0, Rotation.SOUTH, 7.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._7, 40],        
            "pro": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._7, 30], 
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.CRUISER} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
            ],
            "num_of_opponents": 0,
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
    "BLITZ_2": {
        "player_waypoints": [
            [2.0, 20, 248, -180, 10.0], 
            [1.0, 0.0, 593.0, 180, 7.0], 
            [1.0, 0.0, -121.0, -180, 7.0],
            [-137.0, 15.0, 237.0, -90, 9.0],
            [-337.0, 9.0, 237.0, -90, 7.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._4, 35],        
            "pro": [TimeOfDay.NOON, Weather.RAIN, MaxOpponents._8, CopDensity._100, AmbientDensity._100, PedDensity._100, Laps._4, 55], 
        },
        "aimap": {
            "ambient_density": 0.25,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
                f"{PlayerCar.CRUISER} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
            ],
            "num_of_opponents": 0,
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
            [-244.0, -2, 237, 90, 10.0], 
            [-166, 9, 237, 90, 10.0],  
            [-80.0, 15, 237, 90, 10],   
            [-26.0, 15.0, 166, 60, 6.0],   
            [60.0, 15.0, 135.0, 160, 5.0], 
            [72.0, 15.0, 234.0, -180, 7.0], 
            [66.0, 15.0, 301.0, -150, 5],
            [11.0, 15.0, 330.0, -60, 6],
            [7.0, 20.0, 279.0, 0, 2], 
            [15.0, 20.0, 213.0, -20, 4],
            [2.0, 4.0, 60.0, 0, 4],
            [40.0, 1.0, 22.0, 10, 3],
            [48.0, 1.0, -27.0, 22, 3],
            [-48.0, 0.0, -127.0, -55.0, 6],  
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.CLOUDY, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NIGHT, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
            "opponents": {
                PlayerCar.MUSTANG99: [[5.0, 0.0, 35.0], [5.0, 0.0, -130.0]], 
            },
        },
    },
    "RACE_1": {
        "player_waypoints": [
            [46.0, 1, -18, -147, 10.0], 
            [-30, 6, 77, -130, 3.0],  
            [-73.0, 15, 118, -137, 3.0],   
            [-152.0, -2.0, 172, -112, 6.5],   
            [-217.0, -2.0, 200.0, 180, 6], 
            [-180.0, 4.0, 236.0, 90, 8.0], 
            [-65.0, 15.0, 243.0, 140, 9],
            [7.0, 15.0, 274.0, 90, 2],
            [76.0, 15.0, 310.0, 180, 5],
            [-1.0, 1.0, 425.0, -135, 3],
            [-50.0, 1.0, 430.0, 90, 4],
            [-100.0, 0.0, 423.0, -70.0, 7],  
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
            "opponents": {
                PlayerCar.MUSTANG99: [[5.0, 0.0, 35.0], [5.0, 0.0, -130.0]], 
            },
        },
    },
     "RACE_2": {
        "player_waypoints": [
            [40.0, 15, 241, 90, 10.0], 
            [1, 15, 350, 180, 3.0],  
            [-0.0, 0, 583, 180, 7.0],
            [20.0, 20.0, 233, 180.0, 7.0],   
            [2.0, 15.0, 124, -180, 3.0],   
            [2.0, 0.0, -115.0, 180, 7.0], 
            [-41.0, 15.0, 240.0, 180, 8.0],
            [40.0, 15, 241, 180, 10.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.MORNING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
            "opponents": {
                PlayerCar.MUSTANG99: [[5.0, 0.0, 35.0], [5.0, 0.0, -130.0]], 
            },
        },
    },
    "RACE_3": {
        "player_waypoints": [
            [2.0, 20, 248, -180, 10.0], 
            [2, 20, 215, 180, 6.5],  
            [2.0, 15., 125, 180, 2.5],
            [30.0, 1.0, 8, 40.0, 3.0],   
            [49.0, 1.0, -47, 180, 4.5],
            [-25.0, 1.0, -61, 180.0, 5.0],
            [72.0, 15.0, 234.0, -180, 7.0],   
            [-32.0, 15.0, 322.0, -30, 6.0],
            [-80.0, 15, 237, 90, 10], 
            [-219.0, -2.0, 240.0, -145, 8.0],
            [-160.0, -2, 341, 130, 8.0],
            [-90.0, -1, 413, -120, 5.0],
            [-324.0, 7, 270, 180, 6.0],
            [-217.0, -2, 88, 80, 8.0],
            [-75.0, 1, 32, 40, 6.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.MORNING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
            "pro": [TimeOfDay.MORNING, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._0, PedDensity._0],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
            "opponents": {
                PlayerCar.MUSTANG99: [[5.0, 0.0, 35.0], [5.0, 0.0, -130.0]], 
            },
        },
    },
    "CIRCUIT_0": {
        "player_waypoints": [
            [1.0, 0.0, -110, 180, 7], 
            [-25.0, 1.0, -61, 180.0, 5.0],       
            [-42.0, 1.0, -14, 180.0, 7.0],
            [-34.0, 1.0, 38, 105.0, 6.0],
            [38.0, 1.0, 25, 25.0, 7.0],
            [33.0, 1.0, 3, 33.0, 3.5],
            [43.0, 1.0, -33, 0.0, 5.0],
            [32.0, 0.0, -92, -37.0, 6.0],  
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
            "pro": [TimeOfDay.MORNING, Weather.SNOW, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._4],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
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
            [-80.0, 15, 237, 90, 10], 
            [-35.0, 15.0, 158, 35.0, 4.5],       
            [-10.0, 1.0, 40, -60.0, 5.0],
            [-93.0, -2.0, 60, -135.0, 6.0],
            [-218.0, -2.0, 222, 165.0, 7.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
            "pro": [TimeOfDay.EVENING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._4],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0, 
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
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
    "CIRCUIT_2": {
        "player_waypoints": [
            [1.0, 1.0, 31, 180, 7.0], 
            [-4.0, 15.0, 183, 180.0, 2.5],       
            [-14.0, 20.0, 222, 180.0, 5.0],
            [18.0, 20.0, 228, -180.0, 6.0],
            [-14.0, 20.0, 222, 180.0, 5.0],
            [18.0, 20.0, 228, -180.0, 6.0],
            [-14.0, 20.0, 222, 180.0, 5.0],
            [18.0, 20.0, 228, -180.0, 6.0],
            [-80.0, 15.0, 235, -90, 8.0],
            [-218.0, -2.0, 222, 20.0, 7.0],
            [-93.0, -2.0, 60, 65.0, 6.0],
            [-47.0, 1.0, 39, 90.0, 7.0], 
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._2],
            "pro": [TimeOfDay.EVENING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
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
    "CIRCUIT_3": {
        "player_waypoints": [
            [-4.0, 20.0, 263, 90, 5.0], 
            [25.0, 20.0, 235, 0.1, 3.0],       
            [5.0, 20.0, 207, -90.0, 3.0],
            [-21.0, 20.0, 229, -180.0, 3.0],
            [0.0, 20.0, 249, 90.0, 5.0],
            [0.0, 20.0, 216, -90.0, 4.0],
            [-18.0, 20.0, 255, -180.0, 2.5],
        ],
        "mm_data": {
            "ama": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._3],
            "pro": [TimeOfDay.EVENING, Weather.CLEAR, MaxOpponents._8, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._5],
        },
        "aimap": {
            "traffic_density": 0.2,
            "num_of_police": 0,
            "police": [
                f"{PlayerCar.CRUISER} 15.0 0.0 75.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",
            ],
            "num_of_opponents": 0,
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
}
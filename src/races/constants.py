# Headers
CNR_HEADER = "# This is your Cops & Robbers file, note the structure (per 3): Bank/Blue Team Hideout, Gold, Robber/Red Team Hideout\n"
MM_DATA_HEADER = ["CarType", "TimeofDay", "Weather", "Opponents", "Cops", "Ambient", "Peds", "NumLaps", "TimeLimit", "Difficulty"]
CHECKPOINT_PREFIXES = ["ASP1", "ASP2", "ASP3", "ASU1", "ASU2", "ASU3", "AFA1", "AFA2", "AFA3", "AWI1", "AWI2", "AWI3"]

class RaceModeNum:
    CIRCUIT_ALL = "CIRCUIT_ALL"
    CHECKPOINT_ALL = "CHECKPOINT_ALL"
    BLITZ_ALL = "BLITZ_ALL"
    
    BLITZ_0 = "BLITZ_0"
    BLITZ_1 = "BLITZ_1"
    BLITZ_2 = "BLITZ_2"
    BLITZ_3 = "BLITZ_3"
    BLITZ_4 = "BLITZ_4"
    BLITZ_5 = "BLITZ_5"
    BLITZ_6 = "BLITZ_6"
    BLITZ_7 = "BLITZ_7"
    BLITZ_8 = "BLITZ_8"
    BLITZ_9 = "BLITZ_9"
    BLITZ_10 = "BLITZ_10"
    BLITZ_11 = "BLITZ_11"
    BLITZ_12 = "BLITZ_12"
    BLITZ_13 = "BLITZ_13"
    BLITZ_14 = "BLITZ_14"

    CHECKPOINT_0 = "RACE_0"
    CHECKPOINT_1 = "RACE_1"
    CHECKPOINT_2 = "RACE_2"
    CHECKPOINT_3 = "RACE_3"
    CHECKPOINT_4 = "RACE_4"
    CHECKPOINT_5 = "RACE_5"
    CHECKPOINT_6 = "RACE_6"
    CHECKPOINT_7 = "RACE_7"
    CHECKPOINT_8 = "RACE_8"
    CHECKPOINT_9 = "RACE_9"
    CHECKPOINT_10 = "RACE_10"
    CHECKPOINT_11 = "RACE_11"
    CHECKPOINT_11 = "RACE_12"
    
    CIRCUIT_0 = "CIRCUIT_0"
    CIRCUIT_1 = "CIRCUIT_1"
    CIRCUIT_2 = "CIRCUIT_2"
    CIRCUIT_3 = "CIRCUIT_3"
    CIRCUIT_4 = "CIRCUIT_4"
    CIRCUIT_5 = "CIRCUIT_5"
    CIRCUIT_6 = "CIRCUIT_6"
    CIRCUIT_7 = "CIRCUIT_7"
    CIRCUIT_8 = "CIRCUIT_8"
    CIRCUIT_9 = "CIRCUIT_9"
    CIRCUIT_10 = "CIRCUIT_10"
    CIRCUIT_11 = "CIRCUIT_11"
    CIRCUIT_12 = "CIRCUIT_12"
    CIRCUIT_13 = "CIRCUIT_13"
    CIRCUIT_14 = "CIRCUIT_14"
    CIRCUIT_15 = "CIRCUIT_15"


# Race constants
RACE_TYPE_TO_PREFIX = {
    RaceMode.BLITZ: "ABL",
    RaceMode.CIRCUIT: "CIR",
    RaceMode.CHECKPOINT: CHECKPOINT_PREFIXES
}

RACE_TYPE_TO_EXTENSION = {
    RaceMode.BLITZ: ".B_",
    RaceMode.CIRCUIT: ".C_",
    RaceMode.CHECKPOINT: ".R_",
}

RACE_TYPE_INITIALS = {
    RaceMode.BLITZ: "B",
    RaceMode.CIRCUIT: "C",
    RaceMode.CHECKPOINT: "R",
}

DEFAULT_MM_DATA_BY_RACE_MODE = {        
    RaceMode.BLITZ:      [1, 2, 3, 4, 5, 6, 7, 8],   # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps, TimeLimit
    RaceMode.CIRCUIT:    [1, 2, 3, 4, 5, 6, 7],      # TimeofDay, Weather, Opponents, Cops, Ambient, Peds, NumLaps
    RaceMode.CHECKPOINT: [1, 2, 3, 4, 5, 6]          # TimeofDay, Weather, Opponents, Cops, Ambient, Peds
}
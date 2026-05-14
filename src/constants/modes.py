class RaceMode:
    ROAM = "ROAM"
    CRUISE = "CRUISE"
    BLITZ = "BLITZ"
    CHECKPOINT = "RACE"
    CIRCUIT = "CIRCUIT"
    COPS_AND_ROBBERS = "COPSANDROBBERS"


class NetworkMode:
    SINGLE = "SINGLE"
    MULTI = "MULTI"
    SINGLE_AND_MULTI = "All Modes"


class GameMode:
    CRUISE     = 0
    CHECKPOINT = 1
    CNR        = 2
    CIRCUIT    = 3
    BLITZ      = 4


class Difficulty:
    AMATEUR      = 0
    PROFESSIONAL = 1


GAME_MODE_NAMES = {
    GameMode.CRUISE:     "Cruise",
    GameMode.CHECKPOINT: "Checkpoint",
    GameMode.CNR:        "Cops & Robbers",
    GameMode.CIRCUIT:    "Circuit",
    GameMode.BLITZ:      "Blitz",
}
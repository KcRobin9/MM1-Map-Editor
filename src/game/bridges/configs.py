from src.constants.modes import NetworkMode


BRIDGE_CONFIG_TEMPLATE = """
    mmBridgeMgr :076850a0 {{
        BridgeDelta {BridgeDelta}
        BridgeOffGoal {BridgeOffGoal}
        BridgeOnGoal {BridgeOnGoal}
        GateDelta {GateDelta}
        GateOffGoal {GateOffGoal}
        GateOnGoal {GateOnGoal}
        BridgeOnDelay {BridgeOnDelay}
        GateOffDelay {GateOffDelay}
        BridgeOffDelay {BridgeOffDelay}
        GateOnDelay {GateOnDelay}
    }}
    """

BRIDGE_CONFIG_DEFAULT = {
    "BridgeDelta": 0.20,
    "BridgeOffGoal": 0.0,
    "BridgeOnGoal": 0.47,
    "GateDelta": 0.40,
    "GateOffGoal": -1.57,
    "GateOnGoal": 0.0,
    "BridgeOnDelay": 7.79,
    "GateOffDelay": 5.26,
    "BridgeOffDelay": 0.0,
    "GateOnDelay": 5.0,
    "Mode": NetworkMode.SINGLE
}

ORIENTATION_MAPPINGS = {
    "NORTH": (-10, 0, 0),
    "SOUTH": (10, 0, 0),
    "EAST": (0, 0, 10),
    "WEST": (0, 0, -10),
    "NORTH_EAST": (10, 0, 10),
    "NORTH_WEST": (10, 0, -10),
    "SOUTH_EAST": (-10, 0, 10),
    "SOUTH_WEST": (-10, 0, -10)
}
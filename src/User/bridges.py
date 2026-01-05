# from src.constants.waypoints import Rotation

from src.game.waypoints.constants import Rotation

from src.constants.props import Prop
from src.constants.modes import NetworkMode, RaceMode


"""
INFO
    1) You can set a maximum of 1 bridge per cull room, which may have up to 5 attributes
    2) You can set a bridge without any attributes like this:
        (-50.0, 0.01, -100.0), 270, 2, BRIDGE_WIDE, [])
    3) Supported orientations --> see below
    Or you can manually set the orientation in degrees (0.0 - 360.0).
"""

# Structure: (x, y, z, rotation, bridge ID, bridge object)
bridge_list = [
    ((-50.0, 0.01, -100.0), Rotation.WEST, 2, Prop.BRIDGE_WIDE, [
    ((-50.0, 0.15, -115.0), Rotation.WEST, 2, Prop.CROSSGATE),
    ((-50.0, 0.15, -85.0), Rotation.EAST, 2, Prop.CROSSGATE)
    ]),  
    ((-119.0, 0.01, -100.0), Rotation.EAST, 3, Prop.BRIDGE_WIDE, [
    ((-119.0, 0.15, -115.0), Rotation.WEST, 3, Prop.CROSSGATE),
    ((-119.0, 0.15, -85.0), Rotation.EAST, 3, Prop.CROSSGATE)
    ])
] 

#* Custom Bridge Configs (optional)
bridge_race_0 = {
    "RaceType": RaceMode.CHECKPOINT, 
    "RaceNum": "0", 
    "BridgeOffGoal": 0.50, 
    "BridgeOnGoal": 0.50,
    "GateDelta": 0.40,
    "GateOffGoal": -1.57,
    "GateOnGoal": 0.0,
    "BridgeOnDelay": 7.79,
    "GateOffDelay": 5.26 ,
    "BridgeOffDelay": 0.0,
    "GateOnDelay": 5.0,
    "Mode": NetworkMode.SINGLE
}

bridge_cnr = {
    "RaceType": RaceMode.COPS_AND_ROBBERS,
    "BridgeDelta": 0.20,
    "BridgeOffGoal": 0.33,
    "BridgeOnGoal": 0.33,
    "Mode": NetworkMode.MULTI
}

# Pack all Custom Bridge Configurations for processing
bridge_config_list = [bridge_race_0, bridge_cnr]
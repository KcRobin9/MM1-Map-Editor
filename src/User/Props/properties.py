from src.Constants.constants import HUGE
from src.Constants.vehicles import PlayerCar
from src.Constants.props import Prop, AudioProp


prop_properties = {
    PlayerCar.VW_BEETLE: {"ImpulseLimit2": HUGE, "AudioId": AudioProp.GLASS},
    PlayerCar.CITY_BUS:  {"ImpulseLimit2": 50, "Mass": 50, "AudioId": AudioProp.POLE, "Size": "18 6 5", "CG": "0 0 0"},

    # Example of possible values for the Panoz Roadster (original values)
    PlayerCar.ROADSTER: {
        "NodeName": "vppanoz",
        "AudioId": 0,
        "Size": "6 3 4",
        "CG": "0 0 0",
        "Offset": "0 0 0",
        "GlowOffset": "0 0 0",
        "Mass": 1300,
        "Elasticity": 0.3,
        "Friction": 0.2,
        "ImpulseLimit2": 1000,
        "SpinAxis": 0,
        "Flash": 0,
        "CollisionType": 4,
        "NumParts": 0,
        "PartNames": "$0",
        "TexNumber": 0,
        "BillFlags": 0,
        "YRadius": 11.7881
    }
}

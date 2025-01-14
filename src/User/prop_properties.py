from src.Constants.constants import HUGE
from src.Constants.vehicles import PlayerCar
from src.Constants.props import AudioProp


prop_properties = {
    PlayerCar.VW_BEETLE: {"ImpulseLimit2": HUGE, "AudioId": AudioProp.GLASS},
    PlayerCar.CITY_BUS:  {"ImpulseLimit2": 50, "Mass": 50, "AudioId": AudioProp.POLE, "Size": "18 6 5", "CG": "0 0 0"}
}

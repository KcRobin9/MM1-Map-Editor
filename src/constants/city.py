from dataclasses import dataclass
from pathlib import Path

_CITY_RESOURCES = Path(__file__).parent.parent.parent / "resources" / "city_files"


@dataclass(frozen=True)
class CityDefinition:
    name:   str
    folder: str
    prefix: str

    @property
    def path(self) -> Path:
        return _CITY_RESOURCES / self.folder


class City:
    Chicago     = CityDefinition("Chicago",              "CHICAGO",              "CHICAGO")
    RaceCity2nd = CityDefinition("RaceCity 2nd Edition", "RACECITY_2ND_EDITION", "RC2E")
    RaceTrack7  = CityDefinition("Race Track 7",         "RACETRACK_7",          "RACETRACK7")
    RaceTrack8  = CityDefinition("Race Track 8",         "RACETRACK_8",          "RACETRACK8")
    RaceTrack10 = CityDefinition("Race Track 10",        "RACETRACK_10",         "RACETRACK10")
    RaceTrack14 = CityDefinition("Race Track 14",        "RACETRACK_14",         "RACETRACK14")

    # ── Custom cities (community maps; some ship their own custom props) ───────
    BoxDesignRaceway = CityDefinition("Box Design Raceway", "BOX_DESIGN_RACEWAY", "BDRW")
    Archipelago      = CityDefinition("Archipelago",        "ARCHIPELAGO",        "ARCH")
    OffroadMadness   = CityDefinition("Offroad Madness",    "OFFROAD_MADNESS",    "ORM")
    Seaview          = CityDefinition("Seaview",            "SEAVIEW",            "SEAVIEW")
    Paulville        = CityDefinition("Paulville",          "PAULVILLE",          "RACETRACK3")

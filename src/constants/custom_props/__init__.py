"""
Registry of custom props shipped with community maps.

Each custom city stores its prop assets under
`resources/editor/custom/<CITY_FOLDER>/{MESHES,BND,TUNE,TEXTURES}` and lists its
prop ids in a catalogue class. The registry maps a city to its catalogue + asset
roots so the Prop Editor can display them and the build can copy them.
"""
from pathlib import Path
from dataclasses import dataclass

from src.constants.city import City, CityDefinition
from src.constants.folder import TextureFolder
from src.constants.custom_props.box_design import BoxDesignProp
from src.constants.custom_props.archipelago import ArchipelagoProp
from src.constants.custom_props.offroad import OffroadProp
from src.constants.custom_props.seaview import SeaviewProp
from src.constants.custom_props.paulville import PaulvilleProp
from src.constants.custom_props.mm2_props import Mm2Prop


_EDITOR_CUSTOM = Path(__file__).parent.parent.parent.parent / "resources" / "editor" / "custom"


@dataclass(frozen=True)
class CustomCity:
    definition: CityDefinition
    catalogue:  type

    @property
    def root(self) -> Path:
        return _EDITOR_CUSTOM / self.definition.folder

    @property
    def mesh_root(self) -> Path:
        return self.root / "MESHES"

    @property
    def bnd_root(self) -> Path:
        return self.root / "BND"

    @property
    def tune_root(self) -> Path:
        return self.root / "TUNE"

    @property
    def texture_root(self) -> Path:
        return self.root / "TEXTURES"

    @property
    def prop_ids(self) -> list:
        return [v for k, v in vars(self.catalogue).items()
                if isinstance(v, str) and not k.startswith("_")]


# folder name → CustomCity
CUSTOM_CITIES = {
    City.BoxDesignRaceway.folder: CustomCity(City.BoxDesignRaceway, BoxDesignProp),
    City.Archipelago.folder:      CustomCity(City.Archipelago,      ArchipelagoProp),
    City.OffroadMadness.folder:   CustomCity(City.OffroadMadness,   OffroadProp),
    City.Seaview.folder:          CustomCity(City.Seaview,          SeaviewProp),
    City.Paulville.folder:        CustomCity(City.Paulville,        PaulvilleProp),  # textures only, no props
    City.Mm2Props.folder:         CustomCity(City.Mm2Props,         Mm2Prop),        # real MM2 prop meshes
}

# prop id (lowercased) → city folder
_PROP_TO_CITY = {
    pid.lower(): folder
    for folder, city in CUSTOM_CITIES.items()
    for pid in city.prop_ids
}


def get_custom_city(folder: str) -> CustomCity:
    """Return the CustomCity for a city folder name, or None."""
    return CUSTOM_CITIES.get(folder)


def custom_city_of_prop(prop_id: str) -> str:
    """Return the city folder a custom prop id belongs to, or None for stock props."""
    return _PROP_TO_CITY.get(prop_id.lower())


def all_custom_prop_ids() -> set:
    return set(_PROP_TO_CITY)


def custom_city_texture_folders(folder) -> list:
    """
    Extra texture-search folders (TEX16A, TEX16O) for a custom city's own
    geometry/prop DDS, given its city folder name or path. Empty list for stock
    cities. Append these to the editor TEXTURES pool when loading custom meshes.
    """
    name = Path(folder).name if folder else ""
    city = CUSTOM_CITIES.get(name)
    if not city:
        return []
    return [city.texture_root / TextureFolder.ALPHA, city.texture_root / TextureFolder.OPAQUE]

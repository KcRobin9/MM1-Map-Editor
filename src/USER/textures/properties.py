from src.constants.textures import Texture
from src.constants.file_formats import AgiTexParameters


texture_modifications = [
    {
        "name": Texture.ROAD_3_LANE,
        "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
    },
    {
        "name": Texture.ROAD_2_LANE,
        "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
    },
    {
        "name": Texture.ROAD_1_LANE,
        "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
    }
]
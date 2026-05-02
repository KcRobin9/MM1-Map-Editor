from src.constants.textures import Texture
from src.constants.file_formats import AgiTexParameters


texture_modifications = []


#! INFO
#! The example below is commented out, because (for example) transparent textures are not desired by default. 
#! You can uncomment and modify the example to set custom flags for specific textures. 
#! The "flags" list can contain any combination of AgiTexParameters, such as TRANSPARENT, ALPHA_GLOW, etc., 

# texture_modifications = [
#     {
#         "name": Texture.ROAD_2_LANE,
#         "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
#     },
#     {
#         "name": Texture.ROAD_1_LANE,
#         "flags": [AgiTexParameters.TRANSPARENT, AgiTexParameters.ALPHA_GLOW]
#     }
# ]
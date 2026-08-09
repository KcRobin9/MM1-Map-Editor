class Texture:
    SNOW = "SNOW"
    WOOD = "T_WOOD"
    WATER = "T_WATER"
    WATER_WINTER = "T_WATER_WIN"
    GRASS = "T_GRASS"
    GRASS_WINTER = "T_GRASS_WIN"
    GRASS_BASEBALL = "24_GRASS"

    SIDEWALK = "SDWLK2"
    ZEBRA_CROSSING = "RWALK"
    INTERSECTION = "RINTER"

    FREEWAY = "FREEWAY2"
    ROAD_1_LANE = "R2"
    ROAD_2_LANE = "R4"
    ROAD_3_LANE = "R6"
    ROAD = "ROAD"
    ICE = "L_RIVET"

    # Paved AREA surfaces (no lane lines) - for parking lots, plazas, open squares, dirt, piers.
    PARKING_LOT = "LMMALL_LOT"   # an actual parking-lot texture
    ASPHALT = "T_ASPHALT"        # clean asphalt, no lines
    CONCRETE = "T_CONCRETE01"    # concrete slab / civic square
    DIRT = "T_DIRT"              # dirt / gravel
    PIER = "R_NAVYPIER"          # Navy Pier decking - waterfront edge
    TUNNEL_WALL = "T_TUN_WALL"   # authentic Chicago tunnel wall (tunnel02 facade), in core.ar
    TUNNEL_TOP = "T_TUN_TOP"     # authentic Chicago tunnel ceiling/top, in core.ar

    BRICKS_MALL = "OT_MALL_BRICK"
    BRICKS_SAND = "OT_SHOP03_BRICK"
    BRICKS_GREY = "CT_FOOD_BRICK"
    WALL = "T_WALL"
    IND_WALL = "IND_WALL"
    INDUSTRIAL = "IND_ASPHALT"   # gritty industrial-yard ground (paved, oil-stained)
    RAIL = "T_RAIL03"            # see-through guardrail (alpha texture) - bridge/overpass deck edges
    SHOP_BRICK = "CT_SHOP_BRICK"
    MARKT_BRICK = "OT_MARKT_BRICK"

    GLASS = "R_WIN_01"
    STOP_SIGN = "T_STOP"
    BARRICADE = "T_BARRICADE"
    CHECKPOINT = "CHECK04"
    BUS_RED_TOP = "VPBUSRED_TP_BK"
    
    # Custom Textures (see: MM1-Map-Editor \ Custom Textures)
    LAVA = "T_WATER_LAVA"
    BARRICADE_RED_BLACK = "T_RED_BLACK_BARRICADE"
    

TEXTURE_EXPORT = {
    "SNOW": Texture.SNOW,
    "T_WOOD": Texture.WOOD,
    "T_WATER": Texture.WATER,
    "T_WATER_WIN": Texture.WATER_WINTER,
    "T_GRASS": Texture.GRASS,
    "T_GRASS_WIN": Texture.GRASS_WINTER,
    "24_GRASS": Texture.GRASS_BASEBALL,
    "SDWLK2": Texture.SIDEWALK,
    "RWALK": Texture.ZEBRA_CROSSING,
    "RINTER": Texture.INTERSECTION,
    "FREEWAY2": Texture.FREEWAY,
    "R2": Texture.ROAD_1_LANE,
    "R4": Texture.ROAD_2_LANE,
    "R6": Texture.ROAD_3_LANE,
    "OT_MALL_BRICK": Texture.BRICKS_MALL,
    "OT_SHOP03_BRICK": Texture.BRICKS_SAND,
    "CT_FOOD_BRICK": Texture.BRICKS_GREY,
    "R_WIN_01": Texture.GLASS,
    "T_STOP": Texture.STOP_SIGN,
    "T_BARRICADE": Texture.BARRICADE,
    "CHECK04": Texture.CHECKPOINT,
    "VPBUSRED_TP_BK": Texture.BUS_RED_TOP,
    "T_TUN_WALL": Texture.TUNNEL_WALL,
    "T_TUN_TOP": Texture.TUNNEL_TOP,
}


DDS_TO_CONSTANT = {
    v: k for k, v in vars(Texture).items()
    if not k.startswith('_') and isinstance(v, str)
}


# MM1 texture tag -> the real MM2 texture that replaces it when an MM2 poly carries no material of
# its own (psdl-import drops MM2's active texture-ref). Keeps an imported city fully MM2-textured.
MM2_TEXTURE_FALLBACK = {
    "R4":      "R4_F",
    "R6":      "R6_F",
    "RINTER":  "RINTER_F",
    "SDWLK2":  "SWALK_F",
    "T_GRASS": "S_GRASS",
    "T_WATER": "S_WATER",
}

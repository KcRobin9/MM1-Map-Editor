"""
MM2 -> MM1 asset mappings.

Lookup tables that translate Midtown Madness 2's own names into the MM1 equivalents the editor
emits. Kept here, beside the other constants, so the MM2 modules stay parsing/emitting code.
"""
from src.constants.color import Color
from src.constants.modes import RaceMode
from src.constants.vehicles import PlayerCar
from src.constants.textures import Texture
from src.constants.file_formats import Material


class Mm2City:
    """The MM2 cities the converter knows how to build.

    Each has its own .ar (MM2SF.ar, MM2BA.ar, ...) so they coexist in MidtownMadness/ and are picked
    by race locale in-game. The per-city source paths live in the gitignored settings/local.py as
    CITY_CFGS --- this is only the set of names.
    """
    SAN_FRANCISCO = "SF"          # stock MM2
    LONDON        = "LONDON"      # stock MM2
    NEW_YORK      = "NY"          # community-made
    BUENOS_AIRES  = "BA"          # community-made

    ALL = (SAN_FRANCISCO, LONDON, NEW_YORK, BUENOS_AIRES)


class Mm2RaceType:
    """MM2's race-type names, and what each becomes in MM1.

    A checkpoint race carries three different names: MM2 calls it "race" in its file names and
    "Checkpoint" in its .cinfo, while MM1 uses RaceMode.CHECKPOINT ("RACE") as the file prefix.
    Mapping them here keeps that from being re-derived, differently, at each call site.
    """
    ALL = ("blitz", "race", "circuit")
    TO_RACE_MODE = {"blitz": RaceMode.BLITZ, "race": RaceMode.CHECKPOINT, "circuit": RaceMode.CIRCUIT}
    TO_CINFO_KEY = {"blitz": "blitz", "race": "checkpoint", "circuit": "circuit"}


class Mm2CellPreview:
    """Names shared by the MM2 Blender cell preview and the edit round-trip that reads it back.

    The preview (create_blender_meshes_merged_by_cell) writes these; the exporter
    (operators/mm2_cells.py) reads them. They MUST agree --- if one side is renamed on its own the
    round-trip silently exports nothing, so both sides take the names from here.
    """
    COLLECTION = "MM2 Cells"        # collection holding one merged object per landmark cell
    OBJECT_PREFIX = "Cell"          # object naming: Cell<bound_number>

    CELL_ID = "mm2_cell"            # object custom property: which landmark cell this object is
    OBJECT_TYPE = "mm2_ot"          # face int attribute: index into OBJECT_TYPE_LEGEND
    OBJECT_TYPE_LEGEND = "mm2_ot_legend"   # object custom property: JSON list of obj_type names

    # Exported overrides file, written by the operator and read by the build:
    # src/USER/mm2_edits/<MAP_FILENAME>cell_overrides.json
    OVERRIDES_SUFFIX = "cell_overrides"


# MM2 object type -> (MM1 texture tag, physics material, hud colour). Every tag ships in core.ar.
MM2_OBJECT_TYPE = {
    # object type        texture                material          hud colour
    "road":              (Texture.ROAD_2_LANE,   Material.DEFAULT, Color.ROAD),
    "divided_road":      (Texture.ROAD_2_LANE,   Material.DEFAULT, Color.ROAD),
    "walkway":           (Texture.ROAD_2_LANE,   Material.DEFAULT, Color.ROAD),
    "road_triangle_fan": (Texture.INTERSECTION,  Material.DEFAULT, Color.ROAD),        # 0x05 junction
    "triangle_fan":      (Texture.GRASS,         Material.GRASS,   Color.GRASS),       # 0x06 ground fan
    "sidewalk_strip":    (Texture.SIDEWALK,      Material.DEFAULT, Color.WHITE_DARK),
    "crosswalk":         (Texture.SIDEWALK,      Material.DEFAULT, Color.ROAD),
    "facade":            (Texture.BRICKS_GREY,   Material.DEFAULT, Color.IND_WALL),
    "sliver":            (Texture.BRICKS_GREY,   Material.DEFAULT, Color.IND_WALL),
    "roof_triangle_fan": (Texture.BRICKS_GREY,   Material.DEFAULT, Color.IND_WALL),
}

MM2_OBJECT_TYPE_DEFAULT = (Texture.ROAD_2_LANE, Material.DEFAULT, Color.ROAD)


# MM2 prop model name -> MM1 prop: the single table lives in
# src/constants/custom_props/mm2_props.py (MM2_PROP_MODELS) and is served by
# src/game/mapgen/mm2/mm2_props._build_model_map() for both the pathset and the density placer.

# MM2 opponent car -> the closest MM1 player car. MM2 cars with no MM1 counterpart fall back to a
# similar class (Aston -> Panoz GTR1, Audi TT -> Fastback, VW Cup -> Beetle).
MM2_OPPONENT_CAR = {
    "vpbug":        PlayerCar.VW_BEETLE,
    "vpcaddie":     PlayerCar.CADILLAC,
    "vpcop":        PlayerCar.POLICE,
    "vpford":       PlayerCar.FORD_F350,
    "vpbullet":     PlayerCar.FASTBACK,
    "vpmustang99":  PlayerCar.MUSTANG_GT,
    "vppanoz":      PlayerCar.ROADSTER,
    "vppanozgt":    PlayerCar.PANOZ_GTR1,
    "vpbus":        PlayerCar.CITY_BUS,
    "vpsemi":       PlayerCar.SEMI,
    "vpdb7":        PlayerCar.PANOZ_GTR1,
    "vpauditt":     PlayerCar.FASTBACK,
    "vpvwcup":      PlayerCar.VW_BEETLE,
    "vpcoop":       PlayerCar.VW_BEETLE,
    "vpcoop2k":     PlayerCar.VW_BEETLE,
    "vpcab":        PlayerCar.CADILLAC,
    "vp4x4":        PlayerCar.FORD_F350,
    "vpmtruck":     PlayerCar.FORD_F350,
    "vpfer":        PlayerCar.ROADSTER,
}

MM2_OPPONENT_CAR_DEFAULT = PlayerCar.VW_BEETLE

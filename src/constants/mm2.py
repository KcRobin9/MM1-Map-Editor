"""
MM2 -> MM1 asset mappings.

Lookup tables that translate Midtown Madness 2's own names into the MM1 equivalents the editor
emits. Kept here, beside the other constants, so the MM2 modules stay parsing/emitting code.
"""
from src.constants.color import Color
from src.constants.modes import RaceMode
from src.constants.props import Prop, BangerFlags
from src.constants.textures import Texture
from src.constants.file_formats import Material
from src.constants.custom_props.mm2_props import Mm2Prop


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


_BREAKABLE = BangerFlags.BREAKABLE
_BREAKABLE_GLOW = BangerFlags.BREAKABLE_GLOW


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


# MM2 pathset model name -> (MM1 prop id, banger flags). Models with no sensible MM1 stand-in are
# absent, and the pathset importer skips them.
MM2_PATHSET_PROP = {
    "sp_tree1_s":           (Mm2Prop.TREE, _BREAKABLE),                  # REAL MM2 tree mesh (alpha)
    "sp_tree6_s":           (Mm2Prop.TREE6, _BREAKABLE),                 # REAL MM2 tree mesh (alpha)
    "sp_treepalm4_f":       (Mm2Prop.PALM, _BREAKABLE),                   # REAL MM2 palm mesh
    "sp_lightstreet_rt_f":  (Mm2Prop.LAMP, _BREAKABLE_GLOW),   # REAL MM2 banner lamp
    "sp_lightstreet_f":     (Prop.LIGHT_SIDEWALK, _BREAKABLE_GLOW),
    "sp_traflitsingle_f":   (Prop.TRAFFIC_LIGHT_SINGLE, _BREAKABLE),
    "sp_traflitdual_f":     (Prop.TRAFFIC_LIGHT_DUAL, _BREAKABLE),
    "sp_benchwood_f":       (Mm2Prop.BENCH, _BREAKABLE),                  # REAL MM2 bench mesh
    "sp_dumpstr_f":         (Mm2Prop.DUMPSTER, _BREAKABLE),               # REAL MM2 dumpster mesh
    "sp_mailbox_f":         (Mm2Prop.MAIL, _BREAKABLE),                   # REAL MM2 mailbox mesh
    "sp_cone_f":            (Prop.CONE, _BREAKABLE),                      # MM2 cone has no texture -> MM1 cone
    "sp_barricadewood_f":   (Mm2Prop.BARRICADE, _BREAKABLE),             # REAL MM2 wooden barricade
    "sp_crashbarrelgroup_f":(Mm2Prop.CRASHBARREL, _BREAKABLE),           # REAL MM2 crash barrels
    "sp_stackboxbarrel_f":  (Mm2Prop.BOXBARREL, _BREAKABLE),             # REAL MM2 box/barrel stack
    "sp_stackboxcard_f":    (Mm2Prop.BOXCARD, _BREAKABLE),               # REAL MM2 cardboard boxes
    "sp_cleat_f":           (Mm2Prop.CLEAT, _BREAKABLE),                 # REAL MM2 dock cleat (was skipped)
    "sp_stop_f":            (Mm2Prop.STOP, _BREAKABLE),                  # REAL MM2 stop sign (alpha face)
    "sp_noenter_f":         (Mm2Prop.NOENTER, _BREAKABLE),               # REAL MM2 no-entry sign
    "sp_wrongwayfw":        (Mm2Prop.WRONGWAY, _BREAKABLE),              # REAL MM2 wrong-way sign
    # the last skipped pathset props -> now real MM2 meshes too (SF prop set is 100% real meshes)
    "sp_hotdogcart_f":      (Mm2Prop.HOTDOG, _BREAKABLE),
    "sp_hillwarn_f":        (Mm2Prop.HILLWARN, _BREAKABLE),
    "sp_transbayexit_f":    (Mm2Prop.EXIT_TB, _BREAKABLE),
    "sp_marinexit_f":       (Mm2Prop.EXIT_MAR, _BREAKABLE),
    "sp_civcentrexit_f":    (Mm2Prop.EXIT_CC, _BREAKABLE),
    "sp_ggexit_f":          (Mm2Prop.EXIT_GG, _BREAKABLE),
    "sp_embarcexit_f":      (Mm2Prop.EXIT_EMB, _BREAKABLE),
    "np_ghirardelli_f":     (Mm2Prop.GDELLI, _BREAKABLE),
    "cp_banrred_f":         (Mm2Prop.BANNER_RED, _BREAKABLE),
    "cp_banrred_30_f":      (Mm2Prop.BANNER_RED, _BREAKABLE),
    "cp_banrblu_f":         (Mm2Prop.BANNER_BLU, _BREAKABLE),
    "cp_banrblu_20_f":      (Mm2Prop.BANNER_BLU, _BREAKABLE),
    "cp_banryel_f":         (Mm2Prop.BANNER_YEL, _BREAKABLE),
    "cp_banryel_20_f":      (Mm2Prop.BANNER_YEL, _BREAKABLE),
    # ── London props (city/london/props.pathset) -> real London meshes ──────────────
    "sp_bollard_stone_l":   (Mm2Prop.BOLLARD_STONE, _BREAKABLE),
    "sp_bollard_black_l":   (Mm2Prop.BOLLARD_BLACK, _BREAKABLE),
    "sp_lightpark_f":       (Mm2Prop.LIGHT_PARK, _BREAKABLE_GLOW),
    "sp_dumpstr_l":         (Mm2Prop.DUMPSTER_L, _BREAKABLE),
    "sp_cone_l":            (Mm2Prop.CONE_L, _BREAKABLE),
    "sp_oaktree1_s":        (Mm2Prop.OAK, _BREAKABLE),
    "sp_stackboxes_4_l":    (Mm2Prop.BOXES4, _BREAKABLE),
    "sp_lightthames_l":     (Mm2Prop.LIGHT_THAMES, _BREAKABLE_GLOW),
    "sp_pilaster_l":        (Mm2Prop.PILASTER, _BREAKABLE),
    "sp_cenotaph_gen_l":    (Mm2Prop.CENOTAPH, _BREAKABLE),
    "sp_barrelwood_l":      (Mm2Prop.BARREL_WOOD, _BREAKABLE),
    "wp_buck_fence_l":      (Mm2Prop.FENCE, _BREAKABLE),
    "op_eros_l":            (Mm2Prop.EROS, _BREAKABLE),
    "sp_can_gen_f":         (Prop.BIN, _BREAKABLE),                      # NOTEXTURE mesh -> MM1 bin
    # --- DP_WALL-in-the-road FIX ----------------------------------------------------------------
    # r4i_rails_f (freeway railings, 329 type-2 line-strip insts) + sp_fwsupport_f (freeway pillars)
    # were mapped to the MM1 WALL_LOW placeholder = a big "DP_WALL" box. The pathset path runs the
    # FREEWAY CENTRELINE (no edge data), so the WALL_LOW boxes marched down the MIDDLE of the
    # carriageway. r4i_rails_f has NO .pkg mesh at all (placeholder-only), so it can only ever be an
    # ugly box. -> SKIP both (they fall through to `skipped`) until proper edge-offset rails exist.
    # To restore freeway barriers later: re-add with a real mesh (sp_fwsupport_f HAS a .pkg pillar
    # mesh -> could become a real Mm2Prop) and a lateral edge offset so they sit on the road edges.
    # "r4i_rails_f":          (Prop.WALL_LOW, BangerFlags.DRIVABLE_SOLID),
    # "sp_fwsupport_f":       (Prop.WALL_LOW, BangerFlags.DRIVABLE_SOLID),  # freeway pillars
}

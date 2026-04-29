import bpy

from src.constants.misc import Executable
from src.helpers.main import is_process_running
from src.integrations.blender.modeling.uv_mapping import OBJECT_OT_UpdateUVMapping

from src.integrations.blender.operators.custom_properties import OBJECT_OT_AssignCustomProperties
from src.integrations.blender.operators.export_polygons import OBJECT_OT_ExportPolygons
from src.integrations.blender.operators.process_extrude import OBJECT_OT_ProcessPostExtrude
from src.integrations.blender.operators.rename_polygons import (
    OBJECT_OT_RenameSequential,
    OBJECT_OT_FixPolygonNames, OBJECT_OT_CreatePolygon, OBJECT_OT_DuplicatePolygon
)
from src.integrations.blender.operators.polygon_presets import OBJECT_OT_SpawnPreset, PRESET_ITEMS
from src.integrations.blender.operators.ai_streets import (
    AI_STREET_CLASSES,
    INTERSECTION_TYPE_ITEMS, STOP_LIGHT_NAME_ITEMS,
    st_intersection_update, st_tl_update,
)
from src.integrations.blender.operators.ai_street_presets import (
    STREET_PRESET_CLASSES, ST_PRESET_ITEMS,
)
from src.integrations.blender.operators.waypoints import WAYPOINT_CLASSES

from src.integrations.blender.panels.cells import OBJECT_PT_CellTypePanel, CELL_IMPORT
from src.integrations.blender.panels.hud import OBJECT_PT_HUDColorPanel, HUD_COLOR_ITEMS, HUD_IMPORT
from src.integrations.blender.panels.materials import OBJECT_PT_MaterialTypePanel, MATERIAL_IMPORT
from src.integrations.blender.panels.misc import OBJECT_PT_PolygonMiscOptionsPanel
from src.integrations.blender.panels.vertex import OBJECT_PT_VertexCoordinates, VertexGroup
from src.integrations.blender.panels.uv import OBJECT_PT_UVMappingPanel
from src.integrations.blender.panels.sidebar import SIDEBAR_CLASSES
from src.integrations.blender.panels.ai_streets_sidebar import STREET_EDITOR_CLASSES
from src.integrations.blender.panels.waypoint_sidebar import WAYPOINT_EDITOR_CLASSES
from src.integrations.blender.panels.prop_sidebar import PROP_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.props import PROP_EDITOR_CLASSES, PROP_NAME_ITEMS, PROP_NAME_ITEMS_FROM, PROP_NAME_ITEMS_TO, _update_prop_form
from src.integrations.blender.panels.car_editor_sidebar import CAR_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.car_editor import CAR_EDITOR_CLASSES, update_ce_face_texture, update_ce_face_uv
from src.integrations.blender.waypoints.draw import register_draw_handler, unregister_draw_handler
from src.integrations.blender.modeling.uv_mapping import TEXTURE_ENUM_ITEMS, update_texture_name, update_uv_tiling
from src.integrations.blender.operators.road_builder import ROAD_BUILDER_CLASSES, ROAD_TYPE_ITEMS
from src.integrations.blender.panels.road_builder_sidebar import ROAD_BUILDER_PANEL_CLASSES
from src.integrations.blender.operators.facades import FACADE_EDITOR_CLASSES, FACADE_NAME_ITEMS, FACADE_FLAGS_ITEMS, _update_facade_form
from src.integrations.blender.panels.facade_editor_sidebar import FACADE_EDITOR_PANEL_CLASSES


PANEL_CLASSES = [
    OBJECT_PT_CellTypePanel,
    OBJECT_PT_MaterialTypePanel,
    OBJECT_PT_PolygonMiscOptionsPanel,
    OBJECT_PT_HUDColorPanel,
    OBJECT_PT_VertexCoordinates,
    OBJECT_PT_UVMappingPanel,
    *SIDEBAR_CLASSES,
    *STREET_EDITOR_CLASSES,
    *WAYPOINT_EDITOR_CLASSES,
    *PROP_EDITOR_PANEL_CLASSES,
    *CAR_EDITOR_PANEL_CLASSES,
    *ROAD_BUILDER_PANEL_CLASSES,
    *FACADE_EDITOR_PANEL_CLASSES,
]

OPERATOR_CLASSES = [
    OBJECT_OT_UpdateUVMapping,
    OBJECT_OT_ExportPolygons,
    OBJECT_OT_AssignCustomProperties,
    OBJECT_OT_ProcessPostExtrude,
    OBJECT_OT_RenameSequential,
    OBJECT_OT_FixPolygonNames,
    OBJECT_OT_CreatePolygon,
    OBJECT_OT_DuplicatePolygon,
    OBJECT_OT_SpawnPreset,
    *AI_STREET_CLASSES,
    *STREET_PRESET_CLASSES,
    *PROP_EDITOR_CLASSES,
    *CAR_EDITOR_CLASSES,
    *ROAD_BUILDER_CLASSES,
    *FACADE_EDITOR_CLASSES,
]

ALL_CLASSES = [VertexGroup] + PANEL_CLASSES + OPERATOR_CLASSES + WAYPOINT_CLASSES

OBJECT_PROPERTIES = [
    "vertex_coords", "hud_color",
    "tile_x", "tile_y", "angle_degrees", "texture_name",
    "cell_type", "material_index", "always_visible", "sort_vertices",
    # Road Builder spine properties
    "rs_lane_count", "rs_lane_width",
    "rs_curb_width", "rs_curb_height",
    "rs_sidewalk_width", "rs_sidewalk_height",
    "rs_banking_auto", "rs_banking_max_deg",
    "rs_road_tile_x", "rs_road_tile_y",
    # Street properties
    "st_group_name",
    "st_intersection_0", "st_intersection_1",
    "st_stop_light_name_0", "st_stop_light_name_1",
    "st_traffic_blocked_0", "st_traffic_blocked_1",
    "st_ped_blocked_0", "st_ped_blocked_1",
    "st_road_divided", "st_alley",
    "st_sl_pos_0_offset", "st_sl_pos_0_dir",
    "st_sl_pos_1_offset", "st_sl_pos_1_dir",
]

SCENE_PROPERTIES = [
    "replace_in_script",
    "polygon_create_width",
    "polygon_create_length",
    "polygon_create_shape",
    "polygon_preset",
    # Waypoint Editor
    "wp_race_type",
    "wp_race_index_enum",
    "wp_create_type",
    "wp_export_brackets",
    "wp_create_x",
    "wp_create_y",
    "wp_create_z",
    "wp_show_paths",
    "wp_insert_index",
    # Prop Editor
    "pe_active_group_id",
    "pe_active_group_type",
    "pe_prop_name",
    "pe_offset_x",
    "pe_offset_y",
    "pe_offset_z",
    "pe_has_end",
    "pe_end_x",
    "pe_end_y",
    "pe_end_z",
    "pe_angle",
    "pe_area_x1",
    "pe_area_y1",
    "pe_area_z1",
    "pe_area_x2",
    "pe_area_y2",
    "pe_area_z2",
    "pe_seed",
    "pe_rand_count",
    # Replace Prop Type tool
    "pr_from_name",
    "pr_to_name",
    # Create Prop form
    "pc_prop_type",
    "pc_prop_name",
    "pc_offset_x",
    "pc_offset_y",
    "pc_offset_z",
    "pc_has_end",
    "pc_end_x",
    "pc_end_y",
    "pc_end_z",
    "pc_angle",
    "pc_area_x1",
    "pc_area_y1",
    "pc_area_z1",
    "pc_area_x2",
    "pc_area_y2",
    "pc_area_z2",
    "pc_seed",
    "pc_rand_count",
    # Street Editor — vertex tools
    "st_sl_pos_expanded",
    "st_show_arrows",
    "st_vertex_index",
    "st_extend_length",
    "st_extend_angle",
    "st_extend_elevation",
    "st_snap_to_terrain",
    # Car Editor
    "ce_car_folder",
    "ce_texture_folder",
    "ce_load_lights",
    "ce_auto_reload",
    "ce_assign_slot",
    "ce_face_tile_x",
    "ce_face_tile_y",
    "ce_face_rotation",
    "ce_add_shape",
    "ce_add_size",
    "ce_new_tex_name",
    "ce_active_face_index",
    "ce_face_texture",
    "ce_uv_updating",
    "ce_add_to_city",
    "ce_start_game",
    "ce_last_export_dir",
    "ce_show_damage",
    "ce_paint_variant",
    # Street Editor — presets
    "st_street_preset",
    "st_preset_length",
    "st_preset_lane_width",
    "st_preset_turn_radius",
    "st_preset_curve_points",
    "st_preset_length_split",
    "st_preset_lanes",
    "st_preset_lane_separator",
    "st_preset_grouped",
    "st_preset_converge_start",
    "st_preset_converge_end",
    "st_preset_direction",
    "st_poly_from",
    "st_poly_to",
    "st_poly_info_expanded",
    # Road Builder scene properties
    "rd_extend_length", "rd_extend_angle", "rd_extend_elevation",
    "rd_snap_to_terrain", "rd_road_type",
    # Facade Editor — edit form
    "fe_active_group_id",
    "fe_facade_name",
    "fe_flags",
    "fe_offset_x", "fe_offset_y", "fe_offset_z",
    "fe_end_x",    "fe_end_y",    "fe_end_z",
    "fe_axis",
    "fe_separator",
    "fe_sides_x",  "fe_sides_y",  "fe_sides_z",
    "fe_scale_auto",
    "fe_scale",
    # Facade Editor — create form
    "fc_facade_name",
    "fc_flags",
    "fc_offset_x", "fc_offset_y", "fc_offset_z",
    "fc_end_x",    "fc_end_y",    "fc_end_z",
    "fc_axis",
    "fc_separator",
    "fc_sides_x",  "fc_sides_y",  "fc_sides_z",
    "fc_scale_auto",
    "fc_scale",
]


def register_object_properties() -> None:
    bpy.types.Object.hud_color = bpy.props.EnumProperty(
        name="HUD",
        description="HUD minimap color for this polygon",
        items=HUD_COLOR_ITEMS,
        default=HUD_COLOR_ITEMS[0][0],
    )
    bpy.types.Object.tile_x = bpy.props.FloatProperty(
        name="Tile X", default=2.0, update=update_uv_tiling
    )
    bpy.types.Object.tile_y = bpy.props.FloatProperty(
        name="Tile Y", default=2.0, update=update_uv_tiling
    )
    bpy.types.Object.angle_degrees = bpy.props.FloatProperty(
        name="Angle Degrees", default=0.0, update=update_uv_tiling
    )
    bpy.types.Object.texture_name = bpy.props.EnumProperty(
        name="Texture",
        description="Texture used by this polygon",
        items=TEXTURE_ENUM_ITEMS,
        update=update_texture_name
    )
    bpy.types.Object.always_visible = bpy.props.BoolProperty(
        name="Always Visible",
        description="If true, the polygon is always visible",
        default=False
    )
    bpy.types.Object.sort_vertices = bpy.props.BoolProperty(
        name="Sort Vertices",
        description="If true, sort the vertices",
        default=False
    )
    bpy.types.Object.cell_type = bpy.props.EnumProperty(
        items=CELL_IMPORT,
        name="Cell Type",
        description="Select the type of cell"
    )
    bpy.types.Object.material_index = bpy.props.EnumProperty(
        items=MATERIAL_IMPORT,
        name="Material Type",
        description="Select the type of material"
    )


def register_street_properties() -> None:
    bpy.types.Object.st_group_name = bpy.props.StringProperty(
        name="Group Name",
        description="If set, this street exports together with others sharing this name (multi-lane format)",
        default="",
    )
    bpy.types.Object.st_intersection_0 = bpy.props.EnumProperty(
        name="Intersection Type (Start)",
        items=INTERSECTION_TYPE_ITEMS,
        default="3",  # IntersectionType.CONTINUE
        update=st_intersection_update
    )
    bpy.types.Object.st_intersection_1 = bpy.props.EnumProperty(
        name="Intersection Type (End)",
        items=INTERSECTION_TYPE_ITEMS,
        default="3",
        update=st_intersection_update
    )
    bpy.types.Object.st_stop_light_name_0 = bpy.props.EnumProperty(
        name="Stop Light (Start)",
        items=STOP_LIGHT_NAME_ITEMS,
        update=st_tl_update,
    )
    bpy.types.Object.st_stop_light_name_1 = bpy.props.EnumProperty(
        name="Stop Light (End)",
        items=STOP_LIGHT_NAME_ITEMS,
        update=st_tl_update,
    )
    _YES_NO_ITEMS = [("YES", "Yes", ""), ("NO", "No", "")]
    bpy.types.Object.st_traffic_blocked_0 = bpy.props.EnumProperty(
        name="Traffic Blocked (Start)", items=_YES_NO_ITEMS, default="NO"
    )
    bpy.types.Object.st_traffic_blocked_1 = bpy.props.EnumProperty(
        name="Traffic Blocked (End)", items=_YES_NO_ITEMS, default="NO"
    )
    bpy.types.Object.st_ped_blocked_0 = bpy.props.EnumProperty(
        name="Ped Blocked (Start)", items=_YES_NO_ITEMS, default="NO"
    )
    bpy.types.Object.st_ped_blocked_1 = bpy.props.EnumProperty(
        name="Ped Blocked (End)", items=_YES_NO_ITEMS, default="NO"
    )
    bpy.types.Object.st_road_divided = bpy.props.EnumProperty(
        name="Road Divided", items=_YES_NO_ITEMS, default="NO"
    )
    bpy.types.Object.st_alley = bpy.props.EnumProperty(
        name="Alley", items=_YES_NO_ITEMS, default="NO"
    )
    bpy.types.Object.st_sl_pos_0_offset = bpy.props.FloatVectorProperty(
        name="SL 0 Offset", size=3, default=(0.0, 0.0, 0.0), subtype='XYZ',
        update=st_tl_update,
    )
    bpy.types.Object.st_sl_pos_0_dir = bpy.props.FloatVectorProperty(
        name="SL 0 Direction", size=3, default=(0.01, 0.0, 0.0), subtype='XYZ',
        update=st_tl_update,
    )
    bpy.types.Object.st_sl_pos_1_offset = bpy.props.FloatVectorProperty(
        name="SL 1 Offset", size=3, default=(0.0, 0.0, 0.0), subtype='XYZ',
        update=st_tl_update,
    )
    bpy.types.Object.st_sl_pos_1_dir = bpy.props.FloatVectorProperty(
        name="SL 1 Direction", size=3, default=(0.01, 0.0, 0.0), subtype='XYZ',
        update=st_tl_update,
    )


def register_road_builder_properties() -> None:
    bpy.types.Object.rs_lane_count = bpy.props.IntProperty(
        name="Lanes", default=2, min=1, max=6,
        description="Number of lanes in this road",
    )
    bpy.types.Object.rs_lane_width = bpy.props.FloatProperty(
        name="Lane Width", default=4.0, min=1.0, soft_max=20.0,
    )
    bpy.types.Object.rs_curb_width = bpy.props.FloatProperty(
        name="Curb Width", default=0.8, min=0.0, soft_max=5.0,
        description="Width of the raised curb strip (0 = no curb)",
    )
    bpy.types.Object.rs_curb_height = bpy.props.FloatProperty(
        name="Curb Height", default=0.15, min=0.0, soft_max=2.0,
    )
    bpy.types.Object.rs_sidewalk_width = bpy.props.FloatProperty(
        name="Sidewalk Width", default=2.5, min=0.0, soft_max=20.0,
        description="Width of the sidewalk / shoulder (0 = none)",
    )
    bpy.types.Object.rs_sidewalk_height = bpy.props.FloatProperty(
        name="Sidewalk Height", default=0.15, min=0.0, soft_max=2.0,
    )
    bpy.types.Object.rs_banking_auto = bpy.props.BoolProperty(
        name="Auto Banking",
        description="Automatically tilt cross-section on curves",
        default=False,
    )
    bpy.types.Object.rs_banking_max_deg = bpy.props.FloatProperty(
        name="Max Banking",
        description="Maximum banking angle at a 90° turn",
        default=15.0, min=0.0, soft_max=45.0,
    )
    bpy.types.Object.rs_road_tile_x = bpy.props.FloatProperty(
        name="Road Tile X", default=2.0, min=0.1, soft_max=10.0,
    )
    bpy.types.Object.rs_road_tile_y = bpy.props.FloatProperty(
        name="Road Tile Y", default=2.0, min=0.1, soft_max=10.0,
    )


def register_scene_properties() -> None:
    bpy.types.Scene.replace_in_script = bpy.props.BoolProperty(
        name="Replace in Script",
        description="When exporting all polygons, also replace the create_polygon / save_mesh section in MAP_EDITOR_ALPHA_v1.py",
        default=False,
    )
    bpy.types.Scene.polygon_create_width = bpy.props.FloatProperty(
        name="Width", default=15.0, min=0.1, soft_max=200.0
    )
    bpy.types.Scene.polygon_create_length = bpy.props.FloatProperty(
        name="Length", default=15.0, min=0.1, soft_max=200.0
    )
    bpy.types.Scene.polygon_create_shape = bpy.props.EnumProperty(
        name="Shape",
        items=[('QUAD', 'Quad', ''), ('TRI', 'Triangle', '')],
        default='QUAD'
    )
    bpy.types.Scene.polygon_preset = bpy.props.EnumProperty(
        name="Preset",
        items=PRESET_ITEMS,
        default="ROAD_SIDEWALK"
    )

    # ── Waypoint Editor scene properties ─────────────────────────────────────
    from src.USER.races.races import race_data as _race_data

    def _available_race_items(self, context):
        from src.integrations.blender.panels.waypoint_sidebar import _available_race_items
        return _available_race_items(context.scene.wp_race_type)

    bpy.types.Scene.wp_race_type = bpy.props.EnumProperty(
        name="Race Type",
        description="Type of race to load waypoints for",
        items=[
            ("BLITZ",      "Blitz",      "Timed blitz race (max 11 waypoints)"),
            ("CIRCUIT",    "Circuit",    "Circuit / lap race"),
            ("CHECKPOINT", "Checkpoint", "Checkpoint race (stored as RACE_N)"),
        ],
        default="BLITZ",
    )
    bpy.types.Scene.wp_race_index_enum = bpy.props.EnumProperty(
        name="Race",
        description="Which race to load waypoints for — only shows races defined in races.py",
        items=_available_race_items,
    )
    bpy.types.Scene.wp_create_type = bpy.props.EnumProperty(
        name="Create Type",
        description="What kind of object to create at the 3D cursor",
        items=[
            ("WAYPOINT", "Waypoint",       "Race waypoint (WP_...)"),
            ("BANK",     "CnR Bank",       "Cops & Robbers bank / blue team hideout (CR_Bank...)"),
            ("GOLD",     "CnR Gold",       "Cops & Robbers gold position (CR_Gold...)"),
            ("ROBBER",   "CnR Robber",     "Cops & Robbers robber / red team hideout (CR_Robber...)"),
        ],
        default="WAYPOINT",
    )
    bpy.types.Scene.wp_export_brackets = bpy.props.BoolProperty(
        name="Add Brackets",
        description="Wrap each exported waypoint line in [ ] for direct paste into races.py",
        default=False,
    )
    bpy.types.Scene.wp_create_x = bpy.props.FloatProperty(name="X", default=0.0)
    bpy.types.Scene.wp_create_y = bpy.props.FloatProperty(name="Y", default=0.0)
    bpy.types.Scene.wp_create_z = bpy.props.FloatProperty(name="Z", default=0.0)
    bpy.types.Scene.wp_show_paths = bpy.props.BoolProperty(
        name="Show Path Lines",
        description="Draw lines between consecutive waypoints in the 3D viewport",
        default=True,
    )
    bpy.types.Scene.wp_insert_index = bpy.props.IntProperty(
        name="Insert at Index",
        description="Insert new waypoint at this index (-1 = append at end)",
        default=-1,
        min=-1,
    )

    # ── Prop Editor scene properties ──────────────────────────────────────────
    bpy.types.Scene.pe_active_group_id = bpy.props.StringProperty(
        name="Active Prop Group ID",
        description="Internal: which prop group is being edited",
        default="",
    )
    bpy.types.Scene.pe_active_group_type = bpy.props.StringProperty(
        name="Active Prop Group Type",
        description="Internal: 'fixed' or 'random'",
        default="fixed",
    )
    # Prop name dropdown
    bpy.types.Scene.pe_prop_name = bpy.props.EnumProperty(
        name="Prop",
        description="Select prop type",
        items=PROP_NAME_ITEMS,
        update=_update_prop_form,
    )
    # Fixed prop offset (game coords)
    bpy.types.Scene.pe_offset_x = bpy.props.FloatProperty(name="X", default=0.0, update=_update_prop_form)
    bpy.types.Scene.pe_offset_y = bpy.props.FloatProperty(name="Y", default=0.0, description="Height", update=_update_prop_form)
    bpy.types.Scene.pe_offset_z = bpy.props.FloatProperty(name="Z", default=0.0, update=_update_prop_form)
    # Fixed prop end (row props)
    bpy.types.Scene.pe_has_end = bpy.props.BoolProperty(
        name="Has End", description="Enable to make this a row of props", default=False,
        update=_update_prop_form,
    )
    bpy.types.Scene.pe_end_x = bpy.props.FloatProperty(name="X", default=0.0, update=_update_prop_form)
    bpy.types.Scene.pe_end_y = bpy.props.FloatProperty(name="Y", default=0.0, description="Height", update=_update_prop_form)
    bpy.types.Scene.pe_end_z = bpy.props.FloatProperty(name="Z", default=0.0, update=_update_prop_form)
    # Fixed prop angle
    bpy.types.Scene.pe_angle = bpy.props.FloatProperty(
        name="Angle", default=0.0, description="Facing angle in degrees (0=East, 90=North)",
        update=_update_prop_form,
    )
    # Random prop area
    bpy.types.Scene.pe_area_x1 = bpy.props.FloatProperty(name="X", default=0.0, update=_update_prop_form)
    bpy.types.Scene.pe_area_y1 = bpy.props.FloatProperty(name="Y", default=0.0, update=_update_prop_form)
    bpy.types.Scene.pe_area_z1 = bpy.props.FloatProperty(name="Z", default=0.0, update=_update_prop_form)
    bpy.types.Scene.pe_area_x2 = bpy.props.FloatProperty(name="X", default=100.0, update=_update_prop_form)
    bpy.types.Scene.pe_area_y2 = bpy.props.FloatProperty(name="Y", default=0.0, update=_update_prop_form)
    bpy.types.Scene.pe_area_z2 = bpy.props.FloatProperty(name="Z", default=100.0, update=_update_prop_form)
    # Random prop seed / count
    bpy.types.Scene.pe_seed = bpy.props.IntProperty(
        name="Seed", default=0, min=0, description="Random seed for placement",
        update=_update_prop_form,
    )
    bpy.types.Scene.pe_rand_count = bpy.props.IntProperty(
        name="Count", default=1, min=1, description="Number of props to place (count / num_props)",
        update=_update_prop_form,
    )
    # Replace Prop Type tool
    bpy.types.Scene.pr_from_name = bpy.props.EnumProperty(
        name="From",
        description="Prop type to replace. ALL matches every type in the scene.",
        items=PROP_NAME_ITEMS_FROM,
        default="__ALL__",
    )
    bpy.types.Scene.pr_to_name = bpy.props.EnumProperty(
        name="To",
        description="New prop type. RANDOM picks a different random type for each group.",
        items=PROP_NAME_ITEMS_TO,
    )

    # ── Create Prop form scene properties ─────────────────────────────────────
    bpy.types.Scene.pc_prop_type = bpy.props.EnumProperty(
        name="Type",
        description="Type of prop group to create",
        items=[
            ("fixed",  "Fixed",  "Single or row prop at a fixed position"),
            ("random", "Random", "Randomly distributed props in an area"),
        ],
        default="fixed",
    )
    bpy.types.Scene.pc_prop_name = bpy.props.EnumProperty(
        name="Prop",
        description="Select prop type",
        items=PROP_NAME_ITEMS,
    )
    bpy.types.Scene.pc_offset_x = bpy.props.FloatProperty(name="X", default=0.0)
    bpy.types.Scene.pc_offset_y = bpy.props.FloatProperty(name="Y", default=0.0, description="Height")
    bpy.types.Scene.pc_offset_z = bpy.props.FloatProperty(name="Z", default=0.0)
    bpy.types.Scene.pc_has_end = bpy.props.BoolProperty(
        name="Has End", description="Enable to make this a row of props", default=False,
    )
    bpy.types.Scene.pc_end_x = bpy.props.FloatProperty(name="X", default=0.0)
    bpy.types.Scene.pc_end_y = bpy.props.FloatProperty(name="Y", default=0.0, description="Height")
    bpy.types.Scene.pc_end_z = bpy.props.FloatProperty(name="Z", default=0.0)
    bpy.types.Scene.pc_angle = bpy.props.FloatProperty(
        name="Angle", default=0.01, description="Facing angle in degrees (0.01=North)",
    )
    bpy.types.Scene.pc_area_x1 = bpy.props.FloatProperty(name="X", default=0.0)
    bpy.types.Scene.pc_area_y1 = bpy.props.FloatProperty(name="Y", default=0.0)
    bpy.types.Scene.pc_area_z1 = bpy.props.FloatProperty(name="Z", default=0.0)
    bpy.types.Scene.pc_area_x2 = bpy.props.FloatProperty(name="X", default=100.0)
    bpy.types.Scene.pc_area_y2 = bpy.props.FloatProperty(name="Y", default=0.0)
    bpy.types.Scene.pc_area_z2 = bpy.props.FloatProperty(name="Z", default=100.0)
    bpy.types.Scene.pc_seed = bpy.props.IntProperty(
        name="Seed", default=0, min=0, description="Random seed for placement",
    )
    bpy.types.Scene.pc_rand_count = bpy.props.IntProperty(
        name="Count", default=1, min=1, description="Number of props to place",
    )

    # ── Street Editor scene properties ────────────────────────────────────────
    bpy.types.Scene.st_sl_pos_expanded = bpy.props.BoolProperty(
        name="Stop Light Position",
        description="Expand stop light position fields",
        default=False,
    )
    bpy.types.Scene.st_show_arrows = bpy.props.BoolProperty(
        name="Show Direction Arrows",
        description="Show travel-direction chevrons on all streets in the 3D viewport",
        default=True,
    )
    bpy.types.Scene.st_vertex_index = bpy.props.IntProperty(
        name="Active Vertex",
        description="Index of the active vertex for insert / delete / move operations",
        default=0,
        min=0,
        update=_clamp_st_vertex_index,
    )
    bpy.types.Scene.st_extend_length = bpy.props.FloatProperty(
        name="Extend Length",
        description="Distance to extend when using directional extend",
        default=10.0, min=0.1, soft_max=200.0,
    )
    bpy.types.Scene.st_extend_angle = bpy.props.FloatProperty(
        name="Angle Offset",
        description="Horizontal rotation applied to the extension direction (degrees). 0 = same angle.",
        default=0.0, soft_min=-180.0, soft_max=180.0,
    )
    bpy.types.Scene.st_extend_elevation = bpy.props.FloatProperty(
        name="Elevation",
        description="Vertical tilt of the extension (degrees). + = uphill, - = downhill, 0 = flat. Ignored when Snap to Terrain is on.",
        default=0.0, soft_min=-89.0, soft_max=89.0,
    )
    bpy.types.Scene.st_snap_to_terrain = bpy.props.BoolProperty(
        name="Snap to Terrain",
        description="After placing a new vertex, raycast downward and snap its Z to the mesh surface below. Overrides the Elevation setting.",
        default=False,
    )
    # ── Street Presets scene properties ───────────────────────────────────────
    bpy.types.Scene.st_street_preset = bpy.props.EnumProperty(
        name="Street Preset",
        description="AI street preset to spawn",
        items=ST_PRESET_ITEMS,
        default="CUSTOM",
    )
    bpy.types.Scene.st_preset_length = bpy.props.FloatProperty(
        name="Preset Length",
        description="Total length of the road or arm",
        default=80.0, min=5.0, soft_max=500.0,
    )
    bpy.types.Scene.st_preset_lane_width = bpy.props.FloatProperty(
        name="Lane Width",
        description="Width used by fixed topology presets (T/X junctions)",
        default=5.0, min=1.0, soft_max=20.0,
    )
    bpy.types.Scene.st_preset_turn_radius = bpy.props.FloatProperty(
        name="Turn Radius",
        description="Arc radius for curved presets (0 = straight)",
        default=0.0, min=0.0, soft_max=200.0,
    )
    bpy.types.Scene.st_preset_curve_points = bpy.props.IntProperty(
        name="Vertex Count",
        description="Vertices on a curve when Split Length = 0",
        default=7, min=3, max=32,
    )
    bpy.types.Scene.st_preset_length_split = bpy.props.FloatProperty(
        name="Split Length",
        description="Vertex spacing along the road (0 = use Vertex Count for curves)",
        default=10.0, min=0.0, soft_max=50.0,
    )
    bpy.types.Scene.st_preset_lanes = bpy.props.IntProperty(
        name="Lanes",
        description="Number of parallel lane streets to generate",
        default=3, min=1, max=8,
    )
    bpy.types.Scene.st_preset_lane_separator = bpy.props.FloatProperty(
        name="Lane Separator",
        description="Center-to-center distance between parallel lanes",
        default=5.0, min=0.5, soft_max=30.0,
    )
    bpy.types.Scene.st_preset_grouped = bpy.props.BoolProperty(
        name="Grouped Street",
        description="Export all lanes as one multi-lane street dict (lanes format) instead of separate streets",
        default=True,
    )
    bpy.types.Scene.st_preset_converge_start = bpy.props.BoolProperty(
        name="Converge Start",
        description="Pin all lane start-points to the centre lane's start point",
        default=False,
    )
    bpy.types.Scene.st_preset_converge_end = bpy.props.BoolProperty(
        name="Converge End",
        description="Pin all lane end-points to the centre lane's end point",
        default=False,
    )
    import re as _re

    def _natural_key(name):
        return [int(p) if p.isdigit() else p.lower()
                for p in _re.split(r'(\d+)', name)]

    def _poly_search(self, context, edit_text):
        names = [o.name for o in bpy.data.objects
                 if o.type == 'MESH' and o.name.startswith("P")]
        names.sort(key=_natural_key)
        lo = edit_text.lower()
        return [n for n in names if lo in n.lower()]

    bpy.types.Scene.st_poly_from = bpy.props.StringProperty(
        name="Start Polygon",
        description="Intersection polygon where the street begins (V0 = face centre)",
        default="",
        search=_poly_search,
    )
    bpy.types.Scene.st_poly_to = bpy.props.StringProperty(
        name="End Polygon",
        description="Intersection polygon where the street ends (last vertex = face centre)",
        default="",
        search=_poly_search,
    )
    bpy.types.Scene.st_poly_info_expanded = bpy.props.BoolProperty(
        name="Show Info",
        description="Show explanation for the From Polygons feature",
        default=False,
    )
    bpy.types.Scene.st_preset_direction = bpy.props.FloatProperty(
        name="Direction",
        description="Spawn direction in degrees: 0=North (+Y), 90=East (+X), -90=West, 180=South",
        default=0.0,
        soft_min=-180.0,
        soft_max=180.0,
        step=100,
    )

    # ── Road Builder scene properties ─────────────────────────────────────────
    bpy.types.Scene.rd_extend_length = bpy.props.FloatProperty(
        name="Length", default=10.0, min=0.1, soft_max=200.0,
        description="Distance to extend the road spine per step",
    )
    bpy.types.Scene.rd_extend_angle = bpy.props.FloatProperty(
        name="Turn Angle",
        description="Horizontal turn angle in degrees (0=straight, +90=right, -90=left)",
        default=0.0, soft_min=-180.0, soft_max=180.0, step=100,
    )
    bpy.types.Scene.rd_extend_elevation = bpy.props.FloatProperty(
        name="Slope",
        description="Vertical slope angle in degrees (+up, -down). Disabled when Snap to Terrain is on.",
        default=0.0, soft_min=-89.0, soft_max=89.0, step=50,
    )
    bpy.types.Scene.rd_snap_to_terrain = bpy.props.BoolProperty(
        name="Snap to Terrain",
        description="Raycast spine endpoint(s) down onto scene geometry",
        default=False,
    )
    bpy.types.Scene.rd_road_type = bpy.props.EnumProperty(
        name="Road Type",
        description="Quick preset for cross-section dimensions",
        items=ROAD_TYPE_ITEMS,
        default="ROAD_2L",
    )

    # ── Car Editor scene properties ───────────────────────────────────────────
    bpy.types.Scene.ce_car_folder = bpy.props.StringProperty(
        name="Car Folder",
        description="Path to the vehicle BMS folder (e.g. CAR_FILES_TEST/VPFORD)",
        default="",
        subtype="DIR_PATH",
    )
    bpy.types.Scene.ce_texture_folder = bpy.props.StringProperty(
        name="Texture Folder",
        description="Folder containing .DDS textures for the car",
        default="",
        subtype="DIR_PATH",
    )
    bpy.types.Scene.ce_load_lights = bpy.props.BoolProperty(
        name="Load Lights",
        description="Also load headlight / taillight BMS files when loading a car",
        default=False,
    )
    bpy.types.Scene.ce_auto_reload = bpy.props.BoolProperty(
        name="Auto-Reload After Export",
        description="Automatically reimport the exported BMS files after exporting",
        default=False,
    )
    bpy.types.Scene.ce_assign_slot = bpy.props.IntProperty(
        name="Texture Slot",
        description="Material slot index to assign to selected faces",
        default=0,
        min=0,
    )
    bpy.types.Scene.ce_face_tile_x = bpy.props.FloatProperty(
        name="Tile X", default=1.0, min=0.001, soft_max=32.0,
        description="UV tiling scale on X axis for selected faces",
        update=update_ce_face_uv,
    )
    bpy.types.Scene.ce_face_tile_y = bpy.props.FloatProperty(
        name="Tile Y", default=1.0, min=0.001, soft_max=32.0,
        description="UV tiling scale on Y axis for selected faces",
        update=update_ce_face_uv,
    )
    bpy.types.Scene.ce_face_rotation = bpy.props.FloatProperty(
        name="Rotation", default=0.0, soft_min=-360.0, soft_max=360.0,
        description="UV rotation in degrees for selected faces",
        update=update_ce_face_uv,
    )
    bpy.types.Scene.ce_add_shape = bpy.props.EnumProperty(
        name="Shape",
        items=[("QUAD", "Quad", ""), ("TRI", "Triangle", "")],
        default="QUAD",
    )
    bpy.types.Scene.ce_add_size = bpy.props.FloatProperty(
        name="Size", default=0.3, min=0.001, soft_max=10.0,
        description="Side length of the new face",
    )
    bpy.types.Scene.ce_active_face_index = bpy.props.IntProperty(
        name="Active Face Index", default=0, min=0,
    )
    bpy.types.Scene.ce_uv_updating = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.ce_add_to_city = bpy.props.BoolProperty(
        name="Add to City",
        description="Also write exported BMS files to SHOP/BMS/<car_name>/ for in-game use",
        default=True,
    )
    bpy.types.Scene.ce_start_game = bpy.props.BoolProperty(
        name="Launch Game After Export",
        description="Start Open1560.exe after a successful export (only if game is not already running)",
        default=False,
    )
    bpy.types.Scene.ce_last_export_dir = bpy.props.StringProperty(
        name="Last Export Dir",
        description="Path of the most recent timestamped export folder (used by Reload)",
        default="",
    )
    bpy.types.Scene.ce_face_texture = bpy.props.EnumProperty(
        name="Texture",
        description="Texture to assign to selected faces on the active car part",
        items=TEXTURE_ENUM_ITEMS,
        update=update_ce_face_texture,
    )
    bpy.types.Scene.ce_new_tex_name = bpy.props.StringProperty(
        name="Texture Name",
        description="DDS texture name (without extension) to add as a new material slot",
        default="",
    )
    bpy.types.Scene.ce_show_damage = bpy.props.BoolProperty(
        name="Damage View",
        description="Currently showing damage (_DMG) texture variants",
        default=False,
    )
    bpy.types.Scene.ce_paint_variant = bpy.props.StringProperty(
        name="Paint Variant",
        description="Current paint variant prefix (e.g. VPBULLET, VPBULLETBLUE)",
        default="",
    )

    # ── Facade Editor — edit form ─────────────────────────────────────────────
    bpy.types.Scene.fe_active_group_id = bpy.props.StringProperty(
        name="Active Facade Group", default="",
    )
    bpy.types.Scene.fe_facade_name = bpy.props.EnumProperty(
        name="Facade",
        description="Facade mesh name",
        items=FACADE_NAME_ITEMS,
        update=_update_facade_form,
    )
    bpy.types.Scene.fe_flags = bpy.props.EnumProperty(
        name="Flags",
        description="FCD rendering flags",
        items=FACADE_FLAGS_ITEMS,
        update=_update_facade_form,
    )
    _fkw = dict(precision=2, update=_update_facade_form)
    bpy.types.Scene.fe_offset_x = bpy.props.FloatProperty(name="Offset X", **_fkw)
    bpy.types.Scene.fe_offset_y = bpy.props.FloatProperty(name="Offset Y", **_fkw)
    bpy.types.Scene.fe_offset_z = bpy.props.FloatProperty(name="Offset Z", **_fkw)
    bpy.types.Scene.fe_end_x    = bpy.props.FloatProperty(name="End X",    **_fkw)
    bpy.types.Scene.fe_end_y    = bpy.props.FloatProperty(name="End Y",    **_fkw)
    bpy.types.Scene.fe_end_z    = bpy.props.FloatProperty(name="End Z",    **_fkw)
    bpy.types.Scene.fe_axis = bpy.props.EnumProperty(
        name="Axis",
        items=[("x", "X", ""), ("y", "Y", ""), ("z", "Z", "")],
        default="x",
        update=_update_facade_form,
    )
    bpy.types.Scene.fe_separator = bpy.props.FloatProperty(
        name="Separator", default=10.0, min=0.01, precision=3, update=_update_facade_form,
    )
    bpy.types.Scene.fe_sides_x = bpy.props.FloatProperty(name="Sides L", default=0.0, precision=2, update=_update_facade_form)
    bpy.types.Scene.fe_sides_y = bpy.props.FloatProperty(name="Sides R", default=0.0, precision=2, update=_update_facade_form)
    bpy.types.Scene.fe_sides_z = bpy.props.FloatProperty(name="Sides D", default=0.0, precision=2, update=_update_facade_form)
    bpy.types.Scene.fe_scale_auto = bpy.props.BoolProperty(
        name="Auto Scale", default=True, update=_update_facade_form,
    )
    bpy.types.Scene.fe_scale = bpy.props.FloatProperty(
        name="Scale", default=1.0, min=0.001, precision=3, update=_update_facade_form,
    )

    # ── Facade Editor — create form ───────────────────────────────────────────
    bpy.types.Scene.fc_facade_name = bpy.props.EnumProperty(
        name="Facade", items=FACADE_NAME_ITEMS,
    )
    bpy.types.Scene.fc_flags = bpy.props.EnumProperty(
        name="Flags", items=FACADE_FLAGS_ITEMS,
    )
    bpy.types.Scene.fc_offset_x = bpy.props.FloatProperty(name="Offset X", precision=2)
    bpy.types.Scene.fc_offset_y = bpy.props.FloatProperty(name="Offset Y", precision=2)
    bpy.types.Scene.fc_offset_z = bpy.props.FloatProperty(name="Offset Z", precision=2)
    bpy.types.Scene.fc_end_x    = bpy.props.FloatProperty(name="End X",    precision=2)
    bpy.types.Scene.fc_end_y    = bpy.props.FloatProperty(name="End Y",    precision=2)
    bpy.types.Scene.fc_end_z    = bpy.props.FloatProperty(name="End Z",    precision=2)
    bpy.types.Scene.fc_axis = bpy.props.EnumProperty(
        name="Axis",
        items=[("x", "X", ""), ("y", "Y", ""), ("z", "Z", "")],
        default="x",
    )
    bpy.types.Scene.fc_separator = bpy.props.FloatProperty(
        name="Separator", default=10.0, min=0.01, precision=3,
    )
    bpy.types.Scene.fc_sides_x   = bpy.props.FloatProperty(name="Sides L", default=0.0, precision=2)
    bpy.types.Scene.fc_sides_y   = bpy.props.FloatProperty(name="Sides R", default=0.0, precision=2)
    bpy.types.Scene.fc_sides_z   = bpy.props.FloatProperty(name="Sides D", default=0.0, precision=2)
    bpy.types.Scene.fc_scale_auto = bpy.props.BoolProperty(name="Auto Scale", default=True)
    bpy.types.Scene.fc_scale      = bpy.props.FloatProperty(
        name="Scale", default=1.0, min=0.001, precision=3,
    )


def _safe_register(cls) -> None:
    try:
        bpy.utils.register_class(cls)
    except ValueError:
        bpy.utils.unregister_class(cls)
        bpy.utils.register_class(cls)


def _safe_unregister(cls) -> None:
    try:
        bpy.utils.unregister_class(cls)
    except RuntimeError:
        pass


def _clamp_st_vertex_index(self, context):
    from src.integrations.blender.operators.ai_streets import get_street_vertex_count
    obj = context.active_object
    if obj and obj.type == 'CURVE':
        n = get_street_vertex_count(obj)
        if n > 0 and self.st_vertex_index > n - 1:
            self.st_vertex_index = n - 1


def _prefill_car_editor_paths() -> None:
    """Set Car Editor defaults on first load."""
    from src.constants.folder import Folder
    scene = bpy.context.scene
    scene.ce_texture_folder = str(Folder.Resources.Editor.Textures)
    if not scene.ce_car_folder:
        scene.ce_car_folder = str(Folder.Resources.Editor.BMS)


def initialize_blender_panels() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    register_object_properties()
    register_street_properties()
    register_road_builder_properties()
    register_scene_properties()
    _prefill_car_editor_paths()

    # Rename the default master collection from "Collection" to "Polygons"
    scene_col = bpy.context.scene.collection
    if scene_col.name == "Collection":
        scene_col.name = "Polygons"

    _safe_register(VertexGroup)
    bpy.types.Object.vertex_coords = bpy.props.CollectionProperty(type=VertexGroup)

    for cls in PANEL_CLASSES:
        _safe_register(cls)


def initialize_blender_operators() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    for cls in OPERATOR_CLASSES:
        _safe_register(cls)


def initialize_blender_waypoint_editor() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    for cls in WAYPOINT_CLASSES:
        _safe_register(cls)

    register_draw_handler()


def unregister_all() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    unregister_draw_handler()

    for cls in reversed(ALL_CLASSES):
        _safe_unregister(cls)

    for prop in OBJECT_PROPERTIES:
        if hasattr(bpy.types.Object, prop):
            try:
                delattr(bpy.types.Object, prop)
            except AttributeError:
                pass

    for prop in SCENE_PROPERTIES:
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
            except AttributeError:
                pass
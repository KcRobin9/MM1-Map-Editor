import re
import bpy

from src.constants.misc import Executable
from src.constants.props import BangerFlags
from src.helpers.main import is_process_running
from src.integrations.blender.modeling.uv_mapping import OBJECT_OT_UpdateUVMapping

from src.integrations.blender.operators.custom_properties import OBJECT_OT_AssignCustomProperties
from src.integrations.blender.operators.face_side import OBJECT_OT_ToggleGameSidePreview
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
from src.integrations.blender.panels.vertex import VIEW3D_PT_MapEditorVertices, VertexGroup
from src.integrations.blender.panels.uv import OBJECT_PT_UVMappingPanel
from src.integrations.blender.panels.sidebar import SIDEBAR_CLASSES
from src.integrations.blender.panels.ai_streets_sidebar import STREET_EDITOR_CLASSES
from src.integrations.blender.panels.waypoint_sidebar import WAYPOINT_EDITOR_CLASSES
from src.integrations.blender.panels.prop_sidebar import PROP_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.props import PROP_EDITOR_CLASSES, PROP_NAME_ITEMS, PROP_NAME_ITEMS_FROM, PROP_NAME_ITEMS_TO, BANGER_FLAG_ITEMS, CUSTOM_CITY_ITEMS, prop_name_enum_items, _update_prop_form
from src.integrations.blender.panels.car_editor_sidebar import CAR_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.car_editor import (
    CAR_EDITOR_CLASSES, update_ce_face_texture, update_ce_face_uv, _CAR_LIGHT_TAGS,
)
from src.constants.car_assets import LightColor
from src.integrations.blender.waypoints.draw import register_draw_handler, unregister_draw_handler
from src.integrations.blender.handlers import _vertex_poll_timer
from src.integrations.blender.auto_save import shutdown_auto_save
from src.integrations.blender.modeling.uv_mapping import TEXTURE_ENUM_ITEMS, update_texture_name, update_uv_tiling, update_texture_category, OBJECT_OT_RefreshCurrentTextures
from src.integrations.blender.modeling.texture_catalog import CATEGORY_ITEMS
from src.integrations.blender.operators.road_builder import ROAD_BUILDER_CLASSES, ROAD_TYPE_ITEMS
from src.integrations.blender.operators.mm2_cells import MM2_CELLS_CLASSES
from src.integrations.blender.operators.road_automation import ROAD_AUTOMATION_CLASSES, RD_PROP_ITEMS, RD_PROP_FLAG_ITEMS, RD_AI_INTERSECTION_ITEMS, RD_FACADE_ITEMS, RD_JUNCTION_PRESET_ITEMS
from src.integrations.blender.panels.road_builder_sidebar import ROAD_BUILDER_PANEL_CLASSES
from src.integrations.blender.operators.facades import FACADE_EDITOR_CLASSES, FACADE_NAME_ITEMS, FACADE_FLAGS_ITEMS, _update_facade_form
from src.integrations.blender.panels.facade_editor_sidebar import FACADE_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.bridges import BRIDGE_EDITOR_CLASSES, BRIDGE_NAME_ITEMS, _update_bridge_form
from src.integrations.blender.panels.bridge_sidebar import BRIDGE_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.city_loader import CITY_LOADER_CLASSES
from src.integrations.blender.operators.city_polygon_import import CITY_POLYGON_IMPORT_CLASSES
from src.integrations.blender.operators.validate_textures import VALIDATE_TEXTURES_CLASSES
from src.integrations.blender.panels.city_loader_sidebar import CITY_LOADER_PANEL_CLASSES
from src.integrations.blender.operators.skeleton_editor import SKELETON_EDITOR_CLASSES, CHAR_ITEMS, _anim_items
from src.integrations.blender.panels.skeleton_editor_sidebar import SKELETON_EDITOR_PANEL_CLASSES
from src.integrations.blender.operators.dash_editor import DASH_EDITOR_CLASSES, get_dash_car_items, get_dash_texture_items, update_de_preview, update_de_gauge, update_de_reskin_texture
from src.integrations.blender.panels.dash_editor_sidebar import DASH_EDITOR_PANEL_CLASSES


PANEL_CLASSES = [
    OBJECT_PT_CellTypePanel,
    OBJECT_PT_MaterialTypePanel,
    OBJECT_PT_PolygonMiscOptionsPanel,
    OBJECT_PT_HUDColorPanel,
    OBJECT_PT_UVMappingPanel,
    *SIDEBAR_CLASSES,
    VIEW3D_PT_MapEditorVertices,
    *STREET_EDITOR_CLASSES,
    *WAYPOINT_EDITOR_CLASSES,
    *PROP_EDITOR_PANEL_CLASSES,
    *CAR_EDITOR_PANEL_CLASSES,
    *ROAD_BUILDER_PANEL_CLASSES,
    *FACADE_EDITOR_PANEL_CLASSES,
    *BRIDGE_EDITOR_PANEL_CLASSES,
    *CITY_LOADER_PANEL_CLASSES,
    *SKELETON_EDITOR_PANEL_CLASSES,
    *DASH_EDITOR_PANEL_CLASSES,
]

OPERATOR_CLASSES = [
    OBJECT_OT_ToggleGameSidePreview,
    OBJECT_OT_UpdateUVMapping,
    OBJECT_OT_RefreshCurrentTextures,
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
    *ROAD_AUTOMATION_CLASSES,
    *FACADE_EDITOR_CLASSES,
    *BRIDGE_EDITOR_CLASSES,
    *CITY_LOADER_CLASSES,
    *CITY_POLYGON_IMPORT_CLASSES,
    *SKELETON_EDITOR_CLASSES,
    *DASH_EDITOR_CLASSES,
    *VALIDATE_TEXTURES_CLASSES,
    *MM2_CELLS_CLASSES,
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
    "rs_road_enabled", "rs_curb_enabled", "rs_sidewalk_enabled",
    "rs_wall_enabled", "rs_median_enabled",
    "rs_road_angle",
    "rs_curb_tile_x", "rs_curb_tile_y", "rs_curb_angle",
    "rs_sidewalk_tile_x", "rs_sidewalk_tile_y", "rs_sidewalk_angle",
    "rs_wall_height", "rs_median_width",
    "rs_road_texture", "rs_curb_texture", "rs_sidewalk_texture",
    "rs_wall_texture", "rs_median_texture",
    "rs_wall_tile_x", "rs_wall_tile_y", "rs_wall_angle",
    "rs_wall_side", "rs_sidewalk_side",
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
    "texture_category",
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
    "pe_custom_city",
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
    "pe_flags",
    # Replace Prop Type tool
    "pr_from_name",
    "pr_to_name",
    "pr_replace_user_props",
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
    "pc_flags",
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
    "ce_show_parts",
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
    "ce_add_trailer",
    "ce_add_siren",
    "ce_export_paint_variants",
    "ce_last_export_dir",
    "ce_show_damage",
    "ce_paint_variant",
    "ce_template",
    "ce_template_wheel_count",
    "ce_car_display_name",
    "ce_import_decimate_ratio",
    "ce_import_wheel_count",
    "ce_wheel_texture",
    "ce_wheel_style",
    "ce_wheel_size",
    "ce_all_wheel_radius",
    "ce_wheel_radius_syncing",
    *[f"ce_wheel_texture_{i}" for i in range(10)],
    *[f"ce_wheel_radius_{i}" for i in range(10)],
    *[f"ce_trailer_wheel_texture_{i}" for i in range(4)],
    "ce_mirror_x",
    "ce_phys_override",
    "ce_phys_mass",
    "ce_phys_horsepower",
    "ce_phys_drag",
    "ce_phys_downforce",
    "ce_phys_grip",
    "ce_phys_drift",
    "ce_phys_suspension",
    "ce_phys_cg_x",
    "ce_phys_cg_height",
    "ce_phys_cg_z",
    "ce_light_beam",
    "ce_hide_light_glows",
    "ce_light_syncing",
    "ce_siren_color_red",
    "ce_siren_color_blue",
    "ce_info_description",
    "ce_info_colors",
    "ce_info_horsepower",
    "ce_info_topspeed",
    "ce_info_durability",
    "ce_info_mass",
    "ce_audio_profile",
    *[f"ce_light_color_{i}" for i in range(6)],
    # Dash Editor
    "de_dash_car",
    "de_new_car",
    "de_updating",
    "de_preview",
    "de_speed_rot_min",
    "de_speed_rot_max",
    "de_rpm_rot_min",
    "de_rpm_rot_max",
    "de_damage_rot_min",
    "de_damage_rot_max",
    "de_max_speed",
    "de_max_rpm",
    "de_min_speed",
    "de_wheel_fact",
    "de_cam_fov",
    "de_cam_offset",
    "de_cam_pitch",
    "de_cam_near",
    "de_cam_far",
    "de_swap_car",
    "de_reskin_texture",
    "de_reskin_image",
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
    "rd_ai_two_way",
    "rd_ai_intersection_start", "rd_ai_intersection_end",
    "rd_ai_alley", "rd_ai_traffic_blocked", "rd_ai_ped_blocked",
    "rd_prop_name", "rd_prop_interval", "rd_prop_side", "rd_prop_offset",
    "rd_prop_flags", "rd_prop_angle_offset", "rd_prop_height_offset", "rd_prop_stagger",
    "rd_facade_name", "rd_facade_width", "rd_facade_side", "rd_facade_offset",
    "rd_facade_height_offset", "rd_facade_flip", "rd_facade_bright",
    "rd_build_bake", "rd_build_ai", "rd_build_props", "rd_build_facades", "rd_build_junctions",
    "rd_snap_threshold",
    "rd_junction_size", "rd_junction_type", "rd_junction_lights", "rd_junction_crosswalk",
    "rd_junction_preset", "rd_junction_arm_length", "rd_junction_arms", "rd_junction_rotation",
    "rd_fill_width", "rd_fill_length", "rd_fill_rotation",
    "rd_verge_width", "rd_verge_offset", "rd_verge_side", "rd_verge_height",
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
    # City Loader
    "cl_city_folder",
    "cl_load_fcd",
    "cl_load_bng",
    "cl_load_meshes",
    "cl_load_bai",
    "cl_load_gizmo",
    "cl_texture_folder",
    # Bridge Editor — edit form
    "be_active_obj_name",
    "be_active_group_id",
    "be_active_role",
    "be_prop_name",
    "be_offset_x", "be_offset_y", "be_offset_z",
    "be_angle",
    # Bridge Editor — create form
    "bc_offset_x", "bc_offset_y", "bc_offset_z",
    "bc_angle",
    "bc_span",
    "bc_gate_offset",
    "bc_facing_in",
    "bc_drawbridge_name",
    "bc_crossgate_name",
    # Skeleton Editor
    "ske_char_name",
    "ske_anim_name",
    "ske_new_anim_name",
    "ske_new_anim_frames",
    "ske_gen_style",
    "ske_walk_speed",
    "ske_ar_name",
    "ske_var_variant",
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
    "fr_replace_user_facades",
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
        name="Lane Width", default=5.0, min=1.0, soft_max=20.0,
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
        name="Road Tile X", default=1.0, min=0.1, soft_max=10.0,
    )
    bpy.types.Object.rs_road_tile_y = bpy.props.FloatProperty(
        name="Road Tile Y", default=1.0, min=0.1, soft_max=20.0,
    )

    # ── Component toggles ─────────────────────────────────────────────────────
    bpy.types.Object.rs_road_enabled = bpy.props.BoolProperty(
        name="Road",     default=True,
        description="Generate the central road surface zone(s)",
    )
    bpy.types.Object.rs_curb_enabled = bpy.props.BoolProperty(
        name="Curb",     default=True,
        description="Generate raised curb strips between road and sidewalk",
    )
    bpy.types.Object.rs_sidewalk_enabled = bpy.props.BoolProperty(
        name="Sidewalk", default=True,
        description="Generate sidewalks along both edges of the cross-section",
    )
    bpy.types.Object.rs_wall_enabled = bpy.props.BoolProperty(
        name="Wall",     default=False,
        description="Generate outer wall/barrier strips beyond the sidewalk",
    )
    bpy.types.Object.rs_median_enabled = bpy.props.BoolProperty(
        name="Median",   default=False,
        description="Split the road around a central raised median strip",
    )

    # ── Per-zone angle / tiling ───────────────────────────────────────────────
    bpy.types.Object.rs_road_angle = bpy.props.FloatProperty(
        name="Road Angle",
        description="Texture rotation for the road (degrees). 90 = texture U runs across the road",
        default=90.0, soft_min=-180.0, soft_max=180.0, step=100,
    )
    bpy.types.Object.rs_curb_tile_x = bpy.props.FloatProperty(
        name="Curb Tile X", default=1.0, min=0.1, soft_max=10.0,
    )
    bpy.types.Object.rs_curb_tile_y = bpy.props.FloatProperty(
        name="Curb Tile Y", default=5.0, min=0.1, soft_max=20.0,
    )
    bpy.types.Object.rs_curb_angle = bpy.props.FloatProperty(
        name="Curb Angle", default=0.0, soft_min=-180.0, soft_max=180.0, step=100,
    )
    bpy.types.Object.rs_sidewalk_tile_x = bpy.props.FloatProperty(
        name="Sidewalk Tile X", default=1.0, min=0.1, soft_max=20.0,
    )
    bpy.types.Object.rs_sidewalk_tile_y = bpy.props.FloatProperty(
        name="Sidewalk Tile Y", default=5.0, min=0.1, soft_max=10.0,
    )
    bpy.types.Object.rs_sidewalk_angle = bpy.props.FloatProperty(
        name="Sidewalk Angle", default=90.0, soft_min=-180.0, soft_max=180.0, step=100,
    )

    # ── Wall + Median dimensions ──────────────────────────────────────────────
    bpy.types.Object.rs_wall_height = bpy.props.FloatProperty(
        name="Wall Height", default=10.0, min=0.0, soft_max=30.0,
    )
    bpy.types.Object.rs_wall_tile_x = bpy.props.FloatProperty(
        name="Wall Tile X", default=1.0, min=0.1, soft_max=10.0,
    )
    bpy.types.Object.rs_wall_tile_y = bpy.props.FloatProperty(
        name="Wall Tile Y", default=1.0, min=0.1, soft_max=20.0,
    )
    bpy.types.Object.rs_wall_angle = bpy.props.FloatProperty(
        name="Wall Angle", default=0.0, soft_min=-180.0, soft_max=180.0, step=100,
    )
    _SIDE_ITEMS = [("BOTH", "Both", ""), ("LEFT", "Left only", ""), ("RIGHT", "Right only", "")]
    bpy.types.Object.rs_wall_side = bpy.props.EnumProperty(
        name="Wall Side", items=_SIDE_ITEMS, default="BOTH",
        description="Which side(s) to place the wall on",
    )
    bpy.types.Object.rs_sidewalk_side = bpy.props.EnumProperty(
        name="Sidewalk Side", items=_SIDE_ITEMS, default="BOTH",
        description="Which side(s) to place the sidewalk (and curb) on",
    )
    bpy.types.Object.rs_median_width = bpy.props.FloatProperty(
        name="Median Width", default=1.0, min=0.0, soft_max=10.0,
        description="Width of the central median strip (taken out of the road)",
    )


    # ── Texture dropdowns ─────────────────────────────────────────────────────
    from src.constants.textures import Texture as _Tex
    _TEX_LABEL_OVERRIDES = {
        "ROAD_1_LANE": "R2",
        "ROAD_2_LANE": "R4",
        "ROAD_3_LANE": "R6",
    }
    _tex_items = []
    for _attr in dir(_Tex):
        if _attr.startswith("_"):
            continue
        _val = getattr(_Tex, _attr)
        if not isinstance(_val, str):
            continue
        _label = _TEX_LABEL_OVERRIDES.get(_attr, _attr.replace("_", " ").title())
        _tex_items.append((_val, _label, _val))
    _tex_items.sort(key=lambda x: x[1])
    _road_tex_items = [("AUTO", "Auto (by lanes)", "R2/R4/R6 picked by lane count")] + _tex_items

    bpy.types.Object.rs_road_texture = bpy.props.EnumProperty(
        name="Road Texture",     items=_road_tex_items, default="AUTO",
    )
    bpy.types.Object.rs_curb_texture = bpy.props.EnumProperty(
        name="Curb Texture",     items=_tex_items, default=_Tex.SIDEWALK,
    )
    bpy.types.Object.rs_sidewalk_texture = bpy.props.EnumProperty(
        name="Sidewalk Texture", items=_tex_items, default=_Tex.SIDEWALK,
    )
    bpy.types.Object.rs_wall_texture = bpy.props.EnumProperty(
        name="Wall Texture",     items=_tex_items, default=_Tex.WALL,
    )
    bpy.types.Object.rs_median_texture = bpy.props.EnumProperty(
        name="Median Texture",   items=_tex_items, default=_Tex.GRASS,
    )


def _get_wheel_texture_items(self, context):
    from src.constants.folder import Folder
    from src.constants.car_assets import WheelTexture
    return WheelTexture.blender_items(Folder.Resources.Editor.Textures)


def _get_audio_profile_items(self, context):
    """Source cars with a .MMPLAYERCARAUDIO (engine + horn sounds) — the chosen one
    is copied to the custom car so it sounds like that vehicle."""
    from src.constants.folder import Folder
    from src.constants.car_assets import Vehicle

    seen = {}
    for d in (Folder.BASE / "development" / "core" / "TUNE",
              Folder.Resources.Editor.Tune.CarSimulation.parent):
        try:
            for f in d.iterdir():
                if f.suffix.upper() == ".MMPLAYERCARAUDIO":
                    seen.setdefault(f.stem.upper(), f.stem)
        except OSError:
            pass

    stems = sorted(seen.values(), key=lambda s: (Vehicle.ORDER.get(s.upper(), 10_000), s.upper()))
    items = [(s, Vehicle.label(s), f"Use {Vehicle.label(s)} engine + horn sounds") for s in stems]
    return items or [("VPMUSTANG99", "Ford Mustang", "")]


_WHEEL_STYLE_CACHE = []


def _get_wheel_style_items(self, context):
    """Source cars (in resources/editor/MESHES/CARS) that have a WHL0_H.BMS,
    with friendly names and player cars (sensible default) listed first."""
    from src.constants.folder import Folder
    from src.constants.car_assets import Vehicle
    if _WHEEL_STYLE_CACHE:
        return _WHEEL_STYLE_CACHE
    cars_dir = Folder.Resources.Editor.Meshes / "CARS"
    found = []
    if cars_dir.is_dir():
        for d in cars_dir.iterdir():
            if d.is_dir() and (d / "WHL0_H.BMS").is_file():
                found.append(d.name)
    # Catalogue order first (player cars), then any extras alphabetically.
    found.sort(key=lambda n: (Vehicle.ORDER.get(n.upper(), 10_000), n.upper()))
    items = [(n, Vehicle.label(n), f"Use {Vehicle.label(n)} wheels") for n in found]
    if not items:
        items = [("VPMUSTANG99", "Ford Mustang", "Default wheels")]
    _WHEEL_STYLE_CACHE[:] = items
    return _WHEEL_STYLE_CACHE


def _update_wheel_texture(self, context):
    bpy.ops.car.apply_wheel_texture("EXEC_DEFAULT")


def _make_wheel_tex_update(idx):
    def _update(self, context):
        bpy.ops.car.apply_wheel_texture_single(
            "EXEC_DEFAULT", part_tag=f"wheel_{idx}", tex_name=getattr(self, f"ce_wheel_texture_{idx}")
        )
    return _update


def _make_wheel_radius_update(idx):
    def _update(self, context):
        if getattr(self, "ce_wheel_radius_syncing", False):
            return
        bpy.ops.car.set_wheel_radius(
            "EXEC_DEFAULT", part_tag=f"wheel_{idx}", radius=getattr(self, f"ce_wheel_radius_{idx}")
        )
    return _update


def _update_all_wheel_radius(self, context):
    if getattr(self, "ce_wheel_radius_syncing", False):
        return
    bpy.ops.car.set_all_wheel_radius("EXEC_DEFAULT", radius=self.ce_all_wheel_radius)


def _make_trailer_wheel_tex_update(idx):
    def _update(self, context):
        bpy.ops.car.apply_wheel_texture_single(
            "EXEC_DEFAULT", part_tag=f"trailer_wheel_{idx}",
            tex_name=getattr(self, f"ce_trailer_wheel_texture_{idx}")
        )
    return _update


# Single source of truth: colour catalogue from constants, light-slot order from
# the Car Editor (the part tags it loads, e.g. light_head … light_signalR).
_LIGHT_COLOR_ITEMS = LightColor.blender_items()
_LIGHT_PART_TAGS   = list(_CAR_LIGHT_TAGS)


def _make_light_color_update(idx):
    def _update(self, context):
        if getattr(self, "ce_light_syncing", False):
            return
        bpy.ops.car.set_light_color(
            "EXEC_DEFAULT", part_tag=_LIGHT_PART_TAGS[idx],
            color=getattr(self, f"ce_light_color_{idx}"),
        )
    return _update


def _update_light_beam(self, context):
    if getattr(self, "ce_light_syncing", False):
        return
    bpy.ops.car.set_beam_length("EXEC_DEFAULT", factor=self.ce_light_beam)


def _update_hide_light_glows(self, context):
    bpy.ops.car.toggle_light_glows("EXEC_DEFAULT")


def _make_siren_color_update(part_tag, prop_name):
    def _update(self, context):
        if getattr(self, "ce_light_syncing", False):
            return
        bpy.ops.car.set_light_color(
            "EXEC_DEFAULT", part_tag=part_tag, color=getattr(self, prop_name))
    return _update


def register_scene_properties() -> None:
    bpy.types.Scene.texture_category = bpy.props.EnumProperty(
        name="Texture List",
        description="Filter which textures appear in the Texture dropdown",
        items=CATEGORY_ITEMS,
        default="CURRENT",
        update=update_texture_category,
    )
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
    # Custom-city selector — adds that community map's props to the dropdowns
    bpy.types.Scene.pe_custom_city = bpy.props.EnumProperty(
        name="Custom City",
        description="Show custom props from a community map (e.g. Box Design Raceway) alongside stock props",
        items=CUSTOM_CITY_ITEMS,
        default="NONE",
    )
    # Prop name dropdown (stock + selected custom city's props)
    bpy.types.Scene.pe_prop_name = bpy.props.EnumProperty(
        name="Prop",
        description="Select prop type",
        items=prop_name_enum_items,
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
    # Banger collision/breakability flags
    bpy.types.Scene.pe_flags = bpy.props.EnumProperty(
        name="Flags",
        description="Collision behavior: Breakable shatters when hit; Drivable Solid is a solid surface you can drive on (won't break)",
        items=BANGER_FLAG_ITEMS,
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
    # Export → write directly to src/USER/props/props.py (backs up the old file)
    bpy.types.Scene.pr_replace_user_props = bpy.props.BoolProperty(
        name="Replace USER props.py",
        description="Write the export straight into src/USER/props/props.py, backing up the old file as props_backup_{timestamp}.py. When off, you pick a file path",
        default=False,
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
        items=prop_name_enum_items,
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
        name="Angle", default=0.01, description="Facing angle in degrees (must be non-zero; 0.01 ≈ North)",
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
    bpy.types.Scene.pc_flags = bpy.props.EnumProperty(
        name="Flags",
        description="Collision behavior: Breakable shatters when hit; Drivable Solid is a solid surface you can drive on (won't break)",
        items=BANGER_FLAG_ITEMS,
        default=str(BangerFlags.DEFAULT),
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
        default=False,
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
    def _natural_key(name):
        return [int(p) if p.isdigit() else p.lower()
                for p in re.split(r'(\d+)', name)]

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
        default="ROAD_TEST",
    )

    # ── Road Builder automation (AI streets + street props) ───────────────────
    bpy.types.Scene.rd_ai_two_way = bpy.props.BoolProperty(
        name="Two-Way",
        description="Generate opposing lanes (left of centre run the other direction). "
                    "Off = all lanes one-way",
        default=True,
    )
    _rd_yes_no = [("YES", "Yes", ""), ("NO", "No", "")]
    bpy.types.Scene.rd_ai_intersection_start = bpy.props.EnumProperty(
        name="Start", description="Intersection behaviour at the spine's start end",
        items=RD_AI_INTERSECTION_ITEMS,
    )
    bpy.types.Scene.rd_ai_intersection_end = bpy.props.EnumProperty(
        name="End", description="Intersection behaviour at the spine's end",
        items=RD_AI_INTERSECTION_ITEMS,
    )
    bpy.types.Scene.rd_ai_alley = bpy.props.EnumProperty(
        name="Alley", description="Mark generated lanes as an alley",
        items=_rd_yes_no, default="NO",
    )
    bpy.types.Scene.rd_ai_traffic_blocked = bpy.props.EnumProperty(
        name="Traffic Blocked", description="Block AI traffic on the generated lanes",
        items=_rd_yes_no, default="NO",
    )
    bpy.types.Scene.rd_ai_ped_blocked = bpy.props.EnumProperty(
        name="Peds Blocked", description="Block pedestrians on the generated lanes",
        items=_rd_yes_no, default="NO",
    )
    bpy.types.Scene.rd_prop_name = bpy.props.EnumProperty(
        name="Street Prop",
        description="Which prop to place along the sidewalk",
        items=RD_PROP_ITEMS,
    )
    bpy.types.Scene.rd_prop_interval = bpy.props.FloatProperty(
        name="Interval",
        description="Distance between props along the sidewalk (game units)",
        default=20.0, min=1.0, soft_max=100.0,
    )
    bpy.types.Scene.rd_prop_side = bpy.props.EnumProperty(
        name="Side",
        description="Which sidewalk(s) to furnish",
        items=[("BOTH", "Both", ""), ("LEFT", "Left", ""), ("RIGHT", "Right", "")],
        default="BOTH",
    )
    bpy.types.Scene.rd_prop_offset = bpy.props.FloatProperty(
        name="Lateral Nudge",
        description="Fine lateral offset from the sidewalk centre (±, game units)",
        default=0.0, soft_min=-10.0, soft_max=10.0,
    )
    bpy.types.Scene.rd_prop_flags = bpy.props.EnumProperty(
        name="Flags",
        description="Collision/behaviour flags for the placed props (AUTO picks by type)",
        items=RD_PROP_FLAG_ITEMS, default="AUTO",
    )
    bpy.types.Scene.rd_prop_angle_offset = bpy.props.FloatProperty(
        name="Rotate",
        description="Rotate prop facing relative to perpendicular-to-road (degrees)",
        default=0.0, soft_min=-180.0, soft_max=180.0,
    )
    bpy.types.Scene.rd_prop_height_offset = bpy.props.FloatProperty(
        name="Height Nudge",
        description="Raise/lower props off the sidewalk top (±, game units)",
        default=0.0, soft_min=-5.0, soft_max=5.0,
    )
    bpy.types.Scene.rd_prop_stagger = bpy.props.BoolProperty(
        name="Stagger Sides",
        description="Offset the right side by half an interval so the two rows alternate",
        default=False,
    )
    bpy.types.Scene.rd_facade_name = bpy.props.EnumProperty(
        name="Facade",
        description="Which building/wall facade to line the road with",
        items=RD_FACADE_ITEMS,
    )
    bpy.types.Scene.rd_facade_width = bpy.props.FloatProperty(
        name="Panel Width",
        description="Width of each facade panel along the wall (game units)",
        default=10.0, min=1.0, soft_max=50.0,
    )
    bpy.types.Scene.rd_facade_side = bpy.props.EnumProperty(
        name="Side",
        description="Which side(s) to line with facades",
        items=[("BOTH", "Both", ""), ("LEFT", "Left", ""), ("RIGHT", "Right", "")],
        default="BOTH",
    )
    bpy.types.Scene.rd_facade_offset = bpy.props.FloatProperty(
        name="Setback",
        description="Gap from the outer sidewalk edge to the building wall (game units)",
        default=0.0, soft_min=-10.0, soft_max=30.0,
    )
    bpy.types.Scene.rd_facade_height_offset = bpy.props.FloatProperty(
        name="Height Nudge",
        description="Raise/lower the facade base off the road elevation (±, game units)",
        default=0.0, soft_min=-10.0, soft_max=10.0,
    )
    bpy.types.Scene.rd_facade_flip = bpy.props.BoolProperty(
        name="Flip Facing",
        description="Flip which way the facades face (toward / away from the road)",
        default=False,
    )
    bpy.types.Scene.rd_facade_bright = bpy.props.BoolProperty(
        name="Lit (Bright)",
        description="Set the BRIGHT flag for a lit-windows look",
        default=False,
    )
    bpy.types.Scene.rd_build_bake = bpy.props.BoolProperty(
        name="Bake", description="Bake road geometry in Build All", default=True,
    )
    bpy.types.Scene.rd_build_ai = bpy.props.BoolProperty(
        name="AI Lanes", description="Generate AI lanes in Build All", default=True,
    )
    bpy.types.Scene.rd_build_props = bpy.props.BoolProperty(
        name="Props", description="Place street props in Build All", default=False,
    )
    bpy.types.Scene.rd_build_facades = bpy.props.BoolProperty(
        name="Facades", description="Place facades in Build All", default=False,
    )
    bpy.types.Scene.rd_build_junctions = bpy.props.BoolProperty(
        name="Junctions", description="Auto-wire junctions where roads meet in Build Network",
        default=True,
    )
    bpy.types.Scene.rd_snap_threshold = bpy.props.FloatProperty(
        name="Snap Distance",
        description="Spine endpoints from different roads within this distance form a junction",
        default=8.0, min=0.5, soft_max=50.0,
    )
    bpy.types.Scene.rd_junction_size = bpy.props.FloatProperty(
        name="Junction Size",
        description="Side length of the junction road patch (game units)",
        default=14.0, min=2.0, soft_max=80.0,
    )
    bpy.types.Scene.rd_junction_type = bpy.props.EnumProperty(
        name="AI Type",
        description="Intersection type applied to AI lanes ending at this junction",
        items=RD_AI_INTERSECTION_ITEMS,
    )
    bpy.types.Scene.rd_junction_lights = bpy.props.BoolProperty(
        name="Traffic Lights",
        description="Place a traffic light at each junction corner",
        default=False,
    )
    bpy.types.Scene.rd_junction_crosswalk = bpy.props.BoolProperty(
        name="Crosswalks",
        description="Lay a zebra crossing across each road approaching the junction",
        default=False,
    )
    bpy.types.Scene.rd_junction_arms = bpy.props.IntProperty(
        name="Arms", description="Number of road arms for a custom N-way junction",
        default=4, min=1, max=8,
    )
    bpy.types.Scene.rd_junction_rotation = bpy.props.FloatProperty(
        name="Rotation", description="Base rotation for custom junction arms (degrees)",
        default=0.0, soft_min=-180.0, soft_max=180.0,
    )
    bpy.types.Scene.rd_fill_width = bpy.props.FloatProperty(
        name="Fill Width", description="Grass patch width (game units)",
        default=20.0, min=1.0, soft_max=400.0,
    )
    bpy.types.Scene.rd_fill_length = bpy.props.FloatProperty(
        name="Fill Length", description="Grass patch length (game units)",
        default=20.0, min=1.0, soft_max=400.0,
    )
    bpy.types.Scene.rd_fill_rotation = bpy.props.FloatProperty(
        name="Fill Rotation", description="Grass patch rotation around vertical (degrees)",
        default=0.0, soft_min=-180.0, soft_max=180.0,
    )
    bpy.types.Scene.rd_junction_preset = bpy.props.EnumProperty(
        name="Preset", description="Junction skeleton to spawn at the 3D cursor",
        items=RD_JUNCTION_PRESET_ITEMS,
    )
    bpy.types.Scene.rd_junction_arm_length = bpy.props.FloatProperty(
        name="Arm Length", description="Length of each road arm radiating from the junction",
        default=30.0, min=2.0, soft_max=200.0,
    )
    bpy.types.Scene.rd_verge_width = bpy.props.FloatProperty(
        name="Verge Width", description="Grass strip width alongside the road (game units)",
        default=6.0, min=0.5, soft_max=60.0,
    )
    bpy.types.Scene.rd_verge_offset = bpy.props.FloatProperty(
        name="Verge Offset", description="Gap from the outer sidewalk edge to the verge",
        default=0.0, soft_min=-10.0, soft_max=30.0,
    )
    bpy.types.Scene.rd_verge_side = bpy.props.EnumProperty(
        name="Verge Side", description="Which side(s) to line with grass",
        items=[("BOTH", "Both", ""), ("LEFT", "Left", ""), ("RIGHT", "Right", "")],
        default="BOTH",
    )
    bpy.types.Scene.rd_verge_height = bpy.props.FloatProperty(
        name="Verge Height", description="Raise/lower the verge off the road elevation",
        default=0.0, soft_min=-5.0, soft_max=5.0,
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
    bpy.types.Scene.ce_show_parts = bpy.props.BoolProperty(
        name="Show Parts",
        description="Expand the per-part list (body, wheels, lights, trailer)",
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
    bpy.types.Scene.ce_add_trailer = bpy.props.BoolProperty(
        name="Add Trailer",
        description=(
            "Attach a trailer to this car. Packs a {NAME}_TRAILER sub-car (stock "
            "VPSEMI trailer) and sets the trailer flag so the game hitches it on. "
            "Best on a large/semi-style tractor"
        ),
        default=False,
    )
    bpy.types.Scene.ce_export_paint_variants = bpy.props.BoolProperty(
        name="Paint Variants",
        description="If the car's body textures have colour siblings (e.g. built on "
                    "VPBULLET → Blue/Red/White), export the TSH sibling chain so the "
                    "colours are selectable as paint jobs in the game's car menu",
        default=True,
    )
    bpy.types.Scene.ce_add_siren = bpy.props.BoolProperty(
        name="Police Lights / Siren",
        description=(
            "Add flashing red/blue roof lights and a siren. Sets the siren flag and "
            "packs the REDLIGHT/BLUELIGHT meshes; in-game, press the horn key to "
            "toggle. New cars only (full pack)"
        ),
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

    # New Car From Template
    from src.integrations.blender.modeling.car_templates import get_template_items
    bpy.types.Scene.ce_template = bpy.props.EnumProperty(
        name="Template",
        description="Vehicle archetype used as a starting point",
        items=get_template_items(),
        default="SEDAN",
    )
    bpy.types.Scene.ce_template_wheel_count = bpy.props.IntProperty(
        name="Wheels",
        description="Number of wheels for the new car (0 = use the template's own layout; "
                    "1-10 spawns that many at the body's corners — bikes, trikes, 8/10-wheelers)",
        default=0, min=0, max=10,
    )
    bpy.types.Scene.ce_car_display_name = bpy.props.StringProperty(
        name="Menu Name",
        description="Name shown in the game's car selection menu, e.g. Cool Car (filename auto-generated as VP + uppercased name)",
        default="My Car",
    )
    bpy.types.Scene.ce_import_decimate_ratio = bpy.props.FloatProperty(
        name="Decimate Ratio",
        description="Target ratio for the Decimate modifier (1.0 = no change, 0.1 = 10% of faces kept)",
        default=0.3, min=0.01, max=1.0, step=1, precision=2,
    )
    bpy.types.Scene.ce_import_wheel_count = bpy.props.IntProperty(
        name="Wheel Count",
        description="Number of wheels to spawn (1-3 = bike/trike, 4 = car, 6 = truck/bus, 7-10 = extra axles)",
        default=4, min=1, max=10,
    )
    bpy.types.Scene.ce_wheel_texture = bpy.props.EnumProperty(
        name="Wheel Texture",
        description="Wheel texture to apply to all wheels",
        items=_get_wheel_texture_items,
        update=_update_wheel_texture,
    )
    bpy.types.Scene.ce_wheel_style = bpy.props.EnumProperty(
        name="Wheel Style",
        description="Which stock car's wheel geometry/look to use when creating or spawning wheels",
        items=_get_wheel_style_items,
    )
    bpy.types.Scene.ce_wheel_size = bpy.props.FloatProperty(
        name="Wheel Radius",
        description="Wheel radius in metres for spawned wheels (New From Template auto-sizes to the body)",
        default=0.35, min=0.1, max=1.5, precision=2,
    )
    bpy.types.Scene.ce_all_wheel_radius = bpy.props.FloatProperty(
        name="All Wheels Radius",
        description="Resize every wheel to this radius — applies as you change it",
        default=0.35, min=0.05, max=2.0, precision=2,
        update=_update_all_wheel_radius,
    )
    bpy.types.Scene.ce_wheel_radius_syncing = bpy.props.BoolProperty(default=False)
    for _i in range(10):
        setattr(
            bpy.types.Scene,
            f"ce_wheel_texture_{_i}",
            bpy.props.EnumProperty(
                name=f"WHL{_i} Texture",
                description=f"Wheel texture for wheel {_i}",
                items=_get_wheel_texture_items,
                update=_make_wheel_tex_update(_i),
            ),
        )
        setattr(
            bpy.types.Scene,
            f"ce_wheel_radius_{_i}",
            bpy.props.FloatProperty(
                name=f"WHL{_i} Radius",
                description=f"Radius of wheel {_i} (resizes it about its hub)",
                default=0.35, min=0.05, max=2.0, precision=2,
                update=_make_wheel_radius_update(_i),
            ),
        )
    for _i in range(4):
        setattr(
            bpy.types.Scene,
            f"ce_trailer_wheel_texture_{_i}",
            bpy.props.EnumProperty(
                name=f"TWHL{_i} Texture",
                description=f"Texture for trailer wheel {_i}",
                items=_get_wheel_texture_items,
                update=_make_trailer_wheel_tex_update(_i),
            ),
        )
    # ── Car lights (head/tail/brake/reverse/signals) ─────────────────────────
    bpy.types.Scene.ce_light_syncing = bpy.props.BoolProperty(default=False)
    _LIGHT_COLOR_DEFAULTS = [
        "FXLTGLOW", "FXLTGLOWRED", "FXLTGLOWRED",
        "FXLTGLOW", "FXLTGLOWAMBER", "FXLTGLOWAMBER",
    ]
    for _i in range(6):
        setattr(
            bpy.types.Scene,
            f"ce_light_color_{_i}",
            bpy.props.EnumProperty(
                name="Glow Colour",
                description="Glow colour for this light (white / red / amber)",
                items=_LIGHT_COLOR_ITEMS,
                default=_LIGHT_COLOR_DEFAULTS[_i],
                update=_make_light_color_update(_i),
            ),
        )
    bpy.types.Scene.ce_light_beam = bpy.props.FloatProperty(
        name="Headlight Beam",
        description="Lengthen / shorten the headlight beam cone — applies as you change it",
        default=1.0, min=0.2, max=4.0, precision=2,
        update=_update_light_beam,
    )
    bpy.types.Scene.ce_hide_light_glows = bpy.props.BoolProperty(
        name="Hide Glows in Viewport",
        description="Hide the light & siren glow meshes while editing the body (they still render in-game)",
        default=False,
        update=_update_hide_light_glows,
    )
    bpy.types.Scene.ce_siren_color_red = bpy.props.EnumProperty(
        name="Siren Light 1",
        description="Glow colour of the first siren lens",
        items=_LIGHT_COLOR_ITEMS,
        default="FXLTGLOWRED",
        update=_make_siren_color_update("light_red", "ce_siren_color_red"),
    )
    bpy.types.Scene.ce_siren_color_blue = bpy.props.EnumProperty(
        name="Siren Light 2",
        description="Glow colour of the second siren lens",
        items=_LIGHT_COLOR_ITEMS,
        default="FXLTGLOWBLUE",
        update=_make_siren_color_update("light_blue", "ce_siren_color_blue"),
    )

    # ── Car Info (.INFO menu stats) ───────────────────────────────────────────
    bpy.types.Scene.ce_info_description = bpy.props.StringProperty(
        name="Description",
        description="Name shown in the in-game car-select menu",
        default="Custom Car",
    )
    bpy.types.Scene.ce_info_colors = bpy.props.StringProperty(
        name="Colors",
        description="Comma-separated colour names shown in the menu. Auto-set when paint "
                    "variants are exported; used as-is otherwise",
        default="Red",
    )
    bpy.types.Scene.ce_info_horsepower = bpy.props.IntProperty(
        name="Horsepower", description="Menu horsepower stat", default=320, min=0, max=2000,
    )
    bpy.types.Scene.ce_info_topspeed = bpy.props.IntProperty(
        name="Top Speed", description="Menu top-speed stat", default=200, min=0, max=500,
    )
    bpy.types.Scene.ce_info_durability = bpy.props.IntProperty(
        name="Durability", description="How much damage the car takes before wrecking",
        default=500000, min=0, max=10_000_000,
    )
    bpy.types.Scene.ce_info_mass = bpy.props.IntProperty(
        name="Mass", description="Car mass (kg) reported in the menu .INFO",
        default=1500, min=100, max=20_000,
    )
    bpy.types.Scene.ce_audio_profile = bpy.props.EnumProperty(
        name="Engine Sound",
        description="Which car's engine + horn sounds the custom car uses (copied on AR + Launch)",
        items=_get_audio_profile_items,
    )
    bpy.types.Scene.ce_mirror_x = bpy.props.BoolProperty(
        name="X-Axis Symmetry",
        description="When ON, Edit-Mode vertex/edge/face transforms are mirrored across each part's local X axis",
        default=False,
    )

    # ── Car Editor — physics (MMCARSIM) ───────────────────────────────────────
    # When override is ON, these values are written into the car's .MMCARSIM on
    # pack (works for new cars and existing-car edits). When OFF the car keeps
    # its stock/template physics. Loading a car syncs these to its real values.
    bpy.types.Scene.ce_phys_override = bpy.props.BoolProperty(
        name="Override Physics",
        description="Write the values below into the car's MMCARSIM on AR + Launch. "
                    "When off, the car keeps its stock/template handling",
        default=False,
    )
    bpy.types.Scene.ce_phys_mass = bpy.props.FloatProperty(
        name="Mass",
        description="Vehicle mass in kg. Heavier = more momentum, harder to shove around (car ~1300-3200, truck/bus 4500-10000)",
        default=1500.0, min=200.0, max=12000.0,
    )
    bpy.types.Scene.ce_phys_horsepower = bpy.props.FloatProperty(
        name="Horsepower",
        description="Engine max horsepower — acceleration and top speed (stock ~240-600)",
        default=320.0, min=50.0, max=1500.0,
    )
    bpy.types.Scene.ce_phys_drag = bpy.props.FloatProperty(
        name="Drag",
        description="Aerodynamic drag — higher lowers top speed (stock ~0.12-0.62)",
        default=0.12, min=0.0, max=1.0, precision=3,
    )
    bpy.types.Scene.ce_phys_downforce = bpy.props.FloatProperty(
        name="Downforce",
        description="High-speed grip pressing the car down (most cars 0; Panoz 0.4)",
        default=0.0, min=0.0, max=2.0, precision=2,
    )
    bpy.types.Scene.ce_phys_grip = bpy.props.FloatProperty(
        name="Grip",
        description="Overall handling friction (CarFrictionHandling). Higher = more grip / less slide (stock ~0.7-1.13)",
        default=0.9, min=0.3, max=1.6, precision=2,
    )
    bpy.types.Scene.ce_phys_drift = bpy.props.FloatProperty(
        name="Drift Torque",
        description="How readily the car swings its tail out (0 = none; Ford ~14)",
        default=7.0, min=0.0, max=20.0, precision=1,
    )
    bpy.types.Scene.ce_phys_suspension = bpy.props.FloatProperty(
        name="Suspension",
        description="Suspension spring stiffness for all wheels. Higher = stiffer/less body roll (car ~40k-100k, truck 280k-420k)",
        default=75300.0, min=20000.0, max=500000.0,
    )
    bpy.types.Scene.ce_phys_cg_x = bpy.props.FloatProperty(
        name="CG Lateral (X)",
        description="Centre-of-gravity left/right offset (BodyCG X). Negative = left, positive = right",
        default=0.0, min=-10.0, max=10.0, precision=3,
    )
    bpy.types.Scene.ce_phys_cg_height = bpy.props.FloatProperty(
        name="CG Height (Y)",
        description="Centre-of-gravity height (BodyCG Y). Lower = more stable / harder to flip; "
                    "raise it for a tippy car. Useful for big-wheel cars that roll over (stock ~-0.01 to -0.12)",
        default=-0.06, min=-10.0, max=10.0, precision=3,
    )
    bpy.types.Scene.ce_phys_cg_z = bpy.props.FloatProperty(
        name="CG Fore/Aft (Z)",
        description="Centre-of-gravity front/back offset (BodyCG Z). Negative = front, positive = rear",
        default=0.0, min=-10.0, max=10.0, precision=3,
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

    # ── City Loader scene properties ─────────────────────────────────────────
    bpy.types.Scene.cl_city_folder = bpy.props.StringProperty(
        name="City Folder",
        description="Path to the city root folder (e.g. resources/city_files/RACETRACK_7)",
        default="",
        subtype="DIR_PATH",
    )
    bpy.types.Scene.cl_load_fcd = bpy.props.BoolProperty(
        name="Load FCD",
        description="Load and visualise the .FCD facades file",
        default=True,
    )
    bpy.types.Scene.cl_load_bng = bpy.props.BoolProperty(
        name="Load BNG",
        description="Load and place the .BNG props/bangers file",
        default=True,
    )
    bpy.types.Scene.cl_load_meshes = bpy.props.BoolProperty(
        name="Load Meshes",
        description="Load all CULL*.BMS files from the MESHES/ subfolder",
        default=True,
    )
    bpy.types.Scene.cl_load_bai = bpy.props.BoolProperty(
        name="Load BAI",
        description="Load AI streets from the .BAI file in the CITY/ subfolder",
        default=True,
    )
    bpy.types.Scene.cl_load_gizmo = bpy.props.BoolProperty(
        name="Load GIZMO",
        description="Load drawbridges from the .GIZMO file",
        default=True,
    )
    bpy.types.Scene.cl_texture_folder = bpy.props.StringProperty(
        name="Texture Folder",
        description="Texture folder used when loading city meshes (leave blank for default editor textures)",
        default="",
        subtype="DIR_PATH",
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
    # Export → write directly to src/USER/facades.py (backs up the old file)
    bpy.types.Scene.fr_replace_user_facades = bpy.props.BoolProperty(
        name="Replace USER facades.py",
        description="Write the export straight into src/USER/facades.py, backing up the old file as facades_backup_{timestamp}.py. When off, you pick a file path",
        default=False,
    )

    # ── Bridge Editor — edit form ─────────────────────────────────────────────
    bpy.types.Scene.be_active_obj_name = bpy.props.StringProperty(
        name="Active Bridge Object", default="",
    )
    bpy.types.Scene.be_active_group_id = bpy.props.StringProperty(
        name="Active Bridge Group", default="",
    )
    bpy.types.Scene.be_active_role = bpy.props.StringProperty(
        name="Active Bridge Role", default="",
    )
    bpy.types.Scene.be_prop_name = bpy.props.EnumProperty(
        name="Prop", description="Bridge prop type", items=BRIDGE_NAME_ITEMS,
        update=_update_bridge_form,
    )
    _bkw = dict(precision=3, update=_update_bridge_form)
    bpy.types.Scene.be_offset_x = bpy.props.FloatProperty(name="Offset X", **_bkw)
    bpy.types.Scene.be_offset_y = bpy.props.FloatProperty(name="Offset Y", **_bkw)
    bpy.types.Scene.be_offset_z = bpy.props.FloatProperty(name="Offset Z", **_bkw)
    bpy.types.Scene.be_angle = bpy.props.FloatProperty(
        name="Angle", description="Facing angle in degrees (0=East, +90=South per Z+, etc.)",
        default=0.0, precision=2, update=_update_bridge_form,
    )

    # ── Bridge Editor — create form ───────────────────────────────────────────
    bpy.types.Scene.bc_offset_x = bpy.props.FloatProperty(name="X", default=0.0, precision=2)
    bpy.types.Scene.bc_offset_y = bpy.props.FloatProperty(name="Y", default=0.01, precision=2, description="Height")
    bpy.types.Scene.bc_offset_z = bpy.props.FloatProperty(name="Z", default=0.0, precision=2)
    bpy.types.Scene.bc_angle = bpy.props.FloatProperty(
        name="Angle", default=0.01, precision=2,
        description="Facing of the bridge set (degrees, 0=East)",
    )
    bpy.types.Scene.bc_span = bpy.props.FloatProperty(
        name="Span", default=64.8, min=1.0, soft_max=200.0, precision=2,
        description="Distance between the two drawbridge halves",
    )
    bpy.types.Scene.bc_gate_offset = bpy.props.FloatProperty(
        name="Gate Offset", default=15.0, min=0.0, soft_max=50.0, precision=2,
        description="Crossgate offset from drawbridge centre along the road axis",
    )
    bpy.types.Scene.bc_facing_in = bpy.props.BoolProperty(
        name="Halves Face Inward", default=True,
        description="If true, the two drawbridge halves face each other",
    )
    bpy.types.Scene.bc_drawbridge_name = bpy.props.EnumProperty(
        name="Drawbridge", items=BRIDGE_NAME_ITEMS,
        default="tpdrawbridge06",
    )
    bpy.types.Scene.bc_crossgate_name = bpy.props.EnumProperty(
        name="Crossgate", items=BRIDGE_NAME_ITEMS,
        default="tpcrossgate06",
    )

    # ── Skeleton Editor ───────────────────────────────────────────────────────
    bpy.types.Scene.ske_char_name = bpy.props.EnumProperty(
        name="Character",
        description="Pedestrian character to load",
        items=CHAR_ITEMS,
        default="BUSMAN_INIT",
    )
    bpy.types.Scene.ske_anim_name = bpy.props.EnumProperty(
        name="Animation",
        description="Animation to load from the character CSV",
        items=_anim_items,
    )
    bpy.types.Scene.ske_new_anim_name = bpy.props.StringProperty(
        name="Anim Name",
        description="Name for the new blank animation action",
        default="MY_ANIM",
    )
    bpy.types.Scene.ske_new_anim_frames = bpy.props.IntProperty(
        name="Frames",
        description="Number of frames for the new blank animation",
        default=30, min=2, max=1000,
    )
    bpy.types.Scene.ske_gen_style = bpy.props.EnumProperty(
        name="Style",
        description="Procedural animation style to generate",
        items=[
            ("WALK",    "Walk",    "30-frame walk cycle with forward root motion"),
            ("RUN",     "Run",     "20-frame run cycle with fast forward root motion"),
            ("WAVE",    "Wave",    "30-frame right-arm wave"),
            ("IDLE",    "Idle",    "60-frame subtle idle breathing"),
            ("DIVE",    "Dive",    "30-frame forward dive / tackle fall"),
            ("STUMBLE", "Stumble", "20-frame stumble / hit reaction"),
            ("CHEER",   "Cheer",   "40-frame victory cheer with raised arms"),
            ("SCARED",  "Scared",  "24-frame panicked run with flailing arms"),
        ],
        default="WALK",
    )
    bpy.types.Scene.ske_walk_speed = bpy.props.FloatProperty(
        name="Speed",
        description="Multiplier for root motion distance (walk/run/dive/scared)",
        default=1.0, min=0.1, max=5.0, step=10,
    )
    bpy.types.Scene.ske_ar_name = bpy.props.StringProperty(
        name="AR Name",
        description="Output .AR filename (without extension) written to MidtownMadness/",
        default="!!!!!ped_anims",
    )
    def _update_ske_var_variant(self, context):
        bpy.ops.ske.load_variant("EXEC_DEFAULT")

    bpy.types.Scene.ske_var_variant = bpy.props.IntProperty(
        name="Variant",
        description="Clothing color variant (0–5, the game picks one randomly at spawn)",
        default=0, min=0, max=5,
        update=_update_ske_var_variant,
    )

    # ── Dash Editor scene properties ──────────────────────────────────────────
    bpy.types.Scene.de_dash_car = bpy.props.EnumProperty(
        name="Car",
        description="Which car's cockpit dash to load and edit",
        items=get_dash_car_items,
    )
    bpy.types.Scene.de_new_car = bpy.props.StringProperty(
        name="New Car",
        description="Car name to seed a fresh dash for (from the template)",
        default="",
    )
    bpy.types.Scene.de_updating = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.de_preview = bpy.props.FloatProperty(
        name="Preview",
        description="Sweep the gauge needles 0 (rest) → 1 (full scale) to preview them",
        default=0.0, min=0.0, max=1.0,
        update=update_de_preview,
    )
    bpy.types.Scene.de_speed_rot_min = bpy.props.FloatProperty(
        name="Speed Min", description="Speed needle angle at zero (radians)",
        default=0.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_speed_rot_max = bpy.props.FloatProperty(
        name="Speed Max", description="Speed needle angle at max speed (radians)",
        default=0.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_rpm_rot_min = bpy.props.FloatProperty(
        name="RPM Min", description="Tach needle angle at zero (radians)",
        default=0.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_rpm_rot_max = bpy.props.FloatProperty(
        name="RPM Max", description="Tach needle angle at max RPM (radians)",
        default=0.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_damage_rot_min = bpy.props.FloatProperty(
        name="Damage Min", description="Damage needle angle at zero (radians)",
        default=0.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_damage_rot_max = bpy.props.FloatProperty(
        name="Damage Max", description="Damage needle angle at full damage (radians)",
        default=0.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_max_speed = bpy.props.FloatProperty(
        name="Max Speed", description="Full-scale speed for the speed gauge",
        default=160.0, min=1.0, max=400.0,
    )
    bpy.types.Scene.de_max_rpm = bpy.props.FloatProperty(
        name="Max RPM", description="Full-scale RPM for the tach gauge",
        default=8000.0, min=1.0, max=20000.0,
    )
    bpy.types.Scene.de_min_speed = bpy.props.FloatProperty(
        name="Min Speed", description="Speed below which the gauge reads zero",
        default=0.0, min=0.0, max=100.0,
    )
    bpy.types.Scene.de_wheel_fact = bpy.props.FloatProperty(
        name="Wheel Factor", description="Steering-wheel turn amount per steer input",
        default=1.0, min=-10.0, max=10.0, update=update_de_gauge,
    )
    bpy.types.Scene.de_cam_fov = bpy.props.FloatProperty(
        name="Camera FOV", description="Cockpit camera field of view (degrees)",
        default=60.0, min=10.0, max=120.0,
    )
    bpy.types.Scene.de_cam_offset = bpy.props.FloatVectorProperty(
        name="Camera Offset", description="Cockpit camera position (game car-local)",
        size=3, default=(0.0, 1.2, 0.3),
    )
    bpy.types.Scene.de_cam_pitch = bpy.props.FloatProperty(
        name="Camera Pitch", description="Cockpit camera downward tilt (radians)",
        default=0.0, soft_min=-1.5, soft_max=1.5,
    )
    bpy.types.Scene.de_cam_near = bpy.props.FloatProperty(
        name="Near Clip", description="Cockpit camera near clip distance",
        default=0.1, min=0.001, soft_max=10.0,
    )
    bpy.types.Scene.de_cam_far = bpy.props.FloatProperty(
        name="Far Clip", description="Cockpit camera far clip distance",
        default=1600.0, min=1.0, soft_max=10000.0,
    )
    bpy.types.Scene.de_swap_car = bpy.props.EnumProperty(
        name="Swap From",
        description="Source car to borrow a dash part (e.g. steering wheel) from",
        items=get_dash_car_items,
    )
    bpy.types.Scene.de_reskin_texture = bpy.props.EnumProperty(
        name="Dash Texture",
        description="Apply a dash texture (from any car) to the active part's active slot",
        items=get_dash_texture_items,
        update=update_de_reskin_texture,
    )
    bpy.types.Scene.de_reskin_image = bpy.props.StringProperty(
        name="Reskin Image",
        description="Custom .DDS to apply to the active part's active texture slot",
        default="", subtype="FILE_PATH",
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

    # Additive, isolated: the single-graph road-network compiler (its own "Road Net" tab).
    # Guarded so a failure here can never break the rest of the addon registration.
    try:
        from src.integrations.blender.operators.roadnet_editor import register_roadnet
        register_roadnet()
    except Exception as exc:  # pragma: no cover - defensive
        from src.ui.console import item
        item(f"roadnet editor not registered: {exc}")


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

    try:
        from src.integrations.blender.operators.roadnet_editor import unregister_roadnet
        unregister_roadnet()
    except Exception:  # pragma: no cover - defensive
        pass

    if bpy.app.timers.is_registered(_vertex_poll_timer):
        bpy.app.timers.unregister(_vertex_poll_timer)

    shutdown_auto_save()

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
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
    st_intersection_update
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
from src.integrations.blender.operators.props import PROP_EDITOR_CLASSES, PROP_NAME_ITEMS, _update_prop_form
from src.integrations.blender.waypoints.draw import register_draw_handler, unregister_draw_handler
from src.integrations.blender.modeling.uv_mapping import TEXTURE_ENUM_ITEMS, update_texture_name, update_uv_tiling


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
]

ALL_CLASSES = [VertexGroup] + PANEL_CLASSES + OPERATOR_CLASSES + WAYPOINT_CLASSES

OBJECT_PROPERTIES = [
    "vertex_coords", "hud_color",
    "tile_x", "tile_y", "angle_degrees", "texture_name",
    "cell_type", "material_index", "always_visible", "sort_vertices",
    # Street properties
    "st_intersection_0", "st_intersection_1",
    "st_stop_light_name_0", "st_stop_light_name_1",
    "st_traffic_blocked_0", "st_traffic_blocked_1",
    "st_ped_blocked_0", "st_ped_blocked_1",
    "st_road_divided", "st_alley",
    "st_sl_pos_0_offset", "st_sl_pos_0_dir",
    "st_sl_pos_1_offset", "st_sl_pos_1_dir",
]

SCENE_PROPERTIES = [
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
    "st_vertex_index",
    "st_extend_length",
    "st_extend_angle",
    # Street Editor — presets
    "st_street_preset",
    "st_preset_length",
    "st_preset_lane_width",
    "st_preset_turn_radius",
    "st_preset_curve_points",
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
    )
    bpy.types.Object.st_stop_light_name_1 = bpy.props.EnumProperty(
        name="Stop Light (End)",
        items=STOP_LIGHT_NAME_ITEMS,
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
        name="SL 0 Offset", size=3, default=(0.0, 0.0, 0.0), subtype='XYZ'
    )
    bpy.types.Object.st_sl_pos_0_dir = bpy.props.FloatVectorProperty(
        name="SL 0 Direction", size=3, default=(0.01, 0.0, 0.0), subtype='XYZ'
    )
    bpy.types.Object.st_sl_pos_1_offset = bpy.props.FloatVectorProperty(
        name="SL 1 Offset", size=3, default=(0.0, 0.0, 0.0), subtype='XYZ'
    )
    bpy.types.Object.st_sl_pos_1_dir = bpy.props.FloatVectorProperty(
        name="SL 1 Direction", size=3, default=(0.01, 0.0, 0.0), subtype='XYZ'
    )


def register_scene_properties() -> None:
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
    bpy.types.Scene.st_vertex_index = bpy.props.IntProperty(
        name="Active Vertex",
        description="Index of the active vertex for insert / delete / move operations",
        default=0,
        min=0,
    )
    bpy.types.Scene.st_extend_length = bpy.props.FloatProperty(
        name="Extend Length",
        description="Distance to extend when using directional extend",
        default=10.0, min=0.1, soft_max=200.0,
    )
    bpy.types.Scene.st_extend_angle = bpy.props.FloatProperty(
        name="Angle Offset",
        description="Rotation applied to the extension direction (degrees). 0 = same angle.",
        default=0.0, soft_min=-180.0, soft_max=180.0,
    )
    # ── Street Presets scene properties ───────────────────────────────────────
    bpy.types.Scene.st_street_preset = bpy.props.EnumProperty(
        name="Street Preset",
        description="AI street preset to spawn",
        items=ST_PRESET_ITEMS,
        default="SINGLE",
    )
    bpy.types.Scene.st_preset_length = bpy.props.FloatProperty(
        name="Preset Length",
        description="Length of each arm / straight segment in the preset",
        default=40.0, min=5.0, soft_max=500.0,
    )
    bpy.types.Scene.st_preset_lane_width = bpy.props.FloatProperty(
        name="Lane Width",
        description="Width of each lane (used for multi-lane presets)",
        default=5.0, min=1.0, soft_max=20.0,
    )
    bpy.types.Scene.st_preset_turn_radius = bpy.props.FloatProperty(
        name="Turn Radius",
        description="Radius of curved presets (roundabout ring, 90° curves, etc.)",
        default=20.0, min=3.0, soft_max=200.0,
    )
    bpy.types.Scene.st_preset_curve_points = bpy.props.IntProperty(
        name="Curve Points",
        description="Number of vertices used to approximate curves",
        default=7, min=3, max=32,
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


def initialize_blender_panels() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    register_object_properties()
    register_street_properties()
    register_scene_properties()

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
import bpy

from src.constants.misc import Executable
from src.helpers.main import is_process_running
from src.integrations.blender.modeling.uv_mapping import OBJECT_OT_UpdateUVMapping

from src.integrations.blender.operators.custom_properties import OBJECT_OT_AssignCustomProperties
from src.integrations.blender.operators.export_polygons import OBJECT_OT_ExportPolygons
from src.integrations.blender.operators.process_extrude import OBJECT_OT_ProcessPostExtrude
from src.integrations.blender.operators.rename_polygons import (OBJECT_OT_RenameChildren, OBJECT_OT_RenameSequential, OBJECT_OT_FixPolygonNames, OBJECT_OT_CreatePolygon)
from src.integrations.blender.operators.waypoints import (
    CREATE_SINGLE_WAYPOINT_OT_operator,
    EXPORT_ALL_WAYPOINTS_OT_operator,
    EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator,
    EXPORT_SELECTED_WAYPOINTS_OT_operator,
    EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator,
    LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator,
    LOAD_WAYPOINTS_FROM_CSV_OT_operator,
    LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator
)

from src.integrations.blender.panels.cells import OBJECT_PT_CellTypePanel, CELL_IMPORT
from src.integrations.blender.panels.hud import OBJECT_PT_HUDColorPanel, HUD_IMPORT, hud_color_index_update, hud_colors_update
from src.integrations.blender.panels.materials import OBJECT_PT_MaterialTypePanel, MATERIAL_IMPORT
from src.integrations.blender.panels.misc import OBJECT_PT_PolygonMiscOptionsPanel
from src.integrations.blender.panels.vertex import OBJECT_PT_VertexCoordinates, VertexGroup
from src.integrations.blender.panels.uv import OBJECT_PT_UVMappingPanel
from src.integrations.blender.panels.sidebar import SIDEBAR_CLASSES
from src.integrations.blender.modeling.uv_mapping import TEXTURE_ENUM_ITEMS, update_texture_name, update_uv_tiling


PANEL_CLASSES = [
    OBJECT_PT_CellTypePanel,
    OBJECT_PT_MaterialTypePanel,
    OBJECT_PT_PolygonMiscOptionsPanel,
    OBJECT_PT_HUDColorPanel,
    OBJECT_PT_VertexCoordinates,
    OBJECT_PT_UVMappingPanel,
    *SIDEBAR_CLASSES,
]

OPERATOR_CLASSES = [
    OBJECT_OT_UpdateUVMapping,
    OBJECT_OT_ExportPolygons,
    OBJECT_OT_AssignCustomProperties,
    OBJECT_OT_ProcessPostExtrude,
    OBJECT_OT_RenameChildren,
    OBJECT_OT_RenameSequential,
    OBJECT_OT_FixPolygonNames,
    OBJECT_OT_CreatePolygon,
]

WAYPOINT_CLASSES = [
    CREATE_SINGLE_WAYPOINT_OT_operator,
    LOAD_WAYPOINTS_FROM_CSV_OT_operator,
    LOAD_WAYPOINTS_FROM_RACE_DATA_OT_operator,
    LOAD_CNR_WAYPOINTS_FROM_CSV_OT_operator,
    EXPORT_SELECTED_WAYPOINTS_OT_operator,
    EXPORT_SELECTED_WAYPOINTS_WITH_BRACKETS_OT_operator,
    EXPORT_ALL_WAYPOINTS_OT_operator,
    EXPORT_ALL_WAYPOINTS_WITH_BRACKETS_OT_operator,
]

ALL_CLASSES = [VertexGroup] + PANEL_CLASSES + OPERATOR_CLASSES + WAYPOINT_CLASSES

OBJECT_PROPERTIES = [
    "vertex_coords", "hud_color_index", "hud_colors",
    "tile_x", "tile_y", "angle_degrees", "texture_name",
    "cell_type", "material_index", "always_visible", "sort_vertices",
]


def register_object_properties() -> None:
    bpy.types.Object.hud_color_index = bpy.props.IntProperty(
        name="HUD Color Index",
        default=0,
        update=hud_color_index_update
    )
    bpy.types.Object.hud_colors = bpy.props.BoolVectorProperty(
        name="HUD Colors",
        description="Select the color of the HUD",
        size=len(HUD_IMPORT),
        default=(False,) * len(HUD_IMPORT),
        update=hud_colors_update
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

    register_object_properties()  # Must come before any class registration

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


def unregister_all() -> None:
    if not is_process_running(Executable.BLENDER):
        return

    for cls in reversed(ALL_CLASSES):
        _safe_unregister(cls)

    for prop in OBJECT_PROPERTIES:
        if hasattr(bpy.types.Object, prop):
            try:
                delattr(bpy.types.Object, prop)
            except AttributeError:
                pass
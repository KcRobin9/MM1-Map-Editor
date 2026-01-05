import bpy

from src.constants.misc import Color
from src.constants.constants import YES, NO
from src.constants.file_formats import Material, Room


CUSTOM_PROPERTIES_CONFIG_DEFAULT = {
    "cell_type": Room.DEFAULT,
    "material_index": Material.DEFAULT,
    "hud_color": Color.ROAD,
    "sort_vertices": NO,
    "always_visible": YES,
    "tile_x": 2.0,
    "tile_y": 2.0,
    "rotate": 0.01
}

class OBJECT_OT_AssignCustomProperties(bpy.types.Operator):
    bl_idname = "object.assign_custom_properties"
    bl_label = "Assign Custom Properties to Polygons"
    bl_description = "Assign Custom Properties to polygons that do not have them yet"
    bl_options = {"REGISTER", "UNDO"}

    def assign_defaults(self, obj: bpy.types.Object, property_name: str, default_value: any) -> None:
        if property_name not in obj:
            obj[property_name] = default_value

    def execute(self, context: bpy.types.Context) -> set:
        for obj in context.scene.objects:
            if obj.type == "MESH":
                for prop_name, default_value in CUSTOM_PROPERTIES_CONFIG_DEFAULT.items():
                    self.assign_defaults(obj, prop_name, default_value)

                uv_layer = obj.data.uv_layers.active
                
                if uv_layer is None:
                    uv_layer = obj.data.uv_layers.new(name = "UVMap")
                    original_uvs = [(uv_data.uv[0], uv_data.uv[1]) for uv_data in uv_layer.data]
                    obj["original_uvs"] = original_uvs

        self.report({"INFO"}, "Assigned Custom Properties")
        return {"FINISHED"}
      
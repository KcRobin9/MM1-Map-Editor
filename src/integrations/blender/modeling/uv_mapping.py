import bpy
import math


def update_uv_tiling(self, context):
    obj = self
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return

    tile_x = obj.tile_x
    tile_y = obj.tile_y
    angle_degrees = obj.angle_degrees

    base_coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
    center_x, center_y = 0.5, 0.5
    rad = math.radians(angle_degrees)

    computed_uvs = []
    for x, y in base_coords:
        x -= center_x
        y -= center_y
        rx = x * math.cos(rad) - y * math.sin(rad)
        ry = x * math.sin(rad) + y * math.cos(rad)
        computed_uvs.append(((rx + center_x) * tile_x, (ry + center_y) * tile_y))

    for i, uv_data in enumerate(uv_layer.data):
        u, v = computed_uvs[i % len(computed_uvs)]
        uv_data.uv = (u, 1.0 - v)

    obj.data.update()


class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's tile and rotation properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            if obj.type != 'MESH':
                continue
            update_uv_tiling(obj, context)

        return {"FINISHED"}
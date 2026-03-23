import bpy
import math


def unwrap_uv_to_aspect_ratio(obj, image):
    prev_active = bpy.context.view_layer.objects.active

    # Deselect all, select only this object
    for o in bpy.context.selected_objects:
        o.select_set(False)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = prev_active

    # Normalize UVs
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return

    us = [d.uv[0] for d in uv_layer.data]
    vs = [d.uv[1] for d in uv_layer.data]
    u_min, u_max = min(us), max(us)
    v_min, v_max = min(vs), max(vs)
    u_range = u_max - u_min or 1.0
    v_range = v_max - v_min or 1.0

    for d in uv_layer.data:
        d.uv[0] = (d.uv[0] - u_min) / u_range
        d.uv[1] = (d.uv[1] - v_min) / v_range


def tile_uvs(obj, tile_x=1, tile_y=1):
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return

    original_uvs = obj.get("original_uvs")
    if not original_uvs:
        return

    for i, uv_data in enumerate(uv_layer.data):
        uv_data.uv[0] = original_uvs[i][0] * tile_x
        uv_data.uv[1] = original_uvs[i][1] * tile_y


def rotate_uvs(obj, angle_degrees):
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return

    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    for uv_data in uv_layer.data:
        u = uv_data.uv[0] - 0.5
        v = uv_data.uv[1] - 0.5
        uv_data.uv[0] = u * cos_a - v * sin_a + 0.5
        uv_data.uv[1] = u * sin_a + v * cos_a + 0.5


def update_uv_tiling(self, context):
    tile_uvs(self, self.tile_x, self.tile_y)
    rotate_uvs(self, self.rotate)


class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            if obj.type != 'MESH':
                continue
            if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "angle_degrees"]):
                tile_uvs(obj, obj["tile_x"], obj["tile_y"])
                rotate_uvs(obj, obj["angle_degrees"])

        return {"FINISHED"}

    
# # UV MAPPING OPERATOR
# class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
#     bl_idname = "object.update_uv_mapping"
#     bl_label = "Update UV Mapping"
#     bl_description = "Updates UV mapping based on object's custom properties"
#     bl_options = {"REGISTER", "UNDO"}

#     def execute(self, context: bpy.types.Context) -> set:
#         for obj in bpy.context.selected_objects:
            
#             # Check if the object has the necessary custom properties
#             if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "angle_degrees"]):
                
#                 tile_uvs(obj, obj["tile_x"], obj["tile_y"])
#                 rotate_uvs(obj, obj["angle_degrees"])

#         return {"FINISHED"}
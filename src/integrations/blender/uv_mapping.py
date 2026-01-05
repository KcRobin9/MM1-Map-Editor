import bpy 
import math


def unwrap_uv_to_aspect_ratio(obj, image):
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action = 'SELECT')
    
    bpy.ops.uv.unwrap(method = 'ANGLE_BASED', margin = 0.001)
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj.data.uv_layers.active.active = True

    # Normalize the UVs to ensure they use the entire texture
    bbox = [obj.data.uv_layers.active.data[i].uv for i in range(len(obj.data.uv_layers.active.data))]
    uvs_min = [min(co[0] for co in bbox), min(co[1] for co in bbox)]
    uvs_max = [max(co[0] for co in bbox), max(co[1] for co in bbox)]
    
    for uv_loop in obj.data.uv_layers.active.data:
        uv_loop.uv[0] = (uv_loop.uv[0] - uvs_min[0]) / (uvs_max[0] - uvs_min[0])
        uv_loop.uv[1] = (uv_loop.uv[1] - uvs_min[1]) / (uvs_max[1] - uvs_min[1])
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    
def tile_uvs(obj, tile_x = 1, tile_y = 1):
    bpy.ops.object.mode_set(mode = 'OBJECT')

    # Get the active UV layer of the object
    uv_layer = obj.data.uv_layers.active.data

    # Restore original UVs
    original_uvs = obj["original_uvs"]
    for i, uv_data in enumerate(uv_layer):
        uv_data.uv[0] = original_uvs[i][0]
        uv_data.uv[1] = original_uvs[i][1]

    # Loop over each UV coordinate and scale it
    for uv_data in uv_layer:
        uv_data.uv[0] *= tile_x
        uv_data.uv[1] *= tile_y


def rotate_uvs(obj, angle_degrees):    
    bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Get the active UV layer of the object
    uv_layer = obj.data.uv_layers.active.data
    
    angle_rad = math.radians(angle_degrees)

    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)

    # Rotate each UV coordinate around the UV center (0.5, 0.5)
    for uv_data in uv_layer:
        u, v = uv_data.uv
        u -= 0.5
        v -= 0.5
        rotated_u = u * cos_angle - v * sin_angle
        rotated_v = u * sin_angle + v * cos_angle
        uv_data.uv = (rotated_u + 0.5, rotated_v + 0.5)

     
def update_uv_tiling(self, context: bpy.types.Context) -> None:
    bpy.ops.object.select_all(action = 'DESELECT')
    self.select_set(True)
    bpy.context.view_layer.objects.active = self

    tile_uvs(self, self.tile_x, self.tile_y)
    rotate_uvs(self, self.rotate)

    
# UV MAPPING OPERATOR
class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname = "object.update_uv_mapping"
    bl_label = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's custom properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            
            # Check if the object has the necessary custom properties
            if all(prop in obj.keys() for prop in ["tile_x", "tile_y", "angle_degrees"]):
                
                tile_uvs(obj, obj["tile_x"], obj["tile_y"])
                rotate_uvs(obj, obj["angle_degrees"])

        return {"FINISHED"}
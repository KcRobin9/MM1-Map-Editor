import re
import bpy


def get_polygon_objects(context: bpy.types.Context, sort: bool = False) -> list:
    polygons = [obj for obj in context.scene.objects if obj.name.startswith("P")]
    if not sort or not polygons:
        return polygons
    return sorted(polygons, key=lambda x: int(re.search(r"P(\d+)", x.name).group(1)))


def normalize_polygon_names(polygons: list) -> int:
    valid_count = 0
    for obj in polygons:
        match = re.search(r"P(\d+)", obj.name)
        if match:
            number = match.group(1)
            obj.name = f"P{number}"
            valid_count += 1
    return valid_count


def rename_sequential(polygons: list) -> int:
    for i, obj in enumerate(polygons, 1):
        obj.name = f"P{i}"
    return len(polygons)


class OBJECT_OT_RenameChildren(bpy.types.Operator):
    bl_idname = "object.auto_rename_children"
    bl_label = "Auto Rename Children Objects"  # Rename labels/names?
   
    def execute(self, context: bpy.types.Context) -> set:
        try:
            polygons = get_polygon_objects(context, sort = False)
            if not polygons:
                self.report({"WARNING"}, "No polygon objects found")
                return {"CANCELLED"}
                
            count = normalize_polygon_names(polygons)
            self.report({"INFO"}, f"Normalized {count} polygon names (preserving order)")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error normalizing names: {str(e)}")
            return {"CANCELLED"}


class OBJECT_OT_RenameSequential(bpy.types.Operator):
    bl_idname = "object.rename_sequential"
    bl_label = "Rename Objects Sequentially"  # Rename labels/names?
   
    def execute(self, context: bpy.types.Context) -> set:
        try:
            polygons = get_polygon_objects(context, sort = True)
            if not polygons:
                self.report({"WARNING"}, "No polygon objects found")
                return {"CANCELLED"}
                
            count = rename_sequential(polygons)
            self.report({"INFO"}, f"Renamed {count} polygon names sequentially")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error renaming objects: {str(e)}")
            return {"CANCELLED"}
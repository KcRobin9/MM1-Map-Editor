import re
import bpy

from src.integrations.blender.utils import get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties


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
        

class OBJECT_OT_FixPolygonNames(bpy.types.Operator):
    bl_idname = "object.fix_polygon_names"
    bl_label = "Fix Polygon Names"
    bl_description = "Rename polygons with invalid .001-style names to valid unused bound numbers"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        used = get_used_bound_numbers(context.scene)
        renamed = []

        invalid_objects = [
            obj for obj in context.scene.objects
            if obj.type == "MESH" and obj.name.startswith("P") and "." in obj.name
        ]

        if not invalid_objects:
            self.report({"INFO"}, "No invalid names found.")
            return {"FINISHED"}

        for obj in invalid_objects:
            old_name = obj.name
            new_num = next_available_bound_number(used)
            used.add(new_num)
            obj.name = f"P{new_num}"
            renamed.append(f"{old_name} → P{new_num}")

        self.report({"INFO"}, f"Renamed {len(renamed)}: " + ", ".join(renamed))
        return {"FINISHED"}
    

class OBJECT_OT_CreatePolygon(bpy.types.Operator):
    bl_idname = "object.create_polygon"
    bl_label = "Create New Polygon"
    bl_description = "Create a flat quad at the cursor with all Map Editor properties pre-assigned"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        used = get_used_bound_numbers(context.scene)
        bound_num = next_available_bound_number(used)

        bpy.ops.mesh.primitive_plane_add(size=10, location=context.scene.cursor.location)
        obj = context.object
        obj.name = f"P{bound_num}"

        assign_map_editor_properties(obj)

        self.report({"INFO"}, f"Created P{bound_num}")
        return {"FINISHED"}


class OBJECT_OT_DuplicatePolygon(bpy.types.Operator):
    bl_idname = "object.duplicate_polygon"
    bl_label = "Duplicate Polygon"
    bl_description = "Duplicate the selected polygon with a unique bound number and all properties copied"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            context.object is not None
            and context.object.type == "MESH"
            and context.object.name.startswith("P")
        )

    def execute(self, context: bpy.types.Context) -> set:
  

        source = context.object

        used = get_used_bound_numbers(context.scene)
        new_num = next_available_bound_number(used)

        # Duplicate via Blender op — this preserves mesh geometry and materials
        bpy.ops.object.duplicate(linked=False)
        new_obj = context.object  # duplicate sets itself as active

        new_obj.name = f"P{new_num}"

        # Overwrite properties from source to ensure they're in sync
        assign_map_editor_properties(new_obj, source=source)

        # Copy hud_color_index explicitly since assign_map_editor_properties uses raw custom props
        new_obj.hud_color_index = source.hud_color_index

        self.report({"INFO"}, f"Duplicated {source.name} → P{new_num}")
        return {"FINISHED"}
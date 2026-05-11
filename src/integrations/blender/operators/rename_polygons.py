import re
import bpy

from src.integrations.blender.utils import get_used_bound_numbers, next_available_bound_number, assign_map_editor_properties


def get_polygon_objects(context: bpy.types.Context, sort: bool = False) -> list:
    polygons = [obj for obj in context.scene.objects if obj.type == "MESH" and obj.name.startswith("P")]
    if not sort or not polygons:
        return polygons
    return sorted(polygons, key=lambda x: int(re.search(r"P(\d+)", x.name).group(1)))


def rename_sequential(polygons: list) -> int:
    counter = 1
    for obj in polygons:
        if counter == 200:
            counter += 1
        obj.name = f"P{counter}"
        counter += 1
    return len(polygons)


class OBJECT_OT_RenameSequential(bpy.types.Operator):
    bl_idname      = "object.rename_sequential"
    bl_label       = "Rename Objects Sequentially"
    bl_description = "Rename all P-prefixed mesh objects sequentially (P1, P2, … skipping reserved P200)"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        try:
            polygons = get_polygon_objects(context, sort=True)
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
    bl_idname      = "object.fix_polygon_names"
    bl_label       = "Fix Poly Names"
    bl_description = (
        "Fix all polygon naming issues: strips .001-style suffixes (recovering "
        "the original number where possible), renames P200 (reserved) to a safe "
        "number, and ensures P1 exists"
    )
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        used    = get_used_bound_numbers(context.scene)
        renamed = []

        # ── Step 1: fix .001-style suffix names ───────────────────────────────
        # First pass: collect objects that need fixing (have a dot in the name).
        invalid_objects = [
            obj for obj in context.scene.objects
            if obj.type == "MESH" and obj.name.startswith("P") and "." in obj.name
        ]
        for obj in invalid_objects:
            old_name = obj.name
            match = re.match(r"P(\d+)\.", obj.name)
            if match:
                original_num = int(match.group(1))
                if original_num not in used and original_num != 200:
                    # Recover the original number — no conflict
                    used.add(original_num)
                    obj.name = f"P{original_num}"
                    renamed.append(f"{old_name} → P{original_num} (restored)")
                    continue
            # Fallback: original number taken or unrecognised — assign a fresh one
            new_num = next_available_bound_number(used)
            used.add(new_num)
            obj.name = f"P{new_num}"
            renamed.append(f"{old_name} → P{new_num}")

        # ── Step 2: fix reserved P200 ─────────────────────────────────────────
        p200 = context.scene.objects.get("P200")
        if p200 and p200.type == "MESH":
            used.discard(200)
            new_num = next_available_bound_number(used)
            used.add(new_num)
            p200.name = f"P{new_num}"
            renamed.append(f"P200 (reserved) → P{new_num}")

        # ── Step 3: ensure P1 exists ──────────────────────────────────────────
        if "P1" not in context.scene.objects:
            mesh_polys = [
                obj for obj in context.scene.objects
                if obj.type == "MESH" and obj.name.startswith("P")
            ]
            if mesh_polys:
                candidate = mesh_polys[0]
                old_name  = candidate.name
                used.discard(1)
                candidate.name = "P1"
                renamed.append(f"{old_name} → P1 (required)")

        if not renamed:
            self.report({"INFO"}, "No issues found — all polygon names are valid.")
            return {"FINISHED"}

        self.report({"INFO"}, f"Fixed {len(renamed)}: " + ", ".join(renamed))
        return {"FINISHED"}


class OBJECT_OT_CreatePolygon(bpy.types.Operator):
    bl_idname      = "object.create_polygon"
    bl_label       = "New Polygon"
    bl_description = "Create a polygon at the 3D cursor using the current shape/size settings"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        used      = get_used_bound_numbers(context.scene)
        bound_num = next_available_bound_number(used)
        name      = f"P{bound_num}"

        width  = context.scene.polygon_create_width
        length = context.scene.polygon_create_length
        shape  = context.scene.polygon_create_shape
        loc    = context.scene.cursor.location

        hw, hl = width / 2, length / 2

        if shape == 'QUAD':
            verts = [(-hw, -hl, 0.0), (hw, -hl, 0.0), (hw, hl, 0.0), (-hw, hl, 0.0)]
            faces = [(0, 1, 2, 3)]
        else:  # TRI
            verts = [(-hw, -hl, 0.0), (hw, -hl, 0.0), (0.0, hl, 0.0)]
            faces = [(0, 1, 2)]

        mesh = bpy.data.meshes.new(name)
        obj  = bpy.data.objects.new(name, mesh)
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        obj.location = (loc.x, loc.y, loc.z)
        bpy.context.collection.objects.link(obj)

        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name="UVMap")

        assign_map_editor_properties(obj)

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({"INFO"}, f"Created {name} ({shape}, {width}x{length})")
        return {"FINISHED"}


class OBJECT_OT_DuplicatePolygon(bpy.types.Operator):
    bl_idname      = "object.duplicate_polygon"
    bl_label       = "Duplicate Polygon"
    bl_description = "Duplicate the selected polygon with a unique bound number and all properties copied"
    bl_options     = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            context.object is not None
            and context.object.type == "MESH"
            and context.object.name.startswith("P")
        )

    def execute(self, context: bpy.types.Context) -> set:
        source  = context.object
        used    = get_used_bound_numbers(context.scene)
        new_num = next_available_bound_number(used)

        bpy.ops.object.duplicate(linked=False)
        new_obj = context.object

        new_obj.name = f"P{new_num}"

        assign_map_editor_properties(new_obj, source=source)
        new_obj.hud_color = source.hud_color

        self.report({"INFO"}, f"Duplicated {source.name} → P{new_num}")
        return {"FINISHED"}
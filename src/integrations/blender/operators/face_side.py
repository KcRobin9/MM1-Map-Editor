import bpy


def _iter_3d_spaces():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        yield space


def _is_active() -> bool:
    for space in _iter_3d_spaces():
        return space.shading.show_backface_culling
    return False


class OBJECT_OT_ToggleGameSidePreview(bpy.types.Operator):
    bl_idname = "object.toggle_game_side_preview"
    bl_label = "Game Side Preview"
    bl_description = (
        "Toggle backface culling and face orientation overlay across all 3D viewports.\n"
        "When ON: only the game collision/render side of each polygon is visible (blue = front, red = back)"
    )

    def execute(self, context):
        spaces = list(_iter_3d_spaces())
        if not spaces:
            self.report({'WARNING'}, "No 3D viewport found")
            return {'CANCELLED'}

        new_state = not spaces[0].shading.show_backface_culling

        for space in spaces:
            space.shading.show_backface_culling = new_state
            space.overlay.show_face_orientation = new_state

        return {'FINISHED'}

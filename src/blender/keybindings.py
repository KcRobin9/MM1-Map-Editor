def create_keybinding(keymap, operator: str, key: str, modifier: Optional[Dict] = None, properties: Optional[Dict[str, Any]] = None) -> None:
    modifier = modifier or {}
    kmi = keymap.keymap_items.new(operator, key, KeyEvent.PRESS, **modifier)
    
    if properties:
        for prop_name, prop_value in properties.items():
            setattr(kmi.properties, prop_name, prop_value)

def setup_export_keybindings(bind_func) -> None:
    bind_func("object.export_polygons", Key.E, KeyModifier.CTRL, {"select_all": False})
    bind_func("object.export_polygons", Key.E, KeyModifier.SHIFT, {"select_all": True})

def setup_extrude_keybindings(bind_func) -> None:
    bind_func("object.process_post_extrude", Key.X, KeyModifier.SHIFT, {"triangulate": False})
    bind_func("object.process_post_extrude", Key.X, KeyModifier.CTRL_SHIFT, {"triangulate": True})

def setup_property_keybindings(bind_func) -> None:
    bind_func("object.assign_custom_properties", Key.P, KeyModifier.SHIFT)

def setup_rename_keybindings(bind_func) -> None:
    bind_func("object.auto_rename_children", Key.Q, KeyModifier.CTRL_SHIFT)
    bind_func("object.rename_sequential", Key.Q, KeyModifier.CTRL_ALT)

def setup_waypoint_creation_keybindings(bind_func) -> None:
    bind_func("create.single_waypoint", Key.Y, KeyModifier.SHIFT)
    bind_func("load.waypoints_from_csv", Key.C, KeyModifier.SHIFT)
    bind_func("load.waypoints_from_race_data", Key.R, KeyModifier.SHIFT)
    bind_func("load.cnr_from_csv", Key.O, KeyModifier.ALT)

def setup_waypoint_export_keybindings(bind_func) -> None:
    bind_func("export.selected_waypoints", Key.W, KeyModifier.SHIFT)
    bind_func("export.selected_waypoints_with_brackets", Key.W, KeyModifier.CTRL)
    bind_func("export.all_waypoints", Key.W, KeyModifier.CTRL_SHIFT)
    bind_func("export.all_waypoints_with_brackets", Key.W, KeyModifier.CTRL_ALT)

def set_blender_keybinding() -> None:
    if not is_process_running(Executable.BLENDER):
        return
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if not kc:
        return
    
    km = kc.keymaps.new(name = "Object Mode", space_type = "EMPTY")
    
    bind = partial(create_keybinding, km)
    
    setup_export_keybindings(bind)
    setup_extrude_keybindings(bind)
    setup_property_keybindings(bind)
    setup_rename_keybindings(bind)
    setup_waypoint_creation_keybindings(bind)
    setup_waypoint_export_keybindings(bind)
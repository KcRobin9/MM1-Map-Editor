# Physics Tutorial

Physics materials control how surfaces behave in your Midtown Madness map - from sticky asphalt to slippery ice. This guide covers customizing physics properties for your custom city.

## Table of Contents
- [Basic Physics Setup](#basic-physics-setup)
- [Creating Material Constants](#creating-material-constants)
- [Using Materials in Polygons](#using-materials-in-polygons)
- [Understanding Parameters](#understanding-parameters)
- [Common Material Types](#common-material-types)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## Basic Physics Setup

Physics materials are defined in `src/USER/physics.py`. You can customize existing material indices (94-98 are available for custom use):

```python
custom_physics = {
    97: {"friction": 1.5, "elasticity": 0.10, "drag": 0.0},  # High-grip surface
    98: {"friction": 0.1, "elasticity": 0.10, "drag": 0.0}   # Slippery surface
}
```

The index number (97, 98) corresponds to the physics material slot you're customizing.

---

## Creating Material Constants

After defining your physics materials, create constants in `src/constants/file_formats.py`:

```python
class Material:
    DEFAULT = 0
    GRASS = 87
    WATER = 91
    RACE_TRACK = 97    # Your custom material at index 97
    ICE = 98           # Your custom material at index 98
```

This allows you to reference your materials by name instead of remembering index numbers.

---

## Using Materials in Polygons

Reference your custom materials when creating polygons:

```python
# High-grip race track section
create_polygon(
    bound_number = 100,
    material_index = Material.RACE_TRACK,  # References index 97
    vertex_coordinates = [
        (0.0, 0.0, 0.0),
        (50.0, 0.0, 0.0),
        (50.0, 0.0, 20.0),
        (0.0, 0.0, 20.0)
    ]
)

# Slippery ice patch
create_polygon(
    bound_number = 101,
    material_index = Material.ICE,  # References index 98
    vertex_coordinates = [
        (60.0, 0.0, 0.0),
        (80.0, 0.0, 0.0),
        (80.0, 0.0, 20.0),
        (60.0, 0.0, 20.0)
    ]
)
```

**Workflow:**
1. Define physics properties in `src/USER/physics.py` with an index (94-98)
2. Add a constant to `Material` class in `src/constants/file_formats.py`
3. Use the constant name in your `create_polygon()` calls

---

## Understanding Parameters

### Parameters That Matter

**`friction`**: Surface grip (higher = more traction)
```python
"friction": 2.0   # High grip (race track)
"friction": 1.0   # Normal road (vanilla default)
"friction": 0.68  # Grass (vanilla)
"friction": 0.1   # Ice/very slippery
```
*Note: the parameters below need more testing*

**`bump_height` + `bump_width`**: Surface roughness
```python
# Smooth (default)
"bump_height": 0.0, "bump_width": 0.05

# Grass (vanilla)
"bump_height": 0.20, "bump_width": 5.0

# Sidewalk (vanilla)
"bump_height": 0.20, "bump_width": 2.0
```

**`type`**: Surface category
```python
"type": 0  # Default (roads, buildings)
"type": 1  # Sidewalk/pedestrian
"type": 2  # Grass/natural terrain
```

**`sound`**: Audio feedback
```python
"sound": 0  # Road sound
"sound": 1  # Sidewalk/concrete
"sound": 2  # Grass/dirt
```

**`sink_depth`**: How deep vehicles sink
```python
"sink_depth": 1.0   # Normal (default)
"sink_depth": 0.5   # Partial sinking (mud)
"sink_depth": 0.0   # No sinking (water)
```

### Parameters That DON'T Matter

Based on analysis of vanilla materials, these are either unused or always constant:

- **`elasticity`**: Always 0.10 in vanilla (changing may cause issues)
- **`drag`**: Always 0.0 in vanilla (appears unused)
- **`bump_depth`**: Always 0.0 in vanilla (appears unused)
- **`velocity`**: **NOT USED** by the game
- **`ptx_color`**: Always (1.0, 1.0, 1.0) in vanilla

---

## Common Material Types

Each example shows both the physics definition and Material constant.

### High-Grip Road
```python
# In src/USER/physics.py
custom_physics = {
    94: {
        "friction": 1.5,
        "elasticity": 0.10,
        "drag": 0.0
    }
}

# In src/constants/file_formats.py
class Material:
    RACE_TRACK = 94
```

### Ice (Very Slippery)
```python
# In src/USER/physics.py
custom_physics = {
    95: {
        "friction": 0.1,
        "elasticity": 0.10,
        "drag": 0.0
    }
}

# In src/constants/file_formats.py
class Material:
    ICE = 95
```

### Rough Terrain / Mud
```python
# In src/USER/physics.py
custom_physics = {
    96: {
        "friction": 0.5,
        "elasticity": 0.10,
        "drag": 0.0,
        "bump_height": 0.30,
        "bump_width": 3.0,
        "sink_depth": 0.5,
        "type": 2,
        "sound": 2
    }
}

# In src/constants/file_formats.py
class Material:
    MUD = 96
```

### Custom Grass
```python
# In src/USER/physics.py
custom_physics = {
    97: {
        "friction": 0.65,
        "elasticity": 0.10,
        "drag": 0.0,
        "bump_height": 0.20,
        "bump_width": 5.0,
        "type": 2,
        "sound": 2
    }
}

# In src/constants/file_formats.py
class Material:
    GRASS_CUSTOM = 97  # Note: GRASS = 87 already exists
```

---

## Troubleshooting

**Physics changes not appearing in-game:**
- Check that `set_physics = True` in your settings
- Verify you're using available indices (94-98)
- Ensure your polygon references the correct physics index

---

## Tips & Best Practices

- **Complete workflow:** Always create both the physics definition AND the Material constant
- **Available indices:** Only 94-98 are available for custom physics
- **Name your materials:** Use descriptive constant names (ICE, MUD, etc.)
- **Stick to vanilla patterns:** Use `elasticity = 0.10, drag = 0.0` unless experimenting
- **Focus on friction:** This is the primary control for surface behavior
- **Test incrementally:** Change one parameter at a time
- **Reference vanilla:** Check indices 87 (grass) and 91 (water) for examples
- **Debug mode:** Enable `debug_physics = True` to see all physics parameters

---

## Need More Help?

- Physics implementation: `src/file_formats/physics.py`
- Your custom physics: `src/USER/physics.py`
- Material constants: `src/constants/file_formats.py`
- Debug output: `debug/PHYSICS/PHYSICS_DB.txt` when debug enabled
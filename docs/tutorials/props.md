# Props Tutorial

Props are physical objects placed in your Midtown Madness map - from cars to trees, trailers, and bridges. This guide covers most you need to know about placing and customizing props in your custom city.

## Table of Contents
- [Basic Prop Placement](#basic-prop-placement)
- [Advanced Placement Techniques](#advanced-placement-techniques)
- [Randomized Props](#randomized-props)
- [Race-Specific Props](#race-specific-props)
- [Customizing Prop Properties](#customizing-prop-properties)
- [Appending Props to Existing Files](#appending-props-to-existing-files)
- [Visual Reference Gallery](#visual-reference-gallery)
- [Troubleshooting](#troubleshooting)

---

## Basic Prop Placement

Props are defined in `src/USER/props/props.py`. The simplest way to place a prop is by specifying its position, face (rotation), and name:
```python
simple_tree = {
    "offset": (60, 0.0, 25),
    "face": (0,0, 0.0, 0),
    "name": Prop.TREE_SLIM
}

prop_list = [simple_tree]
```

**Parameters:**
- `offset`: `(x, y, z)` - The prop's position in 3D space
- `face`: `(x, y, z)` - Direction the prop faces (needs more documentation)
- `name`: The prop's name (see `src.constants.props.py`)

---

## Advanced Placement Techniques

### Line of Props

Place multiple props along a path between two points (horizontal, vertical, diagonal, or any 3D direction):
```python
trailer_line = {
    "offset": (60, 0.0, 10),
    "end": (60, 0.0, 150),
    "name": Prop.TRAILER,
    "separator": 20.0  # Distance between each prop
}
```

The editor automatically calculates how many props fit between `offset` and `end` based on the `separator` distance (in this case: `(150-10)/20 = 7`).

### Auto-Spacing by Dimension

Instead of a fixed separator distance, you can space props based on their actual dimensions:
```python
trailer_line = {
    "offset": (60, 0.0, 10),
    "end": (60, 0.0, 150),
    "name": Prop.TRAILER,  # Dimensions: X: 16.34 Y: 4.69 Z: 4.00
    "separator": Axis.X  # Space by the prop's X dimension (16.34)
}
```

**Available axes:** `Axis.X`, `Axis.Y`, `Axis.Z`

This is particularly useful for props with varying sizes - the editor reads dimensions from `src\Resources\EditorResources\PROPS\prop_dimensions.txt`.

### Facing Direction

Control which way your prop faces:
```python
bridge = {
    "offset": (35, 12.0, -70),
    "face": (35 * HUGE, 12.0, -70),
    "name": Prop.BRIDGE_SLIM
}
```

*TODO: needs more testing and documentation*

---

## Randomized Props

Scatter props randomly within a defined area:
```python
random_trees = {
    "offset_y": 0.0,
    "name": [Prop.TREE_SLIM] * 20  # 20 trees of this type
}

random_props = [
    {
        "seed": 123,           # Random seed for reproducibility
        "num_props": 1,        # Props placed per name in the list
        "props_dict": random_trees,
        "x_range": (65, 135),  # X coordinate range
        "z_range": (-65, 65)   # Z coordinate range
    }
]
```

**How it works:**
1. `num_props = 1` with 20 names = 20 total props placed
2. `num_props = 2` with 20 names = 40 total props placed
3. Each placement uses random coordinates within the specified ranges
4. The `seed` ensures the same random pattern each time

### Multiple Random Sets

You can combine different random prop types:
```python
random_cars = {
    "offset_y": 0.0,
    "separator": 10.0,
    "name": [
        PlayerCar.VW_BEETLE, 
        PlayerCar.CITY_BUS, 
        PlayerCar.MUSTANG99
    ]
}

random_props = [
    {
        "seed": 99, 
        "num_props": 1, 
        "props_dict": random_trees, 
        "x_range": (50, 100), 
        "z_range": (0, 50)
        },
    {
        "seed": 1, 
        "num_props": 2, 
        "props_dict": random_cars, 
        "x_range": (50, 100), 
        "z_range": (-50, 0)
        }
]
```

---

## Race-Specific Props

Place props that only appear during specific races/modes:
```python

# Single race
trash_boxes = {
    "offset": (20, 0.0, 10),
    "face": (0.0, 0.0, 0),
    "name": Prop.TRASH_BOXES,
    "race": RaceModeNum.CIRCUIT_0
}

# Multiple specific races
barriers = {
    "offset": (30, 0.0, 30),
    "name": Prop.BARRICADE,
    "race": [RaceModeNum.CIRCUIT_0, RaceModeNum.BLITZ_1]
}

# All races of one type
cones = {
    "offset": (20, 0.0, 20),
    "name": Prop.BRIDGE_SLIM,
    "race": RaceModeNum.CHECKPOINT_ALL  # Appears in all checkpoint races
}
```

**Available race modes:**
- Individual: `CIRCUIT_0`, `CIRCUIT_1`, `CHECKPOINT_0`, `BLITZ_0`, etc.
- All of type: `CIRCUIT_ALL`, `CHECKPOINT_ALL`, `BLITZ_ALL`

---

## Customizing Prop Properties

Modify prop's physical properties in `src/USER/props/properties.py`:
```python
prop_properties = {
    PlayerCar.VW_BEETLE: {
        "ImpulseLimit2": HUGE,      # Indestructible
        "AudioId": AudioProp.GLASS  # Glass breaking sound
    },
    
    PlayerCar.CITY_BUS: {
        "ImpulseLimit2": 50,  # Easier to destroy
        "Mass": 50,           # Lighter than default
        "AudioId": AudioProp.POLE,
        "Size": "18 6 5",     # Collision box dimensions
        "CG": "0 0 0"         # Center of gravity
    }
}
```
For a complete list of available properties, see the `PlayerCar.ROADSTER` example in `properties.py`.

*TODO: needs more testing and documentation*

---

## Appending Props to Existing Files

Add props to an existing `.BNG` file without recreating it.

In `src/USER/props/append_to_file.py`:
```python
append_props = True

append_input_props_file = Folder.EDITOR_RESOURCES / "PROPS" / "CHICAGO.BNG"

append_output_props_file = Folder.USER_RESOURCES / "PROPS" / "MODIFIED_CHICAGO.BNG"

app_panoz = {
    'offset': (5, 2, 5),
    'end': (999, 2, 999),
    'name': PlayerCar.PANOZ_GTR_1
}

props_to_append = [app_panoz]
```

This creates a new file with all original props plus your additions.

*TODO: needs more testing and documentation*

---

## Visual Reference Gallery

The most common props are documented with images in `docs/visual_reference/props/`.

---

## Troubleshooting

**Props not appearing in-game:**
- Check that `set_props = True` in your settings
- Ensure coordinates are within your map bounds

**Props floating or underground:**
- Adjust the Y coordinate in `offset`
- Check terrain height at placement location
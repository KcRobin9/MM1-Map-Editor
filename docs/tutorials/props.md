# Props Tutorial

Props are physical objects placed in your Midtown Madness map - from cars to trees, trailers, and bridges. This guide covers most you need to know about placing and customizing props in your custom city.

## Table of Contents
- [Basic Prop Placement](#basic-prop-placement)
- [Advanced Placement Techniques](#advanced-placement-techniques)
- [Randomized Props](#randomized-props)
- [Race-Specific Props](#race-specific-props)
- [Customizing Prop Properties](#customizing-prop-properties)
- [Modifying Existing Prop Files](#modifying-existing-prop-files)
  - [Subtracting Props](#subtracting-props)
  - [Editing Props](#editing-props)
  - [Replacing Props](#replacing-props)
  - [Duplicating Props](#duplicating-props)
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

## Modifying Existing Prop Files

The editor provides tools to modify existing `.BNG` prop files (like the original Chicago). This is useful when you want to customize an existing map rather than building from scratch.

All modification operations share the same filtering system to select which props to affect.

### Filtering Props

Before modifying props, you need to specify which ones to target. **Filters work independently** - you can use any single filter or combine multiple filters.

| Filter | Description | Example |
|--------|-------------|---------|
| `name` | Match by prop type | `"name": Prop.TRAILER` |
| `id` | Match single prop by its index in the file | `"id": 5591` |
| `ids` | Match multiple specific indices | `"ids": [100, 101, 102]` |
| `id_min`, `id_max` | Match a range of indices | `"id_min": 100, "id_max": 200` |
| `offset` | Match by position (with tolerance) | `"offset": (150.5, 0, -220.3)` |
| `offset_min`, `offset_max` | Match props within a bounding box | `"offset_min": (0, 0, 0), "offset_max": (100, 50, 100)` |
| `end`, `separator` | Match a line of props | `"offset": (100, 0, 100), "end": (100, 0, 200), "separator": 10` |

**Filter examples:**

```python
# Match ALL trailers (just name)
{"name": Prop.TRAILER}

# Match prop at index 5591 regardless of type (just id)
{"id": 5591}

# Match ALL props in an area (just position)
{"offset_min": (0, 0, 0), "offset_max": (100, 50, 100)}

# Match only trailers in a specific area (combined)
{"name": Prop.TRAILER, "offset_min": (0, 0, 0), "offset_max": (100, 50, 100)}

# Match trailer #5591 specifically (combined - more restrictive)
{"name": Prop.TRAILER, "id": 5591}
```

---

### Subtracting Props

Remove props from an existing file. Configure in `src/USER/props/subtract.py`:

```python
subtract_props = True
subtract_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO.BNG"
subtract_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_CLEANED.BNG"

# Remove a specific prop by ID
remove_by_id = {
    "name": Prop.TRAILER,
    "id": 5591,
}

# Remove all props in an area
clear_area = {
    "offset_min": (300, 0, 300),
    "offset_max": (350, 10, 400),
}

# Remove a line of barricades
remove_barricade_line = {
    "name": Prop.BARRICADE,
    "offset": (322, 0, 387),
    "end": (322, 0, 317),
    "separator": 4,
}

props_to_subtract = [remove_by_id, clear_area]
ranges_to_subtract = [remove_barricade_line]
```

When you run the editor, it will show matched props and ask for confirmation before removing.

---

### Editing Props

Modify props in place - move them, change their facing, adjust height. Configure in `src/USER/props/edit.py`:

```python
edit_props = True
edit_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO.BNG"
edit_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_EDITED.BNG"

props_to_edit = [
    # ... your edit rules here
]
```

**Available transforms:**

#### Moving Props

```python
# Move props by a delta (relative movement)
{
    "name": Prop.TRAILER,
    "id": 5591,
    "translate": (10, 0, 5),  # Move 10 units on X, 5 on Z
}

# Set absolute position
{
    "name": Prop.BARRICADE,
    "offset": (100, 0, 100),      # Find prop at this location
    "set_offset": (150, 0, 150),  # Move it here
}

# Adjust height only
{
    "name": Prop.TREE_SLIM,
    "add_offset_y": 2.0,  # Raise all trees by 2 units
}

# Set all props to ground level
{
    "offset_min": (0, -100, 0),
    "offset_max": (500, 100, 500),
    "set_offset_y": 0.0,  # Set Y to exactly 0
}
```

#### Changing Facing Direction

```python
# Set facing direction
{
    "name": Prop.BARRICADE,
    "offset": (322, 0, 387),
    "set_face": (1.0, 0.0, 0.0),  # Face along X axis
}
```

#### Mirroring Props

Mirror props across an axis - useful for creating symmetric maps:

```python
# Mirror props across X axis (left-right)
{
    "name": Prop.TREE_SLIM,
    "offset_min": (0, 0, 0),
    "offset_max": (100, 50, 100),
    "mirror_x": True,
    "mirror_x_pivot": 50.0,  # Mirror around X=50
}

# Mirror props across Z axis (front-back)
{
    "name": Prop.BARRICADE,
    "mirror_z": True,
    "mirror_z_pivot": 0.0,  # Mirror around Z=0
}
```

**How mirroring works:**
- `mirror_x` reflects the prop's X position around the pivot point
- A prop at X=30 with pivot=50 moves to X=70 (same distance from pivot, opposite side)
- The prop's facing direction is also flipped

---

### Replacing Props

Swap one prop type for another throughout the file. Configure in `src/USER/props/replace.py`:

```python
replace_props = True
replace_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO.BNG"
replace_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_REPLACED.BNG"

props_to_replace = [
    # Replace all slim trees with wide trees
    {
        "name": Prop.TREE_SLIM,
        "replace_with": Prop.TREE_WIDE,
    },
    
    # Replace barricades in a specific area with cones
    {
        "name": Prop.BARRICADE,
        "offset_min": (100, 0, 100),
        "offset_max": (200, 50, 200),
        "replace_with": Prop.CONE,
    },
    
    # Replace a specific prop by ID
    {
        "name": Prop.TRAILER,
        "id": 5591,
        "replace_with": Prop.SAILBOAT,
    },
]
```

---

### Duplicating Props

Copy existing props and apply transformations to the copies. The original props remain unchanged. Configure in `src/USER/props/duplicate.py`:

```python
duplicate_props = True
duplicate_input_props_file = Folder.RESOURCES_EDITOR / "PROPS" / "CHICAGO.BNG"
duplicate_output_props_file = Folder.RESOURCES_USER / "PROPS" / "CHICAGO_DUPLICATED.BNG"

props_to_duplicate = [
    # Duplicate a trailer and offset the copy
    {
        "name": Prop.TRAILER,
        "id": 5591,
        "translate": (50, 0, 0),  # Copy will be 50 units away on X
    },
    
    # Duplicate all trees in an area and mirror them
    {
        "name": Prop.TREE_SLIM,
        "offset_min": (0, 0, 0),
        "offset_max": (100, 50, 100),
        "mirror_x": True,
        "mirror_x_pivot": 50.0,
    },
    
    # Duplicate and change prop type
    {
        "name": Prop.BARRICADE,
        "id_min": 100,
        "id_max": 150,
        "translate": (0, 0, 100),
        "set_name": Prop.CONE,  # Copies become cones
    },
]
```

**Use cases:**
- Creating symmetric maps by duplicating and mirroring one half
- Adding variations of existing prop arrangements
- Testing different prop configurations without losing the original

---

### Analyzing Prop Files

To understand what's in an existing BNG file, you can use the statistics function:

```python
from src.file_formats.props import Bangers, print_statistics

with open("path/to/CHICAGO.BNG", "rb") as f:
    props = Bangers.read_all(f)

print_statistics(props)
```

This outputs:
```
Prop Statistics:
  Total count: 5847
  Unique types: 42
  Bounds min: (-1200.50, -5.00, -1500.25)
  Bounds max: (1180.00, 45.00, 1420.75)
  Center: (-10.25, 20.00, -39.75)
  
  Type breakdown:
    tp_tree10m: 892
    tp_barricade: 456
    tp_trailer: 234
    ...
```

---

## Appending Props to Existing Files

Add props to an existing `.BNG` file without recreating it.

In `src/USER/props/append.py`:
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

**Edit/Replace/Subtract not finding props:**
- Check that `tolerance` is appropriate (default 0.25 units)
- Use `print_statistics()` to verify the prop exists in the file
- Verify prop name matches exactly (check `src/constants/props.py`)

**Confirmation prompt annoying:**
- Set `require_confirmation = False` in the config file to skip prompts
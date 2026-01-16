# Facades Tutorial

Facades are the building exteriors in your Midtown Madness map - storefronts, office buildings, walls, and architectural elements that create your city's skyline. This guide covers placing and customizing facades in your custom city.

## Table of Contents
- [Basic Facade Placement](#basic-facade-placement)
- [Understanding Parameters](#understanding-parameters)
- [Facade Flags (Visibility & Lighting)](#facade-flags-visibility--lighting)
- [Building Complex Structures](#building-complex-structures)
- [Visual Reference Gallery](#visual-reference-gallery)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## Basic Facade Placement

Facades are defined in `src/USER/facades.py`. A facade requires start and end positions, the axis to build along, and spacing between segments:

```python
simple_wall = {
    "flags": FcdFlags.FRONT,
    "offset": (0.0, 0.0, 0.0),
    "end": (50.0, 0.0, 0.0),
    "separator": 10.0,
    "name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "x"
}

facade_list = [simple_wall]
```

This creates 5 facade segments along the X-axis from (0, 0, 0) to (50, 0, 0), spaced 10 units apart.

---

## Understanding Parameters

### Required Parameters

**`offset`**: `(x, y, z)` - Starting position
```python
"offset": (10.0, 0.0, 25.0)
```

**`end`**: `(x, y, z)` - Ending position
```python
"end": (60.0, 0.0, 25.0)
```

**`axis`**: `"x"`, `"y"`, or `"z"` - Direction to build along
```python
"axis": "x"  # Builds along the X-axis
```

**`separator`**: Spacing between facade segments
```python
"separator": 10.0  # Each segment is 10 units apart
```

**`name`**: The facade type - use `Facade.{autofill}` in Visual Studio Code to see all available options
```python
"name": Facade.BUILDING_ORANGE_WITH_WINDOWS
```
See `src/constants/facades.py` for the complete list.

**`flags`**: Controls visibility - use `FcdFlags.{autofill}` in Visual Studio Code to see all available options
```python
"flags": FcdFlags.FRONT_BRIGHT
```
### Optional Parameters

**`scale`**: Override default facade size
```python
"scale": 1.5  # 50% larger than default
```
Default scales are in `src/Resources/EditorResources/FACADES/FCD scales.txt`

*Note: `scale` and `sides` parameters need more testing and documentation*

---

## Facade Flags (Visibility & Lighting)

Flags control which sides of a facade are rendered and how they're lit.

### Common Flags

```python
# Single-sided
FcdFlags.FRONT              # Front face only
FcdFlags.FRONT_BRIGHT       # Front face with enhanced lighting

# Two-sided
FcdFlags.FRONT_LEFT         # Front and left visible
FcdFlags.FRONT_RIGHT        # Front and right visible
FcdFlags.FRONT_BACK         # Front and back visible
FcdFlags.FRONT_ROOFTOP      # Front with rooftop

# Three-sided
FcdFlags.FRONT_LEFT_RIGHT   # Front, left, and right

# All sides
FcdFlags.ALL_SIDES          # Visible from any angle
```

### When to Use Each Flag

- **Street-facing buildings:** `FcdFlags.FRONT_BRIGHT` - Highlights the main facade
- **Corner buildings:** `FcdFlags.FRONT_LEFT_RIGHT` - Shows multiple sides
- **Free-standing buildings:** `FcdFlags.ALL_SIDES` - Visible from anywhere

---

## Building Complex Structures

### Example: City Block

Create a rectangular building with four walls:

```python
# North wall (along X-axis)
north_wall = {
    "flags": FcdFlags.FRONT_BRIGHT,
    "offset": (-10.0, 0.0, -50.0),
    "end": (10.0, 0.0, -50.0),
    "separator": 10.0,
    "name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "x"
}

# South wall (opposite direction)
south_wall = {
    "flags": FcdFlags.FRONT_BRIGHT,
    "offset": (10.0, 0.0, -70.0),
    "end": (-10.0, 0.0, -70.0),
    "separator": 10.0,
    "name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "x"
}

# West wall (along Z-axis)
west_wall = {
    "flags": FcdFlags.FRONT_BRIGHT,
    "offset": (-10.0, 0.0, -70.0),
    "end": (-10.0, 0.0, -50.0),
    "separator": 10.0,
    "name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "z"
}

# East wall (along Z-axis)
east_wall = {
    "flags": FcdFlags.FRONT_BRIGHT,
    "offset": (10.0, 0.0, -50.0),
    "end": (10.0, 0.0, -70.0),
    "separator": 10.0,
    "name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "z"
}

facade_list = [north_wall, south_wall, west_wall, east_wall]
```

### Example: Varied Storefronts

Mix different facade types along a street:

```python
storefront_a = {
    "flags": FcdFlags.FRONT_BRIGHT,
    "offset": (0.0, 0.0, 0.0),
    "end": (30.0, 0.0, 0.0),
    "separator": 10.0,
    "name": Facade.SHOP_LIQUOR,
    "axis": "x"
}

storefront_b = {
    "flags": FcdFlags.FRONT_BRIGHT,
    "offset": (30.0, 0.0, 0.0),
    "end": (60.0, 0.0, 0.0),
    "separator": 10.0,
    "name": Facade.SHOP_PIZZA,
    "axis": "x"
}

facade_list = [storefront_a, storefront_b]
```

### Example: Tall Building

Build vertically along the Y-axis:

```python
tall_building = {
    "flags": FcdFlags.FRONT,
    "offset": (20.0, 0.0, 30.0),
    "end": (20.0, 50.0, 30.0),
    "separator": 10.0,
    "name": Facade.BUILDING_ORANGE_WITH_WINDOWS,
    "axis": "y"
}

facade_list = [tall_building]
```

---

## Visual Reference Gallery

All available facades are documented with images in `docs/visual_reference/facades/`.

---

## Troubleshooting

**Facades not appearing in-game:**
- Check that `set_facades = True` in your settings
- Verify coordinates are within your map bounds
- Ensure `facade_list` contains your definitions

**Facades facing the wrong direction:**
- The `axis` parameter determines the build direction
- Ensure `offset` and `end` differ on the correct coordinate
- Example: `"axis": "x"` requires different X values in `offset` and `end`

---

## Tips & Best Practices

- **Use Visual Studio Code autocomplete:** Type `Facade.` or `FcdFlags.` to see all available options
- **Start simple:** Build one wall at a time
- **Keep spacing consistent:** Same `separator` values create uniform buildings
- **Plan visibility:** Consider which sides players will see
- **Match corners exactly:** Precise coordinates prevent gaps
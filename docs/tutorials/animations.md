# Animations Tutorial

Animations bring life to your Midtown Madness map with moving objects such as planes and elevated trains. This guide covers setting up animated elements that follow custom paths through your city.

## Table of Contents
- [Basic Animation Setup](#basic-animation-setup)
- [Understanding Parameters](#understanding-parameters)
- [Creating Flight Paths](#creating-flight-paths)
- [Available Animation Types](#available-animation-types)
- [Combining Animations](#combining-animations)
- [Troubleshooting](#troubleshooting)

---

## Basic Animation Setup

Animations are defined in `src/USER/animations.py`. Each animation type requires a list of coordinates that define its path:

```python
animations_data = {
    Anim.PLANE: [
        (450, 30.0, -450),    # Starting position (x, y, z)
        (450, 30.0, 450),     # Waypoint 1
        (-450, 30.0, -450),   # Waypoint 2
        (-450, 30.0, 450)     # Waypoint 3
    ]
}
```

The animated object will continuously loop through these coordinates in order.

---

## Understanding the Parameters

### Coordinate Format

Each waypoint is a tuple of three values:

```python
(x, y, z)
```

- **`x`**: East-West position
- **`y`**: Height/altitude
- **`z`**: North-South position

### Path Behavior

- The object moves from point to point in the order listed
- After reaching the last coordinate, it returns to the first (continuous loop)
- Movement speed is determined by the game engine (cannot be customized)

---

## Creating Flight Paths

Animations follow waypoints in sequence, creating a continuous loop:

```
     2 ----→ 3
     ↑       ↓
     1 ←---- 4
```

### Simple Circular Path

Create a square flight pattern around your city:

```python
animations_data = {
    Anim.PLANE: [
        (200, 100.0, 200),     # Northeast corner
        (-200, 100.0, 200),    # Northwest corner
        (-200, 100.0, -200),   # Southwest corner
        (200, 100.0, -200),    # Southeast corner
        (200, 100.0, 200)      # Return to start for smooth loop
    ]
}
```

**Note:** The last coordinate should match the first for seamless looping.

### Elevated Train Route

Create a train path at elevated track height:

```python
animations_data = {
    Anim.ELTRAIN: [
        (150, 12.0, -150),    # Station 1
        (150, 12.0, 150),     # Station 2
        (-150, 12.0, 150),    # Station 3
        (-150, 12.0, -150),   # Station 4
        (150, 12.0, -150)     # Return to start
    ]
}
```

---

## Available Animation Types

There are two animation types available:

### Plane
```python
Anim.PLANE
```
**Recommended settings:**
- Y coordinate (height): 80.0 - 120.0 for realistic altitude (Chicago uses 95.0 - 115.0)
- Path coverage: Extend beyond map boundaries for smooth entry/exit

### Elevated Train (L-Train)
```python
Anim.ELTRAIN
```
**Recommended settings:**
- Y coordinate (height): 10.0 - 15.0 to match track height (Chicago uses 12.0)
- Align coordinates with your track infrastructure

---

## Combining Animations

You can have **both** a plane and a train simultaneously:

```python
animations_data = {
    Anim.PLANE: [
        (450, 30.0, -450),
        (450, 30.0, 450),
        (-450, 30.0, -450),
        (-450, 30.0, 450),
        (450, 30.0, -450)     # Close the loop
    ],
    Anim.ELTRAIN: [
        (180, 25.0, -180),
        (180, 25.0, 180),
        (-180, 25.0, -180),
        (-180, 25.0, 180),
        (180, 25.0, -180)     # Close the loop
    ]
}
```

**Important:** You cannot have multiple instances of the same animation type unfortunately (e.g., two planes).

---

## Real-World Example: Chicago

Here's how the vanilla Chicago map defines its animations:

### Chicago Plane Path
```python
Anim.PLANE: [
    (1050.85, -0.00126445, 1180.85),
    (1050.85, -0.00103345, 960.349),
    (1049.17, 94.29, 109.849),
    (1007.17, 115.5, -436.15),
    (513.671, 115.5, -1192.15),
    (-168.828, 115.5, -1454.65),
    (-620.327, 115.5, -1360.15),
    (-956.327, 115.5, -992.648),
    (-1103.33, 115.5, -215.649),
    (-1061.33, 115.5, 655.849),
    (-872.327, 115.499, 876.349),
    (-473.327, 115.499, 1317.35),
    (461.172, 115.499, 1674.35),
    (836.02, 94.6045, 1695.34),
    (1016.93, 43.7832, 1443.34),
    (1050.85, -0.00126445, 1180.85)
]
```

The plane starts low, climbs to cruise altitude (115.5), circles the entire city, then descends for landing.

### Chicago El Train Path
```python
Anim.ELTRAIN: [
    (162.327, 12.0004, -188.787),
    (162.336, 12.0003, -159.618),
    (162.342, 12.0003, -143.211),
    # ... (70+ waypoints total)
    (159.128, 12.0004, -200.998),
    (162.327, 12.0004, -188.787)
]
```

The elevated train uses many closely-spaced waypoints to follow the curved track structure at a constant height of ~12.0. This creates smooth, realistic movement along the rails.

**Key takeaways:**
- Planes can vary altitude for takeoff/landing effects
- Trains maintain consistent height
- More waypoints = smoother curves
- Closing the loop (final = first coordinate) ensures seamless transitions

---

## Troubleshooting

**Animations not appearing in-game:**
- Check that `set_anim = True` in your settings
- Verify coordinates are within reasonable bounds of your map
- Ensure you haven't defined multiple animations of the same type

**Path seems erratic:**
- Check that coordinates progress logically
- Ensure waypoints aren't too far/close apart
- Verify all coordinates use consistent Y values for level flight
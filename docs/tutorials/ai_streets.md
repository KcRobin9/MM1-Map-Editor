# AI Streets Tutorial

AI streets define the road network that controls traffic behavior, police pathfinding, and opponent routing in your Midtown Madness map. This guide covers creating functional street networks with proper intersections, traffic controls, and multi-lane configurations.

## Table of Contents
- [Basic Street Setup](#basic-street-setup)
- [Understanding Street Parameters](#understanding-street-parameters)
- [Multi-Lane Streets](#multi-lane-streets)
- [Intersections & Traffic Control](#intersections--traffic-control)
- [Bidirectional Streets](#bidirectional-streets)
- [Real-World Example](#real-world-example)
- [Street Network Design](#street-network-design)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## Basic Street Setup

AI streets are defined in `src/USER/ai_streets.py`. The simplest street requires only a name and a list of vertices:

```python
simple_street = {
    "street_name": "main_road",
    "vertices": [
        (0.0, 0.0, 100.0),   # Start point (x, y, z)
        (0.0, 0.0, 50.0),    # Waypoint 1
        (0.0, 0.0, 0.0),     # Waypoint 2
        (0.0, 0.0, -50.0)    # End point
    ]
}

street_list = [simple_street]
```

This creates a single-lane, one-way street running north to south. Vehicles will drive from the first vertex toward the last vertex.

---

## Understanding Street Parameters

### Required Parameters

**`street_name`**: Unique identifier for the street
```python
"street_name": "downtown_main"
```
Names must be unique across your entire street network.

**`vertices`** OR **`lanes`**: Defines the street path
```python
# Simple single-lane (vertices)
"vertices": [
    (x, y, z),
    (x, y, z),
    ...
]

# Multi-lane (lanes)
"lanes": {
    "lane_1": [(x, y, z), ...],
    "lane_2": [(x, y, z), ...]
}
```

---

### Optional Parameters

All optional parameters have sensible defaults:

**`intersection_types`**: Controls intersection behavior at start/end
```python
"intersection_types": [IntersectionType.STOP_LIGHT, IntersectionType.CONTINUE]
```
Default: `[IntersectionType.CONTINUE, IntersectionType.CONTINUE]`

Available types:
- `IntersectionType.STOP` - Stop sign (requires full stop)
- `IntersectionType.STOP_LIGHT` - Traffic light
- `IntersectionType.YIELD` - Yield
- `IntersectionType.CONTINUE` - No control (default)

**`stop_light_names`**: Visual stop light/sign models
```python
"stop_light_names": [Prop.STOP_LIGHT_DUAL, Prop.STOP_SIGN]
```
Default: `[Prop.STOP_LIGHT_SINGLE, Prop.STOP_LIGHT_SINGLE]`

Available props:
- `Prop.STOP_SIGN` - Physical stop sign
- `Prop.STOP_LIGHT_SINGLE` - Single traffic light
- `Prop.STOP_LIGHT_DUAL` - Dual traffic light

**`stop_light_positions`**: Exact placement of traffic controls
```python
"stop_light_positions": [
    (10.0, 0.0, 100.0),      # Position 1
    (10.01, 0.0, 100.0),     # Direction 1
    (-10.0, 0.0, 100.0),     # Position 2
    (-10.0, 0.0, 100.1)      # Direction 2
]
```
Default: `[(0.0, 0.0, 0.0)] * 4` (placed at origin)

Format: Two sets of position + direction coordinates (4 total).

**`traffic_blocked`**: Prevents traffic on this street
```python
"traffic_blocked": [YES, NO]  # Block start, allow end
```
Default: `[NO, NO]`

**`ped_blocked`**: Prevents pedestrians on this street
```python
"ped_blocked": [NO, YES]  # Allow start, block end
```
Default: `[NO, NO]`

**`road_divided`**: Creates divided highway (median)
```python
"road_divided": YES
```
Default: `NO`

*TODO: needs more testing and documentation*

**`alley`**: Marks street as narrow alley
```python
"alley": YES
```
Default: `NO`

*TODO: needs more testing and documentation*

---

## Multi-Lane Streets

Create streets with multiple parallel lanes using the `lanes` dictionary:

```python
highway = {
    "street_name": "highway_north",
    "lanes": {
        "lane_1": [
            (0.0, 0.0, 100.0),
            (0.0, 0.0, 50.0),
            (0.0, 0.0, 0.0)
        ],
        "lane_2": [  # 5 units to the right
            (5.0, 0.0, 100.0),
            (5.0, 0.0, 50.0),
            (5.0, 0.0, 0.0)
        ],
        "lane_3": [  # 10 units to the right
            (10.0, 0.0, 100.0),
            (10.0, 0.0, 50.0),
            (10.0, 0.0, 0.0)
        ]
    }
}
```

**Note:** All lanes must have the same number of vertices and generally should run parallel to each other.

### Lane Naming

Lane dictionary keys can be anything - they're only used internally:
```python
"lanes": {
    "fast_lane": [...],
    "slow_lane": [...],
    "exit_lane": [...]
}
```

The order of lanes in the dictionary determines their in-game arrangement/priority.

---

## Intersections & Traffic Control

Control how traffic vehicles behave at street endpoints using intersection parameters.

### Stop Sign Intersection

```python
four_way_stop = {
    "street_name": "residential",
    "vertices": [
        (0.0, 0.0, 50.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, -50.0)
    ],
    "intersection_types": [IntersectionType.STOP, IntersectionType.STOP],
    "stop_light_names": [Prop.STOP_SIGN, Prop.STOP_SIGN],
    "stop_light_positions": [
        (3.0, 0.0, 45.0),      # Sign position (start)
        (3.0, 0.0, 44.9),      # Sign direction
        (3.0, 0.0, -45.0),     # Sign position (end)
        (3.0, 0.0, -44.9)      # Sign direction
    ]
}
```

### Traffic Light Intersection

```python
major_intersection = {
    "street_name": "main_street",
    "vertices": [
        (100.0, 0.0, 0.0),
        (50.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (-50.0, 0.0, 0.0)
    ],
    "intersection_types": [
        IntersectionType.STOP_LIGHT, 
        IntersectionType.STOP_LIGHT
    ],
    "stop_light_names": [
        Prop.STOP_LIGHT_DUAL, 
        Prop.STOP_LIGHT_DUAL
    ],
    "stop_light_positions": [
        (105.0, 0.15, 5.0),    # Light position (start)
        (104.0, 0.15, 5.0),    # Light facing direction
        (-55.0, 0.15, 5.0),    # Light position (end)
        (-54.0, 0.15, 5.0)     # Light facing direction
    ]
}
```

### Understanding Intersection Arrays

Most intersection parameters use 2-element arrays representing `[start_intersection, end_intersection]`:

```python
"intersection_types": [
    IntersectionType.STOP,      # Control at first vertex
    IntersectionType.CONTINUE   # Control at last vertex
]

"traffic_blocked": [
    YES,  # Block traffic entering from start
    NO    # Allow traffic entering from end
]
```

---

## Bidirectional Streets

Enable two-way traffic with the `set_reverse_ai_streets` setting:

```python
# In src/USER/settings/ai.py
set_reverse_ai_streets = True
```

When enabled, the editor automatically creates reverse lanes for every street:

```python
# Your definition
two_way_road = {
    "street_name": "city_avenue",
    "vertices": [
        (0.0, 0.0, 100.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, -100.0)
    ]
}

# Automatically becomes (internally):
# Lane 1: (100 → 0 → -100)  [Your original]
# Lane 2: (-100 → 0 → 100)  [Auto-generated reverse]
```

**How it works:**
1. Original vertices are used for forward direction
2. Reversed vertices create the return path
3. Both directions share the same intersection controls
4. Traffic flows both ways on the same street (they may collide)

**When to use:**
- Residential streets
- Downtown areas
- Any road where traffic goes both directions

**When NOT to use:**
- Highways (use separate streets for each direction)
- One-way downtown streets
- Race-specific paths

---

## Real-World Example

```python
double_triangle = {
    "street_name": "double_triangle",
    "vertices": [
        (40.0, 0.0, 100.0),        # Start
        (-50.0, 0.0, 135.0),       # Curve point 1
        (-59.88, 3.04, 125.52),    # Elevated section begins
        (-84.62, 7.67, 103.28),    # Peak of hill
        (-89.69, 8.62, 62.57),     # Descending
        (-61.94, 3.42, 32.00),     # Back to ground level
        (-20, 0.0, 70.0),          # Curve point 2
        (0.0, 0.0, 77.5)           # Connects to main_west
    ]
}
```

**Design features:**
- Gradual Y-coordinate changes create hills
- Curved path (X/Z coordinates change non-linearly)
- 8 vertices provide smooth curvature
- Connects to another street network at endpoint

---

## Street Network Design

### Creating Connected Networks

Streets connect at intersections when their endpoints share the same coordinates:

```python
# Street 1 ends at (0, 0, 0)
main_street = {
    "street_name": "main",
    "vertices": [
        (100.0, 0.0, 0.0),
        (50.0, 0.0, 0.0),
        (0.0, 0.0, 0.0)  # Intersection point
    ]
}

# Street 2 starts at (0, 0, 0) - they connect!
side_street = {
    "street_name": "side",
    "vertices": [
        (0.0, 0.0, 0.0),   # Same intersection point
        (0.0, 0.0, -50.0),
        (0.0, 0.0, -100.0)
    ]
}
```

**Critical:** Coordinates must match **exactly** for streets to connect. Even `0.01` difference may creates separate, disconnected intersections.

---

## Complete Street Example

Here's a fully-configured street using all optional parameters:

```python
downtown_boulevard = {
    "street_name": "downtown_blvd",
    
    # Two parallel lanes
    "lanes": {
        "lane_1": [
            (0.0, 0.0, 150.0),
            (0.0, 0.0, 100.0),
            (0.0, 0.0, 50.0),
            (0.0, 0.0, 0.0)
        ],
        "lane_2": [
            (5.0, 0.0, 150.0),
            (5.0, 0.0, 100.0),
            (5.0, 0.0, 50.0),
            (5.0, 0.0, 0.0)
        ]
    },
    
    # Traffic lights at both ends
    "intersection_types": [
        IntersectionType.STOP_LIGHT,
        IntersectionType.STOP_LIGHT
    ],
    
    # Dual traffic lights (two-way intersection)
    "stop_light_names": [
        Prop.STOP_LIGHT_DUAL,
        Prop.STOP_LIGHT_DUAL
    ],
    
    # Precise light placement
    "stop_light_positions": [
        (8.0, 0.15, 155.0),    # Start position
        (8.0, 0.15, 154.0),    # Start direction
        (8.0, 0.15, -5.0),     # End position
        (8.0, 0.15, -4.0)      # End direction
    ],
    
    # Allow traffic, block pedestrians
    "traffic_blocked": [NO, NO],
    "ped_blocked": [YES, YES],
    
    # Not divided, not an alley
    "road_divided": NO,
    "alley": NO
}

street_list = [downtown_boulevard]
```

---

## Troubleshooting

### Streets not appearing in-game

**Check your settings:**
- Verify `set_ai_streets = True` in `src/USER/settings/ai.py`
- Ensure streets are added to `street_list`
- Confirm `.road` files were generated in `MidtownMadness/dev/CITY/{MAP_FILENAME}/`

**Check the output:**
```
Successfully created 5 AI street file(s)
---streets names: main_west, highway_north, downtown_blvd, residential, side_street
```

If you don't see this message, the streets weren't processed.

---

### Traffic not using streets

**Common issues:**
1. **Disconnected intersections:** Street endpoints must match exactly
   ```python
   # Wrong - off by 0.01
   street_a: [(0.0, 0.0, 0.0)]      # End point
   street_b: [(0.01, 0.0, 0.0)]     # Start point
   
   # Correct
   street_a: [(0.0, 0.0, 0.0)]      # End point
   street_b: [(0.0, 0.0, 0.0)]      # Start point
   ```

2. **Blocked traffic:** Check `traffic_blocked` isn't set to `YES`

3. **Isolated network:** Street must connect to at least one other street

---

### Stop lights not showing

**Verify:**
- `intersection_type` is set to `IntersectionType.STOP_SIGN` or `IntersectionType.STOP_LIGHT`
- `stop_light_positions` are within your map bounds
- `stop_light_names` uses valid prop names

**Example fix:**
```python
# Not working - wrong intersection type
"intersection_types": [IntersectionType.CONTINUE, IntersectionType.CONTINUE]

# Working - correct type
"intersection_types": [IntersectionType.STOP_LIGHT, IntersectionType.STOP_LIGHT]
```

---

### Reverse streets not working

**Check setting:**
```python
# In src/USER/settings/ai.py
set_reverse_ai_streets = True  # Must be True
```

**Verify in console:**
```
Successfully created 3 AI street file(s)
```
With `set_reverse_ai_streets = True`, you should see traffic going both directions.

---

### Lane count mismatch errors

**All lanes must have same vertex count:**
```python
# Wrong - mismatched counts
"lanes": {
    "lane_1": [(0, 0, 100), (0, 0, 0)],           # 2 vertices
    "lane_2": [(5, 0, 100), (5, 0, 50), (5, 0, 0)] # 3 vertices ❌
}

# Correct - matching counts
"lanes": {
    "lane_1": [(0, 0, 100), (0, 0, 50), (0, 0, 0)],  # 3 vertices
    "lane_2": [(5, 0, 100), (5, 0, 50), (5, 0, 0)]   # 3 vertices ✓
}
```

---

## Tips & Best Practices

### Network Design

**Plan intersections first:** Design your intersection points before creating streets
```python
# Define key intersections
intersections = {
    "downtown_center": (0, 0, 0),
    "east_plaza": (200, 0, 0),
    "north_station": (0, 0, 200)
}

# Build streets connecting them
main_street = {
    "vertices": [
        intersections["downtown_center"],
        # ... waypoints ...
        intersections["east_plaza"]
    ]
}
```

**Avoid dead ends:** Every street should connect to at least one other street (unless intentionally creating a dead-end alley)

**Test connectivity:** Drive the network in-game to verify AI can navigate properly

---

### Naming Conventions

**Use descriptive names:**
```python
# Good
"street_name": "downtown_main_street"
"street_name": "highway_101_northbound"
"street_name": "residential_oak_avenue"

# Less helpful
"street_name": "street1"
"street_name": "road_abc"
```

**Consistent prefixes for related streets:**
```python
"highway_north_lane1"
"highway_north_lane2"
"highway_south_lane1"
"highway_south_lane2"
```

---

### Debug and Testing

**Enable debug output** in `src/USER/settings/debug.py`:
```python
set_debug_ai = True
```

This generates detailed `.road` and `.int` files in `debug/AI/` showing:
- Exact vertex positions
- Intersection connections
- Lane configurations
- Traffic control settings

**Visual verification:**
1. Create your streets
2. Boot the game
3. Use free roam to drive the network (press: {shortcut})
4. Watch traffic and AI behavior
5. Adjust vertex positions as needed

*TODO: needs more testing and documentation*

---

### Integration with Races

AI streets are used by:
- **Traffic cars** during races (avoid your streets by setting `traffic_blocked = YES`)
- **Police AI** for chasing players
- **Opponent AI** for pathfinding to waypoints

**Race-specific streets:**
```python
# Shortcut only accessible during races
race_shortcut = {
    "street_name": "race_shortcut",
    "vertices": [...],
    "traffic_blocked": [YES, YES],  # No ambient traffic
    "ped_blocked": [YES, YES]        # No pedestrians
}
```

The street exists in the network but won't have traffic, creating a clear path for racers.

---

## Advanced Example: Complete City Block

Here's a realistic city block with multiple connected streets:

```python
# Main avenue (2 lanes, bidirectional with reverse setting)
main_avenue = {
    "street_name": "main_avenue",
    "lanes": {
        "lane_1": [(0, 0, 200), (0, 0, 100), (0, 0, 0), (0, 0, -100)],
        "lane_2": [(5, 0, 200), (5, 0, 100), (5, 0, 0), (5, 0, -100)]
    },
    "intersection_types": [IntersectionType.STOP_LIGHT, IntersectionType.STOP_LIGHT],
    "stop_light_names": [Prop.STOP_LIGHT_DUAL, Prop.STOP_LIGHT_DUAL]
}

# Cross street 1 (connects at 100)
first_street = {
    "street_name": "first_street",
    "vertices": [(-100, 0, 100), (0, 0, 100), (100, 0, 100)],
    "intersection_types": [IntersectionType.YIELD, IntersectionType.STOP]
}

# Cross street 2 (connects at 0)
second_street = {
    "street_name": "second_street",
    "vertices": [(-100, 0, 0), (0, 0, 0), (100, 0, 0)],
    "intersection_types": [IntersectionType.YIELD, IntersectionType.STOP]
}

# Back alley (parallel to main, fewer traffic controls)
back_alley = {
    "street_name": "back_alley",
    "vertices": [(20, 0, 150), (20, 0, 50), (20, 0, -50)],
    "alley": YES,
    "ped_blocked": [NO, NO]  # Allow pedestrians in alley
}

street_list = [main_avenue, first_street, second_street, back_alley]

# With set_reverse_ai_streets = True, this creates:
# - 2-way traffic on main_avenue (4 lanes total)
# - 2-way traffic on cross streets (2 lanes each)
# - 2-way traffic in alley (2 lanes)
# - Two 4-way intersections with proper traffic control
```

This creates a functional city block where:
- Main avenue has traffic lights at major intersections
- Cross streets have yield/stop signs
- Back alley provides alternative route
- All streets properly connect and allow bidirectional traffic

---

## Need More Help?

- Street implementation: `src/file_formats/ai/street_editor.py`
- Your custom streets: `src/USER/ai_streets.py`
- Map generation: `src/file_formats/ai/map.py`
- Settings: `src/USER/settings/ai.py`
- Debug output: `debug/AI/streets/` and `debug/AI/intersections/` when debug enabled
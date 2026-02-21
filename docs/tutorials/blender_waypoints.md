# Blender Waypoints Tutorial

Waypoints define where the player and opponents start and finish, and where intermediate checkpoints appear. This tutorial covers creating, loading, and exporting waypoints in Blender.

## Table of Contents
- [What Waypoints Are](#what-waypoints-are)
- [Creating a Single Waypoint](#creating-a-single-waypoint)
- [Waypoint Colors](#waypoint-colors)
- [Loading Waypoints from Race Data](#loading-waypoints-from-race-data)
- [Loading Waypoints from CSV](#loading-waypoints-from-csv)
- [Cops and Robbers Waypoints](#cops-and-robbers-waypoints)
- [Exporting Waypoints](#exporting-waypoints)
- [Keybinding Reference](#keybinding-reference)
---

## What Waypoints Are

In Blender, a waypoint is a visual object made up of two vertical poles and a flag panel between them. The width of the flag represents the `Width` parameter (how wide the checkpoint gate is in-game), and the rotation of the object represents the `Rotation` parameter (which direction the gate faces).

All waypoint objects are named with the `WP_` prefix, for example `WP_CIRCUIT0_0`, `WP_B1_3`, or simply `WP_`. Objects named `CR_Bank1`, `CR_Robber1`, and `CR_Gold1` are used for the Cops and Robbers mode (bank hideout, robber hideout, and gold bar respectively).

Creating and editing waypoints directly in Blender on your map makes the whole process much easier. You can export the waypoint coordinates and integrate them into your race settings.

![Preview](https://raw.githubusercontent.com/KcRobin9/MM1-Map-Editor/main/.github/images/tutorials/blender/waypoints/example.png)

---

## Creating a Single Waypoint

**`Shift + Y`** - Creates a single waypoint at the current 3D cursor position.

The new waypoint appears at the cursor with:
- Default rotation (`Rotation.NORTH`)
- Default width (`Width.DEFAULT` = 15 units)
- Blue/green/white flag color (dependent on the index)

To position a waypoint precisely:
1. Place the 3D cursor where you want it (`Shift + Right Click`)
2. Press `Shift + Y`
3. Rename the object in the outliner to match your race/waypoint convention

To adjust rotation and width after placing:
- **Rotation**: Rotate the object on the Z-axis (`R`, `Z`, then type degrees)
- **Width**: Scale the object on the X-axis (`S`, `X`, then type a factor)

---

## Waypoint Colors

Colors update automatically whenever waypoints change:

| Color | Waypoint |
|---|---|
| White | First waypoint (start/spawn) |
| Blue | All intermediate waypoints |
| Green | Last waypoint (finish/end) |

This makes it easy to verify that your sequence is correct. You should always see one white, any number of blue, and one green.

---

## Loading Waypoints from Race Data

**`Shift + R`** - Loads waypoints from the `race_data` dictionary (if available) in your script.

This reads waypoints for a specific race and spawns them into Blender. Useful when you've already defined a race in the Editor and want to visualize or tweak the waypoint positions.

Race data is configured in `src/USER/races/races.py`.

The target race is configured in `src/USER/settings/blender.py`:
```python
# Waypoints from the Editor ("race_data")
waypoint_number_input = "0"
waypoint_type_input = "RACE"
```

After loading, each waypoint is named using the race type and index, for example:
- `WP_C0_0`, `WP_C0_1`, `WP_C0_2` for Circuit race 0
- `WP_B1_0`, `WP_B1_1` for Blitz race 1

Move them around, then export back to get the updated coordinates.

---

## Loading Waypoints from CSV

**`Shift + C`** - Loads waypoints from a CSV file.

The CSV format matches the output of the race system. Each row contains:

```
x, y, z, rotation, width
```

The input file is configured in `src/USER/settings/blender.py`:
```python
input_waypoint_file = Folder.Resources.Editor.Race / "RACE2WAYPOINTS.CSV"
```

The file name determines which race the waypoints belong to. For example `CIRCUIT0WAYPOINTS.CSV` loads waypoints for Circuit race 0.

**`Alt + O`** - Loads Cops and Robbers waypoints from a CSV file:

The input file is configured in `src/USER/settings/blender.py`:
```python
input_cnr_waypoint_file = Folder.Resources.Editor.Race / "COPSWAYPOINTS.CSV"
```

Cops and Robbers waypoints are loaded in sets of three and spawn as distinct object types:
- **`CR_Bank{n}`** - Bank / Blue team hideout (purple flag)
- **`CR_Gold{n}`** - Gold position (gold cube)
- **`CR_Robber{n}`** - Robber / Red team hideout (green flag)

The number suffix increments per set of 3, so if you have two Cops and Robber sets you'll see `CR_Bank1`, `CR_Gold1`, `CR_Robber1`, `CR_Bank2`, `CR_Gold2`, `CR_Robber2`.

---

## Cops and Robbers Waypoints

TODO

---

## Exporting Waypoints

| Keybinding | Exports |
|---|---|
| `Shift + W` | Selected waypoints only |
| `Ctrl + W` | Selected waypoints, formatted with brackets |
| `Ctrl + Shift + W` | All waypoints |
| `Ctrl + Alt + W` | All waypoints, formatted with brackets |

On export:
1. The file is saved to `blender/export/waypoints/Waypoints_{timestamp}.txt`
2. Notepad++ opens the file automatically
3. The content is copied to clipboard

**Without brackets** - plain coordinates, one per line:
```
0.00, 0.00, 55.00, 0.01, 12.00
0.00, 0.00, 15.00, 0.01, 12.00
0.00, 0.00, -40.00, 0.01, 12.00
```

**With brackets** - ready to paste directly into a `player_waypoints` list:
```python
            [0.00, 0.00, 55.00, 0.01, 12.00],
            [0.00, 0.00, 15.00, 0.01, 12.00],
            [0.00, 0.00, -40.00, 0.01, 12.00],
```

Use **with brackets** when pasting into a race definition. Use **without brackets** when pasting into a CSV file or when you want to post-process the values yourself.

The exporter automatically handles the coordinate system conversion (Blender to game), so the output coordinates match what the game expects.

**Rotation** is exported in degrees, normalized to the range `-180` to `180`. This matches the `Rotation` constants used in `player_waypoints`.

---

## Keybinding Reference

| Keybinding | Action | Configuration |
|---|---|---|
| `Shift + Y` | Create a single waypoint at cursor | |
| `Shift + C` | Load waypoints from CSV | `input_waypoint_file` in `src/USER/settings/blender.py` |
| `Shift + R` | Load waypoints from race data | `waypoint_type_input` + `waypoint_number_input` in `src/USER/settings/blender.py` |
| `Alt + O` | Load Cops and Robbers waypoints from CSV | `input_cnr_waypoint_file` in `src/USER/settings/blender.py` |
| `Shift + W` | Export selected waypoints | |
| `Ctrl + W` | Export selected waypoints with brackets | |
| `Ctrl + Shift + W` | Export all waypoints | |
| `Ctrl + Alt + W` | Export all waypoints with brackets | |
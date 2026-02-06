# Races Tutorial

This tutorial will guide you through creating races for your Midtown Madness city. There are three types of races: Blitz, Circuit, Checkpoint.

## Race Types Overview

| Race Type | Max Races | Waypoint Limit | Description |
|-----------|-----------|----------------|-------------|
| **Blitz** | 15 | 11 (including start) | Time-based races where you must reach waypoints before time run out |
| **Circuit** | 15 | Unlimited | Lap-based races on a closed loop |
| **Checkpoint** | 12 | Unlimited | Point-to-point races through a series of checkpoints |

---

## Configuration File Location

All race configuration is done in:
```
src/USER/races/races.py
```

---

## Basic Race Structure

Each race is defined as a dictionary entry in the `race_data` dictionary with the following components:

1. **Race Key** - Identifies the race type and index (e.g., `"BLITZ_0"`, `"CIRCUIT_1"`, `"RACE_0"`)
2. **Player Waypoints** - The checkpoints the player must navigate
3. **MM Data** - Race settings for Amateur and Pro difficulties
4. **AI Map** - Traffic, police, and opponent configurations

---

## Creating Your First Race

### Step 1: Add Race Names

Add your race name to the appropriate list:

```python
blitz_race_names = ["Kacky Madness", "Target Car 2027"]
circuit_race_names = ["Heart Breaker", "Stay Alive"]
checkpoint_race_names = ["Toxic Exhaust", "Among the Trees"]
```

### Step 2: Define the Race

Here's a simple Blitz race example:

```python
"BLITZ_0": {
    "player_waypoints": [
        [0.0, 0.0, 55.0, Rotation.NORTH, 12.0],   # Start position
        [0.0, 0.0, 15.0, Rotation.NORTH, 12.0],   # Waypoint 1
        [0.0, 0.0, -40.0, Rotation.NORTH, 12.0],  # Waypoint 2
        [0.0, 0.0, -130.0, Rotation.NORTH, 12.0], # Finish
    ],
    "mm_data": {
        "ama": [TimeOfDay.NOON, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, 
                AmbientDensity._100, PedDensity._100, Laps._3, 60],
        "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._8, CopDensity._100, 
                AmbientDensity._100, PedDensity._100, Laps._3, 45],
    },
    "aimap": {
        "ambient_density": 0.25,
        "num_of_police": 2,
        "police": [
            f"{PlayerCar.POLICE} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
            f"{PlayerCar.POLICE} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",
        ],
        "num_of_opponents": 1,
        "opponents": [
            {PlayerCar.CADILLAC: [
                [5.0, 0.0, 35.0],
                [5.0, 0.0, -130.0],
            ]},
        ],
    },
},
```

---

## Player Waypoints Explained

### Waypoint Format
Each waypoint is defined as: `[X, Y, Z, Rotation, Width]`

**Position** (X, Y, Z):
- X, Z coordinates define the horizontal/vertical position in the city
- Y coordinate defines the height/elevation

**Rotation**:
- Determines which direction the waypoint faces
- Available cardinal directions: `Rotation.NORTH`, `Rotation.SOUTH`, `Rotation.EAST`, `Rotation.WEST`
- Available diagonal directions: `Rotation.NORTH_EAST`, `Rotation.SOUTH_EAST`, `Rotation.SOUTH_WEST`, `Rotation.NORTH_WEST`
- Special option: `Rotation.AUTO` (0) - Auto-detect direction to the next waypoint
- Or use custom degree value (e.g., `45`, `135`, `-90`)

**Rotation Quick Reference:**

| Direction | Constant | Degrees |
|-----------|----------|---------|
| North | `Rotation.NORTH` | 0.01 |
| North-East | `Rotation.NORTH_EAST` | 45 |
| East | `Rotation.EAST` | 90 |
| South-East | `Rotation.SOUTH_EAST` | 135 |
| South | `Rotation.SOUTH` | 179.99 |
| South-West | `Rotation.SOUTH_WEST` | -135 |
| West | `Rotation.WEST` | -90 |
| North-West | `Rotation.NORTH_WEST` | -45 |
| Auto | `Rotation.AUTO` | 0 |

**Width**:
- Defines the waypoint width of the waypoint
- Predefined sizes:
  - `Width.AUTO` (0) - Auto-detect width (needs testing and documentation)
  - `Width.ALLEY` (3) - Very narrow
  - `Width.SMALL` (11) - Narrow checkpoint
  - `Width.MEDIUM` (15) - Standard size (default)
  - `Width.LARGE` (19) - Wide checkpoint
- Or use a custom float value (e.g., `12.0`, `25.0`, `30.0`)

**Width Quick Reference:**

| Size | Constant | Value | Use Case |
|------|----------|-------|----------|
| Auto | `Width.AUTO` | 0 | Auto-detect |
| Alley | `Width.ALLEY` | 3 | Tight alleyways
| Small | `Width.SMALL` | 11 | Narrow streets
| Medium | `Width.MEDIUM` | 15 | Standard roads
| Large | `Width.LARGE` | 19 | Wide roads

### Example Waypoints

```python
# Simple straight race
[0.0, 0.0, 100.0, Rotation.SOUTH, Width.MEDIUM],   # Start
[0.0, 0.0, 50.0, Rotation.SOUTH, Width.MEDIUM],    # Checkpoint 1
[0.0, 0.0, 0.0, Rotation.SOUTH, Width.MEDIUM],     # Checkpoint 2
[0.0, 0.0, -50.0, Rotation.SOUTH, Width.MEDIUM],   # Finish
```

---

## MM Data Configuration

The `mm_data` section defines race settings for both Amateur and Professional difficulties.

### Blitz Races
```python
"mm_data": {
    "ama": [TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps, TimeLimit],
    "pro": [TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps, TimeLimit],
}
```

### Circuit Races
```python
"mm_data": {
    "ama": [TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps],
    "pro": [TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity, Laps],
}
```

### Checkpoint Races
```python
"mm_data": {
    "ama": [TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity],
    "pro": [TimeOfDay, Weather, MaxOpponents, CopDensity, AmbientDensity, PedDensity],
}
```

### Available Options

**Time of Day:**
- `TimeOfDay.MORNING` - Early morning lighting
- `TimeOfDay.NOON` - Bright midday
- `TimeOfDay.EVENING` - Sunset/dusk
- `TimeOfDay.NIGHT` - Dark with street lights

**Weather:**
- `Weather.CLEAR` - Clear skies
- `Weather.CLOUDY` - Overcast
- `Weather.RAIN` - Rainy conditions
- `Weather.SNOW` - Snowy conditions

**Density Settings:**
- `MaxOpponents._0` through `MaxOpponents._8` - Number of AI racers
- `CopDensity._0` or `CopDensity._100` - Police presence (only 0% or 100%)
- `AmbientDensity._0` through `AmbientDensity._100` - Traffic density (increments of 10)
- `PedDensity._0` through `PedDensity._100` - Pedestrian density (increments of 10)

**Laps/Waypoints (Circuit/Blitz only):**
- `Laps._1` through `Laps._10` - Number of laps/waypoints (menu max is 10)

**Time Limit (Blitz only):**
- Any integer value in seconds (e.g., `999`, `60`, `120`)

### Example Configurations

```python
# Daytime race with heavy traffic
"ama": [TimeOfDay.NOON, Weather.CLEAR, MaxOpponents._4, CopDensity._0, AmbientDensity._80, PedDensity._50, Laps._3],

# Night race in the rain with police
"pro": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._100, AmbientDensity._30, PedDensity._10, Laps._5],
```

---

## AI Map Configuration

The `aimap` section controls traffic, police, and opponents during the race.

### Traffic Settings

```python
"aimap": {
    "ambient_density": 0.25,  # Overall traffic density (0.0 to 1.0)
    "speed_limit": 45,        # Default speed limit (optional, default: 45)
    # ... rest of config
}
```

### Police Configuration

```python
"num_of_police": 2,  # Total number of police cars
"police": [
    f"{PlayerCar.POLICE} X Y Z {Rotation} {StartLane} {Behavior}",
    f"{PlayerCar.POLICE} X Y Z {Rotation} {StartLane} {Behavior}",
],
```

**Police Spawn Format:** `VehicleType X Y Z Rotation StartLane Behavior`

**Start Lane Options:**
- `CopStartLane.STATIONARY` - Parked and waiting
- `CopStartLane.IN_TRAFFIC` - Driving in traffic
- `CopStartLane.PED` - ⚠️ Broken, do not use

**Behavior Options:**

*Basic Behaviors:*
- `CopBehavior.FOLLOW` - Only follow the player
- `CopBehavior.ROADBLOCK` - Attempt to create roadblocks
- `CopBehavior.SPINOUT` - Try to spin the player out
- `CopBehavior.PUSH` - Ram from behind

*Combined Behaviors:*
- `CopBehavior.MIX` - All behaviors combined
- `CopBehavior.FOLLOW_AND_SPINOUT` - Follow and try to spin out
- `CopBehavior.FOLLOW_AND_PUSH` - Follow and push
- `CopBehavior.ROADBLOCK_AND_SPINOUT` - Attempt roadblocks and spin out
- `CopBehavior.ROADBLOCK_AND_PUSH` - Attempt roadblocks and push
- `CopBehavior.SPINOUT_AND_PUSH` - Spin out and push

*Preset Combinations:*
- `CopBehavior.AGGRESSIVE` - Roadblock + Spinout + Push (all except follow)
- `CopBehavior.DEFENSIVE` - Follow + Roadblock (more passive, keeping distance)
- `CopBehavior.CUNNING` - Follow + Spinout (following and occasionally spinning out)
- `CopBehavior.PERSISTENT` - Follow + Push (persistently following and pushing)
- `CopBehavior.UNPREDICTABLE` - Roadblock + Follow + Spinout (unpredictable mix)

### Police Examples

```python
# Stationary roadblock at race start
f"{PlayerCar.POLICE} 10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.STATIONARY} {CopBehavior.ROADBLOCK}",

# Aggressive cop in traffic
f"{PlayerCar.POLICE} -10.0 0.0 65.0 {Rotation.NORTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.MIX}",

# Pusher cop waiting at checkpoint
f"{PlayerCar.POLICE} 15.0 0.0 75.0 {Rotation.SOUTH} {CopStartLane.STATIONARY} {CopBehavior.PUSH}",
```

### Opponent Configuration

There are two formats for defining opponents: **Legacy Format** (dict) and **New Format** (list).

#### New Format (Recommended)
Allows multiple opponents of the same car type:

```python
"num_of_opponents": 3,
"opponents": [
    {PlayerCar.CADILLAC: [
        [5.0, 0.0, 35.0],     # Spawn position
        [5.0, 0.0, -130.0],   # Waypoint 1
    ]},
    {PlayerCar.CADILLAC: [    # Second Cadillac with different path
        [10.0, 0.0, 35.0],
        [10.0, 0.0, -130.0],
    ]},
    {PlayerCar.MUSTANG_GT: [   # Different car type
        [15.0, 0.0, 35.0],
        [15.0, 0.0, -130.0],
    ]},
],
```

#### Legacy Format
Only allows one of each car type:

```python
"num_of_opponents": 2,
"opponents": {
    TrafficCar.LIMO_WHITE: [
        [-10.0, 245, -850],   # Spawn
        [0.0, 0.0, -100],     # Waypoint 1
        [-10.0, 0.0, -75.0]   # Waypoint 2
    ],
    TrafficCar.LIMO_BLACK: [
        [10.0, 245, -850],
        [0.0, 0.0, -100],
        [10.0, 0.0, -75.0],
    ],
}
```

### Available Opponent Cars

**Player Cars:**
```python
PlayerCar.VW_BEETLE
PlayerCar.CITY_BUS
PlayerCar.CADILLAC
PlayerCar.POLICE        # Police car
PlayerCar.FORD_F350
PlayerCar.FASTBACK
PlayerCar.MUSTANG_GT
PlayerCar.ROADSTER
PlayerCar.PANOZ_GTR1
PlayerCar.SEMI
```

**Traffic Cars:**
```python
TrafficCar.TINY
TrafficCar.SEDAN_SMALL
TrafficCar.SEDAN_LARGE
TrafficCar.TAXI_YELLOW
TrafficCar.TAXI_GREEN
TrafficCar.LIMO_WHITE
TrafficCar.LIMO_BLACK
TrafficCar.PICKUP
TrafficCar.VAN_SMALL
TrafficCar.VAN_LARGE
TrafficCar.TRUCK
TrafficCar.BUS
TrafficCar.PLANE
```

### Traffic Exceptions

Control traffic behavior on specific road segments:

```python
"num_of_exceptions": 2,
"exceptions": [
    [4, 0.0, 45],   # Road ID 4: no traffic (0.0), speed limit 45
    [5, 0.5, 30],   # Road ID 5: 50% traffic (0.5), speed limit 30
],
```

---

## Complete Race Examples

### Example 1: Simple Blitz Race

```python
"BLITZ_0": {
    "player_waypoints": [
        [0.0, 0.0, 100.0, Rotation.SOUTH, Width.MEDIUM],
        [0.0, 0.0, 50.0, Rotation.SOUTH, Width.MEDIUM],
        [0.0, 0.0, 0.0, Rotation.SOUTH, Width.MEDIUM],
        [0.0, 0.0, -50.0, Rotation.SOUTH, Width.MEDIUM],
    ],
    "mm_data": {
        "ama": [TimeOfDay.NOON, Weather.CLEAR, MaxOpponents._4, CopDensity._0, AmbientDensity._50, PedDensity._50, Laps._1, 120],
        "pro": [TimeOfDay.EVENING, Weather.CLOUDY, MaxOpponents._6, CopDensity._100, AmbientDensity._70, PedDensity._30, Laps._1, 90],
    },
    "aimap": {
        "ambient_density": 0.3,
        "num_of_police": 1,
        "police": [
            f"{PlayerCar.POLICE} 0.0 0.0 75.0 {Rotation.SOUTH} {CopStartLane.IN_TRAFFIC} {CopBehavior.FOLLOW}",
        ],
        "num_of_opponents": 2,
        "opponents": [
            {PlayerCar.MUSTANG_GT: [[5.0, 0.0, 100.0], [5.0, 0.0, -50.0]]},
            {PlayerCar.CADILLAC: [[-5.0, 0.0, 100.0], [-5.0, 0.0, -50.0]]},
        ],
    },
},
```

### Example 2: Circuit Race with Multiple Laps

```python
"CIRCUIT_0": {
    "player_waypoints": [
        [0.0, 0.0, 100.0, Rotation.SOUTH, Width.MEDIUM],
        [50.0, 0.0, 50.0, Rotation.WEST, Width.MEDIUM],
        [50.0, 0.0, -50.0, Rotation.NORTH, Width.MEDIUM],
        [-50.0, 0.0, -50.0, Rotation.EAST, Width.MEDIUM],
        [-50.0, 0.0, 50.0, Rotation.SOUTH, Width.MEDIUM],
    ],
    "mm_data": {
        "ama": [TimeOfDay.MORNING, Weather.CLEAR, MaxOpponents._6, CopDensity._0, AmbientDensity._20, PedDensity._20, Laps._3],
        "pro": [TimeOfDay.NIGHT, Weather.RAIN, MaxOpponents._8, CopDensity._0, AmbientDensity._30, PedDensity._10, Laps._5],
    },
    "aimap": {
        "traffic_density": 0.15,
        "num_of_police": 0,
        "police": [],
        "num_of_opponents": 4,
        "opponents": [
            {PlayerCar.ROADSTER: [[10.0, 0.0, 100.0], [60.0, 0.0, 50.0], [60.0, 0.0, -50.0]]},
            {PlayerCar.MUSTANG_GT: [[20.0, 0.0, 100.0], [70.0, 0.0, 50.0], [70.0, 0.0, -50.0]]},
            {TrafficCar.LIMO_BLACK: [[-10.0, 0.0, 100.0], [40.0, 0.0, 50.0], [40.0, 0.0, -50.0]]},
            {TrafficCar.PICKUP: [[-20.0, 0.0, 100.0], [30.0, 0.0, 50.0], [30.0, 0.0, -50.0]]},
        ],
    },
},
```
---

## Tips and Best Practices

### Waypoint Placement
- Space waypoints evenly for smooth racing lines
- Use wider waypoints for forgiving turns
- Use narrow waypoints for precision sections
- Set rotation to match the approach direction for clear visual feedback

### Difficulty Balance
- Amateur: Fewer opponents, less traffic, more time/laps
- Professional: More opponents, heavier traffic, tighter time limits, worse weather

### Police Integration
- Mix stationary and moving police for variety
- Use `ROADBLOCK` behavior near tight sections
- Use `MIX` behavior for aggressive chases

### Opponent Variety
- Mix fast player cars (Mustang, Roadster) with slower cars
- Space out opponent spawn positions to avoid collisions at race start
- Give opponents slightly different paths for dynamic racing
- Use 4-8 opponents for exciting races without overwhelming the player

### Testing
- Always test races after creation to ensure waypoints work correctly
- Check that opponent AI follows reasonable paths
- Verify police spawn in correct locations
- Adjust traffic density whenever necessary
---

## Cops and Robbers Mode

Create special waypoints for the Cops and Robbers game mode:

```python
# src/USER/races/cops_and_robbers.py

cops_and_robbers_waypoints = [                           
    ## Set 1 ##
    (20.0, 1.0, 80.0),   # Bank / Blue Team Hideout
    (80.0, 1.0, 20.0),   # Gold Position
    (20.0, 1.0, 80.0),   # Robber / Red Team Hideout
    
    ## Set 2 ##
    (-90.0, 1.0, -90.0), # Bank / Blue Team Hideout
    (90.0, 1.0, 90.0),   # Gold Position
    (-90.0, 1.0, -90.0), # Robber / Red Team Hideout
]
```

**Note:** Waypoints must be in groups of 3:
1. Bank/Blue Team Hideout
2. Gold Position
3. Robber/Red Team Hideout

---

## Troubleshooting

**Race doesn't appear in game menu:**
- Check that race name is added to the appropriate list (`blitz_race_names`, etc.)
- Verify race key format: `"BLITZ_0"`, `"CIRCUIT_1"`, `"RACE_0"`
- Ensure race index matches the position in the name list

**Game crashes on race start:**
- Too many waypoints in Blitz race (max 11)

**Police behaving strangely:**
- Verify behavior flags are correct

---

## Limits and Constraints

| Feature | Limit | Notes |
|---------|-------|-------|
| Blitz Races | 15 | Maximum allowed |
| Circuit Races | 15 | Maximum allowed |
| Checkpoint Races | 12 | Maximum allowed |
| Blitz Waypoints | 11 | Including start position |
| Circuit/Checkpoint Waypoints | Unlimited | Limit approx. 5000 based on the heap
| Laps (Circuit) | 10 | Menu maximum (code supports more) |
| Opponents | 16 | Can be increased further via Open1560 tweaks |
| Police | 256 | MAX_MOVERS limit, requires additional heap |

---
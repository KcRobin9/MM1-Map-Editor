# Lighting Tutorial

Lighting controls the atmosphere and visual mood of your Midtown Madness map - from sunny afternoons to foggy evenings. This guide covers customizing lighting configurations for different times of day and weather conditions.

## Table of Contents
- [Basic Lighting Setup](#basic-lighting-setup)
- [Understanding the Lighting System](#understanding-the-lighting-system)
- [Color Value Ranges](#color-value-ranges)
- [Light Sources](#light-sources)
- [Atmosphere & Effects](#atmosphere--effects)
- [Creating Custom Configs](#creating-custom-configs)
- [Real-World Example: Chicago](#real-world-example-chicago)
- [Multiple Configurations](#multiple-configurations)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## Basic Lighting Setup

Lighting configurations are defined in `src/USER/lighting.py`. Each config targets a specific combination of time of day and weather:

```python
lighting_configs = [
    {
        "time_of_day": TimeOfDay.EVENING,
        "weather": Weather.CLEAR,
        "sun_pitch": 0.5,
        "sun_color": (1.0, 0.6, 0.3),
        "ambient_color": (0.3, 0.3, 0.4)
    }
]
```

This modifies the lighting for Evening + Clear weather only. Other time/weather combinations remain unchanged.

---

## Understanding the Lighting System

### Three-Point Lighting Architecture

Midtown Madness uses a three-point directional lighting system, a technique borrowed from photography and film:

- **Sun Light** (Key Light): Your primary light source representing the sun or moon
- **Fill Light 1** (Fill Light): Secondary light from a different angle to soften harsh shadows
- **Fill Light 2** (Back Light): Additional fill light for more balanced illumination from another direction

All three lights are directional (infinite distance with parallel rays), meaning they illuminate from a specific angle regardless of position in the world.

**Why three lights?** A single light creates pitch-black shadows and high contrast. Fill lights reduce this contrast while maintaining visual depth, creating more realistic and visually appealing scenes.

### Time and Weather Matrix

**`time_of_day`**: Use `TimeOfDay` in Visual Studio Code
```python
TimeOfDay.MORNING  # 0
TimeOfDay.NOON     # 1
TimeOfDay.EVENING  # 2
TimeOfDay.NIGHT    # 3
```

**`weather`**: Use `Weather` in Visual Studio Code
```python
Weather.CLEAR   # 0
Weather.CLOUDY  # 1
Weather.RAIN    # 2
Weather.SNOW    # 3
```

**Note:** Each time/weather combination has its own independent lighting configuration. There are 4 times of day × 4 weather types = 16 possible configurations you can customize.

---

## Color Value Ranges

The game engine uses two different color systems depending on the parameter type:

| Parameter Type | Standard Range | Example | Notes |
|----------------|----------------|---------|-------|
| **Light Source Colors** | | | |
| `sun_color` | 0.0 - 1.0 | `(1.0, 0.6, 0.3)` | Normalized RGB (0.0 = black, 1.0 = full intensity) |
| `fill_1_color` | 0.0 - 1.0 | `(0.8, 0.9, 1.0)` | Same as sun_color |
| `fill_2_color` | 0.0 - 1.0 | `(0.75, 0.8, 1.0)` | Same as sun_color |
| `ambient_color` | 0.0 - 1.0 | `(0.1, 0.1, 0.2)` | Same as sun_color |
| **Atmospheric Colors** | | | |
| `fog_color` | 0 - 255 | `(230.0, 100.0, 35.0)` | Standard 8-bit RGB (0-255 per channel) |
| `shadow_color` | 0 - 255 | `(15.0, 20.0, 30.0)` | Same as fog_color |
| **Opacity** | | | |
| `shadow_alpha` | 0 - 255 | `180.0` | 0 = invisible, 255 = fully opaque |

### Why Two Different Systems?

Light source colors (sun, fills, ambient) use normalized 0-1 values because they're computed in the engine's lighting calculations where this range is standard. Atmospheric effects (fog, shadows) use 0-255 values likely due to legacy rendering pipeline decisions or because they directly map to 8-bit color channels.

### Experimental Values

**Standard ranges are recommendations, not hard limits.** The engine accepts values outside these bounds:

- **Light colors > 1.0**: Creates overbright/glowing effects (e.g., `sun_color: (2.0, 1.5, 1.0)` for intense sunlight)
- **Light colors > 255**: Possible for extreme stylized looks (e.g., purple night sky: `(400.0, 0.0, 400.0)`)
- **Negative angles**: Not tested
- **Pitch beyond 1.57 (π/2)**: Not tested, but possibly creates light from below

Feel free to experiment - just understand that values far outside standard ranges create stylized, unrealistic effects.

---

## Light Sources

### Sun Light (Primary/Key Light)

The sun is your main light source and has the most impact on your scene's appearance.

#### Sun Direction

**`sun_heading`**: Horizontal direction in radians
```python
# Standard compass directions (counter-clockwise from East)
"sun_heading": 0.0     # East
"sun_heading": 1.57    # North (π/2)
"sun_heading": 3.14    # West (π)
"sun_heading": 4.71    # South (3π/2)

# Negative values (not tested)
"sun_heading": -2.5    # Equivalent to ~3.78 radians
```

**Heading wraps around**: Values beyond 2π (6.28) or negative values are valid - the engine likely treats them as circular rotation.

**`sun_pitch`**: Vertical angle in radians
```python
"sun_pitch": 0.0    # Horizon (sun right at eye level)
"sun_pitch": 0.78   # 45 degrees above horizon
"sun_pitch": 1.57   # Directly overhead (π/2, zenith)

# Extreme values create unusual effects
"sun_pitch": 0.1    # Very low sun (long shadows, dramatic lighting)
"sun_pitch": 10.0   # Beyond vertical (experimental - light from below)
```

**Lower pitch = longer shadows.** A sun near the horizon (0.1-0.5) creates dramatic directional lighting with long shadows, while high pitch (1.0-1.57) creates shorter shadows and more even illumination.

#### Sun Color

**`sun_color`**: RGB color in 0.0-1.0 range (per channel)
```python
"sun_color": (1.0, 1.0, 1.0)      # Pure white (neutral daylight)
"sun_color": (1.0, 0.6, 0.3)      # Warm orange (sunset/sunrise)
"sun_color": (0.8, 0.85, 1.0)     # Cool blue-white (overcast day)
"sun_color": (0.12, 0.12, 0.2)    # Dim cool blue (moonlight)

# Experimental overbright
"sun_color": (1.5, 1.2, 0.8)      # Intense bright sun (values > 1.0)
```

**Color temperature matters:** Warm colors (more red) suggest sunrise/sunset, while cool colors (more blue) suggest midday or moonlight.

---

### Fill Light 1 (Secondary Fill)

Fill Light 1 provides secondary illumination from a different angle to reduce shadow harshness.

```python
"fill_1_heading": -2.5           # Direction (negative value wraps around)
"fill_1_pitch": 0.45             # Usually similar to sun pitch
"fill_1_color": (0.8, 0.9, 1.0)  # Often cooler than sun (0.0-1.0 range)
```

**Best practice:** Place fill light opposite or perpendicular to sun heading for best shadow softening. Keep fill color dimmer and often complementary to sun color (warm sun → cool fill).

---

### Fill Light 2 (Tertiary Fill)

Fill Light 2 adds additional illumination from yet another direction for even more balanced lighting.

```python
"fill_2_heading": 0.0             # Direction in radians
"fill_2_pitch": 0.45              # Vertical angle
"fill_2_color": (0.75, 0.8, 1.0)  # Usually dimmest of the three (0.0-1.0 range)
```

**Typical setup:** Fill 2 is usually the dimmest light, used to subtly brighten areas that would otherwise be too dark.

---

## Atmosphere & Effects

### Ambient Light

**`ambient_color`**: Base illumination applied uniformly to all surfaces (0.0-1.0 per channel)

```python
"ambient_color": (0.3, 0.3, 0.4)  # Neutral ambient (moderate)
"ambient_color": (0.1, 0.1, 0.2)  # Dark ambient (moody, high contrast)
"ambient_color": (0.5, 0.5, 0.6)  # Bright ambient (low contrast, flat)
```

**What it does:** Ambient light has no direction - it brightens everything equally. Higher values make dark areas brighter (reducing contrast), while lower values create more dramatic lighting with deeper shadows.

**Note:** Ambient light is added after directional lighting calculations, so even surfaces facing away from all lights receive this illumination.

---

### Fog

Fog creates depth and atmosphere by blending distant objects toward a specific color.

#### Fog Distance

**`fog_end`**: Distance where fog reaches full opacity
```python
"fog_end": 600.0   # Moderate visibility (medium fog)
"fog_end": 300.0   # Heavy fog (low visibility)
"fog_end": 1000.0  # Light fog (high visibility)
```

**How fog works:** The game blends from clear (at the camera) to fully opaque fog color at `fog_end` distance. Objects beyond this distance are completely obscured.

#### Fog Color

**`fog_color`**: RGB color of fog in 0-255 range (per channel)
```python
"fog_color": (200.0, 200.0, 200.0)  # Neutral gray fog
"fog_color": (230.0, 100.0, 35.0)   # Warm orange (sunset atmosphere)
"fog_color": (150.0, 180.0, 200.0)  # Cool blue (morning mist)
"fog_color": (20.0, 20.0, 30.0)     # Dark blue-black (night fog)
```

**Design tip:** Match fog color to your sun color for cohesive atmosphere. Warm sunset sun → warm fog color. Cool moonlight → cool fog color.

---

### Shadows

Shadows add depth and realism by darkening surfaces not directly illuminated by lights.

#### Shadow Opacity

**`shadow_alpha`**: Opacity of shadow overlay (0-255)
```python
"shadow_alpha": 180.0  # Medium shadows (semi-transparent)
"shadow_alpha": 255.0  # Solid shadows (completely opaque)
"shadow_alpha": 100.0  # Faint shadows (subtle)
```

**0 = invisible shadows**, **255 = pitch black shadows**. Most realistic settings are in the 150-200 range.

#### Shadow Color

**`shadow_color`**: RGB tint applied to shadows in 0-255 range (per channel)
```python
"shadow_color": (0.0, 0.0, 0.0)      # Pure black (neutral)
"shadow_color": (15.0, 20.0, 30.0)   # Cool blue-tinted (subtle realism)
"shadow_color": (30.0, 20.0, 10.0)   # Warm brown-tinted (sunset shadows)
```

**Realism tip:** Pure black shadows `(0, 0, 0)` look harsh. Subtly tinted shadows - especially cool blues - appear more natural because they simulate ambient light bouncing into shadowed areas.

---

## Creating Custom Configs

### Example: Golden Hour Sunset

```python
lighting_configs = [
    {
        "time_of_day": TimeOfDay.EVENING,
        "weather": Weather.CLEAR,
        
        # Sun low in the west creating warm directional light
        "sun_heading": 4.5,                    # West-southwest
        "sun_pitch": 0.3,                      # Low on horizon (long shadows)
        "sun_color": (1.0, 0.7, 0.4),          # Warm orange-yellow (0.0-1.0)
        
        # Fill 1 from opposite side with cool sky color
        "fill_1_heading": 1.5,                 # Northeast
        "fill_1_pitch": 0.4,
        "fill_1_color": (0.4, 0.6, 0.8),       # Cool blue sky reflection (0.0-1.0)
        
        # Fill 2 provides additional soft fill
        "fill_2_heading": 0.0,                 # East
        "fill_2_pitch": 0.5,
        "fill_2_color": (0.5, 0.55, 0.7),      # Dim cool fill (0.0-1.0)
        
        # Warm ambient to maintain golden hour feeling
        "ambient_color": (0.25, 0.2, 0.15),    # Warm ambient (0.0-1.0)
        
        # Moderate fog with golden color
        "fog_end": 500.0,
        "fog_color": (255.0, 150.0, 80.0),     # Golden-orange fog (0-255)
        
        # Semi-transparent warm shadows
        "shadow_alpha": 200.0,
        "shadow_color": (20.0, 10.0, 5.0)      # Warm brown tint (0-255)
    }
]
```

**Design choices explained:**
- **Low sun pitch (0.3)** creates long dramatic shadows characteristic of golden hour
- **Warm sun (1.0, 0.7, 0.4) + cool fills (blue-tinted)** creates natural color contrast
- **Fog color matches sun** for atmospheric coherence
- **Warm shadow tint** reinforces the sunset feeling
- **Fill lights from different angles** prevent pitch-black shadowed areas

---

### Example: Moody Overcast Night

```python
lighting_configs = [
    {
        "time_of_day": TimeOfDay.NIGHT,
        "weather": Weather.CLOUDY,
        
        # Very dim "moonlight" obscured by clouds
        "sun_heading": 0.0,                    # Direction less important for dim light
        "sun_pitch": 0.1,                      # Very low (minimal direct light)
        "sun_color": (0.12, 0.12, 0.2),        # Dim cool blue (0.0-1.0)
        
        # Extremely dim fill lights
        "fill_1_heading": 3.0,
        "fill_1_pitch": 0.3,
        "fill_1_color": (0.04, 0.04, 0.08),    # Barely visible (0.0-1.0)
        
        "fill_2_heading": 6.0,
        "fill_2_pitch": 0.3,
        "fill_2_color": (0.04, 0.04, 0.08),    # (0.0-1.0)
        
        # Very dark ambient creates high contrast
        "ambient_color": (0.05, 0.05, 0.1),    # Minimal ambient (0.0-1.0)
        
        # Heavy fog obscures distance
        "fog_end": 300.0,                      # Low visibility
        "fog_color": (20.0, 20.0, 30.0),       # Dark blue-tinted fog (0-255)
        
        # Solid black shadows for dramatic effect
        "shadow_alpha": 255.0,
        "shadow_color": (0.0, 0.0, 0.0)        # Pure black (0-255)
    }
]
```

**Design choices explained:**
- **All lights extremely dim** simulates heavily overcast night
- **Low ambient (0.05)** creates mostly dark scene
- **Cool blue tint throughout** suggests moonlight filtered through clouds
- **Heavy fog (300.0)** obscures distant objects, adding to oppressive mood
- **Solid black shadows** create stark contrast in this dark environment

---

## Real-World Example: Chicago

Here's Chicago's Evening + Cloudy configuration with detailed explanations:

```python
{
    "time_of_day": TimeOfDay.EVENING,
    "weather": Weather.CLOUDY,
    
    # Sun in the west at moderate-low angle
    "sun_heading": 3.14,                   # West (π radians)
    "sun_pitch": 0.65,                     # Moderately low (~37 degrees)
    "sun_color": (1.0, 0.6, 0.3),          # Warm orange sunset (0.0-1.0)
    
    # Fill 1 from southwest with cool sky light
    "fill_1_heading": -2.5,                # Southwest (negative wraps to ~3.78)
    "fill_1_pitch": 0.45,                  # Similar angle to sun
    "fill_1_color": (0.8, 0.9, 1.0),       # Cool blue-white (0.0-1.0)
    
    # Fill 2 from east
    "fill_2_heading": 0.0,                 # East
    "fill_2_pitch": 0.45,
    "fill_2_color": (0.75, 0.8, 1.0),      # Slightly dimmer cool fill (0.0-1.0)
    
    # Dark ambient for evening mood
    "ambient_color": (0.1, 0.1, 0.2),      # Low ambient with cool tint (0.0-1.0)
    
    # Moderate fog with warm sunset color
    "fog_end": 600.0,                      # Medium visibility
    "fog_color": (230.0, 100.0, 35.0),     # Warm orange fog (0-255)
    
    # Semi-transparent cool-tinted shadows
    "shadow_alpha": 180.0,                 # Medium opacity
    "shadow_color": (15.0, 20.0, 30.0)     # Cool blue tint (0-255)
}
```

### Chicago Design Analysis

**Color Contrast Strategy:**
- **Warm sun (orange) + cool fills (blue)** creates natural complementary color contrast
- Mimics real-world sunset where warm sunlight contrasts with cool skylight from opposite direction

**Three-Point Lighting Setup:**
- Sun from west provides main directional light
- Fill 1 from southwest prevents completely dark eastern faces
- Fill 2 from east fills in areas occluded from both other lights

**Atmospheric Coherence:**
- Fog color matches sun color (warm orange) for unified sunset atmosphere
- Cool shadow tint adds visual depth and realism
- Low ambient keeps overall scene moody/dramatic

**Why it works:**
This configuration creates natural-looking evening atmosphere through warm/cool contrast, strategic fill light placement, and coherent color choices throughout all parameters.

---

## Multiple Configurations

You can modify multiple time/weather combinations in a single file. Each configuration is independent:

```python
lighting_configs = [
    {
        # Morning clear - bright and fresh
        "time_of_day": TimeOfDay.MORNING,
        "weather": Weather.CLEAR,
        "sun_heading": 1.5,                    # Northeast (morning sun)
        "sun_pitch": 0.5,                      # Low-medium angle
        "sun_color": (1.0, 0.95, 0.8),         # Slightly warm white (0.0-1.0)
        "fill_1_color": (0.7, 0.8, 1.0),       # Cool fill (0.0-1.0)
        "fill_2_color": (0.65, 0.75, 0.95),    # (0.0-1.0)
        "ambient_color": (0.4, 0.4, 0.45),     # Bright ambient for morning (0.0-1.0)
        "fog_color": (200.0, 210.0, 230.0)     # Light blue morning haze (0-255)
    },
    {
        # Evening clear - warm sunset
        "time_of_day": TimeOfDay.EVENING,
        "weather": Weather.CLEAR,
        "sun_heading": 4.7,                    # West-southwest
        "sun_pitch": 0.3,                      # Low on horizon
        "sun_color": (1.0, 0.7, 0.4),          # Warm orange (0.0-1.0)
        "fill_1_color": (0.5, 0.6, 0.8),       # Cool fill (0.0-1.0)
        "fill_2_color": (0.45, 0.55, 0.75),    # (0.0-1.0)
        "ambient_color": (0.25, 0.2, 0.15),    # Warm dark ambient (0.0-1.0)
        "fog_color": (255.0, 150.0, 70.0)      # Golden fog (0-255)
    },
    {
        # Night rainy - dark and atmospheric
        "time_of_day": TimeOfDay.NIGHT,
        "weather": Weather.RAIN,
        "sun_pitch": 0.1,                      # Very low
        "sun_color": (0.08, 0.08, 0.12),       # Dim moonlight (0.0-1.0)
        "fill_1_color": (0.05, 0.05, 0.1),     # Minimal fill (0.0-1.0)
        "fill_2_color": (0.05, 0.05, 0.1),     # (0.0-1.0)
        "ambient_color": (0.05, 0.05, 0.1),    # Very dark (0.0-1.0)
        "fog_end": 200.0,                      # Heavy fog/rain
        "fog_color": (25.0, 30.0, 40.0),       # Dark blue fog (0-255)
        "shadow_alpha": 255.0,                 # Solid shadows
        "shadow_color": (0.0, 0.0, 0.0)        # Pure black (0-255)
    },
    {
        # Noon snow - bright overcast
        "time_of_day": TimeOfDay.NOON,
        "weather": Weather.SNOW,
        "sun_pitch": 1.2,                      # High but not overhead
        "sun_color": (0.9, 0.9, 1.0),          # Cool white (0.0-1.0)
        "fill_1_color": (0.6, 0.65, 0.75),     # Cool fill (0.0-1.0)
        "fill_2_color": (0.55, 0.6, 0.7),      # (0.0-1.0)
        "ambient_color": (0.5, 0.5, 0.55),     # Very bright (snow reflection) (0.0-1.0)
        "fog_color": (220.0, 220.0, 230.0),    # Light gray-blue fog (0-255)
        "shadow_alpha": 120.0,                 # Faint shadows (overcast)
        "shadow_color": (30.0, 35.0, 45.0)     # Cool tinted (0-255)
    }
]
```

**Key principle:** You only need to specify parameters you want to change. Omitted parameters keep their vanilla Chicago values for that time/weather combination.

---

## Troubleshooting

### Lighting changes not appearing in-game

**Check your settings:**
- Verify `set_lighting = True` in your project settings
- Ensure you're using correct constants: `TimeOfDay.NOON` (not AFTERNOON), `Weather.RAIN` (not RAINY)
- Confirm the time/weather combination in-game matches your config

**Testing tip:** Add a very obvious change (like purple sun color) to verify your config is being applied at all.

---

### Scene too dark or too bright

**Too dark:**
- Increase `ambient_color` values (brightens shadowed areas)
- Increase sun/fill `color` intensities (brighter overall lighting)
- Raise `sun_pitch` (higher sun = more even illumination)
- Check that fill light colors aren't too dim (e.g., `(0.01, 0.01, 0.01)` is nearly black)

**Too bright:**
- Decrease `ambient_color` (allows darker shadows)
- Reduce sun/fill color intensities
- Lower `sun_pitch` (creates more dramatic directional lighting)

**Flat/washed out:**
- Lower `ambient_color` to increase contrast
- Ensure fills are dimmer than sun
- Add cool/warm color contrast between sun and fills

---

### Colors look wrong or unexpected

**Most common issue: Wrong value range**
- **Sun/Fill/Ambient colors:** Use 0.0-1.0 range 
  - ✅ Correct: `"sun_color": (1.0, 0.6, 0.3)`
  - ❌ Wrong: `"sun_color": (255, 153, 76)`
  
- **Fog/Shadow colors:** Use 0-255 range
  - ✅ Correct: `"fog_color": (230.0, 100.0, 35.0)`
  - ❌ Wrong: `"fog_color": (0.9, 0.39, 0.14)`

**Colors too saturated or weird:**
- Verify you're not exceeding 1.0 for light colors (unless intentionally going for overbright effect)
- Check that RGB channels are balanced appropriately

**Scene has wrong color tint:**
- Check `ambient_color` - it tints the entire scene
- Verify fog color matches your intended atmosphere
- Ensure shadow color isn't adding unintended color cast

---

### Fog issues

**Fog obscures everything:**
- Increase `fog_end` distance (higher = fog further away)
- Lighten `fog_color` values (closer to white = less obscuring)

**No visible fog:**
- Decrease `fog_end` distance (fog appears closer)
- Ensure `fog_color` contrasts with scene (dark fog in bright scene shows better)

**Fog color looks wrong:**
- Verify using 0-255 range (not 0-1)
- Match fog color to light colors for cohesive atmosphere
- Remember fog is additive - very bright fog colors wash out distant objects

---

### Shadows issues

**Shadows too dark/harsh:**
- Reduce `shadow_alpha` (lower = more transparent)
- Increase fill light intensities (fills brighten shadowed areas)
- Add blue tint to `shadow_color` instead of pure black

**Shadows barely visible:**
- Increase `shadow_alpha` (higher = more opaque)
- Darken `shadow_color` values
- Lower `ambient_color` (high ambient washes out shadows)

**Shadows wrong color:**
- Verify using 0-255 range for `shadow_color`
- Pure black `(0, 0, 0)` is neutral but harsh
- Cool tints `(15, 20, 30)` look more natural

---

## Tips & Best Practices

### Starting Out

**Start with vanilla configs** rather than creating from scratch:
- Copy an existing Chicago config that's closest to your desired mood
- Modify one parameter at a time to understand its effect
- Test in-game frequently to see changes

**Use partial configs** - only specify parameters you want to change:
```python
{
    "time_of_day": TimeOfDay.EVENING,
    "weather": Weather.CLEAR,
    "sun_color": (1.0, 0.7, 0.4),  # Only changing sun color
    "fog_color": (255.0, 150.0, 80.0)  # And fog color
    # Everything else keeps Chicago's vanilla values
}
```

---

### Color Theory

**Complementary color contrast** creates natural-looking scenes:
- Warm sun (orange/yellow) + cool fills (blue) = realistic sunset
- Cool sun (blue-white) + neutral fills = overcast day
- Matching all colors = stylized/monochromatic look

**Match fog to sun** for atmospheric coherence:
- Orange sunset sun → orange fog
- Cool moonlight → blue-tinted fog
- Bright noon sun → light blue atmospheric haze

**Shadow subtlety:**
- Pure black shadows `(0, 0, 0)` look harsh and unrealistic
- Tinted shadows (especially cool blues) appear more natural
- Shadow tint simulates ambient light bouncing into shadowed areas

---

### Lighting Angle Strategy

**Sun heading and pitch affect mood dramatically:**
- **Low pitch (0.1-0.5):** Long shadows, dramatic lighting, sunrise/sunset feel
- **Medium pitch (0.6-1.0):** Balanced lighting, afternoon feel
- **High pitch (1.2-1.57):** Short shadows, overhead lighting, noon feel

**Fill light placement:**
- Position fills opposite or perpendicular to sun for best shadow softening
- Keep fill lights dimmer than sun (typically 0.5-0.8 when sun is 1.0)
- Use at least two different heading angles for three-point lighting

**Direction matters less** when pitch is very high (overhead lighting) or lights are very dim (night).

---

### Technical Workflow

**Enable debug mode** to see all lighting values:
```python
debug_lighting = True  # In your settings
```
This outputs all computed values to help understand what's actually being applied.

**Test matrix systematically:**
- Modify one time/weather combination at a time
- Switch to that specific time/weather in-game to verify
- Don't assume changes to Evening/Clear affect Evening/Cloudy

**Value range experimentation:**
- Standard ranges (0-1 for lights, 0-255 for atmosphere) are safe
- Values slightly outside these ranges can work for subtle effects
- Extreme values (e.g., `sun_color: (40.0, 0.0, 40.0)`) create stylized looks

---

### Common Patterns

**Sunset/Sunrise:**
- Low sun pitch (0.2-0.5)
- Warm sun color (high red, medium-high green, low blue)
- Cool fill colors (opposite)
- Warm fog matching sun
- Warm-tinted or neutral shadows

**Noon:**
- High sun pitch (1.0-1.5)
- Bright white-ish sun (0.9-1.0 on all channels)
- Moderate fill lights
- High ambient color
- Light fog, moderate shadows

**Night:**
- Very dim all lights (0.05-0.15 range)
- Cool color tint (more blue)
- Very low ambient (0.03-0.08)
- Dark fog
- Solid black or very dark shadows

**Overcast/Cloudy:**
- Reduce sun intensity (dimmer than clear weather)
- Increase ambient relative to sun (reduces contrast)
- Cool color temperature throughout
- Moderate-heavy fog
- Lower shadow alpha (softer shadows)

---

### Reference Chicago Configs

The vanilla Chicago lighting provides excellent templates for different moods. Use `debug_lighting = True` to dump all 16 configurations, then use them as starting points for your custom lighting.

**Most useful Chicago configs to reference:**
- **Noon/Clear:** Bright, neutral baseline
- **Evening/Cloudy:** Classic warm sunset
- **Night/Clear:** Moonlit scene
- **Morning/Rain:** Overcast, cool-tinted

---

### Iteration Tips

**Make backups** before experimenting with extreme values - easy to lose track of what worked.

**Document your choices** with comments explaining design intent:
```python
{
    # Golden hour sunset - warm directional light with cool sky fill
    "time_of_day": TimeOfDay.EVENING,
    "weather": Weather.CLEAR,
    "sun_heading": 4.5,
    "sun_pitch": 0.3,    # Low angle creates long shadows
    # ... etc
}
```

**Test edge cases:**
- Switch between all 4 weather types for your time of day
- Drive toward/away from sun to see how heading affects shadows

---
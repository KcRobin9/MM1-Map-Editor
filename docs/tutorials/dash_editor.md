# Dash Editor Tutorial

The Dash Editor builds and tunes a car's cockpit ("Driver") view - the dashboard, steering wheel, gauges and roof you see from the in-car camera. This guide covers loading a cockpit into Blender, tuning the gauges, swapping parts and textures between cars, and packing the result into the game.

The editor is its own N-panel tab, **Dash Editor**, next to the Car Editor.

## Table of Contents
- [What Is the Cockpit Dash?](#what-is-the-cockpit-dash)
- [The Seven Parts](#the-seven-parts)
- [What the Tach and Damage Needles Are](#what-the-tach-and-damage-needles-are)
- [Quick Start](#quick-start)
- [The Panels](#the-panels)
- [Swapping Parts Between Cars](#swapping-parts-between-cars)
- [Reskinning Dashboard Textures](#reskinning-dashboard-textures)
- [The .MMDASHVIEW Config](#the-mmdashview-config)
- [The .POVCAMCS Camera Config](#the-povcamcs-camera-config)
- [How Packing Works](#how-packing-works)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## What Is the Cockpit Dash?

When you drive in the in-car view, the game draws a small 3D scene in front of the camera: a dashboard with gauges, a steering wheel, and a roof strip. In the engine this is one object, `mmDashView`.

The cockpit is separate from the car body. The body lives in `{CAR}/` (edited in the Car Editor); the cockpit lives in `{CAR}_DASH/` and has its own config files. You can edit a car's cockpit without touching its body.

A dash is made of three things:

| Thing | Where | What it is |
|-------|-------|-----------|
| 7 BMS meshes | `{CAR}_DASH/` | the 3D dashboard, wheel, roof, gauge needles |
| `{CAR}.MMDASHVIEW` | `TUNE/` | placement + gauge mapping (text) |
| `{CAR}_DASH.POVCAMCS` | `TUNE/` | the cockpit camera (text) |

The editor loads all three, lets you edit them visually, and writes them back.

---

## The Seven Parts

A `{CAR}_DASH/` folder always contains these seven meshes:

| Part | Mesh file | What it is |
|------|-----------|-----------|
| Dashboard | `DASH.BMS` | the main dash panel (the gauge faces are painted on it) |
| Roof | `ROOF.BMS` | the windshield-top / visor strip |
| Steering Wheel | `WHEEL.BMS` | turns with your steering input |
| Gear Indicator | `GEAR_INDICATOR.BMS` | the N / 1-8 / R / P / D readout |
| Speed Needle | `SPEED_NEEDLE.BMS` | the speedometer pointer |
| Tach Needle | `TACH_NEEDLE.BMS` | the tachometer pointer |
| Damage Needle | `DAMAGE_NEEDLE.BMS` | the damage gauge pointer |

---

## What the Tach and Damage Needles Are

These two confuse people, so here is what they do:

- **Tach needle** is the tachometer pointer. A tachometer shows engine **RPM** (how hard the engine is revving), not speed. It rises as you accelerate in a gear and drops when the game shifts up. It is driven by the engine's live RPM, full-scale at `Max RPM` (stock cars use 8000).
- **Damage needle** is the damage gauge pointer. The game tracks how wrecked your car is from crashes; this needle sweeps from "fine" toward "wrecked" as damage builds up. It is driven by the car's current damage value.

All three needles (speed, tach, damage) work the same way: a small arrow mesh that pivots around its base. The game rotates each one between a rest angle (gauge reads zero) and a full angle (gauge maxed out). That pair of angles is the needle sweep, and setting it is most of what the Gauges panel does.

---

## Quick Start

1. Launch Blender with the project (`Shift+W` in VSCode).
2. Open the **Dash Editor** tab in the N-panel (press `N` in the viewport).
3. Pick a **Car** (e.g. Beetle) and click **Load Dash**.
4. The cockpit appears, assembled and textured. Drag the **Value** slider in the Gauges panel to sweep the needles and turn the wheel.
5. Click **Look Through Camera** in the Camera panel to see the player's view.
6. Make changes, then click **Export Dash** or **Create AR + Start Game**.

*Note: Blender has no hot-reload. If you change editor code, close Blender and relaunch. Editing a dash needs no relaunch - just Load and Export.*

---

## The Panels

### Dash
- **Car** - dropdown of every car that has a `{CAR}_DASH/` folder.
- **Load Dash** / **Clear** - build or remove the cockpit in the scene.
- **Part list** - click a part to select it in the viewport.
- **New From Template** - type a custom car name and click **Create** to seed a fresh dash from the Mustang template.

Everything is parented to a small DASH root empty. Moving the root moves the whole cockpit; moving a child moves one part.

### Gauges
- **Value** slider (0 to 1) - sweeps all three needles from rest to full and turns the wheel, so you can check the full range in Blender.
- **Reset Gauges** - return the needles to rest.
- **Needle Sweep (radians)** - each gauge has a **Min** angle (gauge reads zero) and a **Max** angle (gauge maxed out). The needle's live position is between these. Increase the gap to make a gauge sweep further; swap which value is larger to flip its direction.
- **Scale** - `Max Speed` and `Max RPM` set the value at which the speed/tach needles reach their Max angle. `Min Speed` is a small dead-zone at the bottom of the speedo. `Wheel Factor` sets how far the steering wheel turns per unit of input.

*Note: angles are in radians, not degrees. A quarter turn is about 1.57; a half turn about 3.14. The stock Beetle uses Speed Min 6.54, Max 3.16 - Min is larger than Max, so its speedo sweeps clockwise.*

### Placement
*(Collapsed by default.)* Select a part, then move it with `G` or type exact numbers into the **Location** field. On export, each part's position is read from the viewport. You can also enter Edit Mode on a part to reshape its mesh; it round-trips back to BMS on export.

*Note: the Dashboard and Gear Indicator carry their position in their geometry, so they sit at the root. For needles, move them to place the gauge pivot; the needle angle is set in the Gauges panel.*

### Camera
*(Collapsed by default.)* The dash is only seen through the cockpit camera, so framing matters.
- **Look Through Camera** - switch the viewport to the cockpit camera to see the player's view.
- **FOV** - field of view in degrees (stock 60).
- **Pitch** - camera downward tilt in radians.
- **Offset** - camera position in the car (game coordinates: x = side, y = height, z = forward/back).
- **Near Clip** / **Far Clip** - the camera's visible distance range.

### Customize
*(Collapsed by default.)* Swap parts between cars and reskin textures - see the next two sections.

### Export
- **Export Dash** - writes the meshes to `SHOP/BMS/{CAR}_DASH/`, the configs to `SHOP/TUNE/`, and any swapped/reskinned textures to `SHOP/TEX16A/`. No game launch.
- **Create AR + Start Game** - exports, packs everything into `!!!!!!!!!!{CAR}_DASH.ar`, and launches the game.

---

## Swapping Parts Between Cars

You can borrow any dash part - most usefully the steering wheel - from another car.

**Workflow:**
1. Load a dash.
2. Open the **Customize** panel and pick a **Source** car.
3. Click **Swap Steering Wheel**, or select any part and click **Swap Selected**.

The swapped-in part keeps the current car's texture names but uses the source car's mesh and skin. The source texture is packed into the override AR under the current car's texture name, so it works in-game with no extra setup.

*Note: the swapped part uses the source car's UV layout, so a borrowed texture may not line up perfectly. It will not crash. To keep the current car's own look instead, reskin the slot afterwards (below).*

---

## Reskinning Dashboard Textures

Most of a dashboard's look is its texture, so you can change the look just by replacing the image - no mesh editing needed. This works like the polygon texture dropdown: pick a texture and it applies.

**Workflow:**
1. Select the part whose texture you want to change (e.g. the Dashboard).
2. In the material list, set the active material slot to the texture you want to replace (the Dashboard has three: left, middle, right). The **Customize** panel shows the active slot name.
3. In the **Customize** panel, pick a texture from the **Dash Texture** dropdown. It lists every dash texture from every car (dash panels, needles, steering wheels, gear digits) with friendly labels like `VPMUSTANG99 · Dash Middle`.

The chosen texture applies to the active slot immediately and is packed into the override AR under the existing slot name. Because it reuses that name, it overrides the stock pixels with no texture-sheet changes.

To use your own artwork instead, pick a `.DDS` file under **Or a custom .DDS** and click the brush button.

*Note: reskinning replaces one slot at a time, and keeps the slot's name - the dropdown just supplies different pixels. Keep custom images the same size/format as the texture you replace.*

---

## The .MMDASHVIEW Config

This text file (in `TUNE/`) holds the placement and gauge mapping. The editor reads it on Load and rewrites only the fields it manages on Export, leaving every other line untouched. The stock Beetle, for reference:

```
mmDashView :17da8aec {
    MaxSpeed 140                          # speed at full speedo deflection
    MaxRPM 8000                           # RPM at full tacho deflection
    DashPos 2.328e-010 0.477 -1.128       # where the whole cockpit sits (car-local)
    RoofPos 0 0.14 0                       # roof offset, relative to the dash
    WheelOffset -0.3372 0.1835 0.2795      # steering-wheel position
    RPMPos -0.631 -0.314 -1.297            # tach needle pivot
    RPMMinRot 6.3                          # tach needle angle at 0 RPM
    RPMMaxRot 2.98                         # tach needle angle at max RPM
    SpeedPos -0.423 0.232 0.003            # speed needle pivot
    SpeedMinRot 6.54                       # speedo angle at 0
    SpeedMaxRot 3.15998                    # speedo angle at max speed
    WheelFact 1                            # steering-wheel turn factor
    DamagePos -1.065 -0.42 -1.631          # damage needle pivot
    DamageMinRot -6.29                     # damage angle at 0 damage
    DamageMaxRot -9.29                     # damage angle at full damage
    DashCamOffset 0 1.2 -0.7               # camera offset hint
    MinSpeed 10                            # speedo dead-zone
}
```

Each value maps to a control: the `*Pos` fields are the part positions (move them in the viewport), the `*MinRot`/`*MaxRot` fields are the Needle Sweep, and `MaxSpeed`/`MaxRPM`/`MinSpeed`/`WheelFact` are the Scale fields.

---

## The .POVCAMCS Camera Config

A separate `TUNE/` file for the cockpit camera. The editor manages `m_Offset`, `m_cameraFOV`, `m_Pitch`, `m_cameraNear` and `m_cameraFar`; the rest is left untouched. A trimmed example:

```
PovCamCS :07538de0 {
    m_Offset 0 1.176 0.34       # camera position in the car
    m_Pitch -0.029             # downward tilt (radians)
    TrackTo 0 1.04 0.16        # point the camera looks at
    m_cameraFOV 60             # field of view (degrees)
    m_cameraNear 0.1           # near clip
    m_cameraFar 1600           # far clip
}
```

---

## How Packing Works

The editor builds one self-contained override archive:

```
!!!!!!!!!!{CAR}_DASH.ar
 BMS/{CAR}_DASH/*.BMS          (the 7 meshes)
 TEX16A/*.DDS                  (swapped / reskinned textures, if any)
 TUNE/{CAR}.MMDASHVIEW
 TUNE/{CAR}_DASH.POVCAMCS
```

The ten leading `!` make the file win over the stock car, so your cockpit overrides it. Because the file is named `{CAR}_DASH`, it never overwrites the car-body AR the Car Editor makes; both load together. To remove a dash override, delete its `!!!!!!!!!!{CAR}_DASH.ar` from `MidtownMadness/`.

*Note: dash part positions use the same coordinate convention as car meshes, not the world convention used for props and city objects. The editor handles the conversion both ways.*

---

## Troubleshooting

**Dash loads but a part is missing**
- That mesh is not in the `{CAR}_DASH/` folder. The editor loads whatever is present.

**Textures look blank**
- The car's dash DDS is not in `resources/editor/TEXTURES/`. The mesh still loads and exports fine; only the Blender preview lacks the image.

**A needle points the wrong way**
- Swap that gauge's Min and Max angles, or nudge them. Use the Value slider to line the needle up with the painted dial.

**No POV camera / "Look Through Camera" says none exists**
- The car had no `.POVCAMCS`. Load a car that has one, or copy a template into `TUNE/`.

**A swapped part's texture looks off**
- The borrowed mesh uses its own UV layout. Reskin the slot, or accept the current car's texture by not relying on the source skin.

**Gear indicator never changes in-game**
- Expected for now. The editor treats the gear readout as a single mesh; the engine's multi-digit gear variants are not authored yet.

**Changes do not show in-game**
- Use **Create AR + Start Game** (or Export, then pack). Confirm `!!!!!!!!!!{CAR}_DASH.ar` exists in `MidtownMadness/`.

---

## Tips & Best Practices

- Start from **Load Dash** on a stock car (the Beetle is a clean reference) before authoring a new one.
- Use the **Value** slider to check gauge sweeps without launching the game.
- Frame with **Look Through Camera** often: tweak, look, repeat.
- Tune one gauge at a time - set Min at rest, then Max, then check with the slider.
- Angles are in radians (about 1.57 per quarter turn).
- Move the root to shift the whole cockpit; move children for individual parts.
- The override AR never edits stock files and is easy to delete.
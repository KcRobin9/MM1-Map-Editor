# Road Builder Tutorial

The Road Builder grows roads from a drawn line ("spine") and then auto-generates everything a city block needs around them - AI traffic lanes, sidewalk props, building facades, junctions, and grass. This guide covers drawing roads, shaping their cross-section, and the one-click automation that turns a set of roads into a connected, decorated network.

It lives in the **Road Builder** N-panel tab, with collapsible sub-panels for each stage.

## Table of Contents
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Spines (Drawing Roads)](#spines-drawing-roads)
- [Cross-Section (The Road Profile)](#cross-section-the-road-profile)
- [Bake (Geometry)](#bake-geometry)
- [AI Traffic](#ai-traffic)
- [Street Props](#street-props)
- [Facades](#facades)
- [Junctions & Fill](#junctions--fill)
- [One-Click Build](#one-click-build)
- [Coordinate Notes](#coordinate-notes)
- [Finetuning Guide](#finetuning-guide)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## How It Works

A road is a **spine**: a Blender curve (named `RS_*`) you draw and extend. The spine carries a **cross-section** - lane count, sidewalks, curbs, walls, median - stored as properties on the curve. **Baking** extrudes that profile along the spine into game polygons (named `P*`, in the "Road Meshes" collection) that export like any hand-placed map polygon.

On top of the geometry, the automation panels read the same spine and generate matching content: AI lanes, props, facades, junctions, and grass. Everything generated is **additive** and either tagged for clean removal or routed into the existing AI Streets / Prop Editor / Facade Editor so it inherits their export pipelines.

A typical road is made of many short **segments** (each segment = one piece of the spine between two points). Most generators work segment by segment so they follow curves.

---

## Quick Start

1. Launch Blender with the project (`Shift+W` in VSCode).
2. Open the **Road Builder** tab (press `N` in the viewport).
3. Click **New Spine** - a short road appears at the 3D cursor.
4. Extend it: in the **Spine** panel, set a length/angle and click **End →** a few times to draw the road.
5. In the **Bake** panel, click **Bake Road → Polygons**.
6. Open **AI Traffic** → **Generate AI Street**, **Street Props** → **Place Street Props**, **Facades** → **Place Facades**.
7. Or skip steps 5-6: in the **Bake** panel, enable the toggles and click **Build All**.

*Note: Blender has no hot-reload. If you change editor code, close Blender and relaunch. Drawing/baking roads needs no relaunch.*

---

## Spines (Drawing Roads)

The **Spine** panel draws and edits the road line.

- **New Spine** - creates a 2-point spine at the 3D cursor (pointing +Y).
- **Extend** - set **Length**, **Turn** (degrees, + right / - left), **Slope** (degrees), then click **← Start** or **End →** to add a vertex off that end.
- **At Cursor** - append the 3D cursor as the next vertex.
- **Undo** - remove the first/last vertex.
- **Lift** - raise/lower the whole spine for easier editing. *Note: lift moves the real geometry, so if you bake while lifted the road bakes at the lifted height - reset lift to 0 before baking unless you want the offset.*
- **Delete Spine** - removes the spine and its baked polygons.

Each segment is colored differently and the ends are marked green (start) / red (end) so you can see direction.

*Note: Snap to Terrain is shared with the AI Paths tab. Enable it there and new vertices snap to the ground here too.*

---

## Cross-Section (The Road Profile)

The **Cross-Section** panel defines what gets baked. Pick a **Road Type** preset (Road Test, Freeway, Custom) and **Apply**, or set each part manually. Each part has an enable toggle, dimensions, a texture, and tiling.

| Part | Controls |
|------|----------|
| Road | lane count, lane width, texture (AUTO picks R2/R4/R6 by lane count), tiling, angle |
| Curb | width, height, texture, tiling |
| Sidewalk | width, height, texture, tiling, side (Both/Left/Right) |
| Wall | height, texture, side, tiling |
| Median | width, texture (grass by default) |
| Banking | auto-bank on curves + max degrees |

Width matters for the automation: sidewalk and facade placement are measured from the road centre using `lanes × lane_width / 2 + curb + sidewalk`.

*Note: new spines start with a minimal curb. Set Curb Width to around 0.8 for a kerb you can see and drive against.*

---

## Bake (Geometry)

The **Bake** panel turns the spine into polygons.

- **Bake Road → Polygons** - generate the geometry. Re-baking clears the old polygons first.
- **Clear Baked Polygons** - remove this spine's baked polygons.
- The baked road uses **curve-following UVs** so textures don't stretch or seam through bends.

The **One-Click Build** box (toggles + **Build All** / **Build Network**) is covered in [One-Click Build](#one-click-build).

*Note: load your city before baking. Baking without a city or texture folder loaded falls back to the default texture pool.*

---

## AI Traffic

The **AI Traffic** panel generates AI lanes that follow the spine, so traffic and cops can drive the road. Lanes are created as AI Street curves (`ST_*`) grouped together, and you edit/export them afterwards in the **AI Paths** tab.

- **Two-Way** - lanes left of centre run the opposite direction (an opposing pair). Off = one-way.
- **Intersection ends (Start / End)** - what traffic does at each end: Continue / Yield / Stop / Stop Light.
- **Alley**, **Traffic Blocked**, **Peds Blocked** - applied to the generated lanes.
- **Generate AI Street** - lane count and width come from the spine.

*Note: keep generated streets at 0 sidewalks (the exporter does this). The reverse-AI-streets feature combined with 0 sidewalks has a known crash, so avoid that specific combination.*

---

## Street Props

The **Street Props** panel lines the sidewalk(s) with furniture at a fixed interval, facing the road.

- **Prop** - lamp posts (blue/green/red/short), highway light, telephone pole, trees, fire hydrant, bench, mailbox, parking meter, trash can.
- **Interval** - distance between props.
- **Side** - Both / Left / Right, plus **Stagger Sides** so the two rows alternate.
- **Lateral Nudge / Height Nudge** - fine position tweaks.
- **Rotate** - turn the facing off perpendicular-to-road.
- **Flags** - AUTO (lights glow, others breakable) or pick a specific collision flag.

Placed props become normal Prop Editor objects, so they inherit the full prop export / BNG pipeline.

---

## Facades

The **Facades** panel lines a building/wall facade along the road behind the outer sidewalk.

- **Facade** - building or wall fronts (Old Town, Downtown, The Loop, Hillside, Residential, Industrial, plain walls).
- **Panel Width** - width of each facade panel along the wall.
- **Side** - Both / Left / Right.
- **Setback** - gap from the sidewalk edge to the wall.
- **Height** - raise/lower the base.
- **Flip Facing** - flip which way the wall faces.
- **Lit** - a brighter, lit-windows look.

Facades follow curves (one panel per sub-segment) and become Facade Editor objects, inheriting the FCD export pipeline.

*Note: which way a wall faces depends on the facade and the road direction. If a wall faces away from the road, toggle **Flip Facing**.*

---

## Junctions & Fill

The **Junctions & Fill** panel builds intersections and ground patches. Most of it works at the **3D cursor** - place the cursor where you want the junction, then click.

### Junction Preset (spawn arms)
Spawns a ready intersection skeleton: several road spines radiating from the cursor plus the centre junction patch.
- **Preset** - 4-Way Cross, T-Junction, Y-Junction, or **Custom N-Way** (set arm count + rotation).
- **Arm Length** - how long each road arm is.
- After spawning, Bake / Build each arm as normal.

### Junction (road patch)
Bakes one junction at the cursor over an existing crossing.
- **Size** - side length of the junction patch (tune to cover the crossing).
- **AI Type** - intersection type applied to any AI lanes ending at the junction.
- **Lights** - a traffic light at each corner. **Crosswalks** - a zebra crossing across each approaching road.
- **Create Junction** - bakes it at the cursor.
- **Snap Distance** + **Auto Junctions** - instead of placing by hand, scan the whole scene and make a junction everywhere roads from two different spines meet within the snap distance.

### Grass
- **Grass Patch** - a rotatable grass rectangle at the cursor (park / median / verge).
- **Grass Verge** (shown when a spine is active) - a continuous grass strip alongside the road beyond the sidewalk.
- **Clear Junctions & Fills** - removes every junction patch, crosswalk, and grass fill the Road Builder made (it does not touch your roads or hand-placed polygons).

---

## One-Click Build

In the **Bake** panel's *One-Click Build* box, the toggles (Bake / AI / Props / Facades / Junctions) choose what runs.

- **Build All (this spine)** - runs the enabled steps for the active spine.
- **Build Network (all/selected)** - runs the enabled steps for every road spine (or just the selected ones), then auto-wires junctions where roads meet.

**Workflow for a whole block:**
1. Draw your roads (or spawn junction presets).
2. Set the cross-section + the AI/Props/Facades settings once.
3. Enable the toggles and click **Build Network**.

---

## Coordinate Notes

Spines, baked road polygons, AI lanes, junctions, and grass all live in **Blender world space** and convert to game space at export. You don't deal with this directly, but it's why spine positions feel like the rest of the map editor. Prop, facade, and junction offsets are converted with the standard `(x, z, -y)` mapping.

The compass for spawning arms: 0° = +Y (north), 90° = +X (east).

---

## Finetuning Guide

Everything generated is a first pass meant to be calibrated by eye in-game. The most useful knobs:

- **Junction Size** - make the patch just cover the crossing; too small leaves gaps, too large overlaps the roads.
- **Facade Flip Facing / Setback** - get walls facing the road and standing at the right distance behind the sidewalk.
- **Prop Rotate / Interval / Height Nudge** - orient lamp arms over the road and space furniture naturally.
- **Crosswalk** - depth and tiling are first guesses; if stripes look wrong, adjust after testing.
- **AI Intersection ends** - set Stop/Stop Light where roads meet so traffic behaves.
- **Grass Verge Width / Height** - widen for green boulevards; nudge height on uneven ground.

Re-running a generator re-reads the current settings, so tweak a value and re-place to compare.

---

## Troubleshooting

**New vertices don't snap to the ground**
- Snap to Terrain is shared with the AI Paths tab. Enable it there, or place vertices manually.

**The road has no visible curb**
- New spines start with a minimal curb width. Set Curb Width in the Cross-Section panel to around 0.8.

**Baked road has no texture**
- A city/texture folder wasn't loaded when you baked. Load your city first, then re-bake.

**Facade wall faces the wrong way**
- Toggle **Flip Facing** in the Facades panel.

**Junction doesn't cover the crossing**
- Increase **Size**. For auto-junctions, increase **Snap Distance** so the road ends are seen as meeting.

**Auto Junctions made nothing**
- It only junctions where ends from *two different* roads are within the snap distance. Extend roads so their ends actually meet, or raise the snap distance.

**Existing props or facades seem to be missing**
- Placement re-reads the existing groups and adds to them, so nothing is deleted. Check the Prop and Facade editors to confirm what is in the scene.

**Too many junction/grass polygons**
- Use **Clear Junctions & Fills** to remove all auto-baked patches/crosswalks/grass and start over.

---

## Tips & Best Practices

- Draw the spine first, get the cross-section right, then automate - the generators read the spine's dimensions.
- Reset **Lift** to 0 before baking unless you want the road raised.
- Set AI/Props/Facades settings once, then use **Build Network** for the whole map.
- Use **Junction Presets** to start intersections, then Build each arm.
- Place the 3D cursor precisely (Shift+Right-click) before junction/grass operations.
- Calibrate one road fully in-game, then reuse those settings everywhere.
- **Clear Junctions & Fills** only removes auto-baked extras, so it's safe to iterate.

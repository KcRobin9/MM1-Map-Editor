# roadnet — single-source-of-truth road-network compiler

The Map-Editor analogue of Angel Studios' unreleased City tool. You edit **one graph**
(intersections + bidirectional road sections); the compiler derives **every** product from
the **same vertices**, so geometry, AI, intersections and cells cannot drift.

The old tooling kept geometry, AI paths and intersections in separate passes that drifted
apart. Deriving them all from one graph removes that whole class of bug at the root.

```
RoadNetwork graph  (the ONLY thing you edit)
  Node { id, pos }                                  -> intersection
  Edge { a, b, lanes_fwd, lanes_rev, sidewalks,     -> road section
         width, divided, alley, speed, isect_type }
        │  sweep ONE bidirectional cross-section along the bowed centreline
        ├─ drivable mesh quads          (road_mesh_quads / intersection_quads)
        ├─ mmRoadSect (.road)           lanes/dir + sidewalks + VertXDirs/VertZDirs
        ├─ mmIntersection (.int)        Sinks/Sources/Paths/Directions + Path/EdgeIndex
        ├─ CHICAGO.map (.map)           street list
        └─ cell ids                     one per section (Type-1) + per intersection (Type-2)
```

## Why this exists

The old tooling had **three disconnected tracks** (`road_builder` geometry,
`road_automation` AI offset-curves, `street_editor` half-`mmRoadSect`) that drift apart.
That drift is the per-junction swerve / 3-lane frozen-`RoadDist` / orbit bug class. Here
the mesh corners **are** the AI `Vertexs[]`, so they cannot disagree.

## Faithfulness anchors (Open1560)

| Field(s) | Mirrored from |
|---|---|
| `CenterVerts`, `RoadLength`, `LaneWidths`, `LaneLengths` | `aiPath::CalcCenterVerts` |
| `Sinks/Sources/Paths/Directions`, `EdgeIndex`, `PathIndex` | `aiIntersection::CreateRoadMap` |
| `.road` field order + `Vertexs[]` layout + fwd/back swaps | `read_write.write_ai_paths` |
| frame convention `VertXDir=(f.z,0,-f.x)`, `VertZDir=-forward` | verified vs `Street0.road` |
| text format (indent, `[ ]` lists, `( )` tuples, `%.2f`) | `helpers.MiniParser` |

## Run it (no Blender needed)

```
cd MM1-Map-Editor
python -m src.game.mapgen.roadnet.demo                 # 3x3 grid, self-test
python -m src.game.mapgen.roadnet.demo --out C:/tmp/AI --cols 5 --rows 5
```

Programmatic:

```python
from src.game.mapgen.roadnet import grid_city, RoadNetworkCompiler

net = grid_city(4, 4, spacing=120.0)
net.edges[3].lanes_fwd, net.edges[3].lanes_rev = 3, 3   # a 3-lane road
compiled = RoadNetworkCompiler().compile(net)
print(compiled.report())                                 # validation summary
compiled.write_ai("out/AI")                              # streets/*.road, intersections/*.int, CHICAGO.map
quads = compiled.road_mesh_quads()                       # drivable mesh (same vertices)
```

In Blender: the **"Road Net"** sidebar tab (its own tab, additive — nothing else changes).
**"Build Demo Grid City"** generates the city as **real textured, exportable polygon
objects** (named `P<bound>`, with DDS materials + the editor's custom props) plus the AI
files — so it shows textured in the viewport AND exports through the normal **Export
Polygons → run build** flow. (Or place `RNODE_<id>` + `RLINK_<a>_<b>` empties and use
"Build From Empties".) Objects are authored in the exporter's coordinate convention
(`game→blender = (x, -z, y)`), so the exported geometry lands exactly where the AI expects.

Feed the existing build pipeline via the adapter:

```python
from src.game.mapgen.roadnet.pipeline_adapter import to_polygon_specs, write_ai_to_devmap
polys = to_polygon_specs(compiled)     # -> create_polygon()/save_mesh()
write_ai_to_devmap(compiled)           # -> Folder.MidtownMadness.DevCityMap
```

## Build a REAL, drivable city (geometry + bounds + textures + AI)

`roadnet` plugs into the full build pipeline so a graph becomes a textured, bounded,
drivable MM1 city — collision bounds / cells / portals / TSH / `.AR` are produced by the
existing pipeline, the AI `.road`/`.map` are written by roadnet.

**One setting** in `src/USER/settings/main.py`:

```python
ROADNET_CITY = (4, 4)     # a 4x4 grid city; or a RoadNetwork, or a zero-arg callable
```

Then run the build (`MAP_EDITOR_ALPHA_v1.py`) exactly as usual. It will:
- replace the hand-authored city (like `MAP_SPEC_FILE` does),
- emit zoned geometry via `create_polygon`/`save_mesh` — carriageway (`R2/R4/R6`),
  sidewalks (`SDWLK2`), grass base (`T_GRASS`); spawn on the first intersection,
- run the normal bounds / cells / portals / HITID / TSH / `.AR` / launch steps,
- force `set_ai_streets = False` and write the roadnet AI (`Street*.road` + `{MAP}.map`)
  into the dev city-map folder, which the game compiles to `.BAI` at load.

For a custom layout, set `ROADNET_CITY` to a callable:

```python
def my_city():
    from src.game.mapgen.roadnet import RoadNetwork
    net = RoadNetwork("Downtown")
    a = net.add_node((0, 0)); b = net.add_node((200, 0)); c = net.add_node((200, 200))
    net.add_edge(a.id, b.id, lanes_fwd=2, lanes_rev=2)
    net.add_edge(b.id, c.id, lanes_fwd=1, lanes_rev=1)
    return net
ROADNET_CITY = my_city
```

The AI writer (`build_city.write_roadnet_ai`) takes `overwrite=False` to preserve any
`.road` you've hand-tweaked, and `write_intersections=True` to also drop `.int` files
(the game regenerates intersections at load, so they're optional).

## Module map

| File | Role |
|---|---|
| `graph.py` | `Node` / `Edge` / `RoadNetwork` + `grid_city()` |
| `geometry.py` | pure-Python vec/frame/sampling helpers |
| `roadsect.py` | cross-section sweep + `CalcCenterVerts` derivation -> two `PathData` |
| `intersections.py` | `CreateRoadMap` solver (atan2 sort, sink/source, indices) |
| `emit.py` | `.road` / `.int` / `.map` text emitters (MiniParser-faithful) |
| `validate.py` | invariant checks mirroring `read_write` |
| `network_compiler.py` | orchestrator graph -> `CompiledNetwork` (+ mesh + cells) |
| `pipeline_adapter.py` | bridge to `PolygonSpec` + the dev city-map folder |
| `demo.py` | standalone demo / self-test |

## v1 scope & honest limitations

**Done:** straight + multi-shape sections, per-direction lane counts, sidewalks, alley/
divided flags, endpoint pinch (lanes converge at nodes), full intersection routing,
coherent mesh + cell ids, validation, standalone self-test (0 errors on grid cities
incl. 2+1 / 3+3 / alley roads).

**Note — VertXDirs/VertZDirs are DERIVED, not authored.** Open1560 computes the frames
from `vertices + normals` at compile (`aiPath::AddPathVerts`, `VertZDir=~(Cv[i-1]-Cv[i])`,
`VertXDir=Normal % VertZDir`), bakes them into `.BAI`, and reads them back at runtime. This
package emits them only to match the canonical text dump (`read_write.write_ai_paths`); the
compiler recomputes them. The authored essentials are the **vertices + normals +
connectivity** — that is what `roadnet` gets right.

**Approximate / TODO:**
- `SubSectionDirs`/`SubSectionOffsets` are best-effort (not used by the cornering math).
- Endpoint pinch is a hard 0→full step at v0→v1; Chicago bows gradually. A smooth ramp is
  a one-line change in `roadsect._build_carriageway._scale` if needed.
- Elevation: v1 emits **flat** roads (`IsFlat=1`, `y=0`, normals up). Sloped roads need
  per-vertex `y` + recomputed sidewalk normals.
- `divided` cross-section: the flag is emitted but the geometry is not yet a true split
  carriageway with a median gap.
- **.road -> .BAI compile:** this package emits the canonical **text intermediate**
  (`.road`/`.int`/`.map`) — the exact input the city AI compiler consumes. Wiring that
  compile step into the build (gencity / the pipeline's BAI writer) is the remaining
  integration task; the text it consumes is now correct by construction.
- Cells/portals are produced as IDs here; driving the actual `.cells`/`.ptl`
  baker from these IDs (instead of post-export polygon adjacency) is the next step.

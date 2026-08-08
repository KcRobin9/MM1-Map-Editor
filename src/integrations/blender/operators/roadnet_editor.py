"""
Blender front-end for the single-graph road-network compiler (src/game/mapgen/roadnet).

Additive and self-contained: registers its own classes + scene props via
register_roadnet()/unregister_roadnet() and lives in its OWN sidebar tab ("Road Net").
inits.py calls register_roadnet() inside a try/except so a failure here can never break
the rest of the addon.

"Compile Demo Grid" / "Compile From Empties" build the city as **real, textured,
exportable polygon objects** — named `P<bound>`, carrying the same custom props
(`material_index`/`cell_type`/`tile_x`/`tile_y`/…) and DDS materials the editor's own
polygons use — so they show textured in the viewport AND export through the normal
"Export Polygons" → build flow. The AI `.road`/`.map` are written alongside.

(For a no-Blender, one-shot textured build set `ROADNET_CITY = (4,4)` in USER settings and
run MAP_EDITOR_ALPHA_v1.py — that path drives create_polygon/save_mesh directly.)
"""
from __future__ import annotations

from pathlib import Path

import bpy  # type: ignore

from src.game.mapgen.roadnet.graph import RoadNetwork, grid_city
from src.game.mapgen.roadnet.network_compiler import RoadNetworkCompiler
from src.game.mapgen.roadnet.build_city import iter_city_quads, stage_roadnet_ai
from src.game.mapgen.roadnet.presets import (
    build_preset, custom_bridge, scale_network, terrain_from_kind, PRESETS, _bow_edge, _scurve_edge)
from src.integrations.blender.utils import assign_map_editor_properties
from src.constants.folder import Folder

_ROADNET_TAG = "roadnet_generated"


# ── geometry helpers ─────────────────────────────────────────────────────────

def _game_to_blender(v):
    """
    game-space (x, y, z) -> Blender, the INVERSE of the exporter's blender_to_game
    (`transform_coordinate_system`: game = (bx, bz, -by)). So game->blender = (gx, -gz, gy).
    Authoring in this convention guarantees the exported geometry lands at exactly the
    game coords the AI .road files use — mesh and AI cannot drift.
    """
    return (v[0], -v[2], v[1])


def _texture_folder() -> Path:
    return Path(str(Folder.Resources.Editor.Textures))


def _apply_material(obj, texture: str, folder: Path) -> None:
    """Build a Principled material with the texture's DDS image node (viewport + export)."""
    path = folder / f"{texture}.DDS"
    mat = bpy.data.materials.get(texture) or bpy.data.materials.new(name=texture)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.active_material = mat
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    out = nodes.new("ShaderNodeOutputMaterial")
    links = mat.node_tree.links
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if path.exists():
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def _clear_previous(context) -> int:
    """Delete objects from a previous roadnet run (tagged), leaving hand-authored ones."""
    doomed = [o for o in bpy.data.objects if o.get(_ROADNET_TAG)]
    for o in doomed:
        bpy.data.objects.remove(o, do_unlink=True)
    return len(doomed)


def _make_quad_object(q, folder) -> "bpy.types.Object":
    verts = [_game_to_blender(v) for v in q.verts]
    faces = [tuple(range(len(verts)))]
    mesh = bpy.data.meshes.new(f"P{q.bound}")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"P{q.bound}", mesh)
    bpy.context.collection.objects.link(obj)
    uv_layer = obj.data.uv_layers.new(name="UVMap") if not obj.data.uv_layers else obj.data.uv_layers[0]
    assign_map_editor_properties(obj)
    obj["cell_type"] = str(q.cell_type)
    obj["material_index"] = str(q.material_index)
    obj["hud_color"] = q.hud_color
    obj.tile_x = 1.0          # actual UVs come from obj["bms_uvs"] below, not tile_x/tile_y
    obj.tile_y = 1.0
    obj.angle_degrees = 0.0
    # Explicit per-loop UVs (flip-synced) for both the viewport preview AND the exporter,
    # which reads obj["bms_uvs"] when present instead of recomputing from tile_x/tile_y.
    from src.game.mapgen.roadnet.build_city import quad_tex_coords
    tex = quad_tex_coords(q)                       # [u0,v0,u1,v1,u2,v2,u3,v3]
    for li, loop in enumerate(obj.data.loops):
        uv_layer.data[li].uv = (tex[2 * li], tex[2 * li + 1])
    obj["bms_uvs"] = tex
    obj[_ROADNET_TAG] = True
    _apply_material(obj, q.texture, folder)
    return obj


# ── shared build ──────────────────────────────────────────────────────────────

def _build(net: RoadNetwork, context, op, write_ai: bool) -> bool:
    try:
        compiled = RoadNetworkCompiler().compile(net)
    except Exception as exc:
        op.report({'ERROR'}, f"Compile failed: {exc}")
        return False

    removed = _clear_previous(context)
    folder = _texture_folder()
    created = []
    for q in iter_city_quads(compiled):
        created.append(_make_quad_object(q, folder))

    bpy.ops.object.select_all(action="DESELECT")
    for o in created:
        o.select_set(True)
    if created:
        context.view_layer.objects.active = created[0]

    msg = (f"{len(created)} textured polygons "
           f"({len(compiled.sections)} roads, {len(compiled.intersections)} ints"
           f"{f', replaced {removed}' if removed else ''})")

    if write_ai:
        try:
            stats = stage_roadnet_ai(compiled)
            msg += (f"; AI staged ({stats['staged']} roads) — it is copied into the dev "
                    f"folder when you run the build")
        except Exception as exc:
            op.report({'WARNING'}, f"polygons OK but AI staging failed: {exc}")

    errs = [i for i in compiled.validate() if i.severity == "ERROR"]
    if errs:
        op.report({'WARNING'}, f"{len(errs)} AI validation error(s)")
    op.report({'INFO'}, msg)
    return True


def _network_from_empties() -> RoadNetwork:
    """Build a network from RNODE_<id> empties + RLINK_<a>_<b> empties (see panel help)."""
    net = RoadNetwork(name="ViewportCity")
    for o in bpy.context.scene.objects:
        if o.name.startswith("RNODE_"):
            try:
                nid = int(o.name.split("_", 1)[1].split(".")[0])
            except ValueError:
                continue
            # blender (bx,by) -> game (x,z) = (bx, -by), inverse of game->blender (gx,-gz,gy)
            net.add_node((o.location.x, -o.location.y), node_id=nid, name=o.name)
    for o in bpy.context.scene.objects:
        if not o.name.startswith("RLINK_"):
            continue
        parts = o.name.split("_")
        if len(parts) < 3:
            continue
        try:
            a, b = int(parts[1]), int(parts[2].split(".")[0])
        except ValueError:
            continue
        if a in net.nodes and b in net.nodes:
            e = net.add_edge(a, b, lanes_fwd=int(o.get("lanes_fwd", 1)),
                             lanes_rev=int(o.get("lanes_rev", 1)))
            # PER-LINK bridge tuners read from the empty's custom props (set by Connect Nodes + the panel)
            e.deck_height = float(o.get("deck_height", 0.0))
            e.deck_profile = str(o.get("deck_profile", "arch"))
            e.bank_deg = float(o.get("bank_deg", 0.0))
            e.median_width = float(o.get("median_width", 0.0))
            e.sidewalk_fwd = bool(o.get("sidewalk_fwd", 1))
            e.sidewalk_rev = bool(o.get("sidewalk_rev", 1))
            e.alley = bool(o.get("alley", 0))
            e.tunnel_height = float(o.get("tunnel_height", 0.0))
            e.speed_limit = float(o.get("speed_limit", 15.0))
            e.intersection_type = (int(o.get("ix_a", 3)), int(o.get("ix_b", 3)))
            amp = float(o.get("curve_amp", 0.0))
            cyc = int(o.get("scurve_cycles", 1))
            if e.deck_height > 0.0 or amp != 0.0:
                e.num_verts = 15                          # densify so the arch / curve is sampled
            if amp != 0.0:
                if cyc >= 2:
                    _scurve_edge(net, e, amp, cyc)
                else:
                    _bow_edge(net, e, amp)
            elif e.deck_height > 0.0:
                _bow_edge(net, e, 0.0)                    # straight deck still needs a densified centreline
    return net


def _apply_city_levers(net) -> RoadNetwork:
    """
    Apply the scene-level CITY LEVERS to a CUSTOM-built network (demo grid + graph editor), so Blender can
    author full cities and not just flat grids: terrain profile + height, flat-climb ribbon, no-scenery,
    race opponents, a spawn point (RSPAWN_ empty) and ground zones (RZONE_ cube empties, kind from their
    "kind" prop). Presets set their own, so this runs ONLY for the custom builds.
    """
    s = bpy.context.scene
    t = terrain_from_kind(getattr(s, "rn_terrain", "flat"), float(getattr(s, "rn_terrain_height", 18.0)))
    if t is not None:
        net.terrain = t
    if getattr(s, "rn_flat_climb", False):
        net.flat_climb = True
    if getattr(s, "rn_no_scenery", False):
        net.no_scenery = True
    net.race_opponents = int(getattr(s, "rn_opponents", 0))
    for o in bpy.context.scene.objects:                  # RSPAWN_ empty -> spawn_near (game coords)
        if o.name.startswith("RSPAWN_"):
            net.spawn_near = (o.location.x, -o.location.y)
            break
    zones = []                                           # RZONE_ cube empties -> ground_zones
    for o in bpy.context.scene.objects:
        if not o.name.startswith("RZONE_"):
            continue
        hx = o.empty_display_size * abs(o.scale.x)
        hy = o.empty_display_size * abs(o.scale.y)
        cx, cz = o.location.x, -o.location.y
        zones.append((cx - hx, cz - hy, cx + hx, cz + hy, str(o.get("kind", "grass"))))
    if zones:
        net.ground_zones = zones
    return net


# ── operators ────────────────────────────────────────────────────────────────

class ROADNET_OT_compile_demo(bpy.types.Operator):
    bl_idname = "roadnet.compile_demo"
    bl_label = "Build Demo Grid City"
    bl_description = ("Build a grid city as textured, exportable polygons + write the AI. "
                      "Export via the normal Export Polygons flow")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene
        net = grid_city(int(s.roadnet_cols), int(s.roadnet_rows),
                        spacing=float(s.roadnet_spacing),
                        lanes_fwd=int(s.roadnet_lanes), lanes_rev=int(s.roadnet_lanes))
        _apply_city_levers(net)
        ok = _build(net, context, self, write_ai=s.roadnet_write_ai)
        return {'FINISHED'} if ok else {'CANCELLED'}


class ROADNET_OT_compile_empties(bpy.types.Operator):
    bl_idname = "roadnet.compile_empties"
    bl_label = "Build From Empties"
    bl_description = "Build a network from RNODE_*/RLINK_* empties as textured polygons + AI"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        net = _network_from_empties()
        if not net.nodes or not net.edges:
            self.report({'ERROR'}, "No RNODE_*/RLINK_* empties found")
            return {'CANCELLED'}
        _apply_city_levers(net)
        ok = _build(net, context, self, write_ai=context.scene.roadnet_write_ai)
        return {'FINISHED'} if ok else {'CANCELLED'}


def _preset_items(self, context):
    """Enum items = every named preset (bridges + cities), built fresh so new presets appear."""
    return [(k, k, "") for k in sorted(PRESETS)]


class ROADNET_OT_build_preset(bpy.types.Operator):
    bl_idname = "roadnet.build_preset"
    bl_label = "Build Preset"
    bl_description = "Build the selected named preset (bridge or city) as textured polygons + AI"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene
        try:
            net = build_preset(s.roadnet_preset)        # build_preset already applies ROADNET_SCALE
        except Exception as exc:
            self.report({'ERROR'}, f"Preset '{s.roadnet_preset}' failed: {exc}")
            return {'CANCELLED'}
        ok = _build(net, context, self, write_ai=s.roadnet_write_ai)
        return {'FINISHED'} if ok else {'CANCELLED'}


class ROADNET_OT_build_custom_bridge(bpy.types.Operator):
    bl_idname = "roadnet.build_custom_bridge"
    bl_label = "Build Custom Bridge"
    bl_description = "Build a bridge from the tuner sliders (deck height / profile / curve / lanes / span)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene
        try:
            net = custom_bridge(
                deck_height=s.rn_deck_height, deck_profile=s.rn_deck_profile,
                curve_amp=s.rn_curve_amp, scurve_cycles=int(s.rn_scurve_cycles),
                lanes_fwd=s.rn_lanes_fwd, lanes_rev=s.rn_lanes_rev,
                span=s.rn_span, num_verts=s.rn_num_verts, bank_deg=s.rn_bank)
            net = scale_network(net, s.rn_scale)
        except Exception as exc:
            self.report({'ERROR'}, f"Custom bridge failed: {exc}")
            return {'CANCELLED'}
        ok = _build(net, context, self, write_ai=s.roadnet_write_ai)
        return {'FINISHED'} if ok else {'CANCELLED'}


# ── panel ────────────────────────────────────────────────────────────────────

def _next_node_id() -> int:
    ids = []
    for o in bpy.context.scene.objects:
        if o.name.startswith("RNODE_"):
            try:
                ids.append(int(o.name.split("_", 1)[1].split(".")[0]))
            except ValueError:
                pass
    return (max(ids) + 1) if ids else 0


class ROADNET_OT_add_node(bpy.types.Operator):
    bl_idname = "roadnet.add_node"
    bl_label = "Add Node"
    bl_description = "Place a road-network NODE empty at the 3D cursor (auto-numbered)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        nid = _next_node_id()
        o = bpy.data.objects.new(f"RNODE_{nid}", None)
        o.empty_display_type = 'SPHERE'
        o.empty_display_size = 6.0
        o.location = context.scene.cursor.location
        o[_ROADNET_TAG] = True
        context.collection.objects.link(o)
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        context.view_layer.objects.active = o
        self.report({'INFO'}, f"Added RNODE_{nid}")
        return {'FINISHED'}


class ROADNET_OT_connect_nodes(bpy.types.Operator):
    bl_idname = "roadnet.connect_nodes"
    bl_label = "Connect Nodes"
    bl_description = "Link two selected node empties; the link carries its own deck/curve/lanes (edit below)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sel = [o for o in context.selected_objects if o.name.startswith("RNODE_")]
        if len(sel) != 2:
            self.report({'ERROR'}, "Select exactly TWO road nodes first")
            return {'CANCELLED'}

        def _nid(o):
            return int(o.name.split("_", 1)[1].split(".")[0])
        a, b = _nid(sel[0]), _nid(sel[1])
        o = bpy.data.objects.new(f"RLINK_{a}_{b}", None)
        o.empty_display_type = 'PLAIN_AXES'
        o.empty_display_size = 5.0
        o.location = (sel[0].location + sel[1].location) / 2.0
        o["deck_height"] = 0.0
        o["deck_profile"] = "arch"
        o["curve_amp"] = 0.0
        o["scurve_cycles"] = 1
        o["lanes_fwd"] = 1
        o["lanes_rev"] = 1
        o["bank_deg"] = 0.0
        o["median_width"] = 0.0
        o["sidewalk_fwd"] = 1
        o["sidewalk_rev"] = 1
        o["alley"] = 0
        o["tunnel_height"] = 0.0
        o["speed_limit"] = 15.0
        o["ix_a"] = 3                 # junction type at the a-end: 0 stop, 1 light, 2 yield, 3 continue
        o["ix_b"] = 3                 # ... at the b-end
        o[_ROADNET_TAG] = True
        context.collection.objects.link(o)
        self.report({'INFO'}, f"Linked RLINK_{a}_{b}")
        return {'FINISHED'}


class ROADNET_OT_add_zone(bpy.types.Operator):
    bl_idname = "roadnet.add_zone"
    bl_label = "Add Ground Zone"
    bl_description = "Place a ground-ZONE cube empty (water/park/lot/...). Scale it to size, set its kind below"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        o = bpy.data.objects.new("RZONE_", None)
        o.empty_display_type = 'CUBE'
        o.empty_display_size = 60.0
        o.location = context.scene.cursor.location
        o["kind"] = "water"
        o[_ROADNET_TAG] = True
        context.collection.objects.link(o)
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        context.view_layer.objects.active = o
        self.report({'INFO'}, "Added RZONE_ (scale it to size; set its kind below)")
        return {'FINISHED'}


class ROADNET_OT_add_spawn(bpy.types.Operator):
    bl_idname = "roadnet.add_spawn"
    bl_label = "Set Spawn Point"
    bl_description = "Place the player SPAWN empty (RSPAWN_) at the 3D cursor (only one is kept)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for o in list(bpy.data.objects):                 # keep only one spawn
            if o.name.startswith("RSPAWN_"):
                bpy.data.objects.remove(o, do_unlink=True)
        o = bpy.data.objects.new("RSPAWN_", None)
        o.empty_display_type = 'ARROWS'
        o.empty_display_size = 10.0
        o.location = context.scene.cursor.location
        o[_ROADNET_TAG] = True
        context.collection.objects.link(o)
        self.report({'INFO'}, "Spawn point set")
        return {'FINISHED'}


class ROADNET_OT_clear_graph(bpy.types.Operator):
    bl_idname = "roadnet.clear_graph"
    bl_label = "Clear Graph"
    bl_description = "Delete all authoring empties (nodes, links, zones, spawn) to start a fresh network"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pre = ("RNODE_", "RLINK_", "RZONE_", "RSPAWN_")
        doomed = [o for o in bpy.data.objects if o.name.startswith(pre)]
        for o in doomed:
            bpy.data.objects.remove(o, do_unlink=True)
        self.report({'INFO'}, f"Cleared {len(doomed)} authoring empties")
        return {'FINISHED'}


class ROADNET_PT_panel(bpy.types.Panel):
    bl_label = "Road Network Compiler"
    bl_idname = "ROADNET_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Road Net"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        box = layout.box()
        box.label(text="Preset bridge / city", icon='WORLD')
        box.prop(s, "roadnet_preset", text="")
        box.operator("roadnet.build_preset", icon='IMPORT')

        box = layout.box()
        box.label(text="Custom bridge (tuners)", icon='MOD_SIMPLEDEFORM')
        box.prop(s, "rn_deck_height")
        box.prop(s, "rn_deck_profile")
        row = box.row(align=True); row.prop(s, "rn_curve_amp"); row.prop(s, "rn_scurve_cycles", text="")
        row = box.row(align=True); row.prop(s, "rn_lanes_fwd"); row.prop(s, "rn_lanes_rev")
        row = box.row(align=True); row.prop(s, "rn_span"); row.prop(s, "rn_num_verts")
        row = box.row(align=True); row.prop(s, "rn_scale"); row.prop(s, "rn_bank")
        box.operator("roadnet.build_custom_bridge", icon='MOD_SIMPLEDEFORM')

        box = layout.box()
        box.label(text="Demo grid", icon='GRID')
        row = box.row(align=True)
        row.prop(s, "roadnet_cols")
        row.prop(s, "roadnet_rows")
        box.prop(s, "roadnet_spacing")
        box.prop(s, "roadnet_lanes")
        box.prop(s, "roadnet_write_ai")
        box.operator("roadnet.compile_demo", icon='AUTO')

        box = layout.box()
        box.label(text="Graph editor (draw the network)", icon='EMPTY_AXIS')
        row = box.row(align=True)
        row.operator("roadnet.add_node", icon='ADD')
        row.operator("roadnet.connect_nodes", icon='LINKED')
        row.operator("roadnet.clear_graph", text="", icon='TRASH')
        ob = context.active_object
        if ob and ob.name.startswith("RLINK_") and "deck_height" in ob:
            col = box.column(align=True)
            col.label(text=f"Link {ob.name[6:]} tuners:")
            col.prop(ob, '["deck_height"]', text="Deck height")
            col.prop(ob, '["deck_profile"]', text="Profile")
            col.prop(ob, '["curve_amp"]', text="Curve")
            col.prop(ob, '["scurve_cycles"]', text="Cycles (1 bow / 2 S)")
            col.prop(ob, '["bank_deg"]', text="Bank (deg)")
            r = col.row(align=True)
            r.prop(ob, '["lanes_fwd"]', text="Fwd")
            r.prop(ob, '["lanes_rev"]', text="Rev")
            col.prop(ob, '["median_width"]', text="Median (divided)")
            r = col.row(align=True)
            r.prop(ob, '["sidewalk_fwd"]', text="Walk F")
            r.prop(ob, '["sidewalk_rev"]', text="Walk R")
            r = col.row(align=True)
            r.prop(ob, '["alley"]', text="Alley")
            r.prop(ob, '["tunnel_height"]', text="Tunnel h")
            col.prop(ob, '["speed_limit"]', text="Speed limit")
            r = col.row(align=True)
            r.prop(ob, '["ix_a"]', text="Junction A")
            r.prop(ob, '["ix_b"]', text="Junction B")
            col.label(text="(junction 0=stop 1=light 2=yield 3=go)")
        else:
            box.label(text="(select a link to tune it)")
        box.operator("roadnet.compile_empties", text="Build From Graph", icon='OUTLINER_OB_EMPTY')

        box = layout.box()
        box.label(text="City levers (demo grid + graph)", icon='WORLD_DATA')
        box.prop(s, "rn_terrain")
        box.prop(s, "rn_terrain_height")
        row = box.row(align=True)
        row.prop(s, "rn_flat_climb"); row.prop(s, "rn_no_scenery")
        box.prop(s, "rn_opponents")
        row = box.row(align=True)
        row.operator("roadnet.add_zone", icon='MESH_PLANE')
        row.operator("roadnet.add_spawn", icon='PMARKER_ACT')
        ob = context.active_object
        if ob and ob.name.startswith("RZONE_") and "kind" in ob:
            box.prop(ob, '["kind"]', text="Zone kind")
            box.label(text="(water / park / lot / plaza / grass / sand / dirt)")

        box = layout.box()
        box.label(text="Then: Export Polygons -> run build", icon='EXPORT')
        box.label(text="(or set ROADNET_CITY in settings)")


_CLASSES = (ROADNET_OT_compile_demo, ROADNET_OT_compile_empties,
            ROADNET_OT_build_preset, ROADNET_OT_build_custom_bridge,
            ROADNET_OT_add_node, ROADNET_OT_connect_nodes,
            ROADNET_OT_add_zone, ROADNET_OT_add_spawn, ROADNET_OT_clear_graph, ROADNET_PT_panel)


def register_roadnet() -> None:
    bpy.types.Scene.roadnet_cols = bpy.props.IntProperty(
        name="Cols", default=3, min=2, max=64, description="Grid columns of intersections")
    bpy.types.Scene.roadnet_rows = bpy.props.IntProperty(
        name="Rows", default=3, min=2, max=64, description="Grid rows of intersections")
    bpy.types.Scene.roadnet_spacing = bpy.props.FloatProperty(
        name="Block size", default=120.0, min=20.0, max=1000.0, subtype='DISTANCE',
        description="Metres between adjacent intersections")
    bpy.types.Scene.roadnet_lanes = bpy.props.IntProperty(
        name="Lanes/dir", default=1, min=1, max=4, description="Lanes per direction")
    bpy.types.Scene.roadnet_write_ai = bpy.props.BoolProperty(
        name="Write AI files", default=True,
        description="Also write Street*.road + {MAP}.map into the dev city-map folder")

    # preset picker + custom-bridge tuner sliders
    bpy.types.Scene.roadnet_preset = bpy.props.EnumProperty(
        name="Preset", items=_preset_items, description="A named preset bridge or city")
    bpy.types.Scene.rn_deck_height = bpy.props.FloatProperty(
        name="Deck height", default=4.0, min=0.0, max=20.0, description="Peak arch height of the deck")
    bpy.types.Scene.rn_deck_profile = bpy.props.EnumProperty(
        name="Slope", default="arch", description="Slope shape of the deck",
        items=[("arch", "Arch (symmetric)", "Up then down, symmetric"),
               ("early", "Early (steep up)", "Steep climb, gentle descent"),
               ("late", "Late (steep down)", "Gentle climb, steep descent"),
               ("double", "Double hump", "Two humps in one deck")])
    bpy.types.Scene.rn_curve_amp = bpy.props.FloatProperty(
        name="Curve", default=30.0, min=0.0, max=120.0, description="Sideways curve amount (0 = straight)")
    bpy.types.Scene.rn_scurve_cycles = bpy.props.EnumProperty(
        name="Curve type", default="1", description="Bow one way, or S-curve both ways",
        items=[("1", "Bow", "Curves one way"), ("2", "S-curve", "Left then right")])
    bpy.types.Scene.rn_lanes_fwd = bpy.props.IntProperty(
        name="Lanes fwd", default=1, min=1, max=4, description="Forward lanes")
    bpy.types.Scene.rn_lanes_rev = bpy.props.IntProperty(
        name="Lanes rev", default=1, min=1, max=4, description="Reverse lanes")
    bpy.types.Scene.rn_span = bpy.props.FloatProperty(
        name="Span", default=220.0, min=80.0, max=600.0, subtype='DISTANCE', description="Bridge length")
    bpy.types.Scene.rn_num_verts = bpy.props.IntProperty(
        name="Detail", default=15, min=6, max=40,
        description="Facet density (lower = bigger facets = less bounce)")
    bpy.types.Scene.rn_scale = bpy.props.FloatProperty(
        name="Scale", default=1.15, min=0.5, max=2.0, description="Overall size multiplier")
    bpy.types.Scene.rn_bank = bpy.props.FloatProperty(
        name="Bank", default=0.0, min=0.0, max=30.0,
        description="Racetrack camber: tilt the deck INTO the curve by this many degrees (needs a curve)")

    # city levers for the CUSTOM builds (demo grid + graph editor); presets set their own
    bpy.types.Scene.rn_terrain = bpy.props.EnumProperty(
        name="Terrain", default="flat", description="Gentle (AI-safe) terrain profile for custom cities",
        items=[("flat", "Flat", "No hills"),
               ("hills", "Rolling hills", "Gentle rolling hills"),
               ("corner", "Corner rise", "Smooth rise toward one corner"),
               ("cone", "Hill town (cone)", "Central peak descending to the rim")])
    bpy.types.Scene.rn_terrain_height = bpy.props.FloatProperty(
        name="Terrain height", default=18.0, min=0.0, max=80.0,
        description="Peak terrain height (keep gentle so the AI can climb it)")
    bpy.types.Scene.rn_opponents = bpy.props.IntProperty(
        name="Opponents", default=0, min=0, max=7,
        description="AI rival cars for the race (needs a loop in the road graph)")
    bpy.types.Scene.rn_flat_climb = bpy.props.BoolProperty(
        name="Flat ribbon", default=False,
        description="On terrain, lift the road UNIFORMLY across its width (a deck-like ribbon, not tilted)")
    bpy.types.Scene.rn_no_scenery = bpy.props.BoolProperty(
        name="No scenery", default=False, description="Skip lamps / trees / facades (open showcase maps)")

    for cls in _CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)


def unregister_roadnet() -> None:
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    for prop in ("roadnet_cols", "roadnet_rows", "roadnet_spacing",
                 "roadnet_lanes", "roadnet_write_ai", "roadnet_preset",
                 "rn_deck_height", "rn_deck_profile", "rn_curve_amp", "rn_scurve_cycles",
                 "rn_lanes_fwd", "rn_lanes_rev", "rn_span", "rn_num_verts", "rn_scale", "rn_bank",
                 "rn_terrain", "rn_terrain_height", "rn_opponents", "rn_flat_climb", "rn_no_scenery"):
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
            except Exception:
                pass

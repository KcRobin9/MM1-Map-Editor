"""
Text emitters for the AI intermediate format (.road / .int / .map).

Self-contained (no `src.*` import) so the core compiler runs standalone. Output matches
`src/file_formats/ai/helpers.py::MiniParser` and the reference `Game_Files/AI` files:
  * 4-space indent per nesting level
  * list  -> `[`  newline, one value per line, `]`        (used for Vec3 columns & strings)
  * tuple -> `(a, b, c)` inline                            (used for offsets / ids / dirs)
  * float -> `%.2f` ;  Vec3 -> `x.xx y.yy z.zz`
The field ORDER and the forward/backward swaps replicate read_write.write_ai_paths so a
round-trip through the Map Editor's own reader validates.
"""
from typing import List, Sequence

from src.game.mapgen.roadnet.roadsect import PathData, RoadSection
from src.game.mapgen.roadnet.intersections import IntersectionRecord


class RoadFileWriter:
    def __init__(self):
        self.buf: List[str] = []
        self.indent = 0

    def _pad(self) -> str:
        return " " * (self.indent * 4)

    def line(self, text: str = "") -> None:
        self.buf.append(f"{self._pad()}{text}\n" if text else "\n")

    def begin(self, cls: str) -> None:
        self.line(f"{cls} :0 {{")
        self.indent += 1

    def end(self) -> None:
        self.indent -= 1
        self.line("}")

    # scalars
    def f_int(self, name, v):     self.line(f"{name} {int(v)}")
    def f_float(self, name, v):   self.line(f"{name} {float(v):.2f}")
    def f_vec3(self, name, v):    self.line(f"{name} {v[0]:.2f} {v[1]:.2f} {v[2]:.2f}")
    def f_str(self, name, s):     self.line(f'{name} "{s}"')

    def f_tuple(self, name, seq: Sequence, as_int=False) -> None:
        if as_int:
            inner = ", ".join(str(int(x)) for x in seq)
        else:
            inner = ", ".join(f"{float(x):.2f}" for x in seq)
        self.line(f"{name} ({inner})")

    def f_vec3_list(self, name, vs) -> None:
        self.line(f"{name} [")
        self.indent += 1
        for v in vs:
            self.line(f"{v[0]:.2f} {v[1]:.2f} {v[2]:.2f}")
        self.indent -= 1
        self.line("]")

    def f_str_list(self, name, ss) -> None:
        self.line(f"{name} [")
        self.indent += 1
        for s in ss:
            self.line(f'"{s}"')
        self.indent -= 1
        self.line("]")

    def text(self) -> str:
        return "".join(self.buf)


def _assemble_vertexs(fwd: PathData, rev: PathData) -> List:
    """Vertexs[] = fwd lane columns + rev lane columns + fwd boundaries + rev boundaries."""
    out = []
    for p in (fwd, rev):
        out.extend(p.lane_vertices()[0: p.num_lanes * p.num_vertexs])
    if fwd.num_sidewalks:
        out.extend(fwd.boundaries)
        out.extend(rev.boundaries)
    return out


def emit_road(section: RoadSection, terrain=None, flat_climb=False) -> str:
    """
    Emit one mmRoadSect (.road) for a section. fwd is path[0], rev is path[1]. If `terrain` is
    given (a callable h(x,z)->y), the rail vertices are lifted onto the hills so AI cars track
    the road height; Normals stay UP (the engine re-derives the lateral frames at load).
    """
    fwd, rev = section.fwd, section.rev
    w = RoadFileWriter()
    w.begin("mmRoadSect")

    w.f_int("NumVertexs", fwd.num_vertexs)
    w.f_int("NumLanes[0]", fwd.num_lanes)
    w.f_int("NumLanes[1]", rev.num_lanes)
    w.f_int("NumSidewalks[0]", fwd.num_sidewalks * 2)
    w.f_int("NumSidewalks[1]", rev.num_sidewalks * 2)

    vertexs = _assemble_vertexs(fwd, rev)
    if terrain is not None and not flat_climb:
        vertexs = [(v[0], v[1] + terrain(v[0], v[2]), v[2]) for v in vertexs]
    elif terrain is not None and flat_climb:
        # FLAT-CLIMB rail (matches the flat-climb road mesh): lift EVERY vertex by terrain at the nearest
        # point on the road's CENTRELINE (the edge's shape), so the whole cross-section gets ONE height and
        # the rail is FLAT across its width like the road. (A per-vertex lift drapes the rail on the cone -
        # rail != road - and the AI wheel-sim NaN-crashes at init.) Using the shape avoids guessing the
        # vertex column order.
        cl = list(getattr(getattr(section, "edge", None), "shape", None) or [])
        if cl:
            cl_lift = [terrain(p[0], p[1]) for p in cl]
            out2 = []
            for v in vertexs:
                best = 0; bd = 1e30
                for i, p in enumerate(cl):
                    dd = (p[0] - v[0]) ** 2 + (p[1] - v[2]) ** 2
                    if dd < bd:
                        bd = dd; best = i
                out2.append((v[0], v[1] + cl_lift[best], v[2]))
            vertexs = out2
        else:
            vertexs = [(v[0], v[1] + terrain(v[0], v[2]), v[2]) for v in vertexs]
    # Lift the rail onto the bridge/overpass DECK arch so AI cars track the elevated deck instead of the
    # water/ground below it. Straight decks only (the only shape we arch); the fraction is the position
    # along the dominant axis, fed to the SAME _deck_lift the road mesh uses -> rail matches the deck.
    deck = getattr(getattr(section, "edge", None), "deck_height", 0.0)
    if deck > 0.0 and len(vertexs) >= 2:
        from src.game.mapgen.roadnet.build_city import _deck_lift
        xs = [v[0] for v in vertexs]; zs = [v[2] for v in vertexs]
        idx = 0 if (max(xs) - min(xs)) >= (max(zs) - min(zs)) else 2
        lo = min(v[idx] for v in vertexs); span = (max(v[idx] for v in vertexs) - lo) or 1.0
        prof = getattr(section.edge, "deck_profile", "arch")
        vertexs = [(v[0], v[1] + _deck_lift((v[idx] - lo) / span, deck, prof), v[2]) for v in vertexs]
    expected = fwd.num_vertexs * (
        fwd.num_lanes + rev.num_lanes + (fwd.num_sidewalks + rev.num_sidewalks) * 2)
    assert len(vertexs) == expected, f"Vertexs {len(vertexs)} != expected {expected}"

    w.f_int("TotalVertexs", len(vertexs))
    w.f_vec3_list("Vertexs", vertexs)
    w.f_vec3_list("Normals", fwd.normals)

    # forward/backward swaps preserved exactly from read_write.write_ai_paths
    w.f_int("IntersectionType[0]", rev.intersection_type)
    w.f_int("IntersectionType[1]", fwd.intersection_type)
    w.f_vec3("StopLightPos[0]", rev.stop_light_pos[0])
    w.f_vec3("StopLightPos[1]", rev.stop_light_pos[1])
    w.f_vec3("StopLightPos[2]", fwd.stop_light_pos[0])
    w.f_vec3("StopLightPos[3]", fwd.stop_light_pos[1])
    w.f_int("Blocked[0]", fwd.blocked)
    w.f_int("Blocked[1]", rev.blocked)
    w.f_int("PedBlocked[0]", fwd.ped_blocked)
    w.f_int("PedBlocked[1]", rev.ped_blocked)
    w.f_str_list("StopLightName", [rev.stop_light_name, fwd.stop_light_name])

    w.f_int("Divided", fwd.divided)
    w.f_int("Alley", fwd.alley)

    # IMPORTANT: Open1560's mmRoadSect TEXT parser accepts ONLY the fields above. Everything
    # else a loaded-BAI dump contains — StopLightIndex, IsFlat, HasBridge, SpeedLimit, ID,
    # OncomingPath, PathIndex, EdgeIndex, IntersectionIds, VertXDirs, VertZDirs, SubSectionDirs,
    # CenterOffsets, SubSectionOffsets, RoadLength, LaneWidths, LaneLengths — is DERIVED by the
    # engine at load (e.g. aiPath::CalcCenterVerts / AddPathVerts compute the frames + lateral
    # maths from Vertexs+Normals). Emitting them makes the parser reject the file
    # ("'X' is not a valid field name in mmRoadSect" -> "This file sucks, change it!"). They
    # belong only to the binary BAI (read_write.write_ai_paths dumps the binary as text).

    w.end()
    return w.text()


def emit_intersection(rec: IntersectionRecord) -> str:
    w = RoadFileWriter()
    w.begin("mmIntersection")
    w.f_int("ID", rec.id)
    w.f_vec3("Position", rec.position)
    w.f_int("NumSinks", len(rec.sinks))
    w.f_tuple("Sinks", rec.sinks, as_int=True)
    w.f_int("NumSources", len(rec.sources))
    w.f_tuple("Sources", rec.sources, as_int=True)
    w.f_tuple("Paths", rec.paths, as_int=True)
    w.f_tuple("Directions", rec.directions)
    w.end()
    return w.text()


def emit_map(street_path_ids: Sequence[int], _name: str = "mmMapData") -> str:
    """CHICAGO.map — NumStreets + the Street name list (one per road section)."""
    w = RoadFileWriter()
    w.begin("mmMapData")
    w.f_int("NumStreets", len(street_path_ids))
    w.f_str_list("Street", [f"Street{pid}" for pid in street_path_ids])
    w.end()
    return w.text()

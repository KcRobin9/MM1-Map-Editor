"""
MM2 `.pkg` prop mesh  ->  MM1 `.bms` (Binary Mesh Set) for CUSTOM props.

Bridges parse_pkg's (sections, shader_tex) geometry to the `bms_data` dict that
`write_bms` consumes -- the missing adapter that lets MM2's real prop meshes (palm,
lamp, traffic light, bench...) be placed by the MM1 banger system instead of MM1
placeholders.

Schema (verified vs read_bms / an existing shipping prop):
- points          : unique vertex positions (game space, Y-up == MM2 pkg space)
- adjuncts        : unique (point_index, uv); vertex_indices[adj]=point, tex_coords[adj]=uv
- surfaces        : triangles as [adjA, adjB, adjC, 0]  (4th slot 0 = triangle marker)
- texture_indices : 1-based texture slot per surface
- flags           : TEXCOORDS only (props don't need NORMALS -- only cars do)
"""
import re
import shutil
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .pkg import parse_pkg
from src.integrations.blender.modeling.bms_writer import write_bms, _quantize_normal
from src.constants.folder import TextureFolder
from src.constants.file_formats import MeshFlags


def pkg_to_bms_data(pkg_path: str, lod: str = "H", base_at_ground: bool = True,
                    origin_shift=None) -> dict:
    # ORIGIN (1:1 with both engines): mmUnhitBangerInstance::Init / dgBangerInstance place the mesh at
    #   world = pos + R*CG + R*vertex      (banger.cpp: `matrix.m3 = cg ^ matrix`)
    # where CG comes from the banger's tune (MM2 dgBangerData CG). MM2 pkg meshes are CENTRED on their
    # origin and the MM2 CG lifts them (lamp CG.y = 3.86 = half height -> base on the ground; a banner
    # CG.y = 8.5 -> it HANGS 8.5 m above its ground-level pathset point). MM1's loose-.bms loader rejects
    # a CG != the baked header offset (see _TUNE_TMPL), so we bake the SAME shift into the vertices
    # instead: origin_shift = MM2 CG  ->  vertex' = vertex + CG, tune CG = 0. Identical world result.
    # origin_shift=None falls back to the old heuristics:
    #   base_at_ground=True  -> shift so the BASE sits at y=0 (ground prop);
    #   base_at_ground=False -> keep the mesh centred (hanging prop).
    # The banger draw path uses agiMeshLighterTriple, which dereferences per-adjunct Normals -> a
    # mesh WITHOUT normals crashes (ACCESS_VIOLATION) at render. So we MUST emit NORMALS: compute a
    # smooth per-vertex normal (sum of incident face normals) and quantize to the engine's packed
    # normal table.
    mesh = parse_pkg(pkg_path, lod)
    sections = mesh.get("sections") or []
    shader_tex = mesh.get("shader_tex") or []

    points: List[tuple] = []
    adjuncts: List[list] = []                  # each: [point_index, (u, v), [nx, ny, nz accumulator]]
    surface_indices: List[int] = []
    texture_indices: List[int] = []
    texture_names: List[str] = []

    point_slot = {}                            # position -> index into points
    adjunct_slot = {}                          # (point_index, u, v) -> index into adjuncts
    texture_slot = {}                          # texture name -> 1-based slot

    for shader_offset, triangles in sections:
        shader_name = shader_tex[shader_offset] if 0 <= shader_offset < len(shader_tex) else ""
        texture_name = (shader_name.strip() or "notexture").upper()   # a few names carry a trailing space
        if texture_name not in texture_slot:
            texture_slot[texture_name] = len(texture_names) + 1      # 1-based slot
            texture_names.append(texture_name)
        slot = texture_slot[texture_name]

        for (p0, uv0), (p1, uv1), (p2, uv2) in triangles:
            # Face normal (game space) = (p1-p0) x (p2-p0), accumulated into each corner for smoothing.
            edge_a = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            edge_b = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            face_normal = (edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
                           edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
                           edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0])

            corners = []
            for position, uv in ((p0, uv0), (p1, uv1), (p2, uv2)):
                position = (float(position[0]), float(position[1]), float(position[2]))
                if position not in point_slot:
                    point_slot[position] = len(points)
                    points.append(position)
                point_index = point_slot[position]

                # Adjuncts are per-corner: one point can carry several UVs, so key on both.
                tex_coord = (float(uv[0]), float(uv[1]))
                key = (point_index, round(tex_coord[0], 5), round(tex_coord[1], 5))
                if key not in adjunct_slot:
                    adjunct_slot[key] = len(adjuncts)
                    adjuncts.append([point_index, tex_coord, [0.0, 0.0, 0.0]])

                normal_accumulator = adjuncts[adjunct_slot[key]][2]
                normal_accumulator[0] += face_normal[0]
                normal_accumulator[1] += face_normal[1]
                normal_accumulator[2] += face_normal[2]
                corners.append(adjunct_slot[key])

            surface_indices.extend((corners[0], corners[1], corners[2], 0))   # 4th slot 0 = triangle
            texture_indices.append(slot)

    # Shift the mesh so its BASE sits at y=0. MM2 pkg meshes are CENTRED on their origin, but MM1
    # bangers place the mesh origin at the ground point -> the prop sinks by half its height (palms
    # ended up with only the head poking out of the grass). base-at-0 makes props sit ON the ground.
    # HANGING props skip this (base_at_ground=False) so they stay centred and hang at the pathset Y.
    if points and origin_shift is not None and not any(abs(c) > 1e-4 for c in origin_shift):
        # A zero MM2 CG on a mesh that is clearly CENTRED (base far below the origin) cannot be what MM2
        # shows (the prop would be half buried); those few tunes are unfilled, so fall back to the
        # base-at-ground heuristic for them. A small negative base (tree roots) is kept 1:1.
        min_y = min(p[1] for p in points)
        height = max(p[1] for p in points) - min_y
        if min_y < -0.25 * height:
            origin_shift = None
            base_at_ground = True

    if points and origin_shift is not None:
        sx, sy, sz = origin_shift
        if any(abs(c) > 1e-4 for c in (sx, sy, sz)):
            points = [(p[0] + sx, p[1] + sy, p[2] + sz) for p in points]
    elif points and base_at_ground:
        min_y = min(p[1] for p in points)
        if abs(min_y) > 1e-3:
            points = [(p[0], p[1] - min_y, p[2]) for p in points]

    normal_indices = []
    for _, _, normal in adjuncts:
        length = (normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) ** 0.5 or 1.0
        normal_indices.append(_quantize_normal(normal[0] / length, normal[1] / length, normal[2] / length))

    return {
        "points":          points,
        "mesh_offset":     (0.0, 0.0, 0.0),
        "num_adjuncts":    len(adjuncts),
        "num_surfaces":    len(texture_indices),
        "tex_coords":      [a[1] for a in adjuncts],
        "vertex_indices":  [a[0] for a in adjuncts],
        "normal_indices":  normal_indices,
        "texture_indices": texture_indices,
        "surface_indices": surface_indices,
        "texture_names":   texture_names,
        "flags":           MeshFlags.TEXCOORDS | MeshFlags.NORMALS,
    }


def convert_pkg_to_bms(pkg_path: str, out_bms: str, lod: str = "H") -> dict:
    """Parse one .pkg LOD and write a .bms. Returns the bms_data (for stats/verify)."""
    data = pkg_to_bms_data(pkg_path, lod)
    write_bms(data, Path(out_bms))
    return data


# CG y = %(cgy)s : MUST EQUAL THE BMS HEADER OFFSET (which pkg_to_bms_data bakes as mesh_offset=(0,0,0)).
# The engine's agiworld/getmesh.cpp GetMeshSet() validates a loose .bms by comparing the baked header offset
# against the offset the banger passes at load time = bng_data->CG (mmUnhitBangerInstance::Init passes &CG).
# If CG != the baked header offset, the mesh is REJECTED ("changed version or offset, recomputing"); in a
# release/no-DLP data set the recompute then fails and the prop is INVISIBLE (this is exactly what made every
# ground prop with CG=(0,sy/2,0) - mm2palm/mm2tree6/mm2stop/... - vanish, while CG=0 props like mm2tree drew).
# So CG MUST stay (0,0,0) to match the (0,0,0) BMS header. Correct GROUND placement is already handled by the
# base-at-ground vertex shift in pkg_to_bms_data (base sits at y=0, placed at the pathset terrain Y) - it does
# NOT need a CG offset. (Trade-off: the collision box is then centred at the base, like every working CG=0
# prop; that is acceptable and matches the in-game props that already render+collide fine.)
_TUNE_TMPL = '''mmBangerData :065862d4 {
    NodeName "%(name)s"
    AudioId 22
    Size %(sx).3f %(sy).3f %(sz).3f
    CG 0 %(cgy).3f 0
    Offset 0 0 0
    GlowOffset 0 500 0
    Mass %(mass).1f
    Elasticity 0.3
    Friction 0.9
    ImpulseLimit2 1000000000
    SpinAxis 0
    Flash 0
    CollisionType 4
    NumParts 0
    PartNames [
        ]
    TexNumber 0
    BillFlags 0
    YRadius %(yr).3f
}'''


def _as_dirs(dirs) -> List[Path]:
    """One dir or a list of dirs -> [Path, ...] (search order preserved)."""
    if isinstance(dirs, (str, Path)):
        return [Path(dirs)]
    return [Path(d) for d in dirs]


def read_mm2_banger_cg(model: str, tune_dirs) -> Optional[Tuple[float, float, float]]:
    """The CG of MM2's `tune/banger/<model>.dgBangerData`, or None when the model has no tune."""
    for d in _as_dirs(tune_dirs):
        path = d / (model + ".dgBangerData")
        if not path.exists():
            continue
        match = re.search(r"^\s*CG\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)",
                          path.read_text(encoding="latin-1"), re.MULTILINE)
        if match:
            return (float(match.group(1)), float(match.group(2)), float(match.group(3)))
    return None


# tex2dds is not part of this repo --- it ships with the psdl-import toolchain. Honour an explicit
# MM2_TOOLS_DIR, else look for a checkout beside or above this repo.
TOOLS_ENV_VAR = "MM2_TOOLS_DIR"
TOOLS_SUBPATHS = (("MM2_TO_MM1", "tools"),
                  ("reverse-engineering", "MM2_TO_MM1", "tools"),
                  ("psdl-import", "tools"),
                  ("tools",))


def _psdl_import_tools() -> Path | None:
    """The psdl-import tools/ directory, or None when no checkout can be found."""
    override = os.environ.get(TOOLS_ENV_VAR)
    if override:
        return Path(override)

    for parent in Path(__file__).resolve().parents:
        for subpath in TOOLS_SUBPATHS:
            candidate = parent.joinpath(*subpath)
            if (candidate / "tex2dds.py").is_file():
                return candidate

    return None


def build_custom_props(jobs, geometry_dir, mm2tex_dir, out_root: str, tune_dirs=None):
    """Convert MM2 prop .pkg models into MM1 custom-prop assets under out_root.

    geometry_dir / mm2tex_dir : one dir or a list, searched in order (player cities reuse stock models)
    tune_dirs                 : MM2 `tune/banger/` dir(s); a model's CG becomes the baked origin shift
    jobs                      : [(model, PROP_ID_UPPER, mass[, base_at_ground])]

    Writes MESHES/<ID>/{H,M,L,VL}.BMS, each texture (cutout -> TEX16A, opaque -> TEX16O) and
    TUNE/<ID>.MMBANGERDATA. Returns [(id, nsurf, textures)].
    """
    tools_dir = _psdl_import_tools()
    if tools_dir and str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    # Deferred: tex2dds only becomes importable once that directory is on sys.path
    try:
        import tex2dds
    except ImportError:
        raise RuntimeError(
            "MM2 prop conversion needs tex2dds from the psdl-import toolchain "
            "(github.com/wilkovatch/psdl-import). Point MM2_TOOLS_DIR at its tools/ folder, "
            f"or place the checkout next to this repo. Looked in: {tools_dir or 'nothing found'}")

    mesh_root = Path(out_root) / "MESHES"
    alpha_dir = Path(out_root) / "TEXTURES" / TextureFolder.ALPHA
    opaque_dir = Path(out_root) / "TEXTURES" / TextureFolder.OPAQUE
    tune_dir = Path(out_root) / "TUNE"
    done = []

    geometry_dirs = _as_dirs(geometry_dir)
    texture_dirs = _as_dirs(mm2tex_dir)

    for job in jobs:
        model, prop_id, mass = job[0], job[1], job[2]
        base_at_ground = job[3] if len(job) > 3 else True   # HANGING props pass False

        pkg_path = next((d / (model + ".pkg") for d in geometry_dirs if (d / (model + ".pkg")).exists()), None)
        if pkg_path is None:
            continue

        origin_shift = read_mm2_banger_cg(model, tune_dirs) if tune_dirs else None

        # Some pkgs ship no H LOD (sections empty) -> fall back to the first LOD that has geometry.
        data = None
        for lod in ("H", "M", "L", "VL"):
            data = pkg_to_bms_data(str(pkg_path), lod, base_at_ground=base_at_ground,
                                   origin_shift=origin_shift)
            if data["num_surfaces"]:
                break
        if not data or not data["num_surfaces"]:
            continue

        mesh_dir = mesh_root / prop_id
        mesh_dir.mkdir(parents=True, exist_ok=True)
        write_bms(data, mesh_dir / "H.BMS")
        for lod in ("M", "L", "VL"):
            shutil.copy(mesh_dir / "H.BMS", mesh_dir / (lod + ".BMS"))

        for texture in data["texture_names"]:
            source = next((d / (texture.lower() + ".tex") for d in texture_dirs
                           if (d / (texture.lower() + ".tex")).exists()), None)
            if source is None:
                continue

            # Alpha cutouts (foliage, railings, signs) must land in TEX16A as A4R4G4B4; everything
            # else goes to TEX16O as RGB565. A texture that changed class leaves a stale twin behind.
            if tex2dds.tex_has_alpha(str(source)):
                alpha_dir.mkdir(parents=True, exist_ok=True)
                tex2dds.tex_to_dds_alpha(str(source), str(alpha_dir / (texture + ".DDS")))
                stale = opaque_dir / (texture + ".DDS")
                if stale.exists():
                    stale.unlink()
            else:
                opaque_dir.mkdir(parents=True, exist_ok=True)
                tex2dds.tex_to_dds(str(source), str(opaque_dir / (texture + ".DDS")))

        points = data["points"]
        size_x = max(p[0] for p in points) - min(p[0] for p in points)
        size_y = max(p[1] for p in points) - min(p[1] for p in points)
        size_z = max(p[2] for p in points) - min(p[2] for p in points)

        # CG MUST equal the baked BMS header offset (mesh_offset=(0,0,0)) or GetMeshSet rejects the loose .bms
        # on the offset check and the prop goes invisible (see _TUNE_TMPL comment). Ground placement comes from
        # the base-at-ground vertex shift, not from CG, so CG stays 0 for BOTH ground and hanging props.
        center_of_gravity_y = 0.0
        tune_dir.mkdir(parents=True, exist_ok=True)
        (tune_dir / (prop_id + ".MMBANGERDATA")).write_text(_TUNE_TMPL % dict(
            name=prop_id.capitalize(), sx=max(size_x, 0.5), sy=max(size_y, 0.5), sz=max(size_z, 0.5),
            mass=mass, yr=size_y / 2.0, cgy=center_of_gravity_y))

        done.append((prop_id, data["num_surfaces"], data["texture_names"], origin_shift))

    return done


if __name__ == "__main__":
    import sys
    from src.integrations.blender.modeling.meshes import read_bms
    pkg, out = sys.argv[1], sys.argv[2]
    d = convert_pkg_to_bms(pkg, out)
    print("wrote %s: pts=%d adj=%d surf=%d tex=%s" % (
        out, len(d["points"]), d["num_adjuncts"], d["num_surfaces"], d["texture_names"]))
    rt = read_bms(Path(out))   # round-trip: must read back cleanly
    ok = (len(rt["points"]) == len(d["points"]) and rt["num_surfaces"] == d["num_surfaces"]
          and rt["num_adjuncts"] == d["num_adjuncts"])
    xs = [p[0] for p in d["points"]]; ys = [p[1] for p in d["points"]]; zs = [p[2] for p in d["points"]]
    print("round-trip OK:", ok, "| bbox x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

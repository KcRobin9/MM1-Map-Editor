"""
Per-car wheel/body DLP generator (Blender-free).

The engine reads a car's wheel spin pivots and body dimensions from its .DLP:
  - mmWheel::Init   -> GetCentroid("WHLn_H")  (wheel hub = spin pivot) + BoundBox
  - mmCarSim::Init  -> BoundBox("BODY_H")     (car dimensions) + GetCentroid("WHL2/3_H")

The .DLP format stores material/texture/physics libraries after the geometry,
so rather than synthesise one from scratch we take the VPMUSTANG99 template DLP
and *retarget* the queried groups: each group's geometry is affinely remapped so
its axis-aligned bounding box equals the new car's actual part AABB. The library
blob is preserved verbatim (DLP.extra), so the engine still loads it.

Coordinates are game space (x=lateral, y=up, z=front) — identical to BMS points
and mesh_offset, which the DLP also uses (verified: mustang DLP WHL centroids ==
BMS wheel mesh_offset hubs).
"""
from pathlib import Path
from typing import Dict, List, Tuple

from src.core.vector.vector_3 import Vector3
from src.file_formats.development import DLP
from src.integrations.blender.modeling.meshes import read_bms

AABB = Tuple[Tuple[float, float, float], Tuple[float, float, float]]


def _remap(v: float, c_min: float, c_max: float, t_min: float, t_max: float) -> float:
    """Map v from source range [c_min,c_max] onto target range [t_min,t_max]."""
    if c_max - c_min < 1e-9:
        return (t_min + t_max) * 0.5
    return t_min + (v - c_min) * (t_max - t_min) / (c_max - c_min)


def _bms_aabb_car_space(bms_path: Path) -> AABB:
    """AABB of a BMS part in car space = mesh_offset + vertex positions."""
    d = read_bms(bms_path)
    ox, oy, oz = d["mesh_offset"]
    pts = d["points"]
    xs = [p[0] + ox for p in pts]
    ys = [p[1] + oy for p in pts]
    zs = [p[2] + oz for p in pts]
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def _targets_from(bms_dir: Path, body_name: str, wheel_prefix: str) -> Dict[str, AABB]:
    """Retarget map for a body group + consecutive wheel groups present in bms_dir."""
    targets: Dict[str, AABB] = {}

    body = bms_dir / f"{body_name}.BMS"
    if body.is_file():
        targets[body_name] = _bms_aabb_car_space(body)

    for i in range(10):
        whl = bms_dir / f"{wheel_prefix}{i}_H.BMS"
        if not whl.is_file():
            break
        targets[f"{wheel_prefix}{i}_H"] = _bms_aabb_car_space(whl)

    return targets


def compute_car_targets(bms_dir: Path) -> Dict[str, AABB]:
    """
    Build the DLP retarget map from a car's exported BMS in bms_dir.

    Includes BODY_H (car dimensions) and every WHLn_H present (wheel pivots).
    """
    return _targets_from(bms_dir, "BODY_H", "WHL")


def compute_trailer_targets(bms_dir: Path) -> Dict[str, AABB]:
    """
    Build the DLP retarget map for a trailer sub-car's exported BMS in bms_dir.

    Includes TRAILER_H (trailer dimensions/centroid) and every TWHLn_H present
    (trailer wheel pivots). Mirrors compute_car_targets but for trailer groups.
    """
    return _targets_from(bms_dir, "TRAILER_H", "TWHL")


def build_car_dlp(template_path: Path, output_path: Path, targets: Dict[str, AABB]) -> List[Tuple[str, tuple]]:
    """
    Retarget the template DLP's named groups so each group's AABB equals the
    requested (min, max), then write output_path.

    Vertices used by a retargeted group are duplicated (and that group's patches
    repointed) so groups sharing the original vertices are never disturbed.
    Returns [(group_name, resulting_centroid), ...] for the groups that changed.
    """
    with open(template_path, "rb") as f:
        dlp = DLP.read(f)

    by_name = {g.name: g for g in dlp.groups}
    applied: List[Tuple[str, tuple]] = []

    for name, (t_min, t_max) in targets.items():
        group = by_name.get(name)
        if group is None:
            continue

        used_ids: List[int] = []
        seen = set()
        for pi in group.patch_indices:
            for vtx in dlp.patches[pi].vertices:
                if vtx.id not in seen:
                    seen.add(vtx.id)
                    used_ids.append(vtx.id)
        if not used_ids:
            continue

        verts = [dlp.vertices[i] for i in used_ids]
        c_min = (min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts))
        c_max = (max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts))

        old_to_new: Dict[int, int] = {}
        for oid in used_ids:
            v = dlp.vertices[oid]
            dlp.vertices.append(Vector3(
                _remap(v.x, c_min[0], c_max[0], t_min[0], t_max[0]),
                _remap(v.y, c_min[1], c_max[1], t_min[1], t_max[1]),
                _remap(v.z, c_min[2], c_max[2], t_min[2], t_max[2]),
            ))
            old_to_new[oid] = len(dlp.vertices) - 1

        for pi in group.patch_indices:
            for vtx in dlp.patches[pi].vertices:
                vtx.id = old_to_new[vtx.id]

        applied.append((name, (
            (t_min[0] + t_max[0]) * 0.5,
            (t_min[1] + t_max[1]) * 0.5,
            (t_min[2] + t_max[2]) * 0.5,
        )))

    dlp.num_vertices = len(dlp.vertices)
    dlp.write(str(output_path), True)
    return applied


def generate_car_dlp(template_path: Path, bms_dir: Path, output_path: Path) -> List[Tuple[str, tuple]]:
    """Convenience: compute targets from bms_dir and write the retargeted DLP."""
    return build_car_dlp(template_path, output_path, compute_car_targets(bms_dir))


def generate_trailer_dlp(template_path: Path, bms_dir: Path, output_path: Path) -> List[Tuple[str, tuple]]:
    """Convenience: compute trailer targets from bms_dir and write the retargeted DLP."""
    return build_car_dlp(template_path, output_path, compute_trailer_targets(bms_dir))

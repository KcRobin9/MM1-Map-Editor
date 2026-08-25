"""
Compare an ORIGINAL city cell mesh against the one the editor generated for that same cell.

    python development/debug_cell_diff.py [city] [cell_id]
    python development/debug_cell_diff.py rt10 201

Cell ids below 200 are landmarks (LM), the rest are city cells. Build with delete_shop = False
first, or there is no generated mesh to compare against.

Sibling tools, which answer different questions:
    debug_bms.py            dump one mesh
    bms_roundtrip_check.py  does write_bms preserve what read_bms read (writer fidelity)
    debug_vertex_diff.py    which car body a mesh matches, vertices only
"""
import sys
from pathlib import Path

# src.* is only importable once the repo root is on sys.path, so this has to run before them
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.constants.city import City, resolve_city
from src.constants.file_formats import FileType
from src.constants.folder import Folder
from src.constants.misc import Shape, Threshold
from src.integrations.blender.modeling.meshes import read_bms
from src.USER.settings.main import MAP_FILENAME

# How much this tool prints and how close counts as equal --- display settings, not format facts.
VERTEX_TOLERANCE = 0.001
UV_TOLERANCE = 0.01
MAX_LISTED = 10               # cap the per-item lines when many entries differ

FIRST_CITY_CELL = Threshold.CELL_TYPE_SWITCH + 1


# Cell meshes appear zero-padded or bare, in either case, depending on who wrote them
def find_cell_mesh(folder: Path, cell_id: int) -> Path | None:
    for extension in (FileType.MESH, FileType.MESH_lowercase):
        for stem in (f"CULL{cell_id:02d}_H", f"CULL{cell_id}_H"):
            path = folder / f"{stem}{extension}"
            if path.exists():
                return path

    return None


def report(label: str, original, generated, formatter=str) -> None:
    same = original == generated
    print(f"  [{'OK ' if same else 'DIFF'}] {label:22} orig={formatter(original)}  gen={formatter(generated)}")


def compare_header(original: dict, generated: dict) -> None:
    print("=== HEADER ===")
    report("vertex_count", len(original["points"]), len(generated["points"]))
    report("adjunct_count", original["num_adjuncts"], generated["num_adjuncts"])
    report("surface_count", original["num_surfaces"], generated["num_surfaces"])
    report("texture_count", len(original["texture_names"]), len(generated["texture_names"]))
    report("flags", original["flags"], generated["flags"], hex)

    # read_bms returns radius as (radius, radius_squared, bounding_box_radius)
    report("radius", round(original["radius"][0], 4), round(generated["radius"][0], 4))
    report("bounding_box_radius", round(original["radius"][2], 4), round(generated["radius"][2], 4))


def compare_textures(original: dict, generated: dict) -> None:
    print("\n=== TEXTURES ===")
    original_names = original["texture_names"]
    generated_names = generated["texture_names"]

    for index, (left, right) in enumerate(zip(original_names, generated_names)):
        report(f"tex[{index}]", left, right)

    if len(original_names) != len(generated_names):
        print(f"  [DIFF] texture count: orig={len(original_names)}  gen={len(generated_names)}")


def compare_vertices(original: dict, generated: dict) -> None:
    print("\n=== VERTICES ===")
    original_points = original["points"]
    generated_points = generated["points"]

    mismatched = [
        (index, left, right)
        for index, (left, right) in enumerate(zip(original_points, generated_points))
        if any(abs(a - b) > VERTEX_TOLERANCE for a, b in zip(left, right))
    ]

    if not mismatched and len(original_points) == len(generated_points):
        print(f"  [OK ] all {len(original_points)} vertices match")
        return

    if len(original_points) != len(generated_points):
        print(f"  [DIFF] count: orig={len(original_points)}  gen={len(generated_points)}")

    for index, left, right in mismatched[:MAX_LISTED]:
        left_text = ", ".join(f"{value:.3f}" for value in left)
        right_text = ", ".join(f"{value:.3f}" for value in right)
        print(f"  [DIFF] vert[{index}]  orig=({left_text})  gen=({right_text})")

    if len(mismatched) > MAX_LISTED:
        print(f"  ... and {len(mismatched) - MAX_LISTED} more")


# UVs are stored per ADJUNCT, and a surface reaches its adjuncts through surface_indices. Slicing
# tex_coords by surface number instead runs off the end, because adjuncts are shared between
# surfaces, so a mesh has fewer of them than surfaces x corners.
def surface_uvs(mesh: dict, surface: int) -> list:
    base = surface * Shape.QUAD
    adjuncts = mesh["surface_indices"][base:base + Shape.QUAD]

    return [mesh["tex_coords"][adjunct] for adjunct in adjuncts if adjunct < len(mesh["tex_coords"])]


def compare_uvs(original: dict, generated: dict) -> None:
    print(f"\n=== UVs (per surface, {Shape.QUAD} corners each) ===")
    original_uvs = original["tex_coords"]
    generated_uvs = generated["tex_coords"]

    for surface in range(max(original["num_surfaces"], generated["num_surfaces"])):
        left = surface_uvs(original, surface)
        right = surface_uvs(generated, surface)

        same = len(left) == len(right) and all(
            abs(a - b) < UV_TOLERANCE
            for left_uv, right_uv in zip(left, right)
            for a, b in zip(left_uv, right_uv)
        )
        left_text = "  ".join(f"({u:.3f}, {v:.3f})" for u, v in left)
        right_text = "  ".join(f"({u:.3f}, {v:.3f})" for u, v in right)
        print(f"  [{'OK ' if same else 'DIFF'}] surf[{surface}]  orig: {left_text}  |  gen: {right_text}")

    if len(original_uvs) != len(generated_uvs):
        print(f"  [DIFF] UV count: orig={len(original_uvs)}  gen={len(generated_uvs)}")
        return

    differing = sum(
        1 for left_uv, right_uv in zip(original_uvs, generated_uvs)
        if any(abs(a - b) > VERTEX_TOLERANCE for a, b in zip(left_uv, right_uv))
    )

    print(f"  [OK ] all {len(original_uvs)} UV pairs match" if not differing
          else f"  [DIFF] {differing}/{len(original_uvs)} UV pairs differ")


def compare_index_list(label: str, original: list, generated: list) -> None:
    print(f"\n=== {label} ===")
    if list(original) == list(generated):
        print(f"  [OK ] all {len(original)} entries match")
        return

    if len(original) != len(generated):
        print(f"  [DIFF] count: orig={len(original)}  gen={len(generated)}")

    differing = [(index, left, right)
                 for index, (left, right) in enumerate(zip(original, generated)) if left != right]
    print(f"  [DIFF] {len(differing)} of {len(original)} differ")

    for index, left, right in differing[:MAX_LISTED]:
        print(f"    [{index:3d}]  orig={left}  gen={right}")

    if len(differing) > MAX_LISTED:
        print(f"  ... and {len(differing) - MAX_LISTED} more")


def compare(original_path: Path, generated_path: Path) -> None:
    print(f"\nOriginal : {original_path}")
    print(f"Generated: {generated_path}\n")

    original = read_bms(original_path)
    generated = read_bms(generated_path)

    compare_header(original, generated)
    compare_textures(original, generated)
    compare_vertices(original, generated)
    compare_uvs(original, generated)
    compare_index_list("NORMAL INDICES", original["normal_indices"], generated["normal_indices"])
    compare_index_list("SURFACE TEXTURE INDICES", original["texture_indices"], generated["texture_indices"])
    compare_index_list("SURFACE INDICES", original["surface_indices"], generated["surface_indices"])
    compare_index_list("ADJUNCT -> VERTEX", original["vertex_indices"], generated["vertex_indices"])


def main() -> None:
    arguments = sys.argv[1:]
    try:
        city = resolve_city(arguments[0]) if arguments and not arguments[0].isdigit() else City.RaceCity2nd
    except ValueError as error:
        raise SystemExit(error)
    cell_id = int(arguments[-1]) if arguments and arguments[-1].isdigit() else FIRST_CITY_CELL

    suffix = "LM" if cell_id < Threshold.CELL_TYPE_SWITCH else "CITY"
    original_folder = city.path / "MESHES" / f"{city.prefix}{suffix}"
    generated_folder = Folder.Shop.Meshes / f"{MAP_FILENAME}{suffix}"

    original = find_cell_mesh(original_folder, cell_id)
    generated = find_cell_mesh(generated_folder, cell_id)

    if not original:
        raise SystemExit(f"No original mesh for cell {cell_id} in {original_folder}")

    if not generated:
        raise SystemExit(f"No generated mesh for cell {cell_id} in {generated_folder} "
                         f"--- run a build with delete_shop = False first")

    compare(original, generated)


if __name__ == "__main__":
    main()

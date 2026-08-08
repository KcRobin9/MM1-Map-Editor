"""
Standalone demo + self-test for the roadnet compiler.

Run from the MM1-Map-Editor root:

    python -m src.game.mapgen.roadnet.demo
    python -m src.game.mapgen.roadnet.demo --out C:/tmp/roadnet_out --cols 4 --rows 4

It builds a grid city, compiles it, prints a validation report, writes the .road/.int/.map
files, and (when run as the smoke test) asserts there are zero ERROR-level issues. No
Blender required.
"""
import argparse
import os
import tempfile

from src.game.mapgen.roadnet.graph import RoadNetwork, grid_city
from src.game.mapgen.roadnet.network_compiler import RoadNetworkCompiler


def build_demo_network(cols: int, rows: int) -> RoadNetwork:
    # A grid with a couple of wider/asymmetric roads to exercise multi-lane handling.
    net = grid_city(cols, rows, spacing=120.0, lanes_fwd=1, lanes_rev=1, name="DemoCity")
    if net.edges:
        net.edges[0].lanes_fwd = 2          # a 2+1 asymmetric carriageway
        net.edges[0].lanes_rev = 1
    if len(net.edges) > 1:
        net.edges[1].lanes_fwd = 3          # a 3-lane road (the historical bug case)
        net.edges[1].lanes_rev = 3
    if len(net.edges) > 2:
        net.edges[2].alley = True           # an alley
        net.edges[2].sidewalk_fwd = False
        net.edges[2].sidewalk_rev = False
    return net


def run(out_dir: str, cols: int, rows: int, quiet: bool = False) -> int:
    net = build_demo_network(cols, rows)
    compiled = RoadNetworkCompiler().compile(net)

    if not quiet:
        print(compiled.report())

    stats = compiled.write_ai(out_dir)
    quads = compiled.road_mesh_quads()
    iquads = compiled.intersection_quads()
    cells = compiled.cell_assignments()

    if not quiet:
        print(f"\nWrote AI to {out_dir}: "
              f"{stats['streets']} streets, {stats['intersections']} intersections")
        print(f"Mesh: {len(quads)} road quads + {len(iquads)} intersection patches, "
              f"{len(cells)} cells")
        sample = os.path.join(out_dir, "streets", f"Street{compiled.sections[0].fwd.id}.road")
        print(f"\n----- sample {os.path.basename(sample)} -----")
        with open(sample) as f:
            print(f.read())

    errors = [i for i in compiled.validate() if i.severity == "ERROR"]
    return len(errors)


def main():
    ap = argparse.ArgumentParser(description="roadnet compiler demo / self-test")
    ap.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "roadnet_out"))
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    errors = run(args.out, args.cols, args.rows, quiet=args.quiet)
    if errors:
        print(f"\nSELF-TEST FAILED: {errors} ERROR-level issue(s)")
        raise SystemExit(1)
    print("\nSELF-TEST PASSED: 0 errors")


if __name__ == "__main__":
    main()

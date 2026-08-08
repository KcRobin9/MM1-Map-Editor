"""
Procedural MapSpec generators (Blender-free).

These emit a MapSpec dict (the same format an AI would write by hand), so either path
feeds the one compiler. Milestone-1: a rectangular city grid.
"""
from typing import Dict, List


def grid_mapspec(cols: int = 3, rows: int = 3, spacing: float = 80.0,
                 lanes: int = 2, name: str = "GridCity") -> dict:
    """A cols x rows grid of intersections joined by 2-way streets, centred on origin.

    spacing = intersection-to-intersection distance (units; 60-100 reads well).
    """
    cols = max(2, cols)
    rows = max(2, rows)

    half_w = (cols - 1) * spacing / 2.0
    half_h = (rows - 1) * spacing / 2.0

    nodes: Dict[str, List[float]] = {}
    for r in range(rows):
        for c in range(cols):
            nodes[f"n{c}_{r}"] = [c * spacing - half_w, r * spacing - half_h]

    roads: List[dict] = []
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:                                   # horizontal edge
                roads.append({"from": f"n{c}_{r}", "to": f"n{c+1}_{r}", "lanes": lanes})
            if r + 1 < rows:                                   # vertical edge
                roads.append({"from": f"n{c}_{r}", "to": f"n{c}_{r+1}", "lanes": lanes})

    pad = spacing
    return {
        "name": name,
        "extent": [-half_w - pad, -half_h - pad, half_w + pad, half_h + pad],
        "ground": {"texture": "grass"},
        "nodes": nodes,
        "roads": roads,
        "spawn": {"node": "n0_0"},
    }

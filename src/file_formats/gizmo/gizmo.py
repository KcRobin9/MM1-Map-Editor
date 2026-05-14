"""
GIZMO file format — drawbridge / crossgate placement data.

A .GIZMO file is a plain-text file containing one or more "DrawBridge<ID>"
blocks. Each block is opened and closed by a `DrawBridge<id>` header line and
contains 1-6 entries (typically 2 drawbridge halves + 4 crossgates):

    DrawBridge3
        tpdrawbridge06,0,162.608,0.0,-552.598,177.608,0.0,-552.742
        tpcrossgate06,0,177.627,0.15,-551.642,178.627,0.15,-551.661
        ...
    DrawBridge3

Each entry line is comma-separated:
    <prop_name>,<flags>,<ox>,<oy>,<oz>,<fx>,<fy>,<fz>

`offset` is the world-space pivot, `face` is a world-space direction reference
point (the drawbridge's physical tip for drawbridge entries, or a near-by
direction marker for crossgates). The unit vector (face - offset).Normalize()
gives the prop's facing direction.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, Iterable


@dataclass
class GizmoEntry:
    """One prop placement inside a DrawBridge block."""
    name: str
    flags: int
    offset: Tuple[float, float, float]
    face:   Tuple[float, float, float]

    def is_drawbridge(self) -> bool:
        return self.name.lower().startswith("tpdrawbridge")

    def is_crossgate(self) -> bool:
        return self.name.lower().startswith("tpcrossgate")

    def is_filler(self) -> bool:
        """Padding entry written for empty attribute slots (offset == -999.99)."""
        return self.offset[0] < -900.0 and self.offset[2] < -900.0


@dataclass
class GizmoBlock:
    """A single `DrawBridge<id>` block — the full set of props that share an ID."""
    bridge_id: int
    entries: List[GizmoEntry] = field(default_factory=list)

    def drawbridges(self) -> List[GizmoEntry]:
        return [e for e in self.entries if e.is_drawbridge()]

    def crossgates(self) -> List[GizmoEntry]:
        return [e for e in self.entries if e.is_crossgate()]


# ── Reading ───────────────────────────────────────────────────────────────────

def _parse_entry(line: str) -> Optional[GizmoEntry]:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 8:
        return None
    try:
        name  = parts[0]
        flags = int(parts[1])
        ox, oy, oz = float(parts[2]), float(parts[3]), float(parts[4])
        fx, fy, fz = float(parts[5]), float(parts[6]), float(parts[7])
        return GizmoEntry(name, flags, (ox, oy, oz), (fx, fy, fz))
    except ValueError:
        return None


def read_gizmo(path: Path) -> List[GizmoBlock]:
    """Parse a .GIZMO file into a list of GizmoBlocks (skipping filler rows)."""
    path = Path(path)
    blocks: List[GizmoBlock] = []
    current: Optional[GizmoBlock] = None

    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.lower().startswith("drawbridge"):
                token = line[len("DrawBridge"):]
                try:
                    bid = int(token)
                except ValueError:
                    bid = -1
                if current is None or current.bridge_id != bid:
                    current = GizmoBlock(bridge_id=bid)
                    blocks.append(current)
                else:
                    current = None  # closing header
                continue

            entry = _parse_entry(line)
            if entry is None or entry.is_filler() or current is None:
                continue
            current.entries.append(entry)

    return blocks


# ── Writing ───────────────────────────────────────────────────────────────────

def _fmt_entry(e: GizmoEntry) -> str:
    ox, oy, oz = e.offset
    fx, fy, fz = e.face
    return f"\t{e.name},{e.flags},{ox:.6f},{oy:.6f},{oz:.6f},{fx:.6f},{fy:.6f},{fz:.6f}\n"


_FILLER_LINE = "\ttpcrossgate06,0,-999.99,0.00,-999.99,-999.99,0.00,-999.99\n"


def write_gizmo(path: Path, blocks: Iterable[GizmoBlock], pad_to_six: bool = True) -> None:
    """Write GIZMO blocks back to disk.

    `pad_to_six` matches the format the game's own files use: each block is
    padded with filler crossgate rows so total entries = 6 (2 drawbridges +
    up to 5 attributes per drawbridge half). Set False for compact output.
    """
    path = Path(path)
    with open(path, "w") as f:
        for blk in blocks:
            if not blk.entries:
                continue
            f.write(f"DrawBridge{blk.bridge_id}\n")
            for e in blk.entries:
                f.write(_fmt_entry(e))
            if pad_to_six:
                slots_per_drawbridge = 5
                want = max(len(blk.drawbridges()), 1) * (1 + slots_per_drawbridge)
                missing = want - len(blk.entries)
                for _ in range(max(0, missing)):
                    f.write(_FILLER_LINE)
            f.write(f"DrawBridge{blk.bridge_id}\n")

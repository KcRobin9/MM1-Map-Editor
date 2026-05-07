from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.constants.constants import CURRENT_TIME_FORMATTED
from src.constants.file_formats import FileType
from src.constants.folder import Folder
from src.file_formats.ai.read_write import debug_ai
from src.file_formats.development import DLP
from src.file_formats.facades.facades import Facades
from src.file_formats.physics import Physics
from src.file_formats.props.props import Bangers
from src.game.lighting import Lighting

if TYPE_CHECKING:
    from typing import Any


def _output_root() -> Path:
    run_dir = Folder.Debug.Output / f"run_{CURRENT_TIME_FORMATTED}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _collect_input_files() -> list[Path]:
    """Return all files under debug/input/, recursing into sub-folders."""
    input_dir = Folder.Debug.Input
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        return []
    return [p for p in input_dir.rglob("*") if p.is_file()]


def _relative_output(input_file: Path, out_root: Path, new_suffix: str) -> Path:
    """Mirror the input sub-path under out_root, appending the original extension before the new suffix.
    e.g. PHYSICS.DB -> PHYSICS_DB.txt, VPPANOZ.BMS -> VPPANOZ_BMS.txt
    """
    rel = input_file.relative_to(Folder.Debug.Input)
    original_ext = input_file.suffix.lstrip(".")
    new_name = f"{input_file.stem}_{original_ext}{new_suffix}"
    return out_root / rel.parent / new_name


def run_auto_debug(Bounds: Any, Meshes: Any, Portals: Any, enabled: bool) -> None:
    """
    Scan debug/input/ for known file types and debug each one.
    Bounds, Meshes, and Portals are passed in to avoid circular imports
    (they are defined inline in MAP_EDITOR_ALPHA_v1.py).
    Output lands in debug/output/run_YYYYMMDD_HHMMSS/.
    """
    if not enabled:
        return

    files = _collect_input_files()
    if not files:
        return

    out_root = _output_root()
    processed = 0
    skipped = 0

    for f in files:
        ext = f.suffix.upper()
        try:
            if ext == FileType.BOUND.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                Bounds.debug_file(f, out, True)

            elif ext == FileType.MESH.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                Meshes.debug_file(f, out, True)

            elif ext == FileType.PROP.upper():
                out_txt = _relative_output(f, out_root, FileType.TEXT)
                out_csv = _relative_output(f, out_root, FileType.CSV)
                out_txt.parent.mkdir(parents=True, exist_ok=True)
                Bangers.debug_file(f, out_txt, True)
                Bangers.debug_file_to_csv(f, out_csv, True)

            elif ext == FileType.FACADE.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                Facades.debug_file(f, out, True)

            elif ext == FileType.PORTAL.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                Portals.debug_file(f, out, True)

            elif ext == FileType.DEVELOPMENT.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                DLP.debug_file(f, out, True)

            elif ext == FileType.DATABASE.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                Physics.debug_file(f, out, True)

            elif ext == FileType.CSV.upper():
                out = _relative_output(f, out_root, FileType.TEXT)
                out.parent.mkdir(parents=True, exist_ok=True)
                Lighting.debug_file(f, out, True)

            elif ext == FileType.AI.upper():
                stem = f.stem
                rel_parent = f.relative_to(Folder.Debug.Input).parent
                out_dir = out_root / rel_parent / "BAI" / stem
                out_dir.mkdir(parents=True, exist_ok=True)
                debug_ai(
                    f,
                    True,
                    out_dir / f"{stem}.map",
                    str(out_dir / f"{stem}_Intersection{{intersection_id}}.int"),
                    str(out_dir / f"{stem}_Street{{paths}}.road"),
                )

            else:
                print(f"[auto-debug] Skipping unsupported file type: {f.name} ({ext})")
                skipped += 1
                continue

            processed += 1

        except Exception as e:
            import traceback
            print(f"[auto-debug] ERROR processing {f.name}: {type(e).__name__}: {e}")
            traceback.print_exc()

    errors = len(files) - processed - skipped
    total  = processed + skipped + errors
    if total == 0:
        print(f"[auto-debug] No supported files found in {Folder.Debug.Input}")
    else:
        parts = [f"{processed} processed"]
        if skipped: parts.append(f"{skipped} skipped")
        if errors:  parts.append(f"{errors} errored")
        print(f"[auto-debug] {', '.join(parts)} -> {out_root}")

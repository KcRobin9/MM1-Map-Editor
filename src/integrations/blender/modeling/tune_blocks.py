"""
Read / patch MetaClass "brace-block" tune files (Blender-free).

The MM1 engine serialises a node's fields as a flat text block:

    mmDashView :17da8aec {
        MaxSpeed 140
        DashPos 2.328e-010 0.477 -1.128
        RPMMinRot 6.3
        ...
    }

This is the same property-tree text format used by .MMCARSIM (see car_physics.py),
but .MMDASHVIEW and _DASH.POVCAMCS are FLAT (a single block, no nested children),
so a small generic reader/patcher covers both completely.

We never re-emit the whole file from scratch: read_values pulls a field out and
set_values rewrites a field in place (line-anchored, like car_physics), so every
untouched line — including the header's :hex id and the game's odd number formats
like "2.328e-010" — survives a round-trip byte-for-byte. New files are produced by
patching a copied template, never by hand-serialising.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional

_NUM = r"-?[\d.]+(?:[eE][+-]?\d+)?"

# A flat data line: <indent> Key  num [num num ...] <trailing>
_DATA_LINE = re.compile(rf"^([ \t]*)([A-Za-z_]\w*)[ \t]+({_NUM}(?:[ \t]+{_NUM})*)[ \t]*$")


def _fmt(value: float) -> str:
    """Format a value the way the tune files do: ints without a decimal point."""
    v = float(value)
    return str(int(round(v))) if v.is_integer() else repr(round(v, 6))


def _line_re(key: str) -> re.Pattern:
    # ^<indent> Key  num [num ...] <trailing>$  — anchored so we never span lines
    # and never match a key that is merely a prefix of another (Speed vs SpeedMin).
    return re.compile(
        rf"^([ \t]*{re.escape(key)}[ \t]+)({_NUM}(?:[ \t]+{_NUM})*)([ \t]*)$",
        re.MULTILINE,
    )


def read_values(text: str, key: str) -> Optional[List[float]]:
    """Return the numeric values for the first line whose first token is `key`."""
    m = _line_re(key).search(text)
    if not m:
        return None
    try:
        return [float(tok) for tok in m.group(2).split()]
    except ValueError:
        return None


def set_values(text: str, key: str, values) -> str:
    """Rewrite the first `key` line's numbers in place, preserving indent/trailing.

    If the key is absent the text is returned unchanged (callers patch templates
    that already contain every field, so a missing key means "not managed here").
    """
    joined = " ".join(_fmt(v) for v in values)
    return _line_re(key).sub(lambda m: f"{m.group(1)}{joined}{m.group(3)}", text, count=1)


def parse_block(text: str) -> Dict[str, List[float]]:
    """Read every flat numeric field of a single-level block into {key: [floats]}.

    Lines that open/close a block ({ or }) or carry non-numeric values (a nested
    class token) are skipped, so this is safe to run on the whole file.
    """
    out: Dict[str, List[float]] = {}
    for line in text.splitlines():
        m = _DATA_LINE.match(line)
        if not m:
            continue
        key = m.group(2)
        if key in out:
            continue  # first occurrence wins, matching read_values
        try:
            out[key] = [float(tok) for tok in m.group(3).split()]
        except ValueError:
            pass
    return out


def read_file(path: Path) -> str:
    return Path(path).read_text(encoding="ascii", errors="replace")


def write_file(path: Path, text: str) -> None:
    Path(path).write_text(text, encoding="ascii")

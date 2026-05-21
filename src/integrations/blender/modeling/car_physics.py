"""
Targeted physics editing for a car's .MMCARSIM (Blender-free).

MMCARSIM is a text property tree:

    mmCarSim :hex {
        Mass 1500
        Drag 0.12
        ...
        Engine mmEngine :hex { MaxHorsePower 320 ... }
        FrontLeft mmWheel :hex { Spring 75300 ... }
        BackLeft  mmWheel :hex { Spring 65000 ... }
        ... particle BirthRules (Mass/Drag appear again here!) ...
    }

Rather than parse the whole tree we rewrite just a small, high-impact subset of
values in place, leaving gear ratios, particle rules and everything else intact.

Two name-collision hazards the patcher must respect:
  * Mass / Drag also appear inside particle BirthRules (with tiny values like
    0.1). The top-level car values are the FIRST occurrence (they sit above the
    Engine block), so those keys are replaced with count=1.
  * Spring is a substring of RubberSpring / RubberSpringLat. The line-anchored
    regex (^[ \\t]*Spring[ \\t]) only matches a line whose first token is exactly
    Spring, so the Rubber* keys are never touched. Spring is replaced in BOTH
    wheel blocks (front + back) so suspension stiffness is uniform.

PARAM_KEYS maps friendly names -> (MMCARSIM key, replace_all). Used by both the
patcher and the loader (read_physics) so the panel can show a car's real values.
"""
import re
from pathlib import Path
from typing import Dict

# friendly name -> (mmcarsim key, replace_all_occurrences)
PARAM_KEYS = {
    "mass":        ("Mass", False),
    "drag":        ("Drag", False),
    "downforce":   ("Downforce", False),
    "drift":       ("DriftTorque", False),
    "grip":        ("CarFrictionHandling", False),
    "horsepower":  ("MaxHorsePower", False),  # unique (Engine block)
    "suspension":  ("Spring", True),          # both wheel blocks
}

# Vector params: friendly name -> (mmcarsim key, component index). BodyCG is the
# body's centre of gravity: x = lateral, y = height (flip tendency — lower = more
# stable), z = fore/aft (weight bias).
VEC_KEYS = {
    "cg_x":      ("BodyCG", 0),
    "cg_height": ("BodyCG", 1),
    "cg_z":      ("BodyCG", 2),
}

# VPMUSTANG99 baseline (the default template) — used as panel defaults.
DEFAULTS = {
    "mass": 1500.0,
    "drag": 0.12,
    "downforce": 0.0,
    "drift": 7.0,
    "grip": 0.9,
    "horsepower": 320.0,
    "suspension": 75300.0,
    "cg_x": 0.0,
    "cg_height": -0.06,
    "cg_z": 0.0,
}

_NUM = r"-?[\d.]+(?:[eE][+-]?\d+)?"


def _fmt(value: float) -> str:
    v = float(value)
    return str(int(round(v))) if v.is_integer() else repr(round(v, 6))


def _line_re(key: str) -> re.Pattern:
    # ^<indent> Key <number> <trailing>$  — indent/trailing are spaces/tabs only,
    # so we never span lines and never match RubberSpring etc.
    return re.compile(
        rf"^([ \t]*{re.escape(key)}[ \t]+)({_NUM})([ \t]*)$",
        re.MULTILINE,
    )


def _vec3_re(key: str) -> re.Pattern:
    # ^<indent> Key  n  n  n  <trailing>$
    return re.compile(
        rf"^([ \t]*{re.escape(key)}[ \t]+)({_NUM})([ \t]+)({_NUM})([ \t]+)({_NUM})([ \t]*)$",
        re.MULTILINE,
    )


def patch_carsim(text: str, params: Dict[str, float]) -> str:
    """Return text with the given friendly params written into the MMCARSIM."""
    for name, value in params.items():
        if value is None:
            continue
        spec = PARAM_KEYS.get(name)
        if spec is not None:
            key, replace_all = spec
            count = 0 if replace_all else 1
            text = _line_re(key).sub(
                lambda m: f"{m.group(1)}{_fmt(value)}{m.group(3)}", text, count=count
            )
            continue
        vspec = VEC_KEYS.get(name)
        if vspec is not None:
            key, comp = vspec
            # groups: 1=indent+key, 2/4/6=x/y/z, 3/5=gaps, 7=trailing
            comp_group = 2 + comp * 2  # comp 0->2, 1->4, 2->6
            def _sub(m, cg=comp_group, val=value):
                parts = list(m.groups())
                parts[cg - 1] = _fmt(val)
                return "".join(parts)
            text = _vec3_re(key).sub(_sub, text, count=1)
    return text


def read_physics(text: str) -> Dict[str, float]:
    """Read the friendly params back out of an MMCARSIM (first match per key)."""
    out: Dict[str, float] = {}
    for name, (key, _) in PARAM_KEYS.items():
        m = _line_re(key).search(text)
        if m:
            try:
                out[name] = float(m.group(2))
            except ValueError:
                pass
    for name, (key, comp) in VEC_KEYS.items():
        m = _vec3_re(key).search(text)
        if m:
            try:
                out[name] = float(m.group(2 + comp * 2))
            except ValueError:
                pass
    return out


def apply_physics_to_file(path: Path, params: Dict[str, float]) -> None:
    p = Path(path)
    text = p.read_text(encoding="ascii", errors="replace")
    p.write_text(patch_carsim(text, params), encoding="ascii")


def read_physics_from_file(path: Path) -> Dict[str, float]:
    return read_physics(Path(path).read_text(encoding="ascii", errors="replace"))

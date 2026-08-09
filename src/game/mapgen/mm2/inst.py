"""
MM2 `.inst` building instance list -> placement dicts.

Each record is: u16 room, u16 modifiers, u8 type, then a name of (type & 0x7F) bytes. Bit 0x80
marks a SIMPLE component (heading + position, 5 floats); otherwise it is a COORDINATE component
carrying a full 3x3 axis matrix plus the origin (12 floats).
"""
import math
from typing import Dict, List

from src.io.binary import read_unpack

SIMPLE_COMPONENT = 0x80
NAME_LENGTH_MASK = 0x7F

RECORD_HEADER_BYTES = 5     # u16 room + u16 modifiers + u8 type
SIMPLE_FLOATS = 5           # heading x/z + position x/y/z
COORDINATE_FLOATS = 12      # 3x3 axis matrix + origin


def parse_inst(path: str) -> List[Dict]:
    """Parse an .inst into placement dicts. Truncated records end the walk rather than raise, so a
    partially written file still yields every building before the cut."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        out: List[Dict] = []

        while f.tell() + RECORD_HEADER_BYTES <= size:
            room, modifiers = read_unpack(f, "<2H")
            component_type, = read_unpack(f, "<B")

            name_length = component_type & NAME_LENGTH_MASK
            if f.tell() + name_length > size:
                break
            name = f.read(name_length).split(b"\x00")[0].decode("latin-1", "ignore")

            if component_type & SIMPLE_COMPONENT:
                if f.tell() + SIMPLE_FLOATS * 4 > size:
                    break

                x_delta, z_delta, x, y, z = read_unpack(f, f"<{SIMPLE_FLOATS}f")
                out.append({
                    "name": name, "pos": (x, y, z),
                    "angle": math.degrees(math.atan2(x_delta, z_delta)),
                    "room": room, "modifiers": modifiers, "simple": True,
                })

            else:
                if f.tell() + COORDINATE_FLOATS * 4 > size:
                    break

                values = read_unpack(f, f"<{COORDINATE_FLOATS}f")
                x_axis, origin = values[0:3], values[9:12]
                out.append({
                    "name": name, "pos": tuple(origin),
                    "angle": math.degrees(math.atan2(x_axis[0], x_axis[2])),
                    "axes": (values[0:3], values[3:6], values[6:9]),
                    "room": room, "modifiers": modifiers, "simple": False,
                })

    return out

import struct
from typing import Tuple, BinaryIO

from src.helpers.main import calc_size


def read_unpack(file: BinaryIO, fmt: str) -> Tuple:
    return struct.unpack(fmt, file.read(calc_size(fmt)))


def read_vectors(file: BinaryIO, count: int) -> list:
    """`count` consecutive XYZ float triples as plain tuples.

    Vector3.readn is the right call when you want Vector3 objects; the MM2 parsers walk hundreds of
    thousands of raw coordinates and index them positionally, so they take the tuples.
    """
    flat = read_unpack(file, f'<{3 * count}f')
    return [(flat[i], flat[i + 1], flat[i + 2]) for i in range(0, 3 * count, 3)]


def write_pack(file: BinaryIO, fmt: str, *args: object) -> None:
    file.write(struct.pack(fmt, *args))


def pack_bytes(fmt: str, *args: object) -> bytes:
    """Like write_pack but returns raw bytes — use when building CRC payloads or buffers."""
    return struct.pack(fmt, *args)


def read_binary_name(f, length: int = None, encoding: str = 'ascii', padding: int = 0) -> str:  # add ascii constant
    name_data = bytearray()
    
    if length is None:
        while True:
            char = f.read(1)
            if char == b"\0" or not char:
                break
            name_data.extend(char)
            
    else:
        name_data = bytearray(f.read(length))
        null_pos = name_data.find(b'\0')
        
        if null_pos != -1:
            name_data = name_data[:null_pos]
        
        if padding > 0:
            f.read(padding)
    
    return name_data.decode(encoding)


def write_binary_name(f, name: str, length: int = None, encoding: str = 'ascii', padding: int = 0, terminate: bool = False) -> None:  # add ascii constant
    name_data = name.encode(encoding)
    
    if length is not None:
        name_data = name_data[:length].ljust(length, b"\0")
        
    elif terminate:
        name_data += b'\0'
    
    f.write(name_data)
    
    if padding > 0:
        f.write(b"\0" * padding)

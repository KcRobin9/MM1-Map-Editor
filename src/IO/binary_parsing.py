from typing import Tuple, BinaryIO
import struct


def read_unpack(file: BinaryIO, fmt: str) -> Tuple:
    return struct.unpack(fmt, file.read(calc_size(fmt)))


def write_pack(file: BinaryIO, fmt: str, *args: object) -> None:
    file.write(struct.pack(fmt, *args))


def calc_size(fmt: str) -> int:
    return struct.calcsize(fmt)


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
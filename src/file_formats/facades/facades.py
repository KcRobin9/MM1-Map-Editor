
from pathlib import Path
from typing import List, BinaryIO

from src.core.vector.vector_3 import Vector3
from src.debug.main import Debug
from src.io.binary import read_unpack, write_pack, read_binary_name, write_binary_name
from src.constants.misc import Default


class Facades:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, sides: Vector3, scale: float, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.sides = sides
        self.scale = scale
        self.name = name
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '<I')[0]

    @classmethod
    def read(cls, f: BinaryIO) -> 'Facades':
        room, flags = read_unpack(f, '<2H')
        offset = Vector3.read(f)
        face = Vector3.read(f)
        sides = Vector3.read(f)
        scale, = read_unpack(f)
        name = read_binary_name(f)
        return cls(room, flags, offset, face, sides, scale, name)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['Facades']:
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, facades: List['Facades']) -> None:
        return write_pack(f, '<I', len(facades))
        
    def write(self, f: BinaryIO) -> None: 
        write_pack(f, '<2H', Default.ROOM, self.flags)  # Hardcode the Room value such that all Facades are visible in the game    
        write_pack(f, '<3f', *self.offset)  
        write_pack(f, '<3f', *self.face)
        write_pack(f, '<3f', *self.sides)
        write_pack(f, '<f', self.scale)
        write_binary_name(f, self.name, terminate = True) 
        
    @classmethod
    def write_all(cls, output_file: Path, facades: List['Facades']) -> None:
        with open(output_file, mode = "wb") as f:
            
            cls.write_n(f, facades)
            
            for facade in facades:
                facade.write(f)

    @staticmethod
    def debug(facades: List['Facades'], debug_facades: bool, output_file: Path) -> None:
        Debug.internal_list(facades, debug_facades, output_file)
                                           
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_facade_file: bool) -> None:
        if not debug_facade_file:
            return

        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, "rb") as in_f:
            facades = cls.read_all(in_f)

        with open(output_file, "w") as out_f:
            for facade in facades:
                out_f.write(repr(facade))
        print(f"Processed {input_file.name} to {output_file.name}")
        
    def __repr__(self):
        return f"""
FACADE
    Room: {self.room}
    Flags: {self.flags}
    Offset: {self.offset}
    Face: {self.face}
    Sides: {self.sides}
    Scale: {self.scale:.2f}
    Name: {self.name}
    """
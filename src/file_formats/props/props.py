from pathlib import Path
from typing import List, BinaryIO

from src.core.vector.vector_3 import Vector3
from src.io.binary import read_unpack, write_pack, read_binary_name
from src.debug.main import Debug
from src.constants.misc import Encoding, Folder, Default
from src.constants.file_formats import FileType
from src.constants.constants import PROP_CAN_COLLIDE_FLAG


class Bangers:
    def __init__(self, room: int, flags: int, offset: Vector3, face: Vector3, name: str) -> None:
        self.room = room
        self.flags = flags
        self.offset = offset
        self.face = face
        self.name = name
                
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '<I')[0]
            
    @classmethod
    def read(cls, f: BinaryIO) -> 'Bangers':
        room, flags = read_unpack(f, '<2H')
        offset = Vector3.read(f, '<')
        face = Vector3.read(f, '<')  
        name = read_binary_name(f)
        return cls(room, flags, offset, face, name)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> 'List[Bangers]':
        return [cls.read(f) for _ in range(cls.readn(f))]
    
    @classmethod
    def write_n(cls, f: BinaryIO, bangers: List['Bangers']) -> None:
        write_pack(f, '<I', len(bangers))
    
    @classmethod
    def write_all(cls, output_file: Path, bangers: List['Bangers'], debug_props: bool) -> None:
        with open(output_file, mode = "wb") as f:
            
            cls.write_n(f, bangers)
        
            for banger in bangers:
                write_pack(f, '<2H', Default.ROOM, PROP_CAN_COLLIDE_FLAG)  
                banger.offset.write(f, '<')
                banger.face.write(f, '<')
                f.write(banger.name.encode(Encoding.UTF_8))
                    
            cls.debug(bangers, debug_props, Folder.DEBUG / "PROPS" / f"{output_file}{FileType.TEXT}")
    
    #! Works, but the Debug file should not land in "...\MM1-Map-Editor\SHOP\CITY"
    @classmethod
    def debug(cls, bangers: List['Bangers'], debug_props: bool, output_file: Path,) -> None:
        Debug.internal_list(bangers, debug_props, output_file)
                    
    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_props_file: bool) -> None:
        if not debug_props_file:
            return

        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, 'rb') as in_f:
            bangers = cls.read_all(in_f)

        with open(output_file, 'w') as out_f:
            for banger in bangers:
                out_f.write(repr(banger))
        print(f"Processed {input_file.name} to {output_file.name}")
        
    @classmethod
    def debug_file_to_csv(cls, input_file: Path, output_file: Path, debug_props_file_to_csv: bool) -> None:
        if not debug_props_file_to_csv:
            return
        
        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)

        with open(input_file, 'rb') as in_f:
            bangers = cls.read_all(in_f)

        with open(output_file, 'w') as out_f:
            out_f.write(f"{len(bangers)}\n")  # Count
            
            for banger in bangers:
                formatted_line = f"{banger.room},{banger.flags}," \
                                 f"{banger.offset.x:.2f},{banger.offset.y:.2f},{banger.offset.z:.2f}," \
                                 f"{banger.face.x:.2f},{banger.face.y:.2f},{banger.face.z:.2f}," \
                                 f"{banger.name}\n"
                                 
                out_f.write(formatted_line)
        print(f"Processed {input_file.name} to {output_file.name} in CSV format")
                                    
    def __repr__(self):
        return f"""
BANGER
    Room: {self.room}
    Flags: {self.flags}
    Start: {self.offset}
    Face: {self.face}
    Name: {self.name}
    """
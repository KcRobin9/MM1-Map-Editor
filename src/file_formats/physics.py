import os
from pathlib import Path
from typing import List, BinaryIO

from src.core.vector.vector_2 import Vector2
from src.core.vector.vector_3 import Vector3
from src.io.binary import read_unpack, write_pack, read_binary_name, write_binary_name
from src.constants.misc import Encoding, Folder


class PhysicsEditor:
    def __init__(self, name: str, friction: float, elasticity: float, drag: float, 
                 bump_height: float, bump_width: float, bump_depth: float, sink_depth: float, 
                 type: int, sound: int, velocity: Vector2, ptx_color: Vector3) -> None:
        
        self.name = name
        self.friction = friction
        self.elasticity = elasticity
        self.drag = drag
        self.bump_height = bump_height
        self.bump_width = bump_width
        self.bump_depth = bump_depth
        self.sink_depth = sink_depth
        self.type = type
        self.sound = sound
        self.velocity = velocity
        self.ptx_color = ptx_color 
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '>I')[0]

    @staticmethod
    def read(f: BinaryIO) -> 'PhysicsEditor':
        name = read_binary_name(f, 32, Encoding.LATIN_1)
        friction, elasticity, drag = read_unpack(f, '>3f')
        bump_height, bump_width, bump_depth, sink_depth = read_unpack(f, '>4f')
        type, sound = read_unpack(f, '>2I')
        velocity = Vector2.read(f, '>')
        ptx_color = Vector3.read(f, '>')
        return PhysicsEditor(name, friction, elasticity, drag, bump_height, bump_width, bump_depth, sink_depth, type, sound, velocity, ptx_color)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['PhysicsEditor']:
        return [cls.read(f) for _ in range(cls.readn(f))]

    def write(self, f: BinaryIO) -> None:        
        write_binary_name(f, self.name, length = 32, encoding = Encoding.LATIN_1, terminate = True)
        write_pack(f, '>3f', self.friction, self.elasticity, self.drag)
        write_pack(f, '>4f', self.bump_height, self.bump_width, self.bump_depth, self.sink_depth)
        write_pack(f, '>2I', self.type, self.sound)
        self.velocity.write(f, '>')
        self.ptx_color.write(f, '>')

    @staticmethod
    def write_all(output_file: Path, custom_params: List['PhysicsEditor']) -> None:
        with open(output_file, "wb") as f:
            write_pack(f, '>I', len(custom_params))
            
            for param in custom_params:                
                param.write(f)
                
    @classmethod    
    def edit(cls, input_file: Path, output_file: Path, user_set_properties: dict, set_physics: bool, debug_physics: bool) -> None:
        if not set_physics:
            return
        
        with open(input_file, "rb") as f:
            original_data = cls.read_all(f)   
             
        for phys_index, properties in user_set_properties.items():
            physics_obj = original_data[phys_index - 1]
            
            for attr, value in properties.items():
                setattr(physics_obj, attr, value)
                    
        cls.write_all(output_file, original_data)
        
        if debug_physics:
            os.makedirs(Folder.DEBUG / "PHYSICS", exist_ok = True)
            cls.debug(Folder.DEBUG / "PHYSICS" / "PHYSICS_DB.txt", original_data)
                        
    @classmethod
    def debug(cls, debug_filename: Path, physics_params: List['PhysicsEditor']) -> None: 
        with open(debug_filename, 'w') as debug_f:
            for idx, physics_param in enumerate(physics_params):
                debug_f.write(physics_param.__repr__(idx))
                debug_f.write("\n")

    def __repr__(self, idx = None) -> str:
        header = f"PHYSICS (# {idx + 1})" if idx is not None else "PHYSICS"
        name = self.name.rstrip('\x00' + 'Í')
        
        return f"""
{header}
    Name: '{name}',
    Friction: {self.friction:.2f},
    Elasticity: {self.elasticity:.2f},
    Drag: {self.drag:.2f},
    Bump height: {self.bump_height:.2f},
    Bump width: {self.bump_width:.2f},
    Bump depth: {self.bump_depth:.2f},
    Sink Depth: {self.sink_depth:.2f},
    Type: {self.type},
    Sound: {self.sound},
    Velocity: {self.velocity},
    Ptx color: {self.ptx_color}
    """


class Physics:
    def __init__(self, name: str, friction: float, elasticity: float, drag: float, 
                 bump_height: float, bump_width: float, bump_depth: float, sink_depth: float, 
                 type: int, sound: int, velocity: Vector2, ptx_color: Vector3) -> None:
        
        self.name = name
        self.friction = friction
        self.elasticity = elasticity
        self.drag = drag
        self.bump_height = bump_height
        self.bump_width = bump_width
        self.bump_depth = bump_depth
        self.sink_depth = sink_depth
        self.type = type
        self.sound = sound
        self.velocity = velocity
        self.ptx_color = ptx_color 
        
    @classmethod
    def readn(cls, f: BinaryIO) -> int:
        return read_unpack(f, '>I')[0]

    @staticmethod
    def read(f: BinaryIO) -> 'PhysicsEditor':
        name = read_binary_name(f, 32, Encoding.LATIN_1)
        friction, elasticity, drag = read_unpack(f, '>3f')
        bump_height, bump_width, bump_depth, sink_depth = read_unpack(f, '>4f')
        type, sound = read_unpack(f, '>2I')
        velocity = Vector2.read(f, '>')
        ptx_color = Vector3.read(f, '>')
        return PhysicsEditor(name, friction, elasticity, drag, bump_height, bump_width, bump_depth, sink_depth, type, sound, velocity, ptx_color)
    
    @classmethod
    def read_all(cls, f: BinaryIO) -> List['PhysicsEditor']:
        return [cls.read(f) for _ in range(cls.readn(f))]

    def write(self, f: BinaryIO) -> None:        
        write_binary_name(f, self.name, length = 32, encoding = Encoding.LATIN_1, terminate = True)
        write_pack(f, '>3f', self.friction, self.elasticity, self.drag)
        write_pack(f, '>4f', self.bump_height, self.bump_width, self.bump_depth, self.sink_depth)
        write_pack(f, '>2I', self.type, self.sound)
        self.velocity.write(f, '>')
        self.ptx_color.write(f, '>')

    @staticmethod
    def write_all(output_file: Path, custom_params: List['PhysicsEditor']) -> None:
        with open(output_file, "wb") as f:
            write_pack(f, '>I', len(custom_params))
            
            for param in custom_params:                
                param.write(f)
                
    @classmethod    
    def edit(cls, input_file: Path, output_file: Path, user_set_properties: dict, set_physics: bool, debug_physics: bool) -> None:
        if not set_physics:
            return
        
        with open(input_file, "rb") as f:
            original_data = cls.read_all(f)   
             
        for phys_index, properties in user_set_properties.items():
            physics_obj = original_data[phys_index - 1]
            
            for attr, value in properties.items():
                setattr(physics_obj, attr, value)
                    
        cls.write_all(output_file, original_data)
        
        if debug_physics:
            os.makedirs(Folder.DEBUG / "PHYSICS", exist_ok = True)
            cls.debug(Folder.DEBUG / "PHYSICS" / "PHYSICS_DB.txt", original_data)
                        
    @classmethod
    def debug(cls, debug_filename: Path, physics_params: List['PhysicsEditor']) -> None: 
        with open(debug_filename, 'w') as debug_f:
            for idx, physics_param in enumerate(physics_params):
                debug_f.write(physics_param.__repr__(idx))
                debug_f.write("\n")

    def __repr__(self, idx = None) -> str:
        header = f"PHYSICS (# {idx + 1})" if idx is not None else "PHYSICS"
        name = self.name.rstrip('\x00' + 'Í')
        
        return f"""
{header}
    Name: '{name}',
    Friction: {self.friction:.2f},
    Elasticity: {self.elasticity:.2f},
    Drag: {self.drag:.2f},
    Bump height: {self.bump_height:.2f},
    Bump width: {self.bump_width:.2f},
    Bump depth: {self.bump_depth:.2f},
    Sink Depth: {self.sink_depth:.2f},
    Type: {self.type},
    Sound: {self.sound},
    Velocity: {self.velocity},
    Ptx color: {self.ptx_color}
    """
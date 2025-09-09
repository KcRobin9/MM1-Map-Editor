from pathlib import Path
from typing import List, BinaryIO

from src.Vector.vector_2 import Vector2
from src.Vector.vector_3 import Vector3
from src.IO.binary_parsing import read_unpack, write_pack, read_binary_name, write_binary_name
from src.Constants.file_types import FileType, Magic


class DLPVertex: 
    def __init__(self, id: int, normal: Vector3, uv: Vector2, color: int) -> None:
        self.id = id
        self.normal = normal
        self.uv = uv
        self.color = color
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLPVertex':
        id, = read_unpack(f, '>H')
        normal = Vector3.read(f, '>')
        uv = Vector2.read(f, '>')
        color, = read_unpack(f, '>I')       
        return cls(id, normal, uv, color)
    
    def write(self, f: BinaryIO) -> None:
        write_pack(f, '>H', self.id)
        self.normal.write(f, '>')    
        self.uv.write(f, '>')       
        write_pack(f, '>I', self.color)
           
    def __repr__(self) -> str:
        return f"""
            Id: {self.id}
            Normal: {self.normal}
            UV: {self.uv}
            Color: {self.color}
            """
    
            
class DLPPatch:
    def __init__(self, s_res: int, t_res: int, flags: int, r_opts: int, 
                 material_index: int, texture_index: int, physics_index: int, 
                 vertices: List[DLPVertex], name: str) -> None:
        
        self.s_res = s_res
        self.t_res = t_res
        self.flags = flags
        self.r_opts = r_opts
        self.material_index = material_index
        self.texture_index = texture_index
        self.physics_index = physics_index
        self.vertices = vertices
        self.name = name
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLPPatch':
        s_res, t_res = read_unpack(f, '>2H')
        flags, r_opts = read_unpack(f, '>2H')
        material_index, texture_index, physics_index = read_unpack(f, '>3H')        
        vertices = [DLPVertex.read(f) for _ in range(s_res * t_res)]
        name_length, = read_unpack(f, '>I')
        name = read_binary_name(f, name_length)
        return cls(s_res, t_res, flags, r_opts, material_index, texture_index, physics_index, vertices, name)
    
    def write(self, f: BinaryIO) -> None:
        write_pack(f, '>2H', self.s_res, self.t_res) 
        write_pack(f, '>2H', self.flags, self.r_opts)
        write_pack(f, '>3H', self.material_index, self.texture_index, self.physics_index)
        
        for vertex in self.vertices:
            vertex.write(f)
            
        write_pack(f, '>I', len(self.name))        
        write_binary_name(f, self.name)
        
    def __repr__(self) -> str:
        return f"""
    Patch:
        S Res: {self.s_res}
        T Res: {self.t_res}
        Flags: {self.flags}
        R Opts: {self.r_opts}
        Material Index: {self.material_index}
        Texture Index: {self.texture_index}
        Physics Index: {self.physics_index}
        Name: {self.name}
        Vertex: {self.vertices}
        """


class DLPGroup:
    def __init__(self, name: str, num_vertices: int, num_patches: int, 
                 vertex_indices: tuple[int, ...], patch_indices: tuple[int, ...]) -> None:
        
        self.name = name
        self.num_vertices = num_vertices
        self.num_patches = num_patches
        self.vertex_indices = vertex_indices
        self.patch_indices = patch_indices
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLPGroup':
        name_length, = read_unpack(f, '>B')
        name = read_binary_name(f, name_length)        
        num_vertices, num_patches = read_unpack(f, '>2I')        
        vertex_indices = [read_unpack(f, '>H')[0] for _ in range(num_vertices)]
        patch_indices = [read_unpack(f, '>H')[0] for _ in range(num_patches)]     
        return cls(name, num_vertices, num_patches, vertex_indices, patch_indices)

    def write(self, f: BinaryIO) -> None:
        write_pack(f, '>B', len(self.name))
        write_binary_name(f, self.name)        
        write_pack(f, '>2I', self.num_vertices, self.num_patches)
        write_pack(f, f'>{self.num_vertices}H', *self.vertex_indices)
        write_pack(f, f'>{self.num_patches}H', *self.patch_indices)
        
    def __repr__(self) -> str:
        return f"""
    Group:
        Name: {self.name}
        Num Vertices: {self.num_vertices}
        Num Patches: {self.num_patches}
        Vertex Indices: {self.vertex_indices}
        Patch Indices: {self.patch_indices}
        """


class DLP:
    def __init__(self, magic: str, num_groups: int, num_patches: int, num_vertices: int, 
                 groups: List[DLPGroup], patches: List[DLPPatch], vertices: List[Vector3]) -> None:
        
        self.magic = magic
        self.num_groups = num_groups
        self.num_patches = num_patches
        self.num_vertices = num_vertices
        self.groups = groups
        self.patches = patches
        self.vertices = vertices 
        
    @classmethod
    def read(cls, f: BinaryIO) -> 'DLP':
        magic = read_binary_name(f, len(Magic.DEVELOPMENT))          
        num_groups, num_patches, num_vertices = read_unpack(f, '>3I')
        groups = [DLPGroup.read(f) for _ in range(num_groups)]
        patches = [DLPPatch.read(f) for _ in range(num_patches)]
        vertices = Vector3.readn(f, num_vertices, '>')
        return cls(magic, num_groups, num_patches, num_vertices, groups, patches, vertices)

    def write(self, output_file: str, set_dlp: bool) -> None:
        if not set_dlp:
            return
        
        with open(output_file, "wb") as f:
            write_binary_name(f, self.magic) 
            write_pack(f, '>3I', self.num_groups, self.num_patches, self.num_vertices)      
            
            for group in self.groups:
                group.write(f)
                      
            for patch in self.patches:
                patch.write(f)    

            for vertex in self.vertices: 
                vertex.write(f, '>') 
                                    
    @staticmethod          
    def debug_file(input_file: Path, output_file: Path, debug_dlp_file: bool) -> None:
        if not debug_dlp_file:
            return
        
        if not input_file.exists():
            raise FileNotFoundError(f"The file {input_file} does not exist.")

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents = True, exist_ok = True)
        
        with open(input_file, "rb") as in_f:
            dlp_data = DLP.read(in_f)

        with open(output_file, "w") as out_f:
            out_f.write(repr(dlp_data))
            
        print(f"Processed {input_file.name} to {output_file.name}")
             
    @staticmethod
    def debug_folder(input_folder: Path, output_folder: Path, debug_dlp_folder: bool) -> None:
        if not debug_dlp_folder:
            return
        
        if not input_folder.exists():
            raise FileNotFoundError(f"The folder {input_folder} does not exist.")

        dlp_files = list(input_folder.glob(f"*{FileType.DEVELOPMENT}"))
        
        if not dlp_files:
            raise FileNotFoundError(f"No {FileType.DEVELOPMENT} files found in {input_folder}.")
        
        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        for file in dlp_files:
            output_file = output_folder / file.with_suffix({FileType.TEXT}).name
            DLP.debug_file(file, output_file, debug_dlp_folder)     

            print(f"Processed {file.name} to {output_file.name}")    
                                                        
    def __repr__(self) -> str:
        return f"""
DLP
    Magic: {self.magic}
    Num Groups: {self.num_groups}
    Num Patches: {self.num_patches}
    Num Vertices: {self.num_vertices}\n
    {self.groups}\n
    {self.patches}\n
    Vertices: 
        {self.vertices}
    """
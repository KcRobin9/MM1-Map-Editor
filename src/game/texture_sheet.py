import csv
from pathlib import Path
from typing import Dict, List

from src.constants.file_formats import FileType
from src.constants.configs import TEXTURESHEET_MAPPING


TEXTURESHEET_HEADER = ["name", "neighborhood", "h", "m", "l", "flags", "alternate", "sibling", "xres", "yres", "hexcolor"]
    
    
class TextureSheet:
    def __init__(self, name: str = "", neighborhood: int = 0, 
                 lod_high: int = 0, lod_medium: int = 0, lod_low: int = 1, 
                 flags: str = "", alternate: str = "", sibling: str = "", 
                 x_res: int = 64, y_res: int = 64, hex_color: str = "000000") -> None:
        
        self.name = name
        self.neighborhood = neighborhood
        self.lod_high = lod_high
        self.lod_medium = lod_medium
        self.lod_low = lod_low
        self.flags = flags
        self.alternate = alternate
        self.sibling = sibling
        self.x_res = x_res
        self.y_res = y_res
        self.hex_color = hex_color
        
    @staticmethod
    def read_sheet(input_file: Path) -> Dict[str, List[str]]:
        with open(input_file, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            return {row[0]: row for row in reader}

    @staticmethod
    def get_custom_texture_filenames(input_textures: Path) -> List[str]:
         return [f.stem for f in input_textures.glob(f"*{FileType.DIRECTDRAW_SURFACE}")]
     
    @staticmethod
    def parse_flags(flags: List[str]) -> str:
        flag_str = "".join(flags)
        # print(f"Parsing flags {flags} to {flag_str}")  
        return flag_str

    @classmethod
    def append_custom_textures(cls, input_file: Path, input_textures: Path, output_file: Path, set_texture_sheet: bool) -> None:
        if not set_texture_sheet:
            return
            
        with open(input_file, "r") as in_f:
            texturesheet_lines = in_f.readlines()
                    
        existing_texture_names = set(line.split(',')[0].strip() for line in texturesheet_lines)
        custom_texture_names = TextureSheet.get_custom_texture_filenames(input_textures)
        
        added_textures = []
        
        with open(output_file, "w") as out_f: 
            out_f.writelines(texturesheet_lines)  # Write the existing texturesheet lines first
                    
            for custom_tex in custom_texture_names:
                if custom_tex not in existing_texture_names:
                    out_f.write(f"{custom_tex},0,0,0,1,,{custom_tex},,64,64,000000\n")  # TODO: Add support for custom flags
                    added_textures.append(custom_tex)
        
        if added_textures:
            texture_list = ", ".join([f"{tex}{FileType.DIRECTDRAW_SURFACE}" for tex in added_textures])
            print(f"Successfully appended {len(added_textures)} custom texture(s) to texture sheet ({texture_list})")
        else:
            print(f"No new custom textures to append")
            
    @staticmethod
    def write(textures: Dict[str, List[str]], output_file: Path):
        with open(output_file, "w", newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(TEXTURESHEET_HEADER)
            
            for row in textures.values():
                writer.writerow(row)

    @classmethod
    def write_tweaked(cls, input_file: Path, output_file: Path, texture_changes: List[dict], set_texture_sheet: bool):
        if not set_texture_sheet:
            return
        
        textures = cls.read_sheet(input_file)

        for changes in texture_changes:
            target = changes.get("name")
            
            if not target or target not in textures:
                print(f"Texture '{target}' not found or not specified.")
                continue

            texture = textures[target]
            
            for key, value in changes.items():
                if key == "name":
                    continue 
                
                if key == "flags":
                    value = cls.parse_flags(value)  
                    
                if key in TEXTURESHEET_MAPPING:
                    texture[TEXTURESHEET_MAPPING[key]] = str(value)

        cls.write(textures, output_file)
        print(f"Successfully created texture sheet file")
                    
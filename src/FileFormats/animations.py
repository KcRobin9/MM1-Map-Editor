import csv
from pathlib import Path
from typing import Dict, List, Tuple

from src.Constants.file_types import FileType


def create_animations(output_folder: Path, anim_data: Dict[str, List[Tuple]], set_anim: bool) -> None:
   if not set_anim:    
       return

   anim_list_file = output_folder / f"ANIM{FileType.CSV}"

   with open(anim_list_file, "w", newline = "") as list_file:
       for anim_name in anim_data:
           csv.writer(list_file).writerow([f"anim_{anim_name}"])
           
           anim_coordinate_file = output_folder / f"anim_{anim_name}{FileType.CSV}"
           
           with open(anim_coordinate_file, "w", newline="") as coord_file:                    
               for coord in anim_data[anim_name]:
                   csv.writer(coord_file).writerow(coord)
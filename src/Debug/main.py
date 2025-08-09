from pathlib import Path
from typing import List, Any

class Debug:
    _created_folders = set()

    @staticmethod
    def _ensure_output_folder_exists(output_file: Path) -> None:
        output_folder = output_file.parent

        if output_folder in Debug._created_folders:
            return

        if not output_folder.exists():
            print(f"The output folder {output_folder} does not exist. Creating it.")
            output_folder.mkdir(parents = True, exist_ok = True)

        Debug._created_folders.add(output_folder)

    @staticmethod
    def internal(instance: Any, debug_flag: bool, output_file: Path) -> None:
        if not debug_flag:
            return

        Debug._ensure_output_folder_exists(output_file)
        
        with open(output_file, 'w') as out_f:
            out_f.write(str(instance))
        
        print(f"Debugged instance data to {output_file.name}")

    @staticmethod
    def internal_list(instance_list: List[Any], debug_flag: bool, output_file: Path) -> None:
        if not debug_flag:
            return
        
        Debug._ensure_output_folder_exists(output_file)

        with open(output_file, 'w') as out_f:
            for instance in instance_list:
                out_f.write(repr(instance)) 

        print(f"Debugged list data to {output_file.name}")
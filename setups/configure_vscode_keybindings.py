import os
import json
import time
from pathlib import Path


def load_keybindings(input_file: Path):
    if input_file.exists():
        with open(input_file, 'r') as f:
            content = []
            for line in f:
                if not line.strip().startswith(("//", "/")):  # Skip lines that start with comment indicators
                    content.append(line)
            # Join the remaining lines back into a single string and parse as JSON
            try:
                return json.loads("".join(content))
            except json.JSONDecodeError as e:
                print(f"\nError decoding JSON from {input_file}: {e}\n")
                return []
    return []


def save_keybindings(dest_file: Path, keybindings):
    with open(dest_file, 'w') as f:
        json.dump(keybindings, f, indent = 4)


def merge_keybindings_files(input_file: Path, dest_file: Path):
    print("\n========= CONFIGURING KEYBINDING START =========")
    if not dest_file.parent.exists():
        dest_file.parent.mkdir(parents = True)  
    
    dest_keybindings = load_keybindings(dest_file)
    src_keybindings = load_keybindings(input_file)
        
    existing_keys = {binding["key"]: binding for binding in dest_keybindings}
    existing_commands = {binding["command"]: binding for binding in dest_keybindings}
    
    # Check for conflicts and merge
    for binding in src_keybindings:
        if binding['key'] in existing_keys:
            print(f"\nError: Conflict detected for key '{binding['key']}'\n")
            return
        
        if binding['command'] in existing_commands:
            print(f"\nError: Conflict detected for command '{binding['command']}'\n")
            return
        
        existing_keys[binding['key']] = binding
        existing_commands[binding['command']] = binding
        
    save_keybindings(dest_file, list(existing_keys.values()))
    
    time.sleep(0.75)
    print("\n========= CONFIGURING KEYBINDING COMPLETE =========\n")


merge_keybindings_files(
    Path(__file__).parent.resolve() / "vscode_keybindings.json", 
    Path(os.getenv("APPDATA")) / "Code/User/keybindings.json"
    )
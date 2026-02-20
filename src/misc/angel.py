import subprocess
import shutil
from pathlib import Path
from src.constants.misc import Folder
from src.constants.constants import REQUIRED_ANGEL_FILES
from src.USER.settings.main import MAP_FILENAME


def copy_angel_resources(shop_folder: Path) -> None:
    """Copy required angel files to SHOP folder."""
    print(f"Copying angel resources to {shop_folder}...")
    
    # Required tools for the build process
    required_tools = ["find.exe", "mkar.exe", "cat.exe", "rm.exe"]
    
    copied_count = 0
    for file in Folder.ANGEL.iterdir():
        # Copy all .exe files needed for the build
        if file.suffix.lower() == '.exe' and file.name.lower() in required_tools:
            shutil.copy(file, shop_folder / file.name)
            print(f"  [OK] Copied {file.name}")
            copied_count += 1
    
    if copied_count == 0:
        print(f"  [WARNING] No .exe tools copied! Check ANGEL folder: {Folder.ANGEL}")
        print(f"  Looking for: {', '.join(required_tools)}")


def create_shiplist(shop_folder: Path, map_filename: str) -> Path:
    """Create shiplist file using Python instead of find.exe."""
    midtown_folder = shop_folder.parent / "MidtownMadness"
    shiplist_path = midtown_folder / f"shiplist.!!!!!{map_filename}"
    
    print("Creating shiplist with Python...")
    
    # Get all files in SHOP folder recursively
    all_files = []
    for file in shop_folder.rglob('*'):
        if file.is_file():
            # Get relative path from SHOP folder, use forward slashes
            rel_path = file.relative_to(shop_folder)
            # Convert to Unix-style path with ./ prefix (as find would output)
            unix_path = './' + str(rel_path).replace('\\', '/')
            all_files.append(unix_path)
    
    # Write shiplist
    with open(shiplist_path, 'w', newline='\n') as f:
        for file_path in sorted(all_files):
            f.write(file_path + '\n')
    
    print(f"  [OK] Shiplist created with {len(all_files)} files")
    return shiplist_path


def run_angel_process(shop_folder: Path) -> None:
    """Run the angel process to create .ar file."""
    
    # First, create the shiplist using Python
    shiplist_path = create_shiplist(shop_folder, MAP_FILENAME)
    
    # Create a simpler batch file that just runs mkar
    run_bat_content = f"""@echo off
if "%1"=="" goto usage

echo Creating archive for %1...
echo.

echo Running mkar.exe...
.\\mkar.exe ..\\MidtownMadness\\%1.ar ..\\MidtownMadness\\shiplist.%1
if errorlevel 1 (
    echo ERROR: Failed to create archive
    pause
    exit /b 1
)
echo   [OK] Archive created

echo Copying to install directory...
cd ..\\MidtownMadness
copy !!mm1revisited.ar C:\\. 2>nul
cd ..\\SHOP

echo.
echo ============================================
echo SUCCESS: %1.ar created!
echo ============================================
goto end

:usage
echo Usage: run [map_name]

:end
"""
    
    # Write the batch file
    run_bat_path = shop_folder / "run.bat"
    with open(run_bat_path, 'w', encoding='utf-8') as f:
        f.write(run_bat_content)
    print("[OK] Created run.bat")
    
    # Run the batch file
    cmd = f'cmd.exe /c run.bat !!!!!{MAP_FILENAME}'
    print(f"\nExecuting: {cmd}")
    print(f"Working directory: {shop_folder}")
    print("-" * 60)
    
    process = subprocess.Popen(
        cmd,
        cwd=str(shop_folder),
        shell=True
    )
    
    return_code = process.wait()
    print("-" * 60)
    
    if return_code != 0:
        print(f"[WARNING] Process returned code {return_code}")
    else:
        print("[OK] Process completed successfully")


def create_angel_resource_file(shop_folder: Path) -> None:
    """Main function to create angel resource file."""
    print("\n" + "=" * 60)
    print("CREATING ANGEL RESOURCE FILE")
    print("=" * 60)
    
    # Verify folders exist
    midtown_folder = shop_folder.parent / "MidtownMadness"
    if not shop_folder.exists():
        print(f"[ERROR] SHOP folder not found: {shop_folder}")
        return
    if not midtown_folder.exists():
        print(f"[ERROR] MidtownMadness folder not found: {midtown_folder}")
        return
    
    print(f"Shop folder: {shop_folder}")
    print(f"Map name: {MAP_FILENAME}")
    print()
    
    # Copy resources
    copy_angel_resources(shop_folder)
    print()
    
    # Show what's in SHOP before packing
    print(f"Files in SHOP folder:")
    shop_files = list(shop_folder.rglob('*'))
    file_count = len([f for f in shop_files if f.is_file()])
    dir_count = len([f for f in shop_files if f.is_dir()])
    print(f"  Files: {file_count}, Directories: {dir_count}")
    if file_count < 10:
        print("  [WARNING] Very few files in SHOP - the archive might be empty!")
    print()
    
    # Run process
    run_angel_process(shop_folder)
    print()
    
    # Verify output
    ar_file = midtown_folder / f"!!!!!{MAP_FILENAME}.ar"
    shiplist_file = midtown_folder / f"shiplist.!!!!!{MAP_FILENAME}"
    
    if ar_file.exists():
        size = ar_file.stat().st_size
        print("=" * 60)
        print(f"[SUCCESS] {MAP_FILENAME}.ar created ({size:,} bytes)")
        print(f"  Location: {ar_file}")
        
        # Show what was packed
        if shiplist_file.exists():
            with open(shiplist_file, 'r') as f:
                lines = f.readlines()
            print(f"  Files packed: {len(lines)}")
            if len(lines) < 10:
                print("  [WARNING] Very few files packed:")
                for line in lines[:10]:
                    print(f"    {line.strip()}")
        print("=" * 60)
    else:
        print("=" * 60)
        print(f"[ERROR] Archive file not found at {ar_file}")
        print("=" * 60)
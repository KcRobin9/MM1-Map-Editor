Write-Host "Running Test_Python.py..."
Start-Sleep -Seconds 2
python ./Test_Python.py
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Installing required Python Packages..."
Write-Host ""
Write-Host "Installing matplotlib (please wait 30 seconds)"
Write-Host ""
Start-Sleep -Seconds 2
Write-Host ""
pip install matplotlib
Start-Sleep -Seconds 30
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host "Installing fake-blender (please wait 30 seconds)"
Write-Host ""
pip install fake-bpy-module-latest
Write-Host ""
Start-Sleep -Seconds 30 

Write-Host "==================================================================="
Write-Host "==================================================================="
Write-Host ""
Write-Host "Installation Complete!"
Write-Host "***Please press Enter to open the Map Editor and exit this Window***"
Write-Host ""
for($i = 30; $i -gt 0; $i--)
{
    if ($Host.UI.RawUI.KeyAvailable -and ($Host.UI.RawUI.ReadKey("IncludeKeyUp,NoEcho").VirtualKeyCode -eq 13))
    {
        break
    }
    Write-Host "$i..."
    Start-Sleep -Seconds 1
}

# Move up to the main folder
cd ..

# Check if 'code' is available in the PATH
if (Get-Command 'code' -ErrorAction SilentlyContinue) {
    # Open the MAP_EDITOR_ALPHA_v1.py file in VS Code
    Start-Process code ./MAP_EDITOR_ALPHA_v1.py
} else {
    # Open the MAP_EDITOR_ALPHA_v1.py file in Notepad
    Start-Process notepad ./MAP_EDITOR_ALPHA_v1.py
}

Write-Host "Closing PowerShell..."
# Force exit PowerShell
[Environment]::Exit(0)

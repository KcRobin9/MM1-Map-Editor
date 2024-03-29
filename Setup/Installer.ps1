Write-Host "Running Test_Python.py..."
Start-Sleep -Seconds 2
python ./Test_Python.py
Start-Sleep -Seconds 2

# Move up to the root directory (one level up from the current location)
cd ..

Write-Host "Installing required Python Packages from requirements.txt..."
Start-Sleep -Seconds 2
pip install -r requirements.txt


Write-Host ""
Write-Host "==================================================="
Write-Host ""
Write-Host "Installation Complete!"
Write-Host ""
Write-Host "==================================================="
Write-Host ""
Write-Host "*** Please press Enter to open the Map Editor and exit this Window ***"
Write-Host ""

# Wait for the Enter key to be pressed
for ($i = 20; $i -gt 0; $i--)
{
    if ($Host.UI.RawUI.KeyAvailable -and ($Host.UI.RawUI.ReadKey("IncludeKeyUp,NoEcho").VirtualKeyCode -eq 13))
    {
        break
    }
    Write-Host "$i..."
    Start-Sleep -Seconds 1
}

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

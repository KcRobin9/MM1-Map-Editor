Write-Host "Running Test_Python.py..."
Start-Sleep -Seconds 2
python ./Test_Python.py
Start-Sleep -Seconds 2
Write-Host ""


Write-Host ""
Write-Host "Running Keybinding_Config.py..."
Start-Sleep -Seconds 2
python ./Keybinding_Config.py
Start-Sleep -Seconds 2
Write-Host ""
Write-Host ""

# Install VS Code extensions if VS Code CLI is available
if (Get-Command 'code' -ErrorAction SilentlyContinue) {
    Write-Host "Installing Visual Studio Code Extensions..."
	Write-Host ""
    Start-Sleep -Seconds 2
    & code --install-extension ms-python.vscode-pylance
    & code --install-extension jacqueslucke.blender-development
    & code --install-extension aaron-bond.better-comments
} else {
    Write-Host "Visual Studio Code is not detected in PATH. Please ensure it is installed and added to PATH."
}
Write-Host ""
Write-Host ""
Start-Sleep -Seconds 2


# Move up to the root directory (one level up from the current location)
cd ..
Write-Host ""
Write-Host "Installing required Python Packages from requirements.txt..."
Write-Host ""
Start-Sleep -Seconds 2
pip install -r requirements.txt

Write-Host ""
Write-Host "==================================================="
Write-Host ""
Write-Host "Installation Complete!"
Write-Host ""
Write-Host "==================================================="
Write-Host ""
Write-Host "*** Press Enter to open the Map Editor and close this Window ***"
Write-Host ""
pause


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

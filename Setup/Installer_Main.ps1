# Test Python
Write-Host "Running Test_Python.py..."
Start-Sleep -Seconds 1
python ./Test_Python.py
Start-Sleep -Seconds 1
Write-Host ""


# Upgrade pip to the latest version
Write-Host "Upgrading pip..."
Start-Sleep -Seconds 1
Write-Host ""
python -m pip install --upgrade pip
Start-Sleep -Seconds 1
Write-Host ""


# Set Visual Studio Code Keybindings
Write-Host ""
Write-Host "Running Keybinding_Config.py..."
Start-Sleep -Seconds 1
python ./Keybinding_Config.py
Start-Sleep -Seconds 1
Write-Host ""


# Install Visual Studio Code Extensions (if VS Code CLI is available)
if (Get-Command 'code' -ErrorAction SilentlyContinue) {
    Write-Host "Installing Visual Studio Code Extensions..."
	Start-Sleep -Seconds 1
	Write-Host ""
    & code --install-extension ms-python.vscode-pylance
    & code --install-extension jacqueslucke.blender-development
    & code --install-extension aaron-bond.better-comments
} else {
    Write-Host "Visual Studio Code is not detected in PATH. Please ensure it is installed and added to PATH."
}
Write-Host ""
Start-Sleep -Seconds 1


# Install Python Libraries
cd ..
Write-Host ""
Write-Host "Installing required Python Packages from requirements.txt..."
Write-Host ""
Start-Sleep -Seconds 1
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


# Open 'MAP_EDITOR_ALPHA_v1.py' in Visual Studio Code or Notepad++
if (Get-Command 'code' -ErrorAction SilentlyContinue) {
    Start-Process code ./MAP_EDITOR_ALPHA_v1.py
} else {
    Start-Process notepad ./MAP_EDITOR_ALPHA_v1.py
}


# Close Powershell
Write-Host "Closing PowerShell..."
[Environment]::Exit(0)

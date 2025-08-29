Start-Sleep -Seconds 0.5
Write-Host "==================================================="
Write-Host "    Starting Installation... (crossing fingers)"
Write-Host "==================================================="
Write-Host ""
Start-Sleep -Seconds 1

# Test Python
Write-Host ""
Write-Host "Running test_python.py..."
Start-Sleep -Seconds 1
python ./test_python.py
Start-Sleep -Seconds 1
Write-Host ""
Write-Host "Did you see 'Hello World!' printed above? (y/n): " -NoNewline
$pythonCheck = Read-Host
if ($pythonCheck -ne 'y' -and $pythonCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Python is not working properly. Please install Python and try again."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""
Write-Host "Python test passed! Continuing..."
Write-Host ""

# Upgrade pip (Python library installer) to the latest version
Write-Host "Upgrading pip..."
Start-Sleep -Seconds 1
Write-Host ""
python -m pip install --upgrade pip
Start-Sleep -Seconds 1
Write-Host ""
Write-Host "Did pip upgrade successfully without errors? (y/n): " -NoNewline
$pipCheck = Read-Host
if ($pipCheck -ne 'y' -and $pipCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Pip upgrade failed. Please check your internet connection and try again."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""
Write-Host "Pip upgrade successful! Continuing..."
Write-Host ""

# Set Visual Studio Code Keybindings (if VS Code CLI is available)
Write-Host "Running configure_vscode_keybindings..."
if (Get-Command 'code' -ErrorAction SilentlyContinue) {
    Start-Sleep -Seconds 1
    python ./configure_vscode_keybindings.py
    Start-Sleep -Seconds 1
    Write-Host ""
} else {
	Write-Host ""
    Write-Host "Custom Visual Studio Code Keybindings are not configured as the program is not detected in PATH"
	Write-Host ""
}	

# Install Visual Studio Code Extensions (if VS Code CLI is available)
if (Get-Command 'code' -ErrorAction SilentlyContinue) {
    Write-Host "Installing Visual Studio Code Extensions..."
	Start-Sleep -Seconds 1
	Write-Host ""
    & code --install-extension ms-python.vscode-pylance
    & code --install-extension jacqueslucke.blender-development
    & code --install-extension aaron-bond.better-comments
} else {
    Write-Host "Visual Studio Code Extensions are not installed as the program is not detected in PATH"
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
Write-Host "Did the requirements install successfully without errors? (y/n): " -NoNewline
$requirementsCheck = Read-Host
if ($requirementsCheck -ne 'y' -and $requirementsCheck -ne 'Y') {
    Write-Host "Requirements installation failed. Please check the error messages above."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""
Write-Host "Requirements installed successfully! Continuing..."
Write-Host ""

# Install bpy library from wheel filey

Write-Host "Installing bpy library..."
Write-Host ""
Start-Sleep -Seconds 1
pip install "./setup/bpy_library/bpy-4.0.0-cp310-cp310-win_amd64.whl"
Write-Host ""
Write-Host "Did the bpy library install successfully without errors? (y/n): " -NoNewline
$bpyCheck = Read-Host
if ($bpyCheck -ne 'y' -and $bpyCheck -ne 'Y') {
    Write-Host "Bpy library installation failed. Please check the error messages above."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""
Write-Host "Bpy library installed successfully! Continuing..."
Write-Host ""

Start-Sleep -Seconds 1
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
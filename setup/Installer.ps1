Start-Sleep -Seconds 0.5
Write-Host "==================================================="
Write-Host "    Starting Installation... (crossing fingers)"
Write-Host "==================================================="
Write-Host ""
Start-Sleep -Seconds 1

Write-Host "Before we begin, let's make sure you have everything installed:"
Write-Host ""
Write-Host "==================================================="
Write-Host "             PRE-INSTALLATION CHECKLIST"
Write-Host "==================================================="
Write-Host ""

# Python 3.10.7 Check
Write-Host "1. Did you install Python 3.10.7?"
Write-Host "   Link: https://www.python.org/ftp/python/3.10.7/python-3.10.7-amd64.exe"
Write-Host "   (Make sure you checked 'Add Python to PATH' during installation)"
Write-Host ""
Write-Host "   Have you installed Python 3.10.7? (y/n): " -NoNewline
$python310Check = Read-Host
if ($python310Check -ne 'y' -and $python310Check -ne 'Y') {
    Write-Host ""
    Write-Host "Please install Python 3.10.7 first, then run this installer again."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""

# Microsoft C++ Build Tools Check
Write-Host "2. Did you install Microsoft C++ Build Tools?"
Write-Host "   Link: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
Write-Host "   (Select 'Desktop development with C++' and reboot after installation)"
Write-Host ""
Write-Host "   Have you installed Microsoft C++ Build Tools? (y/n): " -NoNewline
$cppToolsCheck = Read-Host
if ($cppToolsCheck -ne 'y' -and $cppToolsCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Please install Microsoft C++ Build Tools first, then run this installer again."
    Write-Host "Don't forget to reboot your computer after installation!"
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""

# Blender Check
Write-Host "3. Did you install Blender?"
Write-Host "   Link: https://www.blender.org/download/"
Write-Host "   (Latest version recommended)"
Write-Host ""
Write-Host "   Have you installed Blender? (y/n): " -NoNewline
$blenderCheck = Read-Host
if ($blenderCheck -ne 'y' -and $blenderCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Blender is strongly recommended for this project."
    Write-Host "Please install Blender first, then run this installer again."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""

# Visual Studio Code Check
Write-Host "4. Did you install Visual Studio Code?"
Write-Host "   Link: https://code.visualstudio.com/download"
Write-Host "   (Latest version recommended)"
Write-Host ""
Write-Host "   Have you installed Visual Studio Code? (y/n): " -NoNewline
$vscodeCheck = Read-Host
if ($vscodeCheck -ne 'y' -and $vscodeCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Visual Studio Code is strongly recommended for this project."
    Write-Host "Please install VS Code first, then run this installer again."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""

Write-Host "==================================================="
Write-Host "   All prerequisites confirmed! Continuing..."
Write-Host "==================================================="
Write-Host ""
Start-Sleep -Seconds 1

# Detect which Python command to use
$pythonCmd = $null
Write-Host "Detecting Python installation..."

if (Get-Command 'python' -ErrorAction SilentlyContinue) {
    $pythonCmd = 'python'
    Write-Host "Found: python command is available"
} elseif (Get-Command 'py' -ErrorAction SilentlyContinue) {
    $pythonCmd = 'py'
    Write-Host "Found: py launcher is available"
} else {
    Write-Host "ERROR: Neither 'python' nor 'py' command found!"
    Write-Host "Please install Python from https://python.org"
    Write-Host "Make sure to check 'Add to PATH' during installation"
    Write-Host ""
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}

Write-Host "Using command: $pythonCmd"
Write-Host ""

# Check Python Version
Write-Host "Checking Python version..."
& $pythonCmd --version
Start-Sleep -Seconds 1
Write-Host ""
Write-Host "Is this the correct Python version you want to use? (y/n): " -NoNewline
$versionCheck = Read-Host
if ($versionCheck -ne 'y' -and $versionCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Please ensure the correct Python version is in your PATH."
    Write-Host "You may need to:"
    Write-Host "- Reinstall Python with 'Add to PATH' option checked"
    Write-Host "- Use 'py -3.10' instead of 'python' if you have multiple versions"
    Write-Host "- Restart your terminal after installing Python"
    Write-Host ""
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}

# Test Python
Write-Host ""
Write-Host "Running test_python.py..."
Start-Sleep -Seconds 1
& $pythonCmd ./test_python.py
Start-Sleep -Seconds 1
Write-Host ""
Write-Host "Did you see 'Hello World!' printed above? (y/n): " -NoNewline
$pythonCheck = Read-Host
if ($pythonCheck -ne 'y' -and $pythonCheck -ne 'Y') {
    Write-Host ""
    Write-Host "Python is not working properly. This could be because:"
    Write-Host "- Python is not installed correctly"
    Write-Host "- The test_python.py file is missing or corrupted"
    Write-Host "- Python interpreter is not functioning"
    Write-Host ""
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
& $pythonCmd -m pip install --upgrade pip
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
    & $pythonCmd ./configure_vscode_keybindings.py
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

# Move to parent directory for package installation
cd ..

# Install Python Libraries
Write-Host ""
Write-Host "Installing required Python Packages from requirements.txt..."
Write-Host ""
Start-Sleep -Seconds 1
& $pythonCmd -m pip install -r requirements.txt
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

# Download and Install BPY Library
Write-Host "==================================================="
Write-Host "          DOWNLOADING BPY LIBRARY"
Write-Host "==================================================="
Write-Host ""

Write-Host "NOTE: The BPY library is approximately 400 MB."
Write-Host "Download time may vary from 1 to 10 minutes depending on your internet speed."
Write-Host "Please wait - the download may appear to freeze but is still working."
Write-Host ""

$bpyWheelUrl = "https://download.blender.org/pypi/bpy/bpy-4.0.0-cp310-cp310-win_amd64.whl"
$bpyWheelPath = "./setup/bpy-4.0.0-cp310-cp310-win_amd64.whl"

# Check if BPY wheel file already exists
if (Test-Path $bpyWheelPath) {
    Write-Host "BPY wheel file already exists in ./setup/"
    Write-Host "Using existing file: $bpyWheelPath"
} else {
    Write-Host "Downloading BPY wheel file..."
    Write-Host "From: $bpyWheelUrl"
    Write-Host "To: $bpyWheelPath"
    Write-Host ""
    
    try {
        # Create setup directory if it doesn't exist
        if (!(Test-Path "./setup")) {
            New-Item -ItemType Directory -Path "./setup" -Force
        }
        
        # Download the wheel file
        Invoke-WebRequest -Uri $bpyWheelUrl -OutFile $bpyWheelPath -UseBasicParsing
        Write-Host "BPY wheel file downloaded successfully!"
    }
    catch {
        Write-Host "Failed to download BPY wheel file automatically."
        Write-Host "Error: $($_.Exception.Message)"
        Write-Host ""
        Write-Host "Please download manually from:"
        Write-Host "$bpyWheelUrl"
        Write-Host "And place it in: $bpyWheelPath"
        Write-Host ""
        Write-Host "After downloading manually, press Enter to continue or Ctrl+C to exit..."
        pause
        
        # Check again if file exists after manual download
        if (!(Test-Path $bpyWheelPath)) {
            Write-Host "BPY wheel file still not found. Installation cannot continue."
            Write-Host "Press Enter to exit..."
            pause
            [Environment]::Exit(1)
        }
    }
}

Write-Host ""
Write-Host "Installing BPY library from wheel file..."
Write-Host ""
Start-Sleep -Seconds 1

& $pythonCmd -m pip install $bpyWheelPath

Write-Host ""
Write-Host "Did the BPY library install successfully without errors? (y/n): " -NoNewline
$bpyCheck = Read-Host
if ($bpyCheck -ne 'y' -and $bpyCheck -ne 'Y') {
    Write-Host ""
    Write-Host "BPY library installation failed. This could be because:"
    Write-Host "- Microsoft C++ Build Tools are not installed properly"
    Write-Host "- You haven't rebooted after installing C++ Build Tools"
    Write-Host "- The wheel file is corrupted"
    Write-Host "- Python version mismatch (must be exactly 3.10.x)"
    Write-Host ""
    Write-Host "Please check the error messages above and resolve the issue."
    Write-Host "Press Enter to exit..."
    pause
    [Environment]::Exit(1)
}
Write-Host ""
Write-Host "BPY library installed successfully! Continuing..."
Write-Host ""

Start-Sleep -Seconds 1
Write-Host "==================================================="
Write-Host ""
Write-Host "INSTALLATION COMPLETE!"
Write-Host ""
Write-Host "==================================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Install libraries in Blender (see SETUP.MD for details)"
Write-Host "2. Connect VS Code to Blender"
Write-Host "3. Create your first map!"
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
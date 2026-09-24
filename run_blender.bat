@echo off
setlocal

rem ============================================================================
rem  Midtown Madness 1 Map Editor - open Blender with the Editor already loaded
rem
rem  Double-click this file. Blender opens with the full Map Editor scene,
rem  panels and keybindings ready. No Visual Studio Code needed.
rem
rem  Blender runs the script in its OWN embedded Python, the same interpreter
rem  the VS Code extension uses, so every operator and panel registers exactly
rem  as it does there.
rem
rem  To use a specific Blender, set BLENDER_EXE before running, e.g.
rem      set BLENDER_EXE=D:\Blender\blender.exe
rem  Otherwise the newest supported version below is picked automatically.
rem  Blender 5.0+ is NOT supported by the Editor, so it is not searched.
rem ============================================================================

set "EDITOR_DIR=%~dp0"
set "EDITOR_SCRIPT=%EDITOR_DIR%MAP_EDITOR_ALPHA_v1.py"

if not exist "%EDITOR_SCRIPT%" (
    echo [ERROR] MAP_EDITOR_ALPHA_v1.py not found next to this file.
    echo         Keep run_blender.bat in the MM1-Map-Editor folder.
    goto :fail
)

rem --- Find Blender ------------------------------------------------------------
if defined BLENDER_EXE (
    if not exist "%BLENDER_EXE%" (
        echo [ERROR] BLENDER_EXE is set but does not exist:
        echo         %BLENDER_EXE%
        goto :fail
    )
    goto :found
)

rem 4.3 first: it is the version setup\SETUP.md targets and the one the Editor is
rem tested against. The rest are fallbacks. Blender 5.0+ is not supported.
for %%V in (4.3 4.5 4.4 4.2 4.1 4.0 3.6) do (
    for %%R in (
        "%ProgramFiles%\Blender Foundation\Blender %%V"
        "%ProgramFiles(x86)%\Blender Foundation\Blender %%V"
        "%LOCALAPPDATA%\Programs\Blender Foundation\Blender %%V"
    ) do (
        if exist "%%~R\blender.exe" (
            set "BLENDER_EXE=%%~R\blender.exe"
            goto :found
        )
    )
)

echo [ERROR] Could not find Blender in the usual install folders.
echo.
echo         Install Blender 4.3 (see setup\SETUP.md), or point this script
echo         at your copy by running these two lines instead:
echo.
echo             set BLENDER_EXE=C:\path\to\blender.exe
echo             run_blender.bat
echo.
goto :fail

:found
echo Blender : %BLENDER_EXE%
echo Script  : %EDITOR_SCRIPT%
echo.
echo Starting. Blender may look frozen for a moment while the Editor loads.
echo Leave this window open - script output and any errors appear here.
echo.

cd /d "%EDITOR_DIR%"
"%BLENDER_EXE%" --python "%EDITOR_SCRIPT%"

set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
    echo [Blender exited with code %RC%. Scroll up for the Python traceback.]
    goto :fail
)
echo Blender closed.
endlocal
exit /b 0

:fail
echo.
pause
endlocal
exit /b 1

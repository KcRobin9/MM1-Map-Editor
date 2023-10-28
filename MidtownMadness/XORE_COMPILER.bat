@echo off
cd /d "%~dp0"

:: Create archive file
mkar core.ar shiplist.core

:: Open either Open1560.exe or Midtown.exe
if exist "Open1560.exe" (
    start "" "Open1560.exe"
) else if exist "Midtown.exe" (
    start "" "Midtown.exe"
)

:: Close the console
exit

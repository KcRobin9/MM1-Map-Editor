@echo off
if "%1"=="" goto usage

cd \vck\shop

echo Build a Shiplist and archive
..\angel\find . -type f > ..\build\shiplist.%1
..\angel\mkar.exe ..\build\%1.ar ..\build\shiplist.%1

echo Copy the archive into the Midtown install directory
cd \vck\build
copy !!mm1revisited.ar C:\.
goto done

:usage
echo Usage: ship [ vehicle_name ]

@echo off
if "%1"=="" goto usage

cd \vck\shop

echo Build a Shiplist and archive
..\angel\find . -type f > ..\MidtownMadness\shiplist.%1
..\angel\mkar.exe ..\MidtownMadness\%1.ar ..\MidtownMadness\shiplist.%1

echo Copy the archive into the Midtown install directory
cd \vck\MidtownMadness
copy !!mm1revisited.ar C:\.
goto done

:usage
echo Usage: ship [ vehicle_name ]

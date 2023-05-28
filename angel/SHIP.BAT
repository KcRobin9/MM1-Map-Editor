@echo off
if "%1"=="" goto usage

cd \vck\shop

echo Clean up the unnecessary files prior to shipping
rem Perhaps also get rid of the pre-existing tuning files?
..\angel\rm -f mtl/global.tsh

echo Build the INFO file for the vehicle
echo BaseName=%1 > tune\foo
..\angel\cat tune/foo ../template/.info > tune\foo1
move tune\foo1 tune\%1.info
..\angel\rm -f tune/foo tune/foo1

echo Bootstrap the tuning files
cd \vck\template
copy .mmcarsim ..\shop\tune\%1.mmcarsim
copy .mmdashview ..\shop\tune\%1.mmdashview
copy .mmnetworkcaraudio ..\shop\tune\%1.mmnetworkcaraudio
copy .mmplayer ..\shop\tune\%1.mmplayer
copy .mmplayercaraudio ..\shop\tune\%1.mmplayercaraudio
copy .povcamcs ..\shop\tune\%1.povcamcs
copy _dash.povcamcs ..\shop\tune\%1_dash.povcamcs
copy _far.trackcamcs ..\shop\tune\%1_far.trackcamcs
copy _near.trackcamcs ..\shop\tune\%1_near.trackcamcs
copy _opp.mmcarsim ..\shop\tune\%1_opp.mmcarsim
copy _opp.mmopponentcaraudio ..\shop\tune\%1_opp.mmopponentcaraudio
copy _whl0.mmbangerdata ..\shop\tune\%1_whl0.mmbangerdata
cd \vck\shop

echo Build a Shiplist and archive
..\angel\find . -type f > ..\build\shiplist.%1
..\angel\mkar.exe ..\build\%1.ar ..\build\shiplist.%1

echo Copy the archive into the Midtown install directory
cd \vck\build
copy %1.ar D:\"Midtown"\.
goto done

:usage
echo Usage: ship [ vehicle_name ]

:done

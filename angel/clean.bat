@echo off
cd \vck\shop
echo Clean: BMS 
..\angel\rm -rf bms/*
echo Clean: DLP
..\angel\rm -f dlp/*
echo Clean: GEO
..\angel\rm -f geo/*
echo Clean: MTL
..\angel\rm -f mtl/*
echo Clean: TEX
..\angel\rm -f tex/*
echo Clean: TEX16A
..\angel\rm -f tex16a/*
echo Clean: TEX16O
..\angel\rm -f tex16o/*
echo Clean: TEXP
..\angel\rm -f texp/*
echo Clean: TUNE
..\angel\rm -f tune/*
echo Done!

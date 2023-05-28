cd ..\shop\tex
..\..\angel\todds -texsheet ..\mtl\global.tsh -mipmap -square -date
for %%i in (..\mtl\vp*.tsh) do ..\bin\todds -texsheet %%i -mipmap -square -date

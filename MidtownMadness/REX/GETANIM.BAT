del *.mod
del *.skel
del *.anim
del *.var
dir
copy g:\madness\art\prod\rex\*_init.mod .
copy g:\madness\art\prod\rex\*_low.mod .
copy g:\madness\art\prod\rex\*_init.skel .
copy g:\madness\art\prod\rex\copinit.mod cop_init.mod
copy g:\madness\art\prod\rex\copinit.skel cop_init.skel
copy g:\madness\art\prod\rex\buswom.mod buswom_init.mod
copy g:\madness\art\prod\rex\buswom.skel buswom_init.skel
copy g:\madness\art\prod\rex\*.anim .
copy g:\madness\art\prod\rex\caswom.ase .
copy g:\madness\art\prod\rex\casman.ase .
copy g:\madness\art\prod\rex\buswom.ase .
copy g:\madness\art\prod\rex\busman.ase .
copy g:\madness\art\prod\rex\wintrwom.ase .
copy g:\madness\art\prod\rex\wintrman.ase .

..\bin\getmat caswom.ase caswom_init.var
..\bin\getmat casman.ase casman_init.var
..\bin\getmat buswom.ase buswom_init.var
..\bin\getmat busman.ase busman_init.var
..\bin\getmat wintrwom.ase wintrwom_init.var
..\bin\getmat wintrman.ase wintrman_init.var

REM cop doesn't have any material variations.

REM these models have poly windings flipped for some reason
@call ..\bin\flipit casman_init
@call ..\bin\flipit caswom_init
@call ..\bin\flipit busman_init
@call ..\bin\flipit cop_init
@call ..\bin\flipit wintrman_init
@call ..\bin\flipit wintrwom_init

@call ..\bin\flipit casman_low
@call ..\bin\flipit caswom_low
@call ..\bin\flipit busman_low
REM @call ..\bin\flipit buswom_low
@call ..\bin\flipit cop_low
@call ..\bin\flipit wintrman_low
@call ..\bin\flipit wintrwom_low

del *.ase

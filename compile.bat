@echo off
rem ==========================================================================
rem  Compilation de rp_onepiece_grandline (Windows)
rem  Utilise les outils fournis avec Garry's Mod (dossier GarrysMod\bin).
rem  Adaptez GMOD ci-dessous si Steam est installe ailleurs.
rem  Astuce : CompilePal (https://compilepal.ricochet.dev) fait la meme chose
rem  avec une interface (VBSP + VVIS + VRAD + PACK + cubemaps).
rem ==========================================================================
setlocal
set "GMOD=C:\Program Files (x86)\Steam\steamapps\common\GarrysMod"
set "GAME=%GMOD%\garrysmod"
set "BIN=%GMOD%\bin"
set "MAP=rp_onepiece_grandline"
cd /d "%~dp0"

if not exist "%BIN%\vbsp.exe" (
  echo [ERREUR] vbsp.exe introuvable dans "%BIN%". Modifiez la variable GMOD.
  pause & exit /b 1
)

echo === 1/5 Copie des textures dans garrysmod\materials (pour Hammer et VRAD)
xcopy /E /I /Y "addon\materials" "%GAME%\materials" >nul

echo === 2/5 VBSP (geometrie)
"%BIN%\vbsp.exe" -game "%GAME%" "maps\src\%MAP%" || goto :erreur

echo === 3/5 VVIS (visibilite)
"%BIN%\vvis.exe" -game "%GAME%" "maps\src\%MAP%" || goto :erreur

echo === 4/5 VRAD (lumiere) - peut prendre un moment
"%BIN%\vrad.exe" -both -final -StaticPropLighting -game "%GAME%" "maps\src\%MAP%" || goto :erreur

echo === 5/5 Integration des textures dans le BSP
"%BIN%\bspzip.exe" -addlist "maps\src\%MAP%.bsp" "maps\src\packlist.txt" "maps\src\%MAP%_pack.bsp" -game "%GAME%" || goto :erreur
copy /Y "maps\src\%MAP%_pack.bsp" "%GAME%\maps\%MAP%.bsp" >nul
copy /Y "maps\src\%MAP%_pack.bsp" "addon\maps\%MAP%.bsp" >nul
del "maps\src\%MAP%_pack.bsp"

echo.
echo Termine ! Lancez GMod puis :  map %MAP%
echo Ensuite (une seule fois) :  sv_cheats 1 ; mat_specular 1 ; buildcubemaps
pause
exit /b 0

:erreur
echo.
echo [ERREUR] La compilation a echoue. Voir le fichier maps\src\%MAP%.log
pause
exit /b 1

# ===========================================================================
#  Installateur de rp_onepiece_grandline pour Garry's Mod
#  Lance par INSTALLER.bat (double-clic). Il :
#   1. trouve Garry's Mod (Steam)
#   2. compile la map avec les outils fournis avec GMod (vbsp, vvis, vrad)
#   3. installe la map + les textures + les scripts dans GMod
# ===========================================================================
$ErrorActionPreference = "Stop"
$Map = "rp_onepiece_grandline"
$Root = Split-Path -Parent $PSScriptRoot

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m) { Write-Host $m -ForegroundColor Green }
function Stop-Installer($m) {
    Write-Host ""
    Write-Host "ERREUR : $m" -ForegroundColor Red
    Read-Host "Appuyez sur Entree pour fermer"
    exit 1
}

Write-Host ""
Write-Host "  ===  rp_onepiece_grandline : installation  ===" -ForegroundColor Yellow
Write-Host ""

# --- 1. Trouver Garry's Mod -------------------------------------------------
function Find-GMod {
    $steam = @()
    foreach ($k in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try {
            $p = Get-ItemProperty -Path $k -ErrorAction Stop
            if ($p.SteamPath) { $steam += $p.SteamPath }
            if ($p.InstallPath) { $steam += $p.InstallPath }
        } catch { }
    }
    $steam += 'C:\Program Files (x86)\Steam'
    $libs = @()
    foreach ($s in $steam) {
        $s = $s -replace '/', '\'
        $libs += $s
        $vdf = Join-Path $s 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            $txt = Get-Content -Path $vdf -Raw
            foreach ($m in [regex]::Matches($txt, '"path"\s+"([^"]+)"')) {
                $libs += ($m.Groups[1].Value -replace '\\\\', '\')
            }
        }
    }
    foreach ($l in ($libs | Select-Object -Unique)) {
        $g = Join-Path $l 'steamapps\common\GarrysMod'
        if (Test-Path (Join-Path $g 'garrysmod')) { return $g }
    }
    return $null
}

$GMod = Find-GMod
if (-not $GMod) {
    Write-Host "Garry's Mod n'a pas ete trouve automatiquement."
    $GMod = Read-Host "Collez le chemin du dossier GarrysMod (ex : D:\SteamLibrary\steamapps\common\GarrysMod)"
    $GMod = $GMod.Trim('"', ' ')
}
$Game = Join-Path $GMod 'garrysmod'
if (-not (Test-Path $Game)) { Stop-Installer "dossier GarrysMod invalide : $GMod" }
Ok "Garry's Mod : $GMod"

# --- 2. Outils de compilation (fournis avec GMod) ---------------------------
$Bin = $null
foreach ($b in @((Join-Path $GMod 'bin'), (Join-Path $GMod 'bin\win64'))) {
    if (Test-Path (Join-Path $b 'vbsp.exe')) { $Bin = $b; break }
}
if (-not $Bin) {
    Stop-Installer ("vbsp.exe introuvable dans $GMod\bin.`n" +
        "Dans Steam : clic droit sur Garry's Mod > Proprietes > Fichiers installes > Verifier l'integrite des fichiers.")
}
Ok "Outils de compilation : $Bin"

$env:VPROJECT = $Game
$Work = Join-Path $env:TEMP "rp_onepiece_build"
New-Item -ItemType Directory -Force -Path $Work | Out-Null
Start-Transcript -Path (Join-Path $Work "installation.log") -Force | Out-Null

# --- 3. Textures (le compilateur doit les voir) ------------------------------
Info "Copie des textures..."
$Mat = Join-Path $Game 'materials'
New-Item -ItemType Directory -Force -Path $Mat | Out-Null
Copy-Item -Path (Join-Path $Root 'addon\materials\onepiece') -Destination $Mat -Recurse -Force

# --- 4. Compilation -----------------------------------------------------------
Copy-Item -Path (Join-Path $Root "maps\src\$Map.vmf") -Destination $Work -Force
$Vmf = Join-Path $Work $Map

function Invoke-Tool($exe, $arguments) {
    Info "> $exe $arguments"
    $p = Start-Process -FilePath (Join-Path $Bin $exe) -ArgumentList $arguments -NoNewWindow -Wait -PassThru
    return $p.ExitCode
}

Write-Host ""
Info "Compilation de la map (cela peut prendre de 10 a 40 minutes, ne fermez pas la fenetre)..."
if ((Invoke-Tool 'vbsp.exe' "-game `"$Game`" `"$Vmf`"") -ne 0) { Stop-Installer "vbsp a echoue (voir $Vmf.log)" }
if (-not (Test-Path "$Vmf.bsp")) { Stop-Installer "vbsp n'a pas produit de fichier .bsp (voir $Vmf.log)" }
if ((Invoke-Tool 'vvis.exe' "-game `"$Game`" `"$Vmf`"") -ne 0) { Stop-Installer "vvis a echoue (voir $Vmf.log)" }
if ((Invoke-Tool 'vrad.exe' "-both -final -StaticPropLighting -game `"$Game`" `"$Vmf`"") -ne 0) {
    Stop-Installer "vrad a echoue (voir $Vmf.log)"
}

# --- 5. Integrer les textures dans le BSP (pour un serveur sans Workshop) ----
$Final = "$Vmf.bsp"
$List = Join-Path $Work 'packlist.txt'
$lines = @()
foreach ($f in Get-ChildItem -Path (Join-Path $Root 'addon\materials\onepiece') -File) {
    $lines += "materials/onepiece/$($f.Name)"
    $lines += $f.FullName
}
Set-Content -Path $List -Value $lines -Encoding ASCII
if (Test-Path (Join-Path $Bin 'bspzip.exe')) {
    $code = Invoke-Tool 'bspzip.exe' "-addlist `"$Vmf.bsp`" `"$List`" `"$Vmf`_pack.bsp`""
    if ($code -eq 0 -and (Test-Path "$Vmf`_pack.bsp")) { $Final = "$Vmf`_pack.bsp" }
    else { Write-Host "bspzip n'a pas pu integrer les textures (pas grave : elles sont dans l'addon)." -ForegroundColor Yellow }
}

# --- 6. Installation dans Garry's Mod ----------------------------------------
Info "Installation dans Garry's Mod..."
$Maps = Join-Path $Game 'maps'
New-Item -ItemType Directory -Force -Path $Maps | Out-Null
Copy-Item -Path $Final -Destination (Join-Path $Maps "$Map.bsp") -Force

$Addon = Join-Path $Game "addons\$Map"
New-Item -ItemType Directory -Force -Path $Addon | Out-Null
Copy-Item -Path (Join-Path $Root 'addon\materials') -Destination $Addon -Recurse -Force
Copy-Item -Path (Join-Path $Root 'addon\lua') -Destination $Addon -Recurse -Force
Copy-Item -Path (Join-Path $Root 'addon\addon.json') -Destination $Addon -Force
# les textures copiees pour la compilation sont maintenant dans l'addon
Remove-Item -Path (Join-Path $Mat 'onepiece') -Recurse -Force -ErrorAction SilentlyContinue

Stop-Transcript | Out-Null
Write-Host ""
Ok "=============================================================="
Ok "  Installation terminee !"
Ok "  Lancez Garry's Mod > Nouvelle partie > $Map"
Ok ""
Ok "  La premiere fois, ouvrez la console du jeu et tapez :"
Ok "     sv_cheats 1"
Ok "     mat_specular 1"
Ok "     buildcubemaps"
Ok "  (calcule les reflets de l'eau, a faire une seule fois)"
Ok "=============================================================="
Read-Host "Appuyez sur Entree pour fermer"

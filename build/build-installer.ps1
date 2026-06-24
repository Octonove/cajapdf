# Genera el instalador unico CajaPDF-Setup-x.y.z.exe con Inno Setup.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path (Join-Path $root "dist\CajaPDF\CajaPDF.exe"))) {
    Write-Host "== dist no encontrado: compilando primero ==" -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "build.ps1")
}

$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $cands = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
               "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
               "$env:ProgramFiles\Inno Setup 6\ISCC.exe")
    $iscc = $cands | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $iscc) { Write-Host "Inno Setup no encontrado." -ForegroundColor Red; exit 1 }
Write-Host "ISCC: $iscc" -ForegroundColor Green

New-Item -ItemType Directory -Force -Path (Join-Path $root "installer") | Out-Null
& $iscc (Join-Path $PSScriptRoot "CajaPDF.iss")
if ($LASTEXITCODE -eq 0) {
    $out = Get-ChildItem (Join-Path $root "installer\CajaPDF-Setup-*.exe") -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "`n== LISTO ==" -ForegroundColor Green
    if ($out) { Write-Host ("Instalador: {0} ({1} MB)" -f $out.FullName, [math]::Round($out.Length/1MB,1)) }
} else { exit $LASTEXITCODE }

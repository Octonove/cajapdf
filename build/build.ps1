# Construye el ejecutable de CajaPDF con PyInstaller (onedir).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

# Usa el venv de CapturaPro (comparte dependencias: pyinstaller, pypdf, pikepdf, Pillow)
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "C:\Users\Usuario\Desktop\proyectos\Aplicaciones Windows\CapturaPro\.venv\Scripts\python.exe"
}
if (-not (Test-Path $py)) { $py = "python" }

$icon = Join-Path $PSScriptRoot "icon.ico"
if (Test-Path $icon) { $env:APP_ICON = $icon } else { $env:APP_ICON = "" }

Write-Host "== Compilando CajaPDF ==" -ForegroundColor Cyan
Push-Location $root
& $py -m PyInstaller --noconfirm --clean (Join-Path $PSScriptRoot "CajaPDF.spec")
$code = $LASTEXITCODE
Pop-Location

if ($code -eq 0) {
    Write-Host "`n== LISTO ==" -ForegroundColor Green
    Write-Host "Ejecutable en: $(Join-Path $root 'dist\CajaPDF\CajaPDF.exe')"
} else {
    Write-Host "`nFallo (codigo $code)." -ForegroundColor Red; exit $code
}

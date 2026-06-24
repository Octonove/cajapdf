# Ejecuta CajaPDF en modo desarrollo.
$root = $PSScriptRoot
$py = "C:\Users\Usuario\Desktop\proyectos\Aplicaciones Windows\CapturaPro\.venv\Scripts\pythonw.exe"
if (-not (Test-Path $py)) { $py = "pythonw" }
& $py (Join-Path $root "CajaPDF.py")

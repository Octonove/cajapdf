# CajaPDF

Herramienta de escritorio para **Windows** que permite **unir, dividir y comprimir PDF** — **100% en tu PC** (nada se sube a internet). Pensada para usuarios no técnicos.

<!-- invokard-coffee -->
**&#9749; Si esto te ahorra tiempo, inv&iacute;tame a un caf&eacute;.** [![Inv&iacute;tame a un caf&eacute; con PayPal](https://img.shields.io/badge/PayPal-Inv%C3%ADtame%20a%20un%20caf%C3%A9-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/donate/?business=stradoxx%40gmail.com&no_recurring=0&currency_code=EUR&item_name=Support%20cajapdf)

**USDC** &middot; Solana `5n6Gfosk7SdwbvdtE9xiLWpcGPBBBGDZYRfAkWyCk86g` &middot; Ethereum (ERC-20) `0xe176866f9d7fdb498e0d4a983d3e34d84dcd6bfc`

## ⬇️ Descargar (Windows 10/11)

### ➡️ [**Descargar CajaPDF (instalador .exe)**](https://github.com/Octonove/cajapdf/releases/latest/download/CajaPDF-Setup.exe)

Descarga **directa** del instalador, sin registro. También puedes ver la [última versión y notas](https://github.com/Octonove/cajapdf/releases/latest).

> Si Windows muestra *"Windows protegió tu PC"* (es normal en programas nuevos sin firma): pulsa **Más información → Ejecutar de todas formas**. Se instala sin permisos de administrador.

## Funciones
- **Unir**: varios PDF en uno, en el orden que elijas.
- **Dividir**: una PDF por cada página, o extraer un rango de páginas.
- **Comprimir** con 3 niveles (suave/media/fuerte): remuestrea y recomprime las imágenes del PDF — ahorros reales del 80-95% en documentos escaneados o con fotos; nunca deja el archivo más grande que el original.

## Privacidad
Todo el procesamiento es **local**. No requiere conexión a internet ni sube tus documentos a ningún servidor — ideal para contratos, nóminas, DNIs e información confidencial.

## Ejecutar en desarrollo
```powershell
./run.ps1
```
(usa el venv de CapturaPro, que comparte las dependencias; o crea uno con `requirements.txt`)

## Construir el ejecutable
```powershell
./build/build.ps1
```
→ `dist\CajaPDF\CajaPDF.exe`

## Crear el instalador único
```powershell
./build/build-installer.ps1
```
→ `installer\CajaPDF-Setup-1.0.0.exe` (instala sin admin, con accesos directos y desinstalador)

## Stack
Python 3.14 + Tkinter + **pypdf** (unir/dividir) + **pikepdf** (comprimir) + Pillow + PyInstaller + Inno Setup.

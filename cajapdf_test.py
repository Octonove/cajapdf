"""Pruebas funcionales de CajaPDF: unir, dividir, comprimir + construccion UI."""

from __future__ import annotations

import sys
import tempfile
import tkinter as tk
from pathlib import Path

from PIL import Image

from cajapdf import pdfops

ok = True


def check(name, cond, detail=""):
    global ok
    if not cond:
        ok = False
    print(f"[{'OK ' if cond else 'FAIL'}] {name} {detail}")


work = Path(tempfile.gettempdir()) / "cajapdf_test"
work.mkdir(exist_ok=True)


def make_pdf(path, seed):
    # Imagen tipo foto (gradiente) que comprime bien con JPEG
    w, h = 1600, 1600
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(0, w, 4):
            v = (x + y + seed * 40) % 256
            c = (v, (v * 2) % 256, (255 - v))
            for dx in range(4):
                if x + dx < w:
                    px[x + dx, y] = c
    img.save(path, "PDF", resolution=150.0)


pdfs = []
for i in range(3):
    p = work / f"img{i}.pdf"
    make_pdf(p, i)
    pdfs.append(str(p))
print("PDFs de prueba creados")

# --- Unir ---
merged = str(work / "merged.pdf")
pdfops.merge(pdfs, merged)
check("unir", pdfops.page_count(merged) == 3, f"-> {pdfops.page_count(merged)} pags")

# --- Dividir cada pagina ---
parts = pdfops.split_each_page(merged, str(work / "split"))
check("dividir cada pagina", len(parts) == 3, f"-> {len(parts)} archivos")

# --- Extraer rango ---
rng = str(work / "rango.pdf")
pdfops.split_range(merged, rng, 2, 3)
check("extraer rango 2-3", pdfops.page_count(rng) == 2, f"-> {pdfops.page_count(rng)} pags")

# --- Comprimir ---
comp = str(work / "comprimido.pdf")
src, dst = pdfops.compress(merged, comp, quality=50)
valid = pdfops.page_count(comp) == 3  # el resultado sigue siendo un PDF valido de 3 pags
check("comprimir (no mayor que original)", dst <= src, f"-> {src} -> {dst} bytes ({(1-dst/src)*100:.0f}% menos)")
check("comprimir (PDF valido)", valid, f"-> {pdfops.page_count(comp)} pags")

# --- UI ---
try:
    from cajapdf.app import App
    root = tk.Tk()
    root.withdraw()
    App(root)
    root.update_idletasks()
    root.destroy()
    check("UI construida", True)
except Exception as exc:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check("UI construida", False, str(exc))

print("\nRESULTADO:", "TODO OK" if ok else "HAY FALLOS")
sys.exit(0 if ok else 1)

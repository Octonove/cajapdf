"""Ventana principal de CajaPDF."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import APP_NAME, APP_VERSION
from . import pdfops, theme
from .config import default_output_dir

logger = logging.getLogger(__name__)


def run_async(root: tk.Misc, func, on_done) -> None:
    box: dict = {}

    def worker():
        try:
            box["value"] = func()
        except Exception as exc:  # noqa: BLE001
            box["error"] = exc

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def poll():
        if t.is_alive():
            try:
                root.after(120, poll)
            except tk.TclError:
                pass
            return
        on_done(box.get("value"), box.get("error"))

    try:
        root.after(120, poll)
    except tk.TclError:
        pass


def human(nbytes: float) -> str:
    n = float(nbytes)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{int(n)} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.outdir = str(default_output_dir())
        self._busy = False
        self._build_ui()

    # ----------------------------------------------------------------- UI
    def _build_ui(self) -> None:
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        theme.apply(self.root)
        theme.header(self.root, APP_NAME, "Unir · Dividir · Comprimir PDF — 100% en tu PC")

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=12, pady=8)
        self._build_merge_tab(nb)
        self._build_split_tab(nb)
        self._build_compress_tab(nb)

        self.status = theme.status_bar(self.root, "Listo. Tus archivos no salen de este equipo.")

        self.root.update_idletasks()
        w = max(640, self.root.winfo_reqwidth() + 24)
        h = self.root.winfo_reqheight() + 12
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(min(w, 680), min(h, 520))

    # ------------------------------------------------------------- Unir
    def _build_merge_tab(self, nb) -> None:
        tab = ttk.Frame(nb, padding=14)
        nb.add(tab, text="  Unir  ")

        ttk.Label(tab, text="PDFs a unir (en este orden):",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        body = ttk.Frame(tab)
        body.pack(fill="both", expand=True, pady=6)
        self.merge_list = tk.Listbox(body, height=8, selectmode="extended",
                                     activestyle="none")
        self.merge_list.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(body, command=self.merge_list.yview)
        sb.pack(side="left", fill="y")
        self.merge_list.config(yscrollcommand=sb.set)

        btns = ttk.Frame(body)
        btns.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(btns, text="Anadir...", command=self._merge_add).pack(fill="x", pady=2)
        ttk.Button(btns, text="Quitar", command=self._merge_remove).pack(fill="x", pady=2)
        ttk.Button(btns, text="Subir", command=lambda: self._merge_move(-1)).pack(fill="x", pady=2)
        ttk.Button(btns, text="Bajar", command=lambda: self._merge_move(1)).pack(fill="x", pady=2)
        ttk.Button(btns, text="Limpiar", command=lambda: self.merge_list.delete(0, "end")).pack(fill="x", pady=2)

        ttk.Button(tab, text="Unir y guardar...", style="Primary.TButton",
                   command=self._do_merge).pack(anchor="w", pady=(8, 0))

    def _merge_add(self) -> None:
        files = filedialog.askopenfilenames(
            title="Elige PDFs", filetypes=[("PDF", "*.pdf")])
        for f in files:
            self.merge_list.insert("end", f)

    def _merge_remove(self) -> None:
        for i in reversed(self.merge_list.curselection()):
            self.merge_list.delete(i)

    def _merge_move(self, delta: int) -> None:
        sel = self.merge_list.curselection()
        if not sel:
            return
        i = sel[0]
        j = i + delta
        if j < 0 or j >= self.merge_list.size():
            return
        text = self.merge_list.get(i)
        self.merge_list.delete(i)
        self.merge_list.insert(j, text)
        self.merge_list.selection_set(j)

    def _do_merge(self) -> None:
        items = list(self.merge_list.get(0, "end"))
        if len(items) < 2:
            messagebox.showinfo(APP_NAME, "Anade al menos 2 PDFs para unir.")
            return
        out = filedialog.asksaveasfilename(
            initialdir=self.outdir, initialfile="unido.pdf",
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not out:
            return
        self._run(lambda: pdfops.merge(items, out),
                  lambda v, e: self._done(e, f"PDF unido guardado:\n{out}", out))

    # ----------------------------------------------------------- Dividir
    def _build_split_tab(self, nb) -> None:
        tab = ttk.Frame(nb, padding=14)
        nb.add(tab, text="  Dividir  ")

        row = ttk.Frame(tab)
        row.pack(fill="x")
        ttk.Button(row, text="Elegir PDF...", command=self._split_pick).pack(side="left")
        self.split_lbl = ttk.Label(row, text="Ningun PDF elegido", foreground="#666")
        self.split_lbl.pack(side="left", padx=10)
        self.split_path = None

        mode = ttk.LabelFrame(tab, text="Modo", padding=10)
        mode.pack(fill="x", pady=10)
        self.split_mode = tk.StringVar(value="each")
        ttk.Radiobutton(mode, text="Una PDF por cada pagina", value="each",
                        variable=self.split_mode).pack(anchor="w")
        r2 = ttk.Frame(mode)
        r2.pack(anchor="w", pady=2)
        ttk.Radiobutton(r2, text="Extraer paginas de la", value="range",
                        variable=self.split_mode).pack(side="left")
        self.split_from = tk.IntVar(value=1)
        self.split_to = tk.IntVar(value=1)
        ttk.Spinbox(r2, from_=1, to=99999, width=5, textvariable=self.split_from).pack(side="left", padx=4)
        ttk.Label(r2, text="a la").pack(side="left")
        ttk.Spinbox(r2, from_=1, to=99999, width=5, textvariable=self.split_to).pack(side="left", padx=4)

        ttk.Button(tab, text="Dividir...", style="Primary.TButton",
                   command=self._do_split).pack(anchor="w")

    def _split_pick(self) -> None:
        f = filedialog.askopenfilename(title="Elige un PDF", filetypes=[("PDF", "*.pdf")])
        if not f:
            return
        try:
            n = pdfops.page_count(f)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, f"No se pudo leer el PDF:\n{exc}")
            return
        self.split_path = f
        self.split_lbl.configure(text=f"{Path(f).name}  ({n} paginas)")
        self.split_to.set(n)

    def _do_split(self) -> None:
        if not self.split_path:
            messagebox.showinfo(APP_NAME, "Elige primero un PDF.")
            return
        if self.split_mode.get() == "each":
            d = filedialog.askdirectory(title="Carpeta de salida", initialdir=self.outdir)
            if not d:
                return
            self._run(lambda: pdfops.split_each_page(self.split_path, d),
                      lambda v, e: self._done(e, f"Generadas {len(v) if v else 0} paginas en:\n{d}", d))
        else:
            a, b = self.split_from.get(), self.split_to.get()
            out = filedialog.asksaveasfilename(
                initialdir=self.outdir, initialfile=f"{Path(self.split_path).stem}_{a}-{b}.pdf",
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not out:
                return
            self._run(lambda: pdfops.split_range(self.split_path, out, a, b),
                      lambda v, e: self._done(e, f"Paginas {a}-{b} guardadas:\n{out}", out))

    # ---------------------------------------------------------- Comprimir
    def _build_compress_tab(self, nb) -> None:
        tab = ttk.Frame(nb, padding=14)
        nb.add(tab, text="  Comprimir  ")

        row = ttk.Frame(tab)
        row.pack(fill="x")
        ttk.Button(row, text="Elegir PDF...", command=self._compress_pick).pack(side="left")
        self.compress_lbl = ttk.Label(row, text="Ningun PDF elegido", foreground="#666")
        self.compress_lbl.pack(side="left", padx=10)
        self.compress_path = None

        opt = ttk.LabelFrame(tab, text="Nivel de compresion", padding=10)
        opt.pack(fill="x", pady=10)
        self.compress_level = tk.StringVar(value="media")
        for label, val in (("Suave (mas calidad)", "suave"),
                           ("Media (recomendado)", "media"),
                           ("Fuerte (menor tamano)", "fuerte")):
            ttk.Radiobutton(opt, text=label, value=val,
                            variable=self.compress_level).pack(anchor="w")
        ttk.Label(tab, text="Reduce el peso recomprimiendo las imagenes del PDF. "
                            "Nunca deja el archivo mas grande que el original.",
                  foreground="#888", wraplength=560, justify="left").pack(anchor="w", pady=(0, 8))

        ttk.Button(tab, text="Comprimir y guardar...", style="Primary.TButton",
                   command=self._do_compress).pack(anchor="w")

    def _compress_pick(self) -> None:
        f = filedialog.askopenfilename(title="Elige un PDF", filetypes=[("PDF", "*.pdf")])
        if not f:
            return
        self.compress_path = f
        size = Path(f).stat().st_size
        self.compress_lbl.configure(text=f"{Path(f).name}  ({human(size)})")

    def _do_compress(self) -> None:
        if not self.compress_path:
            messagebox.showinfo(APP_NAME, "Elige primero un PDF.")
            return
        # calidad JPEG y resolucion maxima (lado mayor en px) por nivel: el
        # remuestreo es lo que de verdad reduce fotos/disenos a alta resolucion
        quality, max_side = {"suave": (75, 2200),
                             "media": (55, 1600),
                             "fuerte": (38, 1100)}[self.compress_level.get()]
        out = filedialog.asksaveasfilename(
            initialdir=self.outdir,
            initialfile=f"{Path(self.compress_path).stem}_comprimido.pdf",
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not out:
            return
        if Path(out).resolve() == Path(self.compress_path).resolve():
            messagebox.showinfo(APP_NAME, "Elige un nombre de archivo distinto "
                                          "del PDF original.")
            return

        def work():
            return pdfops.compress(self.compress_path, out, quality=quality,
                                   max_side=max_side)

        def done(value, error):
            if error:
                self._done(error, "", out)
                return
            src, dst = value
            pct = (1 - dst / src) * 100 if src else 0
            self._busy_off()
            self._set_status(f"Comprimido: {human(src)} -> {human(dst)} ({pct:.0f}% menos).")
            if messagebox.askyesno(APP_NAME,
                                   f"Listo.\n{human(src)} -> {human(dst)} ({pct:.0f}% menos)\n\n"
                                   f"Guardado en:\n{out}\n\n¿Abrir la carpeta?"):
                self._open_folder(out)

        self._run(work, done)

    # ------------------------------------------------------------- comun
    def _run(self, func, on_done) -> None:
        if self._busy:
            return
        self._busy = True
        self._set_status("Procesando...")
        run_async(self.root, func, on_done)

    def _busy_off(self) -> None:
        self._busy = False

    def _done(self, error, ok_msg: str, target: str) -> None:
        self._busy_off()
        if error:
            logger.exception("Operacion PDF fallo", exc_info=error)
            self._set_status("La operacion fallo.")
            messagebox.showerror(APP_NAME, f"No se pudo completar:\n{error}")
            return
        self._set_status(ok_msg.replace("\n", " "))
        if messagebox.askyesno(APP_NAME, f"{ok_msg}\n\n¿Abrir la carpeta?"):
            self._open_folder(target)

    def _set_status(self, text: str) -> None:
        try:
            self.status.configure(text=text)
        except tk.TclError:
            pass

    def _open_folder(self, path: str) -> None:
        p = path if Path(path).is_dir() else str(Path(path).parent)
        try:
            if Path(path).is_file():
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                os.startfile(p)  # type: ignore[attr-defined]
        except OSError:
            pass

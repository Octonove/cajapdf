"""Punto de entrada de CajaPDF."""

from __future__ import annotations

import logging
import sys
import tkinter as tk
from tkinter import messagebox

from . import APP_NAME
from .app import App
from .config import setup_logging

logger = logging.getLogger(__name__)


def _excepthook(exc_type, exc, tb):
    logger.error("Excepcion no controlada", exc_info=(exc_type, exc, tb))


def main() -> None:
    try:
        setup_logging()
    except Exception:  # noqa: BLE001
        pass
    sys.excepthook = _excepthook
    try:
        root = tk.Tk()
        App(root)
        root.mainloop()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo al iniciar CajaPDF")
        try:
            messagebox.showerror(APP_NAME, f"Error al iniciar CajaPDF:\n{exc}")
        except Exception:  # noqa: BLE001
            pass
        raise


if __name__ == "__main__":
    main()

"""Rutas de datos y logging (a prueba de %APPDATA% no escribible)."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

from . import APP_NAME

logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    for base in (os.environ.get("APPDATA"), str(Path.home())):
        if not base:
            continue
        d = Path(base) / APP_NAME
        try:
            d.mkdir(parents=True, exist_ok=True)
            return d
        except OSError:
            continue
    d = Path(tempfile.gettempdir()) / APP_NAME
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def default_output_dir() -> Path:
    d = Path.home() / "Documents" / APP_NAME
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        d = get_data_dir()
    return d


LOG_PATH = get_data_dir() / "cajapdf.log"


def setup_logging() -> None:
    handlers: list[logging.Handler] = []
    try:
        handlers.append(logging.FileHandler(LOG_PATH, encoding="utf-8"))
    except OSError:
        try:
            handlers.append(logging.FileHandler(
                Path(tempfile.gettempdir()) / "cajapdf.log", encoding="utf-8"))
        except OSError:
            pass
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler(sys.stderr))
    if not handlers:
        handlers.append(logging.NullHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

# -*- mode: python ; coding: utf-8 -*-
"""Spec de PyInstaller para CajaPDF (onedir, ventana sin consola)."""

import os

block_cipher = None
icon_path = os.environ.get("APP_ICON", "")
icon_arg = icon_path if (icon_path and os.path.isfile(icon_path)) else None

a = Analysis(
    ['..\\CajaPDF.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'scipy', 'pandas', 'matplotlib', 'PyQt5', 'PyQt6', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='CajaPDF',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False, target_arch=None,
    codesign_identity=None, entitlements_file=None, icon=icon_arg,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas,
               strip=False, upx=False, upx_exclude=[], name='CajaPDF')

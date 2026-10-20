"""Resolve the libmpv shipped by PyInstaller before importing python-mpv."""
import ctypes.util
import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    root = Path(sys._MEIPASS)
    names = ('mpv-2.dll', 'libmpv-2.dll', 'libmpv.so.2', 'libmpv.dylib')
    library = next((root / name for name in names if (root / name).is_file()), None)
    if library is None:
        library = next(iter(root.glob('libmpv.so.*')), None)
    if library is None:
        library = next(iter(root.glob('libmpv.*.dylib')), None)
    if library is None:
        raise RuntimeError('La distribution ne contient pas libmpv')
    if os.name == 'nt':
        _mpv_dll_directory = os.add_dll_directory(str(root))
    _original_find_library = ctypes.util.find_library

    def _find_library(name):
        if name in ('mpv', 'mpv-2.dll', 'libmpv-2.dll', 'mpv-1.dll'):
            return str(library)
        return _original_find_library(name)

    ctypes.util.find_library = _find_library

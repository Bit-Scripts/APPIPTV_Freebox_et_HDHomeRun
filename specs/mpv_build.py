"""Shared build inputs. IPTV_LIBMPV must name a native shared library."""
import os
from pathlib import Path


def build_inputs(spec_directory):
    root = Path(spec_directory).resolve().parent
    library = Path(os.environ.get('IPTV_LIBMPV', ''))
    if not library.is_file():
        raise RuntimeError('Définir IPTV_LIBMPV vers libmpv.so.2, libmpv.dylib ou mpv-2.dll')
    return dict(
        scripts=[str(root / 'main.py')],
        pathex=[str(root)],
        binaries=([(str(item), '.') for item in library.parent.glob('*.dll')]
                  if os.name == 'nt' else [(str(library.absolute()), '.')]),
        datas=[(str(root / 'assets'), 'assets')],
        hiddenimports=['mpv', 'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets'],
        runtime_hooks=[str(root / 'specs' / 'mpv_runtime_hook.py')],
    )

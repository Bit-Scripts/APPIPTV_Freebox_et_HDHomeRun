"""Load the exact native library selected for packaging, not a system fallback."""
import ctypes.util
import os
from pathlib import Path

library = str(Path(os.environ['IPTV_LIBMPV']).resolve(strict=True))
original_find_library = ctypes.util.find_library
ctypes.util.find_library = lambda name: library if name in (
    'mpv', 'mpv-2.dll', 'libmpv-2.dll', 'mpv-1.dll') else original_find_library(name)
import mpv

player = mpv.MPV(vo='null', ao='null', config=False)
try:
    print('Native libmpv OK:', library, player.mpv_version)
finally:
    player.terminate()

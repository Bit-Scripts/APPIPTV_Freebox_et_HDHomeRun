# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys
sys.path.insert(0, SPECPATH)
from mpv_build import build_inputs

inputs = build_inputs(SPECPATH)
a = Analysis(inputs.pop('scripts'), **inputs, hookspath=[], hooksconfig={}, excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='APPIPTV',
          console=False, strip=False, upx=False,
          icon=str(Path(SPECPATH).parent / 'assets/image/missing_icon.ico'))

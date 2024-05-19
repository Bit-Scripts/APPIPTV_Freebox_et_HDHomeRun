# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../main.py'],
    pathex=['.'],
    binaries=[
        ('/Applications/VLC.app/Contents/MacOS/lib/*', 'lib/'),
        ('/Applications/VLC.app/Contents/MacOS/plugins/*', 'plugins/'),
        ('../src/*', './src/')],
    datas=[('../assets/image/*', './assets/image/'), 
        ('../assets/logos/*', './assets/logos/'),
    ],
    hiddenimports=['vlc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='APPIPTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='APPIPTV',
)
app = BUNDLE(
    coll,
    name='APPIPTV.app',
    icon='../assets/image/missing_icon.icns',
    bundle_identifier=None,
)

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import exec_statement

block_cipher = None  # Ajout si nécessaire pour 'cipher' dans PYZ

a = Analysis(
    ['../main.py'],
    pathex=['.'],
    binaries=[
        ('C:\\Program Files\\VideoLAN\\VLC\\libvlc.dll', '.'),
        ('C:\\Program Files\\VideoLAN\\VLC\\libvlccore.dll', '.'),
        ('C:\\Program Files\\VideoLAN\\VLC\\plugins\\*', 'plugins'), 
        ('..\\src\\*', '.\\src\\')
    ],
    datas=[('..\\assets\\image\\*', '.\\assets\\image\\'), 
        ('..\\assets\\logos\\*', '.\\assets\\logos\\'),
    ],
    hiddenimports=['vlc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='APPIPTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Change to False if you do not want a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/image/missing_icon.ico',  # Chemin vers l'icône
)



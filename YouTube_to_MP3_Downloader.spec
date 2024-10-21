# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:\\apps\\youtube\\youtube_to_mp3.py'],
    pathex=[],
    binaries=[('E:\\apps\\youtube\\ffmpeg\\bin\\ffmpeg.exe', 'ffmpeg/bin')],
    datas=[('E:\\apps\\youtube\\ffmpeg\\bin', 'ffmpeg/bin')],
    hiddenimports=['pydub.exceptions'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='YouTube_to_MP3_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

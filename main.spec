# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],

    binaries=[],

    datas=[
        ('assets', 'assets'),
        ('database', 'database'),
        ('backend', 'backend'),
    ],

    hiddenimports=[
        'uvicorn',
        'fastapi',
        'starlette',
        'requests',
        'pymysql',
        'PIL',
        'matplotlib',
        'numpy',
        'serial',
        'serial.tools.list_ports',
        'customtkinter',
        'tkinter'

        hiddenimports=[
    'uvicorn',
    'fastapi',
    'starlette',
    'requests',
    'pymysql',
    'PIL',
    'matplotlib',
    'numpy',
    'serial',
    'serial.tools.list_ports',
    'customtkinter',
    'tkinter',
    'sqlite3'
],
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    excludes=[
        'pytest',
        'jupyter',
        'IPython'
    ],

    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,

    name='ThermalManager',

    debug=False,

    bootloader_ignore_signals=False,
    strip=False,

    upx=False,

    console=False,

    disable_windowed_traceback=False,

    argv_emulation=False,
    target_arch=None,

    codesign_identity=None,
    entitlements_file=None,

    icon='assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,

    strip=False,

    upx=False,

    upx_exclude=[],

    name='ThermalManager',
)
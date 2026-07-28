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
<<<<<<< Updated upstream
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

=======
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
        'customtkinter'
    ],
>>>>>>> Stashed changes

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
<<<<<<< Updated upstream

    excludes=[
        'pytest',
        'jupyter',
        'IPython'
    ],

=======
    excludes=[],
>>>>>>> Stashed changes
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
<<<<<<< Updated upstream

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
=======
    name='main',
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
    icon=['assets\\logo.ico'],
>>>>>>> Stashed changes
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
<<<<<<< Updated upstream

    strip=False,

    upx=False,

    upx_exclude=[],

    name='ThermalManager',
=======
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
>>>>>>> Stashed changes
)
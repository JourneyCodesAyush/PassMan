# passman.spec
a = Analysis(
    ['src/passman/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'passman.auth',
        'passman.crypto',
        'passman.database',
        'passman.schema',
        'passman.utils',
        'passman.vault',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='passman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Excel2PDFCatalog
Uso: pyinstaller Excel2PDFCatalog.spec
"""

import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Raccogli tutti i file necessari per reportlab
reportlab_datas, reportlab_binaries, reportlab_hiddenimports = collect_all('reportlab')

# Dati aggiuntivi da includere
added_files = [
    ('app', 'app'),
    ('fonts', 'fonts'),
    ('img_general', 'img_general'),
    ('example_excel', 'example_excel'),
    ('Excel2PDFCatalog.config', '.'),
]

# Aggiungi dati di reportlab
added_files.extend(reportlab_datas)

# Hidden imports necessari
hiddenimports = [
    'openpyxl',
    'openpyxl.cell._writer',
    'pandas',
    'reportlab',
    'reportlab.pdfgen',
    'reportlab.lib',
    'reportlab.platypus',
    'PIL',
    'PIL._tkinter_finder',
] + reportlab_hiddenimports

# Analisi dell'applicazione
a = Analysis(
    ['Excel2PDFCatalog.py'],
    pathex=[],
    binaries=reportlab_binaries,
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pytest',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Rimuovi duplicati
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Configurazione per Windows
if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Excel2PDFCatalog',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # Nasconde la console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.ico' if os.path.exists('icon.ico') else None,
    )

# Configurazione per macOS
elif sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Excel2PDFCatalog',
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
        icon='icon.icns' if os.path.exists('icon.icns') else None,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='Excel2PDFCatalog',
    )
    
    app = BUNDLE(
        coll,
        name='Excel2PDFCatalog.app',
        icon='icon.icns' if os.path.exists('icon.icns') else None,
        bundle_identifier='com.alexscarcella.excel2pdfcatalog',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
        },
    )
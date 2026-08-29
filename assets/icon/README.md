# App icon

Icona dell'applicazione Excel2PDFCatalog. Tema: un **catalogo prodotti aperto**
(libretto/brochure) nella palette di default dell'app — terracotta `#c37225` su
crema `#e6dbc6` — con la pagina di destra a griglia 3×3 come il PDF generato.

| file | uso |
|------|-----|
| `icon.ico` | Windows: `pyinstaller --icon` + `root.iconbitmap()` |
| `icon.icns` | macOS: `pyinstaller --icon` |
| `icon_256.png` | icona della finestra Tk a runtime (`root.iconphoto()` in `app/ui_interface.py`) |
| `icon_1024/512/128.png` | master / anteprime / store |

Tutti i file sono **generati** da `make_icon.py` (serve solo Pillow, già in
`app/requirements.txt`). Per modificare l'icona si edita lo script e si rigenera:

```bash
python assets/icon/make_icon.py
```

`assets/icon/` è incluso nel bundle PyInstaller (`--add-data`) in
`.github/workflows/build.yml`, così `icon_256.png` è raggiungibile via
`paths_utils.resource_path()` anche nell'app impacchettata.

#!/usr/bin/env python3
"""tools/screenshot.py - cattura screenshot della UI Tkinter, su Windows e macOS.

Come funziona
-------------
``ui_interface.build_UI_and_GO()`` costruisce la finestra e poi entra in
``root.mainloop()`` (bloccante). Questo script sostituisce
``tkinter.Tk.mainloop`` con una routine che porta la finestra in primo piano,
la lascia disegnare, cattura una o piu' immagini con ``PIL.ImageGrab`` (gia'
dipendenza del progetto: funziona sia su Windows sia su macOS) e infine chiude
la finestra. Non tocca ``config.json`` e non esegue ``build_pdf()``: apre solo
la UI a scopo di documentazione.

I percorsi mostrati nella scheda *Sources* vengono mascherati per default
(prima parte -> '…', vedi ``--no-censor`` / ``--censor-keep``); le spunte di
validazione ✔ restano invariate perche' leggono il percorso reale.

Uso
---
    python tools/screenshot.py                    # finestra intera -> assets/Preview_<OS>.png
    python tools/screenshot.py --lang en          # forza la lingua della UI
    python tools/screenshot.py --all-tabs         # una PNG per ogni scheda
    python tools/screenshot.py --tab Colors       # solo la scheda che contiene "Colors"
    python tools/screenshot.py --full             # schermo intero, nessun ritaglio
    python tools/screenshot.py --no-censor        # mostra i percorsi per intero
    python tools/screenshot.py --size 1100x720 --out assets --prefix Preview

Note per piattaforma
--------------------
* macOS: la prima volta il processo che lancia lo script (Terminal / iTerm /
  VS Code) deve avere il permesso *Registrazione schermo* in Impostazioni di
  sistema -> Privacy e sicurezza, altrimenti l'immagine mostra solo lo sfondo.
  Pillow ridimensiona il ritaglio Retina alla risoluzione logica; per un PNG
  @2x usare ``screencapture -R x,y,w,h out.png`` a mano.
* Windows: la finestra viene forzata in primo piano; non coprirla o spostarla
  mentre lo script gira (~2 s).

Va eseguito dalla radice del repo (lo script ci si sposta comunque da solo,
perche' ``paths_utils`` risolve i percorsi rispetto al cwd).
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import sys
import time

# --- radice del repo sul path e come cwd --------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)

import tkinter as tk
from tkinter import ttk

try:
    from PIL import ImageGrab
except ImportError:  # pragma: no cover - dipendenza dichiarata in requirements
    sys.exit("Pillow non disponibile: pip install -r app/requirements.txt")

import app.config_utils as config_utils
from app import i18n

OS_NAME = {"Windows": "Windows", "Darwin": "MacOS"}.get(platform.system(), platform.system())


def _censor_path(value, keep=2):
    """Sostituisce la parte iniziale di un percorso con '…', lasciando visibili
    solo gli ultimi ``keep`` segmenti (nasconde utente / unita' / cartelle
    personali negli screenshot). Agnostico al separatore: gestisce sia '\\' sia
    '/', anche misti."""
    s = str(value or "")
    if not s:
        return s
    segments = [p for p in re.split(r"[\\/]+", s) if p]
    if len(segments) <= keep:
        return s
    sep = "\\" if "\\" in s else "/"
    return "…" + sep + sep.join(segments[-keep:])


def _install_path_censor(ui_module, keep):
    """Avvolge ``ui_interface._ellipsize_middle`` cosi' i percorsi mostrati nella
    scheda Sources vengono mascherati *prima* dell'ellissi. Le spunte di
    validazione ✔/✕ leggono il valore reale del percorso, quindi restano verdi."""
    original = ui_module._ellipsize_middle

    def _censored_ellipsize(text, *args, **kwargs):
        return original(_censor_path(text, keep), *args, **kwargs)

    ui_module._ellipsize_middle = _censored_ellipsize


def _pump(root, seconds):
    """Tiene vivo il redraw di Tk per N secondi senza entrare in mainloop()."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            root.update_idletasks()
            root.update()
        except tk.TclError:
            return
        time.sleep(0.02)


def _find_notebook(widget):
    if isinstance(widget, ttk.Notebook):
        return widget
    for child in widget.winfo_children():
        found = _find_notebook(child)
        if found is not None:
            return found
    return None


def _bring_to_front(root):
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    try:
        root.focus_force()
    except tk.TclError:
        pass
    _pump(root, 0.4)


def _grab(root, path, args):
    _pump(root, 0.25)
    if args.full:
        img = ImageGrab.grab(all_screens=True)
    else:
        x, y = root.winfo_rootx(), root.winfo_rooty()
        w, h = root.winfo_width(), root.winfo_height()
        bbox = (x - args.pad, y - args.titlebar, x + w + args.pad, y + h + args.pad)
        try:
            img = ImageGrab.grab(bbox=bbox, all_screens=True)
        except Exception as exc:  # bbox fuori dallo schermo virtuale, monitor multipli, ecc.
            print(f"  grab con bbox fallito ({exc}); catturo lo schermo intero")
            img = ImageGrab.grab(all_screens=True)
    img.save(path)
    try:
        shown = os.path.relpath(path, _REPO_ROOT)
    except ValueError:  # --out su un'altra unita' (Windows): mostra il path assoluto
        shown = path
    print(f"  scritto {shown}  ({img.width}x{img.height})")


def _make_screenshot_mainloop(args):
    """Ritorna una funzione compatibile con la firma di ``tk.Tk.mainloop``."""

    def _screenshot_mainloop(self, n=0):
        root = self
        if args.size:
            root.geometry(args.size)
            _pump(root, 0.2)
        _bring_to_front(root)

        out_dir = os.path.join(_REPO_ROOT, args.out)
        os.makedirs(out_dir, exist_ok=True)

        notebook = _find_notebook(root)
        per_tab = args.all_tabs or bool(args.tab)

        if notebook is not None and per_tab:
            for tab_id in notebook.tabs():
                label = notebook.tab(tab_id, "text")
                if args.tab and args.tab.lower() not in label.lower():
                    continue
                notebook.select(tab_id)
                _pump(root, 0.2)
                safe = "".join(c for c in label if c.isalnum()) or tab_id.rsplit(".", 1)[-1]
                _grab(root, os.path.join(out_dir, f"{args.prefix}_{OS_NAME}_{safe}.png"), args)
        else:
            if notebook is not None:
                notebook.select(notebook.tabs()[0])
                _pump(root, 0.2)
            name = args.name or f"{args.prefix}_{OS_NAME}.png"
            _grab(root, os.path.join(out_dir, name), args)

        try:
            root.attributes("-topmost", False)
            root.destroy()
        except tk.TclError:
            pass

    return _screenshot_mainloop


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot della UI Excel2PDFCatalog (Windows/macOS).")
    parser.add_argument("--lang", choices=["it", "en"], help="forza la lingua della UI")
    parser.add_argument("--all-tabs", action="store_true",
                        help="una PNG per ogni scheda del Notebook")
    parser.add_argument("--tab", help="cattura solo la scheda il cui nome contiene questo testo")
    parser.add_argument("--full", action="store_true",
                        help="cattura tutto lo schermo, senza ritaglio sulla finestra")
    parser.add_argument("--size", help="forza la geometria della finestra, es. 1100x720")
    parser.add_argument("--out", default="assets",
                        help="cartella di destinazione (default: assets)")
    parser.add_argument("--prefix", default="Preview",
                        help="prefisso dei file generati (default: Preview)")
    parser.add_argument("--name", help="nome file esatto per lo scatto singolo (ignora --prefix)")
    parser.add_argument("--pad", type=int, default=6,
                        help="px aggiunti a sinistra/destra/basso attorno alla finestra (default: 6)")
    parser.add_argument("--titlebar", type=int, default=40,
                        help="px aggiunti sopra la finestra per includere la barra del titolo "
                             "(default: 40; 0 = solo area client, sempre pulita a ogni DPI)")
    parser.add_argument("--no-censor", dest="censor", action="store_false",
                        help="NON mascherare i percorsi nella scheda Sources (di default la "
                             "prima parte di ogni percorso viene sostituita con '…')")
    parser.add_argument("--censor-keep", type=int, default=2,
                        help="segmenti finali del percorso lasciati visibili quando si "
                             "maschera (default: 2)")
    parser.set_defaults(censor=True)
    args = parser.parse_args()

    config_utils.load_config()
    if args.lang:
        i18n.set_language(args.lang)
        config_utils.language = i18n.get_language()

    # Sostituisce il mainloop bloccante con la routine di cattura.
    tk.Tk.mainloop = _make_screenshot_mainloop(args)

    import app.ui_interface as ui_interface

    if args.censor:
        _install_path_censor(ui_interface, args.censor_keep)

    print(f"UI: OS={OS_NAME}  lingua={i18n.get_language()}  "
          f"censura percorsi={'on' if args.censor else 'off'}  ->  cartella '{args.out}/'")
    if platform.system() == "Darwin":
        print("macOS: se l'immagine risulta vuota, abilita 'Registrazione schermo' "
              "per il terminale in Impostazioni di sistema > Privacy e sicurezza.")
    ui_interface.build_UI_and_GO()
    print("Fatto.")


if __name__ == "__main__":
    main()

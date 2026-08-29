"""
Generatore dell'icona applicazione di Excel2PDFCatalog.

Concept -- aderente alla parola "catalogo": un catalogo prodotti *aperto*
(libretto / brochure) su un riquadro color terracotta, la tinta di default
dell'app (#c37225 su crema #e6dbc6). La pagina di destra mostra la griglia
3x3 di prodotti -- lo stesso layout del PDF generato (page template
`Matrix_3x3`) -- quella di sinistra la fascia-titolo con le righe di testo
delle schede / listino, con una riga evidenziata in verde "prezzo".

Rende a 4x (supersampling) e riduce con LANCZOS. Riscrive, nella cartella
che lo contiene:

    icon_1024.png / icon_512.png / icon_256.png / icon_128.png
    icon.ico     Windows  (PyInstaller --icon, root.iconbitmap)
    icon.icns    macOS    (PyInstaller --icon)

`icon_256.png` e' anche quello caricato a runtime da `root.iconphoto()` in
app/ui_interface.py. Rigenerare con:  python assets/icon/make_icon.py

Serve Pillow (gia' in app/requirements.txt).
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
if "--dest" in sys.argv:
    OUT_DIR = sys.argv[sys.argv.index("--dest") + 1]
os.makedirs(OUT_DIR, exist_ok=True)

S = 1024          # dimensione logica
K = 4             # fattore di supersampling
W = S * K


def px(v: float) -> int:
    return int(round(v * K))


def rr(xy, radius):
    return [px(c) for c in xy], px(radius)


# ---- colori ---------------------------------------------------------------
TILE_TOP = (222, 138, 62)      # terracotta chiaro
TILE_BOT = (168, 90, 26)       # terracotta scuro
TILE_GLOW = (255, 214, 170)

PAGE = (248, 241, 223)         # crema
PAGE_EDGE = (231, 220, 191)    # crema piu' scuro (bordo pila pagine)
FOLD_SHADOW = (120, 80, 40)

ACCENT = (195, 114, 37)        # #c37225  brand
ACCENT_SOFT = (214, 150, 92)
TEXT_BAR = (150, 110, 74)
GREEN = (77, 122, 66)          # accento "prezzo / novita'"
SHADOW = (60, 30, 8)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ---- composizione -------------------------------------------------------
img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

margin = 40
radius = 210
tile_box = (margin, margin, S - margin, S - margin)

grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
gd = ImageDraw.Draw(grad)
inner_h = W - 2 * px(margin)
for i in range(inner_h):
    t = i / max(1, inner_h - 1)
    gd.line([(px(margin), px(margin) + i), (W - px(margin), px(margin) + i)],
            fill=lerp(TILE_TOP, TILE_BOT, t) + (255,))

mask = Image.new("L", (W, W), 0)
ImageDraw.Draw(mask).rounded_rectangle([px(c) for c in tile_box], px(radius), fill=255)
img.paste(grad, (0, 0), mask)

glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([px(-120), px(-260), px(720), px(360)],
                             fill=TILE_GLOW + (70,))
glow = glow.filter(ImageFilter.GaussianBlur(px(60)))
img = Image.alpha_composite(img, Image.composite(
    glow, Image.new("RGBA", (W, W), (0, 0, 0, 0)), mask))
draw = ImageDraw.Draw(img)

# ombra del libretto
shadow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle(
    [px(196), px(360), px(838), px(792)], px(40), fill=SHADOW + (120,))
shadow = shadow.filter(ImageFilter.GaussianBlur(px(34)))
img = Image.alpha_composite(img, shadow)
draw = ImageDraw.Draw(img)

# pila di pagine dietro (multi-pagina)
for dx, dy in ((26, 30), (14, 16)):
    draw.polygon([(px(176 + dx), px(300 + dy)), (px(848 + dx), px(300 + dy)),
                  (px(848 + dx), px(712 + dy)), (px(176 + dx), px(712 + dy))],
                 fill=PAGE_EDGE + (255,))

# due pagine aperte (leggera "V" allo spine)
spine_l, spine_r = 505, 519
left_page = [(180, 306), (spine_l, 330), (spine_l, 726), (180, 702)]
right_page = [(spine_r, 330), (844, 306), (844, 702), (spine_r, 726)]
draw.polygon([(px(x), px(y)) for x, y in left_page], fill=PAGE + (255,))
draw.polygon([(px(x), px(y)) for x, y in right_page], fill=PAGE + (255,))

# ombra di piega vicino allo spine
fold = Image.new("RGBA", (W, W), (0, 0, 0, 0))
fdd = ImageDraw.Draw(fold)
fdd.polygon([(px(spine_l - 60), px(330)), (px(spine_l), px(332)),
             (px(spine_l), px(724)), (px(spine_l - 60), px(716))],
            fill=FOLD_SHADOW + (60,))
fdd.polygon([(px(spine_r), px(332)), (px(spine_r + 60), px(330)),
             (px(spine_r + 60), px(716)), (px(spine_r), px(724))],
            fill=FOLD_SHADOW + (60,))
fold = fold.filter(ImageFilter.GaussianBlur(px(14)))
img = Image.alpha_composite(img, fold)
draw = ImageDraw.Draw(img)

# highlight sul bordo superiore delle pagine
draw.line([(px(182), px(308)), (px(spine_l - 2), px(332))],
          fill=(255, 255, 255, 150), width=px(3))
draw.line([(px(spine_r + 2), px(332)), (px(842), px(308))],
          fill=(255, 255, 255, 150), width=px(3))

# pagina sinistra: fascia-titolo + righe di testo (ultima = "prezzo" in verde)
box, r = rr((214, 372, 470, 420), 14)
draw.rounded_rectangle(box, r, fill=ACCENT + (255,))
for i, wdt in enumerate((250, 250, 190)):
    y = 452 + i * 40
    box, r = rr((214, y, 214 + wdt, y + 20), 10)
    draw.rounded_rectangle(box, r, fill=TEXT_BAR + (140,))
box, r = rr((214, 572, 334, 592), 10)
draw.rounded_rectangle(box, r, fill=GREEN + (200,))

# pagina destra: griglia 3x3 di prodotti
gx0, gy0 = 556, 376
cell, gap = 84, 16
tints = [ACCENT, ACCENT_SOFT, ACCENT,
         ACCENT_SOFT, ACCENT, GREEN,
         ACCENT, GREEN, ACCENT_SOFT]
for idx in range(9):
    rrow, ccol = divmod(idx, 3)
    x = gx0 + ccol * (cell + gap)
    y = gy0 + rrow * (cell + gap)
    box, r = rr((x, y, x + cell, y + cell), 16)
    draw.rounded_rectangle(box, r, fill=tints[idx] + (255,))
    box, r = rr((x + 12, y + 12, x + cell - 24, y + 26), 7)
    draw.rounded_rectangle(box, r, fill=(255, 255, 255, 60))

# ---- export -----------------------------------------------------------
base = img.resize((S, S), Image.LANCZOS)

for sz in (1024, 512, 256, 128):
    base.resize((sz, sz), Image.LANCZOS).save(os.path.join(OUT_DIR, f"icon_{sz}.png"))

ico_sizes = [16, 24, 32, 48, 64, 128, 256]
frames = [base.resize((s, s), Image.LANCZOS) for s in ico_sizes]
frames[-1].save(os.path.join(OUT_DIR, "icon.ico"), format="ICO",
                sizes=[(s, s) for s in ico_sizes], append_images=frames[:-1])

try:
    base.save(os.path.join(OUT_DIR, "icon.icns"), format="ICNS")
except Exception as exc:  # pragma: no cover
    print("icns FAILED:", exc)

print("icona rigenerata in", OUT_DIR)

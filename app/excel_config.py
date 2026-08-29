# excel_config.py
# Gestione di 'Excel2PDFCatalog.config' (INI), senza Tkinter e senza dipendenze
# esterne: puo' essere importato anche dai test.
#
# Contiene le impostazioni "di progetto" storicamente lette SOLO all'import da
# build_PDF.py e non modificabili dalla UI:
#   [Excel]  -> mappatura fra i campi dell'app e i nomi di colonna del foglio .xlsx
#   [Layout] -> MARGIN (cm) e CARD_BORDER_WIDTH (pt, spessore bordo scheda prodotto)
#   [System] -> LOCALE
#
# La UI (tab "Colonne Excel" + sezione "Layout" del tab "Opzioni") legge/scrive i
# dizionari 'columns' / 'layout' / 'system'; config_utils.save_config() invoca
# save(); build_PDF.py rilegge i valori sia all'import sia all'inizio di
# build_pdf(), cosi' le modifiche fatte dalla UI hanno effetto senza riavvio.
#
# Come per config.json (vedi config_utils.py) il file viene letto/scritto in un
# path SCRIVIBILE indipendente dalla cwd: da sorgente coincide con la working
# directory (comportamento storico), in una build PyInstaller punta alla cartella
# dati per-utente e viene "seminato" dalla copia bundlata al primo avvio.

import configparser
import os
import shutil

from app.logger import logger
from app.paths_utils import resource_path, writable_path

INI_NAME = "Excel2PDFCatalog.config"

# Copia di sola lettura (repo / bundle PyInstaller) usata come seme, e copia
# scrivibile effettiva su cui si leggono/scrivono le modifiche. Da sorgente i due
# path coincidono. Sono attributi di modulo cosi' i test possono ridirigerli.
BUNDLED_PATH = resource_path(INI_NAME)
CONFIG_PATH = writable_path(INI_NAME)

# (chiave logica, chiave INI, valore di default, obbligatoria nel foglio Excel?)
# I nomi delle chiavi INI restano identici a quelli storici (badge incluso come
# XLS_BADGE) per non rompere i file gia' esistenti.
COLUMN_KEYS = [
    ("CATEGORY",    "XLS_COLUMN_CATEGORY",    "Cat_Merc",                True),
    ("COMPANY",     "XLS_COLUMN_COMPANY",     "Azienda",                 True),
    ("ITEM",        "XLS_COLUMN_ITEM",        "Nome_Art",                True),
    ("SIZE",        "XLS_COLUMN_SIZE",        "Formato",                 True),
    ("PRICE",       "XLS_COLUMN_PRICE",       "prezzo_vendita_ingrosso", True),
    ("DESCRIPTION", "XLS_COLUMN_DESCRIPTION", "Descrizione_prodotto",    False),
    ("IMG",         "XLS_COLUMN_IMG",         "Codice_Articolo",         True),
    ("BADGE",       "XLS_BADGE",              "Badge",                   True),
]

LAYOUT_DEFAULTS = {"MARGIN": 2.0, "CARD_BORDER_WIDTH": 2.0}
SYSTEM_DEFAULTS = {"LOCALE": "it_IT.UTF-8"}

# Locale piu' comuni proposti dal combo della UI (editabile: si puo' comunque
# digitare un valore specifico della piattaforma, es. Italian_Italy.1252 su
# Windows). Formato POSIX con encoding UTF-8 - copre macOS/Linux e le versioni
# recenti di Windows; ordinati per lingua/regione, con it/en in testa.
COMMON_LOCALES = [
    "it_IT.UTF-8", "en_US.UTF-8", "en_GB.UTF-8", "fr_FR.UTF-8", "de_DE.UTF-8",
    "es_ES.UTF-8", "es_MX.UTF-8", "pt_PT.UTF-8", "pt_BR.UTF-8", "nl_NL.UTF-8",
    "sv_SE.UTF-8", "nb_NO.UTF-8", "da_DK.UTF-8", "fi_FI.UTF-8", "pl_PL.UTF-8",
    "cs_CZ.UTF-8", "sk_SK.UTF-8", "hu_HU.UTF-8", "ro_RO.UTF-8", "el_GR.UTF-8",
    "tr_TR.UTF-8", "ru_RU.UTF-8", "uk_UA.UTF-8", "ar_SA.UTF-8", "he_IL.UTF-8",
    "hi_IN.UTF-8", "zh_CN.UTF-8", "zh_TW.UTF-8", "ja_JP.UTF-8", "ko_KR.UTF-8",
    "th_TH.UTF-8", "vi_VN.UTF-8", "id_ID.UTF-8", "C", "POSIX",
]

_EXCEL_SECTION = "Excel"
_LAYOUT_SECTION = "Layout"
_SYSTEM_SECTION = "System"

# Stato di modulo: scritto dalla UI, letto da build_PDF.py.
columns = {logical: default for logical, _ini, default, _req in COLUMN_KEYS}
layout = dict(LAYOUT_DEFAULTS)
system = dict(SYSTEM_DEFAULTS)


def _seed_writable_copy():
    """Se la copia scrivibile non esiste ancora, la crea da quella bundlata.
    Best-effort: un errore viene loggato ma non blocca (si prosegue sui default)."""
    try:
        if os.path.exists(CONFIG_PATH):
            return
        if not os.path.exists(BUNDLED_PATH):
            return
        if os.path.abspath(BUNDLED_PATH) == os.path.abspath(CONFIG_PATH):
            return
        shutil.copyfile(BUNDLED_PATH, CONFIG_PATH)
        logger.info("excel_config: writable copy seeded (%s <- %s)", CONFIG_PATH, BUNDLED_PATH)
    except OSError as e:
        logger.warning("excel_config: could not seed writable copy (%s)", e)


def load():
    """(Ri)carica 'Excel2PDFCatalog.config' nei dizionari di modulo. Ogni chiave
    mancante o non valida ricade sul proprio default, senza mai sollevare o
    terminare il processo (stessa filosofia di config_utils.load_config())."""
    _seed_writable_copy()

    parser = configparser.ConfigParser()
    try:
        read_ok = parser.read(CONFIG_PATH, encoding="utf-8")
    except (configparser.Error, OSError) as e:
        logger.error("excel_config: cannot parse %s (%s). Using defaults.", CONFIG_PATH, e)
        read_ok = []
    if not read_ok:
        logger.warning("excel_config: %s not found/readable. Using default values.", CONFIG_PATH)

    for logical, ini_key, default, _req in COLUMN_KEYS:
        try:
            value = parser.get(_EXCEL_SECTION, ini_key, fallback=default)
        except configparser.Error:
            value = default
        columns[logical] = (value or "").strip() or default

    for key, default in LAYOUT_DEFAULTS.items():
        raw = parser.get(_LAYOUT_SECTION, key, fallback=None)
        if raw is None:
            logger.warning("excel_config: %s missing. Keeping default %s.", key, default)
            layout[key] = default
            continue
        try:
            layout[key] = float(str(raw).strip())
        except (TypeError, ValueError):
            logger.warning("excel_config: %s invalid (%r). Keeping default %s.", key, raw, default)
            layout[key] = default

    for key, default in SYSTEM_DEFAULTS.items():
        value = parser.get(_SYSTEM_SECTION, key, fallback=default)
        system[key] = (value or "").strip() or default

    logger.info("excel_config loaded from %s", CONFIG_PATH)
    for _logical, ini_key, _default, _req in COLUMN_KEYS:
        logger.info("  %s -> %s", ini_key, columns[_logical])
    for key in LAYOUT_DEFAULTS:
        logger.info("  %s -> %s", key, layout[key])
    for key in SYSTEM_DEFAULTS:
        logger.info("  %s -> %s", key, system[key])


def _fmt_num(value):
    """2.0 -> '2', 1.5 -> '1.5' (niente '.0' inutili nel file scritto a mano)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(f)) if f.is_integer() else format(f, "g")


def save():
    """Serializza i dizionari di modulo su 'Excel2PDFCatalog.config' (copia
    scrivibile). Scrittura manuale invece di ConfigParser.write() per conservare
    i commenti di sezione. Ritorna True se il salvataggio riesce, False altrimenti."""
    lines = [
        "[" + _EXCEL_SECTION + "]",
        "# mapping between the app fields and the column headers of your .xlsx",
    ]
    for logical, ini_key, _default, _req in COLUMN_KEYS:
        lines.append(f"{ini_key} = {columns.get(logical, '')}")
    lines += [
        "",
        "[" + _LAYOUT_SECTION + "]",
        "# MARGIN: A4 sheet margin, in cm",
        "# CARD_BORDER_WIDTH: product-card border thickness, in points",
        f"MARGIN = {_fmt_num(layout.get('MARGIN', LAYOUT_DEFAULTS['MARGIN']))}",
        f"CARD_BORDER_WIDTH = {_fmt_num(layout.get('CARD_BORDER_WIDTH', LAYOUT_DEFAULTS['CARD_BORDER_WIDTH']))}",
        "",
        "[" + _SYSTEM_SECTION + "]",
        "# LOCALE: platform-specific locale string used by build_PDF.py",
        f"LOCALE = {system.get('LOCALE', SYSTEM_DEFAULTS['LOCALE'])}",
        "",
    ]
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("excel_config saved to %s", CONFIG_PATH)
        return True
    except OSError as e:
        logger.error("excel_config: save failed (%s)", e, exc_info=True)
        return False


# --- accessor tipizzati usati da build_PDF.py -------------------------------

def column(logical):
    """Nome della colonna Excel mappata al campo logico dato (stringa vuota se ignoto)."""
    return columns.get(logical, "")


def all_columns():
    """Copia del dizionario 'campo logico -> nome colonna'."""
    return dict(columns)


def required_column_names():
    """Nomi di colonna che DEVONO esistere nel foglio (DESCRIPTION escluso, come
    nella lista 'required_columns' storica di build_pdf())."""
    return [columns[lk] for lk, _ini, _default, req in COLUMN_KEYS if req]


def margin_cm():
    """Margine pagina in cm (float)."""
    try:
        return float(layout.get("MARGIN", LAYOUT_DEFAULTS["MARGIN"]))
    except (TypeError, ValueError):
        return LAYOUT_DEFAULTS["MARGIN"]


def card_border_width():
    """Spessore del bordo della scheda prodotto in punti (float)."""
    try:
        return float(layout.get("CARD_BORDER_WIDTH", LAYOUT_DEFAULTS["CARD_BORDER_WIDTH"]))
    except (TypeError, ValueError):
        return LAYOUT_DEFAULTS["CARD_BORDER_WIDTH"]


def locale_name():
    """Stringa di locale definita in [System]."""
    return system.get("LOCALE", SYSTEM_DEFAULTS["LOCALE"])


# Auto-load all'import: build_PDF.py (e i test che lo importano direttamente,
# senza passare da config_utils.load_config()) trovano i dizionari gia' popolati.
load()

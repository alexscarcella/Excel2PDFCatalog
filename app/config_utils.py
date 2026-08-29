# per generare i requirements.txt
# pip freeze > requirements.txt
#
# per installare i requirements:
# pip install -r requirements.txt

import os
import json
from pathlib import Path
from app.logger import logger
from app.paths_utils import resource_path, writable_path
import app.i18n as i18n

__version__ = "1.1.0"

# CONFIG_FILE e' un path scrivibile e indipendente dalla cwd: quando l'app e'
# impacchettata con PyInstaller su macOS punta a ~/Library/Application Support/
# Excel2PDFCatalog, altrimenti alla working directory (come in passato).
CONFIG_FILE = writable_path("config.json")

# valori di default che poi vengono sovrascritti
# dal file di configurazione JSON
excel_file = resource_path("example_excel/Product list example.xlsx")
txt_intro_file = resource_path("txt_intros/intro_sample_1.txt")
title = "CHANGE THE TITLE"
subtitle = "Change this subtitle"
footer = "Change this footer"

# Lingua dell'interfaccia ("it" | "en"). None = ancora da risolvere: load_config()
# la prende da config.json oppure la deduce dal locale di sistema (i18n.detect_default()).
language = None

# colors_dictionary è una lista (o altro iterabile) di stringhe
colors_dictionary = {"COVER_TITLE_COLOR": "#ffffff",
                    "COVER_SUBTITLE_COLOR": "#ffffff",
                    "COVER_BACKGROUND_COLOR": "#c37225",
                    "FOOTER_COLOR": "#000000",
                    "CATEGORY_TITLE_COLOR": "#000000",
                    "CATEGORY_BACKGROUND_COLOR": "#c37225",
                    "COMPANY_TITLE_COLOR": "#000000",
                    "PRODUCTS_BACKGROUND_COLOR": "#e6dbc6",
                    "TABLE_COMPANY_NAME_COLOR": "#c37225",
                    "TABLE_ITEM_NAME_COLOR": "#c37225",
                    "TABLE_ITEM_PRICE_COLOR": "#117703",
                    "TABLE_ITEM_SIZE_COLOR": "#c37225",
                    "TABLE_ITEM_NEWS_COLOR": "#c37225",
                    "TABLE_BACKGROUND_COLOR": "#ffffff",
                    "TABLE_BORDER_COLOR": "#c37225",
                    "BODY_BACKGROUND_COLOR": "#e6dbc6",
                    "PARAGRAPH_TITLE1_COLOR": "#c37225",
                    "PARAGRAPH_TITLE2_COLOR": "#000000",
                    "PARAGRAPH_COLOR": "#000000"
                    }

path_dictionary = {
    # FIX (revisione batch A, punto 4): questo path e' usato solo in SCRITTURA
    # (build_PDF.py ci scrive il PDF generato), quindi deve passare per
    # writable_path() come TMP_SYSTEM_FOLDER_PATH sotto - resource_path() risolve
    # in una build PyInstaller a una cartella temporanea (onefile, cancellata
    # all'uscita) o non scrivibile (onedir/macOS .app), facendo perdere il PDF appena creato.
    "OUTPUT_PDF_FOLDER_PATH": Path(writable_path("output/")),
    "PRODUCTS_IMAGES_FOLDER_PATH": Path(resource_path("img_products/")),
    "GENERAL_IMAGES_FOLDER_PATH":Path(resource_path("img_general/")),
    "TMP_SYSTEM_FOLDER_PATH": Path(writable_path("tmp/"))
}

flags_dictionary = {
    "BREAK_PAGE_COMPANY": False,
    "ADD_PRODUCT_DESCRIPTION": True,
    "GENERATE_RANDOM_PRODUCTS_IMAGE": False,
    "HIDE_PRICES": False,
    "FULL_PAGE_CATEGORY": True
}

# Snapshot dei valori predefiniti, catturato PRIMA che load_config() sovrascriva
# i dizionari: usato dai pulsanti "Ripristina" della UI.
COLOR_DEFAULTS = dict(colors_dictionary)
FLAG_DEFAULTS = dict(flags_dictionary)

def load_config():
    global excel_file, txt_intro_file, title, subtitle, footer, language

    # La lingua va risolta subito: cosi' anche il config.json creato al primo
    # avvio (ramo "file non trovato" qui sotto) contiene gia' un valore valido.
    if language is None:
        language = i18n.detect_default()
    i18n.set_language(language)

    if not os.path.exists(CONFIG_FILE):
        logger.warning("JSON Config file not found. Creating new file...")
        save_config()
        return

    
    with open(CONFIG_FILE, 'r') as f:
        logger.info(CONFIG_FILE + " founded. Loading config...")
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("JSON Config file error (READ): %s. Keeping default values.", e, exc_info=True)
            return

    # Ogni chiave viene applicata singolarmente: se manca o non e' valida nel file JSON
    # (es. dopo un aggiornamento che ha introdotto nuove chiavi) si mantiene il default
    # in memoria invece di bloccare l'avvio dell'intera applicazione.
    # Se il path salvato non esiste piu' (es. build "onefile" macOS che estrae il bundle
    # in una dir temporanea diversa a ogni avvio) si torna al default attuale.
    candidate = config.get("excel_file", excel_file)
    if os.path.exists(candidate):
        excel_file = candidate
    else:
        logger.warning("excel_file saved path not found (%s). Keeping default value.", candidate)

    candidate = config.get("txt_intro_file", txt_intro_file)
    if os.path.exists(candidate):
        txt_intro_file = candidate
    else:
        logger.warning("txt_intro_file saved path not found (%s). Keeping default value.", candidate)

    title           = config.get("title", title)
    subtitle        = config.get("subtitle", subtitle)
    footer          = config.get("footer", footer)

    language        = config.get("language", language)
    i18n.set_language(language)

    for k in flags_dictionary:
        if k in config:
            flags_dictionary[k] = _parse_bool(config[k])
        else:
            logger.warning("%s missing in JSON config file. Keeping default value.", k)

    for k in colors_dictionary:
        if k in config:
            colors_dictionary[k] = config[k]
        else:
            logger.warning("%s missing in JSON config file. Keeping default value.", k)

    for k in path_dictionary:
        if k not in config:
            logger.warning("%s missing in JSON config file. Keeping default value.", k)
            continue
        try:
            candidate = Path(config[k])
        except TypeError as e:
            logger.warning("%s invalid in JSON config file (%s). Keeping default value.", k, e)
            continue
        # Se il path salvato non esiste piu' (vedi nota su excel_file) si tiene il default.
        if not candidate.exists():
            logger.warning("%s saved path not found (%s). Keeping default value.", k, candidate)
            continue
        path_dictionary[k] = candidate

    logger.info("language -> %s",       language)
    logger.info("excel_file -> %s",     excel_file)
    logger.info("txt_intro_file -> %s", txt_intro_file)
    logger.info("title -> %s",          title)
    logger.info("subtitle -> %s",       subtitle)
    logger.info("footer -> %s",         footer)
    for k, v in flags_dictionary.items():
        logger.info("%s -> %s", k, v)
    for k, v in colors_dictionary.items():
        logger.info("%s -> %s", k, v)
    for k, v in path_dictionary.items():
        logger.info("%s -> %s", k, str(v))


def save_config():
    """Ritorna True se il salvataggio e' andato a buon fine, False altrimenti."""
    try:
        logger.info("JSON Config file saving...")
        config = {
            "language":   language,
            "excel_file": excel_file,
            "txt_intro_file": txt_intro_file,
            "title":      title,
            "subtitle":   subtitle,
            "footer":     footer,
        }
        # colori
        for k, v in colors_dictionary.items():
            config[f"{k}"] = v
            logger.info("%s -> %s", k, str(v))
        #paths
        for k, v in path_dictionary.items():
            config[f"{k}"] = str(v)
            logger.info("%s -> %s", k, str(v))
        #flags
        for k, v in flags_dictionary.items():
            config[k] = v
            logger.info("%s -> %s", k, str(v))

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except (TypeError, ValueError, OSError) as e:
        logger.error("JSON Config file error (SAVE): %s", e, exc_info=True)
        return False

def _parse_bool(v):
    if isinstance(v, bool):
        return v          # già bool nativo JSON → ok
    if isinstance(v, str):
        return v.strip().lower() == "true"   # gestisce "True", "False", "true", "false"
    return bool(v)


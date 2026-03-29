# per generare i requirements.txt
# pip freeze > requirements.txt
#
# per installare i requirements:
# pip install -r requirements.txt

import os
import json
import sys
from pathlib import Path
from app.logger import logger

__version__ = "0.5"

# CONFIG_FILE relativo al file corrente, non alla working directory
CONFIG_FILE = "config.json"

# valori di default che poi vengono sovrascritti
# dal file di configurazione JSON
excel_file = f"{os.getcwd()}/example_excel/Product list example.xlsx"
txt_intro_file = f"{os.getcwd()}/txt_intros/intro.txt"
title = "CHANGE THE TITLE" 
subtitle = "Change this subtitle" 
footer = "Change this footer" 

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
    "OUTPUT_PDF_FOLDER_PATH": Path(f"{os.getcwd()}/example_catalog/"),
    "PRODUCTS_IMAGES_FOLDER_PATH": Path(f"{os.getcwd()}/img_products/"),
    "GENERAL_IMAGES_FOLDER_PATH":Path(f"{os.getcwd()}/img_general/"),
    "TMP_SYSTEM_FOLDER_PATH": Path(f"{os.getcwd()}/tmp/")
}

flags_dictionary = {
    "BREAK_PAGE_COMPANY": False,
    "ADD_PRODUCT_DESCRIPTION": True,
    "GENERATE_RANDOM_PRODUCTS_IMAGE": False,
    "HIDE_PRICES": False,
    "FULL_PAGE_CATEGORY": True
}

def load_config():
    global excel_file, txt_intro_file, title, subtitle, footer

    #logger.info("JSON Config file reading...")
    if not os.path.exists(CONFIG_FILE):
        logger.warning("JSON Config file not found. Creating new file...")
        save_config()
        return

    
    with open(CONFIG_FILE, 'r') as f:
        logger.info(CONFIG_FILE + " founded. Loading config...")
        try:
            config = json.load(f)

            # 1. Valida/estrai tutto prima di toccare qualsiasi globale
            new_excel_file            = config["excel_file"]
            new_txt_intro_file        = config["txt_intro_file"]
            new_title                 = config["title"]
            new_subtitle              = config["subtitle"]
            new_footer                = config["footer"]
            new_flags   = {k: _parse_bool(config[k]) for k in flags_dictionary}
            new_colors  = {k: config[k]         for k in colors_dictionary}
            new_paths   = {k: Path(config[k])   for k in path_dictionary}

            # 2. Solo se tutto è andato bene, applica
            excel_file              = new_excel_file
            txt_intro_file          = new_txt_intro_file
            title                   = new_title
            subtitle                = new_subtitle
            footer                  = new_footer
            flags_dictionary.update(new_flags)
            colors_dictionary.update(new_colors)
            path_dictionary.update(new_paths)

            # 3. Logga tutto
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

        except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error("JSON Config file error (READ): %s", e, exc_info=True)
            #config = {}
            sys.exit(1)

        

def save_config():
    try:
        logger.info("JSON Config file saving...")
        config = {
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
            # logger.info(f"{k} -> {v}")
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
    except (KeyError, json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error("JSON Config file error (SAVE): %s", e, exc_info=True)
        sys.exit(1)

def _parse_bool(v):
    if isinstance(v, bool):
        return v          # già bool nativo JSON → ok
    if isinstance(v, str):
        return v.strip().lower() == "true"   # gestisce "True", "False", "true", "false"
    return bool(v)


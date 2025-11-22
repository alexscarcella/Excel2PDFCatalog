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

__version__ = "0.4.1"

# valori di default che poi vengono sovrascritti
# dal file di configurazione JSON
excel_file = f"{os.getcwd()}/example_excel/Product list example.xlsx"
break_page_company = True
generate_random_images = False
title = "CHANGE THE TITLE"
subtitle = "Change this subtitle"
footer = "this is a footer"

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
    "GENERATE_RANDOM_PRODUCTS_IMAGE": False
}

# [Colors defaults]
# COVER_TITLE = #ffffff
# COVER_SUBTITLE = #ffffff
# COVER_BACKGROUND = #c37225
# FOOTER = #000000
# CATEGORY_TITLE = #000000
# CATEGORY_BACKGROUND = #c37225
# COMPANY_TITLE = #000000
# PRODUCTS_BACKGROUND = #e6dbc6
# TABLE_COMPANY_NAME = #c37225
# TABLE_ITEM_NAME = #c37225
# TABLE_ITEM_PRICE = #117703
# TABLE_ITEM_SIZE = #c37225
# TABLE_ITEM_NEWS = #c37225
# TABLE_BACKGROUND = #ffffff
# TABLE_BORDER = #c37225
# BODY_BACKGROUND = #e6dbc6
# PARAGRAPH_TITLE1 = #c37225
# PARAGRAPH_TITLE2 = #000000
# PARAGRAPH = #000000

CONFIG_FILE = 'config.json'

def load_config():
    global excel_file, break_page_company, title, subtitle, footer, generate_random_images

    logger.info("JSON Config file reading...")
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                config = json.load(f)
                #
                excel_file = config["excel_file"]
                break_page_company = config["break_page_company"]
                generate_random_images = config["generate_random_images"]
                title = config["title"]
                subtitle = config["subtitle"]
                footer = config["footer"]
                #
                # colori
                for k, v in colors_dictionary.items():
                    colors_dictionary[k] = config[k]
                    logger.info(f"{v} -> {k}")

                # paths
                for k, v in path_dictionary.items():
                    path_dictionary[k] = Path(config[k])
                    logger.info(f"{str(v)} -> {k}")
            except:
                logger.error("JSON Config file error", exc_info=True)
                config = {}
                sys.exit()
    else:
        config = {}
        logger.info("JSON Config file empty. Creating new file...")
        save_config()
        

def save_config():
    try:
        logger.info("JSON Config file saving...")
        config = {}
        # parametri
        config["excel_file"] = excel_file
        config["break_page_company"] = break_page_company
        config["generate_random_images"] = generate_random_images
        config["title"] = title 
        config["subtitle"] = subtitle 
        config["footer"] = footer
        # colori
        for k, v in colors_dictionary.items():
            config[f"{k}"] = v
            logger.info(f"{k} -> {v}")
        #paths
        for k, v in path_dictionary.items():
            config[f"{k}"] = str(v)
            logger.info(f"{k} -> {str(v)}")

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except:
        logger.error("JSON Config file save error", exc_info=True)
        sys.exit()


import app.config_utils as config_utils
from app.ui_interface import build_UI_and_GO
from app.logger import logger
import sys

if __name__ == "__main__":
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info(f"START App - {config_utils.__version__}")
    

    config_utils.load_config()
    build_UI_and_GO()

    
    
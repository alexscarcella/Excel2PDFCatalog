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
    
    try:
        config_utils.load_config()
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        logger.info("END App")
        sys.exit(1)
    try:
        build_UI_and_GO()
    except Exception as e:
        logger.error(f"Error in UI execution: {e}")
        logger.info("END App")
        sys.exit(1) 
    
    
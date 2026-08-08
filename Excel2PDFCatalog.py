import sys
import traceback

import app.paths_utils as paths_utils


def _write_crash(exc_info):
    # Con la build "windowed" di PyInstaller stdout/stderr non sono visibili:
    # si scrive il traceback su un file per rendere diagnosticabili i crash.
    try:
        with open(paths_utils.writable_path("crash.log"), "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            traceback.print_exception(*exc_info, file=f)
    except Exception:
        pass


def _excepthook(exc_type, exc_value, exc_tb):
    _write_crash((exc_type, exc_value, exc_tb))
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _excepthook

# Marcatore di avvio scritto subito, prima di importare il resto, per capire
# se il processo arriva davvero a eseguire Python (vs. essere bloccato dal sistema).
try:
    with open(paths_utils.writable_path("startup.log"), "a", encoding="utf-8") as f:
        f.write("booting\n")
except Exception:
    pass

import app.config_utils as config_utils
from app.ui_interface import build_UI_and_GO
from app.logger import logger

if __name__ == "__main__":
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info("***************************************************************")
    logger.info(f"START App - {config_utils.__version__}")
    

    config_utils.load_config()
    build_UI_and_GO()

    


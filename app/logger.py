# logger.py
import logging
from logging.handlers import RotatingFileHandler

from app.paths_utils import writable_path

# Configurazione del file di log: path scrivibile, indipendente dalla cwd
# (un .app macOS avviato da Finder/Dock ha come cwd la home dell'utente).
LOG_FILENAME = writable_path("logs/app.log")
MAX_LOG_SIZE = 1_000_000  # 1 MB
BACKUP_COUNT = 5          # Numero massimo di file di backup

# Formatter comune
formatter = logging.Formatter(
    "%(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
)

# Handler per il file con rotazione automatica
file_handler = RotatingFileHandler(
    LOG_FILENAME, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Handler per la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Logger condiviso
logger = logging.getLogger("AppLogger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Evita duplicazione dei log se il modulo viene importato più volte
logger.propagate = False

import os
import sys


def is_frozen():
    """True se l'app e' eseguita da un pacchetto PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def resource_path(rel_path):
    """Risolvi il path di una risorsa di sola lettura bundlata (config, fonts,
    cartelle di esempio, ...). Quando si esegue da sorgente coincide con cwd;
    con PyInstaller punta alla directory di estrazione del bundle (_MEIPASS)."""
    if is_frozen():
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    else:
        base = os.getcwd()
    return os.path.join(base, rel_path)


def user_data_dir():
    """Directory scrivibile per i file di runtime (config.json, logs, tmp).

    Su macOS con app bundlata usa ~/Library/Application Support/Excel2PDFCatalog,
    cosi' l'app non dipende dalla directory da cui viene lanciata (un .app avviato
    da Finder/Dock ha come cwd la home dell'utente). Negli altri casi (Windows,
    sviluppo da sorgente) usa la working directory, mantenendo il comportamento
    storico."""
    if is_frozen() and sys.platform == "darwin":
        base = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            "Excel2PDFCatalog",
        )
        os.makedirs(base, exist_ok=True)
        return base
    return os.getcwd()


def writable_path(rel_path):
    """Path completo (con creazione automatica della directory padre) per un
    file di runtime scrivibile (config.json, logs, tmp)."""
    path = os.path.join(user_data_dir(), rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

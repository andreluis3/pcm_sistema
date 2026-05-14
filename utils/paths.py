from pathlib import Path
import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Caminho para assets no PyInstaller
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# =========================
# PASTA DO APP
# =========================

APP_DIR = Path.home() / "PCM_System"

APP_DIR.mkdir(exist_ok=True)

# =========================
# BANCO SQLITE
# =========================

DB_PATH = APP_DIR / "pcmdata.db"
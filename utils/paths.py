from pathlib import Path
import sys


def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS

    except Exception:
        base_path = Path(".").absolute()

    return Path(base_path) / relative_path


BASE_DIR = Path(__file__).resolve().parent.parent

APP_DIR = BASE_DIR

DB_PATH = BASE_DIR / "database" / "pcmdata.db"
from pathlib import Path
import sys

#versao para criar o exe

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS

    except Exception:
        base_path = Path(".").absolute()

    return Path(base_path) / relative_path


APP_DIR = Path.home() / "PCM_System"

APP_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DB_PATH = APP_DIR / "pcmdata.db"
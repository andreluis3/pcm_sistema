from __future__ import annotations

import json
from utils.paths import APP_DIR


SESSION_DIR = APP_DIR / "data"
SESSION_FILE = SESSION_DIR / "user_session.json"


def save_user(nome: str) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    with SESSION_FILE.open("w", encoding="utf-8") as file:
        json.dump({"usuario": nome}, file, ensure_ascii=False, indent=4)


def load_user() -> str | None:

    if not SESSION_FILE.exists():
        return None

    try:

        with SESSION_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except (json.JSONDecodeError, OSError):

        clear_user()
        return None

    nome = data.get("usuario")

    if isinstance(nome, str) and nome.strip():
        return nome.strip()

    clear_user()
    return None


def clear_user() -> None:

    try:

        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

    except OSError:

        try:

            SESSION_DIR.mkdir(parents=True, exist_ok=True)

            with SESSION_FILE.open("w", encoding="utf-8") as file:
                json.dump({}, file)

        except OSError:
            pass
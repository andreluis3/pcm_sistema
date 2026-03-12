import sqlite3
from pathlib import Path
from typing import List, Tuple


class PCMData:
    def __init__(self, db_path: str | Path = "pcmdata.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS temperatures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cycles (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute("INSERT OR IGNORE INTO cycles (id, count) VALUES (1, 0)")

    def insert_temperature(self, value: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO temperatures (value) VALUES (?)", (value,))

    def get_last_temperatures(self, limit: int = 50) -> List[Tuple[float, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT value, created_at
                FROM temperatures
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return rows[::-1]

    def increment_cycle(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE cycles SET count = count + 1 WHERE id = 1")
            row = conn.execute("SELECT count FROM cycles WHERE id = 1").fetchone()
        return int(row[0]) if row else 0

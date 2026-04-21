from __future__ import annotations

import sqlite3
from pathlib import Path

from .pcm_model import PCMResult


class PCMRepository:
    def __init__(self, db_path: str | Path = "pcm_data.db") -> None:
        self.db_path = Path(db_path)
        self.init_db()

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pcm_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    energia REAL NOT NULL,
                    potencia_media REAL NOT NULL,
                    massa_pcm REAL NOT NULL,
                    pico_potencia REAL NOT NULL,
                    pico_temperatura REAL NOT NULL
                )
                """
            )

    def save(self, result: PCMResult) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO pcm_logs (
                    data,
                    energia,
                    potencia_media,
                    massa_pcm,
                    pico_potencia,
                    pico_temperatura
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.data_execucao,
                    result.energia_total,
                    result.potencia_media,
                    result.massa_pcm,
                    result.pico_potencia,
                    result.pico_temperatura,
                ),
            )

    def get_last_results(self, limit: int = 10) -> list[PCMResult]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    data,
                    energia,
                    potencia_media,
                    massa_pcm,
                    pico_potencia,
                    pico_temperatura
                FROM pcm_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            PCMResult(
                energia_total=float(row[1]),
                tempo_total=0.0,
                potencia_media=float(row[2]),
                massa_pcm=float(row[3]),
                pico_potencia=float(row[4]),
                pico_temperatura=float(row[5]),
                data_execucao=str(row[0]),
            )
            for row in rows
        ]

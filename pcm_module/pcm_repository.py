from __future__ import annotations

import sqlite3
from pathlib import Path
from utils.paths import DB_PATH
from .pcm_model import PCMResult


class PCMRepository:
    def __init__(self, db_path: str | Path = DB_PATH):
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
                    tempo_total REAL NOT NULL DEFAULT 0,
                    potencia_media REAL NOT NULL,
                    massa_pcm REAL NOT NULL,
                    pico_potencia REAL NOT NULL,
                    pico_temperatura REAL NOT NULL,
                    status_termico TEXT NOT NULL DEFAULT 'indefinido'
                )
                """
            )
            self._ensure_column(conn, "tempo_total", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(conn, "status_termico", "TEXT NOT NULL DEFAULT 'indefinido'")

    def _ensure_column(self, conn: sqlite3.Connection, column_name: str, column_definition: str) -> None:
        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(pcm_logs)").fetchall()
        }
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE pcm_logs ADD COLUMN {column_name} {column_definition}")

    def save(self, result: PCMResult) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO pcm_logs (
                    data,
                    energia,
                    tempo_total,
                    potencia_media,
                    massa_pcm,
                    pico_potencia,
                    pico_temperatura,
                    status_termico
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.data_execucao,
                    result.energia_total,
                    result.tempo_total,
                    result.potencia_media,
                    result.massa_pcm,
                    result.pico_potencia,
                    result.pico_temperatura,
                    result.status_termico,
                ),
            )

    def get_last_results(self, limit: int = 10) -> list[PCMResult]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    data,
                    energia,
                    tempo_total,
                    potencia_media,
                    massa_pcm,
                    pico_potencia,
                    pico_temperatura,
                    status_termico
                FROM pcm_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            PCMResult(
                energia_total=float(row[1]),
                tempo_total=float(row[2]),
                potencia_media=float(row[3]),
                massa_pcm=float(row[4]),
                pico_potencia=float(row[5]),
                pico_temperatura=float(row[6]),
                data_execucao=str(row[0]),
                delta_tempo=float(row[2]),
                status_termico=str(row[7]),
            )
            for row in rows
        ]

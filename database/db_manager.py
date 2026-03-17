import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "pcmdata.db"


class DatabaseManager:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )
        """)


        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            start_time DATETIME,
            end_time DATETIME,
            delta_time REAL,

            initial_temperature REAL,
            fusion_temperature REAL,
            delta_temperature REAL,

            massa REAL,
            capsula TEXT,
            data_de_experimento DATE,
            operador TEXT,
            calor_latente REAL,
            calor_sensivel REAL,
            energia_armazenada REAL,
            eficiencia REAL
        """);

self.conn.commit()

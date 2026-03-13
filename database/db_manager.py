import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "pcmdata.db"


class DatabaseManager:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS temperature_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME,
            end_time DATETIME,
            max_temp REAL,
            min_temp REAL
        )
        """)

        self.conn.commit()

    def insert_temperature(self, temp):

        self.cursor.execute("""
        INSERT INTO temperature_data (temperature)
        VALUES (?)
        """, (temp,))

        self.conn.commit()

    def get_last_temperatures(self, limit=100):

        self.cursor.execute("""
        SELECT temperature FROM temperature_data
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))

        return [row[0] for row in self.cursor.fetchall()]
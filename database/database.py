import sqlite3

DB_PATH = "database/pcmdata.db"

def connect():
    return sqlite3.connect(DB_PATH)


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        melting_point REAL,
        latent_heat REAL,
        expected_efficiency REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        start_temp REAL,
        end_temp REAL,
        cycle_number INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(material_id) REFERENCES materials(id)
    )
    """)

    conn.commit()
    conn.close()
import sqlite3

conn = sqlite3.connect("pcm_data.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM experiments")
print(cursor.fetchone())
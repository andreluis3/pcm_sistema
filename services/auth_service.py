import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "pcmdata.db"


class AuthService:

    def hash_password(self, password):

        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):

        password_hash = self.hash_password(password)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            """, (username, password_hash))

            conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False

        finally:
            conn.close()

    def login(self, username, password):

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT password_hash FROM users WHERE username=?
        """, (username,))

        result = cursor.fetchone()

        conn.close()

        if not result:
            return False

        password_hash = self.hash_password(password)

        return password_hash == result[0]
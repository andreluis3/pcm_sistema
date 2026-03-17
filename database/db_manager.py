import sqlite3
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path(__file__).parent / "pcmdata.db"


EXPECTED_EXPERIMENT_COLUMNS: tuple[str, ...] = (
    "id",
    "date",
    "material",
    "tempo_inicio",
    "end_time",
    "delta_time",
    "temperatura_inicial",
    "temperatura_final",
    "delta_temperatura",
    "massa",
    "capsula",
    "operador",
    "calor_latente",
    "calor_sensivel",
    "energia_armazenada",
    "eficiencia",
)


class DatabaseManager:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.create_tables()

    def close(self) -> None:
        self.conn.close()

    def create_tables(self) -> None:
        self._ensure_users_table()
        self._ensure_experiments_table()

    def _ensure_users_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def _ensure_experiments_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                material TEXT,
                tempo_inicio DATETIME,
                end_time DATETIME,
                delta_time REAL,
                temperatura_inicial REAL,
                temperatura_final REAL,
                delta_temperatura REAL,
                massa REAL,
                capsula TEXT,
                operador TEXT,
                calor_latente REAL,
                calor_sensivel REAL,
                energia_armazenada REAL,
                eficiencia REAL
            )
            """
        )
        self.conn.commit()
        self._migrate_experiments_if_needed()

    def _get_table_columns(self, table: str) -> list[str]:
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        return [r["name"] for r in rows]

    def _migrate_experiments_if_needed(self) -> None:
        try:
            existing = self._get_table_columns("experiments")
        except sqlite3.OperationalError:
            return

        if set(EXPECTED_EXPERIMENT_COLUMNS).issubset(set(existing)):
            return

        # Best-effort migration for early schemas used in this repo.
        mapping = {
            "id": "id",
            "start_time": "tempo_inicio",
            "end_time": "end_time",
            "delta_time": "delta_time",
            "initial_temperature": "temperatura_inicial",
            "fusion_temperature": "temperatura_final",
            "delta_temperature": "delta_temperatura",
            "massa": "massa",
            "capsula": "capsula",
            "operador": "operador",
            "calor_latente": "calor_latente",
            "calor_sensivel": "calor_sensivel",
            "energia_armazenada": "energia_armazenada",
            "eficiencia": "eficiencia",
            "data_de_experimento": "date",
            "date": "date",
            "material": "material",
        }

        common_src = [c for c in existing if c in mapping]
        if not common_src:
            return

        dst_cols = [mapping[c] for c in common_src]
        src_cols_sql = ", ".join(common_src)
        dst_cols_sql = ", ".join(dst_cols)

        with self.conn:
            self.conn.execute(
                """
                ALTER TABLE experiments RENAME TO experiments_old
                """
            )
            self.conn.execute(
                """
                CREATE TABLE experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    material TEXT,
                    tempo_inicio DATETIME,
                    end_time DATETIME,
                    delta_time REAL,
                    temperatura_inicial REAL,
                    temperatura_final REAL,
                    delta_temperatura REAL,
                    massa REAL,
                    capsula TEXT,
                    operador TEXT,
                    calor_latente REAL,
                    calor_sensivel REAL,
                    energia_armazenada REAL,
                    eficiencia REAL
                )
                """
            )

            self.conn.execute(
                f"""
                INSERT INTO experiments ({dst_cols_sql})
                SELECT {src_cols_sql} FROM experiments_old
                """
            )
            self.conn.execute("DROP TABLE experiments_old")

    def insert_experiment(self, data: dict[str, Any]) -> int:
        keys = [k for k in data.keys() if k in EXPECTED_EXPERIMENT_COLUMNS and k not in {"id", "date"}]
        if not keys:
            raise ValueError("Nenhum campo válido para inserir em experiments.")

        cols_sql = ", ".join(keys)
        placeholders = ", ".join([f":{k}" for k in keys])
        sql = f"INSERT INTO experiments ({cols_sql}) VALUES ({placeholders})"

        with self.conn:
            cur = self.conn.execute(sql, {k: data.get(k) for k in keys})
            return int(cur.lastrowid)

    def update_experiment(self, experiment_id: int, data: dict[str, Any]) -> None:
        keys = [k for k in data.keys() if k in EXPECTED_EXPERIMENT_COLUMNS and k not in {"id"}]
        if not keys:
            return

        set_sql = ", ".join([f"{k} = :{k}" for k in keys])
        sql = f"UPDATE experiments SET {set_sql} WHERE id = :id"
        params = {k: data.get(k) for k in keys}
        params["id"] = experiment_id

        with self.conn:
            self.conn.execute(sql, params)

    def delete_experiment(self, experiment_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))

    def get_experiment_by_id(self, experiment_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()

    def list_experiments(self, limit: int | None = None) -> list[sqlite3.Row]:
        sql = """
            SELECT * FROM experiments
            ORDER BY datetime(date) DESC, id DESC
        """
        params: Iterable[Any] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        return list(self.conn.execute(sql, params).fetchall())

    def search_experiments(self, material: str | None = None, date: str | None = None) -> list[sqlite3.Row]:
        where: list[str] = []
        params: list[Any] = []

        if material:
            where.append("material LIKE ?")
            params.append(f"%{material}%")

        if date:
            # Accept YYYY-MM-DD; compare only the date part.
            where.append("date(date) = date(?)")
            params.append(date)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        sql = f"""
            SELECT * FROM experiments
            {where_sql}
            ORDER BY datetime(date) DESC, id DESC
        """
        return list(self.conn.execute(sql, params).fetchall())

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from utils.paths import DB_PATH
from utils.paths import DB_PATH

print("DB_MANAGER IMPORTADO")
print(DB_PATH.exists())
print(DB_PATH)
EXPECTED_EXPERIMENT_COLUMNS: tuple[str, ...] = (
    "id",
    "date_created",
    "material",
    "operador",
    "capsula",
    "massa",
    "calor_especifico",
    "tempo_inicio",
    "tempo_final",
    "delta_tempo",
    "temperatura_inicial",
    "temperatura_final",
    "delta_temperatura",
)

EXPECTED_THERMAL_CALC_COLUMNS: tuple[str, ...] = (
    "id",
    "experiment_id",
    "calculation_type",
    "calor_latente",
    "calor_sensivel",
    "energia_armazenada",
    "densidade_energetica",
    "eficiencia",
    "date_created",
)


class DatabaseManager:

    def __init__(self, db_path: Path | str | None = None) -> None:

        self.db_path = Path(db_path) if db_path else Path(DB_PATH)

        # garante pasta
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[DB] Banco SQLite usado:")
        print(f"[DB] {self.db_path}\n")

        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30
        )

        self.conn.row_factory = sqlite3.Row

        # estabilidade sqlite
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA temp_store = MEMORY")
        self.conn.execute("PRAGMA cache_size = -64000")

        self.create_tables()
        print("[DB CHECK] Experiments:", self.conn.execute(
            "SELECT COUNT(*) FROM experiments"
        ).fetchone()[0])

    # =========================================================
    # CONNECTION
    # =========================================================

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    # =========================================================
    # TABLES
    # =========================================================

    def create_tables(self) -> None:
        self._ensure_users_table()
        self._ensure_experiments_table()
        self._ensure_thermal_calculations_table()
        self._ensure_tabela_calculos_table()

    def _ensure_users_table(self) -> None:

        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _ensure_experiments_table(self) -> None:

        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                    material TEXT,
                    operador TEXT,
                    capsula TEXT,
                    massa REAL,
                    calor_especifico REAL DEFAULT 2.0,
                    tempo_inicio TEXT,
                    tempo_final TEXT,
                    delta_tempo REAL,
                    temperatura_inicial REAL,
                    temperatura_final REAL,
                    delta_temperatura REAL
                )
            """)

        self._migrate_experiments_if_needed()
        self._ensure_experiments_calor_especifico_fixed()

    def _ensure_thermal_calculations_table(self) -> None:

        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS thermal_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id INTEGER,
                    calculation_type TEXT,
                    calor_latente REAL,
                    calor_sensivel REAL,
                    energia_armazenada REAL,
                    densidade_energetica REAL,
                    eficiencia REAL,
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (experiment_id)
                    REFERENCES experiments(id)
                    ON DELETE SET NULL
                )
            """)

    def _ensure_tabela_calculos_table(self) -> None:

        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tabela_calculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experimento_id INTEGER,
                    massa REAL,
                    calor_especifico REAL,
                    delta_t REAL,
                    resultado REAL,
                    tipo_calculo TEXT,
                    data_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (experimento_id)
                    REFERENCES experiments(id)
                    ON DELETE CASCADE
                )
            """)

        self._normalize_tabela_calculos_calor_especifico_fixed()

    # =========================================================
    # MIGRATIONS
    # =========================================================

    def _get_table_columns(self, table: str) -> list[str]:

        rows = self.conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()

        return [r["name"] for r in rows]

    def _migrate_experiments_if_needed(self) -> None:

        try:
            existing = self._get_table_columns("experiments")
        except sqlite3.OperationalError:
            return

        expected = set(EXPECTED_EXPERIMENT_COLUMNS)
        missing = expected - set(existing)

        if not missing:
            return

        print(f"[DB] Migração necessária experiments: {missing}")

        if missing == {"calor_especifico"}:

            with self.conn:
                self.conn.execute("""
                    ALTER TABLE experiments
                    ADD COLUMN calor_especifico REAL DEFAULT 2.0
                """)

                self.conn.execute("""
                    UPDATE experiments
                    SET calor_especifico = 2.0
                """)

            return

    def _ensure_experiments_calor_especifico_fixed(self) -> None:

        try:
            cols = self._get_table_columns("experiments")
        except sqlite3.OperationalError:
            return

        with self.conn:

            if "calor_especifico" not in cols:

                self.conn.execute("""
                    ALTER TABLE experiments
                    ADD COLUMN calor_especifico REAL DEFAULT 2.0
                """)

            self.conn.execute("""
                UPDATE experiments
                SET calor_especifico = 2.0
            """)

    def _normalize_tabela_calculos_calor_especifico_fixed(self) -> None:

        try:
            cols = self._get_table_columns("tabela_calculos")
        except sqlite3.OperationalError:
            return

        if "calor_especifico" not in cols:
            return

        with self.conn:
            self.conn.execute("""
                UPDATE tabela_calculos
                SET calor_especifico = 2.0
            """)

    # =========================================================
    # EXPERIMENTS CRUD
    # =========================================================

    def insert_experiment(self, data: dict[str, Any]) -> int:

        data = dict(data)
        data["calor_especifico"] = 2.0

        keys = [
            k for k in data.keys()
            if k in EXPECTED_EXPERIMENT_COLUMNS
            and k not in {"id", "date_created"}
        ]

        if not keys:
            raise ValueError("Nenhum campo válido.")

        cols_sql = ", ".join(keys)
        placeholders = ", ".join([f":{k}" for k in keys])

        sql = f"""
            INSERT INTO experiments ({cols_sql})
            VALUES ({placeholders})
        """

        with self.conn:

            cur = self.conn.execute(
                sql,
                {k: data.get(k) for k in keys}
            )

            return int(cur.lastrowid)

    def update_experiment(
        self,
        experiment_id: int,
        data: dict[str, Any]
    ) -> None:

        data = dict(data)
        data["calor_especifico"] = 2.0

        keys = [
            k for k in data.keys()
            if k in EXPECTED_EXPERIMENT_COLUMNS
            and k != "id"
        ]

        if not keys:
            return

        set_sql = ", ".join([f"{k} = :{k}" for k in keys])

        sql = f"""
            UPDATE experiments
            SET {set_sql}
            WHERE id = :id
        """

        params = {
            k: data.get(k)
            for k in keys
        }

        params["id"] = experiment_id

        with self.conn:
            self.conn.execute(sql, params)

    def delete_experiment(self, experiment_id: int) -> None:

        with self.conn:
            self.conn.execute(
                "DELETE FROM experiments WHERE id = ?",
                (experiment_id,)
            )

    def get_experiment_by_id(
        self,
        experiment_id: int
    ) -> sqlite3.Row | None:

        return self.conn.execute(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,)
        ).fetchone()

    def list_experiments(
        self,
        limit: int | None = None
    ) -> list[sqlite3.Row]:

        sql = """
            SELECT *
            FROM experiments
            ORDER BY datetime(date_created) DESC, id DESC
        """

        params: Iterable[Any] = ()

        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        return list(
            self.conn.execute(sql, params).fetchall()
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def search_experiments_flexible(
        self,
        query: str
    ) -> list[sqlite3.Row]:

        q = (query or "").strip()

        if not q:
            return self.list_experiments()

        like = f"%{q}%"

        sql = """
            SELECT *
            FROM experiments
            WHERE
                operador LIKE ?
                OR material LIKE ?
                OR capsula LIKE ?
                OR CAST(id AS TEXT) LIKE ?
            ORDER BY datetime(date_created) DESC, id DESC
        """

        params = (
            like,
            like,
            like,
            like
        )

        return list(
            self.conn.execute(sql, params).fetchall()
        )

    # =========================================================
    # THERMAL CALCULATIONS
    # =========================================================

    def insert_thermal_calculation(
        self,
        data: dict[str, Any]
    ) -> int:

        keys = [
            k for k in data.keys()
            if k in EXPECTED_THERMAL_CALC_COLUMNS
            and k not in {"id", "date_created"}
        ]

        if not keys:
            raise ValueError("Nenhum campo válido.")

        cols_sql = ", ".join(keys)

        placeholders = ", ".join([
            f":{k}" for k in keys
        ])

        sql = f"""
            INSERT INTO thermal_calculations
            ({cols_sql})
            VALUES ({placeholders})
        """

        with self.conn:

            cur = self.conn.execute(
                sql,
                {k: data.get(k) for k in keys}
            )

            return int(cur.lastrowid)

    def list_thermal_calculations(
        self,
        limit: int | None = None
    ) -> list[sqlite3.Row]:

        sql = """
            SELECT *
            FROM thermal_calculations
            ORDER BY datetime(date_created) DESC, id DESC
        """

        params: Iterable[Any] = ()

        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        return list(
            self.conn.execute(sql, params).fetchall()
        )

    def delete_thermal_calculation(
        self,
        calculo_id: int
    ) -> bool:

        with self.conn:

            self.conn.execute(
                """
                DELETE FROM thermal_calculations
                WHERE id = ?
                """,
                (calculo_id,)
            )

        return True

    # =========================================================
    # DASHBOARD HELPERS
    # =========================================================

    def get_delta_t(self, experimento_id: int):

        row = self.get_experiment_by_id(experimento_id)

        if row is None:
            return None

        return row["delta_temperatura"]

    def get_temperatura_media(
        self,
        experimento_id: int
    ):

        row = self.get_experiment_by_id(experimento_id)

        if row is None:
            return None

        t_ini = row["temperatura_inicial"]
        t_fin = row["temperatura_final"]

        if t_ini is None or t_fin is None:
            return None

        return (
            float(t_ini) + float(t_fin)
        ) / 2.0

    def get_heating_rate(
        self,
        experimento_id: int
    ):

        row = self.get_experiment_by_id(experimento_id)

        if row is None:
            return None

        delta_temp = row["delta_temperatura"]
        delta_time = row["delta_tempo"]

        if delta_temp is None:
            return None

        if delta_time in (None, 0):
            return None

        return float(delta_temp) / float(delta_time)

    def get_energia_armazenada(
        self,
        experimento_id: int
    ):

        row = self.get_experiment_by_id(experimento_id)

        if row is None:
            return None

        massa = row["massa"]
        delta_t = row["delta_temperatura"]

        if massa is None or delta_t is None:
            return None

        return float(massa) * 2.0 * float(delta_t)
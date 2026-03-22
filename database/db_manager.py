import sqlite3
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path(__file__).parent / "pcmdata.db"


EXPECTED_EXPERIMENT_COLUMNS: tuple[str, ...] = (
    "id",
    "date_created",
    "material",
    "operador",
    "capsula",
    "massa",
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
        self._ensure_thermal_calculations_table()
        self._ensure_tabela_calculos_table()

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
                date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                material TEXT,
                operador TEXT,
                capsula TEXT,
                massa REAL,
                tempo_inicio TEXT,
                tempo_final TEXT,
                delta_tempo REAL,
                temperatura_inicial REAL,
                temperatura_final REAL,
                delta_temperatura REAL
            )
            """
        )
        self.conn.commit()
        self._migrate_experiments_if_needed()

    def _ensure_thermal_calculations_table(self) -> None:
        self.conn.execute(
            """
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
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE SET NULL
            )
            """
        )
        self.conn.commit()

    def _ensure_tabela_calculos_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tabela_calculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experimento_id INTEGER,
                massa REAL,
                calor_especifico REAL,
                delta_t REAL,
                resultado REAL,
                tipo_calculo TEXT,
                data_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experimento_id) REFERENCES experiments(id) ON DELETE CASCADE
            )
            """
        )
        self.conn.commit()

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
            "tempo_inicio": "tempo_inicio",
            "start_time": "tempo_inicio",
            "tempo_final": "tempo_final",
            "end_time": "tempo_final",
            "delta_tempo": "delta_tempo",
            "delta_time": "delta_tempo",
            "temperatura_inicial": "temperatura_inicial",
            "initial_temperature": "temperatura_inicial",
            "temperatura_final": "temperatura_final",
            "fusion_temperature": "temperatura_final",
            "delta_temperatura": "delta_temperatura",
            "delta_temperature": "delta_temperatura",
            "massa": "massa",
            "capsula": "capsula",
            "operador": "operador",
            "data_de_experimento": "date_created",
            "date": "date_created",
            "date_created": "date_created",
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
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                    material TEXT,
                    operador TEXT,
                    capsula TEXT,
                    massa REAL,
                    tempo_inicio TEXT,
                    tempo_final TEXT,
                    delta_tempo REAL,
                    temperatura_inicial REAL,
                    temperatura_final REAL,
                    delta_temperatura REAL
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
        keys = [k for k in data.keys() if k in EXPECTED_EXPERIMENT_COLUMNS and k not in {"id", "date_created"}]
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
            ORDER BY datetime(date_created) DESC, id DESC
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
            where.append("date(date_created) = date(?)")
            params.append(date)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        sql = f"""
            SELECT * FROM experiments
            {where_sql}
            ORDER BY datetime(date_created) DESC, id DESC
        """
        return list(self.conn.execute(sql, params).fetchall())

    def insert_thermal_calculation(self, data: dict[str, Any]) -> int:
        keys = [k for k in data.keys() if k in EXPECTED_THERMAL_CALC_COLUMNS and k not in {"id", "date_created"}]
        if not keys:
            raise ValueError("Nenhum campo válido para inserir em thermal_calculations.")

        cols_sql = ", ".join(keys)
        placeholders = ", ".join([f":{k}" for k in keys])
        sql = f"INSERT INTO thermal_calculations ({cols_sql}) VALUES ({placeholders})"

        with self.conn:
            cur = self.conn.execute(sql, {k: data.get(k) for k in keys})
            return int(cur.lastrowid)

    def list_thermal_calculations(self, limit: int | None = None) -> list[sqlite3.Row]:
        sql = """
            SELECT * FROM thermal_calculations
            ORDER BY datetime(date_created) DESC, id DESC
        """
        params: Iterable[Any] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        return list(self.conn.execute(sql, params).fetchall())

    def upsert_tabela_calculos(self, data: dict[str, Any]) -> int:
        required = {"experimento_id", "tipo_calculo"}
        if not required.issubset(data.keys()):
            raise ValueError("Campos obrigatórios ausentes para tabela_calculos.")

        existing = self.conn.execute(
            """
            SELECT id FROM tabela_calculos
            WHERE experimento_id = ? AND tipo_calculo = ?
            """,
            (data.get("experimento_id"), data.get("tipo_calculo")),
        ).fetchone()

        keys = [
            "experimento_id",
            "massa",
            "calor_especifico",
            "delta_t",
            "resultado",
            "tipo_calculo",
        ]

        if existing:
            set_sql = ", ".join([f"{k} = :{k}" for k in keys])
            sql = f"UPDATE tabela_calculos SET {set_sql} WHERE id = :id"
            params = {k: data.get(k) for k in keys}
            params["id"] = int(existing["id"])
            with self.conn:
                self.conn.execute(sql, params)
            return int(existing["id"])

        cols_sql = ", ".join(keys)
        placeholders = ", ".join([f":{k}" for k in keys])
        sql = f"INSERT INTO tabela_calculos ({cols_sql}) VALUES ({placeholders})"

        with self.conn:
            cur = self.conn.execute(sql, {k: data.get(k) for k in keys})
            return int(cur.lastrowid)

    def get_calculo_by_experimento(self, experimento_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT * FROM tabela_calculos
            WHERE experimento_id = ?
            ORDER BY datetime(data_calculo) DESC, id DESC
            """,
            (experimento_id,),
        ).fetchone()

    def get_calculo_by_experimento_tipo(self, experimento_id: int, tipo_calculo: str) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT * FROM tabela_calculos
            WHERE experimento_id = ? AND tipo_calculo = ?
            ORDER BY datetime(data_calculo) DESC, id DESC
            """,
            (experimento_id, tipo_calculo),
        ).fetchone()

    def list_tabela_calculos(self, limit: int | None = None) -> list[sqlite3.Row]:
        sql = """
            SELECT * FROM tabela_calculos
            ORDER BY datetime(data_calculo) DESC, id DESC
        """
        params: Iterable[Any] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        return list(self.conn.execute(sql, params).fetchall())

    # ---- Dashboard helpers ----------------------------------------------
    def get_delta_t(self, experimento_id: int) -> float | None:
        row = self.get_experiment_by_id(experimento_id)
        if row is None:
            return None
        return row["delta_temperatura"]

    def get_temperatura_media(self, experimento_id: int) -> float | None:
        row = self.get_experiment_by_id(experimento_id)
        if row is None:
            return None
        t_ini = row["temperatura_inicial"]
        t_fin = row["temperatura_final"]
        if t_ini is None or t_fin is None:
            return None
        return (float(t_ini) + float(t_fin)) / 2.0

    def get_heating_rate(self, experimento_id: int) -> float | None:
        row = self.get_experiment_by_id(experimento_id)
        if row is None:
            return None
        delta_temp = row["delta_temperatura"]
        delta_time = row["delta_tempo"]
        if delta_temp is None or delta_time in (None, 0):
            return None
        return float(delta_temp) / float(delta_time)

    def get_energia_armazenada(self, experimento_id: int) -> float | None:
        row = self.get_experiment_by_id(experimento_id)
        if row is None:
            return None
        massa = row["massa"]
        delta_t = row["delta_temperatura"]
        if massa is None or delta_t is None:
            return None
        calc = self.get_calculo_by_experimento_tipo(experimento_id, "Calor Específico")
        calor_especifico = calc["calor_especifico"] if calc else None
        if calor_especifico is None:
            return None
        return float(massa) * float(calor_especifico) * float(delta_t)

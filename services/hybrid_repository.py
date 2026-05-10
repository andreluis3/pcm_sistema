from services.api_client import ThermaCoreMySQLClient
from database.database_manager import DatabaseManager
import os
import traceback


class HybridRepository:

    def __init__(self):

        self.api = ThermaCoreMySQLClient()
        self.sqlite = DatabaseManager()
        self._debug = os.getenv("THERMACORE_HYBRID_DEBUG", "0") in {"1", "true", "True", "yes", "YES"}

    def api_online(self):
        return self.api.health_check()

    def _safe_api_call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[ERRO API] {e}")
            if self._debug:
                print(traceback.format_exc().rstrip())
            return None

    def insert_experiment(self, data):
        print("USANDO HYBRID REPOSITORY")
        # tenta API primeiro
        if self.api_online():

            try:

                experiment_id = self.api.insert_experiment(data)

                if experiment_id:
                    print(f"[API] Experimento salvo no MySQL ID={experiment_id}")
                    return experiment_id

            except Exception as e:
                print(f"[ERRO API] {e}")

        # fallback sqlite
        print("[FALLBACK] Salvando localmente SQLite")
        return self.sqlite.insert_experiment(data)

    def list_experiments(self):

        if self.api_online():

            try:
                return self.api.list_experiments()

            except Exception as e:
                print(f"[ERRO API] {e}")

        return self.sqlite.list_experiments()
    
    def delete_experiment(self, exp_id):

        if self.api_online():

            try:

                return self.api.delete_experiment(exp_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.delete_experiment(exp_id)

    def update_experiment(self, exp_id, data):

        if self.api_online():

            try:

                return self.api.update_experiment(exp_id, data)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.update_experiment(exp_id, data)

    def search_experiments(self, material):

        if self.api_online():

            try:

                return self.api.search_experiments(material)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.search_experiments(material)

    def search_experiments_flexible(self, texto):

        if self.api_online():

            try:

                return self.api.search_experiments_flexible(texto)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.search_experiments_flexible(texto)

    # =========================
    # CÁLCULOS TÉRMICOS
    # =========================

    def insert_thermal_calculation(self, data):
        """
        Salva cálculo térmico preferindo API/MySQL e fazendo fallback SQLite.

        Payload aceito (normalizado):
        - experimento_id (int) ou id_experimento (int)
        - tipo_calculo (str) ou calculation_type (str)
        - resultado (float) opcional
        - delta_t (float) opcional (salvo como delta_temperatura)

        Persistência:
        - API/MySQL: tabela `calculos_termicos`
        - SQLite fallback: tabela `thermal_calculations`
        """
        experimento_id = data.get("id_experimento") or data.get("experimento_id")
        calculation_type = data.get("calculation_type") or data.get("tipo_calculo")
        resultado = data.get("resultado")
        delta_t = data.get("delta_t") or data.get("delta_temperatura")

        # Monta payload API/MySQL
        api_payload = {
            "id_experimento": int(experimento_id) if experimento_id is not None else None,
            "delta_temperatura": float(delta_t) if delta_t is not None else None,
            "calculation_type": str(calculation_type) if calculation_type is not None else None,
        }

        # Mapeia resultado para o campo correto em calculos_termicos
        if resultado is not None:
            if str(calculation_type) == "Calor Sensível":
                api_payload["calor_sensivel"] = float(resultado)
            elif str(calculation_type) == "Calor Latente":
                api_payload["calor_latente"] = float(resultado)
            else:
                # Energia Absorvida (e outros) -> usa energia_armazenada como "resultado"
                api_payload["energia_armazenada"] = float(resultado)

        if self.api_online():
            result = self._safe_api_call(self.api.insert_thermal_calculation, api_payload)
            if result is not None:
                return result

        # Fallback SQLite (thermal_calculations)
        sqlite_payload = {
            "experiment_id": int(experimento_id) if experimento_id is not None else None,
            "calculation_type": str(calculation_type) if calculation_type is not None else None,
            "delta_temperatura": float(delta_t) if delta_t is not None else None,
        }
        if resultado is not None:
            if str(calculation_type) == "Calor Sensível":
                sqlite_payload["calor_sensivel"] = float(resultado)
            elif str(calculation_type) == "Calor Latente":
                sqlite_payload["calor_latente"] = float(resultado)
            else:
                sqlite_payload["energia_armazenada"] = float(resultado)

        return self.sqlite.upsert_thermal_calculation(sqlite_payload)

    def list_thermal_calculations(self):

        if self.api_online():

            try:

                return self.api.list_thermal_calculations()

            except Exception as e:

                print(f"[ERRO API] {e}")

        # SQLite fallback: normaliza chaves para o mesmo shape da API/MySQL.
        rows = []
        for r in self.sqlite.list_thermal_calculations():
            d = dict(r)
            rows.append(
                {
                    "id": d.get("id"),
                    "id_experimento": d.get("experiment_id"),
                    "temperatura_inicial": d.get("temperatura_inicial"),
                    "temperatura_final": d.get("temperatura_final"),
                    "delta_temperatura": d.get("delta_temperatura"),
                    "calor_latente": d.get("calor_latente"),
                    "calor_sensivel": d.get("calor_sensivel"),
                    "energia_armazenada": d.get("energia_armazenada"),
                    "densidade_energetica": d.get("densidade_energetica"),
                    "eficiencia": d.get("eficiencia"),
                    "calculation_type": d.get("calculation_type"),
                    "data_calculo": d.get("date_created"),
                }
            )
        return rows

    def list_tabela_calculos(self):
        """
        Compatibilidade: historicamente a UI listava `tabela_calculos`.

        Agora, retorna um "view model" derivado de `calculos_termicos` (API) / `thermal_calculations` (SQLite),
        com as chaves antigas esperadas pela UI: experimento_id, tipo_calculo, resultado, data_calculo.
        """
        rows: list[dict] = []

        if self.api_online():
            payload = self._safe_api_call(self.api.list_thermal_calculations)
            if isinstance(payload, list):
                for r in payload:
                    if not isinstance(r, dict):
                        continue
                    tipo = r.get("calculation_type")
                    resultado = r.get("calor_sensivel") if tipo == "Calor Sensível" else r.get("calor_latente") if tipo == "Calor Latente" else r.get("energia_armazenada")
                    rows.append(
                        {
                            "id": r.get("id"),
                            "experimento_id": r.get("id_experimento"),
                            "tipo_calculo": tipo,
                            "massa": None,
                            "delta_t": r.get("delta_temperatura"),
                            "resultado": resultado,
                            "data_calculo": r.get("data_calculo"),
                        }
                    )
                return rows

        # SQLite fallback
        for r in self.sqlite.list_thermal_calculations():
            d = dict(r)
            tipo = d.get("calculation_type")
            resultado = d.get("calor_sensivel") if tipo == "Calor Sensível" else d.get("calor_latente") if tipo == "Calor Latente" else d.get("energia_armazenada")
            rows.append(
                {
                    "id": d.get("id"),
                    "experimento_id": d.get("experiment_id"),
                    "tipo_calculo": tipo,
                    "massa": None,
                    "delta_t": None,
                    "resultado": resultado,
                    "data_calculo": d.get("date_created"),
                }
            )
        return rows

    def get_calculo_by_experimento(self, experimento_id):

        if self.api_online():

            try:

                return self.api.get_calculo_by_experimento(experimento_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        row = self.sqlite.get_calculo_by_experimento(experimento_id)
        return dict(row) if row else None

    def get_calculo_by_experimento_tipo(self, experimento_id, tipo_calculo):
        """
        Necessário para Dashboard e ControllerCalculos.

        - Online: tenta API (/api/tabela-calculos/.../tipo/...)
        - Offline/falha: usa SQLite (DatabaseManager.get_calculo_by_experimento_tipo)
        """
        if self.api_online():
            row = self._safe_api_call(self.api.get_thermal_calculation_by_experiment_type, experimento_id, tipo_calculo)
            if isinstance(row, dict):
                tipo = row.get("calculation_type") or tipo_calculo
                resultado = row.get("calor_sensivel") if tipo == "Calor Sensível" else row.get("calor_latente") if tipo == "Calor Latente" else row.get("energia_armazenada")
                return {
                    "id": row.get("id"),
                    "experimento_id": row.get("id_experimento"),
                    "tipo_calculo": tipo,
                    "resultado": resultado,
                    "data_calculo": row.get("data_calculo"),
                }

        # SQLite fallback: procura em thermal_calculations (não usa mais tabela_calculos)
        for r in self.sqlite.list_thermal_calculations():
            d = dict(r)
            if int(d.get("experiment_id") or 0) != int(experimento_id):
                continue
            if str(d.get("calculation_type") or "") != str(tipo_calculo):
                continue
            resultado = d.get("calor_sensivel") if tipo_calculo == "Calor Sensível" else d.get("calor_latente") if tipo_calculo == "Calor Latente" else d.get("energia_armazenada")
            return {
                "id": d.get("id"),
                "experimento_id": d.get("experiment_id"),
                "tipo_calculo": d.get("calculation_type"),
                "resultado": resultado,
                "data_calculo": d.get("date_created"),
            }

        return None

    def upsert_tabela_calculos(self, data):
        """
        Necessário para ControllerCalculos.save_thermal_calculation().

        MIGRADO: tabela_calculos foi descontinuada; agora salva em calculos_termicos/thermal_calculations.
        """
        return self.insert_thermal_calculation(data)

  
    # =========================
    # DASHBOARD HELPERS
    # =========================

    def get_experiment_by_id(self, exp_id):

        if self.api_online():

            try:

                return self.api.get_experiment_by_id(exp_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        row = self.sqlite.get_experiment_by_id(exp_id)
        return dict(row) if row else None

    def get_delta_t(self, experimento_id):

        if self.api_online():

            try:

                return self.api.get_delta_t(experimento_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.get_delta_t(experimento_id)

    def get_temperatura_media(self, experimento_id):

        if self.api_online():

            try:

                return self.api.get_temperatura_media(experimento_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.get_temperatura_media(experimento_id)

    def get_heating_rate(self, experimento_id):

        if self.api_online():

            try:

                return self.api.get_heating_rate(experimento_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.get_heating_rate(experimento_id)

    def get_energia_armazenada(self, experimento_id):

        if self.api_online():

            try:

                return self.api.get_energia_armazenada(experimento_id)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.get_energia_armazenada(experimento_id)
   

    # =========================
    # DASHBOARD
    # =========================

    def get_metricas(self, exp_id):

        if self.api_online():

            try:
                return self.api.get_metricas(exp_id)
            except Exception as e:
                print(f"[API METRICAS ERROR] {e}")

        return {
            "temperatura_media":
                self.sqlite.get_temperatura_media(exp_id),

            "delta_temperatura":
                self.sqlite.get_delta_t(exp_id),

            "heating_rate":
                self.sqlite.get_heating_rate(exp_id),

            "energia_armazenada":
                self.sqlite.get_energia_armazenada(exp_id)
        }
        
    def delete_thermal_calculation(self, calculo_id):
        try:
            return self.api.delete_thermal_calculation(calculo_id)

        except Exception as e:

            print(f"[HybridRepository] API falhou: {e}")

            return self.sqlite.delete_thermal_calculation(calculo_id)
        

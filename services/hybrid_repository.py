from services.api_client import ThermaCoreMySQLClient
from database.database_manager import DatabaseManager


class HybridRepository:

    def __init__(self):

        self.api = ThermaCoreMySQLClient()
        self.sqlite = DatabaseManager()

    def api_online(self):
        return self.api.health_check()

    def _safe_api_call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[ERRO API] {e}")
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

        if self.api_online():

            try:

                return self.api.insert_thermal_calculation(data)

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.insert_thermal_calculation(data)

    def list_thermal_calculations(self):

        if self.api_online():

            try:

                return self.api.list_thermal_calculations()

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.list_thermal_calculations()

    def list_tabela_calculos(self):

        if self.api_online():

            try:

                return self.api.list_tabela_calculos()

            except Exception as e:

                print(f"[ERRO API] {e}")

        return self.sqlite.list_tabela_calculos()

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
            result = self._safe_api_call(self.api.get_calculo_by_experimento_tipo, experimento_id, tipo_calculo)
            if result is not None:
                return result

        row = self.sqlite.get_calculo_by_experimento_tipo(int(experimento_id), str(tipo_calculo))
        return dict(row) if row else None

    def upsert_tabela_calculos(self, data):
        """
        Necessário para ControllerCalculos.save_thermal_calculation().

        Observação: a API atual não possui endpoint de upsert/insert da tabela_calculos,
        então mantemos este fluxo no SQLite como cache/fallback por enquanto.
        """
        return self.sqlite.upsert_tabela_calculos(data)

  
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
        
        

import requests
from typing import List, Dict, Optional

class ThermaCoreMySQLClient:
    def __init__(self, base_url="http://127.0.0.1:8000/api"):
        self.base_url = base_url

    def health_check(self) -> bool:
        """Check if API is available"""
        try:
            response = requests.get(f"{self.base_url}/experimentos", timeout=2)
            return response.status_code == 200
        except:
            return False

    # ==================== EXPERIMENTOS ====================

    def insert_experiment(self, data: Dict) -> int:
        try:

            response = requests.post(
                f"{self.base_url}/experimentos",
                json=data,
                timeout=10
            )

            response.raise_for_status()

            return response.json().get("id")

        except requests.exceptions.RequestException as e:

            print(f"[API ERROR] {e}")

            return None

    def update_experiment(self, exp_id: int, data: Dict):
        try:
            response = requests.put(
                f"{self.base_url}/experimentos/{exp_id}",
                json=data,
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[API UPDATE ERROR] {e}")

    def delete_experiment(self, exp_id: int):
        try:

            response = requests.delete(
                f"{self.base_url}/experimentos/{exp_id}",
                timeout=10
            )

            response.raise_for_status()

            return True

        except requests.exceptions.RequestException as e:

            print(f"[API DELETE ERROR] {e}")

            return False

    def get_experiment_by_id(self, exp_id: int) -> Optional[Dict]:
        try:
            response = requests.get(f"{self.base_url}/experimentos/{exp_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API GET ERROR] {e}")
            return None

    def list_experiments(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/experimentos", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API LIST ERROR] {e}")
            return []

    # ==================== MÉTRICAS ====================

    def get_metricas(self, exp_id: int) -> Optional[Dict]:
        try:
            response = requests.get(f"{self.base_url}/experimentos/{exp_id}/metricas", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API METRICAS ERROR] {e}")
            return None

    # ==================== CÁLCULOS ====================

    def insert_thermal_calculation(self, data: Dict) -> int:
        try:
            response = requests.post(f"{self.base_url}/calculos-termicos", json=data, timeout=10)
            response.raise_for_status()
            return response.json().get("id")
        except requests.exceptions.RequestException as e:
            print(f"[API CALC CREATE ERROR] {e}")
            return None

    def list_thermal_calculations(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/calculos-termicos", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API CALC LIST ERROR] {e}")
            return []

    def list_tabela_calculos(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/tabela-calculos", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API TABELA LIST ERROR] {e}")
            return []

    def get_calculo_by_experimento(self, experimento_id: int) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/tabela-calculos/experimento/{experimento_id}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API TABELA GET ERROR] {e}")
            return None

    def get_calculo_by_experimento_tipo(self, experimento_id: int, tipo_calculo: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/tabela-calculos/experimento/{experimento_id}/tipo/{tipo_calculo}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API TABELA GET TIPO ERROR] {e}")
            return None
    
    def search_experiments(self, material: str) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/experimentos/buscar/por-material",
                params={"material": material},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API SEARCH ERROR] {e}")
            return []

    def search_experiments_flexible(self, texto: str) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/experimentos/buscar/texto-livre",
                params={"q": texto},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[API SEARCH FLEX ERROR] {e}")
            return []
    
    # =========================
    # DASHBOARD HELPERS
    # =========================

    def get_temperatura_media(self, experimento_id):
        exp = self.get_experiment_by_id(experimento_id)

        if not exp:
            return None

        t_ini = exp.get("temperatura_inicial")
        t_fin = exp.get("temperatura_final")

        if t_ini is None or t_fin is None:
            return None

        return (float(t_ini) + float(t_fin)) / 2

    def get_delta_t(self, experimento_id):
        exp = self.get_experiment_by_id(experimento_id)

        if not exp:
            return None

        return exp.get("delta_temperatura")

    def get_heating_rate(self, experimento_id):
        exp = self.get_experiment_by_id(experimento_id)

        if not exp:
            return None

        delta_temp = exp.get("delta_temperatura")
        delta_time = exp.get("delta_tempo")

        if delta_temp is None or not delta_time:
            return None

        return float(delta_temp) / float(delta_time)

    def get_energia_armazenada(self, experimento_id):
        exp = self.get_experiment_by_id(experimento_id)

        if not exp:
            return None

        massa = exp.get("massa")
        delta_t = exp.get("delta_temperatura")

        if massa is None or delta_t is None:
            return None

        return float(massa) * 2.0 * float(delta_t)

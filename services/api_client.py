import requests
import os
import traceback
from typing import List, Dict, Optional

class ThermaCoreMySQLClient:
    def __init__(self, base_url="http://127.0.0.1:8000/api"):
        self.base_url = base_url
        self._debug = os.getenv("THERMACORE_API_DEBUG", "0") in {"1", "true", "True", "yes", "YES"}

    def _log(self, message: str) -> None:
        if self._debug:
            print(message)

    def _request_json(self, method: str, path: str, **kwargs) -> tuple[int | None, object | None]:
        url = f"{self.base_url}{path}"
        try:
            self._log(f"[API] {method} {url} kwargs={{{', '.join(sorted(kwargs.keys()))}}}")
            resp = requests.request(method, url, **kwargs)
            self._log(f"[API] -> {resp.status_code} ({len(resp.content or b'')} bytes)")
            resp.raise_for_status()
            if not resp.content:
                return resp.status_code, None
            return resp.status_code, resp.json()
        except Exception as e:  # noqa: BLE001
            self._log(f"[API] !! {type(e).__name__}: {e}")
            self._log(traceback.format_exc().rstrip())
            return None, None

    def health_check(self) -> bool:
        """Check if API is available"""
        try:
            response = requests.get(f"{self.base_url}/experimentos", timeout=2)
            return response.status_code == 200
        except:
            return False

    # ==================== EXPERIMENTOS ====================

    def insert_experiment(self, data: Dict) -> int:
        status, payload = self._request_json("POST", "/experimentos", json=data, timeout=10)
        if status is None or not isinstance(payload, dict):
            return None
        return payload.get("id")

    def update_experiment(self, exp_id: int, data: Dict):
        self._request_json("PUT", f"/experimentos/{exp_id}", json=data, timeout=10)

    def delete_experiment(self, exp_id: int):
        status, _payload = self._request_json("DELETE", f"/experimentos/{exp_id}", timeout=10)
        return bool(status)

    def get_experiment_by_id(self, exp_id: int) -> Optional[Dict]:
        status, payload = self._request_json("GET", f"/experimentos/{exp_id}", timeout=10)
        if status is None or not isinstance(payload, dict):
            return None
        return payload

    def list_experiments(self) -> List[Dict]:
        status, payload = self._request_json("GET", "/experimentos", timeout=10)
        if status is None or not isinstance(payload, list):
            return []
        return payload

    # ==================== MÉTRICAS ====================

    def get_metricas(self, exp_id: int) -> Optional[Dict]:
        status, payload = self._request_json("GET", f"/experimentos/{exp_id}/metricas", timeout=10)
        if status is None or not isinstance(payload, dict):
            return None
        return payload

    # ==================== CÁLCULOS ====================

    def insert_thermal_calculation(self, data: Dict) -> int:
        status, payload = self._request_json("POST", "/calculos-termicos", json=data, timeout=10)
        if status is None or not isinstance(payload, dict):
            return None
        return payload.get("id")

    def list_thermal_calculations(self) -> List[Dict]:
        status, payload = self._request_json("GET", "/calculos-termicos", timeout=10)
        if status is None or not isinstance(payload, list):
            return []
        return payload

    def list_thermal_calculations_by_experiment(self, experimento_id: int) -> List[Dict]:
        status, payload = self._request_json(
            "GET",
            f"/calculos-termicos/experimento/{experimento_id}",
            timeout=10,
        )
        if status is None or not isinstance(payload, list):
            return []
        return payload

    def get_thermal_calculation_by_experiment_type(self, experimento_id: int, calculation_type: str) -> Optional[Dict]:
        status, payload = self._request_json(
            "GET",
            f"/calculos-termicos/experimento/{experimento_id}/tipo/{calculation_type}",
            timeout=10,
        )
        if status is None or not isinstance(payload, dict):
            return None
        return payload

    def list_tabela_calculos(self) -> List[Dict]:
        status, payload = self._request_json("GET", "/tabela-calculos", timeout=10)
        if status is None or not isinstance(payload, list):
            return []
        return payload

    def get_calculo_by_experimento(self, experimento_id: int) -> Optional[Dict]:
        status, payload = self._request_json("GET", f"/tabela-calculos/experimento/{experimento_id}", timeout=10)
        if status is None or not isinstance(payload, dict):
            return None
        return payload

    def get_calculo_by_experimento_tipo(self, experimento_id: int, tipo_calculo: str) -> Optional[Dict]:
        status, payload = self._request_json(
            "GET",
            f"/tabela-calculos/experimento/{experimento_id}/tipo/{tipo_calculo}",
            timeout=10,
        )
        if status is None or not isinstance(payload, dict):
            return None
        return payload
    
    def search_experiments(self, material: str) -> List[Dict]:
        status, payload = self._request_json(
            "GET",
            "/experimentos/buscar/por-material",
            params={"material": material},
            timeout=10,
        )
        if status is None or not isinstance(payload, list):
            return []
        return payload

    def search_experiments_flexible(self, texto: str) -> List[Dict]:
        status, payload = self._request_json(
            "GET",
            "/experimentos/buscar/texto-livre",
            params={"q": texto},
            timeout=10,
        )
        if status is None or not isinstance(payload, list):
            return []
        return payload
    
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
    
    def delete_thermal_calculation(self, calculo_id):
        status, payload = self._request_json(
            "DELETE",
            f"/calculos-termicos/{calculo_id}"
        )

        return payload

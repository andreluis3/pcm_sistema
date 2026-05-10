from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core import energy_model
from core.experimental_engine import energia_por_integracao_potencia
from core.pcm_simulator_termico import calcular_pcm_energia_tempo_estabilidade
from database.database_manager import DatabaseManager


class ControllerCalculos:
    """
    Camada de serviço: único ponto de chamada da UI para cálculos térmicos.

    Regras de retorno:
    - experimental: retorna float (energia)
    - pcm: retorna dict {"energia": float, "tempo_estabilidade": float|None}
    """

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self._db = db_manager or DatabaseManager()
        self._current_experiment_id: int | None = None

    def set_current_experiment_id(self, experiment_id: int | None) -> None:
        self._current_experiment_id = int(experiment_id) if experiment_id is not None else None

    # --- Dados (UI -> controller -> DB) ---------------------------------
    def list_experiments(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._db.list_experiments()]

    def get_calculo_by_experimento_tipo(self, experimento_id: int, tipo_calculo: str) -> dict[str, Any] | None:
        # Preferência: repositório híbrido pode implementar este método com API/MySQL.
        row = self._db.get_calculo_by_experimento_tipo(experimento_id, tipo_calculo)
        if row is None:
            return None
        return dict(row) if not isinstance(row, dict) else row

    def get_prefill_values(self, experiment: Mapping[str, Any] | None, calc_type: str) -> dict[str, float]:
        if not experiment or experiment.get("id") is None:
            return {}

        values: dict[str, float] = {}

        massa = experiment.get("massa")
        delta_t = experiment.get("delta_temperatura")
        if massa is not None:
            values["m"] = float(massa)
        if delta_t is not None:
            values["delta_t"] = float(delta_t)

        return values

    def save_thermal_calculation(
        self,
        *,
        experimento_id: int,
        tipo_calculo: str,
        inputs: Mapping[str, float | None],
        resultado: float,
    ) -> int:
        """
        Persistência unificada:
        - Preferência: API/MySQL (`calculos_termicos`)
        - Fallback: SQLite (`thermal_calculations`)

        Mantém assinatura usada pela UI, mas não usa mais `tabela_calculos`.
        """
        payload = {
            "experimento_id": int(experimento_id),
            "tipo_calculo": str(tipo_calculo),
            "delta_t": inputs.get("delta_t"),
            "resultado": float(resultado),
        }
        return int(self._db.insert_thermal_calculation(payload))

    # --- Física (UI -> controller -> core) -------------------------------
    def calculate_thermal(self, calc_type: str, values: Mapping[str, float]) -> float:
        if calc_type == "Energia Absorvida":
            return energy_model.energia_absorvida(values["m"], values["delta_t"])
        if calc_type == "Calor Sensível":
            return energy_model.calor_sensivel(values["m"], values["delta_t"])
        if calc_type == "Calor Latente":
            return energy_model.calor_latente(values["m"], values["l"])
        raise ValueError(f"Tipo de cálculo não suportado: {calc_type}")

    def calculate_experimental_energy(self, *, tempos_s: list[float], potencias_w: list[float]) -> float:
        return float(energia_por_integracao_potencia(tempos_s, potencias_w))

    def calculate_pcm(self, **kwargs: Any) -> dict[str, float | None]:
        # kwargs esperado: massa_pcm_g, delta_t_c, calor_latente_j_g, potencia_w, etc.
        return calcular_pcm_energia_tempo_estabilidade(**kwargs)

    def simulate_pcm_computer(
        self,
        mode: str,
        power_w: float,
        time_min: float | None,
        mass_g: float | None,
    ) -> dict[str, float | None | str]:
        mode_norm = (mode or "").strip().lower()
        if mode_norm in {"pcm necessário", "pcm necessario", "pcm_needed", "needed", "mass"}:
            mode_norm = "pcm_needed"
        elif mode_norm in {"tempo suportado", "time_supported", "supported", "time"}:
            mode_norm = "time_supported"
        else:
            raise ValueError("Modo inválido. Use 'pcm_needed' ou 'time_supported'.")

        power = float(power_w)
        if power <= 0:
            raise ValueError("Potência deve ser maior que zero.")

        delta_t_c = self._get_simulation_delta_t_c()
        if delta_t_c <= 0:
            raise ValueError("ΔT inválido para simulação (deve ser > 0).")

        c = float(energy_model.CONSTANT_C)

        if mode_norm == "pcm_needed":
            if time_min is None:
                raise ValueError("Informe o tempo (min) para o modo 'PCM necessário'.")
            time_s = float(time_min) * 60.0
            if time_s <= 0:
                raise ValueError("Tempo deve ser maior que zero.")
            energy = power * time_s  # J
            mass_kg = energy / (c * delta_t_c)
            pcm_mass_g = mass_kg * 1000.0
            status = "estável" if pcm_mass_g > 0 else "insuficiente"
            return {"energy": energy, "pcm_mass": pcm_mass_g, "time_supported": None, "status": status}

        if mass_g is None:
            raise ValueError("Informe a massa de PCM (g) para o modo 'Tempo suportado'.")
        pcm_mass_g = float(mass_g)
        if pcm_mass_g <= 0:
            raise ValueError("Massa de PCM deve ser maior que zero.")
        energy_pcm = (pcm_mass_g / 1000.0) * c * delta_t_c  # J
        time_supported_s = energy_pcm / power
        time_supported_min = time_supported_s / 60.0
        status = "estável" if time_supported_min >= 1.0 else "insuficiente"
        return {"energy": energy_pcm, "pcm_mass": pcm_mass_g, "time_supported": time_supported_min, "status": status}

    def _get_simulation_delta_t_c(self) -> float:
        if self._current_experiment_id is None:
            return 29.0
        row = self._db.get_experiment_by_id(self._current_experiment_id)
        if row is None:
            return 29.0
        delta_t = row["delta_temperatura"]
        return float(delta_t) if delta_t is not None else 29.0

from __future__ import annotations

CONSTANT_C = 2000.0  # J/kg·K (equivalente a 2.0 kJ/kg·°C)
CONSTANT_C_J_G_C = CONSTANT_C / 1000.0  # 2.0 J/g·°C


def energia_absorvida(massa_g: float, delta_t_c: float) -> float:
    massa_kg = float(massa_g) / 1000.0
    return massa_kg * CONSTANT_C * float(delta_t_c)


def calor_sensivel(massa_g: float, delta_t_c: float) -> float:
    return energia_absorvida(massa_g=massa_g, delta_t_c=delta_t_c)


def calor_latente(massa_g: float, calor_latente_j_g: float) -> float:
    return float(massa_g) * float(calor_latente_j_g)

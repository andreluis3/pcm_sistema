from __future__ import annotations

from collections.abc import Sequence

from core.energy_model import calor_latente, calor_sensivel


def calcular_tempo_estabilidade(
    tempos_s: Sequence[float],
    temperaturas_c: Sequence[float],
    *,
    derivada_max_c_por_s: float = 0.02,
    amostras_consecutivas: int = 10,
) -> float | None:
    if len(tempos_s) != len(temperaturas_c):
        raise ValueError("tempos_s e temperaturas_c devem ter o mesmo tamanho.")
    if len(tempos_s) < 2:
        return None

    stable_count = 0
    for i in range(1, len(tempos_s)):
        t0 = float(tempos_s[i - 1])
        t1 = float(tempos_s[i])
        temp0 = float(temperaturas_c[i - 1])
        temp1 = float(temperaturas_c[i])
        dt = t1 - t0
        if dt <= 0:
            raise ValueError("tempos_s deve estar em ordem crescente (dt > 0).")
        deriv = abs((temp1 - temp0) / dt)
        if deriv <= float(derivada_max_c_por_s):
            stable_count += 1
            if stable_count >= int(amostras_consecutivas):
                return float(tempos_s[i])
        else:
            stable_count = 0
    return None


def calcular_pcm_energia_tempo_estabilidade(
    *,
    massa_pcm_g: float,
    delta_t_c: float,
    calor_latente_j_g: float,
    potencia_w: float | None = None,
    incluir_latente: bool = True,
    tempos_s: Sequence[float] | None = None,
    temperaturas_c: Sequence[float] | None = None,
    derivada_max_c_por_s: float = 0.02,
    amostras_consecutivas: int = 10,
) -> dict[str, float | None]:
    energia_sensivel = calor_sensivel(massa_g=massa_pcm_g, delta_t_c=delta_t_c)
    energia_latente = calor_latente(massa_g=massa_pcm_g, calor_latente_j_g=calor_latente_j_g) if incluir_latente else 0.0
    energia_total = float(energia_sensivel + energia_latente)

    tempo_estabilidade: float | None = None
    if potencia_w is not None:
        potencia = float(potencia_w)
        tempo_estabilidade = (energia_total / potencia) if potencia > 0 else None
    elif tempos_s is not None and temperaturas_c is not None:
        tempo_estabilidade = calcular_tempo_estabilidade(
            tempos_s,
            temperaturas_c,
            derivada_max_c_por_s=derivada_max_c_por_s,
            amostras_consecutivas=amostras_consecutivas,
        )

    return {"energia": energia_total, "tempo_estabilidade": tempo_estabilidade}

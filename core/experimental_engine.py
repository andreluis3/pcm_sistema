from __future__ import annotations

from collections.abc import Sequence


def energia_por_integracao_potencia(tempos_s: Sequence[float], potencias_w: Sequence[float]) -> float:
    if len(tempos_s) != len(potencias_w):
        raise ValueError("tempos_s e potencias_w devem ter o mesmo tamanho.")
    if len(tempos_s) < 2:
        return 0.0

    energia_j = 0.0
    for i in range(1, len(tempos_s)):
        t0 = float(tempos_s[i - 1])
        t1 = float(tempos_s[i])
        p0 = float(potencias_w[i - 1])
        p1 = float(potencias_w[i])
        dt = t1 - t0
        if dt < 0:
            raise ValueError("tempos_s deve estar em ordem crescente.")
        energia_j += (p0 + p1) * 0.5 * dt
    return energia_j

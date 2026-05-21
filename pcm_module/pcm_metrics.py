"""
pcm_metrics.py
══════════════
Cálculos térmicos puros — sem dependência de UI, pandas ou matplotlib.

Todas as funções recebem e retornam tipos primitivos Python:
    list[float], float, int, str, dict, None.
Nenhuma pandas.Series deve entrar ou sair deste módulo.
"""
from __future__ import annotations

from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Constantes físicas do PCM
# ─────────────────────────────────────────────────────────────────────────────

TEMP_FUSAO_PCM: float = 53.0       # °C — início da fusão
TEMP_SATURACAO_PCM: float = 60.0   # °C — saturação (fim da fusão)
CALOR_ESPECIFICO_PCM: float = 2000.0  # J/(kg·K)
CALOR_LATENTE_PCM: float = 180.0      # J/g  (180 kJ/kg)


# ─────────────────────────────────────────────────────────────────────────────
# Derivada discreta dT/dt
# ─────────────────────────────────────────────────────────────────────────────

def calcular_dT_dt(
    tempo_s: list[float],
    temperatura_c: list[float],
) -> list[float]:
    """
    Derivada discreta dT/dt em °C/s usando diferença entre pontos consecutivos.

    Mantém o mesmo comprimento da entrada; dT_dt[0] = 0.0.
    Nunca recebe nem retorna pandas.Series.
    """
    if not tempo_s or not temperatura_c:
        return []

    n = min(len(tempo_s), len(temperatura_c))
    if n <= 1:
        return [0.0] * n

    derivada: list[float] = [0.0]
    for i in range(1, n):
        dt = float(tempo_s[i]) - float(tempo_s[i - 1])
        if dt <= 0.0:
            derivada.append(0.0)
            continue
        dtemp = float(temperatura_c[i]) - float(temperatura_c[i - 1])
        derivada.append(dtemp / dt)

    return derivada


# ─────────────────────────────────────────────────────────────────────────────
# Tempo na faixa PCM com interpolação linear
# ─────────────────────────────────────────────────────────────────────────────

def calcular_tempo_na_faixa_pcm(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    pcm_min_c: float = TEMP_FUSAO_PCM,
    pcm_max_c: float = TEMP_SATURACAO_PCM,
) -> float:
    """
    Tempo total (s) em que a temperatura esteve dentro de [pcm_min_c, pcm_max_c].

    Assume variação linear entre amostras e calcula a interseção por segmento.
    Retorna 0.0 se não houver dados suficientes.
    """
    if not tempo_s or not temperatura_c:
        return 0.0

    n = min(len(tempo_s), len(temperatura_c))
    if n < 2:
        return 0.0

    faixa_min = float(min(pcm_min_c, pcm_max_c))
    faixa_max = float(max(pcm_min_c, pcm_max_c))
    total = 0.0

    for i in range(1, n):
        t0 = float(tempo_s[i - 1])
        t1 = float(tempo_s[i])
        dt = t1 - t0
        if dt <= 0.0:
            continue

        T0 = float(temperatura_c[i - 1])
        T1 = float(temperatura_c[i])

        # Segmento constante
        if T0 == T1:
            if faixa_min <= T0 <= faixa_max:
                total += dt
            continue

        a = (T1 - T0) / dt
        t_enter = t0
        t_exit = t1

        for Tlim, is_lower in ((faixa_min, True), (faixa_max, False)):
            tcross = t0 + (Tlim - T0) / a
            if is_lower:
                if a > 0:
                    t_enter = max(t_enter, tcross)
                else:
                    t_exit = min(t_exit, tcross)
            else:
                if a > 0:
                    t_exit = min(t_exit, tcross)
                else:
                    t_enter = max(t_enter, tcross)

        t_enter = max(t0, min(t_enter, t1))
        t_exit = max(t0, min(t_exit, t1))

        if t_exit > t_enter:
            total += t_exit - t_enter

    return max(0.0, total)


# ─────────────────────────────────────────────────────────────────────────────
# Tempo de estabilização
# ─────────────────────────────────────────────────────────────────────────────

def calcular_estabilizacao(
    tempo_s: list[float],
    dT_dt: list[float],
    *,
    limiar: float = 0.01,
    janela_s: float = 30.0,
) -> Optional[float]:
    """
    Retorna o tempo (s) em que |dT/dt| < limiar de forma contínua por janela_s.

    Retorna None se o sistema não estabilizou dentro dos dados fornecidos.
    """
    if not tempo_s or not dT_dt:
        return None

    n = min(len(tempo_s), len(dT_dt))
    if n < 4:
        return None

    dts = [
        float(tempo_s[i]) - float(tempo_s[i - 1])
        for i in range(1, n)
        if (float(tempo_s[i]) - float(tempo_s[i - 1])) > 0.0
    ]
    if not dts:
        return None

    dt_med = sorted(dts)[len(dts) // 2]
    window_points = max(3, min(40, int(round(janela_s / max(dt_med, 1e-6)))))
    abs_der = [abs(float(v)) for v in dT_dt[:n]]

    for i in range(1, n - window_points):
        if all(v < limiar for v in abs_der[i : i + window_points]):
            return float(tempo_s[i])

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Métricas completas do experimento
# ─────────────────────────────────────────────────────────────────────────────

def calcular_metricas_experimento(
    tempo_s: list[float],
    temperatura_c: list[float],
    energia_total: float,
    massa_pcm: float,
    energia_teorica: float,
    pico_temperatura: float,
    tempo_pico_temperatura: float,
    potencia_media: float,
    delta_tempo: float,
    temperatura_media: float,
    *,
    temperatura_alvo_c: float = 55.0,
    pcm_min_c: float = TEMP_FUSAO_PCM,
    pcm_max_c: float = TEMP_SATURACAO_PCM,
) -> dict[str, Optional[float]]:
    """
    Calcula todas as métricas derivadas do experimento PCM.

    Recebe apenas tipos primitivos Python — NUNCA pandas.Series.
    Retorna dict[str, float | None].

    Parâmetros
    ──────────
    tempo_s, temperatura_c  : séries temporais como list[float]
    energia_total           : energia integrada do CSV (J)
    massa_pcm               : massa estimada de PCM (g)
    energia_teorica         : energia ideal calculada pelo serviço (J)
    pico_temperatura        : temperatura máxima registrada (°C)
    tempo_pico_temperatura  : tempo em que ocorreu o pico (s)
    potencia_media          : potência média durante o ensaio (W)
    delta_tempo             : duração total registrada no CSV (s)
    temperatura_media       : temperatura média registrada (°C)
    """
    # ── Duração ───────────────────────────────────────────────────────────────
    duracao_s: float = float(max(tempo_s)) if tempo_s else float(delta_tempo)
    duracao_min: Optional[float] = duracao_s / 60.0 if duracao_s > 0.0 else None

    # ── Variação térmica ──────────────────────────────────────────────────────
    delta_t_c: float = (
        float(max(temperatura_c)) - float(min(temperatura_c))
        if temperatura_c
        else 0.0
    )

    # ── Taxa de aquecimento ───────────────────────────────────────────────────
    taxa_c_min: Optional[float] = (
        (delta_t_c / duracao_s) * 60.0 if duracao_s > 0.0 else None
    )

    # ── Energia absorvida pelo PCM ────────────────────────────────────────────
    # Q_l = m(g) * L(J/g)
    energia_pcm_absorvida: float = min(
        float(massa_pcm) * CALOR_LATENTE_PCM,
        float(energia_total),
    )
    energia_perdida: float = float(energia_total) - energia_pcm_absorvida

    # ── Eficiência e erro ─────────────────────────────────────────────────────
    eficiencia: Optional[float] = (
        (energia_pcm_absorvida / float(energia_total)) * 100.0
        if energia_total > 0.0
        else None
    )
    erro_percentual: Optional[float] = (
        (energia_perdida / float(energia_total)) * 100.0
        if energia_total > 0.0
        else None
    )

    # ── Tempo até temperatura alvo ────────────────────────────────────────────
    tempo_ate_alvo_s: Optional[float] = None
    for t, temp in zip(tempo_s, temperatura_c):
        if float(temp) >= float(temperatura_alvo_c):
            tempo_ate_alvo_s = float(t)
            break

    # ── Tempo de atuação do PCM ───────────────────────────────────────────────
    tempo_atuacao_pcm_s: float = calcular_tempo_na_faixa_pcm(
        tempo_s,
        temperatura_c,
        pcm_min_c=float(pcm_min_c),
        pcm_max_c=float(pcm_max_c),
    )

    return {
        "duracao_s": duracao_s,
        "duracao_min": duracao_min,
        "pico_temp_c": float(pico_temperatura),
        "tempo_pico_s": float(tempo_pico_temperatura),
        "delta_t_c": delta_t_c,
        "taxa_aquecimento_c_min": taxa_c_min,
        "eficiencia_percent": eficiencia,
        "erro_percentual": erro_percentual,
        "energia_ideal_j": float(energia_teorica),
        "tempo_ate_55c_s": tempo_ate_alvo_s,
        "tempo_atuacao_pcm_s": tempo_atuacao_pcm_s,
        "potencia_media": float(potencia_media),
        "temperatura_media": float(temperatura_media),
        "delta_tempo": float(delta_tempo),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de formatação
# ─────────────────────────────────────────────────────────────────────────────

def formatar_tempo_min_seg(tempo_s: Optional[float]) -> str:
    """Formata segundos em MM:SS. Retorna '--' para None."""
    if tempo_s is None:
        return "--"
    tempo_s = max(0.0, float(tempo_s))
    return f"{int(tempo_s // 60):02d}:{int(round(tempo_s % 60)):02d}"


def formatar_tempo_min(tempo_s: Optional[float]) -> str:
    """Formata segundos em 'X.Y min'. Retorna '--' para None."""
    if tempo_s is None:
        return "--"
    return f"{max(0.0, float(tempo_s)) / 60.0:.1f} min"


def smooth_series(values: list[float], window: int = 7) -> list[float]:
    """
    Média móvel centrada para suavizar curvas científicas.
    Implementação pura Python — sem pandas.
    """
    if len(values) < window or window < 2:
        return list(values)

    half = window // 2
    result: list[float] = []

    for i in range(len(values)):
        start = max(0, i - half)
        end = min(len(values), i + half + 1)
        result.append(sum(values[start:end]) / (end - start))

    return result
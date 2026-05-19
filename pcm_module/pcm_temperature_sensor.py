from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


# Constantes físicas do PCM

MASSA_PCM_KG: float = 1.0

# 2 kJ/kg·K
CALOR_ESPECIFICO_PCM: float = 2000.0

# Temperatura de fusão
TEMP_FUSAO_PCM: float = 53.0

# Região de saturação
TEMP_SATURACAO_PCM: float = 60.0

# 107 J/g → 107000 J/kg
CALOR_LATENTE_PCM: float = 107000.0

# Energia média gerada notebook
ENERGIA_NOTEBOOK_J: float = 234000.0


@dataclass
class SensorPCMResult:
    tempo_s: list[float]
    temperatura_c: list[float]
    temperatura_simulada: list[float]

    # Métricas calculadas a partir da temperatura SIMULADA (10pct)
    tempo_total: float
    pico_temperatura: float          # °C (simulada)
    tempo_pico_s: float              # s
    temperatura_media: float         # °C (simulada)
    temperatura_inicial: float       # °C (simulada)

    # Energia (calculada sobre temp_simulada)
    # Energia
    energia_sensivel_j: float
    energia_latente_j: float
    energia_total_j: float

    energia_ao_longo_tempo: list[float]

    # Eficiência térmica
    eficiencia_pcm: float

    # Estado do PCM
    estado_pcm: str

    # Tempo estabilização
    tempo_estabilizacao_s: float  # Q(t) = m·c·(T(t) - T_inicial)  [J]

    # Tempo dentro da faixa de atuação do PCM (50–60 °C)
    tempo_atuacao_pcm_s: float


class PCMTemperatureSensor:
    """Lê CSV do sensor infravermelho e calcula métricas energéticas usando temp_simulada_10pct."""

    def load_csv(self, csv_path: str | Path) -> SensorPCMResult:
        df = pd.read_csv(csv_path)

        required = {"temp", "time_ms", "minutes", "temp_simulada_10pct"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"CSV inválido. Faltando colunas: {missing}")

        tempo_s = (df["time_ms"].astype(float) / 1000.0).tolist()
        temp_real = df["temp"].astype(float).tolist()
        temp_sim = (
            df["temp_simulada_10pct"]
            .rolling(window=8, center=True)
            .mean()
            .bfill()
            .ffill()
            .astype(float)
            .tolist()
        )

        # Usa temperatura SIMULADA para todos os cálculos de energia / métricas
        T_inicial = temp_sim[0]
        T_pico = max(temp_sim)
        idx_pico = temp_sim.index(T_pico)
        t_pico = tempo_s[idx_pico]

        # ── ΔT total ─────────────────────────────────

        delta_T_total = max(0.0, T_pico - T_inicial)

        # ── Energia sensível ─────────────────────────

        energia_sensivel_j = (
            MASSA_PCM_KG *
            CALOR_ESPECIFICO_PCM *
            delta_T_total
        )

        # ── Fração fundida do PCM ────────────────────

        fracao_fundida = max(
            0.0,
            min(
                (
                    T_pico - TEMP_FUSAO_PCM
                ) / (
                    TEMP_SATURACAO_PCM - TEMP_FUSAO_PCM
                ),
                1.0,
            ),
        )

        # ── Energia latente ──────────────────────────

        energia_latente_j = (
            MASSA_PCM_KG *
            CALOR_LATENTE_PCM *
            fracao_fundida
        )

        # ── Energia total ────────────────────────────

        energia_total_j = (
            energia_sensivel_j +
            energia_latente_j
        )

        # ── Eficiência térmica ───────────────────────

        eficiencia_pcm = (
            energia_total_j /
            ENERGIA_NOTEBOOK_J
        ) * 100.0

        # ── Estado do PCM ────────────────────────────

        if T_pico < TEMP_FUSAO_PCM:
            estado_pcm = "Sólido"

        elif T_pico <= TEMP_SATURACAO_PCM:
            estado_pcm = "Em fusão"

        else:
            estado_pcm = "Saturado"

        # Energia acumulada em cada instante: Q(t) = m·c·(T(t) − T_inicial)
        energia_ao_longo_tempo = []

        for temp in temp_sim:

            delta_t = max(
                0.0,
                temp - T_inicial
            )

            energia_sensivel = (
                MASSA_PCM_KG *
                CALOR_ESPECIFICO_PCM *
                delta_t
            )

            fracao = max(
                0.0,
                min(
                    (
                        temp - TEMP_FUSAO_PCM
                    ) / (
                        TEMP_SATURACAO_PCM - TEMP_FUSAO_PCM
                    ),
                    1.0,
                ),
            )

            energia_latente = (
                MASSA_PCM_KG *
                CALOR_LATENTE_PCM *
                fracao
            )

            energia_total = (
                energia_sensivel +
                energia_latente
            )

            energia_ao_longo_tempo.append(
                energia_total
            )

        tempo_total = float(tempo_s[-1] - tempo_s[0]) if len(tempo_s) > 1 else 0.0
        temp_media = float(sum(temp_sim) / len(temp_sim))

        # Tempo dentro da faixa PCM 50–60 °C (sobre temp_simulada)
        tempo_atuacao_pcm_s = _tempo_na_faixa(tempo_s, temp_sim, faixa_min=50.0, faixa_max=60.0)
        
        
        tempo_estabilizacao_s = 0.0

        for i in range(1, len(temp_sim)):

            dt = tempo_s[i] - tempo_s[i - 1]

            if dt <= 0:
                continue

            dT = temp_sim[i] - temp_sim[i - 1]

            taxa = abs(dT / dt)

            if taxa < 0.0005:
                tempo_estabilizacao_s = tempo_s[i]
                break

        return SensorPCMResult(
            tempo_s=tempo_s,
            temperatura_c=temp_real,
            temperatura_simulada=temp_sim,
            tempo_total=tempo_total,
            pico_temperatura=T_pico,
            tempo_pico_s=t_pico,
            temperatura_media=temp_media,
            temperatura_inicial=T_inicial,
            energia_sensivel_j=energia_sensivel_j,
            energia_latente_j=energia_latente_j,
            energia_total_j=energia_total_j,

            energia_ao_longo_tempo=energia_ao_longo_tempo,

            eficiencia_pcm=eficiencia_pcm,
            estado_pcm=estado_pcm,

            tempo_estabilizacao_s=tempo_estabilizacao_s,

            tempo_atuacao_pcm_s=tempo_atuacao_pcm_s,
        )


# ── helpers ──────────────────────────────────────────────────────────────────

def _tempo_na_faixa(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    faixa_min: float,
    faixa_max: float,
) -> float:
    """Tempo total (s) com interpolação linear em que T está dentro [faixa_min, faixa_max]."""
    n = min(len(tempo_s), len(temperatura_c))
    if n < 2:
        return 0.0
    lo, hi = min(faixa_min, faixa_max), max(faixa_min, faixa_max)
    total = 0.0
    for i in range(1, n):
        t0, t1 = float(tempo_s[i - 1]), float(tempo_s[i])
        dt = t1 - t0
        if dt <= 0:
            continue
        T0, T1 = float(temperatura_c[i - 1]), float(temperatura_c[i])
        if T0 == T1:
            if lo <= T0 <= hi:
                total += dt
            continue
        a = (T1 - T0) / dt
        t_enter, t_exit = t0, t1
        for Tlim, is_lower in ((lo, True), (hi, False)):
            tcross = t0 + (Tlim - T0) / a
            if is_lower:
                t_enter = max(t_enter, tcross) if a > 0 else t_enter
                t_exit = min(t_exit, tcross) if a <= 0 else t_exit
            else:
                t_exit = min(t_exit, tcross) if a > 0 else t_exit
                t_enter = max(t_enter, tcross) if a <= 0 else t_enter
        t_enter = max(t0, min(t_enter, t1))
        t_exit = max(t0, min(t_exit, t1))
        if t_exit > t_enter:
            total += t_exit - t_enter
    return max(0.0, total)
"""
pcm_temperature_sensor.py
════════════════════════════════════════════════════════════════════════════════
Modelo físico correto para o experimento real:

  "Plataforma experimental de análise térmica passiva com PCM em notebook"

O experimento NÃO assume fusão total do PCM.
O objetivo É medir quanto calor o PCM absorve/dissipa passivamente do notebook.

Física adotada:
  - Uma temperatura por instante: temperatura_c (normalizada de qualquer fonte)
  - Energia absorvida: Q = m·c·ΔT  (calor sensível real medido)
  - Eficiência: baseada em redução de pico vs baseline SEM PCM
  - Estado do PCM: baseado na temperatura observada vs faixas físicas
  - Baseline sem PCM: carregada de CSV separado (opcional)

CSV aceito (qualquer um dos dois formatos — normalização automática):
  Formato novo:  timestamp, tempo_s,  temperatura_c, potencia_w, energia_j
  Formato legado: time_ms,  minutes,   temp / temp_filtrada / temp_simulada_10pct
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


# ── Constantes reais do experimento ───────────────────────────────────────────

NOTEBOOK_REFERENCIA_J: float = 234000.0

# massa real da cera de coco
MASSA_PCM_KG: float = 1.182

# calor específico médio da cera de coco
CALOR_ESPECIFICO_PCM: float = 3050.0  # J/kg·K

# calor latente estimado da cera de coco
CALOR_LATENTE_PCM: float = 152000.0   # J/kg

# Faixas térmicas — usadas apenas para classificar estado do PCM
# NÃO são obrigatórias para o experimento atingir
TEMP_FUSAO_PCM:     float = 53.0  # °C — início da fusão
TEMP_SATURACAO_PCM: float = 60.0  # °C — saturação térmica


# ── Mapa de normalização de colunas ───────────────────────────────────────────

_RENAME_MAP: dict[str, str] = {
    # temperatura → padrão interno: temperatura_c
    "temp":                 "temperatura_c",
    "temp_filtrada":        "temperatura_c",
    "temp_simulada_10pct":  "temperatura_c",
    "temp_suavizada":       "temperatura_c",
    # tempo → padrão interno: timestamp (ms) e tempo_s (segundos)
    "time_ms":              "timestamp",
    "minutes":              "tempo_s",
}


@dataclass
class SensorPCMResult:
    """Resultado completo de um ensaio do sensor IR."""

    # Séries temporais
    tempo_s:       list[float]  # tempo em segundos
    temperatura_c: list[float]  # temperatura filtrada (única curva)

    # Métricas do ensaio
    tempo_total:         float  # duração total (s)
    pico_temperatura:    float  # °C — pico máximo observado
    tempo_pico_s:        float  # s  — instante do pico
    temperatura_media:   float  # °C — média do ensaio
    temperatura_inicial: float  # °C — temperatura no início

    # ── NOVO: leitura mais recente do sensor ──────────────────────────────────
    temperatura_atual_c: float = 0.0  # °C — temp_c[-1]

    # Energia absorvida (calor sensível + latente)
    energia_total_j:        float = 0.0
    energia_ao_longo_tempo: list[float] = field(default_factory=list)

    # Estado do PCM com base na temperatura observada
    estado_pcm: str = "Estável"

    # Tempo em que o sensor ficou dentro da faixa de atuação do PCM
    tempo_atuacao_pcm_s: float = 0.0

    # Tempo de estabilização (|dT/dt| < limiar contínuo)
    tempo_estabilizacao_s: float = 0.0


    # Redução absoluta de pico (°C) vs baseline
    reducao_pico_c: float | None = None

    # Atraso térmico
    atraso_termico_s: float | None = None

    # Baseline SEM PCM — série de temperatura (opcional, para overlay no gráfico)
    baseline_tempo_s: list[float] = field(default_factory=list)
    baseline_temp_c:  list[float] = field(default_factory=list)
    baseline_pico_c:  float | None = None

    energia_sensivel_j: float = 0.0
    energia_latente_j:  float = 0.0

    eficiencia_termica:            float = 0.0
    erro_percentual:               float = 0.0
    energia_referencia_notebook_j: float = NOTEBOOK_REFERENCIA_J


class PCMTemperatureSensor:
    """
    Lê CSV do sensor e calcula métricas corretas para o experimento real.

    Aceita qualquer dos dois formatos de CSV sem configuração adicional:
      - Formato novo  (timestamp / tempo_s / temperatura_c)
      - Formato legado (time_ms / minutes / temp ou temp_filtrada)

    Toda a normalização ocorre internamente em _normalizar_colunas().
    O restante do pipeline opera SOMENTE sobre o padrão interno.
    """

    def __init__(self) -> None:
        self._baseline: SensorPCMResult | None = None

    # ── API pública ───────────────────────────────────────────────────────────

    def load_csv(self, file_path: str | Path) -> SensorPCMResult:
        """
        Carrega CSV do sensor, normaliza colunas e calcula métricas.
        Aceita formato legado (time_ms / temp_filtrada) e novo (tempo_s / temperatura_c).
        """
        df = pd.read_csv(file_path)
        df = self._normalizar_colunas(df)
        result = self._calcular(df)

        # Se houver baseline carregada, aplica comparação automaticamente
        if self._baseline is not None:
            self._aplicar_comparacao(result, self._baseline)

        return result

    def load_baseline_csv(self, csv_path: str | Path) -> SensorPCMResult:
        """
        Carrega CSV SEM PCM como baseline de referência.
        Após isso, qualquer load_csv() calculará eficiência relativa automaticamente.
        """
        df = pd.read_csv(csv_path)
        df = self._normalizar_colunas(df)
        self._baseline = self._calcular(df)
        return self._baseline

    def get_baseline(self) -> SensorPCMResult | None:
        return self._baseline

    # ── Normalização unificada de colunas ────────────────────────────────────

    @staticmethod
    def _normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte QUALQUER formato de CSV para o padrão interno:
          temperatura_c | tempo_s | timestamp | potencia_w | energia_j
        """
        # 1. Renomeia colunas legadas ─────────────────────────────────────────
        temp_priority = ["temp_filtrada", "temp_suavizada", "temp_simulada_10pct", "temp"]
        temp_col_to_use = next((c for c in temp_priority if c in df.columns), None)

        non_temp_rename = {k: v for k, v in _RENAME_MAP.items() if v != "temperatura_c"}
        df = df.rename(columns=non_temp_rename)

        if "temperatura_c" not in df.columns and temp_col_to_use is not None:
            actual_name = _RENAME_MAP.get(temp_col_to_use, temp_col_to_use)
            if actual_name in df.columns:
                df = df.rename(columns={actual_name: "temperatura_c"})
            elif temp_col_to_use in df.columns:
                df = df.rename(columns={temp_col_to_use: "temperatura_c"})

        # 2. tempo_s ──────────────────────────────────────────────────────────
        if "tempo_s" not in df.columns:
            if "timestamp" in df.columns:
                try:
                    ts_numeric = pd.to_numeric(df["timestamp"], errors="coerce")
                    if ts_numeric.notna().all():
                        df["tempo_s"] = ts_numeric.astype(float) / 1000.0
                    else:
                        df["tempo_s"] = pd.Series(range(len(df)), dtype=float)
                except Exception:
                    df["tempo_s"] = pd.Series(range(len(df)), dtype=float)
            else:
                df["tempo_s"] = pd.Series(range(len(df)), dtype=float)
        else:
            try:
                max_t = float(df["tempo_s"].max())
                if 0 < max_t < 300:
                    df["tempo_s"] = df["tempo_s"].astype(float) * 60.0
            except Exception:
                pass

        # 3. Garante timestamp ────────────────────────────────────────────────
        if "timestamp" not in df.columns:
            df["timestamp"] = (df["tempo_s"] * 1000.0).astype(int)

        # 4. Garante temperatura_c ────────────────────────────────────────────
        if "temperatura_c" not in df.columns:
            raise ValueError(
                "CSV inválido: nenhuma coluna de temperatura encontrada.\n"
                "Esperado (qualquer um): 'temperatura_c', 'temp', 'temp_filtrada', "
                "'temp_simulada_10pct', 'temp_suavizada'."
            )

        # 5. Converte colunas numéricas essenciais ────────────────────────────
        for col in ("tempo_s", "temperatura_c"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # 6. Garante potencia_w e energia_j ───────────────────────────────────
        if "potencia_w" not in df.columns:
            df["potencia_w"] = 0.0

        if "energia_j" not in df.columns:
            temps = list(df["temperatura_c"])
            energia = [0.0]
            massa, cp = 0.020, 2000.0
            for i in range(1, len(temps)):
                dT = max(float(temps[i]) - float(temps[i - 1]), 0.0)
                energia.append(energia[-1] + massa * cp * dT)
            df["energia_j"] = energia

        # 7. Converte colunas auxiliares numéricas ────────────────────────────
        for col in ("potencia_w", "energia_j"):
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # 8. Valida integridade mínima ─────────────────────────────────────────
        if len(df) < 2:
            raise ValueError("CSV inválido: necessário pelo menos 2 linhas de dados.")

        if df["temperatura_c"].isna().all():
            raise ValueError("CSV inválido: coluna 'temperatura_c' contém apenas valores nulos.")

        return df

    # ── Cálculo das métricas ──────────────────────────────────────────────────

    def _calcular(self, df: pd.DataFrame) -> SensorPCMResult:
        """
        Recebe DataFrame já normalizado (padrão interno) e calcula todas as métricas.
        Opera SOMENTE sobre: tempo_s, temperatura_c, potencia_w, energia_j.
        """
        tempo_s: list[float] = df["tempo_s"].astype(float).tolist()

        temp_c: list[float] = (
            df["temperatura_c"]
            .rolling(window=7, center=True, min_periods=1)
            .mean()
            .astype(float)
            .tolist()
        )

        T_ini    = float(temp_c[0])
        T_atual  = float(temp_c[-1])   # ← leitura mais recente
        T_pico   = float(max(temp_c))
        idx_pico = temp_c.index(T_pico)
        t_pico   = float(tempo_s[idx_pico])

        # ── Energia sensível: Q_s = m·c·ΔT ───────────────────────────────────
        delta_t_total    = max(0.0, T_pico - T_ini)
        energia_sensivel = MASSA_PCM_KG * CALOR_ESPECIFICO_PCM * delta_t_total

        # ── Tempo dentro da faixa de atuação do PCM ───────────────────────────
        tempo_atuacao = _tempo_na_faixa(
            tempo_s,
            temp_c,
            faixa_min=TEMP_FUSAO_PCM,
            faixa_max=TEMP_SATURACAO_PCM,
        )

        # Fração de atuação (limitada a 78 min de ensaio típico)
        fracao_atuacao = min(1.0, max(0.0, tempo_atuacao / (78.0 * 60.0)))

        # ── Calor latente: Q_l = m·L·f ────────────────────────────────────────
        energia_latente = MASSA_PCM_KG * CALOR_LATENTE_PCM * fracao_atuacao

        # ── Energia total absorvida ───────────────────────────────────────────
        energia_total_j = energia_sensivel + energia_latente

        # ── Eficiência térmica vs. notebook de referência ─────────────────────
        eficiencia_termica = min(
            100.0,
            (energia_total_j / NOTEBOOK_REFERENCIA_J) * 100.0,
        )

        erro_percentual = (
            abs(NOTEBOOK_REFERENCIA_J - energia_total_j) / NOTEBOOK_REFERENCIA_J * 100.0
        )

        # ── Curva progressiva ao longo do tempo ───────────────────────────────
        energia_instante: list[float] = []
        for T, ts in zip(temp_c, tempo_s):
            dt_local   = max(0.0, T - T_ini)
            q_s        = MASSA_PCM_KG * CALOR_ESPECIFICO_PCM * dt_local
            frac_local = min(1.0, float(ts) / (78.0 * 60.0))
            q_l        = MASSA_PCM_KG * CALOR_LATENTE_PCM * frac_local
            energia_instante.append(q_s + q_l)

        # ── Estado e estabilização ────────────────────────────────────────────
        estado_pcm  = _classificar_estado(T_atual)   # usa temperatura ATUAL, não pico
        tempo_estab = _calcular_estabilizacao(tempo_s, temp_c)

        tempo_total = float(tempo_s[-1] - tempo_s[0]) if len(tempo_s) > 1 else 0.0
        temp_media  = float(sum(temp_c) / len(temp_c))

        return SensorPCMResult(
            tempo_s=tempo_s,
            temperatura_c=temp_c,
            tempo_total=tempo_total,
            pico_temperatura=T_pico,
            tempo_pico_s=t_pico,
            temperatura_media=temp_media,
            temperatura_inicial=T_ini,
            temperatura_atual_c=T_atual,       # ← NOVO
            energia_total_j=energia_total_j,
            energia_ao_longo_tempo=energia_instante,
            estado_pcm=estado_pcm,
            tempo_atuacao_pcm_s=tempo_atuacao,
            tempo_estabilizacao_s=tempo_estab,
            energia_sensivel_j=energia_sensivel,
            energia_latente_j=energia_latente,
            eficiencia_termica=eficiencia_termica,
            erro_percentual=erro_percentual,
        )


def _classificar_estado(T: float) -> str:
    """
    Estado do PCM baseado na temperatura ATUAL (não no pico).
    Reflete o estado instantâneo para exibição no dashboard.
    """
    if T < TEMP_FUSAO_PCM:
        return "PCM Sólido"
    elif T <= TEMP_SATURACAO_PCM:
        return "PCM em Fusão"
    else:
        return "PCM Saturado"


def _tempo_na_faixa(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    faixa_min: float,
    faixa_max: float,
) -> float:
    """Tempo total (s) com interpolação linear em que T ∈ [faixa_min, faixa_max]."""
    n = min(len(tempo_s), len(temperatura_c))
    if n < 2:
        return 0.0
    lo = min(faixa_min, faixa_max)
    hi = max(faixa_min, faixa_max)
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
        t_exit  = max(t0, min(t_exit,  t1))
        if t_exit > t_enter:
            total += t_exit - t_enter
    return max(0.0, total)


def _calcular_estabilizacao(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    limiar: float = 0.01,   # °C/s — taxa considerada "estável"
    janela_s: float = 30.0,  # deve ser contínuo por 30s
) -> float:
    """Retorna instante (s) em que o sistema estabilizou. 0.0 se não estabilizou."""
    n = min(len(tempo_s), len(temperatura_c))
    if n < 4:
        return 0.0

    dts = [abs(float(tempo_s[i]) - float(tempo_s[i - 1])) for i in range(1, n)]
    dt_med = sorted(dts)[len(dts) // 2] if dts else 1.0
    window = max(3, int(janela_s / max(dt_med, 1e-6)))

    taxas = [0.0]
    for i in range(1, n):
        dt = float(tempo_s[i]) - float(tempo_s[i - 1])
        if dt <= 0:
            taxas.append(0.0)
            continue
        taxas.append(
            abs(float(temperatura_c[i]) - float(temperatura_c[i - 1])) / dt
        )

    for i in range(1, n - window):
        if all(v < limiar for v in taxas[i : i + window]):
            return float(tempo_s[i])

    return 0.0
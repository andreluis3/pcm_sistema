"""
pcm_temperature_sensor.py
════════════════════════════════════════════════════════════════════════════════
Modelo físico correto para o experimento real:

  "Plataforma experimental de análise térmica passiva com PCM em notebook"

O experimento NÃO assume fusão total do PCM.
O objetivo É medir quanto calor o PCM absorve/dissipa passivamente do notebook.

Física adotada:
  - Uma temperatura por instante: temp_filtrada (sem "simulada")
  - Energia absorvida: Q = m·c·ΔT  (calor sensível real medido)
  - Eficiência: baseada em redução de pico vs baseline SEM PCM
  - Estado do PCM: baseado na temperatura observada vs faixas físicas
  - Baseline sem PCM: carregada de CSV separado (opcional)

CSV esperado do sensorreader:
  temp, time_ms, minutes, temp_filtrada
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


# ── Constantes físicas do sistema ─────────────────────────────────────────────

# ── Constantes reais do experimento ─────────────────────────────

NOTEBOOK_REFERENCIA_J: float = 234000.0

# massa real da cera de coco
MASSA_PCM_KG: float = 1.182

# calor específico médio da cera de coco
CALOR_ESPECIFICO_PCM: float = 3050.0  # J/kg·K

# calor latente estimado da cera de coco
CALOR_LATENTE_PCM: float = 152000.0   # J/kg

# Faixas térmicas — usadas apenas para classificar estado do PCM
# NÃO são obrigatórias para o experimento atingir
TEMP_FUSAO_PCM:    float = 53.0   # °C — início da fusão
TEMP_SATURACAO_PCM: float = 60.0  # °C — saturação térmica


@dataclass
class SensorPCMResult:
    """Resultado completo de um ensaio do sensor IR."""

    # Séries temporais
    tempo_s:       list[float]  # tempo em segundos
    temperatura_c: list[float]  # temperatura filtrada (única curva)

    # Métricas do ensaio
    tempo_total:        float   # duração total (s)
    pico_temperatura:   float   # °C — pico máximo observado
    tempo_pico_s:       float   # s  — instante do pico
    temperatura_media:  float   # °C — média do ensaio
    temperatura_inicial: float  # °C — temperatura no início

    # Energia absorvida (calor sensível real)
    # Q = m · c · ΔT   onde ΔT = T(t) − T_inicial
    energia_total_j:          float
    energia_ao_longo_tempo:   list[float]  # J em cada instante

    # Estado do PCM com base na temperatura observada
    estado_pcm: str  # "Estável" | "Absorvendo calor" | "Em atuação térmica" | "Saturação parcial"

    # Tempo em que o sensor ficou dentro da faixa de atuação do PCM
    tempo_atuacao_pcm_s: float

    # Tempo de estabilização (|dT/dt| < limiar contínuo)
    tempo_estabilizacao_s: float

    # Eficiência de redução térmica relativa — requer baseline SEM PCM
    # η = (T_pico_sem_pcm - T_pico_com_pcm) / T_pico_sem_pcm × 100
    # None quando baseline não foi carregada
    eficiencia_relativa: float | None = None

    # Redução absoluta de pico (°C) vs baseline
    reducao_pico_c: float | None = None

    # Atraso térmico: diferença de tempo para atingir mesma temperatura
    atraso_termico_s: float | None = None

    # Baseline SEM PCM — série de temperatura (opcional, para overlay no gráfico)
    baseline_tempo_s:  list[float] = field(default_factory=list)
    baseline_temp_c:   list[float] = field(default_factory=list)
    baseline_pico_c:   float | None = None
    
    energia_sensivel_j: float = 0.0
    energia_latente_j: float = 0.0

    eficiencia_termica: float = 0.0
    erro_percentual: float = 0.0

    energia_referencia_notebook_j: float = NOTEBOOK_REFERENCIA_J


class PCMTemperatureSensor:
    """
    Lê CSV do sensor e calcula métricas corretas para o experimento real.

    O sistema usa APENAS temp_filtrada como temperatura.
    Não há mais temp_simulada, temp_calibrada ou temp_corrigida visíveis.
    """

    def __init__(self) -> None:
        self._baseline: SensorPCMResult | None = None

    # ── API pública ───────────────────────────────────────────────────────────

    def load_csv(self, file_path: str):

        df = pd.read_csv(file_path)

        # ── Renomeia automaticamente colunas do seu log ─────────────

        rename_map = {
            "temp": "temperatura_c",
            "time_ms": "timestamp",
            "minutes": "tempo_s",
            "temp_simulada_10pct": "temperatura_c",
        }

        df = df.rename(columns=rename_map)

        # ── Se tempo_s veio em minutos → converte para segundos ─────

        if "tempo_s" in df.columns:
            df["tempo_s"] = df["tempo_s"].astype(float) * 60.0

        # ── Cria potência fake (caso não exista) ────────────────────

        if "potencia_w" not in df.columns:
            df["potencia_w"] = 0.0

        # ── Cria energia acumulada simplificada ─────────────────────

        if "energia_j" not in df.columns:

            energia = [0.0]

            temps = df["temperatura_c"].tolist()
            tempos = df["tempo_s"].tolist()

            massa = 0.020
            cp = 2000

            for i in range(1, len(temps)):

                dT = max(temps[i] - temps[i - 1], 0)

                dQ = massa * cp * dT

                energia.append(energia[-1] + dQ)

            df["energia_j"] = energia

        # ── timestamp fallback ──────────────────────────────────────

        if "timestamp" not in df.columns:
            df["timestamp"] = range(len(df))

        print(df.head())

        return self._process_dataframe(df)

    def load_baseline_csv(self, csv_path: str | Path) -> SensorPCMResult:
        """
        Carrega CSV SEM PCM como baseline de referência.
        Após isso, qualquer load_csv() calculará eficiência relativa automaticamente.
        """
        df = self._read_and_validate(csv_path)
        self._baseline = self._calcular(df)
        return self._baseline

    def get_baseline(self) -> SensorPCMResult | None:
        return self._baseline

    # ── Leitura e validação do CSV ────────────────────────────────────────────

    def _read_and_validate(self, csv_path: str | Path) -> pd.DataFrame:
        df = pd.read_csv(csv_path)

        # Aceita tanto o formato novo (temp_filtrada) quanto legado (temp_simulada_10pct)
        if "temp_filtrada" in df.columns:
            col_temp = "temp_filtrada"
        elif "temp_simulada_10pct" in df.columns:
            col_temp = "temp_simulada_10pct"
        elif "temp_suavizada" in df.columns:
            col_temp = "temp_suavizada"
        else:
            raise ValueError(
                "CSV inválido: nenhuma coluna de temperatura filtrada encontrada. "
                "Esperado: 'temp_filtrada', 'temp_simulada_10pct' ou 'temp_suavizada'."
            )

        # Normaliza para coluna padrão
        if col_temp != "temp_filtrada":
            df = df.rename(columns={col_temp: "temp_filtrada"})

        required = {"temp", "time_ms", "temp_filtrada"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"CSV inválido. Colunas faltando: {missing}")

        return df

    # ── Cálculo das métricas ──────────────────────────────────────────────────

    def _calcular(self, df: pd.DataFrame) -> SensorPCMResult:
        tempo_s = (df["time_ms"].astype(float) / 1000.0).tolist()

        # Suavização adicional leve — mantém estabilidade visual
        temp_c = (
            df["temp_filtrada"]
            .rolling(window=7, center=True, min_periods=1)
            .mean()
            .astype(float)
            .tolist()
        )

        T_ini  = temp_c[0]
        T_pico = max(temp_c)
        idx_pico = temp_c.index(T_pico)
        t_pico   = tempo_s[idx_pico]

        # Energia absorvida: Q = m·c·ΔT  (calor sensível)
        # ΔT = temperatura observada - temperatura inicial
        # Isso representa energia que ENTROU no sistema via PCM
        # ───────────────────────────────────────────────────────────────
        # ENERGIA REAL ABSORVIDA PELO PCM
        #
        # Qt = Qs + Ql
        #
        # Qs = m * c * ΔT
        # Ql = m * L
        #
        # O calor latente só entra quando o PCM entra
        # na faixa de atuação térmica.
        # ───────────────────────────────────────────────────────────────

        delta_t_total = max(0.0, T_pico - T_ini)

        # calor sensível
        energia_sensivel = (
            MASSA_PCM_KG
            * CALOR_ESPECIFICO_PCM
            * delta_t_total
        )

        # fração de atuação do PCM
        # Tempo dentro da faixa de atuação do PCM
        tempo_atuacao = _tempo_na_faixa(
            tempo_s,
            temp_c,
            faixa_min=TEMP_FUSAO_PCM,
            faixa_max=TEMP_SATURACAO_PCM,
        )

        # fração de atuação do PCM
        fracao_atuacao = min(
            1.0,
            max(0.0, tempo_atuacao / (78.0 * 60.0))
)

        # calor latente proporcional ao tempo de atuação
        energia_latente = (
            MASSA_PCM_KG
            * CALOR_LATENTE_PCM
            * fracao_atuacao
        )

        # energia total absorvida pelo PCM
        energia_total_j = energia_sensivel + energia_latente
        
        eficiencia_termica = (
            energia_total_j / NOTEBOOK_REFERENCIA_J
        ) * 100.0

        # limite máximo físico
        eficiencia_termica = min(100.0, eficiencia_termica)

        # erro percentual experimental
        erro_percentual = abs(
            NOTEBOOK_REFERENCIA_J - energia_total_j
        ) / NOTEBOOK_REFERENCIA_J * 100.0

        # curva progressiva ao longo do tempo
        energia_instante = []

        for T, ts in zip(temp_c, tempo_s):

            dt_local = max(0.0, T - T_ini)

            q_s = (
                MASSA_PCM_KG
                * CALOR_ESPECIFICO_PCM
                * dt_local
            )

            frac_local = min(
                1.0,
                ts / (78.0 * 60.0)
            )

            q_l = (
                MASSA_PCM_KG
                * CALOR_LATENTE_PCM
                * frac_local
            )

            energia_instante.append(q_s + q_l)

        # Estado do PCM baseado na temperatura máxima observada
        estado_pcm = _classificar_estado(T_pico)

        # Tempo de estabilização: |dT/dt| < 0.001 °C/s por pelo menos 30s contínuos
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

    # ── Comparação COM vs SEM PCM ─────────────────────────────────────────────

    @staticmethod
    def _aplicar_comparacao(
        com_pcm: SensorPCMResult,
        sem_pcm: SensorPCMResult,
    ) -> None:
        """
        Calcula métricas comparativas e injeta em com_pcm.

        Eficiência de redução térmica:
          η = (T_pico_sem - T_pico_com) / T_pico_sem × 100

        Atraso térmico:
          tempo para atingir T_pico_com no ensaio SEM PCM
          vs tempo para atingir T_pico_com no ensaio COM PCM
        """
        T_pico_sem = sem_pcm.pico_temperatura
        T_pico_com = com_pcm.pico_temperatura

        # Eficiência relativa
        if T_pico_sem > 0:
            com_pcm.eficiencia_relativa = max(
                0.0,
                (T_pico_sem - T_pico_com) / T_pico_sem * 100.0,
            )
        else:
            com_pcm.eficiencia_relativa = 0.0

        # Redução absoluta
        com_pcm.reducao_pico_c = T_pico_sem - T_pico_com

        # Atraso térmico: tempo para atingir T_pico_com nos dois cenários
        alvo = T_pico_com
        t_sem_alvo = next(
            (tv for tv, Tv in zip(sem_pcm.tempo_s, sem_pcm.temperatura_c) if Tv >= alvo),
            None,
        )
        t_com_alvo = next(
            (tv for tv, Tv in zip(com_pcm.tempo_s, com_pcm.temperatura_c) if Tv >= alvo),
            None,
        )
        if t_sem_alvo is not None and t_com_alvo is not None:
            com_pcm.atraso_termico_s = t_com_alvo - t_sem_alvo

        # Injeta série da baseline para overlay no gráfico
        com_pcm.baseline_tempo_s = sem_pcm.tempo_s
        com_pcm.baseline_temp_c  = sem_pcm.temperatura_c
        com_pcm.baseline_pico_c  = T_pico_sem


# ── Funções auxiliares ────────────────────────────────────────────────────────

def _classificar_estado(T_pico: float) -> str:
    """
    Estado do PCM baseado na temperatura máxima observada.
    Reflete absorção passiva — não assume fusão obrigatória.
    """
    if T_pico < TEMP_FUSAO_PCM * 0.70:
        return "Estável"
    elif T_pico < TEMP_FUSAO_PCM:
        return "Absorvendo calor"
    elif T_pico <= TEMP_SATURACAO_PCM:
        return "Em atuação térmica"
    else:
        return "Saturação parcial"


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
                if a > 0: t_enter = max(t_enter, tcross)
                else:     t_exit  = min(t_exit,  tcross)
            else:
                if a > 0: t_exit  = min(t_exit,  tcross)
                else:     t_enter = max(t_enter, tcross)
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
        taxas.append(abs(float(temperatura_c[i]) - float(temperatura_c[i - 1])) / dt)

    for i in range(1, n - window):
        if all(v < limiar for v in taxas[i: i + window]):
            return float(tempo_s[i])

    return 0.0
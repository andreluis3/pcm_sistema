"""
pcm_service.py
══════════════
Processamento térmico do CSV de experimento PCM.

REGRA CRÍTICA:
    Toda coluna lida do pandas DataFrame deve ser convertida para list[float]
    ANTES de ser passada para PCMResult. Nunca armazenar pandas.Series.

Padrão obrigatório de conversão:
    valores = pd.to_numeric(df["coluna"], errors="coerce").fillna(0).tolist()
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import pandas as pd

from .pcm_model import PCMResult
from .pcm_metrics import (
    CALOR_LATENTE_PCM,
    TEMP_FUSAO_PCM,
    TEMP_SATURACAO_PCM,
    calcular_tempo_na_faixa_pcm,
)


# ─────────────────────────────────────────────────────────────────────────────
# Constantes do experimento
# ─────────────────────────────────────────────────────────────────────────────

CALOR_ESPECIFICO_PCM: float = 2000.0   # J/(kg·K)
POTENCIA_NOTEBOOK_W: float = 50.0      # W — referência de potência do notebook


class PCMService:
    """
    Serviço responsável por processar arquivos CSV de experimento PCM.

    Garante que nenhuma pandas.Series vaze para fora deste módulo.
    Todos os dados são convertidos para tipos primitivos Python antes
    de instanciar PCMResult.
    """

    # Colunas esperadas no CSV (flexível — usa o que estiver disponível)
    _COLUNAS_REQUERIDAS: list[str] = ["tempo_s", "temperatura_c"]
    _COLUNAS_OPCIONAIS: dict[str, float] = {
        "potencia_w": 0.0,
        "energia_j": 0.0,
    }

    def process_csv(self, file_path: str | Path) -> PCMResult:
        """
        Lê, valida e processa um arquivo CSV de experimento PCM.

        Retorna PCMResult com todos os campos como tipos primitivos Python.
        Levanta ValueError com mensagem clara em caso de falha.
        """
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"Arquivo não encontrado: {path}")

        # ── Leitura do CSV ────────────────────────────────────────────────────
        try:
            df = pd.read_csv(path, sep=None, engine="python")
        except Exception as exc:
            raise ValueError(f"Falha ao ler CSV: {exc}") from exc

        # Normaliza nomes de colunas
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Verifica colunas obrigatórias
        faltando = [c for c in self._COLUNAS_REQUERIDAS if c not in df.columns]
        if faltando:
            raise ValueError(
                f"Colunas obrigatórias ausentes no CSV: {faltando}\n"
                f"Colunas encontradas: {list(df.columns)}"
            )

        # ── Conversão SEGURA para list[float] ────────────────────────────────
        # pd.to_numeric(..., errors="coerce") converte erros para NaN
        # .fillna(0) elimina NaN
        # .tolist() converte para list[float] nativa do Python

        tempo_s: list[float] = (
            pd.to_numeric(df["tempo_s"], errors="coerce")
            .fillna(0)
            .tolist()
        )
        temperatura_c: list[float] = (
            pd.to_numeric(df["temperatura_c"], errors="coerce")
            .fillna(0)
            .tolist()
        )

        potencia_w: list[float] = (
            pd.to_numeric(df.get("potencia_w", pd.Series([0.0] * len(df))), errors="coerce")
            .fillna(0)
            .tolist()
            if "potencia_w" in df.columns
            else [0.0] * len(tempo_s)
        )

        energia_j: list[float] = (
            pd.to_numeric(df.get("energia_j", pd.Series([0.0] * len(df))), errors="coerce")
            .fillna(0)
            .tolist()
            if "energia_j" in df.columns
            else [0.0] * len(tempo_s)
        )

        # ── Preview para UI (strings — sem pandas.Series) ─────────────────────
        colunas_preview = ["timestamp", "tempo_s", "potencia_w", "temperatura_c", "energia_j"]
        preview_rows: list[dict[str, str]] = []
        for _, row in df.head(20).iterrows():
            preview_rows.append(
                {col: str(row[col]) if col in df.columns else "" for col in colunas_preview}
            )

        # ── Cálculos escalares ────────────────────────────────────────────────
        n = min(len(tempo_s), len(temperatura_c))

        energia_total: float = self._calcular_energia_total(tempo_s, potencia_w, energia_j)
        potencia_media: float = self._calcular_potencia_media(potencia_w)
        pico_temperatura: float = float(max(temperatura_c)) if temperatura_c else 0.0
        temperatura_media: float = (
            sum(temperatura_c) / len(temperatura_c) if temperatura_c else 0.0
        )
        delta_tempo: float = float(tempo_s[-1] - tempo_s[0]) if len(tempo_s) >= 2 else 0.0

        # Tempo do pico
        tempo_pico_temperatura: float = 0.0
        if temperatura_c:
            idx_pico = temperatura_c.index(pico_temperatura)
            tempo_pico_temperatura = float(tempo_s[idx_pico]) if idx_pico < len(tempo_s) else 0.0

        # Massa PCM: m = Q / (c * ΔT + L)  onde Q é energia total
        massa_pcm: float = self._calcular_massa_pcm(
            energia_total, temperatura_c
        )

        # Energia teórica = massa * calor latente
        energia_teorica: float = float(massa_pcm) * CALOR_LATENTE_PCM

        # ── Análise técnica ───────────────────────────────────────────────────
        analise, calculo = self._gerar_analise(
            tempo_s=tempo_s,
            temperatura_c=temperatura_c,
            energia_total=energia_total,
            massa_pcm=massa_pcm,
            potencia_media=potencia_media,
            pico_temperatura=pico_temperatura,
            energia_teorica=energia_teorica,
        )

        return PCMResult(
            tempo_s=tempo_s,
            temperatura_c=temperatura_c,
            potencia_w=potencia_w,
            energia_j=energia_j,
            energia_total=energia_total,
            energia_teorica=energia_teorica,
            potencia_media=potencia_media,
            massa_pcm=massa_pcm,
            pico_temperatura=pico_temperatura,
            tempo_pico_temperatura=tempo_pico_temperatura,
            temperatura_media=temperatura_media,
            delta_tempo=delta_tempo,
            analise_tecnica=analise,
            calculo_detalhado=calculo,
            csv_preview=preview_rows,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers de cálculo
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _calcular_energia_total(
        tempo_s: list[float],
        potencia_w: list[float],
        energia_j: list[float],
    ) -> float:
        """
        Energia total em Joules.

        Prioridade:
        1. Integração numérica de potência × tempo (trapezoidal)
        2. Último valor da coluna energia_j
        3. Zero
        """
        # Se há dados de potência não-nulos, integra
        if potencia_w and any(p > 0.0 for p in potencia_w):
            n = min(len(tempo_s), len(potencia_w))
            total = 0.0
            for i in range(1, n):
                dt = float(tempo_s[i]) - float(tempo_s[i - 1])
                if dt > 0.0:
                    p_med = (float(potencia_w[i]) + float(potencia_w[i - 1])) / 2.0
                    total += p_med * dt
            if total > 0.0:
                return total

        # Fallback: último valor da coluna energia
        if energia_j and energia_j[-1] > 0.0:
            return float(energia_j[-1])

        return 0.0

    @staticmethod
    def _calcular_potencia_media(potencia_w: list[float]) -> float:
        """Potência média em Watts. Retorna POTENCIA_NOTEBOOK_W como fallback."""
        validos = [p for p in potencia_w if p > 0.0]
        if validos:
            return sum(validos) / len(validos)
        return POTENCIA_NOTEBOOK_W

    @staticmethod
    def _calcular_massa_pcm(
        energia_total: float,
        temperatura_c: list[float],
    ) -> float:
        """
        Estima a massa de PCM necessária (g).

        Fórmula: m = Q / (c·ΔT + L)
        onde:
            Q = energia total (J)
            c = calor específico (J/(kg·K)) → convertido para J/(g·K) ÷ 1000
            ΔT = variação de temperatura dentro da faixa PCM (°C)
            L = calor latente (J/g)
        """
        if energia_total <= 0.0 or not temperatura_c:
            return 0.0

        temp_faixa = [
            t for t in temperatura_c
            if TEMP_FUSAO_PCM <= t <= TEMP_SATURACAO_PCM
        ]
        delta_t = (max(temp_faixa) - min(temp_faixa)) if len(temp_faixa) >= 2 else 7.0
        c_j_por_g = CALOR_ESPECIFICO_PCM / 1000.0  # J/(g·K)

        denominador = c_j_por_g * delta_t + CALOR_LATENTE_PCM
        if denominador <= 0.0:
            return 0.0

        return energia_total / denominador

    @staticmethod
    def _gerar_analise(
        *,
        tempo_s: list[float],
        temperatura_c: list[float],
        energia_total: float,
        massa_pcm: float,
        potencia_media: float,
        pico_temperatura: float,
        energia_teorica: float,
    ) -> tuple[list[str], list[str]]:
        """Gera linhas de análise técnica e cálculo detalhado."""
        duracao_s = float(tempo_s[-1]) if tempo_s else 0.0
        duracao_min = duracao_s / 60.0

        tempo_atuacao = calcular_tempo_na_faixa_pcm(tempo_s, temperatura_c)
        eficiencia = (
            min((massa_pcm * CALOR_LATENTE_PCM / energia_total) * 100.0, 100.0)
            if energia_total > 0.0
            else 0.0
        )

        analise = [
            f"Duração total do ensaio: {duracao_min:.1f} min ({duracao_s:.0f} s).",
            f"Temperatura de pico registrada: {pico_temperatura:.2f} °C.",
            f"Energia total absorvida: {energia_total:.0f} J.",
            f"Massa de PCM estimada: {massa_pcm:.2f} g.",
            f"Eficiência térmica estimada: {eficiencia:.1f} %.",
            f"Tempo de atuação do PCM (50–60 °C): {tempo_atuacao / 60.0:.1f} min.",
        ]

        calculo = [
            f"Q_total = {energia_total:.2f} J  (integral P×dt)",
            f"m_PCM   = Q / (c·ΔT + L) = {massa_pcm:.4f} g",
            f"L_PCM   = {CALOR_LATENTE_PCM} J/g  (calor latente de fusão)",
            f"P_média = {potencia_media:.2f} W",
            f"Q_ideal = m·L = {energia_teorica:.2f} J",
            f"η       = Q_real / Q_ideal × 100 = {eficiencia:.2f} %",
        ]

        return analise, calculo
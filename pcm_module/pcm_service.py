"""
pcm_service.py
══════════════
Importação e saneamento de CSV — única responsabilidade.

REGRA CRÍTICA:
    Toda coluna pandas → list[float] ANTES de passar ao PCMResult.
    Padrão: pd.to_numeric(df["col"], errors="coerce").fillna(0).tolist()

Delegações:
    cálculos físicos → pcm_metrics.py
    persistência     → pcm_repository.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .pcm_model import PCMResult
from .pcm_metrics import (
    CALOR_ESPECIFICO_PCM,
    CALOR_LATENTE_PCM,
    MASSA_PCM_KG,
    POTENCIA_NOTEBOOK_W,
    TEMP_FUSAO_PCM,
    TEMP_SATURACAO_PCM,
    calcular_energia_notebook,
    calcular_energia_absorvida_pcm,
    calcular_eficiencia,
    calcular_tempo_equivalente,
    calcular_energia_acumulada_notebook,
    calcular_energia_acumulada_pcm,
    calcular_tempo_na_faixa_pcm,
    formatar_energia,
)


class PCMService:
    """
    Lê CSV, sanitiza com pandas e entrega PCMResult com tipos primitivos.

    Nenhuma pandas.Series vaza para fora deste módulo.
    """

    _COLUNAS_OBRIGATORIAS = ["tempo_s", "temperatura_c"]

    def process_csv(self, file_path: str | Path) -> PCMResult:
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"Arquivo não encontrado: {path}")

        try:
            df = pd.read_csv(path, sep=None, engine="python")
        except Exception as exc:
            raise ValueError(f"Falha ao ler CSV: {exc}") from exc

        # Normaliza colunas
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        faltando = [c for c in self._COLUNAS_OBRIGATORIAS if c not in df.columns]
        if faltando:
            raise ValueError(
                f"Colunas ausentes: {faltando}\nEncontradas: {list(df.columns)}"
            )

        # ── Conversão segura — NUNCA armazenar Series ─────────────────────────
        def _to_float_list(col: str, fallback: float = 0.0) -> list[float]:
            if col not in df.columns:
                return [fallback] * len(df)
            return pd.to_numeric(df[col], errors="coerce").fillna(fallback).tolist()

        tempo_s       = _to_float_list("tempo_s")
        temperatura_c = _to_float_list("temperatura_c")
        potencia_w    = _to_float_list("potencia_w", fallback=POTENCIA_NOTEBOOK_W)
        energia_j     = _to_float_list("energia_j")

        # ── Preview (strings — sem Series) ────────────────────────────────────
        cols_prev = ["timestamp", "tempo_s", "potencia_w", "temperatura_c", "energia_j"]
        preview: list[dict[str, str]] = [
            {c: str(row[c]) if c in df.columns else "" for c in cols_prev}
            for _, row in df.head(20).iterrows()
        ]

        # ── Escalares ─────────────────────────────────────────────────────────
        pico_temperatura = float(max(temperatura_c)) if temperatura_c else 0.0
        temperatura_media = sum(temperatura_c) / len(temperatura_c) if temperatura_c else 0.0
        delta_tempo = float(tempo_s[-1] - tempo_s[0]) if len(tempo_s) >= 2 else 0.0
        temperatura_inicial = float(temperatura_c[0]) if temperatura_c else 0.0
        temperatura_final   = float(temperatura_c[-1]) if temperatura_c else 0.0

        idx_pico = temperatura_c.index(pico_temperatura) if temperatura_c else 0
        tempo_pico = float(tempo_s[idx_pico]) if idx_pico < len(tempo_s) else 0.0

        potencia_media_val = (
            sum(p for p in potencia_w if p > 0) / max(1, sum(1 for p in potencia_w if p > 0))
            if any(p > 0 for p in potencia_w)
            else POTENCIA_NOTEBOOK_W
        )

        # ── Cálculos físicos — delegados ao pcm_metrics ───────────────────────
        q_notebook = calcular_energia_notebook(tempo_s, potencia_w)
        q_pcm      = calcular_energia_absorvida_pcm(
            temperatura_c,
            massa_kg=MASSA_PCM_KG,
            calor_especifico=CALOR_ESPECIFICO_PCM,
            temp_inicial_c=temperatura_inicial,
            temp_final_c=temperatura_final,
        )
        eficiencia = calcular_eficiencia(q_pcm, q_notebook)
        tempo_eq   = calcular_tempo_equivalente(q_pcm)

        # Massa PCM estimada (legado)
        delta_t_faixa = max(
            (max((t for t in temperatura_c if TEMP_FUSAO_PCM <= t <= TEMP_SATURACAO_PCM),
                 default=temperatura_final)
             - min((t for t in temperatura_c if TEMP_FUSAO_PCM <= t <= TEMP_SATURACAO_PCM),
                   default=temperatura_inicial)),
            temperatura_final - temperatura_inicial,
            1.0,
        )
        c_j_g = CALOR_ESPECIFICO_PCM / 1000.0
        denom = c_j_g * delta_t_faixa + CALOR_LATENTE_PCM / 1000.0
        massa_pcm_g = (q_notebook / denom) if denom > 0 else 0.0

        # Séries acumuladas
        energia_acum_nb  = calcular_energia_acumulada_notebook(tempo_s, potencia_w)
        energia_acum_pcm = calcular_energia_acumulada_pcm(
            tempo_s, temperatura_c,
            massa_kg=MASSA_PCM_KG,
            calor_especifico=CALOR_ESPECIFICO_PCM,
        )

        # ── Análise textual ────────────────────────────────────────────────────
        analise, calculo = self._gerar_analise(
            q_notebook=q_notebook,
            q_pcm=q_pcm,
            eficiencia=eficiencia,
            tempo_eq=tempo_eq,
            pico_temperatura=pico_temperatura,
            temperatura_inicial=temperatura_inicial,
            temperatura_final=temperatura_final,
            duracao_s=delta_tempo,
            massa_pcm_kg=MASSA_PCM_KG,
        )

        return PCMResult(
            tempo_s=tempo_s,
            temperatura_c=temperatura_c,
            potencia_w=potencia_w,
            energia_j=energia_j,
            energia_acum_notebook=energia_acum_nb,
            energia_acum_pcm=energia_acum_pcm,
            q_notebook_j=q_notebook,
            q_pcm_j=q_pcm,
            eficiencia=eficiencia,
            tempo_eq_s=tempo_eq,
            energia_total=q_notebook,
            energia_teorica=q_pcm,
            potencia_media=potencia_media_val,
            massa_pcm=massa_pcm_g,
            pico_temperatura=pico_temperatura,
            tempo_pico_temperatura=tempo_pico,
            temperatura_media=temperatura_media,
            delta_tempo=delta_tempo,
            temperatura_inicial=temperatura_inicial,
            temperatura_final=temperatura_final,
            analise_tecnica=analise,
            calculo_detalhado=calculo,
            csv_preview=preview,
        )

    @staticmethod
    def _gerar_analise(
        *,
        q_notebook: float,
        q_pcm: float,
        eficiencia: float,
        tempo_eq: float,
        pico_temperatura: float,
        temperatura_inicial: float,
        temperatura_final: float,
        duracao_s: float,
        massa_pcm_kg: float,
    ) -> tuple[list[str], list[str]]:

        delta_t = temperatura_final - temperatura_inicial

        analise = [
            f"Energia gerada pelo notebook: {formatar_energia(q_notebook)}.",
            f"Energia absorvida pelo PCM:   {formatar_energia(q_pcm)}.",
            f"Eficiência térmica:           {eficiencia:.2f} %.",
            f"Tempo equivalente de atuação: {tempo_eq:.1f} s ({tempo_eq/60:.1f} min).",
            f"ΔT do PCM: {delta_t:.2f} °C  ({temperatura_inicial:.1f} → {temperatura_final:.1f} °C).",
            f"Temperatura de pico:          {pico_temperatura:.2f} °C.",
        ]

        calculo = [
            f"Q_notebook = P × t = {POTENCIA_NOTEBOOK_W} W × {duracao_s:.0f} s = {formatar_energia(q_notebook)}",
            f"Q_pcm      = m · c · ΔT = {massa_pcm_kg} kg × {CALOR_ESPECIFICO_PCM} J/(kg·K) × {delta_t:.2f} K = {formatar_energia(q_pcm)}",
            f"η          = Q_pcm / Q_notebook × 100 = {eficiencia:.4f} %",
            f"t_eq       = Q_pcm / P = {q_pcm:.1f} / {POTENCIA_NOTEBOOK_W} = {tempo_eq:.1f} s",
        ]

        return analise, calculo
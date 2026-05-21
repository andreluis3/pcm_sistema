"""
pcm_module
══════════
Módulo de análise térmica com PCM (Phase Change Material).

Exporta as classes e funções públicas do sistema.
"""
from __future__ import annotations

# ── Modelos de dados ──────────────────────────────────────────────────────────
from .pcm_model import PCMResult

# ── Serviço de processamento ──────────────────────────────────────────────────
from .pcm_service import PCMService

# ── Repositório ───────────────────────────────────────────────────────────────
from .pcm_repository import PCMRepository

# ── Métricas ─────────────────────────────────────────────────────────────────
from .pcm_metrics import (
    TEMP_FUSAO_PCM,
    TEMP_SATURACAO_PCM,
    CALOR_ESPECIFICO_PCM,
    CALOR_LATENTE_PCM,
    calcular_dT_dt,
    calcular_tempo_na_faixa_pcm,
    calcular_estabilizacao,
    calcular_metricas_experimento,
    formatar_tempo_min_seg,
    formatar_tempo_min,
    smooth_series,
)

# ── Componentes de UI ─────────────────────────────────────────────────────────
from pcm_module.pcm_screen import PCMCalcScreen
from pcm_module.pcm_kpi import PCMKPIFrame
from pcm_module.pcm_charts import PCMChartFrame
from pcm_module.pcm_analysis import PCMAnalysisFrame
from pcm_module.pcm_import import PCMImportFrame

__all__ = [
    # Modelos
    "PCMResult",
    # Serviços
    "PCMService",
    "PCMRepository",
    # Constantes
    "TEMP_FUSAO_PCM",
    "TEMP_SATURACAO_PCM",
    "CALOR_ESPECIFICO_PCM",
    "CALOR_LATENTE_PCM",
    # Métricas
    "calcular_dT_dt",
    "calcular_tempo_na_faixa_pcm",
    "calcular_estabilizacao",
    "calcular_metricas_experimento",
    "formatar_tempo_min_seg",
    "formatar_tempo_min",
    "smooth_series",
    # UI
    "PCMCalcScreen",
    "PCMKPIFrame",
    "PCMChartFrame",
    "PCMAnalysisFrame",
    "PCMImportFrame",
]
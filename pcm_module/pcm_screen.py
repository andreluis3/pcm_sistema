"""
pcm_screen.py
═════════════
Tela principal do Dashboard PCM.

Responsabilidade: montar layout e conectar componentes.
SEM cálculos — delegados ao pcm_metrics.
SEM gráficos diretos — delegados ao pcm_charts.
SEM código do sensor — vive em sensor_pcm_screen.py.
"""
from __future__ import annotations

import customtkinter as ctk

from .pcm_model import PCMResult
from .pcm_metrics import calcular_metricas_experimento
from .pcm_import import PCMImportFrame
from .pcm_kpi import PCMKPIFrame
from .pcm_charts import PCMChartFrame
from .pcm_analysis import PCMAnalysisFrame
from ui_styles import BG_COLOR, PANEL_COLOR, BORDER_COLOR


class PCMCalcScreen(ctk.CTkFrame):
    """
    Layout do Dashboard Térmico PCM.

        row 0 — PCMImportFrame   (header + botão CSV)
        row 1 — PCMKPIFrame      (8 cards físicos)
        row 2 — PCMChartFrame    (4 painéis: notebook + PCM)
        row 3 — PCMAnalysisFrame (análise textual + preview)
    """

    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=BG_COLOR)
        self._current_result: PCMResult | None = None
        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_COLOR,
            scrollbar_button_color="#0F172A",
            scrollbar_button_hover_color=BORDER_COLOR,
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        scroll.grid_columnconfigure(0, weight=1)

        self._import_frame = PCMImportFrame(scroll, on_result=self._on_csv_imported)
        self._import_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(0, 16))

        self._kpi_frame = PCMKPIFrame(scroll)
        self._kpi_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))

        self._chart_frame = PCMChartFrame(scroll)
        self._chart_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 16))

        self._analysis_frame = PCMAnalysisFrame(scroll)
        self._analysis_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 24))

    def _on_csv_imported(self, result: PCMResult) -> None:
        self._current_result = result
        self._update_dashboard(result)

    def _update_dashboard(self, result: PCMResult) -> None:
        """
        Propaga PCMResult para todos os componentes.
        Toda a matemática já está em result (calculada pelo PCMService).
        """
        # Métricas derivadas (duração, delta_t, taxa) — calculadas aqui uma vez
        metricas = calcular_metricas_experimento(
            tempo_s=result.tempo_s,
            temperatura_c=result.temperatura_c,
            energia_total=result.q_notebook_j,
            massa_pcm=result.massa_pcm,
            energia_teorica=result.q_pcm_j,
            pico_temperatura=result.pico_temperatura,
            tempo_pico_temperatura=result.tempo_pico_temperatura,
            potencia_media=result.potencia_media,
            delta_tempo=result.delta_tempo,
            temperatura_media=result.temperatura_media,
            potencia_w=result.potencia_w,
        )

        # KPIs — apenas despacha valores já calculados
        self._kpi_frame.update_kpis(
            q_notebook_j=result.q_notebook_j,
            q_pcm_j=result.q_pcm_j,
            eficiencia=result.eficiencia,
            tempo_eq_s=result.tempo_eq_s,
            duracao_min=metricas.get("duracao_min"),
            massa_pcm_g=result.massa_pcm,
            delta_t_c=float(metricas.get("delta_t_c") or 0.0),
            potencia_media=result.potencia_media,
        )

        # Gráficos — recebe séries pré-calculadas
        self._chart_frame.render_charts(
            tempo_s=result.tempo_s,
            temperatura_c=result.temperatura_c,
            energia_acum_notebook=result.energia_acum_notebook,
            energia_acum_pcm=result.energia_acum_pcm,
            pico_temperatura=result.pico_temperatura,
            tempo_pico_s=result.tempo_pico_temperatura,
            q_notebook_j=result.q_notebook_j,
            q_pcm_j=result.q_pcm_j,
            eficiencia=result.eficiencia,
            tempo_eq_s=result.tempo_eq_s,
        )

        # Análise textual
        self._analysis_frame.update(result)
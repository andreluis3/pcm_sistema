"""
pcm_charts.py
═════════════
Gráficos do experimento PCM — dois painéis separados fisicamente:

    Painel superior  → Notebook: temperatura + energia acumulada gerada
    Painel inferior  → PCM:      temperatura + energia acumulada absorvida

Sem cálculos aqui — recebe dados já processados do pcm_metrics.
Sem código do sensor — separação total.
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from ui_styles import style_ax_dark, PANEL_COLOR, CARD_COLOR, BORDER_COLOR, TEXT_PRIMARY, TEXT_SECONDARY

from .pcm_metrics import (
    TEMP_FUSAO_PCM,
    TEMP_SATURACAO_PCM,
    formatar_tempo_min_seg,
    smooth_series,
)

# ── Paleta do gráfico PCM ──────────────────────────────────────────────────
COLOR_NOTEBOOK_TEMP   = "#F97316"   # laranja — temperatura do notebook
COLOR_NOTEBOOK_ENERGY = "#FB923C"   # laranja claro — energia gerada
COLOR_PCM_TEMP        = "#60A5FA"   # azul — temperatura do PCM
COLOR_PCM_ENERGY      = "#34D399"   # verde esmeralda — energia absorvida
COLOR_FUSAO_BAND      = "#A78BFA"   # roxo — faixa de fusão
COLOR_PICO            = "#FFD700"   # dourado — marcador de pico


def _style(ax) -> None:
    style_ax_dark(
        ax,
        card_color=CARD_COLOR,
        border_color=BORDER_COLOR,
        text_color=TEXT_SECONDARY,
    )


class PCMChartFrame(ctk.CTkFrame):
    """
    Dois gráficos sobrepostos verticalmente:
        ax_top    → Notebook  (temperatura + energia gerada)
        ax_bottom → PCM       (temperatura + energia absorvida)

    Recebe apenas list[float] — nunca pandas.Series.
    """

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._canvases: list[FigureCanvasTkAgg] = []
        self._render_placeholder()

        # ── API pública ───────────────────────────────────────────────────────────
    def render_charts(
        self,
        *,
        tempo_s: list[float],
        temperatura_c: list[float],
        pico_temperatura: float,
        tempo_pico_s: float,
    ) -> None:

        self._clear()

        fig = Figure(figsize=(18.0, 8.5), dpi=110)
        fig.patch.set_facecolor(PANEL_COLOR)

        ax = fig.add_subplot(111)

        _style(ax)

        t_min = [v / 60.0 for v in tempo_s]
        T_smooth = smooth_series(temperatura_c, window=9)

        self._plot_temperatura_notebook(
            ax,
            t_min,
            T_smooth,
            pico_temperatura,
            tempo_pico_s
        )

        self._finalize(fig)

    def render_placeholder(self) -> None:
        self._render_placeholder()

        # ── Plots individuais ─────────────────────────────────────────────────────
    def _plot_temperatura_notebook(
        self,
        ax,
        t_min,
        T_smooth,
        pico,
        tempo_pico_s
    ) -> None:

        ax.set_title(
            "Temperatura do Notebook ao Longo do Tempo",
            color=TEXT_PRIMARY,
            fontsize=16,
            fontweight="bold",
            pad=14
        )

        if not T_smooth:
            return

        # Faixa de fusão do PCM
        ax.axhspan(
            TEMP_FUSAO_PCM,
            TEMP_SATURACAO_PCM,
            color=COLOR_FUSAO_BAND,
            alpha=0.10,
            zorder=1,
            label=f"Fusão PCM ({TEMP_FUSAO_PCM:.0f}–{TEMP_SATURACAO_PCM:.0f} °C)"
        )

        # Linha principal
        ax.plot(
            t_min,
            T_smooth,
            color=COLOR_NOTEBOOK_TEMP,
            linewidth=3.2,
            alpha=0.95,
            label="Temperatura Notebook",
            zorder=5
        )

        # Área preenchida
        ax.fill_between(
            t_min,
            T_smooth,
            min(T_smooth),
            color=COLOR_NOTEBOOK_TEMP,
            alpha=0.12,
            zorder=2
        )

        # Pico
        ax.scatter(
            [tempo_pico_s / 60.0],
            [pico],
            color=COLOR_PICO,
            edgecolors="white",
            s=180,
            marker="o",
            zorder=8
        )

        ax.annotate(
            f"{pico:.1f} °C",
            xy=(tempo_pico_s / 60.0, pico),
            xytext=(10, 12),
            textcoords="offset points",
            fontsize=10,
            color=TEXT_PRIMARY,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor=CARD_COLOR,
                edgecolor=COLOR_PICO,
                alpha=0.95
            )
        )

        ax.set_xlabel(
            "Tempo (min)",
            color=TEXT_PRIMARY,
            fontsize=11
        )

        ax.set_ylabel(
            "Temperatura (°C)",
            color=TEXT_PRIMARY,
            fontsize=11
        )

        ax.legend(
            fontsize=10,
            facecolor=CARD_COLOR,
            edgecolor=BORDER_COLOR,
            labelcolor=TEXT_PRIMARY
        )


    def _render_placeholder(self) -> None:
        self._clear()
        fig = Figure(figsize=(18.0, 8.5), dpi=110)
        fig.patch.set_facecolor(PANEL_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD_COLOR)
        ax.text(0.5, 0.5,
                "Importe um CSV para ver os gráficos de Temperatura e Energia.",
                ha="center", va="center", fontsize=14,
                color=TEXT_SECONDARY, style="italic")
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ["top", "right", "bottom", "left"]:
            ax.spines[side].set_color(BORDER_COLOR)
        self._finalize(fig)

    def _finalize(self, fig: Figure) -> None:
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self._canvases.append(canvas)

    def _clear(self) -> None:
        for c in self._canvases:
            try:
                w = c.get_tk_widget()
                if w.winfo_exists():
                    w.destroy()
            except Exception:
                pass
        self._canvases.clear()

    def destroy(self) -> None:
        self._clear()
        super().destroy()
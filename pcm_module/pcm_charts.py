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
        energia_acum_notebook: list[float],
        energia_acum_pcm: list[float],
        pico_temperatura: float,
        tempo_pico_s: float,
        q_notebook_j: float,
        q_pcm_j: float,
        eficiencia: float,
        tempo_eq_s: float,
    ) -> None:
        """
        Renderiza os dois painéis de gráfico.

        Painel superior  — Notebook: temperatura + energia gerada acumulada
        Painel inferior  — PCM:      temperatura + energia absorvida acumulada
        """
        self._clear()

        fig = Figure(figsize=(13.0, 10.0), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)

        gs = fig.add_gridspec(
            2, 2,
            hspace=0.38,
            wspace=0.32,
            left=0.07, right=0.97,
            top=0.94, bottom=0.07,
        )

        t_min = [v / 60.0 for v in tempo_s]
        T_smooth = smooth_series(temperatura_c, window=9)

        # Energias suavizadas (para visualização)
        E_nb_s  = smooth_series(energia_acum_notebook, window=9)
        E_pcm_s = smooth_series(energia_acum_pcm, window=9)

        # ── Painel superior esquerdo — Temperatura do notebook ─────────────────
        ax_nt = fig.add_subplot(gs[0, 0])
        _style(ax_nt)
        self._plot_temperatura_notebook(ax_nt, t_min, T_smooth, pico_temperatura, tempo_pico_s)

        # ── Painel superior direito — Energia gerada acumulada ─────────────────
        ax_ne = fig.add_subplot(gs[0, 1])
        _style(ax_ne)
        self._plot_energia_notebook(ax_ne, t_min, E_nb_s, q_notebook_j)

        # ── Painel inferior esquerdo — Temperatura do PCM ─────────────────────
        ax_pt = fig.add_subplot(gs[1, 0])
        _style(ax_pt)
        self._plot_temperatura_pcm(ax_pt, t_min, T_smooth)

        # ── Painel inferior direito — Energia absorvida acumulada ──────────────
        ax_pe = fig.add_subplot(gs[1, 1])
        _style(ax_pe)
        self._plot_energia_pcm(ax_pe, t_min, E_pcm_s, q_pcm_j, eficiencia, tempo_eq_s)

        self._finalize(fig)

    def render_placeholder(self) -> None:
        self._render_placeholder()

    # ── Plots individuais ─────────────────────────────────────────────────────

    def _plot_temperatura_notebook(
        self, ax, t_min, T_smooth, pico, tempo_pico_s
    ) -> None:
        ax.set_title("Notebook — Temperatura", color=TEXT_PRIMARY,
                     fontsize=13, fontweight="bold", pad=10)

        if not T_smooth:
            return

        ax.plot(t_min, T_smooth, color=COLOR_NOTEBOOK_TEMP,
                linewidth=2.8, alpha=0.95, label="T notebook", zorder=4)
        ax.fill_between(t_min, T_smooth, min(T_smooth),
                        color=COLOR_NOTEBOOK_TEMP, alpha=0.12, zorder=2)

        # Pico
        ax.scatter([tempo_pico_s / 60.0], [pico],
                   color=COLOR_PICO, edgecolors="white", s=140,
                   marker="*", zorder=7,
                   label=f"Pico: {pico:.1f} °C")
        ax.axvline(tempo_pico_s / 60.0, color=COLOR_PICO,
                   linestyle=":", linewidth=1.6, alpha=0.7)

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel("Temperatura (°C)", color=TEXT_PRIMARY, fontsize=10)
        ax.legend(fontsize=9, facecolor=CARD_COLOR,
                  edgecolor=BORDER_COLOR, labelcolor=TEXT_PRIMARY)

    def _plot_energia_notebook(self, ax, t_min, E_nb, q_total) -> None:
        ax.set_title("Notebook — Energia Gerada Acumulada",
                     color=TEXT_PRIMARY, fontsize=13, fontweight="bold", pad=10)

        if not E_nb:
            return

        ax.plot(t_min, E_nb, color=COLOR_NOTEBOOK_ENERGY,
                linewidth=2.8, alpha=0.95, zorder=4)
        ax.fill_between(t_min, E_nb, 0,
                        color=COLOR_NOTEBOOK_ENERGY, alpha=0.18, zorder=2)

        # Anotação do total
        ax.text(0.97, 0.96,
                f"Q_notebook\n{q_total/1000:.2f} kJ",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=10, fontweight="bold", color=TEXT_PRIMARY,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD_COLOR,
                          edgecolor=COLOR_NOTEBOOK_ENERGY, alpha=0.9))

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel("Energia (J)", color=TEXT_PRIMARY, fontsize=10)

    def _plot_temperatura_pcm(self, ax, t_min, T_smooth) -> None:
        ax.set_title("PCM — Temperatura", color=TEXT_PRIMARY,
                     fontsize=13, fontweight="bold", pad=10)

        if not T_smooth:
            return

        # Faixa de fusão
        ax.axhspan(TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
                   color=COLOR_FUSAO_BAND, alpha=0.12, zorder=1,
                   label=f"Fusão {TEMP_FUSAO_PCM:.0f}–{TEMP_SATURACAO_PCM:.0f} °C")
        ax.axhline(TEMP_FUSAO_PCM, color=COLOR_FUSAO_BAND,
                   linewidth=0.8, linestyle="--", alpha=0.5, zorder=2)

        ax.plot(t_min, T_smooth, color=COLOR_PCM_TEMP,
                linewidth=2.8, alpha=0.95, label="T PCM", zorder=4)
        ax.fill_between(t_min, T_smooth, min(T_smooth),
                        color=COLOR_PCM_TEMP, alpha=0.12, zorder=2)

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel("Temperatura (°C)", color=TEXT_PRIMARY, fontsize=10)
        ax.legend(fontsize=9, facecolor=CARD_COLOR,
                  edgecolor=BORDER_COLOR, labelcolor=TEXT_PRIMARY)

    def _plot_energia_pcm(
        self, ax, t_min, E_pcm, q_pcm, eficiencia, tempo_eq_s
    ) -> None:
        ax.set_title("PCM — Energia Absorvida Acumulada",
                     color=TEXT_PRIMARY, fontsize=13, fontweight="bold", pad=10)

        if not E_pcm:
            return

        ax.plot(t_min, E_pcm, color=COLOR_PCM_ENERGY,
                linewidth=2.8, alpha=0.95, zorder=4)
        ax.fill_between(t_min, E_pcm, 0,
                        color=COLOR_PCM_ENERGY, alpha=0.18, zorder=2)

        # Anotação — mostra η e t_eq
        info = (
            f"Q_pcm = {q_pcm:.1f} J\n"
            f"η = {eficiencia:.2f} %\n"
            f"t_eq = {tempo_eq_s:.0f} s"
        )
        ax.text(0.03, 0.97, info,
                transform=ax.transAxes, ha="left", va="top",
                fontsize=10, fontweight="bold", color=TEXT_PRIMARY,
                bbox=dict(boxstyle="round,pad=0.45", facecolor=CARD_COLOR,
                          edgecolor=COLOR_PCM_ENERGY, alpha=0.92))

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel("Energia (J)", color=TEXT_PRIMARY, fontsize=10)

    # ── Internos ──────────────────────────────────────────────────────────────

    def _render_placeholder(self) -> None:
        self._clear()
        fig = Figure(figsize=(13.0, 9.0), dpi=100)
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
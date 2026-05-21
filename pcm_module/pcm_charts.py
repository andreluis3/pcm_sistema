"""
pcm_charts.py
═════════════
Renderização de gráficos do experimento PCM.

Responsabilidade única: criar e destruir FigureCanvasTkAgg com dados do CSV.

REGRAS:
    - Não contém código do sensor infravermelho.
    - Não faz cálculos de métricas — recebe dados já processados.
    - Não acessa pandas.Series — apenas list[float].
    - Protege todos os destroys com winfo_exists().
    - Evita acúmulo de FigureCanvasTkAgg (limpa antes de renderizar).
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .pcm_metrics import (
    TEMP_FUSAO_PCM,
    TEMP_SATURACAO_PCM,
    formatar_tempo_min_seg,
    smooth_series,
)


# ─────────────────────────────────────────────────────────────────────────────
# Paleta de cores do gráfico PCM
# ─────────────────────────────────────────────────────────────────────────────

COLOR_TEMP_LINE = "#FF5733"
COLOR_TEMP_MA = "#4FC3F7"
COLOR_PCM_BAND = "#00FF96"
COLOR_PICO = "#FFD700"
COLOR_TEMPO55 = "#00BFFF"

PANEL_COLOR = "#111827"
CARD_COLOR = "#0F172A"
BORDER_COLOR = "#334155"
TEXT_PRIMARY = "#F3F4F6"
TEXT_SECONDARY = "#9CA3AF"


def _style_ax(ax) -> None:
    """Aplica estilo científico escuro padronizado a um Axes."""
    ax.set_facecolor(CARD_COLOR)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=11, length=4, width=1.2)
    ax.tick_params(axis="x", pad=6)
    ax.tick_params(axis="y", pad=4)
    ax.grid(True, linestyle="--", linewidth=0.55, alpha=0.30, color="#475569")
    ax.minorticks_on()
    ax.grid(True, which="minor", linestyle=":", linewidth=0.3, alpha=0.15, color="#334155")
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["bottom", "left"]:
        ax.spines[side].set_color(BORDER_COLOR)
        ax.spines[side].set_linewidth(1.4)


# ─────────────────────────────────────────────────────────────────────────────
# PCMChartFrame
# ─────────────────────────────────────────────────────────────────────────────

class PCMChartFrame(ctk.CTkFrame):
    """
    Frame responsável exclusivamente pelos gráficos do experimento PCM (CSV).

    Dados de entrada: list[float] — NUNCA pandas.Series.
    Sem código do sensor infravermelho.
    """

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._canvases: list[FigureCanvasTkAgg] = []
        self._render_placeholder()

    # ── API pública ───────────────────────────────────────────────────────────

    def render_temperature_chart(
        self,
        *,
        tempo_s: list[float],
        temperatura_c: list[float],
        pico_temperatura: float,
        tempo_pico_s: float,
        tempo_55c_s: Optional[float],
        delta_t_c: float,
        tempo_atuacao_pcm_s: float,
    ) -> None:
        """
        Renderiza o gráfico de Temperatura × Tempo.

        Todos os parâmetros são tipos primitivos — list[float] ou float.
        """
        self._clear()

        fig = Figure(figsize=(12.0, 6.5), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)
        ax = fig.add_subplot(111)
        _style_ax(ax)

        ax.set_title(
            "Temperatura × Tempo — Resposta Térmica do PCM",
            color=TEXT_PRIMARY, fontsize=16, fontweight="bold", pad=16,
        )

        if not tempo_s or not temperatura_c:
            ax.text(
                0.5, 0.5,
                "Sem dados de temperatura para plotar.",
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=13, color=TEXT_SECONDARY,
            )
            self._finalize(fig)
            return

        min_temp = float(min(temperatura_c))

        # Faixa de atuação PCM
        ax.axhspan(
            TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
            color=COLOR_PCM_BAND, alpha=0.12,
            label=f"Faixa PCM {TEMP_FUSAO_PCM:.0f}–{TEMP_SATURACAO_PCM:.0f} °C",
            zorder=1,
        )

        # Preenchimento sob a curva
        ax.fill_between(
            tempo_s, temperatura_c, min_temp,
            color=COLOR_TEMP_LINE, alpha=0.15,
            label="Área absorvida", zorder=2,
        )

        # Linha de temperatura
        ax.plot(
            tempo_s, temperatura_c,
            color=COLOR_TEMP_LINE, linewidth=3.0, alpha=0.95,
            label="Temperatura", zorder=4,
        )

        # Média móvel
        t_smooth = smooth_series(temperatura_c, window=7)
        if t_smooth:
            ax.plot(
                tempo_s, t_smooth,
                color=COLOR_TEMP_MA, linewidth=2.2,
                linestyle="--", alpha=0.85,
                label="Média móvel (7 pts)", zorder=3,
            )

        # Marcador de pico
        ax.scatter(
            [tempo_pico_s], [pico_temperatura],
            color=COLOR_TEMP_LINE, edgecolors=COLOR_PICO,
            linewidths=2.0, s=150, marker="*",
            zorder=6, label=f"Pico: {pico_temperatura:.2f} °C",
        )

        # Linha vertical — tempo até 55 °C
        if tempo_55c_s is not None:
            ax.axvline(
                tempo_55c_s, color=COLOR_TEMPO55,
                linestyle=":", linewidth=2.0, alpha=0.8,
                label=f"Tempo até 55 °C: {formatar_tempo_min_seg(tempo_55c_s)}",
            )

        # Linha vertical — tempo do pico
        ax.axvline(
            tempo_pico_s, color=COLOR_PICO,
            linestyle=":", linewidth=2.0, alpha=0.8,
            label=f"Pico em: {formatar_tempo_min_seg(tempo_pico_s)}",
        )

        # Info box
        tempo_atuacao_min = float(tempo_atuacao_pcm_s) / 60.0
        info = f"ΔT = {delta_t_c:.2f} °C  |  Atuação PCM: {tempo_atuacao_min:.1f} min"
        ax.text(
            0.02, 0.95, info,
            transform=ax.transAxes, color="#E5E7EB",
            fontsize=11, fontweight="bold", va="top", zorder=10,
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=CARD_COLOR, edgecolor=BORDER_COLOR, alpha=0.8,
            ),
        )

        ax.set_xlabel("Tempo (s)", color=TEXT_PRIMARY, fontsize=12, fontweight="bold")
        ax.set_ylabel("Temperatura (°C)", color=TEXT_PRIMARY, fontsize=12, fontweight="bold")
        ax.legend(
            loc="lower right", fontsize=10,
            framealpha=0.95, facecolor=CARD_COLOR,
            edgecolor=BORDER_COLOR, labelcolor=TEXT_PRIMARY,
        )

        fig.subplots_adjust(left=0.08, right=0.95, top=0.93, bottom=0.10)
        self._finalize(fig)

    def render_placeholder(self) -> None:
        """Exibe placeholder quando não há dados."""
        self._render_placeholder()

    # ── Internos ──────────────────────────────────────────────────────────────

    def _render_placeholder(self) -> None:
        self._clear()
        fig = Figure(figsize=(11.5, 7.2), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD_COLOR)
        ax.text(
            0.5, 0.5,
            "Os gráficos aparecerão aqui após a importação do CSV.",
            ha="center", va="center",
            fontsize=15, color=TEXT_SECONDARY,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ["top", "right", "bottom", "left"]:
            ax.spines[side].set_color(BORDER_COLOR)
        self._finalize(fig)

    def _finalize(self, fig: Figure) -> None:
        """Adiciona figura ao frame e registra canvas."""
        canvas = FigureCanvasTkAgg(fig, master=self)
        widget = canvas.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self._canvases.append(canvas)

    def _clear(self) -> None:
        """
        Remove todos os canvas acumulados com proteção winfo_exists().

        Evita memory leak e múltiplos FigureCanvasTkAgg sobrepostos.
        """
        for canvas in self._canvases:
            try:
                widget = canvas.get_tk_widget()
                if widget.winfo_exists():
                    widget.destroy()
            except Exception:
                pass
        self._canvases.clear()

    def destroy(self) -> None:
        """Override seguro — limpa canvases antes de destruir o frame."""
        self._clear()
        super().destroy()
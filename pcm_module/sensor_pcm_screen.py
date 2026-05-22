"""
sensor_pcm_screen.py
════════════════════
Dashboard do sensor infravermelho — separado totalmente do PCMCalcScreen.

Usa ThermalCard de pcm_kpi.py para identidade visual unificada.
Sem duplicação de estilos.
"""
from __future__ import annotations

import os
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui_styles import (
    style_ax_dark,
    BG_COLOR, PANEL_COLOR, CARD_COLOR, BORDER_COLOR,
    TEXT_PRIMARY, TEXT_SECONDARY, SUCCESS_COLOR,
    SENSOR_ACCENT, SENSOR_FUSION, SENSOR_ENERGY,
    COLOR_WITH_PCM, COLOR_WITHOUT_PCM,
    THEME_COLORS,
)
from .pcm_kpi import ThermalCard   # componente visual compartilhado
from .pcm_metrics import (
    TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
    smooth_series,
    calcular_energia_absorvida_pcm,
    calcular_eficiencia,
    calcular_tempo_equivalente,
    calcular_energia_acumulada_pcm,
    calcular_dT_dt,
    calcular_estabilizacao,
    MASSA_PCM_KG, CALOR_ESPECIFICO_PCM, Q_NOTEBOOK_REF_J,
)

try:
    from .pcm_temperature_sensor import PCMTemperatureSensor, SensorPCMResult
    _SENSOR_OK = True
except ImportError:
    _SENSOR_OK = False
    PCMTemperatureSensor = None  # type: ignore
    SensorPCMResult = None       # type: ignore

COLOR_PICO = "#FFD700"

def _style(ax) -> None:
    style_ax_dark(ax, card_color=CARD_COLOR,
                  border_color=BORDER_COLOR, text_color=TEXT_SECONDARY)


# ─────────────────────────────────────────────────────────────────────────────
# SensorKPIFrame — usa ThermalCard (identidade visual compartilhada)
# ─────────────────────────────────────────────────────────────────────────────

_SENSOR_KPI_DEFS: list[tuple[str, str]] = [
    ("Temperatura Atual",
     "Temperatura mais recente registrada pelo sensor IR (°C)."),
    ("Energia Absorvida",
     "Q_pcm = m · c · ΔT  (J)  — calor sensível absorvido."),
    ("Eficiência Térmica",
     "η = Q_pcm / Q_notebook_ref × 100  (%).\nFração do calor do notebook desviada para o PCM."),
    ("Tempo Equivalente",
     "t_eq = Q_pcm / P_notebook  (s).\nPor quanto tempo o PCM poderia alimentar o notebook."),
    ("Estado do PCM",
     "Sólido (<53°C) / Em Fusão (53–60°C) / Saturado (>60°C)."),
    ("Tempo de Estabilização",
     "Instante em que |dT/dt| < 0,01 °C/s por 30 s contínuos."),
    ("ΔT do PCM",
     "Variação de temperatura: T_atual − T_inicial (°C)."),
    ("Calor Desviado",
     "Q_pcm — mesma energia absorvida, contexto de dissipação passiva."),
]

_SENSOR_ACCENT = SENSOR_ACCENT   # azul — identidade sensor


class SensorKPIFrame(ctk.CTkFrame):
    """8 KPI cards do sensor — usa ThermalCard, mesma identidade do PCM."""

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._cards: dict[str, ThermalCard] = {}
        for c in range(4):
            self.grid_columnconfigure(c, weight=1, uniform="skpi")
        for idx, (key, tip) in enumerate(_SENSOR_KPI_DEFS):
            card = ThermalCard(self, title=key, tooltip=tip,
                               accent_color=_SENSOR_ACCENT)
            row, col = divmod(idx, 4)
            card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            self._cards[key] = card

    def update_from_result(self, r) -> None:
        """
        Calcula e exibe métricas do sensor.
        Todos os cálculos delegados ao pcm_metrics — sem matemática aqui.
        """
        T_c = [float(v) for v in r.temperatura_c] if r.temperatura_c else []
        T_ini = float(r.temperatura_inicial)
        T_atual = float(T_c[-1]) if T_c else T_ini

        # Cálculos via pcm_metrics
        q_pcm = calcular_energia_absorvida_pcm(
            T_c, massa_kg=MASSA_PCM_KG,
            calor_especifico=CALOR_ESPECIFICO_PCM,
            temp_inicial_c=T_ini, temp_final_c=T_atual,
        )
        eta   = calcular_eficiencia(q_pcm, Q_NOTEBOOK_REF_J)
        t_eq  = calcular_tempo_equivalente(q_pcm)
        dT    = T_atual - T_ini

        # Estabilização
        t_s = [float(v) for v in r.tempo_s]
        deriv = calcular_dT_dt(t_s, T_c)
        t_estab = calcular_estabilizacao(t_s, deriv)

        # Estado
        if T_atual < TEMP_FUSAO_PCM:
            estado, cor = "PCM Sólido",    "#93C5FD"
        elif T_atual <= TEMP_SATURACAO_PCM:
            estado, cor = "PCM em Fusão",  "#FCD34D"
        else:
            estado, cor = "PCM Saturado",  "#F87171"

        def _s(key, text, *, color=TEXT_PRIMARY, sub=""):
            c = self._cards.get(key)
            if c:
                c.set_value(text, color=color)
                if sub:
                    c.set_sub(sub)

        _s("Temperatura Atual",   f"{T_atual:.1f} °C")
        _s("Energia Absorvida",   f"{q_pcm:.1f} J",   sub="Q = m·c·ΔT")
        _s("Eficiência Térmica",  f"{eta:.2f} %",     sub="Q_pcm / Q_ref")
        _s("Tempo Equivalente",   f"{t_eq:.1f} s",    sub=f"≈ {t_eq/60:.1f} min")
        _s("Estado do PCM",       estado,              color=cor)
        _s("Tempo de Estabilização",
           f"{t_estab/60:.1f} min" if t_estab else "Não estabilizou")
        _s("ΔT do PCM",           f"{dT:.2f} °C")
        _s("Calor Desviado",      f"{q_pcm:.1f} J")


# ─────────────────────────────────────────────────────────────────────────────
# SensorChartFrame — gráficos do sensor
# ─────────────────────────────────────────────────────────────────────────────

class SensorChartFrame(ctk.CTkFrame):
    """Temperatura × Tempo  +  Energia Absorvida × Tempo do sensor IR."""

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._canvases: list[FigureCanvasTkAgg] = []
        self._placeholder()

    def render(self, r) -> None:
        self._clear()
        t_s  = [float(v) for v in r.tempo_s]
        T    = [float(v) for v in r.temperatura_c]
        T_sm = smooth_series(T, window=7)
        t_min = [v / 60.0 for v in t_s]

        # Energia acumulada via pcm_metrics
        E_pcm = calcular_energia_acumulada_pcm(
            t_s, T,
            massa_kg=MASSA_PCM_KG,
            calor_especifico=CALOR_ESPECIFICO_PCM,
        )
        E_sm = smooth_series(E_pcm, window=11)

        fig = Figure(figsize=(13.5, 9.5), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)
        gs = fig.add_gridspec(2, 1, height_ratios=[1.1, 0.9], hspace=0.36,
                              left=0.08, right=0.96, top=0.94, bottom=0.07)

        self._plot_temp(fig.add_subplot(gs[0]), t_min, T_sm, r)
        self._plot_energia(fig.add_subplot(gs[1]), t_min, E_sm, r)
        self._finalize(fig)

    def _plot_temp(self, ax, t_min, T_sm, r) -> None:
        _style(ax)
        ax.set_title("Sensor IR — Temperatura do PCM",
                     color=TEXT_PRIMARY, fontsize=15, fontweight="bold", pad=14)

        ax.axhspan(TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
                   color=SENSOR_FUSION, alpha=0.10, zorder=1,
                   label=f"Fusão {TEMP_FUSAO_PCM}–{TEMP_SATURACAO_PCM} °C")

        ax.plot(t_min, T_sm, color=SENSOR_ACCENT,
                linewidth=3.0, label="T sensor", zorder=5)
        ax.fill_between(t_min, T_sm, min(T_sm),
                        color=SENSOR_ACCENT, alpha=0.12, zorder=2)

        if hasattr(r, "baseline_temp_c") and r.baseline_temp_c:
            t_base = [v / 60.0 for v in r.baseline_tempo_s]
            ax.plot(t_base, r.baseline_temp_c, color=COLOR_WITHOUT_PCM,
                    linewidth=2.0, linestyle="--", alpha=0.8, label="Sem PCM")

        t_pico_min = float(r.tempo_pico_s) / 60.0
        ax.scatter([t_pico_min], [float(r.pico_temperatura)],
                   s=160, color=COLOR_PICO, edgecolors="white", zorder=9)
        ax.annotate(f"{float(r.pico_temperatura):.1f} °C",
                    xy=(t_pico_min, float(r.pico_temperatura)),
                    xytext=(8, 10), textcoords="offset points",
                    fontsize=10, color=TEXT_PRIMARY, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=CARD_COLOR,
                              edgecolor=COLOR_PICO, alpha=0.9))

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=11)
        ax.set_ylabel("Temperatura (°C)", color=TEXT_PRIMARY, fontsize=11)
        ax.legend(fontsize=10, facecolor=CARD_COLOR,
                  edgecolor=BORDER_COLOR, labelcolor=TEXT_PRIMARY)

    def _plot_energia(self, ax, t_min, E_sm, r) -> None:
        _style(ax)
        ax.set_title("PCM — Energia Absorvida Acumulada",
                     color=TEXT_PRIMARY, fontsize=15, fontweight="bold", pad=14)

        ax.plot(t_min, E_sm, color=SENSOR_ENERGY,
                linewidth=3.2, alpha=0.95, zorder=5)
        ax.fill_between(t_min, E_sm, 0,
                        color=SENSOR_ENERGY, alpha=0.16, zorder=2)

        q_total = float(r.energia_total_j) if hasattr(r, "energia_total_j") else (
            E_sm[-1] if E_sm else 0.0)
        ax.text(0.97, 0.96,
                f"Q_pcm\n{q_total:.1f} J",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=11, fontweight="bold", color=TEXT_PRIMARY,
                bbox=dict(boxstyle="round,pad=0.45", facecolor=CARD_COLOR,
                          edgecolor=SENSOR_ENERGY, alpha=0.92))

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=11)
        ax.set_ylabel("Energia (J)", color=TEXT_PRIMARY, fontsize=11)

    def _placeholder(self) -> None:
        self._clear()
        fig = Figure(figsize=(12.0, 6.0), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD_COLOR)
        ax.text(0.5, 0.5,
                "Importe o log do sensor para ver os gráficos.",
                ha="center", va="center", fontsize=13,
                color=TEXT_SECONDARY, style="italic")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ["top","right","bottom","left"]:
            ax.spines[s].set_color(BORDER_COLOR)
        self._finalize(fig)

    def _finalize(self, fig):
        c = FigureCanvasTkAgg(fig, master=self)
        c.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        c.draw_idle()
        self._canvases.append(c)

    def _clear(self):
        for c in self._canvases:
            try:
                w = c.get_tk_widget()
                if w.winfo_exists():
                    w.destroy()
            except Exception:
                pass
        self._canvases.clear()

    def destroy(self):
        self._clear()
        super().destroy()


# ─────────────────────────────────────────────────────────────────────────────
# ComparisonChartFrame — Com PCM × Sem PCM
# ─────────────────────────────────────────────────────────────────────────────

class ComparisonChartFrame(ctk.CTkFrame):
    """Gráfico comparativo usando extrapolação linear pré-fusão."""

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._canvases: list[FigureCanvasTkAgg] = []
        self._placeholder()

    def render(self, r) -> None:
        self._clear()
        t_s   = [float(v) for v in r.tempo_s]
        T_s   = [float(v) for v in r.temperatura_c]
        t_min = [v / 60.0 for v in t_s]
        T_ini = float(r.temperatura_inicial)

        # Taxa pré-fusão → curva sem PCM
        taxa = self._taxa_pre_fusao(t_s, T_s)
        T_sem = [T_ini + taxa * tv for tv in t_s]

        T_com = smooth_series(T_s, window=11)
        T_sem = smooth_series(T_sem, window=11)

        pico_com = max(T_com)
        pico_sem = max(T_sem)
        delta_pico = pico_sem - pico_com

        fig = Figure(figsize=(13.0, 6.0), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)
        fig.subplots_adjust(left=0.08, right=0.96, top=0.91, bottom=0.10)

        ax = fig.add_subplot(111)
        _style(ax)
        ax.set_title("Comparação — Com PCM × Sem PCM",
                     color="#6EE7B7", fontsize=14, fontweight="bold", pad=12)

        ax.axhspan(TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
                   color=SENSOR_FUSION, alpha=0.10, zorder=1,
                   label=f"Região fusão ({TEMP_FUSAO_PCM}–{TEMP_SATURACAO_PCM} °C)")

        mask = [T_sem[i] > T_com[i] for i in range(len(t_min))]
        ax.fill_between(t_min, T_sem, T_com, where=mask,
                        color="#34D399", alpha=0.18, zorder=2,
                        label="Calor absorvido pelo PCM")

        ax.plot(t_min, T_com, color=COLOR_WITH_PCM,
                linewidth=3.0, alpha=0.95, zorder=4,
                label=f"Com PCM  ({pico_com:.1f} °C)")
        ax.plot(t_min, T_sem, color=COLOR_WITHOUT_PCM,
                linewidth=2.4, linestyle="--", alpha=0.85, zorder=4,
                label=f"Sem PCM  ({pico_sem:.1f} °C, estimado)")

        if delta_pico > 0.3:
            idx = T_sem.index(pico_sem)
            ax.annotate(f"Redução: {delta_pico:.1f} °C",
                        xy=(t_min[idx], pico_com + delta_pico / 2),
                        xytext=(t_min[idx] + 2, pico_com + delta_pico / 2 + 1.5),
                        fontsize=10, color="#A3E635", fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color="#A3E635", lw=1.4),
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=CARD_COLOR,
                                  edgecolor="#A3E635", alpha=0.85), zorder=8)

        ax.text(0.02, 0.97, f"Δpico = {delta_pico:.1f} °C",
                transform=ax.transAxes, color="#E5E7EB",
                fontsize=10.5, fontweight="bold", va="top", zorder=10,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD_COLOR,
                          edgecolor="#065F46", alpha=0.90))

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=11, fontweight="bold")
        ax.set_ylabel("Temperatura (°C)", color=TEXT_PRIMARY, fontsize=11, fontweight="bold")
        ax.legend(loc="upper left", fontsize=10, framealpha=0.92,
                  facecolor=CARD_COLOR, edgecolor="#065F46", labelcolor=TEXT_PRIMARY)

        self._finalize(fig)

    @staticmethod
    def _taxa_pre_fusao(t_s, T_s) -> float:
        pre_t, pre_T = [], []
        for t, T in zip(t_s, T_s):
            if T >= TEMP_FUSAO_PCM:
                break
            pre_t.append(t); pre_T.append(T)
        if len(pre_t) < 2:
            return 0.0
        dt = pre_t[-1] - pre_t[0]
        return (pre_T[-1] - pre_T[0]) / dt if dt > 0 else 0.0

    def _placeholder(self) -> None:
        self._clear()
        fig = Figure(figsize=(13.0, 5.5), dpi=100)
        fig.patch.set_facecolor(PANEL_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD_COLOR)
        ax.text(0.5, 0.5, "Gráfico comparativo após importar o log.",
                ha="center", va="center", fontsize=13,
                color=TEXT_SECONDARY, style="italic")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ["top","right","bottom","left"]:
            ax.spines[s].set_color("#065F46")
        self._finalize(fig)

    def _finalize(self, fig):
        c = FigureCanvasTkAgg(fig, master=self)
        c.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        c.draw_idle()
        self._canvases.append(c)

    def _clear(self):
        for c in self._canvases:
            try:
                w = c.get_tk_widget()
                if w.winfo_exists():
                    w.destroy()
            except Exception:
                pass
        self._canvases.clear()

    def destroy(self):
        self._clear()
        super().destroy()


# ─────────────────────────────────────────────────────────────────────────────
# SensorPCMScreen — tela completa do sensor
# ─────────────────────────────────────────────────────────────────────────────

class SensorPCMScreen(ctk.CTkFrame):
    """Tela completa do sensor IR. Completamente separada do PCMCalcScreen."""

    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=BG_COLOR)
        self._sensor = PCMTemperatureSensor() if _SENSOR_OK else None
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR,
            scrollbar_button_color=CARD_COLOR,
            scrollbar_button_hover_color=BORDER_COLOR)
        scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        scroll.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color=PANEL_COLOR, corner_radius=18,
                            border_width=1, border_color=BORDER_COLOR)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(0, 16))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr,
            text="Sensor Infravermelho — Análise Energética do PCM",
            font=("Inter", 26, "bold"), text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 6))

        ctk.CTkLabel(hdr,
            text="Q_pcm = m·c·ΔT  |  η = Q_pcm / Q_ref × 100  |  t_eq = Q_pcm / P",
            font=("Inter", 13), text_color=TEXT_SECONDARY,
            wraplength=1080, justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

        actions = ctk.CTkFrame(hdr, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=24, pady=18)
        ctk.CTkButton(actions, text="Importar Log do Sensor",
            command=self._import, width=210, height=42,
            fg_color=THEME_COLORS["primary"], hover_color="#0891B2",
            font=("Inter", 15, "bold")).pack()

        self._status = ctk.CTkLabel(hdr,
            text="Aguardando log do sensor (.csv).",
            font=("Inter", 13), text_color=TEXT_SECONDARY)
        self._status.grid(row=2, column=0, columnspan=2,
                          sticky="w", padx=24, pady=(0, 18))

        # KPIs
        self._kpi = SensorKPIFrame(scroll)
        self._kpi.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))

        # Gráfico sensor
        self._chart = SensorChartFrame(scroll)
        self._chart.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 16))

        # Comparação
        comp_hdr = ctk.CTkFrame(scroll, fg_color=PANEL_COLOR, corner_radius=18,
                                 border_width=1, border_color="#065F46")
        comp_hdr.grid(row=3, column=0, sticky="ew", padx=12, pady=(8, 12))
        comp_hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(comp_hdr,
            text="⚖  Comparação — Com PCM × Sem PCM",
            font=("Inter", 22, "bold"), text_color="#6EE7B7",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 6))
        ctk.CTkLabel(comp_hdr,
            text="Curva 'Sem PCM' estimada por extrapolação da taxa pré-fusão.",
            font=("Inter", 13), text_color=TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

        self._comparison = ComparisonChartFrame(scroll)
        self._comparison.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 28))

    def _import(self) -> None:
        if not _SENSOR_OK:
            messagebox.showerror("Indisponível",
                                 "PCMTemperatureSensor não encontrado.")
            return
        fp = filedialog.askopenfilename(
            initialdir=os.path.expanduser("~"),
            title="Selecionar log do sensor (.csv)",
            filetypes=[("CSV", "*.csv")],
        )
        if not fp:
            return
        try:
            result = self._sensor.load_csv(fp)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            if self._status.winfo_exists():
                self._status.configure(text=f"Erro: {exc}", text_color=TEXT_PRIMARY)
            return

        if self._status.winfo_exists():
            self._status.configure(
                text=f"Log processado: {os.path.basename(fp)}",
                text_color=SUCCESS_COLOR)
        self._kpi.update_from_result(result)
        self._chart.render(result)
        self._comparison.render(result)
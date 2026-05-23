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
    POTENCIA_NOTEBOOK_W, TEMPO_EXPERIMENTO_S,
    Q_NOTEBOOK_REF_J, Q_PCM_ESTIMADO_J, EFICIENCIA_PCM_ESTIMADA,
    smooth_series,
    calcular_eficiencia,
    calcular_tempo_equivalente,
    calcular_dT_dt,
    calcular_estabilizacao,
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
    ("Energia Desviada do Notebook",
     "Q_pcm = η × Q_notebook  (J)\n"
     "Energia térmica absorvida pelo PCM DA FONTE (notebook).\n"
     "NÃO é ΔT do sensor — é fração da energia do notebook desviada."),
    ("Eficiência de Absorção",
     "η = (m·c·ΔT_atuacao) / Q_notebook × 100  (%)\n"
     "Fração da energia do notebook absorvida pelo PCM.\n"
     "ΔT_atuacao = 7°C (faixa 53–60°C)  |  Q_notebook = 234 kJ"),
    ("Tempo Equivalente",
     "t_eq = Q_pcm / P_notebook  (min)\n"
     "Por quantos minutos o PCM pode dissipar sozinho a potência do notebook."),
    ("Estado do PCM",
     "Baseado na temperatura atual do sensor:\n"
     "• Sólido  →  T < 53 °C\n"
     "• Em Fusão  →  53–60 °C\n"
     "• Saturado  →  T > 60 °C"),
    ("Tempo de Estabilização",
     "Instante em que |dT/dt| < 0,01 °C/s por 30 s contínuos.\n"
     "Indica estabilização térmica do PCM."),
    ("Energia Notebook (Ref)",
     "Q_notebook = P × t = 50 W × 4680 s = 234 000 J\n"
     "Energia total gerada pela fonte térmica durante o experimento."),
    ("Potência Desviada Média",
     "P_desviada = Q_pcm / t_experimento  (W)\n"
     "Potência média absorvida pelo PCM ao longo do experimento."),
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
        Exibe métricas do sensor IR.

        MODELO CORRETO: absorção relativa da fonte térmica.
        Q_pcm = EFICIENCIA_PCM_ESTIMADA × Q_NOTEBOOK_REF_J

        O sensor fornece:
          - temperatura atual (estado do PCM)
          - tempo de estabilização
          - validação da atuação na faixa de fusão

        O sensor NÃO define sozinho Q_pcm via ΔT bruto.
        """
        T_c    = [float(v) for v in r.temperatura_c] if r.temperatura_c else []
        T_ini  = float(r.temperatura_inicial)
        T_atual = float(T_c[-1]) if T_c else T_ini
        t_s    = [float(v) for v in r.tempo_s]

        # ── Física principal: absorção relativa da fonte ───────────────────────
        # Q_pcm = η × Q_notebook  (NÃO m·c·ΔT do sensor)
        q_notebook = Q_NOTEBOOK_REF_J                          # 234 000 J
        q_pcm      = Q_PCM_ESTIMADO_J                          # η × Q_notebook
        eta        = EFICIENCIA_PCM_ESTIMADA * 100.0           # %
        t_eq_s     = calcular_tempo_equivalente(q_pcm)         # s
        p_desviada = q_pcm / TEMPO_EXPERIMENTO_S               # W médio absorvido

        # ── Sensor: apenas estado térmico e estabilização ─────────────────────
        deriv   = calcular_dT_dt(t_s, T_c)
        t_estab = calcular_estabilizacao(t_s, deriv)

        if T_atual < TEMP_FUSAO_PCM:
            estado, cor = "PCM Sólido",   "#93C5FD"
        elif T_atual <= TEMP_SATURACAO_PCM:
            estado, cor = "PCM em Fusão", "#FCD34D"
        else:
            estado, cor = "PCM Saturado", "#F87171"

        def _s(key, text, *, color=TEXT_PRIMARY, sub=""):
            card = self._cards.get(key)
            if card:
                card.set_value(text, color=color)
                if sub:
                    card.set_sub(sub)

        _s("Temperatura Atual",
           f"{T_atual:.1f} °C",
           sub=f"Inicial: {T_ini:.1f} °C  |  ΔT: {T_atual - T_ini:.2f} °C")

        _s("Energia Desviada do Notebook",
           f"{q_pcm / 1000:.2f} kJ",
           sub=f"η × Q_notebook = {eta:.2f}% × {q_notebook/1000:.0f} kJ")

        _s("Eficiência de Absorção",
           f"{eta:.2f} %",
           color="#FCD34D" if eta >= 3.0 else "#F87171",
           sub="(m·c·ΔT_faixa) / Q_notebook")

        _s("Tempo Equivalente",
           f"{t_eq_s / 60:.1f} min",
           sub=f"= {t_eq_s:.0f} s  |  Q_pcm / P_notebook")

        _s("Estado do PCM",
           estado, color=cor)

        _s("Tempo de Estabilização",
           f"{t_estab / 60:.1f} min" if t_estab else "Não estabilizou",
           sub="Sensor: |dT/dt| < 0.01 °C/s por 30 s")

        _s("Energia Notebook (Ref)",
           f"{q_notebook / 1000:.0f} kJ",
           sub=f"P × t = {POTENCIA_NOTEBOOK_W:.0f} W × {TEMPO_EXPERIMENTO_S:.0f} s")

        _s("Potência Desviada Média",
           f"{p_desviada:.2f} W",
           sub=f"Q_pcm / t_exp = {q_pcm:.0f} / {TEMPO_EXPERIMENTO_S:.0f}")


# ─────────────────────────────────────────────────────────────────────────────
# SensorChartFrame — gráficos do sensor
# ─────────────────────────────────────────────────────────────────────────────

class SensorChartFrame(ctk.CTkFrame):
    """Temperatura × Tempo  +  Energia Absorvida × Tempo do sensor IR."""

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._canvases: list[FigureCanvasTkAgg] = []
        self._placeholder()

    def render(self, r) -> None:
        """
        Dois gráficos do sensor IR:
            Superior: Temperatura do PCM (sensor) — curva térmica real
            Inferior: Comparação Com PCM × Sem PCM (extrapolação linear)

        NÃO calcula energia aqui — o sensor é validação térmica, não fonte
        do cálculo energético principal.
        """
        self._clear()
        t_s   = [float(v) for v in r.tempo_s]
        T     = [float(v) for v in r.temperatura_c]
        T_sm  = smooth_series(T, window=7)
        t_min = [v / 60.0 for v in t_s]

        # Curva "sem PCM" — extrapolação linear da taxa pré-fusão
        T_ini = float(r.temperatura_inicial)
        taxa  = self._taxa_pre_fusao(t_s, T)
        T_sem = [T_ini + taxa * tv for tv in t_s]
        T_sem_sm = smooth_series(T_sem, window=11)

        fig = Figure(figsize=(18, 10), dpi=110)
        fig.patch.set_facecolor(PANEL_COLOR)
        gs = fig.add_gridspec(2, 1, height_ratios=[1.1, 0.9], hspace=0.38,
                              left=0.08, right=0.96, top=0.94, bottom=0.07)

        self._plot_temp(fig.add_subplot(gs[0]), t_min, T_sm, r)
        self._plot_comparacao(fig.add_subplot(gs[1]), t_min, T_sm, T_sem_sm)
        self._finalize(fig)

    @staticmethod
    def _taxa_pre_fusao(t_s: list[float], T_s: list[float]) -> float:
        """Taxa de aquecimento pré-fusão em °C/s para construir curva sem PCM."""
        pre_t, pre_T = [], []
        for t, T in zip(t_s, T_s):
            if T >= TEMP_FUSAO_PCM:
                break
            pre_t.append(t)
            pre_T.append(T)
        if len(pre_t) < 2:
            return 0.0
        dt = pre_t[-1] - pre_t[0]
        return (pre_T[-1] - pre_T[0]) / dt if dt > 0 else 0.0

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

    def _plot_comparacao(self, ax, t_min, T_com, T_sem) -> None:
        """
        Gráfico de comparação: Com PCM × Sem PCM.
        Mostra o benefício térmico real do PCM via extrapolação linear.
        """
        _style(ax)
        ax.set_title("Sensor IR — Comparação Térmica: Com PCM × Sem PCM",
                     color=TEXT_PRIMARY, fontsize=14, fontweight="bold", pad=12)

        ax.axhspan(TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
                   color=SENSOR_FUSION, alpha=0.10, zorder=1,
                   label=f"Faixa fusão {TEMP_FUSAO_PCM}–{TEMP_SATURACAO_PCM} °C")
        ax.axhline(TEMP_FUSAO_PCM, color=SENSOR_FUSION,
                   linewidth=0.8, linestyle="--", alpha=0.5, zorder=2)

        # Área de calor absorvido
        mask = [T_sem[i] > T_com[i] for i in range(min(len(T_sem), len(T_com)))]
        ax.fill_between(t_min[:len(T_com)], T_sem[:len(T_com)], T_com,
                        where=mask, color="#34D399", alpha=0.20, zorder=2,
                        label="Calor absorvido pelo PCM")

        pico_com = max(T_com) if T_com else 0.0
        pico_sem = max(T_sem) if T_sem else 0.0
        delta    = pico_sem - pico_com

        ax.plot(t_min[:len(T_com)], T_com, color=COLOR_WITH_PCM,
                linewidth=2.8, alpha=0.95, zorder=4,
                label=f"Com PCM  (pico: {pico_com:.1f} °C)")
        ax.plot(t_min[:len(T_sem)], T_sem, color=COLOR_WITHOUT_PCM,
                linewidth=2.2, linestyle="--", alpha=0.85, zorder=4,
                label=f"Sem PCM  (estimado: {pico_sem:.1f} °C)")

        if delta > 0.3:
            ax.text(0.02, 0.97,
                    f"Redução de pico: {delta:.1f} °C",
                    transform=ax.transAxes, ha="left", va="top",
                    fontsize=11, fontweight="bold", color="#A3E635",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD_COLOR,
                              edgecolor="#A3E635", alpha=0.88))

        ax.set_xlabel("Tempo (min)", color=TEXT_PRIMARY, fontsize=11)
        ax.set_ylabel("Temperatura (°C)", color=TEXT_PRIMARY, fontsize=11)
        ax.legend(loc="upper left", fontsize=10, facecolor=CARD_COLOR,
                  edgecolor=BORDER_COLOR, labelcolor=TEXT_PRIMARY)

    def _placeholder(self) -> None:
        self._clear()
        fig = Figure(figsize=(18.0, 10.0), dpi=100)
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
        scroll.grid_rowconfigure(2, weight=1)

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
        self._chart.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 16))
        
        #scroll
        scroll.grid_rowconfigure(2, weight=1)
        scroll.grid_columnconfigure(0, weight=1)

        

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

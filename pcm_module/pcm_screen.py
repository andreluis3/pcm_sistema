from __future__ import annotations

import math
import os
from tkinter import filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from scipy.ndimage import uniform_filter1d
import pandas as pd
from pcm_module.pcm_temperature_sensor import TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM, SensorPCMResult

from .pcm_model import PCMResult
from .pcm_repository import PCMRepository
from .pcm_service import PCMService
from pcm_module.pcm_temperature_sensor import PCMTemperatureSensor, SensorPCMResult
from ui_styles import *


def calcular_dT_dt(tempo_s: list[float], temperatura_c: list[float]) -> list[float]:
    """Derivada discreta dT/dt usando diferença entre pontos consecutivos (°C/s).

    Mantém o mesmo comprimento de entrada; dT/dt[0] = 0.0.
    """
    if not tempo_s or not temperatura_c:
        return []
    n = min(len(tempo_s), len(temperatura_c))
    if n <= 1:
        return [0.0] * n

    derivada: list[float] = [0.0]
    for i in range(1, n):
        dt = float(tempo_s[i]) - float(tempo_s[i - 1])
        if dt <= 0:
            derivada.append(0.0)
            continue
        dtemp = float(temperatura_c[i]) - float(temperatura_c[i - 1])
        derivada.append(dtemp / dt)
    return derivada


def _tempo_na_faixa_pcm_linear(
    tempo_s: list[float],
    temperatura_c: list[float],
    *,
    pcm_min_c: float,
    pcm_max_c: float,
) -> float:
    """Tempo total (s) em que a temperatura permaneceu dentro [pcm_min_c, pcm_max_c].

    Assume variação linear entre amostras e calcula a interseção por segmento.
    """
    if not tempo_s or not temperatura_c:
        return 0.0
    n = min(len(tempo_s), len(temperatura_c))
    if n < 2:
        return 0.0

    faixa_min = float(min(pcm_min_c, pcm_max_c))
    faixa_max = float(max(pcm_min_c, pcm_max_c))

    total = 0.0
    for i in range(1, n):
        t0 = float(tempo_s[i - 1])
        t1 = float(tempo_s[i])
        dt = t1 - t0
        if dt <= 0:
            continue

        T0 = float(temperatura_c[i - 1])
        T1 = float(temperatura_c[i])

        # Segmento constante.
        if T0 == T1:
            if faixa_min <= T0 <= faixa_max:
                total += dt
            continue

        # Parametriza T(t) = T0 + a*(t-t0), com a = (T1-T0)/dt.
        a = (T1 - T0) / dt

        # Encontra intervalos em tempo onde T está dentro da faixa.
        # Resolve limites em termos de t: t = t0 + (Tlim - T0)/a.
        t_enter = t0
        t_exit = t1

        # Para cada limite, atualiza o intervalo de interseção.
        for Tlim, is_lower in ((faixa_min, True), (faixa_max, False)):
            tcross = t0 + (Tlim - T0) / a
            if is_lower:
                if a > 0:
                    t_enter = max(t_enter, tcross)
                else:
                    t_exit = min(t_exit, tcross)
            else:
                if a > 0:
                    t_exit = min(t_exit, tcross)
                else:
                    t_enter = max(t_enter, tcross)

        # Clipa ao segmento original.
        t_enter = max(t0, min(t_enter, t1))
        t_exit = max(t0, min(t_exit, t1))

        if t_exit > t_enter:
            total += t_exit - t_enter

    return max(0.0, total)


def calcular_estabilizacao(
    tempo_s: list[float],
    dT_dt: list[float],
    *,
    limiar: float = 0.01,
    janela_s: float = 30.0,
) -> float | None:
    """Retorna o tempo (s) onde o sistema estabiliza com |dT/dt| < limiar por uma janela.

    Heurística: exige que a condição seja satisfeita continuamente por ~janela_s.
    """
    if not tempo_s or not dT_dt:
        return None

    n = min(len(tempo_s), len(dT_dt))
    if n < 4:
        return None

    # Estima dt típico para converter janela de tempo em janela de pontos.
    dts = [
        float(tempo_s[i]) - float(tempo_s[i - 1])
        for i in range(1, n)
        if (float(tempo_s[i]) - float(tempo_s[i - 1])) > 0
    ]
    if not dts:
        return None
    dt_med = sorted(dts)[len(dts) // 2]
    window_points = max(3, min(40, int(round(janela_s / max(dt_med, 1e-6)))))

    abs_der = [abs(float(v)) for v in dT_dt[:n]]
    for i in range(1, n - window_points):
        if all(v < limiar for v in abs_der[i : i + window_points]):
            return float(tempo_s[i])
    return None


def calcular_metricas_experimento(
    result: PCMResult,
    *,
    temperatura_alvo_c: float = 55.0,
    pcm_min_c: float = 50.0,
    pcm_max_c: float = 60.0,
) -> dict[str, float | None]:
    """Calcula métricas complementares sem alterar a lógica do PCMService/PCMResult."""
    tempo_s = result.tempo_s
    temperatura_c = result.temperatura_c

    duracao_s = float(max(tempo_s)) if tempo_s else float(result.tempo_total)
    duracao_min = duracao_s / 60.0 if duracao_s is not None else None

    pico_temp = float(result.pico_temperatura)
    tempo_pico_s = float(result.tempo_pico_temperatura)

    if temperatura_c:
        delta_t = float(max(temperatura_c) - min(temperatura_c))
    else:
        delta_t = 0.0

    heating_rate_c_por_s = (delta_t / duracao_s) if duracao_s > 0 else None
    heating_rate_c_por_min = (heating_rate_c_por_s * 60.0) if heating_rate_c_por_s is not None else None

    # ---------------------------------------------------------
    # ENERGIA REALMENTE ABSORVIDA PELO PCM
    # ---------------------------------------------------------

    CALOR_LATENTE_PCM = 180.0  # J/g  — ajuste conforme seu material real

    energia_total = float(result.energia_total)

    # Energia absorvida pelo PCM
    energia_pcm_absorvida = float(result.massa_pcm) * CALOR_LATENTE_PCM

    # Evita eficiência acima de 100%
    energia_pcm_absorvida = min(energia_pcm_absorvida, energia_total)

    # Energia perdida no ambiente
    energia_perdida = energia_total - energia_pcm_absorvida

    # ---------------------------------------------------------
    # EFICIÊNCIA TÉRMICA REAL
    # ---------------------------------------------------------

    eficiencia = None

    if energia_total > 0:
        eficiencia = (energia_pcm_absorvida / energia_total) * 100.0

    # ---------------------------------------------------------
    # ERRO PERCENTUAL / PERDAS
    # ---------------------------------------------------------

    erro_percentual = None

    if energia_total > 0:
        erro_percentual = (energia_perdida / energia_total) * 100.0

    # Tempo até temperatura alvo.
    tempo_ate_alvo_s = None
    for t, temp in zip(tempo_s, temperatura_c):
        if float(temp) >= float(temperatura_alvo_c):
            tempo_ate_alvo_s = float(t)
            break

    tempo_atuacao_pcm_s = _tempo_na_faixa_pcm_linear(
        tempo_s,
        temperatura_c,
        pcm_min_c=float(pcm_min_c),
        pcm_max_c=float(pcm_max_c),
    )

    return {
        "duracao_s": duracao_s,
        "duracao_min": duracao_min,
        "pico_temp_c": pico_temp,
        "tempo_pico_s": tempo_pico_s,
        "delta_t_c": delta_t,
        "taxa_aquecimento_c_min": heating_rate_c_por_min,
        "eficiencia_percent": eficiencia,
        "erro_percentual": erro_percentual,
        "energia_ideal_j": float(result.energia_teorica),
        "tempo_ate_55c_s": tempo_ate_alvo_s,
        "tempo_atuacao_pcm_s": tempo_atuacao_pcm_s,
    }


def _formatar_tempo_min_seg(tempo_s: float | None) -> str:
    """Formata segundos em MM:SS."""
    if tempo_s is None:
        return "--"
    tempo_s = max(0.0, float(tempo_s))
    return f"{int(tempo_s // 60):02d}:{int(round(tempo_s % 60)):02d}"

@staticmethod
def _smooth(data: list[float], window: int = 9) -> list[float]:
    """Média móvel simples usando scipy para suavizar curvas."""
    if len(data) < window:
        return data
    arr = np.array(data, dtype=float)
    return list(uniform_filter1d(arr, size=window))
 
 
def _style_ax(ax, panel_color: str, card_color: str, border_color: str, text_secondary: str) -> None:
    """Aplica estilo escuro científico padronizado a um Axes."""
    ax.set_facecolor(card_color)
    ax.tick_params(
        colors=text_secondary,
        labelsize=11,          # ← maior que antes (era 9)
        length=4,
        width=1.2,
    )
    ax.tick_params(axis='x', pad=6)
    ax.tick_params(axis='y', pad=4)
    ax.grid(
        True,
        linestyle="--",
        linewidth=0.55,
        alpha=0.30,
        color="#475569",
    )
    ax.minorticks_on()
    ax.grid(True, which='minor', linestyle=':', linewidth=0.3, alpha=0.15, color="#334155")
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["bottom", "left"]:
        ax.spines[side].set_color(border_color)
        ax.spines[side].set_linewidth(1.4)


class _Tooltip:
    def __init__(self, widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._win = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        self.sensor = PCMTemperatureSensor()
        self.sensor_result: SensorPCMResult | None = None
        self.sensor_chart_canvases: list[FigureCanvasTkAgg] = []
        self.sensor_kpi_values: dict[str, ctk.CTkLabel] = {}

    def _show(self, _event=None) -> None:
        if self._win is not None:
            return
        try:
            x = self.widget.winfo_rootx() + 14
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        except Exception:
            return

        win = ctk.CTkToplevel(self.widget)
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(win, fg_color="#0B0F16", corner_radius=10, border_width=1, border_color="#334155")
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            frame,
            text=self.text,
            font=("Arial", 12),
            text_color="#F3F4F6",
            justify="left",
            wraplength=360,
        ).pack(padx=12, pady=10)
        self._win = win

    def _hide(self, _event=None) -> None:
        if self._win is None:
            return
        self._win.destroy()
        self._win = None


class PCMCalcScreen(ctk.CTkFrame):
    BG_COLOR = "#0B0F16"
    PANEL_COLOR = "#111827"
    CARD_COLOR = "#0F172A"
    BORDER_COLOR = "#334155"
    TEXT_PRIMARY = "#F3F4F6"
    TEXT_SECONDARY = "#9CA3AF"
    SUCCESS_COLOR = "#E5E7EB"
    TEMP_COLOR = "#E5E7EB"
    POWER_COLOR = "#6B7280"
    ENERGY_COLOR = "#D1D5DB"
    ENERGY_FILL = "#9CA3AF"

    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=self.BG_COLOR)
        self.service = PCMService()
        self.repository = PCMRepository()
        self.current_result: PCMResult | None = None
        self.chart_canvases: list[FigureCanvasTkAgg] = []      # ← adiciona
        self.kpi_values: dict[str, ctk.CTkLabel] = {}           # ← adiciona
        self.kpi_subvalues: dict[str, ctk.CTkLabel] = {}        # ← adiciona
        self.sensor = PCMTemperatureSensor()
        self.sensor_result: SensorPCMResult | None = None
        self.sensor_chart_canvases: list[FigureCanvasTkAgg] = []
        self.sensor_kpi_values: dict[str, ctk.CTkLabel] = {}
        self._build_layout()
    
    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.BG_COLOR,
            scrollbar_button_color=self.CARD_COLOR,
            scrollbar_button_hover_color=self.BORDER_COLOR,
        )
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self.scroll_frame, fg_color=self.PANEL_COLOR, corner_radius=18)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Calculos de PCM - Dashboard Térmico",
            font=("Arial", 30, "bold"),
            text_color=self.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 6))

        ctk.CTkLabel(
            header,
            text=(
                "Analise profissional de logs termicos e energeticos com estimativa de massa de PCM "
                "para aplicacoes em hardware."
            ),
            font=("Arial", 15),
            text_color=self.TEXT_SECONDARY,
            wraplength=1080,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=24, pady=18)

        self.import_button = ctk.CTkButton(
            actions,
            text="Importar CSV",
            command=self.import_csv,
            width=190,
            height=42,
            fg_color=self.POWER_COLOR,
            hover_color="#4B5563",
            font=("Arial", 15, "bold"),
        )
        self.import_button.pack()

        self.status_label = ctk.CTkLabel(
            header,
            text="Aguardando arquivo CSV do diretório padrao de logs.",
            font=("Arial", 13),
            text_color=self.SUCCESS_COLOR,
        )
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=24, pady=(0, 20))

        # ── KPIs ──────────────────────────────────────────────────────────────
        self.kpi_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))
        for column in range(4):
            self.kpi_frame.grid_columnconfigure(column, weight=1, uniform="kpi")
        for row in range(3):
            self.kpi_frame.grid_rowconfigure(row, weight=1, uniform="kpi_row")

        self._kpi_defs: list[dict[str, str]] = [
            {
                "key": "Energia Total",
                "default": "--",
                "tooltip": "Energia total integrada ao longo do ensaio (J).",
            },
            {
                "key": "Potência Média",
                "default": "--",
                "tooltip": "Potência média aplicada/observada durante o ensaio (W).",
            },
            {
                "key": "Massa PCM",
                "default": "--",
                "tooltip": "Massa estimada de PCM necessária para absorver a energia do ensaio (g).",
            },
            {
                "key": "Erro Percentual",
                "default": "--",
                "tooltip": "Erro percentual: |E_ideal - E_real| / E_ideal × 100 (%).",
            },
            {
                "key": "Tempo de Atuação do PCM",
                "default": "--",
                "tooltip": "Tempo total em que 50°C ≤ T ≤ 60°C (min).",
            },
            {
                "key": "Delta T",
                "default": "--",
                "tooltip": "Variação térmica total: max(T) − min(T) (°C).",
            },
            {
                "key": "Eficiência Térmica",
                "default": "--",
                "tooltip": "Eficiência: energia_real / energia_ideal × 100 (%), entre 60-99%.",
            },
            {
                "key": "Energia Ideal",
                "default": "--",
                "tooltip": "Energia ideal que o sistema deveria absorver para desempenho perfeito (J).",
            },
            {
                "key": "Duração do Experimento",
                "default": "--",
                "tooltip": "Duração total do ensaio (min).",
            },
        ]
        for index, kpi_def in enumerate(self._kpi_defs):
            self._create_kpi_card(index, kpi_def["key"], kpi_def["default"], tooltip=kpi_def["tooltip"])

        # ── Chart section ─────────────────────────────────────────────────────
        self.chart_section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.chart_section.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 16))
        self.chart_section.grid_columnconfigure(0, weight=1)

        # ── Analysis box ──────────────────────────────────────────────────────
        self.analysis_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.analysis_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 16))
        self.analysis_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.analysis_frame,
            text="Analise Tecnica Automatizada",
            font=("Arial", 20, "bold"),
            text_color=self.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 10))

        self.analysis_box = ctk.CTkTextbox(
            self.analysis_frame,
            height=140,
            fg_color=self.CARD_COLOR,
            text_color=self.TEXT_PRIMARY,
            font=("Courier New", 14),
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.analysis_box.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))

        # ── CSV preview box ───────────────────────────────────────────────────
        self.log_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.log_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 16))
        self.log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.log_frame,
            text="Preview dos Dados do CSV",
            font=("Arial", 20, "bold"),
            text_color=self.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 10))

        self.log_box = ctk.CTkTextbox(
            self.log_frame,
            height=210,
            fg_color=self.CARD_COLOR,
            text_color=self.TEXT_PRIMARY,
            font=("Courier New", 13),
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.log_box.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))

        self._set_initial_content()
        self._build_sensor_section()

    # ── KPI card ──────────────────────────────────────────────────────────────

    def _create_kpi_card(self, index: int, title: str, default_value: str, *, tooltip: str) -> None:
        card = ctk.CTkFrame(
            self.kpi_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        row = index // 4
        col = index % 4
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 14, "bold"),
            text_color=self.TEXT_SECONDARY,
        )
        title_label.pack(anchor="w", padx=18, pady=(16, 8))
        _Tooltip(title_label, tooltip)

        value_label = ctk.CTkLabel(
            card,
            text=default_value,
            font=("Arial", 22, "bold"),
            text_color=self.TEXT_PRIMARY,
            justify="left",
            wraplength=320,
        )
        value_label.pack(anchor="w", padx=18, pady=(0, 16))
        self.kpi_values[title] = value_label

        sub_label = ctk.CTkLabel(
            card,
            text="",
            font=("Arial", 12),
            text_color=self.TEXT_SECONDARY,
            justify="left",
            wraplength=320,
        )
        self.kpi_subvalues[title] = sub_label

    # ── Initial state ─────────────────────────────────────────────────────────

    def _set_initial_content(self) -> None:
        self._write_text(
            self.analysis_box,
            "Importe um arquivo CSV para gerar a interpretacao tecnica do ensaio.",
        )
        self._write_text(
            self.log_box,
            "timestamp           tempo_s  potencia_w  temperatura_c  energia_j\n"
            "------------------  -------  ----------  -------------  ---------\n"
            "Aguardando importacao do arquivo.",
        )
        self._render_placeholder_chart()

    def _render_placeholder_chart(self) -> None:
        self._clear_charts()
        figure = Figure(figsize=(11.5, 7.2), dpi=100)
        figure.patch.set_facecolor(self.PANEL_COLOR)
        axis = figure.add_subplot(111)
        axis.set_facecolor(self.CARD_COLOR)
        axis.text(
            0.5,
            0.5,
            "Os graficos aparecerao aqui apos a importacao do CSV.",
            ha="center",
            va="center",
            fontsize=15,
            color=self.TEXT_SECONDARY,
        )
        axis.set_xticks([])
        axis.set_yticks([])
        for side in ["top", "right", "bottom", "left"]:
            axis.spines[side].set_color(self.BORDER_COLOR)

        canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
        widget = canvas.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self.chart_canvases.append(canvas)

    # ── CSV import ────────────────────────────────────────────────────────────

    def import_csv(self) -> None:
        initial_path = "/home/andre/pc_temperature"

        if not os.path.isdir(initial_path):
            initial_path = os.path.expanduser("~")

        file_path = filedialog.askopenfilename(
            initialdir=initial_path,
            title="Selecionar arquivo CSV",
            filetypes=[("Arquivos CSV", "*.csv")],
        )

        if not file_path:
            return

        try:
            result = self.service.process_csv(file_path)
            self.repository.save(result)
        except Exception as exc:
            messagebox.showerror("Falha ao processar CSV", str(exc))
            self.status_label.configure(text="Falha ao processar o arquivo selecionado.", text_color=self.TEXT_PRIMARY)
            return

        self.current_result = result
        self.status_label.configure(
            text=f"Arquivo processado com sucesso: {os.path.basename(file_path)}",
            text_color=self.SUCCESS_COLOR,
        )
        self._update_dashboard(result)

    # ── Dashboard update ──────────────────────────────────────────────────────

    def _update_dashboard(self, result: PCMResult) -> None:
        metricas = calcular_metricas_experimento(result)

        self.kpi_values["Energia Total"].configure(text=f"{result.energia_total:.0f} J")
        self.kpi_values["Potência Média"].configure(text=f"{result.potencia_media:.2f} W")
        self.kpi_values["Massa PCM"].configure(text=f"{result.massa_pcm:.2f} g")

        erro_pct = metricas["erro_percentual"]
        self.kpi_values["Erro Percentual"].configure(text=f"{erro_pct:.1f} %" if erro_pct is not None else "--")

        tempo_pcm_min = float(metricas["tempo_atuacao_pcm_s"] or 0.0) / 60.0
        self.kpi_values["Tempo de Atuação do PCM"].configure(text=f"{tempo_pcm_min:.0f} min")
        pcm_sub = self.kpi_subvalues["Tempo de Atuação do PCM"]
        pcm_sub.configure(text="Faixa: 50–60°C")
        if not pcm_sub.winfo_ismapped():
            pcm_sub.pack(anchor="w", padx=18, pady=(0, 16))

        self.kpi_values["Delta T"].configure(text=f"{metricas['delta_t_c']:.2f} °C")

        eficiencia = metricas["eficiencia_percent"]
        self.kpi_values["Eficiência Térmica"].configure(text=f"{eficiencia:.1f} %" if eficiencia is not None else "--")

        energia_ideal = metricas["energia_ideal_j"]
        self.kpi_values["Energia Ideal"].configure(text=f"{energia_ideal:.0f} J" if energia_ideal is not None else "--")

        self.kpi_values["Duração do Experimento"].configure(
            text=f"{metricas['duracao_min']:.2f} min" if metricas["duracao_min"] is not None else "--"
        )

        analysis_lines = ["[Analise Tecnica]"]
        analysis_lines.append(
            f"- Pico: {result.pico_temperatura:.2f}°C em {_formatar_tempo_min_seg(result.tempo_pico_temperatura)}."
        )
        analysis_lines.append(
            f"- Tempo até 55°C: {_formatar_tempo_min_seg(metricas['tempo_ate_55c_s'])}."
        )
        analysis_lines.append(f"- Atuação do PCM (50–60°C): {(tempo_pcm_min):.2f} min.")
        analysis_lines.extend(f"- {line}" for line in result.analise_tecnica)
        analysis_lines.append(f"- Delta de tempo total analisado: {result.delta_tempo:.2f} s.")
        analysis_lines.append(f"- Temperatura media registrada: {result.temperatura_media:.2f} C.")
        analysis_lines.append("")
        analysis_lines.append("[Calculo Detalhado]")
        analysis_lines.extend(f"- {line}" for line in result.calculo_detalhado)
        self._write_text(self.analysis_box, "\n".join(analysis_lines))
        self._write_text(self.log_box, self._format_preview_table(result.csv_preview))
        self._render_charts(result)

    # ── Charts ────────────────────────────────────────────────────────────────

    def _render_charts(self, result: SensorPCMResult) -> None:
        self._clear_charts()

        figure = Figure(figsize=(12.0, 6.5), dpi=100)
        figure.patch.set_facecolor(self.PANEL_COLOR)

        ax_temp = figure.add_subplot(111)
        ax_temp.set_facecolor(self.CARD_COLOR)
        ax_temp.tick_params(colors=self.TEXT_SECONDARY, labelsize=10)
        ax_temp.grid(True, linestyle="-", linewidth=0.5, alpha=0.25, color="#64748B")
        for side in ["top", "right"]:
            ax_temp.spines[side].set_visible(False)
        for side in ["bottom", "left"]:
            ax_temp.spines[side].set_color(self.BORDER_COLOR)
            ax_temp.spines[side].set_linewidth(1.2)

        time_values = result.tempo_s
        temps = result.temperatura_c

        if not time_values or not temps:
            ax_temp.set_title(
                "Temperatura × Tempo — Resposta térmica do PCM",
                color=self.TEXT_PRIMARY,
                fontsize=16,
                fontweight="bold",
                pad=16,
            )
            ax_temp.text(
                0.5,
                0.5,
                "Sem dados de temperatura para plotar.",
                transform=ax_temp.transAxes,
                ha="center",
                va="center",
                fontsize=13,
                color=self.TEXT_SECONDARY,
            )
            figure.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.08)
            canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            canvas.draw_idle()
            self.chart_canvases.append(canvas)
            return

        metricas = calcular_metricas_experimento(result)
        tempo_55 = metricas["tempo_ate_55c_s"]
        tempo_pico = metricas["tempo_pico_s"]
        min_temp = float(min(temps))

        ax_temp.set_title(
            "Temperatura × Tempo — Resposta térmica do PCM",
            color=self.TEXT_PRIMARY,
            fontsize=16,
            fontweight="bold",
            pad=16,
        )

        # Faixa de atuação do PCM (50–60°C)
        ax_temp.axhspan(50.0, 60.0, color="#00FF96", alpha=0.12, label="Faixa PCM 50–60°C", zorder=1)

        # Preenchimento sob a curva
        ax_temp.fill_between(time_values, temps, min_temp, color="#FF5733", alpha=0.15, label="Área absorvida", zorder=2)

        # Linha principal
        ax_temp.plot(time_values, temps, color="#FF5733", linewidth=3.0, alpha=0.95, label="Temperatura", zorder=4)

        # Média móvel
        if result.temperatura_media_movel:
            ax_temp.plot(
                time_values,
                result.temperatura_media_movel,
                color="#4FC3F7",
                linewidth=2.2,
                linestyle="--",
                alpha=0.85,
                label="Média móvel (7 pontos)",
                zorder=3,
            )

        # Pico
        ax_temp.scatter(
            [result.tempo_pico_temperatura],
            [result.pico_temperatura],
            color="#FF5733",
            edgecolors="#FFD700",
            linewidths=2.0,
            s=150,
            zorder=6,
            label=f"Pico: {result.pico_temperatura:.2f}°C",
            marker="*",
        )

        # Linha vertical — tempo até 55°C
        if tempo_55 is not None:
            ax_temp.axvline(
                tempo_55,
                color="#00BFFF",
                linestyle=":",
                linewidth=2.0,
                alpha=0.8,
                label=f"Tempo até 55°C: {_formatar_tempo_min_seg(tempo_55)}",
            )

        # Linha vertical — tempo do pico
        if tempo_pico is not None:
            ax_temp.axvline(
                tempo_pico,
                color="#FFD700",
                linestyle=":",
                linewidth=2.0,
                alpha=0.8,
                label=f"Tempo do pico: {_formatar_tempo_min_seg(tempo_pico)}",
            )

        ax_temp.set_xlabel("Tempo (s)", color=self.TEXT_PRIMARY, fontsize=12, fontweight="bold")
        ax_temp.set_ylabel("Temperatura (°C)", color=self.TEXT_PRIMARY, fontsize=12, fontweight="bold")

        delta_t = metricas["delta_t_c"]
        tempo_atuacao_min = float(metricas["tempo_atuacao_pcm_s"] or 0.0) / 60.0
        info_text = f"ΔT = {delta_t:.2f}°C  |  Atuação PCM: {tempo_atuacao_min:.1f} min"
        ax_temp.text(
            0.02,
            0.95,
            info_text,
            transform=ax_temp.transAxes,
            color="#E5E7EB",
            fontsize=11,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, alpha=0.8),
            verticalalignment="top",
            zorder=10,
        )

        ax_temp.legend(
            loc="lower right",
            fontsize=10,
            framealpha=0.95,
            facecolor=self.CARD_COLOR,
            edgecolor=self.BORDER_COLOR,
            labelcolor=self.TEXT_PRIMARY,
            frameon=True,
        )

        figure.subplots_adjust(left=0.08, right=0.95, top=0.93, bottom=0.1)

        canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self.chart_canvases.append(canvas)

    def _clear_charts(self) -> None:
        for canvas in self.chart_canvases:
            canvas.get_tk_widget().destroy()
        self.chart_canvases.clear()

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _write_text(self, textbox: ctk.CTkTextbox, content: str) -> None:
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")

    def _format_preview_table(self, preview_rows: list[dict[str, str]]) -> str:
        if not preview_rows:
            return "Nenhum dado disponivel para exibicao."

        headers = ["timestamp", "tempo_s", "potencia_w", "temperatura_c", "energia_j"]
        widths: dict[str, int] = {header: len(header) for header in headers}

        for row in preview_rows:
            for header in headers:
                widths[header] = max(widths[header], len(str(row.get(header, ""))))

        header_line = "  ".join(header.ljust(widths[header]) for header in headers)
        separator_line = "  ".join("-" * widths[header] for header in headers)
        data_lines = [
            "  ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)
            for row in preview_rows
        ]
        return "\n".join([header_line, separator_line, *data_lines])
    
    
      


    def render_sensor_chart(self, result: SensorPCMResult):
        figure = Figure(figsize=(12, 6), dpi=100)
        ax = figure.add_subplot(111)

        ax.set_title("Sensor PCM — Temperatura × Tempo", fontsize=14)

        ax.plot(
            result.tempo_s,
            result.temperatura_c,
            label="Temperatura filtrada",
            linewidth=2,
            color="#FF5733",
        )

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Temperatura (°C)")
        ax.legend()

        canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
        canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        canvas.draw()
        
    def _build_sensor_section(self) -> None:
        """Constrói toda a seção do sensor abaixo do dashboard principal."""
    
        # ── Divisor visual ────────────────────────────────────────────────────
        divider = ctk.CTkFrame(self.scroll_frame, fg_color=self.BORDER_COLOR, height=1)
        divider.grid(row=5, column=0, sticky="ew", padx=12, pady=(8, 20))
    
        # ── Header da seção sensor ────────────────────────────────────────────
        sensor_header = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        sensor_header.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 16))
        sensor_header.grid_columnconfigure(0, weight=1)
    
        ctk.CTkLabel(
            sensor_header,
            text="Sensor Infravermelho — Absorção de Calor do PCM",
            font=("Arial", 26, "bold"),
            text_color=self.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 6))
    
        ctk.CTkLabel(
            sensor_header,
            text=(
                "Importa o log do sensor infravermelho e plota o gráfico de absorção de calor "
                "(Joules × Tempo). Usa temperatura simulada (+10%) para cálculo energético via Q = m·c·ΔT."
            ),
            font=("Arial", 13),
            text_color=self.TEXT_SECONDARY,
            wraplength=1080,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))
    
        sensor_actions = ctk.CTkFrame(sensor_header, fg_color="transparent")
        sensor_actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=24, pady=18)
    
        self.sensor_import_button = ctk.CTkButton(
            sensor_actions,
            text="Importar Log do Sensor",
            command=self.import_sensor_csv,
            width=210,
            height=42,
            fg_color="#1D4ED8",
            hover_color="#1E40AF",
            font=("Arial", 15, "bold"),
        )
        self.sensor_import_button.pack()
    
        self.sensor_status_label = ctk.CTkLabel(
            sensor_header,
            text="Aguardando log do sensor infravermelho (.csv).",
            font=("Arial", 13),
            text_color=self.TEXT_SECONDARY,
        )
        self.sensor_status_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=24, pady=(0, 18))
    
        # ── KPI cards do sensor ───────────────────────────────────────────────
        self.sensor_kpi_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sensor_kpi_frame.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 16))
        for col in range(4):
            self.sensor_kpi_frame.grid_columnconfigure(col, weight=1, uniform="skpi")
    
        sensor_kpi_defs = [
            ("Pico de Temperatura",   "--",  "Pico de temperatura simulada registrado pelo sensor (°C)."),
            ("Tempo de Absorção",     "--",  "Tempo total de experimento com absorção de calor (min)."),
            ("Energia Total Absorvida", "--", "Q = m·c·ΔT  (m=1 kg, c=2000 J/kg·°C)."),
            ("Tempo Atuação PCM",     "--",  "Tempo em que a temperatura simulada ficou entre 50–60 °C (min)."),
            ("Temperatura Média",     "--",  "Temperatura simulada média ao longo do ensaio (°C)."),
            ("Temperatura Inicial",   "--",  "Temperatura simulada no início do ensaio (°C)."),
            ("ΔT Total",              "--",  "Variação total: T_pico − T_inicial (°C)."),
            ("Taxa de Aquecimento",   "--",  "ΔT / duração  (°C/min)."),
        ]
        for idx, (key, default, tip) in enumerate(sensor_kpi_defs):
            self._create_sensor_kpi_card(idx, key, default, tooltip=tip)
    
        # ── Gráfico do sensor ─────────────────────────────────────────────────
        self.sensor_chart_section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sensor_chart_section.grid(row=8, column=0, sticky="ew", padx=12, pady=(0, 24))
        self.sensor_chart_section.grid_columnconfigure(0, weight=1)
    
        self._render_sensor_placeholder()
 
 
    def _create_sensor_kpi_card(self, index: int, title: str, default: str, *, tooltip: str) -> None:
        card = ctk.CTkFrame(
            self.sensor_kpi_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=16,
            border_width=1,
            border_color="#1E3A5F",
        )
        row, col = divmod(index, 4)
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
    
        # Barra de acento no topo do card
        accent = ctk.CTkFrame(card, fg_color="#1D4ED8", height=3, corner_radius=0)
        accent.pack(fill="x", pady=(0, 0))
    
        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 12, "bold"),
            text_color="#93C5FD",
        )
        title_lbl.pack(anchor="w", padx=14, pady=(10, 4))
    
        # Tooltip inline simples
        try:
            from pcm_module.pcm_screen import _Tooltip
            _Tooltip(title_lbl, tooltip)
        except Exception:
            pass
    
        value_lbl = ctk.CTkLabel(
            card,
            text=default,
            font=("Arial", 20, "bold"),
            text_color=self.TEXT_PRIMARY,
            justify="left",
            wraplength=280,
        )
        value_lbl.pack(anchor="w", padx=14, pady=(0, 12))
        self.sensor_kpi_values[title] = value_lbl
    
    
    def _render_sensor_placeholder(self) -> None:
        self._clear_sensor_charts()
        fig = Figure(figsize=(12.0, 6.0), dpi=100)
        fig.patch.set_facecolor(self.PANEL_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.CARD_COLOR)
        ax.text(
            0.5, 0.5,
            "Gráficos de Temperatura e Energia aparecerão aqui após importar o log.",
            ha="center", va="center", fontsize=13, color=self.TEXT_SECONDARY,
            style="italic",
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ["top", "right", "bottom", "left"]:
            ax.spines[side].set_color(self.BORDER_COLOR)
        canvas = FigureCanvasTkAgg(fig, master=self.sensor_chart_section)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self.sensor_chart_canvases.append(canvas)
    
    
    def import_sensor_csv(self) -> None:
        initial_path = os.path.expanduser("~")
        file_path = filedialog.askopenfilename(
            initialdir=initial_path,
            title="Selecionar log do sensor (.csv)",
            filetypes=[("Arquivos CSV", "*.csv")],
        )
        if not file_path:
            return
        try:
            result = self.sensor.load_csv(file_path)
        except Exception as exc:
            messagebox.showerror("Falha ao processar log do sensor", str(exc))
            self.sensor_status_label.configure(
                text="Falha ao processar o arquivo selecionado.",
                text_color=self.TEXT_PRIMARY,
            )
            return
        self.sensor_result = result
        self.sensor_status_label.configure(
            text=f"Log processado: {os.path.basename(file_path)}",
            text_color=self.SUCCESS_COLOR,
        )
        self._update_sensor_dashboard(result)
 
    
    def _update_sensor_dashboard(self, r: "SensorPCMResult") -> None:
        """Atualiza os KPI cards do sensor IR."""

        dur_min = r.tempo_total / 60.0
        delta_t = r.pico_temperatura - r.temperatura_inicial
        taxa = delta_t / dur_min if dur_min > 0 else 0.0
        atuacao_min = r.tempo_atuacao_pcm_s / 60.0

        # ── Métricas principais ─────────────────────────────────────
        self.sensor_kpi_values["Energia PCM"].configure(
            text=f"{r.energia_total_j:,.0f} J"
        )

        self.sensor_kpi_values["Eficiência Térmica"].configure(
        text=f"{r.eficiencia_termica:.1f} %"
        )

        self.sensor_kpi_values["ΔT Experimental"].configure(
            text=f"{delta_t:.2f} °C"
        )

        self.sensor_kpi_values["Energia Referência"].configure(
            text="234000 J"
        )

        self.sensor_kpi_values["Erro Experimental"].configure(
            text=f"{r.erro_percentual:.1f} %"
        )

        self.sensor_kpi_values["Estado PCM"].configure(
            text=r.estado_pcm
        )
        # ── Estabilização ───────────────────────────────────────────
        if r.tempo_estabilizacao_s > 0:
            txt_estab = f"{r.tempo_estabilizacao_s / 60.0:.2f} min"
        else:
            txt_estab = "--"
        self.sensor_kpi_values["Tempo Estabilização"].configure(
            text=txt_estab
        )
        # ── Comparação COM vs SEM PCM ──────────────────────────────

        eficiencia = (
            f"{r.eficiencia_relativa:.2f} %"
            if r.eficiencia_relativa is not None
            else "--"
        )

        self.sensor_kpi_values["Eficiência Relativa"].configure(
            text=eficiencia
        )

        reducao = (
            f"{r.reducao_pico_c:.2f} °C"
            if r.reducao_pico_c is not None
            else "--"
        )

        self.sensor_kpi_values["Redução de Pico"].configure(
            text=reducao
        )

        atraso = (
            f"{r.atraso_termico_s:.0f} s"
            if r.atraso_termico_s is not None
            else "--"
        )

        self.sensor_kpi_values["Atraso Térmico"].configure(
            text=atraso
        )

        # ── Renderizações ──────────────────────────────────────────

        self._render_sensor_charts(r)
        self._update_comparison_section(r)
   
    def _smooth(values: list[float], window: int = 7) -> list[float]:
        if not values:
            return []

        series = pd.Series(values)

        return (
            series
            .rolling(window=window, center=True, min_periods=1)
            .mean()
            .tolist()
    )
    
    def _render_sensor_charts(self, r: "SensorPCMResult") -> None:
        """Renderiza gráficos científicos do sensor IR."""

        self._clear_sensor_charts()

        fig = Figure(figsize=(13.5, 10.5), dpi=100)
        fig.patch.set_facecolor(self.PANEL_COLOR)

        gs = fig.add_gridspec(
            2,
            1,
            height_ratios=[1.15, 0.85],
            hspace=0.34,
        )

        # ─────────────────────────────────────────────────────────────
        # Dados
        # ─────────────────────────────────────────────────────────────

        t_min = [v / 60.0 for v in r.tempo_s]

        T = list(r.temperatura_c)

        # Suavização leve
        T_smooth = _smooth(T, window=7)
       
        # Energia acumulada via Q = m·c·ΔT (m=1 kg, c=2000 J/kg·°C)# ─────────────────────────────────────────────
    # Energia acumulada REALISTA
    # ─────────────────────────────────────────────

        massa_pcm = 0.020   # 20 g
        cp_pcm = 2000       # J/kg°C

        Q_acumulada = [0.0]

        for i in range(1, len(T_smooth)):

            dT = T_smooth[i] - T_smooth[i - 1]

            # Energia incremental
            dQ = massa_pcm * cp_pcm * max(dT, 0)

            # Região de fusão → absorção extra
            if TEMP_FUSAO_PCM <= T_smooth[i] <= TEMP_SATURACAO_PCM:
                dQ *= 2.8

            # Saturação → reduz absorção
            elif T_smooth[i] > TEMP_SATURACAO_PCM:
                dQ *= 0.45

            Q_acumulada.append(Q_acumulada[-1] + dQ)

        Q_smooth = _smooth(Q_acumulada, window=11)


        # ─────────────────────────────────────────────────────────────
        # GRÁFICO 1 — TEMPERATURA
        # ─────────────────────────────────────────────────────────────

        ax1 = fig.add_subplot(gs[0])

        _style_ax(
            ax1,
            self.PANEL_COLOR,
            self.CARD_COLOR,
            self.BORDER_COLOR,
            self.TEXT_SECONDARY,
        )

        ax1.set_title(
            "Resposta Térmica do PCM",
            fontsize=17,
            fontweight="bold",
            color=self.TEXT_PRIMARY,
            pad=18,
        )

        # Região de atuação do PCM
        ax1.axhspan(
            TEMP_FUSAO_PCM,
            TEMP_SATURACAO_PCM,
            color=SENSOR_FUSION,
            alpha=0.10,
            zorder=1,
        )

        ax1.text(
            0.012,
            0.93,
            f"Faixa PCM: {TEMP_FUSAO_PCM:.0f}–{TEMP_SATURACAO_PCM:.0f} °C",
            transform=ax1.transAxes,
            fontsize=10,
            color=SENSOR_FUSION,
            fontweight="bold",
        )

        # Linha principal COM PCM
        ax1.plot(
            t_min,
            T_smooth,
            color=SENSOR_ACCENT,
            linewidth=3.0,
            label="Com PCM",
            zorder=5,
        )

        # Área térmica
        ax1.fill_between(
            t_min,
            T_smooth,
            min(T_smooth) - 2,
            color=SENSOR_ACCENT,
            alpha=0.12,
            zorder=2,
        )

        # Baseline sem PCM
        if r.baseline_temp_c:

            t_base = [v / 60.0 for v in r.baseline_tempo_s]

            ax1.plot(
                t_base,
                r.baseline_temp_c,
                color="#F87171",
                linewidth=2.0,
                linestyle="--",
                alpha=0.85,
                label="Sem PCM",
                zorder=4,
            )

        # Pico térmico
        t_pico = r.tempo_pico_s / 60.0

        ax1.scatter(
            [t_pico],
            [r.pico_temperatura],
            s=180,
            color="#FFD700",
            edgecolors="white",
            linewidths=1.8,
            zorder=10,
        )

        ax1.axvline(
            t_pico,
            linestyle=":",
            linewidth=1.4,
            color="#FFD700",
            alpha=0.75,
        )

        ax1.annotate(
            f"{r.pico_temperatura:.1f} °C",
            xy=(t_pico, r.pico_temperatura),
            xytext=(12, 14),
            textcoords="offset points",
            fontsize=10,
            color=self.TEXT_PRIMARY,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor=self.CARD_COLOR,
                edgecolor="#FFD700",
                alpha=0.95,
            ),
        )

        # Informações rápidas
        delta_t = r.pico_temperatura - r.temperatura_inicial

        resumo = (
            f"ΔT: {delta_t:.2f} °C\n"
            f"Estado: {r.estado_pcm}\n"
            f"Atuação PCM: {r.tempo_atuacao_pcm_s / 60:.1f} min"
        )

        ax1.text(
            0.985,
            0.97,
            resumo,
            transform=ax1.transAxes,
            ha="right",
            va="top",
            fontsize=10.5,
            color=self.TEXT_PRIMARY,
            bbox=dict(
                boxstyle="round,pad=0.55",
                facecolor=self.CARD_COLOR,
                edgecolor=self.BORDER_COLOR,
                alpha=0.92,
            ),
        )

        ax1.set_xlabel(
            "Tempo (min)",
            fontsize=12,
            fontweight="bold",
            color=self.TEXT_PRIMARY,
        )

        ax1.set_ylabel(
            "Temperatura (°C)",
            fontsize=12,
            fontweight="bold",
            color=self.TEXT_PRIMARY,
        )

        ax1.legend(
            loc="lower right",
            fontsize=10,
            framealpha=0.95,
            facecolor=self.CARD_COLOR,
            edgecolor=self.BORDER_COLOR,
        )

        # ─────────────────────────────────────────────────────────────
        # GRÁFICO 2 — ENERGIA
        # ─────────────────────────────────────────────────────────────

        ax2 = fig.add_subplot(gs[1])

        _style_ax(
            ax2,
            self.PANEL_COLOR,
            self.CARD_COLOR,
            self.BORDER_COLOR,
            self.TEXT_SECONDARY,
        )

        ax2.set_title(
            "Energia Absorvida pelo PCM",
            fontsize=16,
            fontweight="bold",
            color=self.TEXT_PRIMARY,
            pad=16,
        )

        ax2.plot(
            t_min,
            Q_smooth,
            color="#22C55E",
            linewidth=3.4,
            alpha=0.95,
            zorder=5,
        )

        ax2.scatter(
            t_min,
            Q_smooth,
            c=Q_smooth,
            cmap="summer",
            s=14,
            alpha=0.6,
            zorder=4,
        )

        ax2.fill_between(
            t_min,
            Q_smooth,
            min(Q_smooth),
            0,
            color=SENSOR_ENERGY,
            alpha=0.16,
            zorder=2,
        )

        # Pico energia
        Q_max = max(Q_smooth)

        idx_q = Q_smooth.index(Q_max)

        ax2.scatter(
            [t_min[idx_q]],
            [Q_max],
            color="#FFD700",
            s=160,
            edgecolors="white",
            linewidths=1.8,
            zorder=10,
        )

        # Texto energia
        ax2.text(
            0.985,
            0.96,
            f"Energia total\n{r.energia_total_j:,.0f} J",
            transform=ax2.transAxes,
            ha="right",
            va="top",
            fontsize=11,
            color=self.TEXT_PRIMARY,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=self.CARD_COLOR,
                edgecolor=self.BORDER_COLOR,
                alpha=0.92,
            ),
        )

        ax2.set_xlabel(
            "Tempo (min)",
            fontsize=12,
            fontweight="bold",
            color=self.TEXT_PRIMARY,
        )

        ax2.set_ylabel(
            "Energia (J)",
            fontsize=12,
            fontweight="bold",
            color=self.TEXT_PRIMARY,
        )

        # ─────────────────────────────────────────────────────────────
        # Render
        # ─────────────────────────────────────────────────────────────

        canvas = FigureCanvasTkAgg(
            fig,
            master=self.sensor_chart_section,
        )

        canvas.get_tk_widget().grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        canvas.draw_idle()

        self.sensor_chart_canvases.append(canvas)
 
    
    def _clear_sensor_charts(self) -> None:
        for canvas in self.sensor_chart_canvases:
            canvas.get_tk_widget().destroy()
        self.sensor_chart_canvases.clear()
 
    def _build_comparison_section(self) -> None:
        """
        Constrói a seção de Comparação COM PCM × SEM PCM.
        Inclui: gráfico de curvas sobrepostas + tabela de métricas.
        """
    
        # ── Header ────────────────────────────────────────────────────────────
        comp_header = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color="#065F46",  # borda verde escura para diferenciar
        )
        comp_header.grid(row=9, column=0, sticky="ew", padx=12, pady=(8, 12))
        comp_header.grid_columnconfigure(0, weight=1)
    
        ctk.CTkLabel(
            comp_header,
            text="⚖  Comparação Térmica — Com PCM × Sem PCM",
            font=("Arial", 24, "bold"),
            text_color="#6EE7B7",   # verde esmeralda
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))
    
        ctk.CTkLabel(
            comp_header,
            text=(
                "Simulação baseada no dado real do sensor. "
                "A curva 'Sem PCM' é estimada usando a taxa de aquecimento medida antes da fusão, "
                "projetando o comportamento sem absorção latente. "
                "Permite quantificar atraso térmico, redução de pico e eficiência do PCM."
            ),
            font=("Arial", 13),
            text_color=self.TEXT_SECONDARY,
            wraplength=1060,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))
    
        # ── Gráfico comparativo ───────────────────────────────────────────────
        self.comparison_chart_section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.comparison_chart_section.grid(row=10, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.comparison_chart_section.grid_columnconfigure(0, weight=1)
        self.comparison_chart_canvases: list[FigureCanvasTkAgg] = []
    
        self._render_comparison_placeholder()
    
        # ── Tabela de métricas comparativas ───────────────────────────────────
        table_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=16,
            border_width=1,
            border_color="#064E3B",
        )
        table_frame.grid(row=11, column=0, sticky="ew", padx=12, pady=(0, 28))
        table_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
    
        ctk.CTkLabel(
            table_frame,
            text="Métricas Comparativas",
            font=("Arial", 17, "bold"),
            text_color="#6EE7B7",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=22, pady=(16, 12))
    
        # Cabeçalho
        headers_comp = ["Métrica", "Com PCM", "Sem PCM", "Diferença"]
        header_colors = ["#6B7280", "#60A5FA", "#F87171", "#A3E635"]
        for col_i, (h, hc) in enumerate(zip(headers_comp, header_colors)):
            ctk.CTkLabel(
                table_frame,
                text=h,
                font=("Arial", 13, "bold"),
                text_color=hc,
            ).grid(row=1, column=col_i, sticky="w", padx=16, pady=(0, 8))
    
        # Separador
        sep = ctk.CTkFrame(table_frame, fg_color=self.BORDER_COLOR, height=1)
        sep.grid(row=2, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 8))
    
        # Linhas de dados — preenchidas dinamicamente
        self._comp_table_rows: list[list[ctk.CTkLabel]] = []
        metric_names = [
            "Pico Térmico (°C)",
            "Taxa Aquecimento (°C/min)",
            "Tempo até Fusão (min)",
            "Atraso Térmico (s)",
            "Energia Absorvida (J)",
            "Eficiência PCM (%)",
        ]
        for row_i, name in enumerate(metric_names):
            bg = self.CARD_COLOR if row_i % 2 == 0 else self.PANEL_COLOR
            row_labels: list[ctk.CTkLabel] = []
            for col_i in range(4):
                text = name if col_i == 0 else "--"
                color = self.TEXT_PRIMARY if col_i == 0 else self.TEXT_SECONDARY
                lbl = ctk.CTkLabel(
                    table_frame,
                    text=text,
                    font=("Arial", 13, "bold" if col_i == 0 else "normal"),
                    text_color=color,
                    fg_color=bg,
                    corner_radius=4,
                )
                lbl.grid(row=row_i + 3, column=col_i, sticky="ew", padx=16, pady=3)
                row_labels.append(lbl)
            self._comp_table_rows.append(row_labels)
    
        # Nota metodológica
        ctk.CTkLabel(
            table_frame,
            text=(
                "★  Curva 'Sem PCM' estimada por extrapolação linear da taxa de aquecimento pré-fusão. "
                "Os valores são aproximações baseadas no comportamento observado antes da atuação do PCM."
            ),
            font=("Arial", 11),
            text_color="#6B7280",
            wraplength=1000,
            justify="left",
        ).grid(row=9, column=0, columnspan=4, sticky="w", padx=22, pady=(12, 16))
    
 
    def _render_comparison_placeholder(self) -> None:
        """Placeholder do gráfico comparativo."""
        for c in getattr(self, "comparison_chart_canvases", []):
            c.get_tk_widget().destroy()
        if hasattr(self, "comparison_chart_canvases"):
            self.comparison_chart_canvases.clear()
    
        fig = Figure(figsize=(13.0, 5.5), dpi=100)
        fig.patch.set_facecolor(self.PANEL_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.CARD_COLOR)
        ax.text(
            0.5, 0.5,
            "Gráfico Com PCM × Sem PCM aparecerá aqui após importar o log.",
            ha="center", va="center", fontsize=13,
            color=self.TEXT_SECONDARY, style="italic",
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ["top", "right", "bottom", "left"]:
            ax.spines[side].set_color("#065F46")
        canvas = FigureCanvasTkAgg(fig, master=self.comparison_chart_section)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self.comparison_chart_canvases.append(canvas)
    
    def _update_comparison_section(self, r: "SensorPCMResult") -> None:
        """
        Gera a curva 'Sem PCM' por extrapolação e atualiza gráfico + tabela.
    
        Metodologia:
        ─────────────
        • Encontra a taxa de aquecimento pré-fusão (segmento antes de TEMP_FUSAO_PCM)
        • Extrapola uma reta a partir da temperatura inicial com essa taxa
        • Sobrepõe a curva real (Com PCM) para comparação visual
    
        É uma estimativa física conservadora — mostra o que aconteceria se
        o PCM não absorvesse calor latente.
        """
        # Limpa gráficos anteriores
        for c in getattr(self, "comparison_chart_canvases", []):
            c.get_tk_widget().destroy()
        if hasattr(self, "comparison_chart_canvases"):
            self.comparison_chart_canvases.clear()
    
        t_s  = list(r.tempo_s)
        T_s  = list(r.temperatura_c)
        t_min = [v / 60.0 for v in t_s]
    
        # ── Estima taxa de aquecimento pré-fusão ──────────────────────────────
        taxa_pre_fusao = 0.0
        pre_fusao_t: list[float] = []
        pre_fusao_T: list[float] = []
        for t_v, T_v in zip(t_s, T_s):
            if T_v >= TEMP_FUSAO_PCM:
                break
            pre_fusao_t.append(t_v)
            pre_fusao_T.append(T_v)
    
        if len(pre_fusao_t) >= 2:
            dt_seg = pre_fusao_t[-1] - pre_fusao_t[0]
            dT_seg = pre_fusao_T[-1] - pre_fusao_T[0]
            taxa_pre_fusao = dT_seg / dt_seg if dt_seg > 0 else 0.0  # °C/s
    
        # ── Curva sem PCM (extrapolação linear) ───────────────────────────────
        T_ini = r.temperatura_inicial
        T_sem_pcm = [T_ini + taxa_pre_fusao * tv for tv in t_s]
    
        # Suaviza curva real
        T_com_pcm_suave = _smooth(T_s, window=11)
        T_sem_pcm_suave = _smooth(T_sem_pcm, window=11)
    
        pico_com = max(T_com_pcm_suave)
        pico_sem = max(T_sem_pcm_suave)
        delta_pico = pico_sem - pico_com
    
        # ── Calcula atraso térmico ────────────────────────────────────────────
        # Tempo para a curva SEM PCM atingir o pico real da curva COM PCM
        alvo = pico_com
        t_com_alvo = None
        t_sem_alvo = None
        for tv, Tv in zip(t_s, T_com_pcm_suave):
            if Tv >= alvo:
                t_com_alvo = tv
                break
        for tv, Tv in zip(t_s, T_sem_pcm_suave):
            if Tv >= alvo:
                t_sem_alvo = tv
                break
    
        atraso_s = None
        if t_com_alvo is not None and t_sem_alvo is not None:
            atraso_s = t_com_alvo - t_sem_alvo
    
        # ── Tempo até fusão com PCM ───────────────────────────────────────────
        t_fusao_min = None
        for tv, Tv in zip(t_min, T_s):
            if Tv >= TEMP_FUSAO_PCM:
                t_fusao_min = tv
                break
    
        # Taxa de aquecimento
        dur_min = r.tempo_total / 60.0
        delta_t_real = r.pico_temperatura - T_ini
        taxa_com = delta_t_real / dur_min if dur_min > 0 else 0.0
        taxa_sem = (taxa_pre_fusao * 60.0)  # converte para °C/min
    
        eficiencia = getattr(r, "eficiencia_relativa", None)
    
        # ══════════════════════════════════════════════════════════════════════
        # GRÁFICO COMPARATIVO
        # ══════════════════════════════════════════════════════════════════════
        fig = Figure(figsize=(13.0, 6.0), dpi=100)
        fig.patch.set_facecolor(self.PANEL_COLOR)
        fig.subplots_adjust(left=0.08, right=0.96, top=0.92, bottom=0.10)
    
        ax = fig.add_subplot(111)
        _style_ax(ax, self.PANEL_COLOR, self.CARD_COLOR, self.BORDER_COLOR, self.TEXT_SECONDARY)
    
        ax.set_title(
            "Comparação Térmica — Com PCM × Sem PCM",
            color="#6EE7B7", fontsize=15, fontweight="bold", pad=14,
        )
    
        # Região de fusão
        ax.axhspan(
            TEMP_FUSAO_PCM, TEMP_SATURACAO_PCM,
            color=SENSOR_FUSION, alpha=0.10, zorder=1,
            label=f"Região de fusão PCM ({TEMP_FUSAO_PCM}–{TEMP_SATURACAO_PCM} °C)",
        )
        ax.axhline(TEMP_FUSAO_PCM, color=SENSOR_FUSION, linewidth=0.8,
                linestyle="--", alpha=0.50, zorder=2)
    
        # Área entre as curvas — destaca a economia térmica
        ax.fill_between(
            t_min, T_sem_pcm_suave, T_com_pcm_suave,
            where=[s > c for s, c in zip(T_sem_pcm_suave, T_com_pcm_suave)],
            color="#34D399", alpha=0.18, zorder=2,
            label="Calor absorvido pelo PCM (área)",
        )
    
        # Curva COM PCM
        ax.plot(t_min, T_com_pcm_suave,
                color=COLOR_WITH_PCM, linewidth=3.0, alpha=0.95, zorder=4,
                label=f"Com PCM  (pico: {pico_com:.1f} °C)")
    
        # Curva SEM PCM
        ax.plot(t_min, T_sem_pcm_suave,
                color=COLOR_WITHOUT_PCM, linewidth=2.6, alpha=0.88,
                linestyle="--", zorder=4,
                label=f"Sem PCM  (pico: {pico_sem:.1f} °C, estimado)")
    
        # Marcadores de pico
        idx_com = T_com_pcm_suave.index(pico_com)
        idx_sem = T_sem_pcm_suave.index(pico_sem)
        ax.scatter([t_min[idx_com]], [pico_com],
                color=COLOR_WITH_PCM, edgecolors="white", s=180, zorder=7,
                marker="*", linewidths=1.4)
        ax.scatter([t_min[idx_sem]], [pico_sem],
                color=COLOR_WITHOUT_PCM, edgecolors="white", s=180, zorder=7,
                marker="*", linewidths=1.4)
    
        # Anotação de redução de pico
        if delta_pico > 0.5:
            mid_t = t_min[idx_sem]
            ax.annotate(
                f"Redução: {delta_pico:.1f} °C",
                xy=(mid_t, pico_com + delta_pico / 2),
                xytext=(mid_t + 2, pico_com + delta_pico / 2 + 2),
                fontsize=10, color="#A3E635", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#A3E635", lw=1.4),
                bbox=dict(boxstyle="round,pad=0.3",
                        facecolor=self.CARD_COLOR, edgecolor="#A3E635", alpha=0.85),
                zorder=8,
            )
    
        # Linha de atraso térmico
        if atraso_s is not None and t_sem_alvo is not None and t_com_alvo is not None:
            t_sem_min = t_sem_alvo / 60.0
            t_com_min = t_com_alvo / 60.0
            ax.annotate(
                "",
                xy=(t_com_min, alvo),
                xytext=(t_sem_min, alvo),
                arrowprops=dict(
                    arrowstyle="<->", color="#FCD34D", lw=1.8,
                ),
                zorder=8,
            )
            ax.text(
                (t_sem_min + t_com_min) / 2,
                alvo + 0.5,
                f"Atraso: {abs(atraso_s):.0f} s",
                ha="center", fontsize=9.5, color="#FCD34D", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25",
                        facecolor=self.CARD_COLOR, edgecolor="#FCD34D", alpha=0.80),
                zorder=9,
            )
    
        # Info box
        info_parts = [f"Δpico = {delta_pico:.1f} °C"]
        if atraso_s is not None:
            info_parts.append(f"Atraso = {abs(atraso_s):.0f} s")
        if eficiencia is not None:
            info_parts.append(f"η PCM = {eficiencia:.1f} %")
        ax.text(
            0.02, 0.96,
            "   |   ".join(info_parts),
            transform=ax.transAxes, color="#E5E7EB",
            fontsize=10.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5",
                    facecolor=self.CARD_COLOR, edgecolor="#065F46", alpha=0.90),
            va="top", zorder=10,
        )
    
        ax.set_xlabel("Tempo (min)", color=self.TEXT_PRIMARY, fontsize=12, fontweight="bold")
        ax.set_ylabel("Temperatura (°C)", color=self.TEXT_PRIMARY, fontsize=12, fontweight="bold")
        ax.legend(
            loc="upper left", fontsize=10,
            framealpha=0.92, facecolor=self.CARD_COLOR,
            edgecolor="#065F46", labelcolor=self.TEXT_PRIMARY,
            frameon=True,
        )
    
        canvas = FigureCanvasTkAgg(fig, master=self.comparison_chart_section)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self.comparison_chart_canvases.append(canvas)
    
        # ══════════════════════════════════════════════════════════════════════
        # TABELA DE MÉTRICAS COMPARATIVAS
        # ══════════════════════════════════════════════════════════════════════
        if not hasattr(self, "_comp_table_rows") or not self._comp_table_rows:
            return
    
        def _fmt_diff(val: float | None, invert: bool = False) -> tuple[str, str]:
            """Formata diferença com cor: verde = melhor com PCM."""
            if val is None:
                return "--", self.TEXT_SECONDARY
            sign = "+" if val > 0 else ""
            color = "#6EE7B7" if (val < 0 if not invert else val > 0) else "#FCA5A5"
            return f"{sign}{val:.1f}", color
    
        rows_data = [
            # (com_pcm, sem_pcm, diferença, invert_color)
            (f"{pico_com:.1f} °C",
            f"{pico_sem:.1f} °C",
            *_fmt_diff(pico_com - pico_sem)),
    
            (f"{taxa_com:.3f} °C/min",
            f"{taxa_sem:.3f} °C/min",
            *_fmt_diff(taxa_com - taxa_sem)),
    
            (f"{t_fusao_min:.1f} min" if t_fusao_min else "--",
            "—",
            "—", self.TEXT_SECONDARY),
    
            (f"{t_com_alvo:.0f} s" if t_com_alvo else "--",
            f"{t_sem_alvo:.0f} s" if t_sem_alvo else "--",
            *_fmt_diff(abs(atraso_s) if atraso_s else None, invert=True)),
    
            (f"{r.energia_total_j:,.0f} J", "—",
            "—", self.TEXT_SECONDARY),
    
            (f"{eficiencia:.1f} %" if eficiencia else "--",
            "—", "—", self.TEXT_SECONDARY),
        ]
    
        for row_labels, row_vals in zip(self._comp_table_rows, rows_data):
            com, sem, diff, diff_color = row_vals
            row_labels[1].configure(text=com, text_color=COLOR_WITH_PCM)
            row_labels[2].configure(text=sem, text_color=COLOR_WITHOUT_PCM)
            row_labels[3].configure(text=diff, text_color=diff_color)
    

# Compatibilidade com integrações anteriores.
PCMScreen = PCMCalcScreen

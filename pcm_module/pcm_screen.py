from __future__ import annotations

import math
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .pcm_model import PCMResult
from .pcm_repository import PCMRepository
from .pcm_service import PCMService


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
    if tempo_s is None:
        return "--"
    tempo_s = max(0.0, float(tempo_s))
    minutos = int(tempo_s // 60)
    segundos = int(round(tempo_s % 60))
    return f"{minutos:02d}:{segundos:02d}"


class _Tooltip:
    def __init__(self, widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._win = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

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
        self.chart_canvases: list[FigureCanvasTkAgg] = []
        self.kpi_values: dict[str, ctk.CTkLabel] = {}
        self.kpi_subvalues: dict[str, ctk.CTkLabel] = {}

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

    def _render_charts(self, result: PCMResult) -> None:
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


# Compatibilidade com integrações anteriores.
PCMScreen = PCMCalcScreen
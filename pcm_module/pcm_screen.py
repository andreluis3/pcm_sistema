from __future__ import annotations

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
    limiar_estabilizacao: float = 0.01,
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

    eficiencia = None
    if float(result.energia_teorica) > 0:
        eficiencia = (float(result.energia_total) / float(result.energia_teorica)) * 100.0

    # Tempo até temperatura alvo.
    tempo_ate_alvo_s = None
    for t, temp in zip(tempo_s, temperatura_c):
        if float(temp) >= float(temperatura_alvo_c):
            tempo_ate_alvo_s = float(t)
            break

    dT_dt = calcular_dT_dt(tempo_s, temperatura_c)
    tempo_estabilizacao_s = calcular_estabilizacao(tempo_s, dT_dt, limiar=limiar_estabilizacao)

    return {
        "duracao_s": duracao_s,
        "duracao_min": duracao_min,
        "pico_temp_c": pico_temp,
        "tempo_pico_s": tempo_pico_s,
        "delta_t_c": delta_t,
        "taxa_aquecimento_c_min": heating_rate_c_por_min,
        "eficiencia_percent": eficiencia,
        "tempo_ate_55c_s": tempo_ate_alvo_s,
        "tempo_estabilizacao_s": tempo_estabilizacao_s,
    }


def _cor_por_temperatura(temperatura_c: float) -> str:
    if temperatura_c < 50.0:
        return "#00C853"  # verde
    if temperatura_c <= 60.0:
        return "#FBBF24"  # amarelo
    return "#EF4444"  # vermelho


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

        frame = ctk.CTkFrame(win, fg_color="#0B1220", corner_radius=10, border_width=1, border_color="#27415F")
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            frame,
            text=self.text,
            font=("Arial", 12),
            text_color="#E6EEF8",
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
    BG_COLOR = "#07111F"
    PANEL_COLOR = "#0D1726"
    CARD_COLOR = "#132238"
    BORDER_COLOR = "#27415F"
    TEXT_PRIMARY = "#E6EEF8"
    TEXT_SECONDARY = "#93A4B8"
    SUCCESS_COLOR = "#63D297"
    TEMP_COLOR = "#F25F5C"
    POWER_COLOR = "#4A90E2"
    ENERGY_COLOR = "#F59E0B"
    ENERGY_FILL = "#2FBF71"

    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=self.BG_COLOR)
        self.service = PCMService()
        self.repository = PCMRepository()
        self.current_result: PCMResult | None = None
        self.chart_canvases: list[FigureCanvasTkAgg] = []
        self.kpi_values: dict[str, ctk.CTkLabel] = {}

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
            hover_color="#3A77BF",
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

        self.kpi_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))
        for column in range(3):
            self.kpi_frame.grid_columnconfigure(column, weight=1, uniform="kpi")
        for row in range(3):
            self.kpi_frame.grid_rowconfigure(row, weight=1, uniform="kpi_row")

        self._kpi_defs: list[dict[str, str]] = [
            {
                "key": "Energia Total Absorvida (J)",
                "default": "--",
                "tooltip": "Energia total integrada ao longo do ensaio (J).",
            },
            {
                "key": "Potência Média (W)",
                "default": "--",
                "tooltip": "Potência média aplicada/observada durante o ensaio (W).",
            },
            {
                "key": "Massa de PCM (g)",
                "default": "--",
                "tooltip": "Massa estimada de PCM necessária para absorver a energia do ensaio (g).",
            },
            {
                "key": "Pico de Temperatura",
                "default": "--",
                "tooltip": "Maior temperatura registrada e o instante em que ocorreu.",
            },
            {
                "key": "Tempo de Estabilização",
                "default": "--",
                "tooltip": "Instante em que |dT/dt| permanece abaixo do limiar por uma janela (s).",
            },
            {
                "key": "ΔT (Variação)",
                "default": "--",
                "tooltip": "Variação térmica total: max(T) − min(T) (°C).",
            },
            {
                "key": "Taxa de Aquecimento",
                "default": "--",
                "tooltip": "Taxa média: ΔT / tempo_total (°C/min).",
            },
            {
                "key": "Eficiência Energética (%)",
                "default": "--",
                "tooltip": "Eficiência: energia_real / energia_teórica × 100 (%).",
            },
            {
                "key": "Duração do Experimento",
                "default": "--",
                "tooltip": "Duração total do ensaio (min).",
            },
        ]
        for index, kpi_def in enumerate(self._kpi_defs):
            self._create_kpi_card(index, kpi_def["key"], kpi_def["default"], tooltip=kpi_def["tooltip"])

        self.chart_section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.chart_section.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 16))
        self.chart_section.grid_columnconfigure(0, weight=1)

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

    def _create_kpi_card(self, index: int, title: str, default_value: str, *, tooltip: str) -> None:
        card = ctk.CTkFrame(
            self.kpi_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        row = index // 3
        col = index % 3
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
            self.status_label.configure(text="Falha ao processar o arquivo selecionado.", text_color="#F87171")
            return

        self.current_result = result
        self.status_label.configure(
            text=f"Arquivo processado com sucesso: {os.path.basename(file_path)}",
            text_color=self.SUCCESS_COLOR,
        )
        self._update_dashboard(result)

    def _update_dashboard(self, result: PCMResult) -> None:
        metricas = calcular_metricas_experimento(result)

        self.kpi_values["Energia Total Absorvida (J)"].configure(text=f"{result.energia_total:.0f} J")
        self.kpi_values["Potência Média (W)"].configure(text=f"{result.potencia_media:.2f} W")
        self.kpi_values["Massa de PCM (g)"].configure(text=f"{result.massa_pcm:.2f} g")

        pico_text = f"{metricas['pico_temp_c']:.2f} °C @ {_formatar_tempo_min_seg(metricas['tempo_pico_s'])}"
        self.kpi_values["Pico de Temperatura"].configure(text=pico_text, text_color=_cor_por_temperatura(result.pico_temperatura))

        tempo_estab = metricas["tempo_estabilizacao_s"]
        self.kpi_values["Tempo de Estabilização"].configure(text=_formatar_tempo_min_seg(tempo_estab))

        self.kpi_values["ΔT (Variação)"].configure(text=f"{metricas['delta_t_c']:.2f} °C")

        taxa = metricas["taxa_aquecimento_c_min"]
        self.kpi_values["Taxa de Aquecimento"].configure(text=f"{taxa:.3f} °C/min" if taxa is not None else "--")

        eficiencia = metricas["eficiencia_percent"]
        self.kpi_values["Eficiência Energética (%)"].configure(text=f"{eficiencia:.1f} %" if eficiencia is not None else "--")

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
        analysis_lines.append(
            f"- Estabilização (|dT/dt|<0.01): {_formatar_tempo_min_seg(metricas['tempo_estabilizacao_s'])}."
        )
        analysis_lines.extend(f"- {line}" for line in result.analise_tecnica)
        analysis_lines.append(f"- Delta de tempo total analisado: {result.delta_tempo:.2f} s.")
        analysis_lines.append(f"- Temperatura media registrada: {result.temperatura_media:.2f} C.")
        analysis_lines.append("")
        analysis_lines.append("[Calculo Detalhado]")
        analysis_lines.extend(f"- {line}" for line in result.calculo_detalhado)
        self._write_text(self.analysis_box, "\n".join(analysis_lines))
        self._write_text(self.log_box, self._format_preview_table(result.csv_preview))
        self._render_charts(result)

    def _render_charts(self, result: PCMResult) -> None:
        self._clear_charts()

        figure = Figure(figsize=(11.8, 7.8), dpi=100)
        figure.patch.set_facecolor(self.PANEL_COLOR)

        axes = [figure.add_subplot(211), figure.add_subplot(212)]
        titles = [
            "Temperatura vs Tempo",
            "dT/dt vs Tempo",
        ]
        y_labels = ["Temperatura (°C)", "dT/dt (°C/s)"]

        for axis, title, ylabel in zip(axes, titles, y_labels):
            axis.set_facecolor(self.CARD_COLOR)
            axis.set_title(title, color=self.TEXT_PRIMARY, fontsize=14, pad=12)
            axis.set_xlabel("Tempo (s)", color=self.TEXT_PRIMARY, fontsize=10)
            axis.set_ylabel(ylabel, color=self.TEXT_PRIMARY, fontsize=10)
            axis.tick_params(colors=self.TEXT_SECONDARY, labelsize=9)
            axis.grid(True, linestyle="--", linewidth=0.6, alpha=0.22, color="#D6E4F0")
            for side in ["top", "right"]:
                axis.spines[side].set_visible(False)
            for side in ["bottom", "left"]:
                axis.spines[side].set_color(self.BORDER_COLOR)

        time_values = result.tempo_s
        temps = result.temperatura_c
        metricas = calcular_metricas_experimento(result)
        tempo_55 = metricas["tempo_ate_55c_s"]
        tempo_pico = metricas["tempo_pico_s"]
        tempo_estab = metricas["tempo_estabilizacao_s"]

        # Faixa de atuação do PCM (50°C a 60°C)
        axes[0].axhspan(50.0, 60.0, color="#FBBF24", alpha=0.12, label="Faixa PCM 50–60°C")

        # Linha de temperatura com cores por faixa (verde/amarelo/vermelho).
        # Mantém implementação simples: linha base + pontos coloridos para realce.
        axes[0].plot(time_values, temps, color="#CBD5E1", linewidth=1.4, alpha=0.55, label="Temperatura (base)")
        cores = [_cor_por_temperatura(float(t)) for t in temps]
        axes[0].scatter(time_values, temps, c=cores, s=10, alpha=0.95, linewidths=0)

        axes[0].plot(
            time_values,
            result.temperatura_media_movel,
            color="#F8B4B4",
            linewidth=1.6,
            linestyle="--",
            label="Media movel",
        )
        axes[0].scatter(
            [result.tempo_pico_temperatura],
            [result.pico_temperatura],
            color="#FFE082",
            edgecolors=self.TEMP_COLOR,
            linewidths=1.5,
            s=85,
            zorder=5,
            label="Pico",
        )
        delta_T = metricas["delta_t_c"]
        axes[0].text(
            0.02,
            0.92,
            f"ΔT = {delta_T:.2f}°C",
            transform=axes[0].transAxes,
            color="#FFE082",
            fontsize=12,
            fontweight="bold",
        )

        if tempo_55 is not None:
            axes[0].axvline(tempo_55, color="#FBBF24", linestyle="--", linewidth=1.6, alpha=0.95, label="Tempo até 55°C")
        if tempo_pico is not None:
            axes[0].axvline(tempo_pico, color="#FFE082", linestyle="--", linewidth=1.6, alpha=0.95, label="Tempo do pico")
        if tempo_estab is not None:
            axes[0].axvline(tempo_estab, color="#63D297", linestyle=":", linewidth=1.8, alpha=0.95, label="Estabilização")

        indicadores = [
            f"t55={_formatar_tempo_min_seg(tempo_55)}",
            f"tpico={_formatar_tempo_min_seg(tempo_pico)}",
            f"testab={_formatar_tempo_min_seg(tempo_estab)}",
        ]
        axes[0].text(
            0.98,
            0.92,
            "  ".join(indicadores),
            transform=axes[0].transAxes,
            ha="right",
            color=self.TEXT_SECONDARY,
            fontsize=10,
        )

        axes[0].legend(facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, labelcolor=self.TEXT_PRIMARY)

        # dT/dt (diferença entre pontos consecutivos).
        dT_dt = calcular_dT_dt(time_values, temps)
        axes[1].plot(time_values[: len(dT_dt)], dT_dt, color="#94A3B8", linewidth=2.0, label="dT/dt")
        axes[1].axhline(0.0, color="#CBD5E1", linewidth=1.0, alpha=0.6)
        axes[1].axhline(0.01, color="#63D297", linestyle="--", linewidth=1.2, alpha=0.85, label="|dT/dt| limiar")
        axes[1].axhline(-0.01, color="#63D297", linestyle="--", linewidth=1.2, alpha=0.85)

        if tempo_estab is not None:
            axes[1].axvline(tempo_estab, color="#63D297", linestyle=":", linewidth=1.8, alpha=0.95, label="Estabilização")
        if tempo_55 is not None:
            axes[1].axvline(tempo_55, color="#FBBF24", linestyle="--", linewidth=1.2, alpha=0.85, label="55°C")
        if tempo_pico is not None:
            axes[1].axvline(tempo_pico, color="#FFE082", linestyle="--", linewidth=1.2, alpha=0.85, label="Pico")

        axes[1].legend(facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, labelcolor=self.TEXT_PRIMARY)

        figure.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.07, hspace=0.34)

        canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
        widget = canvas.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew")
        canvas.draw_idle()
        self.chart_canvases.append(canvas)

    def _clear_charts(self) -> None:
        for canvas in self.chart_canvases:
            canvas.get_tk_widget().destroy()
        self.chart_canvases.clear()

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

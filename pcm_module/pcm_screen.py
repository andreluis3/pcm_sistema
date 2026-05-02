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

    eficiencia = None
    if float(result.energia_teorica) > 0:
        eficiencia = (float(result.energia_total) / float(result.energia_teorica)) * 100.0

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

        self.kpi_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))
        for column in range(4):
            self.kpi_frame.grid_columnconfigure(column, weight=1, uniform="kpi")
        for row in range(2):
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
                "key": "Pico de Temperatura",
                "default": "--",
                "tooltip": "Maior temperatura registrada durante o ensaio (°C).",
            },
            {
                "key": "Tempo de Atuação do PCM",
                "default": "--",
                "tooltip": "Tempo total em que 50°C ≤ T ≤ 60°C (min).",
            },
            {
                "key": "ΔT (Variação)",
                "default": "--",
                "tooltip": "Variação térmica total: max(T) − min(T) (°C).",
            },
            {
                "key": "Eficiência",
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
            self.status_label.configure(text="Falha ao processar o arquivo selecionado.", text_color=self.TEXT_PRIMARY)
            return

        self.current_result = result
        self.status_label.configure(
            text=f"Arquivo processado com sucesso: {os.path.basename(file_path)}",
            text_color=self.SUCCESS_COLOR,
        )
        self._update_dashboard(result)

    def _update_dashboard(self, result: PCMResult) -> None:
        metricas = calcular_metricas_experimento(result)

        self.kpi_values["Energia Total"].configure(text=f"{result.energia_total:.0f} J")
        self.kpi_values["Potência Média"].configure(text=f"{result.potencia_media:.2f} W")
        self.kpi_values["Massa PCM"].configure(text=f"{result.massa_pcm:.2f} g")

        self.kpi_values["Pico de Temperatura"].configure(text=f"{metricas['pico_temp_c']:.0f} °C")
        pico_sub = self.kpi_subvalues["Pico de Temperatura"]
        pico_sub.configure(text=f"t_pico: {_formatar_tempo_min_seg(metricas['tempo_pico_s'])}")
        if not pico_sub.winfo_ismapped():
            pico_sub.pack(anchor="w", padx=18, pady=(0, 16))

        tempo_pcm_min = float(metricas["tempo_atuacao_pcm_s"] or 0.0) / 60.0
        self.kpi_values["Tempo de Atuação do PCM"].configure(text=f"{tempo_pcm_min:.0f} min")
        pcm_sub = self.kpi_subvalues["Tempo de Atuação do PCM"]
        pcm_sub.configure(text="Faixa: 50–60°C")
        if not pcm_sub.winfo_ismapped():
            pcm_sub.pack(anchor="w", padx=18, pady=(0, 16))

        self.kpi_values["ΔT (Variação)"].configure(text=f"{metricas['delta_t_c']:.2f} °C")

        eficiencia = metricas["eficiencia_percent"]
        self.kpi_values["Eficiência"].configure(text=f"{eficiencia:.1f} %" if eficiencia is not None else "--")

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

    def _render_charts(self, result: PCMResult) -> None:
        self._clear_charts()

        figure = Figure(figsize=(11.8, 9.2), dpi=100)
        figure.patch.set_facecolor(self.PANEL_COLOR)

        ax_temp = figure.add_subplot(311)
        ax_hist = figure.add_subplot(312)
        ax_map = figure.add_subplot(313)

        for axis in (ax_temp, ax_hist, ax_map):
            axis.set_facecolor(self.CARD_COLOR)
            axis.tick_params(colors=self.TEXT_SECONDARY, labelsize=9)
            axis.grid(True, linestyle="--", linewidth=0.6, alpha=0.18, color="#9CA3AF")
            for side in ["top", "right"]:
                axis.spines[side].set_visible(False)
            for side in ["bottom", "left"]:
                axis.spines[side].set_color(self.BORDER_COLOR)

        time_values = result.tempo_s
        temps = result.temperatura_c
        if not time_values or not temps:
            ax_temp.set_title("Temperatura vs Tempo", color=self.TEXT_PRIMARY, fontsize=14, pad=12)
            ax_temp.text(
                0.5,
                0.5,
                "Sem dados de temperatura para plotar.",
                transform=ax_temp.transAxes,
                ha="center",
                va="center",
                fontsize=12,
                color=self.TEXT_SECONDARY,
            )
            ax_hist.set_visible(False)
            ax_map.set_visible(False)
            figure.subplots_adjust(left=0.07, right=0.97, top=0.96, bottom=0.06, hspace=0.38)

            canvas = FigureCanvasTkAgg(figure, master=self.chart_section)
            widget = canvas.get_tk_widget()
            widget.grid(row=0, column=0, sticky="nsew")
            canvas.draw_idle()
            self.chart_canvases.append(canvas)
            return

        metricas = calcular_metricas_experimento(result)
        tempo_55 = metricas["tempo_ate_55c_s"]
        tempo_pico = metricas["tempo_pico_s"]

        # --- (1) Temperatura vs Tempo -----------------------------------
        ax_temp.set_title("Temperatura vs Tempo", color=self.TEXT_PRIMARY, fontsize=14, pad=12)
        ax_temp.set_xlabel("Tempo (s)", color=self.TEXT_PRIMARY, fontsize=10)
        ax_temp.set_ylabel("Temperatura (°C)", color=self.TEXT_PRIMARY, fontsize=10)

        # Faixa de atuação do PCM (50°C a 60°C) em tons neutros.
        ax_temp.axhspan(50.0, 60.0, color="#E5E7EB", alpha=0.06, label="Faixa PCM 50–60°C")

        ax_temp.plot(time_values, temps, color="#E5E7EB", linewidth=2.1, alpha=0.95, label="Temperatura")
        if result.temperatura_media_movel:
            ax_temp.plot(
                time_values,
                result.temperatura_media_movel,
                color="#9CA3AF",
                linewidth=1.6,
                linestyle="--",
                alpha=0.9,
                label="Média móvel",
            )

        ax_temp.scatter(
            [result.tempo_pico_temperatura],
            [result.pico_temperatura],
            color="#F3F4F6",
            edgecolors="#9CA3AF",
            linewidths=1.2,
            s=70,
            zorder=5,
            label="Pico",
        )

        ax_temp.text(
            0.02,
            0.92,
            f"ΔT = {metricas['delta_t_c']:.2f}°C",
            transform=ax_temp.transAxes,
            color="#E5E7EB",
            fontsize=12,
            fontweight="bold",
        )

        if tempo_55 is not None:
            ax_temp.axvline(tempo_55, color="#9CA3AF", linestyle="--", linewidth=1.4, alpha=0.9, label="Tempo até 55°C")
        if tempo_pico is not None:
            ax_temp.axvline(tempo_pico, color="#D1D5DB", linestyle="--", linewidth=1.4, alpha=0.9, label="Tempo do pico")

        indicadores = [
            f"t55={_formatar_tempo_min_seg(tempo_55)}",
            f"tpico={_formatar_tempo_min_seg(tempo_pico)}",
            f"tPCM={(float(metricas['tempo_atuacao_pcm_s'] or 0.0) / 60.0):.0f}min",
        ]
        ax_temp.text(
            0.98,
            0.92,
            "  ".join(indicadores),
            transform=ax_temp.transAxes,
            ha="right",
            color=self.TEXT_SECONDARY,
            fontsize=10,
        )
        ax_temp.legend(facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, labelcolor=self.TEXT_PRIMARY)

        # --- (2) Histograma de temperatura (tempo por faixa) ------------
        ax_hist.set_title("Histograma de Temperatura (tempo por faixa)", color=self.TEXT_PRIMARY, fontsize=14, pad=12)
        ax_hist.set_xlabel("Temperatura (°C)", color=self.TEXT_PRIMARY, fontsize=10)
        ax_hist.set_ylabel("Tempo (min)", color=self.TEXT_PRIMARY, fontsize=10)
        ax_hist.axvspan(50.0, 60.0, color="#E5E7EB", alpha=0.06)

        min_temp = float(min(temps))
        max_temp = float(max(temps))
        step = 5.0
        start = math.floor(min_temp / step) * step
        end = math.ceil(max_temp / step) * step
        edges = [start + i * step for i in range(int(round((end - start) / step)) + 1)]
        if len(edges) < 2:
            edges = [min_temp, max_temp]

        # Soma dt por bin usando temperatura média do segmento (aproximação robusta).
        bin_minutes = [0.0 for _ in range(len(edges) - 1)]
        for i in range(1, min(len(time_values), len(temps))):
            t0 = float(time_values[i - 1])
            t1 = float(time_values[i])
            dt = t1 - t0
            if dt <= 0:
                continue
            tmid = 0.5 * (float(temps[i - 1]) + float(temps[i]))
            idx = int((tmid - start) // step)
            idx = max(0, min(idx, len(bin_minutes) - 1))
            bin_minutes[idx] += dt / 60.0

        centers = [(edges[i] + edges[i + 1]) / 2.0 for i in range(len(edges) - 1)]
        ax_hist.bar(centers, bin_minutes, width=step * 0.92, color="#D1D5DB", edgecolor="#9CA3AF", linewidth=0.8)

        # --- (3) Heatmap térmico simples -------------------------------
        ax_map.set_title("Mapa térmico (temperatura ao longo do tempo)", color=self.TEXT_PRIMARY, fontsize=14, pad=12)
        ax_map.set_xlabel("Tempo (s)", color=self.TEXT_PRIMARY, fontsize=10)
        ax_map.set_yticks([])
        ax_map.grid(False)

        # Suaviza para um visual mais "dissipativo" sem distorcer a escala.
        window = 7
        half = window // 2
        temps_smooth: list[float] = []
        for i in range(len(temps)):
            lo = max(0, i - half)
            hi = min(len(temps), i + half + 1)
            temps_smooth.append(sum(float(v) for v in temps[lo:hi]) / float(hi - lo))

        rows = 26
        center = (rows - 1) / 2.0
        sigma = rows / 6.0
        ambient = float(min_temp)
        matrix: list[list[float]] = []
        for r in range(rows):
            w = math.exp(-((r - center) ** 2) / (2.0 * sigma * sigma))
            row_vals = [ambient + (float(t) - ambient) * w for t in temps_smooth]
            matrix.append(row_vals)

        im = ax_map.imshow(
            matrix,
            aspect="auto",
            origin="lower",
            cmap="Greys",
            extent=[float(time_values[0]), float(time_values[len(temps_smooth) - 1]), 0.0, 1.0],
            vmin=min_temp,
            vmax=max_temp,
            interpolation="bilinear",
        )
        cbar = figure.colorbar(im, ax=ax_map, fraction=0.02, pad=0.02)
        cbar.set_label("°C", color=self.TEXT_PRIMARY)
        cbar.ax.yaxis.set_tick_params(color=self.TEXT_SECONDARY)
        for tick in cbar.ax.get_yticklabels():
            tick.set_color(self.TEXT_SECONDARY)

        figure.subplots_adjust(left=0.07, right=0.97, top=0.96, bottom=0.06, hspace=0.38)

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

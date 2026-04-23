from __future__ import annotations

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .pcm_model import PCMResult
from .pcm_repository import PCMRepository
from .pcm_service import PCMService


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
            text="PCM Thermal Engineering Dashboard",
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
        for column in range(5):
            self.kpi_frame.grid_columnconfigure(column, weight=1, uniform="kpi")

        kpis = [
            ("Energia Total", "-- J"),
            ("Potencia Media", "-- W"),
            ("Pico de Potencia", "-- W"),
            ("Pico de Temperatura", "-- C"),
            ("Massa de PCM", "-- g"),
        ]
        for index, (title, value) in enumerate(kpis):
            self._create_kpi_card(index, title, value)

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

    def _create_kpi_card(self, column: int, title: str, default_value: str) -> None:
        card = ctk.CTkFrame(
            self.kpi_frame,
            fg_color=self.PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        card.grid(row=0, column=column, sticky="nsew", padx=6, pady=6)

        ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 14, "bold"),
            text_color=self.TEXT_SECONDARY,
        ).pack(anchor="w", padx=18, pady=(16, 8))

        value_label = ctk.CTkLabel(
            card,
            text=default_value,
            font=("Arial", 24, "bold"),
            text_color=self.TEXT_PRIMARY,
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
        self.kpi_values["Energia Total"].configure(text=f"{result.energia_total:.2f} J")
        self.kpi_values["Potencia Media"].configure(text=f"{result.potencia_media:.2f} W")
        self.kpi_values["Pico de Potencia"].configure(text=f"{result.pico_potencia:.2f} W")
        self.kpi_values["Pico de Temperatura"].configure(text=f"{result.pico_temperatura:.2f} C")
        self.kpi_values["Massa de PCM"].configure(text=f"{result.massa_pcm:.2f} g")

        analysis_lines = [f"- {line}" for line in result.analise_tecnica]
        analysis_lines.append(f"- Delta de tempo total analisado: {result.delta_tempo:.2f} s.")
        analysis_lines.append(f"- Temperatura media registrada: {result.temperatura_media:.2f} C.")
        self._write_text(self.analysis_box, "\n".join(analysis_lines))
        self._write_text(self.log_box, self._format_preview_table(result.csv_preview))
        self._render_charts(result)

    def _render_charts(self, result: PCMResult) -> None:
        self._clear_charts()

        figure = Figure(figsize=(11.8, 9.0), dpi=100)
        figure.patch.set_facecolor(self.PANEL_COLOR)

        axes = [figure.add_subplot(311), figure.add_subplot(312), figure.add_subplot(313)]
        titles = [
            "Temperatura vs Tempo",
            "Potencia vs Tempo",
            "Energia vs Tempo",
        ]
        y_labels = ["Temperatura (C)", "Potencia (W)", "Energia (J)"]
        colors = [self.TEMP_COLOR, self.POWER_COLOR, self.ENERGY_FILL]
        data_series = [result.temperatura_c, result.potencia_w, result.energia_j]
        smooth_series = [
            result.temperatura_media_movel,
            result.potencia_media_movel,
            result.energia_media_movel,
        ]

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

        axes[0].plot(time_values, data_series[0], color=colors[0], linewidth=2.2, label="Temperatura")
        axes[0].plot(
            time_values,
            smooth_series[0],
            color="#F8B4B4",
            linewidth=1.6,
            linestyle="--",
            label="Media movel",
        )
        axes[0].scatter(
            [result.tempo_pico_temperatura],
            [result.pico_temperatura],
            color="#FFE082",
            edgecolors=colors[0],
            linewidths=1.5,
            s=85,
            zorder=5,
            label="Pico",
        )
        axes[0].legend(facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, labelcolor=self.TEXT_PRIMARY)

        axes[1].plot(time_values, data_series[1], color=colors[1], linewidth=2.2, label="Potencia")
        axes[1].plot(
            time_values,
            smooth_series[1],
            color="#A8C8FF",
            linewidth=1.6,
            linestyle="--",
            label="Media movel",
        )
        axes[1].scatter(
            [result.tempo_pico_potencia],
            [result.pico_potencia],
            color="#D9F3FF",
            edgecolors=colors[1],
            linewidths=1.5,
            s=85,
            zorder=5,
            label="Pico",
        )
        axes[1].legend(facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, labelcolor=self.TEXT_PRIMARY)

        axes[2].plot(time_values, data_series[2], color=self.ENERGY_COLOR, linewidth=2.2, label="Energia acumulada")
        axes[2].plot(
            time_values,
            smooth_series[2],
            color=colors[2],
            linewidth=1.6,
            linestyle="--",
            label="Suavizacao",
        )
        axes[2].fill_between(time_values, data_series[2], color=colors[2], alpha=0.18)
        axes[2].legend(facecolor=self.CARD_COLOR, edgecolor=self.BORDER_COLOR, labelcolor=self.TEXT_PRIMARY)

        figure.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.07, hspace=0.38)

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

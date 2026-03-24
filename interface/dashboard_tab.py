from __future__ import annotations

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import Canvas, ttk

from database.database_manager import DatabaseManager
from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_TITLE,
    WIDGET_HEIGHT_NORMAL,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
    THEME_COLORS,
)


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager: DatabaseManager | None = None) -> None:
        super().__init__(parent, fg_color=THEME_COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.db = db_manager or DatabaseManager()
        self._experiments: list[dict] = []
        self._experiment_map: dict[str, dict] = {}
        self._selected_experiment: dict | None = None
        self._avg_series: list[tuple[float, float]] | None = None
        self._phase_index: int | None = None

        self._sensor_status_var = ctk.StringVar(value="Sensor: Offline")
        self._mqtt_status_var = ctk.StringVar(value="MQTT: Desconectado")
        self._current_experiment_var = ctk.StringVar(value="Experimento: --")
        self._canvas_temp_var = ctk.StringVar(value="-- °C")

        self._bg = Canvas(self, bg=THEME_COLORS["bg"], highlightthickness=0)
        self._bg.place(relwidth=1, relheight=1)
        self.bind("<Configure>", self._draw_noise)

        self._build_layout()
        self.load_dashboard_data()

    # --- Data -------------------------------------------------------------
    def load_dashboard_data(self) -> None:
        self._experiments = [dict(r) for r in self.db.list_experiments()]
        self._refresh_experiment_selector()
        self.update_dashboard()
        self._refresh_statistics()

    def update_dashboard(self) -> None:
        exp = self._selected_experiment
        if not exp:
            self._set_metrics(None, None, None, None)
            self._set_experiment_info({})
            self._canvas_temp_var.set("-- °C")
            self._draw_pcm_state("solid")
            self.plot_temperature_graph([])
            return

        exp_id = exp.get("id")
        temp_media = self.db.get_temperatura_media(exp_id) if exp_id else None
        delta_t = self.db.get_delta_t(exp_id) if exp_id else None
        heating_rate = self.db.get_heating_rate(exp_id) if exp_id else None
        energia = self.db.get_energia_armazenada(exp_id) if exp_id else None

        self._set_metrics(temp_media, delta_t, heating_rate, energia)
        self._set_experiment_info(exp)

        series = self._build_temperature_series(exp)
        self._phase_index = self._detect_phase_change(series)
        self.plot_temperature_graph(series)

        current_temp = exp.get("temperatura_final") or temp_media
        if current_temp is not None:
            self._canvas_temp_var.set(f"{current_temp:.1f} °C")
            self._draw_pcm_state(self._infer_pcm_state(exp, current_temp))
        else:
            self._canvas_temp_var.set("-- °C")
            self._draw_pcm_state("solid")

        self._update_thermo_cards(exp_id)

    # --- Métricas ---------------------------------------------------------
    def _set_metrics(
        self,
        temp_media: float | None,
        delta_t: float | None,
        heating_rate: float | None,
        energia: float | None,
    ) -> None:
        self._metric_temp.configure(text=f"{temp_media:.1f} °C" if temp_media is not None else "--")
        self._metric_delta.configure(text=f"{delta_t:.1f} °C" if delta_t is not None else "--")
        self._metric_rate.configure(text=f"{heating_rate:.2f} °C/min" if heating_rate is not None else "--")
        self._metric_energy.configure(text=f"{energia:.0f} J" if energia is not None else "--")

    # --- Gráfico ----------------------------------------------------------
    def plot_temperature_graph(self, series: list[tuple[float, float]]) -> None:
        self._temp_ax.clear()
        self._style_axis(self._temp_ax, "Temperatura vs Tempo")

        if not series:
            self._temp_canvas.draw_idle()
            return

        x = [p[0] for p in series]
        y = [p[1] for p in series]

        self._temp_ax.plot(x, y, color=THEME_COLORS["accent"], linewidth=2.4)

        if self._avg_series:
            avg_x = [p[0] for p in self._avg_series]
            avg_y = [p[1] for p in self._avg_series]
            self._temp_ax.plot(avg_x, avg_y, color=THEME_COLORS["line_avg"], linewidth=3.0)

        if self._phase_index is not None and 0 <= self._phase_index < len(series):
            px, py = series[self._phase_index]
            self._temp_ax.scatter([px], [py], color=THEME_COLORS["line_avg"], s=44, zorder=5)
            self._temp_ax.text(
                px,
                py + 0.4,
                "Início da Fusão",
                color=THEME_COLORS["text_secondary"],
                fontsize=8,
            )

        self._temp_ax.set_xlabel("Tempo (min)", color=THEME_COLORS["text_muted"], fontsize=8)
        self._temp_ax.set_ylabel("Temperatura (°C)", color=THEME_COLORS["text_muted"], fontsize=8)
        self._temp_canvas.draw_idle()

    def _build_temperature_series(self, exp: dict) -> list[tuple[float, float]]:
        t_initial = exp.get("temperatura_inicial")
        t_final = exp.get("temperatura_final")
        delta_tempo = exp.get("delta_tempo") or 0
        if t_initial is None or t_final is None:
            return []

        points = 24
        x_values = [i * (delta_tempo / (points - 1)) if delta_tempo else i for i in range(points)]
        y_values = [t_initial + (t_final - t_initial) * (i / (points - 1)) for i in range(points)]
        return list(zip(x_values, y_values))

    def _detect_phase_change(self, series: list[tuple[float, float]]) -> int | None:
        if len(series) < 6:
            return None
        y_vals = [p[1] for p in series]
        for i in range(3, len(y_vals)):
            span = max(y_vals[i - 3:i + 1]) - min(y_vals[i - 3:i + 1])
            if span <= 0.25:
                return i - 1
        return None

    # --- Layout -----------------------------------------------------------
    def _build_layout(self) -> None:
        self._configure_ttk_style()

        self.create_header()
        self.create_metrics_panel()
        self.create_main_layout()
        self.create_thermodynamic_cards()
        self.create_control_buttons()

    def create_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Dashboard PCM",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w")

        status_frame = ctk.CTkFrame(header, fg_color=THEME_COLORS["card"], corner_radius=16)
        status_frame.grid(row=0, column=1, sticky="ew", padx=PAD_NORMAL)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)

        exp_label = ctk.CTkLabel(
            status_frame,
            textvariable=self._current_experiment_var,
            text_color=THEME_COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        exp_label.grid(row=0, column=0, sticky="w", padx=PAD_NORMAL, pady=PAD_SMALL)

        status_col = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_col.grid(row=0, column=1, sticky="e", padx=PAD_NORMAL)

        sensor_label = ctk.CTkLabel(
            status_col,
            textvariable=self._sensor_status_var,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        sensor_label.grid(row=0, column=0, sticky="e")

        mqtt_label = ctk.CTkLabel(
            status_col,
            textvariable=self._mqtt_status_var,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        mqtt_label.grid(row=1, column=0, sticky="e")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e")

        self._avg_btn_header = ctk.CTkButton(
            actions,
            text="Calcular Média",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color=THEME_COLORS["card"],
            hover_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            font=FONT_NORMAL,
            command=self._on_average_clicked,
        )
        self._avg_btn_header.grid(row=0, column=0, padx=(0, PAD_SMALL))

        self._export_btn_header = ctk.CTkButton(
            actions,
            text="Exportar",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color=THEME_COLORS["card"],
            hover_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            font=FONT_NORMAL,
            command=self._on_export_clicked,
        )
        self._export_btn_header.grid(row=0, column=1, padx=(0, PAD_SMALL))

        self._reset_btn_header = ctk.CTkButton(
            actions,
            text="Resetar",
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color=THEME_COLORS["card"],
            hover_color=THEME_COLORS["card_soft"],
            text_color=THEME_COLORS["text_primary"],
            font=FONT_NORMAL,
            command=self._on_reset_clicked,
        )
        self._reset_btn_header.grid(row=0, column=2)

    def create_metrics_panel(self) -> None:
        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.grid(row=1, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1)

        self._metric_temp = self._metric_item(metrics, 0, "Temperatura média")
        self._metric_delta = self._metric_item(metrics, 1, "ΔT do experimento")
        self._metric_rate = self._metric_item(metrics, 2, "Taxa de aquecimento")
        self._metric_energy = self._metric_item(metrics, 3, "Energia armazenada")

    def create_main_layout(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(content, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_NORMAL))
        left_col.grid_rowconfigure(0, weight=2)
        left_col.grid_rowconfigure(1, weight=1)
        left_col.grid_columnconfigure(0, weight=1)

        right_col = ctk.CTkFrame(content, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")
        right_col.grid_rowconfigure(0, weight=3)
        right_col.grid_rowconfigure(1, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        self.create_pcm_canvas(left_col)
        self.create_experiment_info_panel(left_col)

        self.create_temperature_graph(right_col)
        self.create_statistics_table(right_col)

    def create_experiment_info_panel(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=18)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            card,
            text="Informações do Experimento",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._info_labels = {}
        fields = [
            ("Material", "material"),
            ("Massa", "massa"),
            ("Quantidade utilizada", "quantidade"),
            ("Operador", "operador"),
            ("Cápsula", "capsula"),
            ("Tempo total", "tempo_total"),
        ]
        for idx, (label, key) in enumerate(fields, start=1):
            row = idx
            col = 0 if idx <= 3 else 1
            row = idx if idx <= 3 else idx - 3

            label_widget = ctk.CTkLabel(
                card,
                text=label,
                text_color=THEME_COLORS["text_muted"],
                font=FONT_NORMAL,
            )
            label_widget.grid(row=row, column=col, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

            value_widget = ctk.CTkLabel(
                card,
                text="--",
                text_color=THEME_COLORS["text_primary"],
                font=FONT_TITLE,
            )
            value_widget.grid(row=row + 1, column=col, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
            self._info_labels[key] = value_widget

    def create_pcm_canvas(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=18)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, PAD_NORMAL))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            card,
            text="Estado do PCM",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._pcm_canvas = Canvas(
            card,
            bg=THEME_COLORS["card"],
            highlightthickness=0,
        )
        self._pcm_canvas.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)

        self._pcm_circle = self._pcm_canvas.create_oval(
            40,
            20,
            240,
            220,
            fill=THEME_COLORS["accent_soft"],
            outline=THEME_COLORS["accent"],
            width=3,
        )
        self._pcm_inner = self._pcm_canvas.create_oval(
            80,
            60,
            200,
            180,
            fill="",
            outline="",
        )
        self._pcm_temp_text = self._pcm_canvas.create_text(
            140,
            125,
            text=self._canvas_temp_var.get(),
            fill=THEME_COLORS["text_primary"],
            font=(FONT_TITLE[0], 20, "bold"),
        )
        self._pcm_state = "solid"
        self._anim_phase = 0
        self._animate_pcm()

    def create_temperature_graph(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=18)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LARGE, pady=(PAD_NORMAL, 0))
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Temperatura x Tempo",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w")

        self._experiment_combo = ttk.Combobox(header, state="readonly", values=[])
        self._experiment_combo.grid(row=0, column=1, sticky="e")
        self._experiment_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_experiment_selected())

        self._temp_fig, self._temp_ax, self._temp_canvas = self._create_chart(card)

    def create_statistics_table(self, parent) -> None:
        table = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=18)
        table.grid(row=1, column=0, sticky="nsew", pady=(PAD_NORMAL, 0))
        table.grid_columnconfigure(0, weight=1)
        table.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            table,
            text="Estatísticas Globais",
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        self._stats_labels = {}
        stats = [
            ("Tempo médio de fusão", "tempo_fusao"),
            ("Pico médio de temperatura", "pico_temp"),
            ("Energia média absorvida", "energia_media"),
            ("Eficiência térmica estimada", "eficiencia"),
        ]
        for idx, (label, key) in enumerate(stats, start=1):
            row = idx
            col = 0 if idx <= 2 else 1
            row = idx if idx <= 2 else idx - 2

            label_widget = ctk.CTkLabel(
                table,
                text=label,
                text_color=THEME_COLORS["text_muted"],
                font=FONT_NORMAL,
            )
            label_widget.grid(row=row, column=col, sticky="w", padx=PAD_LARGE, pady=(0, PAD_SMALL))

            value_widget = ctk.CTkLabel(
                table,
                text="--",
                text_color=THEME_COLORS["text_primary"],
                font=FONT_TITLE,
            )
            value_widget.grid(row=row + 1, column=col, sticky="w", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
            self._stats_labels[key] = value_widget

    def create_thermodynamic_cards(self) -> None:
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=3, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)
        cards.grid_columnconfigure(2, weight=1)

        self._card_sensible = self._thermo_card(cards, 0, "Calor Sensível", "Q = m · c · ΔT")
        self._card_latent = self._thermo_card(cards, 1, "Calor Latente", "Q = m · L")
        self._card_storage = self._thermo_card(cards, 2, "Capacidade de Armazenamento", "0 – 100 %")

    def create_control_buttons(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_columnconfigure(2, weight=1)

        self._avg_btn = ctk.CTkButton(
            footer,
            text="Calcular Média dos Experimentos",
            height=48,
            corner_radius=14,
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_strong"],
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
            command=self._on_average_clicked,
        )
        self._avg_btn.grid(row=0, column=0, sticky="ew", padx=(0, PAD_NORMAL))

        self._export_btn = ctk.CTkButton(
            footer,
            text="Exportar Dados",
            height=48,
            corner_radius=14,
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_strong"],
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
            command=self._on_export_clicked,
        )
        self._export_btn.grid(row=0, column=1, sticky="ew", padx=(0, PAD_NORMAL))

        self._reset_btn = ctk.CTkButton(
            footer,
            text="Resetar Experimento",
            height=48,
            corner_radius=14,
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_strong"],
            text_color=THEME_COLORS["text_primary"],
            font=FONT_TITLE,
            command=self._on_reset_clicked,
        )
        self._reset_btn.grid(row=0, column=2, sticky="ew")

    # --- Helpers ---------------------------------------------------------
    def _thermo_card(self, parent, col: int, title: str, formula: str):
        card = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=18)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else PAD_NORMAL, 0))
        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            text_color=THEME_COLORS["text_secondary"],
            font=FONT_TITLE,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        formula_label = ctk.CTkLabel(
            card,
            text=formula,
            text_color=THEME_COLORS["text_muted"],
            font=FONT_NORMAL,
        )
        formula_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE)

        value_label = ctk.CTkLabel(
            card,
            text="--",
            text_color=THEME_COLORS["text_primary"],
            font=FONT_HEADER,
        )
        value_label.grid(row=2, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_SMALL, PAD_NORMAL))

        return {"card": card, "value": value_label}

    def _metric_item(self, parent, col: int, title: str) -> ctk.CTkLabel:
        block = ctk.CTkFrame(parent, fg_color=THEME_COLORS["card"], corner_radius=16)
        block.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else PAD_NORMAL, 0))
        block.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(block, text=title, text_color=THEME_COLORS["text_secondary"], font=FONT_TITLE)
        label.grid(row=0, column=0, sticky="w", padx=PAD_NORMAL, pady=(PAD_SMALL, PAD_SMALL))

        value = ctk.CTkLabel(block, text="--", text_color=THEME_COLORS["text_primary"], font=FONT_NORMAL)
        value.grid(row=1, column=0, sticky="w", padx=PAD_NORMAL, pady=(0, PAD_SMALL))
        return value

    def _create_chart(self, parent):
        fig = Figure(figsize=(5.6, 3.2), dpi=100)
        fig.patch.set_facecolor(THEME_COLORS["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME_COLORS["card"])
        canvas = FigureCanvasTkAgg(fig, master=parent)
        widget = canvas.get_tk_widget()
        widget.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_LARGE)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        return fig, ax, canvas

    def _style_axis(self, ax, title: str) -> None:
        ax.set_title(title, color=THEME_COLORS["text_primary"], fontsize=11, pad=10)
        ax.tick_params(colors=THEME_COLORS["text_muted"], labelsize=8)
        ax.grid(True, color=THEME_COLORS["border"], linestyle="--", linewidth=0.6, alpha=0.7)
        for side in ["bottom", "top", "left", "right"]:
            ax.spines[side].set_color(THEME_COLORS["card"])

    def _set_experiment_info(self, exp: dict) -> None:
        if not exp:
            self._current_experiment_var.set("Experimento: --")
            for key in self._info_labels:
                self._info_labels[key].configure(text="--")
            return

        material = exp.get("material") or "--"
        massa = exp.get("massa")
        operador = exp.get("operador") or "--"
        capsula = exp.get("capsula") or "--"
        delta_tempo = exp.get("delta_tempo")

        self._current_experiment_var.set(
            f"Experimento: #{exp.get('id') if exp.get('id') is not None else '--'}"
        )

        self._info_labels["material"].configure(text=material)
        self._info_labels["massa"].configure(text=f"{massa:.2f} g" if massa is not None else "--")
        self._info_labels["quantidade"].configure(text=f"{massa:.2f} g" if massa is not None else "--")
        self._info_labels["operador"].configure(text=operador)
        self._info_labels["capsula"].configure(text=capsula)
        self._info_labels["tempo_total"].configure(text=f"{delta_tempo:.1f} min" if delta_tempo is not None else "--")

    def _update_thermo_cards(self, exp_id: int | None) -> None:
        if not exp_id:
            self._card_sensible["value"].configure(text="--")
            self._card_latent["value"].configure(text="--")
            self._card_storage["value"].configure(text="--")
            return

        sensivel = self.db.get_calculo_by_experimento_tipo(exp_id, "Calor Específico")
        latente = self.db.get_calculo_by_experimento_tipo(exp_id, "Calor Latente")
        energia = self.db.get_energia_armazenada(exp_id)

        sensivel_val = sensivel["resultado"] if sensivel and sensivel["resultado"] is not None else None
        latente_val = latente["resultado"] if latente and latente["resultado"] is not None else None

        self._card_sensible["value"].configure(text=f"{sensivel_val:.1f} J" if sensivel_val is not None else "--")
        self._card_latent["value"].configure(text=f"{latente_val:.1f} J" if latente_val is not None else "--")

        if energia is None:
            self._card_storage["value"].configure(text="--")
        else:
            max_energy = max(
                [self.db.get_energia_armazenada(e.get("id")) or 0 for e in self._experiments] or [0]
            )
            percent = (energia / max_energy * 100) if max_energy else 0
            self._card_storage["value"].configure(text=f"{percent:.0f} %")

        if self._phase_index is not None:
            self._card_latent["card"].configure(border_width=2, border_color=THEME_COLORS["line_avg"])
        else:
            self._card_latent["card"].configure(border_width=0)

    def _infer_pcm_state(self, exp: dict, current_temp: float) -> str:
        t_initial = exp.get("temperatura_inicial")
        t_final = exp.get("temperatura_final")
        if t_initial is None or t_final is None:
            return "solid"
        span = t_final - t_initial
        if span <= 0:
            return "solid"
        ratio = (current_temp - t_initial) / span
        if ratio < 0.35:
            return "solid"
        if ratio < 0.75:
            return "transition"
        return "liquid"

    def _draw_pcm_state(self, state: str) -> None:
        self._pcm_state = state
        if state == "solid":
            self._pcm_canvas.itemconfigure(self._pcm_circle, fill=THEME_COLORS["accent_soft"], outline=THEME_COLORS["accent"])
            self._pcm_canvas.itemconfigure(self._pcm_inner, fill="", outline="")
        elif state == "transition":
            self._pcm_canvas.itemconfigure(self._pcm_circle, fill=THEME_COLORS["accent_soft"], outline=THEME_COLORS["line_avg"])
            self._pcm_canvas.itemconfigure(self._pcm_inner, fill=THEME_COLORS["card"], outline="")
        else:
            self._pcm_canvas.itemconfigure(self._pcm_circle, fill=THEME_COLORS["accent"], outline=THEME_COLORS["line_avg"])
            self._pcm_canvas.itemconfigure(self._pcm_inner, fill=THEME_COLORS["accent_soft"], outline="")

        self._pcm_canvas.itemconfigure(self._pcm_temp_text, text=self._canvas_temp_var.get())

    def _animate_pcm(self) -> None:
        if self._pcm_state == "liquid":
            self._anim_phase = (self._anim_phase + 1) % 360
            offset = 3 * (1 if self._anim_phase % 120 < 60 else -1)
            self._pcm_canvas.coords(self._pcm_inner, 82, 60 + offset, 198, 180 + offset)
        else:
            self._pcm_canvas.coords(self._pcm_inner, 80, 60, 200, 180)
        self.after(120, self._animate_pcm)

    def _compute_average_series(self) -> list[tuple[float, float]]:
        candidates = [exp for exp in self._experiments if exp.get("temperatura_inicial") is not None and exp.get("temperatura_final") is not None]
        if not candidates:
            return []
        points = 24
        avg_delta = sum([exp.get("delta_tempo") or 0 for exp in candidates]) / len(candidates)
        x_values = [i * (avg_delta / (points - 1)) if avg_delta else i for i in range(points)]
        y_values = []
        for i in range(points):
            ratios = i / (points - 1)
            temps = []
            for exp in candidates:
                t_initial = exp.get("temperatura_inicial")
                t_final = exp.get("temperatura_final")
                temps.append(t_initial + (t_final - t_initial) * ratios)
            y_values.append(sum(temps) / len(temps))
        return list(zip(x_values, y_values))

    def _refresh_statistics(self) -> None:
        if not self._experiments:
            for lbl in self._stats_labels.values():
                lbl.configure(text="--")
            return

        tempos = [exp.get("delta_tempo") for exp in self._experiments if exp.get("delta_tempo") is not None]
        temps_finais = [exp.get("temperatura_final") for exp in self._experiments if exp.get("temperatura_final") is not None]
        energias = [self.db.get_energia_armazenada(exp.get("id")) for exp in self._experiments]
        energias = [e for e in energias if e is not None]

        if tempos:
            self._stats_labels["tempo_fusao"].configure(text=f"{sum(tempos) / len(tempos):.1f} min")
        if temps_finais:
            self._stats_labels["pico_temp"].configure(text=f"{sum(temps_finais) / len(temps_finais):.1f} °C")
        if energias:
            self._stats_labels["energia_media"].configure(text=f"{sum(energias) / len(energias):.0f} J")

        efficiencies = [
            row["eficiencia"]
            for row in self.db.list_thermal_calculations()
            if row["eficiencia"] is not None
        ]
        if efficiencies:
            self._stats_labels["eficiencia"].configure(text=f"{sum(efficiencies) / len(efficiencies):.0f} %")

    # --- Buttons ---------------------------------------------------------
    def _on_average_clicked(self) -> None:
        self._avg_series = self._compute_average_series()
        self.update_dashboard()

    def _on_export_clicked(self) -> None:
        # Placeholder: integrate with export module if needed.
        return

    def _on_reset_clicked(self) -> None:
        self._avg_series = None
        self.update_dashboard()

    # --- Status updates --------------------------------------------------
    def update_sensor_status(self, status: str) -> None:
        self._sensor_status_var.set(f"Sensor: {status}")

    def update_mqtt_status(self, status: str) -> None:
        self._mqtt_status_var.set(f"MQTT: {status}")

    def update_current_temperature(self, temperature: float) -> None:
        self._canvas_temp_var.set(f"{temperature:.1f} °C")
        if self._selected_experiment:
            self._draw_pcm_state(self._infer_pcm_state(self._selected_experiment, temperature))
        else:
            self._draw_pcm_state("solid")

    # --- Experimentos -----------------------------------------------------
    def _refresh_experiment_selector(self) -> None:
        options = []
        self._experiment_map.clear()

        for row in self._experiments:
            label = f"#{row['id']} - {row.get('material') or 'Sem material'}"
            options.append(label)
            self._experiment_map[label] = row

        if not options:
            options = ["Nenhum experimento"]
            self._experiment_map[options[0]] = None

        self._experiment_combo["values"] = options
        self._experiment_combo.current(0)
        self._selected_experiment = self._experiment_map.get(options[0])

    def _on_experiment_selected(self) -> None:
        label = self._experiment_combo.get()
        self._selected_experiment = self._experiment_map.get(label)
        self.update_dashboard()

    # --- Visuals ----------------------------------------------------------
    def _draw_noise(self, _event=None) -> None:
        self._bg.delete("noise")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 0 or h <= 0:
            return
        from random import randint

        for _ in range(420):
            x = randint(0, w)
            y = randint(0, h)
            shade = randint(14, 24)
            color = f"#{shade:02x}{shade:02x}{shade:02x}"
            self._bg.create_rectangle(x, y, x + 1, y + 1, fill=color, outline="", tags="noise")

    def _configure_ttk_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "TCombobox",
            fieldbackground=THEME_COLORS["bg"],
            background=THEME_COLORS["card"],
            foreground=THEME_COLORS["text_primary"],
            bordercolor=THEME_COLORS["border"],
            arrowcolor=THEME_COLORS["accent"],
            font=FONT_NORMAL,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", THEME_COLORS["bg"])],
            foreground=[("readonly", THEME_COLORS["text_primary"])],
        )

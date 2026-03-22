from __future__ import annotations

from typing import Iterable

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import Canvas, ttk

from database.database_manager import DatabaseManager
from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_SUBTITLE,
    FONT_TITLE,
    SECTION_PAD_X,
    SECTION_PAD_Y,
)


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db_manager: DatabaseManager | None = None) -> None:
        super().__init__(parent, fg_color="#0B0F14")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.db = db_manager or DatabaseManager()
        self._experiments: list[dict] = []
        self._experiment_map: dict[str, dict] = {}
        self._selected_experiment: dict | None = None

        self._bg = Canvas(self, bg="#0B0F14", highlightthickness=0)
        self._bg.place(relwidth=1, relheight=1)
        self.bind("<Configure>", self._draw_noise)

        self._build_layout()
        self.load_dashboard_data()

    # --- Data -------------------------------------------------------------
    def load_dashboard_data(self) -> None:
        self._experiments = [dict(r) for r in self.db.list_experiments()]
        self._refresh_experiment_selector()
        self.update_dashboard()

    def update_dashboard(self) -> None:
        exp = self._selected_experiment
        if not exp:
            self._set_metrics(None, None, None, None)
            self._exp_info_label.configure(text="Nenhum experimento selecionado")
            self.plot_temperature_graph([])
            return

        exp_id = exp.get("id")
        temp_media = self.db.get_temperatura_media(exp_id) if exp_id else None
        delta_t = self.db.get_delta_t(exp_id) if exp_id else None
        heating_rate = self.db.get_heating_rate(exp_id) if exp_id else None
        energia = self.db.get_energia_armazenada(exp_id) if exp_id else None

        self._set_metrics(temp_media, delta_t, heating_rate, energia)
        self._update_latest_experiment(exp)
        self.plot_temperature_graph(self._build_temperature_series(exp))

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

        self._temp_ax.plot(x, y, color="#00FFFF", linewidth=2.4)
        for alpha in [0.18, 0.12, 0.08]:
            self._temp_ax.fill_between(x, y, color="#00FFFF", alpha=alpha)

        self._temp_ax.set_xlabel("Tempo (min)", color="#94A3B8", fontsize=8)
        self._temp_ax.set_ylabel("Temperatura (°C)", color="#94A3B8", fontsize=8)
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

    # --- Layout -----------------------------------------------------------
    def _build_layout(self) -> None:
        self._configure_ttk_style()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SECTION_PAD_X, pady=(SECTION_PAD_Y, 8))
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Dashboard do Experimento",
            text_color="#E5E7EB",
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w")

        self._experiment_combo = ttk.Combobox(header, state="readonly", values=[])
        self._experiment_combo.grid(row=0, column=1, sticky="e")
        self._experiment_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_experiment_selected())

        metrics = ctk.CTkFrame(self, fg_color="#101722", corner_radius=18)
        metrics.grid(row=1, column=0, sticky="ew", padx=SECTION_PAD_X, pady=(0, 12))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1)

        self._metric_temp = self._metric_item(metrics, 0, "Temperatura média")
        self._metric_delta = self._metric_item(metrics, 1, "ΔT do experimento")
        self._metric_rate = self._metric_item(metrics, 2, "Taxa de aquecimento")
        self._metric_energy = self._metric_item(metrics, 3, "Energia armazenada")

        self._latest_card = ctk.CTkFrame(self, fg_color="#0F1622", corner_radius=18)
        self._latest_card.grid(row=2, column=0, sticky="ew", padx=SECTION_PAD_X, pady=(0, 12))
        self._latest_card.grid_columnconfigure(0, weight=1)

        latest_title = ctk.CTkLabel(
            self._latest_card,
            text="Sobre este experimento",
            text_color="#9AA0AB",
            font=FONT_SUBTITLE,
        )
        latest_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        self._about_label = ctk.CTkLabel(
            self._latest_card,
            text=(
                "Este experimento analisa o comportamento térmico de um\n"
                "Material de Mudança de Fase (PCM).\n\n"
                "As métricas apresentadas mostram:\n"
                "- quanto calor o material absorve\n"
                "- quão rápido ele aquece\n"
                "- quanta energia ele consegue armazenar\n\n"
                "Esses dados são fundamentais para avaliar a eficiência\n"
                "do PCM no armazenamento térmico."
            ),
            text_color="#C5D1DE",
            font=FONT_NORMAL,
            justify="left",
        )
        self._about_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        self._exp_info_label = ctk.CTkLabel(
            self._latest_card,
            text="",
            text_color="#00FFFF",
            font=FONT_SUBTITLE,
            justify="left",
        )
        self._exp_info_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

        chart_card = ctk.CTkFrame(self, fg_color="#101722", corner_radius=18)
        chart_card.grid(row=3, column=0, sticky="nsew", padx=SECTION_PAD_X, pady=(0, SECTION_PAD_Y))
        chart_card.grid_columnconfigure(0, weight=1)
        chart_card.grid_rowconfigure(0, weight=1)

        self._temp_fig, self._temp_ax, self._temp_canvas = self._create_chart(chart_card)

    def _metric_item(self, parent, col: int, title: str) -> ctk.CTkLabel:
        block = ctk.CTkFrame(parent, fg_color="#101722", corner_radius=16)
        block.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0), pady=12)
        block.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(block, text=title, text_color="#9AA0AB", font=FONT_NORMAL)
        label.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        value = ctk.CTkLabel(block, text="--", text_color="#00FFFF", font=FONT_TITLE)
        value.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        return value

    def _create_chart(self, parent):
        fig = Figure(figsize=(5.6, 3.2), dpi=100)
        fig.patch.set_facecolor("#101722")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#101722")
        canvas = FigureCanvasTkAgg(fig, master=parent)
        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True, padx=16, pady=16)
        return fig, ax, canvas

    def _style_axis(self, ax, title: str) -> None:
        ax.set_title(title, color="#E5E7EB", fontsize=11, pad=10)
        ax.tick_params(colors="#94A3B8", labelsize=8)
        ax.grid(True, color="#1F2733", linestyle="--", linewidth=0.6, alpha=0.7)
        for side in ["bottom", "top", "left", "right"]:
            ax.spines[side].set_color("#101722")

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

    def _update_latest_experiment(self, exp: dict) -> None:
        material = exp.get("material") or "--"
        operador = exp.get("operador") or "--"
        delta_t = exp.get("delta_temperatura")
        tempo_total = exp.get("delta_tempo")

        info = (
            f"Material: {material}\n"
            f"Operador: {operador}\n"
            f"ΔT: {delta_t:.1f} °C" if delta_t is not None else "ΔT: --"
        )
        if tempo_total is not None:
            info += f"\nDuração: {tempo_total:.1f} min"
        else:
            info += "\nDuração: --"

        self._exp_info_label.configure(text=info)

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
            fieldbackground="#0D1117",
            background="#141A22",
            foreground="#E5E7EB",
            bordercolor="#1F2937",
            arrowcolor="#00FFFF",
            font=FONT_NORMAL,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#0D1117")],
            foreground=[("readonly", "#E5E7EB")],
        )

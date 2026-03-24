import tkinter as tk
from typing import List

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui_styles import (
    FONT_HEADER,
    FONT_NORMAL,
    FONT_TITLE,
    FONT_TEMP,
    WIDGET_HEIGHT_NORMAL,
    WIDGET_HEIGHT_LARGE,
    PAD_SMALL,
    PAD_NORMAL,
    PAD_LARGE,
)


COLORS = {
    "bg": "#0D1117",
    "card": "#161B22",
    "card_soft": "#1B222C",
    "border": "#202734",
    "shadow": "#0A0F14",
    "accent": "#8B93A5",
    "accent_strong": "#7A879B",
    "accent_soft": "#18212B",
    "text_primary": "#E5E7EB",
    "text_secondary": "#9AA0AB",
    "text_muted": "#8B93A5",
    "white": "#E5E7EB",
}


class MinimalLineChart:
    def __init__(self, parent) -> None:
        self.figure = Figure(figsize=(5.6, 2.4), dpi=100)
        self.figure.patch.set_facecolor(COLORS["card"])
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(COLORS["card"])
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_visible(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        (self.line,) = self.ax.plot([], [], color=COLORS["accent"], linewidth=2.4)

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()

    def update(self, data: List[float]) -> None:
        if not data:
            return
        self.line.set_data(range(len(data)), data)
        self.ax.set_xlim(0, max(49, len(data) - 1))
        min_v, max_v = min(data), max(data)
        spread = max(0.6, (max_v - min_v) * 0.15)
        self.ax.set_ylim(min_v - spread, max_v + spread)
        self.canvas.draw_idle()


class SensorPage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=COLORS["bg"])
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.sensor_temperature_var = ctk.StringVar(value="-- °C")
        self.mqtt_status_var = ctk.StringVar(value="MQTT: Tentando reconectar...")
        self.temperature_history: List[float] = []

        self._config_expanded = True
        self._mqtt_status_label = None
        self._gauge_value_label = None
        self._chart = None

        self._build_layout()

    def _build_layout(self) -> None:
        self.create_header()
        self.create_temperature_gauge()
        self.create_temperature_graph()
        self.create_config_panel()

    def create_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD_LARGE, pady=(6, PAD_NORMAL))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Sensor",
            text_color=COLORS["text_primary"],
            font=FONT_HEADER,
        )
        title.grid(row=0, column=0, sticky="w")

        self.create_connection_status(parent=header)

    def create_connection_status(self, parent) -> None:
        status_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        status_card.grid(row=0, column=1, sticky="e")

        self._mqtt_status_label = ctk.CTkLabel(
            status_card,
            textvariable=self.mqtt_status_var,
            text_color=COLORS["text_muted"],
            font=FONT_NORMAL,
        )
        self._mqtt_status_label.grid(row=0, column=0, padx=PAD_LARGE, pady=PAD_SMALL)

    def create_temperature_gauge(self) -> None:
        gauge_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        gauge_card.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        gauge_card.grid_rowconfigure(0, weight=1)
        gauge_card.grid_columnconfigure(0, weight=1)

        canvas_size = 260
        canvas = tk.Canvas(
            gauge_card,
            width=canvas_size,
            height=canvas_size,
            highlightthickness=0,
            bg=COLORS["card"],
        )
        canvas.grid(row=0, column=0, pady=PAD_LARGE)

        shadow_offset = 8
        canvas.create_oval(
            20 + shadow_offset,
            20 + shadow_offset,
            canvas_size - 20 + shadow_offset,
            canvas_size - 20 + shadow_offset,
            fill=COLORS["shadow"],
            outline="",
        )
        canvas.create_oval(
            20,
            20,
            canvas_size - 20,
            canvas_size - 20,
            fill=COLORS["accent_soft"],
            outline=COLORS["border"],
            width=2,
        )
        canvas.create_arc(
            26,
            26,
            canvas_size - 26,
            canvas_size - 26,
            start=110,
            extent=120,
            outline=COLORS["white"],
            width=3,
            style="arc",
        )

        self._gauge_value_label = ctk.CTkLabel(
            gauge_card,
            textvariable=self.sensor_temperature_var,
            text_color=COLORS["white"],
            font=FONT_TEMP,
        )
        self._gauge_value_label.place(relx=0.5, rely=0.5, anchor="center")

        gauge_hint = ctk.CTkLabel(
            gauge_card,
            text="Temperatura IR",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        gauge_hint.place(relx=0.5, rely=0.82, anchor="center")

    def create_temperature_graph(self) -> None:
        graph_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        graph_card.grid(row=2, column=0, sticky="nsew", padx=PAD_LARGE, pady=(0, PAD_LARGE))
        graph_card.grid_columnconfigure(0, weight=1)
        graph_card.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            graph_card,
            text="Tendência",
            text_color=COLORS["text_secondary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, 0))

        self._chart = MinimalLineChart(graph_card)
        self._chart.widget.grid(row=1, column=0, sticky="nsew", padx=PAD_LARGE, pady=PAD_NORMAL)

    def create_config_panel(self) -> None:
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(0, PAD_LARGE), pady=(0, PAD_LARGE))
        panel.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(panel, fg_color=COLORS["card"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=PAD_NORMAL, pady=(PAD_NORMAL, PAD_SMALL))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Configurações",
            text_color=COLORS["text_primary"],
            font=FONT_TITLE,
        )
        title.grid(row=0, column=0, sticky="w")

        toggle_btn = ctk.CTkButton(
            header,
            text="Ocultar" if self._config_expanded else "Mostrar",
            width=88,
            height=WIDGET_HEIGHT_NORMAL,
            corner_radius=12,
            fg_color=COLORS["card_soft"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
            command=self._toggle_config_panel,
        )
        toggle_btn.grid(row=0, column=1, sticky="e")
        self._toggle_btn = toggle_btn

        self._config_body = ctk.CTkFrame(panel, fg_color=COLORS["card"], corner_radius=0)
        self._config_body.grid(row=1, column=0, sticky="nsew", padx=PAD_NORMAL, pady=(0, PAD_NORMAL))
        self._config_body.grid_columnconfigure(0, weight=1)

        self._build_mqtt_section(self._config_body)
        self._build_sensor_section(self._config_body)

    def _build_mqtt_section(self, parent) -> None:
        section = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_soft"],
            corner_radius=18,
        )
        section.grid(row=0, column=0, sticky="ew", pady=(0, PAD_NORMAL))
        section.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            section,
            text="Configurações MQTT",
            text_color=COLORS["text_primary"],
            font=FONT_TITLE,
        )
        label.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        host_label = ctk.CTkLabel(
            section,
            text="Host / IP",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        host_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE)
        self.host_entry = ctk.CTkEntry(
            section,
            placeholder_text="192.168.1.15",
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        self.host_entry.grid(row=2, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        port_label = ctk.CTkLabel(
            section,
            text="Porta",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        port_label.grid(row=3, column=0, sticky="w", padx=PAD_LARGE)
        self.port_entry = ctk.CTkEntry(
            section,
            placeholder_text="1883",
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        self.port_entry.grid(row=4, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        topic_label = ctk.CTkLabel(
            section,
            text="Tópico de leitura",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        topic_label.grid(row=5, column=0, sticky="w", padx=PAD_LARGE)
        self.topic_entry = ctk.CTkEntry(
            section,
            placeholder_text="pcm/sensor/ir/temp",
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        self.topic_entry.grid(row=6, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

        button_row = ctk.CTkFrame(section, fg_color=COLORS["card_soft"], corner_radius=0)
        button_row.grid(row=7, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)

        self.connect_btn = ctk.CTkButton(
            button_row,
            text="Conectar",
            height=WIDGET_HEIGHT_LARGE,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_strong"],
            text_color=COLORS["white"],
            font=FONT_TITLE,
        )
        self.connect_btn.grid(row=0, column=0, sticky="ew", padx=(0, PAD_SMALL))

        self.disconnect_btn = ctk.CTkButton(
            button_row,
            text="Desconectar",
            height=WIDGET_HEIGHT_LARGE,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_strong"],
            text_color=COLORS["white"],
            font=FONT_TITLE,
        )
        self.disconnect_btn.grid(row=0, column=1, sticky="ew", padx=(PAD_SMALL, 0))

    def _build_sensor_section(self, parent) -> None:
        section = ctk.CTkFrame(
            parent,
            fg_color=COLORS["card_soft"],
            corner_radius=18,
        )
        section.grid(row=1, column=0, sticky="ew")
        section.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            section,
            text="Configurações Sensor IR",
            text_color=COLORS["text_primary"],
            font=FONT_TITLE,
        )
        label.grid(row=0, column=0, sticky="w", padx=PAD_LARGE, pady=(PAD_NORMAL, PAD_SMALL))

        emiss_label = ctk.CTkLabel(
            section,
            text="Emissividade (0.1 – 1.0)",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        emiss_label.grid(row=1, column=0, sticky="w", padx=PAD_LARGE)
        self.emissivity_entry = ctk.CTkEntry(
            section,
            placeholder_text="0.95",
            height=WIDGET_HEIGHT_NORMAL,
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        self.emissivity_entry.grid(row=2, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        refresh_label = ctk.CTkLabel(
            section,
            text="Intervalo de refresh",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        refresh_label.grid(row=3, column=0, sticky="w", padx=PAD_LARGE)
        self.refresh_option = ctk.CTkOptionMenu(
            section,
            values=["500ms", "1s", "5s"],
            fg_color=COLORS["card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_strong"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text_primary"],
            text_color=COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        self.refresh_option.set("1s")
        self.refresh_option.grid(row=4, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_SMALL))

        sample_label = ctk.CTkLabel(
            section,
            text="Modo de amostragem",
            text_color=COLORS["text_secondary"],
            font=FONT_NORMAL,
        )
        sample_label.grid(row=5, column=0, sticky="w", padx=PAD_LARGE)
        self.sample_mode_option = ctk.CTkOptionMenu(
            section,
            values=["Temperatura atual", "Média das últimas 5 leituras"],
            fg_color=COLORS["card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_strong"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text_primary"],
            text_color=COLORS["text_primary"],
            font=FONT_NORMAL,
        )
        self.sample_mode_option.set("Temperatura atual")
        self.sample_mode_option.grid(row=6, column=0, sticky="ew", padx=PAD_LARGE, pady=(0, PAD_NORMAL))

    def _toggle_config_panel(self) -> None:
        self._config_expanded = not self._config_expanded
        if self._config_expanded:
            self._config_body.grid()
            self._toggle_btn.configure(text="Ocultar")
        else:
            self._config_body.grid_remove()
            self._toggle_btn.configure(text="Mostrar")

    def update_temperature(self, value) -> None:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return

        self.sensor_temperature_var.set(f"{numeric:.1f} °C")
        self.temperature_history.append(numeric)
        if len(self.temperature_history) > 50:
            self.temperature_history = self.temperature_history[-50:]

        if self._chart:
            self._chart.update(self.temperature_history)

    def update_mqtt_status(self, status) -> None:
        if isinstance(status, bool):
            text = "MQTT: Conectado" if status else "MQTT: Tentando reconectar..."
        else:
            text = str(status)

        self.mqtt_status_var.set(text)
        is_connected = "conectado" in text.lower()
        color = COLORS["accent"] if is_connected else COLORS["text_muted"]
        if self._mqtt_status_label is not None:
            self._mqtt_status_label.configure(text_color=color)

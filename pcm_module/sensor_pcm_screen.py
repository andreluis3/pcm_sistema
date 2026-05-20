from __future__ import annotations
import os
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pcm_module.pcm_temperature_sensor import PCMTemperatureSensor, SensorPCMResult


from ui_styles import (
    BG_COLOR, TEXT_SECONDARY, SENSOR_ACCENT, BG_SENSOR, CARD_BORDER_SENSOR, 
    TEXT_PRIMARY, Tooltip, style_ax_dark
)

class SensorPCMScreen(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent, fg_color=BG_COLOR)
        self.sensor = PCMTemperatureSensor()
        self.sensor_result: SensorPCMResult | None = None
        self.sensor_chart_canvases: list[FigureCanvasTkAgg] = []
        self.sensor_kpi_values: dict[str, ctk.CTkLabel] = {}
        
        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Header Sensor
        sensor_header = ctk.CTkFrame(self.scroll_frame, fg_color="#0A1628", corner_radius=16, border_width=1, border_color=CARD_BORDER_SENSOR)
        sensor_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(0, 16))
        sensor_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sensor_header, text="Sensor IR — Análise Térmica Passiva com PCM", font=("Arial", 24, "bold"), text_color=SENSOR_ACCENT).grid(row=0, column=0, sticky="w", padx=24, pady=(18, 4))
        
        # Grid de KPIs do Sensor
        self.sensor_kpi_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sensor_kpi_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 16))
        for col in range(4): self.sensor_kpi_frame.grid_columnconfigure(col, weight=1, uniform="skpi")

        # Dicionário de montagem dos cards de forma limpa, sem quebrar identação externa
        sensor_kpi_defs = [
            ("Temperatura Pico", "--", "Pico de temperatura filtrada medido pelo sensor (°C)."),
            ("Temperatura Inicial", "--", "Temperatura no início do ensaio (°C)."),
            ("Duração do Ensaio", "--", "Tempo total do experimento (min)."),
            ("Energia Absorvida", "--", "Energia absorvida estimada pelo PCM (J).")
        ]
        for idx, (key, default, tip) in enumerate(sensor_kpi_defs):
            self._create_sensor_kpi_card(idx, key, default, tooltip=tip)

    def _create_sensor_kpi_card(self, index: int, title: str, default: str, *, tooltip: str) -> None:
        card = ctk.CTkFrame(self.sensor_kpi_frame, fg_color=BG_SENSOR, corner_radius=14, border_width=1, border_color=CARD_BORDER_SENSOR)
        card.grid(row=index // 4, column=index % 4, sticky="nsew", padx=5, pady=5)
        
        title_lbl = ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"), text_color="#4A6FA5")
        title_lbl.pack(anchor="w", padx=16, pady=(11, 3))
        Tooltip(title_lbl, tooltip)

        value_lbl = ctk.CTkLabel(card, text=default, font=("Arial", 22, "bold"), text_color=TEXT_PRIMARY)
        value_lbl.pack(anchor="w", padx=16, pady=(0, 12))
        self.sensor_kpi_values[title] = value_lbl

    def import_sensor_csv(self) -> None:
        pass

    def _set_initial_content(self) -> None:
        pass
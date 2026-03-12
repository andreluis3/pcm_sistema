from .charts import LineChart, BarChart
from .sidebar import Sidebar
from .widgets import StatCard
import customtkinter as ctk
from collections import deque
import random


import random
from collections import deque
from typing import Deque

import customtkinter as ctk
from tkinter import Canvas

from .charts import LineChart, BarChart
from .sidebar import Sidebar
from .widgets import StatCard


BG = "#0F1115"
CARD = "#1B1E25"
SIDEBAR = "#15181F"
BORDER = "#2A2E38"
CYAN = "#00F2FF"
AMBER = "#FFB800"
TEXT = "#E5E7EB"
MUTED = "#9AA0AB"


class PCMDashboard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PCM Thermal Manager")
        self.geometry("1200x720")
        self.minsize(1100, 640)
        self.configure(fg_color=BG)

        self._temperature = 28.5
        self._temp_history: Deque[float] = deque(maxlen=60)
        self._energy_history: Deque[float] = deque(maxlen=60)
        self._efficiency_history: Deque[float] = deque(maxlen=8)

        self._build_layout()
        self.after(500, self._update_loop)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, bg_color=SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color=BG)
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=16)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.content, fg_color=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="PCM Thermal Manager",
            text_color=TEXT,
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        status = ctk.CTkFrame(header, fg_color=CARD, corner_radius=16, border_width=1, border_color=BORDER)
        status.grid(row=0, column=1, padx=(12, 0))
        status.grid_columnconfigure(1, weight=1)

        status_dot = ctk.CTkLabel(status, text="●", text_color=CYAN, font=ctk.CTkFont(size=14))
        status_dot.grid(row=0, column=0, padx=(12, 6), pady=10)
        status_label = ctk.CTkLabel(
            status,
            text="Arduino Connected",
            text_color=TEXT,
            font=ctk.CTkFont(size=12),
        )
        status_label.grid(row=0, column=1, padx=(0, 12), pady=10)

        right_block = ctk.CTkFrame(header, fg_color=CARD, corner_radius=16, border_width=1, border_color=BORDER)
        right_block.grid(row=0, column=2, padx=(12, 0))

        self.temp_label = ctk.CTkLabel(
            right_block,
            text="28.5°C",
            text_color=CYAN,
            font=ctk.CTkFont(family="Courier", size=26, weight="bold"),
        )
        self.temp_label.grid(row=0, column=0, padx=16, pady=(12, 2))

        self.phase_badge = ctk.CTkLabel(
            right_block,
            text="SOLID",
            text_color=AMBER,
            fg_color="#22262F",
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.phase_badge.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self.content, fg_color=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=1)
        body.grid_rowconfigure(1, weight=1)

        self._build_left_card(body)
        self._build_charts(body)
        self._build_right_panel(body)

        bottom = ctk.CTkFrame(self.content, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        bottom.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        bottom.grid_columnconfigure(0, weight=1)

        self.bar_chart = BarChart(bottom, "Cycle Efficiency", color="#5BC0FF")
        self.bar_chart.widget.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

    def _build_left_card(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12), pady=(0, 12))
        card.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(card, text="Material State", text_color=TEXT, font=ctk.CTkFont(size=14, weight="bold"))
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self.cylinder = Canvas(card, width=220, height=320, bg=CARD, highlightthickness=0)
        self.cylinder.grid(row=1, column=0, padx=16, pady=(6, 8))
        self._draw_cylinder("SOLID")

        self.material_label = ctk.CTkLabel(
            card,
            text="Coconut Oil",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.material_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

    def _draw_cylinder(self, state: str) -> None:
        self.cylinder.delete("all")
        self.cylinder.create_oval(40, 40, 180, 80, outline=BORDER, width=2, fill="#1E222B")
        self.cylinder.create_rectangle(40, 60, 180, 260, outline=BORDER, width=2, fill="#1A1D24")
        self.cylinder.create_oval(40, 240, 180, 280, outline=BORDER, width=2, fill="#161A22")

        if state == "SOLID":
            top_color = AMBER
            bottom_color = "#EDEDED"
            label = "Solid"
        else:
            top_color = CYAN
            bottom_color = "#CFEFFF"
            label = "Liquid"

        self.cylinder.create_rectangle(50, 80, 170, 170, outline="", fill=top_color)
        self.cylinder.create_rectangle(50, 170, 170, 240, outline="", fill=bottom_color)
        self.cylinder.create_text(110, 140, text=label, fill="#0F1115", font=("Courier", 16, "bold"))

    def _build_charts(self, parent) -> None:
        chart_col = ctk.CTkFrame(parent, fg_color=BG)
        chart_col.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 12))
        chart_col.grid_rowconfigure(1, weight=1)
        chart_col.grid_rowconfigure(2, weight=1)

        temp_card = ctk.CTkFrame(chart_col, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        temp_card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        temp_card.grid_columnconfigure(0, weight=1)

        self.temp_chart = LineChart(temp_card, "Temperature vs Time", color=CYAN)
        self.temp_chart.widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        energy_card = ctk.CTkFrame(chart_col, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        energy_card.grid(row=2, column=0, sticky="nsew")
        energy_card.grid_columnconfigure(0, weight=1)

        self.energy_chart = LineChart(energy_card, "Energy vs Time", color="#62FFA7")
        self.energy_chart.widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    def _build_right_panel(self, parent) -> None:
        panel = ctk.CTkFrame(parent, fg_color=BG)
        panel.grid(row=0, column=2, rowspan=2, sticky="nsew")
        panel.grid_rowconfigure(5, weight=1)

        metrics = [
            ("Melting Temp", "24.0°C"),
            ("Latent Heat", "210 kJ/kg"),
            ("Stored Energy", "3.2 kJ"),
            ("Number of Cycles", "42"),
            ("Efficiency", "86%"),
        ]

        self.metric_values = []
        for idx, (title, value) in enumerate(metrics):
            card = ctk.CTkFrame(panel, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
            card.grid(row=idx, column=0, sticky="ew", pady=(0, 12))

            title_label = ctk.CTkLabel(card, text=title, text_color=MUTED, font=ctk.CTkFont(size=11))
            title_label.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))

            value_label = ctk.CTkLabel(
                card,
                text=value,
                text_color=TEXT,
                font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            )
            value_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
            self.metric_values.append(value_label)

    def _update_loop(self) -> None:
        self._temperature += random.uniform(-0.4, 0.6)
        self._temperature = max(20.0, min(36.0, self._temperature))

        phase = "SOLID"
        phase_color = AMBER
        if self._temperature >= 27.5:
            phase = "LIQUID"
            phase_color = CYAN

        self.temp_label.configure(text=f"{self._temperature:.1f}°C", text_color=phase_color)
        self.phase_badge.configure(text=phase, text_color=phase_color)
        self._draw_cylinder(phase)

        energy = self._temperature * 0.12 + random.uniform(-0.2, 0.2)
        efficiency = random.uniform(72, 95)

        self._temp_history.append(self._temperature)
        self._energy_history.append(energy)
        self._efficiency_history.append(efficiency)

        self.temp_chart.push(self._temperature)
        self.temp_chart.draw()
        self.energy_chart.push(energy)
        self.energy_chart.draw()
        self.bar_chart.push(efficiency)
        self.bar_chart.draw()

        self.after(1000, self._update_loop)
